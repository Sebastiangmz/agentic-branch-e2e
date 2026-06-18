# Example: Backend-only Run Record

## Summary

- Branch: `feat/webhook-signature-rotation`
- Base: `main`
- Source of truth: Linear issue PAY-17
- App entrypoint: `POST http://localhost:8787/webhooks/payment`
- Overall verdict: `PASS`

## Project profile

- Runtime: Cloudflare Worker via local dev server
- Services started: worker, queue emulator, local database
- Browser adapter: not applicable; no browser-visible UI in scope
- HTTP adapter: real local route with HMAC signature and JSON serialization
- Temporary edits: local webhook secret placeholder in ignored env file

## Scope classification

- In-scope: webhook signature rotation accepting active and next secrets.
- Inferred-support: local queue/database fixtures required to observe processing.
- Out-of-scope: none observed in the branch diff.

## Frozen criteria

### C1 — Webhook accepts both active and next signing secrets during rotation

- Source: explicit issue criterion
- Production path: HTTP route → HMAC verification → JSON schema validation → enqueue payment event → queue consumer → database
- Drive plan: send signed webhook once with active secret and once with next secret, then verify accepted responses, enqueued jobs, and persisted payment events.

Evidence:

- Network: `artifacts/c1-active-response.txt`, `artifacts/c1-next-response.txt`, both returned 202
- Logs: `artifacts/worker.log#44-81`, no signature warnings, no schema errors
- Backend state: `artifacts/c1-db.txt`, two payment events persisted with distinct event IDs
- Queue: `artifacts/c1-queue.txt`, both jobs consumed successfully
- Errors: no rejected jobs or server stack traces

Assertions:

- Strong: both valid signatures were accepted and processed through queue to persistence.
- Weak: no duplicate event, no plaintext secret in logs, no 5xx response.

Fidelity gaps: none.

Verdict: `PASS`

Reason: Both accepted secrets were exercised through the real route, signature verifier, queue, consumer, and datastore.

## Negative cases

### N1 — Invalid signature is rejected

- Criterion: C1
- Expected: 401, no queue job, no database row.
- Observed: route returned 401; queue depth unchanged; no row inserted.
- Evidence: `artifacts/n1-response.txt`, `artifacts/n1-queue.txt`, `artifacts/n1-db.txt`
- Verdict: `PASS`

### N2 — Legacy payload missing required id is rejected by schema

- Criterion: C1
- Expected: 400, validation error, no queue job.
- Observed: route returned 400 with user-safe error; no queue job.
- Evidence: `artifacts/n2-response.txt`, `artifacts/n2-log.txt`, `artifacts/n2-queue.txt`
- Verdict: `PASS`

## Overall verdict

`PASS` — backend-only criteria and negative cases were driven through the real HTTP ingress and queue path.

## Teardown

- Services stopped: worker, queue emulator, local database
- Temporary edits reverted: ignored env file removed
- Working tree status: clean

## Not covered

- No browser UI existed for this change.
- Merge readiness, CI, and review-thread status were not checked by this run.
