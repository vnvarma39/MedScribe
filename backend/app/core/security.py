"""
MedScribe — Request Security & Header Helpers
"""
from fastapi import Request

def sanitize_input(text: str) -> str:
    """Strip null bytes and excessive whitespace from clinical note input."""
    if not text:
        return ""
    return text.replace("\x00", "").strip()
