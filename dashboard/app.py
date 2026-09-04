"""
MedScribe — Streamlit Dashboard Home
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.utils import api_get, inject_custom_css, status_badge

st.set_page_config(
    page_title="MedScribe — Clinical Notes AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()

# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 40px 0 20px 0;">
    <div style="font-size: 3.5rem;">🏥</div>
    <h1 style="font-size: 2.8rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa, #a78bfa, #34d399);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 10px 0;">
        MedScribe
    </h1>
    <p style="color: #94a3b8; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
        AI-powered clinical notes processing — Extract diagnoses, medications, allergies,
        and follow-ups from unstructured clinical text in seconds.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Live Stats ────────────────────────────────────────────────────────────────
stats = api_get("/api/v1/stats/")

if stats:
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("👥 Patients", stats["total_patients"])
    with col2:
        st.metric("📋 Notes", stats["total_notes"])
    with col3:
        st.metric("🧬 Diagnoses", stats["total_diagnoses"])
    with col4:
        st.metric("💊 Medications", stats["total_medications"])
    with col5:
        st.metric("⚠️ Allergies", stats["total_allergies"])
    with col6:
        st.metric("📅 Follow-ups", stats["total_follow_ups"])

    st.divider()

    # Extraction Status
    ext = stats.get("extraction", {})
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style="background:#052e16;border:1px solid #16a34a;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:1.8rem;font-weight:700;color:#4ade80;">{ext.get('completed', 0)}</div>
            <div style="color:#86efac;font-size:0.85rem;">✅ Extractions Completed</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background:#1c1917;border:1px solid #b45309;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:1.8rem;font-weight:700;color:#fbbf24;">{ext.get('pending', 0)}</div>
            <div style="color:#fcd34d;font-size:0.85rem;">⏳ Extractions Pending</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        avg_ms = ext.get('avg_duration_ms', 0)
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #3b82f6;border-radius:12px;padding:16px;text-align:center;">
            <div style="font-size:1.8rem;font-weight:700;color:#60a5fa;">{avg_ms:.0f}ms</div>
            <div style="color:#93c5fd;font-size:0.85rem;">⚡ Avg Extraction Time</div>
        </div>""", unsafe_allow_html=True)

    if stats["total_patients"] == 0:
        st.info("💡 The database is currently empty. You can run the seed script to load 6 realistic patients and 20 clinical notes, or ingest notes via the **Ingest Note** page.")
        if st.button("🌱 Populate 20 Sample Clinical Notes Now", type="primary"):
            import subprocess
            with st.spinner("Seeding database with clinical notes..."):
                try:
                    subprocess.run([sys.executable, "../data/seed.py"], check=False)
                    st.success("Seed script executed! Refreshing...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error running seed script: {e}")

else:
    st.warning("⚠️ Could not connect to the MedScribe API. Make sure the backend is running.")
    st.code("cd backend && uvicorn app.main:app --reload", language="bash")

st.divider()

# ── Navigation Cards ──────────────────────────────────────────────────────────
st.markdown("### 🧭 Navigate")
n1, n2, n3, n4 = st.columns(4)

with n1:
    st.markdown("""
    <div class="entity-card" style="text-align:center;">
        <div style="font-size:2rem;">📋</div>
        <h3 style="color:#60a5fa!important;">Patient Records</h3>
        <p style="color:#94a3b8;font-size:0.85rem;">Browse patients and their full note timeline</p>
    </div>""", unsafe_allow_html=True)

with n2:
    st.markdown("""
    <div class="entity-card" style="text-align:center;">
        <div style="font-size:2rem;">🧬</div>
        <h3 style="color:#a78bfa!important;">Entity Viewer</h3>
        <p style="color:#94a3b8;font-size:0.85rem;">Explore extracted diagnoses, meds, allergies</p>
    </div>""", unsafe_allow_html=True)

with n3:
    st.markdown("""
    <div class="entity-card" style="text-align:center;">
        <div style="font-size:2rem;">📊</div>
        <h3 style="color:#34d399!important;">Analytics</h3>
        <p style="color:#94a3b8;font-size:0.85rem;">Insights across your entire patient population</p>
    </div>""", unsafe_allow_html=True)

with n4:
    st.markdown("""
    <div class="entity-card" style="text-align:center;">
        <div style="font-size:2rem;">⚡</div>
        <h3 style="color:#fbbf24!important;">Ingest Note</h3>
        <p style="color:#94a3b8;font-size:0.85rem;">Submit a new clinical note for AI extraction</p>
    </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;color:#475569;font-size:0.8rem;padding:10px 0;">
    MedScribe v1.0.0 &nbsp;|&nbsp; Multi-Provider AI (OpenRouter / Groq / Ollama) &nbsp;|&nbsp;
    <a href="http://localhost:8000/docs" target="_blank" style="color:#60a5fa;">API Docs (Swagger)</a>
</div>""", unsafe_allow_html=True)
