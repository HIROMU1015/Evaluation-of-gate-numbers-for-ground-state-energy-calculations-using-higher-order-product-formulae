from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from review_response import run_pf_first_study_regret_decomposition as decomposition


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = PROJECT_ROOT / "review_response/pf_first_study_regret_decomposition_protocol.json"
ARTIFACT = PROJECT_ROOT / "artifacts/pf_first_study_regret_decomposition_20260925_7f0b30d"


def test_factor_identity_and_margin_split() -> None:
    values = decomposition.decompose_costs(
        c_star=100.0,
        c_selected_formula_star=120.0,
        c_required=150.0,
        c_hat=165.0,
        b_frozen=166.65,
        closure_tolerance=1e-12,
    )
    assert values["factor_model"] == pytest.approx(1.1)
    assert values["factor_margin"] == pytest.approx(1.01)
    assert values["factor_calibration"] == pytest.approx(1.111)
    assert values["factor_time_selection"] == pytest.approx(1.25)
    assert values["factor_pf_selection"] == pytest.approx(1.2)
    assert values["factor_total"] == pytest.approx(1.6665)
    assert values["closure_absolute_error"] <= 1e-12


def test_protocol_fixes_existing_truth_only_scope() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["scope"]["condition_count"] == 6
    assert protocol["scope"]["new_direct_truth_coordinate_count"] == 0
    assert protocol["scope"]["coverage_policy"].startswith("report_coverage_insufficient")
    assert protocol["fixed_margin_multiplier"] == 1.01
    assert protocol["source"]["scoring_sha256"] == (
        "7d4ed0244076eb13259b926730b056a0f9460e63154dd7377b58dad34a95ae78"
    )


def test_committed_artifact_is_complete_and_closed() -> None:
    assert (ARTIFACT / "COMPLETE").is_file()
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    summary = json.loads((ARTIFACT / "summary.json").read_text(encoding="utf-8"))
    assert audit["all_gates_passed"] is True
    assert audit["new_direct_truth_coordinate_count"] == 0
    assert audit["max_closure_absolute_error"] <= audit["closure_tolerance"]
    assert summary["condition_count"] == 6
    assert summary["coverage_complete"] is True
    assert summary["gamma_1_01_safe_condition_count"] == 6
    assert summary["pf_selection_loss_condition_count"] == 0
    assert summary["dominance_counts"] == {"calibration": 3, "time_selection": 3}

    with (ARTIFACT / "regret_decomposition.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    assert all(float(row["factor_pf_selection"]) == pytest.approx(1.0) for row in rows)
    assert all(row["coverage_status"] == "complete_existing_truth" for row in rows)
    by_condition = {row["condition"]: row for row in rows}
    assert by_condition["HF_full_eq_sto3g"]["dominant_component"] == "time_selection"
    assert float(by_condition["HF_full_eq_sto3g"]["factor_model"]) < 1.0
    assert float(by_condition["HF_full_eq_sto3g"]["factor_calibration"]) > 1.0


def test_manifest_hashes_all_declared_artifacts() -> None:
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["artifact_sha256"].items():
        assert decomposition.sha256_file(ARTIFACT / name) == expected
