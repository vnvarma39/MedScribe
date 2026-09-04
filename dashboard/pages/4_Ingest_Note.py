"""
MedScribe — Page 4: Ingest Note
Submit a new clinical note for AI entity extraction
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
import streamlit as st
from components.utils import api_get, api_post, inject_custom_css, status_badge

st.set_page_config(
    page_title="Ingest Note — MedScribe",
    page_icon="⚡",
    layout="wide",
)

inject_custom_css()

st.markdown("# ⚡ Ingest Clinical Note")
st.markdown("<p style='color:#94a3b8;'>Submit a new clinical note. The AI pipeline will automatically extract diagnoses, medications, allergies, and follow-ups.</p>", unsafe_allow_html=True)
st.divider()

col_form, col_tip = st.columns([3, 1])

with col_tip:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0c1a2e,#0f172a);border:1px solid #1e40af;
                border-radius:12px;padding:20px;margin-bottom:16px;">
        <div style="font-weight:700;color:#93c5fd;margin-bottom:10px;">💡 Tips</div>
        <ul style="color:#94a3b8;font-size:0.85rem;padding-left:16px;line-height:1.8;">
            <li>Include patient vitals and chief complaint</li>
            <li>List medications with dosage and frequency</li>
            <li>Mention known allergies explicitly</li>
            <li>State follow-up plans clearly</li>
            <li>Minimum 10 characters required</li>
        </ul>
    </div>

    <div style="background:linear-gradient(135deg,#0a1f1a,#0f172a);border:1px solid #065f46;
                border-radius:12px;padding:20px;">
        <div style="font-weight:700;color:#6ee7b7;margin-bottom:10px;">📡 Extraction Pipeline</div>
        <div style="color:#94a3b8;font-size:0.82rem;line-height:1.8;">
            1. Note saved to SQLite DB<br>
            2. Background job triggered<br>
            3. LLM (OpenRouter / Groq / Ollama) extracts entities<br>
            4. Results persisted to DB<br>
            5. View in Entity Viewer ✓
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_form:
    # ── Patient Selection ─────────────────────────────────────────────────────
    st.markdown("### 1️⃣ Select or Create Patient")

    mode = st.radio("Patient", ["Select existing", "Create new"], horizontal=True, label_visibility="collapsed")

    patient_id = None

    if mode == "Select existing":
        patients_data = api_get("/api/v1/patients/", params={"per_page": 100})
        patients = patients_data.get("items", []) if patients_data else []
        if not patients:
            st.warning("No patients found. Switch to 'Create new' to add one.")
        else:
            patient_map = {f"{p['name']} (ID:{p['id']})": p["id"] for p in patients}
            selected = st.selectbox("Select patient", list(patient_map.keys()))
            patient_id = patient_map[selected]
    else:
        with st.form("new_patient_form"):
            st.markdown("**New Patient Details**")
            pc1, pc2 = st.columns(2)
            with pc1:
                new_name = st.text_input("Full Name *", placeholder="Jane Doe")
                new_gender = st.selectbox("Gender", ["", "Male", "Female", "Other", "Unknown"])
            with pc2:
                new_dob = st.date_input("Date of Birth", value=None, min_value=date(1900, 1, 1))
                new_mrn = st.text_input("MRN (optional)", placeholder="MRN-12345")

            if st.form_submit_button("➕ Create Patient", type="primary"):
                if not new_name:
                    st.error("Name is required.")
                else:
                    payload = {"name": new_name}
                    if new_gender:
                        payload["gender"] = new_gender
                    if new_dob:
                        payload["dob"] = new_dob.isoformat()
                    if new_mrn:
                        payload["mrn"] = new_mrn

                    result = api_post("/api/v1/patients/", payload)
                    if result:
                        st.success(f"✅ Patient created: **{result['name']}** (ID: {result['id']})")
                        st.session_state["new_patient_id"] = result["id"]
                        st.session_state["new_patient_name"] = result["name"]

        if "new_patient_id" in st.session_state:
            patient_id = st.session_state["new_patient_id"]
            st.info(f"Patient: **{st.session_state['new_patient_name']}** selected")

    st.divider()

    # ── Note Form ─────────────────────────────────────────────────────────────
    st.markdown("### 2️⃣ Clinical Note Details")

    with st.form("note_form"):
        note_text = st.text_area(
            "Clinical Note Text *",
            height=250,
            placeholder=(
                "Example:\n"
                "Patient is a 65-year-old female with Type 2 Diabetes Mellitus presenting with "
                "complaints of fatigue and blurred vision for 3 weeks. BP 148/92. "
                "Current medications: Metformin 1000mg twice daily, Atorvastatin 40mg at bedtime. "
                "Allergic to Sulfonamides (rash). "
                "Plan: HbA1c, ophthalmology referral, follow-up in 3 weeks."
            ),
        )

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            source = st.selectbox(
                "Source",
                ["", "Clinic", "ER", "ICU", "Inpatient", "Discharge", "Telehealth", "Urgent Care", "Other"],
            )
        with fc2:
            note_date = st.date_input("Note Date", value=date.today())
        with fc3:
            provider = st.text_input("Provider", placeholder="Dr. Smith")

        submitted = st.form_submit_button("🚀 Submit & Extract", type="primary", use_container_width=True)

        if submitted:
            if not patient_id:
                st.error("Please select or create a patient first.")
            elif not note_text or len(note_text.strip()) < 10:
                st.error("Clinical note must be at least 10 characters.")
            else:
                payload = {
                    "patient_id": patient_id,
                    "raw_text": note_text.strip(),
                }
                if source:
                    payload["source"] = source
                if note_date:
                    payload["note_date"] = note_date.isoformat()
                if provider:
                    payload["provider"] = provider

                with st.spinner("Submitting note and triggering extraction…"):
                    result = api_post("/api/v1/notes/", payload)

                if result:
                    note_id = result["id"]
                    st.success(f"✅ Note #{note_id} ingested! Extraction pipeline started in background.")
                    st.markdown(f"""
                    <div style="background:#052e16;border:1px solid #16a34a;border-radius:12px;padding:20px;margin-top:12px;">
                        <div style="font-size:1rem;font-weight:600;color:#4ade80;">📋 Note #{note_id} Created</div>
                        <div style="color:#86efac;font-size:0.85rem;margin-top:8px;">
                            ✅ Saved to database &nbsp;|&nbsp;
                            ⏳ LLM extraction queued &nbsp;|&nbsp;
                            🔗 View in Entity Viewer
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("🧬 View Extracted Entities →"):
                        st.session_state["entity_viewer_note_id"] = note_id
                        st.switch_page("pages/2_Entity_Viewer.py")

# ── Sample Notes ──────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 📋 Sample Clinical Notes (click to copy)")

SAMPLES = [
    ("🫀 Cardiology", "Patient is a 72-year-old male presenting with exertional chest pain and shortness of breath. EKG shows ST depression in V4-V6. History of hypertension and hyperlipidemia. Medications: Aspirin 81mg daily, Metoprolol succinate 50mg daily, Atorvastatin 40mg nightly, Nitroglycerin PRN. Allergic to Ibuprofen (GI upset). Plan: Admit for cardiac workup, troponin x3, cardiology consult. Follow up with cardiologist in 1 week."),
    ("🫁 Pulmonology", "55-year-old female with history of COPD presents with worsening dyspnea and productive cough for 5 days. Oxygen saturation 92% on room air. Respiratory rate 22. Diagnosed with COPD exacerbation and community-acquired pneumonia. Medications: Tiotropium 18mcg inhaled daily, Albuterol 2.5mg nebulized Q4h, Prednisone 40mg oral daily x5 days, Azithromycin 500mg oral daily x5 days. Allergy to Penicillin (anaphylaxis). Follow up in pulmonary clinic in 2 weeks."),
    ("🩺 Endocrinology", "68-year-old female with poorly controlled Type 2 Diabetes Mellitus. HbA1c 9.8%. BMI 34. Complains of polydipsia and polyuria. Medications: Metformin 1000mg BID, Glipizide 10mg daily, Lisinopril 10mg daily for microalbuminuria. Allergic to Contrast dye (urticaria). Plan: Add insulin glargine 10 units at bedtime, diabetes education referral, ophthalmology and podiatry referrals. Recheck HbA1c in 3 months."),
]

for title, text in SAMPLES:
    with st.expander(title):
        st.code(text, language=None)
