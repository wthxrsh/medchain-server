# API Endpoints

#api #django #fastapi #jwt #records #sharing #appointments #rag

This note documents the current HTTP surface of the project. Django endpoints are rooted at the Django server, usually `http://127.0.0.1:8000`. RAG endpoints are rooted at the FastAPI service, usually a separate port such as `http://127.0.0.1:8001`.

Authorized endpoints use:

```http
Authorization: Bearer <access_token>
```

Related notes: [[System Architecture]], [[Implementation Guide]], [[Security Model]], [[RAG Service]], [[Testing Strategy]]

---

## Django Auth Endpoints

Defined in:

- `medchain_backend/urls.py`
- `users/urls.py`
- `users/views.py`
- `users/jwt.py`

### Register

`POST /auth/register/`

Public.

Request:

```json
{
  "email": "patient@example.com",
  "password": "password123",
  "first_name": "Asha",
  "last_name": "Rao",
  "role": "PATIENT"
}
```

Response:

```json
{
  "message": "User registered successfully",
  "user_id": "uuid",
  "role": "PATIENT"
}
```

Notes:

- Duplicate email returns `400`.
- Role should be server-validated; current serializer accepts role from request.

### Login

`POST /auth/login/`

Public.

Request:

```json
{
  "email": "patient@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "refresh": "jwt",
  "access": "jwt",
  "role": "PATIENT",
  "email": "patient@example.com",
  "first_name": "Asha",
  "last_name": "Rao",
  "user_id": "uuid"
}
```

### Refresh Access Token

`POST /auth/token/refresh/`

Public.

Request:

```json
{
  "refresh": "jwt"
}
```

### Current User

`GET /auth/me/`

Authenticated.

Returns the current user's profile fields without password.

### Google Auth

`POST /auth/google/`

Public.

Request:

```json
{
  "credential": "google_id_token",
  "flow": "login",
  "role": "PATIENT"
}
```

Behavior:

- `flow=login`: requires an existing user.
- `flow=register`: creates a new user if email is not already registered.
- Uses `GOOGLE_CLIENT_ID` from settings.

### List Doctors

`GET /auth/doctors/`

Authenticated.

Returns doctor users with generated display name and specialty.

Current implementation note:

- Specialty is inferred from email/name heuristics, not stored as a doctor profile model.

### Doctor Analytics

`GET /auth/analytics/`

Authenticated, doctor-only in view logic.

Response:

```json
{
  "total_patients": 1,
  "total_appointments": 2,
  "total_records": 5,
  "record_types": {
    "Lab Report": 3,
    "Prescription": 2
  }
}
```

---

## Django Records Endpoints

Defined in:

- `records/urls.py`
- `records/views.py`
- `records/serializers.py`

### Patient Timeline

`GET /records/`

Authenticated.

Returns records owned by the current user, paginated by `StandardResultsSetPagination`.

Query params:

- `page`
- `page_size`, max 20

Response:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "record_type": "Lab Report",
      "doctor_name": "Dr. Singh",
      "record_date": "2026-06-20",
      "file_url": "http://127.0.0.1:8000/media/uploads/file.pdf",
      "blockchain_status": "CONFIRMED"
    }
  ]
}
```

### Upload Record

`POST /records/upload/`

Authenticated. Multipart form.

Accepted content types:

- `application/pdf`
- `image/jpeg`
- `image/png`

Fields:

- `file_url`: uploaded file, required
- `record_type`: string
- `doctor_name`: string
- `record_date`: optional `YYYY-MM-DD`, defaults to local date

Response:

```json
{
  "message": "Record uploaded successfully.",
  "record_id": "uuid",
  "file_hash": "sha256hex",
  "file_url": "http://127.0.0.1:8000/media/uploads/file.pdf",
  "blockchain_status": "PENDING"
}
```

Current implementation notes:

- Hash is computed before save.
- File is stored locally under `MEDIA_ROOT`.
- Blockchain transaction is simulated in a daemon thread.
- MIME type validation trusts client metadata and needs hardening.

### Doctor Reads Patient Records

`GET /records/patient/{patient_id}/`

Authenticated.

Requires an `AccessGrant` where `doctor=request.user` and `patient_id` matches.

Current implementation note:

- Any grant currently returns all records for the patient.
- It does not filter to `AccessGrant.records`.

---

## Django Share Endpoints

Defined in:

- `sharing/urls.py`
- `sharing/views.py`
- `sharing/models.py`

### Generate Share Token

`POST /share/generate/`

Authenticated.

Request for one record:

```json
{
  "record_id": "uuid"
}
```

Request for full vault:

```json
{}
```

Response:

```json
{
  "token": "urlsafe_token",
  "share_url": "http://127.0.0.1:8000/share/urlsafe_token/",
  "expires_at": "2026-06-20T10:00:00Z",
  "record_id": "uuid"
}
```

Behavior:

- One active token per user/record or user/full-vault scope.
- Token expires after one hour by model default.

Security note:

- Current code logs raw share tokens. This must be removed for production.

### Access Shared Records

`GET /share/{token}/`

Public.

Returns:

- A single serialized record when token is tied to a record.
- A paginated record timeline when token is full-vault.

---

## Django Access Request and Grant Endpoints

The router is mounted at:

`/share/access/`

### Access Requests

`GET /share/access/requests/`

Authenticated.

Returns:

- For doctors: requests sent by the doctor.
- For patients: requests received by the patient.

`POST /share/access/requests/`

Authenticated.

Request:

```json
{
  "patient_email": "patient@example.com",
  "reason": "Need to review recent reports"
}
```

Current implementation note:

- The server should enforce `request.user.role == "DOCTOR"` here, but currently does not.

`POST /share/access/requests/{id}/approve/`

Authenticated patient who owns the request.

Side effects:

- Marks request `Approved`.
- Creates or reuses `AccessGrant(patient=request.user, doctor=access_request.doctor)`.

`POST /share/access/requests/{id}/decline/`

Authenticated patient who owns the request.

### Access Grants

`GET /share/access/grants/`

Authenticated.

Returns:

- For doctors: grants where they are the doctor.
- For patients: grants where they are the patient.

Current implementation note:

- The viewset inherits `ModelViewSet`; production should restrict direct create/update/delete unless explicitly intended.

### Granted Patient Records

`GET /share/access/grants/{patient_id}/records/`

Authenticated.

Requires doctor to have an access grant for `patient_id`.

---

## Django Appointment Endpoints

Defined in:

- `appointments/urls.py`
- `appointments/views.py`
- `appointments/serializers.py`

Mounted at:

`/appointments/`

### List Appointments

`GET /appointments/`

Authenticated.

Behavior:

- Patients see their own appointments.
- Doctors see appointments where `doctor` FK matches, plus fallback name-based matches.

Query params:

- `status`
- `page`
- `page_size`, max 100

### Create Appointment

`POST /appointments/`

Authenticated.

Request:

```json
{
  "doctor_name": "Dr. Asha Rao",
  "specialty": "Cardiology",
  "appointment_date": "2026-06-25",
  "appointment_time": "10:30:00",
  "reason": "Follow-up"
}
```

Current implementation note:

- Doctor FK is inferred from name. Production should require a `doctor_id`.

### Retrieve, Update, Partial Update, Delete

Provided by DRF `ModelViewSet`:

- `GET /appointments/{id}/`
- `PUT /appointments/{id}/`
- `PATCH /appointments/{id}/`
- `DELETE /appointments/{id}/`

### Confirm Appointment

`POST /appointments/{id}/confirm/`

Authenticated.

Allowed for booking patient or assigned doctor. Current fallback allows doctors based on name containment.

### Cancel Appointment

`POST /appointments/{id}/cancel/`

Authenticated.

Allowed for booking patient or assigned doctor. Current fallback allows doctors based on name containment.

---

## FastAPI RAG Endpoints

Defined in:

- `medchain-rag/api/routes.py`
- `medchain-rag/api/schemas.py`

Mounted under:

`/api/v1`

### Health

`GET /api/v1/health`

Public.

Returns index state and configured model names.

### Reindex

`POST /api/v1/reindex`

Authenticated.

Current behavior:

- Any authenticated user can trigger full reindexing.

Production target:

- Admin/service-only.
- Run through a queued job with locking and audit logging.

### Query

`POST /api/v1/query`

Authenticated patient only.

Request:

```json
{
  "query": "What are my recent diagnoses?",
  "top_k": 5,
  "question_category": "diagnoses"
}
```

Response:

```json
{
  "answer": "Generated answer",
  "sources": [
    {
      "text": "source chunk",
      "source_type": "diagnosis",
      "source_id": "uuid",
      "patient_id": "uuid",
      "score": 0.82
    }
  ],
  "query": "What are my recent diagnoses?",
  "answer_mode": "record_grounded",
  "follow_up_questions": []
}
```

Current behavior:

- The endpoint ignores body `patient_id` and scopes retrieval to JWT `user_id`.
- Non-patient roles are rejected.

### Questions

`GET /api/v1/questions`

Authenticated patient only.

Returns categories and suggested question-bank entries.

### Compare Patients

`POST /api/v1/compare`

Authenticated.

Request:

```json
{
  "patient_id_1": "uuid",
  "patient_id_2": "uuid",
  "aspects": ["risk_factors", "medications"]
}
```

Current high-risk behavior:

- The endpoint retrieves context for arbitrary supplied patient IDs without owner/grant/admin authorization.
- See [[Bugs & Production Readiness]] before using this with real data.

---

## Endpoint Hardening Checklist

- Add throttling for auth, share token access, upload, and RAG query endpoints.
- Add explicit permission classes instead of inline role checks.
- Add object-level permission tests for every endpoint that returns PHI.
- Remove token values and PHI from logs.
- Ensure every public endpoint has abuse controls.
- Ensure every doctor endpoint validates doctor role server-side.
- Avoid exposing local media URLs directly in production.
