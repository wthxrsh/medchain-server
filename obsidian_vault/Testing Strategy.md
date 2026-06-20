# Testing Strategy

#testing #qa #ci #security #django #fastapi

This note defines the minimum testing strategy for making MedChain reliable and safe enough for production hardening.

Related notes: [[Implementation Guide]], [[Security Model]], [[API Endpoints]], [[Bugs & Production Readiness]], [[Deployment Runbook]]

---

## Current Test State

Current Django app tests are mostly placeholders:

- `users/tests.py`
- `records/tests.py`
- `sharing/tests.py`
- `appointments/tests.py`
- `blockchain/tests.py`
- `parsing/tests.py`

RAG has a tests folder:

- `medchain-rag/tests/test_clinical_rag.py`
- `medchain-rag/tests/test_db.py`
- `medchain-rag/tests/test_generator.py`
- `medchain-rag/tests/test_ingestion.py`
- `medchain-rag/tests/test_retrieval.py`

Priority should be on authorization, PHI access boundaries, upload validation, and RAG scoping.

---

## Test Pyramid

Unit tests:

- model constraints
- serializers
- permission classes
- token helpers
- RAG chunking/retrieval functions

Integration tests:

- auth flows
- record upload/list/download
- share token lifecycle
- access request approval
- doctor grant record reads
- appointment actions
- RAG query with scoped index

End-to-end smoke tests:

- register/login
- upload record
- generate share link
- approve doctor access
- query RAG

Security regression tests:

- patient cannot read another patient's records
- doctor cannot read without grant
- expired share token fails
- arbitrary RAG compare IDs fail
- non-admin reindex fails

---

## Django Test Priorities

### Auth

Must test:

- register patient succeeds
- duplicate email rejected
- login returns role/user fields
- unknown email error is safe
- Google register/login flow with mocked token verifier
- role assignment rules once hardened
- auth throttling once added

### Records

Must test:

- unauthenticated upload rejected
- authenticated upload saves record and hash
- upload rejects unsupported content type
- patient timeline returns only own records
- file URL is generated only for allowed caller
- doctor record read denied without grant
- doctor record read allowed with grant
- selected-record grant does not expose unselected records once implemented

### Sharing

Must test:

- patient can generate full-vault token
- patient can generate single-record token
- user cannot create token for another user's record
- expired token rejected
- invalid token rejected
- token access does not require auth
- raw token is not logged after logging fix
- patient can approve request addressed to them
- patient cannot approve someone else's request
- non-doctor cannot create doctor access request after role fix

### Appointments

Must test:

- patient can create appointment
- patient sees own appointments only
- doctor sees assigned appointments only
- unauthorized doctor cannot confirm/cancel
- name-collision case is denied after doctor-id refactor
- invalid status transition is rejected

### Blockchain

Must test:

- upload creates `BlockchainTransaction(PENDING)`
- async worker/task marks confirmed on success
- failures are marked failed with error metadata after production refactor
- stuck transaction repair command works after added

---

## RAG Test Priorities

Must test:

- JWT validation rejects missing/invalid/expired token.
- patient query scopes retrieval to JWT `user_id`.
- patient cannot query another patient's chunks.
- doctor role is rejected from patient-only query endpoint.
- `/questions` rejects non-patient users.
- `/reindex` rejects non-admin after fix.
- `/compare` rejects arbitrary patient IDs until grant/admin logic exists.
- missing FAISS index returns safe behavior.
- LLM provider exceptions return safe errors.
- source chunks in response all match authorized patient scope.

Recommended evaluation tests:

- answer cites/reuses retrieved context.
- answer says when records do not contain the answer.
- prompt injection in record text does not override system policy.
- medical disclaimer behavior matches product policy.

---

## CI Pipeline

Minimum CI jobs:

1. Install dependencies.
2. Run formatting/linting.
3. Run Django migrations check.
4. Run Django tests.
5. Run RAG tests.
6. Run dependency vulnerability scan.
7. Run secret scan.

Example commands:

```bash
python manage.py makemigrations --check --dry-run
python manage.py test
cd medchain-rag && pytest
```

Add these after tools are selected:

- Ruff or Flake8
- Black
- Bandit
- pip-audit
- detect-secrets or gitleaks

---

## Test Data Rules

- Use synthetic data only.
- Do not commit real patient files.
- Keep uploaded test fixtures small.
- Use clearly fake names/emails.
- Include at least two patients and two doctors for authorization tests.
- Include negative tests for cross-user access.

---

## Definition of Done for Sensitive Changes

A change touching auth, records, sharing, appointments, RAG, or files is done only when:

- happy path test exists
- denied access test exists
- object-level access test exists
- docs are updated
- logs do not expose sensitive data
- migration exists if model changed
- CI passes
