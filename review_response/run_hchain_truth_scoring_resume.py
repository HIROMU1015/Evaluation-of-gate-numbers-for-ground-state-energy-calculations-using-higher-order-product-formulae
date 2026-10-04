"""One authorized same-output continuation; no ground eigensolve or predictor rerun."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
import time

import numpy as np

from review_response.hchain_input_reference_preparation import (
    Ledger, PreparationError, bounded_stage, sha_array, sha_file, write_json,
)
from review_response.hchain_prediction_phase import (
    OLD, PREP, PREP_DOC, NEW_SOURCES, ReadBoundary, check_remote, load_plan,
    preparation_gate, require_clean, verify_blob, verify_entries,
)
from review_response.hchain_selective_calibration_schedule import EPSILON
from review_response.hchain_truth_scoring import (
    DOC as ORIGINAL_DOC, METHOD, PREDICTION, PRED_ROOT, SOURCES as ORIGINAL_SOURCES,
    bundle, commit_stage, git, score_all, source_gate, truth_quality, verify_stage,
)
from review_response.run_hchain_prediction_phase import fixed_environment, load_inputs
from review_response.run_hchain_truth_scoring import full_unitary, helper, serial_truth, utc, write_csv

DOC = "docs/second_study_v2/hchain_truth_scoring_resume_20261004"
STOP = "e8407f60756c4e3efb23ec7c4d6087e8f5d5e5e0"
OUT = "artifacts/hchain_truth_scoring_20261004"
SOURCES = (f"{DOC}/authorization.json", f"{DOC}/protocol.md",
           "review_response/run_hchain_truth_scoring_resume.py",
           "review_tests/test_hchain_truth_scoring_resume.py")
SEAL = f"{DOC}/implementation_manifest.json"


def seal(root):
    require_clean(root)
    check_remote(root)
    content = git(root, "rev-parse", "HEAD").decode().strip()
    git(root, "merge-base", "--is-ancestor", STOP, content)
    if (root/SEAL).exists():
        raise PreparationError("resume seal already exists")
    rows = []
    for name in SOURCES:
        verify_blob(root, name, content)
        rows.append({"path": name, "bytes": (root/name).stat().st_size,
                     "sha256": sha_file(root/name), "origin_result_commit": content,
                     "verified_snapshot_commit": content})
    write_json(root/SEAL, {"content_commit": content, "stopped_publication_commit": STOP,
                          "manifest_self_excluded": True, "files": rows})


def resume_gate(root):
    prediction, source = source_gate(root)  # Original scorer and prediction stay byte-identical.
    verify_blob(root, SEAL, "HEAD")
    manifest = json.loads((root/SEAL).read_text())
    content = manifest["content_commit"]
    git(root, "merge-base", "--is-ancestor", STOP, content)
    git(root, "merge-base", "--is-ancestor", content, "HEAD")
    if {row["path"] for row in manifest["files"]} != set(SOURCES):
        raise PreparationError("resume source set mismatch")
    verify_entries(root, manifest["files"])
    for row in manifest["files"]:
        verify_blob(root, row["path"], content)
    return prediction, {**source, "resume_implementation_commit": content,
                        "resume_manifest_sha256": sha_file(root/SEAL), "resume_sources": manifest["files"]}


def stopped_gate(root):
    auth = json.loads((root/DOC/"authorization.json").read_text())
    directory = root/OUT
    expected = {"STARTED.json", "FAILURE.json", "STOPPED.json", "ground_runtime_preservation.json",
                "report.md", "pre_focused_tests.log", "pre_focused_tests_audit.json", "stop_manifest.json"}
    names = git(root, "ls-tree", "-r", "--name-only", STOP, OUT).decode().splitlines()
    if {Path(name).name for name in names} != expected or len(names) != 8:
        raise PreparationError("stopped publication set mismatch")
    for name in names:
        verify_blob(root, name, STOP)
    for name, key in (("FAILURE.json", "failure_sha256"),
                      ("ground_runtime_preservation.json", "preservation_sha256"),
                      ("stop_manifest.json", "stop_manifest_sha256")):
        if sha_file(directory/name) != auth[key]:
            raise PreparationError("stopped record hash mismatch")
    verify_entries(directory, json.loads((directory/"stop_manifest.json").read_text())["files"])
    failure = json.loads((directory/"FAILURE.json").read_text())
    counts = failure["resources"]["counts"]
    expected_error = f"repository data access outside allowlist: {root}/review_response/hchain_prediction_phase.py"
    if failure["message"] != expected_error or failure["stage_commits"] or counts["full_H_ground_solves"] != 3:
        raise PreparationError("not the authorized pre-ground-freeze integration failure")
    for key in ("full_pf_unitary_builds", "direct_truth_coordinates", "target_phase_gaps",
                "candidate_cheap_pf_actions", "m1_pf_vector_actions", "GPU_queries", "GPU_allocations", "GPU_kernels"):
        if counts[key]:
            raise PreparationError("stopped run already consumed forbidden resume work")
    preservation = json.loads((directory/"ground_runtime_preservation.json").read_text())
    private = directory/".runtime"
    if private.is_symlink() or {path.name for path in private.iterdir()} != {row["path"] for row in preservation["files"]}:
        raise PreparationError("preserved ground file set mismatch")
    verify_entries(private, preservation["files"])
    return failure, preservation


def allowed_reads(root, runtime):
    inherited = json.loads((root/PREP_DOC/"implementation_manifest.json").read_text())
    names = {row["path"] for row in inherited["files"]}
    names.update(NEW_SOURCES)  # The omitted frozen prediction source/test paths, not arbitrary reads.
    names.update(ORIGINAL_SOURCES)
    names.update(SOURCES)
    names.update((SEAL, f"{ORIGINAL_DOC}/implementation_manifest.json", f"{PREP_DOC}/implementation_manifest.json"))
    for directory in (OLD, "docs/second_study_v2/hchain_prediction_20261004"):
        names.update(str(path.relative_to(root)) for path in (root/directory).iterdir() if path.is_file())
    names.update(str(path.relative_to(root)) for path in (root/PREP).iterdir() if path.is_file())
    names.update(f"{PREP}/.runtime/{row['path']}" for row in runtime["files"])
    names.update(git(root, "ls-tree", "-r", "--name-only", PREDICTION, PRED_ROOT).decode().splitlines())
    return [root/name for name in sorted(names)]


def restore_ledger(failure):
    old = failure["resources"]
    ledger = Ledger(counts=Counter(old["counts"]), timings=Counter(old["timings_seconds"]))
    ledger.maximum_gate_cache_bytes = old["maximum_gate_cache_bytes"]
    ledger.maximum_pf_norm_residual = old["maximum_pf_norm_residual"]
    ledger.maximum_h_exp_norm_residual = old["maximum_h_exp_norm_residual"]
    return ledger


def recover_ground(path, h, spec, method, ledger):
    with np.load(path, allow_pickle=False) as archive:
        if set(archive.files) != {"ground_vector", "energy"}:
            raise PreparationError("saved ground member set mismatch")
        vector, scalar = archive["ground_vector"].copy(), archive["energy"].copy()
    ledger.counts["saved_ground_recovery_reads"] += 1
    if vector.shape != (spec["sector_dimension"],) or scalar.shape != ():
        raise PreparationError("saved ground dimension mismatch")
    energy = float(scalar)
    if not np.isfinite(energy) or not np.all(np.isfinite(vector)) or sha_array(h) != spec["H_sha256_numpy_v1"]:
        raise PreparationError("saved ground/H finite or identity gate failed")
    norm = abs(float(np.linalg.norm(vector))-1.)
    ledger.charge("ground_revalidation_H_matvecs", 3)
    ledger.counts["ground_verification_H_matvecs"] += 1
    residual = float(np.linalg.norm(h@vector-energy*vector))
    rule = method["ground_solver"]
    if norm > rule["normalization_absolute_maximum"] or residual > rule["eigenpair_residual_maximum_hartree"]:
        raise PreparationError("saved ground norm/residual gate failed; no repair")
    return {"energy_hartree": energy, "ground_vector_sha256_numpy_v1": sha_array(vector),
            "normalization_residual": norm, "eigenpair_residual_hartree": residual,
            "H_sha256_numpy_v1": spec["H_sha256_numpy_v1"],
            "sector_indices_sha256_numpy_v1": spec["sector_indices_sha256_numpy_v1"],
            "sector_dimension": spec["sector_dimension"], "method": "original scipy.linalg.eigh driver=evd; saved source reused",
            "computed_in_original_process": True, "computed_on_resume": False, "reused": True,
            "historical_Z2_ground_used": False, "first_excitation_gap_hartree": None, "solver_seconds": None,
            "missing_scalar_status": "original_in_memory_gap_and_per_system_time_not_serialized",
            "nondegeneracy_gate": {"status": "passed_in_original_process_before_file_write",
                "tolerance_hartree": rule["ground_energy_ambiguity_tolerance_hartree"],
                "code": "review_response/run_hchain_truth_scoring.py:ground_point",
                "original_execution_commit": "e1cc452e11bb481f7275deaa9a769a7887da18a5",
                "witness": "byte-verified checked source, FAILURE counters and preserved post-gate ground NPZ"}}


def execute(root, *, preflight=False):
    started, before = utc(), time.perf_counter()
    auth = json.loads((root/DOC/"authorization.json").read_text())
    if str(root) != auth["worktree"] or git(root,"branch","--show-current").decode().strip() != auth["branch"]:
        raise PreparationError("same original runtime worktree and truth branch required")
    environment = fixed_environment(json.loads((root/"docs/second_study_v2/hchain_prediction_20261004/authorization.json").read_text()))
    prediction, source = resume_gate(root)
    runtime = preparation_gate(root)
    failure, preservation = stopped_gate(root)
    out = root/OUT
    boundary = ReadBoundary(root, allowed_reads(root, runtime), out)
    sys.addaudithook(boundary.hook)
    ledger, reads, stages = restore_ledger(failure), [], {}
    baseline_counts, baseline_timings = dict(ledger.counts), dict(ledger.timings)

    def resources():
        payload = ledger.payload()
        payload.pop("combined_H1_cost", None)
        payload["resume_counts"] = {key: value-baseline_counts.get(key,0) for key,value in payload["counts"].items()}
        payload["resume_timings_seconds"] = {key: value-baseline_timings.get(key,0.) for key,value in payload["timings_seconds"].items()}
        payload["original_process_peak_RSS_KiB"] = failure["resources"]["peak_RSS_KiB"]
        payload["maximum_across_processes_RSS_KiB"] = max(payload["peak_RSS_KiB"], payload["original_process_peak_RSS_KiB"])
        return {**payload, "scope": "cumulative same-run scorer costs with explicit incremental resume accounting",
                "previous_calibration_costs": "unchanged original prediction resource audit"}

    def access():
        payload = boundary.payload(reads)
        return {**payload, "truth_array_reads": ledger.counts["truth_array_reads"],
                "saved_ground_recovery_reads": ledger.counts["saved_ground_recovery_reads"],
                "ground_arrays_authorized_scorer_only": True,
                "original_known_source_read_denial_preserved": failure["access"]["denied_accesses"]}

    try:
        # Regression gate: the whole composed chain now runs under the *active* boundary.
        prediction, source = resume_gate(root)
        if preparation_gate(root) != runtime:
            raise PreparationError("original runtime changed at active-boundary preflight")
        stopped_gate(root)
        direct = helper(root)  # Source-only AST/byte gate, no direct calculation.
        method = json.loads((root/METHOD).read_text())
        plan = load_plan(root/PREP/"candidate_plan.csv")
        if boundary.denials:
            raise PreparationError("composed source/runtime access preflight denied")
        if preflight:
            print(json.dumps({"status":"resume_active_boundary_preflight_pass", "prediction_files":38,
                              "original_runtime_files":7, "saved_ground_files":3, "numerical_actions":0}), flush=True)
            return
        for name in ("RESUME_STARTED.json", "RESUME_FAILURE.json", "ground", "truth", "result", "checkpoints"):
            if (out/name).exists():
                raise PreparationError("resume already consumed or downstream output exists; no repeat")
        write_json(out/"RESUME_STARTED.json", {"utc":started, "stopped_publication_commit":STOP,
            "original_execution_commit":auth["original_execution_commit"], "prediction_commit":PREDICTION,
            "resume_execution_HEAD":source["execution_HEAD"], "same_output":True, "one_resume_only":True,
            "environment":environment, "ground_eigensolve_repeat":False})
        identity = prediction["input_identity"]
        sequence = [float.fromhex(value) for value in json.loads((root/OLD/"system_and_pf_contract.json").read_text())["PF"]["canonical_sequence_hex"]]
        with bounded_stage(ledger,"resume_input_and_component_preprocessing",1800):
            systems = load_inputs(root,identity,ledger,reads,sequence)
        private = out/".runtime"
        saved = {row["path"]:row for row in preservation["files"]}
        ground = {"prediction_commit":PREDICTION, "scoring_method_sha256":source["scoring_method_sha256"],
                  "source_origin_execution_commit":auth["original_execution_commit"], "systems":{}}
        with bounded_stage(ledger,"saved_ground_revalidation",1800):
            for system in ("H2","H4","H6"):
                name = f"{system}_ground.npz"
                record = recover_ground(private/name,systems[system]["adapter"].h.toarray(),identity[system],method,ledger)
                record["runtime_file"] = saved[name]
                ground["systems"][system] = record
        _, checkpoint_source = resume_gate(root)
        stopped_gate(root)
        files = bundle(out/"ground","ground.json","GROUND_FROZEN.json",ground,
            {"kind":"GROUND_FROZEN","utc":utc(),"new_ground_states_on_resume":0,"saved_ground_states_reused":3,
             "original_ground_solves":3,"prediction_commit":PREDICTION},checkpoint_source,access(),resources())
        stages["ground_commit"] = commit_stage(root,out/"ground",files,"Freeze preserved same-H grounds after authorized technical resume")
        verify_stage(root,out/"ground",stages["ground_commit"],"GROUND_FROZEN.json")
        print(json.dumps({"event":"GROUND_FROZEN","commit":stages["ground_commit"]}),flush=True)
        points = []
        with bounded_stage(ledger,"nine_coordinate_direct_gap_acquisition",1800):
            for system in ("H2","H4","H6"):
                spec = ground["systems"][system]
                verify_entries(private,[spec["runtime_file"]])
                with np.load(private/spec["runtime_file"]["path"],allow_pickle=False) as archive:
                    if set(archive.files) != {"ground_vector","energy"}:
                        raise PreparationError("ground runtime member set mismatch")
                    exact, energy = archive["ground_vector"].copy(), float(archive["energy"])
                ledger.counts["truth_array_reads"] += 1
                if sha_array(exact) != spec["ground_vector_sha256_numpy_v1"] or energy != spec["energy_hartree"]:
                    raise PreparationError("frozen ground hash/value mismatch")
                previous = None
                for row in [item for item in plan if item["system"] == system]:
                    build_started = time.perf_counter()
                    unitary = full_unitary(systems[system]["adapter"],row["time"],ledger)
                    ledger.timings["truth_full_PF_construction"] += time.perf_counter()-build_started
                    ledger.charge("direct_Schur_solves",9)
                    point, previous = direct(unitary,exact,energy,row["time"],row["K"],EPSILON,previous,1e-8)
                    ledger.charge("direct_truth_coordinates",9)
                    ledger.charge("target_phase_gaps",9)
                    ledger.counts["target_eigenpair_matrix_vector_residual_checks"] += 1
                    point = serial_truth(point)
                    point.update({"system":system,"candidate_id":row["candidate_id"],"time_hex":row["time_hex"],
                        "H_sha256_numpy_v1":identity[system]["H_sha256_numpy_v1"],
                        "ground_vector_sha256_numpy_v1":spec["ground_vector_sha256_numpy_v1"],
                        "phase_unwrap_basis":"principal_ground_relative_not_absolute_predictor_integer",
                        "computed":True,"reused":False,
                        "initial_or_continuation":"initial_exact_ground" if len(points)%3==0 else "previous_selected_vector"})
                    point["quality"] = truth_quality(point,method)
                    points.append(point)
                    write_json(out/"checkpoints"/f"{row['candidate_id']}.json",point)
                    print(json.dumps({"event":"DIRECT_FROZEN_POINT","candidate":row["candidate_id"],"quality":point["quality"]["status"]}),flush=True)
        verify_stage(root,out/"ground",stages["ground_commit"],"GROUND_FROZEN.json")
        _, checkpoint_source = resume_gate(root)
        if preparation_gate(root) != runtime:
            raise PreparationError("original input changed during truth acquisition")
        stopped_gate(root)
        truth = {"points":points,"ground_commit":stages["ground_commit"],"prediction_commit":PREDICTION,
            "ground_manifest_sha256":sha_file(out/"ground/manifest.json"),"scoring_method_sha256":source["scoring_method_sha256"],
            "coordinate_count":9,"new_direct_coordinates":9,"reused_coordinates":0,"nearest_or_interpolation":0,
            "new_anchors":0,"representation":"principal_relative_signed_shift","new_gap_used_to_modify_width":False}
        files = bundle(out/"truth","truth.json","TRUTH_FROZEN.json",truth,
            {"kind":"TRUTH_FROZEN","utc":utc(),"coordinates":9,**stages},checkpoint_source,access(),resources())
        stages["truth_commit"] = commit_stage(root,out/"truth",files,"Freeze nine H-chain direct truth and phase gaps before immutable scoring")
        verify_stage(root,out/"truth",stages["truth_commit"],"TRUTH_FROZEN.json")
        print(json.dumps({"event":"TRUTH_FROZEN","commit":stages["truth_commit"]}),flush=True)
        verify_stage(root,out/"ground",stages["ground_commit"],"GROUND_FROZEN.json")
        prediction, checkpoint_source = resume_gate(root)
        with bounded_stage(ledger,"immutable_arithmetic_scoring",1800):
            scored = score_all(prediction,json.loads((out/"truth/truth.json").read_text()),json.loads((out/"ground/ground.json").read_text()))
        ledger.counts["immutable_scoring_runs"] += 1
        for key, required in (("full_H_ground_solves",3),("ground_revalidation_H_matvecs",3),
                              ("full_pf_unitary_builds",9),("direct_Schur_solves",9),
                              ("direct_truth_coordinates",9),("target_phase_gaps",9),("immutable_scoring_runs",1)):
            if ledger.counts[key] != required:
                raise PreparationError("same-run count gate mismatch")
        forbidden = ("candidate_cheap_pf_actions","candidate_h_exponential_actions","m1_pf_vector_actions",
                     "m1_h_matvecs","Arnoldi_chains","GPU_queries","GPU_allocations","GPU_kernels")
        if any(ledger.counts[key] for key in forbidden) or "cupy" in sys.modules or boundary.denials:
            raise PreparationError("calibration/GPU/access gate failed")
        scored.update({"stage_commits":stages,"prediction_commit":PREDICTION,"technical_resume":True,
                       "ground_metadata_missing_fields":"first_excitation_gap and original per-system solve time unavailable"})
        result = out/"result"
        result.mkdir()
        write_json(result/"scoring.json",scored)
        write_csv(result/"coordinate_scoring.csv",scored["coordinate_scores"])
        write_csv(result/"decision_scoring.csv",scored["decision_scores"])
        write_json(result/"COMPLETE.json",{"status":scored["status"],"utc":utc(),"prediction_commit":PREDICTION,
            **stages,"evidence_axes":scored["evidence_axes"],"systems":3,"coordinates":9,
            "next_stage_authorized":False,"push_authorized":False,"prediction_modified":False,
            "original_stop_preserved":True,"ground_eigensolves_repeated":0})
        write_json(result/"source_audit.json",checkpoint_source)
        write_json(result/"access_audit.json",access())
        cost = resources()
        cost.update({"started_utc":started,"finished_utc":utc(),"resume_process_body_seconds":time.perf_counter()-before})
        write_json(result/"resource_audit.json",cost)
        names = ("scoring.json","coordinate_scoring.csv","decision_scoring.csv","COMPLETE.json",
                 "source_audit.json","access_audit.json","resource_audit.json")
        write_json(result/"manifest.json",{"manifest_self_excluded":True,"files":[
            {"path":name,"bytes":(result/name).stat().st_size,"sha256":sha_file(result/name)} for name in names]})
        resume_gate(root)
        preparation_gate(root)
        stopped_gate(root)
        print(json.dumps({"status":scored["status"],"evidence_axes":scored["evidence_axes"],
                          "branch_correct":scored["branch_correct"],"width_covered":scored["width_covered"],
                          "result_manifest_sha256":sha_file(result/"manifest.json")}),flush=True)
    except BaseException as error:
        if not preflight and (out/"RESUME_STARTED.json").exists() and not (out/"RESUME_FAILURE.json").exists():
            write_json(out/"RESUME_FAILURE.json",{"status":"hchain_resume_failure_stop","utc":utc(),
                "error_type":type(error).__name__,"message":str(error),"stage_commits":stages,
                "resources":resources(),"access":access(),"further_resume_authorized":False})
        raise
    finally:
        boundary.enabled = False


def test_log(root, directory):
    if directory.exists():
        raise PreparationError("new test-log destination required")
    env = fixed_environment(json.loads((root/"docs/second_study_v2/hchain_prediction_20261004/authorization.json").read_text()))
    command = [sys.executable,"-m","pytest","-q","-rs","review_tests/test_hchain_truth_scoring_resume.py",
        "review_tests/test_hchain_truth_scoring.py","review_tests/test_hchain_prediction_phase.py",
        "review_tests/test_hchain_input_reference_preparation.py","-p","no:cacheprovider"]
    started, before = utc(), time.perf_counter()
    done = subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=1800)
    log = done.stdout+done.stderr
    directory.mkdir(parents=True)
    (directory/"pytest.log").write_text(log)
    counts = {key:sum(int(value) for value in re.findall(rf"(\d+) {key}\b",log)) for key in ("passed","failed","skipped","error","errors")}
    write_json(directory/"audit.json",{"command":command,"environment":env,"started_utc":started,"finished_utc":utc(),
        "wall_seconds":time.perf_counter()-before,"exit_code":done.returncode,"counts":counts,
        "log_sha256":sha_file(directory/"pytest.log"),"scope":"relevant synthetic and active-boundary source tests; no molecular acquisition"})
    print(log,end="")
    if done.returncode or counts["passed"] == 0 or any(counts[key] for key in ("failed","skipped","error","errors")):
        raise PreparationError("resume focused test gate failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--seal-source",action="store_true")
    modes.add_argument("--preflight",action="store_true")
    modes.add_argument("--test-log-dir",type=Path)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if args.seal_source:
        seal(root)
    elif args.test_log_dir:
        test_log(root,args.test_log_dir.resolve())
    else:
        execute(root,preflight=args.preflight)


if __name__ == "__main__":
    main()
