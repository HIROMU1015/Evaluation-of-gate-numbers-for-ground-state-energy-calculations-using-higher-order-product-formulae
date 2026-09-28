#!/usr/bin/env python3
"""Run D2R R1 on the ten frozen, already-scored selected coordinates.

The runner rebuilds the same four Phase A systems, evaluates CISD/exact-state
echo proxies, and reads direct shifts from the closed Phase B artifact.  It
never constructs a full PF unitary or computes a new PF eigenpair.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import pickle
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

import pf_candidate_validation as validation
import run_second_study_safe_time_domain_phase_a as phase_a
import run_second_study_safe_time_domain_phase_b as phase_b
import second_study_safe_time_domain_execution as execution


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(str(array.shape).encode("ascii"))
    digest.update(array.view(np.uint8))
    return digest.hexdigest()


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
    temporary.replace(path)


def atomic_pickle(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        pickle.dump(value, stream, protocol=pickle.HIGHEST_PROTOCOL)
    temporary.replace(path)


def load_r1_protocol(path: Path) -> tuple[dict[str, Any], str]:
    protocol = validation.read_json(path)
    if protocol.get("schema") != "pf_candidate_validation_r1_protocol_v1":
        raise validation.CandidateValidationError("unexpected R1 protocol schema")
    if protocol.get("status") != "frozen_before_r1_execution":
        raise validation.CandidateValidationError("R1 protocol is not frozen")
    if not protocol["authorization"]["r1_authorized"]:
        raise validation.CandidateValidationError("R1 is not authorized")
    if protocol["authorization"]["r2_authorized"]:
        raise validation.CandidateValidationError("R2 must remain unauthorized")
    return protocol, validation.sha256_file(path)


def environment_identity() -> dict[str, Any]:
    packages = {}
    for name in (
        "numpy",
        "scipy",
        "pyscf",
        "openfermion",
        "openfermionpyscf",
        "qiskit",
    ):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "packages": packages,
        "pythonpath": os.environ.get("PYTHONPATH"),
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
    }


def validate_protocol_and_plan(
    project_root: Path,
    r1_protocol: Mapping[str, Any],
    r0: Mapping[str, Any],
) -> None:
    if r1_protocol["source_commit"] != validation.SOURCE_COMMIT:
        raise validation.CandidateValidationError("R1 source commit changed")
    if r1_protocol["source_protocol_sha256"] != r0["protocol_sha256"]:
        raise validation.CandidateValidationError("R1 source protocol hash changed")
    if (
        r1_protocol["r0"]["ledger_canonical_sha256"]
        != validation.canonical_json_sha256(r0["ledger"])
    ):
        raise validation.CandidateValidationError("R0 ledger identity changed")
    if (
        r1_protocol["r0"]["coordinate_plan_canonical_sha256"]
        != validation.canonical_json_sha256(r0["coordinate_plan"])
    ):
        raise validation.CandidateValidationError("R0 coordinate plan identity changed")
    expected = [
        (str(row["condition"]), str(row["time_hex"]))
        for row in r1_protocol["coordinates"]
    ]
    actual = [
        (str(row["condition"]), float(row["time_hartree_inverse"]).hex())
        for row in r0["coordinate_plan"]
    ]
    if actual != expected:
        raise validation.CandidateValidationError("R1 coordinate list changed")
    for relative in validation.SOURCE_PATHS:
        frozen = validation.git_blob(project_root, validation.SOURCE_COMMIT, relative)
        if validation.sha256_bytes(frozen) != validation.sha256_file(project_root / relative):
            raise validation.CandidateValidationError(
                f"frozen source changed before R1: {relative}"
            )


def prepare_output(
    output_dir: Path, run_identity: Mapping[str, Any]
) -> tuple[Path, dict[str, int]]:
    runtime = output_dir / ".runtime"
    identity_path = runtime / "run_identity.json"
    counts = {"system_cache_reused": 0, "proxy_cache_reused": 0}
    if not output_dir.exists():
        runtime.mkdir(parents=True)
        atomic_json(identity_path, run_identity)
        return runtime, counts
    if (output_dir / "R1_COMPLETE.json").exists():
        raise validation.CandidateValidationError("R1 output is already complete")
    if not identity_path.is_file():
        raise validation.CandidateValidationError("existing output has no run identity")
    if validation.read_json(identity_path) != dict(run_identity):
        raise validation.CandidateValidationError("existing output run identity mismatch")
    unexpected = [
        path
        for path in output_dir.rglob("*")
        if path.is_file()
        and path != identity_path
        and ".runtime" not in path.parts
    ]
    if unexpected:
        raise validation.CandidateValidationError(
            f"incomplete output contains non-runtime files: {unexpected}"
        )
    return runtime, counts


def load_or_build_system(
    *,
    runtime: Path,
    condition: str,
    spec: Mapping[str, Any],
    source_protocol_sha256: str,
    expected_hamiltonian_sha256: str,
    counters: dict[str, int],
) -> tuple[dict[str, Any], dict[str, Any]]:
    cache = runtime / "system_cache" / f"{condition}.pkl"
    if cache.is_file():
        with cache.open("rb") as stream:
            payload = pickle.load(stream)
        system = payload["system"]
        metadata = payload["metadata"]
        if (
            system.get("schema") != "second_study_safe_time_domain_phase_a_system_v1"
            or system.get("condition") != condition
            or system.get("protocol_sha256") != source_protocol_sha256
            or system.get("hamiltonian_sha256") != expected_hamiltonian_sha256
        ):
            raise validation.CandidateValidationError(
                f"invalid R1 system cache: {cache}"
            )
        counters["system_cache_reused"] += 1
        return system, metadata
    cache.parent.mkdir(parents=True, exist_ok=True)
    work_dir = runtime / "pyscf" / condition
    if work_dir.exists():
        for attempt in range(1, 100):
            candidate = runtime / "pyscf" / f"{condition}_attempt{attempt}"
            if not candidate.exists():
                work_dir = candidate
                break
        else:
            raise validation.CandidateValidationError(
                f"{condition}: too many incomplete PySCF attempts"
            )
    system, metadata = phase_a.prepare_condition(
        spec, source_protocol_sha256, work_dir, 1
    )
    if system["hamiltonian_sha256"] != expected_hamiltonian_sha256:
        raise validation.CandidateValidationError(
            f"{condition}: rebuilt Hamiltonian identity mismatch"
        )
    atomic_pickle(cache, {"system": system, "metadata": metadata})
    return system, metadata


def load_or_build_exact(
    *, runtime: Path, condition: str, system: Mapping[str, Any]
) -> tuple[float, np.ndarray, float, bool]:
    cache = runtime / "exact_state_cache" / f"{condition}.pkl"
    if cache.is_file():
        with cache.open("rb") as stream:
            payload = pickle.load(stream)
        state = np.asarray(payload["state"], dtype=np.complex128)
        energy = float(payload["energy"])
        residual = float(
            np.linalg.norm(system["hamiltonian"] @ state - energy * state)
        )
        if (
            payload.get("hamiltonian_sha256") != system["hamiltonian_sha256"]
            or payload.get("state_sha256") != array_sha256(state)
            or residual > 1e-10
        ):
            raise validation.CandidateValidationError(
                f"invalid R1 exact-state cache: {cache}"
            )
        return energy, state, residual, True
    cache.parent.mkdir(parents=True, exist_ok=True)
    energy, state, residual = phase_b.exact_ground_pair(system)
    atomic_pickle(
        cache,
        {
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "energy": energy,
            "state": state,
            "state_sha256": array_sha256(state),
            "residual": residual,
        },
    )
    return energy, state, residual, False


def proxy_cache_path(
    runtime: Path, condition: str, time_value: float, state_kind: str
) -> Path:
    digest = hashlib.sha256(
        f"{time_value.hex()}:{state_kind}".encode("ascii")
    ).hexdigest()
    return runtime / "proxy_cache" / condition / f"{digest}.json"


def computed_proxy(
    *,
    runtime: Path,
    condition: str,
    time_value: float,
    state_kind: str,
    state: np.ndarray,
    system: Mapping[str, Any],
    sequence: Sequence[float],
    r1_protocol_sha256: str,
    counters: dict[str, int],
) -> tuple[dict[str, Any], bool]:
    path = proxy_cache_path(runtime, condition, time_value, state_kind)
    identity = {
        "condition": condition,
        "time_hex": time_value.hex(),
        "state_kind": state_kind,
        "state_sha256": array_sha256(state),
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "r1_protocol_sha256": r1_protocol_sha256,
    }
    if path.is_file():
        payload = validation.read_json(path)
        if payload.get("identity") != identity:
            raise validation.CandidateValidationError(f"stale R1 proxy cache: {path}")
        counters["proxy_cache_reused"] += 1
        return dict(payload["point"]), True
    path.parent.mkdir(parents=True, exist_ok=True)
    local_system = dict(system)
    local_system["cisd_state"] = np.asarray(state, dtype=np.complex128)
    point = phase_a.proxy_point(local_system, sequence, time_value)
    atomic_json(path, {"identity": identity, "point": point})
    return point, False


def saved_proxy_map(project_root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    rows = validation.read_csv(
        project_root / validation.PHASE_A_RELATIVE / "proxy_points.csv"
    )
    result = {}
    for row in rows:
        key = (str(row["condition"]), float(row["time_hartree_inverse"]).hex())
        if key in result:
            raise validation.CandidateValidationError(f"duplicate saved proxy: {key}")
        result[key] = {
            "time_hartree_inverse": float(row["time_hartree_inverse"]),
            "proxy_hartree": float(row["proxy_hartree"]),
            "echo_real": float(row["echo_real"]),
            "echo_imaginary": float(row["echo_imaginary"]),
            "state_error_2_norm": float(row["state_error_2_norm"]),
            "cancellation_index": float(row["cancellation_index"]),
            "pf_state_norm": float(row["pf_state_norm"]),
            "backward_hamiltonian_state_norm": float(
                row["backward_hamiltonian_state_norm"]
            ),
            "pf_action_seconds": float(row["pf_action_seconds"]),
            "hamiltonian_exponential_action_seconds": float(
                row["hamiltonian_exponential_action_seconds"]
            ),
            "proxy_point_seconds": float(row["proxy_point_seconds"]),
            "saved_point_role": row["point_role"],
        }
    return result


def local_budget_diagnostic(
    *, epsilon: float, gamma: float, direct_error: float, proxy_signed: float
) -> dict[str, Any]:
    estimate = abs(proxy_signed)
    if estimate >= epsilon:
        return {
            "estimate_hartree": estimate,
            "feasible": False,
            "allowed_underestimation_hartree": None,
            "actual_underestimation_hartree": direct_error - estimate,
            "energy_margin_hartree": None,
            "would_meet_target_under_inherited_budget_identity": False,
        }
    allowed = (1.0 - 1.0 / gamma) * (epsilon - estimate)
    actual = direct_error - estimate
    margin = allowed - actual
    return {
        "estimate_hartree": estimate,
        "feasible": True,
        "allowed_underestimation_hartree": allowed,
        "actual_underestimation_hartree": actual,
        "energy_margin_hartree": margin,
        "would_meet_target_under_inherited_budget_identity": bool(margin >= 0.0),
    }


def build_report(
    *,
    rows: Sequence[Mapping[str, Any]],
    coordinate_rows: Sequence[Mapping[str, Any]],
    counts: Mapping[str, Any],
) -> str:
    lines = [
        "# D2R R1 selected-coordinate cause decomposition",
        "",
        "The closed second-study decision remains `complete_no_benefit`. All exact-state "
        "and direct-shift use below is post-hoc development diagnosis.",
        "",
        "## Fixed calculation counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Strategy-level decomposition",
            "",
            "| Condition | Strategy | Safe | Attribution | model/a | state/a | proxy/a | CISD-local safe | exact-local safe |",
            "|---|---|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        ratios = row["component_over_original_budget_allowance"]
        lines.append(
            "| {condition} | {strategy} | {safe} | {attribution} | "
            "{model:.3f} | {state:.3f} | {proxy:.3f} | {cisd} | {exact} |".format(
                condition=row["condition"],
                strategy=row["strategy"],
                safe=not row["unsafe_execution"],
                attribution=row["component_attribution"],
                model=ratios["model_component"],
                state=ratios["state_component"],
                proxy=ratios["proxy_eigenvalue_component"],
                cisd=row["local_cisd_budget"][
                    "would_meet_target_under_inherited_budget_identity"
                ],
                exact=row["local_exact_budget"][
                    "would_meet_target_under_inherited_budget_identity"
                ],
            )
        )
    lines.extend(
        [
            "",
            "## Coordinate-level state controls",
            "",
            "| Condition | t | CISD source | CISD residual | exact overlap | exact residual |",
            "|---|---:|---|---:|---:|---:|",
        ]
    )
    for row in coordinate_rows:
        lines.append(
            f"| {row['condition']} | {row['time_hartree_inverse']:.12g} | "
            f"{row['cisd_proxy_source']} | {row['cisd_hamiltonian_residual_2_norm']:.3e} | "
            f"{row['cisd_exact_ground_overlap_probability']:.12g} | "
            f"{row['exact_ground_residual_2_norm']:.3e} |"
        )
    lines.extend(
        [
            "",
            "R2 is not authorized. Stop here for research-direction review.",
        ]
    )
    return "\n".join(lines) + "\n"


def manifest(output_dir: Path, names: Sequence[str]) -> dict[str, Any]:
    entries = []
    for name in names:
        path = output_dir / name
        entries.append(
            {
                "path": name,
                "sha256": validation.sha256_file(path),
                "byte_count": path.stat().st_size,
            }
        )
    return {
        "schema": "pf_candidate_validation_r1_manifest_v1",
        "entry_count": len(entries),
        "entries": entries,
        "runtime_excluded": True,
    }


def run(
    *, project_root: Path, protocol_path: Path, output_dir: Path
) -> dict[str, Any]:
    started = time.perf_counter()
    project_root = project_root.resolve()
    protocol_path = protocol_path.resolve()
    output_dir = output_dir.resolve()
    r1_protocol, r1_protocol_sha256 = load_r1_protocol(protocol_path)
    r0 = validation.build_failure_ledger(project_root)
    validate_protocol_and_plan(project_root, r1_protocol, r0)
    source_manifest = validation.source_manifest(project_root)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, check=True,
        text=True, stdout=subprocess.PIPE
    ).stdout.strip()
    run_identity = {
        "schema": "pf_candidate_validation_r1_run_identity_v1",
        "source_commit": validation.SOURCE_COMMIT,
        "execution_head": head,
        "source_protocol_sha256": r0["protocol_sha256"],
        "r1_protocol_sha256": r1_protocol_sha256,
        "coordinate_plan_sha256": validation.canonical_json_sha256(
            r0["coordinate_plan"]
        ),
        "backend": "cpu_state_action_only",
        "processes": 1,
    }
    runtime, resume_counts = prepare_output(output_dir, run_identity)
    predictions = r0["predictions"]
    prediction_by_condition = {
        row["condition"]: row for row in predictions["conditions"]
    }
    source_protocol = r0["protocol"]
    specs = execution.condition_specs(source_protocol)
    sequence = execution.formula_sequence(source_protocol)
    epsilon = float(source_protocol["scope"]["target_error_hartree"])
    gamma = float(source_protocol["cost_model"]["gamma"])
    saved = saved_proxy_map(project_root)
    counters = {
        **resume_counts,
        "system_regeneration_count": 0,
        "exact_ground_regeneration_count": 0,
        "saved_cisd_proxy_reuse_count": 0,
        "new_cisd_proxy_count": 0,
        "new_exact_proxy_count": 0,
        "computed_this_invocation": 0,
        "new_direct_truth_coordinate_count": 0,
        "full_pf_unitary_build_count": 0,
        "gpu_operation_count": 0,
    }
    systems: dict[str, dict[str, Any]] = {}
    metadata_by_condition: dict[str, dict[str, Any]] = {}
    exact_by_condition: dict[str, tuple[float, np.ndarray, float]] = {}
    for condition in execution.condition_names(source_protocol):
        before_reuse = counters["system_cache_reused"]
        system, metadata = load_or_build_system(
            runtime=runtime,
            condition=condition,
            spec=specs[condition],
            source_protocol_sha256=r0["protocol_sha256"],
            expected_hamiltonian_sha256=prediction_by_condition[condition][
                "hamiltonian_sha256"
            ],
            counters=counters,
        )
        if counters["system_cache_reused"] == before_reuse:
            counters["system_regeneration_count"] += 1
        energy, state, residual, reused = load_or_build_exact(
            runtime=runtime, condition=condition, system=system
        )
        if not reused:
            counters["exact_ground_regeneration_count"] += 1
        systems[condition] = system
        metadata_by_condition[condition] = metadata
        exact_by_condition[condition] = (energy, state, residual)

    coordinate_rows: list[dict[str, Any]] = []
    coordinate_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for planned in r0["coordinate_plan"]:
        condition = str(planned["condition"])
        time_value = float(planned["time_hartree_inverse"])
        key = (condition, time_value.hex())
        system = systems[condition]
        metadata = metadata_by_condition[condition]
        exact_energy, exact_state, exact_residual = exact_by_condition[condition]
        cisd_state = np.asarray(system["cisd_state"], dtype=np.complex128)
        if key in saved:
            cisd_point = dict(saved[key])
            cisd_source = "saved_phase_a_proxy"
            cisd_cache_reused = False
            counters["saved_cisd_proxy_reuse_count"] += 1
        else:
            cisd_point, cisd_cache_reused = computed_proxy(
                runtime=runtime,
                condition=condition,
                time_value=time_value,
                state_kind="cisd",
                state=cisd_state,
                system=system,
                sequence=sequence,
                r1_protocol_sha256=r1_protocol_sha256,
                counters=counters,
            )
            cisd_source = "new_r1_cisd_proxy"
            counters["new_cisd_proxy_count"] += 1
            if not cisd_cache_reused:
                counters["computed_this_invocation"] += 1
        exact_point, exact_cache_reused = computed_proxy(
            runtime=runtime,
            condition=condition,
            time_value=time_value,
            state_kind="exact_ground",
            state=exact_state,
            system=system,
            sequence=sequence,
            r1_protocol_sha256=r1_protocol_sha256,
            counters=counters,
        )
        counters["new_exact_proxy_count"] += 1
        if not exact_cache_reused:
            counters["computed_this_invocation"] += 1
        cisd_proxy = float(cisd_point["proxy_hartree"])
        exact_proxy = float(exact_point["proxy_hartree"])
        direct_shift = float(planned["direct_signed_shift_hartree"])
        cisd_residual = float(metadata["cisd_hamiltonian_residual_2_norm"])
        overlap = float(abs(np.vdot(exact_state, cisd_state)) ** 2)
        row = {
            "condition": condition,
            "time_hartree_inverse": time_value,
            "time_hex": time_value.hex(),
            "selected_relative_to_t_ana": float(
                planned["selected_relative_to_t_ana"]
            ),
            "strategies": list(planned["strategies"]),
            "cisd_proxy_source": cisd_source,
            "cisd_proxy_cache_reused_on_this_invocation": cisd_cache_reused,
            "cisd_proxy_signed_hartree": cisd_proxy,
            "cisd_echo_real": float(cisd_point["echo_real"]),
            "cisd_echo_imaginary": float(cisd_point["echo_imaginary"]),
            "exact_proxy_cache_reused_on_this_invocation": exact_cache_reused,
            "exact_proxy_signed_hartree": exact_proxy,
            "exact_echo_real": float(exact_point["echo_real"]),
            "exact_echo_imaginary": float(exact_point["echo_imaginary"]),
            "direct_shift_signed_hartree": direct_shift,
            "direct_error_hartree": abs(direct_shift),
            "cisd_hamiltonian_residual_2_norm": cisd_residual,
            "cisd_exact_ground_overlap_probability": overlap,
            "exact_ground_energy_without_constant_hartree": exact_energy,
            "exact_ground_residual_2_norm": exact_residual,
            "fixed_population_dimension": int(metadata["population_sector_dimension"]),
            "restricted_dimension": int(metadata["restricted_dimension"]),
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "cisd_state_sha256": array_sha256(cisd_state),
            "exact_state_sha256": array_sha256(exact_state),
            "cisd_proxy_point_seconds": float(cisd_point["proxy_point_seconds"]),
            "exact_proxy_point_seconds": float(exact_point["proxy_point_seconds"]),
        }
        coordinate_rows.append(row)
        coordinate_lookup[key] = row

    decomposition_rows: list[dict[str, Any]] = []
    for ledger in r0["ledger"]:
        condition = str(ledger["condition"])
        time_value = float(ledger["selected_time_hartree_inverse"])
        coordinate = coordinate_lookup[(condition, time_value.hex())]
        f_signed = float(ledger["signed_model_or_central_prediction_hartree"])
        cisd_proxy = float(coordinate["cisd_proxy_signed_hartree"])
        exact_proxy = float(coordinate["exact_proxy_signed_hartree"])
        direct_shift = float(coordinate["direct_shift_signed_hartree"])
        components = {
            "model_component": f_signed - cisd_proxy,
            "state_component": cisd_proxy - exact_proxy,
            "proxy_eigenvalue_component": exact_proxy - direct_shift,
        }
        signed_discrepancy = f_signed - direct_shift
        closure = sum(components.values()) - signed_discrepancy
        if abs(closure) > float(
            r1_protocol["decomposition"]["closure_absolute_tolerance_hartree"]
        ):
            raise validation.CandidateValidationError(
                f"decomposition closure failed: {condition}/{ledger['strategy']}"
            )
        attribution = validation.classify_components(
            components, float(ledger["allowed_underestimation_hartree"])
        )
        cisd_budget = local_budget_diagnostic(
            epsilon=epsilon,
            gamma=gamma,
            direct_error=float(ledger["direct_absolute_error_hartree"]),
            proxy_signed=cisd_proxy,
        )
        exact_budget = local_budget_diagnostic(
            epsilon=epsilon,
            gamma=gamma,
            direct_error=float(ledger["direct_absolute_error_hartree"]),
            proxy_signed=exact_proxy,
        )
        decomposition_rows.append(
            {
                "condition": condition,
                "strategy": str(ledger["strategy"]),
                "time_hartree_inverse": time_value,
                "time_hex": time_value.hex(),
                "unsafe_execution": bool(ledger["unsafe_execution"]),
                "f_signed_hartree": f_signed,
                "budget_error_used_hartree": float(
                    ledger["budget_error_used_hartree"]
                ),
                "guard_premium_over_central_hartree": float(
                    ledger["guard_premium_over_central_hartree"]
                ),
                "cisd_proxy_signed_hartree": cisd_proxy,
                "exact_proxy_signed_hartree": exact_proxy,
                "direct_shift_signed_hartree": direct_shift,
                **components,
                "signed_discrepancy_hartree": signed_discrepancy,
                "closure_residual_hartree": closure,
                "original_allowed_underestimation_hartree": float(
                    ledger["allowed_underestimation_hartree"]
                ),
                "original_actual_underestimation_hartree": float(
                    ledger["actual_underestimation_hartree"]
                ),
                "component_attribution": attribution["attribution"],
                "largest_absolute_component": attribution[
                    "largest_absolute_component"
                ],
                "largest_over_second_largest": attribution[
                    "largest_over_second_largest"
                ],
                "material_by_original_budget_allowance": attribution[
                    "material_by_original_budget_allowance"
                ],
                "component_over_original_budget_allowance": attribution[
                    "component_over_original_budget_allowance"
                ],
                "local_cisd_budget": cisd_budget,
                "local_exact_budget": exact_budget,
                "evidence_class": "post_hoc_development_cause_diagnostic",
            }
        )

    limits = r1_protocol["completion"]
    if len(coordinate_rows) != int(limits["required_coordinate_rows"]):
        raise validation.CandidateValidationError("R1 coordinate row count failed")
    if len(decomposition_rows) != int(limits["required_strategy_decomposition_rows"]):
        raise validation.CandidateValidationError("R1 strategy row count failed")
    required_counts = {
        "saved_cisd_proxy_reuse_count": "required_saved_proxy_reuse_count",
        "new_cisd_proxy_count": "required_new_cisd_proxy_count",
        "new_exact_proxy_count": "required_new_exact_proxy_count",
        "new_direct_truth_coordinate_count": "required_new_direct_truth_count",
        "gpu_operation_count": "required_gpu_count",
    }
    for actual_key, required_key in required_counts.items():
        if int(counters[actual_key]) != int(limits[required_key]):
            raise validation.CandidateValidationError(
                f"R1 count mismatch: {actual_key}={counters[actual_key]}"
            )
    maximum_closure = max(
        abs(float(row["closure_residual_hartree"])) for row in decomposition_rows
    )
    controls = {
        condition: {
            "fixed_population_dimension": int(metadata_by_condition[condition]["population_sector_dimension"]),
            "restricted_dimension": int(metadata_by_condition[condition]["restricted_dimension"]),
            "cisd_hamiltonian_residual_2_norm": float(metadata_by_condition[condition]["cisd_hamiltonian_residual_2_norm"]),
            "cisd_exact_ground_overlap_probability": float(
                abs(
                    np.vdot(
                        exact_by_condition[condition][1],
                        systems[condition]["cisd_state"],
                    )
                ) ** 2
            ),
            "exact_ground_residual_2_norm": float(exact_by_condition[condition][2]),
        }
        for condition in systems
    }
    environment = environment_identity()
    resource_audit = {
        "schema": "pf_candidate_validation_r1_resource_audit_v1",
        "created_at": now(),
        "wall_seconds": float(time.perf_counter() - started),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "counts": counters,
        "condition_controls": controls,
        "maximum_decomposition_closure_residual_hartree": maximum_closure,
        "environment": environment,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    validation.write_json(output_dir / "source_manifest.json", source_manifest)
    validation.write_json(output_dir / "environment_identity.json", environment)
    validation.write_csv(output_dir / "coordinate_proxy_results.csv", coordinate_rows)
    validation.write_csv(output_dir / "strategy_cause_decomposition.csv", decomposition_rows)
    validation.write_json(output_dir / "resource_audit.json", resource_audit)
    (output_dir / "report.md").write_text(
        build_report(
            rows=decomposition_rows,
            coordinate_rows=coordinate_rows,
            counts=counters,
        ),
        encoding="utf-8",
    )
    decision = {
        "schema": "pf_candidate_validation_r1_decision_v1",
        "created_at": now(),
        "status": limits["status"],
        "source_commit": validation.SOURCE_COMMIT,
        "execution_head": head,
        "source_protocol_sha256": r0["protocol_sha256"],
        "r1_protocol_sha256": r1_protocol_sha256,
        "closed_second_study_decision": "complete_no_benefit_unchanged",
        "coordinate_count": len(coordinate_rows),
        "strategy_decomposition_row_count": len(decomposition_rows),
        "counts": counters,
        "maximum_decomposition_closure_residual_hartree": maximum_closure,
        "new_direct_truth_coordinate_count": 0,
        "r2_authorized": False,
        "stop_for_research_direction_review": True,
    }
    validation.write_json(output_dir / "decision.json", decision)
    names = [
        "source_manifest.json",
        "environment_identity.json",
        "coordinate_proxy_results.csv",
        "strategy_cause_decomposition.csv",
        "resource_audit.json",
        "report.md",
        "decision.json",
    ]
    validation.write_json(output_dir / "manifest.json", manifest(output_dir, names))
    complete = {
        "schema": "pf_candidate_validation_r1_complete_v1",
        "created_at": now(),
        "status": limits["status"],
        "decision_sha256": validation.sha256_file(output_dir / "decision.json"),
        "manifest_sha256": validation.sha256_file(output_dir / "manifest.json"),
        "r2_authorized": False,
    }
    validation.write_json(output_dir / "R1_COMPLETE.json", complete)
    return complete


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--project-root", type=Path, required=True)
    value.add_argument("--protocol", type=Path, required=True)
    value.add_argument("--output-dir", type=Path, required=True)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = run(
        project_root=args.project_root,
        protocol_path=args.protocol,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
