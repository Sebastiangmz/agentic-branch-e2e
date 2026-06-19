---
name: agentic-branch-e2e
description: "This skill should be used when the user asks to end-to-end test a feature branch as a real user in a locally running app, verify that a branch fulfills its issue or requested behavior, or bug-hunt UI plus backend behavior before merge. It is harness-agnostic: freeze an evaluation plan before driving the app, then use the strongest available browser, HTTP, CLI, git, issue, log, and evidence adapters; for browser-visible UI prefer a visible/headed Playwright-capable browser so the user can watch the real app flow, and in OMP/Claude-like harnesses load skill://playwright when available. Do not pass a 'flow walks' check; produce criterion-level PASS/FAIL/INCONCLUSIVE verdicts with evidence and negative cases."
version: 1.3.0
author: Chenko
license: MIT
metadata:
  tags: [e2e, testing, browser, qa, bug-hunting, verification, branch-verification, full-stack, harness-agnostic]
  adapters: [browser, playwright, http, cli, git, issue-tracker, logs, datastore]
---

# Agentic Branch E2E

Run a feature branch locally as a real user would, then decide whether the branch delivers the requested behavior and nothing else. This skill is the **brain**: it owns scope, criteria, observability, negative cases, fidelity gaps, and verdicts. Browser/HTTP/CLI/git/issue tools are **adapters**: they execute actions or fetch context, but they do not decide PASS/FAIL.

## Core contract

- Prove behavior through the real entry path, not through internal handlers.
- Prefer issue/user-request scope; if absent, infer scope from the branch diff and label it inferred.
- Use a visible/headed Playwright-capable browser driver for browser-visible UI whenever the harness supports it. In OMP/Claude-like harnesses, load `skill://playwright` when available and prefer a real app browser window over hidden/headless automation.
- Use real HTTP routes, real CLI commands, or real queue producers for backend-only surfaces.
- Capture UI, network, logs, backend state, and errors for every criterion.
- Emit `PASS`, `FAIL`, or `INCONCLUSIVE` per criterion and per negative case.
- Treat every bypassed production layer as a fidelity gap. A skipped layer makes the affected proof `INCONCLUSIVE`, never `PASS`.
- Never equate E2E PASS with merge-ready, production-ready, or approved unless review and CI gates were checked separately.

## When to use

Use when the user asks to:

- test this branch,
- run an E2E,
- verify it works in the real app,
- test as a user,
- click through the flow,
- prove the feature works,
- bug-hunt a branch,
- validate an issue/PR/branch in the local app.

Do not use for documentation-only changes, pure static config with no runtime behavior, or cases where a small unit/integration test is the only requested proof. For backend-only changes, use the same protocol with HTTP/CLI adapters and no browser.

## Required source of truth

Prefer an issue, ticket, PRD, PR description, or explicit user request. Fetch it when the harness provides the needed integration; otherwise ask for the text. If there is no source, derive criteria from `git diff <base>...HEAD`, mark them as inferred, and expose the inferred scope before verdicting.

Out-of-scope behavior must be classified before testing:

- accepted by user: include it in scope,
- rejected by user: stop or report scope failure,
- unresolved: mark the run `INCONCLUSIVE` until decided.

## Required phases

### Phase 0 — Build the project profile

Inspect the repository. Discover package manager, runtime, workspace layout, start commands, service dependencies, env requirements, auth/compliance gates, base branch, existing E2E helpers, and local constraints. Identify required credential classes, but use only local/test credentials or safe placeholders. Stop if a required service, credential class, binary, or runtime cannot be made available without faking the system or exposing production secrets.

### Phase 1 — Freeze criteria and evaluation plan

Extract explicit criteria from the source of truth. Infer missing criteria only when necessary and label them inferred. Before driving the app, write the evaluation plan for each criterion: `pass_requires`, `fail_if`, `inconclusive_if`, required evidence, and at least one negative-case seed. Freeze this plan before interacting with the running app. Later criterion or rubric changes require restarting the affected drive phase; do not move the goalposts after observing app behavior.

### Phase 2 — Classify scope

Diff the branch against the base branch. Classify every changed behavior as in-scope, inferred-support, or out-of-scope. Gate unresolved scope before proceeding.

### Phase 3 — Stand up the real stack

Use project-native commands to install dependencies, start services, apply migrations/seeds, and start the app under a minimal local/test environment. Scrub inherited production credentials before running branch code. Sanity-check the stack through a low-risk real request. Capture startup logs and record temporary edits for teardown.

### Phase 4 — Drive real user behavior

For every criterion:

1. Read the frozen evaluation plan: required evidence, `pass_requires`, `fail_if`, `inconclusive_if`, and negative seeds.
2. State the drive plan: page/route/command, inputs, expected UI state, expected backend state.
3. Enumerate the production path from ingress to effect.
4. Drive from the real ingress using the strongest available adapter.
5. Capture UI, network, logs, backend state, and errors.
6. Compare observations against the frozen evaluation plan.
7. Record `PASS`, `FAIL`, or `INCONCLUSIVE` with evidence pointers.

For browser-visible UI, prefer a visible/headed browser so the user can watch the real app flow while evidence is captured. Use headless or hidden browser automation only when live observation is not requested or the harness cannot open a physical browser; record that limitation as an adapter constraint. Start from observable UI state, interact through semantic/accessible controls when possible, re-observe after navigation or DOM-changing actions, and collect browser evidence. In OMP, this means loading `skill://playwright` and using the browser tool with a visible app target when available.

### Phase 5 — Bug-hunt negative cases

Drive negative cases per criterion. Cover invalid input, authorization boundaries, state boundaries, concurrency/re-entry, degraded dependencies, privacy/leakage, and newly exposed out-of-scope affordances. A negative case passes only when the system fails closed or blocks the action as expected.

### Phase 6 — Verdict and teardown

Aggregate criterion and negative-case verdicts. Emit a single run record. Revert temporary edits, stop services, and leave the working tree as it was found.

## Changed-contract check

When the diff changes validation, schema, parsing, route contracts, guards, required fields, or type narrowing, send newly rejected or transformed inputs through the real caller. A test that constructs objects past validation does not prove the contract still works. Without captured request/response evidence through the changed boundary, mark the criterion `INCONCLUSIVE`.

## Output contract

Return one run record containing:

- project profile summary,
- source of truth and frozen criteria,
- evaluation plan per criterion (`pass_requires`, `fail_if`, `inconclusive_if`, required evidence, negative seeds),
- scope classification decisions,
- per-criterion production path,
- per-criterion evidence pointers,
- per-criterion verdicts and reasons,
- negative cases and verdicts,
- fidelity gaps,
- overall verdict,
- teardown status,
- explicit “not covered” section for CI/review/merge readiness when not checked.

Use `references/evidence-model.md` for the detailed shape. Use `references/verdict-rules.md` to derive verdicts. Use `scripts/validate-run-record.py` to check that a markdown run record includes the required sections and verdict language.

## Installation command

Use `scripts/install-skill.py` to install this skill into an agent harness. The command is
dry-run by default and writes only with `--i-approve`.

Common targets:

```bash
python3 scripts/install-skill.py --harness claude-code
python3 scripts/install-skill.py --harness omp
python3 scripts/install-skill.py --harness hermes
python3 scripts/install-skill.py --harness generic --target /path/to/skills
```

Add `--i-approve` to install, `--force` to replace an existing install, and `--mode symlink`
for development installs that should track this checkout.

## References

- `references/protocol.md` — full harness-agnostic protocol, anti-mask rules, phases, and changed-contract check.
- `references/adapters.md` — browser, Playwright, HTTP, CLI, git, issue, runtime/log, and evidence adapter contracts.
- `references/evidence-model.md` — required evidence fields and run-record shape.
- `references/verdict-rules.md` — PASS/FAIL/INCONCLUSIVE derivation and invalid verdict patterns.

## Examples

- `examples/web-ui-run-record.md` — browser-visible UI success case.
- `examples/backend-only-run-record.md` — backend-only HTTP/queue success case.
- `examples/inconclusive-fidelity-gap.md` — correct INCONCLUSIVE report when a layer is bypassed.

## Verification checklist

Before declaring the E2E passed, confirm:

- [ ] Project profile was produced.
- [ ] Source of truth was resolved or diff-inferred criteria were labeled.
- [ ] Criteria and evaluation plans were frozen before driving.
- [ ] Each criterion had `pass_requires`, `fail_if`, `inconclusive_if`, required evidence, and negative seeds.
- [ ] Scope creep was classified and gated.
- [ ] Stack was started with project-native commands.
- [ ] Each criterion was driven through the real ingress.
- [ ] Browser-visible UI used a visible/headed Playwright-capable driver when available, or recorded why only headless/hidden automation was possible.
- [ ] Production path layers were enumerated.
- [ ] Bypassed layers were marked as fidelity gaps and INCONCLUSIVE.
- [ ] Changed contracts were tested through the real caller.
- [ ] UI, network, logs, backend state, and errors were captured.
- [ ] Negative cases were driven and verdicts recorded.
- [ ] Overall verdict was derived from item verdicts.
- [ ] Teardown left the working tree clean.
- [ ] Merge readiness, CI, and review state were not claimed unless separately checked.
