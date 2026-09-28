#!/usr/bin/env python3
"""Read-only D0 arithmetic summary; never constructs a Hamiltonian or PF."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

EVIDENCE_COMMIT = "a134ba3950a521225a14c46943d0dbe469425e00"
REVIEW_INDEX = Path("review_response/pf_research_direction_review_materials_20260928.json")
R1_ROOT = Path("artifacts/server_pf_candidate_validation_r1_20260928_fba3383")
R0_ROOT = Path("artifacts/pf_candidate_validation_r0_20260928_05649f1")
SECOND_PROTOCOL = Path("review_response/second_study_safe_time_domain_protocol.json")
PILOT_PROTOCOL = Path("review_response/pf_spectral_information_pilot_protocol_draft.json")
AUTHORIZATION = Path("review_response/pf_spectral_information_pilot_authorization.json")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def gamma_required(epsilon: float, estimate: float, direct_error: float) -> float:
    denominator = epsilon - direct_error
    if denominator <= 0:
        return math.inf
    return (epsilon - abs(estimate)) / denominator

def arg_minus_imag(real: float, imag: float, time: float) -> float:
    return math.atan2(imag, real) / time - imag / time

def git_output(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    ).stdout.strip()

def verify_sources(root: Path) -> tuple[str, list[dict[str, Any]]]:
    head = git_output(root, "rev-parse", "HEAD")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", EVIDENCE_COMMIT, head],
        cwd=root, check=True, capture_output=True,
    )
    index = load_json(root / REVIEW_INDEX)
    if index["authorization"]["r2_authorized"]:
        raise RuntimeError("R2 unexpectedly authorized")
    verified: list[dict[str, Any]] = []
    for material in index["materials"]:
        path = root / material["path"]
        if not path.is_file():
            raise RuntimeError(f"missing indexed material: {material['path']}")
        actual = sha256_file(path)
        expected = material.get("sha256")
        if expected is not None and actual != expected:
            raise RuntimeError(f"indexed material hash mismatch: {material['path']}")
        verified.append({
            "path": material["path"], "sha256": actual,
            "expected_sha256": expected, "passed": expected is None or actual == expected,
            "role": material["role"],
        })
    fixed = [
        (SECOND_PROTOCOL, index["fixed_hashes"]["second_study_protocol_sha256"]),
        (Path("review_response/pf_candidate_validation_r1_protocol.json"),
         index["fixed_hashes"]["r1_protocol_sha256"]),
        (R1_ROOT / "manifest.json", index["fixed_hashes"]["r1_result_manifest_sha256"]),
    ]
    for rel, expected in fixed:
        actual = sha256_file(root / rel)
        if actual != expected:
            raise RuntimeError(f"fixed hash mismatch: {rel}")
        verified.append({"path": str(rel), "sha256": actual,
                         "expected_sha256": expected, "passed": True, "role": "fixed_identity"})
    decision = load_json(root / R1_ROOT / "decision.json")
    if decision["status"] != "r1_complete_stop_for_research_direction_review":
        raise RuntimeError("unexpected R1 status")
    if decision["r2_authorized"] or decision["new_direct_truth_coordinate_count"] != 0:
        raise RuntimeError("R1 boundary violated")
    auth = load_json(root / AUTHORIZATION)
    if auth["spectral_pilot_authorized"] or auth["d1_authorized"] or auth["r2_authorized"]:
        raise RuntimeError("scientific execution unexpectedly authorized")
    return head, verified

def build_rows(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    second = load_json(root / SECOND_PROTOCOL)
    epsilon = float(second["scope"]["target_error_hartree"])
    inherited_gamma = float(second["scope"]["budget_multiplier_gamma"])
    coords = load_csv(root / R1_ROOT / "coordinate_proxy_results.csv")
    decomp = load_csv(root / R1_ROOT / "strategy_cause_decomposition.csv")
    ledger = load_csv(root / R0_ROOT / "failure_ledger.csv")
    if len(coords) != 10 or len(decomp) != 16 or len(ledger) != 16:
        raise RuntimeError("frozen row count mismatch")
    d_by_key = {(r["condition"], r["strategy"]): r for r in decomp}
    l_by_key = {(r["condition"], r["strategy"]): r for r in ledger}
    if set(d_by_key) != set(l_by_key):
        raise RuntimeError("R0/R1 strategy key mismatch")
    allowance_by_coord: dict[tuple[str, str], list[float]] = {}
    for row in decomp:
        allowance_by_coord.setdefault((row["condition"], row["time_hex"]), []).append(
            float(row["original_allowed_underestimation_hartree"])
        )
    coordinate_rows: list[dict[str, Any]] = []
    for row in coords:
        time = float(row["time_hartree_inverse"])
        g_cisd = float(row["cisd_proxy_signed_hartree"])
        g_exact = float(row["exact_proxy_signed_hartree"])
        direct = float(row["direct_shift_signed_hartree"])
        direct_error = abs(direct)
        exact_real = float(row["exact_echo_real"])
        exact_imag = float(row["exact_echo_imaginary"])
        key = (row["condition"], row["time_hex"])
        allowance_values = allowance_by_coord.get(key, [])
        coordinate_rows.append({
            "condition": row["condition"],
            "time_hartree_inverse": time,
            "time_hex": row["time_hex"],
            "selected_relative_to_t_ana": float(row["selected_relative_to_t_ana"]),
            "strategies": json.loads(row["strategies"]),
            "cisd_proxy_signed_hartree": g_cisd,
            "exact_proxy_signed_hartree": g_exact,
            "direct_shift_signed_hartree": direct,
            "direct_error_hartree": direct_error,
            "local_cisd_gamma_required": gamma_required(epsilon, g_cisd, direct_error),
            "local_cisd_gamma_operational": max(1.0, gamma_required(epsilon, g_cisd, direct_error)),
            "local_exact_gamma_required": gamma_required(epsilon, g_exact, direct_error),
            "local_exact_gamma_operational": max(1.0, gamma_required(epsilon, g_exact, direct_error)),
            "exact_echo_arg_over_t_hartree": math.atan2(exact_imag, exact_real) / time,
            "exact_echo_imag_over_t_hartree": exact_imag / time,
            "arg_minus_imag_hartree": arg_minus_imag(exact_real, exact_imag, time),
            "signed_exact_direct_gap_hartree": g_exact - direct,
            "absolute_error_gap_hartree": direct_error - abs(g_exact),
            "coordinate_allowance_hartree": min(allowance_values) if allowance_values else None,
            "evidence_class": "post_hoc_read_only_arithmetic",
        })
    strategy_rows: list[dict[str, Any]] = []
    for drow in decomp:
        key = (drow["condition"], drow["strategy"])
        lrow = l_by_key[key]
        if drow["time_hex"] != lrow["selected_time_hex"]:
            raise RuntimeError(f"time mismatch for {key}")
        estimate = abs(float(drow["cisd_proxy_signed_hartree"]))
        direct_error = abs(float(drow["direct_shift_signed_hartree"]))
        old_error = float(lrow["budget_error_used_hartree"])
        old_budget = float(lrow["frozen_pauli_rotation_budget"])
        denominator = epsilon - estimate
        if denominator <= 0:
            gamma_110_budget = math.inf
            gamma_110_qpe = math.inf
            gamma_110_safe = False
        else:
            gamma_110_budget = old_budget * (1.10 / inherited_gamma) * (
                (epsilon - old_error) / denominator
            )
            gamma_110_qpe = denominator / 1.10
            gamma_110_safe = direct_error + gamma_110_qpe <= epsilon + 1e-15
        strategy_rows.append({
            "condition": drow["condition"],
            "strategy": drow["strategy"],
            "time_hex": drow["time_hex"],
            "time_hartree_inverse": float(drow["time_hartree_inverse"]),
            "original_unsafe_execution": lrow["unsafe_execution"] == "True",
            "original_frozen_budget": old_budget,
            "original_required_cost": float(lrow["direct_required_cost"]),
            "original_allowed_underestimation_hartree": float(drow["original_allowed_underestimation_hartree"]),
            "component_attribution": drow["component_attribution"],
            "model_component_hartree": float(drow["model_component"]),
            "state_component_hartree": float(drow["state_component"]),
            "proxy_eigenvalue_component_hartree": float(drow["proxy_eigenvalue_component"]),
            "component_over_original_budget_allowance": json.loads(drow["component_over_original_budget_allowance"]),
            "local_cisd_gamma_required": gamma_required(epsilon, estimate, direct_error),
            "posthoc_local_cisd_gamma_1_10_budget": gamma_110_budget,
            "posthoc_local_cisd_gamma_1_10_required_cost_ratio": (
                gamma_110_budget / float(lrow["direct_required_cost"])
            ),
            "posthoc_local_cisd_gamma_1_10_safe": gamma_110_safe,
            "posthoc_gamma_1_10_is_adopted_method": False,
            "evidence_class": "post_hoc_read_only_arithmetic_not_independent_validation",
        })
    summary = {
        "epsilon_hartree": epsilon,
        "inherited_gamma": inherited_gamma,
        "coordinate_rows": len(coordinate_rows),
        "strategy_rows": len(strategy_rows),
        "maximum_local_cisd_gamma_required": max(r["local_cisd_gamma_required"] for r in coordinate_rows),
        "maximum_absolute_arg_minus_imag_hartree": max(abs(r["arg_minus_imag_hartree"]) for r in coordinate_rows),
        "posthoc_gamma_1_10_safe_strategy_rows": sum(r["posthoc_local_cisd_gamma_1_10_safe"] for r in strategy_rows),
    }
    return coordinate_rows, strategy_rows, summary

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v
                             for k, v in row.items()})

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    if output.exists():
        raise RuntimeError(f"refusing existing output: {output}")
    output.mkdir(parents=True)
    head, verified = verify_sources(root)
    coordinate_rows, strategy_rows, summary = build_rows(root)
    write_csv(output / "coordinate_budget_diagnostics.csv", coordinate_rows)
    write_csv(output / "strategy_budget_comparison.csv", strategy_rows)
    source_manifest = {
        "schema": "pf_r1_readonly_design_source_manifest_v1",
        "evidence_commit": EVIDENCE_COMMIT,
        "planning_bundle_commit": head,
        "verified_material_count": len(verified),
        "verified_materials": verified,
        "substitution_count": 0,
    }
    (output / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    decision = {
        "schema": "pf_r1_reorientation_d0_decision_v1",
        "status": "d0_complete_d1_not_authorized",
        "evidence_commit": EVIDENCE_COMMIT,
        "planning_bundle_commit": head,
        "closed_second_study_status": "complete_no_benefit_unchanged",
        "r1_status": "r1_complete_stop_for_research_direction_review",
        "d1_authorized": False,
        "spectral_pilot_authorized": False,
        "d2_authorized": False,
        "new_scientific_calculation_count": 0,
        "new_hamiltonian_count": 0,
        "new_state_count": 0,
        "new_proxy_count": 0,
        "new_pf_eigenpair_count": 0,
        "new_direct_truth_count": 0,
        "gpu_operation_count": 0,
        "summary": summary,
    }
    (output / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    marker = {
        "status": "d0_complete_d1_not_authorized",
        "planning_bundle_commit": head,
        "d1_authorized": False,
        "d2_authorized": False,
    }
    (output / "D0_COMPLETE.json").write_text(
        json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = f"""# D0 read-only research reorientation summary

- Status: `d0_complete_d1_not_authorized`
- Evidence commit: `{EVIDENCE_COMMIT}`
- Planning bundle commit: `{head}`
- R1 coordinate rows / strategy rows: {summary['coordinate_rows']} / {summary['strategy_rows']}
- Maximum local-CISD required gamma: {summary['maximum_local_cisd_gamma_required']:.15g}
- Maximum `arg(z)/t-Im(z)/t`: {summary['maximum_absolute_arg_minus_imag_hartree']:.15g} Ha
- Post-hoc local-CISD gamma=1.10 safe rows: {summary['posthoc_gamma_1_10_safe_strategy_rows']} / 16
- New scientific calculations: 0

The gamma=1.10 comparison is post-hoc arithmetic, not an adopted or independently validated method. P-SPEC-6 and D1 remain unauthorized. The closed second-study result remains `complete_no_benefit`.
"""
    (output / "report.md").write_text(report, encoding="utf-8")
    manifest_paths = [
        "D0_COMPLETE.json", "coordinate_budget_diagnostics.csv", "decision.json",
        "report.md", "source_manifest.json", "strategy_budget_comparison.csv",
    ]
    manifest = {
        "schema": "pf_r1_readonly_design_manifest_v1",
        "status": "d0_complete_d1_not_authorized",
        "files": [{"path": p, "sha256": sha256_file(output / p),
                   "bytes": (output / p).stat().st_size} for p in manifest_paths],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
