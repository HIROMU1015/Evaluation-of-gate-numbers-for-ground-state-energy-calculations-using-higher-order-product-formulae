#!/usr/bin/env python3
"""Read-only preflight for the second-study safe-time-domain protocol.

This command verifies the frozen protocol, Git ancestry, and byte identity of
the committed first-study evidence.  It deliberately does not construct a new
Hamiltonian or state and does not evaluate either the Phase A proxy or Phase B
direct truth.  The GPU-server-wide independence search remains a separate,
mandatory gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

PROTOCOL_COMMIT = "804331ecc976b83ae880940719706c11999247bc"
EXPECTED_PROTOCOL_SHA256 = (
    "a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b"
)
EXPECTED_REMOTE = (
    "git@github.com:HIROMU1015/"
    "Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-"
    "higher-order-product-formulae.git"
)
DEFAULT_AUDIT = Path(
    "review_response/second_study_safe_time_domain_source_leakage_audit.json"
)
PROTOCOL_PATH = Path(
    "review_response/second_study_safe_time_domain_protocol.json"
)
PROTOCOL_HASH_PATH = Path(str(PROTOCOL_PATH) + ".sha256")


class PreflightError(RuntimeError):
    """Raised when a frozen source-identity check fails."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(
    project_root: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=False,
        capture_output=True,
    )
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise PreflightError(f"git {' '.join(args)} failed: {detail}")
    return result


def _git_text(project_root: Path, *args: str) -> str:
    return _git(project_root, *args).stdout.decode("utf-8").strip()


def _git_blob_sha256(project_root: Path, commit: str, relative: str) -> str:
    return sha256_bytes(_git(project_root, "show", f"{commit}:{relative}").stdout)


def _is_ancestor(project_root: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    return (
        _git(
            project_root,
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
            check=False,
        ).returncode
        == 0
    )


def _record(
    checks: dict[str, dict[str, Any]],
    check_id: str,
    measured: Any,
    expected: Any,
) -> None:
    checks[check_id] = {
        "measured": measured,
        "expected": expected,
        "passed": measured == expected,
    }


def _record_file_and_blob(
    checks: dict[str, dict[str, Any]],
    project_root: Path,
    check_prefix: str,
    relative: str,
    expected_sha256: str,
    source_commit: str,
) -> None:
    path = project_root / relative
    _record(checks, f"{check_prefix}:exists", path.is_file(), True)
    if not path.is_file():
        return
    _record(
        checks,
        f"{check_prefix}:working_tree_sha256",
        sha256_file(path),
        expected_sha256,
    )
    _record(
        checks,
        f"{check_prefix}:source_commit_blob_sha256",
        _git_blob_sha256(project_root, source_commit, relative),
        expected_sha256,
    )


def _validate_git_identity(
    project_root: Path,
    audit: dict[str, Any],
    checks: dict[str, dict[str, Any]],
) -> dict[str, str]:
    identity = audit["git_identity"]
    head = _git_text(project_root, "rev-parse", "HEAD")
    remote = _git_text(project_root, "remote", "get-url", "origin")
    _record(checks, "git:origin", remote, EXPECTED_REMOTE)
    _record(
        checks,
        "git:protocol_commit_is_ancestor",
        _is_ancestor(project_root, PROTOCOL_COMMIT),
        True,
    )
    _record(
        checks,
        "git:base_is_ancestor",
        _is_ancestor(project_root, identity["base_commit"]),
        True,
    )
    ancestry_keys = (
        "evidence_commit",
        "first_study_s4_result",
        "regret_result",
        "completion_result",
    )
    for key in ancestry_keys:
        row = identity[key]
        _record(
            checks,
            f"git:{key}_ancestry",
            _is_ancestor(project_root, row["commit"]),
            row["is_ancestor_of_base"],
        )
    s0 = identity["first_study_s0_result"]
    _record(
        checks,
        "git:first_study_s0_result_ancestry",
        _is_ancestor(project_root, s0["commit"]),
        s0["is_ancestor_of_base"],
    )
    return {"head": head, "origin": remote}


def _validate_protocol_and_audit(
    project_root: Path,
    protocol: dict[str, Any],
    protocol_sha256: str,
    audit_path: Path,
    audit: dict[str, Any],
    checks: dict[str, dict[str, Any]],
) -> None:
    relative_audit = str(audit_path.relative_to(project_root))
    _record(
        checks,
        "protocol:declared_audit_path",
        protocol["source_identity"]["audit_path"],
        relative_audit,
    )
    _record(
        checks,
        "protocol:working_tree_sha256",
        protocol_sha256,
        EXPECTED_PROTOCOL_SHA256,
    )
    _record(
        checks,
        "protocol:sidecar_sha256",
        (project_root / PROTOCOL_HASH_PATH).read_text(encoding="utf-8").split()[
            0
        ],
        EXPECTED_PROTOCOL_SHA256,
    )
    _record(
        checks,
        "protocol:commit_blob_sha256",
        _git_blob_sha256(
            project_root,
            PROTOCOL_COMMIT,
            str(PROTOCOL_PATH),
        ),
        EXPECTED_PROTOCOL_SHA256,
    )
    _record(
        checks,
        "audit:commit_blob_sha256",
        _git_blob_sha256(project_root, PROTOCOL_COMMIT, relative_audit),
        sha256_file(audit_path),
    )
    _record(
        checks,
        "audit:no_new_computation",
        audit["new_computation"],
        {
            "direct_truth_coordinates": 0,
            "phase_a_proxy_points": 0,
            "new_hamiltonians": 0,
            "new_states": 0,
            "new_fits": 0,
        },
    )
    _record(
        checks,
        "audit:fixed_facts_passed",
        audit["fixed_fact_reproduction"]["all_passed"],
        True,
    )
    _record(
        checks,
        "audit:local_independence_search_passed",
        audit["data_use_ledger"]["local_search"]["passed"],
        True,
    )


def _validate_tracked_inputs(
    project_root: Path,
    audit: dict[str, Any],
    checks: dict[str, dict[str, Any]],
) -> None:
    base_commit = audit["git_identity"]["base_commit"]
    for row in audit["input_files"]["tracked_at_base"]:
        relative = row["path"]
        _record_file_and_blob(
            checks,
            project_root,
            f"input:{relative}",
            relative,
            row["sha256"],
            base_commit,
        )


def _validate_first_study_artifacts(
    project_root: Path,
    audit: dict[str, Any],
    checks: dict[str, dict[str, Any]],
) -> None:
    identities = audit["first_study_artifact_identity"]
    for stage in ("s0", "s4"):
        spec = identities[stage]
        commit = spec["result_commit"]
        for filename, value in spec["files"].items():
            expected = value["sha256"] if isinstance(value, dict) else value
            relative = f"{spec['artifact']}/{filename}"
            _record_file_and_blob(
                checks,
                project_root,
                f"artifact:{stage}:{filename}",
                relative,
                expected,
                commit,
            )

    regret = identities["regret"]
    _record_file_and_blob(
        checks,
        project_root,
        "artifact:regret:summary.json",
        f"{regret['artifact']}/summary.json",
        regret["summary_sha256"],
        audit["git_identity"]["regret_result"]["commit"],
    )

    completion = identities["completion"]
    completion_commit = audit["git_identity"]["completion_result"]["commit"]
    completion_files = {
        "summary.json": completion["summary_sha256"],
        "cost_factor_decomposition.csv": completion[
            "cost_factor_decomposition_sha256"
        ],
        "s4_cost_definition_audit.json": completion[
            "s4_beta_1_2_audit_sha256"
        ],
    }
    for filename, expected in completion_files.items():
        _record_file_and_blob(
            checks,
            project_root,
            f"artifact:completion:{filename}",
            f"{completion['artifact']}/{filename}",
            expected,
            completion_commit,
        )


def build_preflight_report(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    audit_path = project_root / DEFAULT_AUDIT
    if not audit_path.is_file():
        raise PreflightError(f"missing frozen source/leakage audit: {audit_path}")
    protocol_path = project_root / PROTOCOL_PATH
    protocol_sha256 = sha256_file(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    checks: dict[str, dict[str, Any]] = {}
    git_identity = _validate_git_identity(project_root, audit, checks)
    _validate_protocol_and_audit(
        project_root,
        protocol,
        protocol_sha256,
        audit_path,
        audit,
        checks,
    )
    _validate_tracked_inputs(project_root, audit, checks)
    _validate_first_study_artifacts(project_root, audit, checks)

    failed = sorted(key for key, row in checks.items() if not row["passed"])
    gpu_pending = [
        "GPU-server-wide LiF/HCl prior numeric-result search",
        "GPU source-root identity and dependency check",
        "GPU free memory >= 8 GiB",
    ]
    return {
        "schema": "second_study_safe_time_domain_local_preflight_v1",
        "status": (
            "failed_local_preflight"
            if failed
            else "local_preflight_pass_gpu_server_preflight_pending"
        ),
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_sha256": protocol_sha256,
        "head": git_identity["head"],
        "origin": git_identity["origin"],
        "read_only": True,
        "new_computation": audit["new_computation"],
        "checks": checks,
        "check_count": len(checks),
        "failed_checks": failed,
        "gpu_server_pending": gpu_pending,
        "phase_a_authorized": False,
        "phase_b_authorized": False,
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output
    if not output.is_absolute():
        output = args.project_root / output
    if output.exists():
        raise PreflightError(f"refusing to overwrite existing output: {output}")
    report = build_preflight_report(args.project_root)
    _atomic_json(output, report)
    if report["failed_checks"]:
        raise PreflightError(
            "local source-identity preflight failed: "
            + ", ".join(report["failed_checks"])
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
