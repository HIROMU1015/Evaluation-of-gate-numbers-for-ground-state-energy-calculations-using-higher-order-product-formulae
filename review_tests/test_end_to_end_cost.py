from __future__ import annotations

import pytest

from trotterlib.end_to_end_cost import ExpectedCostModel


def test_pf_only_limit_reduces_to_rotation_count() -> None:
    model = ExpectedCostModel()

    assert model.expected_cost(1234) == 1234


def test_expected_cost_uses_geometric_attempt_count() -> None:
    model = ExpectedCostModel(
        one_time_cost=10,
        state_preparation_per_attempt=20,
        qpe_fixed_per_attempt=30,
        cost_per_pf_rotation=2,
        ground_state_overlap_probability=0.25,
        conditional_qpe_success_probability=0.8,
    )

    assert model.success_probability_per_attempt == pytest.approx(0.2)
    assert model.expected_attempts == pytest.approx(5.0)
    assert model.expected_cost(100) == pytest.approx(10 + 5 * (20 + 30 + 200))


def test_shared_non_pf_components_preserve_pf_rotation_ranking() -> None:
    model = ExpectedCostModel(
        one_time_cost=100,
        state_preparation_per_attempt=500,
        qpe_fixed_per_attempt=200,
        cost_per_pf_rotation=7,
        ground_state_overlap_probability=0.1,
        conditional_qpe_success_probability=0.7,
    )

    assert model.expected_cost(1_000) < model.expected_cost(1_200)


@pytest.mark.parametrize("probability", [0.0, -0.1, 1.1])
def test_invalid_success_probability_is_rejected(probability: float) -> None:
    with pytest.raises(ValueError):
        ExpectedCostModel(ground_state_overlap_probability=probability)
