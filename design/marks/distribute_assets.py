#!/usr/bin/env python3
"""Guarded distribution of generated Ink and Bone assets.

The generator owns canonical output. This tool copies only the files declared
in a visibility-specific consumer manifest. It is deliberately conservative:
every path is contained, every source is read before the first write, changed
destinations must match their recorded predecessor or be clean in Git, and a
failed write rolls the whole batch back.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_SOURCE_ROOT = SCRIPT_PATH.parents[2]
DEFAULT_MANIFEST = SCRIPT_PATH.with_name("consumers.public.json")
PROVENANCE_JSON = Path("design/BRAND-ASSETS.json")
PROVENANCE_MD = Path("design/BRAND-ASSETS.md")
SUPPORTED_MODES = {"copy", "pythonBase64", "shellBase64"}


class DistributionError(RuntimeError):
    """A safety or validation failure that must stop distribution."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise DistributionError(f"git {' '.join(args)} failed in {repo}: {detail}")
    return result.stdout.strip()


def contained_path(root: Path, relative: str, label: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or not relative or "\x00" in relative:
        raise DistributionError(f"{label} must be a non-empty relative path: {relative!r}")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise DistributionError(f"{label} escapes {resolved_root}: {relative!r}") from exc
    return resolved


def require_repo(projects_root: Path, repository: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", repository):
        raise DistributionError(f"unsafe repository name: {repository!r}")
    repo = contained_path(projects_root, repository, "repository")
    if not (repo / ".git").exists():
        raise DistributionError(f"consumer is not a Git worktree: {repo}")
    actual = Path(run_git(repo, "rev-parse", "--show-toplevel")).resolve()
    if actual != repo:
        raise DistributionError(f"repository root mismatch: expected {repo}, got {actual}")
    return repo


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DistributionError(f"cannot read manifest {path}: {exc}") from exc
    if data.get("schemaVersion") != 1:
        raise DistributionError("manifest schemaVersion must be 1")
    if data.get("visibility") not in {"public", "private"}:
        raise DistributionError("manifest visibility must be public or private")
    consumers = data.get("consumers")
    if not isinstance(consumers, list) or not consumers:
        raise DistributionError("manifest consumers must be a non-empty list")
    return data


def git_path_is_dirty(repo: Path, relative: Path) -> bool:
    output = run_git(repo, "status", "--porcelain=v1", "--", relative.as_posix())
    return bool(output)


def python_assignment_pattern(variable: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?m)^{re.escape(variable)}[ \t]*=[ \t]*\(\n"
        rf"(?:[ \t]*[\"'][A-Za-z0-9+/=]*[\"'][ \t]*\n)+"
        rf"[ \t]*\)"
    )


def extract_python_base64(original: bytes, variable: str) -> bytes:
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DistributionError("pythonBase64 destination is not UTF-8") from exc
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", variable):
        raise DistributionError(f"unsafe Python variable name: {variable!r}")
    matches = list(python_assignment_pattern(variable).finditer(text))
    if len(matches) != 1:
        raise DistributionError(
            f"expected exactly one parenthesized {variable} assignment, found {len(matches)}"
        )
    encoded = "".join(re.findall(r"[\"']([A-Za-z0-9+/=]*)[\"']", matches[0].group(0)))
    try:
        return base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise DistributionError(f"{variable} contains invalid base64") from exc


def replace_python_base64(original: bytes, variable: str, source: bytes) -> bytes:
    extract_python_base64(original, variable)
    text = original.decode("utf-8")
    pattern = python_assignment_pattern(variable)
    encoded = base64.b64encode(source).decode("ascii")
    chunks = "\n".join(f'    "{encoded[i:i + 76]}"' for i in range(0, len(encoded), 76))
    replacement = f"{variable} = (\n{chunks}\n)"
    updated, count = pattern.subn(replacement, text)
    if count != 1:  # Protected by extract_python_base64; keep this as an invariant.
        raise AssertionError(f"unexpected Python assignment replacement count: {count}")
    return updated.encode("utf-8")


def shell_assignment_pattern(variable: str) -> re.Pattern[str]:
    return re.compile(rf"(?m)^{re.escape(variable)}=(['\"])([A-Za-z0-9+/=]*)\1$")


def extract_shell_base64(original: bytes, variable: str) -> bytes:
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DistributionError("shellBase64 destination is not UTF-8") from exc
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", variable):
        raise DistributionError(f"unsafe shell variable name: {variable!r}")
    matches = list(shell_assignment_pattern(variable).finditer(text))
    if len(matches) != 1:
        raise DistributionError(f"expected exactly one {variable} assignment, found {len(matches)}")
    try:
        return base64.b64decode(matches[0].group(2), validate=True)
    except ValueError as exc:
        raise DistributionError(f"{variable} contains invalid base64") from exc


def replace_shell_base64(original: bytes, variable: str, source: bytes) -> bytes:
    extract_shell_base64(original, variable)
    text = original.decode("utf-8")
    pattern = shell_assignment_pattern(variable)
    encoded = base64.b64encode(source).decode("ascii")
    updated, count = pattern.subn(f'{variable}="{encoded}"', text)
    if count != 1:  # Protected by extract_shell_base64; keep this as an invariant.
        raise AssertionError(f"unexpected shell assignment replacement count: {count}")
    return updated.encode("utf-8")


def embedded_payload(mode: str, destination: Path, variable: str) -> bytes:
    original = destination.read_bytes()
    if mode == "pythonBase64":
        return extract_python_base64(original, variable)
    if mode == "shellBase64":
        return extract_shell_base64(original, variable)
    raise DistributionError(f"mode {mode} does not embed a managed payload")


def desired_payload(mode: str, source: bytes, destination: Path, variable: Any) -> bytes:
    if mode == "copy":
        return source
    if not destination.exists():
        raise DistributionError(f"embedded destination does not exist: {destination}")
    if not isinstance(variable, str):
        raise DistributionError(f"{mode} requires a variable name for {destination}")
    original = destination.read_bytes()
    if mode == "pythonBase64":
        return replace_python_base64(original, variable, source)
    if mode == "shellBase64":
        return replace_shell_base64(original, variable, source)
    raise DistributionError(f"unsupported distribution mode: {mode}")


def source_metadata(source_root: Path) -> dict[str, Any]:
    tokens = source_root / "design/brand/brand-tokens.json"
    generator = source_root / "design/marks/generate_marks.py"
    lock = source_root / "requirements.lock"
    for required in (tokens, generator, lock):
        if not required.is_file():
            raise DistributionError(f"required canonical input is missing: {required}")
    try:
        version = json.loads(tokens.read_text(encoding="utf-8"))["$meta"]["version"]
    except (KeyError, json.JSONDecodeError) as exc:
        raise DistributionError(f"canonical token version is unreadable: {exc}") from exc
    return {
        "canonicalSourceCommit": run_git(source_root, "rev-parse", "HEAD"),
        "canonicalSourceDirty": bool(run_git(source_root, "status", "--porcelain=v1")),
        "brandVersion": version,
        "generatorSha256": sha256_file(generator),
        "tokenSha256": sha256_file(tokens),
        "lockSha256": sha256_file(lock),
    }


def provenance_payloads(
    project: str,
    visibility: str,
    metadata: dict[str, Any],
    records: list[dict[str, str]],
) -> tuple[bytes, bytes]:
    aggregate_input = "\n".join(
        f"{item['mode']}\0{item['source']}\0{item['sourceSha256']}\0"
        f"{item['destination']}\0{item['destinationSha256']}"
        for item in sorted(records, key=lambda item: item["destination"])
    ).encode("utf-8")
    document = {
        "schemaVersion": 1,
        "project": project,
        "visibility": visibility,
        **metadata,
        "contentSetSha256": sha256_bytes(aggregate_input),
        "assets": sorted(records, key=lambda item: item["destination"]),
    }
    json_bytes = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    dirty = "yes (working-tree source; input hashes below are authoritative)" if metadata[
        "canonicalSourceDirty"
    ] else "no"
    lines = [
        "# Brand asset provenance",
        "",
        "This file is generated by `design/marks/distribute_assets.py`. Do not edit it by hand.",
        "",
        f"- Brand version: `{metadata['brandVersion']}`",
        f"- Canonical source commit: `{metadata['canonicalSourceCommit']}`",
        f"- Canonical source dirty: {dirty}",
        f"- Generator SHA-256: `{metadata['generatorSha256']}`",
        f"- Token SHA-256: `{metadata['tokenSha256']}`",
        f"- Lock SHA-256: `{metadata['lockSha256']}`",
        f"- Distributed content-set SHA-256: `{document['contentSetSha256']}`",
        "",
        "The JSON companion is the machine-readable authority for exact source and destination hashes.",
        "",
    ]
    return json_bytes, "\n".join(lines).encode("utf-8")


def trusted_previous_provenance(repo: Path, project: str) -> dict[str, dict[str, str]] | None:
    json_path = contained_path(repo, PROVENANCE_JSON.as_posix(), "provenance JSON")
    md_path = contained_path(repo, PROVENANCE_MD.as_posix(), "provenance Markdown")
    if not json_path.exists() and not md_path.exists():
        return None
    if not json_path.is_file() or not md_path.is_file():
        raise DistributionError(f"incomplete prior provenance in {repo}")
    try:
        document = json.loads(json_path.read_text(encoding="utf-8"))
        records = document["assets"]
        metadata = {
            key: document[key]
            for key in (
                "canonicalSourceCommit",
                "canonicalSourceDirty",
                "brandVersion",
                "generatorSha256",
                "tokenSha256",
                "lockSha256",
            )
        }
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise DistributionError(f"prior provenance is unreadable in {repo}: {exc}") from exc
    if document.get("schemaVersion") != 1 or document.get("project") != project:
        raise DistributionError(f"prior provenance identity mismatch in {repo}")
    if not isinstance(records, list):
        raise DistributionError(f"prior provenance asset list is invalid in {repo}")
    canonical_json, canonical_md = provenance_payloads(
        project, str(document.get("visibility")), metadata, records
    )
    if canonical_json != json_path.read_bytes() or canonical_md != md_path.read_bytes():
        raise DistributionError(f"prior provenance was edited or is non-canonical in {repo}")
    trusted: dict[str, dict[str, str]] = {}
    for record in records:
        try:
            destination_value = record["destination"]
            recorded_sha = record["destinationSha256"]
            mode = record["mode"]
            source_sha = record["sourceSha256"]
        except (KeyError, TypeError) as exc:
            raise DistributionError(f"prior provenance has an invalid asset in {repo}") from exc
        destination = contained_path(repo, destination_value, "prior provenance destination")
        if not destination.is_file():
            raise DistributionError(f"prior provenance destination is missing: {destination}")
        if mode == "copy":
            if sha256_file(destination) != recorded_sha:
                raise DistributionError(
                    f"prior provenance no longer matches destination {destination}"
                )
        elif mode in {"pythonBase64", "shellBase64"}:
            variable = record.get("variable")
            if not isinstance(variable, str) or sha256_bytes(
                embedded_payload(mode, destination, variable)
            ) != source_sha:
                raise DistributionError(
                    f"prior provenance no longer matches managed payload in {destination}"
                )
        else:
            raise DistributionError(f"prior provenance contains unsupported mode {mode!r}")
        trusted[destination_value] = record
    return trusted


def preflight(
    manifest: dict[str, Any],
    source_root: Path,
    projects_root: Path,
    selected: set[str],
    require_clean_source: bool = False,
) -> tuple[list[tuple[Path, bytes]], list[str]]:
    metadata = source_metadata(source_root)
    if require_clean_source and metadata["canonicalSourceDirty"]:
        raise DistributionError(
            "canonical source is dirty; commit/stash it or pass --allow-dirty-source explicitly"
        )
    writes: list[tuple[Path, bytes]] = []
    messages: list[str] = []
    seen_destinations: set[Path] = set()
    known_projects = {str(item.get("project")) for item in manifest["consumers"]}
    unknown = selected - known_projects
    if unknown:
        raise DistributionError(f"unknown consumer(s): {', '.join(sorted(unknown))}")

    for consumer in manifest["consumers"]:
        project = consumer.get("project")
        repository = consumer.get("repository")
        output_root_value = consumer.get("outputRoot")
        assets = consumer.get("assets")
        if not all(isinstance(value, str) and value for value in (project, repository, output_root_value)):
            raise DistributionError("each consumer needs project, repository, and outputRoot strings")
        if selected and project not in selected:
            continue
        if not isinstance(assets, list) or not assets:
            raise DistributionError(f"consumer {project} has no declared assets")
        repo = require_repo(projects_root, repository)
        previous = trusted_previous_provenance(repo, project)
        output_root = contained_path(source_root, output_root_value, f"{project} outputRoot")
        if not output_root.is_dir():
            raise DistributionError(f"generated output is missing for {project}: {output_root}")
        records: list[dict[str, str]] = []
        project_writes: list[tuple[Path, bytes]] = []

        for index, asset in enumerate(assets):
            if not isinstance(asset, dict):
                raise DistributionError(f"{project} asset {index} must be an object")
            mode = asset.get("mode")
            if mode not in SUPPORTED_MODES:
                raise DistributionError(f"{project} asset {index} has unsupported mode {mode!r}")
            source_value = asset.get("source")
            destination_value = asset.get("destination")
            if not isinstance(source_value, str) or not isinstance(destination_value, str):
                raise DistributionError(f"{project} asset {index} needs source and destination")
            source_path = contained_path(output_root, source_value, f"{project} source")
            destination = contained_path(repo, destination_value, f"{project} destination")
            if destination in seen_destinations:
                raise DistributionError(f"duplicate destination across manifest: {destination}")
            seen_destinations.add(destination)
            if not source_path.is_file():
                raise DistributionError(f"generated source is missing: {source_path}")
            source_bytes = source_path.read_bytes()
            payload = desired_payload(mode, source_bytes, destination, asset.get("variable"))

            if destination.exists() and destination.read_bytes() != payload:
                current_sha = sha256_file(destination)
                if mode == "copy":
                    expected = asset.get("expectedPreviousSha256")
                    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                        raise DistributionError(f"invalid expectedPreviousSha256 for {destination}")
                    if current_sha != expected and (
                        previous is None
                        or previous.get(destination_value, {}).get("destinationSha256") != current_sha
                    ):
                        raise DistributionError(
                            f"destination guard failed for {destination}: expected {expected}, got {current_sha}"
                        )
                else:
                    variable = asset.get("variable")
                    if not isinstance(variable, str):
                        raise DistributionError(f"{mode} requires a variable for {destination}")
                    current_embedded_sha = sha256_bytes(
                        embedded_payload(mode, destination, variable)
                    )
                    expected_embedded = asset.get("expectedPreviousEmbeddedSha256")
                    previous_record = previous.get(destination_value, {}) if previous else {}
                    if (
                        not isinstance(expected_embedded, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", expected_embedded)
                    ):
                        raise DistributionError(
                            f"invalid expectedPreviousEmbeddedSha256 for {destination}"
                        )
                    if current_embedded_sha not in {
                        expected_embedded,
                        previous_record.get("sourceSha256"),
                    }:
                        raise DistributionError(
                            f"managed payload guard failed for {destination}: got {current_embedded_sha}"
                        )
            elif not destination.exists() and mode != "copy":
                raise DistributionError(f"embedded destination is missing: {destination}")

            source_sha = sha256_bytes(source_bytes)
            destination_sha = sha256_bytes(payload)
            record = {
                    "mode": mode,
                    "source": f"{output_root_value}/{source_value}",
                    "sourceSha256": source_sha,
                    "destination": destination_value,
                    "destinationSha256": destination_sha,
                }
            if mode != "copy":
                record["variable"] = str(asset["variable"])
            records.append(record)
            project_writes.append((destination, payload))

        provenance_json, provenance_md = provenance_payloads(
            project, manifest["visibility"], metadata, records
        )
        project_writes.extend(
            [
                (contained_path(repo, PROVENANCE_JSON.as_posix(), "provenance JSON"), provenance_json),
                (contained_path(repo, PROVENANCE_MD.as_posix(), "provenance Markdown"), provenance_md),
            ]
        )
        changed = sum(1 for path, payload in project_writes if not path.exists() or path.read_bytes() != payload)
        messages.append(f"{project}: {len(records)} assets, {changed} files need update")
        writes.extend(project_writes)

    if not writes:
        raise DistributionError("no consumers selected")
    return writes, messages


def apply_atomically(writes: list[tuple[Path, bytes]]) -> int:
    changed = [(path, payload) for path, payload in writes if not path.exists() or path.read_bytes() != payload]
    if not changed:
        return 0
    originals: dict[Path, tuple[bytes | None, int | None]] = {}
    staged: list[tuple[Path, Path]] = []
    try:
        for destination, payload in changed:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                originals[destination] = (destination.read_bytes(), destination.stat().st_mode)
            else:
                originals[destination] = (None, None)
            handle = tempfile.NamedTemporaryFile(
                prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent, delete=False
            )
            try:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                handle.close()
            temporary = Path(handle.name)
            if originals[destination][1] is not None:
                os.chmod(temporary, originals[destination][1] & 0o777)
            staged.append((temporary, destination))
        for temporary, destination in staged:
            os.replace(temporary, destination)
    except Exception:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
        for destination, (payload, mode) in originals.items():
            if payload is None:
                destination.unlink(missing_ok=True)
                continue
            handle = tempfile.NamedTemporaryFile(
                prefix=f".{destination.name}.rollback.", dir=destination.parent, delete=False
            )
            try:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                handle.close()
            rollback = Path(handle.name)
            if mode is not None:
                os.chmod(rollback, mode & 0o777)
            os.replace(rollback, destination)
        raise
    return len(changed)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument(
        "--projects-root",
        type=Path,
        help="directory containing consumer repositories (default: source root parent)",
    )
    parser.add_argument("--consumer", action="append", default=[], help="limit to one project; repeatable")
    parser.add_argument(
        "--allow-dirty-source",
        action="store_true",
        help="allow --apply from an uncommitted canonical tree and record that fact",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="verify destinations without writing (default)")
    action.add_argument("--apply", action="store_true", help="perform the fully preflighted update")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    projects_root = (args.projects_root or source_root.parent).resolve()
    try:
        manifest = load_manifest(args.manifest.resolve())
        writes, messages = preflight(
            manifest,
            source_root,
            projects_root,
            set(args.consumer),
            require_clean_source=args.apply and not args.allow_dirty_source,
        )
        for message in messages:
            print(message)
        pending = [(path, payload) for path, payload in writes if not path.exists() or path.read_bytes() != payload]
        if args.apply:
            count = apply_atomically(writes)
            print(f"Distribution complete: {count} files updated.")
            return 0
        if pending:
            print(f"Distribution check failed: {len(pending)} files differ or are missing.", file=sys.stderr)
            for path, _ in pending:
                print(f"  {path}", file=sys.stderr)
            return 1
        print("Distribution check passed: all declared assets and provenance match.")
        return 0
    except DistributionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
