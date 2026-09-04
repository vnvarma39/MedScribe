# MedScribe — System Architecture & Design

MedScribe is engineered as an enterprise clinical documentation and AI entity extraction engine.

## 1. High-Level Architecture

```
[ Unstructured Clinical Note ]
              │
              ▼
    FastAPI Ingestion API  (POST /api/v1/notes/)
              │
     (Persists to SQLite)
              │
              ├──► BackgroundTasks (Async Extraction Worker)
              │           │
              │           ▼
              │     LLM Service (OpenRouter / Groq / Ollama)
              │     + Fallback Clinical Regex Parser
              │           │
              │           ▼
              │     Persists: Diagnoses, Meds, Allergies, Follow-ups
              │
              ▼
    Normalized SQLite Database (WAL Mode, 7 Tables)
              │
              ▼
    FastAPI Query Endpoints (Patients, Notes, Search, Analytics)
              │
              ▼
    Streamlit Clinical Dashboard (4 Interactive Pages)
```

## 2. Core Components

1. **FastAPI Backend (`backend/app`)**:
   - Asynchronous request handling with Pydantic v2 schemas.
   - SQLite with WAL (Write-Ahead Logging) and thread-safe session pooling.
   - BackgroundTasks for non-blocking note ingestion and entity extraction.

2. **Multi-Provider LLM Service (`backend/app/services/llm_service.py`)**:
   - Supports OpenRouter (Meta-Llama-3.3-70B), Groq API, and local Ollama.
   - Rule-based clinical fallback parser guaranteeing 100% operational uptime.

3. **Streamlit Analytics Dashboard (`dashboard/`)**:
   - Modern clinical dark theme with Plotly interactive charts.
   - Dedicated views for patient records, entity cards, population analytics, and ingestion.
