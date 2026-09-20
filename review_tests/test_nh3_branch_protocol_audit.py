"""CPU-only regression tests for the NH3 branch/protocol audit."""
from __future__ import annotations

import numpy as np

import audit_nh3_branch_protocol as audit


def test_four_cell_ablation_reuses_saved_points():
    source = audit.load_json(audit.SOURCE_SUMMARY)
    result = audit.ablation(source)
    rows = result["grid_floor_cells"]
    assert len(rows) == 4 * 6 * 4
    assert result["qualified_counts_of_24"]["shared_molecular__5e-13"] == 17
    assert result["qualified_counts_of_24"][
        "legacy_molecular_sensitivity__5e-12"
    ] == 24
    assert all(len(row["selected_times"]) in (0, 5) for row in rows)
    assert all(
        row["fixed_order_alpha"] is not None
        for row in rows if row["qualified"]
    )



def test_interval_audit_reuses_all_four_hamiltonians():
    source = audit.load_json(audit.SOURCE_SUMMARY)
    result = audit.interval_audit(source)
    assert len(result["interval_rows"]) == 4 * 6 * 3
    assert all(row["classification"] for row in result["interval_rows"])
    assert len(result["scale_metrics"]) == 6 * 4


def test_interval_classification_is_local():
    base = {"effective_order": 4.05, "roundoff_risk": False,
            "sign_reversal": False}
    assert audit.classify_interval(base, 4) == "within_formal_order_tolerance"
    assert audit.classify_interval(
        {**base, "roundoff_risk": True}, 4
    ) == "numerical_floor_or_unreliable"
    assert audit.classify_interval(
        {**base, "sign_reversal": True}, 4
    ) == "sign_reversal_or_cancellation"
    assert audit.classify_interval(
        {**base, "effective_order": 3.3}, 4
    ) == "reliable_but_outside_formal_order_tolerance"


def test_plateau_needs_two_contiguous_good_intervals():
    rows = [
        {"left_time": 0.01, "right_time": 0.02,
         "classification": "within_formal_order_tolerance"},
        {"left_time": 0.02, "right_time": 0.04,
         "classification": "within_formal_order_tolerance"},
        {"left_time": 0.04, "right_time": 0.08,
         "classification": "numerical_floor_or_unreliable"},
    ]
    scales = {name: 2.0 for name in audit.SCALE_NAMES}
    found = audit.plateau_ranges(rows, scales)
    assert len(found) == 1
    assert found[0]["t_start"] == 0.01
    assert found[0]["t_stop"] == 0.04
    assert found[0]["tau_ranges"][audit.SCALE_NAMES[0]] == {
        "start": 0.02, "stop": 0.08,
    }


def test_labels_and_path_optimizers():
    t, ratio = audit.time_from_label("r101", 0.2)
    assert np.isclose(t, 0.202)
    assert ratio == 1.01
    assert audit.time_from_label("a030", 0.2) == (0.03, None)
    matrices = [
        np.asarray([[0.9, 0.1], [0.1, 0.9]]),
        np.asarray([[0.9, 0.1], [0.1, 0.9]]),
    ]
    assert audit.greedy_path(matrices) == [0, 0, 0]
    assert audit.global_path(matrices) == [0, 0, 0]


def test_schur_candidates_have_small_residual():
    unitary = np.diag(
        np.exp(1j * np.asarray([0.01, 0.08, 0.2, 0.4, 0.7, 1.0]))
    )
    state = np.zeros(6, dtype=np.complex128)
    state[2] = 1.0
    candidates, vectors, seconds = audit.eigenpair_records(
        unitary, state, 0.0, 0.1
    )
    assert len(candidates) == audit.TOP_K
    assert vectors.shape == (6, audit.TOP_K)
    assert np.isclose(candidates[0]["ground_overlap_probability"], 1.0)
    assert candidates[0]["eigenpair_residual_2_norm"] < 1e-12
    assert seconds >= 0.0
