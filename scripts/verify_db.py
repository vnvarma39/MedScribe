#!/usr/bin/env python3
"""
MedScribe — Database Verification Utility
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.database import SessionLocal
from app.db.models import Patient, ClinicalNote, Diagnosis, Medication, Allergy, FollowUp, ExtractionJob

def verify():
    db = SessionLocal()
    try:
        print("🔍 Checking database counts...")
        print(f"  Patients:        {db.query(Patient).count()}")
        print(f"  Clinical Notes:  {db.query(ClinicalNote).count()}")
        print(f"  Diagnoses:       {db.query(Diagnosis).count()}")
        print(f"  Medications:     {db.query(Medication).count()}")
        print(f"  Allergies:       {db.query(Allergy).count()}")
        print(f"  Follow-ups:      {db.query(FollowUp).count()}")
        print(f"  Extraction Jobs: {db.query(ExtractionJob).count()}")
        print("✅ Database verification completed!")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
