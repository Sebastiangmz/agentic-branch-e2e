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

SAFE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SKILL_NAME_RE = re.compile(r"^name:\s*([a-z0-9][a-z0-9-]{0,63})\s*$", re.MULTILINE)
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
INSTALL_PATHS = REQUIRED_PATHS + ["scripts/install-skill.py"]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def validate_install_name(name: str) -> str:
    if not SAFE_NAME_RE.fullmatch(name):
        raise SystemExit(
            "invalid install name; use lowercase letters, numbers, and hyphens only "
            "(max 64 chars), with no path separators"
        )
    return name


def skill_name(source: Path) -> str:
    text = (source / "SKILL.md").read_text(encoding="utf-8")
    match = SKILL_NAME_RE.search(text)
    if not match:
        raise SystemExit("SKILL.md missing frontmatter name")
    return validate_install_name(match.group(1))


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
    symlinks = [rel for rel in INSTALL_PATHS if (source / rel).is_symlink()]
    if symlinks:
        joined = "\n".join(f"- {item}" for item in symlinks)
        raise SystemExit(f"refusing to install symlinked payload files:\n{joined}")
    missing = [rel for rel in INSTALL_PATHS if not (source / rel).exists()]
    if missing:
        joined = "\n".join(f"- {item}" for item in missing)
        raise SystemExit(f"source skill is incomplete; missing:\n{joined}")


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def resolve_destination(source: Path, target_dir: Path, name: str) -> Path:
    target_resolved = target_dir.resolve(strict=False)
    destination = (target_resolved / validate_install_name(name)).resolve(strict=False)

    if destination.parent != target_resolved:
        raise SystemExit(f"destination escapes target directory: {destination}")

    source_resolved = source.resolve(strict=True)
    if destination == source_resolved:
        raise SystemExit("refusing to install over the source checkout")
    if is_relative_to(destination, source_resolved):
        raise SystemExit("refusing to install inside the source checkout")
    if is_relative_to(source_resolved, destination):
        raise SystemExit("refusing to install from a source inside the destination")

    return destination


def copy_allowlist(source: Path, destination: Path) -> None:
    for rel in INSTALL_PATHS:
        src = source / rel
        dst = destination / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def prepare_destination(destination: Path, force: bool) -> None:
    if not destination.exists() and not destination.is_symlink():
        return
    if not force:
        raise SystemExit(f"destination exists; rerun with --force to replace: {destination}")
    if destination.is_symlink() or destination.is_file():
        destination.unlink()
    else:
        shutil.rmtree(destination)


def install_copy(source: Path, destination: Path, force: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.parent / f".{destination.name}.tmp-{os.getpid()}"
    if temp.exists() or temp.is_symlink():
        if temp.is_symlink() or temp.is_file():
            temp.unlink()
        else:
            shutil.rmtree(temp)
    try:
        temp.mkdir()
        copy_allowlist(source, temp)
        prepare_destination(destination, force)
        temp.rename(destination)
    except Exception:
        if temp.exists() or temp.is_symlink():
            if temp.is_symlink() or temp.is_file():
                temp.unlink()
            else:
                shutil.rmtree(temp)
        raise


def install_symlink(source: Path, destination: Path, force: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.parent / f".{destination.name}.tmp-{os.getpid()}"
    if temp.exists() or temp.is_symlink():
        if temp.is_symlink() or temp.is_file():
            temp.unlink()
        else:
            shutil.rmtree(temp)
    try:
        temp.symlink_to(source, target_is_directory=True)
        prepare_destination(destination, force)
        temp.rename(destination)
    except Exception:
        if temp.exists() or temp.is_symlink():
            temp.unlink()
        raise


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
    name = validate_install_name(args.name) if args.name else skill_name(source)
    target_dir = resolve_target(args)
    destination = resolve_destination(source, target_dir, name)

    print("agentic-branch-e2e installer")
    print(f"source:      {source}")
    print(f"harness:     {args.harness}")
    print(f"target dir:  {target_dir}")
    print(f"destination: {destination}")
    print(f"mode:        {args.mode}")
    print(f"force:       {args.force}")

    if args.mode == "symlink":
        print("warning: symlink mode exposes the trusted source checkout to the harness; use only for development")

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
