# ProofSentry

International, privacy-first fraud prevention and digital trust decision support.

ProofSentry helps people recognize suspicious messages, links, QR codes, impersonation and potentially manipulated media before taking risky actions. It provides evidence, uncertainty and practical verification guidance—not guarantees of safety or authenticity.

## Project documentation

- [Product Requirements Document](docs/PRD.md)
- [Technical Requirements Document](docs/TRD.md)
- [System Design](docs/SYSTEM_DESIGN.md)

## Status

The local API serves a liveness probe and PostgreSQL-backed guest sessions. Local text and URL intake can persist private assessments and queue detector jobs. Jobs stay queued until the dispatcher and worker land.

The initial MVP is a responsive web application for text, URL and screenshot checks. Advanced audio/video screening, business verification, mobile integrations and community reporting are subsequent phases, subject to evaluation, privacy and security gates.

## Local development

Use Python 3.12 from the repository root.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -v
python -m uvicorn services.api.main:app --no-access-log
```

Read `GET /healthz` on localhost port 8000. For the session API, set a local `POSTGRES_PASSWORD` and run `docker compose up --build --wait`. Compose applies versioned migrations before starting the API. Stop with `docker compose down`. PostgreSQL data persists in the named volume.

`POST /v1/session` starts or resumes a 24-hour guest session. `GET /v1/session` returns its expiry. Browser clients use a Secure, HttpOnly, SameSite=Strict cookie. Configure `PUBLIC_ORIGIN` to the exact browser origin and use HTTPS outside loopback development. Expired tokens immediately lose access. New sessions also prune batches of expired rows.

For standalone development, set `DATABASE_URL` and run `python -m services.db.migrate` before using sessions. To include database integration tests, install `httpx==0.28.1` and point `TEST_DATABASE_URL` at a disposable PostgreSQL database.

For local synthetic submissions, set `ENABLE_ASSESSMENT_INTAKE=1` before starting the API. With an active guest cookie, send JSON to `POST /v1/assessments` and supply an `Idempotency-Key` header (1–128 letters, digits, dots, underscores or hyphens). A successful request returns HTTP 202 with an assessment ID. Poll `GET /v1/assessments/{assessment_id}` with the same session. Each 24-hour guest session accepts ten distinct assessments. Matching retries reuse the original assessment, and conflicting key reuse returns HTTP 409.

The [draft JSON intake schema](packages/contracts/intake-v1.schema.json) covers text and URL submissions. Runtime validation also checks URL syntax and blank text. Regenerate after model changes with `python -m packages.contracts.schema > packages/contracts/intake-v1.schema.json`. The [synthetic fixtures](evaluation/intake-v1.json) exercise intake acceptance in English, Urdu and Roman Urdu. Detector accuracy requires a separate labeled benchmark.

See the [threat model](docs/THREAT_MODEL.md) and [privacy inventory](docs/PRIVACY_INVENTORY.md) for rollout gates.

## Next milestone

Implement the outbox dispatcher and first worker with retry-safe job claiming. Add the queue service alongside its consumer. Follow the [TRD implementation sequence](docs/TRD.md#10-implementation-sequence).
