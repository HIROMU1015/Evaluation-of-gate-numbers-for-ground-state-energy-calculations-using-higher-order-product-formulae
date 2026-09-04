"""Exact PF construction using symmetry sectors and small group components.

The complete product-formula unitary is generally dense.  Individual grouped
Hamiltonians, however, split into many small connected components after the
fixed-particle and diagonal-Z symmetry restrictions are applied.  Keeping the
component eigensystems instead of one dense eigensystem per group removes the
dominant preparation-memory cost without approximating the PF.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np
from openfermion.ops import QubitOperator
from scipy.linalg import eigh
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components


@dataclass(frozen=True)
class ComponentBatch:
    """Equal-sized connected components of one grouped Hamiltonian."""

    indices: np.ndarray
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray | None

    @property
    def component_size(self) -> int:
        return int(self.indices.shape[1])

    @property
    def component_count(self) -> int:
        return int(self.indices.shape[0])


@dataclass(frozen=True)
class ComponentSpectrum:
    """Compact exact eigensystem of a grouped sector Hamiltonian."""

    dimension: int
    batches: tuple[ComponentBatch, ...]
    source_nnz: int
    component_count: int
    maximum_component_size: int
    retained_complex_elements: int


def _as_group_operator(group: object) -> QubitOperator:
    if isinstance(group, QubitOperator):
        return group
    result = QubitOperator()
    for operator in group:  # type: ignore[union-attr]
        result += operator
    return result


def fixed_population_basis(
    num_qubits: int, ground_state: np.ndarray, *, support_cutoff: float = 1e-12
) -> tuple[np.ndarray, dict[str, object]]:
    """Return the sorted fixed alpha/beta-population basis containing a state."""
    state = np.asarray(ground_state).reshape(-1)
    support = np.flatnonzero(np.abs(state) > support_cutoff)
    if support.size == 0:
        raise ValueError("ground_state has no support above the cutoff")
    half = num_qubits // 2
    if 2 * half != num_qubits:
        raise ValueError("the spin-separated mapping requires an even qubit count")
    populations = {
        (
            int(index).bit_count()
            - (int(index) & ((1 << half) - 1)).bit_count(),
            (int(index) & ((1 << half) - 1)).bit_count(),
        )
        for index in support
    }
    if len(populations) != 1:
        raise ValueError(f"state spans multiple half-population sectors: {populations}")
    n_alpha, n_beta = next(iter(populations))
    basis = np.asarray(
        [
            index
            for index in range(1 << num_qubits)
            if (index >> half).bit_count() == n_alpha
            and (index & ((1 << half) - 1)).bit_count() == n_beta
        ],
        dtype=np.int64,
    )
    outside_norm_squared = float(
        np.linalg.norm(state) ** 2 - np.linalg.norm(state[basis]) ** 2
    )
    return basis, {
        "kind": "fixed_half_populations",
        "n_alpha": int(n_alpha),
        "n_beta": int(n_beta),
        "dimension": int(basis.size),
        "ground_state_outside_norm_squared": max(0.0, outside_norm_squared),
    }


def _gf2_nullspace(rows: Iterable[int], width: int) -> list[int]:
    """Return an integer-bitmask basis of the GF(2) right nullspace."""
    matrix = []
    for value in set(int(row) for row in rows if row):
        matrix.append([(value >> bit) & 1 for bit in range(width)])
    if not matrix:
        return [1 << bit for bit in range(width)]
    array = np.asarray(matrix, dtype=np.uint8)
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(width):
        candidates = np.flatnonzero(array[pivot_row:, column])
        if candidates.size == 0:
            continue
        selected = pivot_row + int(candidates[0])
        array[[pivot_row, selected]] = array[[selected, pivot_row]]
        other = np.flatnonzero(array[:, column])
        other = other[other != pivot_row]
        array[other] ^= array[pivot_row]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == array.shape[0]:
            break
    free_columns = [column for column in range(width) if column not in pivot_columns]
    result = []
    for free in free_columns:
        vector = 1 << free
        for row_index, pivot in enumerate(pivot_columns):
            if array[row_index, free]:
                vector |= 1 << pivot
        result.append(vector)
    return result


def find_balanced_z2_symmetry(
    groups: Sequence[object],
    num_qubits: int,
    population_basis: np.ndarray,
    population_state: np.ndarray,
    *,
    support_cutoff: float = 1e-12,
) -> tuple[int, int, np.ndarray, dict[str, object]]:
    """Find a nonconstant diagonal Pauli-Z symmetry with definite state parity.

    Candidate masks are derived from the exact Pauli flip patterns, so no
    molecule-specific orbital-parity convention is assumed.  Among candidates
    with a definite ground-state parity, the most balanced sector split is
    selected.
    """
    flip_constraints = []
    for raw_group in groups:
        group = _as_group_operator(raw_group)
        for term in group.terms:
            flip_mask = 0
            for qubit, pauli in term:
                if pauli in ("X", "Y"):
                    flip_mask |= 1 << (num_qubits - 1 - int(qubit))
            if flip_mask:
                flip_constraints.append(flip_mask)
    null_basis = _gf2_nullspace(flip_constraints, num_qubits)
    support = np.flatnonzero(np.abs(population_state) > support_cutoff)
    candidates: list[tuple[int, int, int, np.ndarray]] = []
    # The nullity is small for these molecular Hamiltonians.  Enumerating its
    # span also covers products with the fixed spin-population parities.
    for combination in range(1, 1 << len(null_basis)):
        mask = 0
        for index, generator in enumerate(null_basis):
            if (combination >> index) & 1:
                mask ^= generator
        parity = np.asarray(
            [(int(value) & mask).bit_count() & 1 for value in population_basis],
            dtype=np.int8,
        )
        counts = np.bincount(parity, minlength=2)
        if not counts[0] or not counts[1]:
            continue
        support_parities = set(int(parity[index]) for index in support)
        if len(support_parities) != 1:
            continue
        target = next(iter(support_parities))
        selected = np.flatnonzero(parity == target)
        candidates.append((int(min(counts)), mask, target, selected))
    if not candidates:
        raise RuntimeError("No nonconstant exact diagonal-Z symmetry was found")
    _, mask, target, selected = max(candidates, key=lambda item: (item[0], -item[1]))
    restricted_state = population_state[selected]
    outside = np.setdiff1d(np.arange(population_basis.size), selected)
    return mask, target, selected, {
        "kind": "automatically_discovered_diagonal_Z2",
        "pauli_z_mask_integer": int(mask),
        "pauli_z_qubits": [
            num_qubits - 1 - bit
            for bit in range(num_qubits)
            if (mask >> bit) & 1
        ],
        "target_eigenvalue": 1 if target == 0 else -1,
        "population_sector_dimension": int(population_basis.size),
        "restricted_dimension": int(selected.size),
        "other_dimension": int(population_basis.size - selected.size),
        "ground_state_outside_norm": float(np.linalg.norm(population_state[outside])),
        "restricted_ground_state_norm": float(np.linalg.norm(restricted_state)),
        "nullspace_dimension": len(null_basis),
    }


def qubit_operator_sector_matrix(
    operator: QubitOperator,
    num_qubits: int,
    basis_indices: np.ndarray,
    *,
    remove_constant: bool = True,
    coefficient_cutoff: float = 1e-14,
) -> csr_matrix:
    """Construct a QubitOperator directly in a selected computational basis."""
    basis = np.asarray(basis_indices, dtype=np.int64)
    lookup = np.full(1 << num_qubits, -1, dtype=np.int64)
    lookup[basis] = np.arange(basis.size, dtype=np.int64)
    columns = np.arange(basis.size, dtype=np.int64)
    row_parts: list[np.ndarray] = []
    column_parts: list[np.ndarray] = []
    data_parts: list[np.ndarray] = []
    for term, raw_coefficient in operator.terms.items():
        if not term and remove_constant:
            continue
        coefficient = complex(raw_coefficient)
        if abs(coefficient) <= coefficient_cutoff:
            continue
        target = basis.copy()
        phase = np.full(basis.size, coefficient, dtype=np.complex128)
        for qubit, pauli in term:
            bit_mask = 1 << (num_qubits - 1 - int(qubit))
            occupied = (basis & bit_mask) != 0
            if pauli == "X":
                target ^= bit_mask
            elif pauli == "Y":
                phase *= np.where(occupied, -1j, 1j)
                target ^= bit_mask
            elif pauli == "Z":
                phase *= np.where(occupied, -1.0, 1.0)
            else:  # pragma: no cover - OpenFermion validates Pauli labels
                raise ValueError(f"Unsupported Pauli operator: {pauli}")
        rows = lookup[target]
        valid = rows >= 0
        if np.any(valid):
            row_parts.append(rows[valid])
            column_parts.append(columns[valid])
            data_parts.append(phase[valid])
    if not data_parts:
        return csr_matrix((basis.size, basis.size), dtype=np.complex128)
    matrix = coo_matrix(
        (
            np.concatenate(data_parts),
            (np.concatenate(row_parts), np.concatenate(column_parts)),
        ),
        shape=(basis.size, basis.size),
        dtype=np.complex128,
    ).tocsr()
    matrix.sum_duplicates()
    if matrix.nnz:
        matrix.data[np.abs(matrix.data) <= coefficient_cutoff] = 0.0
        matrix.eliminate_zeros()
    return matrix


def diagonalize_components(
    matrix: csr_matrix, *, structural_cutoff: float = 1e-13
) -> ComponentSpectrum:
    """Diagonalize all connected Hermitian blocks, batched by block size."""
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("matrix must be square")
    hermitian_error = float(np.linalg.norm((matrix - matrix.getH()).data))
    if hermitian_error > 1e-10:
        raise ValueError(f"matrix is not Hermitian: residual={hermitian_error}")
    graph = matrix.copy()
    if graph.nnz:
        graph.data = (np.abs(graph.data) > structural_cutoff).astype(np.int8)
        graph.eliminate_zeros()
    count, labels = connected_components(graph, directed=False)
    by_size: dict[int, list[np.ndarray]] = defaultdict(list)
    for component in range(count):
        indices = np.flatnonzero(labels == component).astype(np.int64, copy=False)
        by_size[int(indices.size)].append(indices)
    batches = []
    retained = 0
    for size in sorted(by_size):
        indices = np.stack(by_size[size])
        if size == 1:
            values = np.asarray(matrix.diagonal()[indices[:, 0]].real)[:, None]
            vectors = None
            retained += int(values.size)
        else:
            dense = np.stack(
                [matrix[item, :][:, item].toarray() for item in indices]
            )
            values, vectors = np.linalg.eigh(dense)
            retained += int(values.size + vectors.size)
        batches.append(ComponentBatch(indices, values, vectors))
    return ComponentSpectrum(
        dimension=int(matrix.shape[0]),
        batches=tuple(batches),
        source_nnz=int(matrix.nnz),
        component_count=int(count),
        maximum_component_size=max(by_size, default=0),
        retained_complex_elements=retained,
    )


def component_exponential(
    spectrum: ComponentSpectrum, scaled_time: float
) -> csr_matrix:
    """Materialize one exact group exponential as a sparse block matrix."""
    rows = []
    columns = []
    values = []
    for batch in spectrum.batches:
        indices = batch.indices
        phases = np.exp(1j * float(scaled_time) * batch.eigenvalues)
        if batch.eigenvectors is None:
            gates = phases[:, :, None]
        else:
            gates = (batch.eigenvectors * phases[:, None, :]) @ np.swapaxes(
                batch.eigenvectors.conj(), -1, -2
            )
        size = batch.component_size
        rows.append(np.repeat(indices, size, axis=1).reshape(-1))
        columns.append(np.tile(indices, (1, size)).reshape(-1))
        values.append(gates.reshape(-1))
    return coo_matrix(
        (np.concatenate(values), (np.concatenate(rows), np.concatenate(columns))),
        shape=(spectrum.dimension, spectrum.dimension),
        dtype=np.complex128,
    ).tocsr()


def _prepare_one_group(
    arguments: tuple[object, int, np.ndarray, np.ndarray | None]
) -> tuple[ComponentSpectrum, np.ndarray | None]:
    raw_group, num_qubits, restricted_basis, validation_state = arguments
    matrix = qubit_operator_sector_matrix(
        _as_group_operator(raw_group), num_qubits, restricted_basis
    )
    action = None if validation_state is None else matrix @ validation_state
    return diagonalize_components(matrix), action


def prepare_component_spectra(
    groups: Sequence[object],
    num_qubits: int,
    restricted_basis: np.ndarray,
    *,
    validation_state: np.ndarray | None = None,
    processes: int = 1,
) -> tuple[list[ComponentSpectrum], dict[str, object]]:
    """Prepare compact exact spectra for all grouped Hamiltonians."""
    spectra = []
    total_source_nnz = 0
    total_retained = 0
    maximum_component_size = 0
    component_counts = []
    summed_action = (
        np.zeros(restricted_basis.size, dtype=np.complex128)
        if validation_state is not None
        else None
    )
    arguments = [
        (raw_group, num_qubits, restricted_basis, validation_state)
        for raw_group in groups
    ]
    if processes > 1:
        with ProcessPoolExecutor(max_workers=int(processes)) as executor:
            prepared = list(executor.map(_prepare_one_group, arguments))
    else:
        prepared = [_prepare_one_group(item) for item in arguments]
    for spectrum, action in prepared:
        if summed_action is not None:
            assert action is not None
            summed_action += action
        spectra.append(spectrum)
        total_source_nnz += spectrum.source_nnz
        total_retained += spectrum.retained_complex_elements
        maximum_component_size = max(
            maximum_component_size, spectrum.maximum_component_size
        )
        component_counts.append(spectrum.component_count)
    dimension = int(restricted_basis.size)
    dense_spectra_elements = len(groups) * (dimension * dimension + dimension)
    diagnostics: dict[str, object] = {
        "group_count": len(groups),
        "dimension": dimension,
        "total_source_nnz": int(total_source_nnz),
        "total_retained_complex_elements": int(total_retained),
        "retained_estimated_bytes": int(16 * total_retained),
        "dense_group_spectra_estimated_bytes": int(16 * dense_spectra_elements),
        "compression_ratio": float(total_retained / dense_spectra_elements),
        "maximum_component_size": int(maximum_component_size),
        "minimum_component_count": int(min(component_counts)),
        "median_component_count": float(np.median(component_counts)),
        "maximum_component_count": int(max(component_counts)),
    }
    if summed_action is not None:
        diagnostics["summed_group_action"] = summed_action
    return spectra, diagnostics
