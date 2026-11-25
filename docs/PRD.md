# ProofSentry — Product Requirements Document (PRD)
**Version:** 0.1 | **Status:** Proposed baseline | **Date:** 2026-11-25  
**Companion documents:** [TRD](TRD.md) · [System design](SYSTEM_DESIGN.md)

## 1. Product vision
Reduce the human vulnerability exploited by scams, fraud, phishing, impersonation, social engineering and manipulated media. ProofSentry is an international, privacy-first decision-support service that helps people verify suspicious content **before** paying, clicking, sharing credentials or trusting a claimed identity. It does not certify truth, guarantee safety, replace authorities or determine criminal liability.

**Core loop:** encounter suspicious content → submit or share it → inspect evidence → understand uncertainty → take a safe next action → optionally report or revisit.

## 2. Users and jobs to be done
| Persona | Need |
|---|---|
| Everyday consumer | Check a message, offer, payment request, link or QR code before acting. |
| Older adult / low digital literacy | Understand a warning and the next step in plain language. |
| Family member or caregiver | Help a relative verify a suspected impersonation without covert monitoring. |
| Job seeker / shopper / traveler | Check suspicious employment, marketplace, investment and travel offers. |
| Small business employee | Triage invoice, supplier and executive impersonation attempts. |
| Trust and safety team (later) | Integrate consented risk assessments and evidence into existing workflows. |

## 3. Scope and priorities
P0 = public MVP release blocker; P1 = expansion; P2 = dependent on validation/partners.

| ID | Priority | Requirement / acceptance |
|---|---|---|
| P-01 | P0 | Guest can paste text, submit a URL, or upload a screenshot/image from a responsive website. Unsupported types, size and invalid input are explained without losing the draft. |
| P-02 | P0 | Text analysis identifies potential impersonation, urgency, requests for credentials/payment, advance fees, suspicious instructions and context gaps; shows evidence spans where safe. |
| P-03 | P0 | URL inspection normalizes internationalized domains, detects deceptive hostnames and checks licensed reputation sources if available. Unknown URLs are not treated as safe; user is not directed to an unsafe live link. |
| P-04 | P0 | Screenshot OCR and QR extraction feed the same text/URL pipeline. Users can correct OCR before assessment. QR destinations are displayed as inert text. |
| P-05 | P0 | Unified assessment displays concern level (high/elevated/limited/inconclusive), evidence, checks performed/unavailable, limitations and concrete next actions; no uncalibrated probability or “verified safe” badge. |
| P-06 | P0 | Detect likely submission language; offer English, Urdu and Roman Urdu as pilot languages, with explicit fallback for unsupported or uncertain languages. RTL and screen-reader support; human review of translated warnings. |
| P-07 | P0 | Verification guidance includes independently sourcing official contact details, pausing transfers, protecting credentials, and country-aware reporting routes where maintained. For money already sent or accounts compromised, show urgent recovery steps. |
| P-08 | P0 | Explicit upload notice, minimum retention, deletion, no model training on submissions by default, no public listing of submitted content. Guest access is rate limited; login is optional for history. |
| P-09 | P0 | User can mark a result helpful/incorrect, request deletion, and opt in separately to submitting redacted evidence for improvement. No public accusation generated from unverified reports. |
| P-10 | P0 | Media uploads show observable signals and provenance status where supported; no authenticity verdict based only on OCR, metadata or a single detector. Unsupported audio/video explicitly deferred. |
| P-11 | P1 | Optional mobile share target, browser extension and native apps with minimal permissions, no background monitoring by default. |
| P-12 | P1 | Audio/video manipulation screening using evaluated detectors and provenance, with source, quality, domain shift and limitations visible; independent verification remains necessary. |
| P-13 | P1 | Business/merchant verification using official registry links, domain history, licensed review sources, evidence attribution, disputes and correction workflow. No scraped personal dossier or automatic public blacklist. |
| P-14 | P1 | Community reports and campaign clustering using moderated, redacted, evidence-backed signals; prevent brigading, duplicate votes and retaliation. |
| P-15 | P2 | Opt-in family protection, enterprise API, email gateway and partner integrations; require separate security, permission and compliance review. |

### Non-goals for MVP
Automatic blocking of transactions, monitoring private messages, facial identification, voice identity verification, public suspect lists, identity guarantees, money recovery services, or a universally accurate deepfake detector. Do not collect bank credentials, OTPs, seed phrases or government IDs.

## 4. Experience and decision policy
1. Select submission type and paste/upload. Show privacy notice and optional local redaction.
2. Validate input; show progress, cancel and fallback if a detector times out.
3. Present recommendation first (e.g. “Do not pay yet; verify through a separately sourced number”). Show concern category, not a verdict about a person or business.
4. Explain evidence in plain language; expandable technical details include source, timestamp, coverage and uncertainty. No clickable malicious URLs.
5. Offer localized recovery/reporting steps, opt-in feedback and deletion.

| Concern | Meaning | Default action |
|---|---|---|
| High | Strong, independently supported harmful indicators or applicable confirmed reputation evidence | Avoid interaction, verify independently, report if appropriate |
| Elevated | Credible warning signs or conflicting evidence | Pause and investigate |
| Limited | Completed checks found limited concern; coverage may be incomplete | Still verify before sensitive actions |
| Inconclusive | Insufficient, unsupported, unavailable or conflicting evidence prevents a useful conclusion | Do not rely on assessment; verify independently |

A claim of authenticity is never inferred from missing evidence, absent provenance, HTTPS or an LLM's confidence. Explicitly distinguish facts, heuristics, external reports and model estimates.

## 5. Internationalization and accessibility
Global architecture from day one; initial coverage limited to evaluated languages and countries. Pilot English and Pakistan-oriented Urdu/Roman Urdu; English-language guidance is global and country-specific resources are activated only after review. Next locales selected by demand, scam prevalence and qualified reviewers. Store BCP-47 locale and user-selected country independently; no mandatory geolocation. Handle Unicode, RTL, transliteration, currencies, phone formats and mixed languages. Target WCAG 2.2 AA; test keyboard, contrast, labels, screen-reader announcements and low-bandwidth mobile experience. Do not imply all jurisdictions have the same reporting rules.

## 6. Success metrics and launch gates
Proposed targets, to be measured on a versioned independent test set before marketing claims:
- High-concern precision ≥ 95% and harmful-sample recall ≥ 80% on supported text/URL strata; report 95% intervals, per-language/campaign breakdown and sample sizes. No launch for unsupported or failing strata.
- Benign false-high rate ≤ 2%; track false negatives, abstention, coverage, source freshness and calibration separately. Hold out entire scam campaigns and later time windows.
- ≥ 90% of representative usability participants correctly understand recommended action and that limited concern is not a safety guarantee; include older/low-literacy users.
- p95 ≤ 5 s text and ≤ 15 s screenshot/URL under defined pilot load (see TRD); ≥ 99.5% monthly availability target.
- 100% of security-critical acceptance cases pass; no open critical/high security findings; deletion and retention verified.
- Track optional self-reported avoided risky actions, not claimed losses prevented; avoid treating submitted cases as representative of global prevalence.

## 7. Business model and rollout
Free guest core checks with fair-use quotas; no ads or paywall on essential warnings or recovery guidance. Future paid convenience features: higher limits, consented family seats, enterprise/API integrations. No selling submission data or paid risk-ranking improvements. 
- Phase 0: threat model, privacy/data inventory, licensed source selection, datasets and evaluation harness.
- Phase 1: web text/URL checks, evidence policy, multilingual UI.
- Phase 2: screenshot OCR/QR, feedback/deletion, closed pilot; release only after gates.
- Phase 3: mobile/extension, evaluated media screening and business verification.
- Phase 4: moderated reports, partner integrations and scaling.

## 8. Product risks and mitigations
False reassurance → conservative abstention, independent verification and subgroup tests. False accusation → private factual evidence, no public lists, appeals. Malicious uploads/links → sandboxing, no active navigation. Adversarial drift → temporal holdouts, source freshness, rollback. Sensitive data → minimization, consent, short retention and redaction. Abuse by scammers optimizing against the tool → rate limits, no exposed detector thresholds or bypass advice. Vendor outages/cost → quotas, fallback and transparent coverage. Local regulatory variation → country rollout review.

## 9. Open decisions
Pilot budget and traffic; source licenses and commercial terms; exact retention after jurisdictional review; qualified localization reviewers; operating entity and applicable law; final model/dataset selection after benchmark. No compliance or detection-performance claims until validated. Product owner approves scope changes and launch gates.
