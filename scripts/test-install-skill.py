#!/usr/bin/env python3
"""Narrow tests for scripts/install-skill.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install-skill.py"


class InstallSkillTests(unittest.TestCase):
    def run_installer(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INSTALLER), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_generic_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_installer("--harness", "generic", "--target", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("dry-run: no files written", result.stdout)
            self.assertFalse((Path(tmp) / "agentic-branch-e2e").exists())

    def test_generic_approved_copy_installs_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_installer("--harness", "generic", "--target", tmp, "--i-approve")
            self.assertEqual(result.returncode, 0, result.stderr)
            destination = Path(tmp) / "agentic-branch-e2e"
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue((destination / "references" / "adapters.md").is_file())
            self.assertTrue((destination / "examples" / "web-ui-run-record.md").is_file())
            self.assertTrue((destination / "scripts" / "validate-run-record.py").is_file())
            self.assertFalse((destination / ".git").exists())

    def test_generic_existing_destination_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = self.run_installer("--harness", "generic", "--target", tmp, "--i-approve")
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_installer("--harness", "generic", "--target", tmp, "--i-approve")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("--force", second.stderr + second.stdout)


if __name__ == "__main__":
    unittest.main()
