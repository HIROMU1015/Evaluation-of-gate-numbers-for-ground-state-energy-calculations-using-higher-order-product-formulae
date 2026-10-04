"""Integrity boundaries for the separately authorized truth-free prediction phase."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from review_response.hchain_input_reference_preparation import (
    PreparationError, sha_file, write_json,
)

DOC = "docs/second_study_v2/hchain_prediction_20261004"
PREP_DOC = "docs/second_study_v2/hchain_input_reference_preparation_20261004"
OLD = "docs/second_study_v2/hchain_independent_validation_20261004"
PREP = "artifacts/hchain_input_reference_preparation_20261004_06922cb"
BASE = "a03bd71415cac6deb3b653c131905f32b744cec5"
INPUT_COMMIT = "ed8b77ffb2d446283a079a6a6c9083c0a22886de"
NEW_SOURCES = (f"{DOC}/authorization.json", f"{DOC}/protocol.md",
               "review_response/hchain_prediction_phase.py",
               "review_response/run_hchain_prediction_phase.py",
               "review_tests/test_hchain_prediction_phase.py")
INPUT_FILES = ("INPUT_FROZEN.json", "input_identity.json", "runtime_manifest.json",
               "source_audit.json", "input_access_audit.json", "input_resource_audit.json")
BUNDLE_FILES = ("prediction.json", "FREEZE.json", "source_audit.json", "access_audit.json",
                "resource_audit.json", "prediction.sha256", "manifest.json")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def check_remote(root):
    url = git(root, "remote", "get-url", "origin").decode().strip()
    normalized = url.removesuffix(".git")
    allowed = ("git@github.com:HIROMU1015/", "https://github.com/HIROMU1015/")
    if not any(normalized.startswith(prefix) for prefix in allowed):
        raise PreparationError("local commits only permitted for HIROMU1015 remote")
    return url


def require_clean(root):
    if git(root, "diff", "--name-only").strip() or git(root, "diff", "--cached", "--name-only").strip():
        raise PreparationError("tracked/staged changes outside freeze")


def verify_blob(root, path, commit):
    target = root / path
    if target.is_symlink() or target.read_bytes() != git(root, "show", f"{commit}:{path}"):
        raise PreparationError(f"snapshot blob mismatch: {path}")


def verify_entries(directory, entries):
    if len(entries) != len({entry["path"] for entry in entries}):
        raise PreparationError("duplicate manifest entries")
    for entry in entries:
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise PreparationError("unsafe manifest path")
        path = directory / relative
        if path.is_symlink() or not path.is_file():
            raise PreparationError(f"missing or linked frozen file: {path}")
        if path.stat().st_size != entry["bytes"] or sha_file(path) != entry["sha256"]:
            raise PreparationError(f"frozen byte/hash mismatch: {path}")


def source_gate(root):
    require_clean(root)
    sealed_path = f"{DOC}/implementation_manifest.json"
    verify_blob(root, sealed_path, "HEAD")
    sealed = json.loads((root / sealed_path).read_text())
    content = sealed["content_commit"]
    git(root, "merge-base", "--is-ancestor", BASE, content)
    git(root, "merge-base", "--is-ancestor", content, "HEAD")
    if {entry["path"] for entry in sealed["files"]} != set(NEW_SOURCES):
        raise PreparationError("new source manifest file set mismatch")
    verify_entries(root, sealed["files"])
    for entry in sealed["files"]:
        verify_blob(root, entry["path"], content)
    inherited_path = root / PREP_DOC / "implementation_manifest.json"
    if sha_file(inherited_path) != "d78293705e830826e2e048a850ea97c5d35a45f01229b3491a411602bd93ffda":
        raise PreparationError("preparation source manifest changed")
    inherited = json.loads(inherited_path.read_text())
    verify_entries(root, inherited["files"])
    for entry in inherited["files"]:
        verify_blob(root, entry["path"], BASE)
    # Preserve the complete old planning directory, not only imported rules.
    names = git(root, "ls-tree", "-r", "--name-only", BASE, OLD).decode().splitlines()
    for name in names:
        verify_blob(root, name, BASE)
    return {"execution_HEAD": git(root, "rev-parse", "HEAD").decode().strip(),
            "implementation_commit": content, "preparation_verified_snapshot_commit": BASE,
            "input_origin_result_commit": INPUT_COMMIT,
            "implementation_manifest_sha256": sha_file(root / sealed_path),
            "new_sources": sealed["files"], "inherited_source_count": len(inherited["files"]),
            "inherited_sources_byte_identical": True, "old_formal_artifacts_unchanged": True}


def preparation_gate(root):
    directory = root / PREP
    manifest = directory / "manifest.json"
    if sha_file(manifest) != "ec3bd3d8b709d9e8128a1cd00bf31212bd1419e1e9fa82b10f171b7ccfc5d2af":
        raise PreparationError("preparation result manifest mismatch")
    entries = json.loads(manifest.read_text())["files"]
    verify_entries(directory, entries)
    for entry in entries:
        verify_blob(root, f"{PREP}/{entry['path']}", BASE)
    for name in INPUT_FILES:
        verify_blob(root, f"{PREP}/{name}", INPUT_COMMIT)
    complete = json.loads((directory / "COMPLETE.json").read_text())
    if complete["status"] != "hchain_input_reference_preparation_complete_execution_ready":
        raise PreparationError("preparation not complete")
    runtime = directory / ".runtime"
    entries = json.loads((directory / "runtime_manifest.json").read_text())["files"]
    found = {str(path.relative_to(runtime)) for path in runtime.rglob("*") if path.is_file()}
    if found != {entry["path"] for entry in entries} or len(entries) != 7:
        raise PreparationError("runtime file set mismatch")
    if runtime.is_symlink() or any(path.is_symlink() for path in runtime.rglob("*")):
        raise PreparationError("original runtime must not be linked or substituted")
    verify_entries(runtime, entries)
    if sum(entry["bytes"] for entry in entries) != 913581:
        raise PreparationError("runtime total bytes mismatch")
    return {"files": entries, "file_count": 7, "bytes": 913581,
            "runtime_manifest_sha256": sha_file(directory / "runtime_manifest.json"),
            "candidate_plan_sha256": sha_file(directory / "candidate_plan.csv"),
            "byte_identical": True, "runtime_copied_or_regenerated": False}


def load_plan(path):
    with Path(path).open(newline="") as handle:
        raw = list(csv.DictReader(handle))
    rows = []
    for item in raw:
        row = dict(item)
        for key in ("time", "ratio", "t_ref"):
            value = float.fromhex(item[f"{key}_hex"])
            if value.hex() != float(item[key]).hex() or not math.isfinite(value) or value <= 0:
                raise PreparationError("candidate binary64 coordinate mismatch")
            row[key] = value
        if (row["ratio"] * row["t_ref"]).hex() != row["time_hex"]:
            raise PreparationError("candidate reference product mismatch")
        row["K"], row["primary_m"] = int(item["K"]), int(item["primary_m"])
        rows.append(row)
    expected = [(system, ratio) for system in ("H2", "H4", "H6") for ratio in (.5, .65, .8)]
    if [(row["system"], row["ratio"]) for row in rows] != expected:
        raise PreparationError("nine ordered fixed coordinates required")
    if len({row["candidate_id"] for row in rows}) != 9:
        raise PreparationError("duplicate candidate")
    return rows


def finite_json(value, path="", missing=None):
    """Nonfinite width stays unavailable, never a narrower accepted value."""
    missing = [] if missing is None else missing
    if isinstance(value, dict):
        return {key: finite_json(item, f"{path}/{key}", missing) for key, item in value.items()}
    if isinstance(value, list):
        return [finite_json(item, f"{path}/{index}", missing) for index, item in enumerate(value)]
    if isinstance(value, float) and not math.isfinite(value):
        missing.append({"path": path, "original": str(value), "serialized": None})
        return None
    return value


class CoordinateActions:
    def __init__(self, adapter, time_value, maximum):
        self.adapter, self.time, self.maximum = adapter, time_value, maximum
        self.pf_count = self.h_count = 0

    def pf(self, vector):
        if self.pf_count >= self.maximum:
            raise PreparationError("coordinate PF action ceiling")
        self.pf_count += 1
        return self.adapter.pf(vector, self.time, kind="m1")

    def h(self, vector):
        if self.h_count >= self.maximum:
            raise PreparationError("coordinate H action ceiling")
        self.h_count += 1
        return self.adapter.h_matvec(vector)


class ReadBoundary:
    """Audited Python repository-data access, not an OS-level sandbox."""
    def __init__(self, root, allowed_reads, output):
        self.root, self.output = Path(root).resolve(), Path(output).resolve()
        self.allowed = {Path(path).resolve() for path in allowed_reads}
        self.reads, self.denials = set(), []
        self.enabled = True

    def hook(self, event, args):
        if not self.enabled or event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        if not path.is_relative_to(self.root):
            return  # interpreter/library/platform IO is not molecular input
        mode, flags = args[1], args[2]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(
            flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        in_output = path.is_relative_to(self.output)
        if (writing and not in_output) or (not writing and path not in self.allowed and not in_output):
            self.denials.append(str(path))
            raise PreparationError(f"repository data access outside allowlist: {path}")
        if not writing:
            self.reads.add(str(path))

    def payload(self, members):
        return {"mechanism": "Python open audit + named NPZ members + explicit Git subprocesses",
                "OS_hermeticity_claim": False, "repository_reads": sorted(self.reads),
                "denied_accesses": self.denials, "sanitized_member_reads": members,
                "truth_array_reads": 0, "historical_mixed_archives_opened": 0,
                "GPU_queries_allocations_kernels": 0, "CuPy_imported": "cupy" in sys.modules}


def make_bundle(directory, payload, marker, source, access, resource):
    directory = Path(directory)
    if directory.exists():
        raise PreparationError("freeze directory already exists; no overwrite/retry")
    directory.mkdir(parents=True)
    write_json(directory / "prediction.json", payload)
    digest = sha_file(directory / "prediction.json")
    write_json(directory / "FREEZE.json", {**marker, "prediction_sha256": digest})
    write_json(directory / "source_audit.json", source)
    write_json(directory / "access_audit.json", access)
    write_json(directory / "resource_audit.json", resource)
    (directory / "prediction.sha256").write_text(digest + "  prediction.json\n")
    entries = [{"path": name, "bytes": (directory / name).stat().st_size,
                "sha256": sha_file(directory / name)} for name in BUNDLE_FILES[:-1]]
    write_json(directory / "manifest.json", {"files": entries, "manifest_self_excluded": True})
    return digest


def verify_bundle(root, directory, commit):
    relative = str(Path(directory).relative_to(root))
    manifest = json.loads((directory / "manifest.json").read_text())
    if {row["path"] for row in manifest["files"]} != set(BUNDLE_FILES[:-1]):
        raise PreparationError("freeze manifest set mismatch")
    verify_entries(directory, manifest["files"])
    for name in BUNDLE_FILES:
        verify_blob(root, f"{relative}/{name}", commit)
    marker = json.loads((directory / "FREEZE.json").read_text())
    if marker["prediction_sha256"] != sha_file(directory / "prediction.json"):
        raise PreparationError("freeze prediction digest mismatch")


def commit_bundle(root, directory, message):
    check_remote(root)
    require_clean(root)
    relative = str(Path(directory).relative_to(root))
    paths = [f"{relative}/{name}" for name in BUNDLE_FILES]
    if set(path.name for path in directory.iterdir()) != set(BUNDLE_FILES):
        raise PreparationError("freeze directory file set must be exactly seven lightweight files")
    git(root, "add", "--", *paths)
    if set(git(root, "diff", "--cached", "--name-only").decode().splitlines()) != set(paths):
        raise PreparationError("freeze staged file set mismatch; stop without commit")
    git(root, "commit", "-m", message)
    commit = git(root, "rev-parse", "HEAD").decode().strip()
    if set(git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).decode().splitlines()) != set(paths):
        raise PreparationError("freeze commit contains unexpected files")
    verify_bundle(root, directory, commit)
    require_clean(root)
    return commit


def seal_source(root):
    require_clean(root)
    check_remote(root)
    content = git(root, "rev-parse", "HEAD").decode().strip()
    git(root, "merge-base", "--is-ancestor", BASE, content)
    entries = []
    for name in NEW_SOURCES:
        verify_blob(root, name, content)
        entries.append({"path": name, "bytes": (root / name).stat().st_size,
                        "sha256": sha_file(root / name), "origin_result_commit": content,
                        "verified_snapshot_commit": content})
    path = root / DOC / "implementation_manifest.json"
    if path.exists():
        raise PreparationError("source manifest already sealed")
    write_json(path, {"schema": "hchain_prediction_source_manifest_v1", "content_commit": content,
                      "preparation_snapshot_commit": BASE, "manifest_self_excluded": True,
                      "files": entries})
