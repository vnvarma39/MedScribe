"""
MedScribe — Clinical Note Pydantic Schemas
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.entities import (
    AllergyResponse,
    DiagnosisResponse,
    ExtractionJobResponse,
    FollowUpResponse,
    MedicationResponse,
)


class NoteBase(BaseModel):
    patient_id: int = Field(..., description="ID of the patient this note belongs to")
    raw_text: str = Field(..., min_length=10, description="Unstructured clinical note text")
    note_date: Optional[date] = Field(None, description="Date of the clinical note")
    source: Optional[str] = Field(
        None,
        max_length=100,
        description="Origin of the note (e.g. ER, Clinic, ICU, Discharge)",
    )
    provider: Optional[str] = Field(None, max_length=200, description="Attending provider name")


class NoteCreate(NoteBase):
    """Request schema for ingesting a new clinical note."""
    pass


class NoteResponse(NoteBase):
    """Basic note response (list view)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    extraction_status: Optional[str] = None  # Derived from latest ExtractionJob


class NoteDetailResponse(NoteResponse):
    """Full note response with all extracted entities."""
    diagnoses: List[DiagnosisResponse] = []
    medications: List[MedicationResponse] = []
    allergies: List[AllergyResponse] = []
    follow_ups: List[FollowUpResponse] = []
    extraction_jobs: List[ExtractionJobResponse] = []


class PaginatedNotesResponse(BaseModel):
    """Response schema for paginated note list."""
    total: int
    page: int
    per_page: int
    items: List[NoteResponse]


class SummaryResponse(BaseModel):
    """AI-generated clinical summary."""
    note_id: int
    summary: str
    model_used: str
    generated_at: datetime
