from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from review_response.audit_d04_equal_classical_budget import (
    choose_best_under_budget,
    compact_d4_incremental_working_bytes,
    dense_bch_incremental_working_bytes,
    direct_incremental_working_bytes,
)


ARTIFACT = Path("artifacts/prevalidation_d04_equal_classical_budget_20260922")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_d04_memory_models_and_budget_selection() -> None:
    assert direct_incremental_working_bytes(4) == 3 * 4 * 4 * 16
    assert compact_d4_incremental_working_bytes(4, 5, 2) == 14 * 4 * 16
    assert dense_bch_incremental_working_bytes(4, 8) == 6 * 10 * 4 * 4 * 16
    rows = [
        {
            "method_id": "slow_better",
            "marginal_seconds_warm_cache": 2.0,
            "higher_order_residual_over_epsilon": 0.001,
            "direct_point_count": 2,
        },
        {
            "method_id": "fast_worse",
            "marginal_seconds_warm_cache": 1.0,
            "higher_order_residual_over_epsilon": 0.01,
            "direct_point_count": 3,
        },
    ]
    assert choose_best_under_budget(rows, 0.5) is None
    assert choose_best_under_budget(rows, 1.0)["method_id"] == "fast_worse"
    assert choose_best_under_budget(rows, 2.0)["method_id"] == "slow_better"


def test_d04_artifact_closes_equal_budget_accounting() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete_with_findings"
    assert audit["passed"] is True
    assert audit["scope"]["catalog_item"] == "D04"
    assert audit["scope"]["new_scientific_direct_points"] == 0
    assert audit["scope"]["remeasured_existing_h05_points"] == 40
    assert all(check["passed"] for check in audit["checks"])
    assert len(audit["resource_rows"]) == 40
    assert len(audit["direct_point_rows"]) == 40
    assert len(audit["dense_bch_rows"]) == 8
    assert len(audit["method_summaries"]) == 6
    assert len(audit["same_point_rows"]) == 2
    assert len(audit["frontier_rows"]) == 24
    assert audit["summary"]["fixed_two_point_residual_pass_count"] == 8
    assert audit["summary"]["dense_bch_residual_pass_count"] == 8
    assert audit["summary"]["maximum_remeasured_shift_difference_hartree"] < 2e-13


def test_d04_manifest_hashes_and_csv_rows_match() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == audit["status"]
    for group in ("source_sha256", "input_sha256", "artifact_sha256"):
        for path_text, expected_hash in manifest[group].items():
            assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "direct_point_timing.csv": "direct_point_rows",
        "method_resources.csv": "resource_rows",
        "dense_bch_timing.csv": "dense_bch_rows",
        "method_summary.csv": "method_summaries",
        "same_point_comparison.csv": "same_point_rows",
        "equal_time_frontier.csv": "frontier_rows",
    }
    for filename, key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[key])
