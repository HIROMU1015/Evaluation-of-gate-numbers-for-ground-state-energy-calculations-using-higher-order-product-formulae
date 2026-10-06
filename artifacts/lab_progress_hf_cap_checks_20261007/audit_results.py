#!/usr/bin/env python3
"""Read-only scientific-result integrity audit; no molecular calculations."""
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def close(a, b, tol=1e-12):
    assert math.isclose(float(a), float(b), rel_tol=tol, abs_tol=1e-18), (a, b)


def main():
    protocol = read(HERE / "protocol.json")
    predictions = read(HERE / "predictions.json")
    freeze = read(HERE / "SELECTION_FROZEN.json")
    summary = read(HERE / "summary.json")
    assert sha(HERE / "protocol.json") == freeze["protocol_sha256"]
    assert sha(HERE / "predictions.json") == freeze["predictions_sha256"]
    assert sha(ROOT / "review_response/run_lab_progress_hf_cap_checks_20261007.py") == freeze["runner_sha256"]
    for record in protocol["source_registry"]:
        assert sha(ROOT / record["path"]) == record["sha256"]
        assert len(record["origin_result_commit"]) == 40
        assert len(record["verified_snapshot_commit"]) == 40
    original = read(ROOT / protocol["source_registry"][0]["path"])
    old_pf = {(c["condition"], p["formula"]): p for c in original["conditions"] for p in c["pf_predictions"]}
    for m in protocol["models"]:
        assert m["model"] == old_pf[(m["condition"], m["formula"])]["model"]
        assert m["original_diagnostic"] == old_pf[(m["condition"], m["formula"])]["diagnostic"]
    rows = list(csv.DictReader((HERE / "scoring.csv").open()))
    assert len(rows) == len(predictions["pf_choices"]) == 12
    for r, p in zip(rows, predictions["pf_choices"], strict=True):
        assert r["condition"] == p["condition"] and r["formula"] == p["formula"]
        close(r["cap"], p["cap"])
        close(r["selected_time"], p["selected_time"])
        close(r["budget"], p["budget"])
        close(float(r["budget"]) / float(r["predicted_cost"]), protocol["budget_multiplier"])
        close(float(r["qpe_error"]) * float(r["selected_time"]) * float(r["budget"]) / float(r["rotations"]), protocol["qpe_beta"])
        close(float(r["direct_error"]) + float(r["qpe_error"]), r["total_error"])
        close(sum(float(r[k]) for k in ("model_difference", "state_difference", "proxy_difference")),
              float(r["predicted_signed_shift"]) - float(r["signed_direct_shift"]))
        assert (r["precision_pass"] == "True") == (float(r["total_error"]) <= protocol["target_error_hartree"])
        close(float(r["precision_margin"]) + float(r["total_error"]), protocol["target_error_hartree"])
    joint = list(csv.DictReader((HERE / "joint_selection_scoring.csv").open()))
    assert len(joint) == 6
    for j in joint:
        matching = [r for r in rows if r["condition"] == j["condition"] and r["cap"] == j["cap"]]
        cheapest_prediction = min(matching, key=lambda r: float(r["predicted_cost"]))
        assert j["formula"] == cheapest_prediction["formula"]
        close(j["budget"], cheapest_prediction["budget"])
    branch = list(csv.DictReader((HERE / "branch_audit.csv").open()))
    assert len(branch) == sum(len(t) for t in protocol["refined_truth_times"].values()) == 532
    for key, expected in protocol["refined_truth_times"].items():
        actual = [float(r["time"]) for r in branch if r["condition"] + "__" + r["formula"] == key]
        assert actual == expected
    assert all(r["independent_rule_agrees"] == "True" for r in branch)
    assert max(float(r["eigenpair_residual"]) for r in branch) < 1e-10
    assert min(float(r["adjacent_overlap_probability"]) for r in branch if r["adjacent_overlap_probability"]) >= .9
    assert summary["pf_precision_pass_count"] == sum(r["precision_pass"] == "True" for r in rows) == 7
    assert summary["joint_precision_pass_count"] == sum(r["precision_pass"] == "True" for r in joint) == 2
    controls = list(csv.DictReader((ROOT / "artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201/scoring.csv").open()))
    assert len(controls) == 6 and all(r["success_gamma_1_01"] == "True" for r in controls)
    assert summary["new_model_fit_count"] == 0
    print("PASS: immutable selections/models, 12 budgets and three-component decompositions, 6 joint choices, 532 fixed branch points, and 6 saved controls")


if __name__ == "__main__":
    main()
