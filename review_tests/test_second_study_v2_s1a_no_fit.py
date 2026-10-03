from __future__ import annotations

from pathlib import Path

import pytest

import second_study_v2_s1a_no_fit as s1a


def _arm(gamma: float) -> dict:
    return {
        "gamma": gamma,
        "eligible_candidates": ["c1", "c2"],
        "selected_candidate": "c2",
        "fallback": False,
        "frozen_continuous_budget": 10.0,
    }


def test_exact_gamma_frontier_accepts_only_four_fixed_arms() -> None:
    result = s1a.exact_gamma_frontier([_arm(g) for g in s1a.EXPECTED_GAMMAS])
    assert result["available"] is True
    assert result["gamma_values"] == [1.01, 1.02, 1.05, 1.1]


def test_exact_gamma_frontier_rejects_missing_or_derived_frontier() -> None:
    result = s1a.exact_gamma_frontier([])
    assert result["available"] is False
    assert "gamma_arm_count_not_four" in result["failures"]
    assert "gamma_values_not_exact_frontier" in result["failures"]


def test_classification_d_requires_frozen_contract_failure() -> None:
    decision = s1a.classify_contract_failure({"contract_replayable": False})
    assert decision["classification_code"] == "D"
    assert decision["truth_required_for_classification"] is False
    with pytest.raises(s1a.S1AError):
        s1a.classify_contract_failure({"contract_replayable": True})


def test_predictor_has_no_truth_cli_or_truth_source_path() -> None:
    source = (Path(__file__).parents[1] / "review_response" / "run_second_study_v2_s1a_predictor.py").read_text()
    assert "--truth" not in source
    assert "truth-source" not in source
    assert '"truth_open_count": 0' in source


def test_scorer_contract_failure_path_has_no_truth_cli() -> None:
    source = (Path(__file__).parents[1] / "review_response" / "run_second_study_v2_s1a_scorer.py").read_text()
    assert "--truth" not in source
    assert "truth-source" not in source
    assert "classify_contract_failure" in source
