"""Run the frozen F01/F02/F05 full-electron HF mechanism bridge.

The runner consumes the exact H01 pickle caches.  F01 matrix-log and F05
eigendecomposition points are predeclared mechanism diagnostics and are never
used to refit an error model, update a cost decision, or alter the committed
success/failure labels.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import resource
import subprocess
import time
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from flint import acb, acb_mat, ctx as flint_ctx
from scipy.linalg import expm, logm, schur
from scipy.optimize import linear_sum_assignment

from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _relative_matrix_error,
    _sha256,
    _write_csv,
    fit_even_effective_operators,
    operator_decomposition,
)
from review_response.audit_f02_tau8_state_mixing import (
    decompose_a8_state_mixing,
)
from review_response.bch_matrix_series import eigenenergy_perturbation_series
import review_response.run_full_electron_nh3_higher_term_diagnosis as diagnosis
import review_response.run_h01_approximate_state_calibration as h01
from trotterlib.pf_decomposition import iter_s2_sequence_steps


PROTOCOL_PATH = Path(__file__).with_name("f_hf_mechanism_bridge_protocol.json")
EXPECTED_PROTOCOL_SHA256 = (
    "2b239b180c5fffe3c79e492220b344bfdec15e9a9f4d37259b9b815b52de26f4"
)
CONDITIONS = ("HF_full_eq_sto3g", "HF_full_stretch150_sto3g")
FORMULAE = ("yoshida4", "current_m3")
REQUIRED_ORDERS = (4, 6, 8)
FIT_ORDERS = (4, 6, 8, 10, 12)
FORMAL_MAXIMUM_ORDER = 8
TIME_RTOL = 1e-12
NEW_DIRECT_TRUTH_POINT_COUNT = 0
ARB_PRECISION_BITS = 128
FORMAL_IDENTITY_GAUGE = "per_group_spectral_midpoint"
FINITE_LOG_BRANCH_METHOD = "exact_hamiltonian_reference_unwrap"


class SourceIdentityError(RuntimeError):
    """The required H01 cache is absent or does not have the frozen identity."""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _protocol() -> dict[str, Any]:
    digest = _sha256(PROTOCOL_PATH)
    if digest != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError(f"bridge protocol hash mismatch: {digest}")
    return _load_json(PROTOCOL_PATH)


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _versions() -> dict[str, Any]:
    packages: dict[str, str | None] = {}
    for package in (
        "numpy",
        "scipy",
        "matplotlib",
        "mpmath",
        "python-flint",
        "openfermion",
        "pyscf",
    ):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": packages,
    }


def reconstruct_component_spectrum(spectrum: Any) -> np.ndarray:
    """Reconstruct one dense grouped Hamiltonian from ComponentSpectrum."""

    result = np.zeros((int(spectrum.dimension), int(spectrum.dimension)), dtype=np.complex128)
    for batch in spectrum.batches:
        indices = np.asarray(batch.indices, dtype=int)
        eigenvalues = np.asarray(batch.eigenvalues, dtype=float)
        if batch.eigenvectors is None:
            if indices.shape[1] != 1 or eigenvalues.shape[1] != 1:
                raise ValueError("eigenvectors may be omitted only for 1x1 blocks")
            result[indices[:, 0], indices[:, 0]] += eigenvalues[:, 0]
            continue
        vectors = np.asarray(batch.eigenvectors, dtype=np.complex128)
        if vectors.shape[:2] != indices.shape:
            raise ValueError("ComponentBatch eigenvector shape disagrees with indices")
        for block_indices, values, block_vectors in zip(
            indices, eigenvalues, vectors, strict=True
        ):
            block = (block_vectors * values[None, :]) @ block_vectors.conj().T
            result[np.ix_(block_indices, block_indices)] += block
    return (result + result.conj().T) / 2.0


def reconstruct_group_matrices(system: dict[str, Any]) -> list[np.ndarray]:
    return [
        reconstruct_component_spectrum(spectrum)
        for spectrum in system["component_spectra"]
    ]


def _frobenius(matrix: np.ndarray) -> float:
    array = np.asarray(matrix)
    squared = np.sum(np.abs(array) ** 2, dtype=np.longdouble)
    return float(np.sqrt(squared))


def _relative(value: np.ndarray, reference: np.ndarray) -> float:
    return _frobenius(np.asarray(value) - np.asarray(reference)) / max(
        _frobenius(reference), 1e-300
    )


def _multiply_series(
    left: Sequence[np.ndarray], right: Sequence[np.ndarray], maximum_degree: int,
    dtype: np.dtype[Any],
) -> list[np.ndarray]:
    dimension = int(left[0].shape[0])
    result = [
        np.zeros((dimension, dimension), dtype=dtype)
        for _ in range(maximum_degree + 1)
    ]
    for degree in range(maximum_degree + 1):
        for left_degree in range(degree + 1):
            result[degree] += left[left_degree] @ right[degree - left_degree]
    return result


def effective_hamiltonian_series_dtype(
    group_matrices: Sequence[np.ndarray],
    steps: Sequence[tuple[int, float]],
    maximum_effective_order: int,
    dtype: np.dtype[Any] | type[np.complexfloating[Any, Any]],
) -> list[np.ndarray]:
    """Formal ordered-product log using either complex128 or clongdouble."""

    requested_dtype = np.dtype(dtype)
    matrices = [np.asarray(matrix, dtype=requested_dtype) for matrix in group_matrices]
    dimension = int(matrices[0].shape[0])
    maximum_degree = int(maximum_effective_order) + 1
    identity = np.eye(dimension, dtype=requested_dtype)
    zero = lambda: np.zeros((dimension, dimension), dtype=requested_dtype)
    product = [zero() for _ in range(maximum_degree + 1)]
    product[0] = identity
    imaginary = requested_dtype.type(1j)
    for group_index, raw_weight in steps:
        generator = imaginary * requested_dtype.type(raw_weight) * matrices[int(group_index)]
        exponential = [zero() for _ in range(maximum_degree + 1)]
        exponential[0] = identity
        for degree in range(1, maximum_degree + 1):
            exponential[degree] = exponential[degree - 1] @ generator / degree
        product = _multiply_series(
            exponential, product, maximum_degree, requested_dtype
        )
    x_series = [np.array(value, copy=True) for value in product]
    x_series[0] -= identity
    logarithm = [zero() for _ in range(maximum_degree + 1)]
    power = [np.array(value, copy=True) for value in x_series]
    for exponent in range(1, maximum_degree + 1):
        scale = requested_dtype.type((1.0 if exponent % 2 else -1.0) / exponent)
        for degree in range(1, maximum_degree + 1):
            logarithm[degree] += scale * power[degree]
        if exponent != maximum_degree:
            power = _multiply_series(power, x_series, maximum_degree, requested_dtype)
    return [logarithm[degree + 1] / imaginary for degree in range(maximum_degree)]


def center_group_identity_components(
    group_matrices: Sequence[np.ndarray],
) -> tuple[list[np.ndarray], list[float], float]:
    """Remove a deterministic scalar identity gauge from every Hermitian group.

    Product-formula error operators are invariant under independent scalar
    shifts of the grouped Hamiltonians.  Using each group's spectral midpoint
    minimizes its operator norm and prevents those irrelevant identity phases
    from consuming the precision of the complex128/clongdouble cross-check.
    """

    if not group_matrices:
        raise ValueError("group_matrices must not be empty")
    dimension = int(np.asarray(group_matrices[0]).shape[0])
    identity = np.eye(dimension, dtype=np.complex128)
    centered: list[np.ndarray] = []
    shifts: list[float] = []
    for raw_matrix in group_matrices:
        matrix = np.asarray(raw_matrix, dtype=np.complex128)
        eigenvalues = np.linalg.eigvalsh(matrix)
        shift = float((eigenvalues[0] + eigenvalues[-1]) / 2.0)
        centered.append(matrix - shift * identity)
        shifts.append(shift)
    return centered, shifts, float(sum(shifts))


def _acb_matrix_from_numpy(matrix: np.ndarray) -> acb_mat:
    array = np.asarray(matrix, dtype=np.complex128)
    return acb_mat([[complex(value) for value in row] for row in array])


def _acb_zero(dimension: int) -> acb_mat:
    return acb_mat(int(dimension), int(dimension))


def _acb_identity(dimension: int) -> acb_mat:
    return acb_mat(
        [
            [1 if row == column else 0 for column in range(int(dimension))]
            for row in range(int(dimension))
        ]
    )


def _multiply_acb_series(
    left: Sequence[acb_mat],
    right: Sequence[acb_mat],
    maximum_degree: int,
    dimension: int,
) -> list[acb_mat]:
    result = [_acb_zero(dimension) for _ in range(maximum_degree + 1)]
    for degree in range(maximum_degree + 1):
        for left_degree in range(degree + 1):
            result[degree] += left[left_degree] * right[degree - left_degree]
    return result


def effective_hamiltonian_series_arb(
    group_matrices: Sequence[np.ndarray],
    steps: Sequence[tuple[int, float]],
    maximum_effective_order: int,
    *,
    precision_bits: int = ARB_PRECISION_BITS,
) -> tuple[list[np.ndarray], list[float]]:
    """Return an Arb-ball reference for the formal PF logarithm.

    The required forbidden coefficients vanish through cancellations between
    matrices as large as the allowed D8 coefficient.  IEEE extended precision
    is therefore retained as a portability cross-check, while this independent
    ball-arithmetic evaluation supplies the numerical reference.
    """

    if not group_matrices or not steps:
        raise ValueError("group_matrices and steps must not be empty")
    dimension = int(np.asarray(group_matrices[0]).shape[0])
    maximum_degree = int(maximum_effective_order) + 1
    with flint_ctx.workprec(int(precision_bits)):
        matrices = [_acb_matrix_from_numpy(matrix) for matrix in group_matrices]
        identity = _acb_identity(dimension)
        product = [_acb_zero(dimension) for _ in range(maximum_degree + 1)]
        product[0] = identity
        exponential_cache: dict[tuple[int, float], list[acb_mat]] = {}
        for group_index, raw_weight in steps:
            key = (int(group_index), float(raw_weight))
            exponential = exponential_cache.get(key)
            if exponential is None:
                generator = matrices[key[0]] * acb(0, key[1])
                exponential = [
                    _acb_zero(dimension) for _ in range(maximum_degree + 1)
                ]
                exponential[0] = identity
                for degree in range(1, maximum_degree + 1):
                    exponential[degree] = (
                        exponential[degree - 1] * generator / degree
                    )
                exponential_cache[key] = exponential
            product = _multiply_acb_series(
                exponential, product, maximum_degree, dimension
            )

        x_series = [acb_mat(value) for value in product]
        x_series[0] -= identity
        logarithm = [_acb_zero(dimension) for _ in range(maximum_degree + 1)]
        power = [acb_mat(value) for value in x_series]
        for exponent in range(1, maximum_degree + 1):
            scale = acb(1 if exponent % 2 else -1) / exponent
            for degree in range(1, maximum_degree + 1):
                logarithm[degree] += power[degree] * scale
            if exponent != maximum_degree:
                power = _multiply_acb_series(
                    power, x_series, maximum_degree, dimension
                )

        effective = [
            logarithm[degree + 1] / acb(0, 1)
            for degree in range(maximum_degree)
        ]
        midpoint_matrices: list[np.ndarray] = []
        maximum_radii: list[float] = []
        for matrix in effective:
            midpoint = np.empty((dimension, dimension), dtype=np.complex128)
            radius = 0.0
            for row in range(dimension):
                for column in range(dimension):
                    value = matrix[row, column]
                    midpoint[row, column] = complex(value.mid())
                    radius = max(radius, float(value.rad()))
            midpoint_matrices.append(midpoint)
            maximum_radii.append(radius)
    return midpoint_matrices, maximum_radii


def _phase_cut_margin(unitary: np.ndarray) -> float:
    return float(np.min(np.pi - np.abs(np.angle(np.linalg.eigvals(unitary)))))


def circular_phase_gap(eigenvalues: Sequence[complex], selected: int) -> float:
    values = np.asarray(eigenvalues, dtype=np.complex128)
    if values.size < 2:
        raise ValueError("at least two eigenvalues are required")
    target = values[int(selected)]
    distances = np.abs(np.angle(values / target))
    distances[int(selected)] = np.inf
    return float(np.min(distances))


def diagnostic_annotations(source: str) -> dict[str, Any]:
    if source not in ("reused_committed_point", "new_predeclared_f05_diagnostic"):
        raise ValueError(source)
    return {
        "point_role": "f05_diagnostic_only",
        "used_as_direct_truth": False,
        "used_for_model_fit": False,
        "used_for_cost_validation": False,
        "source": source,
    }


def require_checks(checks: Sequence[dict[str, Any]], error_type: type[Exception]) -> None:
    failed = [check["check_id"] for check in checks if not check["passed"]]
    if failed:
        raise error_type("failed checks: " + ", ".join(failed))


def _source_identity(
    source_root: Path, protocol: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    if not (source_root / "COMPLETE").is_file():
        raise SourceIdentityError(f"missing H01 COMPLETE: {source_root}")
    summary_path = source_root / "aggregate/summary.json"
    if not summary_path.is_file():
        raise SourceIdentityError(f"missing H01 summary: {summary_path}")
    expected = {
        entry["condition"]: entry["expected_hamiltonian_sha256"]
        for entry in protocol["primary_controlled_pair"]
    }
    systems: dict[str, dict[str, Any]] = {}
    records = []
    checks = []
    for condition in CONDITIONS:
        pickle_path = source_root / "cache" / f"{condition}.pkl"
        metadata_path = pickle_path.with_suffix(".metadata.json")
        if not pickle_path.is_file() or not metadata_path.is_file():
            raise SourceIdentityError(f"missing H01 cache or metadata: {condition}")
        try:
            system = h01._load_system(pickle_path)
        except Exception as exc:
            raise SourceIdentityError(f"cannot validate H01 cache {condition}: {exc}") from exc
        metadata = _load_json(metadata_path)
        group_matrices = reconstruct_group_matrices(system)
        hamiltonian = np.asarray(system["hamiltonian"].toarray(), dtype=np.complex128)
        group_sum = sum(group_matrices, np.zeros_like(hamiltonian))
        group_error = _relative(group_sum, hamiltonian)
        expected_hash = expected[condition]
        condition_checks = {
            "internal_protocol_hash": system.get("protocol_sha256")
            == metadata.get("protocol_sha256"),
            "internal_hamiltonian_hash": system.get("hamiltonian_sha256")
            == expected_hash,
            "metadata_hamiltonian_hash": metadata.get("system", {}).get(
                "hamiltonian_sha256"
            )
            == expected_hash,
            "metadata_complete": metadata.get("status") == "complete",
            "group_sum": group_error
            <= float(protocol["numerical_gates"]["group_sum_relative_frobenius"]),
        }
        for check_id, passed in condition_checks.items():
            checks.append(
                {
                    "check_id": f"source_identity:{condition}:{check_id}",
                    "measured": group_error if check_id == "group_sum" else bool(passed),
                    "threshold": (
                        protocol["numerical_gates"]["group_sum_relative_frobenius"]
                        if check_id == "group_sum"
                        else True
                    ),
                    "comparison": "<=" if check_id == "group_sum" else "==",
                    "passed": bool(passed),
                }
            )
        records.append(
            {
                "condition": condition,
                "pickle_path": str(pickle_path.resolve()),
                "pickle_sha256": _sha256(pickle_path),
                "metadata_path": str(metadata_path.resolve()),
                "metadata_sha256": _sha256(metadata_path),
                "internal_protocol_sha256": system["protocol_sha256"],
                "internal_hamiltonian_sha256": system["hamiltonian_sha256"],
                "expected_hamiltonian_sha256": expected_hash,
                "group_count": len(group_matrices),
                "restricted_dimension": int(hamiltonian.shape[0]),
                "group_sum_relative_frobenius": group_error,
                "checks": condition_checks,
            }
        )
        system["bridge_group_matrices"] = group_matrices
        systems[condition] = system
    require_checks(checks, SourceIdentityError)
    source = {
        "absolute_path": str(source_root.resolve()),
        "summary_path": str(summary_path.resolve()),
        "summary_sha256": _sha256(summary_path),
        "systems": records,
    }
    return systems, source, checks


def _same_time(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=TIME_RTOL, abs_tol=0.0)


def _walk_direct_points(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if "time" in value and "signed_direct_shift_hartree" in value:
            yield value
        for child in value.values():
            yield from _walk_direct_points(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_direct_points(child)


def _committed_points(record: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for point in _walk_direct_points(record):
        if not any(
            _same_time(point["time"], existing["time"])
            and math.isclose(
                float(point["signed_direct_shift_hartree"]),
                float(existing["signed_direct_shift_hartree"]),
                rel_tol=0.0,
                abs_tol=1e-14,
            )
            for existing in result
        ):
            result.append(point)
    return result


def _find_committed_point(
    points: Sequence[dict[str, Any]], time_value: float
) -> dict[str, Any] | None:
    matches = [point for point in points if _same_time(point["time"], time_value)]
    if not matches:
        return None
    shifts = [float(point["signed_direct_shift_hartree"]) for point in matches]
    if max(shifts) - min(shifts) > 1e-12:
        raise RuntimeError("committed direct points disagree at the same time")
    return matches[0]


def _build_unitary(
    system: dict[str, Any], sequence: Sequence[float], time_value: float
) -> tuple[np.ndarray, dict[str, Any]]:
    return diagnosis._build_cpu(system, sequence, float(time_value))


def _finite_log_record(
    unitary: np.ndarray,
    time_value: float,
    exact_energies: np.ndarray,
    exact_vectors: np.ndarray,
) -> dict[str, Any]:
    """Recover a gauge-invariant continuous logarithm using exact-H branches.

    A principal matrix logarithm is not invariant under an energy-origin shift
    and necessarily encounters its cut once the full spectral width spans the
    circle.  Here the exact Hamiltonian is used only to choose the integer
    unwrap for each PF eigenphase.  The PF unitary supplies every finite-time
    value fitted below.
    """

    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    eigenvalues = np.diag(triangular)
    phases = np.angle(eigenvalues)
    overlaps = np.abs(np.asarray(exact_vectors).conj().T @ vectors) ** 2
    exact_indices, pf_indices = linear_sum_assignment(-overlaps)
    exact_for_pf = np.empty(len(exact_energies), dtype=int)
    exact_for_pf[pf_indices] = exact_indices
    reference_phases = np.asarray(exact_energies)[exact_for_pf] * float(time_value)
    relative_phases = np.angle(np.exp(1j * (phases - reference_phases)))
    unwrap_integers = np.rint(
        (reference_phases - phases) / (2.0 * np.pi)
    ).astype(int)
    unwrapped_phases = phases + 2.0 * np.pi * unwrap_integers
    unwrapped_energies = unwrapped_phases / float(time_value)
    effective = (vectors * unwrapped_energies[None, :]) @ vectors.conj().T
    effective = (effective + effective.conj().T) / 2.0

    principal_logarithm, principal_estimate = logm(unitary, disp=False)
    principal_raw = principal_logarithm / (1j * float(time_value))
    principal_effective = (principal_raw + principal_raw.conj().T) / 2.0
    return {
        "effective_hamiltonian": effective,
        "branch_method": FINITE_LOG_BRANCH_METHOD,
        "branch_cut_margin_radians": float(
            np.min(np.pi - np.abs(relative_phases))
        ),
        "principal_branch_cut_margin_radians": _phase_cut_margin(unitary),
        "minimum_reference_assignment_overlap_probability": float(
            np.min(overlaps[exact_indices, pf_indices])
        ),
        "maximum_reference_relative_phase_radians": float(
            np.max(np.abs(relative_phases))
        ),
        "minimum_phase_unwrap_integer": int(np.min(unwrap_integers)),
        "maximum_phase_unwrap_integer": int(np.max(unwrap_integers)),
        "raw_hermiticity_residual_frobenius": _frobenius(
            effective - effective.conj().T
        ),
        "principal_logm_error_estimate": float(principal_estimate),
        "principal_log_hermiticity_residual_frobenius": _frobenius(
            principal_raw - principal_raw.conj().T
        ),
        "principal_log_unitary_reconstruction_residual_frobenius": _frobenius(
            expm(1j * float(time_value) * principal_effective) - unitary
        ),
        "unitary_reconstruction_residual_frobenius": _frobenius(
            expm(1j * float(time_value) * effective) - unitary
        ),
    }


def _f05_point(
    unitary: np.ndarray,
    system: dict[str, Any],
    time_value: float,
    previous_vector: np.ndarray | None,
    committed: dict[str, Any] | None,
    tolerance: float,
) -> tuple[dict[str, Any], np.ndarray]:
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    eigenvalues = np.diag(triangular)
    state = np.asarray(system["state"], dtype=np.complex128)
    overlaps = np.abs(vectors.conj().T @ state) ** 2
    selected = int(np.argmax(overlaps))
    eigenvalue = complex(eigenvalues[selected])
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    phase = float(np.angle(eigenvalue))
    energy = float(system["energy"])
    unwrap = int(np.rint((energy * float(time_value) - phase) / (2.0 * np.pi)))
    selected_energy = (phase + 2.0 * np.pi * unwrap) / float(time_value)
    shift = float(selected_energy - energy)
    difference = (
        None
        if committed is None
        else abs(shift - float(committed["signed_direct_shift_hartree"]))
    )
    if difference is not None and difference > tolerance:
        raise RuntimeError(
            f"committed direct shift mismatch at t={time_value}: {difference}"
        )
    source = (
        "reused_committed_point"
        if committed is not None
        else "new_predeclared_f05_diagnostic"
    )
    point = {
        **diagnostic_annotations(source),
        "time": float(time_value),
        "signed_pf_eigenvalue_shift_hartree": shift,
        "committed_signed_shift_hartree": (
            None
            if committed is None
            else float(committed["signed_direct_shift_hartree"])
        ),
        "committed_shift_absolute_difference_hartree": difference,
        "ground_overlap_probability": float(overlaps[selected]),
        "adjacent_selected_vector_overlap_probability": (
            None
            if previous_vector is None
            else float(abs(np.vdot(previous_vector, vector)) ** 2)
        ),
        "phase_unwrap_integer": unwrap,
        "eigenpair_residual_2_norm": _frobenius(
            unitary @ vector - eigenvalue * vector
        ),
        "selected_phase_gap_radians": circular_phase_gap(eigenvalues, selected),
    }
    point["phase_gap_over_time_hartree"] = (
        point["selected_phase_gap_radians"] / float(time_value)
    )
    return point, vector


def _fit_direct_three_term(record: dict[str, Any]) -> dict[str, Any]:
    points = list(record["training_direct_points"][:5])
    times = np.asarray([point["time"] for point in points], dtype=float)
    shifts = np.asarray(
        [point["signed_direct_shift_hartree"] for point in points], dtype=float
    )
    scale = float(np.max(times))
    design = np.column_stack([(times / scale) ** order for order in (4, 6, 8)])
    scaled = np.linalg.lstsq(design, shifts, rcond=None)[0]
    coefficients = scaled / np.asarray([scale**order for order in (4, 6, 8)])
    residual = design @ scaled - shifts
    return {
        "point_count": len(points),
        "minimum_time": float(np.min(times)),
        "maximum_time": float(np.max(times)),
        "scaled_design_condition_number": float(np.linalg.cond(design)),
        "fitted_a4": float(coefficients[0]),
        "fitted_a6": float(coefficients[1]),
        "fitted_a8": float(coefficients[2]),
        "maximum_fit_residual_hartree": float(np.max(np.abs(residual))),
        "diagnostic_only": True,
        "used_to_refute_operator_decomposition": False,
    }


def _read_metrics(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _truth_label_rows(metrics: Sequence[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for condition in CONDITIONS:
        matches = [
            row
            for row in metrics
            if row["condition"] == condition
            and row["formula"] == "yoshida4"
            and row["model"] == "two_term_5point"
            and row["primary"] == "True"
        ]
        if len(matches) != 1:
            raise RuntimeError(f"missing unique committed label for {condition}")
        row = matches[0]
        rows.append(
            {
                "condition": condition,
                "formula": "yoshida4",
                "model": "two_term_5point",
                "committed_passed": row["passed"] == "True",
                "label_role": (
                    "two_term_success"
                    if condition.endswith("eq_sto3g")
                    else "two_term_failure"
                ),
                "label_changed": False,
            }
        )
    expected = [True, False]
    if [row["committed_passed"] for row in rows] != expected:
        raise RuntimeError(f"committed HF labels differ from protocol: {rows}")
    return rows


def _plot_operator(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    selected = [row for row in rows if row["order"] in (4, 8)]
    labels = [
        f"{row['condition'].replace('HF_full_', '').replace('_sto3g', '')}\n"
        f"{row['formula']} D{row['order']}"
        for row in selected
    ]
    values = [row["operator_frobenius_norm"] for row in selected]
    figure, axis = plt.subplots(figsize=(10.5, 4.5))
    axis.bar(np.arange(len(values)), values)
    axis.set_yscale("log")
    axis.set_ylabel("operator Frobenius norm")
    axis.set_xticks(np.arange(len(values)), labels, rotation=35, ha="right")
    axis.grid(True, axis="y", which="both", alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _plot_phase(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    figure, axis = plt.subplots(figsize=(8.2, 4.8))
    for condition in CONDITIONS:
        for formula in FORMULAE:
            subset = [
                row
                for row in rows
                if row["condition"] == condition and row["formula"] == formula
            ]
            subset.sort(key=lambda row: row["relative_to_t_ana"])
            axis.plot(
                [row["relative_to_t_ana"] for row in subset],
                [row["phase_gap_over_time_hartree"] for row in subset],
                marker="o",
                markersize=3,
                label=f"{condition}:{formula}",
            )
    axis.set_yscale("log")
    axis.set_xlabel("t / t_ana")
    axis.set_ylabel("nearest PF phase gap / t [Hartree]")
    axis.grid(True, which="both", alpha=0.25)
    axis.legend(frameon=False, fontsize=7)
    figure.tight_layout()
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    comparison = audit["condition_comparison"]
    finite_log_rows = audit["finite_log_diagnostics"]
    primary = [row for row in comparison if row["formula"] == "yoshida4"]
    eq = next(row for row in primary if row["condition"].endswith("eq_sto3g"))
    stretch = next(
        row for row in primary if row["condition"].endswith("stretch150_sto3g")
    )
    lines = [
        "# F01/F02/F05 full-electron HF mechanism bridge",
        "",
        f"Status: **{audit['status']}**",
        "",
        "The committed Yoshida-4/two-term labels are reused unchanged: HF "
        "equilibrium passes and HF stretch150 fails. New truth points: **0**. "
        "The new matrix-log and eigendecomposition work is predeclared, "
        "diagnostic-only mechanism computation.",
        "",
        "## Retry-1 numerical remediation",
        "",
        "- Formal D4/D6/D8 operators use 128-bit Arb ball arithmetic. The "
        "required complex128/clongdouble comparison is evaluated after removing "
        "each group's scalar spectral midpoint; the scalar sum is restored to H0.",
        "- Finite-time matrix logarithms use exact-H eigenbranches only to choose "
        "phase unwrap integers. This convention is invariant under a global "
        "energy-origin shift; principal-log margins remain diagnostic fields.",
        "- Frozen PFs, time grids, thresholds, committed labels, and truth points "
        "are unchanged from the original protocol.",
        "",
        "## Source identity",
        "",
        f"- H01 artifact: `{audit['source_identity']['absolute_path']}`",
        "- Both pickle Hamiltonian hashes and the reconstructed group sums passed.",
        "- Hamiltonians were not regenerated.",
        "",
        "## Controlled Yoshida-4 comparison",
        "",
        "| condition | committed label | t_ana | |a4|/||D4|| | "
        "||QD4|0>||/||D4|| | mixing fraction | |t8/(t4+t6)| at t_ana | "
        "minimum phase compression |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in primary:
        lines.append(
            "| {condition} | {label} | {analytic_time:.4e} | "
            "{leading_diagonal_ratio:.4e} | "
            "{leading_coupling_ratio:.4e} | {mixing_fraction:.4e} | "
            "{absolute_t8_over_t4_plus_t6_at_t_ana:.4e} | "
            "{phase_compression_ratio:.4e} |".format(
                **row,
                label="pass" if row["committed_passed"] else "fail",
            )
        )
    changes = {
        "D4 diagonal": abs(stretch["a4"] / max(abs(eq["a4"]), 1e-300)),
        "D4 coupling": stretch["d4_coupling_norm"]
        / max(eq["d4_coupling_norm"], 1e-300),
        "D8 direct": abs(stretch["a8_diag"] / max(abs(eq["a8_diag"]), 1e-300)),
        "D4 mixing": abs(stretch["a8_mix"] / max(abs(eq["a8_mix"]), 1e-300)),
    }
    change_factors = {
        name: max(ratio, 1.0 / max(ratio, 1e-300))
        for name, ratio in changes.items()
    }
    dominant = max(change_factors, key=change_factors.get)
    lines.extend(
        [
            "",
            "## Predeclared mechanism reading",
            "",
            f"- The largest multiplicative equilibrium-to-stretch change among "
            f"the four requested Yoshida-4 components is **{dominant}** "
            f"(stretch/equilibrium={changes[dominant]:.4g}, "
            f"change factor={change_factors[dominant]:.4g}x).",
            "- Stretch/equilibrium component ratios: "
            + ", ".join(f"{name}={ratio:.4g}" for name, ratio in changes.items())
            + ".",
            f"- State-mixing flag at stretch: `{stretch['substantial_state_mixing']}`; "
            f"strong-a8-cancellation flag: `{stretch['strong_a8_cancellation']}`.",
            f"- The physical gap changes by a factor of "
            f"{stretch['physical_gap_hartree']/eq['physical_gap_hartree']:.4g}; "
            f"the minimum normalized phase-gap ratio changes from "
            f"{eq['phase_compression_ratio']:.4g} to "
            f"{stretch['phase_compression_ratio']:.4g}.",
            f"- The smaller stretched a4 increases t_ana by "
            f"{stretch['analytic_time']/eq['analytic_time']:.4g}x. At t_ana, "
            f"the formal |t8/(t4+t6)| ratio changes from "
            f"{eq['absolute_t8_over_t4_plus_t6_at_t_ana']:.4g} to "
            f"{stretch['absolute_t8_over_t4_plus_t6_at_t_ana']:.4g}.",
            "- These flags are controlled-pair explanatory candidates, not a proof "
            "of a unique cause. Physical gap, PF phase gap, and polynomial order "
            "are not interpreted alone.",
            "- current_m3 is diagnostic control only. N2/CO rows are external "
            "success context; no dense N2/CO D8 operator was constructed.",
            "",
            "## Finite-log window audit",
            "",
            "All three frozen windows are shown; no favorable window is selected "
            "post hoc. Large recovery errors mark finite-window instability and "
            "do not replace the Arb formal operators.",
            "",
            "| condition | PF | window | D4 rel. error | D6 rel. error | "
            "D8 rel. error | fit residual | unwrap margin |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in finite_log_rows:
        lines.append(
            "| {condition} | {formula} | {window_id} | {relative_error_d4:.4e} | "
            "{relative_error_d6:.4e} | {relative_error_d8:.4e} | "
            "{training_residual_frobenius_max:.4e} | "
            "{minimum_branch_cut_margin_radians:.4e} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Numerical gates",
            "",
            "| gate | measured | threshold | pass |",
            "|---|---:|---:|:---:|",
        ]
    )
    for check in audit["checks"]:
        lines.append(
            f"| {check['check_id']} | {check['measured']} | "
            f"{check['threshold']} | {'yes' if check['passed'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Diagnostic accounting",
            "",
            f"- `new_direct_truth_point_count = {audit['accounting']['new_direct_truth_point_count']}`",
            f"- `reused_committed_direct_point_count = {audit['accounting']['reused_committed_direct_point_count']}`",
            f"- `new_f05_diagnostic_eigendecomposition_count = {audit['accounting']['new_f05_diagnostic_eigendecomposition_count']}`",
            f"- `new_finite_log_diagnostic_unitary_count = {audit['accounting']['new_finite_log_diagnostic_unitary_count']}`",
            "- Diagnostic-to-fit/cost/PF-selection leakage check: "
            f"`{audit['accounting']['diagnostic_nonleakage_passed']}`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _artifact_hashes(output_dir: Path) -> dict[str, str]:
    return {
        str(path.relative_to(output_dir)): _sha256(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name not in {"manifest.json", "COMPLETE"}
    }


def run(source_root: Path, holdout_root: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    output_dir.mkdir(parents=True)
    started = time.perf_counter()
    protocol = _protocol()
    try:
        systems, source_identity, source_checks = _source_identity(
            source_root.resolve(), protocol
        )
    except SourceIdentityError as exc:
        audit = {
            "schema": "f_hf_mechanism_bridge_v1",
            "created_at": datetime.now().astimezone().isoformat(),
            "status": "failed_source_identity",
            "error": str(exc),
            "new_direct_truth_point_count": 0,
        }
        _atomic_json(output_dir / "audit.json", audit)
        (output_dir / "report.md").write_text(
            "# HF mechanism bridge\n\nStatus: **failed_source_identity**\n\n"
            + str(exc)
            + "\n",
            encoding="utf-8",
        )
        _atomic_json(
            output_dir / "manifest.json",
            {
                "status": "failed_source_identity",
                "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
                "source_root": str(source_root.resolve()),
                "new_direct_truth_point_count": 0,
            },
        )
        return audit

    metrics_path = holdout_root / "aggregate/metrics.csv"
    metrics = _read_metrics(metrics_path)
    labels = _truth_label_rows(metrics)
    label_by_condition = {row["condition"]: row for row in labels}
    external_rows = [
        row
        for row in metrics
        if row["condition"] in protocol["external_success_context"]
        and row["formula"] == "yoshida4"
        and row["model"] == "two_term_5point"
        and row["primary"] == "True"
    ]
    if len(external_rows) != 4:
        raise RuntimeError("expected four N2/CO external context rows")

    operator_rows: list[dict[str, Any]] = []
    mixing_rows: list[dict[str, Any]] = []
    state_rows: list[dict[str, Any]] = []
    direct_fit_rows: list[dict[str, Any]] = []
    finite_log_rows: list[dict[str, Any]] = []
    phase_rows: list[dict[str, Any]] = []
    condition_rows: list[dict[str, Any]] = []
    numeric_checks: list[dict[str, Any]] = list(source_checks)
    operators: dict[tuple[str, str, int], np.ndarray] = {}
    formal_energy: dict[tuple[str, str], np.ndarray] = {}
    finite_log_unitary_count = 0
    f05_eigendecomposition_count = 0
    reused_committed_count = 0

    gates = protocol["numerical_gates"]
    formula_records: dict[tuple[str, str], dict[str, Any]] = {}
    formula_points: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for condition in CONDITIONS:
        for formula in FORMULAE:
            raw_path = holdout_root / "raw" / f"{condition}__{formula}.json"
            record = _load_json(raw_path)
            formula_records[(condition, formula)] = record
            formula_points[(condition, formula)] = _committed_points(record)

    for condition in CONDITIONS:
        system = systems[condition]
        groups = system["bridge_group_matrices"]
        hamiltonian = np.asarray(system["hamiltonian"].toarray(), dtype=np.complex128)
        state = np.asarray(system["state"], dtype=np.complex128)
        exact_energies, exact_vectors = np.linalg.eigh(hamiltonian)
        centered_groups, identity_shifts, total_identity_shift = (
            center_group_identity_components(groups)
        )
        identity_128 = np.eye(hamiltonian.shape[0], dtype=np.complex128)
        identity_long = np.eye(hamiltonian.shape[0], dtype=np.clongdouble)
        for formula in FORMULAE:
            sequence = diagnosis._formula_s2_sequence(formula)
            steps = list(iter_s2_sequence_steps(len(groups), sequence))
            formal_128 = effective_hamiltonian_series_dtype(
                centered_groups, steps, FORMAL_MAXIMUM_ORDER, np.complex128
            )
            formal_long = effective_hamiltonian_series_dtype(
                centered_groups, steps, FORMAL_MAXIMUM_ORDER, np.clongdouble
            )
            formal_128[0] += total_identity_shift * identity_128
            formal_long[0] += np.clongdouble(total_identity_shift) * identity_long
            formal_arb, formal_arb_radii = effective_hamiltonian_series_arb(
                groups,
                steps,
                FORMAL_MAXIMUM_ORDER,
                precision_bits=ARB_PRECISION_BITS,
            )
            formal = [
                (np.asarray(value, dtype=np.complex128)
                 + np.asarray(value, dtype=np.complex128).conj().T)
                / 2.0
                for value in formal_arb
            ]
            h0_error = max(
                _relative(formal_long[0], hamiltonian.astype(np.clongdouble)),
                _relative(formal_arb[0], hamiltonian),
            )
            forbidden = max(
                _frobenius(formal_arb[order])
                / max(_frobenius(hamiltonian), 1e-300)
                for order in (1, 2, 3, 5, 7)
            )
            numeric_checks.extend(
                [
                    {
                        "check_id": f"{condition}:{formula}:h0_relative_frobenius",
                        "measured": h0_error,
                        "threshold": gates["h0_relative_frobenius"],
                        "comparison": "<=",
                        "passed": h0_error <= gates["h0_relative_frobenius"],
                    },
                    {
                        "check_id": f"{condition}:{formula}:forbidden_order_relative_frobenius",
                        "measured": forbidden,
                        "threshold": gates["forbidden_order_relative_frobenius"],
                        "comparison": "<=",
                        "passed": forbidden <= gates["forbidden_order_relative_frobenius"],
                    },
                ]
            )
            for order in REQUIRED_ORDERS:
                difference = _relative(formal_128[order], formal_long[order])
                arb_difference = _relative(formal_long[order], formal_arb[order])
                threshold = gates[f"precision_relative_difference_d{order}"]
                numeric_checks.extend(
                    [
                        {
                            "check_id": f"{condition}:{formula}:precision_d{order}",
                            "measured": difference,
                            "threshold": threshold,
                            "comparison": "<=",
                            "passed": difference <= threshold,
                        },
                        {
                            "check_id": (
                                f"{condition}:{formula}:arb_reference_d{order}"
                            ),
                            "measured": arb_difference,
                            "threshold": threshold,
                            "comparison": "<=",
                            "passed": arb_difference <= threshold,
                        },
                    ]
                )
                operators[(condition, formula, order)] = formal[order]
                row = operator_decomposition(
                    hamiltonian, state, formal[order], order
                )
                row.update(
                    {
                        "condition": condition,
                        "formula": formula,
                        "formal_reference": "python-flint Arb ball arithmetic",
                        "formal_reference_precision_bits": ARB_PRECISION_BITS,
                        "formal_identity_gauge": FORMAL_IDENTITY_GAUGE,
                        "total_removed_identity_hartree": total_identity_shift,
                        "maximum_group_identity_shift_hartree": max(
                            abs(value) for value in identity_shifts
                        ),
                        "arb_maximum_entry_radius": formal_arb_radii[order],
                        "hermiticity_relative_residual": _relative(
                            formal_arb[order], np.asarray(formal_arb[order]).conj().T
                        ),
                        "complex128_vs_clongdouble_relative_difference": difference,
                        "clongdouble_vs_arb_relative_difference": arb_difference,
                        "h0_relative_frobenius": h0_error,
                        "forbidden_order_max_relative_frobenius": forbidden,
                    }
                )
                operator_rows.append(row)
            perturbation = eigenenergy_perturbation_series(
                formal, state, maximum_order=FORMAL_MAXIMUM_ORDER
            )
            formal_energy[(condition, formula)] = np.asarray(
                perturbation["energy_coefficients"], dtype=np.complex128
            )

            t_ana = float(formula_records[(condition, formula)]["analytic_time"])
            unitary_cache: dict[float, np.ndarray] = {}
            for window in protocol["operator_expansion"][
                "finite_log_windows_relative_to_t_ana"
            ]:
                relatives = np.geomspace(
                    float(window["minimum"]),
                    float(window["maximum"]),
                    int(window["bins"]),
                )
                times = relatives * t_ana
                corrections = []
                margins = []
                principal_margins = []
                assignment_overlaps = []
                reconstruction = []
                for relative_time, time_value in zip(relatives, times, strict=True):
                    unitary, _ = _build_unitary(system, sequence, float(time_value))
                    finite_log_unitary_count += 1
                    unitary_cache[float(time_value)] = unitary
                    finite = _finite_log_record(
                        unitary,
                        float(time_value),
                        exact_energies,
                        exact_vectors,
                    )
                    corrections.append(finite["effective_hamiltonian"] - hamiltonian)
                    margins.append(finite["branch_cut_margin_radians"])
                    principal_margins.append(
                        finite["principal_branch_cut_margin_radians"]
                    )
                    assignment_overlaps.append(
                        finite["minimum_reference_assignment_overlap_probability"]
                    )
                    reconstruction.append(
                        finite["unitary_reconstruction_residual_frobenius"]
                    )
                fit = fit_even_effective_operators(
                    times, np.asarray(corrections), FIT_ORDERS
                )
                row = {
                    "condition": condition,
                    "formula": formula,
                    "window_id": window["window_id"],
                    "minimum_relative_to_t_ana": window["minimum"],
                    "maximum_relative_to_t_ana": window["maximum"],
                    "point_count": int(window["bins"]),
                    "scaled_design_condition_number": fit["condition_number"],
                    "training_residual_frobenius_max": fit[
                        "training_residual_frobenius_max"
                    ],
                    "branch_method": FINITE_LOG_BRANCH_METHOD,
                    "minimum_branch_cut_margin_radians": min(margins),
                    "minimum_principal_branch_cut_margin_radians": min(
                        principal_margins
                    ),
                    "minimum_reference_assignment_overlap_probability": min(
                        assignment_overlaps
                    ),
                    "maximum_unitary_reconstruction_residual_frobenius": max(
                        reconstruction
                    ),
                    "point_role": "f01_finite_log_diagnostic_only",
                    "used_as_direct_truth": False,
                }
                for index, order in enumerate(FIT_ORDERS):
                    if order in REQUIRED_ORDERS:
                        row[f"relative_error_d{order}"] = _relative_matrix_error(
                            fit["coefficients"][index], formal[order]
                        )
                finite_log_rows.append(row)

    # Cross-condition and cross-PF ratios requested by F01.
    operator_lookup = {
        (row["condition"], row["formula"], row["order"]): row
        for row in operator_rows
    }
    for row in operator_rows:
        other_condition = (
            "HF_full_stretch150_sto3g"
            if row["condition"] == "HF_full_eq_sto3g"
            else "HF_full_eq_sto3g"
        )
        stretch_row = operator_lookup[
            ("HF_full_stretch150_sto3g", row["formula"], row["order"])
        ]
        eq_row = operator_lookup[
            ("HF_full_eq_sto3g", row["formula"], row["order"])
        ]
        control = (
            "current_m3" if row["formula"] == "yoshida4" else "yoshida4"
        )
        control_row = operator_lookup[(row["condition"], control, row["order"])]
        row["stretch_over_equilibrium_frobenius_ratio"] = (
            stretch_row["operator_frobenius_norm"]
            / max(eq_row["operator_frobenius_norm"], 1e-300)
        )
        row["current_m3_over_yoshida4_frobenius_ratio"] = (
            operator_lookup[(row["condition"], "current_m3", row["order"])][
                "operator_frobenius_norm"
            ]
            / max(
                operator_lookup[(row["condition"], "yoshida4", row["order"])][
                    "operator_frobenius_norm"
                ],
                1e-300,
            )
        )
        row["comparison_partner_condition"] = other_condition
        row["comparison_partner_formula"] = control_row["formula"]

    for condition in CONDITIONS:
        system = systems[condition]
        hamiltonian = np.asarray(system["hamiltonian"].toarray(), dtype=np.complex128)
        state = np.asarray(system["state"], dtype=np.complex128)
        for formula in FORMULAE:
            d4 = operators[(condition, formula, 4)]
            d8 = operators[(condition, formula, 8)]
            decomposition = decompose_a8_state_mixing(
                hamiltonian, state, d4, d8
            )
            reference_a8 = float(formal_energy[(condition, formula)][8].real)
            identity_relative = abs(
                decomposition["a8_from_components_hartree"] - reference_a8
            ) / max(abs(reference_a8), 1e-300)
            numeric_checks.append(
                {
                    "check_id": f"{condition}:{formula}:a8_decomposition_relative_identity",
                    "measured": identity_relative,
                    "threshold": gates["a8_decomposition_relative_identity"],
                    "comparison": "<=",
                    "passed": identity_relative
                    <= gates["a8_decomposition_relative_identity"],
                }
            )
            diag = float(decomposition["d8_expectation_hartree"])
            mix = float(decomposition["d4_second_order_mixing_hartree"])
            component_scale = abs(diag) + abs(mix)
            summary = {
                "condition": condition,
                "formula": formula,
                "physical_gap_hartree": decomposition[
                    "minimum_excitation_gap_hartree"
                ],
                "a8_diag": diag,
                "a8_mix": mix,
                "a8_total": reference_a8,
                "a8_component_sum": decomposition["a8_from_components_hartree"],
                "a8_identity_relative_residual": identity_relative,
                "mixing_fraction": abs(mix) / max(component_scale, 1e-300),
                "cancellation_ratio": component_scale
                / max(abs(reference_a8), 1e-300),
                "a8_diag_sign": int(np.sign(diag)),
                "a8_mix_sign": int(np.sign(mix)),
                "a8_total_sign": int(np.sign(reference_a8)),
            }
            mixing_rows.append(summary)
            for state_row in decomposition["state_rows"]:
                state_rows.append(
                    {"condition": condition, "formula": formula, **state_row}
                )
            direct_fit = _fit_direct_three_term(
                formula_records[(condition, formula)]
            )
            direct_fit.update(
                {
                    "condition": condition,
                    "formula": formula,
                    "formal_a8": reference_a8,
                    "fitted_vs_formal_a8_relative_difference": abs(
                        direct_fit["fitted_a8"] - reference_a8
                    )
                    / max(abs(reference_a8), 1e-300),
                }
            )
            direct_fit_rows.append(direct_fit)

    minimum_branch_margin = math.inf
    minimum_overlap = math.inf
    maximum_residual = 0.0
    maximum_stored_difference = 0.0
    for condition in CONDITIONS:
        system = systems[condition]
        energies = np.linalg.eigvalsh(system["hamiltonian"].toarray())
        physical_gap = float(energies[1] - energies[0])
        for formula in FORMULAE:
            sequence = diagnosis._formula_s2_sequence(formula)
            record = formula_records[(condition, formula)]
            committed_points = formula_points[(condition, formula)]
            t_ana = float(record["analytic_time"])
            previous = None
            for relative_time in protocol["phase_gap_grid_relative_to_t_ana"]:
                time_value = float(relative_time) * t_ana
                committed = _find_committed_point(committed_points, time_value)
                unitary, build = _build_unitary(system, sequence, time_value)
                if committed is None:
                    f05_eigendecomposition_count += 1
                point, previous = _f05_point(
                    unitary,
                    system,
                    time_value,
                    previous,
                    committed,
                    float(gates["stored_direct_shift_absolute_hartree"]),
                )
                if committed is not None:
                    reused_committed_count += 1
                point.update(
                    {
                        "condition": condition,
                        "formula": formula,
                        "relative_to_t_ana": float(relative_time),
                        "physical_excitation_gap_hartree": physical_gap,
                        "normalized_phase_gap_over_physical_gap": point[
                            "phase_gap_over_time_hartree"
                        ]
                        / physical_gap,
                        "build_seconds": build["build_seconds"],
                    }
                )
                phase_rows.append(point)
                minimum_branch_margin = min(
                    minimum_branch_margin, _phase_cut_margin(unitary)
                )
                minimum_overlap = min(
                    minimum_overlap, point["ground_overlap_probability"]
                )
                maximum_residual = max(
                    maximum_residual, point["eigenpair_residual_2_norm"]
                )
                if point["committed_shift_absolute_difference_hartree"] is not None:
                    maximum_stored_difference = max(
                        maximum_stored_difference,
                        point["committed_shift_absolute_difference_hartree"],
                    )

    minimum_log_margin = min(
        row["minimum_branch_cut_margin_radians"] for row in finite_log_rows
    )
    numeric_checks.extend(
        [
            {
                "check_id": "finite_log_minimum_branch_cut_margin_radians",
                "measured": minimum_log_margin,
                "threshold": gates["minimum_log_branch_cut_margin_radians"],
                "comparison": ">=",
                "passed": minimum_log_margin
                >= gates["minimum_log_branch_cut_margin_radians"],
            },
            {
                "check_id": "f05_minimum_selected_branch_overlap_probability",
                "measured": minimum_overlap,
                "threshold": gates["minimum_selected_branch_overlap_probability"],
                "comparison": ">=",
                "passed": minimum_overlap
                >= gates["minimum_selected_branch_overlap_probability"],
            },
            {
                "check_id": "f05_maximum_eigenpair_residual_2_norm",
                "measured": maximum_residual,
                "threshold": gates["maximum_eigenpair_residual_2_norm"],
                "comparison": "<=",
                "passed": maximum_residual
                <= gates["maximum_eigenpair_residual_2_norm"],
            },
            {
                "check_id": "reused_committed_shift_absolute_hartree",
                "measured": maximum_stored_difference,
                "threshold": gates["stored_direct_shift_absolute_hartree"],
                "comparison": "<=",
                "passed": maximum_stored_difference
                <= gates["stored_direct_shift_absolute_hartree"],
            },
        ]
    )

    operator_by_key = {
        (row["condition"], row["formula"], row["order"]): row
        for row in operator_rows
    }
    mixing_by_key = {
        (row["condition"], row["formula"]): row for row in mixing_rows
    }
    label_lookup = {row["condition"]: row for row in labels}
    flags = protocol["predeclared_mechanism_flags"]
    for condition in CONDITIONS:
        for formula in FORMULAE:
            d4 = operator_by_key[(condition, formula, 4)]
            mix = mixing_by_key[(condition, formula)]
            points = [
                row
                for row in phase_rows
                if row["condition"] == condition and row["formula"] == formula
            ]
            leading_diagonal_ratio = abs(d4["ground_expectation_real"]) / max(
                d4["operator_frobenius_norm"], 1e-300
            )
            leading_coupling_ratio = d4["ground_to_excited_coupling_norm"] / max(
                d4["operator_frobenius_norm"], 1e-300
            )
            phase_ratio = min(
                row["normalized_phase_gap_over_physical_gap"] for row in points
            )
            t_ana = float(formula_records[(condition, formula)]["analytic_time"])
            energy_coefficients = formal_energy[(condition, formula)]
            formal_contributions = {
                order: float(np.real(energy_coefficients[order])) * t_ana**order
                for order in (4, 6, 8)
            }
            condition_rows.append(
                {
                    "condition": condition,
                    "formula": formula,
                    "model": "two_term_5point",
                    "committed_passed": (
                        label_lookup[condition]["committed_passed"]
                        if formula == "yoshida4"
                        else "diagnostic_control_not_reclassified"
                    ),
                    "a4": d4["ground_expectation_real"],
                    "d4_frobenius_norm": d4["operator_frobenius_norm"],
                    "d4_coupling_norm": d4["ground_to_excited_coupling_norm"],
                    "a8_diag": mix["a8_diag"],
                    "a8_mix": mix["a8_mix"],
                    "a8_total": mix["a8_total"],
                    "formal_a6": float(np.real(energy_coefficients[6])),
                    "analytic_time": t_ana,
                    "formal_t4_contribution_at_t_ana": formal_contributions[4],
                    "formal_t6_contribution_at_t_ana": formal_contributions[6],
                    "formal_t8_contribution_at_t_ana": formal_contributions[8],
                    "absolute_t8_over_t4_plus_t6_at_t_ana": abs(
                        formal_contributions[8]
                    )
                    / max(
                        abs(formal_contributions[4] + formal_contributions[6]),
                        1e-300,
                    ),
                    "mixing_fraction": mix["mixing_fraction"],
                    "a8_cancellation_ratio": mix["cancellation_ratio"],
                    "physical_gap_hartree": mix["physical_gap_hartree"],
                    "phase_compression_ratio": phase_ratio,
                    "leading_diagonal_ratio": leading_diagonal_ratio,
                    "leading_coupling_ratio": leading_coupling_ratio,
                    "leading_diagonal_cancellation": leading_diagonal_ratio
                    <= flags["leading_diagonal_cancellation_max_ratio"],
                    "substantial_leading_coupling": leading_coupling_ratio
                    >= flags["leading_coupling_min_ratio"],
                    "substantial_state_mixing": mix["mixing_fraction"]
                    >= flags["state_mixing_min_fraction"],
                    "strong_a8_cancellation": mix["cancellation_ratio"]
                    >= flags["a8_cancellation_min_ratio"],
                    "phase_compression": phase_ratio
                    <= flags["phase_compression_max_ratio"],
                }
            )

    nonleakage = all(
        not row["used_as_direct_truth"]
        and not row["used_for_model_fit"]
        and not row["used_for_cost_validation"]
        for row in phase_rows
    )
    numeric_checks.append(
        {
            "check_id": "diagnostic_nonleakage",
            "measured": nonleakage,
            "threshold": True,
            "comparison": "==",
            "passed": nonleakage,
        }
    )
    passed = all(check["passed"] for check in numeric_checks)
    status = "complete_with_findings" if passed else "failed_numerical_validation"
    audit = {
        "schema": "f_hf_mechanism_bridge_v1_retry1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "numerical_remediation": {
            "formal_reference": "python-flint Arb ball arithmetic",
            "formal_reference_precision_bits": ARB_PRECISION_BITS,
            "formal_identity_gauge": FORMAL_IDENTITY_GAUGE,
            "finite_log_branch_method": FINITE_LOG_BRANCH_METHOD,
            "thresholds_changed": False,
            "time_grids_changed": False,
            "pf_coefficients_changed": False,
            "committed_labels_changed": False,
        },
        "source_identity": source_identity,
        "committed_labels": labels,
        "checks": numeric_checks,
        "operator_decomposition": operator_rows,
        "a8_state_mixing": mixing_rows,
        "excited_state_contributions": state_rows,
        "direct_fit_diagnostics": direct_fit_rows,
        "finite_log_diagnostics": finite_log_rows,
        "phase_gap_points": phase_rows,
        "condition_comparison": condition_rows,
        "accounting": {
            "new_direct_truth_point_count": 0,
            "reused_committed_direct_point_count": reused_committed_count,
            "new_f05_diagnostic_eigendecomposition_count": f05_eigendecomposition_count,
            "new_finite_log_diagnostic_unitary_count": finite_log_unitary_count,
            "diagnostic_nonleakage_passed": nonleakage,
            "diagnostic_values_used_for_model_fit": False,
            "diagnostic_values_used_for_cost_validation": False,
            "diagnostic_values_used_for_pf_selection": False,
            "diagnostic_values_used_to_change_committed_labels": False,
        },
        "runtime": {
            "wall_seconds": float(time.perf_counter() - started),
            "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "peak_gpu_memory_mib": None,
            "gpu_used": False,
        },
    }
    _write_csv(output_dir / "operator_decomposition.csv", operator_rows)
    _write_csv(output_dir / "a8_state_mixing.csv", mixing_rows)
    _write_csv(output_dir / "excited_state_contributions.csv", state_rows)
    _write_csv(output_dir / "direct_fit_diagnostics.csv", direct_fit_rows)
    _write_csv(output_dir / "finite_log_diagnostics.csv", finite_log_rows)
    _write_csv(output_dir / "phase_gap_points.csv", phase_rows)
    _write_csv(output_dir / "condition_comparison.csv", condition_rows)
    _write_csv(output_dir / "external_success_context.csv", external_rows)
    _plot_operator(output_dir / "operator_norm_comparison.png", operator_rows)
    _plot_phase(output_dir / "phase_gap_comparison.png", phase_rows)
    _atomic_json(output_dir / "audit.json", audit)
    _write_report(output_dir / "report.md", audit)
    manifest = {
        "status": status,
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "numerical_remediation": audit["numerical_remediation"],
        "base_commit": _git("rev-parse", "HEAD"),
        "source_commits": protocol["source"],
        "source_identity": source_identity,
        "holdout_artifact": str(holdout_root.resolve()),
        "holdout_metrics_sha256": _sha256(metrics_path),
        "new_direct_truth_point_count": 0,
        "reused_committed_direct_point_count": reused_committed_count,
        "new_f05_diagnostic_eigendecomposition_count": f05_eigendecomposition_count,
        "new_finite_log_diagnostic_unitary_count": finite_log_unitary_count,
        "diagnostic_nonleakage_passed": nonleakage,
        "environment": _versions(),
        "runtime": audit["runtime"],
        "artifact_hashes": _artifact_hashes(output_dir),
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--holdout-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    audit = run(arguments.source_root, arguments.holdout_root, arguments.output_dir)
    print(
        json.dumps(
            {
                "status": audit["status"],
                "output_dir": str(arguments.output_dir),
                "accounting": audit.get("accounting"),
                "runtime": audit.get("runtime"),
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    if audit["status"] not in ("complete_with_findings",):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
