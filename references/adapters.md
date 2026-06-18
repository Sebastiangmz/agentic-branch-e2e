# Harness Adapters

This skill is a protocol first. Harness-specific tools are adapters. The protocol owns scope, criteria, evidence, negative cases, fidelity gaps, and verdicts. Adapters only execute actions or fetch context.

## Installer adapter

Use `scripts/install-skill.py` to install the skill payload into an agent harness. Copy mode uses
an explicit allowlist; symlink mode links the trusted source checkout for development. Presets are intentionally thin:

- `--harness claude-code` → `~/.claude/skills/`
- `--harness omp` → `~/.omp/agent/skills/`
- `--harness hermes` → `~/.hermes/skills/`
- `--harness generic --target <dir>` → any harness skills directory

The installer is dry-run by default. Pass `--i-approve` to write files. Use `--target` for
unknown harnesses instead of adding harness-specific assumptions to the protocol.

## Adapter selection order

Use the strongest local adapter that can exercise the real entry path without bypassing layers.

1. Harness-native browser automation for browser-visible UI.
2. Harness-native HTTP/API/CLI execution for backend-only criteria.
3. Project-provided E2E runner or fixture helpers when they still drive the real app through ingress.
4. Manual command/browser instructions only when automation is unavailable; mark unobserved evidence as INCONCLUSIVE.

Never choose an adapter because it is convenient if it bypasses auth, validation, routing, queues, persistence, or another production layer.

## Browser adapter contract

A browser adapter must support, or have an equivalent for:

- opening a local app URL,
- observing accessible UI state or DOM state,
- clicking, typing, selecting, scrolling, and uploading like a user,
- waiting for navigation, UI changes, and network responses,
- capturing URL, DOM/accessibility state, screenshots, console errors, and network request/response evidence,
- preserving realistic browser behavior such as disabled controls, focus, cookies, storage, and redirects.

Prefer semantic locators and accessibility snapshots. Avoid brittle generated CSS selectors unless there is no stable semantic handle.

### OMP / Claude-like harness

When a harness exposes skills or resources, load the local browser automation instructions before driving UI. In OMP, load `skill://playwright` and use the `browser` tool. Treat Playwright as the hands, not the judge.

### Generic Playwright harness

Use the Playwright API or test runner directly. Keep the same evidence obligations: observe before interacting, wait for the relevant post-action state, collect console/network failures, and record artifacts per criterion.

### Browser unavailable

If a criterion is UI-visible and no browser-equivalent driver is available, do not replace it with an internal handler test. Either obtain a browser driver or mark the UI portion INCONCLUSIVE. Backend effects may still be tested through real HTTP/CLI ingress, but the UI criterion remains unresolved.

## HTTP/API adapter contract

Use an HTTP/API adapter only when the criterion is backend-only or when checking backend effects after a UI drive. It must:

- send requests through the real route or public local ingress,
- include realistic headers, auth, cookies, signatures, idempotency keys, and payload serialization,
- capture request URL, method, headers relevant to behavior, body shape, response status, response headers, and response body,
- avoid calling internal functions, services, or queue consumers directly.

If auth or validation cannot be exercised locally, mark that layer as a fidelity gap.

## CLI adapter contract

Use a CLI adapter when the user-facing entry point is a command. It must invoke the actual binary/script with realistic arguments and environment. Capture stdout, stderr, exit code, filesystem changes, network calls if observable, and backend state.

## Issue/source adapter contract

Prefer issue text or explicit user request. Adapter examples: GitHub issue/PR, GitLab issue/MR, Linear, Jira, local markdown, pasted text. If no source is available, derive scope from the git diff and label criteria as inferred.

A source adapter fetches context; it does not decide pass/fail.

## Git/diff adapter contract

Use git only to determine base branch, changed files, and scope classification. The diff informs criteria and scope creep; it is not proof of runtime behavior.

## Runtime/log adapter contract

A runtime/log adapter starts services with project-native commands, captures process output, and tears down what it started. It must not silently swap in fake services. If a local dependency cannot run, stop and report the missing prerequisite.

## Evidence adapter contract

Persist or summarize evidence in a stable way. Evidence pointers may be file paths, artifact IDs, URLs, command outputs, screenshots, HAR files, DB query outputs, or copied excerpts. Every verdict must point to evidence or explicitly explain why evidence is missing.

## Adapter failure rules

- Adapter cannot reach a required layer: INCONCLUSIVE for that layer.
- Adapter bypasses a production layer: INCONCLUSIVE for the bypassed layer.
- Adapter observes a failure: FAIL unless the failure is the expected negative-case behavior.
- Adapter lacks evidence capture: rerun with capture enabled or mark missing evidence INCONCLUSIVE.
