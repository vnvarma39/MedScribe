"""
MedScribe — Page 3: Analytics Dashboard
Charts and insights across the full patient population
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from components.utils import api_get, inject_custom_css

st.set_page_config(
    page_title="Analytics — MedScribe",
    page_icon="📊",
    layout="wide",
)

inject_custom_css()

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0f172a",
    font=dict(family="Inter", color="#94a3b8"),
    xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
)

st.markdown("# 📊 Analytics")
st.markdown("<p style='color:#94a3b8;'>Population-level insights from extracted clinical entities across all notes.</p>", unsafe_allow_html=True)
st.divider()

# ── Fetch stats ───────────────────────────────────────────────────────────────
stats = api_get("/api/v1/stats/")
if not stats:
    st.stop()

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
kpis = [
    (k1, "👥", "Patients", stats["total_patients"]),
    (k2, "📋", "Notes", stats["total_notes"]),
    (k3, "🏥", "Diagnoses", stats["total_diagnoses"]),
    (k4, "💊", "Medications", stats["total_medications"]),
    (k5, "⚠️", "Allergies", stats["total_allergies"]),
    (k6, "📅", "Follow-ups", stats["total_follow_ups"]),
]
for col, icon, label, val in kpis:
    with col:
        st.metric(f"{icon} {label}", val)

st.divider()

# ── Row 1: Top Diagnoses + Top Medications ────────────────────────────────────
col_diag, col_med = st.columns(2)

with col_diag:
    st.markdown("#### 🏥 Top Diagnoses")
    diag_data = stats.get("top_diagnoses", [])
    if diag_data:
        df_diag = pd.DataFrame(diag_data)
        fig = px.bar(
            df_diag,
            x="count",
            y="name",
            orientation="h",
            color="count",
            color_continuous_scale=["#1e3a5f", "#3b82f6", "#60a5fa"],
            labels={"name": "", "count": "Occurrences"},
        )
        fig.update_layout(**PLOTLY_THEME, coloraxis_showscale=False, height=350, margin=dict(l=0, r=20, t=20, b=20))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No diagnosis data yet.")

with col_med:
    st.markdown("#### 💊 Top Medications")
    med_data = stats.get("top_medications", [])
    if med_data:
        df_med = pd.DataFrame(med_data)
        fig = px.bar(
            df_med,
            x="count",
            y="name",
            orientation="h",
            color="count",
            color_continuous_scale=["#1a3a2f", "#10b981", "#34d399"],
            labels={"name": "", "count": "Occurrences"},
        )
        fig.update_layout(**PLOTLY_THEME, coloraxis_showscale=False, height=350, margin=dict(l=0, r=20, t=20, b=20))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No medication data yet.")

st.divider()

# ── Row 2: Top Allergens + Notes by Source ────────────────────────────────────
col_allergy, col_source = st.columns(2)

with col_allergy:
    st.markdown("#### ⚠️ Top Allergens")
    allergy_data = stats.get("top_allergens", [])
    if allergy_data:
        df_allergy = pd.DataFrame(allergy_data)
        fig = px.bar(
            df_allergy,
            x="count",
            y="name",
            orientation="h",
            color="count",
            color_continuous_scale=["#3b0000", "#dc2626", "#f87171"],
            labels={"name": "", "count": "Occurrences"},
        )
        fig.update_layout(**PLOTLY_THEME, coloraxis_showscale=False, height=320, margin=dict(l=0, r=20, t=20, b=20))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No allergy data yet.")

with col_source:
    st.markdown("#### 🏥 Notes by Source")
    source_data = stats.get("notes_by_source", {})
    if source_data:
        df_source = pd.DataFrame(
            [{"source": k, "count": v} for k, v in source_data.items()]
        )
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"]
        fig = go.Figure(data=[go.Pie(
            labels=df_source["source"],
            values=df_source["count"],
            hole=0.55,
            marker=dict(colors=colors[:len(df_source)], line=dict(color="#0f172a", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#e2e8f0"),
        )])
        fig.update_layout(
            **PLOTLY_THEME,
            height=320,
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=0),
            annotations=[dict(text=f"<b>{sum(source_data.values())}</b><br>Notes", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#f1f5f9"))],
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No source data yet.")

st.divider()

# ── Row 3: Extraction Stats ───────────────────────────────────────────────────
st.markdown("#### ⚙️ Extraction Pipeline Health")
ext = stats.get("extraction", {})

e1, e2, e3, e4 = st.columns(4)
with e1:
    st.metric("Total Jobs", ext.get("total_jobs", 0))
with e2:
    completed = ext.get("completed", 0)
    total_jobs = ext.get("total_jobs", 1) or 1
    pct = round(completed / total_jobs * 100, 1)
    st.metric("✅ Completed", completed, delta=f"{pct}% success rate")
with e3:
    st.metric("❌ Failed", ext.get("failed", 0))
with e4:
    avg = ext.get("avg_duration_ms", 0)
    st.metric("⚡ Avg Latency", f"{avg:.0f} ms")

# ── Extraction donut ──────────────────────────────────────────────────────────
ext_fig = go.Figure(data=[go.Pie(
    labels=["Completed", "Failed", "Pending"],
    values=[ext.get("completed", 0), ext.get("failed", 0), ext.get("pending", 0)],
    hole=0.6,
    marker=dict(colors=["#4ade80", "#ef4444", "#facc15"], line=dict(color="#0f172a", width=2)),
    textinfo="label+value",
    textfont=dict(color="#e2e8f0"),
)])
ext_fig.update_layout(
    **PLOTLY_THEME, height=280, showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
    annotations=[dict(text="<b>Jobs</b>", x=0.5, y=0.5, showarrow=False, font=dict(size=13, color="#f1f5f9"))],
)
st.plotly_chart(ext_fig, use_container_width=True)
