"""Low-storage PF eigenphase estimates from repeated overlap moments."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def _moment_at(moments: np.ndarray, index: int) -> complex:
    """Return a positive or negative unitary moment."""
    if index >= 0:
        return complex(moments[index])
    return complex(np.conj(moments[-index]))


def dominant_phase_from_moments(
    moments: Sequence[complex],
    *,
    evolution_time: float,
    reference_energy: float,
    subspace_dimension: int | None = None,
    gram_relative_cutoff: float = 1e-10,
) -> dict[str, Any]:
    """Estimate the dominant PF eigenphase from ``<psi|U**k|psi>``.

    The routine assumes the project convention

    ``U |phi_j> = exp(+i * E_j * evolution_time) |phi_j>``.

    It first demodulates the moments by the known reference energy.  It then
    solves the Rayleigh--Ritz problem in the time-evolved subspace without
    storing the time-evolved state vectors.  For a requested dimension ``m``,
    only moments ``C_0, ..., C_m`` are needed.
    """
    raw = np.asarray(moments, dtype=complex).ravel()
    if raw.size < 2:
        raise ValueError("At least C_0 and C_1 are required")
    if evolution_time <= 0 or not np.isfinite(evolution_time):
        raise ValueError("evolution_time must be finite and positive")
    if not np.isfinite(reference_energy):
        raise ValueError("reference_energy must be finite")
    if not 0 < gram_relative_cutoff < 1:
        raise ValueError("gram_relative_cutoff must lie in (0, 1)")
    if not np.all(np.isfinite(raw.real)) or not np.all(np.isfinite(raw.imag)):
        raise ValueError("moments must be finite")
    if abs(raw[0]) == 0:
        raise ValueError("C_0 must be nonzero")

    raw = raw / raw[0]
    maximum_dimension = raw.size - 1
    dimension = maximum_dimension if subspace_dimension is None else int(
        subspace_dimension
    )
    if dimension < 1 or dimension > maximum_dimension:
        raise ValueError(
            "subspace_dimension must be between 1 and len(moments) - 1"
        )

    indices = np.arange(raw.size, dtype=float)
    demodulated = raw * np.exp(
        -1j * reference_energy * evolution_time * indices
    )
    overlap = np.empty((dimension, dimension), dtype=complex)
    projected_unitary = np.empty_like(overlap)
    for row in range(dimension):
        for column in range(dimension):
            overlap[row, column] = _moment_at(
                demodulated, column - row
            )
            projected_unitary[row, column] = _moment_at(
                demodulated, column - row + 1
            )

    overlap = 0.5 * (overlap + overlap.conj().T)
    gram_values, gram_vectors = np.linalg.eigh(overlap)
    largest_gram = float(gram_values[-1])
    if largest_gram <= 0:
        raise RuntimeError("The moment Gram matrix is not positive")
    retained = gram_values > gram_relative_cutoff * largest_gram
    if not np.any(retained):
        raise RuntimeError("The Gram cutoff removed the entire moment space")

    kept_values = gram_values[retained]
    canonical = gram_vectors[:, retained] / np.sqrt(kept_values)
    reduced_unitary = canonical.conj().T @ projected_unitary @ canonical
    ritz_values, reduced_vectors = np.linalg.eig(reduced_unitary)

    candidates: list[dict[str, Any]] = []
    positive_moments = demodulated[:dimension]
    for index, ritz_value in enumerate(ritz_values):
        coefficients = canonical @ reduced_vectors[:, index]
        norm_squared = float(
            np.real(coefficients.conj() @ overlap @ coefficients)
        )
        if norm_squared <= 0 or abs(ritz_value) == 0:
            continue
        coefficients /= np.sqrt(norm_squared)
        ground_amplitude = complex(positive_moments @ coefficients)
        overlap_probability = float(abs(ground_amplitude) ** 2)
        phase = float(np.angle(ritz_value))
        energy_shift = phase / evolution_time
        candidates.append(
            {
                "ritz_index": int(index),
                "phase_radians": phase,
                "energy_shift_hartree": energy_shift,
                "effective_energy_hartree": reference_energy + energy_shift,
                "ritz_value_real": float(ritz_value.real),
                "ritz_value_imag": float(ritz_value.imag),
                "ritz_value_magnitude": float(abs(ritz_value)),
                "estimated_reference_overlap_probability": overlap_probability,
            }
        )

    if not candidates:
        raise RuntimeError("No finite Ritz candidates were produced")
    selected = max(
        candidates,
        key=lambda candidate: candidate[
            "estimated_reference_overlap_probability"
        ],
    )
    smallest_kept = float(kept_values[0])
    return {
        "subspace_dimension": dimension,
        "retained_rank": int(np.count_nonzero(retained)),
        "gram_relative_cutoff": float(gram_relative_cutoff),
        "smallest_retained_gram_eigenvalue": smallest_kept,
        "largest_gram_eigenvalue": largest_gram,
        "retained_gram_eigenvalue_ratio": smallest_kept / largest_gram,
        "discarded_gram_eigenvalues": int(dimension - np.count_nonzero(retained)),
        "selected": selected,
        "candidates": candidates,
    }
