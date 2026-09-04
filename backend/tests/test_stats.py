"""
MedScribe — Analytics & Statistics Unit Tests
"""

def test_stats_aggregation_empty(client):
    response = client.get("/api/v1/stats/")
    assert response.status_code == 200
    data = response.json()
    assert data["total_patients"] == 0
    assert data["total_notes"] == 0
    assert isinstance(data["top_diagnoses"], list)
    assert isinstance(data["top_medications"], list)
