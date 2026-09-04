"""
MedScribe — Clinical Notes API Tests
"""
from __future__ import annotations

import pytest


@pytest.fixture
def patient(client):
    """Create and return a test patient."""
    resp = client.post("/api/v1/patients/", json={"name": "Test Patient", "mrn": "MRN-TEST"})
    assert resp.status_code == 201
    return resp.json()


SAMPLE_NOTE = (
    "Patient is a 58-year-old male with a history of Type 2 Diabetes Mellitus and hypertension. "
    "He presents with complaints of increased thirst and frequent urination over the past 2 weeks. "
    "Current medications include Metformin 1000mg twice daily and Lisinopril 10mg daily. "
    "Allergic to Penicillin (causes hives). "
    "Plan: Order HbA1c, Fasting glucose, BMP. Follow-up in 4 weeks."
)


def test_create_note(client, patient):
    """POST /api/v1/notes/ creates a note and returns 201."""
    payload = {
        "patient_id": patient["id"],
        "raw_text": SAMPLE_NOTE,
        "source": "Clinic",
        "provider": "Dr. Smith",
    }
    response = client.post("/api/v1/notes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == patient["id"]
    assert data["source"] == "Clinic"
    assert "id" in data
    assert data["extraction_status"] == "pending"


def test_create_note_invalid_patient(client):
    """POST /api/v1/notes/ with unknown patient_id returns 404."""
    payload = {"patient_id": 9999, "raw_text": SAMPLE_NOTE}
    response = client.post("/api/v1/notes/", json=payload)
    assert response.status_code == 404


def test_create_note_too_short_text(client, patient):
    """POST /api/v1/notes/ with very short text returns 422 (Pydantic validation)."""
    payload = {"patient_id": patient["id"], "raw_text": "hi"}
    response = client.post("/api/v1/notes/", json=payload)
    assert response.status_code == 422


def test_list_notes_empty(client, patient):
    """GET /api/v1/notes/ returns empty list when no notes."""
    response = client.get("/api/v1/notes/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_notes_pagination(client, patient):
    """GET /api/v1/notes/ supports pagination."""
    for i in range(5):
        client.post(
            "/api/v1/notes/",
            json={"patient_id": patient["id"], "raw_text": SAMPLE_NOTE + f" Visit {i}"},
        )

    response = client.get("/api/v1/notes/?page=1&per_page=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2


def test_list_notes_search(client, patient):
    """GET /api/v1/notes/ full-text search on raw_text."""
    client.post(
        "/api/v1/notes/",
        json={"patient_id": patient["id"], "raw_text": "Patient has severe chest pain and dyspnea."},
    )
    client.post(
        "/api/v1/notes/",
        json={"patient_id": patient["id"], "raw_text": "Routine follow-up for diabetes management."},
    )

    response = client.get("/api/v1/notes/?search=chest+pain")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "chest pain" in data["items"][0]["raw_text"]


def test_get_note(client, patient):
    """GET /api/v1/notes/{id} returns note with entity arrays."""
    create_resp = client.post(
        "/api/v1/notes/",
        json={"patient_id": patient["id"], "raw_text": SAMPLE_NOTE},
    )
    note_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/notes/{note_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    # Entities lists should be present (may be empty if extraction is still running)
    assert "diagnoses" in data
    assert "medications" in data
    assert "allergies" in data
    assert "follow_ups" in data
    assert "extraction_jobs" in data


def test_get_note_not_found(client):
    """GET /api/v1/notes/9999 returns 404."""
    response = client.get("/api/v1/notes/9999")
    assert response.status_code == 404


def test_delete_note(client, patient):
    """DELETE /api/v1/notes/{id} removes the note."""
    create_resp = client.post(
        "/api/v1/notes/",
        json={"patient_id": patient["id"], "raw_text": SAMPLE_NOTE},
    )
    note_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/notes/{note_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/notes/{note_id}")
    assert get_resp.status_code == 404


def test_stats_endpoint(client, patient):
    """GET /api/v1/stats/ returns aggregate stats."""
    client.post(
        "/api/v1/notes/",
        json={"patient_id": patient["id"], "raw_text": SAMPLE_NOTE},
    )

    response = client.get("/api/v1/stats/")
    assert response.status_code == 200
    data = response.json()
    assert data["total_patients"] == 1
    assert data["total_notes"] == 1
    assert "extraction" in data
    assert "top_diagnoses" in data


def test_extraction_and_summary_flow(client, patient, db_session):
    """Test full extraction service and summary endpoint."""
    from app.services.extraction_service import run_extraction
    from app.db.models import ClinicalNote

    create_resp = client.post(
        "/api/v1/notes/",
        json={"patient_id": patient["id"], "raw_text": SAMPLE_NOTE},
    )
    note_id = create_resp.json()["id"]

    note = db_session.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    job = run_extraction(note, db_session)
    assert job.status == "completed"

    get_resp = client.get(f"/api/v1/notes/{note_id}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert len(detail["diagnoses"]) > 0
    assert len(detail["medications"]) > 0

    summary_resp = client.get(f"/api/v1/notes/{note_id}/summary")
    assert summary_resp.status_code == 200
    sdata = summary_resp.json()
    assert len(sdata["summary"]) > 20
    assert sdata["note_id"] == note_id
