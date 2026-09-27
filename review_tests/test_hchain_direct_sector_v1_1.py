from __future__ import annotations

import numpy as np
import pytest

import hchain_direct_sector_v1_1 as sector
import run_hchain_direct_optimal_time_scaling_v1_1 as wrapper


def _state(indices: list[int], dimension: int = 16) -> np.ndarray:
    result = np.zeros(dimension, dtype=complex)
    result[indices] = 1.0 / np.sqrt(len(indices))
    return result


def test_population_inference_selects_block_ordering() -> None:
    indices, populations, convention = sector.fixed_population_indices(
        _state([0b0101, 0b0110, 0b1001, 0b1010]), 4
    )
    assert convention == "block_alpha_beta"
    assert populations == (1, 1)
    assert indices.tolist() == [0b0101, 0b0110, 0b1001, 0b1010]


def test_population_inference_selects_interleaved_ordering() -> None:
    indices, populations, convention = sector.fixed_population_indices(
        _state([0b0011, 0b0110, 0b1001, 0b1100]), 4
    )
    assert convention == "interleaved_even_odd"
    assert populations == (1, 1)
    assert indices.tolist() == [0b0011, 0b0110, 0b1001, 0b1100]


def test_population_inference_rejects_ambiguous_single_basis_state() -> None:
    with pytest.raises(RuntimeError, match="ambiguous"):
        sector.fixed_population_indices(_state([0b0011]), 4)


def test_H2_preparation_uses_interleaved_sector_without_leakage() -> None:
    system = sector.prepare_sparse_sector_system_v1_1(2)
    audit = system["sector"]
    assert audit["state_vector_ordering_convention"] == "interleaved_even_odd"
    assert audit["population_counts"] == [1, 1]
    assert audit["dimension"] == 4
    assert audit["maximum_group_sector_leakage_frobenius_norm"] <= 1e-11
    assert audit["ground_state_eigenpair_residual"] <= 1e-9


def test_wrapper_pins_parent_and_amendment_hashes() -> None:
    assert len(wrapper.EXPECTED_PARENT_PROTOCOL_SHA256) == 64
    assert len(wrapper.EXPECTED_AMENDMENT_SHA256) == 64
    assert wrapper.EXPECTED_PARENT_PROTOCOL_SHA256 != wrapper.EXPECTED_AMENDMENT_SHA256
