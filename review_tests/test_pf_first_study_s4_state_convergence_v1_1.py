from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from review_response import run_pf_first_study_s4_state_convergence as base
from review_response import run_pf_first_study_s4_state_convergence_v1_1 as v1_1


def test_amendment_hash_parent_and_frozen_prediction() -> None:
    amendment = v1_1._load_and_verify_amendment()
    assert amendment["parent_s4_protocol_sha256"] == base.EXPECTED_PROTOCOL_SHA256
    assert amendment["frozen_phase_a"]["result_commit"] == v1_1.EXPECTED_PHASE_A_COMMIT
    assert amendment["frozen_phase_a"]["prediction_sha256"] == v1_1.EXPECTED_PREDICTION_SHA256
    assert amendment["failed_phase_b_preflight"]["new_direct_truth_point_count"] == 0


def test_uniform_rule_applies_to_all_groups_and_counts_anchors_as_new() -> None:
    amendment = v1_1._load_and_verify_amendment()
    rule = amendment["uniform_anchor_rule"]
    accounting = amendment["fixed_accounting"]
    assert rule["applies_to"].startswith("all 12")
    assert rule["anchor_time_factor_of_minimum_inserted_coordinate"] == 0.5
    assert rule["new_direct_truth_coordinate"] is True
    assert rule["saved_h01_native_anchor_used"] is False
    assert accounting["maximum_inserted_direct_coordinates"] == 60
    assert accounting["new_uniform_anchor_coordinates"] == 12
    assert accounting["maximum_total_new_direct_coordinates"] == 72
    assert accounting["saved_anchor_recomputation_count"] == 0


def test_v1_1_cache_key_cannot_reuse_parent_cache() -> None:
    system = {"hamiltonian_sha256": "h" * 64}
    parent = base._direct_cache_key(
        "p" * 64, "condition", "current_m3", 0.2, "gpu", system
    )
    amended = base._direct_cache_key(
        "p" * 64, "condition", "current_m3", 0.2, "gpu", system,
        v1_1.EXPECTED_AMENDMENT_SHA256,
    )
    assert "s4_phase_b_amendment_sha256" not in parent
    assert amended["s4_phase_b_amendment_sha256"] == v1_1.EXPECTED_AMENDMENT_SHA256
    assert amended != parent


def _synthetic_predictions() -> dict:
    conditions = []
    strategies = list(base.STRATEGIES)
    for condition_index in range(6):
        selections = {}
        # Every condition uses both PFs. The first two conditions have four
        # unique coordinates and the remaining four have three: 2*4+4*3=20.
        current_times = [0.10, 0.20] if condition_index < 2 else [0.10]
        yoshida_times = [0.30, 0.40]
        for index, strategy in enumerate(strategies):
            if index < 4:
                formula = "current_m3"
                time_value = current_times[index % len(current_times)]
            else:
                formula = "yoshida4"
                time_value = yoshida_times[(index - 4) % len(yoshida_times)]
            selections[strategy] = {"selection": {
                "status": "selected",
                "selected_formula": formula,
                "selected_time": time_value,
            }}
        conditions.append({
            "condition": f"condition_{condition_index}",
            "strategies": selections,
        })
    return {"conditions": conditions}


def test_preflight_derives_all_anchor_times_without_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    phase_a = tmp_path / "phase_a"
    failed = tmp_path / "failed_phase_b"
    phase_a.mkdir()
    failed.mkdir()
    (phase_a / "predictions.json").write_text("frozen\n", encoding="utf-8")
    predictions = _synthetic_predictions()
    monkeypatch.setattr(
        base, "verify_phase_a_freeze",
        lambda root: ({"prediction_sha256": v1_1.EXPECTED_PREDICTION_SHA256}, predictions),
    )
    original_sha = base._sha256
    monkeypatch.setattr(
        base, "_sha256",
        lambda path: (
            v1_1.EXPECTED_PREDICTION_SHA256
            if Path(path).name == "predictions.json" else original_sha(Path(path))
        ),
    )
    monkeypatch.setattr(base, "_git_is_ancestor", lambda *args: True)
    amendment, record = v1_1.preflight(phase_a, failed)
    assert amendment["protocol_id"] == "pf_first_study_s4_uniform_anchor_v1_1"
    assert record["truth_opened_by_preflight"] is False
    assert record["unique_selected_coordinate_count"] == 20
    assert record["condition_formula_group_count"] == 12
    assert len(record["planned_anchors"]) == 12
    assert all(
        row["uniform_anchor_time"] == pytest.approx(0.5 * row["minimum_inserted_time"])
        for row in record["planned_anchors"]
    )


def test_wrapper_changes_only_phase_b_and_defers_complete() -> None:
    source = inspect.getsource(v1_1.run)
    assert "run_phase_a" not in source
    assert "phase_b_amendment=amendment" in source
    assert "defer_complete_marker=True" in source
    assert "COMPLETE" in source
