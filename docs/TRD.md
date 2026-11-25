# ProofSentry — Technical Requirements Document (TRD)
**Version:** 0.1 | **Status:** Proposed baseline | **Date:** 2026-11-25  
**Product:** [PRD](PRD.md) · **Architecture:** [System design](SYSTEM_DESIGN.md)

## 1. Technical objectives and constraints
Deliver a secure, low-cost, multilingual risk assessment web application. Untrusted input must never acquire network, execution, prompt or administrative privileges. Findings are evidence-backed, reproducible against pinned versions and independently verifiable. External source, model and dataset selection is provisional until licensing, privacy, security and evaluation pass. Build with a modular monolith and isolated workers before microservices.

## 2. Stack and interfaces
| Layer | Proposed choice | Rationale / constraint |
|---|---|---|
| Web | Next.js, TypeScript, Tailwind, accessible components | Responsive installable web app, locale routing, RTL |
| API | Python, FastAPI, Pydantic, OpenAPI | Typed interfaces and ML ecosystem |
| Database | PostgreSQL, SQLAlchemy, Alembic | Transactional lifecycle, versioned evidence, tenant isolation |
| Queue | Redis + Celery | Bounded async workloads, idempotent tasks; DB outbox is authoritative |
| Objects | Private S3-compatible storage | Quarantine and encrypted temporary media; signed internal access |
| ML | CPU-first rules, OCR (Tesseract/PaddleOCR candidates), QR decoder, evaluated compact multilingual model; optional LLM | Model adapters with no direct tools; benchmark before selection |
| Infra | Docker, GitHub Actions; managed cloud containers/DB/storage; GCP candidate | Separate environments; no production credentials in CI; infrastructure as code |
| Observability | OpenTelemetry, structured redacted logs, metrics and alerts | Never log content, full URLs, tokens, secrets or raw uploads |

Pin supported dependency versions and container digests during implementation; no arbitrary latest versions or vendor commitments. No GPU required for initial text/URL workflow; measure OCR needs.

## 3. Functional requirements and traceability
| ID | PRD | Requirement and acceptance |
|---|---|---|
| T-01 | P-01 | Validate typed submissions; text ≤ 20,000 Unicode characters, URL ≤ 4,096 characters, image ≤ 10 MiB and ≤ 20 MP; reject archive/executable/polyglot or mismatched magic bytes; enforce limits at edge and worker. |
| T-02 | P-02 | Normalize text without destroying original offsets; language detection, deterministic indicators, model adapter with schema-constrained output; no user instruction execution; evidence spans map to original or corrected OCR text. |
| T-03 | P-03 | Parse only HTTP(S); canonicalize IDNA and display both Unicode and ASCII host; flag mixed scripts, deceptive subdomains, IP literals and ambiguous URLs; strip credentials and redact sensitive query/fragment values. Reputation provider lookup only with allowed disclosure and license; no arbitrary URL fetching in MVP. |
| T-04 | P-04 | Isolated OCR/QR workers with no egress, bounded resources and safe decode/re-encode; inert QR result, user correction flow; treat OCR and QR content as hostile. |
| T-05 | P-05 | Deterministic policy combines typed findings; record severity, source, version, timestamp, coverage and conflicts; provider errors or unsupported inputs cannot produce limited concern. Only completed required checks may yield limited concern. |
| T-06 | P-06/07 | BCP-47 locale and separately selected country; versioned localized action templates and reviewed official resource directory with last verification date; missing locale/country uses explicit generic fallback. |
| T-07 | P-08 | Guest session via opaque secure cookie; optional OIDC for account history; server-side ownership check for every object; lifecycle deletion cascade, raw media TTL and guest expiry. |
| T-08 | P-09 | Record feedback without public publication; separate consent for redacted evidence reuse; rate limit, deduplicate and review before promotion to dataset. |
| T-09 | P-10/12 | Inspect image metadata/provenance only if supported; validation state distinct from authenticity; adapter for later audio/video detectors, disabled until evaluation. |
| T-10 | P-11/13–15 | Stable versioned interfaces; feature flags and permissions for future share targets, registries, reports and partners. Not part of MVP acceptance. |

## 4. API contract (v1)
All endpoints use TLS, JSON except multipart upload, standard request IDs and RFC 9457-style problem responses. Authorization scope is derived from server session, never supplied by client. No endpoint exposes other users' assessments.

| Method and path | Semantics |
|---|---|
| POST /v1/assessments | JSON text/URL or multipart image + locale/country/consent; 202 with opaque assessment_id, status and poll interval; Idempotency-Key scoped to owner and request hash |
| GET /v1/assessments/{id} | 200 status, findings, coverage and action templates when ready; 404 for absent/unauthorized |
| POST /v1/assessments/{id}/corrections | Validate OCR correction; create new assessment revision with linked parent; never mutate original evidence |
| POST /v1/assessments/{id}/cancel | Cancel queued work or prevent publishing results after cancellation; idempotent |
| DELETE /v1/assessments/{id} | 202 deletion requested; tombstone immediately denies access, queue cleanup; idempotent |
| GET /v1/deletions/{id} | Owner-scoped deletion status without content |
| POST /v1/assessments/{id}/feedback | Feedback plus separate opt-in flag; rate limited |
| GET /v1/resources?country=…&locale=… | Reviewed reporting/recovery links, version and freshness; generic fallback |

Common response fields: assessment_id, status (queued/running/completed/partial/failed/canceled/deleting/deleted), concern (high/elevated/limited/inconclusive/null), findings[], checks[], recommended_actions[], policy_version, generated_at, expires_at. Finding fields: code, severity, evidence_kind, redacted_excerpt, span, source_ref, observed_at, detector_version, limitations. Check states: completed, unavailable, unsupported, skipped, failed. No numerical confidence shown unless later validated. 400 invalid syntax, 413 too large, 415 unsupported media, 422 validation, 429 quota, 503 service unavailable. Poll with bounded exponential backoff; return Retry-After where applicable.

## 5. Data, retention and privacy
Proposed policy pending legal review: guest results 24 h, raw media at most 24 h (delete earlier after processing), account result history 30 days by default, content-free security metrics 30 days, encrypted backup expiry ≤ 30 days. Redacted opt-in training evidence requires separate retention notice and consent record; withdrawal stops future reuse and removes deletable dataset records; do not promise reversal of already trained models. Data inventory tracks controller, purpose, region, recipient and TTL per field. Delete transient text and OCR artifacts after assessment/short correction window; stored results contain only necessary redacted excerpts. Backup restoration must reapply deletion ledger before serving traffic. Enforce no public buckets; encryption at rest/in transit; per-environment secret manager. Avoid cross-border data transfer until appropriate terms and rollout review; never send raw messages to external vendors by default.

## 6. Non-functional requirements
| Dimension | Proposed acceptance |
|---|---|
| Performance | At pilot workload 10 concurrent users, 1 submitted check/s sustained for 15 min, mixed 60% text/25% URL/15% image: p95 end-to-end ≤ 5 s text, ≤ 15 s URL/image; track incomplete results separately; ≤ 30 s hard processing deadline. |
| Availability | ≥ 99.5% monthly service SLO; provider outages degrade to explicit partial/inconclusive, not fabricated findings. |
| Capacity | Bounded upload/worker concurrency, per-owner quotas, queue depth caps and backpressure; initial guest quota 10 checks/day subject to pilot tuning; global provider budget cap. |
| Reliability | At-least-once delivery, deduplication, monotonic state transitions, max two bounded retries for transient failures, dead-letter handling and restart recovery. |
| Disaster recovery | Pilot RPO ≤ 24 h/RTO ≤ 4 h; quarterly restore exercise; validate deletion replay. |
| Accessibility | WCAG 2.2 AA target; keyboard, screen reader, RTL, low-bandwidth and mobile tests. |
| Security | No critical/high open findings; dependency, secret, static and container scans; least privilege and explicit egress deny policy. |
| Cost | Measure cost per completed check and per detector; establish approved monthly cap before public launch; graceful budget exhaustion, never silently skip required checks. |

## 7. Threat model and controls
Assets: submissions, identity/session, private findings, provider credentials, evidence/policy integrity, reports, reputation and service availability. Adversaries: scam operators probing detectors, hostile uploads, abusive reporters, malicious external content and compromised dependencies/vendors.
- SSRF: no direct fetch in MVP; any future fetcher requires separate egress-only sandbox, DNS pinning, deny private/link-local/metadata and reserved IPs, revalidation of redirects and strict budgets.
- Prompt injection: inputs and provider text treated as data; no model tools, credentials or arbitrary outbound calls; validated schemas, output escaping, policy-owned actions and failure fallback.
- File attacks: quarantine, magic/size/pixel limits, scan, sandbox with read-only image, CPU/memory/time caps, no network, safe conversion and purge.
- XSS/CSRF/IDOR: render inert text, CSP, secure HttpOnly SameSite cookies, CSRF/origin controls, opaque IDs and ownership checks; test cross-account access.
- Poisoning and harassment: source allowlist, versioned signed/config-controlled policy, moderation, no public accusation, appeal/correction workflow.
- Abuse and cost: rate limits, bounded queue, request size limits, provider circuit breakers, no disclosure of exact detector thresholds or adversarial bypass hints.
- Operational security: RBAC, MFA for administrators, audited privileged actions without content, key rotation, backup access controls, incident playbook.

## 8. Model and evidence quality
Build versioned labeled datasets from permissioned/synthetic sources with benign near-misses and multiple languages. Split by campaign, entity and time to avoid leakage; adjudicate disagreements, measure subgroup confidence intervals. Pin detector/prompt/policy and dataset versions; record model and external evidence lineage. Evaluate precision, recall, false-high rate, abstention, calibration if applicable, coverage, latency and cost. Use adversarial cases (Unicode spoofing, obfuscated URLs, multilingual social engineering, prompt injection, noisy OCR). Run shadow/challenger comparisons, gated rollout and rollback. Media provenance is optional evidence; absence is inconclusive. No raw data in training unless explicitly consented and reviewed.

## 9. Test and release criteria
- Unit: canonicalization, URL redaction, policy rules, state transitions, retention and source freshness.
- Contract/integration: OpenAPI validation, DB migrations, idempotency, worker crash/retry, provider timeout/rate limits, malformed response, cancel/delete race, locale fallback.
- Security: malicious file fixtures, SSRF parser corpus, XSS/prompt injection, cross-owner access, credential leakage, consent and deletion replay; use harmless test fixtures.
- ML: PRD launch metrics per supported strata; publish model card and evaluation report with coverage/limitations.
- E2E: submit → result → guidance → feedback/delete; OCR correction, guest/account and RTL; verify no unsafe link activation.
- CI: format/lint/typecheck, unit/integration/E2E smoke, dependency and secret scan, container build; staging smoke/load/restore before production. Release checklist requires product, security and privacy approval, no failing mandatory tests, approved budget and operational runbook.

## 10. Implementation sequence
1. Repository scaffolding, threat model, privacy inventory, CI and local compose.
2. Typed contracts, DB migrations, guest session, job outbox, policy engine and test fixtures.
3. Text detector and language handling; URL normalization and licensed provider adapter.
4. Quarantine, OCR/QR, evidence UI, reporting templates and deletion worker.
5. Evaluation harness, adversarial regression, accessibility/load/security checks and closed pilot.
6. After gates: controlled production rollout; P1 adapters only after separate review.

## 11. Open decisions
Provider licensing and quota, benchmark corpora and model choice, budget and cloud region, legal controller/retention rules, launch locale reviewers, account identity vendor. Targets are specifications, not measured results.
