"""Regression tests for the B03 S2 path-equivalence audit."""

from __future__ import annotations

import audit_b03_s2_order_merge_equivalence as audit


def test_explicit_merge_sequential_cache_and_inverse_paths_agree() -> None:
    rows, _ = audit.sequence_and_matrix_checks()

    assert len(rows) == 15
    assert all(row["passed"] for row in rows)
    assert {row["number_of_groups"] for row in rows} == {1, 2, 3}
    assert max(row["cached_vs_explicit_unitary_residual"] for row in rows) < 3e-12
    assert max(row["maximum_delta_e_path_difference"] for row in rows) < 3e-12


def test_nonpalindromic_probe_detects_left_right_product_reversal() -> None:
    rows = audit.order_direction_checks()

    assert len(rows) == 3
    assert all(row["passed"] for row in rows)
    noncommuting = [row for row in rows if row["number_of_groups"] > 1]
    assert min(row["wrong_right_product_control_residual"] for row in noncommuting) > 1e-3
    assert min(
        row["same_sequence_negative_time_vs_adjoint_residual"]
        for row in noncommuting
    ) > 1e-3
    assert max(
        row["inverse_sequence_vs_adjoint_residual"] for row in rows
    ) < 3e-12


def test_qiskit_registry_and_precomputed_paths_match_explicit_reference() -> None:
    rows = audit.qiskit_registry_checks()

    assert len(rows) == 9
    assert all(row["passed"] for row in rows)
    assert {row["formula_id"] for row in rows} == {
        "second_order",
        "yoshida4",
        "morales_y8m10b",
    }
    assert max(row["precomputed_vs_explicit_unitary_residual"] for row in rows) < 3e-12
    assert all(
        row["expected_rotation_count"]
        == row["legacy_rotation_count"]
        == row["precomputed_rotation_count"]
        for row in rows
    )


def test_zero_weight_control_records_identity_rotation_overhead() -> None:
    rows, _ = audit.sequence_and_matrix_checks()
    zero_rows = [row for row in rows if row["formula_id"] == "zero_middle_control"]

    assert len(zero_rows) == 3
    assert all(
        row["merged_rotation_count"]
        > row["effective_nonzero_merged_rotation_count"]
        for row in zero_rows
        if row["number_of_groups"] > 1
    )
    one_group = next(row for row in zero_rows if row["number_of_groups"] == 1)
    assert one_group["merged_rotation_count"] == one_group[
        "effective_nonzero_merged_rotation_count"
    ]
    assert max(row["unmerged_vs_merged_unitary_residual"] for row in zero_rows) < 3e-12


def test_complete_audit_summary_and_source_sentinels() -> None:
    result = audit.run_analysis()

    assert result["status"] == "complete"
    assert result["formula_count"] == 5
    assert result["matrix_case_count"] == 15
    assert result["qiskit_registry_case_count"] == 9
    assert result["direction_probe_case_count"] == 3
    assert result["zero_coefficient_identity_rotations_retained"] is True
    assert result["maximum_dense_unitary_residual"] < 3e-12
    assert result["maximum_qiskit_unitary_residual"] < 3e-12
    assert all(row["sentinel_present"] for row in result["_source_rows"])
