# Privacy inventory

This scaffold processes synthetic examples locally during tests. The API exposes liveness and documentation. Proposed retention below follows the TRD and requires approval before collecting submissions. The product owner is responsible for confirming the legal controller, hosting region, subprocessors and deletion evidence before pilot intake.

| Fields | Purpose / recipient | Proposed retention and deletion |
|---|---|---|
| Original text, submitted URL, screenshot bytes, decoded OCR/QR | Private assessment by scoped intake and workers in the selected region | Purge transient inputs after processing or the disclosed correction window. Raw media ceiling 24 hours. Delete immediately on accepted erasure through the lifecycle worker. |
| Locale, optional selected country, processing consent | Select guidance and record permission within the assessment | Expire with result. Country is user-selected. Evidence reuse requires a separate opt-in. |
| Opaque session reference, assessment ID, state, redacted findings, policy version | Authorize private result access and explain checks | Guest results 24 hours. Account history defaults to 30 days. Tombstone on deletion and purge linked records. |
| Scoped job reference, request hash, generation | Deduplicate and safely retry within the private data plane | Remove with assessment after outstanding work is invalidated. Keep raw input out of the queue. |
| Optional feedback, redacted evidence, reuse consent | Private review by authorized reviewers | Feedback follows result expiry. Enable reuse only after separate retention terms, consent evidence and withdrawal workflow exist. |
| Categorical durations, errors, request IDs | Operate the service in-region | Content-free security metrics 30 days. Exclude original URLs, message bodies, session tokens and filenames. |
| Encrypted backups, deletion ledger | Disaster recovery under restricted operator access | Backups expire within 30 days. Keep content-free tombstones through the restore horizon and replay before serving restored data. |

External reputation disclosure is disabled. Record the exact approved fields, recipient, region, purpose, license and withdrawal implications before enabling any provider.
