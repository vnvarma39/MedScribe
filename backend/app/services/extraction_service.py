"""
MedScribe — Extraction Orchestration Service

Coordinates the full pipeline:
    ClinicalNote  →  LLM extraction  →  Parsed entities  →  DB persistence
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.database import SessionLocal
from app.db.models import (
    Allergy,
    ClinicalNote,
    Diagnosis,
    ExtractionJob,
    FollowUp,
    Medication,
)
from app.services.llm_service import llm_service
from app.core.config import settings


def run_extraction(note: ClinicalNote, db: Session) -> ExtractionJob:
    """
    Run LLM entity extraction for a note and persist all entities to DB.

    Args:
        note: The ClinicalNote ORM object (must be committed to DB already).
        db:   An active SQLAlchemy session.

    Returns:
        The completed (or failed) ExtractionJob record.
    """
    # Create extraction job record
    provider_name, _, _, model_name = llm_service.get_provider_and_model()
    job = ExtractionJob(
        note_id=note.id,
        status="running",
        llm_provider=provider_name,
        model_used=model_name,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info("Starting extraction job={} for note={}", job.id, note.id)

    try:
        entities, duration_ms, provider_used, model_used = llm_service.extract_entities(note.raw_text)

        # Update actual provider/model used (may be fallback)
        job.llm_provider = provider_used
        job.model_used = model_used

        # ── Persist diagnoses ─────────────────────────────────────────────────
        for d in entities.get("diagnoses", []):
            db.add(
                Diagnosis(
                    note_id=note.id,
                    code=d.get("code") or None,
                    description=d["description"],
                    severity=d.get("severity") or "unknown",
                )
            )

        # ── Persist medications ───────────────────────────────────────────────
        for m in entities.get("medications", []):
            db.add(
                Medication(
                    note_id=note.id,
                    name=m["name"],
                    dosage=m.get("dosage") or None,
                    frequency=m.get("frequency") or None,
                    route=m.get("route") or None,
                )
            )

        # ── Persist allergies ─────────────────────────────────────────────────
        for a in entities.get("allergies", []):
            db.add(
                Allergy(
                    note_id=note.id,
                    allergen=a["allergen"],
                    reaction=a.get("reaction") or None,
                    severity=a.get("severity") or "unknown",
                )
            )

        # ── Persist follow-ups ────────────────────────────────────────────────
        for f in entities.get("follow_ups", []):
            db.add(
                FollowUp(
                    note_id=note.id,
                    task=f["task"],
                    due_date=f.get("due_date") or None,
                    priority=f.get("priority") or "routine",
                )
            )

        # Mark job completed
        job.status = "completed"
        job.duration_ms = duration_ms
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "Extraction job={} completed in {} ms [{}:{}] — diagnoses={}, meds={}, allergies={}, followups={}",
            job.id,
            duration_ms,
            provider_used,
            model_used,
            len(entities.get("diagnoses", [])),
            len(entities.get("medications", [])),
            len(entities.get("allergies", [])),
            len(entities.get("follow_ups", [])),
        )

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.error("Extraction job={} failed: {}", job.id, exc)
        raise

    return job


def run_extraction_background(note_id: int) -> None:
    """
    Background-safe wrapper: creates its own DB session.
    Use this with FastAPI BackgroundTasks (not in the request session scope).
    """
    db = SessionLocal()
    try:
        note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
        if not note:
            logger.error("Background extraction: note_id={} not found", note_id)
            return
        run_extraction(note, db)
    except Exception as exc:
        logger.error("Background extraction failed for note_id={}: {}", note_id, exc)
    finally:
        db.close()
