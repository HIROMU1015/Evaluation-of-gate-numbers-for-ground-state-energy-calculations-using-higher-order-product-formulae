#!/usr/bin/env python3
"""Execute the one-run P-SPEC-6 D1 pilot on six existing HCl coordinates.

The runner verifies the original Phase A runtime before loading its two HCl
systems.  It never constructs a new Hamiltonian, changes the PF, queries a GPU,
or evaluates a new time coordinate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import resource
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.linalg import schur

from review_response import run_second_study_safe_time_domain_phase_b as phase_b
from review_response import second_study_safe_time_domain_execution as execution


D0_RESULT_COMMIT = "0d13decb8793c5e6fd83075b1559e05424f93c04"
EXPECTED_PYTHON = "/home/AbeHiromu/venvs/trotter-common/bin/python"
EXPECTED_HASHES = {
    "review_response/pf_spectral_information_pilot_protocol_draft.json":
        "44d69fa249a075a6dd863ddc518a5d93da7e6699d4f888037c8476e68e5cdb9e",
    "review_response/pf_spectral_information_pilot_authorization.json":
        "74c7644a7e1f1f427e3fd2f9fe9d183828a588697f2d195bc5f04cd8f6f58f9a",
    "artifacts/pf_r1_readonly_design_summary_20260928/manifest.json":
        "cb6bc10625c117ab025d2b94b54f6eccf4517cbd57e63c23417e712f958d8f87",
    "artifacts/pf_r1_readonly_design_summary_20260928/coordinate_budget_diagnostics.csv":
        "d492668367d96d3839f37bc2a3fec4da45a8752792416ab8720ec3126b8ba770",
    "review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json":
        "a95a9abf87f1d428c35d34ed13cbea8c2ff930e91a3e5eb3a2550fd5d1dd1051",
    "review_response/second_study_safe_time_domain_protocol.json":
        "a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b",
    "artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/direct_points.csv":
        "dc0df4d7587f6c3342ea5ee09b753dec588d7cc6b634cde2adf4a7aeb20bfc78",
    "artifacts/server_pf_candidate_validation_r1_20260928_fba3383/coordinate_proxy_results.csv":
        "b32ff4fe1e45b5012b4a0174465764b6829aaba5d67d1dfb79be4676951fa995",
}
PHASE_A_INVENTORY_SHA256 = (
    "5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91"
)
HCL_CONDITIONS = ("HCl_full_eq_sto3g", "HCl_full_stretch150_sto3g")
COMPLETE_STATUSES = {
    "d1_complete_prototype_candidate_stop",
    "d1_complete_information_cost_limit_stop",
    "d1_complete_close_spectral_route_stop",
}


class PilotError(RuntimeError):
    """Raised when a frozen D1 gate is violated."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(str(array.shape).encode("ascii"))
    digest.update(array.view(np.uint8))
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PilotError("non-finite value in public output")
        return value
    if isinstance(value, complex):
        return {"real": float(value.real), "imaginary": float(value.imag)}
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return str(value)


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def atomic_pickle(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        pickle.dump(payload, stream, protocol=pickle.HIGHEST_PROTOCOL)
    temporary.replace(path)


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise PilotError(f"refusing empty CSV: {path}")
    fields: list[str] = []
    for row in rows:
        for key in row:
            if str(key) not in fields:
                fields.append(str(key))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, sort_keys=True)
                if isinstance(value, (list, dict))
                else value
                for key, value in jsonable(dict(row)).items()
            })


def git_output(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def verify_manifest(root: Path, relative: Path) -> None:
    manifest = load_json(root / relative)
    artifact_root = root / relative.parent
    for row in manifest.get("files", []):
        path = artifact_root / str(row["path"])
        if (
            not path.is_file()
            or path.stat().st_size != int(row["bytes"])
            or sha256_file(path) != str(row["sha256"])
        ):
            raise PilotError(f"manifest mismatch: {path}")


def verify_source_identity(
    root: Path,
    protocol_path: Path,
    d0_authorization_path: Path,
    d1_authorization_path: Path,
    phase_a_amendment_path: Path,
) -> dict[str, Any]:
    head = git_output(root, "rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", D0_RESULT_COMMIT, head],
        cwd=root,
        check=False,
        capture_output=True,
    ).returncode != 0:
        raise PilotError("D0 result commit is not an ancestor of HEAD")
    actual_paths = {
        protocol_path.resolve(): EXPECTED_HASHES[
            "review_response/pf_spectral_information_pilot_protocol_draft.json"
        ],
        d0_authorization_path.resolve(): EXPECTED_HASHES[
            "review_response/pf_spectral_information_pilot_authorization.json"
        ],
        phase_a_amendment_path.resolve(): EXPECTED_HASHES[
            "review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json"
        ],
    }
    verified: list[dict[str, Any]] = []
    for relative, expected in EXPECTED_HASHES.items():
        path = root / relative
        actual = sha256_file(path)
        if actual != expected:
            raise PilotError(f"fixed source hash mismatch: {relative}")
        verified.append({"path": relative, "sha256": actual})
    for path, expected in actual_paths.items():
        if sha256_file(path) != expected:
            raise PilotError(f"caller supplied wrong fixed file: {path}")
    verify_manifest(
        root, Path("artifacts/pf_r1_readonly_design_summary_20260928/manifest.json")
    )
    d0_decision = load_json(
        root / "artifacts/pf_r1_readonly_design_summary_20260928/decision.json"
    )
    if (
        d0_decision.get("status") != "d0_complete_d1_not_authorized"
        or d0_decision.get("new_scientific_calculation_count") != 0
        or d0_decision.get("d2_authorized")
    ):
        raise PilotError("D0 decision boundary mismatch")
    protocol = load_json(protocol_path)
    if (
        protocol.get("status") != "d0_protocol_frozen_d1_not_authorized"
        or protocol["scope"].get("coordinate_count") != 6
        or protocol["authorization"].get("d2_authorized")
    ):
        raise PilotError("D0 protocol boundary mismatch")
    d0_authorization = load_json(d0_authorization_path)
    if (
        d0_authorization.get("spectral_pilot_authorized")
        or d0_authorization.get("d1_authorized")
        or d0_authorization.get("r2_authorized")
    ):
        raise PilotError("D0 authorization file changed")
    d1_authorization = load_json(d1_authorization_path)
    if (
        d1_authorization.get("schema")
        != "pf_spectral_information_pilot_d1_authorization_v1"
        or d1_authorization.get("status")
        != "d1_authorized_once_d2_not_authorized"
        or not d1_authorization["execution"].get("d1_spectral_pilot_authorized")
        or d1_authorization["execution"].get("maximum_completed_runs") != 1
        or not d1_authorization["not_authorized"].get("d2")
    ):
        raise PilotError("invalid D1 authorization")
    return {
        "head": head,
        "d1_authorization_sha256": sha256_file(d1_authorization_path),
        "verified_source_count": len(verified),
        "verified_sources": verified,
        "protocol": protocol,
        "d1_authorization": d1_authorization,
    }


def validate_process_environment(protocol: Mapping[str, Any], processes: int) -> dict[str, Any]:
    limits = protocol["calculation_limits"]
    if processes != 1 or int(limits["processes"]) != 1:
        raise PilotError("D1 requires exactly one process")
    if Path(sys.executable).resolve() != Path(EXPECTED_PYTHON).resolve():
        raise PilotError(f"unexpected Python executable: {sys.executable}")
    threads = {
        name: os.environ.get(name)
        for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
    }
    if any(value != "1" for value in threads.values()):
        raise PilotError(f"BLAS thread environment is not fixed to one: {threads}")
    if "cupy" in sys.modules:
        raise PilotError("CuPy was imported before the CPU-only D1 run")
    return {
        "python_executable": sys.executable,
        "python_realpath": str(Path(sys.executable).resolve()),
        "python_version": sys.version,
        "threads": threads,
        "backend": "cpu",
        "gpu_query_count": 0,
        "gpu_allocation_count": 0,
        "gpu_kernel_count": 0,
    }


def prepare_output(output: Path, run_identity: Mapping[str, Any]) -> tuple[Path, bool]:
    runtime = output / ".runtime"
    identity = runtime / "run_identity.json"
    if not output.exists():
        runtime.mkdir(parents=True)
        atomic_json(identity, run_identity)
        return runtime, False
    if (output / "D1_COMPLETE.json").exists():
        raise PilotError("D1 output is already complete")
    if not identity.is_file() or load_json(identity) != dict(run_identity):
        raise PilotError("existing D1 output has a different run identity")
    for path in output.rglob("*"):
        if path.is_symlink():
            raise PilotError(f"symlink forbidden in resume output: {path}")
        if not path.is_file() or path == identity:
            continue
        relative = path.relative_to(output)
        if ".tmp" in path.suffixes or (
            relative.parts[:2] not in {
                (".runtime", "exact_state"),
                (".runtime", "coordinate"),
            }
            or path.suffix != ".pkl"
        ):
            raise PilotError(f"unexpected resume file: {relative}")
    return runtime, True


def load_hcl_systems(
    phase_a_root: Path,
    amendment: Mapping[str, Any],
    source_protocol: Mapping[str, Any],
    source_protocol_sha256: str,
    expected_hamiltonians: Mapping[str, str],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    expected_root = Path(amendment["phase_a_runtime"]["absolute_artifact_root"])
    if phase_a_root.resolve() != expected_root:
        raise PilotError("Phase A root differs from the frozen amendment")
    inventory = phase_b.verify_phase_a_runtime_inventory(phase_a_root)
    if (
        inventory["inventory_sha256"] != PHASE_A_INVENTORY_SHA256
        or inventory["file_count"] != 56
        or inventory["total_bytes"] != 113469289
    ):
        raise PilotError("Phase A runtime identity mismatch")
    input_manifest = load_json(phase_a_root / "sanitized_input_manifest.json")
    entries = {str(row["condition"]): row for row in input_manifest["entries"]}
    expected_cache = amendment["phase_a_runtime"]["system_cache_sha256"]
    systems: dict[str, dict[str, Any]] = {}
    for condition in HCL_CONDITIONS:
        row = entries[condition]
        cache = phase_a_root / str(row["runtime_system_cache"])
        if (
            sha256_file(cache) != expected_cache[condition]
            or row["runtime_system_cache_sha256"] != expected_cache[condition]
        ):
            raise PilotError(f"{condition}: Phase A system-cache mismatch")
        with cache.open("rb") as stream:
            system = pickle.load(stream)
        if (
            system.get("schema") != "second_study_safe_time_domain_phase_a_system_v1"
            or system.get("protocol_sha256") != source_protocol_sha256
            or system.get("condition") != condition
            or system.get("hamiltonian_sha256") != expected_hamiltonians[condition]
        ):
            raise PilotError(f"{condition}: invalid original Phase A system")
        systems[condition] = system
    if source_protocol["scope"]["formulae"] != ["current_m3"]:
        raise PilotError("source PF identity changed")
    return systems, inventory


def load_or_compute_exact(
    runtime: Path,
    condition: str,
    system: Mapping[str, Any],
) -> tuple[float, np.ndarray, float, bool]:
    path = runtime / "exact_state" / f"{condition}.pkl"
    if path.is_file():
        with path.open("rb") as stream:
            payload = pickle.load(stream)
        state = np.asarray(payload["state"], dtype=np.complex128)
        energy = float(payload["energy"])
        residual = float(np.linalg.norm(system["hamiltonian"] @ state - energy * state))
        if (
            payload.get("hamiltonian_sha256") != system["hamiltonian_sha256"]
            or payload.get("state_sha256") != array_sha256(state)
            or residual > 1e-10
        ):
            raise PilotError(f"{condition}: stale exact-state cache")
        return energy, state, residual, True
    energy, state, residual = phase_b.exact_ground_pair(system)
    atomic_pickle(path, {
        "condition": condition,
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "energy": energy,
        "state": state,
        "state_sha256": array_sha256(state),
        "residual": residual,
    })
    return energy, state, residual, False


def circular_distance(left: float, right: float) -> float:
    return float(abs(np.angle(np.exp(1j * (float(left) - float(right))))))


def phase_clusters(phases: Sequence[float], tolerance: float) -> list[list[int]]:
    values = np.asarray(phases, dtype=float)
    parent = list(range(len(values)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left in range(len(values)):
        for right in range(left + 1, len(values)):
            if circular_distance(values[left], values[right]) <= tolerance:
                union(left, right)
    groups: dict[int, list[int]] = {}
    for index in range(len(values)):
        groups.setdefault(find(index), []).append(index)
    result = list(groups.values())
    result.sort(key=lambda group: (min(values[index] for index in group), min(group)))
    return result


def _near_reference(principal: float, reference: float, period: float) -> tuple[float, int]:
    integer = int(round((float(reference) - float(principal)) / float(period)))
    return float(principal + integer * period), integer


def analyze_coordinate(
    *,
    condition: str,
    time_value: float,
    time_hex: str,
    system: Mapping[str, Any],
    exact_energy: float,
    exact_state: np.ndarray,
    exact_ground_residual: float,
    sequence: Sequence[float],
    saved_direct: Mapping[str, str],
    saved_r1: Mapping[str, str],
    allowance: float,
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    unitary, build = phase_b._build_unitary(system, sequence, time_value, "cpu", 0)
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    eigenvalues = np.diag(triangular)
    weights = np.abs(vectors.conj().T @ exact_state) ** 2
    selected = int(np.argmax(weights))
    target_eigenvalue = complex(eigenvalues[selected])
    saved_shift = float(saved_direct["signed_direct_shift_hartree"])
    principal_shift = float(
        np.angle(np.exp(-1j * exact_energy * time_value) * target_eigenvalue)
        / time_value
    )
    shift, unwrap_integer = _near_reference(
        principal_shift, saved_shift, 2.0 * np.pi / time_value
    )
    raw_phases = np.angle(eigenvalues)
    relative_eigenvalues = np.exp(-1j * exact_energy * time_value) * eigenvalues
    relative_phases = np.angle(relative_eigenvalues)
    clusters = phase_clusters(
        raw_phases,
        float(protocol["definitions"]["phase_cluster_circular_distance_maximum_rad"]),
    )
    cluster_by_index = {
        member: cluster_index
        for cluster_index, members in enumerate(clusters)
        for member in members
    }
    target_cluster = cluster_by_index[selected]
    target_members = set(clusters[target_cluster])
    outside_gaps = [
        circular_distance(raw_phases[selected], raw_phases[index])
        for index in range(len(raw_phases))
        if index not in target_members
    ]
    phase_gap = min(outside_gaps) if outside_gaps else math.inf
    matrix_echo = complex(
        np.exp(-1j * exact_energy * time_value)
        * np.vdot(exact_state, unitary @ exact_state)
    )
    reconstructed_echo = complex(np.sum(weights * relative_eigenvalues))
    saved_echo = complex(
        float(saved_r1["exact_echo_real"]),
        float(saved_r1["exact_echo_imaginary"]),
    )
    exact_proxy = float(reconstructed_echo.imag / time_value)
    saved_exact_proxy = float(saved_r1["exact_proxy_signed_hartree"])
    target_sine = math.sin(time_value * shift)
    component_rows: list[dict[str, Any]] = []
    for index in range(len(eigenvalues)):
        component_rows.append({
            "condition": condition,
            "time_hartree_inverse": time_value,
            "time_hex": time_hex,
            "schur_index": index,
            "cluster_index": cluster_by_index[index],
            "target_cluster": cluster_by_index[index] == target_cluster,
            "selected_target_vector": index == selected,
            "weight": float(weights[index]),
            "raw_phase_radian": float(raw_phases[index]),
            "relative_phase_radian": float(relative_phases[index]),
            "relative_eigenvalue_real": float(relative_eigenvalues[index].real),
            "relative_eigenvalue_imaginary": float(relative_eigenvalues[index].imag),
        })
    component_rows.sort(
        key=lambda row: (
            int(row["cluster_index"]),
            float(row["relative_phase_radian"]),
            -float(row["weight"]),
            int(row["schur_index"]),
        )
    )
    cluster_rows: list[dict[str, Any]] = []
    for cluster_index, members in enumerate(clusters):
        weight = float(np.sum(weights[members]))
        weighted_sine = float(np.sum(weights[members] * np.sin(relative_phases[members])))
        representative = float(
            np.angle(np.sum(weights[members] * np.exp(1j * raw_phases[members])))
        ) if weight > 0.0 else float(min(raw_phases[index] for index in members))
        contribution = float((weighted_sine - weight * target_sine) / time_value)
        cluster_rows.append({
            "condition": condition,
            "time_hartree_inverse": time_value,
            "time_hex": time_hex,
            "cluster_index": cluster_index,
            "target_cluster": cluster_index == target_cluster,
            "member_count": len(members),
            "member_schur_indices": members,
            "weight": weight,
            "representative_raw_phase_radian": representative,
            "weighted_relative_sine": weighted_sine,
            "signed_contribution_relative_to_target_hartree": contribution,
        })
    target_row = cluster_rows[target_cluster]
    target_internal = float(
        target_row["signed_contribution_relative_to_target_hartree"]
    )
    non_target = [
        row for row in cluster_rows if not bool(row["target_cluster"])
    ]
    non_target_sum = float(sum(
        float(row["signed_contribution_relative_to_target_hartree"])
        for row in non_target
    ))
    nonlinear = float(target_sine / time_value - shift)
    closure = float(
        (exact_proxy - shift) - (nonlinear + target_internal + non_target_sum)
    )
    top_k_rows: list[dict[str, Any]] = []
    for ranking in ("weight_ranked", "oracle_contribution_ranked"):
        if ranking == "weight_ranked":
            ordered = sorted(
                non_target,
                key=lambda row: (
                    -float(row["weight"]),
                    float(row["representative_raw_phase_radian"]),
                    int(row["cluster_index"]),
                ),
            )
        else:
            ordered = sorted(
                non_target,
                key=lambda row: (
                    -abs(float(row["signed_contribution_relative_to_target_hartree"])),
                    -float(row["weight"]),
                    float(row["representative_raw_phase_radian"]),
                    int(row["cluster_index"]),
                ),
            )
        for raw_k in protocol["definitions"]["top_k"]["values"]:
            retained = ordered if raw_k == "all" else ordered[: min(int(raw_k), len(ordered))]
            retained_ids = {int(row["cluster_index"]) for row in retained}
            omitted = [
                row for row in non_target
                if int(row["cluster_index"]) not in retained_ids
            ]
            omitted_signed = float(sum(
                float(row["signed_contribution_relative_to_target_hartree"])
                for row in omitted
            ))
            q_omit = float(sum(float(row["weight"]) for row in omitted))
            bound = float(2.0 * q_omit / time_value)
            actual_ratio = abs(omitted_signed) / allowance
            bound_ratio = bound / allowance
            top_k_rows.append({
                "condition": condition,
                "time_hartree_inverse": time_value,
                "time_hex": time_hex,
                "ranking": ranking,
                "k": raw_k,
                "retained_cluster_count": len(retained),
                "retained_cluster_indices": sorted(retained_ids),
                "omitted_cluster_count": len(omitted),
                "omitted_weight": q_omit,
                "omitted_signed_residual_hartree": omitted_signed,
                "omitted_actual_absolute_residual_hartree": abs(omitted_signed),
                "omitted_conservative_bound_hartree": bound,
                "coordinate_allowance_hartree": allowance,
                "actual_omitted_over_allowance": actual_ratio,
                "conservative_bound_over_allowance": bound_ratio,
                "actual_gate_pass": actual_ratio
                <= float(protocol["compression_gate"][
                    "actual_omitted_over_allowance_maximum"
                ]),
                "conservative_gate_pass": bound_ratio
                <= float(protocol["compression_gate"][
                    "conservative_bound_over_allowance_maximum"
                ]),
            })
    dimension = int(unitary.shape[0])
    unitarity = float(np.linalg.norm(
        unitary.conj().T @ unitary - np.eye(dimension, dtype=np.complex128),
        ord="fro",
    ))
    eigenpair_residuals = np.linalg.norm(
        unitary @ vectors - vectors * eigenvalues[None, :], axis=0
    )
    maximum_eigenpair = float(np.max(eigenpair_residuals))
    weight_residual = float(abs(np.sum(weights) - 1.0))
    saved_overlap = float(saved_direct["ground_overlap_probability"])
    saved_branch_disagreement = (
        str(saved_direct["branch_selection_disagrees_with_independent_rule"])
        .strip()
        .lower()
        == "true"
    )
    echo_residual = max(
        abs(reconstructed_echo - matrix_echo),
        abs(matrix_echo - saved_echo),
    )
    gates = protocol["numerical_gates"]
    gate_results = {
        "weight_normalization": weight_residual
        <= float(gates["weight_normalization_absolute_residual_maximum"]),
        "eigenpair": maximum_eigenpair
        <= float(gates["eigenpair_residual_maximum"]),
        "unitarity": unitarity
        <= float(gates["unitarity_frobenius_residual_maximum"]),
        "exact_ground": exact_ground_residual
        <= float(gates["exact_ground_residual_maximum"]),
        "complex_echo": echo_residual
        <= float(gates["complex_echo_absolute_residual_maximum"]),
        "energy_proxy_reconstruction": abs(exact_proxy - saved_exact_proxy)
        <= float(gates["energy_proxy_reconstruction_residual_hartree_maximum"]),
        "saved_direct_shift": abs(shift - saved_shift)
        <= float(gates["saved_direct_shift_residual_hartree_maximum"]),
        "saved_target_overlap": abs(float(weights[selected]) - saved_overlap)
        <= float(gates["saved_target_overlap_absolute_residual_maximum"]),
        "phase_gap": phase_gap > float(gates["phase_gap_rad_strict_minimum"]),
        "branch_agreement": not saved_branch_disagreement,
    }
    coordinate_row = {
        "condition": condition,
        "time_hartree_inverse": time_value,
        "time_hex": time_hex,
        "dimension": dimension,
        "cluster_count": len(clusters),
        "target_cluster_index": target_cluster,
        "target_cluster_member_count": len(target_members),
        "target_cluster_weight": float(target_row["weight"]),
        "selected_target_weight": float(weights[selected]),
        "saved_target_overlap": saved_overlap,
        "saved_branch_selection_disagreement": saved_branch_disagreement,
        "target_overlap_residual": abs(float(weights[selected]) - saved_overlap),
        "signed_direct_shift_hartree": shift,
        "saved_direct_shift_hartree": saved_shift,
        "direct_shift_residual_hartree": abs(shift - saved_shift),
        "phase_unwrap_integer": unwrap_integer,
        "phase_gap_radian": phase_gap,
        "exact_proxy_signed_hartree": exact_proxy,
        "saved_exact_proxy_signed_hartree": saved_exact_proxy,
        "energy_proxy_reconstruction_residual_hartree":
            abs(exact_proxy - saved_exact_proxy),
        "matrix_echo_real": float(matrix_echo.real),
        "matrix_echo_imaginary": float(matrix_echo.imag),
        "reconstructed_echo_real": float(reconstructed_echo.real),
        "reconstructed_echo_imaginary": float(reconstructed_echo.imag),
        "saved_echo_real": float(saved_echo.real),
        "saved_echo_imaginary": float(saved_echo.imag),
        "complex_echo_absolute_residual": float(echo_residual),
        "weight_normalization_residual": weight_residual,
        "maximum_eigenpair_residual_2_norm": maximum_eigenpair,
        "unitarity_residual_frobenius": unitarity,
        "exact_ground_residual_2_norm": exact_ground_residual,
        "single_phase_nonlinearity_hartree": nonlinear,
        "target_cluster_internal_hartree": target_internal,
        "non_target_signed_contribution_hartree": non_target_sum,
        "decomposition_closure_residual_hartree": closure,
        "coordinate_allowance_hartree": allowance,
        "all_numerical_gates_pass": all(gate_results.values()),
        "numerical_gates": gate_results,
        "timing_seconds": {
            **build,
            "total_including_schur_and_analysis": time.perf_counter() - started,
        },
    }
    del unitary, triangular, vectors
    return {
        "coordinate": coordinate_row,
        "components": component_rows,
        "clusters": cluster_rows,
        "top_k": top_k_rows,
    }


def _coordinate_gate(
    top_k_rows: Sequence[Mapping[str, Any]],
    condition: str,
    time_hex: str,
    ranking: str,
    maximum_k: int,
    require_conservative: bool,
) -> bool:
    for row in top_k_rows:
        if (
            row["condition"] == condition
            and row["time_hex"] == time_hex
            and row["ranking"] == ranking
            and row["k"] != "all"
            and int(row["k"]) <= maximum_k
            and bool(row["actual_gate_pass"])
            and (bool(row["conservative_gate_pass"]) or not require_conservative)
        ):
            return True
    return False


def choose_outcome(
    protocol: Mapping[str, Any],
    coordinate_rows: Sequence[Mapping[str, Any]],
    top_k_rows: Sequence[Mapping[str, Any]],
) -> tuple[str, dict[str, Any]]:
    truth_free_route = {
        "candidate": "unitary_krylov_moments_from_frozen_approximate_state",
        "subspace_dimension_maximum": 8,
        "pf_actions_per_coordinate_maximum": 8,
        "hamiltonian_actions_per_coordinate_maximum": 8,
        "uses_direct_truth_operationally": False,
        "uses_exact_state_operationally": False,
        "implemented_or_validated_in_d1": False,
        "resource_envelope_within_d0_limits": True,
        "unresolved": [
            "branch correspondence without truth",
            "conditioning and truncation",
            "measurement precision and classical information cost",
            "transfer from exact-ground diagnostic weights to an obtainable state",
        ],
    }
    expected_keys = {
        (str(row["condition"]), str(row["time_hex"]))
        for row in protocol["scope"]["coordinates"]
    }
    keys = [(str(row["condition"]), str(row["time_hex"])) for row in coordinate_rows]
    if len(keys) != 6 or len(set(keys)) != 6 or set(keys) != expected_keys:
        raise PilotError("D1 outcome requires the exact six frozen coordinates")
    if not all(bool(row["all_numerical_gates_pass"]) for row in coordinate_rows):
        return "failed_numerical_validation", {
            "all_numerical_gates_pass": False,
            "weight_ranked_k_le_4_actual_and_conservative_all_six": False,
            "oracle_contribution_k_le_8_actual_all_six": False,
            "truth_free_route": truth_free_route,
            "d2_authorized": False,
        }
    weight_k4 = all(_coordinate_gate(
        top_k_rows, condition, time_hex, "weight_ranked", 4, True
    ) for condition, time_hex in keys)
    oracle_k8 = all(_coordinate_gate(
        top_k_rows, condition, time_hex, "oracle_contribution_ranked", 8, False
    ) for condition, time_hex in keys)
    if weight_k4:
        status = "d1_complete_prototype_candidate_stop"
    elif oracle_k8:
        status = "d1_complete_information_cost_limit_stop"
    else:
        status = "d1_complete_close_spectral_route_stop"
    return status, {
        "all_numerical_gates_pass": True,
        "weight_ranked_k_le_4_actual_and_conservative_all_six": weight_k4,
        "oracle_contribution_k_le_8_actual_all_six": oracle_k8,
        "truth_free_route": truth_free_route,
        "d2_authorized": False,
    }


def cache_key(
    *,
    head: str,
    protocol_sha256: str,
    authorization_sha256: str,
    condition: str,
    time_hex: str,
    hamiltonian_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": "pf_spectral_information_pilot_d1_coordinate_cache_key_v1",
        "head": head,
        "protocol_sha256": protocol_sha256,
        "authorization_sha256": authorization_sha256,
        "condition": condition,
        "time_hex": time_hex,
        "hamiltonian_sha256": hamiltonian_sha256,
        "backend": "cpu",
    }


def coordinate_cache_path(runtime: Path, key: Mapping[str, Any]) -> Path:
    digest = hashlib.sha256(
        json.dumps(key, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return runtime / "coordinate" / str(key["condition"]) / f"{digest}.pkl"


def build_report(
    status: str,
    decision: Mapping[str, Any],
    coordinates: Sequence[Mapping[str, Any]],
) -> str:
    maximum_eigenpair = max(float(row["maximum_eigenpair_residual_2_norm"]) for row in coordinates)
    maximum_unitarity = max(float(row["unitarity_residual_frobenius"]) for row in coordinates)
    minimum_overlap = min(float(row["selected_target_weight"]) for row in coordinates)
    return (
        "# P-SPEC-6 D1 completion\n\n"
        f"- Status: `{status}`\n"
        "- Scope: existing HCl equilibrium/stretch150 at 0.5/0.65/0.8 t_ana\n"
        "- Existing coordinates: 6; new coordinates: 0\n"
        f"- Maximum eigenpair residual: {maximum_eigenpair:.16g}\n"
        f"- Maximum unitarity residual: {maximum_unitarity:.16g}\n"
        f"- Minimum selected target weight: {minimum_overlap:.16g}\n"
        f"- Weight-ranked K<=4 certified at all six: "
        f"{decision['scientific_gates'].get('weight_ranked_k_le_4_actual_and_conservative_all_six')}\n"
        f"- Oracle-contribution K<=8 actual compression at all six: "
        f"{decision['scientific_gates'].get('oracle_contribution_k_le_8_actual_all_six')}\n"
        "- D2 authorized: false\n\n"
        "This is a post-hoc protocol-design pilot. It does not change the closed "
        "second-study `complete_no_benefit` result and does not validate a "
        "truth-free spectral method.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--d0-authorization", required=True, type=Path)
    parser.add_argument("--d1-authorization", required=True, type=Path)
    parser.add_argument("--phase-a-cache-amendment", required=True, type=Path)
    parser.add_argument("--phase-a-root", required=True, type=Path)
    parser.add_argument("--processes", required=True, type=int)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    root = args.project_root.resolve()
    protocol_path = (
        args.protocol if args.protocol.is_absolute() else root / args.protocol
    ).resolve()
    d0_authorization_path = (
        args.d0_authorization
        if args.d0_authorization.is_absolute()
        else root / args.d0_authorization
    ).resolve()
    d1_authorization_path = (
        args.d1_authorization
        if args.d1_authorization.is_absolute()
        else root / args.d1_authorization
    ).resolve()
    phase_a_amendment_path = (
        args.phase_a_cache_amendment
        if args.phase_a_cache_amendment.is_absolute()
        else root / args.phase_a_cache_amendment
    ).resolve()
    output = (
        args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    ).resolve()
    source = verify_source_identity(
        root,
        protocol_path,
        d0_authorization_path,
        d1_authorization_path,
        phase_a_amendment_path,
    )
    protocol = source["protocol"]
    environment = validate_process_environment(protocol, args.processes)
    protocol_sha256 = sha256_file(protocol_path)
    authorization_sha256 = sha256_file(d1_authorization_path)
    run_identity = {
        "schema": "pf_spectral_information_pilot_d1_run_identity_v1",
        "head": source["head"],
        "protocol_sha256": protocol_sha256,
        "d1_authorization_sha256": authorization_sha256,
        "phase_a_runtime_inventory_sha256": PHASE_A_INVENTORY_SHA256,
        "phase_a_root": str(args.phase_a_root.resolve()),
        "coordinate_time_hex": [
            str(row["time_hex"]) for row in protocol["scope"]["coordinates"]
        ],
        "backend": "cpu",
        "processes": 1,
    }
    runtime, resumed = prepare_output(output, run_identity)
    source_protocol_path = root / "review_response/second_study_safe_time_domain_protocol.json"
    source_protocol = load_json(source_protocol_path)
    source_protocol_sha256 = sha256_file(source_protocol_path)
    amendment = load_json(phase_a_amendment_path)
    r1_rows = load_csv(
        root / "artifacts/server_pf_candidate_validation_r1_20260928_fba3383/"
        "coordinate_proxy_results.csv"
    )
    r1_by_key = {
        (row["condition"], row["time_hex"]): row for row in r1_rows
    }
    expected_hamiltonians = {
        condition: next(
            row["hamiltonian_sha256"] for row in r1_rows
            if row["condition"] == condition
        )
        for condition in HCL_CONDITIONS
    }
    systems, phase_a_inventory = load_hcl_systems(
        args.phase_a_root.resolve(),
        amendment,
        source_protocol,
        source_protocol_sha256,
        expected_hamiltonians,
    )
    direct_rows = load_csv(
        root / "artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/"
        "direct_points.csv"
    )
    direct_by_key = {
        (row["condition"], float(row["time_hartree_inverse"]).hex()): row
        for row in direct_rows
    }
    allowance_rows = load_csv(
        root / "artifacts/pf_r1_readonly_design_summary_20260928/"
        "coordinate_budget_diagnostics.csv"
    )
    allowance_by_key = {
        (row["condition"], row["time_hex"]): float(row["coordinate_allowance_hartree"])
        for row in allowance_rows
    }
    sequence = execution.formula_sequence(source_protocol)
    exact_by_condition: dict[str, tuple[float, np.ndarray, float]] = {}
    exact_reused = 0
    exact_computed = 0
    for condition in HCL_CONDITIONS:
        energy, state, residual, reused = load_or_compute_exact(
            runtime, condition, systems[condition]
        )
        exact_by_condition[condition] = (energy, state, residual)
        exact_reused += int(reused)
        exact_computed += int(not reused)
    coordinate_payloads: list[dict[str, Any]] = []
    coordinate_computed = 0
    coordinate_reused = 0
    for coordinate in protocol["scope"]["coordinates"]:
        condition = str(coordinate["condition"])
        time_value = float(coordinate["time_hartree_inverse"])
        time_hex = str(coordinate["time_hex"])
        if time_value.hex() != time_hex:
            raise PilotError(f"{condition}: coordinate hex identity mismatch")
        key = cache_key(
            head=source["head"],
            protocol_sha256=protocol_sha256,
            authorization_sha256=authorization_sha256,
            condition=condition,
            time_hex=time_hex,
            hamiltonian_sha256=str(systems[condition]["hamiltonian_sha256"]),
        )
        cache = coordinate_cache_path(runtime, key)
        if cache.is_file():
            with cache.open("rb") as stream:
                cached = pickle.load(stream)
            if cached.get("cache_key") != key:
                raise PilotError(f"{condition}/{time_hex}: stale coordinate cache")
            payload = cached["payload"]
            coordinate_reused += 1
        else:
            energy, state, residual = exact_by_condition[condition]
            payload = analyze_coordinate(
                condition=condition,
                time_value=time_value,
                time_hex=time_hex,
                system=systems[condition],
                exact_energy=energy,
                exact_state=state,
                exact_ground_residual=residual,
                sequence=sequence,
                saved_direct=direct_by_key[(condition, time_hex)],
                saved_r1=r1_by_key[(condition, time_hex)],
                allowance=allowance_by_key[(condition, time_hex)],
                protocol=protocol,
            )
            atomic_pickle(cache, {"cache_key": key, "payload": payload})
            coordinate_computed += 1
        coordinate_payloads.append(payload)
        elapsed = time.perf_counter() - started
        if elapsed > float(protocol["calculation_limits"]["total_wall_seconds_maximum"]):
            raise PilotError("D1 wall-time limit exceeded")
        peak_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
        if peak_bytes > int(protocol["calculation_limits"]["peak_memory_bytes_maximum"]):
            raise PilotError("D1 peak-memory limit exceeded")
    coordinate_rows = [payload["coordinate"] for payload in coordinate_payloads]
    component_rows = [
        row for payload in coordinate_payloads for row in payload["components"]
    ]
    cluster_rows = [
        row for payload in coordinate_payloads for row in payload["clusters"]
    ]
    top_k_rows = [
        row for payload in coordinate_payloads for row in payload["top_k"]
    ]
    status, scientific_gates = choose_outcome(
        protocol, coordinate_rows, top_k_rows
    )
    elapsed = time.perf_counter() - started
    peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    resource_gates = {
        "wall_time": elapsed
        <= float(protocol["calculation_limits"]["total_wall_seconds_maximum"]),
        "peak_memory": peak_rss_kib * 1024
        <= int(protocol["calculation_limits"]["peak_memory_bytes_maximum"]),
        "cpu_only": "cupy" not in sys.modules,
        "processes": args.processes == 1,
    }
    if not all(resource_gates.values()):
        status = "failed_resource_validation"
    runtime_coordinate_files = list((runtime / "coordinate").rglob("*.pkl"))
    runtime_exact_files = list((runtime / "exact_state").glob("*.pkl"))
    if len(runtime_coordinate_files) != 6 or len(runtime_exact_files) != 2:
        raise PilotError("D1 runtime calculation count mismatch")
    counts = {
        "condition_count": 2,
        "coordinate_count": 6,
        "new_direct_coordinate_count": 0,
        "existing_coordinate_full_pf_unitary_rebuild_count": 6,
        "existing_coordinate_pf_eigendecomposition_count": 6,
        "same_h_exact_ground_regeneration_count": 2,
        "coordinate_computed_this_invocation": coordinate_computed,
        "coordinate_reused_this_invocation": coordinate_reused,
        "exact_ground_computed_this_invocation": exact_computed,
        "exact_ground_reused_this_invocation": exact_reused,
        "new_hamiltonian_count": 0,
        "new_state_approximation_method_count": 0,
        "new_proxy_sampling_campaign_count": 0,
        "optimization_count": 0,
        "gpu_query_count": 0,
        "gpu_allocation_count": 0,
        "gpu_kernel_count": 0,
    }
    decision = {
        "schema": "pf_spectral_information_pilot_d1_decision_v1",
        "status": status,
        "evidence_class": "post_hoc_protocol_design_spectral_diagnostic",
        "closed_second_study_status": "complete_no_benefit_unchanged",
        "d0_result_commit": D0_RESULT_COMMIT,
        "execution_head": source["head"],
        "protocol_sha256": protocol_sha256,
        "d1_authorization_sha256": authorization_sha256,
        "counts": counts,
        "all_numerical_gates_pass": all(
            bool(row["all_numerical_gates_pass"]) for row in coordinate_rows
        ),
        "scientific_gates": scientific_gates,
        "resource_gates": resource_gates,
        "d2_authorized": False,
        "method_implementation_authorized": False,
        "holdout_authorized": False,
        "retuning_authorized": False,
    }
    resource_audit = {
        "schema": "pf_spectral_information_pilot_d1_resource_audit_v1",
        "environment": environment,
        "resumed": resumed,
        "wall_seconds": elapsed,
        "peak_cpu_rss_kib": peak_rss_kib,
        "phase_a_runtime": phase_a_inventory,
        "counts": counts,
        "resource_gates": resource_gates,
        "runtime_file_count": len(runtime_coordinate_files) + len(runtime_exact_files) + 1,
        "runtime_files_committed": False,
    }
    source_manifest = {
        "schema": "pf_spectral_information_pilot_d1_source_manifest_v1",
        "head": source["head"],
        "protocol_sha256": protocol_sha256,
        "d1_authorization_sha256": authorization_sha256,
        "verified_source_count": source["verified_source_count"],
        "verified_sources": source["verified_sources"],
        "phase_a_runtime_inventory_sha256": phase_a_inventory["inventory_sha256"],
        "source_substitution_count": 0,
    }
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "coordinate_summary.csv", coordinate_rows)
    write_csv(output / "spectral_components.csv", component_rows)
    write_csv(output / "spectral_clusters.csv", cluster_rows)
    write_csv(output / "top_k_compression.csv", top_k_rows)
    atomic_json(output / "decision.json", decision)
    atomic_json(output / "resource_audit.json", resource_audit)
    atomic_json(output / "source_manifest.json", source_manifest)
    atomic_json(output / "route_assessment.json", scientific_gates["truth_free_route"])
    (output / "report.md").write_text(
        build_report(status, decision, coordinate_rows), encoding="utf-8"
    )
    public_paths = [
        "coordinate_summary.csv",
        "decision.json",
        "report.md",
        "resource_audit.json",
        "route_assessment.json",
        "source_manifest.json",
        "spectral_clusters.csv",
        "spectral_components.csv",
        "top_k_compression.csv",
    ]
    if status in COMPLETE_STATUSES:
        atomic_json(output / "D1_COMPLETE.json", {
            "status": status,
            "protocol_sha256": protocol_sha256,
            "d1_authorization_sha256": authorization_sha256,
            "d2_authorized": False,
        })
        public_paths.insert(0, "D1_COMPLETE.json")
    manifest = {
        "schema": "pf_spectral_information_pilot_d1_manifest_v1",
        "status": status,
        "files": [
            {
                "path": relative,
                "bytes": (output / relative).stat().st_size,
                "sha256": sha256_file(output / relative),
            }
            for relative in public_paths
        ],
        "runtime_files_committed": False,
    }
    atomic_json(output / "manifest.json", manifest)
    print(json.dumps(jsonable(decision), indent=2, sort_keys=True))
    return 0 if status in COMPLETE_STATUSES else 2


if __name__ == "__main__":
    raise SystemExit(main())
