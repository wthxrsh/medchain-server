# Requirements

#requirements #dependencies #environment #django #fastapi #rag

This note summarizes runtime, development, configuration, and production requirements.

Related notes: [[Local Development Guide]], [[Deployment Runbook]], [[Security Model]], [[Testing Strategy]]

---

## Runtime Requirements

### Django API

Python packages from root `requirements.txt`:

- Django
- django-cors-headers
- djangorestframework
- djangorestframework_simplejwt
- psycopg2-binary
- PyJWT
- google-auth
- requests

External services:

- PostgreSQL for local/current Django database.
- Optional frontend at `localhost:3000` for configured CORS.

### RAG API

Python packages from `medchain-rag/requirements.txt` include FastAPI/RAG stack dependencies.

External services:

- FAISS index persisted on disk.
- SQLite file by current connector default.
- Gemini API or Ollama, depending on `LLM_PROVIDER`.
- Valid JWT secret matching Django token signing.

---

## Environment Variables

### Django

Current settings read:

- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `GOOGLE_CLIENT_ID`

Production-required additions:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `CORS_ALLOWED_ORIGINS`
- `SECURE_SSL_REDIRECT`
- object storage credentials
- task queue broker URL
- logging/monitoring DSNs

### RAG

Current config reads:

- `DB_PATH`
- `FAISS_INDEX_PATH`
- `FAISS_META_PATH`
- `EMBEDDING_MODEL`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `TOP_K`
- `LLM_PROVIDER`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `CORS_ORIGINS`

Production-required additions:

- admin/service authentication settings for reindexing
- managed database DSN if RAG reads from PostgreSQL
- vector-store configuration if moving off local FAISS files
- PHI-safe logging controls

---

## Functional Requirements

### Users and Auth

- Users register and log in with email/password.
- Users can authenticate with Google ID tokens.
- JWTs include user role and email claims.
- Roles are currently `PATIENT` and `DOCTOR`.

### Records

- Authenticated users can upload PDF/JPEG/PNG records.
- The system computes a SHA-256 file hash.
- The system stores upload metadata.
- The system creates a blockchain transaction record for each upload.
- Patients can list their own records.

### Sharing

- Patients can create one-hour public share tokens.
- Tokens can share one record or the whole vault.
- Doctors can request access to patient records.
- Patients can approve or decline requests.
- Approved requests create access grants.

### Appointments

- Patients can create appointments.
- Patients and assigned doctors can confirm/cancel appointments.
- Doctors can view their appointment list.

### RAG

- Authenticated patients can query their own indexed context.
- Patients can fetch suggested questions.
- Reindexing builds a vector index from patient data.
- Patient comparison currently exists but needs authorization hardening.

---

## Non-Functional Requirements for Production

Security:

- No hardcoded secrets.
- No debug mode in production.
- Explicit role and object-level authorization.
- Rate limiting on public and expensive endpoints.
- PHI-safe logs.
- Private media storage.

Reliability:

- Durable background tasks.
- Idempotent blockchain submission.
- Database migrations and rollback plan.
- Health/readiness checks.
- Backup and restore process.

Compliance-oriented controls:

- Audit trail for PHI access.
- Data retention policy.
- Token revocation.
- Encryption at rest and in transit.
- Least-privilege service accounts.

Operations:

- Structured logs.
- Metrics and alerts.
- CI test suite.
- Dependency and secret scanning.
- Environment-specific settings.

---

## Version Notes

The comment in `medchain_backend/settings.py` mentions Django 6.0.3, while `requirements.txt` pins Django 5.2.13. Treat `requirements.txt` as authoritative for the current environment unless the project is upgraded intentionally.
