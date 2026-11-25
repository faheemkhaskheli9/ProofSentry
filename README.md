# ProofSentry

International, privacy-first fraud prevention and digital trust decision support.

ProofSentry helps people recognize suspicious messages, links, QR codes, impersonation and potentially manipulated media before taking risky actions. It provides evidence, uncertainty and practical verification guidance—not guarantees of safety or authenticity.

## Project documentation

- [Product Requirements Document](docs/PRD.md)
- [Technical Requirements Document](docs/TRD.md)
- [System Design](docs/SYSTEM_DESIGN.md)

## Status

The local API serves a liveness probe. Draft text and URL contracts and synthetic intake fixtures are available for development. Assessment processing is planned.

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

Read `GET /healthz` on localhost port 8000. Alternatively, run `docker compose up --build --wait` and stop with `docker compose down`. Compose currently runs the API only.

The [draft JSON intake schema](packages/contracts/intake-v1.schema.json) covers text and URL submissions. Runtime validation also checks URL syntax and blank text. Regenerate after model changes with `python -m packages.contracts.schema > packages/contracts/intake-v1.schema.json`. The [synthetic fixtures](evaluation/intake-v1.json) exercise intake acceptance in English, Urdu and Roman Urdu. Detector accuracy requires a separate labeled benchmark.

See the [threat model](docs/THREAT_MODEL.md) and [privacy inventory](docs/PRIVACY_INVENTORY.md) for rollout gates.

## Next milestone

Add PostgreSQL migrations and owner-scoped guest sessions, then connect assessment creation to a transactional job outbox. Add database and queue services to Compose as their consumers land. Follow the [TRD implementation sequence](docs/TRD.md#10-implementation-sequence).
