"""
MedScribe Backend — Application Settings
"""
from __future__ import annotations

from typing import Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "MedScribe API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Clinical Notes AI Summarization Service — "
        "Ingest unstructured clinical notes, extract structured medical entities, "
        "and generate AI-powered summaries."
    )
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/medscribe.db"

    # ── LLM Settings (OpenRouter / Groq / Ollama) ───────────────────────────
    LLM_PROVIDER: str = "auto"  # auto | openrouter | groq | ollama
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3"

    # Fallback / generic model setting if specified
    LLM_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2000

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:8501",
        "http://dashboard:8501",
        "http://localhost:3000",
        "*",
    ]

    # ── Pagination ───────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 500

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    return json.loads(v_str)
                except Exception:
                    pass
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        return v


settings = Settings()
