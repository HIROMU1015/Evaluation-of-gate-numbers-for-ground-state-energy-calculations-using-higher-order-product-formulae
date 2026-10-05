"""Stdlib-only saved-scalar analysis. Never imports a scientific acquisition backend."""

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import time

DOCS = "docs/second_study_v2/budget_safety_mechanism_20261005"
OUT = "artifacts/budget_safety_mechanism_20261005"
EPS = 0.00015936001019904
BETA = 1.2
GAMMAS = (1.01, 1.02, 1.05, 1.10)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b, label, absolute=1e-15):
    require(math.isclose(a, b, rel_tol=1e-12, abs_tol=absolute), label)


def finite(*values):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool)
               and math.isfinite(v) for v in values)


def cheap_capacity(e, c, gamma, epsilon=EPS):
    """No truth-conditioned policy selection; gamma_req is an oracle diagnostic."""
    if not finite(e, c, gamma, epsilon) or min(e, c) < 0 or gamma < 1 or epsilon <= 0:
        return {"status": "indeterminate_invalid_input"}
    if c >= epsilon:
        return {"status": "invalid_cheap_denominator"}
    if e >= epsilon:
        return {"status": "no_finite_safe_uncorrected_budget"}
    margin = (1 - 1 / gamma) * (epsilon - c)
    u = e - c
    return {"status": "resolved", "underestimation_hartree": u,
            "margin_hartree": margin, "safety_slack_hartree": margin - u,
            "underestimation_to_margin_ratio": u / margin if margin > 0 else None,
            "ratio_status": "resolved" if margin > 0 else "undefined_zero_margin_use_slack",
            "gamma_req": (epsilon - c) / (epsilon - e),
            "gamma_req_restricted_ge_1": max(1, (epsilon - c) / (epsilon - e))}


def width_window(delta_m, t, k, comparator_budget, eta, epsilon=EPS):
    if (not finite(delta_m, t, k, comparator_budget, eta, epsilon)
            or min(t, k, comparator_budget) <= 0 or not 0 <= eta < 1):
        return None
    return epsilon - abs(delta_m) - BETA * k / (t * (1 - eta) * comparator_budget)


def decompose(delta_m, delta, pf_hat, h_hat, e0, pf_target, identity_verified):
    if not identity_verified or not finite(delta_m, delta, pf_hat, h_hat, e0, pf_target):
        return {"decomposition_status": "indeterminate_identity_or_independent_energy_missing"}
    scale = max(1, abs(pf_hat), abs(h_hat), abs(e0), abs(pf_target))
    tolerance = 64 * math.ulp(scale)
    require(abs((pf_hat - h_hat) - delta_m) <= tolerance, "M1 absolute shift closure")
    require(abs((pf_target - e0) - delta) <= tolerance, "truth absolute shift closure")
    a, r = pf_hat - pf_target, h_hat - e0
    residual = (delta_m - delta) - (a - r)
    require(abs(residual) <= 2 * tolerance, "PF/H error decomposition closure")
    return {"decomposition_status": "same_H_origin_physical_lift_verified_saved_diagnostic",
            "PF_energy_error_signed_hartree": a, "H_reference_error_signed_hartree": r,
            "shift_error_signed_hartree": delta_m - delta,
            "closure_rounding_residual_hartree": residual,
            "closure_rounding_allowance_hartree": 2 * tolerance,
            "causal_state_or_rank_attribution": "not_established"}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                       allow_nan=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_sources(root, registry):
    checked = []
    for row in registry["sources"]:
        path = Path(row["path"])
        require(not path.is_absolute() and ".." not in path.parts, "unsafe source path")
        require(".runtime" not in path.parts and path.suffix in {".json", ".csv", ".md", ".py"},
                "not an allowed tracked scalar/document source")
        require(not (root / path).is_symlink(), "source must not be a symlink")
        b = (root / path).read_bytes()
        require(len(b) == row["bytes"] and digest(b) == row["sha256"], "source byte/hash gate")
        for key in ("origin_result_commit", "verified_snapshot_commit"):
            require(git(root, "show", row[key] + ":" + row["path"]) == b, "source commit gate")
        checked.append(row["id"])
    return checked


class Sources:
    def __init__(self, root, registry):
        self.root = root
        self.rows = {r["id"]: r for r in registry["sources"]}
        self.accesses = []

    def read(self, name):
        row = self.rows[name]
        self.accesses.append(name)
        data = (self.root / row["path"]).read_text()
        if row["path"].endswith(".csv"):
            return list(csv.DictReader(io.StringIO(data)))
        return json.loads(data)


def prefix(core):
    matches = [p for p in core["prefixes"] if p["dimension"] == core["primary_dimension_used"]]
    require(len(matches) == 1, "primary prefix must be unique")
    return matches[0]


def index(rows, key):
    result = {key(r): r for r in rows}
    require(len(result) == len(rows), "duplicate scalar coordinate")
    return result


def hf_rows(src):
    prediction = src.read("hf_prediction")
    scored = src.read("hf_scoring")
    g2 = src.read("hf_g2_prediction")
    diagnostics = index(scored["coordinate_diagnostics"], lambda x: x["candidate_id"])
    g2_conditions = index(g2["conditions"], lambda x: x["condition"])
    coords, decisions = [], []
    for cond in prediction["conditions"]:
        name = cond["condition"]
        baseline = g2_conditions[name]["cheap"]["B0"]["frozen_continuous_budget"]
        for cand in cond["candidates"]:
            m, cheap = cand["M1"], cand["B1"]
            d = diagnostics[m["candidate_id"]]
            core = m["prediction_detail"]
            require(d["time_hex"] == m["time_hex"] == float(m["time_hartree_inverse"]).hex(),
                    "HF exact coordinate")
            close(d["cheap_shift_hartree"], cheap[0]["signed_shift_estimate_hartree"],
                  "HF cheap shift join")
            close(d["M1_shift_hartree"], core["signed_shift_estimate_hartree"],
                  "HF spectral join")
            coords.append({"condition": name, "family": "HF", "contract": "HF_T0_1.3T0_1.6T0",
                           "candidate_id": m["candidate_id"], "time": m["time_hartree_inverse"],
                           "time_hex": m["time_hex"], "K": core["K_current_m3"],
                           "delta_C": cheap[0]["signed_shift_estimate_hartree"],
                           "delta_M": core["signed_shift_estimate_hartree"],
                           "delta": d["direct_shift_hartree"],
                           "width": core["empirical_width_hartree"], "core": core,
                           "abstain": m["abstained"], "m1_eligible": m["eligible"],
                           "M1_budget": m["continuous_budget"], "baseline_budget": baseline,
                           "baseline_scope": "inherited_B0_at_T0_not_recomputed_cheap_formula",
                           "baseline_time": g2_conditions[name]["cheap"]["B0"]["selected_time_hartree_inverse"],
                           "truth_valid": d["M1_physical_branch_correct"],
                           "saved_coverage": d["M1_empirical_width_covers"],
                           "cheap_budgets": {r["gamma"]: r["continuous_budget"] for r in cheap},
                           "cheap_eligible": {r["gamma"]: r["eligible"] for r in cheap},
                           "prediction_source": "hf_prediction", "scoring_source": "hf_scoring",
                           "decomposition": decompose(None, None, None, None, None, None, False)})
    for c in scored["condition_scores"]:
        arms = [(a, c[a]) for a in ("B0", "B2", "H1", "always_M1")]
        arms += [("B1_gamma_" + str(r["gamma"]), r) for r in c["B1_fixed_frontier"]]
        for arm, r in arms:
            decisions.append({"condition": c["condition"], "arm": arm,
                              "candidate_id": r["candidate_id"], "time": r["time_hartree_inverse"],
                              "frozen_budget": r["frozen_continuous_budget"], "saved_safe": r["safe_and_valid"],
                              "saved_raw_safe": r["budget_safe"], "saved_lhs": r["budget_safety_lhs_hartree"],
                              "fallback": r["fallback"], "B_over_B0": r["B_over_B0"],
                              "saved_safe_target": r["safe_target_met"], "q": c["q"],
                              "procedurally_valid": r["procedurally_valid"], "source": "hf_scoring"})
    return coords, decisions


def chain_rows(src, tag):
    p, s, g, truth = (src.read(tag + "_" + k) for k in ("prediction", "scoring", "ground", "truth"))
    ds = index(s["coordinate_scores"], lambda x: x["candidate_id"])
    ts = index(truth["points"], lambda x: x["candidate_id"])
    coords, decisions = [], []
    for name, cheap in p["cheap_B0_B1_B2_q"].items():
        cs = index(cheap["points"], lambda x: x["candidate_id"])
        candidate_actions = index(p["always_M1_decisions"][name]["candidate_rows"],
                                  lambda x: x["candidate_id"])
        for row in p["M1"][name]:
            cid, core = row["candidate_id"], row["core_prediction"]
            d, t, c, h, inp = ds[cid], ts[cid], cs[cid], g["systems"][name], p["input_identity"][name]
            require(row["time_hex"] == d["time_hex"] == t["time_hex"] == c["time_hex"]
                    == float(row["time"]).hex(), "H-chain exact time join")
            for a, b in [(row["delta_M_hartree"], d["delta_M_hartree"]),
                         (c["delta_C_hartree"], d["delta_C_hartree"]),
                         (t["signed_direct_shift_hartree"], d["delta_direct_hartree"])]:
                close(a, b, "H-chain shift join")
            ident = (inp["H_sha256_numpy_v1"] == h["H_sha256_numpy_v1"] == t["H_sha256_numpy_v1"]
                     and inp["sector_dimension"] == h["sector_dimension"]
                     and inp["sector_indices_sha256_numpy_v1"] == h["sector_indices_sha256_numpy_v1"]
                     and t["ground_vector_sha256_numpy_v1"] == h["ground_vector_sha256_numpy_v1"]
                     and d["same_physical_lift_diagnostic"] and d["truth_quality"] == "resolved")
            pr = prefix(core)
            dec = decompose(row["delta_M_hartree"], d["delta_direct_hartree"],
                            pr["selected_unwrapped_energy_hartree"], pr["h_reference_energy_hartree"],
                            h["energy_hartree"], d["absolute_PF_target_hartree"], ident)
            require(ident, "H-chain saved identity/lift gate")
            close(pr["selected_unwrapped_energy_hartree"], d["absolute_PF_estimate_hartree"],
                  "saved absolute PF join")
            coords.append({"condition": name, "family": "H-chain", "contract": "Hchain_r0.5_0.65_0.8_t_ref",
                           "candidate_id": cid, "time": row["time"], "time_hex": row["time_hex"],
                           "K": cheap["K"], "delta_C": c["delta_C_hartree"],
                           "delta_M": row["delta_M_hartree"], "delta": d["delta_direct_hartree"],
                           "width": row["width_M_hartree"], "core": core, "abstain": row["abstain"],
                           "m1_eligible": candidate_actions[cid]["eligible"],
                           "M1_budget": core["frozen_pauli_rotation_budget"],
                           "baseline_budget": cheap["B0"]["budget"], "baseline_time": cheap["B0"]["time"],
                           "baseline_scope": "Hchain_B0_at_r0.5",
                           "truth_valid": d["branch_correct_shift_gap"],
                           "saved_coverage": d["empirical_width_covers"],
                           "cheap_budgets": {a["gamma"]: next(x["budget"] for x in a["rows"]
                                                              if x["candidate_id"] == cid)
                                             for a in cheap["B1_frontier"]},
                           "cheap_eligible": {a["gamma"]: next(x["eligible"] for x in a["rows"]
                                                               if x["candidate_id"] == cid)
                                              for a in cheap["B1_frontier"]},
                           "prediction_source": tag + "_prediction", "scoring_source": tag + "_scoring",
                           "decomposition": {**dec, "ground_source": tag + "_ground",
                                             "truth_source": tag + "_truth", "same_H_hash": h["H_sha256_numpy_v1"]}})
    for r in s["decision_scores"]:
        decisions.append({"condition": r["system"], "arm": r["arm"], "candidate_id": r["candidate_id"],
                          "time": r["time"], "frozen_budget": r["frozen_budget"], "saved_safe": r["safe"],
                          "saved_raw_safe": r["raw_arithmetic_safe"], "saved_lhs": r["total_error_hartree"],
                          "fallback": r["fallback"], "B_over_B0": r["B_over_B0"],
                          "saved_safe_target": r["safe_target_met"],
                          "q": p["cheap_B0_B1_B2_q"][r["system"]]["q"],
                          "procedurally_valid": r["physical_truth_valid"], "source": tag + "_scoring"})
    return coords, decisions


def hcl_rows(src):
    p, scored, audit, c0 = (src.read(k) for k in ("hcl_prediction", "hcl_scoring", "hcl_audit", "hcl_c0"))
    key = lambda x: (x["condition"], x["time_hex"])
    ds, au, widths = index(scored["rows"], key), index(audit["rows"], key), index(c0, key)
    coords = []
    for row in p["predictions"]:
        d, a, w = ds[key(row)], au[key(row)], widths[key(row)]
        require(row["time_hex"] == float(row["time_hartree_inverse"]).hex(), "HCl time hex")
        close(row["empirical_width_hartree"], float(w["current_width_hartree"]), "C0 width join")
        close(d["direct_signed_shift_hartree"], a["direct_signed_shift_hartree"], "HCl truth join")
        coords.append({"condition": row["condition"], "family": "HCl", "contract": "HCl_r0.5_0.65_0.8_t_ana",
                       "candidate_id": row["condition"] + "_r" + str(row["relative_to_t_ana"]),
                       "time": row["time_hartree_inverse"], "time_hex": row["time_hex"],
                       "K": row["K_current_m3"], "delta_C": d["baseline_local_cisd_proxy_signed_hartree"],
                       "delta_M": row["signed_shift_estimate_hartree"], "delta": d["direct_signed_shift_hartree"],
                       "width": row["empirical_width_hartree"], "core": row, "abstain": row["abstained"],
                       "m1_eligible": None, "M1_budget": row["frozen_pauli_rotation_budget"],
                       "baseline_budget": d["main_baseline_budget"], "baseline_time": row["time_hartree_inverse"],
                       "baseline_scope": "same_time_main_baseline_gamma1.02_not_condition_B0",
                       "truth_valid": a["physical_branch_correct"],
                       "saved_coverage": abs(d["direct_signed_shift_hartree"] - row["signed_shift_estimate_hartree"])
                                         <= row["empirical_width_hartree"],
                       "cheap_budgets": {float(g): b for g, b in json.loads(d["baseline_budgets_by_gamma"]).items()},
                       "cheap_eligible": {g: None for g in GAMMAS},
                       "prediction_source": "hcl_prediction", "scoring_source": "hcl_scoring+hcl_audit",
                       "original_branch_integer_score": d["branch_correct"],
                       "decomposition": {**decompose(None, None, None, None, None, None, False),
                                         "reason": "audit_common_H_reference_target_is_not_independent_ground_origin"}})
    return coords, []


def scalar_tables(coords, decisions):
    cheap_rows, spectral, windows, decomposition, oracles, same_time_oracles, model = [], [], [], [], [], [], []
    cmap = index(coords, lambda x: (x["condition"], x["candidate_id"]))
    baseline_rows = {name: min((r for r in coords if r["condition"] == name), key=lambda x: x["time"])
                     for name in {r["condition"] for r in coords}}
    for r in coords:
        cid = {"condition": r["condition"], "family": r["family"], "contract": r["contract"],
               "candidate_id": r["candidate_id"], "time": r["time"], "time_hex": r["time_hex"], "K": r["K"]}
        e, c = abs(r["delta"]), abs(r["delta_C"])
        ec, em = abs(r["delta_C"] - r["delta"]), abs(r["delta_M"] - r["delta"])
        require(finite(e, c, ec, em, r["width"]) and r["width"] >= 0, "scalar finite gate")
        for gamma in (1, *GAMMAS):
            calc = cheap_capacity(e, c, gamma)
            b = gamma * BETA * r["K"] / (r["time"] * (EPS - c)) if c < EPS else None
            if gamma in r["cheap_budgets"] and b is not None:
                close(b, r["cheap_budgets"][gamma], "native fixed gamma budget reconciliation", 1e-8)
                b = r["cheap_budgets"][gamma]
            lhs = e + BETA * r["K"] / (r["time"] * b) if b is not None else None
            cheap_rows.append({**cid, "delta_C_signed_hartree": r["delta_C"],
                               "delta_direct_signed_hartree": r["delta"], "e_hartree": e, "c_hartree": c,
                               "signed_point_error_hartree": ec, "gamma": gamma,
                               "gamma_scope": "diagnostic_unmargined_not_operational" if gamma == 1 else "saved_fixed_gamma",
                               "frozen_or_diagnostic_budget": b,
                               "native_eligible": r["cheap_eligible"].get(gamma),
                               "safe_arithmetic": lhs <= EPS if lhs is not None else None,
                               "physical_truth_valid": r["truth_valid"], **calc,
                               "source": r["prediction_source"] + ";" + r["scoring_source"],
                               "evidence_class": "post_hoc_development_arithmetic"})
        core = r["core"]
        close(core["e_use_hartree"], abs(r["delta_M"]) + r["width"], "M1 e_use reconciliation")
        require((em <= r["width"]) == r["saved_coverage"], "saved width coverage reconciliation")
        if r["M1_budget"] is not None:
            close(r["M1_budget"], BETA * r["K"] / (r["time"] * (EPS - core["e_use_hartree"])),
                  "M1 budget reconciliation", 1e-8)
        spectral.append({**cid, "delta_M_signed_hartree": r["delta_M"],
                         "delta_direct_signed_hartree": r["delta"], "E_C_hartree": ec, "E_M_hartree": em,
                         "point_improves_over_cheap": em < ec, "width_hartree": r["width"],
                         "empirical_width_covers": em <= r["width"], "physical_branch_valid": r["truth_valid"],
                         "original_integer_branch_score": r.get("original_branch_integer_score"),
                         "abstained": r["abstain"], "failure_reasons": core["failure_reasons"],
                         "requested_rank": core["requested_primary_dimension"],
                         "used_rank": core["primary_dimension_used"], "available_rank": core["available_dimension"],
                         "e_use_hartree": core["e_use_hartree"],
                         "positive_qpe_allowance": EPS - core["e_use_hartree"] > 0,
                         "native_candidate_eligible": r["m1_eligible"], "M1_frozen_budget": r["M1_budget"],
                         "width_claim_class": "empirical_not_certificate", "source": r["prediction_source"]})
        comparators = [(r["baseline_scope"], r["baseline_budget"])]
        comparators += [("same_time_fixed_cheap_gamma_" + str(g), b) for g, b in r["cheap_budgets"].items()]
        for label, b in comparators:
            same_time = label.startswith("same_time_")
            baseline_point = baseline_rows[r["condition"]]
            comparator_point = r if same_time else baseline_point
            comparator_safe = (comparator_point["truth_valid"] and abs(comparator_point["delta"])
                               + BETA * r["K"] / (comparator_point["time"] * b) <= EPS)
            for eta in (0, .10):
                win = width_window(r["delta_M"], r["time"], r["K"], b, eta)
                valid = comparator_safe and win is not None
                windows.append({**cid, "comparator_scope": label, "comparator_budget": b,
                                "comparison_time": r["time"], "comparator_saved_native_time":
                                    r["baseline_time"] if label == r["baseline_scope"] else r["time"],
                                "named_reference_at_its_own_time_is_safe": comparator_safe,
                                "eta": eta, "w_win_hartree": win, "w_current_hartree": r["width"],
                                "arithmetic_window_valid": valid,
                                "no_nonnegative_width_can_win": win < 0 if win is not None else None,
                                "current_width_within_window": r["width"] <= win if valid else None,
                                "native_rank_abstention_gate_unchanged": r["abstain"],
                                "window_is_operational_success_claim": False,
                                "evidence_class": "post_hoc_development_arithmetic"})
        native_gamma = 1.02 if r["family"] == "HCl" else 1.01
        cb = r["cheap_budgets"][native_gamma]
        truth_budget = BETA * r["K"] / (r["time"] * (EPS - e)) if e < EPS and r["truth_valid"] else None
        reference_safe = r["truth_valid"] and e + BETA * r["K"] / (r["time"] * cb) <= EPS
        same_time_oracles.append({**cid, "same_time_reference_gamma": native_gamma,
                                 "same_time_cheap_budget": cb, "same_time_reference_safe": reference_safe,
                                 "same_time_perfect_truth_budget": truth_budget,
                                 "S_max_same_time": 1 - truth_budget / cb if truth_budget is not None and reference_safe else None,
                                 "headroom_bound_type": "fixed_comparator_cost_free_truth_oracle_arithmetic",
                                 "intervention_achievability": "not_established"})
        decomposition.append({**cid, "used_prefix_dimension": core["primary_dimension_used"],
                              **r["decomposition"]})
    scored_decisions = []
    for d in decisions:
        r = cmap[d["condition"], d["candidate_id"]]
        require(d["time"] == r["time"], "decision coordinate join")
        e, c, b = abs(r["delta"]), abs(r["delta_C"]), d["frozen_budget"]
        resolution = BETA * r["K"] / (r["time"] * b)
        lhs = e + resolution
        close(lhs, d["saved_lhs"], "saved decision safety lhs")
        raw_safe = lhs <= EPS
        require(raw_safe == d["saved_raw_safe"], "saved raw safety flag")
        require((raw_safe and d["procedurally_valid"]) == d["saved_safe"], "saved procedural safety flag")
        scored_decisions.append({**d, "K": r["K"], "e_hartree": e, "c_hartree": c,
                                 "underestimation_hartree": e - c,
                                 "budget_margin_capacity_hartree": EPS - c - resolution,
                                 "safety_slack_hartree": EPS - lhs, "qpe_resolution_hartree": resolution,
                                 "safety_reconciled": True, "budget_changed": False})
    for condition in sorted({r["condition"] for r in coords}):
        rows = [r for r in coords if r["condition"] == condition]
        require(len(rows) == 3, "native contract must contain exactly three saved candidates")
        eligible_truth = [r for r in rows if r["truth_valid"] and abs(r["delta"]) < EPS]
        if not eligible_truth:
            oracles.append({"condition": condition, "status": "indeterminate_no_valid_saved_truth"})
            continue
        cost = lambda r: BETA * r["K"] / (r["time"] * (EPS - abs(r["delta"])))
        best = min(eligible_truth, key=cost)
        baseline_row = min(rows, key=lambda r: r["time"])
        baseline = baseline_row["baseline_budget"]
        safe_reference = abs(baseline_row["delta"]) + BETA * baseline_row["K"] / (baseline_row["time"] * baseline) <= EPS
        oracles.append({"condition": condition, "family": best["family"], "contract": best["contract"],
                        "saved_candidate_count": 3, "valid_truth_candidates": len(eligible_truth),
                        "oracle_candidate_id": best["candidate_id"], "oracle_budget": cost(best),
                        "reference_budget": baseline, "reference_scope":
                            "lowest_saved_time_main_gamma1.02_not_formal_selected_baseline" if best["family"] == "HCl"
                            else baseline_row["baseline_scope"],
                        "reference_safe": safe_reference,
                        "oracle_relative_saving": 1 - cost(best) / baseline if safe_reference else None,
                        "oracle_is_attainable_intervention": False,
                        "intervention_achievability": "not_established",
                        "evidence_class": "post_hoc_fixed_native_candidate_oracle"})
        if best["family"] == "H-chain":
            selected = next(d for d in scored_decisions if d["condition"] == condition and d["arm"] == "B2")
            model_ratio = .5 * (1 - .5 ** 4 / 5) / (.8 * (1 - .8 ** 4 / 5))
            model.append({"condition": condition, "fixed_time_ratio": .5 / .8,
                          "leading_model_budget_ratio": model_ratio,
                          "leading_model_saving": 1 - model_ratio,
                          "saved_B2_budget_ratio": selected["B_over_B0"],
                          "saved_B2_saving": 1 - selected["B_over_B0"],
                          "saving_minus_model_percentage_points": 100 * (model_ratio - selected["B_over_B0"]),
                          "saved_selected_candidate": selected["candidate_id"],
                          "saved_B2_safe": selected["saved_safe"],
                          "safe_status_is_empirical_evidence_not_model_inference": True,
                          "difference_is_independent_causal_component": False})
    return {"budget_safety_capacity": cheap_rows, "selected_frozen_budget_safety": scored_decisions,
            "m1_point_width_abstention": spectral, "width_decision_windows": windows,
            "m1_reference_error_decomposition": decomposition, "oracle_headroom_by_contract": oracles,
            "same_time_oracle_headroom": same_time_oracles,
            "hchain_model_vs_observation": model}


def resource_rows(src):
    rows = []
    def visit(name, value, pointer, scope):
        if isinstance(value, dict):
            for k, v in value.items():
                visit(name, v, pointer + "/" + str(k), scope)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                visit(name, v, pointer + "/" + str(i), scope)
        else:
            low = pointer.lower()
            unit = ("KiB" if "kib" in low else "bytes" if "bytes" in low
                    else "seconds" if "seconds" in low else "metadata_or_saved_count")
            rows.append({"source_id": name, "source_path": src.rows[name]["path"],
                         "saved_json_pointer": pointer, "saved_value": value, "unit": unit,
                         "cost_scope": scope, "summed_or_converted": False,
                         "measured_in_current_analysis": False})
    for name in src.rows:
        if "resource" in name:
            scope = ("validation_truth_or_ground_not_operational_calibration" if any(k in name for k in ("ground", "truth", "scored"))
                     else "shared_preparation_reference_not_incremental_H1" if any(k in name for k in ("input", "reference"))
                     else "saved_acquisition_nested_timers_and_process_peaks_not_additive")
            visit(name, src.read(name), "", scope)
    for tag in ("odd", "h8"):
        visit(tag + "_prediction", src.read(tag + "_prediction")["schedule_resource"],
              "/schedule_resource", "combined_shared_path_q0_comparator_excluded_not_cold_cost")
    return rows


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                             for k, v in row.items()})


def file_manifest(root, paths):
    return {"manifest_self_excluded": True, "files": [
        {"path": p, "bytes": len((root / p).read_bytes()), "sha256": digest((root / p).read_bytes())}
        for p in sorted(paths)]}


def freeze_manifest(root):
    require(not (root / DOCS / "design_manifest.json").exists(), "design manifest already exists")
    registry = json.loads((root / DOCS / "source_registry.json").read_text())
    verify_sources(root, registry)
    paths = [str(p.relative_to(root)) for p in (root / DOCS).iterdir() if p.is_file()]
    paths += ["review_response/budget_safety_mechanism_analysis.py", "review_tests/test_budget_safety_mechanism_analysis.py"]
    (root / DOCS / "design_manifest.json").write_bytes(json_bytes(file_manifest(root, paths)))


def run(root, freeze_commit):
    require(git(root, "rev-parse", "HEAD").decode().strip() == freeze_commit, "HEAD must be design freeze commit")
    require(not git(root, "diff", "--name-only") and not git(root, "diff", "--cached", "--name-only"), "tracked tree clean")
    protocol = json.loads((root / DOCS / "analysis_protocol.json").read_text())
    require(protocol["base_snapshot"] == "7cdee807c09ebfc7a4d11e7e275ed8d6258e9452", "base identity")
    manifest = json.loads((root / DOCS / "design_manifest.json").read_text())
    for r in manifest["files"]:
        b = (root / r["path"]).read_bytes()
        require(digest(b) == r["sha256"] and git(root, "show", freeze_commit + ":" + r["path"]) == b,
                "design/implementation freeze byte gate")
    require(git(root, "show", freeze_commit + ":" + DOCS + "/design_manifest.json")
            == (root / DOCS / "design_manifest.json").read_bytes(), "manifest commit gate")
    registry = json.loads((root / DOCS / "source_registry.json").read_text())
    checked_before = verify_sources(root, registry)
    output = root / OUT
    require(not output.exists(), "never overwrite/re-run main analysis output")
    started = time.perf_counter()
    src = Sources(root, registry)
    coords, decisions = hf_rows(src)
    for tag in ("even", "odd", "h8"):
        c, d = chain_rows(src, tag)
        coords += c
        decisions += d
    c, _ = hcl_rows(src)
    coords += c
    require(len(coords) == protocol["expected_coordinate_count"], "coordinate count gate")
    tables = scalar_tables(coords, decisions)
    require(len(tables["budget_safety_capacity"]) == protocol["expected_cheap_rows"], "cheap table count")
    require(len(decisions) == protocol["expected_selected_decisions"], "saved decisions count")
    tables["resource_accounting_scope"] = resource_rows(src)
    summary = {"status": protocol["stop_status"], "design_freeze_commit": freeze_commit,
               "direction": protocol["study_direction"], "claim_class": protocol["claim_class"],
               "table_counts": {k: len(v) for k, v in tables.items()},
               "conditions": {}, "new_scientific_acquisition_count": 0,
               "new_PF_actions": 0, "new_H_actions": 0, "new_truth_ground_gap": 0,
               "GPU_operations": 0, "runtime_arrays_opened": 0,
               "policy_budget_threshold_modified": False, "next_stage_authorized": False,
               "paper_landing_requires_review": True, "H3": "reference_failed_not_scored_not_effect_zero"}
    for name in sorted({r["condition"] for r in coords}):
        rs = [r for r in tables["m1_point_width_abstention"] if r["condition"] == name]
        ss = [r for r in tables["selected_frozen_budget_safety"] if r["condition"] == name]
        summary["conditions"][name] = {"coordinates": len(rs),
            "M1_point_improves": sum(r["point_improves_over_cheap"] for r in rs),
            "M1_abstentions": sum(r["abstained"] for r in rs),
            "empirical_width_covers": sum(r["empirical_width_covers"] for r in rs),
            "physical_branch_valid": sum(r["physical_branch_valid"] for r in rs),
            "selected_actions": {r["arm"]: {k: r[k] for k in ("candidate_id", "saved_safe", "safety_slack_hartree", "B_over_B0", "q")}
                                 for r in ss}}
    checked_after = verify_sources(root, registry)
    audit = {"source_checks_before": checked_before, "source_checks_after": checked_after,
             "source_bytes_unchanged": checked_before == checked_after,
             "decoded_scalar_sources": sorted(set(src.accesses)),
             "source_scope": "tracked_registry_only_no_runtime_arrays",
             "new_scientific_computation": 0,
             "scalar_analysis_wall_seconds": time.perf_counter() - started,
             "wall_scope": "after_freeze_source_preflight_through_scalar_tables_and_postflight_not_total_CLI",
             "raw_unwrap_integers_compared": False, "saved_decision_checks": len(decisions)}
    output.mkdir()
    for name, rows in tables.items():
        write_csv(output / (name + ".csv"), rows)
    (output / "analysis.json").write_bytes(json_bytes({"summary": summary, "tables": tables}))
    (output / "COMPLETE.json").write_bytes(json_bytes(summary))
    (output / "execution_audit.json").write_bytes(json_bytes(audit))
    (output / "manifest.json").write_bytes(json_bytes(file_manifest(root, [str(p.relative_to(root))
                                                                         for p in output.iterdir()])))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--freeze-manifest", action="store_true")
    parser.add_argument("--design-freeze-commit")
    args = parser.parse_args()
    if args.freeze_manifest:
        freeze_manifest(args.root.resolve())
    else:
        require(args.design_freeze_commit is not None, "explicit design freeze required")
        run(args.root.resolve(), args.design_freeze_commit)


if __name__ == "__main__":
    main()
