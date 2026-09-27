import json
from pathlib import Path

import analyze_hchain_direct_optimal_time_scaling_partial_v1_2 as partial
import run_hchain_direct_optimal_time_scaling as parent


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_partial_amendment_identity_and_scope():
    path = (
        PROJECT_ROOT
        / "review_response/hchain_direct_optimal_time_scaling_partial_stop_amendment_v1_2.json"
    )
    assert parent._sha256(path) == partial.EXPECTED_PARTIAL_AMENDMENT_SHA256
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["primary_scaling_systems"] == ["H2", "H4", "H6"]
    assert payload["descriptive_only_systems"] == ["H5"]
    assert payload["not_executed_systems"] == ["H7"]
    assert payload["expected_completed_direct_point_count"] == 248
    assert payload["expected_H7_completed_direct_point_count"] == 0
    assert payload["analysis_rules"]["full_protocol_COMPLETE_forbidden"] is True


def test_runtime_direct_point_count_ignores_short_time_fit_points():
    payload = {
        "results": {
            "H7": {
                "results": {
                    "formula": {
                        "points": [],
                        "short_time_fit": {"points": [{"time": 0.1}]},
                    }
                }
            }
        }
    }
    assert partial._runtime_direct_point_count(payload, "H7") == 0


def test_runtime_direct_point_count_counts_only_direct_points():
    payload = {
        "results": {
            "H7": {
                "results": {
                    "m5": {"points": [{}, {}]},
                    "y8": {"points": [{}]},
                }
            }
        }
    }
    assert partial._runtime_direct_point_count(payload, "H7") == 3
