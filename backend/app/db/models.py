"""
MedScribe — SQLAlchemy ORM Models

Tables:
    patients           - Patient demographics
    clinical_notes     - Raw clinical note text
    diagnoses          - Extracted diagnosis entities
    medications        - Extracted medication entities
    allergies          - Extracted allergy entities
    follow_ups         - Extracted follow-up tasks
    extraction_jobs    - LLM extraction job tracking
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Patient
# ─────────────────────────────────────────────────────────────────────────────
class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mrn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)  # Medical Record Number
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    notes: Mapped[List["ClinicalNote"]] = relationship(
        "ClinicalNote", back_populates="patient", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} name={self.name!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Clinical Note
# ─────────────────────────────────────────────────────────────────────────────
class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    note_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # ER, Clinic, ICU, etc.
    provider: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="notes")
    diagnoses: Mapped[List["Diagnosis"]] = relationship(
        "Diagnosis", back_populates="note", cascade="all, delete-orphan"
    )
    medications: Mapped[List["Medication"]] = relationship(
        "Medication", back_populates="note", cascade="all, delete-orphan"
    )
    allergies: Mapped[List["Allergy"]] = relationship(
        "Allergy", back_populates="note", cascade="all, delete-orphan"
    )
    follow_ups: Mapped[List["FollowUp"]] = relationship(
        "FollowUp", back_populates="note", cascade="all, delete-orphan"
    )
    extraction_jobs: Mapped[List["ExtractionJob"]] = relationship(
        "ExtractionJob", back_populates="note", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ClinicalNote id={self.id} patient_id={self.patient_id}>"


# ─────────────────────────────────────────────────────────────────────────────
# Diagnosis
# ─────────────────────────────────────────────────────────────────────────────
class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinical_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)   # ICD-10
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # mild|moderate|severe|unknown

    note: Mapped["ClinicalNote"] = relationship("ClinicalNote", back_populates="diagnoses")

    def __repr__(self) -> str:
        return f"<Diagnosis id={self.id} description={self.description!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Medication
# ─────────────────────────────────────────────────────────────────────────────
class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinical_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    route: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # oral|IV|topical|etc.

    note: Mapped["ClinicalNote"] = relationship("ClinicalNote", back_populates="medications")

    def __repr__(self) -> str:
        return f"<Medication id={self.id} name={self.name!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Allergy
# ─────────────────────────────────────────────────────────────────────────────
class Allergy(Base):
    __tablename__ = "allergies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinical_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    allergen: Mapped[str] = mapped_column(String(200), nullable=False)
    reaction: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # mild|moderate|severe|life-threatening

    note: Mapped["ClinicalNote"] = relationship("ClinicalNote", back_populates="allergies")

    def __repr__(self) -> str:
        return f"<Allergy id={self.id} allergen={self.allergen!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Follow-Up
# ─────────────────────────────────────────────────────────────────────────────
class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinical_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task: Mapped[str] = mapped_column(String(500), nullable=False)
    due_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Free-text or ISO date
    priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # high|medium|low|routine

    note: Mapped["ClinicalNote"] = relationship("ClinicalNote", back_populates="follow_ups")

    def __repr__(self) -> str:
        return f"<FollowUp id={self.id} task={self.task!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Job
# ─────────────────────────────────────────────────────────────────────────────
class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clinical_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending | running | completed | failed
    llm_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    note: Mapped["ClinicalNote"] = relationship("ClinicalNote", back_populates="extraction_jobs")

    def __repr__(self) -> str:
        return f"<ExtractionJob id={self.id} status={self.status!r}>"
