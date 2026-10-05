"""One bounded, staged existing-scalar replay; no scientific dependencies."""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

from review_response import hf_g2_fixed_rule_replay as core


DOC = Path("docs/second_study_v2/hf_g2_fixed_rule_replay_20261005")
ARTIFACT = Path("artifacts/hf_g2_fixed_rule_replay_20261005")
ZERO_COUNTS = {k: 0 for k in ("new_PF_actions", "new_H_exponential_actions", "new_H_matvecs",
    "new_M1_Arnoldi", "new_truth", "new_gap", "new_state_or_Hamiltonian", "policy_or_threshold_fit",
    "GPU_query", "GPU_allocation", "GPU_kernel", "CuPy_import", "combined_acquisition_cost_measurement")}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def head(root):
    return git(root, "rev-parse", "HEAD").decode().strip()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_implementation(root):
    manifest = load(root / DOC / "implementation_manifest.json")
    for f in manifest["files"]:
        data = (root / f["path"]).read_bytes()
        core.require(digest(data) == f["sha256"] and len(data) == f["bytes"], "implementation identity changed: " + f["path"])
        core.require(data == git(root, "show", "HEAD:" + f["path"]), "implementation not committed")
    core.require((root / DOC / "implementation_manifest.json").read_bytes() == git(root, "show", "HEAD:" + (DOC / "implementation_manifest.json").as_posix()), "implementation manifest not committed")


def source_bytes(root, registry, role, stage, accesses):
    source = next(s for s in registry["sources"] if s["role"] == role)
    core.require(stage in source["allowed_stages"], "source opened at wrong stage: " + role)
    data = (root / source["path"]).read_bytes()
    core.require(digest(data) == source["sha256"] and len(data) == source["bytes"], "source hash mismatch: " + role)
    core.require(data == git(root, "show", source["verified_snapshot_commit"] + ":" + source["path"]), "source snapshot mismatch")
    core.require(data == git(root, "show", source["origin_result_commit"] + ":" + source["path"]), "source origin mismatch")
    accesses.append({"role": role, "path": source["path"], "sha256": digest(data), "stage": stage,
                     "origin_result_commit": source["origin_result_commit"], "verified_snapshot_commit": source["verified_snapshot_commit"]})
    return data


def verify_frozen(root, stage, commit, require_head=False):
    if require_head:
        core.require(head(root) == commit, "stage HEAD must equal preceding freeze commit")
    path = root / ARTIFACT / stage
    manifest = load(path / "manifest.json")
    names = {f["path"] for f in manifest["files"]} | {"manifest.json"}
    core.require({x.name for x in path.iterdir()} == names, "frozen artifact file set changed")
    for name in names:
        data = (path / name).read_bytes()
        core.require(data == git(root, "show", commit + ":" + (ARTIFACT / stage / name).as_posix()), "freeze blob mismatch: " + name)
    for f in manifest["files"]:
        data = (path / f["path"]).read_bytes()
        core.require(digest(data) == f["sha256"] and len(data) == f["bytes"], "freeze manifest mismatch")
    marker_name = {"cheap": "ACQUISITION_FROZEN.json", "h1": "H1_FROZEN.json", "prediction": "PREDICTION_FROZEN.json"}[stage]
    marker = load(path / marker_name)
    core.require(digest((path / marker["payload_file"]).read_bytes()) == marker["payload_sha256"], "freeze marker mismatch")
    return load(path / marker["payload_file"]), sorted(names)


def write_stage(root, stage, payload, marker, elapsed, extra=None):
    path = root / ARTIFACT / stage
    filename = {"cheap": "decisions.json", "h1": "h1.json", "prediction": "prediction.json", "result": "result.json"}[stage]
    dump(path / filename, payload)
    dump(path / marker, {"status": payload["status"], "payload_file": filename,
        "payload_sha256": digest((path / filename).read_bytes()), "truth_open_count_before_freeze": 0 if stage != "result" else None,
        "not_prospective_or_holdout": True, "automatic_next_stage": False})
    dump(path / "resource_audit.json", {"stage": stage, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python_executable": sys.executable, "python_version": sys.version, "processes": 1,
        "new_scientific_computation_count": 0, "counts": ZERO_COUNTS,
        "replay_work_seconds_before_artifact_serialization": elapsed,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scope": "file/hash/Git/decision replay cost, not calibration acquisition or combined H1 molecular runtime"})
    if stage == "prediction":
        (path / "prediction.sha256").write_text(digest((path / filename).read_bytes()) + "  prediction.json\n", encoding="utf-8")
    if extra:
        for name, content in extra.items():
            (path / name).write_text(content, encoding="utf-8")
    files = [{"path": p.name, "bytes": p.stat().st_size, "sha256": digest(p.read_bytes())} for p in sorted(path.iterdir())]
    dump(path / "manifest.json", {"schema": "hf_g2_stage_manifest_v1", "stage": stage,
        "status": payload["status"], "manifest_self_excluded": True, "file_count": len(files), "files": files})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("cheap", "h1", "prediction", "score"), required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--previous-commit")
    args = parser.parse_args()
    root = args.project_root.resolve()
    started = time.perf_counter()
    started_head = head(root)
    core.require(git(root, "status", "--porcelain=v1", "--untracked-files=all") == b"", "worktree must be clean before each stage")
    verify_implementation(root)
    protocol = load(root / DOC / "protocol.json")
    registry = load(root / DOC / "source_registry.json")
    core.require(protocol["execution_authorized"] is True and protocol["maximum_replay_count"] == 1, "G2 not authorized")
    core.require(protocol["scope"]["conditions"] == list(core.CONDITIONS), "G2 scope changed")
    core.require(protocol["constants"]["gammas"] == list(core.GAMMAS) and protocol["constants"]["eta"] == .10, "G2 constants changed")
    accesses = []
    parent = json.loads(source_bytes(root, registry, "parent_hf_protocol", args.stage, accesses))
    authorization = json.loads(source_bytes(root, registry, "parent_hf_authorization", args.stage, accesses))
    rules = json.loads(source_bytes(root, registry, "s1a_rules", args.stage, accesses))
    core.require(rules["fixed_constants"]["gamma_frontier"] == list(core.GAMMAS), "parent gamma rule changed")
    core.require(authorization["resolved_execution_blockers"]["eta"]["value"] == .10, "parent eta differs")
    constants = parent["fixed_constants"]
    core.require(constants["epsilon_E_hartree"] == protocol["constants"]["epsilon_E_hartree"] and constants["beta"] == protocol["constants"]["beta"] and constants["K_current_m3_per_step"] == 9108, "HF constants mismatch")
    baselines = {b["condition"]: b for b in parent["baseline_contract"]["conditions"]}
    output_stage = "result" if args.stage == "score" else args.stage
    path = root / ARTIFACT / output_stage
    core.require(not path.exists(), "one-run boundary: stage output already exists")
    if args.stage != "cheap":
        core.require(args.previous_commit is not None, "preceding freeze commit required")
    path.mkdir(parents=True)
    common = {"schema": "hf_g2_" + output_stage + "_v1", "stage_start_HEAD": started_head,
        "protocol_sha256": digest((root / DOC / "protocol.json").read_bytes()),
        "claim_class": "post_hoc_development_replay", "new_scientific_computation_count": 0,
        "Direction_C_provisionally_approved": True, "next_stage_authorized": False}
    if args.stage == "cheap":
        raw = source_bytes(root, registry, "saved_hf_prediction", "cheap", accesses).decode()
        projected, decoded = core.lexical_project(raw, core.cheap_paths())
        core.require(projected["status"] == "hf_domain_prediction_frozen_truth_not_opened", "unexpected source prediction status")
        core.require(projected["p0_protocol_sha256"] == digest((root / registry["role_paths"]["parent_hf_protocol"]).read_bytes()), "parent prediction protocol mismatch")
        core.require(projected["authorization_sha256"] == digest((root / registry["role_paths"]["parent_hf_authorization"]).read_bytes()), "parent prediction authorization mismatch")
        plan = {r["candidate_id"]: r for r in csv.DictReader(io.StringIO(source_bytes(root, registry, "candidate_plan", "cheap", accesses).decode()))}
        core.require(len(plan) == 6 and len(projected["conditions"]) == 2, "six coordinates and two conditions required")
        core.require(tuple(c["condition"] for c in projected["conditions"]) == core.CONDITIONS, "source condition order changed")
        decisions = [core.cheap_policy(c, baselines[c["condition"]], constants, plan) for c in projected["conditions"]]
        common.update({"status": "hf_g2_acquisition_frozen_truth_and_M1_not_decoded", "implementation_commit": started_head,
            "conditions": decisions, "candidate_count": 6, "condition_count": 2,
            "q_acquisition_count": sum(c["q"] for c in decisions), "truth_open_count": 0,
            "M1_values_decoded_count": 0, "source_accesses": accesses,
            "field_projection": {"decoded_value_paths": decoded, "excluded_M1_value_subtrees_decoded": 0,
                "combined_source_bytes_read_for_hash_and_lexical_projection": True,
                "operational_scope": "field-level decoding boundary, not OS sandbox or prospective blinding"}})
        write_stage(root, "cheap", common, "ACQUISITION_FROZEN.json", time.perf_counter() - started)
    elif args.stage == "h1":
        cheap, names = verify_frozen(root, "cheap", args.previous_commit, True)
        indices = [i for i, c in enumerate(cheap["conditions"]) if c["q"]]
        spectral_by_index = {}
        decoded = []
        if indices:
            raw = source_bytes(root, registry, "saved_hf_prediction", "h1", accesses).decode()
            projected, decoded = core.lexical_project(raw, core.spectral_paths(indices))
            for i in indices:
                c = cheap["conditions"][i]
                spectral_by_index[i] = core.validate_spectral(projected["conditions"][i], c, baselines[c["condition"]])
        finals = [{"condition": c["condition"], "q": c["q"], **core.h1_final(c, spectral_by_index.get(i), constants)} for i, c in enumerate(cheap["conditions"])]
        common.update({"status": "hf_g2_H1_frozen_truth_not_opened", "cheap_commit": args.previous_commit,
            "cheap_files_byte_identical": names, "conditions": finals, "truth_open_count": 0,
            "conditional_M1_rows_decoded": 3 * len(indices), "q_zero_M1_rows_decoded": 0,
            "source_accesses": accesses, "decoded_value_paths": decoded})
        write_stage(root, "h1", common, "H1_FROZEN.json", time.perf_counter() - started)
    elif args.stage == "prediction":
        h1, h1_names = verify_frozen(root, "h1", args.previous_commit, True)
        cheap, cheap_names = verify_frozen(root, "cheap", h1["cheap_commit"])
        indices = [i for i, c in enumerate(cheap["conditions"]) if not c["q"]]
        completion = {}
        decoded = []
        if indices:
            raw = source_bytes(root, registry, "saved_hf_prediction", "prediction", accesses).decode()
            projected, decoded = core.lexical_project(raw, core.spectral_paths(indices))
            for i in indices:
                c = cheap["conditions"][i]
                completion[i] = core.validate_spectral(projected["conditions"][i], c, baselines[c["condition"]])
        conditions = []
        for i, c in enumerate(cheap["conditions"]):
            spectral = h1["conditions"][i]["spectral"] if c["q"] else completion[i]
            conditions.append({"condition": c["condition"], "cheap": c,
                "H1": h1["conditions"][i], "always_M1": spectral})
        saved_cost = json.loads(source_bytes(root, registry, "saved_arm_cost", "prediction", accesses))
        attributed = []
        for c in conditions:
            rows = [r for r in saved_cost["coordinates"] if r["condition"] == c["condition"]]
            core.require(len(rows) == 3 and {r["candidate_id"] for r in rows} == {p["candidate_id"] for p in c["cheap"]["points"]}, "cost coordinate contract mismatch")
            cheap_wall = sum(r["local_proxy_wall_seconds"] for r in rows)
            spectral_wall = sum(r["spectral_wall_seconds"] for r in rows)
            spectral_pf = sum(r["M1"]["pf_per_vector_actions"] for r in rows)
            spectral_h = sum(r["M1"]["hamiltonian_matvecs"] for r in rows)
            q = c["cheap"]["q"]
            attributed.append({"condition": c["condition"], "q": q, "saved_cheap_wall_seconds": cheap_wall,
                "saved_standalone_spectral_wall_seconds": spectral_wall,
                "saved_cheap_PF_actions": sum(r["B1_pf_actions"] for r in rows),
                "saved_cheap_H_exponential_actions": sum(r["B1_hamiltonian_exponential_actions"] for r in rows),
                "saved_standalone_spectral_PF_actions": spectral_pf, "saved_standalone_spectral_H_matvecs": spectral_h,
                "H1_saved_spectral_actions_attributed": {"PF": q * spectral_pf, "H_matvec": q * spectral_h},
                "q_zero_comparator_M1_excluded_from_H1": not bool(q),
                "saved_arm_replay_wall_scenarios_seconds": [max(cheap_wall, spectral_wall), cheap_wall + spectral_wall] if q else [cheap_wall, cheap_wall],
                "scenario_is_actual_combined_cost_bound": False,
                "actual_combined_H1_acquisition_cost": "not_measured", "internal_cheap_H_matvecs": "unknown_not_counted_as_one"})
        common.update({"status": "hf_g2_prediction_frozen_truth_not_opened", "implementation_commit": cheap["implementation_commit"],
            "cheap_commit": h1["cheap_commit"], "H1_commit": args.previous_commit,
            "cheap_files_byte_identical": cheap_names, "H1_files_byte_identical": h1_names,
            "conditions": conditions, "truth_open_count": 0, "M1_available_rows": 6,
            "conditional_M1_rows_decoded_after_q_freeze": h1["conditional_M1_rows_decoded"],
            "comparator_M1_rows_decoded_after_H1_freeze": 3 * len(indices),
            "resource_value": {"separate_arm_attribution": attributed, "combined_cost_status": "combined_cost_not_evaluable",
                "saved_peak_process_rss_kib_not_arm_specific": saved_cost["peak_cpu_rss_kib"],
                "source_driver_wall_not_combined_H1": saved_cost["total_driver_wall_seconds"],
                "shared_or_cache_cost": "not_separately_measured_in_saved_HF_runner"},
            "source_accesses": accesses, "decoded_value_paths_for_comparator": decoded})
        write_stage(root, "prediction", common, "PREDICTION_FROZEN.json", time.perf_counter() - started)
    else:
        prediction, names = verify_frozen(root, "prediction", args.previous_commit, True)
        verify_frozen(root, "cheap", prediction["cheap_commit"])
        verify_frozen(root, "h1", prediction["H1_commit"])
        truth_rows = list(csv.DictReader(io.StringIO(source_bytes(root, registry, "saved_truth_csv", "score", accesses).decode())))
        core.require(len(truth_rows) == 6, "exact six saved truth rows required")
        truth = {(r["condition"], r["candidate_id"]): r for r in truth_rows}
        core.require(len(truth) == 6, "duplicate truth coordinate")
        scores, diagnostics = [], []
        for c in prediction["conditions"]:
            condition = c["condition"]
            cheap = c["cheap"]
            baseline = baselines[condition]
            spectral = {r["candidate_id"]: r for r in c["always_M1"]["rows"]}
            controls = []
            for p in cheap["points"]:
                saved = truth[(condition, p["candidate_id"])]
                require_time = float(saved["time_hartree_inverse"])
                core.require(require_time.hex() == float(p["time_hartree_inverse"]).hex() and float(saved["factor_of_T0"]) == p["factor_of_T0"], "truth exact coordinate mismatch")
                direct = float(saved["direct_shift_hartree"])
                gap = float(saved["phase_gap_radians"])
                m1 = spectral[p["candidate_id"]]
                branch = core.inherited.physical_branch_correct(predicted_shift_hartree=m1["signed_shift_estimate_hartree"], direct_shift_hartree=direct, truth_phase_gap_radians=gap, time_value=require_time)
                error_m = abs(m1["signed_shift_estimate_hartree"] - direct)
                delta_c = p["B1"][0]["signed_shift_estimate_hartree"]
                diagnostics.append({"condition": condition, "candidate_id": p["candidate_id"], "time_hex": require_time.hex(),
                    "time_hartree_inverse": require_time, "cheap_shift_hartree": delta_c,
                    "M1_shift_hartree": m1["signed_shift_estimate_hartree"], "direct_shift_hartree": direct,
                    "E_C_hartree": abs(delta_c - direct), "E_M_hartree": error_m, "M1_width_hartree": m1["width_hartree"],
                    "M1_empirical_width_covers": error_m <= m1["width_hartree"], "M1_physical_branch_correct": branch,
                    "truth_phase_gap_radians": gap, "M1_abstained": m1["abstained"], "M1_e_use_hartree": m1["e_use_hartree"]})
                if p["factor_of_T0"] == 1:
                    controls.append(core.inherited.t0_reproduction_pass(abstained=m1["abstained"], branch_correct=branch,
                        predicted_shift_hartree=m1["signed_shift_estimate_hartree"], width_hartree=m1["width_hartree"], direct_shift_hartree=direct))
            core.require(len(controls) == 1, "one T0 control required")
            control = controls[0]
            def score(action):
                direct = float(truth[(condition, action["selected_candidate"])]["direct_shift_hartree"])
                return core.score_action(action, direct, baseline, constants, control)
            fixed = [{"gamma": arm["gamma"], **score(arm)} for arm in cheap["B1"]]
            b2, h1_score = score(cheap["B2"]), score(c["H1"]["action"])
            outcome = core.outcome(b2, h1_score, fixed, cheap["q"], control)
            change = any(cheap["B2"][k] != c["H1"]["action"][k] for k in ("selected_candidate", "frozen_continuous_budget", "fallback"))
            scores.append({"condition": condition, "q": cheap["q"], "cheap_instability": cheap["instability"],
                "B2_gamma": cheap["B2_gamma"], "T0_reproduction_pass": control, "B0": score(cheap["B0"]),
                "B1_fixed_frontier": fixed, "B2": b2, "H1": h1_score, "always_M1": score(c["always_M1"]["selection"]),
                "H1_source": c["H1"]["source"], "decision_changed": change, "outcome": outcome,
                "spectral_consistency": c["H1"]["consistency"]})
        if any(s["outcome"].startswith("incomplete") for s in scores):
            classification = "incomplete_reference_control_failure"
        elif any(s["outcome"].startswith("D_") for s in scores):
            classification = "D_gate_false_negative"
        elif any(s["outcome"].startswith("C_") for s in scores):
            classification = "C_conditional_spectral_decision_value_cost_unresolved"
        elif all(s["outcome"].startswith("A_") for s in scores):
            classification = "A_cheap_sufficient"
        else:
            classification = "B_no_unique_spectral_value"
        aggregates = {}
        for arm in ("B0", "B2", "H1", "always_M1"):
            aggregates[arm] = {"budget_sum": sum(s[arm]["frozen_continuous_budget"] for s in scores),
                "safe_and_valid_count": sum(s[arm]["safe_and_valid"] for s in scores),
                "unsafe_budget_count": sum(not s[arm]["budget_safe"] for s in scores),
                "safe_target_count": sum(s[arm]["safe_target_met"] for s in scores)}
        frontier = [{"gamma": gamma, "budget_sum": sum(s["B1_fixed_frontier"][i]["frozen_continuous_budget"] for s in scores),
            "safe_count": sum(s["B1_fixed_frontier"][i]["safe_and_valid"] for s in scores)} for i, gamma in enumerate(core.GAMMAS)]
        q_count = sum(s["q"] for s in scores)
        common.update({"status": "second_study_v2_hf_g2_fixed_rule_replay_complete_review_required",
            "classification": classification, "classification_is_not_original_S1A_taxonomy": True,
            "prediction_commit": args.previous_commit, "prediction_files_byte_identical": names,
            "condition_scores": scores, "coordinate_diagnostics": diagnostics, "aggregates": aggregates,
            "B1_gamma_frontier": frontier, "q_acquisition_count": q_count, "nontrivial_selective_acquisition": 0 < q_count < 2,
            "decision_change_count": sum(s["decision_changed"] for s in scores), "truth_existing_coordinates_reused": 6,
            "new_truth_coordinates": 0, "nearest_or_interpolation_count": 0,
            "source_accesses": accesses, "resource_value": prediction["resource_value"],
            "original_S1A_D_unchanged": True, "original_HF_robust_signal_unchanged": True,
            "novelty_finalized": False, "human_final_direction_review_required": True,
            "push_authorized": False, "automatic_next_steps": []})
        csv_output = io.StringIO()
        writer = csv.DictWriter(csv_output, fieldnames=list(diagnostics[0]))
        writer.writeheader()
        writer.writerows(diagnostics)
        lines = ["# HF G2 fixed-rule replay result", "", "Status: `" + common["status"] + "`", "",
            "Classification: `" + classification + "`。既知developmentデータのreplayであり、holdout・新規取得・安全性certificateではない。", "",
            "| 条件 | q | B2 gamma | B2 safe | H1 safe | H1変更 | 判定 |", "|---|---:|---:|---|---|---|---|"]
        for s in scores:
            lines.append(f"| {s['condition']} | {s['q']} | {s['B2_gamma']} | {s['B2']['safe_and_valid']} | {s['H1']['safe_and_valid']} | {s['decision_changed']} | {s['outcome']} |")
        lines += ["", "## 解釈と停止", "",
            "q=0/unsafeが一件でもあればcheap stability gateのfalse negativeであり、低budgetを利益に数えない。q=1の変更はfixed-cheap frontierで再現できるかを別に評価する。Direction Cは暫定のまま、最終RQ・paper landing・gate redesignの判断へ戻る。", "",
            "新規PF/H action、M1、truth、gap、fit、GPUは全て0。保存作用回数と実際のreplay I/O/runtimeを混同しない。q=1 combined acquisition costは未測定で、保存separate-arm時間のmax/sumはscenarioであり厳密上下界ではない。", "",
            "元HF robust_signal、元S1A D、過去H-chain/D2-A判定を変更していない。HCl/LiF/C1/D2-B・追加baseline・threshold救済・pushは自動許可しない。", ""]
        write_stage(root, "result", common, "COMPLETE.json", time.perf_counter() - started,
            {"coordinate_diagnostics.csv": csv_output.getvalue(), "report.md": "\n".join(lines)})
    print(json.dumps({"stage": args.stage, "status": common["status"],
        "classification": common.get("classification"), "output": str(path), "new_scientific_computation_count": 0}))


if __name__ == "__main__":
    main()
