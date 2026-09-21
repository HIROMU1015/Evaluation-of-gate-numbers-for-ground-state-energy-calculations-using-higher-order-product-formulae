"""Regression tests for the B01 sign, unit, and constant audit."""

from __future__ import annotations

import audit_b01_time_units_constants as audit


def test_dense_pf_and_qiskit_sign_conventions_are_distinguished() -> None:
    rows = {row["check_id"]: row for row in audit.small_matrix_checks()}
    assert len(rows) == 8
    assert all(row["passed"] for row in rows.values())
    assert rows["sector_pf_positive_time_matches_manual_plus_i"][
        "measured_residual"
    ] < 2e-12
    assert rows["qiskit_native_positive_time_matches_minus_i"][
        "measured_residual"
    ] < 2e-12
    assert rows["wrong_sign_control_is_distinguishable"][
        "measured_residual"
    ] > 0.1


def test_constant_shift_leaves_corrected_pf_bias_invariant() -> None:
    rows = audit.constant_shift_checks()
    assert {row["time_hartree_inverse"] for row in rows} == {0.43, -0.43}
    assert all(row["passed"] for row in rows)
    assert max(
        row["corrected_bias_absolute_difference_hartree"] for row in rows
    ) < 1e-12
    assert max(row["global_phase_matrix_residual"] for row in rows) < 2e-12


def test_atomic_time_and_coordinate_conversions_and_nuclear_restore() -> None:
    unit_rows = audit.energy_time_unit_checks()
    coordinate_rows = audit.coordinate_and_nuclear_checks()
    assert len(unit_rows) == 3
    assert len(coordinate_rows) == 7
    assert all(row["passed"] for row in unit_rows)
    assert all(row["passed"] for row in coordinate_rows)
    lookup = {row["check_id"]: row for row in coordinate_rows}
    assert lookup["angstrom_to_bohr_coordinates"]["measured_residual"] == 0.0
    assert lookup["nuclear_repulsion_remove_restore_fci"][
        "measured_residual"
    ] < 2e-13


def test_current_implementation_path_sentinels_are_present() -> None:
    rows = audit.implementation_path_checks()
    assert len(rows) == 7
    assert all(row["sentinel_present"] for row in rows)
    conventions = {row["path_id"]: row["evolution_convention"] for row in rows}
    assert conventions["dense_sector_pf"] == "exp(+i H tau)"
    assert conventions["component_sector_pf"] == "exp(+i H tau)"
    assert conventions["qiskit_gate_native"] == "exp(-i H tau)"
