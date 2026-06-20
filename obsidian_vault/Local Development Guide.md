# Local Development Guide

#setup #local #django #postgres #fastapi #rag #docker

This guide gets the current project running locally. It documents what the code does today, not the final production target.

Related notes: [[Requirements]], [[API Endpoints]], [[RAG Service]], [[Deployment Runbook]], [[Testing Strategy]]

---

## Prerequisites

- Python 3.10 or newer.
- Docker Desktop for local PostgreSQL.
- Git.
- Optional: Obsidian for browsing `obsidian_vault`.
- Optional for RAG: Ollama or a Gemini API key, depending on `LLM_PROVIDER`.

---

## Django API Setup

### 1. Create and Activate Virtual Environment

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure `.env`

Create `.env` in the repo root.

```ini
DB_ENGINE=django.db.backends.postgresql
DB_NAME=medchain
DB_USER=postgres
DB_PASSWORD=password123
DB_HOST=127.0.0.1
DB_PORT=5433
GOOGLE_CLIENT_ID=
```

Current settings note:

- `SECRET_KEY` and `DEBUG` are hardcoded in `medchain_backend/settings.py`.
- This is acceptable only for local/demo work. See [[Security Model]] and [[Bugs & Production Readiness]].

### 4. Start PostgreSQL

```powershell
docker compose up -d
```

The compose file maps:

- Host `5433`
- Container `5432`

This avoids clashing with a native PostgreSQL service on host port `5432`.

### 5. Apply Migrations

```powershell
python manage.py migrate
```

### 6. Create Admin User

```powershell
python manage.py createsuperuser
```

Use an email address as the username because `CustomUser.USERNAME_FIELD = "email"`.

### 7. Seed Demo Data

The repository includes a test-data generator.

Generate only:

```powershell
python generate_test_data.py --count 1000 --output test_users_data.json
```

Generate and load:

```powershell
python generate_test_data.py --load
```

### 8. Run Django Server

```powershell
python manage.py runserver
```

Default URL:

```text
http://127.0.0.1:8000/
```

---

## RAG Service Setup

The RAG service is in `medchain-rag`.

### 1. Install RAG Dependencies

```powershell
cd medchain-rag
pip install -r requirements.txt
```

### 2. Configure RAG `.env`

Create `medchain-rag/.env` or export environment variables.

```ini
DB_PATH=../db.sqlite3
FAISS_INDEX_PATH=./data/faiss.index
FAISS_META_PATH=./data/faiss_meta.json
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=400
CHUNK_OVERLAP=80
TOP_K=5
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash
JWT_SECRET=local-django-secret
JWT_ALGORITHM=HS256
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Important current mismatch:

- Django local setup uses PostgreSQL.
- RAG connector currently uses SQLite through `DB_PATH`.
- For end-to-end local RAG with current code, either point RAG at a SQLite DB that has the Django schema/data or update the connector to use PostgreSQL.

### 3. Run RAG Server

```powershell
uvicorn main:app --reload --port 8001
```

Default URL:

```text
http://127.0.0.1:8001/api/v1/health
```

### 4. Build FAISS Index

Use a valid Django JWT:

```powershell
curl -X POST http://127.0.0.1:8001/api/v1/reindex -H "Authorization: Bearer <access_token>"
```

Current warning:

- `/reindex` is not admin-only yet. Treat this as a local/demo endpoint.

---

## Useful Local API Calls

### Register

```powershell
curl -X POST http://127.0.0.1:8000/auth/register/ -H "Content-Type: application/json" -d "{\"email\":\"patient@example.com\",\"password\":\"password123\",\"role\":\"PATIENT\"}"
```

### Login

```powershell
curl -X POST http://127.0.0.1:8000/auth/login/ -H "Content-Type: application/json" -d "{\"email\":\"patient@example.com\",\"password\":\"password123\"}"
```

### Timeline

```powershell
curl http://127.0.0.1:8000/records/ -H "Authorization: Bearer <access_token>"
```

### RAG Health

```powershell
curl http://127.0.0.1:8001/api/v1/health
```

---

## Common Problems

### Database Connection Refused

Check:

- Docker is running.
- `docker compose up -d` completed.
- `.env` uses `DB_PORT=5433`.
- No firewall is blocking localhost.

### Login Fails After Seeding

Check:

- Seed script loaded users into the same database configured in `.env`.
- Passwords are known and hashed through Django user creation logic.

### Uploaded Files Return 404

Check:

- `DEBUG=True` for local media serving.
- File exists under `media/uploads/`.
- `MEDIA_URL=/media/` and `MEDIA_ROOT=BASE_DIR / "media"`.

### RAG Reindex Finds No Data

Check:

- RAG `DB_PATH` points to an actual SQLite DB with Django tables.
- If using PostgreSQL locally, the current RAG connector will not read it without code changes.

---

## Local Development Rules of Thumb

- Keep local `.env` out of git.
- Do not use demo secrets or `password123` outside local development.
- Do not test with real PHI until security and audit gaps are fixed.
- Prefer adding tests with every permission or data-access change.
- Keep the vault updated when routes, models, or workflows change.
