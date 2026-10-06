"""Read saved scalars to audit the slide explanation; perform no PF calculation."""

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
SNAPSHOT = "52261023678c2fc4369ce4312b9385830b843399"
SOURCES = {
    "h4_prediction": "artifacts/pf_first_study_phase_a_20260925_6265243/predictions.json",
    "h4_direct": "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/branch_audit.csv",
    "h4_protocol": "PF_first_study_protocol_20260925.json",
    "one_two_comparison": "artifacts/m3_one_two_term_model_comparison_server2_20260910_92df2db_cpu/summary.json",
    "practical_prediction": "artifacts/server_practical_calibration_minimal_20260923_79035cc/predictions.json",
    "practical_protocol": "review_response/practical_calibration_minimal_protocol.json",
}


def read_json(key):
    return json.loads((ROOT / SOURCES[key]).read_text())


def main():
    registry = {}
    for key, relative in SOURCES.items():
        data = (ROOT / relative).read_bytes()
        snapshot_data = subprocess.check_output(
            ["git", "show", f"{SNAPSHOT}:{relative}"], cwd=ROOT
        )
        assert data == snapshot_data, relative
        origin = subprocess.check_output(
            ["git", "log", "-1", "--format=%H", SNAPSHOT, "--", relative], cwd=ROOT
        ).decode().strip()
        registry[key] = {
            "path": relative,
            "origin_result_commit": origin,
            "verified_snapshot_commit": SNAPSHOT,
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    experiment = read_json("h4_prediction")["experiment_B"]
    formula = next(
        row for row in experiment["formula_predictions"]
        if row["formula_id"] == "m5_best"
    )
    grid = formula["selection_grid_hartree_inverse"]
    with (ROOT / SOURCES["h4_direct"]).open() as stream:
        rows = [
            row for row in csv.DictReader(stream)
            if row["experiment_id"] == "B"
            and row["grid_role"] == "decision_frozen_grid" and row["sign"] == "1"
            and row["branch_reliable"] == "True"
            and row["infeasible_error_budget"] == "False"
        ]
    best = min(rows, key=lambda row: float(row["direct_cost"]))
    assert best["formula_id"] == "m5_best"
    time_value = float(best["time_hartree_inverse"])
    assert time_value == 3.5175172132783867
    index = grid.index(time_value)
    model = formula["primary_model"]
    predicted_shift = sum(
        coefficient * time_value**power
        for coefficient, power in zip(model["coefficients"], model["powers"])
    )
    # The target is recorded explicitly in the frozen practical protocol.
    target = float(read_json("practical_protocol")["target_error_hartree"])
    assert math.isclose(target, 1.5936001019904e-4, rel_tol=1e-15)
    assert abs(predicted_shift) > target
    assert abs(float(best["direct_shift_hartree"])) < target

    comparisons = []
    for row in read_json("one_two_comparison")["records"]:
        if row["condition"] not in ("H6", "H7") or row["formula"] != "current_m3":
            continue
        models = {}
        for name in ("original_one_term", "two_term"):
            saved = row["models"][name]
            point = saved["predicted_time_direct_point"]
            relative_error = abs(saved["predicted_time_model_cost"] - point["direct_cost"]) / point["direct_cost"]
            assert math.isclose(relative_error, saved["metrics"]["predicted_time_cost_relative_error"], rel_tol=1e-12)
            models[name] = {
                "time_hartree_inverse": point["time"],
                "predicted_absolute_error_hartree": abs(saved["predicted_time_model_shift_hartree"]),
                "direct_absolute_error_hartree": point["direct_error_hartree"],
                "cost_prediction_relative_error": relative_error,
            }
        comparisons.append({"condition": row["condition"], "formula": row["formula"], "models": models})

    hf = []
    for row in read_json("practical_prediction")["conditions"]:
        if not row["condition"].startswith("HF_"):
            continue
        selection = row["selection"]
        selected = next(item for item in row["pf_predictions"] if item["formula"] == selection["selected_formula"])
        diagnostic = selected["diagnostic"]
        assert diagnostic["fallback_cancellation"]
        assert not diagnostic["fallback_sentinel_residual"]
        assert not diagnostic["fallback_sign"]
        assert math.isclose(selection["selected_time"], 0.5 * selected["proxy_analytic_time"], rel_tol=1e-15)
        hf.append({
            "condition": row["condition"],
            "formula": selection["selected_formula"],
            "proxy_reference_time_hartree_inverse": selected["proxy_analytic_time"],
            "selected_time_hartree_inverse": selection["selected_time"],
            "cancellation_ratio_at_0p1_reference_time": diagnostic["cancellation_index_primary"],
            "trigger": "cancellation_ratio_below_0.02",
        })

    result = {
        "analysis_type": "post_hoc_saved_scalar_and_procedure_audit",
        "scientific_calculation_performed": False,
        "original_artifacts_modified": False,
        "source_registry": registry,
        "h4_m5_comparison_minimum": {
            "time_hartree_inverse": time_value,
            "zero_based_candidate_index": index,
            "candidate_count": len(grid),
            "candidate_interval_hartree_inverse": [min(grid), max(grid)],
            "proxy_reference_time_hartree_inverse": formula["proxy_t_ana_hartree_inverse"],
            "saved_model": model,
            "post_hoc_predicted_signed_shift_hartree": predicted_shift,
            "target_error_hartree": target,
            "predicted_feasible": False,
            "saved_direct_shift_hartree": float(best["direct_shift_hartree"]),
            "saved_direct_cost": float(best["direct_cost"]),
            "direct_feasible": True,
            "interpretation": "Candidate was present in the original grid, but the saved prediction rejected it on the error condition.",
        },
        "saved_one_two_term_examples": comparisons,
        "saved_hf_cap_triggers": hf,
    }
    target_path = OUTPUT / "selection_and_model_checks.json"
    target_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "self_excluded": "manifest.json is excluded from its own hash list",
        "files": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), target_path)
        },
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Verified saved one/two-term scalars, H4 candidate inclusion and rejection, and HF cap triggers.")


if __name__ == "__main__":
    main()
