"""Truth-free Phase-A predictor for the HF domain-intervention pilot."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import pickle
import resource
import time
from typing import Any

import numpy as np

import hf_domain_intervention_pilot as core
import pf_spectral_recoverability_d2 as d2
import run_pf_spectral_recoverability_d2_a_predictor as d2runner
import run_practical_calibration_minimal as practical


P0_PROTOCOL_SHA256 = "a2f1b286eb0a94f63bd23702c7c1b26a46480d1c3731932e74dd22c074b60a1c"
D2_PROTOCOL_SHA256 = "fb1d112e13830924ee5bed058cea8a8a6196d01b303b96fff664676db98d83f5"
D2_CORE_SHA256 = "04eafd4051430be55c1494a6fbadf1800b2dc7c54ab1c3071a7a3e0a7616d033"
CONDITIONS = ("HF_full_eq_sto3g", "HF_full_stretch150_sto3g")


def validate_environment(processes: int) -> dict[str, Any]:
    if processes != 1:
        raise core.HFPilotError("predictor requires one process")
    threads = {}
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        threads[name] = os.environ.get(name)
        if threads[name] != "1":
            raise core.HFPilotError(f"{name} must equal 1")
    return {"processes": 1, "threads": threads, "gpu_operations": 0}


def load_fixed_inputs(
    *, project_root: Path, p0_protocol: Path, authorization_path: Path,
    sanitized_root: Path, candidate_plan: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    if core.sha256_file(p0_protocol) != P0_PROTOCOL_SHA256:
        raise core.HFPilotError("P0 protocol identity mismatch")
    if core.sha256_file(project_root / "review_response/pf_spectral_recoverability_d2_protocol_draft.json") != D2_PROTOCOL_SHA256:
        raise core.HFPilotError("D2 protocol identity mismatch")
    if core.sha256_file(project_root / "review_response/pf_spectral_recoverability_d2.py") != D2_CORE_SHA256:
        raise core.HFPilotError("D2 core identity mismatch")
    authorization = core.load_json(authorization_path)
    if authorization["parent_protocol"]["sha256"] != P0_PROTOCOL_SHA256:
        raise core.HFPilotError("authorization does not bind the P0 protocol")
    p0 = core.load_json(p0_protocol)
    manifest = core.load_json(sanitized_root / "sanitized_input_manifest.json")
    if manifest.get("authorization_sha256") != core.sha256_file(authorization_path):
        raise core.HFPilotError("sanitized input authorization mismatch")
    with candidate_plan.open(newline="", encoding="utf-8") as stream:
        candidates = list(csv.DictReader(stream))
    if len(candidates) != 6 or {row["condition"] for row in candidates} != set(CONDITIONS):
        raise core.HFPilotError("candidate plan must contain the fixed six HF coordinates")
    return p0, authorization, candidates, manifest


def load_views(sanitized_root: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, d2runner.PredictorSystemView]]:
    systems: dict[str, Any] = {}
    views: dict[str, d2runner.PredictorSystemView] = {}
    entries = {row["condition"]: row for row in manifest["entries"]}
    for condition in CONDITIONS:
        row = entries[condition]
        path = sanitized_root / row["sanitized_relative_path"]
        if core.sha256_file(path) != row["sanitized_sha256"]:
            raise core.HFPilotError(f"sanitized cache hash mismatch: {condition}")
        with path.open("rb") as stream:
            system = pickle.load(stream)
        expected_fields = {
            "schema", "condition", "source_pickle_sha256", "protocol_sha256",
            "hamiltonian_sha256", "hamiltonian", "component_spectra",
            "term_counts", "cisd_state",
        }
        if set(system) != expected_fields or system["schema"] != "hf_domain_intervention_sanitized_system_v1":
            raise core.HFPilotError(f"sanitized allowlist mismatch: {condition}")
        state = np.asarray(system["cisd_state"], dtype=np.complex128).reshape(-1)
        view = d2runner.PredictorSystemView(
            condition=condition,
            protocol_sha256=str(system["protocol_sha256"]),
            hamiltonian_sha256=str(system["hamiltonian_sha256"]),
            hamiltonian=system["hamiltonian"],
            component_spectra=tuple(system["component_spectra"]),
            term_counts=tuple(int(value) for value in system["term_counts"]),
            cisd_state=state / np.linalg.norm(state),
            dimension=int(state.size),
        )
        systems[condition] = system
        views[condition] = view
    return systems, views


def manifest_for(output: Path, names: list[str]) -> dict[str, Any]:
    return {
        "schema": "hf_domain_intervention_prediction_manifest_v1",
        "manifest_self_excluded": True,
        "files": [
            {
                "path": name,
                "bytes": (output / name).stat().st_size,
                "sha256": core.sha256_file(output / name),
            }
            for name in names
        ],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    root = args.project_root.resolve()
    environment = validate_environment(args.processes)
    p0, authorization, candidates, sanitized_manifest = load_fixed_inputs(
        project_root=root,
        p0_protocol=args.p0_protocol.resolve(),
        authorization_path=args.authorization.resolve(),
        sanitized_root=args.sanitized_root.resolve(),
        candidate_plan=args.candidate_plan.resolve(),
    )
    output = args.output_dir.resolve()
    if output.exists():
        raise core.HFPilotError("prediction output must be new")
    output.mkdir(parents=True)
    systems, views = load_views(args.sanitized_root.resolve(), sanitized_manifest)
    source_contract = core.load_json(args.source_contract.resolve())
    sequence = [float(value) for value in source_contract["current_m3_sequence"]]
    d2_protocol = core.load_json(root / "review_response/pf_spectral_recoverability_d2_protocol_draft.json")
    numerical_rules = d2_protocol["numerical_rules"]
    constants = p0["fixed_constants"]
    epsilon = float(constants["epsilon_E_hartree"])
    beta = float(constants["beta"])
    rotations = int(constants["K_current_m3_per_step"])
    eta = float(authorization["resolved_execution_blockers"]["eta"]["value"])
    gammas = [float(value) for value in authorization["phase_a"]["gamma_arms"]]
    baselines = {
        row["condition"]: row for row in p0["baseline_contract"]["conditions"]
    }
    by_condition_candidates: dict[str, list[dict[str, Any]]] = {key: [] for key in CONDITIONS}
    m1_rows: list[dict[str, Any]] = []
    b1_rows: list[dict[str, Any]] = []
    resource_rows: list[dict[str, Any]] = []
    previous_vectors: dict[str, np.ndarray] = {}
    spectral_wall = 0.0
    local_wall = 0.0
    for raw in candidates:
        condition = raw["condition"]
        candidate_id = raw["candidate_id"]
        time_value = float(raw["time_hartree_inverse"])
        factor = float(raw["factor_of_T0"])
        allowance = core.target_allowance(
            epsilon_hartree=epsilon, beta=beta, rotations=rotations,
            time_value=time_value,
            baseline_budget=float(baselines[condition]["B0_continuous"]),
            eta=eta,
        )
        view = views[condition]
        counter = d2runner.ActionCounter()
        actions = d2runner.CoordinateActions(view, sequence, time_value, counter)
        spectral_started = time.perf_counter()
        prediction, selected_vector = d2.analyze_coordinate(
            start=view.cisd_state,
            apply_u=actions.apply_pf,
            apply_h=actions.apply_h,
            time_value=time_value,
            prefix_dimensions=[1, 2, 4, 8],
            primary_dimension=8,
            previous_vector=previous_vectors.get(condition),
            numerical_rules=numerical_rules,
            epsilon_hartree=epsilon,
            beta=beta,
            rotations_per_step=rotations,
        )
        spectral_elapsed = time.perf_counter() - spectral_started
        spectral_wall += spectral_elapsed
        if selected_vector is not None:
            previous_vectors[condition] = selected_vector.copy()
        m1 = core.m1_arm_row(
            candidate_id=candidate_id, time_value=time_value,
            factor_of_t0=factor, prediction=prediction,
            allowance_hartree=allowance, beta=beta, rotations=rotations,
            epsilon_hartree=epsilon,
        )
        m1.update({
            "condition": condition,
            "time_hex": raw["time_hex"],
            "prediction_detail": prediction,
            "resource_counts": counter.payload(),
        })
        m1_rows.append(m1)
        local_started = time.perf_counter()
        proxy = practical.proxy_point(systems[condition], sequence, time_value)
        local_elapsed = time.perf_counter() - local_started
        local_wall += local_elapsed
        local_rows = core.b1_arm_rows(
            candidate_id=candidate_id, time_value=time_value,
            factor_of_t0=factor,
            signed_proxy_hartree=float(proxy["echo_imag_hartree"]),
            allowance_hartree=allowance, gammas=gammas,
            beta=beta, rotations=rotations, epsilon_hartree=epsilon,
        )
        for row in local_rows:
            row.update({"condition": condition, "time_hex": raw["time_hex"]})
        b1_rows.extend(local_rows)
        by_condition_candidates[condition].append({
            "candidate_id": candidate_id,
            "time_hartree_inverse": time_value,
            "factor_of_T0": factor,
            "allowance_hartree": allowance,
            "M1": m1,
            "B1": local_rows,
            "local_proxy_diagnostic": proxy,
        })
        resource_rows.append({
            "condition": condition,
            "candidate_id": candidate_id,
            "spectral_wall_seconds": spectral_elapsed,
            "local_proxy_wall_seconds": local_elapsed,
            "M1": counter.payload(),
            "B1_pf_actions": 1,
            "B1_hamiltonian_exponential_actions": 1,
            "B1_internal_H_matvecs": "not_exposed_by_scipy_expm_multiply",
        })
    if sum(int(row["M1"]["pf_per_vector_actions"]) for row in resource_rows) > 48:
        raise core.HFPilotError("spectral PF action limit exceeded")
    if sum(int(row["M1"]["hamiltonian_matvecs"]) for row in resource_rows) > 48:
        raise core.HFPilotError("spectral H action limit exceeded")
    limits = authorization["resolved_execution_blockers"]["resource_envelope"]
    if spectral_wall > float(limits["spectral_arm_wall_seconds_maximum"]):
        raise core.HFPilotError("spectral arm wall limit exceeded")
    if local_wall > float(limits["local_proxy_arm_wall_seconds_maximum"]):
        raise core.HFPilotError("local-proxy arm wall limit exceeded")
    selections: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        baseline = baselines[condition]
        fallback_id = next(
            row["candidate_id"] for row in by_condition_candidates[condition]
            if float(row["factor_of_T0"]) == 1.0
        )
        selections.append({
            "condition": condition,
            "M1": core.select_condition(
                [row for row in m1_rows if row["condition"] == condition],
                arm="M1_fixed_D2A_spectral", gamma=None,
                fallback_candidate_id=fallback_id,
                fallback_time=float(baseline["T0_hartree_inverse"]),
                fallback_budget=float(baseline["B0_continuous"]),
            ),
            "B1": [
                core.select_condition(
                    [row for row in b1_rows if row["condition"] == condition],
                    arm="B1_local_CISD_proxy", gamma=gamma,
                    fallback_candidate_id=fallback_id,
                    fallback_time=float(baseline["T0_hartree_inverse"]),
                    fallback_budget=float(baseline["B0_continuous"]),
                )
                for gamma in gammas
            ],
        })
    payload = {
        "schema": "hf_domain_intervention_prediction_v1",
        "status": "hf_domain_prediction_frozen_truth_not_opened",
        "p0_protocol_sha256": P0_PROTOCOL_SHA256,
        "authorization_sha256": core.sha256_file(args.authorization.resolve()),
        "budget_model": "continuous_rotation_cost_proxy",
        "discrete_budget_model": "not_defined_in_inherited_study",
        "eta": eta,
        "truth_open_count": 0,
        "direct_truth_count": 0,
        "full_hamiltonian_eigendecomposition_count": 0,
        "full_pf_construction_count": 0,
        "full_pf_eigendecomposition_count": 0,
        "gpu_operation_count": 0,
        "conditions": [
            {
                "condition": condition,
                "candidates": by_condition_candidates[condition],
                "selection": next(row for row in selections if row["condition"] == condition),
            }
            for condition in CONDITIONS
        ],
    }
    core.write_json(output / "prediction.json", payload)
    digest = core.sha256_file(output / "prediction.json")
    (output / "prediction.sha256").write_text(f"{digest}  prediction.json\n", encoding="utf-8")
    core.write_json(output / "PREDICTION_FROZEN.json", {
        "schema": "hf_domain_intervention_prediction_frozen_v1",
        "prediction_sha256": digest,
        "truth_open_count_before_freeze": 0,
        "phase_b_allowed_only_after_prediction_commit": True,
    })
    core.write_json(output / "source_audit.json", {
        "p0_protocol_sha256": P0_PROTOCOL_SHA256,
        "authorization_sha256": core.sha256_file(args.authorization.resolve()),
        "D2_protocol_sha256": D2_PROTOCOL_SHA256,
        "D2_core_sha256": D2_CORE_SHA256,
        "sanitized_manifest_sha256": core.sha256_file(args.sanitized_root.resolve() / "sanitized_input_manifest.json"),
        "source_pickle_sha256": {
            row["condition"]: row["source_pickle_sha256"]
            for row in sanitized_manifest["entries"]
        },
    })
    core.write_json(output / "access_audit.json", {
        "truth_paths_exposed": False,
        "truth_open_count": 0,
        "allowed_sanitized_fields_only": True,
        "direct_truth_import_count": 0,
        "full_eigensolver_count": 0,
    })
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if peak * 1024 > int(limits["peak_memory_bytes_maximum"]):
        raise core.HFPilotError("peak CPU memory limit exceeded")
    core.write_json(output / "resource_audit.json", {
        "environment": environment,
        "separate_arm_accounting": True,
        "spectral_arm_wall_seconds": spectral_wall,
        "local_proxy_arm_wall_seconds": local_wall,
        "total_driver_wall_seconds": time.perf_counter() - started,
        "peak_cpu_rss_kib": peak,
        "coordinates": resource_rows,
    })
    names = [
        "prediction.json", "prediction.sha256", "PREDICTION_FROZEN.json",
        "source_audit.json", "access_audit.json", "resource_audit.json",
    ]
    core.write_json(output / "manifest.json", manifest_for(output, names))
    print(json.dumps({
        "status": payload["status"], "prediction_sha256": digest,
        "coordinate_count": 6, "truth_open_count": 0,
        "output": str(output),
    }, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--p0-protocol", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--source-contract", required=True, type=Path)
    parser.add_argument("--candidate-plan", required=True, type=Path)
    parser.add_argument("--sanitized-root", required=True, type=Path)
    parser.add_argument("--processes", required=True, type=int)
    parser.add_argument("--output-dir", required=True, type=Path)
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
