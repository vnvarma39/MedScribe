"""
MedScribe — Entity & Extraction Job Pydantic Schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────────────
# Diagnosis
# ─────────────────────────────────────────────────────────────────────────────
class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    code: Optional[str] = None
    description: str
    severity: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Medication
# ─────────────────────────────────────────────────────────────────────────────
class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Allergy
# ─────────────────────────────────────────────────────────────────────────────
class AllergyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Follow-Up
# ─────────────────────────────────────────────────────────────────────────────
class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    task: str
    due_date: Optional[str] = None
    priority: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Job
# ─────────────────────────────────────────────────────────────────────────────
class ExtractionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    status: str
    llm_provider: Optional[str] = None
    model_used: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate: all entities for a note
# ─────────────────────────────────────────────────────────────────────────────
class NoteEntitiesResponse(BaseModel):
    """All extracted entities for a given note."""
    note_id: int
    diagnoses: List[DiagnosisResponse] = Field(default_factory=list)
    medications: List[MedicationResponse] = Field(default_factory=list)
    allergies: List[AllergyResponse] = Field(default_factory=list)
    follow_ups: List[FollowUpResponse] = Field(default_factory=list)
    entity_counts: Dict[str, int] = Field(default_factory=dict)
