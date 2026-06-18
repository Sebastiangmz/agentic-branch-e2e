#!/usr/bin/env python3
"""Install this skill into a target agent harness skills directory.

Dry-run by default. Pass --i-approve to write files.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

SKILL_NAME_RE = re.compile(r"^name:\s*([a-z0-9][a-z0-9-]{0,63})\s*$", re.MULTILINE)
DEFAULT_EXCLUDES = {".git", "__pycache__", ".DS_Store"}
REQUIRED_PATHS = [
    "SKILL.md",
    "references/protocol.md",
    "references/adapters.md",
    "references/evidence-model.md",
    "references/verdict-rules.md",
    "examples/web-ui-run-record.md",
    "examples/backend-only-run-record.md",
    "examples/inconclusive-fidelity-gap.md",
    "scripts/validate-run-record.py",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def skill_name(source: Path) -> str:
    text = (source / "SKILL.md").read_text(encoding="utf-8")
    match = SKILL_NAME_RE.search(text)
    if not match:
        raise SystemExit("SKILL.md missing frontmatter name")
    return match.group(1)


def expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path))).resolve()


def preset_target(harness: str) -> Path | None:
    home = Path.home()
    presets = {
        "claude-code": home / ".claude" / "skills",
        "omp": home / ".omp" / "agent" / "skills",
        "hermes": home / ".hermes" / "skills",
    }
    return presets.get(harness)


def resolve_target(args: argparse.Namespace) -> Path:
    if args.target:
        return expand(args.target)
    if args.harness == "generic":
        raise SystemExit("--target is required for --harness generic")
    if args.harness == "auto":
        env_target = os.environ.get("AGENT_SKILLS_DIR") or os.environ.get("SKILLS_DIR")
        if env_target:
            return expand(env_target)
        raise SystemExit("auto mode needs --target, AGENT_SKILLS_DIR, or SKILLS_DIR")
    target = preset_target(args.harness)
    if target is None:
        raise SystemExit(f"unknown harness preset: {args.harness}")
    return target.resolve()


def validate_source(source: Path) -> None:
    missing = [rel for rel in REQUIRED_PATHS if not (source / rel).exists()]
    if missing:
        joined = "\n".join(f"- {item}" for item in missing)
        raise SystemExit(f"source skill is incomplete; missing:\n{joined}")


def copy_filter(directory: str, names: list[str]) -> set[str]:
    ignored = set(DEFAULT_EXCLUDES).intersection(names)
    ignored.update(name for name in names if name.endswith(".pyc"))
    return ignored


def install_copy(source: Path, destination: Path, force: bool) -> None:
    if destination.exists():
        if not force:
            raise SystemExit(f"destination exists; rerun with --force to replace: {destination}")
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        else:
            shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=copy_filter)


def install_symlink(source: Path, destination: Path, force: bool) -> None:
    if destination.exists() or destination.is_symlink():
        if not force:
            raise SystemExit(f"destination exists; rerun with --force to replace: {destination}")
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        else:
            shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(source, target_is_directory=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install agentic-branch-e2e into an agent harness skills directory. Dry-run by default."
    )
    parser.add_argument("--harness", choices=["auto", "generic", "claude-code", "omp", "hermes"], default="auto")
    parser.add_argument("--target", help="Skills directory to install into; works for any harness")
    parser.add_argument("--source", default=str(repo_root()), help="Skill directory to install; defaults to this repo")
    parser.add_argument("--name", help="Installed directory name; defaults to SKILL.md name")
    parser.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    parser.add_argument("--force", action="store_true", help="Replace an existing installed skill")
    parser.add_argument("--i-approve", action="store_true", help="Actually install; without this flag, only print the plan")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    source = expand(args.source)
    validate_source(source)
    name = args.name or skill_name(source)
    target_dir = resolve_target(args)
    destination = target_dir / name

    print("agentic-branch-e2e installer")
    print(f"source:      {source}")
    print(f"harness:     {args.harness}")
    print(f"target dir:  {target_dir}")
    print(f"destination: {destination}")
    print(f"mode:        {args.mode}")
    print(f"force:       {args.force}")

    if not args.i_approve:
        print("dry-run: no files written; rerun with --i-approve to install")
        return 0

    if args.mode == "copy":
        install_copy(source, destination, args.force)
    else:
        install_symlink(source, destination, args.force)

    print(f"installed:   {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
