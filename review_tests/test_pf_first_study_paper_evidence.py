from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from review_response import run_pf_first_study_paper_evidence as evidence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = PROJECT_ROOT / "review_response/pf_first_study_paper_evidence_protocol.json"
OUTPUT = PROJECT_ROOT / "paper/evidence"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _lookup() -> dict[str, dict[str, str]]:
    return {row["metric_id"]: row for row in _rows(OUTPUT / "paper_numbers.csv")}


def test_protocol_freezes_existing_evidence_only_scope() -> None:
    protocol = _load(PROTOCOL)
    assert protocol["base_commit"] == (
        "6a1e54d5e830a20b8817791f9f1f65729815fc12"
    )
    assert protocol["scope"]["claim_ids"] == [f"C{number}" for number in range(1, 11)]
    assert len(protocol["scope"]["conditions"]) == 6
    assert len(protocol["scope"]["primary_conditions"]) == 4
    assert len(protocol["scope"]["stress_conditions"]) == 2
    assert protocol["scope"]["new_direct_truth_coordinate_count"] == 0
    assert protocol["scope"]["new_hamiltonian_count"] == 0
    assert protocol["scope"]["new_state_generation_count"] == 0
    assert protocol["scope"]["new_fit_count"] == 0
    assert protocol["scope"]["generate_figures"] is False
    assert protocol["scope"]["write_manuscript"] is False
    assert [entry["title"] for entry in protocol["figure_order"]] == [
        "decision pipeline",
        "three-error decomposition",
        "safety versus efficiency",
        "within-domain versus domain loss",
    ]


def test_all_claims_have_unique_traceable_metrics() -> None:
    rows = _rows(OUTPUT / "paper_numbers.csv")
    assert {row["claim_id"] for row in rows} == {f"C{number}" for number in range(1, 11)}
    assert len({row["metric_id"] for row in rows}) == len(rows)
    for row in rows:
        for field in (
            "scope",
            "evaluation_group",
            "coverage_status",
            "source_path",
            "source_sha256",
            "source_commit",
            "limitation",
        ):
            assert row[field]
        assert evidence.sha256_file(PROJECT_ROOT / row["source_path"]) == row[
            "source_sha256"
        ]


def test_key_claim_numbers_are_exact() -> None:
    rows = _lookup()
    assert int(rows["s1_s2.all.state_dominant_count"]["value"]) == 79
    assert int(rows["s1_s2.all.state_dominant_count"]["denominator"]) == 128
    assert int(rows["s1_s2.all.mixed_count"]["value"]) == 49
    assert int(rows["s1_s2.h4.state_dominant_count"]["value"]) == 49
    assert int(rows["s1_s2.h4.mixed_count"]["value"]) == 7
    assert int(rows["s1_s2.two_level.state_dominant_count"]["value"]) == 30
    assert int(rows["s1_s2.two_level.mixed_count"]["value"]) == 42
    assert int(rows["s0.gamma_1_01.safe_condition_count"]["value"]) == 6
    assert int(rows["s0.gamma_1_01.safe_condition_count"]["denominator"]) == 6
    assert int(rows["resource.pf_selection_loss_condition_count"]["value"]) == 0
    assert float(rows["resource.HF_full_eq_sto3g.factor_total"]["value"]) == pytest.approx(
        2.150312596824562
    )
    assert float(
        rows["resource.HF_full_stretch150_sto3g.factor_total"]["value"]
    ) == pytest.approx(2.102856787762811)
    assert float(rows["domain.HF_full_eq_sto3g.factor_domain_lower"]["value"]) == pytest.approx(
        2.1146592190772195
    )
    assert float(
        rows["domain.HF_full_stretch150_sto3g.factor_domain_lower"]["value"]
    ) == pytest.approx(2.069663523283636)


def test_resource_dominance_and_s4_negative_result_are_scoped() -> None:
    rows = _lookup()
    assert rows["regret.N2_active_eq_sto3g.dominant_component"]["value"] == "calibration"
    assert rows["regret.N2_active_stretch150_sto3g.dominant_component"]["value"] == "time_selection"
    assert rows["regret.CO_active_eq_sto3g.dominant_component"]["value"] == "calibration"
    assert rows["regret.CO_active_stretch150_sto3g.dominant_component"]["value"] == "calibration"
    assert int(rows["regret.primary.calibration_dominant_count"]["value"]) == 3
    assert int(rows["regret.primary.time_selection_dominant_count"]["value"]) == 1
    assert int(rows["s4.state_risk_positive_group_count"]["value"]) == 2
    assert int(rows["s4.state_risk_positive_group_count"]["denominator"]) == 12
    assert rows["s4.fixed_outcome"]["value"] == "no_benefit"
    assert float(rows["s4.practical_baseline.mean_regret"]["value"]) == pytest.approx(
        float(rows["s4.state_targeted_fallback.mean_regret"]["value"])
    )


def test_s4_beta_audit_uses_corrected_absolute_values_and_6x7_scope() -> None:
    rows = _lookup()
    safe = rows["s4_beta_audit.corrected_safe_row_count"]
    assert int(safe["value"]) == 42
    assert int(safe["numerator"]) == 42
    assert int(safe["denominator"]) == 42
    assert "six development conditions times seven frozen strategies" in safe["scope"]
    assert int(rows["s4_beta_audit.success_changed_row_count"]["value"]) == 0
    assert rows["s4_beta_audit.corrected_outcome"]["value"] == "no_benefit"
    assert float(rows["s4_beta_audit.practical_cost_beta"]["value"]) == 1.2
    assert float(rows["s4_beta_audit.stored_scoring_beta"]["value"]) == 0.105
    assert float(rows["s4_beta_audit.minimum_corrected_energy_margin"]["value"]) == pytest.approx(
        6.423920546350928e-07
    )
    metric_ids = set(rows)
    assert not any("stored_phase_error" in metric_id for metric_id in metric_ids)
    assert not any("stored_energy_margin" in metric_id for metric_id in metric_ids)


def test_matrix_and_manifest_record_supersession_and_stop_scope() -> None:
    matrix = (OUTPUT / "paper_evidence_matrix.md").read_text(encoding="utf-8")
    manifest = _load(OUTPUT / "paper_source_manifest.json")
    positions = [
        matrix.index("**Decision pipeline**"),
        matrix.index("**Three-error decomposition**"),
        matrix.index("**Safety versus efficiency**"),
        matrix.index("**Within-domain versus domain loss**"),
    ]
    assert positions == sorted(positions)
    assert "S4原成果物の絶対phase-error/marginは引用せず" in matrix
    assert "6 development conditions x 7 frozen strategies" in matrix
    assert "新規計算、図作成、本文執筆" in matrix
    assert manifest["status"] == "complete_existing_evidence_package"
    assert manifest["source_identity_all_passed"] is True
    assert manifest["evidence"]["claim_count"] == 10
    assert all(value == 0 for value in manifest["new_computation"].values())
    for stage in ("s1_s2", "s0", "s3", "s4", "regret", "completion"):
        record = manifest["sources"][stage]
        assert record["complete_exists"] is True
        for file_record in record["files"].values():
            assert file_record["working_tree_matches"] is True
            assert file_record["source_commit_matches"] is True
    for name, expected in manifest["outputs"].items():
        assert evidence.sha256_file(OUTPUT / name) == expected


def test_runner_reproduces_all_outputs_in_fresh_directory(tmp_path: Path) -> None:
    output = tmp_path / "paper-evidence"
    manifest = evidence.run(PROJECT_ROOT, PROTOCOL, output)
    assert manifest["evidence"]["claim_count"] == 10
    for name in (
        "paper_numbers.csv",
        "paper_evidence_matrix.md",
        "paper_source_manifest.json",
    ):
        assert (output / name).read_bytes() == (OUTPUT / name).read_bytes()
