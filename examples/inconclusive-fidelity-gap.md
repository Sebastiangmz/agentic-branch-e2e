# Example: INCONCLUSIVE Fidelity Gap

## Summary

- Branch: `feat/invite-validation`
- Base: `main`
- Source of truth: user request
- App entrypoint: intended `POST /api/invites`
- Overall verdict: `INCONCLUSIVE`

## Project profile

- Runtime: Node API with browser UI
- Services attempted: web, api
- Browser adapter: unavailable because app startup halted before UI loaded
- HTTP adapter: unavailable because route depended on missing auth emulator
- Missing prerequisite: project-supported auth provider emulator


## Frozen criteria

### C1 — Creating an invite rejects non-company email domains

- Source: explicit user request
- Production path intended: browser UI → session auth → `POST /api/invites` → request schema validation → invite service → email queue → database
- Production path exercised: invite service → database
- Drive plan attempted: open invite UI and submit `person@gmail.com` as an admin.

Evidence:

- UI: not captured; local app could not start because the auth provider emulator was missing.
- Network: not captured for `POST /api/invites`.
- Logs: `artifacts/startup.log#18-24`, auth emulator connection refused.
- Backend state: `artifacts/service-unit-output.txt`, direct service call rejected gmail domain.
- Errors: startup error in auth emulator dependency.

Assertions:

- Strong: non-company domain should be rejected through the real route.
- Observed: non-company domain was rejected only when calling the internal service directly.

Fidelity gaps:

- Browser UI not exercised.
- Session auth not exercised.
- HTTP route not exercised.
- Request schema validation not exercised.
- Serialization/parsing not exercised.
- Email queue not exercised.

Verdict: `INCONCLUSIVE`

Reason: The direct service call suggests the domain rule exists, but the real ingress path was not exercised. The skipped route and validation layers are exactly where malformed payloads, missing auth, or changed schema contracts can regress.

## Negative cases

### N1 — Gmail invite is rejected

- Criterion: C1
- Expected: UI/route rejects request with a user-visible error and no invite row.
- Observed: internal service rejected the email; route/UI not reached.
- Evidence: `artifacts/service-unit-output.txt`
- Verdict: `INCONCLUSIVE`

## Overall verdict

`INCONCLUSIVE` — no criterion failed, but the required production path was bypassed. A PASS would be false confidence.

## Required next action

Start or mock the auth provider through the project-supported local mechanism, then rerun C1 from the browser UI or real HTTP route. Do not reuse the internal service call as proof.

## Teardown

- Services stopped: api process
- Temporary edits reverted: none
- Working tree status: clean
