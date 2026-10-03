from __future__ import annotations

import argparse
from pathlib import Path

import second_study_v2_s1a_no_fit as core


STATUS = "s1a_prediction_frozen_contract_not_replayable_truth_not_opened"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--source-contract", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    protocol_path = (root / args.protocol).resolve()
    authorization_path = (root / args.authorization).resolve()
    contract_path = (root / args.source_contract).resolve()
    output = (root / args.output_dir).resolve()
    if output.exists():
        raise core.S1AError(f"output already exists: {output}")

    protocol = core.load_json(protocol_path)
    authorization = core.load_json(authorization_path)
    contract = core.load_json(contract_path)
    if protocol.get("status") != "s1a_no_fit_rules_frozen_execution_not_started":
        raise core.S1AError("unexpected protocol status")
    if authorization.get("status") != "authorized_once_under_frozen_protocol":
        raise core.S1AError("unexpected authorization status")
    if contract.get("truth_paths_exposed_to_predictor") != 0:
        raise core.S1AError("predictor source contract exposes truth paths")

    source_records = []
    for source in contract["sources"]:
        path = (root / source["path"]).resolve()
        actual = core.sha256_file(path)
        if actual != source["sha256"]:
            raise core.S1AError(f"source SHA-256 mismatch: {source['path']}")
        source_records.append({
            "path": source["path"],
            "expected_sha256": source["sha256"],
            "actual_sha256": actual,
            "identity_pass": True,
            "access_stage": source["access_stage"],
        })

    by_role = {source["role"]: root / source["path"] for source in contract["sources"]}
    hf = core.load_json(by_role["HF frozen B1 frontier and M1 rows"])
    hcl = core.load_json(by_role["HCl frozen cheap strategy and selector records"])

    condition_audits = []
    for condition in hf.get("conditions", []):
        name = condition.get("condition")
        if name not in protocol["scope"]["conditions"]:
            continue
        frontier = core.exact_gamma_frontier(condition.get("selection", {}).get("B1", []))
        condition_audits.append({
            "condition": name,
            "family": "HF",
            "native_candidate_contract": "T0_1p3T0_1p6T0",
            "frontier": frontier,
            "B2_decision_frozen": False,
            "q_frozen": False,
        })

    for condition in hcl.get("conditions", []):
        name = condition.get("condition")
        if name not in protocol["scope"]["conditions"]:
            continue
        strategies = condition.get("strategies", {})
        saved_frontier = strategies.get("B1", []) if isinstance(strategies, dict) else []
        frontier = core.exact_gamma_frontier(saved_frontier)
        if not saved_frontier:
            frontier["failures"] = ["saved_four_gamma_frontier_absent"]
            frontier["available"] = False
        condition_audits.append({
            "condition": name,
            "family": "HCl",
            "native_candidate_contract": "0p5_0p65_0p8_tana",
            "frontier": frontier,
            "B2_decision_frozen": False,
            "q_frozen": False,
        })

    expected_conditions = set(protocol["scope"]["conditions"])
    observed_conditions = {row["condition"] for row in condition_audits}
    missing_conditions = sorted(expected_conditions - observed_conditions)
    for name in missing_conditions:
        condition_audits.append({
            "condition": name,
            "family": "unknown",
            "native_candidate_contract": "unknown",
            "frontier": {"available": False, "arm_count": 0, "gamma_values": [], "failures": ["condition_missing"]},
            "B2_decision_frozen": False,
            "q_frozen": False,
        })

    failed = [row["condition"] for row in condition_audits if not row["frontier"]["available"]]
    contract_replayable = not failed and len(condition_audits) == 4
    if contract_replayable:
        raise core.S1AError("this frozen implementation only handles the predeclared fail-closed contract audit")

    prediction = {
        "schema": "second_study_v2_s1a_no_fit_prediction_v1",
        "status": STATUS,
        "claim_class": "post_hoc_development_diagnostic",
        "protocol_sha256": core.sha256_file(protocol_path),
        "authorization_sha256": core.sha256_file(authorization_path),
        "source_contract_sha256": core.sha256_file(contract_path),
        "condition_count": 4,
        "matched_coordinate_count": 12,
        "condition_audits": sorted(condition_audits, key=lambda row: row["condition"]),
        "contract_replayable": False,
        "contract_failure_conditions": sorted(failed),
        "contract_failure_action": "classification_D_without_rescue",
        "B2_decision_count": 0,
        "q_decision_count": 0,
        "M1_available_coordinate_count": 12,
        "M1_opened_coordinate_count": 0,
        "truth_open_count": 0,
        "new_scientific_computation_count": 0,
        "policy_fit_count": 0,
        "threshold_fit_count": 0,
    }

    output.mkdir(parents=True)
    core.write_json(output / "prediction.json", prediction)
    prediction_hash = core.sha256_file(output / "prediction.json")
    (output / "prediction.sha256").write_text(prediction_hash + "  prediction.json\n", encoding="utf-8")
    core.write_json(output / "PREDICTION_FROZEN.json", {
        "schema": "second_study_v2_s1a_prediction_frozen_v1",
        "status": STATUS,
        "prediction_sha256": prediction_hash,
        "truth_open_count_before_freeze": 0,
        "M1_opened_coordinate_count": 0,
    })
    core.write_json(output / "source_audit.json", {
        "schema": "second_study_v2_s1a_source_audit_v1",
        "source_count": len(source_records),
        "sources": source_records,
        "all_identity_pass": True,
    })
    core.write_json(output / "access_audit.json", {
        "schema": "second_study_v2_s1a_access_audit_v1",
        "cheap_condition_rows_opened": 4,
        "M1_available_coordinate_count": 12,
        "M1_opened_coordinate_count": 0,
        "truth_paths_exposed_to_predictor": 0,
        "truth_open_count": 0,
        "conditional_access_stopped_at_contract_gate": True,
    })
    core.write_json(output / "resource_audit.json", {
        "schema": "second_study_v2_s1a_resource_audit_v1",
        "new_PF_actions": 0,
        "new_H_actions": 0,
        "new_Arnoldi_actions": 0,
        "new_truth": 0,
        "new_state_or_Hamiltonian": 0,
        "combined_cost_measurement": 0,
        "saved_cost_rows_opened": 0,
        "cost_envelope_status": "not_evaluated_after_contract_failure",
        "gpu_operations": 0,
    })
    manifest_names = [
        "prediction.json", "prediction.sha256", "PREDICTION_FROZEN.json",
        "source_audit.json", "access_audit.json", "resource_audit.json",
    ]
    core.write_json(output / "manifest.json", core.manifest_payload(
        output, manifest_names, "second_study_v2_s1a_prediction_manifest_v1", STATUS
    ))
    print(STATUS)
    print(f"prediction_sha256={prediction_hash}")
    print("contract_failure_conditions=" + ",".join(sorted(failed)))


if __name__ == "__main__":
    main()
