# Evidence Model

Every verdict must be backed by evidence. Evidence is not limited to screenshots; it is the set of observable facts proving what happened through the real entry path.

## Run record shape

A complete run record contains:

```yaml
run:
  branch: string
  base_branch: string
  commit: string
  source_of_truth: issue | user_request | diff_inferred
  app_entrypoint: string
  started_services: [string]
  temporary_edits: [string]

scope_classification:
  in_scope: [string]
  inferred_support: [string]
  out_of_scope: [string]
  unresolved: [string]

criteria:
  - id: C1
    text: string
    source: explicit | inferred
    production_path: [ingress, auth, validation, service, persistence]
    drive_plan: string
    evidence:
      ui: [artifact]
      network: [artifact]
      logs: [artifact]
      backend_state: [artifact]
      errors: [artifact]
    strong_assertion: string
    weak_assertions: [string]
    fidelity_gaps: [string]
    verdict: PASS | FAIL | INCONCLUSIVE
    reason: string

negative_cases:
  - id: N1
    criterion_id: C1
    case: string
    expected: string
    observed: string
    evidence: [artifact]
    verdict: PASS | FAIL | INCONCLUSIVE

overall_verdict:
  verdict: PASS | FAIL | INCONCLUSIVE
  reason: string

teardown:
  services_stopped: [string]
  temporary_edits_reverted: [string]
  working_tree_status: clean | dirty
```

## Evidence fields

### UI evidence

Capture URL, visible state, accessible/DOM state, and screenshots when visuals matter. For browser-visible criteria, UI evidence must show the user-facing state before and after the critical action.

### Network evidence

Capture relevant requests and responses. Include status codes and body shape. Redact secrets but preserve fields needed to prove behavior.

### Log evidence

Capture app/server logs around the action window. Include warnings and errors, not only fatal exceptions.

### Backend-state evidence

Query the relevant datastore or project-native operator surface after the action. Prefer project-provided CLIs, APIs, or admin views over ad-hoc internal calls. The evidence should prove the persisted effect or prove that no forbidden side effect occurred.

### Error evidence

Record browser console errors, unhandled rejections, failed network calls, server stack traces, rejected jobs, and worker/queue errors. Clean runs state that no such errors were observed and identify where they were checked.

## Artifact pointers

Use stable pointers: file paths, artifact IDs, URLs, command outputs, screenshots, HAR files, DB query outputs, or inline excerpts. A verdict without a pointer is only acceptable when the reason is INCONCLUSIVE due to missing capture.

## Redaction

Do not expose secrets, session tokens, API keys, private user data, or credentials in the run record. Redact values while preserving field names and behavior-relevant shapes.

## Minimum evidence by verdict

PASS requires:

- strong assertion evidence,
- weak assertion evidence,
- clean error/log/network evidence,
- no unhandled fidelity gaps,
- teardown evidence.

FAIL requires:

- the failing observation,
- the expected behavior,
- the actual behavior,
- the layer where failure was observed.

INCONCLUSIVE requires:

- the missing layer or missing evidence,
- what was tested anyway,
- what is needed to decide.
