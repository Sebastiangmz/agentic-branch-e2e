# Example: Web UI Run Record

## Summary

- Branch: `feat/refund-approval`
- Base: `main`
- Source of truth: GitHub issue #42
- App entrypoint: `http://localhost:3000/admin/refunds`
- Overall verdict: `PASS`

## Project profile

- Runtime: Node 22, pnpm workspace
- Services started: web, api, postgres
- Browser adapter: Playwright-capable browser driver
- Auth gate: admin login with seeded local admin
- Temporary edits: none

## Scope classification

- In-scope: refund approval UI, `POST /api/refunds/:id/approve`, audit-row persistence.
- Inferred-support: seeded admin account and pending refund fixture.
- Out-of-scope: none observed in the branch diff.

## Frozen criteria

### C1 — Admin can approve a pending refund

- Source: explicit issue criterion
- Production path: browser UI → session auth → `POST /api/refunds/:id/approve` → request validation → refund service → audit writer → postgres
- Drive plan: sign in as seeded admin, open pending refund, click Approve, confirm modal, observe success state, verify persisted refund status and audit row.

Evidence:

- UI: `artifacts/c1-after-approve.png`, DOM excerpt shows `Refund approved`
- Network: `artifacts/c1-approve.har`, `POST /api/refunds/ref_123/approve` returned 200
- Logs: `artifacts/api.log#12-35`, no errors or warnings during action window
- Backend state: `artifacts/c1-db.txt`, `refunds.status = approved`, `audit_events.action = refund.approved`
- Errors: browser console captured, no errors or unhandled rejections

Assertions:

- Strong: refund status changed to approved and audit row was written.
- Weak: no duplicate audit row, no console errors, no failed network calls, no unrelated refund row changed.

Fidelity gaps: none.

Verdict: `PASS`

Reason: Requested UI action completed through the real browser and API route, persisted the expected backend state, and produced clean signals.

## Negative cases

### N1 — Non-admin cannot approve refund

- Criterion: C1
- Expected: action unavailable or rejected with 403; no state change.
- Observed: approve button hidden for support user; direct request returned 403; refund remained pending.
- Evidence: `artifacts/n1-ui.png`, `artifacts/n1-response.txt`, `artifacts/n1-db.txt`
- Verdict: `PASS`

### N2 — Double-click approval does not create duplicate audit rows

- Criterion: C1
- Expected: one approval, one audit row.
- Observed: second click disabled while request in flight; one audit row exists.
- Evidence: `artifacts/n2-network.har`, `artifacts/n2-db.txt`
- Verdict: `PASS`

## Overall verdict

`PASS` — every criterion and negative case passed, no fidelity gaps were recorded, and teardown left the tree clean.

## Teardown

- Services stopped: web, api, postgres
- Temporary edits reverted: none
- Working tree status: clean

## Not covered

- Merge readiness, CI, and review-thread status were not checked by this run.
