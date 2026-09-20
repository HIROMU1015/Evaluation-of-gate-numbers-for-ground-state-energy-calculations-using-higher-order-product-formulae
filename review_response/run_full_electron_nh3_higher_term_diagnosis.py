"""Exact full-electron NH3 diagnosis for one-, two-, and three-term PF models.

The expensive molecular preparation is checkpointed once per geometry.  Exact
PF unitaries are then built in the fixed-population/diagonal-Z sector, either
with SciPy sparse-dense products on CPU or CuPy sparse-dense products on one
assigned GPU.  Eigenphases are always obtained from a dense SciPy Schur
decomposition; overlap phases are diagnostics only.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import gzip
import importlib.metadata
import json
import math
import os
from pathlib import Path
import pickle
import platform
import resource
import subprocess
import sys
import threading
import time
from typing import Any, Sequence

import numpy as np
from openfermion.ops import FermionOperator, QubitOperator
from openfermion.transforms import jordan_wigner
from pyscf import ao2mo, gto, mcscf, scf
from scipy.linalg import eigh, schur

from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
from trotterlib.component_sector_pf import (
    ComponentSpectrum,
    component_exponential,
    find_balanced_z2_symmetry,
    prepare_component_spectra,
    qubit_operator_sector_matrix,
)
from trotterlib.config import BETA, TARGET_ERROR
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.product_formula import (
    actual_circuit_optimized_4th_m5_list,
    morales_2025_y8m10b_list,
    yoshida_4th_list,
)


EPSILON_E = float(TARGET_ERROR)
FIT_GRID = tuple(float(value) for value in np.geomspace(0.02, 1.8, 34))
FIT_WINDOW = 5
FIT_NOISE_FLOOR = 5e-13
FIT_ORDER_TOLERANCE = 0.2
FIT_MINIMUM_R2 = 0.999
TRAINING_RELATIVE_TIMES = (0.1, 0.2, 0.3, 0.4, 0.5)
LEGACY_TRAINING_RELATIVE_TIMES = (0.1, 0.2, 0.3)
VALIDATION_RELATIVE_TO_T_STAR = (0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15)
OPTIMIZATION_RELATIVE_INTERVAL = (0.05, 1.8)
OPTIMIZATION_GRID_POINTS = 35001
PASS_THRESHOLDS = {
    "eta_star": 0.01,
    "eta_min": 0.01,
    "eta_t": 0.05,
    "maximum_unseen_residual_over_epsilon": 0.05,
}

NH3_GEOMETRY = (
    ("N", (-0.0404260543, 1.0241077531, 0.0625637998)),
    ("H", (0.0172574639, 0.0125452063, -0.0273771593)),
    ("H", (0.9157893661, 1.3587451948, -0.0287577581)),
    ("H", (-0.5202777357, 1.3435321258, -0.7755426124)),
)

TWO_TERM_CENTER = (
    -0.5479746372736223,
    0.4130665734843169,
    0.1864679228988850,
    0.1744528222536092,
)
PAPER_NEW4 = (
    -0.6581584493683974,
    0.420087292300873,
    0.4089919323833257,
)
JOINT_REFINE = (
    -1.0873996519284317,
    0.8623983814720917,
    0.08656065765564214,
    0.09474078683648192,
)
YOSHIDA6_M3 = (
    1.315186320683908,
    -1.177679984178871,
    0.235573213359357,
    0.78451361047756,
)
CURRENT_M3 = (
    -0.4737318199452465,
    0.3316118001935053,
    0.2092246690782796,
    0.1960294407008384,
)


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


def _display(value: Any, format_spec: str = ".6g") -> str:
    return "n/a" if value is None else format(float(value), format_spec)


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

    def run(*command: str) -> str:
        return subprocess.run(
            command, cwd=root, text=True, capture_output=True, check=False
        ).stdout.strip()

    status = run("git", "status", "--porcelain").splitlines()
    return {
        "commit": run("git", "rev-parse", "HEAD") or None,
        "branch": run("git", "branch", "--show-current") or None,
        "dirty": bool(status),
        "status": status,
    }


def _versions() -> dict[str, Any]:
    packages = {}
    for name in (
        "numpy", "scipy", "pyscf", "openfermion", "cupy-cuda12x",
        "qiskit", "qiskit-aer", "qiskit-aer-gpu",
    ):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "packages": packages,
    }


def _geometry(name: str) -> list[tuple[str, tuple[float, float, float]]]:
    if name == "equilibrium":
        return list(NH3_GEOMETRY)
    if name != "stretch150":
        raise ValueError(f"unknown geometry: {name}")
    nitrogen = np.asarray(NH3_GEOMETRY[0][1], dtype=float)
    result = [NH3_GEOMETRY[0]]
    for atom, coordinates in NH3_GEOMETRY[1:]:
        hydrogen = nitrogen + 1.5 * (np.asarray(coordinates) - nitrogen)
        result.append((atom, tuple(map(float, hydrogen))))
    return result


def _formulae() -> dict[str, dict[str, Any]]:
    return {
        "yoshida4": {
            "display_name": "Yoshida 4th",
            "formal_order": 4,
            "weights": tuple(map(float, yoshida_4th_list())),
            "provenance": "src/trotterlib/product_formula.py:yoshida_4th_list",
        },
        "paper_new4": {
            "display_name": "paper 4th(new_2)",
            "formal_order": 4,
            "weights": PAPER_NEW4,
            "provenance": (
                "review_response/search_pf_cost_predictability_m2_m3.py:"
                "projected_reference_candidate(2)"
            ),
        },
        "m5_best": {
            "display_name": "4th(m5_best)",
            "formal_order": 4,
            "weights": tuple(map(float, actual_circuit_optimized_4th_m5_list())),
            "provenance": (
                "src/trotterlib/product_formula.py:"
                "actual_circuit_optimized_4th_m5_list"
            ),
        },
        "current_m3": {
            "display_name": "current_m3",
            "formal_order": 4,
            "weights": CURRENT_M3,
            "provenance": (
                "fixed comparison coefficient vector supplied for the "
                "unified NH3 comparison"
            ),
        },
        "two_term_center": {
            "display_name": "two_term_center",
            "formal_order": 4,
            "weights": TWO_TERM_CENTER,
            "provenance": "fixed multi-molecule two-term candidate",
        },
        "joint_refine_r0_s0046": {
            "display_name": "joint_refine_r0_s0046",
            "formal_order": 4,
            "weights": JOINT_REFINE,
            "provenance": (
                "artifacts/m3_joint_full_frozen_refinement_20260913/"
                "refinement_results.json.gz:ranked_candidates[0]"
            ),
        },
        "yoshida6_m3": {
            "display_name": "Yoshida 6th m=3",
            "formal_order": 6,
            "weights": YOSHIDA6_M3,
            "provenance": (
                "Yoshida 1990 Table 1 Solution A; committed comparison constant"
            ),
        },
        "morales_y8m10b": {
            "display_name": "Morales 8th Y8m10b",
            "formal_order": 8,
            "weights": tuple(map(float, morales_2025_y8m10b_list())),
            "provenance": (
                "src/trotterlib/product_formula.py:"
                "morales_2025_y8m10b_list"
            ),
        },
    }


def _formula_s2_sequence(formula_name: str) -> list[float]:
    """Return the exact S2 sequence used by this runner for one named PF."""
    formula = _formulae()[formula_name]
    return list(map(float, symmetric_s2_sequence(formula["weights"])))


def _verify_joint_candidate(root: Path) -> dict[str, Any]:
    path = root / "artifacts/m3_joint_full_frozen_refinement_20260913/refinement_results.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    selected = payload["ranked_candidates"][0]
    observed = tuple(map(float, selected["weights"]))
    if str(selected["name"]) != "joint_refine_r0_s0046":
        raise RuntimeError(f"unexpected joint candidate: {selected['name']}")
    if not np.allclose(observed, JOINT_REFINE, atol=1e-15, rtol=0.0):
        raise RuntimeError("joint candidate weights do not match fixed inputs")
    return {"name": selected["name"], "weights": list(observed), "source": str(path)}


def _population_basis(num_orbitals: int, n_alpha: int, n_beta: int) -> np.ndarray:
    low_mask = (1 << int(num_orbitals)) - 1
    return np.asarray(
        [
            index
            for index in range(1 << (2 * int(num_orbitals)))
            if (index >> int(num_orbitals)).bit_count() == int(n_alpha)
            and (index & low_mask).bit_count() == int(n_beta)
        ],
        dtype=np.int64,
    )


def _hermitize(operator: QubitOperator) -> tuple[QubitOperator, dict[str, float]]:
    result = QubitOperator()
    removed = []
    for term, raw in operator.terms.items():
        coefficient = complex(raw)
        removed.append(float(coefficient.imag))
        if abs(coefficient.imag) > 1e-9:
            raise RuntimeError(f"unexpected imaginary coefficient {coefficient}")
        result += QubitOperator(term, float(coefficient.real))
    return result, {
        "maximum_removed_imaginary_pauli_coefficient": max(
            (abs(value) for value in removed), default=0.0
        )
    }


def prepare_system(geometry_name: str, work_dir: Path, processes: int) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    work_dir.mkdir(parents=True, exist_ok=True)
    molecule = gto.Mole()
    molecule.atom = _geometry(geometry_name)
    molecule.unit = "Angstrom"
    molecule.basis = "sto-3g"
    molecule.spin = 0
    molecule.charge = 0
    molecule.symmetry = False
    molecule.verbose = 3
    molecule.output = str(work_dir / "pyscf.log")
    molecule.build()
    mean_field = scf.RHF(molecule)
    mean_field.conv_tol = 1e-12
    mean_field.max_cycle = 200
    mean_field.kernel()
    if not mean_field.converged:
        raise RuntimeError("RHF did not converge")

    ncas = int(mean_field.mo_coeff.shape[1])
    nelecas = int(molecule.nelectron)
    cas = mcscf.CASCI(mean_field, ncas, nelecas)
    cas.ncore = 0
    h1_effective, core_energy = cas.get_h1eff(mean_field.mo_coeff)
    eri_compact = ao2mo.kernel(molecule, mean_field.mo_coeff)
    eri_active = ao2mo.restore(1, eri_compact, ncas)
    two_body = np.asarray(eri_active.transpose(0, 2, 3, 1), order="C")

    grouper = Almost_optimal_grouper(
        float(core_energy), np.asarray(h1_effective), two_body,
        fermion_qubit_mapping=jordan_wigner, validation=True,
    )
    grouped = grouper.group_term_list
    grouped[0].insert(0, FermionOperator("", grouper._const_fermion))
    groups = [
        _hermitize(jordan_wigner(sum(group, FermionOperator())))[0]
        for group in grouped
    ]
    hamiltonian, hermitization = _hermitize(sum(groups, QubitOperator()))
    constant = float(complex(hamiltonian.terms.get((), 0.0)).real)

    n_alpha = nelecas // 2
    n_beta = nelecas - n_alpha
    basis = _population_basis(ncas, n_alpha, n_beta)
    sector_sparse = qubit_operator_sector_matrix(
        groups[0], 2 * ncas, basis, remove_constant=True
    )
    for group in groups[1:]:
        sector_sparse = sector_sparse + qubit_operator_sector_matrix(
            group, 2 * ncas, basis, remove_constant=True
        )
    sector_hamiltonian = sector_sparse.toarray()
    ground_values, ground_vectors = eigh(
        sector_hamiltonian, subset_by_index=[0, 0], check_finite=False,
        driver="evr",
    )
    energy = float(ground_values[0])
    population_state = np.asarray(ground_vectors[:, 0], dtype=np.complex128)
    population_state /= np.linalg.norm(population_state)
    ground_residual = float(
        np.linalg.norm(sector_hamiltonian @ population_state - energy * population_state)
    )
    del sector_hamiltonian

    try:
        mask, target, selected, symmetry = find_balanced_z2_symmetry(
            groups, 2 * ncas, basis, population_state, support_cutoff=1e-9
        )
    except RuntimeError as exc:
        if "No nonconstant exact diagonal-Z symmetry" not in str(exc):
            raise
        mask, target = 0, 0
        selected = np.arange(basis.size, dtype=np.int64)
        symmetry = {
            "kind": "no_nonconstant_exact_diagonal_Z2",
            "population_sector_dimension": int(basis.size),
            "restricted_dimension": int(basis.size),
        }
    restricted_basis = basis[selected]
    restricted_state = population_state[selected].copy()
    restricted_state /= np.linalg.norm(restricted_state)
    spectra, compact = prepare_component_spectra(
        groups, 2 * ncas, restricted_basis,
        validation_state=restricted_state, processes=int(processes),
    )
    summed_action = np.asarray(compact.pop("summed_group_action"))
    restricted_residual = float(np.linalg.norm(summed_action - energy * restricted_state))
    if restricted_residual > 1e-8:
        raise RuntimeError(f"restricted ground residual is {restricted_residual}")
    term_counts = [sum(1 for term in group.terms if term) for group in groups]
    system = {
        "geometry": geometry_name,
        "state": restricted_state,
        "energy": energy,
        "component_spectra": spectra,
        "term_counts": term_counts,
    }
    metadata = {
        "geometry_name": geometry_name,
        "geometry_angstrom": _geometry(geometry_name),
        "basis": "sto-3g",
        "charge": 0,
        "multiplicity": 1,
        "total_electron_count": nelecas,
        "active_electron_count": nelecas,
        "frozen_core_spatial_orbitals": 0,
        "active_spatial_orbitals": ncas,
        "num_qubits": 2 * ncas,
        "n_alpha": n_alpha,
        "n_beta": n_beta,
        "population_sector_dimension": int(basis.size),
        "restricted_dimension": int(restricted_basis.size),
        "group_count": len(groups),
        "nonidentity_pauli_term_count": sum(term_counts),
        "ground_energy_without_constant_hartree": energy,
        "removed_constant_hartree": constant,
        "ground_residual_2_norm": ground_residual,
        "restricted_ground_residual_2_norm": restricted_residual,
        "z2_mask": int(mask),
        "z2_target": int(target),
        "z2_symmetry": symmetry,
        "component_representation": compact,
        "numerical_hermitization": hermitization,
        "scf_energy_hartree": float(mean_field.e_tot),
        "scf_converged": bool(mean_field.converged),
        "preparation_seconds": float(time.perf_counter() - started),
    }
    return system, metadata


def _rotation_count(system: dict[str, Any], sequence: Sequence[float]) -> int:
    counts = system["term_counts"]
    return int(sum(counts[index] for index, _ in iter_s2_sequence_steps(len(counts), sequence)))


def _apply_pf(system: dict[str, Any], sequence: Sequence[float], time_value: float) -> np.ndarray:
    current = np.asarray(system["state"], dtype=np.complex128).copy()
    gates: dict[tuple[int, float], Any] = {}
    for group_index, raw_weight in iter_s2_sequence_steps(
        len(system["component_spectra"]), sequence
    ):
        key = (int(group_index), float(raw_weight))
        gate = gates.get(key)
        if gate is None:
            gate = component_exponential(
                system["component_spectra"][group_index],
                float(time_value) * float(raw_weight),
            )
            gates[key] = gate
        current = gate @ current
    return current


def _build_cpu(system: dict[str, Any], sequence: Sequence[float], time_value: float) -> tuple[np.ndarray, dict[str, Any]]:
    started = time.perf_counter()
    spectra = system["component_spectra"]
    unitary = np.eye(spectra[0].dimension, dtype=np.complex128)
    stages: dict[float, np.ndarray] = {}
    materialization = 0.0
    multiplication = 0.0
    for raw_weight in sequence:
        weight = float(raw_weight)
        stage = stages.get(weight)
        if stage is None:
            stage = np.eye(spectra[0].dimension, dtype=np.complex128)
            for group_index, factor in iter_s2_sequence_steps(len(spectra), [weight]):
                gate_started = time.perf_counter()
                gate = component_exponential(
                    spectra[group_index], float(time_value) * float(factor)
                )
                materialization += time.perf_counter() - gate_started
                multiply_started = time.perf_counter()
                stage = gate @ stage
                multiplication += time.perf_counter() - multiply_started
            stages[weight] = stage
        multiply_started = time.perf_counter()
        unitary = stage @ unitary
        multiplication += time.perf_counter() - multiply_started
    return unitary, {
        "backend": "cpu_component_sector_dense_final",
        "build_seconds": float(time.perf_counter() - started),
        "component_gate_materialization_seconds": float(materialization),
        "multiplication_seconds": float(multiplication),
        "unique_s2_stage_count": len(stages),
    }


class GpuMemoryMonitor:
    def __init__(self, physical_gpu: int, interval: float = 0.2):
        self.gpu = int(physical_gpu)
        self.interval = float(interval)
        self.values: list[int] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _query(self) -> None:
        while not self._stop.is_set():
            result = subprocess.run(
                ["nvidia-smi", f"--id={self.gpu}", "--query-gpu=memory.used",
                 "--format=csv,noheader,nounits"],
                text=True, capture_output=True, check=False,
            )
            try:
                self.values.append(int(result.stdout.strip().splitlines()[0]))
            except (ValueError, IndexError):
                pass
            self._stop.wait(self.interval)

    def __enter__(self):
        self._thread = threading.Thread(target=self._query, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def summary(self) -> dict[str, Any]:
        return {
            "physical_gpu_id": self.gpu,
            "samples": len(self.values),
            "minimum_used_mib": min(self.values) if self.values else None,
            "maximum_used_mib": max(self.values) if self.values else None,
            "peak_increment_mib": (
                max(self.values) - min(self.values) if self.values else None
            ),
        }


def _build_gpu(system: dict[str, Any], sequence: Sequence[float], time_value: float, physical_gpu: int) -> tuple[np.ndarray, dict[str, Any]]:
    import cupy as cp
    from cupyx.scipy.sparse import csr_matrix as gpu_csr_matrix

    started = time.perf_counter()
    spectra = system["component_spectra"]
    dimension = spectra[0].dimension
    pool = cp.get_default_memory_pool()
    pool.free_all_blocks()
    stages: dict[float, Any] = {}
    cpu_materialization = 0.0
    transfer_and_sparse_multiply = 0.0
    dense_multiply = 0.0
    with GpuMemoryMonitor(physical_gpu) as monitor:
        unitary = cp.eye(dimension, dtype=cp.complex128)
        for raw_weight in sequence:
            weight = float(raw_weight)
            stage = stages.get(weight)
            if stage is None:
                stage = cp.eye(dimension, dtype=cp.complex128)
                for group_index, factor in iter_s2_sequence_steps(len(spectra), [weight]):
                    gate_started = time.perf_counter()
                    gate_cpu = component_exponential(
                        spectra[group_index], float(time_value) * float(factor)
                    )
                    cpu_materialization += time.perf_counter() - gate_started
                    multiply_started = time.perf_counter()
                    gate_gpu = gpu_csr_matrix(gate_cpu)
                    stage = gate_gpu @ stage
                    cp.cuda.Stream.null.synchronize()
                    transfer_and_sparse_multiply += time.perf_counter() - multiply_started
                    del gate_gpu, gate_cpu
                stages[weight] = stage
            multiply_started = time.perf_counter()
            unitary = stage @ unitary
            cp.cuda.Stream.null.synchronize()
            dense_multiply += time.perf_counter() - multiply_started
        transfer_started = time.perf_counter()
        host = cp.asnumpy(unitary)
        cp.cuda.Stream.null.synchronize()
        output_transfer = time.perf_counter() - transfer_started
        pool_peak = int(pool.total_bytes())
        del unitary, stages
        pool.free_all_blocks()
    return host, {
        "backend": "gpu_component_sector_dense_final_cpu_schur",
        "physical_gpu_id": int(physical_gpu),
        "build_seconds": float(time.perf_counter() - started),
        "cpu_component_gate_materialization_seconds": float(cpu_materialization),
        "gpu_transfer_sparse_multiply_seconds": float(transfer_and_sparse_multiply),
        "gpu_dense_multiply_seconds": float(dense_multiply),
        "output_transfer_seconds": float(output_transfer),
        "cupy_pool_peak_reserved_mib": float(pool_peak / 2**20),
        "gpu_memory": monitor.summary(),
        "unique_s2_stage_count": len(set(map(float, sequence))),
    }


def _schur_point(
    unitary: np.ndarray,
    state: np.ndarray,
    energy: float,
    time_value: float,
    rotations: int,
    previous_vector: np.ndarray | None = None,
) -> tuple[dict[str, Any], np.ndarray]:
    started = time.perf_counter()
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    schur_seconds = time.perf_counter() - started
    eigenvalues = np.diag(triangular)
    ground_overlaps = np.abs(vectors.conj().T @ state) ** 2
    selected = int(np.argmax(ground_overlaps))
    eigenvalue = complex(eigenvalues[selected])
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    shift = float(
        np.angle(np.exp(-1j * float(energy) * float(time_value)) * eigenvalue)
        / float(time_value)
    )
    residual = float(np.linalg.norm(unitary @ vector - eigenvalue * vector))
    result = {
        "time": float(time_value),
        "signed_direct_shift_hartree": shift,
        "direct_error_hartree": abs(shift),
        "direct_cost": _cost(time_value, abs(shift), rotations),
        "ground_overlap_probability": float(ground_overlaps[selected]),
        "adjacent_selected_vector_overlap_probability": (
            None if previous_vector is None
            else float(abs(np.vdot(previous_vector, vector)) ** 2)
        ),
        "selected_eigenvalue": eigenvalue,
        "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
        "eigenpair_residual_2_norm": residual,
        "schur_seconds": float(schur_seconds),
        "selection_rule": "maximum exact-ground-state overlap in exact invariant sector",
    }
    return result, vector


def _cost(time_value: float, error: float, rotations: int) -> float | None:
    if time_value <= 0.0 or error < 0.0 or error >= EPSILON_E:
        return None
    return float(BETA * int(rotations) / (time_value * (EPSILON_E - error)))


def _qualify_fit(times: Sequence[float], errors: Sequence[float], order: int) -> dict[str, Any]:
    windows = rolling_loglog_fits(
        np.asarray(times), np.asarray(errors), formal_order=int(order),
        noise_floor=FIT_NOISE_FLOOR, window_size=FIT_WINDOW,
    )
    eligible = [
        window for window in windows
        if float(window["order_deviation"]) <= FIT_ORDER_TOLERANCE
        and float(window["r2"]) >= FIT_MINIMUM_R2
    ]
    selected = min(eligible, key=lambda item: int(item["start_index"]), default=None)
    return {
        "qualified": selected is not None,
        "selected_window": selected,
        "evaluated_windows": windows,
        "formal_order": int(order),
        "grid": list(FIT_GRID),
        "noise_floor": FIT_NOISE_FLOOR,
        "window_size": FIT_WINDOW,
        "order_tolerance": FIT_ORDER_TOLERANCE,
        "minimum_r2": FIT_MINIMUM_R2,
        "selection_rule": "earliest qualifying consecutive five-point window",
    }


def _short_time_fit(system: dict[str, Any], sequence: Sequence[float], order: int) -> dict[str, Any]:
    times: list[float] = []
    errors: list[float] = []
    points: list[dict[str, Any]] = []
    qualification: dict[str, Any] | None = None
    for time_value in FIT_GRID:
        started = time.perf_counter()
        evolved = _apply_pf(system, sequence, time_value)
        overlap = complex(np.vdot(system["state"], evolved))
        rotated = np.exp(-1j * system["energy"] * time_value) * overlap
        error = abs(float(rotated.imag / time_value))
        times.append(time_value)
        errors.append(error)
        points.append({
            "time": time_value,
            "perturbative_error_hartree": error,
            "phase_rotated_overlap": rotated,
            "survival_probability": float(abs(rotated) ** 2),
            "evolved_state_norm": float(np.linalg.norm(evolved)),
            "elapsed_seconds": float(time.perf_counter() - started),
        })
        if len(points) >= FIT_WINDOW:
            qualification = _qualify_fit(times, errors, order)
            if qualification["qualified"]:
                break
    assert qualification is not None
    qualification["points"] = points
    qualification["times_computed"] = times
    qualification["errors_hartree"] = errors
    qualification["error_definition"] = (
        "abs(imag(exp(-i*E0*t)*<psi0|U_PF(t)|psi0>)/t)"
    )
    return qualification


def _analytic_time(alpha: float, order: int) -> float:
    return float((EPSILON_E / ((int(order) + 1) * alpha)) ** (1.0 / int(order)))


def _fit_model(
    points: Sequence[dict[str, Any]], order: int, analytic_time: float,
    powers: Sequence[int], name: str,
) -> dict[str, Any]:
    times = np.asarray([float(point["time"]) for point in points])
    shifts = np.asarray([float(point["signed_direct_shift_hartree"]) for point in points])
    relative = times / float(analytic_time)
    scale = float(np.max(np.abs(shifts))) or 1.0
    design = np.column_stack([relative ** (power) for power in powers])
    scaled_coefficients = np.linalg.lstsq(design, shifts / scale, rcond=None)[0]
    coefficients = [
        float(scale * coefficient / float(analytic_time) ** power)
        for coefficient, power in zip(scaled_coefficients, powers)
    ]
    fitted = sum(coefficient * times**power for coefficient, power in zip(coefficients, powers))
    return {
        "name": name,
        "formal_order": int(order),
        "coefficient_powers": list(map(int, powers)),
        "coefficient_values": coefficients,
        "coefficient_signs": [int(np.sign(value)) for value in coefficients],
        "training_relative_to_t_ana": relative.tolist(),
        "training_maximum_absolute_residual_hartree": float(np.max(np.abs(fitted - shifts))),
        "training_design_condition_number": float(np.linalg.cond(design)),
        "coefficient_source": "least-squares fit to the same five signed direct points",
    }


def _asymptotic_model(
    points: Sequence[dict[str, Any]], order: int, alpha: float,
) -> dict[str, Any]:
    shifts = np.asarray([
        float(point["signed_direct_shift_hartree"]) for point in points
    ])
    leading_sign = float(np.sign(np.median(shifts)))
    if leading_sign == 0.0:
        raise RuntimeError("zero leading sign in direct training points")
    times = np.asarray([float(point["time"]) for point in points])
    coefficient = leading_sign * float(alpha)
    fitted = coefficient * times ** int(order)
    return {
        "name": "short_time_asymptotic_one_term",
        "formal_order": int(order),
        "coefficient_powers": [int(order)],
        "coefficient_values": [coefficient],
        "coefficient_signs": [int(np.sign(coefficient))],
        "training_relative_to_t_ana": [
            float(point["relative_to_t_ana"]) for point in points
        ],
        "training_maximum_absolute_residual_hartree": float(
            np.max(np.abs(fitted - shifts))
        ),
        "training_design_condition_number": 1.0,
        "coefficient_source": "fixed-order alpha from the selected proxy window; sign from direct training points",
    }


def _prediction(model: dict[str, Any], time_value: float) -> float:
    return float(sum(
        coefficient * float(time_value) ** power
        for power, coefficient in zip(model["coefficient_powers"], model["coefficient_values"])
    ))


def _model_optimum(model: dict[str, Any], analytic_time: float, rotations: int) -> dict[str, Any]:
    relative = np.linspace(*OPTIMIZATION_RELATIVE_INTERVAL, OPTIMIZATION_GRID_POINTS)
    times = relative * float(analytic_time)
    shifts = np.zeros_like(times)
    for power, coefficient in zip(model["coefficient_powers"], model["coefficient_values"]):
        shifts += coefficient * times**power
    errors = np.abs(shifts)
    costs = np.full_like(times, np.inf)
    valid = errors < EPSILON_E
    costs[valid] = BETA * rotations / (times[valid] * (EPSILON_E - errors[valid]))
    selected = int(np.argmin(costs))
    if not np.isfinite(costs[selected]):
        raise RuntimeError(f"{model['name']}: no finite cost in optimization interval")
    return {
        "time": float(times[selected]),
        "relative_to_t_ana": float(relative[selected]),
        "signed_shift_hartree": float(shifts[selected]),
        "error_hartree": float(errors[selected]),
        "cost": float(costs[selected]),
        "at_optimization_boundary": selected in (0, len(times) - 1),
        "relative_interval": list(OPTIMIZATION_RELATIVE_INTERVAL),
        "grid_points": OPTIMIZATION_GRID_POINTS,
    }


def _direct_point(
    system: dict[str, Any], sequence: Sequence[float], time_value: float,
    rotations: int, backend: str, gpu_id: int, previous_vector: np.ndarray | None,
) -> tuple[dict[str, Any], np.ndarray]:
    started = time.perf_counter()
    if backend == "gpu":
        unitary, build = _build_gpu(system, sequence, time_value, gpu_id)
    elif backend == "cpu":
        unitary, build = _build_cpu(system, sequence, time_value)
    else:
        raise ValueError(f"unknown backend: {backend}")
    point, vector = _schur_point(
        unitary, system["state"], system["energy"], time_value, rotations,
        previous_vector,
    )
    point["timing_seconds"] = {
        **build,
        "schur": point.pop("schur_seconds"),
        "total": float(time.perf_counter() - started),
    }
    point["peak_cpu_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    del unitary
    return point, vector


def _validate_model(
    system: dict[str, Any], sequence: Sequence[float], rotations: int,
    model: dict[str, Any], analytic_time: float, backend: str, gpu_id: int,
) -> dict[str, Any]:
    optimum = _model_optimum(model, analytic_time, rotations)
    points = []
    previous = None
    for relative in VALIDATION_RELATIVE_TO_T_STAR:
        point, vector = _direct_point(
            system, sequence, float(relative) * optimum["time"], rotations,
            backend, gpu_id, previous,
        )
        predicted = _prediction(model, point["time"])
        point.update({
            "relative_to_t_star": relative,
            "relative_to_t_ana": float(point["time"] / analytic_time),
            "model_signed_shift_hartree": predicted,
            "model_cost": _cost(point["time"], abs(predicted), rotations),
            "signed_residual_hartree": float(point["signed_direct_shift_hartree"] - predicted),
            "residual_over_epsilon": float(abs(point["signed_direct_shift_hartree"] - predicted) / EPSILON_E),
        })
        points.append(point)
        previous = vector
    at_star = next(point for point in points if point["relative_to_t_star"] == 1.0)
    finite = [point for point in points if point["direct_cost"] is not None]
    direct_minimum = (
        min(finite, key=lambda point: float(point["direct_cost"]))
        if finite else None
    )
    minimum_index = points.index(direct_minimum) if direct_minimum is not None else None
    direct_cost_at_star = at_star["direct_cost"]
    metrics = {
        "eta_star": (
            float(abs(optimum["cost"] - direct_cost_at_star) / direct_cost_at_star)
            if direct_cost_at_star is not None else None
        ),
        "eta_min": (
            float(direct_cost_at_star / direct_minimum["direct_cost"] - 1.0)
            if direct_cost_at_star is not None and direct_minimum is not None else None
        ),
        "eta_t": (
            float(abs(optimum["time"] / direct_minimum["time"] - 1.0))
            if direct_minimum is not None else None
        ),
        "maximum_unseen_residual_over_epsilon": max(point["residual_over_epsilon"] for point in points),
        "minimum_ground_overlap_probability": min(point["ground_overlap_probability"] for point in points),
        "minimum_adjacent_vector_overlap_probability": min(
            point["adjacent_selected_vector_overlap_probability"]
            for point in points[1:]
        ),
        "maximum_eigenpair_residual_2_norm": max(point["eigenpair_residual_2_norm"] for point in points),
        "local_minimum_bracketed": (
            minimum_index is not None and 0 < minimum_index < len(points) - 1
        ),
    }
    checks = {
        key: metrics[key] is not None and metrics[key] <= threshold
        for key, threshold in PASS_THRESHOLDS.items()
    }
    diagnostics = {
        "model_optimum_interior": not optimum["at_optimization_boundary"],
        "direct_local_minimum_bracketed": metrics["local_minimum_bracketed"],
    }
    checks.update(diagnostics)
    term_contributions = [
        {
            "power": int(power),
            "coefficient": float(coefficient),
            "signed_contribution_hartree": float(
                coefficient * float(optimum["time"]) ** int(power)
            ),
        }
        for power, coefficient in zip(
            model["coefficient_powers"], model["coefficient_values"]
        )
    ]
    return {
        "model": model,
        "model_optimum": optimum,
        "term_contributions_at_t_star": term_contributions,
        "direct_validation_points": points,
        "direct_grid_minimum": direct_minimum,
        "invalid_cost_at_model_optimum": direct_cost_at_star is None,
        "invalid_cost_reason": (
            "direct error is not below epsilon_E, so the cost denominator is non-positive"
            if direct_cost_at_star is None else None
        ),
        "metrics": metrics,
        "checks": checks,
        "diagnostics": diagnostics,
        "passed": all(
            checks[name] for name in PASS_THRESHOLDS
        ),
    }


def command_prepare(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = {
        "status": "preparing", "started_at": _now(), "geometry": args.geometry,
        "git": _git_state(), "environment": _versions(),
    }
    _atomic_json(output.with_suffix(".metadata.json"), payload)
    system, metadata = prepare_system(
        args.geometry, output.parent / f"{output.stem}_work", args.component_processes
    )
    with output.open("wb") as stream:
        pickle.dump(system, stream, protocol=pickle.HIGHEST_PROTOCOL)
    payload.update({
        "status": "complete", "completed_at": _now(), "system": metadata,
        "cache_path": str(output), "cache_bytes": output.stat().st_size,
    })
    _atomic_json(output.with_suffix(".metadata.json"), payload)
    print(json.dumps(_jsonable(metadata), indent=2), flush=True)
    return 0


def _load_system(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return pickle.load(stream)


def command_benchmark(args: argparse.Namespace) -> int:
    system = _load_system(Path(args.system_cache))
    formula = _formulae()[args.formula]
    sequence = _formula_s2_sequence(args.formula)
    rotations = _rotation_count(system, sequence)
    payload: dict[str, Any] = {
        "status": "running", "started_at": _now(), "git": _git_state(),
        "environment": _versions(), "formula": formula,
        "time": args.time, "physical_gpu_id": args.gpu_id,
    }
    output = Path(args.output)
    _atomic_json(output, payload)
    action_started = time.perf_counter()
    sector_action = _apply_pf(system, sequence, args.time)
    sector_action_seconds = time.perf_counter() - action_started
    cpu_unitary, cpu_profile = _build_cpu(system, sequence, args.time)
    cpu_point, _ = _schur_point(
        cpu_unitary, system["state"], system["energy"], args.time, rotations
    )
    gpu_unitary, gpu_profile = _build_gpu(
        system, sequence, args.time, args.gpu_id
    )
    gpu_point, _ = _schur_point(
        gpu_unitary, system["state"], system["energy"], args.time, rotations
    )
    difference = float(np.linalg.norm(gpu_unitary - cpu_unitary) / np.linalg.norm(cpu_unitary))
    action_difference = float(
        np.linalg.norm((gpu_unitary - cpu_unitary) @ system["state"])
        / np.linalg.norm(cpu_unitary @ system["state"])
    )
    sector_action_difference = float(
        np.linalg.norm(sector_action - cpu_unitary @ system["state"])
        / np.linalg.norm(cpu_unitary @ system["state"])
    )
    passed = bool(
        difference <= 1e-10
        and abs(gpu_point["signed_direct_shift_hartree"] - cpu_point["signed_direct_shift_hartree"]) <= 1e-10
    )
    chosen = "gpu" if passed and gpu_profile["build_seconds"] < cpu_profile["build_seconds"] else "cpu"
    payload.update({
        "status": "complete", "completed_at": _now(), "rotations": rotations,
        "cpu": {"profile": cpu_profile, "direct": cpu_point},
        "gpu": {"profile": gpu_profile, "direct": gpu_point},
        "exact_sector_state_action": {
            "seconds": float(sector_action_seconds),
            "relative_2_norm_difference_vs_cpu_dense_final": sector_action_difference,
            "note": "Exact PF state action, but not a direct eigenphase solver.",
        },
        "gpu_vs_cpu_unitary_relative_frobenius_difference": difference,
        "gpu_vs_cpu_state_action_relative_2_norm_difference": action_difference,
        "agreement_tolerance": 1e-10, "agreement_passed": passed,
        "chosen_backend": chosen,
        "legacy_full_group_dense_note": (
            "Not separately retained: the exact component-sector representation "
            "builds the same dense final PF unitary without retaining one dense "
            "eigenvector matrix per Hamiltonian group."
        ),
    })
    _atomic_json(output, payload)
    print(f"agreement={passed} chosen_backend={chosen} relative={difference:.3e}", flush=True)
    return 0 if passed else 2


def command_formula(args: argparse.Namespace) -> int:
    root = Path(__file__).resolve().parents[1]
    joint = _verify_joint_candidate(root)
    system = _load_system(Path(args.system_cache))
    formula = _formulae()[args.formula]
    sequence = _formula_s2_sequence(args.formula)
    rotations = _rotation_count(system, sequence)
    output = Path(args.output)
    payload: dict[str, Any] = {
        "status": "short_time_fit", "started_at": _now(),
        "geometry": system["geometry"], "formula_name": args.formula,
        "formula": {**formula, "s2_sequence": sequence,
                    "s2_stage_count": len(sequence), "rotations": rotations},
        "joint_candidate_verification": joint,
        "backend": args.backend, "physical_gpu_id": args.gpu_id,
        "git": _git_state(), "environment": _versions(),
        "protocol": {
            "fit_grid": FIT_GRID, "fit_window": FIT_WINDOW,
            "fit_noise_floor": FIT_NOISE_FLOOR,
            "fit_order_tolerance": FIT_ORDER_TOLERANCE,
            "fit_minimum_r2": FIT_MINIMUM_R2,
            "training_relative_times": TRAINING_RELATIVE_TIMES,
            "legacy_training_relative_times": LEGACY_TRAINING_RELATIVE_TIMES,
            "validation_relative_to_t_star": VALIDATION_RELATIVE_TO_T_STAR,
            "pass_thresholds": PASS_THRESHOLDS,
        },
    }
    _atomic_json(output, payload)
    try:
        fit = _short_time_fit(system, sequence, formula["formal_order"])
        payload["short_time_fit"] = fit
        if not fit["qualified"]:
            payload.update({
                "status": "short_time_fit_failed",
                "completed_at": _now(),
                "failure_reason": "no qualifying window; protocol not changed",
            })
            _atomic_json(output, payload)
            return 0
        alpha = float(fit["selected_window"]["fixed_order_alpha"])
        analytic_time = _analytic_time(alpha, formula["formal_order"])
        payload.update({
            "status": "training_direct_points", "alpha": alpha,
            "analytic_time": analytic_time, "training_direct_points": [],
        })
        _atomic_json(output, payload)
        previous = None
        vectors = []
        for relative in TRAINING_RELATIVE_TIMES:
            point, vector = _direct_point(
                system, sequence, relative * analytic_time, rotations,
                args.backend, args.gpu_id, previous,
            )
            point["relative_to_t_ana"] = relative
            point["used_for_direct_model_fit"] = True
            payload["training_direct_points"].append(point)
            vectors.append(vector)
            previous = vector
            _atomic_json(output, payload)
        order = int(formula["formal_order"])
        training = payload["training_direct_points"]
        models = {
            "short_time_asymptotic_one_term": _asymptotic_model(
                training, order, alpha
            ),
            "direct_refit_one_term": _fit_model(
                training, order, analytic_time, [order],
                "direct_refit_one_term",
            ),
            "two_term": _fit_model(training, order, analytic_time, [order, order + 2], "two_term"),
            "three_term": _fit_model(training, order, analytic_time, [order, order + 2, order + 4], "three_term"),
        }
        payload.update({"status": "model_validation", "models": {}})
        _atomic_json(output, payload)
        for name, model in models.items():
            payload["models"][name] = _validate_model(
                system, sequence, rotations, model, analytic_time,
                args.backend, args.gpu_id,
            )
            _atomic_json(output, payload)
        payload.update({"status": "complete", "completed_at": _now()})
        _atomic_json(output, payload)
        return 0
    except Exception as exc:
        payload.update({
            "status": "failed", "completed_at": _now(),
            "error_type": type(exc).__name__, "error": str(exc),
        })
        _atomic_json(output, payload)
        raise


def command_aggregate(args: argparse.Namespace) -> int:
    raw_dir = Path(args.raw_dir)
    output = Path(args.output)
    records = []
    for path in sorted(raw_dir.glob("*.json")):
        if path.name.startswith("benchmark"):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "formula_name" in payload:
            records.append(payload)
    expected = set(_formulae())
    observed = {record["formula_name"] for record in records}
    rows = []
    for record in records:
        if record["status"] != "complete":
            rows.append({
                "formula": record["formula_name"], "status": record["status"],
                "model": None, "passed": False,
            })
            continue
        for name, result in record["models"].items():
            rows.append({
                "formula": record["formula_name"], "display_name": record["formula"]["display_name"],
                "formal_order": record["formula"]["formal_order"],
                "s2_stage_count": record["formula"]["s2_stage_count"],
                "rotations": record["formula"]["rotations"],
                "model": name, "passed": result["passed"],
                **result["metrics"],
                "predicted_cost": result["model_optimum"]["cost"],
                "direct_cost_at_prediction": next(
                    point["direct_cost"] for point in result["direct_validation_points"]
                    if point["relative_to_t_star"] == 1.0
                ),
            })
    complete_set = expected == observed and all(
        record["status"] in ("complete", "short_time_fit_failed") for record in records
    )
    healthy = complete_set and all(
        row.get("maximum_eigenpair_residual_2_norm", 0.0) <= 1e-8
        for row in rows if row.get("model") is not None
    )
    summary = {
        "created_at": _now(), "geometry": args.geometry,
        "expected_formulae": sorted(expected), "observed_formulae": sorted(observed),
        "complete": complete_set, "numerically_healthy": healthy,
        "rows": rows,
    }
    _atomic_json(output, summary)
    report = [
        f"# Full-electron NH3 higher-term diagnosis: {args.geometry}", "",
        f"Status: {'complete' if complete_set else 'incomplete'}", "",
        "| PF | model | pass | eta* | eta_min | eta_t | max residual/eps | direct cost |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        if row.get("model") is None:
            report.append(f"| {row['formula']} | n/a | False | n/a | n/a | n/a | n/a | n/a |")
        else:
            report.append(
                f"| {row['formula']} | {row['model']} | {row['passed']} | "
                f"{_display(row['eta_star'])} | {_display(row['eta_min'])} | "
                f"{_display(row['eta_t'])} | "
                f"{row['maximum_unseen_residual_over_epsilon']:.6g} | "
                f"{_display(row['direct_cost_at_prediction'], '.8g')} |"
            )
    output.with_suffix(".md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0 if complete_set and healthy else 3


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--geometry", choices=("equilibrium", "stretch150"), required=True)
    prepare.add_argument("--component-processes", type=int, default=8)
    prepare.add_argument("--output", type=Path, required=True)
    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--system-cache", type=Path, required=True)
    benchmark.add_argument("--formula", choices=tuple(_formulae()), default="yoshida4")
    benchmark.add_argument("--time", type=float, default=0.4)
    benchmark.add_argument("--gpu-id", type=int, required=True)
    benchmark.add_argument("--output", type=Path, required=True)
    formula = sub.add_parser("formula")
    formula.add_argument("--system-cache", type=Path, required=True)
    formula.add_argument("--formula", choices=tuple(_formulae()), required=True)
    formula.add_argument("--backend", choices=("cpu", "gpu"), required=True)
    formula.add_argument("--gpu-id", type=int, required=True)
    formula.add_argument("--output", type=Path, required=True)
    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--geometry", required=True)
    aggregate.add_argument("--raw-dir", type=Path, required=True)
    aggregate.add_argument("--output", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "prepare":
        return command_prepare(args)
    if args.command == "benchmark":
        return command_benchmark(args)
    if args.command == "formula":
        return command_formula(args)
    if args.command == "aggregate":
        return command_aggregate(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
