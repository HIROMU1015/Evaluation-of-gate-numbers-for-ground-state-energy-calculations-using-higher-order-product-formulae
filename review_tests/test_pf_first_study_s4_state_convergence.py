from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pytest

from review_response import run_pf_first_study_s4_state_convergence as s4


def test_protocol_hash_and_fixed_scope() -> None:
    assert hashlib.sha256(s4.PROTOCOL_PATH.read_bytes()).hexdigest() == s4.EXPECTED_PROTOCOL_SHA256
    protocol = s4._protocol()
    assert protocol["state_pair"]["retained_squared_norm"] == 0.99
    assert protocol["operator_sensitive_diagnostic"]["risk_threshold"] == 0.05
    assert protocol["phase_b"]["exact_time_factors"] == [0.99, 1.0, 1.01]
    assert protocol["resource_accounting"]["budget_multiplier"] == 1.01
    assert len(s4._conditions(protocol)) == 6


def test_truncation_is_deterministic_and_uses_index_tie_break() -> None:
    state = np.asarray([0.6, -0.6, 0.4j, 0.2], dtype=np.complex128)
    state /= np.linalg.norm(state)
    first, metadata = s4.truncate_cisd_state(state, 0.70)
    second, again = s4.truncate_cisd_state(state, 0.70)
    assert np.array_equal(first, second)
    assert metadata == again
    assert metadata["hamiltonian_used_for_truncation"] is False
    assert np.count_nonzero(first) == metadata["retained_coefficient_count"]
    assert np.linalg.norm(first) == pytest.approx(1.0)
    # Equal 0.6 magnitudes retain restricted-basis index 0 before index 1.
    one, one_meta = s4.truncate_cisd_state(state, 0.30)
    assert one_meta["retained_coefficient_count"] == 1
    assert one[0] != 0 and one[1] == 0


def test_state_risk_uses_fixed_magnitude_and_signed_rules() -> None:
    epsilon = 1e-3
    safe = s4.assess_state_risk([1e-4, 2e-4], [0.99e-4, 2.01e-4], epsilon, 0.05, 1e-9)
    assert safe["state_risk"] is False
    magnitude = s4.assess_state_risk([1e-4], [3e-5], epsilon, 0.05, 1e-9)
    assert magnitude["magnitude_risk"] is True
    signed = s4.assess_state_risk([1e-4], [-1e-4], 1.0, 0.05, 1e-9)
    assert signed["sign_risk"] is True


def test_phase_a_selector_has_no_source_or_truth_arguments() -> None:
    assert set(inspect.signature(s4.run_phase_a_selector).parameters) == {"output_dir"}
    source = inspect.getsource(s4.run_phase_a_selector)
    assert "h01_root" not in source
    assert "p03_root" not in source
    assert "exact_ground" not in source
    assert "_source_truth_points" not in source
    assert "direct_branch_point" not in source


def _baseline_condition() -> dict:
    rows = []
    for formula, cost in (("current_m3", 10.0), ("yoshida4", 12.0)):
        rows.append({
            "condition": "synthetic",
            "formula": formula,
            "rotations": 10,
            "proxy_analytic_time": 1.0,
            "model": {"coefficient_powers": [4, 6], "coefficient_values": [1e-5, 1e-5]},
            "diagnostic": {},
            "fallback_triggered": False,
            "maximum_relative_time_after_fallback": 1.8,
            "eligible": True,
            "rejection_reason": None,
            "optimum": {"time": 1.0, "relative_to_proxy_t_ana": 1.0, "signed_shift_hartree": 1e-5, "error_hartree": 1e-5, "cost": cost},
        })
    return {"pf_predictions": rows}


def test_targeted_fallback_only_caps_flagged_formula(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    def fake_optimum(model, t_ana, rotations, maximum):
        calls.append(maximum)
        relative = 0.5 if maximum == 0.5 else 1.0
        return {"time": relative, "relative_to_proxy_t_ana": relative, "signed_shift_hartree": 0.0, "error_hartree": 0.0, "cost": relative}
    monkeypatch.setattr(s4, "_optimum", fake_optimum)
    models = {formula: row["model"] for formula, row in zip(s4.FORMULAE, _baseline_condition()["pf_predictions"], strict=True)}
    result = s4._strategy_pf_rows(
        _baseline_condition(), {"current_m3": True, "yoshida4": False}, models
    )
    targeted = {row["formula"]: row for row in result["state_targeted_fallback"]}
    universal = {row["formula"]: row for row in result["universal_fallback"]}
    assert targeted["current_m3"]["maximum_relative_time_after_fallback"] == 0.5
    assert targeted["yoshida4"]["maximum_relative_time_after_fallback"] == 1.8
    assert all(row["maximum_relative_time_after_fallback"] == 0.5 for row in universal.values())


def test_selected_coordinates_are_deduplicated() -> None:
    strategies = {}
    for index, strategy in enumerate(s4.STRATEGIES):
        strategies[strategy] = {"selection": {
            "status": "selected", "selected_formula": "current_m3",
            "selected_time": 0.4 if index < 5 else 0.5,
        }}
    predictions = {"conditions": [{"condition": "c", "strategies": strategies}]}
    grouped = s4.unique_selected_coordinates(predictions)
    assert grouped == {("c", "current_m3"): [0.4, 0.5]}


def test_direct_cache_key_binds_protocol_prediction_and_hamiltonian() -> None:
    key = s4._direct_cache_key("p" * 64, "c", "f", 0.2, "gpu", {"hamiltonian_sha256": "h" * 64})
    assert key["s4_protocol_sha256"] == s4.EXPECTED_PROTOCOL_SHA256
    assert key["s4_prediction_sha256"] == "p" * 64
    assert key["hamiltonian_sha256"] == "h" * 64
    assert key["absolute_time"] == 0.2


def test_benefit_decision_requires_all_three_fixed_gates() -> None:
    rows = []
    regrets = {
        "practical_baseline": 0.20,
        "state_targeted_fallback": 0.10,
        "universal_fallback": 0.13,
        "equal_cost_extra_points": 0.12,
        "fixed_current_m3": 0.2,
        "fixed_yoshida4": 0.2,
        "diagnostic_record_only": 0.2,
    }
    for strategy in s4.STRATEGIES:
        for index in range(6):
            rows.append({
                "strategy": strategy,
                "condition": f"c{index}",
                "evaluation_group": "primary" if index < 4 else "stress_test",
                "joint_formula_time_selection_regret": regrets[strategy],
                "success_gamma_1_01": True,
            })
    decision = s4.evaluate_benefit(rows)
    assert decision["minimum_safety"] is True
    assert decision["efficiency_gain"] is True
    assert decision["diagnostic_specificity"] is True
    assert decision["outcome_benefit"] is True
    rows[0]["success_gamma_1_01"] = False
    # The modified row is baseline, so targeted safety remains unchanged.
    assert s4.evaluate_benefit(rows)["minimum_safety"] is True
    targeted = next(row for row in rows if row["strategy"] == "state_targeted_fallback")
    targeted["success_gamma_1_01"] = False
    assert s4.evaluate_benefit(rows)["outcome_benefit"] is False


def test_scope_forbids_s5_without_benefit() -> None:
    protocol = s4._protocol()
    assert protocol["decision"]["next_step_if_benefit"].startswith("Freeze one S5")
    assert protocol["decision"]["next_step_if_no_benefit"].startswith("Do not add diagnostics")
    assert any("S5 is forbidden" in row for row in protocol["scope_limits"])
