# Bugs & Production Readiness

#bugs #production #security #privacy #django #fastapi #rag

This branch tracks current bugs, risky implementation choices, and the concrete changes needed to move MedChain toward production-grade operation. It is based on the current backend, sharing, appointments, blockchain, and RAG service code.

Related notes: [[System Architecture]], [[Database Schema]], [[API Endpoints]], [[Local Development Guide]], [[Requirements]]

---

## Executive Summary

The project is functional for a demo/local environment, but it is not production-ready yet. The highest-risk issues are hardcoded secrets, permissive debug settings, missing rate limits, medical data access-control gaps, public share-token exposure in logs, local file storage for health records, and background processing implemented with unmanaged threads.

Recommended production sequence:

1. Lock down secrets, settings, CORS, hosts, HTTPS, and logging.
2. Fix record-sharing and RAG authorization bugs before exposing real patient data.
3. Move file storage and background processing to durable managed infrastructure.
4. Add audit trails, throttling, tests, monitoring, and deployment checks.

---

## Critical Bugs

### CRIT-001: Hardcoded Django `SECRET_KEY` and RAG `JWT_SECRET`

Evidence:
- `medchain_backend/settings.py` hardcodes `SECRET_KEY`.
- `medchain-rag/config.py` falls back to the same hardcoded secret in `JWT_SECRET`.

Impact:
- Anyone with repository access can forge or tamper with signed tokens if this key reaches production.
- Session integrity, password reset tokens, CSRF signing, and JWT validation are compromised.
- Rotating the secret later could invalidate active tokens unexpectedly without a planned process.

Suggested fix:
- Read `SECRET_KEY` and `JWT_SECRET` only from environment or a secret manager.
- Fail startup if either secret is missing in non-development environments.
- Use one authoritative identity provider/signing configuration; avoid duplicated secret defaults across Django and FastAPI.
- Add documented key rotation steps.

Production-grade change:
```python
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is required")
```

### CRIT-002: `DEBUG=True` and Development Hosts in Settings

Evidence:
- `medchain_backend/settings.py` sets `DEBUG = True`.
- `ALLOWED_HOSTS` only contains localhost values.
- Media files are served by Django when debug is enabled.

Impact:
- Public tracebacks can expose stack frames, settings, paths, and sensitive request data.
- Deployment may fail or behave inconsistently behind real domains.
- Django is not appropriate for serving protected media directly in production.

Suggested fix:
- Make `DEBUG` environment-driven and default to `False`.
- Require explicit `ALLOWED_HOSTS` in production.
- Add `SECURE_SSL_REDIRECT`, secure cookie flags, HSTS, proxy SSL header configuration, and security headers.

### CRIT-003: RAG `/compare` Can Retrieve Arbitrary Patient Context

Evidence:
- `medchain-rag/api/routes.py` accepts `patient_id_1` and `patient_id_2` from the request body.
- The endpoint retrieves chunks for both supplied patient IDs after only validating that the caller has any valid JWT.
- There is no role, ownership, grant, or admin authorization check for those patient IDs.

Impact:
- A user who can guess or obtain patient UUIDs may compare or retrieve summaries of other patients.
- This is a serious PHI/medical-data access-control issue.

Suggested fix:
- Restrict patient users to their own `user_id`.
- For doctors, verify an active `AccessGrant` before allowing access to a patient.
- For admins, require an explicit admin role and audit entry.
- Consider removing the endpoint until authorization rules are fully implemented.

### CRIT-004: Share Tokens Are Logged in Plain Text

Evidence:
- `sharing/views.py` logs the generated token in `GenerateShareTokenView`.
- `AccessSharedRecordsView` logs the token again when it is used.

Impact:
- Anyone with application log access can open shared medical records until the token expires.
- Logs are commonly exported to third-party systems, backups, and dashboards.

Suggested fix:
- Never log bearer tokens, share tokens, credentials, or raw PHI.
- Log only a token fingerprint such as the first 8 chars of an HMAC or the token model ID.
- Add structured audit events without sensitive values.

### CRIT-005: Access Grants Model Selected Records, but Reads Allow All Records

Evidence:
- `sharing/models.py` has `AccessGrant.records = ManyToManyField(Record, blank=True)`.
- `records/views.py` `DoctorPatientRecordsView` only checks that any grant exists, then returns all patient records.
- `sharing/views.py` `GrantedPatientRecordsView` does the same.

Impact:
- If the product intends selective sharing, doctors receive broader access than the data model suggests.
- Patients may believe only selected records are shared while the API exposes the full timeline.

Suggested fix:
- Define product semantics: all-record grant, selected-record grant, or both.
- If selected sharing is intended, filter by `grant.records.all()`.
- If all-record grants are intended, remove the unused M2M field or add a clear `scope` field.
- Add tests proving a doctor cannot fetch ungranted records.

---

## High Priority Bugs

### HIGH-001: No API Rate Limiting or Brute-Force Protection

Evidence:
- `REST_FRAMEWORK` does not define throttle classes/rates.
- Public endpoints include auth registration, login, Google auth, and share-token access.

Impact:
- Brute-force login attempts, token probing, registration spam, and file-fetch abuse are not controlled.

Suggested fix:
- Add DRF throttles globally and stricter endpoint-specific throttles for auth/share endpoints.
- Add IP/user-based login failure tracking.
- Put the API behind a reverse proxy/WAF with request limits.

### HIGH-002: Background Blockchain Work Uses Unmanaged Threads

Evidence:
- `blockchain/services.py` starts a daemon `threading.Thread` for each blockchain submission.

Impact:
- Work is lost when the web process restarts.
- No durable retries, backoff, visibility, or dead-letter queue.
- High upload volume can exhaust process resources.

Suggested fix:
- Use Celery/RQ/Dramatiq with Redis or RabbitMQ.
- Store retries, failure reasons, and external transaction IDs.
- Make transaction submission idempotent.

### HIGH-003: Medical Files Are Stored on Local Disk

Evidence:
- `records/models.py` stores uploads in `FileField(upload_to="uploads/")`.
- `medchain_backend/settings.py` sets `MEDIA_ROOT = BASE_DIR / "media"`.

Impact:
- Files disappear on container rebuilds unless mounted carefully.
- Multi-instance deployments cannot reliably serve uploaded records.
- Access control around direct file URLs is weak unless media serving is carefully gated.

Suggested fix:
- Use private object storage such as S3, GCS, or Azure Blob.
- Serve files through short-lived signed URLs or a permission-checked proxy endpoint.
- Encrypt objects at rest and define lifecycle/retention policies.

### HIGH-004: Default Database Credentials in Code and Compose

Evidence:
- `medchain_backend/settings.py` defaults to `postgres/password123`.
- `docker-compose.yml` also sets `POSTGRES_PASSWORD=password123`.

Impact:
- Demo credentials can leak into staging/production.
- Attackers routinely scan for default Postgres credentials.

Suggested fix:
- Move DB credentials into `.env` or a secret manager.
- Fail startup in production when default credentials are detected.
- Use separate users for app runtime, migrations, and admin operations.

### HIGH-005: RAG `/reindex` Is Not Admin-Only

Evidence:
- `medchain-rag/api/routes.py` comment says "Doctors and admins only in production; any authenticated user here for demo."
- The implementation permits any authenticated user.

Impact:
- Any user can trigger expensive full-database indexing.
- Reindex can leak data into a shared vector index if access scoping is not airtight.
- This creates denial-of-service and privacy risks.

Suggested fix:
- Restrict to admin/service roles.
- Queue reindexing as an admin task.
- Add locking so concurrent reindex jobs cannot corrupt index files.
- Audit who triggered reindex and what data scope was indexed.

---

## Medium Priority Bugs and Design Risks

### MED-001: Doctor AccessRequest Creation Does Not Enforce Doctor Role

Evidence:
- `AccessRequestViewSet.create` creates requests with `doctor=request.user`.
- It does not check `request.user.role == "DOCTOR"`.

Impact:
- A patient account can create doctor-style access requests unless blocked by the frontend.

Suggested fix:
- Enforce role checks server-side.
- Add permissions classes such as `IsDoctor`, `IsPatient`, and `IsOwnerOrGrantedDoctor`.

### MED-002: AccessGrant ViewSet Allows Unsafe Default ModelViewSet Actions

Evidence:
- `AccessGrantViewSet` inherits `ModelViewSet`.
- The serializer exposes `fields = "__all__"`.

Impact:
- Depending on DRF behavior and request payloads, authenticated users may attempt create/update/delete operations not intended by the product.
- Even where queryset scoping limits reads, write permissions should be explicit.

Suggested fix:
- Use read-only viewsets where grants should only be created by approval flow.
- Disable direct create/update/delete or enforce strict role/object validation.

### MED-003: Appointment Doctor Matching Uses Name Heuristics

Evidence:
- `appointments/views.py` links doctors by partial first/last name and allows confirm/cancel fallback based on name containment.

Impact:
- Two doctors with similar names can be mismatched.
- A doctor may see or modify appointments not assigned to their account.

Suggested fix:
- Require booking by `doctor_id`, not free-form `doctor_name`.
- Keep `doctor_name` as a snapshot/display field only.
- Authorize confirm/cancel by doctor FK or patient FK.

### MED-004: File Upload Validation Trusts MIME Type

Evidence:
- `RecordUploadView` checks `uploaded_file.content_type`.

Impact:
- Clients can spoof content types.
- Malicious files could be stored and later served to users.

Suggested fix:
- Validate file signatures with a library such as python-magic.
- Add max upload size, malware scanning, extension normalization, and safe content-disposition.
- Consider converting images/PDFs to sanitized derivatives for display.

### MED-005: Insufficient Audit Trail for PHI Access

Evidence:
- Current logging captures some share events, but there is no durable audit model for record reads, uploads, token generation, grants, approvals, RAG queries, or file downloads.

Impact:
- Production healthcare systems need traceability for who accessed what, when, and why.

Suggested fix:
- Add an immutable `AuditEvent` model/table.
- Capture actor, patient, object type, object ID, action, IP, user agent, outcome, and request ID.
- Keep sensitive tokens and raw PHI out of logs.

### MED-006: Empty Test Files for Core Django Apps

Evidence:
- `users/tests.py`, `records/tests.py`, and `sharing/tests.py` contain only placeholder comments.

Impact:
- Access-control regressions can ship unnoticed.
- Upload, sharing, grant, and auth behavior has no automated guardrails.

Suggested fix:
- Add tests for auth flows, role permissions, record upload/listing, share-token expiry, selective grants, doctor access, and negative access cases.
- Add CI to run Django and RAG tests on every push.

---

## Production-Grade Roadmap

### Security and Configuration

- Replace hardcoded secrets with environment variables or a managed secret store.
- Add separate settings modules for local, test, staging, and production.
- Default `DEBUG` to false.
- Configure allowed hosts, trusted origins, secure cookies, HSTS, HTTPS redirects, and proxy headers.
- Add dependency vulnerability scanning and secret scanning in CI.
- Remove sensitive values from logs and error messages.

### Authentication and Authorization

- Create reusable permission classes:
  - `IsPatient`
  - `IsDoctor`
  - `IsAdmin`
  - `IsRecordOwner`
  - `HasPatientGrant`
- Apply role checks server-side to every role-dependent endpoint.
- Add object-level authorization tests.
- Consider refresh-token rotation and blacklist support.
- Add account lockout or throttling for repeated failed logins.

### Privacy and Compliance

- Add durable audit logging for all PHI access.
- Define retention and deletion policy for records, logs, tokens, vector indexes, and backups.
- Encrypt database, file storage, and backups at rest.
- Use signed URLs or permission-checked streaming for files.
- Document breach-response and key-rotation processes.

### Data and Storage

- Move uploads to private object storage.
- Add upload size limits and malware scanning.
- Store file hash, content type, original filename, storage key, and scan status.
- Add database constraints for role-specific relationships where appropriate.
- Add migrations to support grant scopes clearly.

### Background Jobs and Blockchain

- Replace daemon threads with a durable task queue.
- Add idempotency keys for blockchain submissions.
- Track retries, failure reasons, and last attempted time.
- Add a repair command for stuck `PENDING` transactions.
- Separate mock blockchain code from real chain integration.

### RAG Service

- Make RAG authorization patient- and grant-aware.
- Restrict `/reindex` to admin/service users.
- Prevent arbitrary patient ID queries.
- Partition or filter vector indexes by patient with defense-in-depth.
- Avoid logging full user queries if they may contain PHI.
- Add health/readiness endpoints that do not expose sensitive system details.

### Observability and Operations

- Add structured JSON logging with request IDs.
- Add metrics for auth failures, uploads, share-token accesses, grant changes, RAG latency, task failures, and DB errors.
- Add Sentry/OpenTelemetry or equivalent tracing.
- Add readiness/liveness checks for Django, RAG, DB, Redis, object storage, and task workers.
- Create runbooks for failed uploads, stuck jobs, token abuse, and index rebuilds.

### Testing and CI

- Add Django tests for every critical permission path.
- Add RAG tests for token validation and patient scoping.
- Add upload validation tests for file type, size, and malicious names.
- Add integration tests for share-token expiry and grant approval.
- Run linting, formatting, migrations check, tests, and dependency audit in CI.

---

## Suggested Fix Order

1. Secrets/config hardening: `SECRET_KEY`, `JWT_SECRET`, `DEBUG`, DB credentials, secure cookies.
2. Access-control fixes: RAG compare/reindex, grant scoping, role permission classes.
3. Sensitive logging cleanup: remove share tokens and PHI from logs.
4. Rate limiting: auth, token refresh, share access, uploads, RAG query endpoints.
5. Storage hardening: object storage, signed URLs, file validation, upload limits.
6. Background jobs: queue blockchain submission and add stuck-job repair.
7. Tests and CI: start with negative authorization tests and share-token expiry.
8. Observability and audit: structured logs, audit events, metrics, runbooks.

---

## Definition of Production-Ready

MedChain should not be considered production-ready until:

- No production secrets or credentials exist in code.
- `DEBUG` is false by default outside local development.
- Every endpoint has explicit role and object-level authorization.
- PHI access is audited without leaking tokens or raw sensitive data in logs.
- Record files are stored privately and served only after permission checks.
- Critical async work is durable and retryable.
- Auth, sharing, uploads, appointments, grants, and RAG access have automated tests.
- CI blocks insecure settings, failing tests, missing migrations, and known-vulnerable dependencies.
