# Clinical Entity Extraction & AI Summarization

MedScribe uses structured output prompts with JSON schemas to extract clinical entities from raw text.

## 1. Entity Types Extracted

1. **Diagnoses**: ICD-10 code, disease description, severity (`mild`, `moderate`, `severe`, `unknown`).
2. **Medications**: Drug name, dosage, frequency, administration route (`oral`, `IV`, `inhaled`, etc.).
3. **Allergies**: Allergen name, reaction type, severity classification.
4. **Follow-ups**: Action items, due dates, priority level (`high`, `medium`, `low`, `routine`).

## 2. Multi-Provider Fallback Strategy

To ensure zero downtime:
- Primary Provider: OpenRouter / Groq API.
- Secondary Provider: Ollama local model.
- Heuristic NLP Fallback: Built-in rule-based clinical parser handles rate limits or network issues seamlessly.
