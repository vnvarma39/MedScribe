"""
MedScribe — Stats / Analytics API Route

Endpoint:
    GET /api/v1/stats/   Aggregate dashboard statistics
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import (
    Allergy,
    ClinicalNote,
    Diagnosis,
    ExtractionJob,
    FollowUp,
    Medication,
    Patient,
)
from app.schemas.stats import ExtractionStatsResponse, StatsResponse, TopEntityItem

router = APIRouter(prefix="/stats", tags=["Analytics"])


@router.get(
    "/",
    response_model=StatsResponse,
    summary="Get aggregate statistics for the dashboard",
)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    # ── Entity counts ─────────────────────────────────────────────────────────
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    total_notes = db.query(func.count(ClinicalNote.id)).scalar() or 0
    total_diagnoses = db.query(func.count(Diagnosis.id)).scalar() or 0
    total_medications = db.query(func.count(Medication.id)).scalar() or 0
    total_allergies = db.query(func.count(Allergy.id)).scalar() or 0
    total_follow_ups = db.query(func.count(FollowUp.id)).scalar() or 0

    # ── Extraction job stats ──────────────────────────────────────────────────
    total_jobs = db.query(func.count(ExtractionJob.id)).scalar() or 0
    completed = (
        db.query(func.count(ExtractionJob.id))
        .filter(ExtractionJob.status == "completed")
        .scalar() or 0
    )
    failed = (
        db.query(func.count(ExtractionJob.id))
        .filter(ExtractionJob.status == "failed")
        .scalar() or 0
    )
    pending = (
        db.query(func.count(ExtractionJob.id))
        .filter(ExtractionJob.status.in_(["pending", "running"]))
        .scalar() or 0
    )
    avg_duration = (
        db.query(func.avg(ExtractionJob.duration_ms))
        .filter(ExtractionJob.status == "completed")
        .scalar() or 0.0
    )

    # ── Top diagnoses ─────────────────────────────────────────────────────────
    diag_rows = (
        db.query(Diagnosis.description, func.count(Diagnosis.id).label("cnt"))
        .group_by(Diagnosis.description)
        .order_by(func.count(Diagnosis.id).desc())
        .limit(10)
        .all()
    )
    top_diagnoses: List[TopEntityItem] = [
        TopEntityItem(name=row.description, count=row.cnt) for row in diag_rows
    ]

    # ── Top medications ───────────────────────────────────────────────────────
    med_rows = (
        db.query(Medication.name, func.count(Medication.id).label("cnt"))
        .group_by(Medication.name)
        .order_by(func.count(Medication.id).desc())
        .limit(10)
        .all()
    )
    top_medications: List[TopEntityItem] = [
        TopEntityItem(name=row.name, count=row.cnt) for row in med_rows
    ]

    # ── Top allergens ─────────────────────────────────────────────────────────
    allergy_rows = (
        db.query(Allergy.allergen, func.count(Allergy.id).label("cnt"))
        .group_by(Allergy.allergen)
        .order_by(func.count(Allergy.id).desc())
        .limit(10)
        .all()
    )
    top_allergens: List[TopEntityItem] = [
        TopEntityItem(name=row.allergen, count=row.cnt) for row in allergy_rows
    ]

    # ── Notes by source ───────────────────────────────────────────────────────
    source_rows = (
        db.query(ClinicalNote.source, func.count(ClinicalNote.id).label("cnt"))
        .group_by(ClinicalNote.source)
        .all()
    )
    notes_by_source = {
        (row.source or "Unknown"): row.cnt for row in source_rows
    }

    return StatsResponse(
        total_patients=total_patients,
        total_notes=total_notes,
        total_diagnoses=total_diagnoses,
        total_medications=total_medications,
        total_allergies=total_allergies,
        total_follow_ups=total_follow_ups,
        extraction=ExtractionStatsResponse(
            total_jobs=total_jobs,
            completed=completed,
            failed=failed,
            pending=pending,
            avg_duration_ms=round(avg_duration, 1),
        ),
        top_diagnoses=top_diagnoses,
        top_medications=top_medications,
        top_allergens=top_allergens,
        notes_by_source=notes_by_source,
    )
