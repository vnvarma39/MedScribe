#!/usr/bin/env python3
"""
MedScribe — Ingest Single Clinical Note CLI
"""
import sys
import requests

API_URL = "http://localhost:8000"

def ingest(patient_id: int, note_text: str, source: str = "Clinic"):
    payload = {
        "patient_id": patient_id,
        "raw_text": note_text,
        "source": source
    }
    r = requests.post(f"{API_URL}/api/v1/notes/", json=payload)
    if r.status_code == 201:
        print(f"✅ Ingested Note #{r.json()['id']} successfully!")
    else:
        print(f"❌ Error: {r.status_code} {r.text}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        ingest(int(sys.argv[1]), sys.argv[2])
    else:
        print("Usage: python ingest_single_note.py <patient_id> <note_text>")
