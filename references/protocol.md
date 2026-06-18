# Agentic Branch E2E Protocol

This file defines the harness-agnostic protocol. It does not depend on Claude Code, OMP, a specific browser tool, or a specific issue tracker.

## Purpose

Run a feature branch locally as a real user would, then decide whether the branch delivers the requested behavior and nothing else. The protocol rejects the weak verdict “the flow walked.” A pass requires criterion-level evidence, clean observable signals, negative-case coverage, and no unmarked fidelity gaps.

## Source of truth

Prefer an issue, ticket, PRD, or explicit user request as the source of truth. If none exists, derive the intended scope from the branch diff against the base branch and mark every criterion as inferred. Do not silently invent scope.

Freeze the criteria before driving the app. Any later criterion change requires restarting the relevant drive phase.

## Anti-mask questions

For every criterion, answer all five questions:

1. Did the branch deliver the requested behavior?
2. Did the branch avoid unrelated behavior or scope creep?
3. Did the test attempt to break the change with realistic negative cases?
4. Were UI, network, logs, backend state, and error signals clean?
5. Was the real entry path exercised from ingress to effect?

If any answer is no or unknown, do not emit an overall pass.

## Hard rules

1. Inspect the project before running it. Discover package manager, runtime, app boundaries, start commands, service dependencies, env, auth gates, and existing E2E conventions from the repository.
2. Drive the real user entry point. For UI criteria, use a real browser automation driver. For backend-only criteria, use the real HTTP route, CLI command, queue producer, or equivalent ingress.
3. Monitor every observable signal. Capture UI state, network traffic, app logs, backend state, and errors while the action runs.
4. Judge per criterion. Emit PASS, FAIL, or INCONCLUSIVE for every criterion and every negative case. The final verdict is the conjunction of those verdicts.
5. Name the production path and downgrade bypassed layers. If the run skips auth, parsing, schema validation, routing, queueing, persistence, or another layer between ingress and effect, mark that layer as a fidelity gap and the affected criterion INCONCLUSIVE for that layer.

## Required phases

### Phase 0 — Project profile

Produce a project profile with:

- repository root and base branch,
- package manager and runtime,
- app/workspace layout,
- start commands and service commands,
- env requirements and safe local placeholders,
- auth/compliance gates,
- existing E2E helpers and fixtures,
- known local constraints.

Stop if a required dependency, service, credential class, or runtime cannot be obtained locally with safe local/test credentials. Do not fake a service, pass production credentials to branch code, or inherit sensitive environment variables into untrusted startup commands.

### Phase 1 — Freeze criteria

Fetch or accept the issue/user request. Extract explicit criteria, infer missing criteria from the request, and derive at least one negative-case seed per criterion. If no issue exists, infer criteria from the diff and label them as inferred.

### Phase 2 — Classify scope

Diff the branch against the base branch. Classify each change as in-scope, inferred-support, or out-of-scope. Gate out-of-scope work before testing it.

### Phase 3 — Stand up the real stack

Install dependencies if required, start services with project-native commands, apply migrations/seeds with project-native commands, start the app under a minimal local/test environment, and sanity-check the stack through a low-risk real request. Scrub inherited production secrets before running branch code. Capture startup logs and record every temporary edit for teardown.

### Phase 4 — Drive real user behavior

For each frozen criterion, state the drive plan, enumerate the production path, drive from the real ingress, capture evidence, assert strong and weak expectations, and record the criterion verdict.

### Phase 5 — Bug-hunt

Drive the negative suite. Cover invalid input, auth boundaries, state boundaries, concurrency/re-entry, degraded dependencies, privacy/leakage, and any UI or API affordance not requested by the source of truth.

### Phase 6 — Verdict and teardown

Aggregate verdicts, emit a single run record, revert temporary edits, stop services, and leave the working tree as it was found. Never equate E2E PASS with merge-ready, production-ready, or approved unless review state and CI were checked independently.

## Changed-contract check

When the diff changes validation, schema, parsing, route contracts, guards, required fields, or type narrowing, send newly rejected/transformed inputs through the real caller. A test that hand-builds objects past validation does not prove the contract still works. If no captured request/response exercises the changed boundary, mark the criterion INCONCLUSIVE.
