"""
MedScribe — LLM Service (Multi-Provider: OpenRouter, Groq, Ollama + Robust Fallback)

Provides two capabilities:
    1. extract_entities()  — structured JSON extraction from raw clinical text
    2. generate_summary()  — natural language clinical summary
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI, APIError

from app.core.config import settings
from app.core.logging import logger


# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────
EXTRACTION_SYSTEM_PROMPT = """You are a clinical NLP specialist. Your job is to extract structured medical entities from unstructured clinical notes.

You MUST return ONLY valid JSON — no markdown fences, no explanation, no extra text.

JSON structure (use exactly these keys):
{
  "diagnoses": [
    {"code": "<ICD-10 code or empty string>", "description": "<diagnosis name>", "severity": "<mild|moderate|severe|unknown>"}
  ],
  "medications": [
    {"name": "<drug name>", "dosage": "<amount and unit>", "frequency": "<how often>", "route": "<oral|IV|IM|topical|inhaled|subcutaneous|other>"}
  ],
  "allergies": [
    {"allergen": "<substance>", "reaction": "<reaction description>", "severity": "<mild|moderate|severe|life-threatening|unknown>"}
  ],
  "follow_ups": [
    {"task": "<follow-up action>", "due_date": "<ISO date or free-text timeframe or empty>", "priority": "<high|medium|low|routine>"}
  ]
}

Rules:
- Return empty arrays [] for categories with no entities.
- Do NOT invent or hallucinate entities not present in the note.
- Use exact drug names, do not abbreviate.
- ICD-10 codes are optional; use them only when clearly implied."""

EXTRACTION_USER_TEMPLATE = """Extract all medical entities from the following clinical note:

---
{note_text}
---"""

SUMMARY_SYSTEM_PROMPT = """You are a clinical documentation specialist. Generate concise, professional clinical summaries suitable for chart review.

Write 3-5 sentences that cover:
1. Patient presentation and chief complaint
2. Key diagnoses identified
3. Current medications and allergies
4. Recommended follow-up actions

Use clinical language. Be precise. Do not include patient identifiers."""

SUMMARY_USER_TEMPLATE = """Clinical Note:
{note_text}

Extracted Entities:
{entities_json}

Generate a clinical summary."""


# ─────────────────────────────────────────────────────────────────────────────
# JSON Parsing Utilities
# ─────────────────────────────────────────────────────────────────────────────
def _parse_json_response(content: str) -> Dict[str, Any]:
    """Robustly parse JSON from LLM output (handles markdown fences, extra text)."""
    content = content.strip()

    # Strip markdown code fences
    if "```" in content:
        match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()

    # Try direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract the outermost JSON object
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Cannot parse JSON from LLM response. Preview: {content[:300]!r}")


def _normalize_extracted(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all required keys exist and item fields are strings."""
    result: Dict[str, list] = {
        "diagnoses": [],
        "medications": [],
        "allergies": [],
        "follow_ups": [],
    }

    for d in raw.get("diagnoses", []):
        if isinstance(d, dict) and d.get("description"):
            result["diagnoses"].append({
                "code": str(d.get("code", "") or ""),
                "description": str(d["description"]),
                "severity": str(d.get("severity", "unknown") or "unknown"),
            })

    for m in raw.get("medications", []):
        if isinstance(m, dict) and m.get("name"):
            result["medications"].append({
                "name": str(m["name"]),
                "dosage": str(m.get("dosage", "") or ""),
                "frequency": str(m.get("frequency", "") or ""),
                "route": str(m.get("route", "") or ""),
            })

    for a in raw.get("allergies", []):
        if isinstance(a, dict) and a.get("allergen"):
            result["allergies"].append({
                "allergen": str(a["allergen"]),
                "reaction": str(a.get("reaction", "") or ""),
                "severity": str(a.get("severity", "unknown") or "unknown"),
            })

    for f in raw.get("follow_ups", []):
        if isinstance(f, dict) and f.get("task"):
            result["follow_ups"].append({
                "task": str(f["task"]),
                "due_date": str(f.get("due_date", "") or ""),
                "priority": str(f.get("priority", "routine") or "routine"),
            })

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Heuristic Fallback Extractor (Clinical NLP Rules)
# ─────────────────────────────────────────────────────────────────────────────
KNOWN_DIAGNOSES = [
    ("Type 2 Diabetes Mellitus", "E11.9", "moderate"),
    ("Type 2 Diabetes", "E11.9", "moderate"),
    ("T2DM", "E11.9", "moderate"),
    ("Essential Hypertension", "I10", "moderate"),
    ("Hypertension", "I10", "moderate"),
    ("COPD exacerbation", "J44.1", "severe"),
    ("Chronic Obstructive Pulmonary Disease", "J44.9", "moderate"),
    ("COPD", "J44.9", "moderate"),
    ("Congestive Heart Failure", "I50.9", "severe"),
    ("CHF", "I50.9", "severe"),
    ("Rheumatoid Arthritis", "M06.9", "moderate"),
    ("RA flare", "M06.9", "moderate"),
    ("STEMI", "I21.3", "severe"),
    ("Myocardial Infarction", "I21.9", "severe"),
    ("Community-acquired pneumonia", "J18.9", "moderate"),
    ("Pneumonia", "J18.9", "moderate"),
    ("Hypoglycemia", "E16.2", "severe"),
    ("Hyperlipidemia", "E78.5", "mild"),
    ("Asthma", "J45.9", "moderate"),
    ("Atrial Fibrillation", "I48.9", "moderate"),
    ("Chronic Kidney Disease", "N18.9", "moderate"),
    ("Osteoarthritis", "M19.9", "mild"),
    ("Depression", "F32.9", "mild"),
    ("Anxiety", "F41.9", "mild"),
    ("Septic arthritis", "M00.9", "severe"),
    ("Peripheral edema", "R60.0", "mild"),
]

KNOWN_DRUGS = [
    "Metformin", "Glipizide", "Lisinopril", "Amlodipine", "Atorvastatin", "Empagliflozin",
    "Tiotropium Bromide", "Tiotropium", "Albuterol/Ipratropium", "Albuterol", "Furosemide",
    "Methylprednisolone", "Prednisone", "Azithromycin", "Fluticasone/Salmeterol", "Spironolactone",
    "Carvedilol", "Methotrexate", "Folic acid", "Hydroxychloroquine", "Naproxen", "Celecoxib",
    "Aspirin", "Clopidogrel", "Metoprolol succinate", "Metoprolol", "Nitroglycerin", "Insulin glargine",
    "Insulin", "Dextrose", "Gabapentin", "Omeprazole", "Losartan", "Simvastatin", "Levothyroxine",
]


def _fallback_extract_entities(note_text: str) -> Dict[str, Any]:
    """Extract clinical entities via rule-based heuristics if LLM is unavailable or fails."""
    diagnoses = []
    seen_diag = set()
    for diag_name, icd, severity in KNOWN_DIAGNOSES:
        pattern = r"\b" + re.escape(diag_name) + r"\b"
        if re.search(pattern, note_text, re.IGNORECASE):
            norm = diag_name.title()
            if norm not in seen_diag:
                seen_diag.add(norm)
                diagnoses.append({
                    "code": icd,
                    "description": diag_name,
                    "severity": severity,
                })

    medications = []
    seen_med = set()
    for drug in KNOWN_DRUGS:
        # Match drug name followed by dosage / freq if present
        pattern = r"\b(" + re.escape(drug) + r")\s*(\d+[\.\d]*\s*(?:mg|mcg|units|g|ml|%))?\s*([a-zA-Z/]+)?(?:\s+(oral|IV|IM|topical|inhaled|subcutaneous|SL|nebulized))?"
        match = re.search(pattern, note_text, re.IGNORECASE)
        if match:
            d_name = match.group(1).title()
            if d_name not in seen_med:
                seen_med.add(d_name)
                dosage = match.group(2) or ""
                extra = match.group(3) or ""
                route = match.group(4) or ("inhaled" if "inhaled" in note_text.lower() and d_name in ["Albuterol", "Tiotropium"] else ("IV" if "IV" in note_text and d_name in ["Furosemide", "Dextrose"] else "oral"))
                
                # Check frequency words near the drug
                freq = ""
                for candidate in ["twice daily", "BID", "once daily", "daily", "at bedtime", "QHS", "Q4h", "Q6h", "weekly", "PRN"]:
                    if re.search(r"\b" + re.escape(candidate) + r"\b", note_text[match.start():match.start()+100], re.IGNORECASE):
                        freq = candidate
                        break

                medications.append({
                    "name": d_name,
                    "dosage": dosage.strip(),
                    "frequency": freq,
                    "route": route,
                })

    # Allergies
    allergies = []
    allergy_match = re.search(r"(?:allergic to|allerg(?:y|ies):?)\s+([^.\n]+)", note_text, re.IGNORECASE)
    if allergy_match:
        raw_allergy = allergy_match.group(1).strip()
        # Parse items separated by commas or parentheses
        allergen_parts = re.split(r",|;|\band\b", raw_allergy)
        for part in allergen_parts:
            part = part.strip()
            if not part:
                continue
            reaction = ""
            r_match = re.search(r"\(([^)]+)\)", part)
            if r_match:
                reaction = r_match.group(1).strip()
                part = re.sub(r"\([^)]+\)", "", part).strip()
            severity = "severe" if any(w in (part + reaction).lower() for w in ["anaphylaxis", "stevens-johnson", "sjs", "severe"]) else "moderate"
            if len(part) > 1 and not part.lower().startswith("plan"):
                allergies.append({
                    "allergen": part.capitalize(),
                    "reaction": reaction or "Documented adverse reaction",
                    "severity": severity,
                })

    # Follow-ups
    follow_ups = []
    for sentence in re.split(r"[.\n]", note_text):
        sentence = sentence.strip()
        if re.search(r"\b(follow-?up|recheck|referral|consult|admit|repeat|schedule)\b", sentence, re.IGNORECASE):
            due = ""
            time_match = re.search(r"\b(?:in\s+)?(\d+\s+(?:days?|weeks?|months?))\b", sentence, re.IGNORECASE)
            if time_match:
                due = time_match.group(1)
            priority = "high" if any(w in sentence.lower() for w in ["admit", "cardiac", "urgent", "emergency", "immediate"]) else "routine"
            clean_task = re.sub(r"^(Plan:?|Assessment:?)\s*", "", sentence, flags=re.IGNORECASE).strip()
            if len(clean_task) > 8:
                follow_ups.append({
                    "task": clean_task,
                    "due_date": due,
                    "priority": priority,
                })

    return {
        "diagnoses": diagnoses[:8],
        "medications": medications[:10],
        "allergies": allergies[:5],
        "follow_ups": follow_ups[:5],
    }


def _fallback_generate_summary(note_text: str, entities: Dict[str, Any]) -> str:
    """Generate a high-quality clinical narrative summary when LLM is unavailable."""
    diag_names = [d.get("description", "") for d in entities.get("diagnoses", []) if d.get("description")]
    med_names = [m.get("name", "") for m in entities.get("medications", []) if m.get("name")]
    allergy_names = [a.get("allergen", "") for a in entities.get("allergies", []) if a.get("allergen")]
    follow_tasks = [f.get("task", "") for f in entities.get("follow_ups", []) if f.get("task")]

    sentences = []
    # Presentation / Diagnosis
    if diag_names:
        sentences.append(f"Patient presented for clinical evaluation with prominent diagnoses including {', '.join(diag_names[:3])}.")
    else:
        sentences.append("Patient underwent clinical assessment and chart documentation for ongoing care management.")

    # Medications & Allergies
    if med_names:
        sentences.append(f"Active medication management includes {', '.join(med_names[:4])}.")
    if allergy_names:
        sentences.append(f"Noted significant drug allergies to {', '.join(allergy_names)}.")
    else:
        sentences.append("No adverse drug reactions or allergies reported during this encounter.")

    # Plan / Follow-up
    if follow_tasks:
        sentences.append(f"Plan and follow-up directives: {follow_tasks[0]}.")
    else:
        sentences.append("Recommended routine follow-up as clinically indicated.")

    return " ".join(sentences)


# ─────────────────────────────────────────────────────────────────────────────
# LLM Service Class
# ─────────────────────────────────────────────────────────────────────────────
class LLMService:
    """Multi-provider LLM service supporting OpenRouter, Groq, and Ollama."""

    def __init__(self) -> None:
        self._client: Optional[OpenAI] = None
        self._resolved_provider: Optional[str] = None
        self._resolved_model: Optional[str] = None

    def get_provider_and_model(self) -> Tuple[str, str, str, str]:
        """
        Determines (provider_name, base_url, api_key, model_name).
        Supports: openrouter, groq, ollama, or auto-detection.
        """
        provider = (settings.LLM_PROVIDER or "auto").lower().strip()

        # 1. Groq
        if provider == "groq" or (provider == "auto" and settings.GROQ_API_KEY):
            return (
                "groq",
                "https://api.groq.com/openai/v1",
                settings.GROQ_API_KEY,
                settings.GROQ_MODEL or "llama-3.3-70b-versatile",
            )

        # 2. OpenRouter
        if provider == "openrouter" or (provider == "auto" and settings.OPENROUTER_API_KEY):
            return (
                "openrouter",
                "https://openrouter.ai/api/v1",
                settings.OPENROUTER_API_KEY,
                settings.OPENROUTER_MODEL or settings.LLM_MODEL or "meta-llama/llama-3.3-70b-instruct",
            )

        # 3. Ollama
        if provider == "ollama" or (provider == "auto" and not settings.OPENROUTER_API_KEY and not settings.GROQ_API_KEY):
            return (
                "ollama",
                settings.OLLAMA_BASE_URL or "http://localhost:11434/v1",
                "ollama",
                settings.OLLAMA_MODEL or "llama3",
            )

        # Default fallback to OpenRouter
        return (
            "openrouter",
            "https://openrouter.ai/api/v1",
            settings.OPENROUTER_API_KEY,
            settings.OPENROUTER_MODEL or settings.LLM_MODEL or "meta-llama/llama-3.3-70b-instruct",
        )

    def _get_client(self) -> Tuple[OpenAI, str, str]:
        provider, base_url, api_key, model = self.get_provider_and_model()
        headers = {}
        if provider == "openrouter":
            headers = {
                "HTTP-Referer": "https://github.com/medscribe",
                "X-Title": "MedScribe",
            }

        client = OpenAI(
            base_url=base_url,
            api_key=api_key or "no-key",
            default_headers=headers,
            timeout=25.0,
        )
        return client, provider, model

    def extract_entities(self, note_text: str) -> Tuple[Dict[str, Any], int, str, str]:
        """
        Extract structured medical entities from a clinical note.

        Returns:
            (entities_dict, duration_ms, provider_used, model_used)
        """
        provider, base_url, api_key, model = self.get_provider_and_model()

        # If dummy key or empty key and not ollama, use immediate heuristic extraction
        if (not api_key or api_key in ["test-key", "sk-or-v1-your-key-here"]) and provider != "ollama":
            logger.info("Using heuristic clinical fallback extractor (no active external API key)")
            start = time.perf_counter()
            entities = _fallback_extract_entities(note_text)
            duration_ms = int((time.perf_counter() - start) * 1000)
            return entities, duration_ms, "fallback-rule-based", "clinical-nlp-heuristics"

        start = time.perf_counter()
        try:
            client, provider, model = self._get_client()
            logger.info("Extracting entities via provider={} model={}", provider, model)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": EXTRACTION_USER_TEMPLATE.format(note_text=note_text)},
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            raw_content = response.choices[0].message.content or ""
            raw = _parse_json_response(raw_content)
            entities = _normalize_extracted(raw)
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info("Extraction succeeded in {} ms (provider={}, model={})", duration_ms, provider, model)
            return entities, duration_ms, provider, model

        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.warning(
                "LLM extraction failed via provider={} (error={}). Engaging clinical fallback parser.",
                provider, exc,
            )
            entities = _fallback_extract_entities(note_text)
            return entities, duration_ms, f"{provider}-fallback", "clinical-nlp-heuristics"

    def generate_summary(self, note_text: str, entities: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate a professional clinical summary from note text + extracted entities.

        Returns:
            (summary_text, model_used)
        """
        provider, base_url, api_key, model = self.get_provider_and_model()

        if (not api_key or api_key in ["test-key", "sk-or-v1-your-key-here"]) and provider != "ollama":
            return _fallback_generate_summary(note_text, entities), "clinical-nlp-heuristics"

        try:
            client, provider, model = self._get_client()
            logger.info("Generating summary via provider={} model={}", provider, model)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": SUMMARY_USER_TEMPLATE.format(
                            note_text=note_text,
                            entities_json=json.dumps(entities, indent=2),
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=600,
            )
            summary = (response.choices[0].message.content or "").strip()
            if summary:
                return summary, f"{provider}:{model}"
        except Exception as exc:
            logger.warning("LLM summary generation failed ({}). Using clinical fallback.", exc)

        return _fallback_generate_summary(note_text, entities), f"{provider}-fallback:heuristics"


# ── Singleton ─────────────────────────────────────────────────────────────────
llm_service = LLMService()
