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
INSTALL_PATHS = [
    "SKILL.md",
    "references/protocol.md",
    "references/adapters.md",
    "references/evidence-model.md",
    "references/verdict-rules.md",
    "examples/web-ui-run-record.md",
    "examples/backend-only-run-record.md",
    "examples/inconclusive-fidelity-gap.md",
    "scripts/validate-run-record.py",
    "scripts/install-skill.py",
]


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

    def make_source(self, root: Path, name: str = "agentic-branch-e2e") -> Path:
        source = root / name
        for rel in INSTALL_PATHS:
            path = source / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if rel == "SKILL.md":
                path.write_text(f"---\nname: {name}\ndescription: test skill\n---\n", encoding="utf-8")
            else:
                path.write_text(f"test payload for {rel}\n", encoding="utf-8")
        return source

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
            self.assertTrue((destination / "scripts" / "install-skill.py").is_file())
            self.assertFalse((destination / ".git").exists())

    def test_generic_existing_destination_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = self.run_installer("--harness", "generic", "--target", tmp, "--i-approve")
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_installer("--harness", "generic", "--target", tmp, "--i-approve")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("--force", second.stderr + second.stdout)

    def test_invalid_name_cannot_escape_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for bad_name in ("../victim", "/tmp/victim", "a/b", ".", ".."):
                result = self.run_installer(
                    "--harness",
                    "generic",
                    "--target",
                    tmp,
                    "--name",
                    bad_name,
                    "--force",
                    "--i-approve",
                )
                self.assertNotEqual(result.returncode, 0, bad_name)
                self.assertIn("invalid install name", result.stderr + result.stdout)

    def test_force_refuses_to_delete_source_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            result = self.run_installer(
                "--source",
                str(source),
                "--harness",
                "generic",
                "--target",
                str(root),
                "--force",
                "--i-approve",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source checkout", result.stderr + result.stdout)
            self.assertTrue((source / "SKILL.md").is_file())

    def test_copy_mode_uses_allowlist_and_does_not_copy_local_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root / "src")
            (source / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            (source / "notes.local.md").write_text("private notes\n", encoding="utf-8")
            target = root / "target"
            result = self.run_installer("--source", str(source), "--harness", "generic", "--target", str(target), "--i-approve")
            self.assertEqual(result.returncode, 0, result.stderr)
            destination = target / "agentic-branch-e2e"
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertFalse((destination / ".env").exists())
            self.assertFalse((destination / "notes.local.md").exists())

    def test_symlinked_payload_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root / "src")
            (source / "references" / "adapters.md").unlink()
            (source / "references" / "adapters.md").symlink_to(root / "outside-secret")
            result = self.run_installer("--source", str(source), "--harness", "generic", "--target", str(root / "target"), "--i-approve")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlinked payload", result.stderr + result.stdout)

    def test_symlinked_payload_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root / "src")
            outside = root / "outside"
            outside.mkdir()
            shutil_target = source / "references"
            shutil_target.rename(root / "original-references")
            (outside / "protocol.md").write_text("external protocol\n", encoding="utf-8")
            (outside / "adapters.md").write_text("SECRET_FROM_OUTSIDE\n", encoding="utf-8")
            (outside / "evidence-model.md").write_text("external evidence\n", encoding="utf-8")
            (outside / "verdict-rules.md").write_text("external verdicts\n", encoding="utf-8")
            shutil_target.symlink_to(outside, target_is_directory=True)
            result = self.run_installer("--source", str(source), "--harness", "generic", "--target", str(root / "target"), "--i-approve")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlinked payload", result.stderr + result.stdout)

    def test_force_replaces_destination_symlink_without_deleting_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root / "src")
            target = root / "target"
            target.mkdir()
            other_skill = target / "other-skill"
            other_skill.mkdir()
            marker = other_skill / "marker.txt"
            marker.write_text("keep me\n", encoding="utf-8")
            (target / "agentic-branch-e2e").symlink_to(other_skill, target_is_directory=True)
            result = self.run_installer(
                "--source",
                str(source),
                "--harness",
                "generic",
                "--target",
                str(target),
                "--force",
                "--i-approve",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(marker.is_file())
            self.assertTrue((target / "agentic-branch-e2e" / "SKILL.md").is_file())
            self.assertFalse((target / "agentic-branch-e2e").is_symlink())


if __name__ == "__main__":
    unittest.main()
