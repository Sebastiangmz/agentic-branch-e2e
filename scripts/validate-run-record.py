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
    "Frozen criteria",
    "Evidence",
    "Negative cases",
    "Overall verdict",
    "Teardown",
]

VERDICT_RE = re.compile(r"\b(PASS|FAIL|INCONCLUSIVE)\b")
CRITERION_RE = re.compile(r"\bC\d+\b")
NEGATIVE_RE = re.compile(r"\bN\d+\b")
FIDELITY_RE = re.compile(r"fidelity gap|fidelity gaps|bypassed layer", re.IGNORECASE)
MERGE_BOUNDARY_RE = re.compile(r"merge readiness|merge-ready|CI|review", re.IGNORECASE)
EVIDENCE_POINTER_RE = re.compile(r"(artifacts?/|artifact://|https?://|\.har\b|\.png\b|\.txt\b|log#|db\.txt)")


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

    if not EVIDENCE_POINTER_RE.search(text):
        errors.append("missing evidence pointers such as artifact paths, HAR, screenshots, logs, or URLs")

    if not FIDELITY_RE.search(text):
        errors.append("missing fidelity-gap statement; say none if none were found")

    if not MERGE_BOUNDARY_RE.search(text):
        errors.append("missing merge/CI/review boundary statement")

    if "the flow walked" in text.lower() and "not" not in text.lower():
        errors.append("contains a likely weak 'flow walked' verdict")

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
