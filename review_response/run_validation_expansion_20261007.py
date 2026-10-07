"""User-approved A1 -> A3 -> A6 -> B3; fixed coordinates, scalar publication."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import signal
import shutil
import subprocess
import sys
import time

import numpy as np
import scipy
from scipy.linalg import schur
from scipy.sparse.linalg import expm_multiply

from review_response._pf_first_study_experiment_a_support import sha256_array
from review_response._pf_first_study_phase_a_base import _mechanism_models
from review_response._pf_first_study_phase_b_base import _decomposition, _dominance_rows
from review_response.pf_first_study_experiment_a import track_direct_branch
from review_response.pf_first_study_phase_common import (
    align_to_reference, build_unitary, controlled_state_family, load_h4_source,
    model_cost, proxy_noise_hartree, quality_class, state_diagnostics,
)
from review_response import run_lab_progress_hchain_transfer_20261007 as chain
from review_response import run_lab_progress_hf_cap_checks_20261007 as hf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/validation_expansion_20261007"
PRIVATE = Path("/tmp/pf-validation-expansion-private-20261007")
OLD_CHAIN = "artifacts/lab_progress_hchain_transfer_20261007"
OLD_H4 = "artifacts/lab_progress_h4_state_checks_20261007"
OLD_HF = "artifacts/lab_progress_hf_cap_checks_20261007"
SCRIPT = Path(__file__)
EPS = 0.00015936001019904
BETA = 1.2
STAGES = ("a1_proxy", "a1_truth", "a3", "a6", "b3")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n")
    tmp.replace(path)


def rows(path):
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))


def csv_write(path, records):
    assert records
    fields = list(dict.fromkeys(k for row in records for k in row))
    with Path(path).open("w", newline="") as f:
        w = csv.DictWriter(f, fields, lineterminator="\n")
        w.writeheader()
        w.writerows({k: repr(v) if isinstance(v, (list, dict)) else v for k, v in row.items()} for row in records)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def freeze():
    if OUT.exists() or PRIVATE.exists():
        raise FileExistsError("one-shot output/private directory exists; no automatic rerun")
    base = read(ROOT / "PF_first_study_protocol_20260925.json")
    cp = read(ROOT / OLD_CHAIN / "protocol.json")
    h6 = next(s for s in cp["systems"] if s["system"] == "H6")
    input_path = Path("/home/abe/myproject/Evaluation_numGate_highorder") / h6["runtime_source"]
    assert sha(input_path) == h6["input_file_sha256"]
    ground_path = Path("/tmp/lab_progress_hchain_transfer_20261007/H6_ground.npz")
    assert ground_path.is_file()
    proposals = read(ROOT / "artifacts/lab_progress_validation_expansion_plan_20261007/proposed_scopes.json")
    a6 = next(c["proposed_scope"] for c in proposals["candidates"] if c["candidate_id"] == "A6")
    hf_base = read(ROOT / OLD_HF / "protocol.json")
    original = read(hf.PRED)
    choices, joint, models, coarse, fine = [], [], [], {}, {}
    for c in original["conditions"]:
        if c["condition"] not in hf.CONDITIONS:
            continue
        for pf in c["pf_predictions"]:
            assert not pf["diagnostic"]["fallback_sentinel_residual"] and not pf["diagnostic"]["fallback_sign"]
            pick = hf.selection(pf, 0.75, EPS)
            choices.append(pick)
            key = c["condition"] + "__" + pf["formula"]
            anchor = .025 * pf["proxy_analytic_time"]
            grid = sorted(set([anchor + (pick["selected_time"] - anchor) * i / 64 for i in range(65)] + [pick["selected_time"]]))
            coarse[key] = grid
            fine[key] = sorted(set(grid + [(a + b) / 2 for a, b in zip(grid[:-1], grid[1:])]))
            models.append(dict(condition=c["condition"], formula=pf["formula"], model=pf["model"],
                               proxy_analytic_time=pf["proxy_analytic_time"], rotations=pf["rotations"]))
    assert len(choices) == 4
    for c in hf.CONDITIONS:
        joint.append(min((p for p in choices if p["condition"] == c), key=lambda p: p["predicted_cost"]))
    cache = Path("/tmp/pf-first-s0-hf-transfer-20260925/h01_hf_mechanism_transfer_20260922_VY56wx/cache")
    for c in hf.CONDITIONS:
        assert sha(cache / (c + ".pkl")) == hf_base["source_cache_sha256"][c]
    sources = ["PF_first_study_protocol_20260925.json", OLD_CHAIN + "/protocol.json",
               OLD_CHAIN + "/ground_scalar_diagnostics.json", OLD_CHAIN + "/H6/direct_grid_m5_best.csv",
               OLD_H4 + "/direct_grid.csv", OLD_H4 + "/spectral_protocol.json",
               OLD_HF + "/protocol.json", OLD_HF + "/joint_selection_scoring.csv",
               "artifacts/pf_first_study_phase_a_20260925_6265243/predictions.json",
               "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/dominance_summary.csv",
               str(hf.PRED.relative_to(ROOT)), str(hf.BASE_PROTOCOL.relative_to(ROOT)),
               "review_response/run_lab_progress_hchain_transfer_20261007.py",
               "review_response/run_lab_progress_hf_cap_checks_20261007.py",
               "review_response/audit_lab_progress_h4_spectral_proxy_20261007.py",
               "review_response/_pf_first_study_phase_a_base.py", "review_response/_pf_first_study_phase_b_base.py",
               "review_response/run_pf_first_study_phase_a.py", "review_response/run_pf_first_study_phase_b.py",
               "review_response/pf_first_study_phase_common.py", "review_response/pf_first_study_experiment_a.py",
               "review_response/_pf_first_study_experiment_a_support.py",
               "review_response/run_h01_approximate_state_calibration.py",
               "review_response/run_full_electron_nh3_higher_term_diagnosis.py",
               "src/trotterlib/component_sector_pf.py", "src/trotterlib/sector_pf.py", "src/trotterlib/pf_decomposition.py"]
    snapshot = git("rev-parse", "HEAD")
    registry = []
    for path in sources:
        assert subprocess.check_output(["git", "show", snapshot + ":" + path], cwd=ROOT) == (ROOT / path).read_bytes()
        registry.append(dict(path=path, origin_result_commit=git("log", snapshot, "--diff-filter=A", "-1", "--format=%H", "--", path),
                             verified_snapshot_commit=snapshot, sha256=sha(ROOT / path),
                             git_blob_sha=git("rev-parse", snapshot + ":" + path)))
    OUT.mkdir(); PRIVATE.mkdir()
    shutil.copyfile(input_path, PRIVATE / "H6_input.npz")
    shutil.copyfile(ground_path, PRIVATE / "H6_ground.npz")
    protocol = dict(schema="approved_validation_expansion_v1", frozen_UTC=datetime.now(timezone.utc).isoformat(),
                    user_authorization="2026-10-07: execute GPT-reviewed A1 then A3 then A6 then B3; do not edit slides",
                    execution_order=list(STAGES), excluded=["B1", "B2", "new methods", "research strategy changes", "slide edits"],
                    input_snapshot_commit=snapshot, source_registry=registry, runner_sha256=sha(SCRIPT),
                    constants=base["constants"], formulae=base["formulae"],
                    h6_spec=h6, h6_private_ground_sha256=sha(ground_path),
                    h6_ground_origin_result_commit="8436a2f3644e0403ff5ebf19bee6caae364ae66e",
                    numerical_gates=base["numerical_gates"], mechanism=base["experiment_B_h4"],
                    A1=dict(case_count=56, evaluation_row_count=672, distinct_pf_times=88, max_full_pf_builds=176,
                            max_h_vector_actions=2640, max_pf_schur_calls=88, full_H_ground_solves=0,
                            exact_source="reuse retained prior H6 ground; certify hashes and public energy/residual",
                            backend="existing H6 MolecularActions component PF and block expm_multiply; same signed proxy and frozen H4 fit/classification helpers",
                            phase_convention="reuse controlled_state_family including its common fixed pivot convention; same across all PFs",
                            truth_barrier="save all proxy models and their hashes before PF Schur evaluation; artificial states are explicit oracle diagnostics"),
                    A3=dict(formula="m5_best", times=[0.4, 2.2834071119880326], max_full_pf_builds=1,
                            short_time_unitary_reused_from_A1=True, max_pf_schur_calls=2,
                            long_phase_target="saved reliable delta with original H6 ground energy; match phase only, no new continuation",
                            closure_gate=1e-12, original_selected_point_unchanged=3.0391925964974056),
                    A6=dict(formula="m5_best", times=a6["proposed_nine_point_grid"], new_coordinate_count=6,
                            repeated_saved_coordinate_count=3, max_full_pf_builds=9, max_pf_schur_calls=9,
                            method="same track_direct_branch; compare all three anchors to saved branch within 1e-9 Ha",
                            original_budget=17744668.46650517, original_minimum_cost=8946044.72065897),
                    B3=dict(cap=0.75, models=models, choices=choices, joint_choices=joint,
                            formulae=hf_base["formulae"], coarse_truth_times=coarse, refined_truth_times=fine,
                            branch_protocol=hf_base["branch_rule"], branch_checks=hf_base["branch_checks"],
                            max_full_pf_builds=sum(map(len, fine.values())), max_pf_schur_calls=sum(map(len, fine.values())) + sum(map(len, coarse.values())),
                            max_selected_state_pf_actions=8, max_reference_H_vector_actions=4,
                            cache_dir=str(cache), source_cache_sha256=hf_base["source_cache_sha256"],
                            source_hamiltonian_sha256=hf_base["source_hamiltonian_sha256"], model_refits=0),
                    resource_caps=dict(BLAS_threads=1, concurrent_workers=1, wall_seconds_per_stage=3600, memory_GiB_per_process=4),
                    stop="fixed package only; numerical gate failure stops affected stage; no reruns with adjusted times/gates/margins",
                    publication="scalar/code/protocol/report/hash only; private inputs and units stay outside public artifacts",
                    historical_results_modified=False)
    write(OUT / "protocol.json", protocol)
    write(OUT / "PROTOCOL_FROZEN.json", dict(protocol_sha256=sha(OUT / "protocol.json"), runner_sha256=sha(SCRIPT)))
    write(OUT / "B3_SELECTION_FROZEN.json", dict(choices=choices, joint_choices=joint,
                                               protocol_sha256=sha(OUT / "protocol.json"), new_truth_opened=False))
    print(json.dumps(dict(event="FROZEN", stages=list(STAGES), B3_branch_points=protocol["B3"]["max_full_pf_builds"])), flush=True)


def verify(stage):
    p = read(OUT / "protocol.json"); marker = read(OUT / "PROTOCOL_FROZEN.json")
    assert marker["protocol_sha256"] == sha(OUT / "protocol.json") and marker["runner_sha256"] == sha(SCRIPT)
    for s in p["source_registry"]:
        assert sha(ROOT / s["path"]) == s["sha256"]
    if (OUT / (stage + "_COMPLETE.json")).exists() or (OUT / (stage + "_FAILED.json")).exists():
        raise RuntimeError("completed/failed stage cannot be automatically rerun")
    index = STAGES.index(stage)
    if index:
        assert (OUT / (STAGES[index - 1] + "_COMPLETE.json")).exists()
    return p


def h6_actions(p):
    chain.PRIVATE = PRIVATE
    action = chain.MolecularActions("H6", dict(systems=[p["h6_spec"]]))
    with np.load(PRIVATE / "H6_ground.npz", allow_pickle=False) as data:
        exact, energy = data["state"], float(data["energy"])
    assert sha(PRIVATE / "H6_ground.npz") == p["h6_private_ground_sha256"]
    g = next(r for r in read(ROOT / OLD_CHAIN / "ground_scalar_diagnostics.json") if r["system"] == "H6")
    assert abs(energy - g["energy"]) < 1e-12
    assert np.linalg.norm(action.h @ exact - energy * exact) < 1e-10
    assert np.linalg.norm(sum(action.groups) - action.h) < 1e-12
    assert np.linalg.norm(action.h - action.h.conj().T) / max(np.linalg.norm(action.h), 1) < 1e-12
    return action, exact, energy


def a1_proxy(p):
    action, exact, energy = h6_actions(p)
    cisd = align_to_reference(action.cisd, exact)
    rhf = np.zeros_like(cisd); rhf[int(np.flatnonzero(action.indices == p["h6_spec"]["input_identity"]["RHF_reference_integer"])[0])] = 1
    rhf = align_to_reference(rhf, exact)
    spec = p["mechanism"]; controlled, chi = controlled_state_family(exact, cisd, spec["controlled_state"]["q_values"], spec["controlled_state"]["phase_values_radians"])
    states = {"rhf": rhf, "cisd": cisd, **controlled, "exact": exact}
    assert len(states) == 15 and abs(np.vdot(exact, chi)) < 1e-12
    for state in states.values():
        assert abs(np.linalg.norm(state) - 1) < 1e-12
    track = spec["fixed_time_mechanism_track"]
    train = set(track["training_time_magnitudes_hartree_inverse"])
    mags = sorted(train | set(track["evaluation_time_magnitudes_hartree_inverse"]))
    observations, models, diag = [], [], []
    for sid, state in states.items():
        diag.append(dict(state_id=sid, state_sha256=sha256_array(state), **state_diagnostics(action.h, state, exact, energy)))
    for fid, fs in p["formulae"].items():
        obs, units, signed = [], [], []
        for sign in (-1, 1):
            for mag in mags:
                t = sign * mag
                u = action.unitary(fs["s2_sequence"], t); repeat = action.unitary(fs["s2_sequence"], t)
                unitarity = float(np.linalg.norm(u.conj().T @ u - np.eye(400)))
                assert unitarity <= 1e-10
                values = action.proxies(u, list(states.values()), t)
                repeats = action.proxies(repeat, list(states.values()), t)
                for sid, value, value2 in zip(states, values, repeats, strict=True):
                    noise = proxy_noise_hartree(unitarity, abs(value - value2), action.hnorm, t)
                    rho, quality = quality_class(value, noise)
                    obs.append(dict(experiment_id="B", case_id="H6", formula_id=fid, state_id=sid,
                                    sign=sign, absolute_time=mag, time_hartree_inverse=t,
                                    proxy_imag_hartree=value, proxy_noise_hartree=noise, signal_to_noise_rho=rho,
                                    quality_class=quality, unitarity_residual_frobenius=unitarity,
                                    proxy_repeatability_error_hartree=abs(value - value2)))
                units.append(u); signed.append(t)
        np.savez(PRIVATE / (fid + "_units.npz"), units=np.asarray(units), times=np.asarray(signed))
        for i, mag in enumerate(mags):
            assert np.linalg.norm(units[i] - units[len(mags) + i].conj().T) / np.sqrt(400) < 1e-10
        training = [r for r in obs if r["absolute_time"] in train and r["state_id"] != "exact"]
        fm = _mechanism_models(training, list(states)[:-1], track["maximum_scaled_design_condition_number"])
        models.extend(dict(experiment_id="B", case_id="H6", formula_id=fid, **r) for r in fm)
        observations.extend(obs)
        print(json.dumps(dict(event="A1_PROXY", formula=fid, observations=len(obs), models=len(fm))), flush=True)
    assert action.full_builds == 176 and action.exponentials == 2640
    csv_write(OUT / "A1_observations.csv", observations); csv_write(OUT / "A1_models.csv", models)
    csv_write(OUT / "A1_state_diagnostics.csv", diag)
    write(OUT / "A1_PREDICTIONS_FROZEN.json", dict(protocol_sha256=sha(OUT / "protocol.json"),
          observations_sha256=sha(OUT / "A1_observations.csv"), models_sha256=sha(OUT / "A1_models.csv"),
          unitary_cache_hashes={fid: sha(PRIVATE / (fid + "_units.npz")) for fid in p["formulae"]},
          new_pf_eigenvalues_used=False, oracle_state_diagnostic=True))
    return dict(resources=action.resource(), states=15, models=len(models), observations=len(observations), exact_sha256=sha256_array(exact))


def a1_truth(p):
    frozen = read(OUT / "A1_PREDICTIONS_FROZEN.json")
    assert frozen["models_sha256"] == sha(OUT / "A1_models.csv") and frozen["observations_sha256"] == sha(OUT / "A1_observations.csv")
    assert frozen["protocol_sha256"] == sha(OUT / "protocol.json")
    with np.load(PRIVATE / "H6_ground.npz", allow_pickle=False) as d:
        exact, energy = d["state"], float(d["energy"])
    direct = []
    for fid in p["formulae"]:
        f = PRIVATE / (fid + "_units.npz"); assert sha(f) == frozen["unitary_cache_hashes"][fid]
        with np.load(f, allow_pickle=False) as data:
            units, times = data["units"], data["times"]
        for sign in (-1, 1):
            ids = np.flatnonzero(np.sign(times) == sign)
            tracked = track_direct_branch(units[ids], times[ids], exact, energy, 1e-8)
            for i, tr in zip(ids, tracked, strict=True):
                assert tr["eigenpair_residual_2_norm"] <= 1e-10
                direct.append(dict(experiment_id="B", case_id="H6", formula_id=fid,
                                   grid_role="mechanism_fixed", sign=sign, absolute_time=abs(float(times[i])),
                                   time_hartree_inverse=float(times[i]), **tr,
                                   branch_reliable=tr["ground_state_overlap_probability"] >= .9 and tr["previous_branch_overlap_probability"] >= .9))
    obs = rows(OUT / "A1_observations.csv")
    dec = _decomposition(phase_a_observations=[r for r in obs if r["state_id"] != "exact"],
                         exact_observations=[r for r in obs if r["state_id"] == "exact"],
                         model_rows=rows(OUT / "A1_models.csv"), direct_rows=direct,
                         b_evaluation_times=set(p["mechanism"]["fixed_time_mechanism_track"]["evaluation_time_magnitudes_hartree_inverse"]))
    assert len(dec) == 672 and max(abs(r["closure_residual_hartree"]) for r in dec) <= max(1e-12, 1e-8 * EPS)
    dominance = _dominance_rows(dec, EPS)
    csv_write(OUT / "A1_branch_audit.csv", direct); csv_write(OUT / "A1_error_decomposition.csv", dec)
    csv_write(OUT / "A1_dominance_summary.csv", dominance)
    count = dict(Counter(r["dominant_component"] for r in dominance))
    by_pf = {fid: dict(Counter(r["dominant_component"] for r in dominance if r["formula_id"] == fid)) for fid in p["formulae"]}
    invalid = [r for r in rows(OUT / "A1_models.csv") if r["model_id"] == "raw_positive_even_two_term" and r["status"] != "fit_ok"]
    return dict(case_count=56, evaluation_rows=len(dec), inherited_dominance_counts=count, per_formula=by_pf,
                primary_fit_not_identifiable_count=len(invalid), no_resolved_evaluation_case_count=sum(r["resolved_point_count"] == 0 for r in dominance),
                unreliable_branch_point_count=sum(not r["branch_reliable"] for r in direct), pf_schur_calls=len(direct),
                maximum_closure=max(abs(r["closure_residual_hartree"]) for r in dec),
                classification_helper_unchanged=True)


def a3(p):
    action, exact, energy = h6_actions(p)
    components, summaries = [], []
    target = next(r for r in rows(ROOT / OLD_CHAIN / "H6/direct_grid_m5_best.csv") if float(r["time"]) == p["A3"]["times"][1])
    assert target["branch_reliable"] == "True"
    short = next(r for r in rows(OUT / "A1_branch_audit.csv") if r["formula_id"] == "m5_best" and float(r["time_hartree_inverse"]) == .4)
    assert short["branch_reliable"] == "True"
    for t in p["A3"]["times"]:
        if t == .4:
            f = PRIVATE / "m5_best_units.npz"
            assert sha(f) == read(OUT / "A1_PREDICTIONS_FROZEN.json")["unitary_cache_hashes"]["m5_best"]
            with np.load(f, allow_pickle=False) as d:
                u = d["units"][int(np.flatnonzero(d["times"] == t)[0])]
            delta = float(short["direct_shift_hartree"])
        else:
            u = action.unitary(p["formulae"]["m5_best"]["s2_sequence"], t)
            delta = float(target["direct_shift"])
        tri, vectors = schur(u, output="complex", check_finite=False)
        vals = np.diag(tri); phases = np.angle(vals)
        distance = np.abs(np.angle(np.exp(1j * (phases - (energy + delta) * t))))
        selected = int(np.argmin(distance)); assert distance[selected] / t <= 1e-9
        weights = np.abs(vectors.conj().T @ exact) ** 2
        contributions = weights * np.sin(phases - energy * t) / t
        proxy = action.proxies(u, [exact], t)[0]
        other = float(np.sum(np.delete(contributions, selected))); ground = float(contributions[selected])
        sine = float(np.sin(t * delta) / t - delta)
        weight_loss = float((weights[selected] - 1) * np.sin(t * delta) / t)
        resid = float(np.max(np.linalg.norm(u @ vectors - vectors * vals[None, :], axis=0)))
        closure = abs(float(np.sum(contributions)) - proxy)
        bias_closure = abs(sine + weight_loss + other - (proxy - delta))
        assert resid <= 1e-10 and closure <= 1e-12 and bias_closure <= 1e-12
        assert np.linalg.norm(u.conj().T @ u - np.eye(400)) <= 1e-10
        assert abs(float(np.sum(weights)) - 1) <= 1e-12 and weights[selected] >= .9
        for j in range(400):
            components.append(dict(time=t, eigencomponent_index=j, tracked=j == selected, weight=float(weights[j]),
                                   relative_phase=float(np.angle(np.exp(1j * (phases[j] - energy * t)))), contribution=float(contributions[j])))
        summaries.append(dict(time=t, direct_shift=delta, exact_proxy=proxy, tracked_weight=float(weights[selected]),
                              other_weight=float(1 - weights[selected]), tracked_contribution=ground, other_contribution=other,
                              sine_bias=sine, weight_loss_bias=weight_loss, spectral_closure=closure,
                              bias_closure=bias_closure, eigenpair_residual=resid, phase_match_distance=float(distance[selected])))
    csv_write(OUT / "A3_spectral_components.csv", components); csv_write(OUT / "A3_spectral_summary.csv", summaries)
    return dict(points=summaries, scalar_component_rows=len(components), pf_schur_calls=2, resources=action.resource(), original_formal_classification_unchanged=True)


def a6(p):
    system, source = load_h4_source(ROOT, read(ROOT / "PF_first_study_protocol_20260925.json"))
    times = p["A6"]["times"]; sequence = p["formulae"]["m5_best"]["s2_sequence"]
    units = [build_unitary(system["spectra"], sequence, t) for t in times]
    direct = track_direct_branch(units, times, system["states"]["exact"], system["energy"], 1e-8)
    old = {float(r["time_hartree_inverse"]): r for r in rows(ROOT / OLD_H4 / "direct_grid.csv") if r["formula_id"] == "m5_best"}
    saved = []; result = []
    for t, u, d in zip(times, units, direct, strict=True):
        assert np.linalg.norm(u.conj().T @ u - np.eye(36)) <= 1e-10 and d["eigenpair_residual_2_norm"] <= 1e-10
        reliable = d["ground_state_overlap_probability"] >= .9 and d["previous_branch_overlap_probability"] >= .9
        matches = [k for k in old if abs(k - t) < 1e-12]
        if matches:
            difference = abs(float(old[matches[0]]["direct_shift_hartree"]) - d["direct_shift_hartree"])
            assert difference <= 1e-9
            saved.append(dict(time=t, direct_shift_difference=difference))
        cost = model_cost(EPS, BETA, 3996, t, d["direct_shift_hartree"]) if reliable else None
        result.append(dict(time=t, is_new_coordinate=not bool(matches), branch_reliable=reliable, **d,
                           direct_cost=cost, frozen_original_budget=p["A6"]["original_budget"],
                           frozen_budget_over_cost=p["A6"]["original_budget"] / cost if cost else None))
    assert len(saved) == 3 and sum(r["is_new_coordinate"] for r in result) == 6
    valid = [r for r in result if r["direct_cost"] is not None]
    minimum = min(valid, key=lambda r: r["direct_cost"]) if valid else None
    csv_write(OUT / "A6_local_grid.csv", result)
    return dict(local_minimum=minimum, repeated_anchor_reproduction=saved, new_coordinates=6, full_pf_builds=9,
                pf_schur_calls=9, unreliable_points=sum(not r["branch_reliable"] for r in result),
                relative_cost_change=minimum["direct_cost"] / p["A6"]["original_minimum_cost"] - 1 if minimum else None,
                original_budget_and_grid_minimum_unchanged=True, source_audit=source)


def b3(p):
    s = p["B3"]; frozen = read(OUT / "B3_SELECTION_FROZEN.json")
    assert frozen["protocol_sha256"] == sha(OUT / "protocol.json") and frozen["choices"] == s["choices"]
    sys.path.insert(0, str(ROOT / "review_response"))
    import run_h01_approximate_state_calibration as h01
    import run_full_electron_nh3_higher_term_diagnosis as diagnosis
    audit, scoring = [], []
    for condition in hf.CONDITIONS:
        cache = Path(s["cache_dir"]) / (condition + ".pkl")
        assert sha(cache) == s["source_cache_sha256"][condition]
        system = h01._load_system(cache)
        assert h01._sparse_hash(system["hamiltonian"]) == s["source_hamiltonian_sha256"][condition]
        exact, cisd = system["state"], system["states"]["cisd"]
        assert abs(np.linalg.norm(cisd) - 1) < 1e-10 and np.linalg.norm(system["hamiltonian"] @ exact - system["energy"] * exact) < 1e-8
        for model in [m for m in s["models"] if m["condition"] == condition]:
            fid = model["formula"]; key = condition + "__" + fid
            seq = s["formulae"][fid]["s2_sequence"]
            assert h01._rotation_count(system, seq) == model["rotations"]
            pick = next(c for c in s["choices"] if c["condition"] == condition and c["formula"] == fid)
            coarse_set = set(s["coarse_truth_times"][key]); prev_fine = prev_coarse = None
            scored = None
            for t in s["refined_truth_times"][key]:
                u, _ = diagnosis._build_cpu(system, seq, t)
                point, prev_fine = h01._branch_schur_point(u, exact, system["energy"], t, model["rotations"], prev_fine)
                assert np.linalg.norm(u.conj().T @ u - np.eye(len(exact))) < 1e-10
                assert point["eigenpair_residual_2_norm"] < 1e-10 and not point["branch_selection_disagrees_with_independent_rule"]
                assert point["adjacent_selected_vector_overlap_probability"] is None or point["adjacent_selected_vector_overlap_probability"] >= .9
                diff = None
                if t in coarse_set:
                    cp, prev_coarse = h01._branch_schur_point(u, exact, system["energy"], t, model["rotations"], prev_coarse)
                    diff = abs(cp["signed_direct_shift_hartree"] - point["signed_direct_shift_hartree"])
                    assert diff < 1e-9 and (cp["adjacent_selected_vector_overlap_probability"] is None or cp["adjacent_selected_vector_overlap_probability"] >= .9)
                audit.append(dict(condition=condition, formula=fid, time=t, is_coarse=t in coarse_set,
                                  is_selected=t == pick["selected_time"], direct_shift=point["signed_direct_shift_hartree"],
                                  ground_overlap=point["ground_overlap_probability"], previous_overlap=point["adjacent_selected_vector_overlap_probability"],
                                  eigenpair_residual=point["eigenpair_residual_2_norm"], coarse_refined_difference=diff))
                if t == pick["selected_time"]:
                    pf, _ = h01._apply_pf_cpu(system, seq, t, np.column_stack([cisd, exact]))
                    assert np.linalg.norm(pf - u @ np.column_stack([cisd, exact])) < 1e-10
                    ref = expm_multiply(1j * t * system["hamiltonian"], cisd)
                    g = float(np.vdot(ref, pf[:, 0]).imag / t)
                    g0 = float(np.vdot(np.exp(1j * system["energy"] * t) * exact, pf[:, 1]).imag / t)
                    delta = point["signed_direct_shift_hartree"]
                    direct_cost = hf.cost(t, abs(delta), model["rotations"], EPS)
                    qpe = BETA * model["rotations"] / (t * pick["budget"])
                    scored = dict(**pick, direct_shift=delta, exact_proxy=g0, cisd_proxy=g,
                                  fit_difference=pick["predicted_signed_shift"] - g, state_difference=g - g0, proxy_difference=g0 - delta,
                                  actual_required_cost=direct_cost, qpe_error=qpe, total_error=abs(delta) + qpe,
                                  precision_pass=abs(delta) + qpe <= EPS,
                                  budget_over_required_cost=pick["budget"] / direct_cost if direct_cost else None)
            assert scored is not None
            scoring.append(scored)
            print(json.dumps(dict(event="B3", condition=condition, formula=fid, precision_pass=scored["precision_pass"])), flush=True)
    joint = [next(r for r in scoring if r["condition"] == q["condition"] and r["formula"] == q["formula"]) for q in s["joint_choices"]]
    csv_write(OUT / "B3_branch_audit.csv", audit); csv_write(OUT / "B3_scoring.csv", scoring); csv_write(OUT / "B3_joint_scoring.csv", joint)
    return dict(individual_selections=scoring, joint_selections=joint, branch_points=len(audit),
                full_pf_builds=len(audit), pf_schur_calls=len(audit) + sum(r["is_coarse"] for r in audit),
                model_refits=0, gates_and_budget_margin_unchanged=True)


def execute(stage):
    p = verify(stage); start = time.perf_counter()
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024 ** 3, 4 * 1024 ** 3))
    def deadline(signum, frame):
        raise TimeoutError("frozen per-stage wall-time cap reached")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(p["resource_caps"]["wall_seconds_per_stage"])
    try:
        result = globals()[stage](p)
        result.update(stage=stage, protocol_sha256=sha(OUT / "protocol.json"),
                      execution_commit=git("rev-parse", "HEAD"), elapsed_seconds=time.perf_counter() - start,
                      peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                                       BLAS_threads={k: os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")}))
        write(OUT / (stage + "_COMPLETE.json"), result)
        print(json.dumps(dict(event="COMPLETE", stage=stage, seconds=result["elapsed_seconds"])), flush=True)
    except Exception as exc:
        write(OUT / (stage + "_FAILED.json"), dict(stage=stage, exception_type=type(exc).__name__, exception=str(exc),
                                                 elapsed_seconds=time.perf_counter() - start, protocol_sha256=sha(OUT / "protocol.json")))
        raise
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("stage", choices=("freeze", *STAGES))
    args = parser.parse_args()
    freeze() if args.stage == "freeze" else execute(args.stage)
