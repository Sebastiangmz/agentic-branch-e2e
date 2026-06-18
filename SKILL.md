---
name: agentic-branch-e2e
description: "Use when the user asks to end-to-end test a feature branch as a real user in a running app, to verify a branch fulfills its purpose, or to bug-hunt a branch in the live UI + backend. The skill is stack-agnostic and project-agnostic — it inspects the project (manifest, scripts, services, runtime), then drives the running app as a user would while monitoring every observable signal (UI state, network, backend state, logs, errors), asserting the branch actually delivers the requested work and nothing else. Always-on when triggered: do not silently pass a 'the flow walks' check — derive a real correctness verdict per acceptance criterion AND attempt to break the change with inferred negative cases."
version: 1.1.0
author: Chenko
license: MIT
metadata:
  hermes:
    tags: [e2e, testing, browser, qa, bug-hunting, verification, branch-verification, full-stack]
    related_skills: [playwright, github-pr-workflow, requesting-code-review, systematic-debugging]
---

# Agentic Branch E2E (stack-agnostic)

## What this gives you

A **real, user-level end-to-end test of a feature branch running locally**, with a **bug-hunter
posture**: the agent stands up the project from source on the current branch, drives the running
app exactly as a real user would, watches every observable signal (UI, network, backend, logs,
errors), and decides — per acceptance criterion, not per happy-path walk — whether the branch
delivers the requested work and nothing else. The skill is **stack-agnostic and project-agnostic**:
it inspects the project to discover the manifest, scripts, runtime, services and how to start them,
and adapts. It deliberately refuses the easy "the flow walks without errors" verdict.

Use this to prove a branch is correct before merging, when unit tests are not enough, when the
user/reviewer wants proof in the running app, or when past runs of naive E2E have been observed
to mask real defects.

## When to use / when NOT

USE when:
- The user asks to "test this branch", "run an E2E", "verify it works in the real app",
  "test as a user", "click through the flow", "prove it works", "bug-hunt this branch".
- The user/reviewer wants visual + backend proof the requested issue/feature is delivered
  correctly, including attempts to break it.
- A naive E2E previously passed but the user found real defects afterwards.

Do NOT use when:
- A unit/integration test already covers the behavior in-process — prefer that, it's faster and
  runs in CI. This skill is for the *running-app* proof on top of unit tests.
- The change is documentation-only, config-only with no runtime effect, or infra-only with no
  user-visible surface to drive.
- The user only wants the backend exercised and no UI exists or is in scope — fall back to the
  *Backend-only mode* at the end of this file.

## What "anti-mask" means in this skill

A naive E2E asks "did the flow walk end-to-end without exceptions?" and calls that a pass. This
skill rejects that verdict. The real questions are:

1. **Did the branch actually deliver the requested work?** Per acceptance criterion, does the
   live behavior match what was asked? A walk that returns 200 but doesn't perform the requested
   action is a fail.
2. **Did the branch do ONLY the requested work?** Scope creep — features, fields, endpoints,
   UI elements not in the issue — is a fail (or at least a gate that requires explicit user
   approval before proceeding).
3. **Can the change be broken?** The skill must attempt negative cases inferred from the change
   and from the issue's edge cases, and prove the change fails closed (or fails loudly) when
   abused.
4. **Is every observable signal clean during the test?** Console errors, network errors,
   server logs with stack traces, unhandled promise rejections, audit anomalies, persisted
   secrets, leaked internal data — any of these is a fail.
5. **Did I exercise the REAL entry point — top to bottom — for each criterion?** The bug
   usually hides in a layer a convenient harness skips. Driving an internal
   function/handler directly (instead of the real ingress: the HTTP route + its auth +
   its input validation/parsing + the queue + the consumer) is NOT a real test of that
   path — it silently skips the exact layer where a contract change (a tightened schema, a
   new required field, a parser) most often regresses. **Peripheral realness — a real DB, a
   real network fetch, a real object store — does NOT make the test faithful** if the entry
   point or any validation layer between it and the asserted effect was bypassed. The
   realness that counts is the path from the ingress to the effect, not the props around it.

If any of the five questions is "no / unknown", the E2E fails. The skill never declares a pass
on the basis of "it loaded and navigated".

## Mental model: the five hard rules

1. **The skill inspects the project, it does not assume it.** It reads the repo to discover
   the package manager, the start command, the services the app needs, the runtime (Node,
   Bun, Deno, Python, Go, Java, .NET, workers, containers, native binaries), and any required
   databases, queues, caches. It then picks a start strategy. If a needed piece is missing or
   unrunnable, it asks the user — it does not silently substitute a fake.

2. **The browser (or HTTP client) is the source of truth for user behavior.** The skill
   drives the app as a real user would: types, clicks, scrolls, navigates, waits, reads back
   what the screen shows. If a real browser is available and the app is web/native/mobile, it
   uses it. If a browser is not available or the surface is not browser-shaped, it uses an
   HTTP client with realistic headers and a user-pacing delay. The capture medium (screenshots,
   HAR, video, plain text) is chosen per project and recorded.

3. **Every observable is monitored while the test runs.** The skill subscribes to: browser
   console, browser network (with request/response capture), the app process's stdout/stderr,
   any backend service logs, and any reachable state store (DB, KV, file). The full capture
   is part of the deliverable; nothing that produced a warning/exception is hidden.

4. **The verdict is per criterion, not per flow.** The skill enumerates the acceptance criteria
   from the issue (or from the user, if there is no issue), derives negative cases from them,
   drives each, and emits one of: PASS, FAIL (with the specific reason and the captured
   evidence), INCONCLUSIVE (with what's missing to decide). A final overall verdict of PASS
   requires every criterion PASS and no FAILs in the negative suite.

5. **Drive the real entry point, top to bottom — name every layer, downgrade every bypassed
   one.** Before driving a criterion, enumerate the production path from the real ingress to
   the asserted effect (e.g. HTTP route → auth/HMAC → request-schema validation → service →
   queue → consumer → data store). Drive from the ingress, not from an internal function. For
   every layer you do NOT exercise — because you called a function directly, stubbed a hop, or
   hand-built a payload that skips validation — record it as a **fidelity gap**: that criterion
   is **INCONCLUSIVE for the bypassed layer, never PASS**. A green run that skipped the
   input-validation layer proves nothing about the inputs that layer would reject or transform.
   This is the rule that catches self-introduced regressions: if your branch tightened a
   contract, the only proof it didn't break real inputs is sending those inputs through the
   real validation layer.

## The required user input: the issue

The skill **requires a source of truth for what the branch is supposed to do**. The default
source is a ticket/issue with acceptance criteria. The user supplies it as a URL, an ID, or
inline text on the first invocation. The skill:

- Tries to fetch the issue from common sources (GitHub/GitLab/Jira/Linear) using the repo
  metadata it discovered in Phase 0.
- If it cannot find or fetch the issue, **it asks the user to paste the issue text or
  describe the acceptance criteria explicitly**. It does not proceed without it.
- If the user explicitly says there is no issue (e.g. exploratory refactor, spike, drive-by
  fix), the skill switches to **scope-by-diff mode**: it derives the implied scope from
  `git diff <base>...HEAD` and asks the user to confirm it before driving. The user can
  accept, edit, or reject the inferred scope. Rejection halts the test.

Work not in the issue (or not in the confirmed scope) is **scope creep**. The skill flags
it loudly and **halts for user decision** before continuing. It does not silently continue
testing extra work, and it does not silently fail the run because of extras — it asks.

## Prerequisites

- A clean working tree on the branch under test (`git status --short` empty). The skill will
  make temporary edits to start scripts, config or env; all are reverted in Phase 6.
- The repo on disk and runnable (dependencies installed or installable).
- The project manifest readable (so the skill can discover how to run it).
- A browser-driving or HTTP-driving tool available. For browser-visible UI, load and use the
  `playwright` skill as the default UI driver. Use HTTP driving only for backend-only surfaces
  or when no browser-shaped surface exists.

## Browser UI driver policy

When a criterion has a browser-visible UI, **use Playwright as the hands and this skill as the
brain**. Load `skill://playwright` before driving the UI. `agentic-branch-e2e` remains responsible
for scope, acceptance criteria, scope-creep detection, observability, negative cases, fidelity-gap
classification, and PASS/FAIL/INCONCLUSIVE verdicts. Playwright only performs the user actions and
captures browser evidence.

Use Playwright/browser to open the local app URL, observe the accessible UI state, click/type/scroll
like a user, re-observe after each navigation or DOM-changing action, wait for relevant network/UI
settlement, and capture screenshot/DOM/network evidence per criterion. Prefer semantic locators
and accessibility snapshots over brittle CSS selectors. Never let a successful Playwright
click-through become the verdict by itself; it is evidence for one step, not proof that the branch
delivered the requested behavior.

## TL;DR (the flow at a glance)

```
Phase 0 — Inspect the project
        manifest, scripts, services, runtime, base branch, env
Phase 1 — Resolve the issue
        fetch or ask; derive acceptance criteria and the negative-case seed
Phase 2 — Detect scope creep
        diff the branch; anything not in the issue is flagged and gated
Phase 3 — Stand up the stack
        start services the project needs (with the discovered commands)
Phase 4 — Drive the app as a real user
        per acceptance criterion, with full signal capture
Phase 5 — Bug-hunt
        attempt inferred negative cases and edge cases
Phase 6 — Verdict + teardown
        per-criterion PASS/FAIL/INCONCLUSIVE; revert temporary changes
```

---

## Phase 0 — Inspect the project

The skill must NOT hard-code how to start the app. It discovers this from the repo.

1. **Identify the manifest and package manager.** Read the root directory and look for
   `package.json`, `pnpm-workspace.yaml`, `yarn.lock`, `package-lock.json`, `pyproject.toml`,
   `requirements.txt`, `go.mod`, `Cargo.toml`, `Gemfile`, `pom.xml`, `build.gradle`,
   `*.csproj`, `*.sln`, `deno.json`, `bun.lockb`, etc. Use the first one that fits the
   primary language.
2. **Identify the workspace layout.** Multi-package monorepos are common; identify the
   apps (web, api, mobile, desktop, worker) by reading each subdirectory's manifest and any
   `workspaces`/`packages` declaration.
3. **Discover scripts.** Parse the root and per-app `scripts`/`tasks` to find:
   - `dev`, `start`, `serve`, `build` (production-shaped run for E2E),
   - `db:migrate`, `db:seed`, `db:reset`,
   - `test`, `e2e` (existing test runners to learn from and to NOT collide with),
   - `lint`, `typecheck` (cheap gates).
4. **Discover services.** Look for `docker-compose.yml`, `compose.yaml`, `Dockerfile`s, and any
   process-manifest file the project uses. List the services the app needs to run (DB, cache,
   queue, object store, identity provider, mock server).
5. **Discover env.** Look for `.env.example`, `.env.sample`, `.env.dist`, `Procfile`,
   `app.yaml`, `fly.toml`, `manifest.json`, `pyproject.toml` env sections, etc. Build a map
   of required env vars and dev fallbacks. Note any secrets the project will need
   placeholders for during E2E (e.g. an OAuth client id and secret) and propose safe
   placeholder values.
6. **Discover the runtime.** Read the manifest's `engines`, the lockfile, and any
   `Dockerfile`s. Note if any service is restricted to a specific runtime (a particular
   language version, a serverless-only API, a JVM service, a system binary, a custom
   container image).
7. **Discover auth and compliance gates.** Look for sign-up/sign-in pages, "verify your
   email" screens, consent/TOS/privacy gates, MFA flows. These are gates the driver must
   satisfy; the skill plans for them, it doesn't pretend they don't exist.
8. **Identify the base branch.** `git symbolic-ref refs/remotes/origin/HEAD` or
   `git remote show origin | grep HEAD`, falling back to `main`, `master`, `develop`. The
   base branch is the diff target for scope detection.
9. **Inventory the existing E2E/test infra.** Read `tests/e2e/`, `e2e/`, `__tests__/e2e/`,
   `playwright.config.*`, `cypress.config.*`, `*.spec.ts` in those folders, plus any
   `scripts/e2e/*` and CI workflow files. The skill re-uses conventions, fixtures, and
   helpers from the project; it does not invent a parallel harness.
10. **Output of Phase 0:** an internal *project profile* listing start commands per service,
    required env, services to start, base branch, the location of the existing E2E helpers,
    and the discovered auth/compliance gates. This profile drives every later phase.

If a needed piece (a service binary, a credential, a port, a node version) is missing or
unrunnable, the skill **stops and asks the user** — it does not silently substitute a fake.

## Phase 1 — Resolve the issue

Goal: a frozen list of acceptance criteria and the seed for negative cases.

1. **Try to fetch the issue from common sources.** The skill inspects the git remote to
   detect the forge (GitHub / GitLab / Jira / Linear / Shortcut) and the namespace. It tries,
   in order, common URL shapes (`<host>/<owner>/<repo>/issues/<n>`,
   `<host>/browse/<KEY>`, `<host>/issue/<ID>`). If a CLI is available (`gh`, `glab`, `jira`,
   `linear`), it uses it. The issue body is parsed for: title, description, acceptance
   criteria (explicit or implicit), out-of-scope notes, links, attachments.
2. **If fetching fails or no ID was provided, ask the user.** The skill asks explicitly for
   either: (a) the issue URL/ID, (b) the issue text inline, or (c) explicit confirmation
   that there is no issue and the scope should be derived from the diff.
3. **Extract acceptance criteria.** The skill lists them as a numbered checklist. Criteria
   not stated explicitly are derived from the description and marked "inferred" so the
   user can override.
4. **Extract the negative-case seed.** From each criterion, the skill derives at least one
   negative case: an invalid input, a missing pre-condition, a permissions boundary, a
   boundary value, a race, a state where the change is supposed to fail closed. The full
   negative suite is expanded in Phase 5.
5. **Freeze the criterion list.** Once the user confirms, the list is frozen for the run.
   Any criterion added later requires re-running the E2E from Phase 4. The frozen list is
   part of the run record.

## Phase 2 — Detect scope creep (diff against the issue)

The skill diffs the branch against the base branch and classifies every change as:

- **In-scope**: required to deliver a frozen criterion.
- **Inferred-support**: not in the issue, but plausibly required (test fixtures, env
  defaults, refactors the change depends on, dependencies the change needs).
- **Out-of-scope**: unrelated to any criterion (e.g. a new field, a new endpoint, a UI
  change the issue didn't ask for).

The classification is **derived, not assumed**. Each out-of-scope item is shown to the user
with its file path, the change, and why it was flagged. The user decides, per item:

- **Accept** (it's actually in-scope or a fair inferred support) — the run continues.
- **Reject** (it's scope creep; revert or split) — the E2E **halts**.
- **Defer** (note for the user to address after the merge).

The skill never silently rolls scope creep into the test. It also never silently fails
the run because of scope creep — it asks. The default, when in doubt, is to ask.

## Phase 3 — Stand up the stack

The skill uses the *project profile* from Phase 0 to start everything the app needs.
Concretely it:

1. **Installs dependencies** if not already installed (using the discovered package manager).
2. **Starts the required services** (DB, cache, queue, etc.) using the project's preferred
   mechanism (`docker compose up`, `make up`, `npm run services:start`, etc.). It records
   their ports, credentials, and how it started them so Phase 6 can stop them.
3. **Applies migrations / seeds** to whatever the project's local equivalent is. It uses
   the project's own scripts, not a hand-rolled SQL file.
4. **Builds (if needed) and starts the app** with the dev/prod-shaped start command. It
   captures stdout/stderr to a log file.
5. **Sanity-checks the stack** with a single low-risk request that exercises one internal
   hop (e.g. a public health endpoint, the index page, an unauthenticated API call). The
   expected response class (200, 401, 302) is asserted, not just "no exception". A wrong
   class means the stack is not up correctly and the run halts with a clear reason.
6. **Temporarily edits** any start config or env required to make the local run work
   (e.g. placeholder secrets, a test-only env var, a port mapping). All edits are recorded
   for Phase 6 to revert.

If any service fails to start, the skill surfaces the **first** relevant error from the
captured log and stops. It does not retry blindly.

## Phase 4 — Drive the app as a real user

Per acceptance criterion, with full signal capture.

For each criterion in the frozen list:

1. **State the drive plan.** Which page, which inputs, which expected UI state, which
   expected backend state. The plan is shown to the user in the run log; the user can
   short-circuit a criterion if needed.
2. **Drive the user action from the real entry point.** For browser-visible UI, load
   `skill://playwright` and drive the actual local app page with Playwright/browser. Start from
   `tab.observe()`, interact through observed/semantic elements, re-observe after navigation or
   DOM-changing actions, and capture browser evidence for the criterion. For backend-only surfaces,
   use an HTTP client or CLI against the actual ingress (the real route with its auth + request
   validation, or the real CLI/queue producer). Honor real user pacing. Do NOT call internal
   handlers, services, or queue-consumer functions directly and treat the result as a pass — that
   bypasses auth, input validation, and serialization, which is exactly where regressions hide. If
   there is genuinely no local way to reach a hop except invoking an internal function, record it as
   a fidelity gap and mark the bypassed layer INCONCLUSIVE (hard rule 5). The only exception is a
   criterion that is *specifically* about an internal unit driven in-process — and even then the
   ingress/validation layer it skips stays INCONCLUSIVE, not PASS.
3. **Capture every signal.**
   - **UI**: the URL, the DOM, the visible state, a screenshot or HAR per step. For
     native/mobile, the equivalent surface and a screen capture.
   - **Network**: the full request/response for every call, including headers and bodies.
   - **App logs**: the captured stdout/stderr, with timestamps.
   - **Backend state**: the relevant rows/records in the data store, queried with the
     project's own tools when possible (the CLI, the pipeline, the API) so the test
     matches what an operator would see.
   - **Errors**: console errors, unhandled rejections, network failures, server stack
     traces — all of them, not just the first.
4. **Assert the criterion.** The criterion has a **strong assertion** (the required effect
   happened) and **weak assertions** (no errors, no warnings, no extra side effects). All
   must hold.
5. **Record the verdict for the criterion.** PASS, FAIL (with the specific reason and the
   captured evidence pointer), or INCONCLUSIVE (with what's missing to decide).

The skill is explicit that "the screen rendered" is not a strong assertion. A criterion
that says "approving a refund writes an audit row" needs the audit row to be confirmed, not
just the "approved" toast.

### Changed-contract check (mandatory when the diff touches validation)

If the branch tightens or changes any input contract — a schema (`z.string().url()`), a new
required field, a regex, a parser, a type narrowing, a guard — you MUST drive that exact layer
through its **real caller** with the inputs most likely to be newly **rejected or transformed**:
the boundary value, the now-stricter case, and the legacy-but-valid shape (e.g. a *relative* URL
where the old code accepted relative and the new schema demands absolute). A test that hand-builds
an object *past* the changed validation does not exercise the change. Litmus: "what input did my
change make the system start rejecting or rewriting, and did I send that exact input through the
real validation path?" If you cannot answer with a captured request/response, the criterion is
INCONCLUSIVE — not PASS.

## Phase 5 — Bug-hunt (negative cases and edge cases)

The seed from Phase 1 is expanded here. Per criterion, the skill derives and drives a
negative suite. Categories to cover, with examples (not exhaustive — adapt per change):

- **Invalid input**: empty values, malformed values, values at boundary lengths, unicode,
  script-tag-like content, SQL/command injection-shaped strings.
- **Authorization boundary**: the same action performed by a different role, by an
  unauthenticated user, by a user from a different tenant.
- **State boundary**: the action attempted before its preconditions are met, after they
  expire, in a state the issue didn't mention (paused, archived, deleted, suspended).
- **Concurrency / re-entry**: the same action fired twice in quick succession, fired
  while the previous one is still in flight.
- **Resilience**: the action attempted while a dependent service is degraded (timeouts,
  5xx, slow response). The change must fail closed, not silently succeed.
- **Privacy / leakage**: inputs that should not be persisted (PII, secrets), outputs that
  should not include more than they should (other users' data, internal IDs).
- **Work-not-in-scope trigger**: an action the new code offers but the issue did not
  request (e.g. a "delete" button added alongside a "rename" feature). The skill drives
  the extras only to detect their presence and surface them, not to assert they work.

For each negative case, the skill records:

- The case itself (a one-line description).
- The expected behavior (fail closed, fail loudly, or be prevented from running).
- The observed behavior.
- A verdict: PASS (failed as expected), FAIL (passed when it should have failed, or
  failed in a way the user can't see), INCONCLUSIVE.

The negative suite is part of the run record and is required to be empty of FAILs for the
overall verdict to be PASS.

## Phase 6 — Verdict + teardown

1. **Aggregate the verdicts.** Per criterion: PASS / FAIL / INCONCLUSIVE. Per negative
   case: PASS / FAIL / INCONCLUSIVE. Overall: PASS only if every item is PASS.
2. **Emit the run record.** A single document the user can paste into a PR description or
   an audit log. It includes: project profile summary, frozen criteria, scope-creep
   decisions, per-criterion verdict + evidence, per-negative-case verdict + evidence, the
   captured signals, the temporary edits made, the cleanup status. The record never claims
   a pass it cannot back up with a captured evidence pointer.
3. **Revert temporary edits.** Restore every start-config/env change, kill every service
   the skill started, leave the working tree as it was found (`git status --short` empty).
4. **Honest failures.** If the verdict is FAIL or INCONCLUSIVE, the skill says so plainly
   and lists the next required action (revert the change, fix criterion X, re-fetch the
   issue, etc.). It does not soften a FAIL to "looks good, with a couple of caveats".
5. **State what the verdict does and does NOT cover.** The run record names, per criterion,
   which layers were exercised through the real entry point and which were bypassed (fidelity
   gaps). A criterion is PASS only if driven end-to-end through the real ingress; any bypassed
   layer is INCONCLUSIVE for that layer. The E2E verdict is **one input to merge-readiness, not
   a merge decision**: an E2E PASS does NOT clear open human-review threads
   (CHANGES-REQUESTED), reviewer blockers, or required CI, and does NOT make peripheral-real
   coverage equal to full-path coverage. Never report "ready to merge", "apt for production", or
   "approved" on an E2E pass alone — report "E2E PASS for criteria X,Y through the real path;
   layers A,B INCONCLUSIVE; review/CI state is separate and was checked independently (or not)."

## Backend-only mode (no browser)

When the change has no user-visible UI (a worker, a CLI, a library, a backend service, an
infra-only change), the skill drops the browser and uses an HTTP client or a CLI driver
that issues realistic requests. The structure is the same:

- Project profile still includes the run command.
- The "user" is the real client driving the **real ingress** — the actual HTTP route (with its
  auth/signature + request-schema validation), the real CLI command, the real queue producer —
  NOT an internal handler/service/consumer function invoked directly. Calling
  `handleThing(payload)` with a hand-built object is the single most common way this mode lies:
  it skips the route's auth and the producer's input validation, so a contract regression there
  (a tightened schema, a new required field) passes the test and breaks in production. Stand up
  the worker/queue locally and let a real enqueue flow through, or hit the real route; if a hop
  truly cannot be reached locally, mark it a fidelity gap and INCONCLUSIVE (hard rule 5).
- Pacing is honored; the captured signal is request/response, the app log, and the backend state.
- Per-criterion and per-negative-case verdicts follow the same rules.

## Pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The skill reports PASS but the user found a real bug | The "flow walked" verdict was used in place of per-criterion assertion | Re-run with explicit criteria; the skill refuses the global walk verdict |
| Scope creep is silently merged into the run | Phase 2 was skipped or defaulted to "accept" | Re-run with Phase 2 explicit per item; the user must decide each out-of-scope change |
| The driver "passes" the gate by skipping it | A compliance gate (consent, email-verify) was bypassed in the driver | Drive the gate like a user; if it cannot be satisfied, the criterion is INCONCLUSIVE, not PASS |
| A negative case is skipped because "the form didn't expose it" | The negative case is real, the UI is just not test-driving it | The skill surfaces this; the criterion stays open as a known gap |
| The stack boots but `/api/*` 503s | Service binding / proxy misconfigured in the project's local setup | Inspect the project's own start scripts; use them, do not invent your own |
| Console errors are visible but ignored | The skill filtered to "fatal only" | The skill captures *all* console messages, warnings included |
| The run is "green" but audit/state is wrong | The skill asserted on UI only, not on the data store | Re-run with the data-store check; UI-only assertions are explicitly insufficient |
| The browser drives a click that the real button ignores (a disabled-attribute, gate, or pointer-events: none) | The driver needs to satisfy the gate first | Read the gate's conditions from the DOM, satisfy them in order, then re-attempt |
| The skill cannot find a service binary | The project's local run needs a dependency the environment lacks | Stop and ask the user; do not fake the service |
| Re-running the skill on the same branch gives different results | Non-determinism (timestamps, IDs, env) | The skill freezes the data inputs and the clock where possible, and surfaces residual non-determinism |
| The run is "green" but the bug was in a skipped layer | The harness called an internal function / hand-built a payload past validation; peripheral realness (real DB/network/R2) created false confidence | Drive from the real ingress; enumerate every layer; mark bypassed layers INCONCLUSIVE (hard rule 5) |
| A tightened schema/validation regresses real inputs but tests pass | Tests build objects *past* the validation layer | Changed-contract check: send the newly-rejected/transformed input through the real validation path |
| Agent declares "merge-ready / apt for production" off a green E2E | Confusing the E2E verdict with the merge decision | The E2E verdict is one input; independently check review threads (CHANGES-REQUESTED), reviewer blockers, and CI before any readiness claim |
| Substantive reviewer feedback dismissed as "noise" | "Ignore the bot comments" over-applied to a named human reviewer's real blockers | Separate automated-tool noise from named-reviewer blockers; re-confirm each prior blocker is resolved, by source, before claiming done |

## Verification checklist (before declaring the E2E passed)

- [ ] Project profile (Phase 0) was produced and the user could see it.
- [ ] The issue was resolved (fetched or pasted) and the acceptance criteria were frozen.
- [ ] Every criterion is enumerated, with a strong assertion and weak assertions.
- [ ] Scope creep was classified and the user decided per item; no silent acceptance.
- [ ] The stack was stood up using the project's own commands; sanity check passed.
- [ ] Per criterion, the user-action was driven through the real UI with Playwright/browser (or
      real API/CLI in backend-only mode), not bypassed.
- [ ] Per criterion, the production entry path was enumerated and driven from the real
      ingress; every bypassed layer is recorded as a fidelity gap and marked INCONCLUSIVE.
- [ ] If the diff changed any validation/schema/contract, the newly-rejected/transformed
      input was sent through the real validation path (changed-contract check).
- [ ] No "merge-ready / apt for production / approved" claim is made off the E2E alone; open
      review threads, named-reviewer blockers, and CI were checked independently.
- [ ] Every signal was captured: UI, network, app logs, backend state, errors.
- [ ] Negative cases were driven per criterion; the suite is non-empty and the verdicts are
      recorded.
- [ ] Per-criterion and per-negative-case verdicts are emitted with evidence pointers.
- [ ] The overall verdict is the conjunction of every per-item verdict — no global walk
      verdict.
- [ ] Teardown done: every temporary edit reverted, every service stopped, `git status
      --short` empty.
- [ ] The run record is a single document the user can paste, with no hidden "the flow
      walked" handwave.
