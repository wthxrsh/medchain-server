# Deployment Runbook

#deployment #operations #production #runbook

This runbook describes how MedChain should be prepared and operated in staging/production. The current code needs the hardening items in [[Bugs & Production Readiness]] before handling real patient data.

Related notes: [[Requirements]], [[Security Model]], [[Testing Strategy]], [[RAG Service]], [[System Architecture]]

---

## Environments

Recommended environments:

- Local: developer-only, fake data.
- Test/CI: isolated database, automated tests.
- Staging: production-like, synthetic data.
- Production: real users and protected data.

Each environment should have:

- separate database
- separate object storage bucket/container
- separate secrets
- separate logs/metrics
- separate OAuth client IDs
- separate CORS/host configuration

---

## Pre-Deployment Checklist

Code:

- [ ] All tests pass.
- [ ] Migrations are committed.
- [ ] No pending model changes without migrations.
- [ ] Dependency audit is clean or exceptions are documented.
- [ ] Secret scan is clean.
- [ ] Vault documentation is updated.

Configuration:

- [ ] `DEBUG=False`.
- [ ] `SECRET_KEY` set through secret manager.
- [ ] DB credentials are not defaults.
- [ ] `ALLOWED_HOSTS` contains production domains only.
- [ ] CORS origins are explicit.
- [ ] HTTPS/security settings enabled.
- [ ] Object storage configured.
- [ ] Task queue configured.
- [ ] Logging, metrics, and tracing configured.

Data:

- [ ] Database backup exists.
- [ ] Migration rollback strategy is known.
- [ ] Object storage lifecycle policy is set.
- [ ] Audit log retention policy is set.

---

## Django Deployment Steps

1. Build immutable application artifact/container.
2. Inject environment variables/secrets.
3. Run `python manage.py check --deploy`.
4. Run migrations:

```bash
python manage.py migrate --noinput
```

5. Collect static files if serving Django static assets:

```bash
python manage.py collectstatic --noinput
```

6. Start app server:

```bash
gunicorn medchain_backend.wsgi:application
```

7. Verify health endpoint or smoke endpoints.
8. Verify login and protected endpoint access.

Note:

- The project does not currently define a dedicated health endpoint for Django. Add one before production.

---

## RAG Deployment Steps

1. Build RAG service artifact/container.
2. Inject RAG secrets and model configuration.
3. Verify JWT secret/public-key configuration matches Django.
4. Start app server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

5. Verify:

```bash
GET /api/v1/health
```

6. Run reindex through admin/service workflow only.
7. Verify patient-scoped query with synthetic user.

Production note:

- Do not expose `/reindex` to ordinary authenticated users.
- Consider disabling `/compare` until authorization is fixed.

---

## Background Worker Deployment

Current code uses daemon threads for blockchain simulation. Production target:

- Redis or RabbitMQ broker.
- Celery/RQ/Dramatiq worker.
- Separate worker deployment.
- Retry policy and dead-letter handling.

Minimum worker health checks:

- broker reachable
- worker heartbeat
- job failure rate
- stuck `PENDING` blockchain transactions

---

## Database Operations

Backup:

- automated daily backups
- point-in-time recovery where available
- restore test at least monthly

Migrations:

- run in maintenance window for risky schema changes
- use backward-compatible migrations when possible
- avoid long locks on large tables

Monitoring:

- connection count
- slow queries
- lock waits
- storage usage
- replication lag if using replicas

---

## Object Storage Operations

Production requirements:

- private bucket/container
- server-side encryption
- no public ACLs
- lifecycle rules
- access logs
- signed URLs or proxy streaming only

Recommended metadata:

- patient/user ID
- record ID
- content type
- byte size
- hash
- scan status

---

## Incident Runbooks

### Share Token Exposure

1. Revoke affected token(s).
2. Search logs for token access events.
3. Identify accessed records.
4. Notify required stakeholders according to policy.
5. Rotate logging filters if exposure came from app logs.
6. Add regression test.

### Stuck Blockchain Transactions

1. Query transactions in `PENDING` beyond expected SLA.
2. Check worker/broker status.
3. Retry idempotently.
4. Mark permanent failures with `FAILED` and `last_error`.
5. Alert engineering if failure rate exceeds threshold.

### Unauthorized PHI Access

1. Disable affected account/session/token.
2. Preserve audit logs.
3. Identify accessed records and timeframe.
4. Patch authorization gap.
5. Add regression test.
6. Follow compliance notification process.

### RAG Index Corruption

1. Stop reindex jobs.
2. Restore last known-good index version.
3. Validate source counts and metadata.
4. Rebuild in staging.
5. Promote fixed index.

---

## Go-Live Criteria

- Security checklist in [[Security Model]] complete.
- Critical and high issues in [[Bugs & Production Readiness]] resolved or explicitly accepted.
- Tests in [[Testing Strategy]] implemented for auth/sharing/RAG access.
- Production settings pass `manage.py check --deploy`.
- Monitoring and alerting are live.
- Backup and restore have been tested.
- Incident runbooks are approved.
