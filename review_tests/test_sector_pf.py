from __future__ import annotations

import numpy as np
import pytest
from scipy.linalg import eigh

from trotterlib.sector_pf import (
    build_sector_pf_unitary_cached_s2,
    build_sector_pf_unitary_sequential,
)


def _random_spectra(
    dimension: int, number_of_groups: int, seed: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    generator = np.random.default_rng(seed)
    spectra: list[tuple[np.ndarray, np.ndarray]] = []
    for _ in range(number_of_groups):
        raw = generator.normal(size=(dimension, dimension)) + 1j * generator.normal(
            size=(dimension, dimension)
        )
        matrix = raw + raw.conj().T
        spectra.append(eigh(matrix, check_finite=False))
    return spectra


@pytest.mark.parametrize(
    "sequence",
    [
        [0.2, -0.3, 0.7, -0.3, 0.2],
        [0.2, 0.2, -0.1, 0.2, 0.2],
    ],
)
def test_cached_s2_builder_matches_sequential_builder(
    sequence: list[float],
) -> None:
    spectra = _random_spectra(dimension=7, number_of_groups=4, seed=1234)

    sequential = build_sector_pf_unitary_sequential(spectra, sequence, 0.83)
    cached = build_sector_pf_unitary_cached_s2(spectra, sequence, 0.83)

    assert np.linalg.norm(cached - sequential) / np.linalg.norm(sequential) < 1e-13
    identity = np.eye(sequential.shape[0])
    assert np.linalg.norm(cached.conj().T @ cached - identity) < 1e-12
