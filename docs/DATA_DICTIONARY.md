# MedScribe — Clinical Data Dictionary

## Normalized Database Schema (7 Tables)

1. `patients`: ID, Name, DOB, Gender, MRN, CreatedAt.
2. `clinical_notes`: ID, PatientID, RawText, NoteDate, Source, Provider, CreatedAt.
3. `diagnoses`: ID, NoteID, Code (ICD-10), Description, Severity.
4. `medications`: ID, NoteID, Name, Dosage, Frequency, Route.
5. `allergies`: ID, NoteID, Allergen, Reaction, Severity.
6. `follow_ups`: ID, NoteID, Task, DueDate, Priority.
7. `extraction_jobs`: ID, NoteID, Status, LLMProvider, ModelUsed, DurationMs, ErrorMessage.
