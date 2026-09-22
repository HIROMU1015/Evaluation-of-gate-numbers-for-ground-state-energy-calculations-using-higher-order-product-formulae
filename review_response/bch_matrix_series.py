"""High-precision matrix power series for product-formula BCH checks.

This module is deliberately limited to small dense matrices.  It provides an
independent reference for a scalable commutator implementation: construct the
Taylor series of the *actual ordered product* of exponentials, take its formal
matrix logarithm, and read off the effective-Hamiltonian coefficients.

The convention matches :mod:`trotterlib.sector_pf`: if ``steps`` is iterated
from first to last, every new exponential is applied on the left,

    U(t) = exp(i t w_last H_last) ... exp(i t w_first H_first).

Thus ``log(U(t)) / (i t)`` is the effective Hamiltonian for the repository's
``exp(+i t H)`` convention.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager
from typing import Iterator

import mpmath as mp
import numpy as np


MatrixSeries = list[mp.matrix]


@contextmanager
def _working_precision(decimal_digits: int) -> Iterator[None]:
    if decimal_digits < 30:
        raise ValueError("decimal_digits must be at least 30")
    with mp.workdps(int(decimal_digits)):
        yield


def _zero_matrix(dimension: int) -> mp.matrix:
    return mp.matrix(int(dimension), int(dimension))


def _copy_matrix(matrix: mp.matrix) -> mp.matrix:
    return mp.matrix(matrix)


def _as_mpmath_matrix(matrix: np.ndarray) -> mp.matrix:
    array = np.asarray(matrix, dtype=np.complex128)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("matrix must be square")
    dimension = int(array.shape[0])
    result = _zero_matrix(dimension)
    for row in range(dimension):
        for column in range(dimension):
            value = complex(array[row, column])
            result[row, column] = mp.mpc(
                mp.mpf(str(value.real)), mp.mpf(str(value.imag))
            )
    return result


def _as_numpy_matrix(matrix: mp.matrix) -> np.ndarray:
    result = np.empty((matrix.rows, matrix.cols), dtype=np.complex128)
    for row in range(matrix.rows):
        for column in range(matrix.cols):
            result[row, column] = complex(matrix[row, column])
    return result


def _zero_series(dimension: int, maximum_degree: int) -> MatrixSeries:
    return [_zero_matrix(dimension) for _ in range(maximum_degree + 1)]


def _multiply_series(
    left: Sequence[mp.matrix],
    right: Sequence[mp.matrix],
    maximum_degree: int,
) -> MatrixSeries:
    if not left or not right:
        raise ValueError("both series must be non-empty")
    dimension = int(left[0].rows)
    result = _zero_series(dimension, maximum_degree)
    for degree in range(maximum_degree + 1):
        accumulator = _zero_matrix(dimension)
        for left_degree in range(degree + 1):
            if left_degree >= len(left):
                break
            right_degree = degree - left_degree
            if right_degree >= len(right):
                continue
            accumulator += left[left_degree] * right[right_degree]
        result[degree] = accumulator
    return result


def _multiply_numpy_series(
    left: Sequence[np.ndarray],
    right: Sequence[np.ndarray],
    maximum_degree: int,
) -> list[np.ndarray]:
    dimension = int(np.asarray(left[0]).shape[0])
    result = [
        np.zeros((dimension, dimension), dtype=np.complex128)
        for _ in range(maximum_degree + 1)
    ]
    for degree in range(maximum_degree + 1):
        for left_degree in range(degree + 1):
            if left_degree >= len(left):
                break
            right_degree = degree - left_degree
            if right_degree < len(right):
                result[degree] += left[left_degree] @ right[right_degree]
    return result


def _exponential_series(generator: mp.matrix, maximum_degree: int) -> MatrixSeries:
    dimension = int(generator.rows)
    result = _zero_series(dimension, maximum_degree)
    result[0] = mp.eye(dimension)
    for degree in range(1, maximum_degree + 1):
        result[degree] = result[degree - 1] * generator / degree
    return result


def _ordered_exponential_product_series_mp(
    generators: Sequence[np.ndarray], maximum_degree: int
) -> MatrixSeries:
    arrays = [np.asarray(generator, dtype=np.complex128) for generator in generators]
    dimension = int(arrays[0].shape[0])
    product = _zero_series(dimension, maximum_degree)
    product[0] = mp.eye(dimension)
    for raw_generator in arrays:
        exponential = _exponential_series(
            _as_mpmath_matrix(raw_generator), maximum_degree
        )
        product = _multiply_series(exponential, product, maximum_degree)
    return product


def _formal_logarithm_series_mp(
    series: Sequence[mp.matrix], maximum_degree: int
) -> MatrixSeries:
    dimension = int(series[0].rows)
    identity = mp.eye(dimension)
    x_series = [_copy_matrix(value) for value in series]
    x_series[0] -= identity
    logarithm = _zero_series(dimension, maximum_degree)
    power = [_copy_matrix(value) for value in x_series]
    for exponent in range(1, maximum_degree + 1):
        scale = mp.mpf(1 if exponent % 2 else -1) / exponent
        for degree in range(1, maximum_degree + 1):
            logarithm[degree] += scale * power[degree]
        if exponent != maximum_degree:
            power = _multiply_series(power, x_series, maximum_degree)
    return logarithm


def ordered_exponential_product_series(
    generators: Sequence[np.ndarray],
    maximum_degree: int,
    *,
    decimal_digits: int = 80,
) -> list[np.ndarray]:
    """Return coefficients of the repository-ordered exponential product.

    ``generators[j]`` denotes the time-independent matrix ``A_j`` in
    ``exp(t A_j)``.  In iteration order the factors are left-applied, exactly
    as in the dense sector PF builder.
    """

    if maximum_degree < 0:
        raise ValueError("maximum_degree must be non-negative")
    if not generators:
        raise ValueError("generators must not be empty")
    arrays = [np.asarray(generator, dtype=np.complex128) for generator in generators]
    dimension = int(arrays[0].shape[0])
    if any(array.shape != (dimension, dimension) for array in arrays):
        raise ValueError("all generators must have the same square shape")

    with _working_precision(decimal_digits):
        product = _ordered_exponential_product_series_mp(arrays, maximum_degree)
        return [_as_numpy_matrix(coefficient) for coefficient in product]


def formal_logarithm_series(
    series: Sequence[np.ndarray],
    maximum_degree: int,
    *,
    decimal_digits: int = 80,
) -> list[np.ndarray]:
    """Return the formal series of ``log(series)`` through a fixed degree."""

    if maximum_degree < 1:
        raise ValueError("maximum_degree must be at least one")
    if len(series) < maximum_degree + 1:
        raise ValueError("series does not contain all requested degrees")
    arrays = [np.asarray(value, dtype=np.complex128) for value in series]
    dimension = int(arrays[0].shape[0])
    if arrays[0].shape != (dimension, dimension):
        raise ValueError("series coefficients must be square matrices")
    if not np.allclose(arrays[0], np.eye(dimension), atol=1e-13, rtol=0.0):
        raise ValueError("constant series coefficient must be the identity")

    with _working_precision(decimal_digits):
        converted = [_as_mpmath_matrix(value) for value in arrays]
        logarithm = _formal_logarithm_series_mp(converted, maximum_degree)
        return [_as_numpy_matrix(coefficient) for coefficient in logarithm]


def effective_hamiltonian_series(
    group_matrices: Sequence[np.ndarray],
    steps: Sequence[tuple[int, float]],
    maximum_effective_order: int = 6,
    *,
    decimal_digits: int = 80,
) -> dict[str, list[np.ndarray]]:
    """Expand the PF effective Hamiltonian for small dense matrices.

    Returns both the ordered-product series and the formal logarithm.  Entry
    ``effective_hamiltonian[k]`` is the coefficient of ``t**k`` in
    ``log(U(t))/(i*t)``.
    """

    if maximum_effective_order < 0:
        raise ValueError("maximum_effective_order must be non-negative")
    if not group_matrices:
        raise ValueError("group_matrices must not be empty")
    if not steps:
        raise ValueError("steps must not be empty")
    matrices = [np.asarray(matrix, dtype=np.complex128) for matrix in group_matrices]
    dimension = int(matrices[0].shape[0])
    if any(matrix.shape != (dimension, dimension) for matrix in matrices):
        raise ValueError("all group matrices must have the same square shape")

    generators: list[np.ndarray] = []
    for group_index, weight in steps:
        if group_index < 0 or group_index >= len(matrices):
            raise IndexError(f"invalid group index {group_index}")
        generators.append(1j * float(weight) * matrices[group_index])

    log_degree = int(maximum_effective_order) + 1
    with _working_precision(decimal_digits):
        product_mp = _ordered_exponential_product_series_mp(generators, log_degree)
        logarithm_mp = _formal_logarithm_series_mp(product_mp, log_degree)
        effective_mp = [
            logarithm_mp[degree + 1] / mp.j for degree in range(log_degree)
        ]
        product = [_as_numpy_matrix(coefficient) for coefficient in product_mp]
        logarithm = [
            _as_numpy_matrix(coefficient) for coefficient in logarithm_mp
        ]
        effective = [
            _as_numpy_matrix(coefficient) for coefficient in effective_mp
        ]
    return {
        "ordered_product": product,
        "logarithm": logarithm,
        "effective_hamiltonian": effective,
    }


def effective_hamiltonian_series_numpy(
    group_matrices: Sequence[np.ndarray],
    steps: Sequence[tuple[int, float]],
    maximum_effective_order: int = 6,
) -> dict[str, list[np.ndarray]]:
    """Complex128 counterpart of :func:`effective_hamiltonian_series`.

    This backend is intended for medium dense validation systems after its
    cancellation error has been checked against the high-precision small
    system reference.
    """

    if maximum_effective_order < 0:
        raise ValueError("maximum_effective_order must be non-negative")
    if not group_matrices or not steps:
        raise ValueError("group_matrices and steps must not be empty")
    matrices = [np.asarray(matrix, dtype=np.complex128) for matrix in group_matrices]
    dimension = int(matrices[0].shape[0])
    if any(matrix.shape != (dimension, dimension) for matrix in matrices):
        raise ValueError("all group matrices must have the same square shape")
    maximum_degree = int(maximum_effective_order) + 1
    identity = np.eye(dimension, dtype=np.complex128)
    product = [
        np.zeros((dimension, dimension), dtype=np.complex128)
        for _ in range(maximum_degree + 1)
    ]
    product[0] = identity
    for group_index, weight in steps:
        generator = 1j * float(weight) * matrices[int(group_index)]
        exponential = [
            np.zeros((dimension, dimension), dtype=np.complex128)
            for _ in range(maximum_degree + 1)
        ]
        exponential[0] = identity
        for degree in range(1, maximum_degree + 1):
            exponential[degree] = exponential[degree - 1] @ generator / degree
        product = _multiply_numpy_series(exponential, product, maximum_degree)

    x_series = [np.array(value, copy=True) for value in product]
    x_series[0] -= identity
    logarithm = [
        np.zeros((dimension, dimension), dtype=np.complex128)
        for _ in range(maximum_degree + 1)
    ]
    power = [np.array(value, copy=True) for value in x_series]
    for exponent in range(1, maximum_degree + 1):
        scale = (1.0 if exponent % 2 else -1.0) / exponent
        for degree in range(1, maximum_degree + 1):
            logarithm[degree] += scale * power[degree]
        if exponent != maximum_degree:
            power = _multiply_numpy_series(power, x_series, maximum_degree)
    effective = [
        logarithm[degree + 1] / 1j for degree in range(maximum_degree)
    ]
    return {
        "ordered_product": product,
        "logarithm": logarithm,
        "effective_hamiltonian": effective,
    }


def evaluate_matrix_series(
    series: Sequence[np.ndarray], time_value: float
) -> np.ndarray:
    """Evaluate a matrix polynomial using Horner's rule."""

    if not series:
        raise ValueError("series must not be empty")
    result = np.zeros_like(np.asarray(series[0], dtype=np.complex128))
    for coefficient in reversed(series):
        result = result * float(time_value) + np.asarray(
            coefficient, dtype=np.complex128
        )
    return result


def eigenenergy_perturbation_series(
    effective_hamiltonian: Sequence[np.ndarray],
    reference_state: np.ndarray,
    maximum_order: int | None = None,
) -> dict[str, object]:
    """Expand the eigenenergy connected to ``reference_state`` recursively.

    ``effective_hamiltonian[k]`` is the coefficient of ``t**k``.  The
    eigenvector corrections use intermediate normalization.  This captures
    all cross terms automatically; for example the order-eight coefficient
    includes both ``<D8>`` and the second-order ``D4`` correction.
    """

    if not effective_hamiltonian:
        raise ValueError("effective_hamiltonian must not be empty")
    available_order = len(effective_hamiltonian) - 1
    if maximum_order is None:
        maximum_order = available_order
    if maximum_order < 0 or maximum_order > available_order:
        raise ValueError("maximum_order lies outside the supplied series")

    h0 = np.asarray(effective_hamiltonian[0], dtype=np.complex128)
    if h0.ndim != 2 or h0.shape[0] != h0.shape[1]:
        raise ValueError("effective-Hamiltonian coefficients must be square")
    dimension = int(h0.shape[0])
    state = np.asarray(reference_state, dtype=np.complex128).reshape(-1)
    if state.size != dimension:
        raise ValueError("reference_state has the wrong dimension")
    state /= np.linalg.norm(state)

    energies, eigenvectors = np.linalg.eigh(h0)
    overlaps = np.abs(eigenvectors.conj().T @ state) ** 2
    selected = int(np.argmax(overlaps))
    if selected > 0 and abs(energies[selected] - energies[0]) > 1e-10:
        raise ValueError("reference_state does not select the ground eigenvalue")
    gaps = float(energies[selected]) - energies
    near_degenerate = [
        index
        for index, gap in enumerate(gaps)
        if index != selected and abs(float(gap)) <= 1e-12
    ]
    if near_degenerate:
        raise ValueError("selected eigenvalue is degenerate within tolerance")

    transformed = [
        eigenvectors.conj().T
        @ np.asarray(matrix, dtype=np.complex128)
        @ eigenvectors
        for matrix in effective_hamiltonian[: maximum_order + 1]
    ]
    vectors = [np.zeros(dimension, dtype=np.complex128) for _ in range(maximum_order + 1)]
    vectors[0][selected] = 1.0
    coefficients = np.zeros(maximum_order + 1, dtype=np.complex128)
    coefficients[0] = complex(energies[selected])
    identity = np.eye(dimension, dtype=np.complex128)

    for order in range(1, maximum_order + 1):
        coefficient = 0.0j
        for perturbation_order in range(1, order + 1):
            coefficient += (
                transformed[perturbation_order]
                @ vectors[order - perturbation_order]
            )[selected]
        coefficients[order] = coefficient

        right_hand_side = np.zeros(dimension, dtype=np.complex128)
        for perturbation_order in range(1, order + 1):
            right_hand_side += (
                transformed[perturbation_order]
                - coefficients[perturbation_order] * identity
            ) @ vectors[order - perturbation_order]
        for index in range(dimension):
            if index != selected:
                vectors[order][index] = right_hand_side[index] / gaps[index]

    return {
        "energy_coefficients": coefficients,
        "eigenvector_correction_norms": np.asarray(
            [np.linalg.norm(vector) for vector in vectors], dtype=float
        ),
        "selected_unperturbed_eigenstate_index": selected,
        "selected_reference_overlap_probability": float(overlaps[selected]),
        "minimum_excitation_gap_hartree": float(
            min(abs(float(gap)) for index, gap in enumerate(gaps) if index != selected)
        ),
    }
