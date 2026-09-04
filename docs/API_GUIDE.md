# MedScribe — REST API Reference Guide

All endpoints are prefixed with `/api/v1`. Interactive Swagger documentation is available at `http://localhost:8000/docs`.

## Patients API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/patients/` | Create a new patient profile |
| `GET` | `/api/v1/patients/` | List patients (search by name/MRN, pagination) |
| `GET` | `/api/v1/patients/{id}` | Get single patient details |
| `PATCH` | `/api/v1/patients/{id}` | Update patient demographics |
| `DELETE` | `/api/v1/patients/{id}` | Delete patient and associated notes |
| `GET` | `/api/v1/patients/{id}/notes` | Retrieve clinical notes timeline for a patient |

## Clinical Notes API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/notes/` | Ingest clinical note and trigger async entity extraction |
| `GET` | `/api/v1/notes/` | List notes with full-text search and pagination |
| `GET` | `/api/v1/notes/{id}` | Get full note detail with extracted medical entities |
| `GET` | `/api/v1/notes/{id}/summary` | Generate on-demand AI clinical summary |
| `DELETE` | `/api/v1/notes/{id}` | Delete a note and its extracted entities |

## Analytics API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/stats/` | Aggregate population stats, top diagnoses, meds, and pipeline health |
