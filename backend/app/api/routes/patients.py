"""
MedScribe — Patient API Routes

Endpoints:
    POST   /api/v1/patients/           Create a new patient
    GET    /api/v1/patients/           List patients (paginated + search)
    GET    /api/v1/patients/{id}       Get single patient
    PATCH  /api/v1/patients/{id}       Update patient
    DELETE /api/v1/patients/{id}       Delete patient
    GET    /api/v1/patients/{id}/notes Patient note history
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_pagination
from app.db.models import ClinicalNote, ExtractionJob, Patient
from app.schemas.note import NoteResponse, PaginatedNotesResponse
from app.schemas.patient import (
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)

router = APIRouter(prefix="/patients", tags=["Patients"])


def _build_patient_response(patient: Patient, db: Session) -> PatientResponse:
    note_count = db.query(func.count(ClinicalNote.id)).filter(
        ClinicalNote.patient_id == patient.id
    ).scalar() or 0
    data = PatientResponse.model_validate(patient)
    data.note_count = note_count
    return data


# ── POST /patients/ ───────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new patient",
)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
) -> PatientResponse:
    # Check MRN uniqueness
    if patient_in.mrn:
        existing = db.query(Patient).filter(Patient.mrn == patient_in.mrn).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Patient with MRN '{patient_in.mrn}' already exists (id={existing.id})",
            )

    patient = Patient(**patient_in.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return _build_patient_response(patient, db)


# ── GET /patients/ ────────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=PatientListResponse,
    summary="List patients with pagination and search",
)
def list_patients(
    search: Optional[str] = Query(None, description="Full-text search on patient name or MRN"),
    pagination: dict = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> PatientListResponse:
    query = db.query(Patient)

    if search:
        term = f"%{search}%"
        query = query.filter(
            (Patient.name.ilike(term)) | (Patient.mrn.ilike(term))
        )

    total = query.count()
    patients = (
        query.order_by(Patient.created_at.desc())
        .offset(pagination["offset"])
        .limit(pagination["per_page"])
        .all()
    )

    items = [_build_patient_response(p, db) for p in patients]
    return PatientListResponse(
        total=total,
        page=pagination["page"],
        per_page=pagination["per_page"],
        items=items,
    )


# ── GET /patients/{id} ────────────────────────────────────────────────────────
@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get a single patient by ID",
)
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> PatientResponse:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return _build_patient_response(patient, db)


# ── PATCH /patients/{id} ──────────────────────────────────────────────────────
@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update patient fields",
)
def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
) -> PatientResponse:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    update_data = patient_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return _build_patient_response(patient, db)


# ── DELETE /patients/{id} ─────────────────────────────────────────────────────
@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a patient and all associated notes",
)
def delete_patient(patient_id: int, db: Session = Depends(get_db)) -> None:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    db.delete(patient)
    db.commit()


# ── GET /patients/{id}/notes ──────────────────────────────────────────────────
@router.get(
    "/{patient_id}/notes",
    response_model=PaginatedNotesResponse,
    summary="Get all clinical notes for a patient",
)
def get_patient_notes(
    patient_id: int,
    pagination: dict = Depends(get_pagination),
    db: Session = Depends(get_db),
) -> PaginatedNotesResponse:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    query = db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id)
    total = query.count()
    notes = (
        query.order_by(ClinicalNote.created_at.desc())
        .offset(pagination["offset"])
        .limit(pagination["per_page"])
        .all()
    )

    items = []
    for note in notes:
        note_resp = NoteResponse.model_validate(note)
        # Attach latest extraction status
        latest_job = (
            db.query(ExtractionJob)
            .filter(ExtractionJob.note_id == note.id)
            .order_by(ExtractionJob.created_at.desc())
            .first()
        )
        note_resp.extraction_status = latest_job.status if latest_job else None
        items.append(note_resp)

    return PaginatedNotesResponse(
        total=total,
        page=pagination["page"],
        per_page=pagination["per_page"],
        items=items,
    )
