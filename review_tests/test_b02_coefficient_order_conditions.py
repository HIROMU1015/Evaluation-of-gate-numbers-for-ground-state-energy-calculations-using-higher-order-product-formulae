"""Regression tests for the B02 coefficient and formal-order audit."""

from __future__ import annotations

import pytest

import audit_b02_coefficient_order_conditions as audit


@pytest.fixture(scope="module")
def result() -> dict:
    return audit.run_analysis()


def test_all_unified_comparison_coefficients_pass_complete_word_conditions(
    result: dict,
) -> None:
    assert result["status"] == "complete"
    assert result["formula_count"] == 10
    assert result["production_stored_count"] == 9
    assert result["production_stored_passed"] == 9
    assert result["hard_word_condition_count"] == 2670
    assert result["maximum_production_hard_linf_formula"] == "yoshida8"
    assert result["maximum_production_hard_linf"] < 1e-12


def test_printed_new2_fails_but_separately_projected_value_passes(
    result: dict,
) -> None:
    assert result["printed_new2_passed"] is False
    assert result["projected_new2_passed"] is True
    rows = {
        (row["formula_id"], row["variant"]): row
        for row in result["_variant_rows"]
    }
    printed = rows[("paper_new4_printed_registry", "stored_float_binary")]
    projected = rows[("paper_new4_projected", "stored_float_binary")]
    assert float(printed["complete_word_hard_linf"]) > 1e-10
    assert float(projected["complete_word_hard_linf"]) < 2e-12
    maximum_change = float(result["_projection_rows"][0]["maximum_coefficient_change"])
    assert 9e-9 < maximum_change < 1e-8


def test_odd_moments_are_not_used_as_complete_high_order_test(
    result: dict,
) -> None:
    assert result["moment_only_odd_moments_passed"] is True
    assert result["moment_only_complete_word_conditions_passed"] is False
    assert result["moment_only_complete_word_hard_linf"] > 1.0
    assert all(row["odd_moment_passed"] for row in result["_moment_rows"])
    assert not any(
        row["complete_word_conditions_passed"]
        for row in result["_moment_rows"]
    )


def test_rounding_sweep_resolves_precision_requirements(result: dict) -> None:
    digits = result["minimum_passing_significant_digits"]
    assert digits["paper_new4_printed_registry"] is None
    assert digits["yoshida6_m3"] == 14
    assert digits["yoshida8"] == 16
    assert digits["morales_y8m10b"] == 12
    assert result["maximum_production_crossover_tau"] < 0.02
    assert "unit coefficient scale" in result["crossover_time_basis"]
    assert result["rounding_explains_prior_breakdown_on_current_grid"].startswith(
        "not_determined"
    )


def test_published_morales_decimal_literals_are_kept_separate_from_float(
    result: dict,
) -> None:
    rows = {
        (row["formula_id"], row["variant"]): row
        for row in result["_variant_rows"]
    }
    stored = rows[("morales_y8m10b", "stored_float_binary")]
    published = rows[
        ("morales_y8m10b", "published_decimal_literals_high_precision")
    ]
    assert float(stored["complete_word_hard_linf"]) < 1e-17
    assert float(published["complete_word_hard_linf"]) < 1e-30
    assert stored["weights"] != published["weights"]
