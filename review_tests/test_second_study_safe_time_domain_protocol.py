from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from review_response import second_study_safe_time_domain_guard as guard


PROTOCOL_PATH = Path(
    "review_response/second_study_safe_time_domain_protocol.json"
)
AUDIT_PATH = Path(
    "review_response/second_study_safe_time_domain_source_leakage_audit.json"
)


def _protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def _predictions() -> dict:
    protocol, protocol_sha = guard.load_protocol()
    rows = []
    for item in protocol["data_partition"]["independent_evaluation"][
        "conditions"
    ]:
        strategies = {
            strategy: {
                "status": "selected",
                "selected_time_hartree_inverse": 0.49,
            }
            for strategy in guard.STRATEGIES
        }
        rows.append(
            {
                "condition": item["name"],
                "proxy_analytic_time_hartree_inverse": 1.0,
                "strategies": strategies,
            }
        )
    return {
        "schema": "second_study_safe_time_domain_phase_a_predictions_v1",
        "protocol_sha256": protocol_sha,
        "oracle_access": {key: 0 for key in guard.ORACLE_ACCESS_COUNTERS},
        "conditions": rows,
    }


def test_protocol_hash_sidecar_and_scope_are_frozen() -> None:
    protocol, digest = guard.load_protocol()
    expected = Path(str(PROTOCOL_PATH) + ".sha256").read_text().split()[0]
    assert digest == expected
    assert digest == hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()
    assert protocol["scope"]["formulae"] == ["current_m3"]
    assert protocol["scope"]["pf_selection_enabled"] is False
    assert protocol["scope"]["new_direct_truth_in_protocol_preparation"] == 0
    assert protocol["scope"]["phase_b_executed_in_protocol_preparation"] is False
    assert protocol["information_source"]["selected"] == (
        "multiple_window_consistency"
    )
    assert not any(
        protocol["information_source"]["other_candidate_sources_enabled"].values()
    )


def test_development_and_independent_conditions_do_not_overlap() -> None:
    protocol = _protocol()
    development = set(
        protocol["data_partition"]["development_only"][
            "rule_development_conditions"
        ]
    )
    evaluation = {
        row["name"]
        for row in protocol["data_partition"]["independent_evaluation"][
            "conditions"
        ]
    }
    assert development.isdisjoint(evaluation)
    assert evaluation == {
        "LiF_active_eq_sto3g",
        "LiF_active_stretch150_sto3g",
        "HCl_full_eq_sto3g",
        "HCl_full_stretch150_sto3g",
    }
    assert protocol["data_partition"]["independent_evaluation"][
        "replacement_after_preflight_failure"
    ].startswith("forbidden")


def test_candidate_sequence_thresholds_and_direct_count_are_frozen() -> None:
    protocol = _protocol()
    extension = protocol["phase_a"]["extension"]
    assert extension["candidate_sequence_relative_to_t_ana"] == [
        0.65,
        0.8,
        0.95,
        1.1,
        1.25,
        1.4,
        1.55,
        1.7,
    ]
    assert extension["window_width_points"] == 3
    assert extension["one_step_residual_over_epsilon_maximum"] == 0.05
    assert extension[
        "adjacent_window_disagreement_over_epsilon_maximum"
    ] == 0.05
    assert extension[
        "minimum_predicted_budget_reduction_relative_to_current_fallback"
    ] == 0.05
    plan = protocol["phase_b"]["truth_coordinate_plan"]
    assert plan["maximum_candidate_grid_coordinates"] == 36
    assert plan["maximum_original_selection_coordinates"] == 4
    assert plan["new_anchor_coordinates"] == 4
    assert plan["maximum_total_new_direct_truth_coordinates"] == 44
    assert plan["old_direct_cache_reuse"] == 0


def test_selector_allowlist_rejects_truth_and_past_labels() -> None:
    _, protocol_sha = guard.load_protocol()
    allowed = {
        "schema": "second_study_safe_time_domain_phase_a_input_v1",
        "condition": "LiF_active_eq_sto3g",
        "protocol_sha256": protocol_sha,
        "hamiltonian_sha256": "h" * 64,
        "hamiltonian": object(),
        "component_spectra": [],
        "term_counts": [],
        "cisd_state": [1.0],
        "current_m3": {"s2_sequence": [0.1]},
        "target_error_hartree": 0.00015936001019904,
        "measurement_costs": {},
        "runtime_cache_key": {},
    }
    guard.validate_phase_a_selector_payload(allowed)

    with pytest.raises(guard.ProtocolBoundaryError, match="forbidden"):
        guard.validate_phase_a_selector_payload(
            {**allowed, "current_m3": {"direct_truth": 1e-6}}
        )
    with pytest.raises(guard.ProtocolBoundaryError, match="unexpected"):
        guard.validate_phase_a_selector_payload(
            {**allowed, "exact_ground_state": [1.0]}
        )
    with pytest.raises(guard.ProtocolBoundaryError, match="forbidden"):
        guard.validate_phase_a_selector_payload(
            {**allowed, "measurement_costs": {"past_label": "safe"}}
        )


def test_prediction_oracle_counters_must_be_exactly_zero() -> None:
    predictions = _predictions()
    guard.validate_phase_a_predictions(predictions)
    predictions["oracle_access"]["direct_truth_open_count"] = 1
    with pytest.raises(guard.ProtocolBoundaryError, match="oracle access"):
        guard.validate_phase_a_predictions(predictions)


def test_phase_b_plan_is_derived_without_truth_and_is_bounded() -> None:
    predictions = _predictions()
    plan = guard.derive_phase_b_coordinate_plan(predictions)
    assert len(plan) == 4
    assert sum(len(row["coordinates"]) for row in plan) == 44
    assert all(
        row["anchor_time_hartree_inverse"] == pytest.approx(0.245)
        for row in plan
    )
    assert all(
        all(
            "truth" not in key.lower()
            for coordinate in row["coordinates"]
            for key in coordinate
        )
        for row in plan
    )


def test_phase_a_freeze_detects_prediction_tampering(tmp_path: Path) -> None:
    predictions = _predictions()
    prediction_path = tmp_path / guard.PREDICTION_FILE
    prediction_path.write_text(
        json.dumps(predictions, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    marker = guard.freeze_phase_a(tmp_path, "a" * 40)
    assert marker["phase_b_coordinate_count"] == 44
    guard.verify_phase_a_freeze(tmp_path)
    prediction_path.write_bytes(prediction_path.read_bytes() + b"\n")
    with pytest.raises(guard.ProtocolBoundaryError, match="prediction SHA-256"):
        guard.verify_phase_a_freeze(tmp_path)


def test_source_audit_preserves_first_study_boundaries() -> None:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    assert audit["new_computation"] == {
        "direct_truth_coordinates": 0,
        "phase_a_proxy_points": 0,
        "new_hamiltonians": 0,
        "new_states": 0,
        "new_fits": 0,
    }
    facts = audit["fixed_fact_reproduction"]
    assert facts["s0_gamma_1_01_safe"] == {
        "safe_count": 6,
        "condition_count": 6,
        "passed": True,
    }
    assert facts["pf_selection_factor_one"]["count"] == 6
    assert facts["s4"]["strategy_condition_row_count"] == 42
    assert facts["s4"]["condition_count"] == 6
    assert facts["s4"]["strategy_count"] == 7
    assert facts["s4"]["corrected_beta"] == 1.2
    assert facts["s4"]["corrected_outcome"] == "no_benefit"
    assert audit["git_identity"]["first_study_s0_result"][
        "is_ancestor_of_base"
    ] is False
    assert all(
        row["byte_identical_to_result_commit"]
        for row in audit["first_study_artifact_identity"]["s0"]["files"].values()
    )


def test_source_audit_file_hashes_match_worktree() -> None:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    for row in audit["input_files"]["tracked_at_base"]:
        assert hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() == row[
            "sha256"
        ]

    identities = audit["first_study_artifact_identity"]
    for filename, record in identities["s0"]["files"].items():
        path = Path(identities["s0"]["artifact"]) / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    for filename, expected in identities["s4"]["files"].items():
        path = Path(identities["s4"]["artifact"]) / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    completion = Path(identities["completion"]["artifact"])
    assert hashlib.sha256((completion / "summary.json").read_bytes()).hexdigest() == (
        identities["completion"]["summary_sha256"]
    )
    assert hashlib.sha256(
        (completion / "cost_factor_decomposition.csv").read_bytes()
    ).hexdigest() == identities["completion"][
        "cost_factor_decomposition_sha256"
    ]
    assert hashlib.sha256(
        (completion / "s4_cost_definition_audit.json").read_bytes()
    ).hexdigest() == identities["completion"]["s4_beta_1_2_audit_sha256"]
