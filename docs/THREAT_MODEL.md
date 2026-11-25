# Threat model

The API exposes liveness, documentation and guest sessions. Local synthetic assessment creation requires explicit enablement. The following gates apply as each boundary becomes reachable.

| Boundary and asset | Failure | Control and verification |
|---|---|---|
| Browser → API, private assessment | Client supplies another owner or reads another result | Reject undeclared intake fields (tested). Creation derives scope from the session. Status reads return identical responses for absent and foreign IDs (tested). |
| Submission → detector, network and credentials | Submitted link triggers outbound traffic or hostile text changes worker behavior | Current intake uses local parsing only. Before detectors ship, run workers with denied egress, inert outputs and no tools. Test with outbound access disabled. |
| Upload → decoder, worker availability | Excessive dimensions or malformed media exhaust resources | Gate multipart intake on quarantine, byte/pixel/deadline budgets, isolated decoding and cleanup tests using synthetic media. |
| Provider → policy, result integrity | Stale or unavailable evidence produces reassurance | Require source/version/freshness, validate typed outputs and exercise failure and incomplete coverage before publishing results. |
| Job → storage, erasure | A retry republishes a deleted record | Creation commits owner-bound idempotency, input, job and outbox together. Gate worker publication on tombstones and a delete/retry race test. |
| API → telemetry, submitted secrets | Validation errors, access logs or traces expose input | Intake returns generic validation errors (tested with synthetic identifiers). Local service access logging is disabled. Verify deployed logs and traces before pilot rollout. |
| CI → build, supply chain | Unreviewed dependency or privileged job alters artifacts | Pin Python dependencies and action revisions. CI has read-only repository access. Require image digest review, vulnerability and secret scans before deployment. |

Service owner reviews changes to these boundaries. Provider credentials, media handling and external data disclosure require separate implementation review before activation.
