# Directory & Modules Map

#structure #modules #django #fastapi #codebase

This note explains the repository layout and ownership boundaries.

Related notes: [[System Architecture]], [[Implementation Guide]], [[API Endpoints]], [[RAG Service]]

---

## Top-Level Layout

```text
medchain-server/
|-- manage.py
|-- requirements.txt
|-- docker-compose.yml
|-- generate_test_data.py
|-- test_users_data.json
|-- medchain_backend/
|-- users/
|-- records/
|-- sharing/
|-- appointments/
|-- blockchain/
|-- clinical/
|-- parsing/
|-- medchain-rag/
|-- obsidian_vault/
```

---

## Django Project Core: `medchain_backend/`

Files:

- `settings.py`: environment loading, installed apps, middleware, database, CORS, JWT, media/static settings.
- `urls.py`: mounts auth, records, sharing, and appointments routes.
- `wsgi.py`: WSGI entrypoint.
- `asgi.py`: ASGI entrypoint.

Important implementation details:

- Settings currently hardcode `SECRET_KEY`, `DEBUG=True`, and default DB credentials.
- `REST_FRAMEWORK` uses JWT authentication and `IsAuthenticated` by default.
- Local media serving is enabled when debug is true.

---

## Authentication and Users: `users/`

Files:

- `models.py`: UUID email-login `CustomUser` with role choices.
- `serializers.py`: user creation serializer.
- `jwt.py`: custom SimpleJWT serializer/view.
- `views.py`: register, profile, doctor analytics, doctor list, Google auth.
- `urls.py`: auth route definitions.

Key behaviors:

- Email replaces username.
- Login response includes role/profile fields.
- JWT contains role and email claims.
- Google auth supports separate login/register flow.

Production concerns:

- Public role assignment needs policy.
- Auth endpoints need throttling.
- Doctor profile/specialty should be a real model, not email heuristics.

---

## Records: `records/`

Files:

- `models.py`: `Record` model with file metadata and SHA-256 hash.
- `serializers.py`: upload and timeline serializers.
- `views.py`: upload, patient timeline, doctor patient-record access.
- `pagination.py`: standard page size defaults.
- `urls.py`: records routes.

Key behaviors:

- Upload accepts PDF, JPEG, PNG by client-provided MIME type.
- Hash is computed from uploaded chunks.
- Upload creates a pending blockchain transaction.
- Timeline returns file URL and blockchain status.

Production concerns:

- Need stronger file validation and malware scanning.
- Need private object storage.
- Doctor access should be grant-scope aware.

---

## Sharing: `sharing/`

Files:

- `models.py`: `ShareToken`, `AccessRequest`, `AccessGrant`.
- `serializers.py`: access request/grant serializers and nested user details.
- `views.py`: token generation/access, access request actions, grant views.
- `urls.py`: token and router routes.

Key behaviors:

- Share tokens expire after one hour.
- Optional `record_id` limits a token to one record.
- Access requests are approved or declined by patients.
- Approval creates an access grant.

Production concerns:

- Raw tokens are logged.
- Access requests do not enforce doctor role on create.
- `AccessGrantViewSet` is too broad for a sensitive object.
- Grant `records` M2M is not enforced by record reads.

---

## Appointments: `appointments/`

Files:

- `models.py`: appointment model.
- `serializers.py`: appointment serializer.
- `views.py`: appointment viewset with confirm/cancel actions.
- `urls.py`: DRF router.

Key behaviors:

- Patients create appointments.
- Doctor FK is inferred from `doctor_name`.
- Doctors can see appointments by FK or name fallback.
- Confirm/cancel allowed for patient or assigned doctor.

Production concerns:

- Require `doctor_id` for booking.
- Remove name-based authorization fallback.
- Add appointment conflict/time-zone validation.

---

## Clinical Data: `clinical/`

Files:

- `models.py`: `Vitals`, `Diagnosis`, `Prescription`.
- `apps.py`: app config.
- migrations.

Key behaviors:

- Structured medical data exists at the model layer.
- There are no current project URL routes for clinical CRUD endpoints.
- RAG ingestion can read clinical tables.

Production concerns:

- Add explicit APIs only after permission and audit model are ready.
- Add validation ranges for vitals.
- Add medical coding conventions for diagnoses/medications if required.

---

## Blockchain: `blockchain/`

Files:

- `models.py`: `BlockchainTransaction`.
- `services.py`: mock background submission.
- `views.py`: present but not mounted in main URLs.

Key behaviors:

- Every uploaded record gets a one-to-one transaction row.
- Background thread waits 3 seconds, writes mock `tx_hash`, and marks confirmed.

Production concerns:

- Replace thread with Celery/RQ/Dramatiq.
- Add retries, idempotency, and failure observability.
- Separate mock implementation from real blockchain adapter.

---

## Parsing: `parsing/`

Files:

- `models.py`
- `views.py`
- migrations.

Current role:

- Placeholder for OCR/AI extracted document data.
- RAG connector references `parsing_parseddata`, so this layer is intended to feed structured extracted values.

Production concerns:

- Define the parsing model/API contract clearly.
- Add async parsing jobs after upload.
- Store confidence, source spans, parser version, and review status.

---

## RAG Service: `medchain-rag/`

Top-level files:

- `main.py`: FastAPI app, CORS, lifespan, global exception handler.
- `config.py`: env-driven paths, model config, JWT config, CORS.
- `requirements.txt`: RAG service dependencies.
- `pytest.ini`: RAG test config.

Subfolders:

- `api/`: route handlers and Pydantic schemas.
- `auth/`: JWT validation.
- `db/`: DB connector.
- `embeddings/`: embedding model and FAISS index.
- `ingestion/`: document building and chunking.
- `llm/`: provider integration, question bank, answer generation.
- `retrieval/`: vector retrieval and context building.
- `tests/`: RAG unit/integration tests.
- `utils/`: logging setup.

Production concerns:

- Align RAG database connector with Django production database.
- Fix admin-only reindexing.
- Fix compare endpoint authorization.
- Avoid logging PHI queries.

---

## Documentation Vault: `obsidian_vault/`

Purpose:

- Project knowledge base and implementation handbook.
- Architecture, endpoint, schema, security, production, testing, and runbook notes.

Recommended use:

- Start at [[Index]].
- Use graph view around [[Implementation Guide]], [[Security Model]], and [[Bugs & Production Readiness]] for current work.
