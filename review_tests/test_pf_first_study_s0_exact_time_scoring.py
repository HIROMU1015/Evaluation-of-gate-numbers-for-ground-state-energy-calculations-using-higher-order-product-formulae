from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from review_response import run_pf_first_study_s0_exact_time_scoring as s0


PRACTICAL = Path("artifacts/server_practical_calibration_minimal_20260923_79035cc")


def test_frozen_practical_predictions_and_protocol_are_exact() -> None:
    protocol, predictions = s0._verify_with_canonical_constant_keys(
        PRACTICAL, Path("PF_first_study_protocol_20260925.json")
    )
    assert s0._base._sha256(PRACTICAL / "predictions.json") == s0.EXPECTED_PREDICTIONS_SHA256
    assert protocol["resource_metrics"]["target_error_hartree"] == protocol["constants"][
        "target_error_hartree"
    ]
    assert predictions["phase_a_commit"] == s0.EXPECTED_PHASE_A_COMMIT
    selections = [row["selection"] for row in predictions["conditions"]]
    assert len(selections) == 6
    assert all(row["status"] == "selected" for row in selections)
    assert all(row["selected_formula"] == "current_m3" for row in selections)


def test_nearest_lower_anchor_uses_reliable_saved_point_only() -> None:
    points = [
        {
            "time": 0.4,
            "eigenpair_residual_2_norm": 1e-13,
            "ground_overlap_probability": 0.99,
        },
        {
            "time": 0.5,
            "eigenpair_residual_2_norm": 1e-8,
            "ground_overlap_probability": 0.99,
        },
        {
            "time": 0.6,
            "eigenpair_residual_2_norm": 1e-13,
            "ground_overlap_probability": 0.99,
        },
    ]
    anchor = s0.nearest_lower_reliable_anchor(
        points, 0.55, {"direct_eigenpair_residual_2_norm": 1e-10}
    )
    assert anchor["time"] == 0.4


def test_direct_branch_point_recovers_signed_shift_and_diagnostics() -> None:
    time_value = 0.25
    energy = -1.2
    shift = 2.5e-4
    unitary = np.diag(
        [
            np.exp(1j * (energy + shift) * time_value),
            np.exp(1j * 0.7 * time_value),
        ]
    ).astype(np.complex128)
    exact = np.asarray([1.0, 0.0], dtype=np.complex128)
    point, vector = s0.direct_branch_point(
        unitary,
        exact,
        energy,
        time_value,
        rotations=17,
        epsilon=1e-3,
        previous_vector=exact,
        degeneracy_gap=1e-8,
    )
    assert abs(point["signed_direct_shift_hartree"] - shift) <= 1e-14
    assert point["branch_quality"] == "resolved"
    assert point["previous_branch_overlap_probability"] == 1.0
    assert point["ground_state_overlap_probability"] == 1.0
    assert point["eigenpair_residual_2_norm"] <= 1e-14
    assert point["unitarity_residual_frobenius"] <= 1e-14
    assert abs(abs(np.vdot(exact, vector)) - 1.0) <= 1e-14


def test_manifested_practical_scoring_is_not_rewritten_by_s0() -> None:
    before = s0._base._sha256(PRACTICAL / "predictions.json")
    marker = json.loads((PRACTICAL / "SELECTION_FROZEN").read_text(encoding="utf-8"))
    assert marker["prediction_sha256"] == before
    assert before == s0.EXPECTED_PREDICTIONS_SHA256

