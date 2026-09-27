#!/usr/bin/env python3
"""Same-physical-time backend-parity v1.2 wrapper for H5/H7 GPU direct."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any

import run_gpu_hchain_direct_h5_h7 as base
import run_gpu_hchain_direct_h5_h7_v1_1 as v1_1


PARITY_AMENDMENT = Path(
    "review_response/hchain_direct_gpu_h5_h7_parity_amendment_v1_2.json"
)
PARITY_AMENDMENT_MD = Path(
    "review_response/hchain_direct_gpu_h5_h7_parity_amendment_v1_2.md"
)
PARITY_AMENDMENT_SHA256 = (
    "04527c31289ee07888a4e9fee8875324249731ce85f8314ceae183b9434cad95"
)
_V1_1_SOURCE_PATHS = tuple(v1_1._BASE_SOURCE_PATHS) + (
    v1_1.IDENTITY_AMENDMENT,
    v1_1.IDENTITY_AMENDMENT_MD,
    Path("review_response/run_gpu_hchain_direct_h5_h7_v1_1.py"),
    Path("review_tests/test_gpu_hchain_direct_h5_h7_v1_1.py"),
)


def verify_parent_identity() -> dict[str, str]:
    identity = v1_1.verify_parent_identity()
    actual = base.sha256(base.PROJECT_ROOT / PARITY_AMENDMENT)
    if actual != PARITY_AMENDMENT_SHA256:
        raise RuntimeError(f"parity amendment SHA-256 mismatch: {actual}")
    identity["gpu_parity_amendment_v1_2_sha256"] = PARITY_AMENDMENT_SHA256
    return identity


def focused_test_args() -> list[str]:
    return [
        base.sys.executable,
        "-m",
        "pytest",
        "-q",
        "review_tests/test_gpu_hchain_direct_h5_h7_v1_2.py",
        "review_tests/test_hchain_direct_optimal_time_scaling.py",
        "review_tests/test_hchain_direct_optimal_time_scaling_partial_v1_2.py",
        "review_tests/test_hchain_direct_sector_v1_1.py",
        "review_tests/test_sector_pf.py",
    ]


def install_base_overrides() -> None:
    v1_1.install_base_overrides()
    base.SOURCE_PATHS = tuple(
        dict.fromkeys(
            _V1_1_SOURCE_PATHS
            + (
                PARITY_AMENDMENT,
                PARITY_AMENDMENT_MD,
                Path("review_response/run_gpu_hchain_direct_h5_h7_v1_2.py"),
                Path("review_tests/test_gpu_hchain_direct_h5_h7_v1_2.py"),
            )
        )
    )
    base.verify_parent_identity = verify_parent_identity
    base.focused_test_args = focused_test_args
    base.validate_phase_a = validate_phase_a
    base.initialize_output = initialize_output
    base.cache_key = cache_key
    base.update_h5_parity = update_h5_parity


def _copy_parity_amendment(output: Path) -> None:
    for source, name in (
        (PARITY_AMENDMENT, "gpu_parity_amendment_v1_2.json"),
        (PARITY_AMENDMENT_MD, "gpu_parity_amendment_v1_2.md"),
    ):
        source_path = base.PROJECT_ROOT / source
        destination = output / name
        if destination.exists():
            if base.sha256(destination) != base.sha256(source_path):
                raise RuntimeError(f"parity amendment copy mismatch: {destination}")
        else:
            shutil.copyfile(source_path, destination)


def _refresh_manifest(output: Path, schema: str, status: str) -> None:
    public = sorted(
        path
        for path in output.rglob("*")
        if path.is_file()
        and ".runtime" not in path.parts
        and path.name != "manifest.json"
    )
    base.parent._manifest(
        output,
        public,
        {
            "schema_version": schema,
            "status": status,
            "identity_amendment_v1_1_sha256": v1_1.IDENTITY_AMENDMENT_SHA256,
            "parity_amendment_v1_2_sha256": PARITY_AMENDMENT_SHA256,
            "created_at_utc": base.utc_now(),
        },
    )


def freeze_phase_a(output: Path, physical_gpu: int) -> None:
    install_base_overrides()
    base.freeze_phase_a(output, physical_gpu)
    v1_1._copy_amendment(output)
    _copy_parity_amendment(output)
    audit_path = output / "audit.json"
    audit = base.load_json(audit_path)
    audit.update(
        {
            "identity_amendment_v1_1_sha256": v1_1.IDENTITY_AMENDMENT_SHA256,
            "parity_amendment_v1_2_sha256": PARITY_AMENDMENT_SHA256,
            "corrected_expected_H5_group_count": 43,
            "parity_rule": "fresh exact CPU and GPU direct shifts compared at identical physical times",
            "prior_failed_parity_raw_reused_as_cache": False,
        }
    )
    base.write_json(audit_path, audit)
    marker_path = output / "PHASE_A_FROZEN"
    marker = base.load_json(marker_path)
    marker["identity_amendment_v1_1_sha256"] = v1_1.IDENTITY_AMENDMENT_SHA256
    marker["parity_amendment_v1_2_sha256"] = PARITY_AMENDMENT_SHA256
    base.write_json(marker_path, marker)
    _refresh_manifest(
        output,
        "hchain_direct_gpu_h5_h7_phase_a_manifest_v1_2",
        "phase_a_frozen_no_new_truth_generated_parity_amended",
    )


def validate_phase_a(phase_a: Path) -> dict[str, Any]:
    marker = v1_1.validate_phase_a(phase_a)
    if marker.get("parity_amendment_v1_2_sha256") != PARITY_AMENDMENT_SHA256:
        raise RuntimeError("Phase A parity amendment hash mismatch")
    copy = phase_a / "gpu_parity_amendment_v1_2.json"
    if not copy.exists() or base.sha256(copy) != PARITY_AMENDMENT_SHA256:
        raise RuntimeError("Phase A parity amendment copy mismatch")
    payload = base.load_json(copy)
    if payload["unchanged"][0] != "maximum absolute direct-shift difference threshold 1e-9 Ha":
        raise RuntimeError("parity shift threshold changed")
    verify_parent_identity()
    return marker


def initialize_output(output: Path, phase_a: Path, h_chain: int) -> None:
    v1_1._ORIGINAL_INITIALIZE_OUTPUT(output, phase_a, h_chain)
    v1_1._copy_amendment(output)
    _copy_parity_amendment(output)


def cache_key(
    phase_a: Path, h_chain: int, formula_key: str
) -> tuple[str, dict[str, Any]]:
    _, material = v1_1.cache_key(phase_a, h_chain, formula_key)
    material["gpu_parity_amendment_v1_2_sha256"] = PARITY_AMENDMENT_SHA256
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest(), material


def same_time_cpu_comparison(
    gpu_payload: dict[str, Any], formula_key: str
) -> dict[str, Any]:
    started = time.perf_counter()
    system = base.sector_v1_1.prepare_sparse_sector_system_v1_1(5)
    base.validate_system_identity(system, 5)
    label = str(base.FORMULAS[formula_key]["label"])
    gpu_points = base.formula_result(gpu_payload, 5, formula_key)["points"]
    previous_vector = None
    previous_shift = None
    differences: list[float] = []
    identity_matches: list[bool] = []
    for gpu_point in gpu_points:
        cpu_point, previous_vector, previous_shift = base.direct._direct_point(
            system,
            label,
            float(gpu_point["time"]),
            float(gpu_point["model_error_hartree"]),
            0.00015936001019904,
            previous_vector,
            previous_shift,
            "s2-cache",
        )
        for branch, shift_key in (
            ("maximum_ground_overlap_branch", "energy_shift_hartree"),
            ("continuously_tracked_branch", "unwrapped_energy_shift_hartree"),
        ):
            differences.append(
                abs(
                    float(gpu_point[branch][shift_key])
                    - float(cpu_point[branch][shift_key])
                )
            )
        gpu_same = abs(
            float(gpu_point["maximum_ground_overlap_branch"]["energy_shift_hartree"])
            - float(gpu_point["continuously_tracked_branch"]["unwrapped_energy_shift_hartree"])
        ) <= 1e-10
        cpu_same = abs(
            float(cpu_point["maximum_ground_overlap_branch"]["energy_shift_hartree"])
            - float(cpu_point["continuously_tracked_branch"]["unwrapped_energy_shift_hartree"])
        ) <= 1e-10
        identity_matches.append(gpu_same == cpu_same)
    maximum = max(differences)
    return {
        "comparison": "fresh exact CPU s2-cache versus GPU at identical physical times",
        "formula_key": formula_key,
        "point_count": len(gpu_points),
        "maximum_absolute_direct_shift_difference_hartree": maximum,
        "direct_shift_tolerance_hartree": 1e-9,
        "all_maximum_ground_vs_continuous_identity_relations_match": all(identity_matches),
        "pass": maximum <= 1e-9 and all(identity_matches),
        "elapsed_seconds": time.perf_counter() - started,
        "cpu_system_identity": {
            "num_groups": int(system["num_groups"]),
            "population_counts": list(system["sector"]["population_counts"]),
            "dimension": int(system["sector"]["dimension"]),
        },
    }


def update_h5_parity(
    output: Path,
    formula_key: str,
    unitary_result: dict[str, Any] | None,
) -> dict[str, Any]:
    path = output / "backend_parity.json"
    parity = base.load_json(path) if path.exists() else {
        "schema_version": "hchain_direct_gpu_h5_backend_parity_v1_2",
        "status": "incomplete",
    }
    raw = base.load_json(output / "raw" / f"H5_{formula_key}.json")
    same_time = same_time_cpu_comparison(raw, formula_key)
    parent_schedule = base.compare_raw_to_parent(raw, formula_key)
    parent_schedule["gate_role"] = (
        "diagnostic_only_because_parent_and_fresh_physical_times_differ"
    )
    summary = base.selected_summary(raw, 5, formula_key)
    parity[formula_key] = {
        "same_physical_time_cpu_gpu_comparison": same_time,
        "parent_raw_schedule_diagnostic": parent_schedule,
        "summary": summary,
    }
    if unitary_result is not None:
        parity["unitary_gpu_cpu"] = unitary_result
    m5 = parity.get("m5")
    if m5 is not None:
        selected_pass = m5["summary"].get("relative_t_grid_star") == 1.35
        m5["selected_relative_time_pass"] = selected_pass
        m5["pass"] = bool(
            selected_pass
            and m5["same_physical_time_cpu_gpu_comparison"]["pass"]
            and parity.get("unitary_gpu_cpu", {}).get("pass", False)
        )
    y8 = parity.get("y8")
    if y8 is not None:
        disagreement = y8["summary"]["numerical"][
            "maximum_branch_shift_disagreement_hartree"
        ]
        y8["known_branch_disagreement_reproduced"] = disagreement > 1e-10
        y8["pass"] = bool(
            y8["same_physical_time_cpu_gpu_comparison"]["pass"]
            and y8["known_branch_disagreement_reproduced"]
            and y8["summary"]["status"] == "not_scorable_gate_failure"
        )
    parity["overall_pass"] = bool(
        parity.get("m5", {}).get("pass", False)
        and parity.get("y8", {}).get("pass", False)
    )
    parity["status"] = "passed" if parity["overall_pass"] else "incomplete_or_failed"
    parity["parity_amendment_v1_2_sha256"] = PARITY_AMENDMENT_SHA256
    parity["updated_at_utc"] = base.utc_now()
    base.write_json(path, parity)
    return parity


def _register_amendments_in_raw(output: Path, h_chain: int, formula_key: str) -> None:
    path = output / "raw" / f"H{h_chain}_{formula_key}.json"
    payload = base.load_json(path)
    registered = payload.setdefault("registered_amendments", {})
    registered["gpu_identity_v1_1_sha256"] = v1_1.IDENTITY_AMENDMENT_SHA256
    registered["gpu_parity_v1_2_sha256"] = PARITY_AMENDMENT_SHA256
    base.write_json(path, payload)


def run_cell(
    phase_a: Path,
    output: Path,
    h_chain: int,
    formula_key: str,
    physical_gpu: int,
    h5_output: Path | None,
) -> dict[str, Any]:
    install_base_overrides()
    result = base.run_cell(
        phase_a,
        output,
        h_chain,
        formula_key,
        physical_gpu,
        h5_output,
    )
    _register_amendments_in_raw(output, h_chain, formula_key)
    return result


def analyze_outputs(
    phase_a: Path,
    h5_output: Path,
    h7_output: Path | None,
    full_test_log: Path | None,
) -> dict[str, Any]:
    install_base_overrides()
    result = base.analyze_outputs(phase_a, h5_output, h7_output, full_test_log)
    outputs = [h5_output] + ([h7_output] if h7_output is not None else [])
    for output in outputs:
        assert output is not None
        audit_path = output / "audit.json"
        audit = base.load_json(audit_path)
        audit.update(
            {
                "gpu_identity_amendment_v1_1_sha256": v1_1.IDENTITY_AMENDMENT_SHA256,
                "gpu_parity_amendment_v1_2_sha256": PARITY_AMENDMENT_SHA256,
                "expected_H5_group_count": 43,
                "parity_rule": "fresh exact CPU and GPU shifts at identical physical times",
            }
        )
        base.write_json(audit_path, audit)
        report_path = output / "report.md"
        report = report_path.read_text(encoding="utf-8")
        report += (
            "\nIdentity amendment v1.1 corrected only the expected H5 group "
            "count from 45 to 43. Parity amendment v1.2 compares exact CPU "
            "and GPU shifts at identical physical times without changing the "
            "1e-9 Ha threshold.\n"
        )
        report_path.write_text(report, encoding="utf-8")
        _refresh_manifest(
            output,
            "hchain_direct_gpu_h5_h7_manifest_v1_2",
            str(result["status"]),
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze-phase-a")
    freeze.add_argument("--output", type=Path, required=True)
    freeze.add_argument("--gpu", type=int, default=1)
    cell = subparsers.add_parser("run-cell")
    cell.add_argument("--phase-a", type=Path, required=True)
    cell.add_argument("--output", type=Path, required=True)
    cell.add_argument("--system", type=int, choices=[5, 7], required=True)
    cell.add_argument("--formula", choices=["m5", "y8"], required=True)
    cell.add_argument("--gpu", type=int, default=1)
    cell.add_argument("--h5-output", type=Path)
    tests = subparsers.add_parser("run-tests")
    tests.add_argument("--kind", choices=["focused", "all"], required=True)
    tests.add_argument("--log", type=Path, required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--phase-a", type=Path, required=True)
    analyze.add_argument("--h5-output", type=Path, required=True)
    analyze.add_argument("--h7-output", type=Path)
    analyze.add_argument("--full-test-log", type=Path)
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path if path.is_absolute() else base.PROJECT_ROOT / path


def main() -> None:
    args = parse_args()
    if args.command == "freeze-phase-a":
        freeze_phase_a(resolved(args.output), args.gpu)
        result: Any = {
            "status": "phase_a_frozen_parity_amended",
            "output": str(resolved(args.output)),
        }
    elif args.command == "run-cell":
        result = run_cell(
            resolved(args.phase_a),
            resolved(args.output),
            args.system,
            args.formula,
            args.gpu,
            resolved(args.h5_output) if args.h5_output else None,
        )
    elif args.command == "run-tests":
        install_base_overrides()
        result = base.execute_tests(args.kind, resolved(args.log))
    elif args.command == "analyze":
        result = analyze_outputs(
            resolved(args.phase_a),
            resolved(args.h5_output),
            resolved(args.h7_output) if args.h7_output else None,
            resolved(args.full_test_log) if args.full_test_log else None,
        )
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
