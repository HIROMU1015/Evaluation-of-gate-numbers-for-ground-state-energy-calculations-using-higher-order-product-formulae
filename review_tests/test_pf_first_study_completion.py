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
S3 = ROOT / "artifacts/pf_first_study_s3_hf_connection_20260925"
S4_PHASE_A = ROOT / "artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f"
S4_COMPLETE = (
    ROOT
    / "artifacts/server_pf_first_study_s4_state_convergence_v1_1_20260925_96699df"
)
FINAL_DECISION = ROOT / "PF_first_study_final_decision_20260925.json"
FINAL_SYNTHESIS = ROOT / "PF_first_study_final_synthesis_20260925.md"
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
S4_PROTOCOL_SHA256 = (
    "5c3c33fab6752b5ccf0ec9ee415e115bdf2134256e5a956f6b0e9b639f554c40"
)
S4_AMENDMENT_SHA256 = (
    "9ce996b2732e02a7bb2fa4f1d6f8a4e09fd503896a4eda7a9a4496be0f402150"
)
S4_PREDICTION_SHA256 = (
    "47cdef9b52ea73feef0c005229cb9a482ee8e95afff87f038ff8461549f1c729"
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


def test_s3_and_s4_close_the_first_study_without_s5() -> None:
    s3 = _load(S3 / "decision.json")
    assert (S3 / "COMPLETE").is_file()
    assert s3["status"] == "complete_retrospective_synthesis"
    assert all(s3["s3_exit_gate"].values())
    assert s3["new_direct_truth_point_count"] == 0

    phase_a = _load(S4_PHASE_A / "phase_a_audit.json")
    assert (S4_PHASE_A / "PHASE_A_FROZEN").is_file()
    assert phase_a == {
        "condition_count": 6,
        "new_direct_truth_point_count": 0,
        "phase_a_commit": "f66e86f05473dc00790f47cf4ce493d9f64f5a57",
        "prediction_sha256": S4_PREDICTION_SHA256,
        "protocol_sha256": S4_PROTOCOL_SHA256,
        "status": "selection_frozen",
        "strategy_count": 7,
        "truth_opened": False,
    }

    audit = _load(S4_COMPLETE / "audit.json")
    manifest = _load(S4_COMPLETE / "manifest.json")
    decision = _load(S4_COMPLETE / "decision.json")
    assert (S4_COMPLETE / "COMPLETE").is_file()
    assert audit["status"] == manifest["status"] == "complete_no_benefit"
    assert all(audit["checks"].values())
    assert audit["accounting"] == {
        "cache_reuse_count": 0,
        "inserted_direct_coordinate_count": 60,
        "new_direct_truth_coordinate_count": 72,
        "new_uniform_anchor_coordinate_count": 12,
        "saved_anchor_recomputation_count": 0,
        "strategy_scoring_row_count": 42,
        "unique_selected_coordinate_count": 20,
    }
    assert decision["minimum_safety"]
    assert decision["diagnostic_specificity"]
    assert not decision["efficiency_gain"]
    assert decision["outcome"] == "no_benefit"
    assert decision["strategy_summary"]["state_targeted_fallback"] == (
        decision["strategy_summary"]["practical_baseline"]
    )
    assert manifest["protocol_sha256"] == S4_PROTOCOL_SHA256
    assert manifest["phase_b_amendment_sha256"] == S4_AMENDMENT_SHA256
    assert manifest["prediction_sha256"] == S4_PREDICTION_SHA256
    assert _sha256(S4_COMPLETE / "predictions.json") == S4_PREDICTION_SHA256
    assert _sha256(S4_COMPLETE / "s4_anchor_protocol.json") == S4_AMENDMENT_SHA256
    assert _csv_count(S4_COMPLETE / "branch_audit.csv") == 72
    assert _csv_count(S4_COMPLETE / "strategy_scoring.csv") == 42
    assert _manifest_hashes_match(S4_COMPLETE)

    final = _load(FINAL_DECISION)
    assert final["status"] == "complete_mechanism_study_no_method_benefit"
    assert final["stages"]["s4_state_convergence"]["result_commit"] == (
        "4d831b52475a7399b74a048a7471eaba6c4527c0"
    )
    assert final["stages"]["s4_state_convergence"]["outcome"] == "no_benefit"
    final_s4 = final["stages"]["s4_state_convergence"]
    assert final_s4["unique_selected_coordinate_count"] == (
        audit["accounting"]["unique_selected_coordinate_count"]
    )
    assert final_s4["inserted_direct_coordinate_count"] == (
        audit["accounting"]["inserted_direct_coordinate_count"]
    )
    assert final_s4["uniform_anchor_coordinate_count"] == (
        audit["accounting"]["new_uniform_anchor_coordinate_count"]
    )
    assert final_s4["new_direct_truth_coordinate_count"] == (
        audit["accounting"]["new_direct_truth_coordinate_count"]
    )
    assert final_s4["baseline_mean_regret"] == (
        decision["strategy_summary"]["practical_baseline"]["mean_regret"]
    )
    assert final_s4["targeted_fallback_mean_regret"] == (
        decision["strategy_summary"]["state_targeted_fallback"]["mean_regret"]
    )
    assert final_s4["equal_cost_mean_regret"] == (
        decision["strategy_summary"]["equal_cost_extra_points"]["mean_regret"]
    )
    assert final_s4["minimum_safety_passed"] == decision["minimum_safety"]
    assert final_s4["efficiency_gain_passed"] == decision["efficiency_gain"]
    assert final_s4["diagnostic_specificity_passed"] == (
        decision["diagnostic_specificity"]
    )
    assert final["research_decision"] == {
        "core_mechanism_result_complete": True,
        "method_extension_supported": False,
        "proceed_to_s5": False,
        "additional_selector_tuning_in_current_study": False,
        "next_action": "paper_and_reproducibility_synthesis",
    }

    synthesis = FINAL_SYNTHESIS.read_text(encoding="utf-8")
    for required in (
        "complete_mechanism_study_no_method_benefit",
        "complete_no_benefit",
        "4d831b52475a7399b74a048a7471eaba6c4527c0",
        S4_PROTOCOL_SHA256,
        S4_AMENDMENT_SHA256,
        S4_PREDICTION_SHA256,
        "S5の未使用active-space分子評価へ進まない",
    ):
        assert required in synthesis
