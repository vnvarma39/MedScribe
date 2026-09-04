"""
MedScribe — Patient Pydantic Schemas
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Full patient name")
    dob: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, max_length=20, description="Gender (Male/Female/Other/Unknown)")
    mrn: Optional[str] = Field(None, max_length=50, description="Medical Record Number")


class PatientCreate(PatientBase):
    """Request schema for creating a patient."""
    pass


class PatientUpdate(BaseModel):
    """Request schema for partially updating a patient."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    dob: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    mrn: Optional[str] = Field(None, max_length=50)


class PatientResponse(PatientBase):
    """Response schema for a single patient."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    note_count: Optional[int] = 0


class PatientListResponse(BaseModel):
    """Response schema for paginated patient list."""
    total: int
    page: int
    per_page: int
    items: list[PatientResponse]
