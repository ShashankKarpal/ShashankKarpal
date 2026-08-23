#!/usr/bin/env python3
"""Fail if private mark material can enter the public brand tree by default."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "design/marks/consumers.public.json"
PIPELINE = ROOT / "design/brand/run-mark-pipeline.sh"
FORBIDDEN_TRACKED_PREFIXES = (
    "design/marks/out/private/",
)
FORBIDDEN_TRACKED_FILES = {
    "design/marks/private_marks.py",
    "design/marks/private_projects.py",
    "design/marks/exploration/2026-08-19-github-avatar/round1-a-monogram.png",
    "design/marks/exploration/2026-08-19-github-avatar/round1-contact-sheet.png",
}
REQUIRED_IGNORES = {
    "design/marks/out/private/",
    "design/marks/private_marks.py",
    "design/marks/private_projects.py",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def git_candidates() -> set[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    candidates = {item.decode("utf-8") for item in result.stdout.split(b"\0") if item}
    return {relative for relative in candidates if (ROOT / relative).exists()}


def load_public_projects() -> set[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1 or data.get("visibility") != "public":
        raise ValueError("public consumer manifest identity is invalid")
    projects: set[str] = set()
    for consumer in data.get("consumers", []):
        project = consumer.get("project")
        repository = consumer.get("repository")
        output_root = consumer.get("outputRoot")
        if not isinstance(project, str) or not project:
            raise ValueError("public manifest contains an invalid project")
        if repository != project:
            raise ValueError(f"repository/project mismatch for {project}")
        if output_root != f"design/marks/out/{project}":
            raise ValueError(f"unexpected public output root for {project}")
        if project in projects:
            raise ValueError(f"duplicate public project {project}")
        projects.add(project)
        for asset in consumer.get("assets", []):
            for key in ("source", "destination"):
                value = asset.get(key)
                if not isinstance(value, str) or not value:
                    raise ValueError(f"invalid {key} for {project}")
                if "private" in Path(value).parts:
                    raise ValueError(f"private path segment in public {key} for {project}")
    if not projects:
        raise ValueError("public manifest has no consumers")
    return projects


def visible_targets() -> set[str]:
    result = subprocess.run(
        ["bash", str(PIPELINE), "--list-targets"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"public generator target listing failed: {detail}")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def main() -> int:
    errors: list[str] = []
    try:
        projects = load_public_projects()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail(str(exc))
        return 1

    candidates = git_candidates()
    for path in sorted(candidates):
        if path in FORBIDDEN_TRACKED_FILES or path.startswith(FORBIDDEN_TRACKED_PREFIXES):
            errors.append(f"forbidden private-capable path is tracked: {path}")
        if path.startswith("design/marks/out/"):
            parts = Path(path).parts
            if len(parts) > 3 and parts[3] not in projects | {"github", "qa"}:
                errors.append(f"unapproved generated output root is tracked: {parts[3]}")

    ignore_lines = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    for required in sorted(REQUIRED_IGNORES - ignore_lines):
        errors.append(f"required public ignore rule is missing: {required}")

    try:
        targets = visible_targets()
    except RuntimeError as exc:
        errors.append(str(exc))
    else:
        expected = projects | {"avatar", "qa"}
        if targets != expected:
            errors.append(
                "default generator targets differ from the public allowlist: "
                f"expected {sorted(expected)}, got {sorted(targets)}"
            )

    if errors:
        for error in errors:
            fail(error)
        return 1
    print(
        f"Public-boundary check passed: {len(projects)} public projects, "
        f"{len(candidates)} tracked or commit-candidate paths, no private-capable public output."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
