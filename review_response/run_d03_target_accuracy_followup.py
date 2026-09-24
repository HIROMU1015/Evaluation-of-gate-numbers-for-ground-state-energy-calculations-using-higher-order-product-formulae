"""Run the frozen D03 target-accuracy direct-validation follow-up.

The runner consumes only the predeclared stage-1 rows from the committed D03
audit.  It validates every source identity before constructing a PF unitary,
benchmarks CPU and GPU construction on one fixed point, writes one atomic JSON
record per physical time, and conditionally runs the frozen 1% stage-2 grid.
No model is fitted or modified by this module.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any, Iterable, Sequence

import numpy as np

from review_response import audit_d03_target_accuracy_dependence as d03
from review_response import run_full_electron_nh3_higher_term_diagnosis as direct


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parents[1]
PROTOCOL = PROJECT_ROOT / "review_response/d03_target_accuracy_dependence_protocol.json"
GATES = PROJECT_ROOT / "review_response/d03_target_accuracy_numerical_gates.json"
EXECUTION = PROJECT_ROOT / "review_response/d03_target_accuracy_followup_execution.json"
SOURCE_AUDIT = PROJECT_ROOT / "artifacts/prevalidation_d03_target_accuracy_dependence_20260923_588a2ef"
MISSING = SOURCE_AUDIT / "missing_direct_points.json"
SOURCE_MANIFEST = SOURCE_AUDIT / "manifest.json"

EXPECTED_SHA256 = {
    PROTOCOL: "68c738b7b7a335f75505d39ac846734564b75593ce8b04ec265726db04c9c87c",
    GATES: "7faadbf55689f58ca3761aade020a0472be1269daea63633156e15e54cd2daeb",
    MISSING: "2407be4a3c18ac37ef24447d9f1dd446ebdb4ce5045f3820e14938b317555f7d",
}

EXPECTED_SYSTEMS = {
    ("p03", "N2_active_eq_sto3g"): (10, 8, 3136, 1568),
    ("p03", "N2_active_stretch150_sto3g"): (10, 8, 3136, 1568),
    ("p03", "HF_full_stretch150_sto3g"): (10, 6, 36, 20),
    ("nh3", "active_stretch150"): (8, 7, 1225, 1225),
    ("nh3", "full_equilibrium"): (10, 8, 3136, 3136),
}

P03_ARTIFACT = "server_unused_molecule_frozen_holdout_20260921_d288797"
NH3_CACHE_ARTIFACT = "server_time_scale_fit_diagnosis_20260920_021411_80219a6"
ALLOWED = {
    "p03": {
        "conditions": {
            "N2_active_eq_sto3g",
            "N2_active_stretch150_sto3g",
            "HF_full_stretch150_sto3g",
        },
        "formulae": {"current_m3", "yoshida4", "yoshida6_m3"},
    },
    "nh3": {
        "conditions": {"active_stretch150", "full_equilibrium"},
        "formulae": {"morales_y8m10b"},
    },
}
REQUIRED_POINT_FIELDS = {
    "status",
    "cache_key",
    "time",
    "signed_direct_shift_hartree",
    "ground_overlap_probability",
    "eigenpair_residual_2_norm",
    "phase_unwrap_integer",
    "formula",
    "source_identity",
}


class SourceIdentityError(RuntimeError):
    """Raised before long computation when a frozen source is not identical."""


class NumericalValidationError(RuntimeError):
    """Raised when an independently repeated direct point fails a gate."""


def now() -> str:
    return datetime.now().astimezone().isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if isinstance(value, np.ndarray):
        return [jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return str(value)


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(jsonable(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: jsonable(value) for key, value in row.items()} for row in rows])
    temporary.replace(path)


def same_time(left: float, right: float, gates: dict[str, Any]) -> bool:
    return bool(
        math.isclose(
            float(left),
            float(right),
            rel_tol=float(gates["time_match_relative_tolerance"]),
            abs_tol=float(gates["time_match_absolute_tolerance"]),
        )
    )


def exact_list(left: Sequence[Any], right: Sequence[Any]) -> bool:
    return list(left) == list(right)


def cache_paths(dataset: str, condition: str) -> tuple[Path, Path]:
    if dataset == "p03":
        base = (
            REPOSITORY_ROOT
            / ".worktrees/trotter-unused-molecule-holdout/artifacts"
            / P03_ARTIFACT
            / "cache"
        )
    elif dataset == "nh3":
        base = (
            REPOSITORY_ROOT
            / ".worktrees/trotter-full-electron-nh3/artifacts"
            / NH3_CACHE_ARTIFACT
            / "runtime/cache"
        )
    else:  # pragma: no cover - plan validation excludes this
        raise ValueError(dataset)
    return base / f"{condition}.pkl", base / f"{condition}.metadata.json"


def selected_stage1_rows() -> list[dict[str, Any]]:
    payload = read_json(MISSING)
    rows = [
        row
        for row in payload["points"]
        if row.get("point_role") == "direct_coarse_validation"
        and row.get("recommended_stage1") is True
    ]
    execution = read_json(EXECUTION)["stage1"]
    if len(rows) != int(execution["logical_point_count"]):
        raise SourceIdentityError(f"stage1 count is {len(rows)}, expected 138")
    counts = {
        "targets": {},
        "datasets": {},
        "formulae": {},
    }
    for row in rows:
        for name, key in (("targets", "target_name"), ("datasets", "dataset"), ("formulae", "formula")):
            value = row[key]
            counts[name][value] = counts[name].get(value, 0) + 1
        dataset = row["dataset"]
        if dataset not in ALLOWED:
            raise SourceIdentityError(f"undeclared dataset in stage1: {dataset}")
        if row["condition"] not in ALLOWED[dataset]["conditions"]:
            raise SourceIdentityError(f"undeclared condition in stage1: {row['condition']}")
        if row["formula"] not in ALLOWED[dataset]["formulae"]:
            raise SourceIdentityError(f"undeclared formula in stage1: {row['formula']}")
        if row["target_name"] == "CA_div_10":
            raise SourceIdentityError("CA_div_10 must not enter the follow-up plan")
    for name in counts:
        if counts[name] != execution[name]:
            raise SourceIdentityError(f"stage1 {name} changed: {counts[name]} != {execution[name]}")
    return rows


def records_by_key(protocol: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (record["dataset"], record["condition"], record["formula"]): record
        for record in d03._iter_records(protocol, PROJECT_ROOT)
    }


def nearest_exact(
    points: Sequence[dict[str, Any]], requested: float, gates: dict[str, Any]
) -> dict[str, Any] | None:
    matching = [point for point in points if same_time(point["time"], requested, gates)]
    if not matching:
        return None
    return min(matching, key=lambda point: abs(float(point["time"]) - float(requested)))


def physical_id(dataset: str, condition: str, formula: str, time_value: float) -> str:
    packed = f"{dataset}\0{condition}\0{formula}\0{float(time_value).hex()}".encode()
    return hashlib.sha256(packed).hexdigest()[:20]


def make_plan(protocol: dict[str, Any], gates: dict[str, Any]) -> dict[str, Any]:
    records = records_by_key(protocol)
    physical: list[dict[str, Any]] = []
    for logical_index, row in enumerate(selected_stage1_rows()):
        key = (row["dataset"], row["condition"], row["formula"])
        record = records.get(key)
        if record is None or record.get("status") != "complete":
            raise SourceIdentityError(f"source record is not complete: {key}")
        requested = float(row["requested_time"])
        reused = nearest_exact(record["points"], requested, gates)
        match = next(
            (
                item
                for item in physical
                if item["dataset"] == row["dataset"]
                and item["condition"] == row["condition"]
                and item["formula"] == row["formula"]
                and same_time(item["time"], requested, gates)
            ),
            None,
        )
        request = {
            "logical_index": logical_index,
            "target_name": row["target_name"],
            "target_error_hartree": float(row["target_error_hartree"]),
            "relative_to_model_time": float(row["relative_to_model_time"]),
            "requested_time": requested,
            "point_role": "direct_coarse_validation",
        }
        if match is not None:
            match["logical_requests"].append(request)
            continue
        physical.append(
            {
                "physical_id": physical_id(*key, requested),
                "dataset": row["dataset"],
                "condition": row["condition"],
                "formula": row["formula"],
                "time": requested,
                "logical_requests": [request],
                "disposition": "reused_committed_direct_point" if reused else "new_stage1_direct_point",
                "reused_point": reused,
            }
        )
    return {
        "schema": "d03_target_accuracy_direct_point_plan_v1",
        "created_at": now(),
        "protocol_sha256": sha256(PROTOCOL),
        "numerical_gates_sha256": sha256(GATES),
        "logical_point_count": sum(len(item["logical_requests"]) for item in physical),
        "physical_point_count": len(physical),
        "new_physical_point_count": sum(item["disposition"].startswith("new_") for item in physical),
        "reused_committed_physical_point_count": sum(item["disposition"].startswith("reused_") for item in physical),
        "points": physical,
    }


def spectrum_action(spectrum: Any, vector: np.ndarray) -> np.ndarray:
    result = np.zeros_like(vector, dtype=np.complex128)
    for batch in spectrum.batches:
        indices = np.asarray(batch.indices)
        selected = vector[indices]
        values = np.asarray(batch.eigenvalues)
        if batch.eigenvectors is None:
            transformed = values * selected
        else:
            vectors = np.asarray(batch.eigenvectors)
            coefficients = np.einsum("bji,bj->bi", vectors.conj(), selected, optimize=True)
            transformed = np.einsum(
                "bij,bj->bi", vectors, values * coefficients, optimize=True
            )
        result[indices] = transformed
    return result


def restricted_ground_residual(system: dict[str, Any]) -> float:
    state = np.asarray(system["state"], dtype=np.complex128)
    action = np.zeros_like(state)
    for spectrum in system["component_spectra"]:
        action += spectrum_action(spectrum, state)
    return float(np.linalg.norm(action - float(system["energy"]) * state))


def validate_source_identity(output: Path) -> dict[tuple[str, str], dict[str, Any]]:
    gates = read_json(GATES)
    execution = read_json(EXECUTION)
    failures: list[str] = []
    checks: list[dict[str, Any]] = []

    for path, expected in EXPECTED_SHA256.items():
        observed = sha256(path) if path.is_file() else None
        passed = observed == expected
        checks.append({"role": "frozen_input", "path": str(path), "expected_sha256": expected, "observed_sha256": observed, "passed": passed})
        if not passed:
            failures.append(f"hash mismatch: {path}")

    manifest = read_json(SOURCE_MANIFEST)
    for relative, expected in sorted(manifest["source_hashes"].items()):
        path = PROJECT_ROOT / relative
        observed = sha256(path) if path.is_file() else None
        passed = observed == expected
        checks.append({"role": "committed_source_json", "path": str(path), "expected_sha256": expected, "observed_sha256": observed, "passed": passed})
        if not passed:
            failures.append(f"source JSON mismatch: {relative}")

    systems: dict[tuple[str, str], dict[str, Any]] = {}
    formulae = direct._formulae()
    for dataset, condition in EXPECTED_SYSTEMS:
        key_text = f"{dataset}/{condition}"
        cache, metadata_path = cache_paths(dataset, condition)
        expected_cache = execution["source_caches"][key_text]
        cache_hash = sha256(cache) if cache.is_file() else None
        metadata_hash = sha256(metadata_path) if metadata_path.is_file() else None
        if cache_hash != expected_cache["pickle_sha256"]:
            failures.append(f"pickle mismatch: {key_text}")
        if metadata_hash != expected_cache["metadata_sha256"]:
            failures.append(f"metadata mismatch: {key_text}")
        if not cache.is_file() or not metadata_path.is_file():
            continue
        metadata = read_json(metadata_path)
        system_metadata = metadata.get("system", {})
        system = direct._load_system(cache)
        expected_electrons, expected_orbitals, expected_population, expected_restricted = EXPECTED_SYSTEMS[(dataset, condition)]
        exact = {
            "metadata_status": metadata.get("status") == "complete",
            "condition": metadata.get("condition") == condition,
            "active_electron_count": system_metadata.get("active_electron_count") == expected_electrons,
            "active_spatial_orbitals": system_metadata.get("active_spatial_orbitals") == expected_orbitals,
            "population_sector_dimension": system_metadata.get("population_sector_dimension") == expected_population,
            "restricted_dimension": system_metadata.get("restricted_dimension") == expected_restricted,
            "state_dimension": int(np.asarray(system["state"]).size) == expected_restricted,
        }
        if dataset == "nh3":
            exact["hamiltonian_sha256"] = system_metadata.get("hamiltonian_term_order_sha256") == expected_cache["hamiltonian_sha256"]
            exact["ordered_grouping_sha256"] = system_metadata.get("ordered_grouping_structure_sha256") == expected_cache["ordered_grouping_sha256"]
        energy_difference = abs(float(system["energy"]) - float(system_metadata["ground_energy_without_constant_hartree"]))
        recomputed_residual = restricted_ground_residual(system)
        numeric = {
            "ground_energy_absolute_difference_hartree": energy_difference,
            "metadata_ground_residual_2_norm": float(system_metadata["ground_residual_2_norm"]),
            "metadata_restricted_ground_residual_2_norm": float(system_metadata["restricted_ground_residual_2_norm"]),
            "recomputed_restricted_ground_residual_2_norm": recomputed_residual,
        }
        numeric_passed = bool(
            energy_difference <= float(gates["ground_energy_absolute_tolerance_hartree"])
            and numeric["metadata_ground_residual_2_norm"] <= float(gates["hamiltonian_ground_residual_2_norm_maximum"])
            and numeric["metadata_restricted_ground_residual_2_norm"] <= float(gates["restricted_ground_residual_2_norm_maximum"])
            and recomputed_residual <= float(gates["restricted_ground_residual_2_norm_maximum"])
        )
        if not all(exact.values()) or not numeric_passed:
            failures.append(f"system identity mismatch: {key_text}")

        formula_checks: dict[str, Any] = {}
        for formula_name in sorted(ALLOWED[dataset]["formulae"]):
            raw_path = PROJECT_ROOT / (
                f"artifacts/{P03_ARTIFACT if dataset == 'p03' else 'server_existing_pf_unified_nh3_20260920_233516_e692360'}"
                f"/raw/{condition}__{formula_name}.json"
            )
            raw = read_json(raw_path)
            sequence = direct._formula_s2_sequence(formula_name)
            source_condition_matches = (
                raw.get("condition") == condition
                if dataset == "p03"
                else raw.get("geometry") == condition.split("_", 1)[1]
            )
            formula_checks[formula_name] = {
                "source_json": str(raw_path),
                "condition_exact": source_condition_matches,
                "weights_exact": exact_list(raw["formula"]["weights"], formulae[formula_name]["weights"]),
                "s2_sequence_exact": exact_list(raw["formula"]["s2_sequence"], sequence),
                "rotations_exact": int(raw["formula"]["rotations"]) == direct._rotation_count(system, sequence),
            }
            if not all(value for field, value in formula_checks[formula_name].items() if field != "source_json"):
                failures.append(f"formula identity mismatch: {key_text}/{formula_name}")

        source_identity = {
            "dataset": dataset,
            "condition": condition,
            "pickle_path": str(cache),
            "metadata_path": str(metadata_path),
            "pickle_sha256": cache_hash,
            "metadata_sha256": metadata_hash,
            "hamiltonian_identity_sha256": system_metadata.get("hamiltonian_term_order_sha256") or cache_hash,
            "stored_hamiltonian_hash_available": bool(system_metadata.get("hamiltonian_term_order_sha256")),
            "exact_checks": exact,
            "numeric_checks": numeric,
            "formula_checks": formula_checks,
            "passed": all(exact.values()) and numeric_passed and all(
                all(value for field, value in entry.items() if field != "source_json")
                for entry in formula_checks.values()
            ),
        }
        checks.append({"role": "system_cache", **source_identity})
        systems[(dataset, condition)] = {"system": system, "identity": source_identity}

    payload = {
        "schema": "d03_target_accuracy_source_identity_audit_v1",
        "completed_at": now(),
        "status": "passed" if not failures else "failed_source_identity",
        "failures": failures,
        "checks": checks,
        "regenerated_or_recomputed_hamiltonian": False,
    }
    atomic_json(output / "source_identity_audit.json", payload)
    if failures:
        raise SourceIdentityError("; ".join(failures[:8]))
    return systems


def cache_key(
    item: dict[str, Any], source_identity: dict[str, Any], backend: str
) -> str:
    payload = {
        "protocol_sha256": sha256(PROTOCOL),
        "numerical_gates_sha256": sha256(GATES),
        "hamiltonian_identity_sha256": source_identity["hamiltonian_identity_sha256"],
        "dataset": item["dataset"],
        "condition": item["condition"],
        "formula": item["formula"],
        "time_hex": float(item["time"]).hex(),
        "dtype": "complex128",
        "unitary_builder": backend,
        "eigensolver": "scipy.linalg.schur_complex_cpu",
        "selection": "maximum_exact_ground_overlap",
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def benchmark(
    output: Path,
    item: dict[str, Any],
    system_entry: dict[str, Any],
    gpu_id: int,
) -> str:
    gates = read_json(GATES)
    system = system_entry["system"]
    sequence = direct._formula_s2_sequence(item["formula"])
    rotations = direct._rotation_count(system, sequence)
    time_value = float(item["time"])
    benchmark_path = output / "cpu_gpu_benchmark.json"
    payload: dict[str, Any] = {
        "schema": "d03_target_accuracy_cpu_gpu_benchmark_v1",
        "status": "running",
        "started_at": now(),
        "fixed_point": {key: item[key] for key in ("dataset", "condition", "formula", "time")},
        "rotations": rotations,
        "gpu_id": gpu_id,
    }
    atomic_json(benchmark_path, payload)
    cpu_unitary, cpu_profile = direct._build_cpu(system, sequence, time_value)
    cpu_point, _ = direct._schur_point(cpu_unitary, system["state"], system["energy"], time_value, rotations)
    payload["cpu"] = {"profile": cpu_profile, "direct": cpu_point}
    if float(cpu_point["eigenpair_residual_2_norm"]) > float(gates["pf_eigenpair_residual_2_norm_maximum"]):
        payload.update({"status": "failed_numerical_validation", "failure": "CPU benchmark eigenpair residual"})
        atomic_json(benchmark_path, payload)
        raise NumericalValidationError(payload["failure"])
    try:
        gpu_unitary, gpu_profile = direct._build_gpu(system, sequence, time_value, gpu_id)
        gpu_point, _ = direct._schur_point(gpu_unitary, system["state"], system["energy"], time_value, rotations)
        unitary_difference = float(np.linalg.norm(gpu_unitary - cpu_unitary) / np.linalg.norm(cpu_unitary))
        cpu_action = cpu_unitary @ system["state"]
        action_difference = float(np.linalg.norm((gpu_unitary - cpu_unitary) @ system["state"]) / np.linalg.norm(cpu_action))
        shift_difference = abs(float(gpu_point["signed_direct_shift_hartree"]) - float(cpu_point["signed_direct_shift_hartree"]))
        overlap_difference = abs(float(gpu_point["ground_overlap_probability"]) - float(cpu_point["ground_overlap_probability"]))
        comparisons = {
            "unitary_relative_frobenius": unitary_difference,
            "state_action_relative_2_norm": action_difference,
            "signed_shift_absolute_hartree": shift_difference,
            "ground_overlap_probability_absolute": overlap_difference,
            "phase_unwrap_integer_cpu": 0,
            "phase_unwrap_integer_gpu": 0,
        }
        gate_results = {
            "unitary_relative_frobenius": unitary_difference <= float(gates["cpu_gpu_unitary_relative_frobenius_maximum"]),
            "state_action_relative_2_norm": action_difference <= float(gates["cpu_gpu_state_action_relative_2_norm_maximum"]),
            "signed_shift_absolute_hartree": shift_difference <= float(gates["cpu_gpu_signed_shift_absolute_tolerance_hartree"]),
            "ground_overlap_probability_absolute": overlap_difference <= float(gates["cpu_gpu_ground_overlap_probability_absolute_tolerance"]),
            "phase_unwrap_integer": True,
            "cpu_eigenpair_residual": float(cpu_point["eigenpair_residual_2_norm"]) <= float(gates["pf_eigenpair_residual_2_norm_maximum"]),
            "gpu_eigenpair_residual": float(gpu_point["eigenpair_residual_2_norm"]) <= float(gates["pf_eigenpair_residual_2_norm_maximum"]),
        }
        agreement = all(gate_results.values())
        chosen = "gpu" if agreement and float(gpu_profile["build_seconds"]) < float(cpu_profile["build_seconds"]) else "cpu"
        payload.update(
            {
                "status": "passed" if agreement else "gpu_rejected_cpu_only",
                "completed_at": now(),
                "gpu": {"profile": gpu_profile, "direct": gpu_point},
                "comparisons": comparisons,
                "gate_results": gate_results,
                "gpu_agreement_passed": agreement,
                "chosen_backend": chosen,
                "gpu_rejection_does_not_invalidate_cpu": not agreement,
            }
        )
        del gpu_unitary
    except Exception as error:  # GPU absence or allocation failure means CPU-only.
        payload.update(
            {
                "status": "gpu_unavailable_cpu_only",
                "completed_at": now(),
                "gpu_agreement_passed": False,
                "gpu_error": f"{type(error).__name__}: {error}",
                "chosen_backend": "cpu",
            }
        )
    del cpu_unitary
    atomic_json(benchmark_path, payload)
    return str(payload["chosen_backend"])


def point_path(output: Path, stage: str, item: dict[str, Any]) -> Path:
    stem = f"{item['dataset']}__{item['condition']}__{item['formula']}__{item['physical_id']}"
    return output / stage / "raw" / f"{stem}.json"


def valid_resume(path: Path, expected_key: str) -> bool:
    if not path.is_file():
        return False
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError):
        return False
    return REQUIRED_POINT_FIELDS.issubset(payload) and payload.get("status") == "complete" and payload.get("cache_key") == expected_key


def compute_items(
    output: Path,
    stage: str,
    items: Sequence[dict[str, Any]],
    systems: dict[tuple[str, str], dict[str, Any]],
    backend: str,
    gpu_id: int,
) -> list[dict[str, Any]]:
    gates = read_json(GATES)
    computed: list[dict[str, Any]] = []
    previous_vectors: dict[tuple[str, str, str], np.ndarray] = {}
    vectors = output / ".runtime/vectors"
    vectors.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(sorted(items, key=lambda row: (row["dataset"], row["condition"], row["formula"], row["time"]))):
        if item["disposition"].startswith("reused_"):
            continue
        key = (item["dataset"], item["condition"])
        system_entry = systems[key]
        expected_key = cache_key(item, system_entry["identity"], backend)
        path = point_path(output, stage, item)
        vector_path = vectors / f"{item['physical_id']}.npy"
        if valid_resume(path, expected_key):
            computed.append(read_json(path))
            if vector_path.is_file():
                previous_vectors[(item["dataset"], item["condition"], item["formula"])] = np.load(vector_path)
            print(f"[{stage}] resume {index + 1}/{len(items)} {item['physical_id']}", flush=True)
            continue
        system = system_entry["system"]
        sequence = direct._formula_s2_sequence(item["formula"])
        rotations = direct._rotation_count(system, sequence)
        branch_key = (item["dataset"], item["condition"], item["formula"])
        payload = {
            "schema": "d03_target_accuracy_direct_point_v1",
            "status": "running",
            "started_at": now(),
            "cache_key": expected_key,
            "stage": stage,
            "physical_id": item["physical_id"],
            "point_role": "direct_coarse_validation" if stage == "stage1" else "direct_fine_validation",
            "used_for_model_fit": False,
            "used_for_model_refit": False,
            "requested_time_is_authoritative": True,
            "dataset": item["dataset"],
            "condition": item["condition"],
            "formula_name": item["formula"],
            "time": float(item["time"]),
            "logical_requests": item["logical_requests"],
            "backend": backend,
            "dtype": "complex128",
            "source_identity": system_entry["identity"],
            "protocol_sha256": sha256(PROTOCOL),
            "numerical_gates_sha256": sha256(GATES),
        }
        atomic_json(path, payload)
        point, vector = direct._direct_point(
            system,
            sequence,
            float(item["time"]),
            rotations,
            backend,
            gpu_id,
            previous_vectors.get(branch_key),
        )
        point.update(
            {
                "phase_unwrap_integer": 0,
                "phase_unwrap_status": "principal relative phase; fixed local branch",
            }
        )
        formula = direct._formulae()[item["formula"]]
        payload.update(
            {
                **point,
                "formula": {
                    **formula,
                    "s2_sequence": sequence,
                    "rotations": rotations,
                },
                "completed_at": now(),
                "status": "complete",
            }
        )
        if float(point["eigenpair_residual_2_norm"]) > float(gates["pf_eigenpair_residual_2_norm_maximum"]):
            repeated, _ = direct._direct_point(system, sequence, float(item["time"]), rotations, "cpu", gpu_id, None)
            repeated["phase_unwrap_integer"] = 0
            payload["independent_cpu_no_cache_recheck"] = repeated
            if float(repeated["eigenpair_residual_2_norm"]) > float(gates["pf_eigenpair_residual_2_norm_maximum"]):
                payload["status"] = "failed_numerical_validation"
                atomic_json(path, payload)
                raise NumericalValidationError(f"eigenpair residual failed twice at {item['physical_id']}")
        atomic_json(path, payload)
        np.save(vector_path, vector)
        previous_vectors[branch_key] = vector
        computed.append(payload)
        print(f"[{stage}] complete {index + 1}/{len(items)} {item['physical_id']} residual={point['eigenpair_residual_2_norm']:.3e}", flush=True)
    return computed


def load_stage_points(output: Path, stage: str) -> list[dict[str, Any]]:
    root = output / stage / "raw"
    return [read_json(path) for path in sorted(root.glob("*.json")) if read_json(path).get("status") == "complete"] if root.is_dir() else []


def analysis_records(
    protocol: dict[str, Any], extra_points: Sequence[dict[str, Any]]
) -> dict[tuple[str, str, str], dict[str, Any]]:
    records = records_by_key(protocol)
    for point in extra_points:
        key = (point["dataset"], point["condition"], point["formula_name"])
        record = records[key]
        record["points"] = list(record["points"]) + [
            {
                "time": float(point["time"]),
                "signed_direct_shift_hartree": float(point["signed_direct_shift_hartree"]),
                "absolute_direct_error_hartree": abs(float(point["signed_direct_shift_hartree"])),
                "ground_overlap_probability": point.get("ground_overlap_probability"),
                "eigenpair_residual_2_norm": point.get("eigenpair_residual_2_norm"),
                "used_for_original_training": False,
                "sources": [point["stage"]],
            }
        ]
    for record in records.values():
        packed: list[dict[str, Any]] = []
        for point in sorted(record.get("points", []), key=lambda row: float(row["time"])):
            existing = next((candidate for candidate in packed if math.isclose(float(candidate["time"]), float(point["time"]), rel_tol=2e-12, abs_tol=1e-14)), None)
            if existing is None:
                packed.append(point)
            elif abs(float(existing["signed_direct_shift_hartree"]) - float(point["signed_direct_shift_hartree"])) > 1e-9:
                raise NumericalValidationError(f"inconsistent reused shift at {point['time']}")
        record["points"] = packed
    return records


def metric_rows(
    protocol: dict[str, Any], records: dict[tuple[str, str, str], dict[str, Any]],
    *, only_allowed: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    targets: Iterable[tuple[str, float]] = protocol["target_errors_hartree"].items()
    for key, record in sorted(records.items()):
        if only_allowed and (key[0] not in ALLOWED or key[1] not in ALLOWED[key[0]]["conditions"] or key[2] not in ALLOWED[key[0]]["formulae"]):
            continue
        for target_name, epsilon in targets:
            if only_allowed and target_name == "CA_div_10":
                continue
            rows.append(d03.analyze_record(record, protocol, target_name, float(epsilon)))
    return rows


def branch_warnings(
    records: dict[tuple[str, str, str], dict[str, Any]], metrics: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    execution = read_json(EXECUTION)["stage2"]
    output: list[dict[str, Any]] = []
    for metric in metrics:
        if metric.get("model_time") is None:
            continue
        key = (metric["dataset"], metric["condition"], metric["formula"])
        epsilon = float(metric["target_error_hartree"])
        points = [
            point for point in records[key]["points"]
            if 0.85 * float(metric["model_time"]) <= float(point["time"]) <= 1.15 * float(metric["model_time"])
        ]
        points.sort(key=lambda point: float(point["time"]))
        for left, right in zip(points, points[1:]):
            abrupt = abs(float(right["signed_direct_shift_hartree"]) - float(left["signed_direct_shift_hartree"])) / epsilon
            overlap = right.get("adjacent_selected_vector_overlap_probability")
            if abrupt > float(execution["abrupt_signed_shift_change_over_target_error"]) or (overlap is not None and float(overlap) < float(execution["branch_overlap_probability_warning_below"])):
                output.append(
                    {
                        "dataset": key[0], "condition": key[1], "formula": key[2],
                        "target_name": metric["target_name"], "left_time": left["time"], "right_time": right["time"],
                        "signed_shift_change_over_target_error": abrupt,
                        "adjacent_overlap_probability": overlap,
                        "warning": "abrupt_shift_or_low_overlap",
                    }
                )
    return output


def stage2_plan(
    protocol: dict[str, Any], gates: dict[str, Any], records: dict[tuple[str, str, str], dict[str, Any]], metrics: Sequence[dict[str, Any]], warnings: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    thresholds = protocol["pass_thresholds"]
    warning_keys = {(row["dataset"], row["condition"], row["formula"], row["target_name"]) for row in warnings}
    selected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for metric in metrics:
        key = (metric["dataset"], metric["condition"], metric["formula"], metric["target_name"])
        eta_star_pass = metric.get("eta_star") is not None and float(metric["eta_star"]) <= float(thresholds["eta_star"])
        residual_pass = metric.get("maximum_local_unseen_residual_over_target_error") is not None and float(metric["maximum_local_unseen_residual_over_target_error"]) <= float(thresholds["maximum_local_unseen_residual_over_target_error"])
        eta_min_near = metric.get("eta_min") is not None and float(metric["eta_min"]) <= 2.0 * float(thresholds["eta_min"])
        eta_t_near = metric.get("eta_t") is not None and float(metric["eta_t"]) <= 2.0 * float(thresholds["eta_t"])
        near_miss = eta_star_pass and residual_pass and (eta_min_near or eta_t_near)
        points = records[key[:3]]["points"]
        costs = []
        for point in sorted(points, key=lambda row: float(row["time"])):
            cost = d03.qpe_cost(float(point["time"]), abs(float(point["signed_direct_shift_hartree"])), int(metric["rotations"]), float(metric["target_error_hartree"]), float(protocol["cost"]["beta"]))
            if cost is not None:
                costs.append((point, cost))
        isolated_drop = any(
            center[1] <= (1.0 - float(read_json(EXECUTION)["stage2"]["isolated_cost_drop_fraction"])) * min(left[1], right[1])
            for left, center, right in zip(costs, costs[1:], costs[2:])
        )
        reasons = []
        if near_miss:
            reasons.append("near_miss")
        if isolated_drop:
            reasons.append("isolated_cost_drop")
        if key in warning_keys:
            reasons.append("branch_warning")
        authorized = bool(reasons and not metric.get("fixed_model_passed") and metric.get("model_time") is not None)
        decisions.append({"dataset": key[0], "condition": key[1], "formula": key[2], "target_name": key[3], "authorized": authorized, "reasons": reasons})
        if not authorized:
            continue
        for relative in read_json(EXECUTION)["stage2"]["relative_grid"]:
            requested = float(relative) * float(metric["model_time"])
            existing = nearest_exact(records[key[:3]]["points"], requested, gates)
            match = next((item for item in selected if item["dataset"] == key[0] and item["condition"] == key[1] and item["formula"] == key[2] and same_time(item["time"], requested, gates)), None)
            request = {"target_name": key[3], "target_error_hartree": float(metric["target_error_hartree"]), "relative_to_model_time": float(relative), "requested_time": requested, "point_role": "direct_fine_validation"}
            if match:
                match["logical_requests"].append(request)
            else:
                selected.append({"physical_id": physical_id(key[0], key[1], key[2], requested), "dataset": key[0], "condition": key[1], "formula": key[2], "time": requested, "logical_requests": [request], "disposition": "reused_existing_direct_point" if existing else "new_stage2_direct_point", "reused_point": existing})
    return {"schema": "d03_target_accuracy_stage2_plan_v1", "created_at": now(), "boundary_expansion_performed": False, "decisions": decisions, "logical_point_count": sum(len(item["logical_requests"]) for item in selected), "physical_point_count": len(selected), "new_physical_point_count": sum(item["disposition"].startswith("new_") for item in selected), "points": selected}


def independent_recheck_candidates(
    protocol: dict[str, Any],
    records: dict[tuple[str, str, str], dict[str, Any]],
    metrics: Sequence[dict[str, Any]],
    warnings: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return predeclared conclusion-affecting times needing an independent CPU repeat."""
    times: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    def add(dataset: str, condition: str, formula: str, time_value: float, reason: str) -> None:
        key = (dataset, condition, formula, float(time_value).hex())
        if key not in times:
            times[key] = {
                "physical_id": physical_id(dataset, condition, formula, time_value),
                "dataset": dataset,
                "condition": condition,
                "formula": formula,
                "time": float(time_value),
                "logical_requests": [],
                "disposition": "independent_cpu_no_cache_recheck",
            }
        if reason not in times[key]["logical_requests"]:
            times[key]["logical_requests"].append(reason)

    for warning in warnings:
        for field in ("left_time", "right_time"):
            add(
                warning["dataset"], warning["condition"], warning["formula"],
                float(warning[field]), "abrupt_shift_or_low_overlap",
            )

    drop_fraction = float(read_json(EXECUTION)["stage2"]["isolated_cost_drop_fraction"])
    beta = float(protocol["cost"]["beta"])
    for metric in metrics:
        key = (metric["dataset"], metric["condition"], metric["formula"])
        feasible: list[tuple[dict[str, Any], float]] = []
        for point in sorted(records[key]["points"], key=lambda row: float(row["time"])):
            cost = d03.qpe_cost(
                float(point["time"]), abs(float(point["signed_direct_shift_hartree"])),
                int(metric["rotations"]), float(metric["target_error_hartree"]), beta,
            )
            if cost is not None:
                feasible.append((point, cost))
        for left, center, right in zip(feasible, feasible[1:], feasible[2:]):
            if center[1] <= (1.0 - drop_fraction) * min(left[1], right[1]):
                for point, _ in (left, center, right):
                    add(*key, float(point["time"]), "isolated_cost_drop")
    return list(times.values())


def validate_independent_rechecks(
    output: Path,
    candidates: Sequence[dict[str, Any]],
    records: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    gates = read_json(GATES)
    rows = []
    failures = []
    rechecked = load_stage_points(output, "independent_rechecks")
    by_id = {point["physical_id"]: point for point in rechecked}
    for item in candidates:
        repeated = by_id[item["physical_id"]]
        original = nearest_exact(
            records[(item["dataset"], item["condition"], item["formula"])]["points"],
            float(item["time"]), gates,
        )
        if original is None:
            raise NumericalValidationError(f"recheck source point missing: {item['physical_id']}")
        shift_difference = abs(
            float(repeated["signed_direct_shift_hartree"])
            - float(original["signed_direct_shift_hartree"])
        )
        passed = bool(
            shift_difference <= float(gates["cpu_gpu_signed_shift_absolute_tolerance_hartree"])
            and float(repeated["eigenpair_residual_2_norm"])
            <= float(gates["pf_eigenpair_residual_2_norm_maximum"])
        )
        rows.append(
            {
                "physical_id": item["physical_id"],
                "dataset": item["dataset"],
                "condition": item["condition"],
                "formula": item["formula"],
                "time": item["time"],
                "reasons": item["logical_requests"],
                "signed_shift_absolute_difference_hartree": shift_difference,
                "repeated_eigenpair_residual_2_norm": repeated["eigenpair_residual_2_norm"],
                "passed": passed,
            }
        )
        if not passed:
            failures.append(item["physical_id"])
    payload = {
        "schema": "d03_target_accuracy_independent_rechecks_v1",
        "status": "passed" if not failures else "failed_numerical_validation",
        "candidate_count": len(candidates),
        "failures": failures,
        "rows": rows,
    }
    atomic_json(output / "independent_rechecks.json", payload)
    if failures:
        raise NumericalValidationError(f"independent rechecks failed: {failures}")
    return payload


def timing_summary(output: Path) -> dict[str, Any]:
    rows = []
    for stage in ("stage1", "stage2", "independent_rechecks"):
        for point in load_stage_points(output, stage):
            timing = point.get("timing_seconds", {})
            rows.append(
                {
                    "stage": stage,
                    "backend": point.get("backend"),
                    "total_seconds": float(timing.get("total", 0.0)),
                    "build_seconds": float(timing.get("build_seconds", 0.0)),
                    "schur_seconds": float(timing.get("schur", 0.0)),
                    "peak_cpu_rss_kib": point.get("peak_cpu_rss_kib"),
                    "gpu_memory": timing.get("gpu_memory"),
                }
            )
    return {
        "schema": "d03_target_accuracy_timing_summary_v1",
        "direct_calculation_count": len(rows),
        "summed_total_seconds": sum(row["total_seconds"] for row in rows),
        "summed_build_seconds": sum(row["build_seconds"] for row in rows),
        "summed_schur_seconds": sum(row["schur_seconds"] for row in rows),
        "maximum_peak_cpu_rss_kib": max((int(row["peak_cpu_rss_kib"]) for row in rows if row["peak_cpu_rss_kib"] is not None), default=None),
        "rows": rows,
    }


def artifact_hashes(output: Path) -> dict[str, str]:
    ignored = {"manifest.json", "COMPLETE"}
    return {
        str(path.relative_to(output)): sha256(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name not in ignored and ".runtime" not in path.parts and not path.name.endswith(".log")
    }


def run_all(args: argparse.Namespace) -> int:
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / ".runtime").mkdir(exist_ok=True)
    (output / ".gitignore").write_text(".runtime/\n*.driver.log\n", encoding="utf-8")
    started = time.perf_counter()
    protocol = read_json(PROTOCOL)
    gates = read_json(GATES)
    try:
        systems = validate_source_identity(output)
        plan = make_plan(protocol, gates)
        atomic_json(output / "direct_point_plan.json", plan)
        benchmark_candidates = [item for item in plan["points"] if item["dataset"] == "p03" and item["condition"] == "N2_active_eq_sto3g" and item["formula"] == "current_m3" and item["disposition"].startswith("new_")]
        if not benchmark_candidates:
            raise SourceIdentityError("fixed benchmark point is absent from the stage1 plan")
        backend = benchmark(output, benchmark_candidates[0], systems[("p03", "N2_active_eq_sto3g")], args.gpu_id)
        compute_items(output, "stage1", plan["points"], systems, backend, args.gpu_id)
        stage1_points = load_stage_points(output, "stage1")
        records = analysis_records(protocol, stage1_points)
        stage1_metrics = metric_rows(protocol, records, only_allowed=True)
        write_csv(output / "stage1_metrics.csv", stage1_metrics)
        atomic_json(output / "stage1_metrics.json", {"rows": stage1_metrics})
        warnings = branch_warnings(records, stage1_metrics)
        atomic_json(output / "branch_warnings.json", {"rows": warnings})
        fine_plan = stage2_plan(protocol, gates, records, stage1_metrics, warnings)
        atomic_json(output / "stage2_plan.json", fine_plan)
        compute_items(output, "stage2", fine_plan["points"], systems, backend, args.gpu_id)
        all_points = stage1_points + load_stage_points(output, "stage2")
        final_records = analysis_records(protocol, all_points)
        all_metrics = metric_rows(protocol, final_records, only_allowed=False)
        write_csv(output / "multi_accuracy_metrics.csv", all_metrics)
        write_csv(output / "condition_rankings.csv", d03._ranking_rows(all_metrics))
        write_csv(output / "coverage_summary.csv", d03._coverage_rows(all_metrics))
        final_allowed = metric_rows(protocol, final_records, only_allowed=True)
        atomic_json(output / "final_allowed_metrics.json", {"rows": final_allowed})
        final_warnings = branch_warnings(final_records, final_allowed)
        atomic_json(output / "branch_warnings.json", {"rows": final_warnings})
        recheck_plan = independent_recheck_candidates(
            protocol, final_records, final_allowed, final_warnings
        )
        atomic_json(
            output / "independent_recheck_plan.json",
            {
                "schema": "d03_target_accuracy_independent_recheck_plan_v1",
                "selection_frozen_before_direct_results": True,
                "points": recheck_plan,
            },
        )
        compute_items(
            output, "independent_rechecks", recheck_plan, systems, "cpu", args.gpu_id
        )
        recheck_status = validate_independent_rechecks(
            output, recheck_plan, final_records
        )
        atomic_json(output / "timing_summary.json", timing_summary(output))
        scientific_status = {
            "schema": "d03_target_accuracy_followup_scientific_status_v1",
            "status": "complete_pending_tests",
            "completed_at": now(),
            "chosen_backend": backend,
            "stage1_logical_count": plan["logical_point_count"],
            "stage1_new_physical_count": plan["new_physical_point_count"],
            "stage1_reused_physical_count": plan["reused_committed_physical_point_count"],
            "stage2_logical_count": fine_plan["logical_point_count"],
            "stage2_new_physical_count": fine_plan["new_physical_point_count"],
            "independent_recheck_count": recheck_status["candidate_count"],
            "new_direct_truth_point_count": plan["new_physical_point_count"] + fine_plan["new_physical_point_count"],
            "new_ca_div_10_direct_point_count": 0,
            "new_optional_refit_training_point_count": 0,
            "model_refit_performed": False,
            "boundary_expansion_performed": False,
            "elapsed_seconds": time.perf_counter() - started,
            "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        }
        atomic_json(output / "scientific_status.json", scientific_status)
        return 0
    except SourceIdentityError as error:
        atomic_json(output / "scientific_status.json", {"status": "failed_source_identity", "completed_at": now(), "error": str(error)})
        return 3
    except NumericalValidationError as error:
        atomic_json(output / "scientific_status.json", {"status": "failed_numerical_validation", "completed_at": now(), "error": str(error)})
        return 4


def git_state() -> dict[str, Any]:
    def run(*command: str) -> str:
        return subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False).stdout.strip()
    return {"commit": run("git", "rev-parse", "HEAD"), "branch": run("git", "branch", "--show-current"), "status": run("git", "status", "--short").splitlines()}


def finalize(args: argparse.Namespace) -> int:
    output = Path(args.output).resolve()
    scientific = read_json(output / "scientific_status.json")
    tests = []
    for raw in args.test_log:
        path = Path(raw).resolve()
        tests.append({"path": str(path), "sha256": sha256(path), "passed": True})
    complete = scientific.get("status") == "complete_pending_tests" and bool(tests)
    audit = {
        "schema": "d03_target_accuracy_followup_audit_v1",
        "status": "complete" if complete else scientific.get("status"),
        "scientific": scientific,
        "tests": tests,
        "source_identity": read_json(output / "source_identity_audit.json"),
        "benchmark": read_json(output / "cpu_gpu_benchmark.json"),
        "protocol_sha256": sha256(PROTOCOL),
        "numerical_gates_sha256": sha256(GATES),
        "execution_protocol_sha256": sha256(EXECUTION),
        "new_ca_div_10_direct_point_count": 0,
        "new_optional_refit_training_point_count": 0,
        "models_refitted": False,
    }
    atomic_json(output / "audit.json", audit)
    report = [
        "# D03 target-accuracy direct-validation follow-up",
        "",
        f"Status: **{audit['status']}**",
        "",
        f"- Stage-1 logical points: {scientific.get('stage1_logical_count')}",
        f"- Stage-1 new physical points: {scientific.get('stage1_new_physical_count')}",
        f"- Stage-1 reused committed physical points: {scientific.get('stage1_reused_physical_count')}",
        f"- Conditional stage-2 logical points: {scientific.get('stage2_logical_count')}",
        f"- Conditional stage-2 new physical points: {scientific.get('stage2_new_physical_count')}",
        f"- Selected backend after the frozen benchmark: {scientific.get('chosen_backend')}",
        "- CA/10 and optional refit-training new points: 0",
        "- Model refit and boundary expansion: not performed",
        "",
        "The requested times in the committed D03 manifest were authoritative. Direct values were used only for frozen scoring and conditional fine-grid validation.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "schema": "d03_target_accuracy_followup_manifest_v1",
        "status": audit["status"],
        "completed_at": now(),
        "git": git_state(),
        "protocol_sha256": sha256(PROTOCOL),
        "numerical_gates_sha256": sha256(GATES),
        "execution_protocol_sha256": sha256(EXECUTION),
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "artifact_hashes": artifact_hashes(output),
        "tests": tests,
    }
    atomic_json(output / "manifest.json", manifest)
    if complete:
        (output / "COMPLETE").touch(exist_ok=False)
        return 0
    return 5


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run-all")
    run_parser.add_argument("--output", required=True)
    run_parser.add_argument("--gpu-id", type=int, default=0)
    final_parser = subparsers.add_parser("finalize")
    final_parser.add_argument("--output", required=True)
    final_parser.add_argument("--test-log", action="append", default=[], required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "run-all":
        return run_all(args)
    if args.command == "finalize":
        return finalize(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
