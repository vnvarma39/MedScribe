"""
MedScribe — Page 2: Entity Viewer
View extracted medical entities and AI summary for a clinical note
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from components.utils import (
    api_get, api_post, inject_custom_css,
    severity_badge, priority_badge, status_badge,
)

st.set_page_config(
    page_title="Entity Viewer — MedScribe",
    page_icon="🧬",
    layout="wide",
)

inject_custom_css()

st.markdown("# 🧬 Entity Viewer")
st.markdown("<p style='color:#94a3b8;'>Explore AI-extracted clinical entities for any note, and generate a narrative summary.</p>", unsafe_allow_html=True)
st.divider()

# ── Patient → Note selector ───────────────────────────────────────────────────
patients_data = api_get("/api/v1/patients/", params={"per_page": 100})
if not patients_data or not patients_data.get("items"):
    st.warning("No patients found. Please ingest some clinical notes first.")
    st.stop()

patients = patients_data["items"]
patient_map = {f"{p['name']} (ID:{p['id']})": p["id"] for p in patients}

col_p, col_n = st.columns(2)
with col_p:
    selected_patient_label = st.selectbox("👤 Select Patient", list(patient_map.keys()))
    selected_patient_id = patient_map[selected_patient_label]

# Fetch notes for selected patient
notes_data = api_get(f"/api/v1/patients/{selected_patient_id}/notes", params={"per_page": 100})
notes = notes_data.get("items", []) if notes_data else []

if not notes:
    with col_n:
        st.warning("No notes for this patient.")
    st.stop()

note_map = {
    f"Note #{n['id']} — {n.get('source', 'Unknown')} — {n.get('note_date', '—')}": n["id"]
    for n in notes
}

# Pre-select if coming from Patient Records page
preselected_note_id = st.session_state.get("entity_viewer_note_id")
preselected_label = next(
    (k for k, v in note_map.items() if v == preselected_note_id), list(note_map.keys())[0]
)

with col_n:
    selected_note_label = st.selectbox("📝 Select Note", list(note_map.keys()), index=list(note_map.keys()).index(preselected_label))
    selected_note_id = note_map[selected_note_label]

st.divider()

# ── Fetch full note detail ────────────────────────────────────────────────────
note = api_get(f"/api/v1/notes/{selected_note_id}")
if not note:
    st.stop()

# ── Note Header ───────────────────────────────────────────────────────────────
header_cols = st.columns([3, 1, 1, 1])
with header_cols[0]:
    st.markdown(f"#### 📋 Note #{note['id']} &nbsp; | &nbsp; {note.get('source', 'Unknown')} &nbsp; | &nbsp; {note.get('note_date', '—')}")
with header_cols[1]:
    st.markdown(f"**Status:** {status_badge(note.get('extraction_status'))}", unsafe_allow_html=True)
with header_cols[2]:
    if note.get("provider"):
        st.markdown(f"**Provider:** {note['provider']}")
with header_cols[3]:
    total_entities = (
        len(note.get("diagnoses", [])) +
        len(note.get("medications", [])) +
        len(note.get("allergies", [])) +
        len(note.get("follow_ups", []))
    )
    st.markdown(f"**Entities:** {total_entities}")

# ── Raw Note Text ─────────────────────────────────────────────────────────────
with st.expander("📄 Raw Clinical Note Text", expanded=False):
    st.markdown(f"""
    <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:16px;
                color:#cbd5e1;font-family:monospace;font-size:0.88rem;white-space:pre-wrap;line-height:1.6;">
    {note['raw_text']}
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Entity Tabs ───────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"🏥 Diagnoses ({len(note.get('diagnoses', []))})",
    f"💊 Medications ({len(note.get('medications', []))})",
    f"⚠️ Allergies ({len(note.get('allergies', []))})",
    f"📅 Follow-ups ({len(note.get('follow_ups', []))})",
    "🤖 AI Summary",
])

# ── Tab 1: Diagnoses ──────────────────────────────────────────────────────────
with tab1:
    diagnoses = note.get("diagnoses", [])
    if not diagnoses:
        st.info("No diagnoses extracted from this note.")
    else:
        for d in diagnoses:
            st.markdown(f"""
            <div class="entity-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;color:#f1f5f9;font-size:1rem;">🏥 {d['description']}</span>
                        {"<span style='color:#64748b;font-size:0.8rem;margin-left:10px;'>ICD: " + d['code'] + "</span>" if d.get('code') else ""}
                    </div>
                    {severity_badge(d.get('severity'))}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Tab 2: Medications ────────────────────────────────────────────────────────
with tab2:
    medications = note.get("medications", [])
    if not medications:
        st.info("No medications extracted from this note.")
    else:
        for m in medications:
            cols = st.columns([3, 1, 1, 1])
            with cols[0]:
                st.markdown(f"""
                <div class="entity-card">
                    <div style="font-weight:600;color:#f1f5f9;font-size:1rem;">💊 {m['name']}</div>
                    <div style="color:#94a3b8;font-size:0.85rem;margin-top:6px;">
                        {"📏 " + m['dosage'] + "&nbsp;&nbsp;" if m.get('dosage') else ""}
                        {"🕐 " + m['frequency'] + "&nbsp;&nbsp;" if m.get('frequency') else ""}
                        {"🔬 " + m['route'] if m.get('route') else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ── Tab 3: Allergies ──────────────────────────────────────────────────────────
with tab3:
    allergies = note.get("allergies", [])
    if not allergies:
        st.info("No allergies extracted from this note.")
    else:
        for a in allergies:
            st.markdown(f"""
            <div class="entity-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;color:#f1f5f9;font-size:1rem;">⚠️ {a['allergen']}</span>
                        {"<span style='color:#94a3b8;font-size:0.85rem;margin-left:12px;'>→ " + a['reaction'] + "</span>" if a.get('reaction') else ""}
                    </div>
                    {severity_badge(a.get('severity'))}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Tab 4: Follow-ups ─────────────────────────────────────────────────────────
with tab4:
    follow_ups = note.get("follow_ups", [])
    if not follow_ups:
        st.info("No follow-up tasks extracted from this note.")
    else:
        for f in follow_ups:
            st.markdown(f"""
            <div class="entity-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;color:#f1f5f9;font-size:1rem;">📅 {f['task']}</span>
                        {"<span style='color:#94a3b8;font-size:0.85rem;margin-left:12px;'>📆 " + f['due_date'] + "</span>" if f.get('due_date') else ""}
                    </div>
                    {priority_badge(f.get('priority'))}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Tab 5: AI Summary ─────────────────────────────────────────────────────────
with tab5:
    st.markdown("Generate a professional clinical summary using the same LLM that performed entity extraction.")

    if st.button("🤖 Generate Clinical Summary", use_container_width=False, type="primary"):
        with st.spinner("Generating AI clinical summary…"):
            summary_data = api_get(f"/api/v1/notes/{selected_note_id}/summary")

        if summary_data:
            st.success("Summary generated!")
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0c1445,#0f172a);
                        border:1px solid #3b82f6;border-radius:12px;padding:24px;
                        margin-top:16px;">
                <div style="color:#93c5fd;font-size:0.75rem;font-weight:600;margin-bottom:12px;">
                    🤖 {summary_data.get('model_used', 'LLM')} &nbsp;|&nbsp; {summary_data.get('generated_at', '')}
                </div>
                <div style="color:#e2e8f0;font-size:1rem;line-height:1.8;">{summary_data['summary']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#1e293b;border:1px dashed #475569;border-radius:12px;padding:32px;text-align:center;">
            <div style="font-size:2rem;">🤖</div>
            <div style="color:#94a3b8;margin-top:8px;">Click the button above to generate an AI clinical summary</div>
        </div>
        """, unsafe_allow_html=True)

# ── Extraction Job History ────────────────────────────────────────────────────
with st.expander("⚙️ Extraction Job History", expanded=False):
    jobs = note.get("extraction_jobs", [])
    if not jobs:
        st.info("No extraction jobs recorded.")
    else:
        for job in sorted(jobs, key=lambda j: j["created_at"], reverse=True):
            status_html = status_badge(job["status"])
            duration = f"{job['duration_ms']} ms" if job.get("duration_ms") else "—"
            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-bottom:8px;
                        display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#94a3b8;font-size:0.85rem;">Job #{job['id']} &nbsp;|&nbsp; {job.get('model_used','—')}</span>
                <span style="color:#94a3b8;font-size:0.85rem;">{duration}</span>
                {status_html}
            </div>
            {"<div style='color:#ef4444;font-size:0.8rem;padding:4px 12px;'>" + job['error_message'] + "</div>" if job.get('error_message') else ""}
            """, unsafe_allow_html=True)
