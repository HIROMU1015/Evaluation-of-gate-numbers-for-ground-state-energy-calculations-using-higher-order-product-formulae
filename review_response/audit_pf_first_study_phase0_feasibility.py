"""Scalar-only, immutable-source Phase 0 audit. No science modules are imported."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

SNAPSHOT = "c515562f1c00b5402d5ca266852986ba12ca4002"
REPOSITORY = "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
PHASE_B = "artifacts/pf_first_study_phase_b_20260925_5a2f0a2"
COMPLETION = "artifacts/pf_first_study_completion_analysis_20260926_940ee7f"
AUTHORITY = [
    "docs/current_research_status.md",
    "PF_first_study_paper_claim_ledger_20260926.md",
    "PF_first_study_final_synthesis_20260925.md",
    "PF_first_study_final_decision_20260925.json",
    "PF_first_study_results_20260925.md",
    "PF_first_study_protocol_20260925.md",
    f"{PHASE_B}/report.md", f"{PHASE_B}/error_decomposition.csv",
    f"{PHASE_B}/allocation_scoring.csv",
    "artifacts/pf_first_study_regret_decomposition_20260925_7f0b30d/report.md",
    f"{COMPLETION}/report.md", f"{COMPLETION}/calibration_precision.csv",
    f"{COMPLETION}/cost_factor_decomposition.csv", f"{COMPLETION}/decision_trace.csv",
    "docs/second_study_v2/evidence_integration_20261006/README.md",
    "docs/second_study_v2/evidence_integration_20261006/evidence_map.md",
]
SUPPORTING = [
    "AGENTS.md", "PF_first_study_protocol_20260925.json",
    f"{PHASE_B}/dominance_summary.csv", f"{PHASE_B}/audit.json",
    f"{PHASE_B}/manifest.json", f"{PHASE_B}/predictions.json",
    f"{PHASE_B}/protocol.json", f"{PHASE_B}/prediction.sha256",
    f"{COMPLETION}/metric_dictionary.md", f"{COMPLETION}/protocol.json",
    f"{COMPLETION}/manifest.json", f"{COMPLETION}/source_manifest.json",
    f"{COMPLETION}/s4_cost_definition_audit.json",
    "review_response/_pf_first_study_phase_b_base.py",
    "review_response/pf_first_study_experiment_a.py",
]
PATTERN = re.compile(r"controlled_q([0-9.]+)_phi([0-9.]+)$")
META = ["source_row", "experiment_id", "case_id", "formula_id", "state_id",
        "state_family", "q", "phase_radians", "sign", "absolute_time",
        "model_status", "quality_class", "primary_eligible", "original_case_dominance"]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"Empty table: {path}")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def sign(value):
    return (value > 0) - (value < 0)


def ratio(a, b):
    return a / b if b != 0 else None


def close(a, b):
    # Numerical tolerances inherited from completion-analysis protocol, not a GO rule.
    return math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-13)


def source_registry(repo):
    records = []
    for path in AUTHORITY + SUPPORTING:
        raw = (repo / path).read_bytes()
        frozen = git(repo, "show", f"{SNAPSHOT}:{path}")
        if raw != frozen:
            raise ValueError(f"Source differs from frozen snapshot: {path}")
        origin = git(repo, "log", "-1", "--format=%H", SNAPSHOT, "--", path).decode().strip()
        creation = git(repo, "log", "--diff-filter=A", "--format=%H", SNAPSHOT, "--", path).decode().splitlines()[-1]
        if git(repo, "show", f"{origin}:{path}") != raw:
            raise ValueError(f"Origin blob mismatch: {path}")
        records.append({
            "path": path, "role": "authority" if path in AUTHORITY else "supporting_or_protected",
            "origin_result_commit": origin,
            "origin_role": "result_publication" if path.startswith("artifacts/") else "document_or_code_version",
            "first_publication_commit": creation,
            "verified_snapshot_commit": SNAPSHOT,
            "git_blob_sha": git(repo, "rev-parse", f"{SNAPSHOT}:{path}").decode().strip(),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "origin_matches_snapshot": True,
            "origin_github_url": f"https://github.com/{REPOSITORY}/blob/{origin}/{path}",
            "snapshot_github_url": f"https://github.com/{REPOSITORY}/blob/{SNAPSHOT}/{path}",
        })
    return {"repository": REPOSITORY, "verified_snapshot_commit": SNAPSHOT,
            "identity_policy": "Origin/result and verified snapshot roles remain separate even for identical blobs.",
            "sources": records}


def normalize(rows, dominance):
    lookup = {tuple(r[k] for k in ["experiment_id", "case_id", "formula_id", "state_id"]): r["dominant_component"] for r in dominance}
    result = []
    seen = set()
    for i, source in enumerate(rows, 2):
        r = dict(source)
        for k in source:
            if k.endswith("_hartree") or k in {"absolute_time", "time_hartree_inverse"}:
                r[k] = float(source[k])
                if not math.isfinite(r[k]):
                    raise ValueError(f"Nonfinite source scalar: row {i}, {k}")
        r["sign"] = int(r["sign"])
        key = tuple(r[k] for k in ["experiment_id", "case_id", "formula_id", "state_id"])
        identity = key + (r["sign"], r["absolute_time"])
        if identity in seen:
            raise ValueError("Duplicate scalar source row")
        seen.add(identity)
        r["source_row"] = i
        r["original_case_dominance"] = lookup[key]
        match = PATTERN.fullmatch(r["state_id"])
        r["state_family"] = "controlled" if match else r["state_id"]
        r["q"] = float(match[1]) if match else None
        r["phase_radians"] = float(match[2]) if match else None
        r["primary_eligible"] = r["model_status"] == "fit_ok" and r["quality_class"] == "resolved"
        for component, expected in [
            ("fit", r["fhat_approx_hartree"] - r["g_approx_hartree"]),
            ("state", r["g_approx_hartree"] - r["g_exact_hartree"]),
            ("proxy", r["g_exact_hartree"] - r["delta_direct_hartree"]),
            ("total", r["fhat_approx_hartree"] - r["delta_direct_hartree"]),
        ]:
            if not close(r[f"E_{component}_signed_hartree"], expected) or not close(r[f"E_{component}_hartree"], abs(expected)):
                raise ValueError(f"Column-definition mismatch in row {i}")
        result.append(r)
    return result


def metadata(r):
    return {k: r[k] for k in META}


def phase_analysis(rows):
    groups = defaultdict(list)
    for r in rows:
        if r["state_family"] == "controlled":
            key = tuple(r[k] for k in ["experiment_id", "case_id", "formula_id", "q", "absolute_time", "sign"])
            groups[key].append(r)
    expanded, quartets = [], []
    for key, group in sorted(groups.items()):
        indices = [round(r["phase_radians"] / (math.pi / 2)) for r in group]
        if len(group) != 4 or set(indices) != {0, 1, 2, 3}:
            raise ValueError(f"Incomplete/duplicate phase quartet: {key}")
        if any(abs(r["phase_radians"] - index * math.pi / 2) > 1e-11 for r, index in zip(group, indices)):
            raise ValueError("Unexpected phase coordinate")
        if len({r["g_exact_hartree"] for r in group}) != 1:
            raise ValueError("Quartet exact reference differs")
        average_proxy = math.fsum(r["g_approx_hartree"] for r in group) / 4
        average_error = average_proxy - group[0]["g_exact_hartree"]
        original_rms_squared = math.fsum(r["E_state_signed_hartree"]**2 for r in group) / 4
        interference_rms_squared = math.fsum((r["E_state_signed_hartree"] - average_error)**2 for r in group) / 4
        original_mean_abs = math.fsum(abs(r["E_state_signed_hartree"]) for r in group) / 4
        q = group[0]["q"]
        common = {k: group[0][k] for k in ["experiment_id", "case_id", "formula_id", "q", "sign", "absolute_time"]}
        common.update({
            "phase_count": 4, "all_proxy_resolved": all(r["quality_class"] == "resolved" for r in group),
            "all_models_fit_ok": all(r["model_status"] == "fit_ok" for r in group),
            "g_exact_hartree": group[0]["g_exact_hartree"], "phase_average_proxy_hartree": average_proxy,
            "phase_average_state_error_hartree": average_error,
            "original_state_mean_abs_hartree": original_mean_abs,
            "original_state_rms_hartree": math.sqrt(original_rms_squared),
            "interference_rms_hartree": math.sqrt(interference_rms_squared),
            "mean_abs_retention_ratio": ratio(abs(average_error), original_mean_abs),
            "mean_abs_reduction_ratio": 1 - abs(average_error) / original_mean_abs if original_mean_abs else None,
            "interference_squared_error_fraction": ratio(interference_rms_squared, original_rms_squared),
            "averaged_over_q_hartree": average_error / q,
            "interference_rms_over_sqrt_q_one_minus_q_hartree": math.sqrt(interference_rms_squared / (q * (1-q))),
            "pythagorean_closure_hartree_squared": original_rms_squared - average_error**2 - interference_rms_squared,
            "mean_interference_hartree": math.fsum(r["E_state_signed_hartree"] - average_error for r in group) / 4,
        })
        quartets.append(common)
        for r in sorted(group, key=lambda item: item["phase_radians"]):
            expanded.append({**metadata(r), "quartet_all_proxy_resolved": common["all_proxy_resolved"],
                "g_approx_hartree": r["g_approx_hartree"], "g_exact_hartree": r["g_exact_hartree"],
                "original_state_error_hartree": r["E_state_signed_hartree"],
                "phase_average_proxy_hartree": average_proxy, "phase_average_state_error_hartree": average_error,
                "interference_component_hartree": r["E_state_signed_hartree"] - average_error,
                "state_abs_retention_ratio": ratio(abs(average_error), abs(r["E_state_signed_hartree"])),
                "state_abs_reduction_ratio": 1 - abs(average_error) / abs(r["E_state_signed_hartree"]) if r["E_state_signed_hartree"] else None,
                "quartet_interference_squared_error_fraction": common["interference_squared_error_fraction"]})
    scaling = []
    by_coordinate = defaultdict(list)
    for r in quartets:
        by_coordinate[tuple(r[k] for k in ["experiment_id", "case_id", "formula_id", "sign", "absolute_time"])].append(r)
    for key, group in sorted(by_coordinate.items()):
        if {r["q"] for r in group} != {0.001, 0.01, 0.05}:
            raise ValueError("Missing q in matched scaling diagnostic")
        av = [r["averaged_over_q_hartree"] for r in group]
        it = [r["interference_rms_over_sqrt_q_one_minus_q_hartree"] for r in group]
        scaling.append({**dict(zip(["experiment_id", "case_id", "formula_id", "sign", "absolute_time"], key)),
            "q_count": 3, "all_q_quartets_proxy_resolved": all(r["all_proxy_resolved"] for r in group),
            "averaged_over_q_min_hartree": min(av), "averaged_over_q_max_hartree": max(av),
            "averaged_over_q_range_hartree": max(av)-min(av),
            "averaged_over_q_relative_range": ratio(max(av)-min(av), max(abs(v) for v in av)),
            "interference_normalized_min_hartree": min(it), "interference_normalized_max_hartree": max(it),
            "interference_normalized_range_hartree": max(it)-min(it),
            "interference_normalized_relative_range": ratio(max(it)-min(it), max(it))})
    return expanded, quartets, scaling


def oracle_and_budget(rows):
    oracle, budgets = [], []
    for r in rows:
        fit, state, proxy, total = (r[f"E_{k}_signed_hartree"] for k in ["fit", "state", "proxy", "total"])
        residual = fit + proxy
        original_hat, direct = r["fhat_approx_hartree"], r["delta_direct_hartree"]
        corrected_hat = original_hat - state
        bottleneck = "fit" if abs(fit) > abs(proxy) else "proxy" if abs(proxy) > abs(fit) else "tie"
        oracle.append({**metadata(r), "fit_signed_hartree": fit, "state_signed_hartree": state,
            "proxy_signed_hartree": proxy, "original_total_signed_hartree": total,
            "original_total_abs_hartree": abs(total), "no_state_signed_hartree": residual,
            "no_state_abs_hartree": abs(residual), "no_state_predicted_shift_hartree": corrected_hat,
            "abs_retention_ratio": ratio(abs(residual), abs(total)),
            "abs_reduction_ratio": 1 - abs(residual) / abs(total) if total else None,
            "improves_absolute_error": abs(residual) < abs(total), "residual_bottleneck": bottleneck,
            "algebraic_closure_hartree": corrected_hat - direct - residual})
        crossing = sign(original_hat) != sign(direct)
        underestimation = abs(direct) - abs(original_hat)
        components = {name: None if crossing else -sign(direct) * value for name, value in [("fit", fit), ("state", state), ("proxy", proxy)]}
        positive = {name: value for name, value in components.items() if value is not None and value > 0}
        if crossing:
            largest = "not_attributed_sign_crossing"
        elif not positive:
            largest = "no_positive_component"
        else:
            largest = "|".join(name for name, value in positive.items() if value == max(positive.values()))
        budget = {**metadata(r), "direct_shift_hartree": direct, "predicted_shift_hartree": original_hat,
            "prediction_sign": sign(original_hat), "direct_sign": sign(direct), "sign_crossing": crossing,
            "sign_status": "sign_crossing" if crossing else "same_sign",
            "signed_total_error_hartree": total, "underestimation_hartree": underestimation,
            "underestimates_magnitude": underestimation > 0,
            "largest_positive_unsafe_component": largest,
            "no_state_predicted_shift_hartree": corrected_hat,
            "no_state_sign_crossing": sign(corrected_hat) != sign(direct),
            "no_state_underestimation_hartree": abs(direct) - abs(corrected_hat),
            "underestimation_attribution_closure_hartree": None if crossing else math.fsum(components.values())-underestimation}
        for k, value in components.items():
            budget[f"u_{k}_hartree"] = value
            budget[f"{k}_direction"] = "not_attributed_sign_crossing" if value is None else "unsafe" if value > 0 else "conservative" if value < 0 else "zero"
        budgets.append(budget)
    return oracle, budgets


def truth_free_bound(beta, rotations, cap, epsilon, frozen_budget):
    if min(beta, rotations, cap, epsilon, frozen_budget) <= 0:
        raise ValueError("Bound requires positive cost parameters")
    return 1 - beta * rotations / (cap * epsilon * frozen_budget)


def resource_analysis(calibration, factors, trace, constants):
    by_factor = {r["condition"]: r for r in factors}
    selected = {r["condition"]: r for r in trace if r["selected_formula"] == "True"}
    epsilon, gamma, beta = (constants[k] for k in ["target_error_hartree", "budget_multiplier", "practical_cost_beta"])
    margins, resources = [], []
    for source in calibration:
        name = source["condition"]
        f, tr = by_factor[name], selected[name]
        c, e = float(source["predicted_error_hartree"]), float(source["direct_error_hartree"])
        u = e-c
        capacity = (1-1/gamma)*(epsilon-c)
        slack = capacity-u
        saved_margin = float(source["energy_margin_gamma_1_01_hartree"])
        required = (epsilon-c)/(epsilon-e) if e < epsilon else None
        if not close(slack, saved_margin) or (slack >= 0) != (source["success_gamma_1_01"] == "True"):
            raise ValueError(f"Saved safety disagrees: {name}")
        margins.append({"condition": name, "evaluation_group": source["evaluation_group"],
            "selected_formula": source["selected_formula"], "epsilon_energy_hartree": epsilon,
            "c_hartree": c, "e_hartree": e, "underestimation_hartree": u, "gamma": gamma,
            "M_gamma_hartree": capacity, "safety_slack_hartree": slack,
            "gamma_req_posthoc": required, "gamma_req_status": "finite_algebraic_diagnostic" if required is not None else "direct_not_feasible",
            "saved_energy_margin_gamma_1_01_hartree": saved_margin, "margin_difference_hartree": slack-saved_margin,
            "original_safety": source["success_gamma_1_01"], "recomputed_safety": slack >= 0})
        fm, fg, fc, ft, fp, total = (float(f[k]) for k in ["factor_model", "factor_margin", "factor_calibration", "saved_factor_time", "factor_pf", "factor_total"])
        time, cap, b0, chat, creq = (float(f[k]) for k in ["selected_time", "allowed_time_cap", "b_frozen", "c_hat", "c_required_selected_time"])
        rotations = int(tr["rotations"])
        identities = [close(fm*fg, fc), close(fc*ft*fp, total), close(gamma*chat, b0),
            close(beta*rotations/(time*(epsilon-e)), creq), close(beta*rotations/(time*(epsilon-c)), chat),
            close(time, float(tr["condition_selected_time"])), close(cap, float(tr["allowed_time_cap"]))]
        if not all(identities) or time > cap:
            raise ValueError(f"Resource source identity mismatch: {name}")
        bound = truth_free_bound(beta, rotations, cap, epsilon, b0)
        same_time = 1-1/fc
        if bound + 1e-13 < same_time:
            raise ValueError("Domain upper bound below same-time oracle saving")
        resources.append({"condition": name, "evaluation_group": source["evaluation_group"],
            "selected_formula": source["selected_formula"], "selected_time": time, "allowed_time_cap_T": cap,
            "beta": beta, "rotations_K_P": rotations, "epsilon_energy_hartree": epsilon,
            "B0_frozen": b0, "C_required_saved_time": creq, "F_model": fm, "F_margin": fg,
            "F_calibration": fc, "F_time": ft,
            "F_within": float(f["factor_within"]) if f["factor_within"] else None,
            "F_domain": float(f["factor_domain"]) if f["factor_domain"] else None,
            "F_within_lower": float(f["factor_within_lower"]), "F_within_upper": float(f["factor_within_upper"]),
            "F_domain_lower": float(f["factor_domain_lower"]), "F_domain_upper": float(f["factor_domain_upper"]),
            "F_PF": fp, "F_total": total, "actual_total_regret": total-1,
            "same_time_calibration_headroom": same_time,
            "same_time_perfect_prediction_fixed_gamma_saving": 1-1/fm,
            "truth_free_within_domain_maximum_saving_bound": bound,
            "truth_free_domain_cost_lower_bound": beta*rotations/(cap*epsilon),
            "remaining_factor_after_same_time_perfect_calibration": ft*fp,
            "coverage_status": f["coverage_status"], "selected_at_cap": f["selected_at_cap"],
            "interpretation": "time_domain_bound" if f["coverage_status"] == "analytic_bound_at_cap" else "saved_grid_continuous_values_no_new_classification"})
    return margins, resources


def subgroup_summaries(oracle, budgets):
    budget_by_row = {r["source_row"]: r for r in budgets}
    summaries = []
    dimensions = [[], ["experiment_id"], ["experiment_id", "formula_id"],
        ["experiment_id", "case_id"], ["experiment_id", "state_family"],
        ["experiment_id", "state_id"], ["experiment_id", "absolute_time"],
        ["experiment_id", "q"], ["experiment_id", "original_case_dominance"],
        ["experiment_id", "quality_class", "model_status"]]
    for eligibility in ["all_saved_rows", "fit_ok_and_resolved"]:
        selected = [r for r in oracle if eligibility == "all_saved_rows" or r["primary_eligible"]]
        for dims in dimensions:
            groups = defaultdict(list)
            for row in selected:
                groups[tuple(row[k] for k in dims)].append(row)
            for key, group in sorted(groups.items(), key=lambda item: str(item[0])):
                bb = [budget_by_row[r["source_row"]] for r in group]
                same = [b for b in bb if not b["sign_crossing"]]
                unsafe_same = [b for b in same if b["underestimates_magnitude"]]
                original_sum = math.fsum(r["original_total_abs_hartree"] for r in group)
                residual_sum = math.fsum(r["no_state_abs_hartree"] for r in group)
                retention = [r["abs_retention_ratio"] for r in group if r["abs_retention_ratio"] is not None]
                rec = {"eligibility": eligibility, "group_dimensions": "+".join(dims) or "overall",
                    "group_values": json.dumps(dict(zip(dims, key)), ensure_ascii=False, sort_keys=True),
                    "row_count": len(group), "original_sum_abs_hartree": original_sum, "no_state_sum_abs_hartree": residual_sum,
                    "sum_abs_retention_ratio": ratio(residual_sum, original_sum),
                    "sum_abs_reduction_ratio": 1-residual_sum/original_sum if original_sum else None,
                    "median_row_abs_retention_ratio": statistics.median(retention) if retention else None,
                    "improved_rows": sum(r["improves_absolute_error"] for r in group),
                    "worsened_rows": sum(r["no_state_abs_hartree"] > r["original_total_abs_hartree"] for r in group),
                    "residual_fit_largest_rows": sum(r["residual_bottleneck"] == "fit" for r in group),
                    "residual_proxy_largest_rows": sum(r["residual_bottleneck"] == "proxy" for r in group),
                    "residual_tie_rows": sum(r["residual_bottleneck"] == "tie" for r in group),
                    "sign_crossing_rows": sum(b["sign_crossing"] for b in bb), "same_sign_rows": len(same),
                    "underestimated_rows_all_signs": sum(b["underestimates_magnitude"] for b in bb),
                    "underestimated_same_sign_rows": len(unsafe_same),
                    "no_state_underestimated_rows_all_signs": sum(b["no_state_underestimation_hartree"] > 0 for b in bb),
                    "positive_underestimation_sum_hartree": math.fsum(max(b["underestimation_hartree"], 0) for b in bb),
                    "no_state_positive_underestimation_sum_hartree": math.fsum(max(b["no_state_underestimation_hartree"], 0) for b in bb),
                    "state_conservative_same_sign_rows": sum(b["state_direction"] == "conservative" for b in same)}
                for component in ["fit", "state", "proxy"]:
                    rec[f"unsafe_same_sign_{component}_largest_rows"] = sum(b["largest_positive_unsafe_component"] == component for b in unsafe_same)
                summaries.append(rec)
    return summaries


def phase_summaries(quartets):
    result = []
    for eligibility in ["all_complete_quartets", "all_four_proxies_resolved"]:
        selected = [r for r in quartets if eligibility == "all_complete_quartets" or r["all_proxy_resolved"]]
        for dims in [["experiment_id"], ["experiment_id", "formula_id"], ["experiment_id", "q"], ["experiment_id", "absolute_time"]]:
            groups = defaultdict(list)
            for r in selected:
                groups[tuple(r[k] for k in dims)].append(r)
            for key, group in sorted(groups.items(), key=lambda item: str(item[0])):
                original = math.fsum(r["original_state_mean_abs_hartree"] for r in group)
                averaged = math.fsum(abs(r["phase_average_state_error_hartree"]) for r in group)
                original_sq = math.fsum(r["original_state_rms_hartree"]**2 for r in group)
                int_sq = math.fsum(r["interference_rms_hartree"]**2 for r in group)
                result.append({"eligibility": eligibility, "group_dimensions": "+".join(dims),
                    "group_values": json.dumps(dict(zip(dims, key)), sort_keys=True), "quartet_count": len(group),
                    "pooled_state_abs_retention_ratio": ratio(averaged, original),
                    "pooled_state_abs_reduction_ratio": 1-averaged/original if original else None,
                    "pooled_interference_squared_error_fraction": ratio(int_sq, original_sq)})
    return result


def build(repo, output):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError("Use a NEW output directory; frozen outputs are never overwritten")
    registry = source_registry(repo)
    source_hashes = {r["path"]: r["sha256"] for r in registry["sources"]}
    dominance = read_csv(repo / PHASE_B / "dominance_summary.csv")
    counts = Counter(r["dominant_component"] for r in dominance)
    if len(dominance) != 128 or counts != {"E_state_hartree": 79, "mixed": 49}:
        raise ValueError("Frozen formal classification differs")
    rows = normalize(read_csv(repo / PHASE_B / "error_decomposition.csv"), dominance)
    phase, quartets, scaling = phase_analysis(rows)
    oracle, budgets = oracle_and_budget(rows)
    completion_protocol = json.loads((repo / COMPLETION / "protocol.json").read_text())
    margins, resources = resource_analysis(read_csv(repo / COMPLETION / "calibration_precision.csv"),
        read_csv(repo / COMPLETION / "cost_factor_decomposition.csv"), read_csv(repo / COMPLETION / "decision_trace.csv"),
        completion_protocol["fixed_values"])
    summaries = subgroup_summaries(oracle, budgets)
    ps = phase_summaries(quartets)
    final_decision = json.loads((repo / "PF_first_study_final_decision_20260925.json").read_text())
    if final_decision["stages"]["s4_state_convergence"]["outcome"] != "no_benefit":
        raise ValueError("Frozen S4 result changed")
    verification = {
        "status": "passed", "formal_first_study_results_unchanged": True, "new_science_calculation_count": 0,
        "protected_source_count": len(source_hashes), "authority_file_count": len(AUTHORITY),
        "original_formal_case_count": 128, "original_formal_state_dominant_cases": 79, "original_formal_mixed_cases": 49,
        "saved_scalar_row_count": len(rows), "experiment_row_counts": dict(Counter(r["experiment_id"] for r in rows)),
        "primary_eligible_row_counts": dict(Counter(r["experiment_id"] for r in rows if r["primary_eligible"])),
        "phase_quartet_count": len(quartets), "phase_quartet_counts": dict(Counter(r["experiment_id"] for r in quartets)),
        "phase_expanded_row_count": len(phase), "q_scaling_coordinate_count": len(scaling), "resource_condition_count": len(resources),
        "max_source_three_way_closure_hartree": max(abs(math.fsum(r[f"E_{k}_signed_hartree"] for k in ["fit", "state", "proxy"])-r["E_total_signed_hartree"]) for r in rows),
        "max_oracle_algebraic_closure_hartree": max(abs(r["algebraic_closure_hartree"]) for r in oracle),
        "max_same_sign_underestimation_closure_hartree": max(abs(r["underestimation_attribution_closure_hartree"]) for r in budgets if not r["sign_crossing"]),
        "max_mean_interference_hartree": max(abs(r["mean_interference_hartree"]) for r in quartets),
        "max_pythagorean_closure_hartree_squared": max(abs(r["pythagorean_closure_hartree_squared"]) for r in quartets),
        "max_saved_margin_difference_hartree": max(abs(r["margin_difference_hartree"]) for r in margins),
        "all_six_saved_safety_decisions_match": all(r["recomputed_safety"] == (r["original_safety"] == "True") for r in margins),
        "sign_crossing_attribution_always_null": all(all(r[f"u_{k}_hartree"] is None for k in ["fit", "state", "proxy"]) for r in budgets if r["sign_crossing"]),
        "numerical_tolerance_source": f"{COMPLETION}/protocol.json:numerical_gates", "go_thresholds_created": False,
        "execution_boundary": "stdlib scalar arithmetic; git show/log/rev-parse reads only; no science module imports, fit, PF/H actions, state generation or eigensolve",
    }
    if len(rows) != 1536 or len(quartets) != 360 or len(margins) != 6:
        raise ValueError("Unexpected source coverage")
    for path, digest in source_hashes.items():
        if hashlib.sha256((repo / path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Source modified during audit: {path}")
    output.mkdir(parents=True)
    tables = {"phase_average_analysis.csv": phase, "phase_quartet_summary.csv": quartets,
        "phase_q_scaling.csv": scaling, "phase_group_summary.csv": ps,
        "oracle_state_removal.csv": oracle, "budget_direction_attribution.csv": budgets,
        "mechanism_and_budget_summary.csv": summaries,
        "margin_capacity_first_study.csv": margins, "resource_headroom.csv": resources}
    for name, table in tables.items():
        write_csv(output / name, table)
    write_json(output / "source_registry.json", registry)
    write_json(output / "verification.json", verification)
    write_json(output / "summary.json", {"mechanism_and_budget": summaries, "phase": ps, "resource": resources,
        "q_scaling": scaling, "formal_results": {"state_dominant": 79, "mixed": 49, "case_count": 128, "s4": "no_benefit"}})
    write_json(output / "analysis_protocol.json", {
        "analysis_id": "first_study_phase0_feasibility_20261006", "analysis_date_jst": "2026-10-06",
        "verified_snapshot_commit": SNAPSHOT, "analysis_type": "posthoc_readonly_scalar_feasibility_audit",
        "science_actions_authorized": 0, "formal_results_immutable": True, "authority": AUTHORITY,
        "prediction_definition": "fhat_approx_hartree; g_approx/g_exact use Im(echo amplitude)/signed time, NOT the arg-phase proxy",
        "primary_row_summary": "model_status=fit_ok AND quality_class=resolved; all saved rows also retained separately",
        "primary_phase_summary": "four proxies resolved in a complete quartet; fit status is irrelevant to the proxy average",
        "grouping": "experiment, case (lambda separated), PF, q, absolute time, sign; no merging lambda or sign",
        "phase_interference_fraction": "mean_phi(E_int**2)/mean_phi(E_state**2); squared-error share, not an additive absolute-error percentage",
        "oracle_removal": "E_fit+E_proxy with original fit held fixed; not refitting an exact-state model or a realizable intervention",
        "unsafe_component_label": "largest strictly positive u_k on same-sign rows; argmax only, not a new formal dominance criterion",
        "sign_crossing": "all componentwise absolute-risk attribution null; oracle u still evaluated directly using absolute values",
        "reduction": "1-new_abs/original_abs; negative worsening retained; zero denominators null; pooled values use sums, not means of ratios",
        "power_law_policy": "compare E_avg/q and RMS(E_int)/sqrt(q*(1-q)) across the 3 saved q values; no exponent fit or general power-law claim",
        "margin_and_policy": "gamma=1.01 unchanged; gamma_req diagnostic only; same-time H_cal includes cost-free removal of fixed margin",
        "domain_bound": "same PF, fixed cap T, B0 frozen; truth_free_bound function takes no truth scalar; no claim outside cap or across PFs",
        "coverage_policy": "HF F_within/F_domain remain intervals; active-space exact refers only to saved grid",
        "decision_authority": "GO/NO-GO is a feasibility recommendation for GPT/user review, not authorization for a pilot or revised paper claims",
        "threshold_policy": "No new quantitative scientific, GO, gamma, selector or classification thresholds",
        "forbidden": ["new Hamiltonian", "ground solve", "PF action", "direct truth", "Schur/eigensolve", "new state", "refitting", "new q/time/PF/molecule/geometry", "gamma/threshold/selector tuning", "S4 redesign", "formal result modification"],
    })
    return verification


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.repo, args.output), ensure_ascii=False, indent=2))
