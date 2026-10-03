from __future__ import annotations

import argparse
from pathlib import Path

import second_study_v2_s1a_no_fit as core


STATUS = "second_study_v2_s1a_no_fit_replay_complete_review_required"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--prediction-root", required=True)
    parser.add_argument("--prediction-commit", required=True)
    parser.add_argument("--prediction-artifact-relative", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    prediction_root = (root / args.prediction_root).resolve()
    artifact_relative = Path(args.prediction_artifact_relative)
    output = (root / args.output_dir).resolve()
    if output.exists():
        raise core.S1AError(f"output already exists: {output}")
    commit_identity = core.verify_prediction_commit(
        root, prediction_root, args.prediction_commit, artifact_relative
    )
    prediction = core.load_json(prediction_root / "prediction.json")
    marker = core.load_json(prediction_root / "PREDICTION_FROZEN.json")
    if prediction.get("truth_open_count") != 0 or marker.get("truth_open_count_before_freeze") != 0:
        raise core.S1AError("prediction freeze is not truth-free")
    decision = core.classify_contract_failure(prediction)

    result = {
        "schema": "second_study_v2_s1a_no_fit_result_v1",
        "status": STATUS,
        "claim_class": "post_hoc_development_diagnostic",
        **decision,
        **commit_identity,
        "condition_count": prediction["condition_count"],
        "matched_coordinate_count": prediction["matched_coordinate_count"],
        "contract_failure_conditions": prediction["contract_failure_conditions"],
        "M1_opened_coordinate_count": 0,
        "truth_open_count": 0,
        "new_scientific_computation_count": 0,
        "policy_fit_count": 0,
        "threshold_fit_count": 0,
        "next_step": "external_research_direction_review",
        "automatic_next_steps": [],
    }
    output.mkdir(parents=True)
    core.write_json(output / "result.json", result)
    core.write_json(output / "decision.json", {
        "schema": "second_study_v2_s1a_no_fit_decision_v1",
        "status": STATUS,
        **decision,
        "contract_failure_conditions": prediction["contract_failure_conditions"],
        "next_step": "external_research_direction_review",
        "authorization": {
            "B2_H1_fitting": False,
            "missing_M1_acquisition": False,
            "combined_cost_measurement": False,
            "new_molecule": False,
            "holdout": False,
            "external_baseline": False,
            "new_PF": False,
            "push": False,
        },
    })
    core.write_json(output / "source_audit.json", {
        "schema": "second_study_v2_s1a_result_source_audit_v1",
        **commit_identity,
        "prediction_sha256": core.sha256_file(prediction_root / "prediction.json"),
        "truth_source_open_count": 0,
        "classification_did_not_require_truth": True,
    })
    core.write_json(output / "resource_audit.json", {
        "schema": "second_study_v2_s1a_result_resource_audit_v1",
        "new_PF_actions": 0,
        "new_H_actions": 0,
        "new_Arnoldi_actions": 0,
        "new_truth": 0,
        "M1_opened_coordinate_count": 0,
        "truth_open_count": 0,
        "cost_envelope_status": "not_evaluated_after_contract_failure",
        "gpu_operations": 0,
    })
    (output / "report.md").write_text(
        "# S1A no-fit replay result\n\n"
        f"Status: `{STATUS}`\n\n"
        "Classification: **D — contract_or_cost_not_replayable**\n\n"
        "HFの保存済み4-gamma frontierは確認できたが、HCl 2条件にはRule 1が要求する保存済み4-gamma frontierが存在しない。"
        "protocolで禁止したfrontier生成・fit・別contract置換を行わず、M1とtruthを開く前にfail-closedで停止した。\n\n"
        "この結果はselective calibrationの性能否定ではなく、現在の12座標を一つのno-fit ruleでreplayできるという前提が成立しなかったことを示す。\n",
        encoding="utf-8",
    )
    core.write_json(output / "COMPLETE.json", {
        "schema": "second_study_v2_s1a_complete_v1",
        "status": STATUS,
        "classification_code": "D",
        "review_required": True,
    })
    manifest_names = [
        "result.json", "decision.json", "source_audit.json",
        "resource_audit.json", "report.md", "COMPLETE.json",
    ]
    core.write_json(output / "manifest.json", core.manifest_payload(
        output, manifest_names, "second_study_v2_s1a_result_manifest_v1", STATUS
    ))
    print(STATUS)
    print("classification=D:contract_or_cost_not_replayable")
    print("truth_open_count=0")


if __name__ == "__main__":
    main()
