from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from review_response import run_pf_first_study_completion_analysis as analysis


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (
    PROJECT_ROOT
    / "review_response/pf_first_study_completion_analysis_protocol.json"
)
ARTIFACT = (
    PROJECT_ROOT
    / "artifacts/pf_first_study_completion_analysis_20260926_940ee7f"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_protocol_freezes_saved_data_only_scope_and_sources() -> None:
    protocol = _load(PROTOCOL)
    assert protocol["base_commit"] == (
        "940ee7f58bc1b3db54049f7decb69b48e7dfbd7e"
    )
    assert protocol["scope"]["condition_count"] == 6
    assert protocol["scope"]["formula_count"] == 2
    assert protocol["scope"]["new_direct_truth_coordinate_count"] == 0
    assert protocol["scope"]["new_hamiltonian_count"] == 0
    assert protocol["scope"]["new_state_generation_count"] == 0
    assert protocol["scope"]["new_fit_count"] == 0
    assert protocol["scope"]["selector_changes"] == 0
    assert protocol["fixed_values"]["practical_cost_beta"] == 1.2
    assert protocol["fixed_values"]["s4_saved_scoring_beta"] == 0.105
    assert protocol["sources"]["s0"]["scoring_sha256"] == (
        "7d4ed0244076eb13259b926730b056a0f9460e63154dd7377b58dad34a95ae78"
    )
    assert protocol["sources"]["s4"]["strategy_scoring_sha256"] == (
        "25323aeb13d0b2b5361a574dace8aba35a0c76eed4ee5924d7d774c44bb79314"
    )


def test_cost_bias_identity_and_cap_bounds_are_reproduced() -> None:
    calibration = _rows(ARTIFACT / "calibration_precision.csv")
    assert len(calibration) == 6
    for row in calibration:
        assert float(row["factor_model_from_costs"]) == pytest.approx(
            float(row["factor_model_from_bias_identity"]), rel=1e-12, abs=1e-13
        )
        assert float(row["identity_absolute_error"]) <= 1e-12

    boundary = _load(ARTIFACT / "boundary_bounds.json")
    assert boundary["new_direct_truth_coordinate_count"] == 0
    assert len(boundary["rows"]) == 2
    by_condition = {row["condition"]: row for row in boundary["rows"]}
    assert by_condition["HF_full_eq_sto3g"]["factor_within_upper"] == pytest.approx(
        1.012708972041748
    )
    assert by_condition["HF_full_eq_sto3g"]["factor_domain_lower"] == pytest.approx(
        2.1146592190772195
    )
    assert by_condition["HF_full_stretch150_sto3g"][
        "factor_within_upper"
    ] == pytest.approx(1.0032361603760322)
    assert by_condition["HF_full_stretch150_sto3g"][
        "factor_domain_lower"
    ] == pytest.approx(2.069663523283636)


def test_decision_trace_records_all_formulae_and_hf_cap() -> None:
    rows = _rows(ARTIFACT / "decision_trace.csv")
    assert len(rows) == 12
    assert {row["formula"] for row in rows} == {"current_m3", "yoshida4"}
    assert sum(row["selected_formula"] == "True" for row in rows) == 6
    hf = [row for row in rows if row["condition"].startswith("HF_")]
    assert len(hf) == 4
    assert all(row["fallback_triggered"] == "True" for row in hf)
    assert all(row["fallback_reasons"] == "cancellation" for row in hf)
    assert all(float(row["allowed_relative_time_max"]) == 0.5 for row in hf)
    assert all(row["at_optimization_boundary"] == "True" for row in hf)


def test_factor_split_is_closed_and_coverage_is_explicit() -> None:
    rows = _rows(ARTIFACT / "cost_factor_decomposition.csv")
    assert len(rows) == 6
    assert {row["coverage_status"] for row in rows} == {
        "exact_saved_grid_only",
        "analytic_bound_at_cap",
    }
    assert sum(row["coverage_status"] == "exact_saved_grid_only" for row in rows) == 4
    assert sum(row["coverage_status"] == "analytic_bound_at_cap" for row in rows) == 2
    for row in rows:
        assert float(row["expanded_factor_closure_error"]) <= 1e-12
        assert float(row["factor_pf"]) == pytest.approx(1.0)
    by_condition = {row["condition"]: row for row in rows}
    assert float(by_condition["N2_active_stretch150_sto3g"]["saved_factor_time"]) > 1.2
    assert float(by_condition["HF_full_eq_sto3g"]["factor_model"]) < 1.0


def test_s4_definition_mismatch_is_confirmed_but_outcome_is_robust() -> None:
    audit = _load(ARTIFACT / "s4_cost_definition_audit.json")
    rows = _rows(ARTIFACT / "s4_cost_definition_audit.csv")
    assert len(rows) == 42
    assert audit["status"] == "definition_mismatch_confirmed_outcome_robust"
    assert audit["practical_cost_beta"] == 1.2
    assert audit["s4_saved_scoring_beta"] == 0.105
    assert audit["stored_safe_row_count"] == 42
    assert audit["consistent_safe_row_count"] == 42
    assert audit["success_changed_row_count"] == 0
    assert audit["minimum_consistent_energy_margin_hartree"] == pytest.approx(
        6.423920546350928e-07
    )
    assert audit["minimum_safety_remains_passed"] is True
    assert audit["targeted_equals_baseline_regret"] is True
    assert audit["saved_decision_outcome"] == "no_benefit"
    assert audit["consistent_outcome"] == "no_benefit"
    assert all(row["consistent_success"] == "True" for row in rows)
    assert all(row["success_changed"] == "False" for row in rows)


def test_committed_artifact_is_complete_and_hash_closed() -> None:
    assert (ARTIFACT / "COMPLETE").is_file()
    audit = _load(ARTIFACT / "audit.json")
    summary = _load(ARTIFACT / "summary.json")
    manifest = _load(ARTIFACT / "manifest.json")
    assert audit["all_gates_passed"] is True
    assert all(audit["checks"].values())
    assert summary["status"] == "complete_first_study_completion_analysis"
    assert summary["condition_count"] == 6
    assert summary["decision_trace_row_count"] == 12
    assert summary["s4_definition_audit_row_count"] == 42
    assert summary["new_direct_truth_coordinate_count"] == 0
    assert summary["s0_gamma_1_01_safe_count"] == 6
    assert summary["pf_selection_loss_count"] == 0
    assert summary["research_decision"]["proceed_to_s5"] is False
    for name, expected in manifest["artifact_sha256"].items():
        assert analysis.sha256_file(ARTIFACT / name) == expected


def test_runner_reproduces_analysis_in_a_fresh_directory(tmp_path: Path) -> None:
    output = tmp_path / "completion-analysis"
    summary = analysis.run(PROJECT_ROOT, PROTOCOL, output)
    assert summary["condition_count"] == 6
    assert summary["s4_definition_audit"]["consistent_safe_row_count"] == 42
    assert summary["s4_definition_audit"]["consistent_outcome"] == "no_benefit"
    assert (output / "COMPLETE").is_file()
    assert _load(output / "boundary_bounds.json") == _load(
        ARTIFACT / "boundary_bounds.json"
    )


def test_paper_claim_ledger_and_status_route_to_corrected_analysis() -> None:
    ledger = (
        PROJECT_ROOT / "PF_first_study_paper_claim_ledger_20260926.md"
    ).read_text(encoding="utf-8")
    status = (PROJECT_ROOT / "docs/current_research_status.md").read_text(
        encoding="utf-8"
    )
    assert "paper_claims_frozen_from_existing_evidence" in ledger
    assert "S4原報告の絶対phase-errorとenergy-margin値は引用せず" in ledger
    assert "F_domain >= 2.11466" in ledger
    assert "F_domain >= 2.06966" in ledger
    assert "S5、新分子、新PF、別基底、別精度、新diagnosticへは進まない" in ledger
    assert (
        "PF_first_study_paper_claim_ledger_20260926.md"
        in status
    )
    assert "S4 beta監査" in status
    assert "42/42で安全性を維持" in status
