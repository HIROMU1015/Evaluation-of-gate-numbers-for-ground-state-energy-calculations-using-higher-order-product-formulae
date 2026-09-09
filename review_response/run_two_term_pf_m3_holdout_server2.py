"""Exact CPU holdout validation for the fixed two-term m=3 product formula.

The shared GPU server is handled conservatively: fixed-particle and exact
diagonal-Z2 sectors are used, PF unitaries are built exactly on CPU, and every
completed stage/direct point is checkpointed atomically.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import traceback
from typing import Any

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


EPSILON_E = float(TARGET_ERROR)
FORMAL_ORDER = 4
FIT_GRID = tuple(float(value) for value in np.geomspace(0.06, 0.80, 15))
FIT_WINDOW = 5
FIT_NOISE_FLOOR = 5e-13
FIT_ORDER_TOLERANCE = 0.2
FIT_MINIMUM_R2 = 0.999
TRAINING_RELATIVE_TIMES = (0.1, 0.2, 0.3)
MODEL_OPTIMIZATION_INTERVAL = (0.1, 1.4)
MODEL_OPTIMIZATION_POINTS = 20001
PASS_THRESHOLDS = {
    "eta_star": 0.01,
    "eta_min": 0.01,
    "eta_t": 0.05,
    "maximum_unseen_residual_over_epsilon": 0.05,
}
FORMULAS: dict[str, tuple[float, ...]] = {
    "two_term_center": (
        -0.5479746372736223,
        0.4130665734843169,
        0.1864679228988850,
        0.1744528222536092,
    ),
    "current_m3": (
        -0.4737318199452465,
        0.3316118001935053,
        0.2092246690782796,
        0.1960294407008384,
    ),
}
NH3_GEOMETRY = (
    ("N", (-0.0404260543, 1.0241077531, 0.0625637998)),
    ("H", (0.0172574639, 0.0125452063, -0.0273771593)),
    ("H", (0.9157893661, 1.3587451948, -0.0287577581)),
    ("H", (-0.5202777357, 1.3435321258, -0.7755426124)),
)


def _h_chain_geometry(length: int, distance: float = 1.0):
    shift = (int(length) - 1) / 2.0
    return [
        ("H", (0.0, 0.0, float(distance) * (index - shift)))
        for index in range(int(length))
    ]


CONDITIONS: dict[str, dict[str, Any]] = {
    "H6": dict(
        geometry=_h_chain_geometry(6), basis="sto-3g", multiplicity=1,
        charge=0, frozen_core_spatial_orbitals=0,
        active_spatial_orbitals=6, selection_role="unused H-chain holdout",
    ),
    "H7": dict(
        geometry=_h_chain_geometry(7), basis="sto-3g", multiplicity=3,
        charge=1, frozen_core_spatial_orbitals=0,
        active_spatial_orbitals=7, selection_role="unused H-chain holdout",
    ),
    "NH3_sto3g": dict(
        geometry=list(NH3_GEOMETRY), basis="sto-3g", multiplicity=1,
        charge=0, frozen_core_spatial_orbitals=1,
        active_spatial_orbitals=7, selection_role="unused molecular holdout",
    ),
    "NH3_631g": dict(
        geometry=list(NH3_GEOMETRY), basis="6-31g", multiplicity=1,
        charge=0, frozen_core_spatial_orbitals=1,
        active_spatial_orbitals=7, selection_role="unused molecular holdout",
    ),
    "NH3_ccpvdz": dict(
        geometry=list(NH3_GEOMETRY), basis="cc-pvdz", multiplicity=1,
        charge=0, frozen_core_spatial_orbitals=1,
        active_spatial_orbitals=7, selection_role="unused molecular holdout",
    ),
}


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


def _package_versions() -> dict[str, str | None]:
    result = {}
    for name in ("numpy", "scipy", "pyscf", "openfermion", "openfermionpyscf"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def _sha256(value: Any) -> str:
    encoded = json.dumps(
        _jsonable(value), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _term_key(term: tuple[tuple[int, str], ...]) -> list[list[Any]]:
    return [[int(qubit), str(pauli)] for qubit, pauli in term]


def _operator_term_records(operator: QubitOperator):
    return [
        {
            "term": _term_key(term),
            "coefficient": [
                float(complex(coefficient).real),
                float(complex(coefficient).imag),
            ],
        }
        for term, coefficient in operator.terms.items()
    ]


def _group_hashes(groups: Sequence[QubitOperator], hamiltonian: QubitOperator):
    ordered = [[_term_key(term) for term in group.terms] for group in groups]
    unordered = sorted(
        [
            sorted(
                (_term_key(term) for term in group.terms), key=lambda item: repr(item)
            )
            for group in groups
        ],
        key=lambda item: repr(item),
    )
    return {
        "hamiltonian_term_order_sha256": _sha256(
            _operator_term_records(hamiltonian)
        ),
        "ordered_grouping_structure_sha256": _sha256(ordered),
        "unordered_grouping_structure_sha256": _sha256(unordered),
    }


def _population_basis(num_orbitals: int, n_alpha: int, n_beta: int):
    num_qubits = 2 * int(num_orbitals)
    low_mask = (1 << int(num_orbitals)) - 1
    return np.asarray(
        [
            index
            for index in range(1 << num_qubits)
            if (index >> int(num_orbitals)).bit_count() == int(n_alpha)
            and (index & low_mask).bit_count() == int(n_beta)
        ],
        dtype=np.int64,
    )


def _hermitize(operator: QubitOperator):
    result = QubitOperator()
    removed = []
    for term, raw in operator.terms.items():
        coefficient = complex(raw)
        removed.append(float(coefficient.imag))
        if abs(coefficient.imag) > 1e-9:
            raise RuntimeError(
                f"unexpected imaginary Pauli coefficient {coefficient} for {term}"
            )
        result += QubitOperator(term, float(coefficient.real))
    return result, {
        "maximum_removed_imaginary_pauli_coefficient": max(
            (abs(value) for value in removed), default=0.0
        ),
        "removed_imaginary_coefficients_l2": float(np.linalg.norm(removed)),
    }


def _prepare_system(
    name: str,
    spec: dict[str, Any],
    work_dir: Path,
    component_processes: int,
):
    started = time.perf_counter()
    molecule = gto.Mole()
    molecule.atom = spec["geometry"]
    molecule.unit = "Angstrom"
    molecule.basis = str(spec["basis"])
    molecule.spin = int(spec["multiplicity"]) - 1
    molecule.charge = int(spec["charge"])
    molecule.symmetry = False
    molecule.verbose = 3
    molecule.output = str(work_dir / "pyscf.log")
    molecule.build()
    mean_field = scf.RHF(molecule)
    mean_field.conv_tol = 1e-12
    mean_field.max_cycle = 200
    mean_field.kernel()
    if not bool(mean_field.converged):
        raise RuntimeError(f"{name}: RHF did not converge")

    ncore = int(spec["frozen_core_spatial_orbitals"])
    ncas = int(spec["active_spatial_orbitals"])
    if int(mean_field.mo_coeff.shape[1]) < ncore + ncas:
        raise RuntimeError(f"{name}: requested CAS exceeds available orbitals")
    active_indices = list(range(ncore, ncore + ncas))
    nelecas = int(molecule.nelectron - 2 * ncore)
    cas = mcscf.CASCI(mean_field, ncas, nelecas)
    cas.ncore = ncore
    h1_effective, core_energy = cas.get_h1eff(mean_field.mo_coeff)
    active_coefficients = np.asarray(mean_field.mo_coeff[:, active_indices])
    eri_compact = ao2mo.kernel(molecule, active_coefficients)
    eri_active = ao2mo.restore(1, eri_compact, ncas)
    two_body = np.asarray(eri_active.transpose(0, 2, 3, 1), order="C")

    grouper = Almost_optimal_grouper(
        float(core_energy),
        np.asarray(h1_effective),
        two_body,
        fermion_qubit_mapping=jordan_wigner,
        validation=True,
    )
    grouped_fermion = grouper.group_term_list
    grouped_fermion[0].insert(0, FermionOperator("", grouper._const_fermion))
    groups = [
        _hermitize(jordan_wigner(sum(group, FermionOperator())))[0]
        for group in grouped_fermion
    ]
    hamiltonian, numerical_hermitization = _hermitize(
        sum(groups, QubitOperator())
    )
    constant = float(complex(hamiltonian.terms.get((), 0.0)).real)

    n_alpha = (nelecas + int(spec["multiplicity"]) - 1) // 2
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
        sector_hamiltonian,
        check_finite=False,
        driver="evd",
    )
    energy = float(ground_values[0])
    population_state = np.asarray(ground_vectors[:, 0], dtype=np.complex128)
    population_state /= np.linalg.norm(population_state)
    ground_residual = float(
        np.linalg.norm(
            sector_hamiltonian @ population_state - energy * population_state
        )
    )
    try:
        mask, target, selected, symmetry = find_balanced_z2_symmetry(
            groups, 2 * ncas, basis, population_state, support_cutoff=1e-9
        )
    except RuntimeError as exc:
        if "No nonconstant exact diagonal-Z symmetry" not in str(exc):
            raise
        mask = 0
        target = 0
        selected = np.arange(basis.size, dtype=np.int64)
        symmetry = {
            "kind": "no_nonconstant_exact_diagonal_Z2",
            "fallback": "fixed_alpha_beta_population_sector",
            "population_sector_dimension": int(basis.size),
            "restricted_dimension": int(basis.size),
            "ground_state_outside_norm": 0.0,
            "restricted_ground_state_norm": 1.0,
        }
    restricted_basis = basis[selected]
    restricted_state = population_state[selected].copy()
    restricted_state /= np.linalg.norm(restricted_state)
    spectra, compact = prepare_component_spectra(
        groups,
        2 * ncas,
        restricted_basis,
        validation_state=restricted_state,
        processes=int(component_processes),
    )
    summed_action = np.asarray(compact.pop("summed_group_action"))
    restricted_residual = float(
        np.linalg.norm(summed_action - energy * restricted_state)
    )
    if restricted_residual > 1e-8:
        raise RuntimeError(
            f"{name}: restricted ground residual is {restricted_residual}"
        )

    hashes = _group_hashes(groups, hamiltonian)
    system = {
        "name": name,
        "num_qubits": 2 * ncas,
        "groups": groups,
        "state": restricted_state,
        "energy": energy,
        "component_spectra": spectra,
    }
    metadata = {
        "name": name,
        "geometry_angstrom": spec["geometry"],
        "basis": str(spec["basis"]),
        "charge": int(spec["charge"]),
        "multiplicity": int(spec["multiplicity"]),
        "total_electron_count": int(molecule.nelectron),
        "active_electron_count": int(nelecas),
        "n_alpha": int(n_alpha),
        "n_beta": int(n_beta),
        "frozen_core_spatial_orbitals": int(ncore),
        "locked_core_spatial_orbitals": 0,
        "active_spatial_orbitals": int(ncas),
        "active_spatial_orbital_indices": active_indices,
        "active_orbital_selection_rule": (
            "ascending canonical RHF/ROHF MO index after frozen core"
        ),
        "num_qubits": int(2 * ncas),
        "population_sector_dimension": int(basis.size),
        "restricted_dimension": int(restricted_basis.size),
        "group_count": len(groups),
        "nonidentity_pauli_term_count": sum(
            1 for term in hamiltonian.terms if term
        ),
        "ground_energy_without_constant_hartree": energy,
        "removed_constant_hartree": constant,
        "ground_residual_2_norm": ground_residual,
        "restricted_ground_residual_2_norm": restricted_residual,
        "z2_mask": int(mask),
        "z2_target": int(target),
        "z2_symmetry": symmetry,
        "numerical_hermitization": numerical_hermitization,
        "component_representation": compact,
        "scf_energy_hartree": float(mean_field.e_tot),
        "scf_converged": bool(mean_field.converged),
        "preparation_seconds": float(time.perf_counter() - started),
        **hashes,
    }
    return system, metadata

def _rotation_count(system: dict[str, Any], sequence: Sequence[float]) -> int:
    counts = [sum(1 for term in group.terms if term) for group in system["groups"]]
    return int(
        sum(
            counts[group_index]
            for group_index, _ in iter_s2_sequence_steps(len(counts), sequence)
        )
    )


def _apply_pf_components(
    spectra: Sequence[ComponentSpectrum],
    sequence: Sequence[float],
    time_value: float,
    state: np.ndarray,
) -> np.ndarray:
    current = np.asarray(state, dtype=np.complex128).copy()
    gates: dict[tuple[int, float], Any] = {}
    for group_index, raw_weight in iter_s2_sequence_steps(
        len(spectra), sequence
    ):
        key = (int(group_index), float(raw_weight))
        gate = gates.get(key)
        if gate is None:
            gate = component_exponential(
                spectra[group_index], float(time_value) * float(raw_weight)
            )
            gates[key] = gate
        current = gate @ current
    return current


def _build_pf_unitary_cpu(
    spectra: Sequence[ComponentSpectrum],
    sequence: Sequence[float],
    time_value: float,
):
    started = time.perf_counter()
    unitary = np.eye(spectra[0].dimension, dtype=np.complex128)
    gates: dict[tuple[int, float], Any] = {}
    materialization_seconds = 0.0
    multiplication_seconds = 0.0
    for group_index, raw_weight in iter_s2_sequence_steps(
        len(spectra), sequence
    ):
        key = (int(group_index), float(raw_weight))
        gate = gates.get(key)
        if gate is None:
            gate_started = time.perf_counter()
            gate = component_exponential(
                spectra[group_index], float(time_value) * float(raw_weight)
            )
            materialization_seconds += time.perf_counter() - gate_started
            gates[key] = gate
        multiplication_started = time.perf_counter()
        unitary = gate @ unitary
        multiplication_seconds += time.perf_counter() - multiplication_started
    return unitary, {
        "cpu_total_build_seconds": float(time.perf_counter() - started),
        "component_gate_materialization_seconds": float(
            materialization_seconds
        ),
        "sparse_dense_multiplication_seconds": float(multiplication_seconds),
        "unique_component_gate_count": len(gates),
    }


def _qualify_fit(times: Sequence[float], errors: Sequence[float]):
    windows = rolling_loglog_fits(
        np.asarray(times),
        np.asarray(errors),
        formal_order=FORMAL_ORDER,
        noise_floor=FIT_NOISE_FLOOR,
        window_size=FIT_WINDOW,
    )
    eligible = [
        window
        for window in windows
        if float(window["order_deviation"]) <= FIT_ORDER_TOLERANCE
        and float(window["r2"]) >= FIT_MINIMUM_R2
    ]
    selected = min(
        eligible, key=lambda window: int(window["start_index"]), default=None
    )
    return {
        "qualified": selected is not None,
        "selected_window": selected,
        "evaluated_windows": windows,
        "times": list(map(float, times)),
        "errors_hartree": list(map(float, errors)),
        "noise_floor": FIT_NOISE_FLOOR,
        "order_tolerance": FIT_ORDER_TOLERANCE,
        "minimum_r2": FIT_MINIMUM_R2,
        "window_size": FIT_WINDOW,
        "formal_order": FORMAL_ORDER,
    }


def _short_time_fit(
    system: dict[str, Any], sequence: Sequence[float], checkpoint: Any
):
    points: list[dict[str, Any]] = []
    errors: list[float] = []
    fit = None
    started = time.perf_counter()
    for time_value in FIT_GRID:
        point_started = time.perf_counter()
        evolved = _apply_pf_components(
            system["component_spectra"],
            sequence,
            float(time_value),
            system["state"],
        )
        overlap = complex(np.vdot(system["state"], evolved))
        rotated = (
            np.exp(-1j * float(system["energy"]) * float(time_value))
            * overlap
        )
        error = abs(float(rotated.imag / float(time_value)))
        errors.append(error)
        points.append(
            {
                "time": float(time_value),
                "perturbative_error_hartree": error,
                "phase_rotated_overlap": rotated,
                "survival_probability": float(abs(rotated) ** 2),
                "evolved_state_norm": float(np.linalg.norm(evolved)),
                "elapsed_seconds": float(time.perf_counter() - point_started),
            }
        )
        if len(points) >= FIT_WINDOW:
            fit = _qualify_fit(
                [point["time"] for point in points], errors
            )
        checkpoint({"points": points, "qualification": fit})
        if fit is not None and fit["qualified"]:
            break
    if fit is None or not fit["qualified"]:
        raise RuntimeError(
            "common short-time fit did not qualify on the declared grid"
        )
    fit["points"] = points
    fit["elapsed_seconds"] = float(time.perf_counter() - started)
    fit["error_definition"] = (
        "abs(imag(exp(-i*E0*t)*<psi0|U_PF(t)|psi0>)/t)"
    )
    return fit


def _analytic_time(alpha: float) -> float:
    return float(
        (EPSILON_E / ((FORMAL_ORDER + 1) * float(alpha)))
        ** (1.0 / FORMAL_ORDER)
    )


def _cost(time_value: float, error: float, rotations: int):
    if time_value <= 0.0 or error < 0.0 or error >= EPSILON_E:
        return None
    return float(
        float(BETA)
        * int(rotations)
        / (float(time_value) * (EPSILON_E - float(error)))
    )


def _direct_point(
    system: dict[str, Any],
    sequence: Sequence[float],
    time_value: float,
    rotations: int,
):
    started = time.perf_counter()
    unitary, build = _build_pf_unitary_cpu(
        system["component_spectra"], sequence, float(time_value)
    )
    schur_started = time.perf_counter()
    triangular, vectors = schur(
        unitary, output="complex", check_finite=False
    )
    schur_seconds = time.perf_counter() - schur_started
    eigenvalues = np.diag(triangular)
    overlaps = np.abs(vectors.conj().T @ system["state"]) ** 2
    selected = int(np.argmax(overlaps))
    eigenvalue = complex(eigenvalues[selected])
    vector = vectors[:, selected]
    signed_shift = float(
        np.angle(
            np.exp(-1j * float(system["energy"]) * float(time_value))
            * eigenvalue
        )
        / float(time_value)
    )
    residual = float(
        np.linalg.norm(unitary @ vector - eigenvalue * vector)
    )
    point = {
        "time": float(time_value),
        "signed_direct_shift_hartree": signed_shift,
        "direct_error_hartree": abs(signed_shift),
        "direct_cost": _cost(float(time_value), abs(signed_shift), rotations),
        "selection_rule": (
            "maximum exact-ground-state overlap; overlap phase is diagnostic only"
        ),
        "selected_schur_index": selected,
        "selected_eigenvalue": eigenvalue,
        "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
        "ground_overlap_probability": float(overlaps[selected]),
        "eigenpair_residual_2_norm": residual,
        "schur_off_diagonal_residual_frobenius_norm": float(
            np.linalg.norm(triangular - np.diag(eigenvalues))
        ),
        "timing_seconds": {
            **build,
            "cpu_schur": float(schur_seconds),
            "total": float(time.perf_counter() - started),
        },
    }
    del unitary, vectors, triangular
    return point


def _fit_two_term(
    training_points: Sequence[dict[str, Any]],
    alpha: float,
    analytic_time: float,
):
    ordered = sorted(
        training_points, key=lambda point: float(point["relative_to_t_ana"])
    )
    relative = np.asarray(
        [float(point["relative_to_t_ana"]) for point in ordered]
    )
    times = np.asarray([float(point["time"]) for point in ordered])
    shifts = np.asarray(
        [float(point["signed_direct_shift_hartree"]) for point in ordered]
    )
    leading_sign = float(np.sign(np.median(shifts)))
    if leading_sign == 0.0:
        raise RuntimeError("zero leading sign in two-term fit")
    normalized = shifts / (
        leading_sign * float(alpha) * times**FORMAL_ORDER
    )
    design = np.column_stack([np.ones_like(relative), relative**2])
    b0, b2 = np.linalg.lstsq(design, normalized, rcond=None)[0]
    a4 = float(leading_sign * float(alpha) * float(b0))
    a6 = float(
        leading_sign
        * float(alpha)
        * float(b2)
        / float(analytic_time) ** 2
    )
    return {
        "model": "delta_E_2term(t) = a4*t^4 + a6*t^6",
        "cost_model": (
            "beta*N_exp / (t*(epsilon_E - abs(a4*t^4+a6*t^6)))"
        ),
        "fit_rule": (
            "least squares after normalization by sign*alpha*t^4, "
            "as in committed two-term analysis"
        ),
        "training_relative_to_t_ana": list(TRAINING_RELATIVE_TIMES),
        "leading_sign": leading_sign,
        "normalized_b0": float(b0),
        "normalized_b2": float(b2),
        "a4": a4,
        "a6": a6,
    }


def _model_prediction(model: dict[str, Any], time_value: float) -> float:
    return float(
        model["a4"] * float(time_value) ** 4
        + model["a6"] * float(time_value) ** 6
    )


def _model_optimum(
    model: dict[str, Any], analytic_time: float, rotations: int
):
    relative = np.linspace(
        MODEL_OPTIMIZATION_INTERVAL[0],
        MODEL_OPTIMIZATION_INTERVAL[1],
        MODEL_OPTIMIZATION_POINTS,
    )
    times = relative * float(analytic_time)
    shifts = model["a4"] * times**4 + model["a6"] * times**6
    errors = np.abs(shifts)
    costs = np.full(times.shape, np.inf)
    valid = errors < EPSILON_E
    costs[valid] = (
        float(BETA)
        * int(rotations)
        / (times[valid] * (EPSILON_E - errors[valid]))
    )
    selected = int(np.argmin(costs))
    if not np.isfinite(costs[selected]):
        raise RuntimeError(
            "two-term model has no finite optimum in the declared domain"
        )
    return {
        "optimization_domain_relative_to_t_ana": list(
            MODEL_OPTIMIZATION_INTERVAL
        ),
        "dense_grid_points": MODEL_OPTIMIZATION_POINTS,
        "relative_to_t_ana": float(relative[selected]),
        "time": float(times[selected]),
        "signed_shift_hartree": float(shifts[selected]),
        "error_hartree": float(errors[selected]),
        "cost": float(costs[selected]),
    }


def _add_direct(
    points: list[dict[str, Any]],
    relative_to_t_star: float,
    t_star: float,
    t_ana: float,
    system: dict[str, Any],
    sequence: Sequence[float],
    rotations: int,
    model: dict[str, Any],
    checkpoint: Any,
) -> None:
    target_time = float(relative_to_t_star) * float(t_star)
    if any(
        abs(float(point["time"]) - target_time)
        <= 1e-12 * max(1.0, target_time)
        for point in points
    ):
        return
    point = _direct_point(system, sequence, target_time, rotations)
    prediction = _model_prediction(model, target_time)
    point.update(
        {
            "relative_to_t_star": float(relative_to_t_star),
            "relative_to_t_ana": float(target_time / t_ana),
            "two_term_signed_shift_hartree": prediction,
            "two_term_error_hartree": abs(prediction),
            "two_term_cost": _cost(target_time, abs(prediction), rotations),
            "two_term_signed_residual_hartree": float(
                point["signed_direct_shift_hartree"] - prediction
            ),
            "two_term_residual_over_epsilon": float(
                abs(float(point["signed_direct_shift_hartree"]) - prediction)
                / EPSILON_E
            ),
        }
    )
    points.append(point)
    points.sort(key=lambda item: float(item["time"]))
    checkpoint(points)


def _local_direct_grid(
    system: dict[str, Any],
    sequence: Sequence[float],
    rotations: int,
    model: dict[str, Any],
    optimum: dict[str, Any],
    analytic_time: float,
    checkpoint: Any,
):
    points: list[dict[str, Any]] = []
    t_star = float(optimum["time"])
    for ratio in (0.9, 1.0, 1.1):
        _add_direct(
            points, ratio, t_star, analytic_time, system, sequence,
            rotations, model, checkpoint
        )
    finite = [point for point in points if point["direct_cost"] is not None]
    minimum = min(finite, key=lambda point: float(point["direct_cost"]))
    if abs(float(minimum["relative_to_t_star"]) - 1.0) < 1e-12:
        additions = (0.95, 1.05)
        initial_case = "center_minimum"
    elif float(minimum["relative_to_t_star"]) < 1.0:
        additions = (0.8,)
        initial_case = "lower_endpoint_minimum"
    else:
        additions = (1.2,)
        initial_case = "upper_endpoint_minimum"
    for ratio in additions:
        _add_direct(
            points, ratio, t_star, analytic_time, system, sequence,
            rotations, model, checkpoint
        )

    finite = sorted(
        [point for point in points if point["direct_cost"] is not None],
        key=lambda point: float(point["time"]),
    )
    minimum_index = min(
        range(len(finite)),
        key=lambda index: float(finite[index]["direct_cost"]),
    )
    bracketed_before = 0 < minimum_index < len(finite) - 1
    bisection_ratios: list[float] = []
    if bracketed_before:
        center_ratio = float(finite[minimum_index]["relative_to_t_star"])
        bisection_ratios = [
            0.5
            * (
                float(finite[minimum_index - 1]["relative_to_t_star"])
                + center_ratio
            ),
            0.5
            * (
                center_ratio
                + float(finite[minimum_index + 1]["relative_to_t_star"])
            ),
        ]
    elif minimum_index == 0 and len(finite) > 1:
        bisection_ratios = [
            0.5
            * (
                float(finite[0]["relative_to_t_star"])
                + float(finite[1]["relative_to_t_star"])
            )
        ]
    elif len(finite) > 1:
        bisection_ratios = [
            0.5
            * (
                float(finite[-2]["relative_to_t_star"])
                + float(finite[-1]["relative_to_t_star"])
            )
        ]
    for ratio in bisection_ratios:
        _add_direct(
            points, ratio, t_star, analytic_time, system, sequence,
            rotations, model, checkpoint
        )

    finite = sorted(
        [point for point in points if point["direct_cost"] is not None],
        key=lambda point: float(point["time"]),
    )
    minimum_index = min(
        range(len(finite)),
        key=lambda index: float(finite[index]["direct_cost"]),
    )
    return points, {
        "rule": {
            "initial": [0.9, 1.0, 1.1],
            "center_minimum_add": [0.95, 1.05],
            "endpoint_minimum_extend": [0.8, 1.2],
            "final_refinement": (
                "bisect each side of a bracketed minimum once; "
                "if censored, bisect the available edge"
            ),
        },
        "initial_case": initial_case,
        "bracketed_before_bisection": bool(bracketed_before),
        "bisection_relative_to_t_star": bisection_ratios,
        "direct_grid_minimum": finite[minimum_index],
        "final_grid_bracketed": bool(
            0 < minimum_index < len(finite) - 1
        ),
    }


def _formula_result(
    formula_name: str,
    weights: Sequence[float],
    system: dict[str, Any],
    formula_record: dict[str, Any],
    checkpoint: Any,
):
    sequence = symmetric_s2_sequence(weights)
    rotations = _rotation_count(system, sequence)
    formula_record.update(
        {
            "status": "short_time_fit",
            "weights": list(map(float, weights)),
            "formal_order": FORMAL_ORDER,
            "s2_sequence": sequence,
            "s2_stage_count": len(sequence),
            "rotations_per_pf_step": rotations,
        }
    )
    checkpoint()

    def fit_checkpoint(partial: dict[str, Any]) -> None:
        formula_record["short_time_fit_partial"] = partial
        checkpoint()

    fit = _short_time_fit(system, sequence, fit_checkpoint)
    formula_record.pop("short_time_fit_partial", None)
    alpha = float(fit["selected_window"]["fixed_order_alpha"])
    analytic_time = _analytic_time(alpha)
    formula_record.update(
        {
            "status": "training_direct_points",
            "short_time_fit": fit,
            "alpha": alpha,
            "analytic_time": analytic_time,
            "one_term_analytic_model_cost": _cost(
                analytic_time, alpha * analytic_time**4, rotations
            ),
            "training_direct_points": [],
        }
    )
    checkpoint()
    for relative in TRAINING_RELATIVE_TIMES:
        point = _direct_point(
            system, sequence, float(relative) * analytic_time, rotations
        )
        point.update(
            {
                "relative_to_t_ana": float(relative),
                "one_term_model_error_hartree": float(
                    alpha * point["time"] ** 4
                ),
                "used_for_two_term_fit": True,
            }
        )
        formula_record["training_direct_points"].append(point)
        checkpoint()

    model = _fit_two_term(
        formula_record["training_direct_points"], alpha, analytic_time
    )
    optimum = _model_optimum(model, analytic_time, rotations)
    formula_record.update(
        {
            "status": "local_direct_grid",
            "two_term_model": model,
            "two_term_model_optimum": optimum,
            "local_direct_points": [],
        }
    )
    checkpoint()

    def local_checkpoint(points: list[dict[str, Any]]) -> None:
        formula_record["local_direct_points"] = points
        checkpoint()

    local_points, local_analysis = _local_direct_grid(
        system, sequence, rotations, model, optimum, analytic_time,
        local_checkpoint
    )
    at_star = min(
        local_points,
        key=lambda point: abs(float(point["relative_to_t_star"]) - 1.0),
    )
    direct_minimum = local_analysis["direct_grid_minimum"]
    if at_star["direct_cost"] is None or direct_minimum["direct_cost"] is None:
        raise RuntimeError(
            f"{formula_name}: non-finite direct cost near optimum"
        )
    eta_star = (
        abs(float(optimum["cost"]) - float(at_star["direct_cost"]))
        / float(at_star["direct_cost"])
    )
    eta_min = (
        float(at_star["direct_cost"]) / float(direct_minimum["direct_cost"])
        - 1.0
    )
    eta_t = abs(
        float(optimum["time"]) / float(direct_minimum["time"]) - 1.0
    )
    maximum_residual = max(
        float(point["two_term_residual_over_epsilon"])
        for point in local_points
    )
    all_direct = formula_record["training_direct_points"] + local_points
    metrics = {
        "eta_star": eta_star,
        "eta_min": eta_min,
        "eta_t": eta_t,
        "eta_t_interpretation": (
            "grid-resolved reference; not a continuous optimum"
        ),
        "maximum_unseen_residual_over_epsilon": maximum_residual,
        "minimum_ground_overlap_probability": min(
            float(point["ground_overlap_probability"])
            for point in all_direct
        ),
        "maximum_eigenpair_residual_2_norm": max(
            float(point["eigenpair_residual_2_norm"])
            for point in all_direct
        ),
    }
    checks = {
        key: float(metrics[key]) <= threshold
        for key, threshold in PASS_THRESHOLDS.items()
    }
    formula_record.update(
        {
            "status": "complete",
            "local_direct_points": local_points,
            "local_grid_analysis": local_analysis,
            "metrics": metrics,
            "threshold_checks": checks,
            "passed": all(checks.values()),
        }
    )
    checkpoint()
    return formula_record


def worker(args: argparse.Namespace) -> int:
    output = Path(args.output)
    work_dir = output.parent / (output.stem + "_work")
    work_dir.mkdir(parents=True, exist_ok=True)
    spec = CONDITIONS[str(args.condition)]
    payload: dict[str, Any] = {
        "status": "running",
        "started_at": _now(),
        "condition": str(args.condition),
        "selection_provenance": {
            "candidate_narrowing": ["H2", "H4", "H5"],
            "final_selection": [
                "LiH x 3 bases", "BeH2 x 3 bases", "H2O x 3 bases"
            ],
            "unused_holdouts": ["H6", "H7", "NH3 x 3 bases"],
        },
        "git": _git_state(),
        "environment": {
            "python": platform.python_version(),
            "python_executable": os.path.realpath(sys.executable),
            "packages": _package_versions(),
            "blas_threads": int(args.blas_threads),
            "component_processes": int(args.component_processes),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        },
        "protocol": {
            "epsilon_E_hartree": EPSILON_E,
            "beta": float(BETA),
            "short_time_fit_grid": FIT_GRID,
            "training_relative_to_t_ana": TRAINING_RELATIVE_TIMES,
            "model_optimization_interval_relative_to_t_ana": (
                MODEL_OPTIMIZATION_INTERVAL
            ),
            "pass_thresholds": PASS_THRESHOLDS,
            "direct_label": (
                "ground-connected maximum-ground-overlap PF eigenbranch"
            ),
            "signed_quantity": (
                "delta_E_direct(t) = E_tilde_g(t) - E0"
            ),
            "unsigned_quantity": (
                "e_direct(t) = abs(delta_E_direct(t))"
            ),
        },
        "system": None,
        "formulas": {},
    }

    def checkpoint() -> None:
        _atomic_json(output, payload)

    checkpoint()
    started = time.perf_counter()
    try:
        print(f"{args.condition}: preparing active-space system", flush=True)
        system, metadata = _prepare_system(
            str(args.condition),
            spec,
            work_dir,
            int(args.component_processes),
        )
        payload["system"] = metadata
        payload["status"] = "formulas"
        checkpoint()
        print(
            f"{args.condition}: sector "
            f"{metadata['population_sector_dimension']} -> "
            f"{metadata['restricted_dimension']}, "
            f"groups={metadata['group_count']}",
            flush=True,
        )
        for formula_name, weights in FORMULAS.items():
            print(f"{args.condition}: {formula_name}", flush=True)
            formula_record: dict[str, Any] = {}
            payload["formulas"][formula_name] = formula_record
            _formula_result(
                formula_name, weights, system, formula_record, checkpoint
            )

        candidate = payload["formulas"]["two_term_center"]
        current = payload["formulas"]["current_m3"]
        candidate_cost = float(
            min(
                candidate["local_direct_points"],
                key=lambda point: abs(
                    float(point["relative_to_t_star"]) - 1.0
                ),
            )["direct_cost"]
        )
        current_cost = float(
            min(
                current["local_direct_points"],
                key=lambda point: abs(
                    float(point["relative_to_t_star"]) - 1.0
                ),
            )["direct_cost"]
        )
        payload["comparison"] = {
            "direct_cost_at_each_formulas_own_predicted_optimum_ratio_new_over_current": (
                candidate_cost / current_cost
            ),
            "prediction_metrics": {
                name: payload["formulas"][name]["metrics"]
                for name in FORMULAS
            },
            "cost_and_prediction_are_reported_separately": True,
        }
        payload.update(
            {
                "status": "complete",
                "completed_at": _now(),
                "elapsed_seconds": float(time.perf_counter() - started),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
            }
        )
        checkpoint()
        print(f"{args.condition}: complete", flush=True)
        return 0
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "completed_at": _now(),
                "elapsed_seconds": float(time.perf_counter() - started),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
            }
        )
        checkpoint()
        traceback.print_exc()
        return 1


def _read_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "queued"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "temporarily_unreadable", "error": str(exc)}
    formulas = payload.get("formulas", {})
    return {
        "status": payload.get("status"),
        "system": payload.get("system"),
        "formula_status": {
            name: value.get("status") for name, value in formulas.items()
        },
        "formula_training_points": {
            name: len(value.get("training_direct_points", []))
            for name, value in formulas.items()
        },
        "formula_local_points": {
            name: len(value.get("local_direct_points", []))
            for name, value in formulas.items()
        },
        "error": payload.get("error"),
    }


def _resource_snapshot() -> dict[str, Any]:
    commands = {
        "lscpu": ["lscpu"],
        "free": ["free", "-h"],
        "uptime": ["uptime"],
        "nvidia_smi": [
            "nvidia-smi",
            "--query-gpu="
            "index,name,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader",
        ],
    }
    result = {}
    for name, command in commands.items():
        completed = subprocess.run(
            command, text=True, capture_output=True, check=False
        )
        result[name] = {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    return result


def _aggregate(output_dir: Path) -> dict[str, Any]:
    records = {}
    for condition in CONDITIONS:
        path = output_dir / f"{condition}.json"
        records[condition] = json.loads(path.read_text(encoding="utf-8"))
    all_complete = all(
        record.get("status") == "complete" for record in records.values()
    )
    new_checks = {
        condition: (
            record.get("formulas", {})
            .get("two_term_center", {})
            .get("threshold_checks", {})
        )
        for condition, record in records.items()
    }
    summary = {
        "status": "complete" if all_complete else "failed",
        "completed_at": _now(),
        "git": _git_state(),
        "condition_status": {
            name: record.get("status") for name, record in records.items()
        },
        "new_candidate_checks": new_checks,
        "new_candidate_all_five_conditions_passed": bool(
            all_complete
            and all(
                checks and all(checks.values())
                for checks in new_checks.values()
            )
        ),
        "records": {
            condition: {
                "system": record.get("system"),
                "comparison": record.get("comparison"),
                "formula_summaries": {
                    name: {
                        "weights": formula.get("weights"),
                        "alpha": formula.get("alpha"),
                        "analytic_time": formula.get("analytic_time"),
                        "two_term_model": formula.get("two_term_model"),
                        "two_term_model_optimum": formula.get(
                            "two_term_model_optimum"
                        ),
                        "metrics": formula.get("metrics"),
                        "threshold_checks": formula.get("threshold_checks"),
                        "passed": formula.get("passed"),
                    }
                    for name, formula in record.get("formulas", {}).items()
                },
            }
            for condition, record in records.items()
        },
    }
    _atomic_json(output_dir / "summary.json", summary)
    return summary


def _write_report(output_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Fixed m=3 two-term PF holdout validation",
        "",
        f"Status: {summary['status']}",
        "",
        (
            "The coefficients were fixed before H6, H7, and NH3 were "
            "evaluated. These holdouts were not used for coefficient selection."
        ),
        "",
        (
            "| condition | formula | eta_* | eta_min | eta_t | "
            "max unseen residual / epsilon | pass |"
        ),
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for condition, record in summary["records"].items():
        for formula_name, formula in record["formula_summaries"].items():
            metrics = formula.get("metrics") or {}
            lines.append(
                f"| {condition} | {formula_name} | "
                f"{metrics.get('eta_star', float('nan')):.6g} | "
                f"{metrics.get('eta_min', float('nan')):.6g} | "
                f"{metrics.get('eta_t', float('nan')):.6g} | "
                f"{metrics.get('maximum_unseen_residual_over_epsilon', float('nan')):.6g} | "
                f"{formula.get('passed')} |"
            )
    lines.extend(
        [
            "",
            (
                "eta_t is resolved only on the declared local grid and is not "
                "claimed as a continuous optimum."
            ),
            (
                "Costs and prediction errors are retained separately in each "
                "condition JSON and in summary.json."
            ),
            "",
        ]
    )
    (output_dir / "report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def launch(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "running",
        "started_at": _now(),
        "git": _git_state(),
        "conditions": list(CONDITIONS),
        "execution_strategy": {
            "backend": (
                "CPU exact sector PF build plus CPU complex Schur"
            ),
            "condition_workers": int(args.condition_workers),
            "blas_threads_per_worker": int(args.blas_threads),
            "component_processes_per_condition": int(
                args.component_processes
            ),
            "numa_policy": (
                "OS placement; no exclusive-core or memory binding "
                "on the shared server"
            ),
            "gpu_decision": (
                "GPU 0/1 occupied by the ongoing H14 validation and GPU 2/3 "
                "occupied by another user at launch; no GPU process was "
                "interrupted or displaced"
            ),
            "adaptation": (
                "EPYC 7532 x2 has 64 physical cores and about 503 GiB RAM, "
                "so concurrency is reduced from the 128-core/1-TiB premise"
            ),
        },
        "resource_snapshot": _resource_snapshot(),
        "progress_file": str(output_dir / "progress.json"),
    }
    _atomic_json(output_dir / "run_manifest.json", manifest)

    queue = list(CONDITIONS)
    running: dict[str, tuple[subprocess.Popen[Any], Any]] = {}
    failures: dict[str, int] = {}
    environment = os.environ.copy()
    environment.update(
        {
            "OPENBLAS_NUM_THREADS": str(int(args.blas_threads)),
            "OMP_NUM_THREADS": str(int(args.blas_threads)),
            "MKL_NUM_THREADS": str(int(args.blas_threads)),
            "NUMEXPR_NUM_THREADS": str(int(args.blas_threads)),
            "CUDA_VISIBLE_DEVICES": "",
            "TMPDIR": str(output_dir / "tmp"),
        }
    )
    (output_dir / "tmp").mkdir()
    while queue or running:
        while queue and len(running) < int(args.condition_workers):
            condition = queue.pop(0)
            log_handle = (output_dir / f"{condition}.log").open(
                "a", encoding="utf-8", buffering=1
            )
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "worker",
                "--condition",
                condition,
                "--output",
                str(output_dir / f"{condition}.json"),
                "--blas-threads",
                str(int(args.blas_threads)),
                "--component-processes",
                str(int(args.component_processes)),
            ]
            process = subprocess.Popen(
                command,
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=False,
            )
            running[condition] = (process, log_handle)
            print(
                f"started {condition}: pid={process.pid}", flush=True
            )
        progress = {
            "updated_at": _now(),
            "queued": list(queue),
            "running": {
                condition: process.pid
                for condition, (process, _) in running.items()
            },
            "failures": failures,
            "conditions": {
                condition: _read_status(
                    output_dir / f"{condition}.json"
                )
                for condition in CONDITIONS
            },
        }
        _atomic_json(output_dir / "progress.json", progress)
        if not running:
            continue
        time.sleep(float(args.poll_seconds))
        for condition, (process, log_handle) in list(running.items()):
            returncode = process.poll()
            if returncode is None:
                continue
            log_handle.close()
            del running[condition]
            if returncode != 0:
                failures[condition] = int(returncode)
            print(
                f"finished {condition}: returncode={returncode}",
                flush=True,
            )

    summary = _aggregate(output_dir)
    _write_report(output_dir, summary)
    manifest.update(
        {
            "status": summary["status"],
            "completed_at": _now(),
            "failures": failures,
            "summary": str(output_dir / "summary.json"),
            "report": str(output_dir / "report.md"),
        }
    )
    _atomic_json(output_dir / "run_manifest.json", manifest)
    return 0 if summary["status"] == "complete" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument(
        "--condition", choices=list(CONDITIONS), required=True
    )
    worker_parser.add_argument("--output", type=Path, required=True)
    worker_parser.add_argument("--blas-threads", type=int, default=2)
    worker_parser.add_argument(
        "--component-processes", type=int, default=1
    )
    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument("--output-dir", type=Path, required=True)
    launch_parser.add_argument(
        "--condition-workers", type=int, default=2
    )
    launch_parser.add_argument("--blas-threads", type=int, default=2)
    launch_parser.add_argument(
        "--component-processes", type=int, default=1
    )
    launch_parser.add_argument("--poll-seconds", type=float, default=15.0)
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    if parsed.command == "worker":
        raise SystemExit(worker(parsed))
    raise SystemExit(launch(parsed))
