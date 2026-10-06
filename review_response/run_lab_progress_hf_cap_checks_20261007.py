#!/usr/bin/env python3
"""Frozen HF cap sensitivity checks; reuse existing coefficients and PF code.

Run ``freeze`` before ``score``. Selection never loads a molecular cache or
direct truth. Published outputs are scalar JSON/CSV; vectors remain in memory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/lab_progress_hf_cap_checks_20261007"
PRED = ROOT / "artifacts/server_practical_calibration_minimal_20260923_79035cc/predictions.json"
BASE_PROTOCOL = ROOT / "review_response/practical_calibration_minimal_protocol.json"
S0 = ROOT / "artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201/scoring.csv"
CONDITIONS = ("HF_full_eq_sto3g", "HF_full_stretch150_sto3g")
CAPS = (0.5, 1.0, 1.8)
BETA = 1.2
MARGIN = 1.01


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def signed_model(model, t):
    return sum(float(v) * float(t) ** int(p) for p, v in
               zip(model["coefficient_powers"], model["coefficient_values"], strict=True))


def cost(t, error, rotations, epsilon):
    return BETA * rotations / (t * (epsilon - error)) if error < epsilon else None


def selection(pf, cap, epsilon):
    """Same 35,001-point linear specification as the original cap optimizer."""
    tp = pf["proxy_analytic_time"]
    best = None
    for i in range(35001):
        relative = .05 + (cap - .05) * i / 35000
        t = relative * tp
        shift = signed_model(pf["model"], t)
        c = cost(t, abs(shift), pf["rotations"], epsilon)
        if c is not None and (best is None or c < best["predicted_cost"]):
            best = dict(condition=pf["condition"], formula=pf["formula"], cap=cap,
                        grid_index=i, selected_time=t, relative_time=relative,
                        predicted_signed_shift=shift, predicted_error=abs(shift),
                        predicted_cost=c, budget=MARGIN * c, rotations=pf["rotations"],
                        at_boundary=i in (0, 35000))
    if best is None:
        raise RuntimeError("No feasible model point")
    return best


def source_registry(paths, snapshot):
    records = []
    for p in paths:
        rel = str(p.relative_to(ROOT))
        expected = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{snapshot}:{rel}"])
        if expected != p.read_bytes():
            raise RuntimeError(f"Input differs from snapshot: {rel}")
        records.append(dict(path=rel, sha256=sha(p), verified_snapshot_commit=snapshot,
                            origin_result_commit=git("log", "-1", "--format=%H", snapshot, "--", rel)))
    return records


def freeze():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "SELECTION_FROZEN.json").exists():
        raise RuntimeError("Freeze already exists; preserve original run")
    original = read(PRED)
    base = read(BASE_PROTOCOL)
    epsilon = base["target_error_hartree"]
    predictions = []
    coarse_times, fine_times = {}, {}
    models = []
    for condition in original["conditions"]:
        if condition["condition"] not in CONDITIONS:
            continue
        for pf in condition["pf_predictions"]:
            if pf["diagnostic"]["fallback_sentinel_residual"] or pf["diagnostic"]["fallback_sign"]:
                raise RuntimeError("Cap comparison would also alter another fallback")
            picks = [selection(pf, cap, epsilon) for cap in CAPS]
            old = pf["optimum"]
            assert math.isclose(picks[0]["selected_time"], old["time"], rel_tol=1e-14)
            assert math.isclose(picks[0]["predicted_cost"], old["cost"], rel_tol=1e-14)
            predictions.extend(picks)
            key = condition["condition"] + "__" + pf["formula"]
            anchor = .025 * pf["proxy_analytic_time"]
            maximum = max(p["selected_time"] for p in picks)
            coarse = sorted(set([anchor + (maximum - anchor) * i / 64 for i in range(65)]
                                + [p["selected_time"] for p in picks]))
            fine = sorted(set(coarse + [(a + b) / 2 for a, b in zip(coarse[:-1], coarse[1:])]))
            coarse_times[key], fine_times[key] = coarse, fine
            models.append(dict(condition=condition["condition"], formula=pf["formula"],
                               model=pf["model"], proxy_analytic_time=pf["proxy_analytic_time"],
                               original_diagnostic=pf["diagnostic"], rotations=pf["rotations"]))
    assert len(predictions) == 12
    joint = []
    for condition in CONDITIONS:
        for cap in CAPS:
            selected = min((p for p in predictions if p["condition"] == condition and p["cap"] == cap),
                           key=lambda p: p["predicted_cost"])
            joint.append(dict(condition=condition, cap=cap, formula=selected["formula"],
                              selected_time=selected["selected_time"], budget=selected["budget"]))
    snapshot = git("rev-parse", "HEAD")
    paths = [PRED, BASE_PROTOCOL, S0, ROOT / "review_response/run_practical_calibration_minimal.py",
             ROOT / "review_response/run_h01_approximate_state_calibration.py",
             ROOT / "review_response/run_full_electron_nh3_higher_term_diagnosis.py"]
    protocol = dict(schema="lab_progress_hf_cap_sensitivity_v1", frozen_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    authorization="User 2026-10-07 authorized reasonable additional verification conditions and parallel execution",
                    evaluation_type="post-hoc fixed development sensitivity comparison; not independent holdout",
                    source_registry=source_registry(paths, snapshot), conditions=list(CONDITIONS),
                    formulae=base["formulae"], input_state="original CISD", models=models,
                    target_error_hartree=epsilon, qpe_beta=BETA, budget_multiplier=MARGIN,
                    caps=list(CAPS), optimization_grid=dict(lower_relative=.05, points=35001,
                    upper_relative="specified cap", kind="linear, recreated per cap exactly as original optimizer"),
                    changed_parameter="cancellation-triggered upper cap only",
                    unchanged_rules="original r=0.02 and other diagnostics retained; no residual/sign fallback active on these HF PFs",
                    model_refitting=False, original_result_modified=False,
                    source_cache_sha256={c: base["source_identity"]["pickle_sha256"][c] for c in CONDITIONS},
                    source_hamiltonian_sha256={c: base["source_identity"]["hamiltonian_sha256"][c] for c in CONDITIONS},
                    coarse_truth_times=coarse_times, refined_truth_times=fine_times,
                    branch_rule="anchor at .025 tproxy, maximum exact-state overlap; then maximum preceding-vector overlap",
                    branch_checks="64 coarse intervals versus all midpoint-refined intervals; all coarse shifts <= 1e-9 Ha difference; previous-vector overlap >= .9; independent-ground rule agreement and residual checks",
                    branch_failure_policy="stop this fixed run as numerically invalid; no adaptive truth coordinates or result rescue",
                    proxy_times="unique 12 preselected PF/time pairs only, full CISD and exact state",
                    truth_access_barrier="write predictions, protocol, freeze hashes before cache loading and any new direct evaluation",
                    stop_point="score the fixed 12 choices, 6 joint selections and saved 6-condition controls; no rescue, refit or rule optimization",
                    public_data_policy="only scalar JSON/CSV/code/report; no cache, matrix, vector, unitary or exact state")
    write(OUT / "protocol.json", protocol)
    write(OUT / "predictions.json", dict(pf_choices=predictions, joint_choices=joint,
                                         oracle_information_used_for_new_selection=False))
    write(OUT / "SELECTION_FROZEN.json", dict(protocol_sha256=sha(OUT / "protocol.json"),
                                             predictions_sha256=sha(OUT / "predictions.json"),
                                             runner_sha256=sha(Path(__file__)),
                                             truth_scoring_started=False))
    print(f"Frozen 12 PF choices and 6 joint choices; refined branch points {sum(map(len, fine_times.values()))}", flush=True)


def verify_freeze():
    frozen = read(OUT / "SELECTION_FROZEN.json")
    for filename, key in (("protocol.json", "protocol_sha256"), ("predictions.json", "predictions_sha256")):
        assert sha(OUT / filename) == frozen[key]
    assert sha(Path(__file__)) == frozen["runner_sha256"]
    protocol = read(OUT / "protocol.json")
    for record in protocol["source_registry"]:
        assert sha(ROOT / record["path"]) == record["sha256"]
    return protocol, read(OUT / "predictions.json")


def write_csv(path, rows):
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def score(cache_dir):
    protocol, predictions = verify_freeze()
    if (OUT / "COMPLETE").exists():
        raise RuntimeError("Already complete; preserve first result")
    sys.path.insert(0, str(ROOT / "review_response"))
    import numpy as np
    import scipy
    from scipy.sparse.linalg import expm_multiply
    import run_h01_approximate_state_calibration as h01
    import run_full_electron_nh3_higher_term_diagnosis as diagnosis
    assert diagnosis.BETA == BETA
    started = time.perf_counter()
    epsilon = protocol["target_error_hartree"]
    scoring, branch_rows, cache_audit, direct_lookup = [], [], [], {}
    for condition in CONDITIONS:
        path = cache_dir / f"{condition}.pkl"
        assert sha(path) == protocol["source_cache_sha256"][condition]
        system = h01._load_system(path)
        assert system["hamiltonian_sha256"] == protocol["source_hamiltonian_sha256"][condition]
        assert h01._sparse_hash(system["hamiltonian"]) == system["hamiltonian_sha256"]
        cisd = system["states"]["cisd"]
        exact = system["state"]
        assert abs(np.linalg.norm(cisd) - 1) < 1e-10
        assert np.linalg.norm(system["hamiltonian"] @ exact - system["energy"] * exact) < 1e-8
        cache_audit.append(dict(condition=condition, source_pickle_sha256=sha(path),
                                hamiltonian_sha256=system["hamiltonian_sha256"], sector_dimension=len(exact),
                                cisd_exact_overlap_probability=float(abs(np.vdot(exact, cisd))**2)))
        for model_record in [m for m in protocol["models"] if m["condition"] == condition]:
            formula = model_record["formula"]
            key = condition + "__" + formula
            sequence = protocol["formulae"][formula]["s2_sequence"]
            rotations = model_record["rotations"]
            assert h01._rotation_count(system, sequence) == rotations
            selected = [p for p in predictions["pf_choices"] if p["condition"] == condition and p["formula"] == formula]
            selected_times = set(p["selected_time"] for p in selected)
            coarse_set = set(protocol["coarse_truth_times"][key])
            prev_coarse = prev_fine = None
            results = {}
            for t in protocol["refined_truth_times"][key]:
                unitary, _ = diagnosis._build_cpu(system, sequence, t)
                point, prev_fine = h01._branch_schur_point(unitary, exact, system["energy"], t, rotations, prev_fine)
                # The component builder and the state-action code must agree.
                assert np.linalg.norm(unitary.conj().T @ unitary - np.eye(len(exact))) < 1e-10
                assert point["eigenpair_residual_2_norm"] < 1e-10
                assert not point["branch_selection_disagrees_with_independent_rule"]
                assert point["adjacent_selected_vector_overlap_probability"] is None or point["adjacent_selected_vector_overlap_probability"] >= .9
                if t in coarse_set:
                    cp, prev_coarse = h01._branch_schur_point(unitary, exact, system["energy"], t, rotations, prev_coarse)
                    assert abs(cp["signed_direct_shift_hartree"] - point["signed_direct_shift_hartree"]) < 1e-9
                    assert cp["adjacent_selected_vector_overlap_probability"] is None or cp["adjacent_selected_vector_overlap_probability"] >= .9
                branch_rows.append(dict(condition=condition, formula=formula, time=t,
                                         is_coarse=t in coarse_set, is_selected=t in selected_times,
                                         signed_direct_shift=point["signed_direct_shift_hartree"],
                                         exact_overlap_probability=point["ground_overlap_probability"],
                                         adjacent_overlap_probability=point["adjacent_selected_vector_overlap_probability"],
                                         eigenpair_residual=point["eigenpair_residual_2_norm"],
                                         independent_rule_agrees=True))
                if t not in selected_times:
                    continue
                pf_vectors, _ = h01._apply_pf_cpu(system, sequence, t, np.column_stack([cisd, exact]))
                assert np.linalg.norm(pf_vectors - unitary @ np.column_stack([cisd, exact])) < 1e-10
                ref_cisd = expm_multiply(1j * t * system["hamiltonian"], cisd)
                ref_exact = np.exp(1j * system["energy"] * t) * exact
                g_cisd = float(np.vdot(ref_cisd, pf_vectors[:, 0]).imag / t)
                g_exact = float(np.vdot(ref_exact, pf_vectors[:, 1]).imag / t)
                results[t] = dict(delta=point["signed_direct_shift_hartree"], g_cisd=g_cisd, g_exact=g_exact)
            for p in selected:
                t = p["selected_time"]
                vals = results[t]
                delta = vals["delta"]
                model_difference = p["predicted_signed_shift"] - vals["g_cisd"]
                state_difference = vals["g_cisd"] - vals["g_exact"]
                proxy_difference = vals["g_exact"] - delta
                assert abs(model_difference + state_difference + proxy_difference - (p["predicted_signed_shift"] - delta)) < 1e-18
                actual_cost = cost(t, abs(delta), rotations, epsilon)
                qpe = BETA * rotations / (t * p["budget"])
                total = abs(delta) + qpe
                r = dict(**p, signed_direct_shift=delta, direct_error=abs(delta),
                         g_cisd=vals["g_cisd"], g_exact=vals["g_exact"],
                         model_difference=model_difference, state_difference=state_difference,
                         proxy_difference=proxy_difference, total_signed_prediction_difference=p["predicted_signed_shift"] - delta,
                         actual_required_cost=actual_cost, qpe_error=qpe, total_error=total,
                         precision_margin=epsilon - total, precision_pass=total <= epsilon,
                         budget_over_actual_required_cost=p["budget"] / actual_cost if actual_cost else None)
                scoring.append(r)
                direct_lookup[(condition, formula, p["cap"])] = r
            print(f"Scored {condition} {formula}, {len(protocol['refined_truth_times'][key])} branch points", flush=True)
    # Existing exact-time scoring is an external numerical baseline, not a source of new choices.
    controls = list(csv.DictReader(S0.open()))
    reproduced = []
    for c in controls:
        if c["condition"] not in CONDITIONS:
            continue
        r = direct_lookup[(c["condition"], c["selected_formula"], .5)]
        err = abs(r["signed_direct_shift"] - float(c["exact_time_direct_signed_shift_hartree"]))
        assert err < 1e-9
        reproduced.append(dict(condition=c["condition"], direct_shift_difference=err,
                                frozen_budget_difference=r["budget"] - float(c["frozen_budget_gamma_1_01"])))
    joint = []
    for p in predictions["joint_choices"]:
        r = direct_lookup[(p["condition"], p["formula"], p["cap"])]
        original = direct_lookup[(p["condition"], p["formula"], .5)]
        joint.append(dict(**r, budget_ratio_to_original_cap= r["budget"] / original["budget"],
                          budget_reduction_from_original_cap=1-r["budget"] / original["budget"]))
    summary = dict(schema="lab_progress_hf_cap_sensitivity_results_v1", frozen_inputs_verified=True,
                   original_cap_reproduced=reproduced, cache_audit=cache_audit,
                   pf_choices_scored=len(scoring), joint_choices_scored=len(joint),
                   pf_precision_pass_count=sum(r["precision_pass"] for r in scoring),
                   joint_precision_pass_count=sum(r["precision_pass"] for r in joint),
                   branch_point_count=len(branch_rows), new_model_fit_count=0,
                   source_results_unchanged=True, source_registry=protocol["source_registry"],
                   environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                                    thread_limits={k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")}),
                   wall_seconds=time.perf_counter()-started,
                   branch_checks=dict(coarse_refined_selected_shift_tolerance=1e-9,
                                      all_independent_ground_rules_agree=True,
                                      minimum_adjacent_overlap=min(r["adjacent_overlap_probability"] for r in branch_rows if r["adjacent_overlap_probability"] is not None),
                                      maximum_eigenpair_residual=max(r["eigenpair_residual"] for r in branch_rows)))
    write_csv(OUT / "scoring.csv", scoring)
    write_csv(OUT / "joint_selection_scoring.csv", joint)
    write_csv(OUT / "branch_audit.csv", branch_rows)
    write_csv(OUT / "existing_six_condition_controls.csv", controls)
    write(OUT / "summary.json", summary)
    (OUT / "COMPLETE").write_text("Fixed 12 choices scored; no optimization after truth access.\n")
    print(json.dumps(dict(pf_pass=summary["pf_precision_pass_count"], joint_pass=summary["joint_precision_pass_count"], wall_seconds=summary["wall_seconds"])))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("phase", choices=("freeze", "score"))
    parser.add_argument("--cache-dir", type=Path,
                        default=Path("/tmp/pf-first-s0-hf-transfer-20260925/h01_hf_mechanism_transfer_20260922_VY56wx/cache"))
    args = parser.parse_args()
    freeze() if args.phase == "freeze" else score(args.cache_dir)


if __name__ == "__main__":
    main()
