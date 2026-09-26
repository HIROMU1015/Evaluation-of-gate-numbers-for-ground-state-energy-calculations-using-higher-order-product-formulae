from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from PIL import Image

from review_response import run_pf_first_study_paper_figures as figures


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = PROJECT_ROOT / "review_response/pf_first_study_paper_figures_protocol.json"
FIGURE_ROOT = PROJECT_ROOT / "paper/figures"
TABLE_ROOT = PROJECT_ROOT / "paper/tables"
MANIFEST = FIGURE_ROOT / "paper_figure_manifest.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_protocol_freezes_evidence_only_scope_and_figure_order() -> None:
    protocol = _load(PROTOCOL)
    assert protocol["base_commit"] == "cd81018932b9557b7a55e2e1cd8c5e3988245409"
    assert protocol["source"]["numbers_sha256"] == (
        "8bf1333d6c824a3bc033f81997aac1f63b91c43c12cb032a2778675bbc20b174"
    )
    assert [record["slug"] for record in protocol["figures"]] == [
        "decision_pipeline",
        "three_error_decomposition",
        "safety_vs_efficiency",
        "within_vs_domain_loss",
    ]
    assert len(protocol["scope"]["conditions"]) == 6
    assert len(protocol["scope"]["strategies"]) == 7
    for field in (
        "new_direct_truth_coordinate_count",
        "new_hamiltonian_count",
        "new_state_generation_count",
        "new_fit_count",
        "selector_changes",
        "manuscript_sections",
    ):
        assert protocol["scope"][field] == 0


def test_table_1_is_the_frozen_six_by_two_decision_trace() -> None:
    rows = _rows(TABLE_ROOT / "table_1_decision_trace.csv")
    assert len(rows) == 12
    assert {row["formula"] for row in rows} == {"current_m3", "yoshida4"}
    assert sum(row["selected_formula"] == "true" for row in rows) == 6
    assert sum(row["evaluation_group"] == "primary" for row in rows) == 8
    hf = [row for row in rows if row["condition"].startswith("HF_")]
    assert len(hf) == 4
    assert all(row["fallback_triggered"] == "true" for row in hf)
    assert all(row["fallback_reasons"] == "cancellation" for row in hf)
    assert all(float(row["allowed_relative_time_max"]) == 0.5 for row in hf)


def test_table_2_keeps_saved_grid_and_hf_bounds_distinct() -> None:
    rows = _rows(TABLE_ROOT / "table_2_resource_factors.csv")
    assert len(rows) == 6
    assert sum(row["coverage_status"] == "exact_saved_grid_only" for row in rows) == 4
    assert sum(row["coverage_status"] == "analytic_bound_at_cap" for row in rows) == 2
    by_condition = {row["condition"]: row for row in rows}
    assert all(float(row["factor_pf_selection"]) == pytest.approx(1.0) for row in rows)
    assert float(by_condition["HF_full_eq_sto3g"]["factor_total"]) == pytest.approx(
        2.1503125962499605
    )
    assert float(
        by_condition["HF_full_stretch150_sto3g"]["factor_total"]
    ) == pytest.approx(2.102856788337413)
    assert float(
        by_condition["HF_full_eq_sto3g"]["factor_domain_lower"]
    ) == pytest.approx(2.1146592190772195)
    assert float(
        by_condition["HF_full_stretch150_sto3g"]["factor_within_upper"]
    ) == pytest.approx(1.0032361603760322)


def test_table_3_uses_corrected_six_by_seven_s4_audit() -> None:
    rows = _rows(TABLE_ROOT / "table_3_s4_strategy_summary.csv")
    assert len(rows) == 7
    assert all(int(row["corrected_safe_count"]) == 6 for row in rows)
    assert all(int(row["condition_count"]) == 6 for row in rows)
    assert all(row["coverage_status"] == "beta_1.2_corrected_audit" for row in rows)
    by_strategy = {row["strategy"]: row for row in rows}
    assert float(by_strategy["practical_baseline"]["mean_original_grid_regret"]) == pytest.approx(
        float(by_strategy["state_targeted_fallback"]["mean_original_grid_regret"])
    )
    assert float(
        by_strategy["practical_baseline"]["minimum_corrected_energy_margin_hartree"]
    ) == pytest.approx(6.423920546350928e-07)


def test_four_figures_have_valid_png_pdf_and_svg_assets() -> None:
    stems = (
        "figure_1_decision_pipeline",
        "figure_2_three_error_decomposition",
        "figure_3_safety_vs_efficiency",
        "figure_4_within_vs_domain_loss",
    )
    for stem in stems:
        png = FIGURE_ROOT / f"{stem}.png"
        pdf = FIGURE_ROOT / f"{stem}.pdf"
        svg = FIGURE_ROOT / f"{stem}.svg"
        with Image.open(png) as image:
            assert image.width >= 1200
            assert image.height >= 650
        assert pdf.read_bytes().startswith(b"%PDF")
        svg_text = svg.read_text(encoding="utf-8")
        assert "<svg" in svg_text
        assert "run_pf_first_study_paper_figures.py" in svg_text


def test_captions_and_manifest_preserve_interpretation_gates() -> None:
    captions = (PROJECT_ROOT / "paper/figure_captions.md").read_text(encoding="utf-8")
    manifest = _load(MANIFEST)
    assert "not a continuous-time global oracle" in captions
    assert "six development conditions times seven" in captions
    assert "superseded by the corrected audit" in captions
    assert manifest["status"] == "complete_paper_figure_package"
    assert manifest["figure_count"] == 4
    assert manifest["figure_asset_count"] == 12
    assert manifest["table_count"] == 3
    assert all(manifest["source_audit"]["checks"].values())
    assert all(manifest["interpretation_gates"].values())
    assert all(value == 0 for value in manifest["new_computation"].values())
    for relative, expected in manifest["outputs"].items():
        assert figures.sha256_file(PROJECT_ROOT / relative) == expected


def test_runner_is_byte_reproducible_in_fresh_directory(tmp_path: Path) -> None:
    manifest = figures.run(PROJECT_ROOT, PROTOCOL, tmp_path)
    committed_manifest = _load(MANIFEST)
    assert manifest == committed_manifest
    for relative in committed_manifest["outputs"]:
        assert (tmp_path / relative).read_bytes() == (PROJECT_ROOT / relative).read_bytes()
    generated_manifest = tmp_path / "paper/figures/paper_figure_manifest.json"
    assert generated_manifest.read_bytes() == MANIFEST.read_bytes()
