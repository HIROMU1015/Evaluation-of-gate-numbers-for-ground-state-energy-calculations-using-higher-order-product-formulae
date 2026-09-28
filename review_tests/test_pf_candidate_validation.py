from __future__ import annotations

import math
from pathlib import Path

import pf_candidate_validation as validation
import run_pf_candidate_validation_r1 as r1_runner


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_positive_two_term_zero() -> None:
    model = {
        "coefficient_powers": [4, 6],
        "coefficient_values": [-4.0, 1.0],
    }
    assert validation.positive_two_term_zero(model) == 2.0
    assert validation.positive_two_term_zero(
        {"coefficient_powers": [4, 6], "coefficient_values": [4.0, 1.0]}
    ) is None
    assert validation.positive_two_term_zero(
        {"coefficient_powers": [2, 4], "coefficient_values": [-4.0, 1.0]}
    ) is None


def test_frozen_failure_ledger_and_coordinate_plan() -> None:
    result = validation.build_failure_ledger(PROJECT_ROOT)
    assert len(result["ledger"]) == 16
    assert len(result["coordinate_plan"]) == 10
    assert result["checks"]["selected_coordinate_counts_by_condition"] == {
        "LiF_active_eq_sto3g": 2,
        "LiF_active_stretch150_sto3g": 2,
        "HCl_full_eq_sto3g": 3,
        "HCl_full_stretch150_sto3g": 3,
    }
    assert result["checks"]["saved_selected_coordinate_proxy_count"] == 5
    assert result["checks"]["missing_selected_coordinate_proxy_count"] == 5
    assert result["checks"]["maximum_budget_identity_relative_error"] < 5e-15
    assert (
        result["checks"]["maximum_margin_identity_absolute_residual_hartree"]
        < 5e-18
    )


def test_guarded_error_is_the_budget_error_for_mwr() -> None:
    rows = validation.build_failure_ledger(PROJECT_ROOT)["ledger"]
    row = next(
        item
        for item in rows
        if item["condition"] == "HCl_full_eq_sto3g"
        and item["strategy"] == "multiple_window_rule"
    )
    assert math.isclose(row["absolute_central_prediction_hartree"], 1.8864010878277525e-7)
    assert math.isclose(row["budget_error_used_hartree"], 6.4363245484305005e-6)
    assert row["guard_premium_over_central_hartree"] > 0.0


def test_unsafe_negative_frozen_budget_regret_is_not_safety() -> None:
    rows = validation.build_failure_ledger(PROJECT_ROOT)["ledger"]
    row = next(
        item
        for item in rows
        if item["condition"] == "LiF_active_eq_sto3g"
        and item["strategy"] == "current_fallback"
    )
    assert row["unsafe_execution"] is True
    assert row["frozen_budget_regret"] < 0.0
    assert row["required_cost_over_frozen_budget"] > 1.8
    assert row["evidence_class"] == "post_hoc_truth_diagnostic"


def test_lif_equilibrium_zero_is_near_selected_time() -> None:
    rows = validation.build_failure_ledger(PROJECT_ROOT)["ledger"]
    row = next(
        item
        for item in rows
        if item["condition"] == "LiF_active_eq_sto3g"
        and item["strategy"] == "current_fallback"
    )
    assert math.isclose(
        row["original_model_positive_zero_hartree_inverse"],
        0.9329842669044777,
        rel_tol=0.0,
        abs_tol=2e-15,
    )
    assert row["distance_to_original_model_zero"] < 5e-6


def test_proxy_sign_convention() -> None:
    time_value = 0.2
    positive_shift = 1.0e-3
    negative_shift = -2.0e-3
    assert math.isclose(
        validation.proxy_signed_from_echo(
            math.sin(positive_shift * time_value), time_value
        ),
        math.sin(positive_shift * time_value) / time_value,
    )
    assert validation.proxy_signed_from_echo(
        math.sin(positive_shift * time_value), time_value
    ) > 0.0
    assert validation.proxy_signed_from_echo(
        math.sin(negative_shift * time_value), time_value
    ) < 0.0
    assert validation.proxy_signed_from_echo(0.0, time_value) == 0.0


def test_component_classification_is_fixed_and_cancellation_aware() -> None:
    single = validation.classify_components(
        {"model": 4.0, "state": 1.0, "proxy": 0.5}, 1.5
    )
    assert single["attribution"] == "model"
    assert single["material_by_original_budget_allowance"] == {
        "model": True,
        "state": False,
        "proxy": False,
    }
    mixed = validation.classify_components(
        {"model": 4.0, "state": -3.0, "proxy": 0.1}, 1.0
    )
    assert mixed["attribution"] == "mixed_or_none"
    assert mixed["largest_absolute_component"] == "model"


def test_environment_bridge_amendment_is_frozen_and_uses_saved_points() -> None:
    path = (
        PROJECT_ROOT
        / "review_response/pf_candidate_validation_r1_environment_amendment_v1_1.json"
    )
    amendment = validation.read_json(path)
    assert validation.sha256_file(path) == (
        "bd0f9c1d32db6fda391b912a769688e6f53d4b39ecdb2e8ce8ab196f1baf03fd"
    )
    assert amendment["parent_r1_protocol_sha256"] == (
        "186d2240bbf78733c1389fac66e2b261a7dfe50d8712b656ce0e1c45a6c67e49"
    )
    points = amendment["bridge"]["points"]
    assert len(points) == 11
    assert len({(row["condition"], row["time_hex"]) for row in points}) == 11
    saved = validation.read_csv(
        PROJECT_ROOT / validation.PHASE_A_RELATIVE / "proxy_points.csv"
    )
    keys = {
        (row["condition"], float(row["time_hartree_inverse"]).hex())
        for row in saved
    }
    assert all((row["condition"], row["time_hex"]) in keys for row in points)


def test_phase_a_cache_amendment_is_frozen_and_keeps_r2_closed() -> None:
    path = (
        PROJECT_ROOT
        / "review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json"
    )
    amendment, digest = r1_runner.load_phase_a_cache_amendment(
        path,
        "186d2240bbf78733c1389fac66e2b261a7dfe50d8712b656ce0e1c45a6c67e49",
    )
    assert digest == "a95a9abf87f1d428c35d34ed13cbea8c2ff930e91a3e5eb3a2550fd5d1dd1051"
    assert amendment["system_source_rule"]["local_hamiltonian_reconstruction_count"] == 0
    assert amendment["calculation_accounting"]["phase_a_system_cache_reuse_count"] == 4
    assert amendment["calculation_accounting"]["new_direct_truth_coordinate_count"] == 0
    assert amendment["interpretation_limit"]["r2_authorized"] is False
    assert len(amendment["phase_a_runtime"]["system_cache_sha256"]) == 4


def test_phase_a_cache_loader_requires_frozen_hashes(tmp_path, monkeypatch) -> None:
    condition = "LiF_active_eq_sto3g"
    metadata_path = tmp_path / ".runtime/system_cache/condition.metadata.json"
    metadata_path.parent.mkdir(parents=True)
    validation.write_json(
        metadata_path,
        {
            "cisd_hamiltonian_residual_2_norm": 0.0,
            "population_sector_dimension": 1,
            "restricted_dimension": 1,
        },
    )
    cache_sha = "1" * 64
    validation.write_json(
        tmp_path / "sanitized_input_manifest.json",
        {
            "entries": [
                {
                    "condition": condition,
                    "metadata": metadata_path.relative_to(tmp_path).as_posix(),
                    "metadata_sha256": validation.sha256_file(metadata_path),
                    "runtime_system_cache_sha256": cache_sha,
                }
            ]
        },
    )
    monkeypatch.setattr(
        r1_runner.phase_b,
        "verify_phase_a_runtime_inventory",
        lambda root: {"inventory_sha256": "2" * 64, "file_count": 56},
    )
    monkeypatch.setattr(
        r1_runner.phase_b,
        "load_phase_a_systems",
        lambda root, protocol, protocol_sha256: {
            condition: {"hamiltonian_sha256": "3" * 64}
        },
    )
    systems, metadata, identity = r1_runner.load_phase_a_cache_systems(
        phase_a_root=tmp_path,
        source_protocol={},
        source_protocol_sha256="4" * 64,
        prediction_by_condition={condition: {"hamiltonian_sha256": "3" * 64}},
        amendment={
            "phase_a_runtime": {
                "absolute_artifact_root": str(tmp_path.resolve()),
                "runtime_inventory_sha256": "2" * 64,
                "system_cache_sha256": {condition: cache_sha},
            }
        },
    )
    assert set(systems) == {condition}
    assert metadata[condition]["system_source"] == "original_phase_a_runtime_cache"
    assert metadata[condition]["rebuilt_hamiltonian_byte_identity_match"] is True
    assert identity["file_count"] == 56


def test_local_environment_failure_audit_manifest() -> None:
    root = (
        PROJECT_ROOT
        / "artifacts/pf_candidate_validation_r1_local_environment_gate_20260928_5c36399"
    )
    decision = validation.read_json(root / "decision.json")
    assert decision["status"] == "failed_environment_reconstruction_bridge"
    assert decision["failed_point_count"] == 4
    assert decision["exact_ground_state_count"] == 0
    assert decision["new_direct_truth_coordinate_count"] == 0
    assert decision["threshold_relaxed"] is False
    assert decision["r2_authorized"] is False
    manifest = validation.read_json(root / "manifest.json")
    for row in manifest["entries"]:
        path = root / row["path"]
        assert path.stat().st_size == row["byte_count"]
        assert validation.sha256_file(path) == row["sha256"]
