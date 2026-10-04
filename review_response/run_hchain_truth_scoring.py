"""One same-H ground/truth acquisition, Git freezes, then immutable scoring."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np
from scipy.linalg import eigh, schur

from trotterlib.component_sector_pf import component_exponential
from review_response.hchain_input_reference_preparation import (
    Ledger, PreparationError, bounded_stage, checked_functions, sha_array, sha_file, write_json,
)
from review_response.hchain_prediction_phase import (
    OLD, PREP, PREP_DOC, ReadBoundary, preparation_gate, load_plan, verify_entries,
)
from review_response.hchain_selective_calibration_schedule import EPSILON, budget
from review_response.run_hchain_prediction_phase import fixed_environment, load_inputs
from review_response.hchain_truth_scoring import (
    DOC, METHOD, PREDICTION, PRED_ROOT, SOURCES, bundle, commit_stage, git,
    score_all, seal_source, source_gate, truth_quality, verify_stage,
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def helper(root):
    return checked_functions(root/"review_response/_pf_first_study_s0_exact_time_scoring_base.py",
        "a4b32ba8456d74acb072601b4dee0f3a6162be5d591ff4d79f08378f32250619",
        ("_phase_distance", "direct_branch_point"),
        {"schur": schur, "practical": SimpleNamespace(_cost=lambda t,e,k,eps: budget(t,e,k))})["direct_branch_point"]


def ground_point(h, spec, method, ledger):
    ledger.charge("full_H_ground_solves", 3)
    before = time.perf_counter()
    values, vectors = eigh(h, driver="evd", check_finite=True)
    elapsed = time.perf_counter()-before
    energy, vector = float(values[0]), np.asarray(vectors[:,0], dtype=np.complex128)
    rule = method["ground_solver"]
    gap = float(values[1]-values[0])
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(vector)):
        raise PreparationError("same-H ground solve nonfinite")
    if gap <= rule["ground_energy_ambiguity_tolerance_hartree"]:
        raise PreparationError("same-H ground indeterminate: degenerate at frozen tolerance")
    norm = abs(float(np.linalg.norm(vector))-1.)
    ledger.counts["ground_verification_H_matvecs"] += 1
    residual = float(np.linalg.norm(h@vector-energy*vector))
    if norm > rule["normalization_absolute_maximum"] or residual > rule["eigenpair_residual_maximum_hartree"]:
        raise PreparationError("same-H ground norm/residual gate failed")
    return {"energy_hartree": energy, "first_excitation_gap_hartree": gap,
            "ground_vector_sha256_numpy_v1": sha_array(vector), "normalization_residual": norm,
            "eigenpair_residual_hartree": residual, "solver_seconds": elapsed,
            "H_sha256_numpy_v1": spec["H_sha256_numpy_v1"],
            "sector_indices_sha256_numpy_v1": spec["sector_indices_sha256_numpy_v1"],
            "sector_dimension": spec["sector_dimension"], "method": "scipy.linalg.eigh driver=evd",
            "computed": True, "reused": False, "historical_Z2_ground_used": False}, vector


def full_unitary(adapter, t, ledger):
    ledger.charge("full_pf_unitary_builds", 9)
    unitary = np.eye(adapter.h.shape[0], dtype=np.complex128)
    gates = {}
    for index, weight in adapter.steps:
        key = (int(index), float(weight))
        if key not in gates:
            gates[key] = component_exponential(adapter.spectra[index], float(t)*float(weight))
            ledger.counts["truth_component_gate_materializations"] += 1
        unitary = gates[key] @ unitary
        ledger.counts["truth_sparse_matrix_dense_matrix_multiplies"] += 1
        ledger.check_memory()
    if not np.all(np.isfinite(unitary)):
        raise PreparationError("full PF finite gate failed before Schur")
    return unitary


def serial_truth(point):
    result = dict(point)
    value = result["selected_eigenvalue"]
    result["selected_eigenvalue"] = [float(value.real),float(value.imag)]
    return result


def write_csv(path, rows):
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, keys, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value,sort_keys=True) if isinstance(value,(list,dict)) else value
                             for key,value in row.items()})


def execute(root):
    body_started, started_utc = time.perf_counter(), utc()
    auth = json.loads((root/DOC/"authorization.json").read_text())
    if str(root) != auth["worktree"] or git(root,"branch","--show-current").decode().strip() != auth["branch"]:
        raise PreparationError("same runtime worktree and scoring branch required")
    environment = fixed_environment(json.loads((root/"docs/second_study_v2/hchain_prediction_20261004/authorization.json").read_text()))
    prediction, source = source_gate(root)
    runtime = preparation_gate(root)
    method = json.loads((root/METHOD).read_text())
    out = root/auth["output_root"]
    if out.exists():
        raise PreparationError("truth run already started; no repeat or replacement output")
    inherited = json.loads((root/PREP_DOC/"implementation_manifest.json").read_text())
    allowed = [root/row["path"] for row in inherited["files"]] + [root/name for name in SOURCES]
    allowed += [root/DOC/"implementation_manifest.json",root/PREP_DOC/"implementation_manifest.json"]
    allowed += list((root/OLD).glob("*"))
    allowed += list((root/"docs/second_study_v2/hchain_prediction_20261004").glob("*"))
    allowed += [path for path in (root/PREP).iterdir() if path.is_file()]
    allowed += [root/PREP/".runtime"/row["path"] for row in runtime["files"]]
    allowed += [root/name for name in git(root,"ls-tree","-r","--name-only",PREDICTION,PRED_ROOT).decode().splitlines()]
    boundary = ReadBoundary(root,allowed,out)
    sys.addaudithook(boundary.hook)
    ledger, reads, stages = Ledger(), [], {}
    out.mkdir()
    write_json(out/"STARTED.json", {"utc": started_utc,"prediction_commit": PREDICTION,
                                  "scorer_execution_HEAD": source["execution_HEAD"],"one_run_only": True})
    def resources():
        payload = ledger.payload()
        payload.pop("combined_H1_cost",None)
        return {**payload,"scope":"scorer costs only; no new calibration actions",
                "previous_calibration_costs":"unchanged original prediction resource audit"}
    def access():
        payload = boundary.payload(reads)
        payload["truth_array_reads"] = ledger.counts["truth_array_reads"]
        payload["ground_arrays_authorized_scorer_only"] = True
        return payload
    try:
        identity = prediction["input_identity"]
        plan = load_plan(root/PREP/"candidate_plan.csv")
        sequence = [float.fromhex(value) for value in json.loads((root/OLD/"system_and_pf_contract.json").read_text())["PF"]["canonical_sequence_hex"]]
        with bounded_stage(ledger,"scorer_input_and_component_preprocessing",1800):
            systems = load_inputs(root,identity,ledger,reads,sequence)
        ground = {"prediction_commit": PREDICTION,"scoring_method_sha256": auth["scoring_method_sha256"],"systems": {}}
        private = out/".runtime"
        private.mkdir()
        with bounded_stage(ledger,"same_H_ground_acquisition",1800):
            for system in ("H2","H4","H6"):
                record, vector = ground_point(systems[system]["adapter"].h.toarray(),identity[system],method,ledger)
                path = private/f"{system}_ground.npz"
                np.savez_compressed(path,ground_vector=vector,energy=np.asarray(record["energy_hartree"]))
                record["runtime_file"] = {"path":path.name,"bytes":path.stat().st_size,"sha256":sha_file(path)}
                ground["systems"][system] = record
        _, checkpoint_source = source_gate(root)
        files = bundle(out/"ground","ground.json","GROUND_FROZEN.json",ground,
            {"kind":"GROUND_FROZEN","utc":utc(),"new_ground_states":3,"prediction_commit":PREDICTION},
            checkpoint_source,access(),resources())
        stages["ground_commit"] = commit_stage(root,out/"ground",files,"Freeze three same-H ground sources before direct truth")
        verify_stage(root,out/"ground",stages["ground_commit"],"GROUND_FROZEN.json")
        print(json.dumps({"event":"GROUND_FROZEN","commit":stages["ground_commit"]}),flush=True)
        direct = helper(root)
        points = []
        with bounded_stage(ledger,"nine_coordinate_direct_gap_acquisition",1800):
            for system in ("H2","H4","H6"):
                spec = ground["systems"][system]
                verify_entries(private,[spec["runtime_file"]])
                with np.load(private/spec["runtime_file"]["path"],allow_pickle=False) as archive:
                    if set(archive.files) != {"ground_vector","energy"}:
                        raise PreparationError("ground runtime member set mismatch")
                    exact = archive["ground_vector"].copy()
                    energy = float(archive["energy"])
                ledger.counts["truth_array_reads"] += 1
                if sha_array(exact) != spec["ground_vector_sha256_numpy_v1"] or energy != spec["energy_hartree"]:
                    raise PreparationError("frozen ground source hash/value mismatch")
                previous = None
                for row in [row for row in plan if row["system"] == system]:
                    before = time.perf_counter()
                    unitary = full_unitary(systems[system]["adapter"],row["time"],ledger)
                    ledger.timings["truth_full_PF_construction"] += time.perf_counter()-before
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
        _, checkpoint_source = source_gate(root)
        if preparation_gate(root) != runtime:
            raise PreparationError("original input changed during truth acquisition")
        truth = {"points":points,"ground_commit":stages["ground_commit"],"prediction_commit":PREDICTION,
                 "ground_manifest_sha256":sha_file(out/"ground/manifest.json"),"scoring_method_sha256":auth["scoring_method_sha256"],
                 "coordinate_count":9,"new_direct_coordinates":9,"reused_coordinates":0,
                 "nearest_or_interpolation":0,"new_anchors":0,"representation":"principal_relative_signed_shift",
                 "new_gap_used_to_modify_width":False}
        files = bundle(out/"truth","truth.json","TRUTH_FROZEN.json",truth,
            {"kind":"TRUTH_FROZEN","utc":utc(),"coordinates":9,**stages},checkpoint_source,access(),resources())
        stages["truth_commit"] = commit_stage(root,out/"truth",files,"Freeze nine H-chain direct truth and phase gaps before scoring")
        verify_stage(root,out/"truth",stages["truth_commit"],"TRUTH_FROZEN.json")
        print(json.dumps({"event":"TRUTH_FROZEN","commit":stages["truth_commit"]}),flush=True)
        # Scoring starts only after both actual Git freeze barriers pass.
        verify_stage(root,out/"ground",stages["ground_commit"],"GROUND_FROZEN.json")
        prediction, checkpoint_source = source_gate(root)
        ground = json.loads((out/"ground/ground.json").read_text())
        truth = json.loads((out/"truth/truth.json").read_text())
        with bounded_stage(ledger,"immutable_arithmetic_scoring",1800):
            scored = score_all(prediction,truth,ground)
        if "cupy" in sys.modules or boundary.denials:
            raise PreparationError("CPU/access gate failed")
        for key,required in (("full_H_ground_solves",3),("full_pf_unitary_builds",9),("direct_Schur_solves",9),("direct_truth_coordinates",9),("target_phase_gaps",9)):
            if ledger.counts[key] != required:
                raise PreparationError("ground/direct count gate mismatch")
        if any(ledger.counts[key] for key in ("candidate_cheap_pf_actions","candidate_h_exponential_actions","m1_pf_vector_actions","m1_h_matvecs","Arnoldi_chains","GPU_queries","GPU_allocations","GPU_kernels")):
            raise PreparationError("unauthorized calibration/GPU action")
        scored["stage_commits"] = stages
        scored["prediction_commit"] = PREDICTION
        result = out/"result"
        result.mkdir()
        write_json(result/"scoring.json",scored)
        write_csv(result/"coordinate_scoring.csv",scored["coordinate_scores"])
        write_csv(result/"decision_scoring.csv",scored["decision_scores"])
        write_json(result/"COMPLETE.json",{"status":scored["status"],"utc":utc(),"prediction_commit":PREDICTION,
            **stages,"evidence_axes":scored["evidence_axes"],"systems":3,"coordinates":9,
            "next_stage_authorized":False,"push_authorized":False,"prediction_modified":False})
        write_json(result/"source_audit.json",checkpoint_source)
        write_json(result/"access_audit.json",access())
        cost = resources()
        cost["process_body_elapsed_before_final_write_seconds"] = time.perf_counter()-body_started
        cost["started_utc"],cost["finished_utc"] = started_utc,utc()
        write_json(result/"resource_audit.json",cost)
        names = ("scoring.json","coordinate_scoring.csv","decision_scoring.csv","COMPLETE.json","source_audit.json","access_audit.json","resource_audit.json")
        write_json(result/"manifest.json",{"manifest_self_excluded":True,"files":[
            {"path":name,"bytes":(result/name).stat().st_size,"sha256":sha_file(result/name)} for name in names]})
        source_gate(root)
        preparation_gate(root)
        print(json.dumps({"status":scored["status"],"evidence_axes":scored["evidence_axes"],
                          "branch_correct":scored["branch_correct"],"width_covered":scored["width_covered"],
                          "result_manifest_sha256":sha_file(result/"manifest.json")}),flush=True)
    except BaseException as error:
        write_json(out/"FAILURE.json",{"status":"hchain_truth_or_scoring_failure_stop","utc":utc(),
            "error_type":type(error).__name__,"message":str(error),"stage_commits":stages,
            "resources":resources(),"access":access(),"no_rescue_or_rerun_authorized":True})
        raise
    finally:
        boundary.enabled = False


def test_log(root,directory):
    if directory.exists():
        raise PreparationError("test log directory exists")
    contract = json.loads((root/"docs/second_study_v2/hchain_prediction_20261004/authorization.json").read_text())
    env = fixed_environment(contract)
    command = [sys.executable,"-m","pytest","-q","-rs","review_tests/test_hchain_truth_scoring.py",
               "review_tests/test_hchain_prediction_phase.py","review_tests/test_hchain_input_reference_preparation.py","-p","no:cacheprovider"]
    started, before = utc(),time.perf_counter()
    completed = subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=1800)
    finished,elapsed = utc(),time.perf_counter()-before
    directory.mkdir(parents=True)
    log = completed.stdout+completed.stderr
    (directory/"pytest.log").write_text(log)
    counts = {key:sum(int(value) for value in re.findall(rf"(\d+) {key}\b",log)) for key in ("passed","failed","skipped","error","errors")}
    write_json(directory/"audit.json",{"command":command,"environment":env,"started_utc":started,
        "finished_utc":finished,"wall_seconds":elapsed,"exit_code":completed.returncode,"counts":counts,
        "log_sha256":sha_file(directory/"pytest.log"),"scope":"relevant synthetic/source/scoring tests; no extra molecular acquisition or GPU"})
    print(log,end="")
    if completed.returncode or counts["passed"] == 0 or any(counts[key] for key in ("failed","skipped","error","errors")):
        raise PreparationError("scorer focused test gate failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal-source",action="store_true")
    parser.add_argument("--test-log-dir",type=Path)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if args.seal_source and args.test_log_dir:
        parser.error("choose one diagnostic mode")
    if args.seal_source:
        seal_source(root)
    elif args.test_log_dir:
        test_log(root,args.test_log_dir.resolve())
    else:
        execute(root)


if __name__ == "__main__":
    main()
