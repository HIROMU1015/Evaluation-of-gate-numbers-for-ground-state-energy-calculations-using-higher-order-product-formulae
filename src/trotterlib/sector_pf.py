"""Dense product-formula construction inside a conserved sector.

The cached builder exploits repeated coefficients in a symmetric composition:
an identical second-order block is constructed once and then reused.  This is
an algebraic reordering of adjacent exponentials of the same Hamiltonian group,
not an approximation.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .pf_decomposition import iter_s2_sequence_steps


GroupSpectrum = tuple[np.ndarray, np.ndarray]


def _left_apply_group_exponential(
    matrix: np.ndarray,
    spectrum: GroupSpectrum,
    scaled_time: float,
) -> np.ndarray:
    values, vectors = spectrum
    return vectors @ (
        np.exp(1j * scaled_time * values)[:, None]
        * (vectors.conj().T @ matrix)
    )


def build_sector_pf_unitary_sequential(
    spectra: Sequence[GroupSpectrum],
    s2_sequence: Sequence[float],
    evolution_time: float,
) -> np.ndarray:
    """Build a dense PF unitary by applying every merged group exponential."""
    if not spectra:
        raise ValueError("spectra must contain at least one Hamiltonian group")
    dimension = int(spectra[0][0].shape[0])
    unitary = np.eye(dimension, dtype=complex)
    for group_index, weight in iter_s2_sequence_steps(
        len(spectra), s2_sequence
    ):
        unitary = _left_apply_group_exponential(
            unitary,
            spectra[group_index],
            float(evolution_time) * float(weight),
        )
    return unitary


def _build_s2_block(
    spectra: Sequence[GroupSpectrum],
    block_weight: float,
    evolution_time: float,
) -> np.ndarray:
    dimension = int(spectra[0][0].shape[0])
    block = np.eye(dimension, dtype=complex)
    for group_index, weight in iter_s2_sequence_steps(
        len(spectra), [block_weight]
    ):
        block = _left_apply_group_exponential(
            block,
            spectra[group_index],
            float(evolution_time) * float(weight),
        )
    return block


def build_sector_pf_unitary_cached_s2(
    spectra: Sequence[GroupSpectrum],
    s2_sequence: Sequence[float],
    evolution_time: float,
) -> np.ndarray:
    """Build a dense PF unitary while reusing identical S2 block matrices."""
    if not spectra:
        raise ValueError("spectra must contain at least one Hamiltonian group")
    dimension = int(spectra[0][0].shape[0])
    unitary = np.eye(dimension, dtype=complex)
    blocks: dict[float, np.ndarray] = {}
    for raw_weight in s2_sequence:
        weight = float(raw_weight)
        block = blocks.get(weight)
        if block is None:
            block = _build_s2_block(spectra, weight, evolution_time)
            blocks[weight] = block
        unitary = block @ unitary
    return unitary


def build_sector_pf_unitary(
    spectra: Sequence[GroupSpectrum],
    s2_sequence: Sequence[float],
    evolution_time: float,
    *,
    method: str = "s2-cache",
) -> np.ndarray:
    """Build a sector PF unitary using the requested exact construction."""
    if method == "sequential":
        return build_sector_pf_unitary_sequential(
            spectra, s2_sequence, evolution_time
        )
    if method == "s2-cache":
        return build_sector_pf_unitary_cached_s2(
            spectra, s2_sequence, evolution_time
        )
    raise ValueError(f"unknown unitary build method: {method}")
