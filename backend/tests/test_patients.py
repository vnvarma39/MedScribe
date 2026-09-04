"""
MedScribe — Patient API Tests
"""
from __future__ import annotations


def test_create_patient(client):
    """POST /api/v1/patients/ creates a patient."""
    payload = {"name": "Jane Doe", "gender": "Female", "mrn": "MRN-001"}
    response = client.post("/api/v1/patients/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["mrn"] == "MRN-001"
    assert "id" in data


def test_create_patient_duplicate_mrn(client):
    """POST /api/v1/patients/ with duplicate MRN returns 409."""
    payload = {"name": "John Smith", "mrn": "MRN-DUP"}
    client.post("/api/v1/patients/", json=payload)
    response = client.post("/api/v1/patients/", json=payload)
    assert response.status_code == 409


def test_list_patients_empty(client):
    """GET /api/v1/patients/ returns empty list when no patients."""
    response = client.get("/api/v1/patients/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_patients_pagination(client):
    """GET /api/v1/patients/ supports pagination."""
    for i in range(5):
        client.post("/api/v1/patients/", json={"name": f"Patient {i}"})

    response = client.get("/api/v1/patients/?page=1&per_page=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["per_page"] == 3


def test_list_patients_search(client):
    """GET /api/v1/patients/ supports name search."""
    client.post("/api/v1/patients/", json={"name": "Alice Johnson"})
    client.post("/api/v1/patients/", json={"name": "Bob Smith"})

    response = client.get("/api/v1/patients/?search=Alice")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Alice Johnson"


def test_get_patient(client):
    """GET /api/v1/patients/{id} returns the patient."""
    create_resp = client.post("/api/v1/patients/", json={"name": "Test Patient"})
    patient_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/patients/{patient_id}")
    assert response.status_code == 200
    assert response.json()["id"] == patient_id


def test_get_patient_not_found(client):
    """GET /api/v1/patients/999 returns 404."""
    response = client.get("/api/v1/patients/999")
    assert response.status_code == 404


def test_update_patient(client):
    """PATCH /api/v1/patients/{id} updates fields."""
    create_resp = client.post("/api/v1/patients/", json={"name": "Old Name"})
    patient_id = create_resp.json()["id"]

    response = client.patch(f"/api/v1/patients/{patient_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_patient(client):
    """DELETE /api/v1/patients/{id} removes the patient."""
    create_resp = client.post("/api/v1/patients/", json={"name": "To Delete"})
    patient_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/patients/{patient_id}")
    assert response.status_code == 204

    get_resp = client.get(f"/api/v1/patients/{patient_id}")
    assert get_resp.status_code == 404
