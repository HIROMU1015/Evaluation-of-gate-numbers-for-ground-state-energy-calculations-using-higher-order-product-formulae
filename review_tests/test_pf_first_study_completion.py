from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(".")
EXPERIMENT_A = ROOT / "artifacts/pf_first_study_experiment_a_20260925_d3fadde"
PHASE_A = ROOT / "artifacts/pf_first_study_phase_a_20260925_6265243"
PHASE_B = ROOT / "artifacts/pf_first_study_phase_b_20260925_5a2f0a2"
S0_FAILED = ROOT / "artifacts/server_pf_first_study_s0_exact_time_20260925_b3a079f"
S0_COMPLETE = (
    ROOT
    / "artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201"
)
FIRST_STUDY_PROTOCOL_SHA256 = (
    "410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565"
)
PHASE_A_PREDICTION_SHA256 = (
    "60058fe333d4b25f1ad4b8f3f5342a3736f2379ce9490b3f2ecde69583beeeda"
)
S0_PREDICTION_SHA256 = (
    "fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e"
)
S0_ANCHOR_PROTOCOL_SHA256 = (
    "8f776ded65e42b7657d5c014cf525421b95cbbfb40aa0744c69d2c11f00204b1"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_count(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _manifest_hashes_match(root: Path) -> bool:
    manifest = _load(root / "manifest.json")
    return all(
        _sha256(root / name) == expected
        for name, expected in manifest["artifact_sha256"].items()
    )


def test_first_study_all_fixed_stages_are_complete() -> None:
    assert _sha256(ROOT / "PF_first_study_protocol_20260925.json") == (
        FIRST_STUDY_PROTOCOL_SHA256
    )

    experiment_a = _load(EXPERIMENT_A / "audit.json")
    assert (EXPERIMENT_A / "COMPLETE").is_file()
    assert experiment_a["status"] == "complete_validation"
    assert all(row["passed"] for row in experiment_a["checks"])
    assert _manifest_hashes_match(EXPERIMENT_A)

    phase_a = _load(PHASE_A / "audit.json")
    assert (PHASE_A / "SELECTION_FROZEN").is_file()
    assert phase_a["status"] == "selection_frozen"
    assert phase_a["prediction_sha256"] == PHASE_A_PREDICTION_SHA256
    assert _sha256(PHASE_A / "predictions.json") == PHASE_A_PREDICTION_SHA256
    assert _manifest_hashes_match(PHASE_A)

    phase_b = _load(PHASE_B / "audit.json")
    assert (PHASE_B / "COMPLETE").is_file()
    assert phase_b["status"] == "complete_with_findings"
    assert all(phase_b["checks"].values())
    assert phase_b["phase_a_prediction_sha256"] == PHASE_A_PREDICTION_SHA256
    assert phase_b["stopping_outcomes"] == {
        "A_single_component_dominates": True,
        "B_dominant_component_switches": False,
        "C_material_error_but_resource_robust": False,
        "dominant_components_observed": ["E_state_hartree"],
        "null_result": False,
    }
    assert phase_b["counts"]["decomposition_rows"] == 1536
    assert phase_b["counts"]["observable_rows"] == 2256
    assert phase_b["counts"]["direct_truth_rows"] == 1764
    assert _manifest_hashes_match(PHASE_B)


def test_failed_s0_is_preserved_and_v1_1_is_complete() -> None:
    failed = _load(S0_FAILED / "audit.json")
    assert failed["status"] == "failed_numerical_validation"
    assert not (S0_FAILED / "COMPLETE").exists()
    assert not failed["checks"]["anchor_shift_reproduction_passed"]
    assert failed["extrema"]["maximum_anchor_shift_reproduction_difference_hartree"] > 1e-9

    audit = _load(S0_COMPLETE / "audit.json")
    manifest = _load(S0_COMPLETE / "manifest.json")
    source = _load(S0_COMPLETE / "source_manifest.json")
    assert (S0_COMPLETE / "COMPLETE").is_file()
    assert audit["status"] == manifest["status"] == "complete_exact_time_scoring"
    assert all(audit["checks"].values())
    assert all(row["passed"] for row in source["h01_p03_source_checks"])
    assert audit["accounting"] == {
        "anchor_recomputation_count": 6,
        "branch_audit_row_count": 24,
        "cache_reuse_count": 0,
        "new_direct_truth_point_count": 18,
        "scoring_row_count": 6,
    }
    assert audit["extrema"]["maximum_anchor_shift_reproduction_difference_hartree"] <= 1e-9
    assert manifest["first_study_protocol_sha256"] == FIRST_STUDY_PROTOCOL_SHA256
    assert manifest["practical_predictions_sha256"] == S0_PREDICTION_SHA256
    assert manifest["s0_anchor_protocol_sha256"] == S0_ANCHOR_PROTOCOL_SHA256
    assert _sha256(S0_COMPLETE / "predictions.json") == S0_PREDICTION_SHA256
    assert _sha256(S0_COMPLETE / "s0_anchor_protocol.json") == (
        S0_ANCHOR_PROTOCOL_SHA256
    )
    assert _csv_count(S0_COMPLETE / "branch_audit.csv") == 24
    assert _csv_count(S0_COMPLETE / "scoring.csv") == 6
    assert _manifest_hashes_match(S0_COMPLETE)
