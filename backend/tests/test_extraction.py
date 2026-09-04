"""
MedScribe — Entity Extraction Service Unit Tests
"""
from app.services.llm_service import _fallback_extract_entities, _fallback_generate_summary

def test_heuristic_extraction():
    note = "Patient has Hypertension and T2DM. Prescribed Metformin 1000mg twice daily oral. Allergic to Penicillin (rash). Follow up in 2 weeks."
    entities = _fallback_extract_entities(note)
    assert len(entities["diagnoses"]) >= 1
    assert len(entities["medications"]) >= 1
    assert len(entities["allergies"]) >= 1

def test_heuristic_summary():
    note = "Patient has severe COPD. Prescribed Tiotropium 18mcg inhaled daily. Follow up in 1 month."
    entities = _fallback_extract_entities(note)
    summary = _fallback_generate_summary(note, entities)
    assert len(summary) > 20
    assert "COPD" in summary or "Tiotropium" in summary or "patient" in summary.lower()
