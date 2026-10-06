"""Read saved scalars for the slide gap review; no PF, state, or fit calculations."""

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
SNAPSHOT = "9bddbca9f41b13ddeeefa64dffac4eecf8550ac7"
SOURCES = {
    "h6": "artifacts/two_term_pf_m3_holdout_server2_20260910_d2360f4_cpu/H6.json",
    "h7": "artifacts/two_term_pf_m3_holdout_server2_20260910_d2360f4_cpu/H7.json",
    "h4_decomposition": "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/error_decomposition.csv",
    "h4_observables": "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/observables.csv",
    "h4_dominance": "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/dominance_summary.csv",
    "molecule_costs": "artifacts/pf_first_study_completion_analysis_20260926_940ee7f/cost_factor_decomposition.csv",
    "molecule_precision": "artifacts/pf_first_study_completion_analysis_20260926_940ee7f/calibration_precision.csv",
    "hchain_coverage": "docs/second_study_v2/hchain_independent_validation_summary_20261005.md",
    "approved_scope": "docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md",
}
EPSILON = 0.00015936001019904


def read_csv(key):
    with (ROOT / SOURCES[key]).open() as stream:
        return list(csv.DictReader(stream))


def main():
    registry = {}
    for key, relative in SOURCES.items():
        data = (ROOT / relative).read_bytes()
        assert data == subprocess.check_output(["git", "show", f"{SNAPSHOT}:{relative}"], cwd=ROOT)
        origin = subprocess.check_output(
            ["git", "log", "-1", "--format=%H", SNAPSHOT, "--", relative], cwd=ROOT
        ).decode().strip()
        registry[key] = {
            "path": relative, "origin_result_commit": origin,
            "verified_snapshot_commit": SNAPSHOT,
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    local_checks = []
    expected_ratios = [0.9, 0.95, 0.975, 1.0, 1.025, 1.05, 1.1]
    for system in ("h6", "h7"):
        saved = json.loads((ROOT / SOURCES[system]).read_text())
        for formula, values in saved["formulas"].items():
            points = values["local_direct_points"]
            ratios = [point["relative_to_t_star"] for point in points]
            assert ratios == expected_ratios
            best = min(points, key=lambda point: point["direct_cost"])
            assert best["relative_to_t_star"] == 1.0
            local_checks.append({
                "system": system.upper(), "formula": formula,
                "model_optimum_time": values["two_term_model_optimum"]["time"],
                "direct_relative_times": ratios,
                "direct_minimum_relative_time": best["relative_to_t_star"],
                "scope": "minimum among seven local saved points, not continuous global optimality",
            })

    decomposition = [row for row in read_csv("h4_decomposition") if row["experiment_id"] == "B"]
    dominance = [row for row in read_csv("h4_dominance") if row["experiment_id"] == "B"]
    assert len(decomposition) == 56 * 12 and len(dominance) == 56
    counts = Counter(row["dominant_component"] for row in dominance)
    assert counts == {"E_state_hartree": 49, "mixed": 7}
    assert {int(row["sign"]) for row in decomposition} == {-1, 1}
    resolved_counts = Counter(int(row["resolved_point_count"]) for row in dominance)
    assert resolved_counts == {12: 44, 10: 10, 9: 2}
    times = sorted({float(row["absolute_time"]) for row in decomposition})
    assert times == [0.125, 0.175, 0.225, 0.275, 0.35, 0.4]
    for row in decomposition:
        total = sum(float(row[key]) for key in (
            "E_fit_signed_hartree", "E_state_signed_hartree", "E_proxy_signed_hartree"
        ))
        assert math.isclose(total, float(row["E_total_signed_hartree"]), abs_tol=1e-18)

    example = next(row for row in decomposition if row["formula_id"] == "m5_best"
                   and row["state_id"] == "cisd" and row["sign"] == "1"
                   and float(row["absolute_time"]) == 0.4)
    example_values = {key: float(example[key]) for key in (
        "fhat_approx_hartree", "g_approx_hartree", "g_exact_hartree", "delta_direct_hartree",
        "E_fit_hartree", "E_state_hartree", "E_proxy_hartree"
    )}
    example_values["state_component_over_target"] = example_values["E_state_hartree"] / EPSILON
    phase_examples = []
    for row in decomposition:
        if (row["formula_id"] == "m5_best" and row["sign"] == "1"
                and float(row["absolute_time"]) == 0.4
                and row["state_id"].startswith("controlled_q0.010_")):
            phase_examples.append({"state_id": row["state_id"],
                                   "g_approx_hartree": float(row["g_approx_hartree"]),
                                   "state_difference_signed_hartree": float(row["E_state_signed_hartree"]),
                                   "quality_class": row["quality_class"]})
    assert len(phase_examples) == 4 and all(row["quality_class"] == "resolved" for row in phase_examples)

    observables = [row for row in read_csv("h4_observables") if row["experiment_id"] == "B"]
    observable_times = sorted({float(row["absolute_time"]) for row in observables})
    assert max(observable_times) == 0.4
    assert not any(float(row["absolute_time"]) > 0.4 for row in observables)

    precision = {row["condition"]: row for row in read_csv("molecule_precision")}
    allocations = []
    for row in read_csv("molecule_costs"):
        other = precision[row["condition"]]
        budget = float(row["b_frozen"])
        required = float(row["c_required_selected_time"])
        reference = float(row["c_star_reference_grid"])
        ratio = budget / required
        assert math.isclose(budget / reference, float(row["factor_total"]), rel_tol=1e-12)
        assert math.isclose(ratio, float(row["factor_calibration"]), rel_tol=1e-12)
        margin = float(other["energy_margin_gamma_1_01_hartree"])
        assert row["success_gamma_1_01"] == other["success_gamma_1_01"] == "True"
        assert margin > 0
        allocations.append({
            "condition": row["condition"], "selected_formula": row["selected_formula"],
            "selected_time": float(row["selected_time"]), "budget_rotations": budget,
            "selected_time_required_rotations": required, "reference_minimum_rotations": reference,
            "budget_over_selected_time_required": ratio, "budget_over_reference": budget / reference,
            "total_energy_error_hartree": EPSILON - margin, "target_hartree": EPSILON,
            "target_met": True, "cap_applied": row["fallback_triggered"] == "True",
            "reference_minimum_inside_allowed_domain": row["reference_grid_oracle_admissible"] == "True",
        })
    assert len(allocations) == 6

    output = {
        "analysis_type": "post_hoc_saved_scalar_and_coverage_audit",
        "new_scientific_calculations": 0, "refitting_performed": False,
        "original_predictions_budgets_rules_results_modified": False,
        "source_registry": registry,
        "holdout_local_time_checks": local_checks,
        "h4_dominance_scope": {"case_count": 56, "evaluation_signs": [-1, 1],
                               "evaluation_magnitudes": times, "scheduled_points_per_case": 12,
                               "resolved_points_per_case_counts": dict(resolved_counts),
                               "classification_counts": dict(counts)},
        "h4_cisd_m5_at_time_0_4": example_values,
        "h4_m5_same_overlap_phase_examples_at_time_0_4": phase_examples,
        "h4_observable_time_magnitudes": observable_times,
        "h4_allocation_time_proxy_components_available_in_this_source": False,
        "molecule_frozen_allocation_results": allocations,
        "unestablished_links": [
            "short-time state dominance to prediction failure at the H4 allocation times",
            "systematic approximate-state improvement to resource improvement on a common candidate set",
            "sensitivity of the resource decision to the HF cap rule",
            "the same four-PF 401-time allocation experiment on a second H chain",
            "whether the CISD truncation diagnostic detects true prediction failures",
        ],
        "additional_scientific_experiments_approved_by_this_audit": False,
    }
    scalar = OUTPUT / "checks.json"
    scalar.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "self_excluded": "manifest.json is excluded from its own hash list",
        "files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in (Path(__file__).resolve(), scalar)},
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Verified seven local times, signed H4 decomposition scope, state examples, and six frozen allocation results.")


if __name__ == "__main__":
    main()
