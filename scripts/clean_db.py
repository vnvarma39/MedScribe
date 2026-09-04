#!/usr/bin/env python3
"""
MedScribe — Database Reset Utility
"""
import os
import glob

def clean():
    files = glob.glob("data/medscribe.db*") + glob.glob("backend/data/medscribe.db*")
    for f in files:
        try:
            os.remove(f)
            print(f"Removed {f}")
        except Exception as e:
            print(f"Could not remove {f}: {e}")
    print("Database reset complete.")

if __name__ == "__main__":
    clean()
