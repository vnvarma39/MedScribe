"""
MedScribe — Stats & Analytics Pydantic Schemas
"""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class ExtractionStatsResponse(BaseModel):
    total_jobs: int
    completed: int
    failed: int
    pending: int
    avg_duration_ms: float


class TopEntityItem(BaseModel):
    name: str
    count: int


class StatsResponse(BaseModel):
    """Aggregate statistics for the dashboard."""
    total_patients: int
    total_notes: int
    total_diagnoses: int
    total_medications: int
    total_allergies: int
    total_follow_ups: int

    extraction: ExtractionStatsResponse

    # Top entities (for charts)
    top_diagnoses: List[TopEntityItem]
    top_medications: List[TopEntityItem]
    top_allergens: List[TopEntityItem]

    # Notes per source
    notes_by_source: Dict[str, int]
