"""Truth-only Phase B runner for the frozen safe-time-domain study."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import pickle
import resource
import subprocess
import time
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.linalg import eigh, schur

from review_response import second_study_safe_time_domain_execution as execution
from review_response import second_study_safe_time_domain_guard as guard
from review_response import run_second_study_safe_time_domain_phase_a as phase_a


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    phase_a._write_json(path, payload)


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise execution.ExecutionError(f"refusing to write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(str(key))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows([phase_a._jsonable(dict(row)) for row in rows])


def _array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(array.tobytes())
    return digest.hexdigest()


def _git_blob_sha256(project_root: Path, commit: str, path: Path) -> str:
    content = subprocess.run(
        ["git", "show", f"{commit}:{path.as_posix()}"],
        cwd=project_root,
        check=True,
        capture_output=True,
    ).stdout
    return execution.sha256_bytes(content)


def verify_phase_a_commit(
    *,
    project_root: Path,
    phase_a_root: Path,
    phase_a_commit: str,
    phase_a_artifact_relative: Path,
) -> dict[str, Any]:
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", phase_a_commit, "HEAD"],
        cwd=project_root,
        check=False,
    ).returncode != 0:
        raise execution.ExecutionError("Phase A commit is not an ancestor of HEAD")
    remote_branches = subprocess.run(
        ["git", "branch", "-r", "--contains", phase_a_commit],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if not any(branch.strip().startswith("origin/") for branch in remote_branches):
        raise execution.ExecutionError("Phase A commit is not present on origin")
    manifest = execution.load_json(phase_a_root / "manifest.json")
    committed_files = list(manifest["files"]) + [
        {
            "path": "manifest.json",
            "sha256": execution.sha256_file(phase_a_root / "manifest.json"),
        }
    ]
    for row in committed_files:
        local = phase_a_root / str(row["path"])
        if not local.is_file() or execution.sha256_file(local) != row["sha256"]:
            raise execution.ExecutionError(f"Phase A artifact mismatch: {local}")
        committed = phase_a_artifact_relative / str(row["path"])
        if execution.sha256_file(local) != _git_blob_sha256(
            project_root, phase_a_commit, committed
        ):
            raise execution.ExecutionError(
                f"Phase A file differs from commit: {committed}"
            )
    marker = guard.verify_phase_a_freeze(phase_a_root)
    return {
        "commit": phase_a_commit,
        "artifact_root": str(phase_a_root.resolve()),
        "artifact_relative": phase_a_artifact_relative.as_posix(),
        "prediction_sha256": marker["prediction_sha256"],
        "phase_b_coordinate_count": marker["phase_b_coordinate_count"],
        "remote_branches_containing_commit": [
            value.strip() for value in remote_branches
        ],
    }


def verify_phase_a_runtime_inventory(
    phase_a_root: Path,
) -> dict[str, Any]:
    inventory_path = phase_a_root / "runtime_hash_inventory.json"
    inventory = execution.load_json(inventory_path)
    if (
        inventory.get("schema")
        != "second_study_safe_time_domain_phase_a_runtime_hash_inventory_v1"
    ):
        raise execution.ExecutionError("invalid Phase A runtime inventory schema")
    runtime_root = (phase_a_root / ".runtime").resolve()
    if str(inventory.get("runtime_root")) != str(runtime_root):
        raise execution.ExecutionError("Phase A runtime root identity mismatch")
    rows = inventory.get("files")
    if not isinstance(rows, list) or not rows:
        raise execution.ExecutionError("Phase A runtime inventory is empty")
    expected: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        relative = Path(str(row.get("path", "")))
        if (
            not str(relative)
            or relative.is_absolute()
            or ".." in relative.parts
            or relative.as_posix() in expected
        ):
            raise execution.ExecutionError(
                "unsafe or duplicate Phase A runtime inventory path"
            )
        expected[relative.as_posix()] = row
    actual = {
        path.relative_to(runtime_root).as_posix(): path
        for path in runtime_root.rglob("*")
        if path.is_file()
    }
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise execution.ExecutionError(
            f"Phase A runtime inventory file-set mismatch: "
            f"missing={missing}, extra={extra}"
        )
    total_bytes = 0
    for relative, path in actual.items():
        row = expected[relative]
        size = int(path.stat().st_size)
        total_bytes += size
        if size != int(row.get("bytes", -1)):
            raise execution.ExecutionError(
                f"Phase A runtime byte-count mismatch: {relative}"
            )
        if str(row.get("absolute_path")) != str(path.resolve()):
            raise execution.ExecutionError(
                f"Phase A runtime absolute-path mismatch: {relative}"
            )
        if execution.sha256_file(path) != row.get("sha256"):
            raise execution.ExecutionError(
                f"Phase A runtime SHA-256 mismatch: {relative}"
            )
    if len(actual) != int(inventory.get("file_count", -1)):
        raise execution.ExecutionError("Phase A runtime file count mismatch")
    if total_bytes != int(inventory.get("total_bytes", -1)):
        raise execution.ExecutionError("Phase A runtime total byte count mismatch")
    return {
        "inventory_sha256": execution.sha256_file(inventory_path),
        "runtime_root": str(runtime_root),
        "file_count": len(actual),
        "total_bytes": total_bytes,
        "all_files_byte_identical": True,
    }


def prepare_phase_b_output(
    output_dir: Path,
    run_identity: Mapping[str, Any],
) -> dict[str, Any]:
    runtime_root = output_dir / ".runtime"
    marker = runtime_root / "run_identity.json"
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        _write_json(marker, run_identity)
        return {
            "resumed": False,
            "preexisting_direct_cache_files": 0,
            "run_identity_sha256": execution.sha256_file(marker),
        }
    if not output_dir.is_dir():
        raise execution.ExecutionError("Phase B output exists and is not a directory")
    if not marker.is_file():
        raise execution.ExecutionError(
            "existing Phase B output lacks exact-run identity marker"
        )
    if execution.load_json(marker) != dict(run_identity):
        raise execution.ExecutionError("existing Phase B run identity mismatch")
    allowed_marker = marker.relative_to(output_dir).as_posix()
    cache_files = []
    for path in output_dir.rglob("*"):
        if path.is_symlink():
            raise execution.ExecutionError(
                f"symlink forbidden in Phase B resume output: {path}"
            )
        if not path.is_file():
            continue
        relative = path.relative_to(output_dir).as_posix()
        if relative == allowed_marker:
            continue
        if (
            len(Path(relative).parts) < 4
            or Path(relative).parts[:2] != (".runtime", "direct_cache")
            or path.suffix != ".pkl"
        ):
            raise execution.ExecutionError(
                f"unexpected file in Phase B resume output: {relative}"
            )
        cache_files.append(relative)
    return {
        "resumed": True,
        "preexisting_direct_cache_files": len(cache_files),
        "run_identity_sha256": execution.sha256_file(marker),
    }


def load_phase_a_systems(
    phase_a_root: Path,
    protocol: Mapping[str, Any],
    protocol_sha256: str,
) -> dict[str, dict[str, Any]]:
    manifest = execution.load_json(
        phase_a_root / "sanitized_input_manifest.json"
    )
    if manifest.get("protocol_sha256") != protocol_sha256:
        raise execution.ExecutionError("Phase A system manifest protocol mismatch")
    expected = execution.condition_names(protocol)
    if [row["condition"] for row in manifest["entries"]] != expected:
        raise execution.ExecutionError("Phase A system condition order changed")
    systems: dict[str, dict[str, Any]] = {}
    for row in manifest["entries"]:
        path = phase_a_root / str(row["runtime_system_cache"])
        if execution.sha256_file(path) != row["runtime_system_cache_sha256"]:
            raise execution.ExecutionError(f"Phase A runtime cache mismatch: {path}")
        with path.open("rb") as stream:
            system = pickle.load(stream)
        if (
            system.get("schema")
            != "second_study_safe_time_domain_phase_a_system_v1"
            or system.get("protocol_sha256") != protocol_sha256
            or system.get("condition") != row["condition"]
            or system.get("hamiltonian_sha256") != row["hamiltonian_sha256"]
        ):
            raise execution.ExecutionError(f"invalid Phase A system cache: {path}")
        systems[str(row["condition"])] = system
    return systems


def exact_ground_pair(system: Mapping[str, Any]) -> tuple[float, np.ndarray, float]:
    matrix = system["hamiltonian"].toarray()
    values, vectors = eigh(
        matrix,
        subset_by_index=[0, 0],
        check_finite=False,
        driver="evr",
    )
    energy = float(values[0])
    state = np.asarray(vectors[:, 0], dtype=np.complex128)
    state /= np.linalg.norm(state)
    residual = float(
        np.linalg.norm(system["hamiltonian"] @ state - energy * state)
    )
    del matrix
    if residual > 1e-10:
        raise execution.ExecutionError(
            f"ground eigenpair residual exceeds integrity gate: {residual}"
        )
    return energy, state, residual


def _build_unitary(
    system: Mapping[str, Any],
    sequence: Sequence[float],
    time_value: float,
    backend: str,
    gpu_id: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    import run_full_electron_nh3_higher_term_diagnosis as diagnosis

    if backend == "gpu":
        return diagnosis._build_gpu(
            dict(system), sequence, float(time_value), int(gpu_id)
        )
    if backend == "cpu":
        return diagnosis._build_cpu(
            dict(system), sequence, float(time_value)
        )
    raise execution.ExecutionError(f"unsupported backend: {backend}")


def direct_point(
    *,
    system: Mapping[str, Any],
    exact_energy: float,
    exact_state: np.ndarray,
    sequence: Sequence[float],
    rotations: int,
    time_value: float,
    roles: Sequence[str],
    backend: str,
    gpu_id: int,
    previous_vector: np.ndarray | None,
    previous_unwrapped_shift: float | None,
    epsilon: float,
    beta: float,
) -> tuple[dict[str, Any], np.ndarray, float]:
    started = time.perf_counter()
    unitary, build = _build_unitary(
        system, sequence, time_value, backend, gpu_id
    )
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    eigenvalues = np.diag(triangular)
    ground_overlaps = np.abs(vectors.conj().T @ exact_state) ** 2
    independent_index = int(np.argmax(ground_overlaps))
    if previous_vector is None:
        selected_index = independent_index
        previous_overlap = None
        selection_rule = "anchor_maximum_exact_ground_overlap"
    else:
        previous_overlaps = np.abs(vectors.conj().T @ previous_vector) ** 2
        selected_index = int(np.argmax(previous_overlaps))
        previous_overlap = float(previous_overlaps[selected_index])
        selection_rule = "ascending_time_maximum_previous_vector_overlap"
    eigenvalue = complex(eigenvalues[selected_index])
    vector = np.asarray(vectors[:, selected_index], dtype=np.complex128)
    principal_shift = float(
        np.angle(np.exp(-1j * exact_energy * time_value) * eigenvalue)
        / time_value
    )
    if previous_unwrapped_shift is None:
        unwrapped_shift = principal_shift
        unwrap_integer = 0
    else:
        period = 2.0 * np.pi / time_value
        unwrap_integer = int(
            round((previous_unwrapped_shift - principal_shift) / period)
        )
        unwrapped_shift = float(principal_shift + unwrap_integer * period)
    relative_phases = np.abs(
        np.angle(eigenvalues * np.conj(eigenvalue))
    )
    relative_phases[selected_index] = np.inf
    phase_gap = float(np.min(relative_phases))
    eigenpair_residual = float(
        np.linalg.norm(unitary @ vector - eigenvalue * vector)
    )
    dimension = int(unitary.shape[0])
    unitarity_residual = float(
        np.linalg.norm(
            unitary.conj().T @ unitary
            - np.eye(dimension, dtype=np.complex128),
            ord="fro",
        )
    )
    direct_error = abs(unwrapped_shift)
    direct_cost = execution.required_cost(
        time_value, direct_error, rotations, epsilon, beta
    )
    point = {
        "time_hartree_inverse": float(time_value),
        "roles": list(roles),
        "selection_rule": selection_rule,
        "selected_schur_index": selected_index,
        "independent_maximum_ground_overlap_index": independent_index,
        "branch_selection_disagrees_with_independent_rule": bool(
            selected_index != independent_index
        ),
        "ground_overlap_probability": float(
            ground_overlaps[selected_index]
        ),
        "independent_ground_overlap_probability": float(
            ground_overlaps[independent_index]
        ),
        "previous_vector_overlap_probability": previous_overlap,
        "selected_eigenvalue_real": float(eigenvalue.real),
        "selected_eigenvalue_imaginary": float(eigenvalue.imag),
        "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
        "principal_energy_shift_hartree": principal_shift,
        "phase_unwrap_integer": unwrap_integer,
        "signed_direct_shift_hartree": unwrapped_shift,
        "direct_error_hartree": direct_error,
        "direct_required_cost": direct_cost,
        "eigenpair_residual_2_norm": eigenpair_residual,
        "unitarity_residual_frobenius": unitarity_residual,
        "phase_gap_radian": phase_gap,
        "timing_seconds": {
            **build,
            "total_including_schur_and_validation": float(
                time.perf_counter() - started
            ),
        },
        "peak_cpu_rss_kib": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        ),
    }
    del unitary, triangular, vectors
    return point, vector, unwrapped_shift


def cached_direct_point(
    *,
    cache_root: Path,
    protocol_sha256: str,
    prediction_sha256: str,
    condition: str,
    system: Mapping[str, Any],
    formula_sha256: str,
    sequence: Sequence[float],
    rotations: int,
    exact_energy: float,
    exact_state: np.ndarray,
    time_value: float,
    roles: Sequence[str],
    backend: str,
    gpu_id: int,
    previous_vector: np.ndarray | None,
    previous_unwrapped_shift: float | None,
    epsilon: float,
    beta: float,
) -> tuple[dict[str, Any], np.ndarray, float, bool]:
    previous_hash = (
        None if previous_vector is None else _array_sha256(previous_vector)
    )
    cache_key = execution.phase_b_cache_key(
        protocol_sha256=protocol_sha256,
        prediction_sha256=prediction_sha256,
        condition=condition,
        hamiltonian_sha256=str(system["hamiltonian_sha256"]),
        formula_sha256_value=formula_sha256,
        time_value=time_value,
        backend=backend,
        previous_vector_sha256=previous_hash,
    )
    digest = execution.canonical_json_sha256(cache_key)
    path = cache_root / condition / f"{digest}.pkl"
    if path.is_file():
        with path.open("rb") as stream:
            payload = pickle.load(stream)
        if payload.get("cache_key") != cache_key:
            raise execution.ExecutionError(f"stale direct cache: {path}")
        vector = np.asarray(payload["selected_vector"], dtype=np.complex128)
        if payload.get("selected_vector_sha256") != _array_sha256(vector):
            raise execution.ExecutionError(f"direct cache vector mismatch: {path}")
        point = dict(payload["point"])
        if point.get("roles") != list(roles):
            raise execution.ExecutionError(f"direct cache role mismatch: {path}")
        return (
            point,
            vector,
            float(point["signed_direct_shift_hartree"]),
            True,
        )
    point, vector, shift = direct_point(
        system=system,
        exact_energy=exact_energy,
        exact_state=exact_state,
        sequence=sequence,
        rotations=rotations,
        time_value=time_value,
        roles=roles,
        backend=backend,
        gpu_id=gpu_id,
        previous_vector=previous_vector,
        previous_unwrapped_shift=previous_unwrapped_shift,
        epsilon=epsilon,
        beta=beta,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".pkl.tmp")
    with temporary.open("wb") as stream:
        pickle.dump(
            {
                "cache_key": cache_key,
                "point": point,
                "selected_vector": vector,
                "selected_vector_sha256": _array_sha256(vector),
            },
            stream,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    temporary.replace(path)
    return point, vector, shift, False


def validate_numerical_gates(
    direct_by_condition: Mapping[str, Sequence[Mapping[str, Any]]],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    points = [
        point for rows in direct_by_condition.values() for point in rows
    ]
    anchors = [
        point for point in points if "anchor" in point["roles"]
    ]
    nonanchors = [
        point for point in points if "anchor" not in point["roles"]
    ]
    gates = protocol["phase_b"]["numerical_gates"]
    metrics = {
        "maximum_eigenpair_residual_2_norm": max(
            float(point["eigenpair_residual_2_norm"]) for point in points
        ),
        "maximum_unitarity_residual_frobenius": max(
            float(point["unitarity_residual_frobenius"]) for point in points
        ),
        "minimum_anchor_ground_overlap_probability": min(
            float(point["ground_overlap_probability"]) for point in anchors
        ),
        "minimum_tracked_previous_overlap_probability": min(
            float(point["previous_vector_overlap_probability"])
            for point in nonanchors
        ),
        "minimum_tracked_ground_overlap_probability": min(
            float(point["ground_overlap_probability"]) for point in points
        ),
        "minimum_phase_gap_radian": min(
            float(point["phase_gap_radian"]) for point in points
        ),
        "branch_disagreement_count": sum(
            int(point["branch_selection_disagrees_with_independent_rule"])
            for point in points
        ),
    }
    checks = {
        "eigenpair_residual": metrics[
            "maximum_eigenpair_residual_2_norm"
        ]
        <= float(gates["maximum_eigenpair_residual_2_norm"]),
        "unitarity_residual": metrics[
            "maximum_unitarity_residual_frobenius"
        ]
        <= float(gates["maximum_unitarity_residual_frobenius"]),
        "anchor_ground_overlap": metrics[
            "minimum_anchor_ground_overlap_probability"
        ]
        >= float(gates["minimum_anchor_ground_overlap_probability"]),
        "previous_overlap": metrics[
            "minimum_tracked_previous_overlap_probability"
        ]
        >= float(gates["minimum_tracked_previous_overlap_probability"]),
        "tracked_ground_overlap": metrics[
            "minimum_tracked_ground_overlap_probability"
        ]
        >= float(gates["minimum_tracked_ground_overlap_probability"]),
        "phase_gap": metrics["minimum_phase_gap_radian"]
        > float(gates["minimum_phase_gap_radian_exclusive"]),
        "branch_disagreement": metrics["branch_disagreement_count"] == 0,
    }
    return {"metrics": metrics, "checks": checks, "passed": all(checks.values())}


def _manifest(output_dir: Path, required: Sequence[str]) -> dict[str, Any]:
    files = []
    for name in required:
        path = output_dir / name
        if not path.is_file():
            raise execution.ExecutionError(f"missing Phase B artifact: {name}")
        files.append(
            {
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": execution.sha256_file(path),
            }
        )
    payload = {
        "schema": "second_study_safe_time_domain_phase_b_manifest_v1",
        "created_at": execution.now(),
        "files": files,
        "excluded_from_commit": ["*.pkl", "*.npy", ".runtime/"],
    }
    _write_json(output_dir / "manifest.json", payload)
    return payload


def run(
    *,
    project_root: Path,
    protocol_path: Path,
    preflight_root: Path,
    phase_a_root: Path,
    phase_a_commit: str,
    phase_a_artifact_relative: Path,
    backend: str,
    gpu_id: int,
    processes: int,
    output_dir: Path,
) -> dict[str, Any]:
    if int(processes) != 1:
        raise execution.ExecutionError("Phase B requires --processes 1")
    if backend != "gpu":
        raise execution.ExecutionError("formal Phase B requires --backend gpu")
    project_root = project_root.resolve()
    phase_a_root = phase_a_root.resolve()
    output_dir = output_dir.resolve()
    protocol, protocol_sha = execution.load_frozen_protocol(protocol_path)
    environment = phase_a.validate_process_environment(project_root)
    preflight = phase_a.validate_preflight(project_root, preflight_root.resolve())
    phase_a_identity = verify_phase_a_commit(
        project_root=project_root,
        phase_a_root=phase_a_root,
        phase_a_commit=phase_a_commit,
        phase_a_artifact_relative=phase_a_artifact_relative,
    )
    phase_a_runtime_identity = verify_phase_a_runtime_inventory(phase_a_root)
    output_identity = prepare_phase_b_output(
        output_dir,
        {
            "schema": "second_study_safe_time_domain_phase_b_run_identity_v1",
            "protocol_sha256": protocol_sha,
            "prediction_sha256": phase_a_identity["prediction_sha256"],
            "phase_a_commit": phase_a_commit,
            "phase_a_artifact_root": str(phase_a_root),
            "phase_a_artifact_relative": phase_a_artifact_relative.as_posix(),
            "backend": backend,
            "gpu_id": int(gpu_id),
            "processes": int(processes),
        },
    )
    started = time.perf_counter()
    predictions = execution.load_json(phase_a_root / guard.PREDICTION_FILE)
    prediction_sha = execution.sha256_file(
        phase_a_root / guard.PREDICTION_FILE
    )
    if prediction_sha != phase_a_identity["prediction_sha256"]:
        raise execution.ExecutionError("Phase A prediction identity mismatch")
    systems = load_phase_a_systems(phase_a_root, protocol, protocol_sha)
    sequence = execution.formula_sequence(protocol)
    formula_hash = execution.formula_sha256(protocol)
    coordinate_plan = guard.derive_phase_b_coordinate_plan(predictions)
    maximum = int(
        protocol["phase_b"]["truth_coordinate_plan"][
            "maximum_total_new_direct_truth_coordinates"
        ]
    )
    coordinate_count = sum(len(row["coordinates"]) for row in coordinate_plan)
    if coordinate_count > maximum:
        raise execution.ExecutionError("Phase B coordinate plan exceeds protocol")
    epsilon = float(protocol["scope"]["target_error_hartree"])
    beta = float(protocol["cost_model"]["beta"])
    direct_by_condition: dict[str, list[dict[str, Any]]] = {}
    ground_audit = {}
    cache_counts = {"computed": 0, "reused": 0}
    for row in coordinate_plan:
        condition = str(row["condition"])
        system = systems[condition]
        exact_energy, exact_state, ground_residual = exact_ground_pair(system)
        ground_audit[condition] = {
            "energy_without_constant_hartree": exact_energy,
            "eigenpair_residual_2_norm": ground_residual,
            "ground_state_sha256": _array_sha256(exact_state),
        }
        rotations = phase_a._rotation_count(system, sequence)
        previous_vector: np.ndarray | None = None
        previous_shift: float | None = None
        points = []
        for coordinate in row["coordinates"]:
            point, previous_vector, previous_shift, reused = cached_direct_point(
                cache_root=output_dir / ".runtime/direct_cache",
                protocol_sha256=protocol_sha,
                prediction_sha256=prediction_sha,
                condition=condition,
                system=system,
                formula_sha256=formula_hash,
                sequence=sequence,
                rotations=rotations,
                exact_energy=exact_energy,
                exact_state=exact_state,
                time_value=float(coordinate["time_hartree_inverse"]),
                roles=coordinate["roles"],
                backend=backend,
                gpu_id=gpu_id,
                previous_vector=previous_vector,
                previous_unwrapped_shift=previous_shift,
                epsilon=epsilon,
                beta=beta,
            )
            cache_counts["reused" if reused else "computed"] += 1
            points.append(point)
        direct_by_condition[condition] = points
    numerical = validate_numerical_gates(direct_by_condition, protocol)
    flattened = [
        {"condition": condition, **point}
        for condition, rows in direct_by_condition.items()
        for point in rows
    ]
    _write_json(
        output_dir / "direct_points.json",
        {
            "schema": "second_study_safe_time_domain_direct_points_v1",
            "protocol_sha256": protocol_sha,
            "prediction_sha256": prediction_sha,
            "points": flattened,
        },
    )
    _write_csv(output_dir / "direct_points.csv", flattened)
    if not numerical["passed"]:
        decision = {
            "schema": "second_study_safe_time_domain_decision_v1",
            "status": "failed_numerical_validation",
            "created_at": execution.now(),
            "protocol_sha256": protocol_sha,
            "prediction_sha256": prediction_sha,
            "phase_a": phase_a_identity,
            "phase_a_runtime": phase_a_runtime_identity,
            "phase_b_output_identity": output_identity,
            "preflight": preflight,
            "environment": environment,
            "numerical_validation": numerical,
            "phase_b_coordinate_count": coordinate_count,
            "direct_cache_counts": cache_counts,
            "threshold_relaxed": False,
        }
        _write_json(output_dir / "decision.json", decision)
        _write_json(
            output_dir / "phase_b_audit.json",
            {
                **decision,
                "ground_state_audit": ground_audit,
                "wall_seconds": float(time.perf_counter() - started),
            },
        )
        _manifest(
            output_dir,
            [
                "direct_points.json",
                "direct_points.csv",
                "decision.json",
                "phase_b_audit.json",
            ],
        )
        return decision
    scoring = execution.score_phase_b(
        predictions=predictions,
        direct_points_by_condition=direct_by_condition,
        protocol=protocol,
    )
    status = (
        "complete_with_benefit"
        if scoring["benefit"]
        else "complete_no_benefit"
    )
    _write_json(output_dir / "strategy_scoring.json", scoring)
    _write_csv(output_dir / "strategy_scoring.csv", scoring["rows"])
    decision = {
        "schema": "second_study_safe_time_domain_decision_v1",
        "status": status,
        "created_at": execution.now(),
        "protocol_sha256": protocol_sha,
        "prediction_sha256": prediction_sha,
        "phase_a": phase_a_identity,
        "phase_a_runtime": phase_a_runtime_identity,
        "phase_b_output_identity": output_identity,
        "preflight": preflight,
        "environment": environment,
        "numerical_validation": numerical,
        "phase_b_coordinate_count": coordinate_count,
        "direct_cache_counts": cache_counts,
        "benefit_checks": scoring["benefit_checks"],
        "post_evaluation_retuning_performed": False,
    }
    _write_json(output_dir / "decision.json", decision)
    audit = {
        **decision,
        "ground_state_audit": ground_audit,
        "formula_sha256": formula_hash,
        "phase_b_wall_seconds": float(time.perf_counter() - started),
        "peak_cpu_rss_kib": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        ),
    }
    _write_json(output_dir / "phase_b_audit.json", audit)
    (output_dir / "COMPLETE").write_text(
        f"status={status}\n"
        f"protocol_sha256={protocol_sha}\n"
        f"prediction_sha256={prediction_sha}\n",
        encoding="utf-8",
    )
    _manifest(
        output_dir,
        [
            "direct_points.json",
            "direct_points.csv",
            "strategy_scoring.json",
            "strategy_scoring.csv",
            "decision.json",
            "phase_b_audit.json",
            "COMPLETE",
        ],
    )
    return decision


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--preflight-root", type=Path, required=True)
    parser.add_argument("--phase-a-root", type=Path, required=True)
    parser.add_argument("--phase-a-commit", required=True)
    parser.add_argument("--phase-a-artifact-relative", type=Path, required=True)
    parser.add_argument("--backend", choices=("gpu",), required=True)
    parser.add_argument("--gpu-id", type=int, default=0)
    parser.add_argument("--processes", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    decision = run(
        project_root=arguments.project_root,
        protocol_path=arguments.protocol,
        preflight_root=arguments.preflight_root,
        phase_a_root=arguments.phase_a_root,
        phase_a_commit=arguments.phase_a_commit,
        phase_a_artifact_relative=arguments.phase_a_artifact_relative,
        backend=arguments.backend,
        gpu_id=arguments.gpu_id,
        processes=arguments.processes,
        output_dir=arguments.output,
    )
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0 if str(decision["status"]).startswith("complete_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
