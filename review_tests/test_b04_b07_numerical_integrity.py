"""Regression tests for the combined B04--B07 numerical-integrity audit."""

from __future__ import annotations

import pytest

import audit_b04_b07_numerical_integrity as audit


@pytest.fixture(scope="module")
def result() -> dict:
    return audit.run_analysis()


def test_all_four_component_audits_complete(result: dict) -> None:
    assert result["status"] == "complete"
    assert result["component_status"] == {
        "B04": "complete",
        "B05": "complete",
        "B06": "complete",
        "B07": "complete",
    }


def test_b04_group_symmetry_and_full_sector_equivalence(result: dict) -> None:
    summary = result["B04"]
    assert summary["system_count"] == 2
    assert summary["sector_equivalence_case_count"] == 2
    assert summary["maximum_relative_group_commutator_norm"] < 2e-11
    assert summary["maximum_group_sector_cross_block_norm"] < 2e-11
    assert summary["maximum_projected_full_vs_restricted_unitary_residual"] < 5e-12
    assert summary["maximum_full_pf_sector_leakage_norm"] < 5e-12


def test_b04_negative_control_rejects_groupwise_nonconserving_split(
    result: dict,
) -> None:
    control = result["B04"]["noninvariant_split_control"]
    assert control["detector_passed"] is True
    assert control["total_hamiltonian_commutator_norm"] < 1e-15
    assert control["maximum_group_commutator_norm"] > 0.1
    assert control["full_pf_sector_leakage_norm"] > 1e-3
    assert control["projected_full_vs_restricted_residual"] > 1e-3


def test_b05_actual_branch_is_stable_and_degenerate_control_warns(
    result: dict,
) -> None:
    summary = result["B05"]
    assert summary["actual_time_count"] == 34
    assert summary["actual_selection_disagreement_count"] == 0
    assert summary["minimum_actual_previous_branch_overlap_probability"] > 0.99
    control = summary["degenerate_control"]
    assert control["detector_passed"] is True
    assert control["single_vector_and_continuity_disagreement_count"] > 0
    assert control["minimum_ground_subspace_projection_probability"] > 1 - 1e-12
    assert control["exact_degeneracy_requires_subspace_tracking"] is True


def test_b06_fixed_noise_floor_is_supported_on_analytic_fixture(
    result: dict,
) -> None:
    summary = result["B06"]
    assert summary["fixed_noise_floor_hartree"] == 5e-13
    assert summary["above_floor_point_count"] > 0
    assert summary["below_floor_point_count"] > 0
    assert summary["fixed_floor_supported_on_fixture"] is True
    assert summary["fixed_floor_is_universal_ultrashort_bound"] is False
    assert summary[
        "ultrashort_below_truth_floor_but_float_above_floor_count"
    ] > 0
    assert summary[
        "current_protocol_minimum_time_maximum_float_difference_hartree"
    ] < 5e-13
    assert summary["maximum_float_reference_difference_above_floor_hartree"] < 5e-13
    assert summary["maximum_unitarity_residual"] < 5e-12
    assert summary["maximum_eigenpair_residual"] < 5e-12


def test_b07_independent_paths_commuting_control_and_orders(result: dict) -> None:
    rows = result["_b07_rows"]
    order_rows = result["_b07_order_rows"]
    assert len(rows) == 3
    assert all(row["passed"] for row in rows)
    assert max(row["independent_vs_production_unitary_residual"] for row in rows) < 5e-12
    assert max(row["commuting_pf_vs_exact_unitary_residual"] for row in rows) < 5e-12
    assert all(row["passed"] for row in order_rows)
    fitted = {row["formula_id"]: row["fitted_signed_eigenvalue_shift_order"] for row in order_rows}
    assert fitted["second_order"] == pytest.approx(2.0, abs=0.1)
    assert fitted["yoshida4"] == pytest.approx(4.0, abs=0.1)
    assert fitted["morales_y8m10b"] == pytest.approx(8.0, abs=0.1)


def test_gpu_unavailability_is_explicit_not_silently_substituted(
    result: dict,
) -> None:
    environment = result["B07"]["environment"]
    assert environment["scf_reexecution_mixed_into_cpu_gpu_comparison"] is False
    if not environment["gpu_available"]:
        assert environment["gpu_comparison_status"] == "not_run_gpu_unavailable"


def test_source_sentinels_are_recorded(result: dict) -> None:
    assert all(row["sentinel_present"] for row in result["_source_rows"])
