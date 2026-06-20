# Security Model

#security #privacy #authorization #jwt #phi #production

This note describes the intended security posture and the current gaps that must be closed before real patient data is used.

Related notes: [[Bugs & Production Readiness]], [[API Endpoints]], [[Implementation Guide]], [[Deployment Runbook]], [[Testing Strategy]]

---

## Data Classification

Highly sensitive:

- Medical record files.
- Structured clinical data.
- RAG source chunks and answers.
- Share tokens and JWTs.
- Audit logs that identify PHI access.

Sensitive:

- User emails and names.
- Appointment metadata.
- Access request reasons.
- File hashes and storage keys.

Operational:

- Request IDs.
- Non-sensitive status metrics.
- Aggregated counts without patient identifiers.

---

## Authentication

Current implementation:

- Email/password login through SimpleJWT.
- Google ID token login/registration.
- JWT claims include `role` and `email`.
- RAG service validates JWT with shared secret.

Production requirements:

- Store signing secrets outside code.
- Enable refresh token rotation and blacklist if long-lived sessions are needed.
- Add throttling and lockout/risk controls for login.
- Add MFA for admins and potentially doctors.
- Avoid duplicating JWT secret defaults across services.

---

## Authorization

Current roles:

- `PATIENT`
- `DOCTOR`

Recommended permission classes:

- `IsPatient`
- `IsDoctor`
- `IsAdmin`
- `IsRecordOwner`
- `HasPatientGrant`
- `CanAccessSharedRecord`

Authorization rules:

- Patients can read/write only their own records and clinical data.
- Doctors can read patient data only through active grants.
- Public share-token access can read only what the token grants and only before expiry.
- RAG patient query must be scoped to JWT `user_id`.
- RAG admin operations must require admin/service credentials.

Current gaps:

- Access request creation does not require doctor role.
- Access grants imply selected records but reads allow all records.
- RAG compare endpoint can access arbitrary patient IDs.
- RAG reindex allows any authenticated user.
- Appointment doctor authorization uses name matching fallback.

---

## Token Handling

JWTs:

- Treat access and refresh tokens as bearer secrets.
- Do not log tokens.
- Validate signature, expiration, and required claims.

Share tokens:

- Current code stores raw token and logs raw token.
- Production should store a hashed token.
- Display raw token only once to the patient.
- Add revocation and access audit.

Recommended token storage pattern:

```python
token = secrets.token_urlsafe(32)
token_hash = hmac_sha256(secret_pepper, token)
```

Lookup by hash, not raw token.

---

## File Security

Current behavior:

- Files are saved to local media storage.
- URLs are returned directly.
- Django serves media when `DEBUG=True`.

Production target:

- Private object storage.
- File access through signed URLs or a permission-checked proxy.
- Upload size limits.
- File signature validation.
- Malware scanning.
- Safe content-disposition headers.
- No public bucket access.

---

## Logging and Audit

Logs should contain:

- request ID
- actor user ID
- action name
- object type and ID
- outcome
- latency
- IP and user agent where appropriate

Logs should not contain:

- share tokens
- JWTs
- passwords
- raw PHI
- full RAG questions/answers unless explicitly routed to a PHI-compliant audit store

Recommended audit events:

- user login success/failure
- record upload
- record download/view
- share token creation/revocation/access
- access request create/approve/decline
- grant create/revoke
- appointment create/update/cancel/confirm
- RAG query
- RAG reindex
- admin action

---

## Configuration Security

Current gaps:

- `SECRET_KEY` hardcoded.
- `DEBUG=True`.
- default database password in settings and compose.
- RAG `JWT_SECRET` fallback hardcoded.

Production requirements:

- Fail startup when required secrets are missing.
- Use strict `ALLOWED_HOSTS`.
- Use strict CORS and CSRF trusted origins.
- Enable HTTPS redirects.
- Enable secure cookies.
- Enable HSTS after HTTPS is confirmed.
- Configure proxy SSL headers behind a load balancer.

---

## Minimum Production Security Checklist

- [ ] No hardcoded secrets.
- [ ] `DEBUG=False`.
- [ ] All PHI endpoints have role and object-level permission tests.
- [ ] Public endpoints are throttled.
- [ ] Share tokens are not logged and are stored hashed.
- [ ] Medical files are private.
- [ ] RAG compare and reindex are locked down.
- [ ] Audit model/table exists.
- [ ] CI includes tests, secret scanning, and dependency audit.
- [ ] Backups and logs are encrypted and access-controlled.
