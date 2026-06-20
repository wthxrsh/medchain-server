# MedChain Knowledge Vault

#index #medchain #backend #documentation

This Obsidian vault is the project handbook for the MedChain backend and RAG service. It documents what exists now, the implementation details that matter, and the work required to make the project production-grade.

---

## Start Here

- [[System Architecture]] - service boundaries, core flows, and production target architecture.
- [[Implementation Guide]] - how the code is implemented and how to extend it safely.
- [[Project Roadmap & Workflow]] - full project plan from current MVP to decentralized production platform.
- [[Bugs & Production Readiness]] - current bugs, risks, suggested fixes, and roadmap.

---

## Reference

- [[Directory & Modules Map]] - repo layout and module ownership.
- [[Database Schema]] - Django models, fields, relationships, and data integrity notes.
- [[API Endpoints]] - current Django and FastAPI HTTP endpoints with examples.
- [[Requirements]] - runtime, environment, functional, and production requirements.
- [[Local Development Guide]] - local setup for Django, PostgreSQL, and RAG.

---

## Security and Operations

- [[Security Model]] - auth, authorization, token handling, file security, audit, and production checklist.
- [[Testing Strategy]] - current test gaps, required regression tests, and CI plan.
- [[Deployment Runbook]] - environment, deployment, incident, and go-live procedures.
- [[RAG Service]] - FastAPI RAG pipeline, indexing, query flow, config, and risks.

---

## Current Production Readiness Snapshot

Critical blockers:

- Hardcoded Django and RAG secrets.
- `DEBUG=True`.
- RAG compare endpoint can retrieve arbitrary patient IDs.
- Share tokens are logged in plaintext.
- Grant model suggests selected-record access but current reads return all records.

High-priority blockers:

- No API throttling.
- Local media storage for medical files.
- Background blockchain work uses daemon threads.
- Default database credentials.
- RAG reindex is not admin-only.

See [[Bugs & Production Readiness]] for details and suggested implementation order.

---

## Recommended Reading Paths

For a new developer:

1. [[Directory & Modules Map]]
2. [[System Architecture]]
3. [[Local Development Guide]]
4. [[API Endpoints]]
5. [[Implementation Guide]]

For production hardening:

1. [[Bugs & Production Readiness]]
2. [[Project Roadmap & Workflow]]
3. [[Security Model]]
4. [[Testing Strategy]]
5. [[Deployment Runbook]]
6. [[RAG Service]]

For decentralized blockchain implementation:

1. [[Project Roadmap & Workflow]]
2. [[System Architecture]]
3. [[Security Model]]
4. [[Implementation Guide]]
5. [[Bugs & Production Readiness]]

For API/frontend integration:

1. [[API Endpoints]]
2. [[Database Schema]]
3. [[Security Model]]

---

## Quick Tags

#architecture #api #database #django #fastapi #rag #security #testing #deployment #production #records #sharing #appointments #blockchain

---

Created: 2026-06-20
Last updated: 2026-06-20
