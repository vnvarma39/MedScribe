"""
MedScribe Backend — SQLAlchemy Database Engine & Session
"""
from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# ── Ensure data directory exists ─────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

from sqlalchemy.pool import StaticPool

# ── Engine ────────────────────────────────────────────────────────────────────
connect_args = {"check_same_thread": False}  # Required for SQLite
engine_kwargs = {"connect_args": connect_args, "echo": settings.DEBUG}

if ":memory:" in settings.DATABASE_URL:
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)


# Enable WAL mode for better concurrent read performance on SQLite (file-based only)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    if ":memory:" not in settings.DATABASE_URL:
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ── Session Factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Declarative Base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables defined in the ORM models."""
    Base.metadata.create_all(bind=engine)
