"""
MedScribe Dashboard — Shared Utilities
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")


# ─────────────────────────────────────────────────────────────────────────────
# API Client
# ─────────────────────────────────────────────────────────────────────────────
def api_get(path: str, params: Optional[Dict] = None, timeout: int = 15) -> Optional[Any]:
    """GET from API, returns parsed JSON or None on error."""
    try:
        resp = requests.get(f"{API_URL}{path}", params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to MedScribe API. Is the backend running?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def api_post(path: str, payload: Dict, timeout: int = 30) -> Optional[Any]:
    """POST to API, returns parsed JSON or None on error."""
    try:
        resp = requests.post(
            f"{API_URL}{path}",
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to MedScribe API. Is the backend running?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error {e.response.status_code}: {e.response.json().get('detail', e.response.text)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def api_delete(path: str, timeout: int = 10) -> bool:
    """DELETE via API, returns True on success."""
    try:
        resp = requests.delete(f"{API_URL}{path}", timeout=timeout)
        return resp.status_code == 204
    except Exception as e:
        st.error(f"Delete failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# UI Helpers
# ─────────────────────────────────────────────────────────────────────────────
SEVERITY_COLORS = {
    "mild": "#4ade80",
    "moderate": "#facc15",
    "severe": "#f97316",
    "life-threatening": "#ef4444",
    "unknown": "#94a3b8",
}

PRIORITY_COLORS = {
    "high": "#ef4444",
    "medium": "#f97316",
    "low": "#4ade80",
    "routine": "#94a3b8",
}

STATUS_COLORS = {
    "completed": "#4ade80",
    "pending": "#facc15",
    "running": "#60a5fa",
    "failed": "#ef4444",
}


def severity_badge(severity: Optional[str]) -> str:
    s = (severity or "unknown").lower()
    color = SEVERITY_COLORS.get(s, "#94a3b8")
    return f'<span style="background:{color};color:#000;padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;">{s.upper()}</span>'


def priority_badge(priority: Optional[str]) -> str:
    p = (priority or "routine").lower()
    color = PRIORITY_COLORS.get(p, "#94a3b8")
    return f'<span style="background:{color};color:#000;padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;">{p.upper()}</span>'


def status_badge(status: Optional[str]) -> str:
    s = (status or "unknown").lower()
    color = STATUS_COLORS.get(s, "#94a3b8")
    return f'<span style="background:{color};color:#000;padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;">{s.upper()}</span>'


def metric_card(label: str, value: Any, icon: str = "📊", delta: str = "") -> str:
    return f"""
    <div style="
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-size: 2rem;">{icon}</div>
        <div style="font-size: 2rem; font-weight: 700; color: #f1f5f9; margin: 8px 0;">{value}</div>
        <div style="color: #94a3b8; font-size: 0.85rem; font-weight: 500;">{label}</div>
        {"<div style='color:#4ade80;font-size:0.75rem;margin-top:4px;'>" + delta + "</div>" if delta else ""}
    </div>
    """


def inject_custom_css() -> None:
    st.markdown("""
    <style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }

    /* ── Main area ── */
    .main { background-color: #0f172a !important; }
    .block-container { padding-top: 1.5rem !important; }

    /* ── Headers ── */
    h1 { color: #f1f5f9 !important; font-weight: 700 !important; }
    h2 { color: #e2e8f0 !important; font-weight: 600 !important; }
    h3 { color: #cbd5e1 !important; font-weight: 500 !important; }

    /* ── Metric ── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] { color: #f1f5f9 !important; }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; }

    /* ── Buttons ── */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }

    /* ── Input / Select ── */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: #1e293b !important;
        border: 1px solid #475569 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
    }

    /* ── Divider ── */
    hr { border-color: #334155 !important; }

    /* ── Card ── */
    .entity-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        transition: border-color 0.2s ease;
    }
    .entity-card:hover { border-color: #3b82f6; }

    /* ── Success / Error  ── */
    .stSuccess { background: #052e16 !important; border: 1px solid #16a34a !important; }
    .stError { background: #450a0a !important; border: 1px solid #dc2626 !important; }
    </style>
    """, unsafe_allow_html=True)
