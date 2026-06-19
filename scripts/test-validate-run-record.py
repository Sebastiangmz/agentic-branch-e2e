#!/usr/bin/env python3
"""Narrow tests for scripts/validate-run-record.py."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-run-record.py"

spec = importlib.util.spec_from_file_location("validate_run_record", VALIDATOR)
assert spec is not None
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


BASE_RECORD = """
# Run Record

## Project profile

Runtime: test

## Scope classification

In-scope: C1.

## Frozen criteria

### C1 — Criterion

## Evaluation plan

{evaluation_plan}

## Evidence

Evidence: artifacts/c1.txt

Fidelity gaps: none.

Verdict: PASS

## Negative cases

### N1 — Negative

Verdict: PASS

## Overall verdict

PASS

## Teardown

Working tree status: clean

## Not covered

Merge readiness, CI, and review were not checked.
"""


class ValidateRunRecordTests(unittest.TestCase):
    def validate(self, evaluation_plan: str) -> list[str]:
        return module.validate(BASE_RECORD.format(evaluation_plan=evaluation_plan))

    def test_accepts_yaml_evaluation_plan_keys(self) -> None:
        errors = self.validate(
            """
pass_requires:
  - expected observation
fail_if:
  - failure observation
inconclusive_if:
  - missing evidence
required_evidence:
  ui: screenshot
negative_seeds:
  - invalid input
"""
        )
        self.assertEqual(errors, [])

    def test_rejects_substring_match_for_pass_requires(self) -> None:
        errors = self.validate(
            """
- Bypass requires a fidelity gap note.
- Fail if: failure observation
- Inconclusive if: missing evidence
- Required evidence: screenshot
- Negative seeds: invalid input
"""
        )
        self.assertIn("pass requires", "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
