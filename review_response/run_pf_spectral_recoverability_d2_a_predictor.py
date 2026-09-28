#!/usr/bin/env python3
"""Run the truth-free predictor half of the fixed D2-A pilot."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
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

from review_response import pf_spectral_recoverability_d2 as d2
from review_response import second_study_safe_time_domain_execution as execution
from trotterlib.component_sector_pf import component_exponential
from trotterlib.pf_decomposition import iter_s2_sequence_steps


PLANNING_COMMIT = "d99715ef2c575a547394f2a5916abad27213d6fb"
EXPECTED_PYTHON = "/home/AbeHiromu/venvs/trotter-common/bin/python"
EXPECTED_HASHES = {
    "review_response/pf_spectral_recoverability_d2_protocol_draft.json":
        "fb1d112e13830924ee5bed058cea8a8a6196d01b303b96fff664676db98d83f5",
    "review_response/pf_spectral_recoverability_d2_planning_manifest.json":
        "efcd862712109f1bafc8c9e02f2f9a00ffcbd30b6f40826898758753b7e2f053",
    "review_response/pf_spectral_recoverability_d2_a_authorization.json":
        "7c0e7bfd3197d0c7d7d0fd37a09bcc92d00c861d6bbaf0400f405450858a1654",
    "review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json":
        "a95a9abf87f1d428c35d34ed13cbea8c2ff930e91a3e5eb3a2550fd5d1dd1051",
    "review_response/second_study_safe_time_domain_protocol.json":
        "a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b",
    "artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694/runtime_hash_inventory.json":
        "5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91",
}
HCL_CONDITIONS = ("HCl_full_eq_sto3g", "HCl_full_stretch150_sto3g")


class PredictorError(RuntimeError):
    """Raised when a frozen predictor gate fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return str(value)


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def git_output(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def verify_sources(root: Path) -> dict[str, Any]:
    head = git_output(root, "rev-parse", "HEAD")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PLANNING_COMMIT, head],
        cwd=root,
        check=False,
        capture_output=True,
    ).returncode == 0
    if not ancestry:
        raise PredictorError("D2 planning commit is not an ancestor of HEAD")
    rows = []
    for relative, expected in EXPECTED_HASHES.items():
        actual = sha256_file(root / relative)
        if actual != expected:
            raise PredictorError(f"fixed source hash mismatch: {relative}")
        rows.append({"path": relative, "sha256": actual})
    protocol = load_json(
        root / "review_response/pf_spectral_recoverability_d2_protocol_draft.json"
    )
    authorization = load_json(
        root / "review_response/pf_spectral_recoverability_d2_a_authorization.json"
    )
    if (
        protocol.get("status") != "d2_protocol_prepared_not_authorized"
        or authorization.get("status")
        != "d2_a_authorized_once_d2_b_not_authorized"
        or not authorization["authorization"].get("d2_a_predictor_authorized")
        or not authorization["not_authorized"].get("d2_b")
    ):
        raise PredictorError("D2 protocol/authorization boundary mismatch")
    return {
        "head": head,
        "planning_commit": PLANNING_COMMIT,
        "verified_source_count": len(rows),
        "verified_sources": rows,
        "protocol": protocol,
        "authorization": authorization,
    }


def validate_environment(processes: int) -> dict[str, Any]:
    if processes != 1:
        raise PredictorError("D2-A requires one process")
    threads = {
        name: os.environ.get(name)
        for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
    }
    if any(value != "1" for value in threads.values()):
        raise PredictorError(f"BLAS threads are not fixed to one: {threads}")
    if Path(sys.executable).resolve() != Path(EXPECTED_PYTHON).resolve():
        raise PredictorError(f"unexpected Python: {sys.executable}")
    if "cupy" in sys.modules:
        raise PredictorError("CuPy imported in CPU-only predictor")
    return {
        "python_executable": sys.executable,
        "python_realpath": str(Path(sys.executable).resolve()),
        "python_version": sys.version,
        "threads": threads,
        "processes": 1,
        "backend": "cpu",
        "gpu_query_count": 0,
        "gpu_allocation_count": 0,
        "gpu_kernel_count": 0,
    }


def verify_runtime_inventory(phase_a_root: Path) -> dict[str, Any]:
    inventory_path = phase_a_root / "runtime_hash_inventory.json"
    inventory = load_json(inventory_path)
    if (
        inventory.get("schema")
        != "second_study_safe_time_domain_phase_a_runtime_hash_inventory_v1"
        or sha256_file(inventory_path)
        != EXPECTED_HASHES[
            "artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694/runtime_hash_inventory.json"
        ]
    ):
        raise PredictorError("Phase A runtime inventory identity mismatch")
    runtime = (phase_a_root / ".runtime").resolve()
    if str(inventory.get("runtime_root")) != str(runtime):
        raise PredictorError("Phase A runtime absolute root changed")
    expected: dict[str, Mapping[str, Any]] = {}
    for row in inventory.get("files", []):
        relative = Path(str(row.get("path", "")))
        if (
            not str(relative)
            or relative.is_absolute()
            or ".." in relative.parts
            or relative.as_posix() in expected
        ):
            raise PredictorError("unsafe or duplicate runtime inventory path")
        expected[relative.as_posix()] = row
    actual = {
        path.relative_to(runtime).as_posix(): path
        for path in runtime.rglob("*")
        if path.is_file()
    }
    if set(actual) != set(expected):
        raise PredictorError("Phase A runtime file set changed")
    total = 0
    for relative, path in actual.items():
        row = expected[relative]
        size = path.stat().st_size
        total += size
        if (
            size != int(row["bytes"])
            or str(path.resolve()) != str(row["absolute_path"])
            or sha256_file(path) != str(row["sha256"])
        ):
            raise PredictorError(f"Phase A runtime mismatch: {relative}")
    if len(actual) != 56 or total != 113469289:
        raise PredictorError("Phase A runtime aggregate identity mismatch")
    return {
        "inventory_sha256": sha256_file(inventory_path),
        "runtime_root": str(runtime),
        "file_count": len(actual),
        "total_bytes": total,
        "all_files_byte_identical": True,
    }


@dataclass
class ActionCounter:
    pf_per_vector_actions: int = 0
    pf_block_calls: int = 0
    component_gate_materializations: int = 0
    sparse_state_multiplies: int = 0
    hamiltonian_matvecs: int = 0
    hamiltonian_exponential_actions: int = 0
    gate_cache_peak_bytes: int = 0
    basis_vector_peak_bytes: int = 0
    component_gate_materialization_seconds: float = 0.0
    sparse_state_multiply_seconds: float = 0.0
    hamiltonian_matvec_seconds: float = 0.0
    reorthogonalization_and_projected_solve_seconds: float = 0.0

    def payload(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PredictorSystemView:
    condition: str
    protocol_sha256: str
    hamiltonian_sha256: str
    hamiltonian: Any = field(repr=False)
    component_spectra: Sequence[Any] = field(repr=False)
    term_counts: Sequence[int]
    cisd_state: np.ndarray = field(repr=False)
    dimension: int

    @classmethod
    def from_fixed_cache(cls, raw: Mapping[str, Any]) -> "PredictorSystemView":
        required = {
            "schema", "condition", "protocol_sha256", "hamiltonian_sha256",
            "hamiltonian", "component_spectra", "term_counts", "cisd_state",
        }
        if not required.issubset(raw):
            raise PredictorError("fixed system cache lacks an allowlisted field")
        if raw["schema"] != "second_study_safe_time_domain_phase_a_system_v1":
            raise PredictorError("invalid Phase A system schema")
        state = np.asarray(raw["cisd_state"], dtype=np.complex128).reshape(-1).copy()
        state /= np.linalg.norm(state)
        hamiltonian = raw["hamiltonian"]
        if hamiltonian.shape != (state.size, state.size):
            raise PredictorError("Hamiltonian/state dimension mismatch")
        return cls(
            condition=str(raw["condition"]),
            protocol_sha256=str(raw["protocol_sha256"]),
            hamiltonian_sha256=str(raw["hamiltonian_sha256"]),
            hamiltonian=hamiltonian,
            component_spectra=tuple(raw["component_spectra"]),
            term_counts=tuple(int(value) for value in raw["term_counts"]),
            cisd_state=state,
            dimension=state.size,
        )


class CoordinateActions:
    """Coordinate-local cached actions with explicit resource counters."""

    def __init__(
        self,
        view: PredictorSystemView,
        sequence: Sequence[float],
        time_value: float,
        counter: ActionCounter,
    ) -> None:
        self.view = view
        self.steps = tuple(
            iter_s2_sequence_steps(len(view.component_spectra), sequence)
        )
        self.time_value = float(time_value)
        self.counter = counter
        self.gates: dict[tuple[int, float], Any] = {}

    @staticmethod
    def _sparse_bytes(matrix: Any) -> int:
        return int(matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes)

    def apply_pf(self, vector: np.ndarray) -> np.ndarray:
        self.counter.pf_per_vector_actions += 1
        self.counter.pf_block_calls += 1
        current = np.asarray(vector, dtype=np.complex128).reshape(-1).copy()
        for group_index, raw_weight in self.steps:
            key = (int(group_index), float(raw_weight))
            gate = self.gates.get(key)
            if gate is None:
                started = time.perf_counter()
                gate = component_exponential(
                    self.view.component_spectra[group_index],
                    self.time_value * float(raw_weight),
                )
                self.counter.component_gate_materialization_seconds += (
                    time.perf_counter() - started
                )
                self.counter.component_gate_materializations += 1
                self.gates[key] = gate
                self.counter.gate_cache_peak_bytes = max(
                    self.counter.gate_cache_peak_bytes,
                    sum(self._sparse_bytes(item) for item in self.gates.values()),
                )
            started = time.perf_counter()
            current = np.asarray(gate @ current).reshape(-1)
            self.counter.sparse_state_multiply_seconds += (
                time.perf_counter() - started
            )
            self.counter.sparse_state_multiplies += 1
        return current

    def apply_h(self, vector: np.ndarray) -> np.ndarray:
        started = time.perf_counter()
        result = np.asarray(self.view.hamiltonian @ vector).reshape(-1)
        self.counter.hamiltonian_matvec_seconds += time.perf_counter() - started
        self.counter.hamiltonian_matvecs += 1
        return result


def load_system_views(
    phase_a_root: Path,
    amendment: Mapping[str, Any],
) -> dict[str, PredictorSystemView]:
    expected_root = Path(amendment["phase_a_runtime"]["absolute_artifact_root"])
    if phase_a_root.resolve() != expected_root:
        raise PredictorError("Phase A root differs from the fixed amendment")
    manifest = load_json(phase_a_root / "sanitized_input_manifest.json")
    entries = {str(row["condition"]): row for row in manifest["entries"]}
    expected_hashes = amendment["phase_a_runtime"]["system_cache_sha256"]
    views: dict[str, PredictorSystemView] = {}
    for condition in HCL_CONDITIONS:
        row = entries[condition]
        path = phase_a_root / str(row["runtime_system_cache"])
        if (
            sha256_file(path) != expected_hashes[condition]
            or row["runtime_system_cache_sha256"] != expected_hashes[condition]
            or row.get("truth_path_exposed")
        ):
            raise PredictorError(f"{condition}: system cache identity mismatch")
        with path.open("rb") as stream:
            raw = pickle.load(stream)
        view = PredictorSystemView.from_fixed_cache(raw)
        del raw
        if (
            view.condition != condition
            or view.hamiltonian_sha256 != row["hamiltonian_sha256"]
            or view.protocol_sha256 != manifest["protocol_sha256"]
        ):
            raise PredictorError(f"{condition}: sanitized view identity mismatch")
        views[condition] = view
    return views


def rotation_count(view: PredictorSystemView, sequence: Sequence[float]) -> int:
    return int(sum(
        view.term_counts[index]
        for index, _ in iter_s2_sequence_steps(len(view.term_counts), sequence)
    ))


def build_manifest(output: Path, names: Sequence[str]) -> dict[str, Any]:
    rows = []
    for name in names:
        path = output / name
        rows.append({
            "path": name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {
        "schema": "pf_spectral_recoverability_d2_a_prediction_manifest_v1",
        "files": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--phase-a-cache-amendment", required=True, type=Path)
    parser.add_argument("--phase-a-root", required=True, type=Path)
    parser.add_argument("--processes", required=True, type=int)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    started = time.perf_counter()
    fixed_arguments = {
        "protocol": (
            args.protocol,
            root / "review_response/pf_spectral_recoverability_d2_protocol_draft.json",
        ),
        "authorization": (
            args.authorization,
            root / "review_response/pf_spectral_recoverability_d2_a_authorization.json",
        ),
        "phase-a-cache-amendment": (
            args.phase_a_cache_amendment,
            root / "review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json",
        ),
    }
    for label, (provided, expected) in fixed_arguments.items():
        resolved = provided if provided.is_absolute() else root / provided
        if resolved.resolve() != expected.resolve():
            raise PredictorError(f"caller supplied a non-fixed {label} path")
    source = verify_sources(root)
    environment = validate_environment(args.processes)
    protocol = source["protocol"]
    phase_a_root = args.phase_a_root.resolve()
    runtime_identity = verify_runtime_inventory(phase_a_root)
    amendment_path = (
        args.phase_a_cache_amendment
        if args.phase_a_cache_amendment.is_absolute()
        else root / args.phase_a_cache_amendment
    ).resolve()
    amendment = load_json(amendment_path)
    views = load_system_views(phase_a_root, amendment)
    output = (
        args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    ).resolve()
    if output.exists():
        raise PredictorError("prediction output must be new")
    output.mkdir(parents=True)
    second_protocol = load_json(
        root / "review_response/second_study_safe_time_domain_protocol.json"
    )
    sequence = execution.formula_sequence(second_protocol)
    coordinates = protocol["scope"]["coordinates"]
    predictions: list[dict[str, Any]] = []
    resource_rows: list[dict[str, Any]] = []
    previous_by_condition: dict[str, np.ndarray] = {}
    for coordinate in coordinates:
        condition = str(coordinate["condition"])
        view = views[condition]
        counter = ActionCounter()
        actions = CoordinateActions(
            view, sequence, float(coordinate["time_hartree_inverse"]), counter
        )
        coordinate_started = time.perf_counter()
        prediction, selected_vector = d2.analyze_coordinate(
            start=view.cisd_state,
            apply_u=actions.apply_pf,
            apply_h=actions.apply_h,
            time_value=float(coordinate["time_hartree_inverse"]),
            prefix_dimensions=protocol["scope"]["prefix_dimensions"],
            primary_dimension=int(protocol["scope"]["primary_dimension"]),
            previous_vector=previous_by_condition.get(condition),
            numerical_rules=protocol["numerical_rules"],
            epsilon_hartree=float(
                protocol["prediction_and_budget"]["epsilon_E_hartree"]
            ),
            beta=float(protocol["prediction_and_budget"]["qpe_beta"]),
            rotations_per_step=rotation_count(view, sequence),
        )
        if selected_vector is not None:
            previous_by_condition[condition] = selected_vector.copy()
            counter.basis_vector_peak_bytes = int(
                view.dimension
                * int(protocol["scope"]["primary_dimension"])
                * np.dtype(np.complex128).itemsize
                * 3
            )
        counter.reorthogonalization_and_projected_solve_seconds = float(
            time.perf_counter() - coordinate_started
            - counter.component_gate_materialization_seconds
            - counter.sparse_state_multiply_seconds
            - counter.hamiltonian_matvec_seconds
        )
        counts = counter.payload()
        if (
            counts["pf_per_vector_actions"] > 8
            or counts["hamiltonian_matvecs"] > 8
            or counts["hamiltonian_exponential_actions"] != 0
        ):
            raise PredictorError("per-coordinate action budget exceeded")
        predictions.append({
            "condition": condition,
            "time_hartree_inverse": float(coordinate["time_hartree_inverse"]),
            "time_hex": str(coordinate["time_hex"]),
            "relative_to_t_ana": float(coordinate["relative_to_t_ana"]),
            "hamiltonian_sha256": view.hamiltonian_sha256,
            **prediction,
            "resource_counts": counts,
        })
        resource_rows.append({
            "condition": condition,
            "time_hex": str(coordinate["time_hex"]),
            **counts,
        })
    if len(predictions) != 6:
        raise PredictorError("predictor did not produce exactly six coordinates")
    payload = {
        "schema": "pf_spectral_recoverability_d2_a_prediction_v1",
        "status": "d2_a_prediction_frozen_truth_not_opened",
        "head": source["head"],
        "planning_commit": PLANNING_COMMIT,
        "protocol_sha256": EXPECTED_HASHES[
            "review_response/pf_spectral_recoverability_d2_protocol_draft.json"
        ],
        "authorization_sha256": EXPECTED_HASHES[
            "review_response/pf_spectral_recoverability_d2_a_authorization.json"
        ],
        "truth_open_count": 0,
        "full_hamiltonian_eigendecomposition_count": 0,
        "full_pf_construction_count": 0,
        "full_pf_eigendecomposition_count": 0,
        "new_coordinate_count": 0,
        "gpu_query_count": 0,
        "gpu_allocation_count": 0,
        "gpu_kernel_count": 0,
        "predictions": predictions,
    }
    prediction_path = output / "prediction.json"
    atomic_json(prediction_path, payload)
    prediction_hash = sha256_file(prediction_path)
    (output / "prediction.sha256").write_text(
        f"{prediction_hash}  prediction.json\n", encoding="utf-8"
    )
    atomic_json(output / "source_audit.json", {
        **{key: value for key, value in source.items() if key not in {"protocol", "authorization"}},
        "forbidden_truth_import_count": 0,
    })
    atomic_json(output / "access_audit.json", {
        "schema": "pf_spectral_recoverability_d2_a_access_audit_v1",
        "truth_open_count": 0,
        "loaded_condition_count": len(views),
        "loaded_conditions": list(HCL_CONDITIONS),
        "raw_system_dropped_before_estimator": True,
        "forbidden_runtime_fields_exposed_to_estimator": [],
        "full_hamiltonian_eigendecomposition_count": 0,
        "full_pf_construction_count": 0,
        "full_pf_eigendecomposition_count": 0,
    })
    atomic_json(output / "resource_audit.json", {
        "schema": "pf_spectral_recoverability_d2_a_prediction_resources_v1",
        "environment": environment,
        "runtime_identity": runtime_identity,
        "coordinates": resource_rows,
        "wall_seconds": time.perf_counter() - started,
        "peak_cpu_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    })
    atomic_json(output / "PREDICTION_FROZEN.json", {
        "schema": "pf_spectral_recoverability_d2_a_prediction_frozen_v1",
        "prediction_sha256": prediction_hash,
        "prediction_file": "prediction.json",
        "truth_open_count_before_freeze": 0,
        "scoring_authorized_only_after_this_marker": True,
        "d2_b_authorized": False,
    })
    names = [
        "prediction.json", "prediction.sha256", "source_audit.json",
        "access_audit.json", "resource_audit.json", "PREDICTION_FROZEN.json",
    ]
    atomic_json(output / "manifest.json", build_manifest(output, names))
    print(json.dumps({
        "status": payload["status"],
        "prediction_sha256": prediction_hash,
        "coordinate_count": len(predictions),
        "truth_open_count": 0,
        "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
