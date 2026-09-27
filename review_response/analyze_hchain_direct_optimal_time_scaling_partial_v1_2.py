#!/usr/bin/env python3
"""Analyze the user-requested H-chain partial run through H6.

This script performs no Hamiltonian construction, PF action, or direct
diagonalization.  It accepts only the completed, protocol-identical H2/H4/H5/H6
raw jobs, verifies that the preserved H7 runtime has zero completed direct
points, and applies the parent protocol's unchanged scoring functions.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

import run_hchain_direct_optimal_time_scaling as parent
import run_hchain_direct_optimal_time_scaling_v1_1 as v1_1


EXPECTED_PARENT_PROTOCOL_SHA256 = (
    "12d10562cf481b836242786462184d8a6ffb342153404c9bf84ff4d5ca836ab9"
)
EXPECTED_SECTOR_AMENDMENT_SHA256 = (
    "5ca0ea30f9ad08bc7e4a54fcd8bab8f50195752dcaf3717c219281a458b0122e"
)
EXPECTED_PARTIAL_AMENDMENT_SHA256 = (
    "526bdede05c1b39d0fab21e062b39a48284a1338fd51bc3c94fd3488732c70ff"
)
COMPLETED_SIZES = (2, 4, 5, 6)
PRIMARY_SIZES = (2, 4, 6)
FORMULA_KEYS = ("m5", "y8")


def _runtime_direct_point_count(payload: dict[str, Any], system_id: str) -> int:
    count = 0
    system = payload.get("results", {}).get(system_id, {})
    for formula in system.get("results", {}).values():
        count += len(formula.get("points", []))
    return count


def _report(analysis: dict[str, Any]) -> str:
    lines = [
        "# H-chain direct optimal-time scaling: partial result through H6",
        "",
        f"- Status: `{analysis['status']}`",
        f"- Decision: `{analysis['decision']}`",
        f"- Parent protocol SHA-256: `{analysis['protocol_sha256']}`",
        f"- Sector amendment SHA-256: `{analysis['sector_amendment_v1_1_sha256']}`",
        f"- Partial-stop amendment SHA-256: `{analysis['partial_amendment_v1_2_sha256']}`",
        "- Scope: H2/H4/H6 form the even-family scaling analysis; H5 is descriptive only; H7 has zero completed direct points.",
        "",
        "## Direct grid optima",
        "",
        "| system | family | PF | t_ana | t_grid* | t_grid*/t_ana | min cost | 1% interval | zero-crossing assisted | status |",
        "|---|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for system_id, formula_map in analysis["systems"].items():
        family = analysis["system_families"][system_id]
        for formula_key, row in formula_map.items():
            interval = row.get("near_optimal_component")
            if interval is None:
                lines.append(
                    f"| {system_id} | {family} | {formula_key} | — | — | — | — | — | — | {row['status']} |"
                )
                continue
            lines.append(
                "| "
                f"{system_id} | {family} | {formula_key} | "
                f"{row['analytic_optimal_time']:.9g} | {row['t_grid_star']:.9g} | "
                f"{row['relative_t_grid_star']:.3f} | {row['minimum_direct_cost']:.9g} | "
                f"[{interval['relative_time_start']:.3f}, {interval['relative_time_stop']:.3f}] | "
                f"{row['zero_crossing_assisted_near_optimum']} | {row['status']} |"
            )
    lines.extend(
        [
            "",
            "## Even-family scaling decisions",
            "",
            "| PF | exponent b | power-law LOO max error | constant LOO max error | decision |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for formula_key, row in analysis["scaling"].items():
        if "power_law_fit" not in row:
            lines.append(f"| {formula_key} | — | — | — | {row['decision']} |")
        else:
            lines.append(
                f"| {formula_key} | {row['power_law_fit']['b']:.6g} | "
                f"{row['power_law_leave_one_out']['maximum_relative_error']:.3%} | "
                f"{row['constant_leave_one_out']['maximum_relative_error']:.3%} | "
                f"{row['decision']} |"
            )
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- This is partial completion through H6, not completion of the parent H2/H4/H5/H6/H7 protocol.",
            "- `t_grid*` is a discrete minimum in the fixed 0.20–1.70 `t_ana` domain, not a global optimum over all positive time.",
            "- H5 is not pooled with the even neutral singlet family, and one odd-family size cannot support a scaling fit.",
            "- H7 and H8 were not executed. The H2/H4/H6 relation is retrospective small-system evidence only.",
            "- The cost is the repository continuous QPE precision-allocation proxy, not a complete end-to-end QPE implementation cost.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    output = (
        args.output if args.output.is_absolute() else project_root / args.output
    ).resolve()
    protocol_path = project_root / "review_response/hchain_direct_optimal_time_scaling_protocol.json"
    sector_amendment_path = project_root / "review_response/hchain_direct_optimal_time_scaling_amendment_v1_1.json"
    partial_amendment_path = project_root / "review_response/hchain_direct_optimal_time_scaling_partial_stop_amendment_v1_2.json"
    identities = (
        (protocol_path, EXPECTED_PARENT_PROTOCOL_SHA256),
        (sector_amendment_path, EXPECTED_SECTOR_AMENDMENT_SHA256),
        (partial_amendment_path, EXPECTED_PARTIAL_AMENDMENT_SHA256),
    )
    for path, expected in identities:
        if parent._sha256(path) != expected:
            raise RuntimeError(f"fixed identity mismatch: {path}")

    derived_names = (
        "analysis_partial_v1_2.json",
        "audit_partial_v1_2.json",
        "report_partial_v1_2.md",
        "manifest_partial_v1_2.json",
        "PARTIAL_H6_COMPLETE",
    )
    if any((output / name).exists() for name in derived_names):
        raise RuntimeError("refusing to overwrite an existing partial analysis")

    protocol = parent._load_json(protocol_path)
    partial_amendment = parent._load_json(partial_amendment_path)
    grid = parent._grid_from_protocol(protocol)
    expected_points = int(partial_amendment["expected_points_per_system_formula"])
    summaries: dict[str, dict[str, Any]] = {}
    families = {
        str(row["id"]): str(row["family"])
        for row in protocol["systems"]["included"]
    }
    raw_paths: list[Path] = []
    maximums = {
        "unitarity": 0.0,
        "schur": 0.0,
        "branch_shift_disagreement_hartree": 0.0,
    }
    minimum_previous_overlap = 1.0
    minimum_ground_overlap = 1.0
    all_gate_pass = True
    for size in COMPLETED_SIZES:
        system_id = f"H{size}"
        formula_map: dict[str, Any] = {}
        for formula_key in FORMULA_KEYS:
            path = output / "raw" / parent._job_name(size, formula_key)
            payload = parent._load_json(path)
            if not v1_1._v1_1_job_matches(
                payload,
                protocol_sha256=EXPECTED_PARENT_PROTOCOL_SHA256,
                amendment_sha256=EXPECTED_SECTOR_AMENDMENT_SHA256,
                grid=grid,
                h_chain=size,
                formula_key=formula_key,
            ):
                raise RuntimeError(f"raw v1.1 identity mismatch: {path}")
            formula_result = payload["results"][system_id]["results"][
                parent.LABEL_BY_KEY[formula_key]
            ]
            if len(formula_result["points"]) != expected_points:
                raise RuntimeError(f"unexpected completed point count: {path}")
            summary = parent.summarize_formula(formula_result, protocol)
            formula_map[formula_key] = summary
            all_gate_pass &= summary.get("status") == "scorable"
            numerical = summary.get("numerical")
            if numerical is not None:
                maximums["unitarity"] = max(
                    maximums["unitarity"],
                    numerical["maximum_unitarity_frobenius_residual"],
                )
                maximums["schur"] = max(
                    maximums["schur"],
                    numerical["maximum_schur_off_diagonal_frobenius_residual"],
                )
                maximums["branch_shift_disagreement_hartree"] = max(
                    maximums["branch_shift_disagreement_hartree"],
                    numerical["maximum_branch_shift_disagreement_hartree"],
                )
                minimum_previous_overlap = min(
                    minimum_previous_overlap, numerical["minimum_previous_overlap"]
                )
                minimum_ground_overlap = min(
                    minimum_ground_overlap, numerical["minimum_ground_overlap"]
                )
            raw_paths.append(path)
        summaries[system_id] = formula_map

    h7_runtime_path = output / ".runtime/H7_m5.json"
    if not h7_runtime_path.exists():
        raise RuntimeError("preserved H7 interrupted runtime is missing")
    h7_runtime = parent._load_json(h7_runtime_path)
    h7_direct_points = _runtime_direct_point_count(h7_runtime, "H7")
    if h7_direct_points != int(
        partial_amendment["expected_H7_completed_direct_point_count"]
    ):
        raise RuntimeError("H7 runtime contains a completed direct point")
    summaries["H7"] = {
        key: {"status": "not_executed_user_stop", "point_count": 0}
        for key in FORMULA_KEYS
    }

    scaling = {
        key: parent.scaling_summary(key, summaries, protocol)
        for key in FORMULA_KEYS
    }
    decisions = [row["decision"] for row in scaling.values()]
    if not all_gate_pass:
        status = "failed_numerical_or_boundary_validation"
        decision = "not_scorable_due_to_numerical_or_boundary_gate"
    elif all(
        item == "small_system_predictable_requires_H8_holdout"
        for item in decisions
    ):
        status = "complete_partial_h6_analysis"
        decision = "small_system_predictable_requires_H8_holdout"
    else:
        status = "complete_partial_h6_analysis"
        decision = "no_common_predictable_scaling_on_current_sizes"

    completed_direct_points = sum(
        int(row["point_count"])
        for system_id, formula_map in summaries.items()
        if system_id != "H7"
        for row in formula_map.values()
    )
    primary_direct_points = sum(
        int(summaries[f"H{size}"][key]["point_count"])
        for size in PRIMARY_SIZES
        for key in FORMULA_KEYS
    )
    if completed_direct_points != int(
        partial_amendment["expected_completed_direct_point_count"]
    ):
        raise RuntimeError("completed direct-point total differs from amendment")
    if primary_direct_points != int(
        partial_amendment["expected_primary_scaling_direct_point_count"]
    ):
        raise RuntimeError("primary direct-point total differs from amendment")

    analysis = {
        "schema_version": "hchain_direct_optimal_time_scaling_partial_analysis_v1_2",
        "status": status,
        "decision": decision,
        "protocol_sha256": EXPECTED_PARENT_PROTOCOL_SHA256,
        "sector_amendment_v1_1_sha256": EXPECTED_SECTOR_AMENDMENT_SHA256,
        "partial_amendment_v1_2_sha256": EXPECTED_PARTIAL_AMENDMENT_SHA256,
        "created_at_utc": parent._utc_now(),
        "systems": summaries,
        "system_families": families,
        "scaling": scaling,
        "audit_summary": {
            "completed_systems": [f"H{size}" for size in COMPLETED_SIZES],
            "primary_scaling_systems": [f"H{size}" for size in PRIMARY_SIZES],
            "descriptive_only_systems": ["H5"],
            "not_executed_systems": ["H7"],
            "completed_direct_point_count": completed_direct_points,
            "primary_scaling_direct_point_count": primary_direct_points,
            "H5_descriptive_direct_point_count": 62,
            "H7_completed_direct_point_count": h7_direct_points,
            "all_completed_formula_numerical_and_boundary_gates_pass": all_gate_pass,
            "maximum_unitarity_frobenius_residual": maximums["unitarity"],
            "maximum_schur_off_diagonal_frobenius_residual": maximums["schur"],
            "maximum_branch_shift_disagreement_hartree": maximums[
                "branch_shift_disagreement_hartree"
            ],
            "minimum_previous_overlap": minimum_previous_overlap,
            "minimum_ground_overlap": minimum_ground_overlap,
            "prior_direct_results_reused": False,
            "H7_executed": False,
            "H8_holdout_executed": False,
        },
    }
    analysis_path = output / "analysis_partial_v1_2.json"
    audit_path = output / "audit_partial_v1_2.json"
    report_path = output / "report_partial_v1_2.md"
    manifest_path = output / "manifest_partial_v1_2.json"
    parent._write_json(analysis_path, analysis)
    report_path.write_text(_report(analysis), encoding="utf-8")
    audit = {
        "schema_version": "hchain_direct_optimal_time_scaling_partial_audit_v1_2",
        "status": status,
        "git_head": parent._git_value(project_root, "rev-parse", "HEAD"),
        "git_branch": parent._git_value(project_root, "branch", "--show-current"),
        "protocol_sha256": EXPECTED_PARENT_PROTOCOL_SHA256,
        "sector_amendment_v1_1_sha256": EXPECTED_SECTOR_AMENDMENT_SHA256,
        "partial_amendment_v1_2_sha256": EXPECTED_PARTIAL_AMENDMENT_SHA256,
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "platform": platform.platform(),
        },
        "environment": {
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"),
        },
        "H7_interrupted_runtime": {
            "path": str(h7_runtime_path.relative_to(output)),
            "sha256": parent._sha256(h7_runtime_path),
            "status": h7_runtime.get("status"),
            "completed_direct_point_count": h7_direct_points,
            "included_in_analysis_or_manifest": False,
        },
        **analysis["audit_summary"],
    }
    parent._write_json(audit_path, audit)

    for source, name, expected in (
        (protocol_path, "protocol.json", EXPECTED_PARENT_PROTOCOL_SHA256),
        (sector_amendment_path, "amendment_v1_1.json", EXPECTED_SECTOR_AMENDMENT_SHA256),
        (partial_amendment_path, "amendment_partial_v1_2.json", EXPECTED_PARTIAL_AMENDMENT_SHA256),
    ):
        destination = output / name
        if destination.exists():
            if parent._sha256(destination) != expected:
                raise RuntimeError(f"output identity copy mismatch: {destination}")
        else:
            shutil.copyfile(source, destination)

    public_files = [
        output / "protocol.json",
        output / "amendment_v1_1.json",
        output / "amendment_partial_v1_2.json",
        analysis_path,
        report_path,
        audit_path,
        *raw_paths,
    ]
    entries = [
        {
            "path": str(path.relative_to(output)),
            "sha256": parent._sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(public_files)
    ]
    parent._write_json(
        manifest_path,
        {
            "schema_version": "hchain_direct_optimal_time_scaling_partial_manifest_v1_2",
            "status": status,
            "protocol_sha256": EXPECTED_PARENT_PROTOCOL_SHA256,
            "sector_amendment_v1_1_sha256": EXPECTED_SECTOR_AMENDMENT_SHA256,
            "partial_amendment_v1_2_sha256": EXPECTED_PARTIAL_AMENDMENT_SHA256,
            "created_at_utc": parent._utc_now(),
            "files": entries,
        },
    )
    if status == "complete_partial_h6_analysis":
        (output / "PARTIAL_H6_COMPLETE").write_text(status + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
