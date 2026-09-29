from __future__ import annotations

import ast
import json
import math
from pathlib import Path

from review_response import (
    run_pf_spectral_recoverability_d2_a_scoring_audit as audit,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / (
    "review_response/"
    "pf_spectral_recoverability_d2_a_scoring_audit_protocol.json"
)
RUNNER = ROOT / "review_response/run_pf_spectral_recoverability_d2_a_scoring_audit.py"


def coordinate_inputs(predicted_shift: float) -> tuple[dict, dict, dict]:
    time_value = 0.2
    principal = 1.0
    period = 2.0 * math.pi / time_value
    integer = -1
    unwrapped = principal + integer * period
    h_reference = unwrapped - predicted_shift
    prediction = {
        "condition": "synthetic",
        "time_hartree_inverse": time_value,
        "time_hex": time_value.hex(),
        "primary_dimension_used": 8,
        "signed_shift_estimate_hartree": predicted_shift,
        "prefixes": [{
            "dimension": 8,
            "selected_phase_unwrap_integer": integer,
            "selected_unit_circle_eigenvalue_real": math.cos(principal * time_value),
            "selected_unit_circle_eigenvalue_imaginary": math.sin(principal * time_value),
            "h_reference_energy_hartree": h_reference,
            "selected_unwrapped_energy_hartree": unwrapped,
        }],
    }
    scoring = {
        "condition": "synthetic",
        "time_hex": time_value.hex(),
        "predicted_signed_shift_hartree": predicted_shift,
        "direct_signed_shift_hartree": 0.0,
        "predicted_phase_unwrap_integer": integer,
        "truth_phase_unwrap_integer": 0,
        "branch_correct": False,
        "abstained": False,
        "frozen_budget_safe": True,
        "quantum_budget_lower_than_main_baseline": False,
    }
    d1 = {
        "condition": "synthetic",
        "time_hex": time_value.hex(),
        "phase_unwrap_integer": "0",
        "phase_gap_radian": "0.1",
    }
    return prediction, scoring, d1


def test_different_integer_coordinates_do_not_reject_same_physical_branch() -> None:
    prediction, scoring, d1 = coordinate_inputs(1e-3)
    row = audit.audit_coordinate(prediction, scoring, d1)
    assert row["d2_absolute_unwrap_integer"] == -1
    assert row["d1_relative_unwrap_integer"] == 0
    assert row["integer_labels_equal"] is False
    assert row["integer_coordinates_directly_comparable"] is False
    assert row["original_branch_correct"] is False
    assert row["physical_branch_correct"] is True


def test_representation_invariant_half_gap_still_rejects_physical_failure() -> None:
    prediction, scoring, d1 = coordinate_inputs(1.0)
    row = audit.audit_coordinate(prediction, scoring, d1)
    assert row["physical_branch_correct"] is False
    assert row["phase_error_radian"] > row["half_phase_gap_radian"]


def test_common_reference_check_equals_shift_error() -> None:
    prediction, scoring, d1 = coordinate_inputs(1e-3)
    row = audit.audit_coordinate(prediction, scoring, d1)
    reference = abs(prediction["prefixes"][0]["h_reference_energy_hartree"])
    assert math.isclose(
        row["common_reference_energy_error_hartree"],
        row["absolute_shift_error_hartree"],
        rel_tol=0.0,
        abs_tol=2.0 * math.ulp(reference),
    )


def test_protocol_preserves_formal_result_and_forbids_new_science() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["classification"]["post_hoc"] is True
    assert protocol["classification"]["new_scientific_computation"] is False
    assert protocol["completion"]["original_status_unchanged"] is True
    assert protocol["completion"]["d2_b_authorized"] is False
    assert protocol["not_authorized"]["arnoldi_rerun"] is True
    assert protocol["not_authorized"]["hamiltonian_or_pf_action"] is True
    assert protocol["not_authorized"]["new_truth"] is True


def test_runner_imports_only_standard_library_and_has_zero_action_counts() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    forbidden = ("numpy", "scipy", "pyscf", "cupy", "trotterlib")
    assert not any(name.startswith(forbidden) for name in imported)
    assert '"arnoldi_action_count": 0' in source
    assert '"hamiltonian_action_count": 0' in source
    assert '"pf_action_count": 0' in source
    assert '"new_truth_count": 0' in source
    assert '"d2_b_authorized": False' in source
