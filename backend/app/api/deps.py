"""
MedScribe — FastAPI Route Dependencies
"""
from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db


def get_pagination(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page",
    ),
) -> dict:
    """Shared pagination dependency."""
    return {"page": page, "per_page": per_page, "offset": (page - 1) * per_page}


__all__ = ["get_db", "get_pagination"]
