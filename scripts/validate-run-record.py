#!/usr/bin/env python3
"""Validate the structural completeness of an Agentic Branch E2E run record.

This is a lightweight guardrail, not a semantic proof. It checks that a markdown
run record contains the sections and verdict language required by the skill.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_PHRASES = [
    "Project profile",
    "Scope classification",
    "Frozen criteria",
    "Evaluation plan",
    "Evidence",
    "Negative cases",
    "Overall verdict",
    "Teardown",
]

VERDICT_RE = re.compile(r"\b(PASS|FAIL|INCONCLUSIVE)\b")
CRITERION_RE = re.compile(r"\bC\d+\b")
NEGATIVE_RE = re.compile(r"\bN\d+\b")
FIDELITY_RE = re.compile(r"fidelity gap|fidelity gaps|bypassed layer", re.IGNORECASE)
EVAL_TERM_PATTERNS = {
    "pass requires": re.compile(r"^\s*(?:[-*]\s*)?(?:pass requires|pass_requires)\s*:", re.IGNORECASE | re.MULTILINE),
    "fail if": re.compile(r"^\s*(?:[-*]\s*)?(?:fail if|fail_if)\s*:", re.IGNORECASE | re.MULTILINE),
    "inconclusive if": re.compile(
        r"^\s*(?:[-*]\s*)?(?:inconclusive if|inconclusive_if)\s*:", re.IGNORECASE | re.MULTILINE
    ),
    "required evidence": re.compile(
        r"^\s*(?:[-*]\s*)?(?:required evidence|required_evidence)\s*:", re.IGNORECASE | re.MULTILINE
    ),
    "negative seeds": re.compile(
        r"^\s*(?:[-*]\s*)?(?:negative seeds|negative_seeds)\s*:", re.IGNORECASE | re.MULTILINE
    ),
}
MERGE_BOUNDARY_RE = re.compile(r"\bnot covered\b|\bmerge readiness\b|\bmerge-ready\b|\bCI\b|\breview\b", re.IGNORECASE)
EVIDENCE_POINTER_RE = re.compile(
    r"(artifacts?/|artifact://|local://|mcp://|https?://|stdout:|stderr:|\.har\b|\.png\b|\.jpe?g\b|\.webm\b|\.log\b|\.jsonl?\b|\.txt\b|\.sqlite\b|log#|db\.txt)"
)
WEAK_FLOW_RE = re.compile(r"(?<!not )\bthe flow walked\b", re.IGNORECASE)


def validate(text: str) -> list[str]:
    errors: list[str] = []

    for phrase in REQUIRED_PHRASES:
        if phrase.lower() not in text.lower():
            errors.append(f"missing required section/phrase: {phrase}")

    verdicts = VERDICT_RE.findall(text)
    if not verdicts:
        errors.append("missing PASS/FAIL/INCONCLUSIVE verdict language")

    if not CRITERION_RE.search(text):
        errors.append("missing criterion IDs like C1")

    if not NEGATIVE_RE.search(text):
        errors.append("missing negative-case IDs like N1")

    missing_eval_terms = [term for term, pattern in EVAL_TERM_PATTERNS.items() if not pattern.search(text)]
    if missing_eval_terms:
        missing = ", ".join(missing_eval_terms)
        errors.append(f"missing evaluation-plan terms: {missing}")

    if not EVIDENCE_POINTER_RE.search(text):
        errors.append("missing evidence pointers such as artifact paths, HAR, screenshots, logs, or URLs")

    if not FIDELITY_RE.search(text):
        errors.append("missing fidelity-gap statement; say none if none were found")

    if not MERGE_BOUNDARY_RE.search(text):
        errors.append("missing merge/CI/review boundary statement")

    if WEAK_FLOW_RE.search(text):
        errors.append("contains a likely weak 'the flow walked' verdict")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate-run-record.py <run-record.md>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    text = path.read_text(encoding="utf-8")
    errors = validate(text)

    if errors:
        print("INVALID run record:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID run record structure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
