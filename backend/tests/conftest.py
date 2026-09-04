"""
MedScribe Test Suite — Shared Fixtures

Strategy: Set DATABASE_URL env var to in-memory SQLite BEFORE any app modules
are imported. This ensures the Settings object picks up the test URL and the
engine created in database.py connects to the in-memory DB.
"""
from __future__ import annotations

import os

# ── MUST be set before any app imports ────────────────────────────────────────
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["OPENROUTER_API_KEY"] = "test-key"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

# Import app modules AFTER env is patched
from app.db.database import Base, engine as app_engine, get_db  # noqa: E402
from app.main import app  # noqa: E402

# Build a session factory bound to the app's (now in-memory) engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Create all tables before each test; drop and recreate after."""
    Base.metadata.create_all(bind=app_engine)
    yield
    Base.metadata.drop_all(bind=app_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provide an isolated test DB session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with DB dependency overridden to use test session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
