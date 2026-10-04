"""Frozen-budget arithmetic and integrity gates; no predictor updates or actions."""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path

from review_response.hchain_input_reference_preparation import (
    PreparationError, sha_file, write_json,
)
from review_response.hchain_prediction_phase import (
    check_remote, git, require_clean, source_gate as prediction_source_gate,
    verify_blob, verify_bundle, verify_entries,
)
from review_response.hchain_selective_calibration_schedule import EPSILON, BETA

PREDICTION = "858265dacd304c844029ce2576b4559221f0c7c1"
PRED_ROOT = "artifacts/hchain_truth_free_prediction_20261004"
DOC = "docs/second_study_v2/hchain_truth_scoring_20261004"
METHOD = "docs/second_study_v2/hchain_input_reference_preparation_20261004/truth_scoring_method.json"
METHOD_HASH = "a30afdee106d34c3fe4395bed5aa3459763413f68beea12a601b15d22e772e0e"
SOURCES = (f"{DOC}/authorization.json", f"{DOC}/protocol.md",
           "review_response/hchain_truth_scoring.py", "review_response/run_hchain_truth_scoring.py",
           "review_tests/test_hchain_truth_scoring.py")


def prediction_gate(root):
    source = prediction_source_gate(root)
    names = git(root, "ls-tree", "-r", "--name-only", PREDICTION, PRED_ROOT).decode().splitlines()
    if len(names) != 38:  # q seven + H1 seven + final publication 24
        raise PreparationError("original prediction artifact set mismatch")
    actual = git(root, "ls-files", "--", PRED_ROOT).decode().splitlines()
    if set(actual) != set(names):
        raise PreparationError("prediction tracked artifact set changed")
    for name in names:
        verify_blob(root, name, PREDICTION)
    directory = root / PRED_ROOT
    verify_bundle(root, directory / "final", PREDICTION)
    prediction = json.loads((directory / "final" / "prediction.json").read_text())
    for name, subdir in (("ACQUISITION_FROZEN", "acquisition"), ("H1_FROZEN", "h1")):
        verify_bundle(root, directory / subdir, prediction["stage_commits"][name])
    if sha_file(directory / "final" / "prediction.json") != "a830300b3a90bd9947951a2369b6bcbd01dcd96dfe13db8e24390a3f9c7b8e6f":
        raise PreparationError("fixed prediction hash mismatch")
    if sha_file(root / METHOD) != METHOD_HASH:
        raise PreparationError("frozen scoring method mismatch")
    return prediction, {**source, "prediction_commit": PREDICTION, "prediction_files_verified": 38,
                        "prediction_byte_identical": True, "scoring_method_sha256": METHOD_HASH}


def source_gate(root):
    prediction, inherited = prediction_gate(root)
    path = root / DOC / "implementation_manifest.json"
    verify_blob(root, str(path.relative_to(root)), "HEAD")
    manifest = json.loads(path.read_text())
    content = manifest["content_commit"]
    git(root, "merge-base", "--is-ancestor", PREDICTION, content)
    git(root, "merge-base", "--is-ancestor", content, "HEAD")
    if {row["path"] for row in manifest["files"]} != set(SOURCES):
        raise PreparationError("scorer source set mismatch")
    verify_entries(root, manifest["files"])
    for row in manifest["files"]:
        verify_blob(root, row["path"], content)
    return prediction, {**inherited, "scorer_implementation_commit": content,
                        "scorer_manifest_sha256": sha_file(path), "scorer_sources": manifest["files"]}


def seal_source(root):
    require_clean(root)
    check_remote(root)
    content = git(root, "rev-parse", "HEAD").decode().strip()
    git(root, "merge-base", "--is-ancestor", PREDICTION, content)
    rows = []
    for name in SOURCES:
        verify_blob(root, name, content)
        rows.append({"path": name, "bytes": (root / name).stat().st_size,
                     "sha256": sha_file(root / name), "origin_result_commit": content,
                     "verified_snapshot_commit": content})
    path = root / DOC / "implementation_manifest.json"
    if path.exists():
        raise PreparationError("scorer source seal exists")
    write_json(path, {"schema": "hchain_truth_scorer_implementation_manifest_v1",
                      "content_commit": content, "prediction_commit": PREDICTION,
                      "manifest_self_excluded": True, "files": rows})


def truth_quality(point, method):
    rule = method["direct_branch"]
    required = ("signed_direct_shift_hartree", "minimum_selected_phase_gap_radians",
                "ground_state_overlap_probability", "previous_branch_overlap_probability",
                "unitarity_residual_frobenius", "eigenpair_residual_2_norm")
    if any(point.get(key) is None or not math.isfinite(float(point[key])) for key in required):
        raise PreparationError("nonfinite or missing direct numerical field")
    if point["unitarity_residual_frobenius"] > rule["unitarity_Frobenius_maximum"]:
        raise PreparationError("direct unitarity gate failed")
    if point["eigenpair_residual_2_norm"] > rule["eigenpair_residual_maximum"]:
        raise PreparationError("direct eigenpair gate failed")
    warnings = []
    if point["minimum_selected_phase_gap_radians"] <= 1e-8:
        warnings.append("unresolved_target_phase")
    for key in ("ground_state_overlap_probability", "previous_branch_overlap_probability"):
        if point[key] < rule["ground_and_previous_overlap_warning_floor"]:
            warnings.append(key)
    return {"status": "resolved" if not warnings else "truth_branch_indeterminate",
            "physical_branch_valid": not warnings, "warnings": warnings}


def finite_scalar(value):
    return value is not None and math.isfinite(float(value))


def score_coordinate(cheap, m1, truth, energy):
    if cheap["candidate_id"] != m1["candidate_id"] or m1["candidate_id"] != truth["candidate_id"]:
        raise PreparationError("scoring exact candidate mismatch")
    if float(cheap["time"]).hex() != m1["time_hex"] or m1["time_hex"] != truth["time_hex"]:
        raise PreparationError("scoring exact time mismatch")
    t = float(truth["time"])
    direct = truth["signed_direct_shift_hartree"]
    valid = truth["quality"]["physical_branch_valid"]
    delta, width = m1["delta_M_hartree"], m1["width_M_hartree"]
    e_c = abs(cheap["delta_C_hartree"] - direct)
    e_m = abs(delta - direct) if finite_scalar(delta) else None
    gap = truth["minimum_selected_phase_gap_radians"]
    branch = bool(e_m < gap / (2*t)) if valid and e_m is not None else None
    coverage = bool(e_m <= width) if valid and e_m is not None and finite_scalar(width) and width >= 0 else None
    core = m1["core_prediction"]
    primary = next(row for row in core["prefixes"] if row["dimension"] == core["primary_dimension_used"])
    absolute_estimate = primary["selected_unwrapped_energy_hartree"]
    absolute_target = energy + direct
    absolute_difference = absolute_estimate - absolute_target if finite_scalar(absolute_estimate) else None
    same_lift = valid and absolute_difference is not None and abs(absolute_difference) < math.pi / t
    return {"system": truth["system"], "candidate_id": truth["candidate_id"], "time": t,
        "time_hex": truth["time_hex"], "delta_C_hartree": cheap["delta_C_hartree"],
        "delta_M_hartree": delta, "delta_direct_hartree": direct, "e_direct_hartree": abs(direct),
        "E_C_hartree": e_c, "E_M_hartree": e_m, "E_C_over_epsilon": e_c/EPSILON,
        "E_M_over_epsilon": None if e_m is None else e_m/EPSILON,
        "width_M_hartree": width, "width_M_over_epsilon": None if not finite_scalar(width) else width/EPSILON,
        "empirical_width_covers": coverage, "branch_correct_shift_gap": branch,
        "M1_policy_abstained": m1["abstain"], "M1_original_failure_reasons": core["failure_reasons"],
        "M1_available_dimension": core["available_dimension"], "M1_requested_dimension": core["requested_primary_dimension"],
        "g_phase_rad": gap, "g_E_hartree": gap/t,
        "g_target_projected_unit_circle_chord": 2*math.sin(gap/2),
        "g_rho_others": None, "g_rho_others_status": "not_acquired_or_used_for_width",
        "truth_quality": truth["quality"]["status"],
        "absolute_PF_estimate_hartree": absolute_estimate, "absolute_PF_target_hartree": absolute_target,
        "same_physical_lift_diagnostic": bool(same_lift),
        "absolute_PF_difference_hartree": absolute_difference if same_lift else None,
        "absolute_lift_comparison_status": "same_lift_diagnostic_not_ground_certificate" if same_lift else "indeterminate",
        "unwrap_integers_compared": False}


def score_action(system, arm, action, cheap, truth_by_id, *, gamma=None):
    identifier = action["candidate_id"]
    if identifier not in truth_by_id:
        raise PreparationError("frozen action truth unavailable")
    truth = truth_by_id[identifier]
    if truth["system"] != system:
        raise PreparationError("frozen action system mismatch")
    t, budget = float(action["time"]), action["budget"]
    if t.hex() != truth["time_hex"]:
        raise PreparationError("frozen action time mismatch")
    if not finite_scalar(budget) or budget <= 0 or not math.isfinite(t) or t <= 0:
        raise PreparationError("invalid frozen budget/time; no repair")
    qpe_error = BETA * cheap["K"] / (t * budget)
    total = abs(truth["signed_direct_shift_hartree"]) + qpe_error
    raw_safe = total <= EPSILON
    valid = truth["quality"]["physical_branch_valid"]
    safe = bool(raw_safe) if valid else None
    target_algebraic = t > cheap["B0"]["time"] and budget <= .90 * cheap["B0"]["budget"]
    return {"system": system, "arm": arm, "gamma": gamma, "candidate_id": identifier,
        "time": t, "time_hex": t.hex(), "frozen_budget": budget, "fallback": action["fallback"],
        "B_over_B0": budget/cheap["B0"]["budget"], "e_direct_hartree": abs(truth["signed_direct_shift_hartree"]),
        "qpe_resolution_error_hartree": qpe_error, "total_error_hartree": total,
        "epsilon_E_hartree": EPSILON, "error_headroom_hartree": EPSILON-total,
        "safe": safe, "unsafe": None if safe is None else not safe,
        "raw_arithmetic_safe": bool(raw_safe), "physical_truth_valid": valid,
        "target_budget_time_condition": bool(target_algebraic),
        "safe_target_met": bool(raw_safe and target_algebraic) if valid else None,
        "budget_modified_after_truth": False}


def score_all(prediction, truth, ground):
    before = json.dumps(prediction, sort_keys=True, allow_nan=False)
    by_id = {row["candidate_id"]: row for row in truth["points"]}
    if len(by_id) != 9 or len(truth["points"]) != 9:
        raise PreparationError("exactly nine unique frozen truth records required")
    expected = {row["candidate_id"] for item in prediction["cheap_B0_B1_B2_q"].values() for row in item["points"]}
    if set(by_id) != expected or set(ground["systems"]) != {"H2", "H4", "H6"}:
        raise PreparationError("frozen truth/ground system or coordinate set mismatch")
    coordinate_rows, decision_rows, summaries = [], [], {}
    for system in ("H2", "H4", "H6"):
        cheap = prediction["cheap_B0_B1_B2_q"][system]
        m1_by_id = {row["candidate_id"]: row for row in prediction["M1"][system]}
        for point in cheap["points"]:
            coordinate_rows.append(score_coordinate(point, m1_by_id[point["candidate_id"]],
                by_id[point["candidate_id"]], ground["systems"][system]["energy_hartree"]))
        arms = [("B0", cheap["B0"], None), *[(f"B1_gamma_{arm['gamma']}", arm["selected"], arm["gamma"])
                for arm in cheap["B1_frontier"]], ("B2", cheap["B2"], cheap["B2_gamma"]),
                ("H1", prediction["H1"][system]["action"], cheap["B2_gamma"]),
                ("always_M1", prediction["always_M1_decisions"][system]["selected"], None)]
        rows = [score_action(system, name, action, cheap, by_id, gamma=gamma) for name, action, gamma in arms]
        decision_rows.extend(rows)
        minimum = next((row["gamma"] for row in rows if row["arm"].startswith("B1_") and row["safe"] is True), None)
        summaries[system] = {"q": cheap["q"], "B2_H1_action_identical": cheap["B2"] == prediction["H1"][system]["action"],
            "minimum_safe_gamma_in_fixed_frontier": minimum,
            "q_one_conditional_path_performance": "not_measured" if cheap["q"] == 0 else "see_frozen_conditional_path",
            "decisions": rows}
    if before != json.dumps(prediction, sort_keys=True, allow_nan=False):
        raise PreparationError("immutable scorer changed prediction")
    axes = {arm: {"safe": sum(row["safe"] is True for row in decision_rows if row["arm"] == arm),
                  "unsafe": sum(row["safe"] is False for row in decision_rows if row["arm"] == arm),
                  "indeterminate": sum(row["safe"] is None for row in decision_rows if row["arm"] == arm),
                  "safe_target_met": sum(row["safe_target_met"] is True for row in decision_rows if row["arm"] == arm)}
            for arm in ("B0", "B2", "H1", "always_M1")}
    return {"status": "hchain_independent_validation_complete_review_required",
            "coordinate_scores": coordinate_rows, "decision_scores": decision_rows,
            "system_summaries": summaries, "evidence_axes": axes,
            "branch_correct": sum(row["branch_correct_shift_gap"] is True for row in coordinate_rows),
            "width_covered": sum(row["empirical_width_covers"] is True for row in coordinate_rows),
            "M1_abstentions_preserved": sum(row["M1_policy_abstained"] for row in coordinate_rows),
            "basic_units": "three systems; nine coordinates are not independent samples",
            "new_signal_taxonomy": "not_defined", "next_stage_authorized": False,
            "old_formal_decisions_unchanged": True, "prediction_modified": False,
            "width_is_rigorous_certificate": False, "holdout_or_scaling_claim": False}


def bundle(directory, payload_name, marker_name, payload, marker, source, access, resource):
    if directory.exists():
        raise PreparationError("new freeze bundle exists; no overwrite")
    directory.mkdir(parents=True)
    write_json(directory / payload_name, payload)
    digest = sha_file(directory / payload_name)
    write_json(directory / marker_name, {**marker, "payload_name": payload_name, "payload_sha256": digest})
    write_json(directory / "source_audit.json", source)
    write_json(directory / "access_audit.json", access)
    write_json(directory / "resource_audit.json", resource)
    (directory / "payload.sha256").write_text(digest + "  " + payload_name + "\n")
    files = (payload_name, marker_name, "source_audit.json", "access_audit.json", "resource_audit.json", "payload.sha256")
    write_json(directory / "manifest.json", {"manifest_self_excluded": True, "files": [
        {"path": name, "bytes": (directory/name).stat().st_size, "sha256": sha_file(directory/name)} for name in files]})
    return [*files, "manifest.json"]


def verify_stage(root, directory, commit, marker_name):
    manifest = json.loads((directory/"manifest.json").read_text())
    verify_entries(directory, manifest["files"])
    for name in [row["path"] for row in manifest["files"]] + ["manifest.json"]:
        verify_blob(root, str((directory/name).relative_to(root)), commit)
    marker = json.loads((directory/marker_name).read_text())
    if marker["payload_sha256"] != sha_file(directory/marker["payload_name"]):
        raise PreparationError("stage freeze marker digest mismatch")


def commit_stage(root, directory, files, message):
    check_remote(root)
    require_clean(root)
    paths = [str((directory/name).relative_to(root)) for name in files]
    if set(path.name for path in directory.iterdir()) != set(files):
        raise PreparationError("stage exact lightweight file set mismatch")
    git(root, "add", "--", *paths)
    if set(git(root, "diff", "--cached", "--name-only").decode().splitlines()) != set(paths):
        raise PreparationError("unexpected staged file; no commit")
    git(root, "commit", "-m", message)
    commit = git(root, "rev-parse", "HEAD").decode().strip()
    if set(git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).decode().splitlines()) != set(paths):
        raise PreparationError("unexpected committed file set")
    return commit
