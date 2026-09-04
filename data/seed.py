#!/usr/bin/env python3
"""
MedScribe — Database Seed Script

Populates the database with 6 realistic patients and 20 clinical notes.
Requires the MedScribe backend to be running (local or Docker).

Usage:
    # With backend running locally:
    python data/seed.py

    # With Docker Compose:
    docker-compose up -d
    python data/seed.py
"""
from __future__ import annotations

import sys
import time
from datetime import date, timedelta
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import requests

API_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def check_api() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def create_patient(name: str, dob: Optional[str], gender: str, mrn: str) -> Optional[int]:
    payload = {"name": name, "gender": gender, "mrn": mrn}
    if dob:
        payload["dob"] = dob
    r = requests.post(f"{API_URL}/api/v1/patients/", json=payload, headers=HEADERS, timeout=10)
    if r.status_code == 201:
        return r.json()["id"]
    elif r.status_code == 409:
        # Already exists — fetch by listing
        list_r = requests.get(f"{API_URL}/api/v1/patients/?search={name}", timeout=10)
        items = list_r.json().get("items", [])
        if items:
            return items[0]["id"]
    print(f"  ⚠️  Failed to create patient {name}: {r.status_code} {r.text[:100]}")
    return None


def create_note(patient_id: int, text: str, source: str, note_date: str, provider: str) -> Optional[int]:
    payload = {
        "patient_id": patient_id,
        "raw_text": text,
        "source": source,
        "note_date": note_date,
        "provider": provider,
    }
    r = requests.post(f"{API_URL}/api/v1/notes/", json=payload, headers=HEADERS, timeout=15)
    if r.status_code == 201:
        return r.json()["id"]
    print(f"  ⚠️  Failed to create note: {r.status_code} {r.text[:100]}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Sample Data
# ─────────────────────────────────────────────────────────────────────────────
PATIENTS = [
    {"name": "Margaret Sullivan", "dob": "1956-04-12", "gender": "Female", "mrn": "MRN-10001"},
    {"name": "Robert Chen", "dob": "1948-09-28", "gender": "Male", "mrn": "MRN-10002"},
    {"name": "Amara Okafor", "dob": "1972-01-15", "gender": "Female", "mrn": "MRN-10003"},
    {"name": "James Rivera", "dob": "1965-07-03", "gender": "Male", "mrn": "MRN-10004"},
    {"name": "Linda Kowalski", "dob": "1980-11-22", "gender": "Female", "mrn": "MRN-10005"},
    {"name": "David Pham", "dob": "1990-03-08", "gender": "Male", "mrn": "MRN-10006"},
]

CLINICAL_NOTES = [
    # ── Margaret Sullivan (Diabetes + Hypertension) ───────────────────────────
    {
        "patient_mrn": "MRN-10001",
        "source": "Clinic",
        "note_date": "2024-01-15",
        "provider": "Dr. Sarah Mitchell",
        "text": (
            "Patient is a 68-year-old female with longstanding Type 2 Diabetes Mellitus (T2DM) and essential hypertension, "
            "presenting for routine 3-month follow-up. HbA1c today is 8.2%, up from 7.6% last visit. Patient reports poor "
            "dietary compliance over the holiday period and decreased physical activity. Blood pressure 152/94 mmHg. "
            "BMI 31.4. Mild peripheral edema noted bilaterally. Current medications: Metformin 1000mg twice daily, "
            "Glipizide 10mg once daily with breakfast, Lisinopril 20mg once daily, Amlodipine 5mg once daily, "
            "Atorvastatin 40mg at bedtime. Allergic to Sulfonamides (causes diffuse urticarial rash). "
            "Assessment: Suboptimal glycemic control. Hypertension partially controlled. "
            "Plan: Increase Glipizide to 10mg twice daily. Add SGLT2 inhibitor - Empagliflozin 10mg daily. "
            "Dietary counseling referral. Recheck HbA1c, BMP, and urine microalbumin in 3 months. "
            "Ophthalmology referral for annual diabetic eye exam."
        ),
    },
    {
        "patient_mrn": "MRN-10001",
        "source": "ER",
        "note_date": "2024-03-02",
        "provider": "Dr. Kevin Walsh",
        "text": (
            "68-year-old female with known T2DM and hypertension presenting to ED with dizziness, nausea, and blood "
            "glucose of 52 mg/dL per home glucometer. Patient reports she took her Glipizide but skipped breakfast this "
            "morning. BP 138/88, HR 98. No diaphoresis currently. IV access established, dextrose 50% 25g IV administered. "
            "Repeat glucose 98 mg/dL, patient asymptomatic. Diagnosed with hypoglycemia secondary to sulfonylurea use. "
            "Current medications unchanged from chart. No new allergies. "
            "Discharge plan: Reduce Glipizide to 5mg daily. Strict instruction to eat with medication. "
            "Follow up with primary care in 1 week. Contact Dr. Mitchell regarding medication adjustment."
        ),
    },
    {
        "patient_mrn": "MRN-10001",
        "source": "Clinic",
        "note_date": "2024-06-10",
        "provider": "Dr. Sarah Mitchell",
        "text": (
            "Follow-up visit for Margaret. HbA1c improved to 7.4% — excellent glycemic control. BP 128/82. "
            "Patient tolerating Empagliflozin well, reports increased urination which has stabilized. No genital infections. "
            "Lipids: LDL 68 mg/dL, HDL 52 mg/dL, TG 145 mg/dL — well controlled on statin. "
            "Medications: Metformin 1000mg BID, Glipizide 5mg daily, Empagliflozin 10mg daily, Lisinopril 20mg daily, "
            "Amlodipine 5mg daily, Atorvastatin 40mg QHS. Allergy: Sulfonamides (rash). "
            "Assessment: T2DM well controlled, hypertension at goal. Continue current regimen. "
            "Follow-up in 6 months, HbA1c and comprehensive metabolic panel at that time."
        ),
    },

    # ── Robert Chen (COPD + CHF) ──────────────────────────────────────────────
    {
        "patient_mrn": "MRN-10002",
        "source": "Inpatient",
        "note_date": "2024-02-20",
        "provider": "Dr. Angela Torres",
        "text": (
            "76-year-old male admitted for acute exacerbation of chronic obstructive pulmonary disease (AECOPD) and "
            "decompensated congestive heart failure (CHF). Patient presented with 5-day history of worsening dyspnea, "
            "orthopnea, bilateral leg swelling, and increased sputum production. O2 saturation 88% on room air on admission, "
            "now 94% on 2L nasal cannula. CXR: bilateral pulmonary edema, cardiomegaly. BNP 1,840 pg/mL. "
            "Chest CT showed emphysematous changes consistent with COPD GOLD stage III. "
            "Medications: Tiotropium Bromide 18mcg inhaled daily, Albuterol/Ipratropium nebulized Q6h, "
            "Furosemide 40mg IV BID, Methylprednisolone 125mg IV Q8h, Azithromycin 500mg IV daily. "
            "Allergies: Aspirin (bronchospasm), Penicillin (anaphylaxis). "
            "Cardiology and pulmonology consults placed. Transition to oral medications when clinically stable. "
            "Follow-up: Pulmonology in 2 weeks, Cardiology in 1 week post-discharge."
        ),
    },
    {
        "patient_mrn": "MRN-10002",
        "source": "Discharge",
        "note_date": "2024-02-27",
        "provider": "Dr. Angela Torres",
        "text": (
            "Discharge summary for Robert Chen. Patient hospitalized 7 days for AECOPD and decompensated CHF. "
            "Improved significantly on IV diuresis and steroids. Discharge O2 saturation 96% on 2L home oxygen. "
            "Discharge medications: Tiotropium 18mcg inhaled daily, Albuterol MDI 2 puffs Q4-6h PRN, "
            "Fluticasone/Salmeterol 250/50 mcg inhaled BID, Furosemide 40mg oral daily, "
            "Spironolactone 25mg oral daily, Carvedilol 6.25mg oral BID, Prednisone 40mg oral taper x7 days. "
            "Allergies: Aspirin (bronchospasm), Penicillin (anaphylaxis). "
            "Follow-up appointments: Pulmonology in 2 weeks (Dr. Torres), Cardiology in 1 week. "
            "Instruct patient: Daily weight monitoring, call if weight gain >2 lbs in 24h or >5 lbs in 1 week. "
            "Home oxygen therapy arranged. Home health nursing for medication compliance."
        ),
    },
    {
        "patient_mrn": "MRN-10002",
        "source": "Clinic",
        "note_date": "2024-03-14",
        "provider": "Dr. Angela Torres",
        "text": (
            "Post-hospitalization follow-up for Robert. He is 2 weeks out from discharge. "
            "Doing reasonably well at home on home oxygen at 2L. Adherent to all medications. "
            "Weight today 183 lbs, down 8 lbs from admission weight. No orthopnea. Mild exertional dyspnea on stairs. "
            "BP 118/74, HR 62, SpO2 96% on 2L O2. Lungs: distant breath sounds, mild expiratory wheeze. "
            "Continues on Tiotropium, Fluticasone/Salmeterol BID, Furosemide, Spironolactone, Carvedilol. "
            "Allergies unchanged: Aspirin, Penicillin. Diagnoses: COPD exacerbation resolving, CHF stable. "
            "Plan: Continue current medications. Pulmonary rehabilitation referral. Repeat echocardiogram in 6 weeks. "
            "Influenza and pneumococcal vaccinations updated today."
        ),
    },

    # ── Amara Okafor (Rheumatoid Arthritis) ──────────────────────────────────
    {
        "patient_mrn": "MRN-10003",
        "source": "Clinic",
        "note_date": "2024-01-08",
        "provider": "Dr. Patricia Nguyen",
        "text": (
            "52-year-old female with seropositive rheumatoid arthritis (RA) diagnosed 8 years ago. "
            "Presents for quarterly rheumatology follow-up. Reports improvement in joint pain and morning stiffness "
            "over the past 3 months on current DMARD regimen. Morning stiffness now <30 minutes. "
            "Examination: mild synovitis in bilateral MCP joints and left wrist. DAS28 score 2.8 (low disease activity). "
            "Labs: CRP 0.8 mg/dL (improved from 2.4), RF positive 124 IU/mL, anti-CCP positive. LFTs normal. CBC normal. "
            "Current medications: Methotrexate 20mg subcutaneous weekly, Folic acid 1mg daily, "
            "Hydroxychloroquine 200mg twice daily, Naproxen 500mg twice daily with food PRN. "
            "Allergies: Sulfa drugs (Stevens-Johnson syndrome — SEVERE). NSAIDs such as Ibuprofen (GI intolerance). "
            "Assessment: RA in low disease activity. Continue current regimen. "
            "Plan: Repeat CMP and CBC in 3 months given MTX use. Continue biologic therapy discussion if disease flares. "
            "Follow-up with Dr. Nguyen in 4 months."
        ),
    },
    {
        "patient_mrn": "MRN-10003",
        "source": "Urgent Care",
        "note_date": "2024-04-15",
        "provider": "Dr. Brian Scott",
        "text": (
            "52-year-old female with RA presents to urgent care with 3-day history of right knee swelling, warmth, "
            "and significant pain limiting ambulation. Temperature 37.8°C. Right knee with large effusion, restricted ROM. "
            "Concern for septic arthritis vs. RA flare. Knee aspiration performed: fluid straw-colored, WBC 28,000 "
            "(differential 62% PMN). Gram stain negative. Culture pending. "
            "Diagnosis: Suspected RA flare, septic arthritis ruled out pending culture. "
            "Medications: Patient on Methotrexate, Hydroxychloroquine, Folic acid. Holding Methotrexate pending culture. "
            "Started Prednisone 30mg oral daily x5 days then taper. Celecoxib 200mg daily for pain (Naproxen inadequate). "
            "Allergy reminder: Sulfa drugs (SJS), Ibuprofen (GI). "
            "Follow-up with rheumatology in 48-72 hours or sooner if worsening. Culture follow-up essential."
        ),
    },

    # ── James Rivera (Post-MI Cardiac Care) ──────────────────────────────────
    {
        "patient_mrn": "MRN-10004",
        "source": "Clinic",
        "note_date": "2024-02-05",
        "provider": "Dr. Michael Kim",
        "text": (
            "59-year-old male, 3 months post ST-elevation myocardial infarction (STEMI) with DES placement to LAD. "
            "EF 40% on last echo. Presents for cardiology follow-up. Doing well, no chest pain or dyspnea. "
            "Compliant with dual antiplatelet therapy. BP 122/78, HR 64 bpm. "
            "Echo today: EF improved to 48%, no regional wall motion abnormalities. "
            "Medications: Aspirin 81mg daily, Clopidogrel 75mg daily (continue 12 months from stenting), "
            "Metoprolol succinate 50mg daily, Lisinopril 5mg daily, Atorvastatin 80mg nightly, "
            "Nitroglycerin 0.4mg SL PRN. Allergies: Codeine (nausea and vomiting), Shellfish — iodine allergy "
            "(relevant for contrast procedures). "
            "Assessment: Post-STEMI with improving EF. Continue dual antiplatelet therapy. "
            "Cardiac rehab enrollment confirmed. LDL today 62 mg/dL — at target. "
            "Follow-up in 3 months or sooner if symptoms return. Repeat echo at 6 months."
        ),
    },
    {
        "patient_mrn": "MRN-10004",
        "source": "Clinic",
        "note_date": "2024-05-10",
        "provider": "Dr. Michael Kim",
        "text": (
            "6-month cardiology follow-up for post-STEMI patient James Rivera. He completed 12-week cardiac rehab program "
            "with excellent functional improvement. Reports significantly improved exercise tolerance — walking 1 mile daily. "
            "No angina, no dyspnea at rest. BP 118/76. HR 60 bpm. "
            "Echo: EF now 55%, fully recovered. LDL 58 mg/dL on high-intensity statin. "
            "Medications: Aspirin 81mg daily (lifelong), Clopidogrel 75mg daily (6 months remaining), "
            "Metoprolol succinate 50mg daily, Lisinopril 10mg daily (dose uptitrated), Atorvastatin 80mg nightly. "
            "Allergies: Codeine (nausea/vomiting), Shellfish/iodine contrast. "
            "Diagnoses: Post-STEMI with normalized EF, hypertension, dyslipidemia, coronary artery disease. "
            "Plan: Continue all medications. Can trial gradual Metoprolol reduction to 25mg at 12-month mark. "
            "Annual stress test. Follow-up in 6 months."
        ),
    },

    # ── Linda Kowalski (Migraine + Anxiety) ──────────────────────────────────
    {
        "patient_mrn": "MRN-10005",
        "source": "Telehealth",
        "note_date": "2024-01-22",
        "provider": "Dr. Rachel Green",
        "text": (
            "44-year-old female with chronic migraine disorder and generalized anxiety disorder (GAD). "
            "Telehealth visit for medication management. Reports 8-10 migraines per month, up from 4-5 previously. "
            "Identifies triggers: menstrual cycle, stress, screen time. Current prophylaxis with Propranolol 40mg BID "
            "providing partial relief. Acute treatments: Sumatriptan 50mg (effective but causes chest tightness), "
            "Ondansetron 4mg ODT for associated nausea. Anxiety managed with Sertraline 100mg daily and Lorazepam 0.5mg PRN. "
            "Allergies: Aspirin (migraines worsen — triggers headache), Codeine (allergic reaction — hives). "
            "Plan: Add Amitriptyline 10mg at bedtime as additional migraine prophylaxis and for anxiety. "
            "Consider CGRP antagonist (Rimegepant or Ubrogepant) as alternative acute therapy to Sumatriptan. "
            "Neurology referral. Follow up in 6 weeks or sooner."
        ),
    },
    {
        "patient_mrn": "MRN-10005",
        "source": "Clinic",
        "note_date": "2024-03-05",
        "provider": "Dr. Rachel Green",
        "text": (
            "6-week in-person follow-up for migraine and anxiety management. Patient reports migraine frequency "
            "reduced to 5-6 per month since adding Amitriptyline 10mg. Sleep improved. Anxiety better controlled. "
            "No suicidal ideation. PHQ-9 score 7 (mild depression). GAD-7 score 9 (mild anxiety). "
            "Medications: Propranolol 40mg BID, Amitriptyline 10mg QHS, Sertraline 100mg daily, "
            "Sumatriptan 50mg PRN (limiting to 2 uses/week), Ondansetron 4mg ODT PRN, Lorazepam 0.5mg PRN (using rarely). "
            "Allergies: Aspirin (migraine trigger), Codeine (hives). "
            "Assessment: Improved migraine prophylaxis, partial response. Anxiety stable. "
            "Uptitrate Amitriptyline to 25mg QHS. Neurology appointment scheduled for next month. "
            "Neurologist may discuss CGRP pathway options."
        ),
    },

    # ── David Pham (Young Adult — Asthma + GERD) ─────────────────────────────
    {
        "patient_mrn": "MRN-10006",
        "source": "Clinic",
        "note_date": "2024-01-30",
        "provider": "Dr. Omar Hassan",
        "text": (
            "34-year-old male with moderate persistent asthma and gastroesophageal reflux disease (GERD). "
            "Presents with worsening asthma symptoms over past 2 weeks — using rescue inhaler >2 times per week. "
            "Nighttime symptoms 3-4 times per week. GERD also poorly controlled with current therapy. "
            "Spirometry: FEV1 72% predicted. Physical exam: bilateral expiratory wheezing. "
            "Current medications: Fluticasone 110mcg inhaled BID, Albuterol MDI 90mcg PRN, "
            "Omeprazole 20mg once daily. "
            "Allergies: Naproxen (worsens asthma — NSAID-exacerbated respiratory disease), "
            "Latex (contact dermatitis). "
            "Assessment: Poorly controlled moderate persistent asthma. NSAID-exacerbated respiratory disease. Uncontrolled GERD. "
            "Plan: Step up asthma therapy — add Montelukast 10mg daily and long-acting beta agonist. "
            "Switch to Fluticasone/Salmeterol 115/21mcg 1 puff BID. Increase Omeprazole to 40mg daily. "
            "Asthma action plan provided. Follow up in 4 weeks."
        ),
    },
    {
        "patient_mrn": "MRN-10006",
        "source": "ER",
        "note_date": "2024-02-18",
        "provider": "Dr. Priya Sharma",
        "text": (
            "34-year-old male with known asthma presenting to ED with acute exacerbation. Triggered by cat exposure "
            "at a friend's house. Severe bronchospasm, SpO2 91% on arrival. Speaking in short sentences. "
            "Diagnosed with acute severe asthma exacerbation. "
            "Treatment: Albuterol 2.5mg nebulized Q20min x3, Ipratropium 500mcg nebulized x3, "
            "Methylprednisolone 125mg IV x1, Supplemental oxygen via face mask. "
            "SpO2 improved to 97% after treatment. No intubation required. "
            "Allergies: Naproxen (NSAID-exacerbated respiratory disease), Latex (contact dermatitis). "
            "Discharged with: Prednisone 40mg oral x5 days, continue Fluticasone/Salmeterol 115/21mcg BID, "
            "Montelukast 10mg daily, Albuterol MDI PRN. "
            "Follow up with primary care in 2-3 days. Allergy/immunology referral for allergen testing and "
            "possible immunotherapy. Patient advised to avoid cat allergen exposure."
        ),
    },
    {
        "patient_mrn": "MRN-10006",
        "source": "Clinic",
        "note_date": "2024-04-22",
        "provider": "Dr. Omar Hassan",
        "text": (
            "3-month follow-up for David's asthma and GERD. Great improvement since step-up therapy. "
            "Rescue inhaler use now <1 time/week. No nocturnal symptoms. GERD heartburn well controlled on Omeprazole 40mg. "
            "Completed allergy testing: significant sensitization to cat dander, dust mites, cockroach. "
            "Allergen immunotherapy (allergy shots) initiated 3 weeks ago at allergist. "
            "Spirometry: FEV1 88% predicted — significant improvement. "
            "Medications: Fluticasone/Salmeterol 115/21mcg 1 puff BID, Montelukast 10mg daily, "
            "Albuterol MDI 90mcg PRN, Omeprazole 40mg daily. "
            "Allergies: Naproxen (NSAID-exacerbated asthma), Latex (contact dermatitis). "
            "Assessment: Asthma well controlled, GERD controlled, allergen immunotherapy initiated. "
            "Continue current therapy. Follow up in 6 months. Pulmonary function test at next visit. "
            "Consider step-down therapy if asthma remains well controlled for 3 months."
        ),
    },

    # ── Mixed: Orthopedics, Neurology, Oncology ───────────────────────────────
    {
        "patient_mrn": "MRN-10004",
        "source": "Inpatient",
        "note_date": "2024-07-14",
        "provider": "Dr. Christine Park",
        "text": (
            "59-year-old male admitted for elective right total knee arthroplasty (TKA). "
            "History of severe osteoarthritis right knee, post-STEMI with normalized EF, HTN, dyslipidemia. "
            "Pre-op assessment: EF 55%, functional status good. Cardiology cleared for surgery. "
            "Procedure: R TKA performed under spinal anesthesia without complications. Blood loss ~200mL. "
            "Post-op day 1: Ambulating with physical therapy. Pain controlled. "
            "DVT prophylaxis: Enoxaparin 40mg subcutaneous daily x14 days. "
            "Pain management: Acetaminophen 1000mg Q8h, Oxycodone 5mg Q6h PRN breakthrough pain, "
            "Celecoxib 200mg daily (COX-2 selective — safe given iodine allergy, avoiding Ketorolac). "
            "Home medications resumed: Aspirin 81mg daily, Metoprolol 50mg daily, Lisinopril 10mg daily, Atorvastatin 80mg. "
            "Held Clopidogrel peri-operatively — restarted day 1 post-op. "
            "Allergies: Codeine (nausea/vomiting), Shellfish/iodine contrast. "
            "Discharge plan: Physical therapy TID, wound care, VTE prophylaxis. "
            "Follow up with orthopedics in 2 weeks."
        ),
    },
    {
        "patient_mrn": "MRN-10003",
        "source": "Clinic",
        "note_date": "2024-08-05",
        "provider": "Dr. Patricia Nguyen",
        "text": (
            "52-year-old female with RA presenting for routine follow-up. RA in sustained low disease activity. "
            "DAS28 score 2.3. No significant joint swelling or morning stiffness. Tolerating MTX well. "
            "Labs: CRP 0.4, LFTs normal, CBC: WBC 4.8, Hgb 12.6, platelets 245. "
            "Screening: DEXA scan ordered given long-term DMARD use and steroid exposure history — "
            "T-score hip -1.8, spine -2.1 (osteopenia). "
            "New diagnosis: Osteopenia. Starting calcium 600mg BID with Vitamin D 1000 IU daily. "
            "Medications: Methotrexate 20mg SQ weekly, Folic acid 1mg daily, Hydroxychloroquine 200mg BID, "
            "Calcium carbonate 600mg BID, Vitamin D 1000 IU daily. "
            "Allergies: Sulfa drugs (Stevens-Johnson syndrome — SEVERE), Ibuprofen (GI intolerance). "
            "Weight bearing exercise recommended. Rheumatology follow up in 6 months. "
            "Repeat DEXA in 2 years. Consider bisphosphonate therapy if T-score worsens."
        ),
    },
    {
        "patient_mrn": "MRN-10001",
        "source": "Clinic",
        "note_date": "2024-09-12",
        "provider": "Dr. Sarah Mitchell",
        "text": (
            "Annual visit for Margaret. 69-year-old female with T2DM, hypertension, hyperlipidemia. "
            "Feeling well overall. HbA1c 7.1% — excellent glycemic control maintained. "
            "BP 126/80 — at target. LDL 72 mg/dL. Renal function stable: GFR 72 mL/min, "
            "urine albumin/creatinine ratio 28 mg/g (microalbuminuria). "
            "Comprehensive foot exam: normal sensation with monofilament, intact peripheral pulses, no lesions. "
            "Ophthalmology: mild non-proliferative diabetic retinopathy — annual monitoring. "
            "Medications continued: Metformin 1000mg BID, Glipizide 5mg daily, Empagliflozin 10mg daily, "
            "Lisinopril 20mg daily (cardioprotective and renoprotective), Amlodipine 5mg daily, Atorvastatin 40mg QHS. "
            "Allergies: Sulfonamides (urticarial rash). "
            "Annual labs ordered: HbA1c, BMP, lipid panel, urine microalbumin, thyroid function. "
            "Influenza vaccine administered today. Shingrix series (second dose) recommended. "
            "Follow up in 6 months."
        ),
    },
    {
        "patient_mrn": "MRN-10005",
        "source": "Clinic",
        "note_date": "2024-10-08",
        "provider": "Dr. Rachel Green",
        "text": (
            "44-year-old female returns for migraine and mental health follow-up. Significant improvement — "
            "migraine frequency now 3-4 per month with Amitriptyline 25mg and Propranolol. "
            "Neurologist confirmed migraine diagnosis and added Topiramate 25mg daily (titrating to 50mg). "
            "Anxiety well controlled: GAD-7 score 5 (minimal). PHQ-9 score 4. Sleeping better. "
            "Discontinued Lorazepam — no longer needed. "
            "Current medications: Propranolol 40mg BID, Amitriptyline 25mg QHS, Topiramate 25mg BID (titrating), "
            "Sertraline 100mg daily, Sumatriptan 100mg PRN (max 2x/week), Ondansetron 4mg PRN nausea. "
            "Allergies: Aspirin (migraine trigger), Codeine (hives). "
            "Side effects noted: mild word-finding difficulty with Topiramate — will monitor. "
            "Counseling referral for CBT for anxiety — appointment scheduled. "
            "Follow up in 2 months. Repeat neuropsychological assessment at next visit."
        ),
    },
    {
        "patient_mrn": "MRN-10002",
        "source": "Clinic",
        "note_date": "2024-10-20",
        "provider": "Dr. Angela Torres",
        "text": (
            "76-year-old male with COPD GOLD III and CHF with reduced EF (last EF 40%) for routine pulmonology visit. "
            "Stable at home on 2L home oxygen. 6-minute walk test: 280 meters (limited by dyspnea). "
            "No recent hospitalizations since February. Weight stable. "
            "Spirometry: FEV1 42% predicted, FEV1/FVC 0.58 — consistent with GOLD III COPD. "
            "Echocardiogram last month: EF 42%, mild mitral regurgitation, elevated filling pressures. "
            "Medications: Tiotropium 18mcg inhaled daily, Fluticasone/Salmeterol 250/50mcg BID, "
            "Albuterol MDI PRN, Furosemide 40mg oral daily, Spironolactone 25mg daily, "
            "Carvedilol 12.5mg BID (dose increased), Sacubitril/Valsartan 24/26mg BID (added for CHF). "
            "Allergies: Aspirin (bronchospasm), Penicillin (anaphylaxis). "
            "Plan: Pulmonary rehab maintenance. Pneumococcal vaccine (PPSV23) given today. "
            "Continue home oxygen. Advance care planning discussion initiated. "
            "Cardiology follow-up in 3 months for CHF management. Pulmonology in 4 months."
        ),
    },
]


def main():
    print("🏥 MedScribe Seed Script")
    print("=" * 50)

    # Check API connectivity
    print(f"\n🔍 Checking API connectivity at {API_URL}...")
    retries = 0
    while not check_api():
        if retries >= 5:
            print("❌ Cannot connect to API. Start the backend first:\n   uvicorn app.main:app --reload")
            sys.exit(1)
        print(f"   Waiting for API... ({retries + 1}/5)")
        time.sleep(3)
        retries += 1
    print("✅ API is up!\n")

    # Create patients
    print("👥 Creating patients...")
    patient_id_map = {}
    for p in PATIENTS:
        pid = create_patient(p["name"], p.get("dob"), p["gender"], p["mrn"])
        if pid:
            patient_id_map[p["mrn"]] = pid
            print(f"   ✅ {p['name']} (ID: {pid})")
        else:
            print(f"   ❌ Failed: {p['name']}")

    # Create notes
    print(f"\n📋 Creating {len(CLINICAL_NOTES)} clinical notes...")
    notes_created = 0
    for i, note_data in enumerate(CLINICAL_NOTES, 1):
        mrn = note_data["patient_mrn"]
        pid = patient_id_map.get(mrn)
        if not pid:
            print(f"   ⚠️  Note {i}: Patient MRN {mrn} not found, skipping")
            continue

        nid = create_note(
            patient_id=pid,
            text=note_data["text"],
            source=note_data["source"],
            note_date=note_data["note_date"],
            provider=note_data["provider"],
        )
        if nid:
            print(f"   ✅ Note #{nid}: {note_data['source']} — {note_data['note_date']} (Patient: {mrn})")
            notes_created += 1
        else:
            print(f"   ❌ Failed to create note {i}")
        time.sleep(0.25)

    print(f"\n🎉 Seed complete!")
    print(f"   👥 Patients: {len(patient_id_map)}")
    print(f"   📋 Notes: {notes_created}")
    print(f"\n⏳ LLM extraction running in background for all notes...")
    print(f"   📡 API Docs: {API_URL}/docs")
    print(f"   📊 Dashboard: http://localhost:8501")
    print("\n✅ Done! Check the dashboard to see extracted entities.")


if __name__ == "__main__":
    main()
