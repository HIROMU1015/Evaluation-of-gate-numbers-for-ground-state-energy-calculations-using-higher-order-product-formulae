"""Exact m5 PF eigenphases using a compact symmetry/component representation.

Preparation discovers an exact diagonal-Z symmetry inside the fixed alpha/beta
population sector and diagonalizes each grouped Hamiltonian only within its
small connected components.  A direct-time worker constructs the resulting
dense PF unitary on one GPU, transfers that single matrix to CPU, and obtains
the complete eigensystem with a complex Schur decomposition.

This is an exact direct solver (up to floating-point roundoff), not a projected
or moment approximation.  It remains cubic in the final symmetry-block size.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import importlib.metadata
import json
import math
import os
from pathlib import Path
import pickle
import platform
import resource
import subprocess
import time
import traceback
from typing import Any, Sequence

import numpy as np
from scipy.linalg import schur

from benchmark_direct_pf_solvers import prepare_system
from benchmark_sparse_pf_smoke import GpuMemoryMonitor, _gpu_info
from trotterlib.component_sector_pf import (
    ComponentSpectrum,
    component_exponential,
    find_balanced_z2_symmetry,
    fixed_population_basis,
    prepare_component_spectra,
)
from trotterlib.config import BETA, DECOMPO_NUM, TARGET_ERROR
from trotterlib.product_formula import _get_s2_sequence

# This import preloads the CUDA wheel libraries required by both Aer and CuPy.
from trotterlib import qiskit_time_evolution_grouping as _cuda_preload  # noqa: F401,E402


LABEL = "4th(m5_best)"


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _git_state() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True,
        capture_output=True, check=False,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, text=True,
        capture_output=True, check=False,
    ).stdout.splitlines()
    return {"commit": commit or None, "dirty": bool(status), "status": status}


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _cost(time_value: float, error: float, rotations: int) -> float | None:
    if not math.isfinite(error) or error >= TARGET_ERROR:
        return None
    return float(BETA * rotations / (time_value * (TARGET_ERROR - error)))


def prepare(args: argparse.Namespace) -> int:
    args.output_dir.mkdir(parents=True, exist_ok=False)
    metadata: dict[str, Any] = {
        "status": "running",
        "started_at": _now(),
        "git": _git_state(),
        "configuration": {
            "h_chain": int(args.h_chain),
            "label": LABEL,
            "preparation_processes": int(args.processes),
        },
    }
    _atomic_json(args.output_dir / "system.json", metadata)
    try:
        started = time.perf_counter()
        source = prepare_system(int(args.h_chain), dense=False)
        groups = source["groups"]
        num_qubits = int(source["num_qubits"])
        full_state = np.asarray(source["full_ground_state"], dtype=np.complex128)
        population_basis, population = fixed_population_basis(num_qubits, full_state)
        population_state = full_state[population_basis].copy()
        population_state /= np.linalg.norm(population_state)
        mask, target, selected, symmetry = find_balanced_z2_symmetry(
            groups, num_qubits, population_basis, population_state
        )
        restricted_basis = population_basis[selected]
        restricted_state = population_state[selected].copy()
        restricted_state /= np.linalg.norm(restricted_state)
        spectra, compact = prepare_component_spectra(
            groups,
            num_qubits,
            restricted_basis,
            validation_state=restricted_state,
            processes=int(args.processes),
        )
        summed_action = np.asarray(compact.pop("summed_group_action"))
        energy = float(source["ground_energy_without_constant_hartree"])
        ground_residual = float(np.linalg.norm(summed_action - energy * restricted_state))
        if ground_residual > 1e-8:
            raise RuntimeError(f"restricted ground-state residual is {ground_residual}")
        data = {
            "h_chain": int(args.h_chain),
            "num_qubits": num_qubits,
            "groups": len(groups),
            "restricted_basis": restricted_basis,
            "restricted_ground_state": restricted_state,
            "ground_energy_without_constant_hartree": energy,
            "component_spectra": spectra,
        }
        with (args.output_dir / "compact_system.pkl").open("wb") as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        metadata.update(
            {
                "status": "complete",
                "completed_at": _now(),
                "system": {
                    "h_chain": int(args.h_chain),
                    "num_qubits": num_qubits,
                    "full_state_dimension": 1 << num_qubits,
                    "group_count": len(groups),
                    "ground_energy_without_constant_hartree": energy,
                    "population_sector": population,
                    "diagonal_z2_symmetry": symmetry,
                    "symmetry_mask": int(mask),
                    "symmetry_target_bit": int(target),
                    "restricted_ground_state_residual": ground_residual,
                    "component_representation": compact,
                },
                "timing_seconds": {
                    "total_preparation": float(time.perf_counter() - started),
                    "source_preparation": source[
                        "preparation_seconds_before_dense_sector"
                    ],
                },
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                "artifact": str(args.output_dir / "compact_system.pkl"),
            }
        )
        _atomic_json(args.output_dir / "system.json", metadata)
        print(
            f"prepared H{args.h_chain}: population {population_basis.size}, "
            f"symmetry block {restricted_basis.size}, max component "
            f"{compact['maximum_component_size']}, retained "
            f"{compact['retained_estimated_bytes'] / 2**20:.1f} MiB",
            flush=True,
        )
        return 0
    except Exception as exc:
        metadata.update(
            {
                "status": "failed",
                "completed_at": _now(),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
        )
        _atomic_json(args.output_dir / "system.json", metadata)
        traceback.print_exc()
        return 1


def _build_s2_stage_gpu(
    spectra: Sequence[ComponentSpectrum], time_value: float, weight: float
):
    import cupy as cp
    from cupyx.scipy.sparse import csr_matrix as gpu_csr_matrix

    dimension = spectra[0].dimension
    stage = cp.eye(dimension, dtype=cp.complex128)
    half_gates = []
    half_time = float(time_value) * float(weight) / 2.0
    for spectrum in spectra[:-1]:
        gate = gpu_csr_matrix(component_exponential(spectrum, half_time))
        half_gates.append(gate)
        stage = gate @ stage
    last_gate = gpu_csr_matrix(
        component_exponential(spectra[-1], float(time_value) * float(weight))
    )
    stage = last_gate @ stage
    del last_gate
    for gate in reversed(half_gates):
        stage = gate @ stage
    del half_gates
    return stage


def build_pf_unitary_gpu(
    spectra: Sequence[ComponentSpectrum], time_value: float
) -> tuple[np.ndarray, dict[str, Any]]:
    import cupy as cp

    sequence = [float(value) for value in _get_s2_sequence(LABEL)]
    dimension = spectra[0].dimension
    cache: dict[float, Any] = {}
    stage_seconds: dict[str, float] = {}
    build_started = time.perf_counter()
    for weight in dict.fromkeys(sequence):
        started = time.perf_counter()
        cache[weight] = _build_s2_stage_gpu(spectra, time_value, weight)
        cp.cuda.Stream.null.synchronize()
        stage_seconds[repr(weight)] = float(time.perf_counter() - started)
    assembly_started = time.perf_counter()
    unitary = cp.eye(dimension, dtype=cp.complex128)
    for weight in sequence:
        unitary = cache[weight] @ unitary
    cp.cuda.Stream.null.synchronize()
    assembly_seconds = time.perf_counter() - assembly_started
    transfer_started = time.perf_counter()
    host = cp.asnumpy(unitary)
    cp.cuda.Stream.null.synchronize()
    transfer_seconds = time.perf_counter() - transfer_started
    total = time.perf_counter() - build_started
    del unitary, cache
    cp.get_default_memory_pool().free_all_blocks()
    return host, {
        "gpu_total_build_seconds": float(total),
        "unique_s2_stage_build_seconds": stage_seconds,
        "dense_stage_assembly_seconds": float(assembly_seconds),
        "gpu_to_cpu_transfer_seconds": float(transfer_seconds),
        "s2_stage_count": len(sequence),
        "unique_s2_stage_count": len(set(sequence)),
    }


def analyze_unitary(
    unitary: np.ndarray,
    state: np.ndarray,
    energy: float,
    time_value: float,
    rotations: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    triangular, vectors = schur(
        unitary, output="complex", overwrite_a=False, check_finite=False
    )
    schur_seconds = time.perf_counter() - started
    eigenvalues = np.diag(triangular)
    overlaps = np.abs(vectors.conj().T @ state) ** 2
    selected = int(np.argmax(overlaps))
    eigenvalue = complex(eigenvalues[selected])
    vector = vectors[:, selected]
    phase = float(np.angle(eigenvalue))
    branch = int(np.rint((energy * time_value - phase) / (2 * np.pi)))
    effective_energy = float((phase + 2 * np.pi * branch) / time_value)
    shift = float(effective_energy - energy)
    residual = float(np.linalg.norm(unitary @ vector - eigenvalue * vector))
    return {
        "signed_eigenvalue_shift_hartree": shift,
        "direct_error_hartree": abs(shift),
        "direct_cost": _cost(time_value, abs(shift), rotations),
        "effective_energy_hartree": effective_energy,
        "raw_eigenphase_rad": phase,
        "phase_branch_integer": branch,
        "selected_ground_state_overlap_probability": float(overlaps[selected]),
        "maximum_ground_state_overlap_probability": float(np.max(overlaps)),
        "eigenvalue_magnitude": float(abs(eigenvalue)),
        "eigenpair_residual_2_norm": residual,
        "schur_seconds": float(schur_seconds),
    }


def direct_time(args: argparse.Namespace) -> int:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "status": "running",
        "started_at": _now(),
        "git": _git_state(),
        "configuration": {
            "system_dir": str(args.system_dir),
            "time": float(args.time),
            "relative_time": args.relative_time,
            "physical_gpu_id": int(args.gpu_id),
            "label": LABEL,
        },
    }
    _atomic_json(args.output, payload)
    try:
        visible = os.environ.get("CUDA_VISIBLE_DEVICES")
        if visible != str(args.gpu_id):
            raise RuntimeError(
                f"CUDA_VISIBLE_DEVICES must be {args.gpu_id}, got {visible!r}"
            )
        gpu = _gpu_info(int(args.gpu_id))
        if 2 * int(gpu["memory_used_mib"]) > int(gpu["memory_total_mib"]):
            raise RuntimeError("selected GPU has less than half its memory free")
        load_started = time.perf_counter()
        with (args.system_dir / "compact_system.pkl").open("rb") as handle:
            system = pickle.load(handle)
        load_seconds = time.perf_counter() - load_started
        dimension = int(system["restricted_ground_state"].size)
        rotations = int(DECOMPO_NUM[f"H{system['h_chain']}"][LABEL])
        total_started = time.perf_counter()
        with GpuMemoryMonitor(int(args.gpu_id), interval_ms=200) as monitor:
            unitary, build = build_pf_unitary_gpu(
                system["component_spectra"], float(args.time)
            )
        gpu_memory = monitor.summary()
        result = analyze_unitary(
            unitary,
            np.asarray(system["restricted_ground_state"]),
            float(system["ground_energy_without_constant_hartree"]),
            float(args.time),
            rotations,
        )
        total_seconds = time.perf_counter() - total_started
        payload.update(
            {
                "status": "complete",
                "completed_at": _now(),
                "environment": {
                    "python": platform.python_version(),
                    "python_executable": os.path.realpath(os.sys.executable),
                    "packages": {
                        name: _version(name)
                        for name in ("numpy", "scipy", "cupy-cuda12x")
                    },
                    "gpu": gpu,
                    "cuda_visible_devices": visible,
                },
                "system": {
                    "h_chain": int(system["h_chain"]),
                    "num_qubits": int(system["num_qubits"]),
                    "symmetry_block_dimension": dimension,
                    "dense_unitary_bytes": int(16 * dimension * dimension),
                    "pauli_rotations_per_pf_application": rotations,
                },
                "timing_seconds": {
                    "compact_system_load": float(load_seconds),
                    **build,
                    "total_excluding_compact_preparation": float(total_seconds),
                },
                "gpu_memory": gpu_memory,
                "cpu_peak_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                "direct": result,
            }
        )
        _atomic_json(args.output, payload)
        print(
            f"H{system['h_chain']} t={args.time:.12g}: "
            f"shift={result['signed_eigenvalue_shift_hartree']:.12g}, "
            f"build={build['gpu_total_build_seconds']:.1f}s, "
            f"schur={result['schur_seconds']:.1f}s",
            flush=True,
        )
        return 0
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "completed_at": _now(),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
        )
        _atomic_json(args.output, payload)
        traceback.print_exc()
        return 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    subparsers = result.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--h-chain", type=int, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--processes", type=int, default=8)
    prepare_parser.set_defaults(function=prepare)
    direct_parser = subparsers.add_parser("direct-time")
    direct_parser.add_argument("--system-dir", type=Path, required=True)
    direct_parser.add_argument("--time", type=float, required=True)
    direct_parser.add_argument("--relative-time", type=float)
    direct_parser.add_argument("--gpu-id", type=int, required=True)
    direct_parser.add_argument("--output", type=Path, required=True)
    direct_parser.set_defaults(function=direct_time)
    return result


def main() -> int:
    args = parser().parse_args()
    return int(args.function(args))


if __name__ == "__main__":
    raise SystemExit(main())
