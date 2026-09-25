import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "pf_first_study_s3_hf_connection_20260925"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_s3_completion_and_zero_new_science_computation():
    manifest = json.loads((ARTIFACT / "source_manifest.json").read_text())
    decision = json.loads((ARTIFACT / "decision.json").read_text())

    assert (ARTIFACT / "COMPLETE").is_file()
    assert manifest["status"] == "complete_retrospective_synthesis"
    assert decision["status"] == "complete_retrospective_synthesis"
    assert manifest["new_hamiltonian_count"] == 0
    assert manifest["new_direct_truth_point_count"] == 0
    assert manifest["new_fit_count"] == 0
    assert manifest["post_hoc_threshold_change_count"] == 0
    assert decision["not_independent_validation"] is True
    assert decision["s4_started"] is False


def test_s3_local_source_hashes_and_external_identities_are_fixed():
    manifest = json.loads((ARTIFACT / "source_manifest.json").read_text())
    sources = {item["id"]: item for item in manifest["sources"]}

    local_ids = {
        "first_study_integrated",
        "phase_b_dominance",
        "s0_exact_time_scoring_v1_1",
    }
    for source_id in local_ids:
        item = sources[source_id]
        assert _sha256(ROOT / item["path"]) == item["sha256"]

    assert sources["h01_report"]["commit"] == (
        "568f00249abb5b89ae3e6bb39cb4af87ed8581bd"
    )
    assert sources["hf_bridge_report"]["commit"] == (
        "6eb1aa02f1d28904741b2cee4f70347e1203198f"
    )
    assert len({item["id"] for item in manifest["sources"]}) == len(
        manifest["sources"]
    )


def test_s3_evidence_matrix_and_exit_gate():
    with (ARTIFACT / "evidence_matrix.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    decision = json.loads((ARTIFACT / "decision.json").read_text())

    assert [row["evidence_id"] for row in rows] == [
        "S3-E01",
        "S3-E02",
        "S3-E03",
        "S3-E04",
        "S3-E05",
        "S3-E06",
        "S3-E07",
    ]
    assert all(decision["s3_exit_gate"].values())
    assert decision["recommended_s4_method"] == (
        "operator_sensitive_two_state_convergence_diagnostic_with_frozen_fallback"
    )


def test_s3_report_preserves_scope_and_negative_findings():
    report = (ROOT / "PF_first_study_s3_hf_connection_20260925.md").read_text()

    required = [
        "回顧的証拠統合（独立検証ではない）",
        "D4 mixing fractionは伸長側で増えて",
        "PF位相gap圧縮も観測されていない",
        "新direct truth点、新Hamiltonian、新fit、post-hoc閾値変更は0",
        "operator-sensitive state-convergence diagnostic",
        "S4専用の新しい事前固定protocol",
    ]
    for text in required:
        assert text in report

