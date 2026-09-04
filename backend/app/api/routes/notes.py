"""
MedScribe — Clinical Notes API Routes

Endpoints:
    POST  /api/v1/notes/            Ingest a new note + trigger background extraction
    GET   /api/v1/notes/            List notes (paginated + full-text search)
    GET   /api/v1/notes/{id}        Get note with all extracted entities
    GET   /api/v1/notes/{id}/summary  Generate AI clinical summary
    DELETE /api/v1/notes/{id}       Delete a note
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_pagination
from app.core.config import settings
from app.db.models import ClinicalNote, ExtractionJob, Patient
from app.schemas.note import (
    NoteCreate,
    NoteDetailResponse,
    NoteResponse,
    PaginatedNotesResponse,
    SummaryResponse,
)
from app.services.extraction_service import run_extraction_background
from app.services.llm_service import llm_service

router = APIRouter(prefix="/notes", tags=["Clinical Notes"])


def _get_extraction_status(note_id: int, db: Session) -> Optional[str]:
    job = (
        db.query(ExtractionJob)
        .filter(ExtractionJob.note_id == note_id)
        .order_by(ExtractionJob.created_at.desc())
        .first()
    )
    return job.status if job else None


# ── POST /notes/ ──────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a clinical note and trigger LLM entity extraction",
)
def create_note(
    note_in: NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> NoteResponse:
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == note_in.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {note_in.patient_id} not found",
        )

    note = ClinicalNote(**note_in.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)

    # Queue background extraction (non-blocking)
    background_tasks.add_task(run_extraction_background, note.id)

    response = NoteResponse.model_validate(note)
    response.extraction_status = "pending"
    return response


# ── GET /notes/ ───────────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=PaginatedNotesResponse,
    summary="List clinical notes with pagination and full-text search",
)
def list_notes(
    search: Optional[str] = Query(None, description="Full-text search on raw note text"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    source: Optional[str] = Query(None, description="Filter by note source (ER, ICU, Clinic …)"),
    pagination: dict = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> PaginatedNotesResponse:
    query = db.query(ClinicalNote)

    if search:
        query = query.filter(ClinicalNote.raw_text.ilike(f"%{search}%"))
    if patient_id:
        query = query.filter(ClinicalNote.patient_id == patient_id)
    if source:
        query = query.filter(ClinicalNote.source.ilike(f"%{source}%"))

    total = query.count()
    notes = (
        query.order_by(ClinicalNote.created_at.desc())
        .offset(pagination["offset"])
        .limit(pagination["per_page"])
        .all()
    )

    items = []
    for note in notes:
        resp = NoteResponse.model_validate(note)
        resp.extraction_status = _get_extraction_status(note.id, db)
        items.append(resp)

    return PaginatedNotesResponse(
        total=total,
        page=pagination["page"],
        per_page=pagination["per_page"],
        items=items,
    )


# ── GET /notes/{id} ───────────────────────────────────────────────────────────
@router.get(
    "/{note_id}",
    response_model=NoteDetailResponse,
    summary="Get a clinical note with all extracted entities",
)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteDetailResponse:
    note = (
        db.query(ClinicalNote)
        .options(
            joinedload(ClinicalNote.diagnoses),
            joinedload(ClinicalNote.medications),
            joinedload(ClinicalNote.allergies),
            joinedload(ClinicalNote.follow_ups),
            joinedload(ClinicalNote.extraction_jobs),
        )
        .filter(ClinicalNote.id == note_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")

    response = NoteDetailResponse.model_validate(note)
    response.extraction_status = _get_extraction_status(note_id, db)
    return response


# ── GET /notes/{id}/summary ───────────────────────────────────────────────────
@router.get(
    "/{note_id}/summary",
    response_model=SummaryResponse,
    summary="Generate an AI clinical summary for a note",
)
def get_note_summary(note_id: int, db: Session = Depends(get_db)) -> SummaryResponse:
    note = (
        db.query(ClinicalNote)
        .options(
            joinedload(ClinicalNote.diagnoses),
            joinedload(ClinicalNote.medications),
            joinedload(ClinicalNote.allergies),
            joinedload(ClinicalNote.follow_ups),
        )
        .filter(ClinicalNote.id == note_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")

    entities = {
        "diagnoses": [{"code": d.code, "description": d.description, "severity": d.severity} for d in note.diagnoses],
        "medications": [{"name": m.name, "dosage": m.dosage, "frequency": m.frequency, "route": m.route} for m in note.medications],
        "allergies": [{"allergen": a.allergen, "reaction": a.reaction, "severity": a.severity} for a in note.allergies],
        "follow_ups": [{"task": f.task, "due_date": f.due_date, "priority": f.priority} for f in note.follow_ups],
    }

    summary_text, model_used = llm_service.generate_summary(note.raw_text, entities)

    return SummaryResponse(
        note_id=note_id,
        summary=summary_text,
        model_used=model_used,
        generated_at=datetime.now(timezone.utc),
    )


# ── DELETE /notes/{id} ────────────────────────────────────────────────────────
@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a clinical note and all its entities",
)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    db.delete(note)
    db.commit()
