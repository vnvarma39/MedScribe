#!/usr/bin/env python3
"""
MedScribe — Export Clinical Summary Report CLI
"""
import json
import requests

API_URL = "http://localhost:8000"

def export_report(output_file: str = "clinical_report.json"):
    stats = requests.get(f"{API_URL}/api/v1/stats/").json()
    with open(output_file, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Report saved to {output_file}")

if __name__ == "__main__":
    export_report()
