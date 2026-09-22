from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import analyze_three_vs_five_point_holdout as analysis


ARTIFACT = Path("artifacts/three_vs_five_point_holdout_reanalysis_20260922")


def test_source_summary_is_frozen() -> None:
    observed = hashlib.sha256(analysis.SOURCE_RELATIVE.read_bytes()).hexdigest()
    assert observed == analysis.SOURCE_SHA256


def test_reanalysis_decision_and_counts() -> None:
    summary = json.loads((ARTIFACT / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "complete"
    assert summary["paired_comparison_count"] == 16
    assert summary["pass_decisions_agree"] is True
    assert summary["base_budget_decisions_agree"] is True
    assert summary["one_percent_budget_decisions_agree"] is True
    assert summary["three_point_active_space_reduced_calibration_candidate"] is True
    assert summary["three_point_all_condition_pass_formulae"] == [
        "current_m3",
        "two_term_center",
        "yoshida4",
    ]
    assert summary["five_point_all_condition_pass_formulae"] == [
        "current_m3",
        "two_term_center",
        "yoshida4",
    ]

    with (ARTIFACT / "paired_results.csv").open(encoding="utf-8", newline="") as stream:
        paired = list(csv.DictReader(stream))
    assert len(paired) == 16
    assert all(row["pass_agrees"] == "True" for row in paired)


def test_reanalysis_manifest_hashes() -> None:
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"]["sha256"] == analysis.SOURCE_SHA256
    for relative, expected in manifest["artifact_sha256"].items():
        path = Path(relative)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
