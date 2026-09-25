import json
import math
from pathlib import Path

from review_response import run_m01_resource_metric_sensitivity as m01


def test_protocol_declares_fifteen_frozen_rows_and_no_new_truth_points():
    config = m01.protocol()
    scope = config["scope"]
    expected = (
        len(scope["primary_conditions"])
        * len(scope["primary_targets"])
        * len(scope["formulae"])
        + len(scope["diagnostic_conditions"])
        * len(scope["diagnostic_targets"])
        * len(scope["formulae"])
    )
    assert expected == 15
    assert scope["new_direct_pf_eigenvalue_point_count"] == 0
    assert config["time_and_qpe_rule"]["time_is_not_reoptimized_per_resource_metric"]


def test_frozen_source_hashes_match_committed_inputs():
    audit = m01.validate_sources(m01.protocol())
    assert audit["status"] == "passed"
    assert audit["checks"]
    assert all(row["passed"] for row in audit["checks"])


def test_clifford_angle_classification_uses_pi_over_two_grid():
    tolerance = 1e-10
    assert m01.is_clifford_angle(0.0, tolerance)
    assert m01.is_clifford_angle(math.pi / 2, tolerance)
    assert m01.is_clifford_angle(-3 * math.pi / 2, tolerance)
    assert not m01.is_clifford_angle(math.pi / 4, tolerance)


def test_hand_s2_resource_counts_keep_rotation_and_layers_distinct():
    term_counts = [2, 1]
    z_terms = [
        {frozenset({0}): 1.0, frozenset({1}): 2.0},
        {frozenset({0, 1}): 3.0},
    ]
    result = m01.circuit_counts(
        term_counts,
        z_terms,
        [1.0],
        0.1,
        1e-14,
        1e-10,
    )
    assert result["merged_group_exponential_count"] == 3
    assert result["pauli_rotations_per_pf_unitary"] == 5
    assert result["compiled_rz_candidates_per_pf_unitary"] == 5
    assert result["nonclifford_rz_per_pf_unitary"] == 5
    assert result["rz_layer_depth_per_pf_unitary"] == 3
    assert result["nonclifford_rz_layer_depth_per_pf_unitary"] == 3


def test_zero_and_clifford_rotations_are_removed_from_t_resources():
    result = m01.circuit_counts(
        [2],
        [{frozenset({0}): 0.0, frozenset({1}): 1.0}],
        [1.0],
        math.pi / 4,
        1e-14,
        1e-10,
    )
    # A one-group S2 block is one full-weight step.  The zero term is removed
    # and angle 2*(pi/4)*1 = pi/2 is Clifford.
    assert result["zero_angle_rz_per_pf_unitary"] == 1
    assert result["clifford_rz_per_pf_unitary"] == 1
    assert result["nonclifford_rz_per_pf_unitary"] == 0
    assert result["nonclifford_rz_layer_depth_per_pf_unitary"] == 0


def test_ranker_detects_pairwise_metric_inversion():
    rows = []
    values = {
        "current_m3": (1.0, 3.0, 1.0, 3.0),
        "yoshida4": (2.0, 1.0, 2.0, 1.0),
        "yoshida6_m3": (3.0, 2.0, 3.0, 2.0),
    }
    for formula, metrics in values.items():
        rows.append(
            {
                "condition": "synthetic",
                "target_name": "CA",
                "formula": formula,
                **dict(zip(m01.METRICS, metrics)),
            }
        )
    rankings, summaries, inversions = m01.rank_resources(rows, 1e-9)
    assert len(rankings) == 12
    assert summaries[0]["best_pf_changes_across_metrics"] is True
    assert summaries[0]["pairwise_inversion_count"] > 0
    assert any(row["pairwise_order_inversion"] for row in inversions)
