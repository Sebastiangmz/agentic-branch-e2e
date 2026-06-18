# Verdict Rules

Verdicts are per criterion and per negative case. The overall verdict is derived, not guessed.

## Criterion verdicts

### PASS

Emit PASS only when all are true:

- the strong assertion happened through the real entry path,
- weak assertions held: no relevant console errors, network failures, server errors, warnings, or unexpected side effects,
- backend or persisted state matches the requested behavior when state is part of the criterion,
- negative cases for the criterion are empty of FAIL,
- no required layer is bypassed or unobserved,
- evidence pointers are present.

### FAIL

Emit FAIL when the branch demonstrably violates a criterion or safety expectation:

- requested behavior does not happen,
- UI claims success while backend state is wrong,
- backend effect occurs without required UI or auth state,
- an invalid/unauthorized/concurrent/degraded negative case succeeds when it should fail closed,
- logs, console, network, or state show a regression,
- scope creep changes runtime behavior without user acceptance.

A FAIL must name the violated criterion and the observed evidence.

### INCONCLUSIVE

Emit INCONCLUSIVE when the test cannot prove or disprove the criterion:

- required service, credential class, or browser driver is unavailable,
- the run bypasses a production layer,
- evidence capture is missing,
- source of truth is absent and the inferred diff scope was not confirmed,
- a changed contract was not exercised through its real caller,
- the local environment cannot represent a required production behavior.

Do not soften INCONCLUSIVE into PASS. It is a hard unknown.

## Negative-case verdicts

A negative case PASS means the system failed closed, blocked the action, or surfaced the expected user-visible error. A negative case FAIL means the invalid action succeeded, failed invisibly, corrupted state, leaked data, or produced an unrelated error. A negative case INCONCLUSIVE means the negative path could not be driven or observed.

## Overall verdict

Use this derivation:

```text
if any criterion verdict is FAIL: overall = FAIL
else if any negative-case verdict is FAIL: overall = FAIL
else if any criterion or negative-case verdict is INCONCLUSIVE: overall = INCONCLUSIVE
else overall = PASS
```

The overall verdict must list every non-PASS item.

## Scope verdicts

Out-of-scope runtime behavior is not ignored. Classify it before driving:

- accepted by user: include it in scope and test it,
- rejected by user: stop or report FAIL for scope creep,
- unresolved: INCONCLUSIVE until the user decides.

## Merge-readiness boundary

E2E PASS is not merge-ready. Merge readiness also requires whatever the repository uses for review, CI, security, visual review, release approval, and deployment gates. If those are not checked, state that they are not covered.

## Common invalid verdicts

- “Looks good” without per-criterion verdicts.
- “PASS” because the page loaded.
- “PASS” after calling an internal handler instead of the real route.
- “PASS” while console/network/server errors are present.
- “PASS” without backend-state evidence for a state-changing criterion.
- “Merge-ready” based only on E2E.
