"""
MedScribe — Page 1: Patient Records
Browse patients with search, view note timelines
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from components.utils import api_get, api_delete, inject_custom_css, status_badge

st.set_page_config(
    page_title="Patient Records — MedScribe",
    page_icon="📋",
    layout="wide",
)

inject_custom_css()

st.markdown("# 📋 Patient Records")
st.markdown("<p style='color:#94a3b8;'>Search, browse, and manage patient records and their clinical note timeline.</p>", unsafe_allow_html=True)
st.divider()

# ── Search & Filter ───────────────────────────────────────────────────────────
col_search, col_page, col_perpage = st.columns([4, 1, 1])
with col_search:
    search = st.text_input("🔍 Search patients", placeholder="Name or MRN…", label_visibility="collapsed")
with col_page:
    page = st.number_input("Page", min_value=1, value=1, step=1, label_visibility="collapsed")
with col_perpage:
    per_page = st.selectbox("Per page", [10, 20, 50], index=1, label_visibility="collapsed")

# ── Fetch Patients ────────────────────────────────────────────────────────────
params = {"page": page, "per_page": per_page}
if search:
    params["search"] = search

data = api_get("/api/v1/patients/", params=params)

if not data:
    st.stop()

patients = data.get("items", [])
total = data.get("total", 0)

if total == 0:
    st.info("No patients found. Use **⚡ Ingest Note** to add your first patient and note.")
    st.stop()

# ── Patient Count ─────────────────────────────────────────────────────────────
st.markdown(
    f"<p style='color:#94a3b8;margin-bottom:16px;'>Showing <b style='color:#f1f5f9;'>{len(patients)}</b> of <b style='color:#f1f5f9;'>{total}</b> patients</p>",
    unsafe_allow_html=True,
)

# ── Patient Grid ──────────────────────────────────────────────────────────────
selected_patient_id = st.session_state.get("selected_patient_id")

for patient in patients:
    pid = patient["id"]
    name = patient["name"]
    gender = patient.get("gender") or "—"
    dob = patient.get("dob") or "—"
    mrn = patient.get("mrn") or "—"
    note_count = patient.get("note_count", 0)

    is_selected = (pid == selected_patient_id)
    border_color = "#3b82f6" if is_selected else "#334155"

    with st.container():
        st.markdown(f"""
        <div class="entity-card" style="border-color:{border_color};">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="font-size:1.1rem;font-weight:700;color:#f1f5f9;">👤 {name}</span>
                    <span style="color:#64748b;font-size:0.85rem;margin-left:12px;">ID: {pid} &nbsp;|&nbsp; MRN: {mrn}</span>
                </div>
                <div style="color:#94a3b8;font-size:0.85rem;">
                    🚻 {gender} &nbsp;|&nbsp; 🎂 {dob} &nbsp;|&nbsp; 📄 {note_count} note{'s' if note_count != 1 else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        btn_col1, btn_col2, _ = st.columns([1, 1, 8])
        with btn_col1:
            if st.button(
                "📄 View Notes" if not is_selected else "🔼 Collapse",
                key=f"view_patient_{pid}",
                use_container_width=True,
            ):
                if is_selected:
                    st.session_state["selected_patient_id"] = None
                else:
                    st.session_state["selected_patient_id"] = pid
                st.rerun()

# ── Note Timeline ─────────────────────────────────────────────────────────────
if selected_patient_id:
    st.divider()
    patient_data = next((p for p in patients if p["id"] == selected_patient_id), None)
    if patient_data:
        st.markdown(f"### 📄 Notes for **{patient_data['name']}**")

    notes_data = api_get(f"/api/v1/patients/{selected_patient_id}/notes", params={"per_page": 50})
    if notes_data:
        notes = notes_data.get("items", [])
        if not notes:
            st.info("No notes found for this patient.")
        else:
            for note in notes:
                note_id = note["id"]
                source = note.get("source") or "Unknown"
                note_date = note.get("note_date") or "—"
                provider = note.get("provider") or "Unknown"
                ext_status = note.get("extraction_status") or "unknown"
                preview = note["raw_text"][:200] + ("…" if len(note["raw_text"]) > 200 else "")

                st.markdown(f"""
                <div class="entity-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <span style="font-weight:600;color:#e2e8f0;">📝 Note #{note_id} &nbsp; | &nbsp; 🏥 {source} &nbsp; | &nbsp; 📅 {note_date}</span>
                        {status_badge(ext_status)}
                    </div>
                    <div style="color:#94a3b8;font-size:0.8rem;margin-bottom:6px;">👨‍⚕️ {provider}</div>
                    <div style="color:#cbd5e1;font-size:0.88rem;font-style:italic;border-left:3px solid #334155;padding-left:12px;">"{preview}"</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🧬 View Entities → Note #{note_id}", key=f"goto_entity_{note_id}"):
                    st.session_state["entity_viewer_note_id"] = note_id
                    st.switch_page("pages/2_Entity_Viewer.py")
