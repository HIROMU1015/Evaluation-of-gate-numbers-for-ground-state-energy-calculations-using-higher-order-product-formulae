from __future__ import annotations

from pathlib import Path

from review_response import run_pf_first_study_s0_exact_time_scoring_v1_1 as s0


PRACTICAL = Path("artifacts/server_practical_calibration_minimal_20260923_79035cc")
H01 = Path("artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8")
P03 = Path("artifacts/server_unused_molecule_frozen_holdout_20260921_d288797")


def test_anchor_amendment_hash_and_parent_identities_are_frozen() -> None:
    amendment = s0._load_and_verify_amendment(Path("."))
    assert (
        amendment["parent_first_study_protocol_sha256"]
        == s0._base.EXPECTED_FIRST_STUDY_PROTOCOL_SHA256
    )
    assert (
        amendment["frozen_practical_predictions_sha256"]
        == s0._base.EXPECTED_PREDICTIONS_SHA256
    )


def test_co_equilibrium_anchor_is_h01_native_not_p03_nearest() -> None:
    points, _ = s0._base._source_truth_points(
        H01, P03, "CO_active_eq_sto3g", "current_m3"
    )
    first_inserted = 0.99 * 0.6127481451622522
    gates = {"direct_eigenpair_residual_2_norm": 1e-10}
    old_anchor = s0._ORIGINAL_NEAREST_LOWER_ANCHOR(
        points, first_inserted, gates
    )
    new_anchor = s0.nearest_lower_h01_native_anchor(
        points, first_inserted, gates
    )
    assert old_anchor["time"] == 0.5894372011255475
    assert old_anchor.get("truth_provenance") is None
    assert old_anchor["truth_sources"] == ["p03_raw"]
    assert new_anchor["time"] == 0.5886807290771116
    assert s0._is_h01_native_truth(new_anchor)


def test_preflight_selects_six_h01_native_anchors_without_changing_predictions() -> None:
    selections = s0._preflight_anchor_selections(
        Path("."), PRACTICAL, H01, P03, None
    )
    assert len(selections) == 6
    assert all(row["formula"] == "current_m3" for row in selections.values())
    assert all(
        row["truth_provenance"] == s0.REQUIRED_TRUTH_PROVENANCE
        and "h01_saved_truth" in row["truth_sources"]
        for row in selections.values()
    )


def test_v1_1_cache_key_cannot_reuse_failed_v1_0_cache() -> None:
    system = {"hamiltonian_sha256": "abc"}
    old = s0._ORIGINAL_POINT_CACHE_KEY(
        "CO_active_eq_sto3g", "current_m3", 0.6, "gpu", system
    )
    new = s0._point_cache_key_v1_1(
        "CO_active_eq_sto3g", "current_m3", 0.6, "gpu", system
    )
    assert "s0_anchor_protocol_sha256" not in old
    assert (
        new["s0_anchor_protocol_sha256"]
        == s0.EXPECTED_ANCHOR_PROTOCOL_SHA256
    )
    assert new != old
