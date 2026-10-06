#!/usr/bin/env python3
"""Fresh-allocation CPU workers, truth commit barrier, immutable scoring, publication."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import numpy as np

import prospective_truth_scoring as s
import prospective_input_reference as prep
import prospective_candidate_prediction as p
import run_prospective_candidate_prediction as pred_runner

TESTS = ("review_tests/test_prospective_input_reference.py", "review_tests/test_prospective_candidate_prediction.py",
         "review_tests/test_prospective_truth_scoring.py")


def paths(root):
    output = root/s.OUTPUT
    private = output/".private"
    return output, private


def disk_roots(root, runtime):
    original_p3 = runtime.parent
    repo = root.parents[1]
    prediction_root = repo/".worktrees/gpu-pf-study2-prospective-prediction-20261006"
    return [original_p3, original_p3.parent/"prospective_preparation_control_20261005",
            prediction_root/p.OUTPUT, root/p.PREP, root/p.OUTPUT, root/s.OUTPUT]


def allocated(root, runtime, allocation):
    if allocation is None or runtime is None or runtime.name != ".runtime" or runtime.is_symlink():
        raise prep.PreparationError("fresh allocation and original P3 runtime required")
    if runtime.parent.name != Path(p.PREP).name or (runtime.parent/"INPUT_FROZEN.json").read_bytes() != (root/p.PREP/"INPUT_FROZEN.json").read_bytes():
        raise prep.PreparationError("original P3 runtime identity differs; no regeneration")
    data = s.allocation_gate(prep.read(allocation), root/s.OUTPUT, allocation.parent, disk_roots(root, runtime))
    s.resource_guard(data)
    return data


def one_shot(path, phase):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump({"phase": phase, "created_UTC": prep.utc(), "scientific_retry": False, "technical_retries_used": 0}, stream)


def tests(root, private, label):
    path = private/f"{label}_tests.json"
    if path.exists():
        raise prep.PreparationError("focused test record exists; preserve it")
    cmd = [sys.executable, "-m", "pytest", "-q", "-rs", *TESTS, "-p", "no:cacheprovider"]
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=600)
    log = result.stdout+result.stderr
    name = f"{label}_tests.log"
    (private/name).write_text(log)
    match = re.search(r"(\d+) passed", log)
    record = {"label": label, "HEAD": p.git(root, "rev-parse", "HEAD").decode().strip(), "created_UTC": prep.utc(),
              "command": ["${P3_PYTHON}", *cmd[1:]], "returncode": result.returncode,
              "passed": int(match[1]) if match else 0,
              "failures_or_skips": bool(re.search(r"\b\d+ (?:failed|skipped|errors?|xfailed|xpassed)\b", log)),
              "test_sources": [{"path": f, "sha256": prep.sha_file(root/f)} for f in TESTS],
              "log": name, "log_sha256": prep.sha_file(private/name), "molecular_truth_tests": 0}
    prep.write(path, record)
    passed_tests(root, private, label)
    print(log, end="", flush=True)
    return record


def passed_tests(root, private, label):
    record = prep.read(private/f"{label}_tests.json")
    if record["label"] != label or record["returncode"] != 0 or record["failures_or_skips"] or record["passed"] <= 102:
        raise prep.PreparationError("focused truth/scorer and inherited tests require fail/skip 0")
    if record["HEAD"] != p.git(root, "rev-parse", "HEAD").decode().strip():
        raise prep.PreparationError("focused tests must cover current source HEAD")
    if prep.sha_file(private/record["log"]) != record["log_sha256"]:
        raise prep.PreparationError("focused test log hash mismatch")
    for row in record["test_sources"]:
        if prep.sha_file(root/row["path"]) != row["sha256"]:
            raise prep.PreparationError("tested source modified")
    return record


def preflight(root, private, runtime, allocation):
    prediction, protocol, specs, plan, identities, source = s.source_gate(root)
    data = allocated(root, runtime, allocation)
    test = passed_tests(root, private, "pre")
    actual = pred_runner.environment(identities)
    runtime_files = pred_runner.runtime_gate(runtime, identities)
    started = time.monotonic()
    loaded = []
    for cid, identity in identities.items():
        if cid in p.TERMINAL:
            continue
        s.resource_guard(data)
        h, state, groups = prep.load_input(identity, runtime/cid)
        group_count = sum(1 for _ in groups)
        if group_count != identity["group_count"]:
            raise prep.PreparationError("full ordered group identity incomplete")
        loaded.append({"condition_id": cid, "H_dense_numpy_v1": identity["H_dense_numpy_v1"],
                       "CISD_numpy_v1": identity["CISD_numpy_v1"], "sector_indices_numpy_v1": identity["sector_indices_numpy_v1"],
                       "input_identity_sha256": prep.sha_file(root/p.PREP/"conditions"/cid/"input_identity.json"),
                       "ordered_groups": group_count, "runtime_files": len(identity["runtime_files"])})
        del h, state, groups
        gc.collect()
        status(private, "prospective_pre_truth_verification", validated_conditions=len(loaded), science_actions=0)
    gate = {"status": "PASS", "created_UTC": prep.utc(), "source": source,
            "execution_HEAD": p.git(root, "rev-parse", "HEAD").decode().strip(),
            "prediction_sha256": s.PREDICTION_SHA, "attempted_conditions": 16, "ready_conditions": 13,
            "frozen_coordinates": 39, "truth_opened": False, "frozen_rules_modified": False,
            "terminal_runtime_reads": 0, "runtime_files_verified": len(runtime_files), "inputs": loaded,
            "environment": actual, "fresh_allocation_sha256": prep.sha_file(allocation),
            "allocation_authority": data["authority"], "starts_UTC": data["starts_UTC"], "expires_UTC": data["expires_UTC"],
            "approved_output_root": "${WORKTREE}/"+s.OUTPUT, "focused_tests": test,
            "validation_wall_seconds": time.monotonic()-started, "science_actions": 0}
    if (private/"pre_truth_gate.json").exists():
        raise prep.PreparationError("pre-truth gate exists; do not overwrite")
    prep.write(private/"pre_truth_gate.json", gate)
    return gate


def status(private, state, **fields):
    prep.write(private/"run_status.json", {"status": state, "updated_UTC": prep.utc(), "coordinator_pid": os.getpid(), **fields})


def worker(root, private, runtime, allocation, cid):
    prediction, protocol, specs, plan, identities, source = s.source_gate(root)
    if cid in p.TERMINAL or cid not in identities:
        raise prep.PreparationError("terminal condition cannot acquire ground/truth")
    data = allocated(root, runtime, allocation)
    gate = prep.read(private/"pre_truth_gate.json")
    if gate["status"] != "PASS" or gate["truth_opened"] is not False or gate["execution_HEAD"] != p.git(root, "rev-parse", "HEAD").decode().strip() or gate["fresh_allocation_sha256"] != prep.sha_file(allocation):
        raise prep.PreparationError("pre-truth execution/hash/allocation gate differs")
    directory = private/"workers"/cid
    one_shot(directory/"STARTED.json", "condition_truth")
    identity = identities[cid]
    allowed = [p.safe_member(runtime/cid, r["path"]) for r in identity["runtime_files"]]+[root/s.HELPER]
    audit = p.ReadBoundary(root, runtime, allowed, root/s.OUTPUT)
    sys.addaudithook(audit.hook)
    last_disk = [0.]
    def guard():
        if datetime.now(timezone.utc) >= datetime.fromisoformat(data["expires_UTC"]):
            raise prep.PreparationError("fresh allocation deadline reached")
        if time.monotonic()-last_disk[0] > 5:
            s.resource_guard(data)
            last_disk[0] = time.monotonic()
    ledger = s.TruthLedger(data["worker_rss_limit_bytes"], directory/"action_checkpoint.json", guard)
    coordinates = [r for r in p.coordinate_rows(plan) if r["condition_id"] == cid]
    if [r["ratio"] for r in coordinates] != [.8, 1., 1.2] or coordinates != sorted(coordinates, key=lambda r:r["time"]):
        raise prep.PreparationError("condition truth must use three ascending frozen times")
    begin = time.monotonic()
    def phase(name, coordinate=None, coordinate_start=None):
        prep.write(directory/"current_phase.json", {"stage": name, "updated_UTC": prep.utc(),
                   "coordinate_id": None if coordinate is None else coordinate["coordinate_id"],
                   "coordinate_started_UTC": coordinate_start, "completed_coordinates": len(points),
                   "counts": dict(ledger.counts)})
    points, ground = [], None
    try:
        with prep.bounded_process(ledger, min(data["worker_wall_seconds"], prep.remaining_worker_wall(data))):
            phase("input_validation")
            h, state, groups = prep.load_input(identity, runtime/cid)
            ledger.counts["input_cache_bytes_verified"] += sum((runtime/cid/r["path"]).stat().st_size for r in identity["runtime_files"])
            # Validate/build all inherited groups before the first ground solve.
            phase("group_component_preprocessing")
            clock = time.perf_counter()
            adapter = prep.ReferenceAdapter(h, groups, [float.fromhex(v) for v in identity["PF_sequence_hex"]], ledger)
            ledger.timings["group_component_preprocessing"] += time.perf_counter()-clock
            phase("same_H_ground")
            ground, exact = s.ground_point(h, identity, protocol["truth_future"], ledger)
            if exact is None:
                points = [s.missing_point(c, "same_H_ground_indeterminate") for c in coordinates]
            else:
                np.savez_compressed(directory/"ground_runtime.npz", ground_vector=exact, energy=np.asarray(ground["energy_hartree"]))
                ground["private_runtime_sha256"] = prep.sha_file(directory/"ground_runtime.npz")
                direct = s.direct_helper(root)
                previous, broken = None, False
                for coordinate in coordinates:
                    if broken:
                        points.append(s.missing_point(coordinate, "continuation_undefined_after_indeterminate_branch"))
                        continue
                    coordinate_start = prep.utc()
                    phase("full_PF", coordinate, coordinate_start)
                    clock = time.monotonic()
                    unitary = s.full_unitary(adapter, coordinate["time"], ledger)
                    phase("complex_Schur", coordinate, coordinate_start)
                    ledger.charge("direct_Schur_solves")
                    point, vector = direct(unitary, exact, ground["energy_hartree"], coordinate["time"],
                                           coordinate["K"], protocol["resource"]["epsilon_E"], previous,
                                           protocol["truth_future"]["phase_cluster_ambiguity_rad"])
                    elapsed = time.monotonic()-clock
                    if elapsed > data["direct_coordinate_wall_seconds"]:
                        raise prep.PreparationError("direct coordinate wall cap reached")
                    quality = s.truth_quality(point, protocol["truth_future"])
                    eigenvalue = point["selected_eigenvalue"]
                    point["selected_eigenvalue"] = [float(eigenvalue.real), float(eigenvalue.imag)]
                    nonfinite = []
                    point = p.finite_json(point, nonfinite)
                    point.update({**coordinate, "attempted": True, "quality": quality,
                                  "status": quality["status"], "ground_vector_numpy_v1": ground["ground_vector_numpy_v1"],
                                  "H_dense_numpy_v1": identity["H_dense_numpy_v1"], "sector_indices_numpy_v1": identity["sector_indices_numpy_v1"],
                                  "input_identity_sha256": next(r["input_identity_sha256"] for r in gate["inputs"] if r["condition_id"] == cid), "PF_sequence_hex": identity["PF_sequence_hex"],
                                  "ordered_pauli_groups_sha256": identity["ordered_pauli_groups_sha256"],
                                  "removed_scalar_hartree": identity["removed_scalar_hartree"],
                                  "coordinate_wall_seconds": elapsed, "nonfinite_fields": nonfinite,
                                  "selection_anchor": "same_H_ground" if previous is None else "previous_selected_PF_vector",
                                  "predictor_unwrap_rescue": False, "new_gap_eigensolves": 0})
                    ledger.counts["target_phase_gap_diagnostics"] += 1
                    ledger.timings["direct_Schur"] += point["timing_seconds"]["schur"]
                    ledger.timings["direct_unitarity_verification"] += point["timing_seconds"]["unitarity"]
                    points.append(point)
                    previous = vector if quality["physical_branch_valid"] else None
                    broken = not quality["physical_branch_valid"]
                    np.savez_compressed(directory/"last_selected_vector.npz", selected_PF_vector=vector)
                    prep.write(directory/"progress.json", {"ground": ground, "points": points, "resource": ledger.payload()})
                    del unitary, vector
                    gc.collect()
                    ledger.check_memory()
            phase("condition_complete")
        access = audit.payload()
        access.pop("truth_array_reads", None)
        access.update({"historical_truth_array_reads": 0, "newly_generated_ground_runtime_file_reads": 0,
                       "new_ground_vector_used_in_memory": ground["status"] == "same_H_ground_valid",
                       "truth_worker_prediction_values_used_for_selection": False})
        record = {"condition_id": cid, "condition": identity["condition"], "ground": ground, "points": points,
                  "status": "truth_complete_valid" if all(r["quality"]["physical_branch_valid"] for r in points) else "truth_indeterminate",
                  "resource": {**ledger.payload(), "condition_wall_seconds": time.monotonic()-begin,
                               "worker_rss_cap_bytes": data["worker_rss_limit_bytes"], "BLAS_threads": 1}, "access": access}
        prep.write(directory/"result.json", record)
    except BaseException as error:
        audit.enabled = False
        prep.write(directory/"STOPPED.json", {"reason": str(error), "ground": ground, "points": points,
                                              "counts": dict(ledger.counts), "scientific_retry": False})
        raise
    finally:
        audit.enabled = False


def rss(pid):
    try:
        text = Path(f"/proc/{pid}/status").read_text()
        match = re.search(r"^VmRSS:\s+(\d+) kB", text, re.M)
        return 0 if match is None else int(match[1])*1024
    except FileNotFoundError:
        return 0


def stop_owned(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def root_preservation(root, private):
    repo = root.parents[1]
    original = prep.read(private/"root_preservation_baseline.json")
    actual = {"HEAD": p.git(repo,"rev-parse","HEAD").decode().strip(), "branch": p.git(repo,"branch","--show-current").decode().strip(),
              "index_sha256": hashlib.sha256((repo/".git/index").read_bytes()).hexdigest(),
              "tracked_edits": {n:prep.sha_file(repo/n) for n in p.git(repo,"diff","--name-only").decode().splitlines()},
              "cached_diff_sha256": hashlib.sha256(p.git(repo,"diff","--cached","--binary")).hexdigest()}
    result = {k: actual[k] == value for k,value in original.items()}
    if not all(result.values()):
        raise prep.PreparationError("unrelated root preservation gate failed")
    return result


def publish(root, commit, private):
    branch = p.check_remote(root)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_SSH_COMMAND="ssh -oBatchMode=yes")
    cmd = ["git","-C",str(root),"push","origin",f"{commit}:refs/heads/{branch}"]
    push = subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=120)
    (private/"push.log").write_text(push.stdout+push.stderr)
    result = {"push_returncode":push.returncode,"branch":branch,"commit":commit,"remote_SHA_verified":False,
              "push_command":'git -C "'+str(root)+'" push origin '+commit+':refs/heads/'+branch}
    if push.returncode == 0:
        remote = subprocess.run(["git","-C",str(root),"ls-remote","origin",f"refs/heads/{branch}"],capture_output=True,text=True,env=env,timeout=120)
        fields = remote.stdout.split()
        if remote.returncode == 0 and fields and fields[0] == commit:
            fetched = subprocess.run(["git","-C",str(root),"fetch","--no-tags","origin",f"refs/heads/{branch}"],capture_output=True,text=True,env=env,timeout=120)
            result["remote_SHA_verified"] = fetched.returncode == 0 and p.git(root,"rev-parse","FETCH_HEAD").decode().strip() == commit
    prep.write(private/"publication_status.json",result)
    return result


def execute(root, private, runtime, allocation, do_push):
    prediction, protocol, specs, plan, identities, source = s.source_gate(root)
    data = allocated(root, runtime, allocation)
    if not (private/"pre_truth_gate.json").exists():
        preflight(root, private, runtime, allocation)
    gate = prep.read(private/"pre_truth_gate.json")
    passed_tests(root, private, "pre")
    if gate["execution_HEAD"] != p.git(root,"rev-parse","HEAD").decode().strip() or gate["fresh_allocation_sha256"] != prep.sha_file(allocation):
        raise prep.PreparationError("pre-truth gate cannot be reused for a different execution")
    one_shot(private/"EXECUTION_STARTED.json", "truth_scoring")
    ready = [cid for cid in identities if cid not in p.TERMINAL]
    pending, running, completed = list(ready), {}, []
    cpus = sorted(os.sched_getaffinity(0))[:int(data["workers"])]
    max_worker_rss, max_total_rss, last_report, last_disk = 0, 0, 0., 0.
    started = time.monotonic()
    try:
        while pending or running:
            while pending and len(running)<data["workers"]:
                used_cpus = {item["cpu"] for item in running.values()}
                cpu = next(v for v in cpus if v not in used_cpus)
                cid = pending.pop(0)
                directory = private/"workers"/cid
                directory.mkdir(parents=True,exist_ok=True)
                log = (directory/"worker.log").open("x")
                cmd = [sys.executable,"review_response/run_prospective_truth_scoring.py","worker","--project-root",str(root),
                       "--runtime-root",str(runtime),"--allocation",str(allocation),"--condition",cid]
                process = subprocess.Popen(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                os.sched_setaffinity(process.pid,{cpu})
                running[cid] = {"process":process,"log":log,"started":time.monotonic(),"cpu":cpu}
            now = time.monotonic()
            if datetime.now(timezone.utc)>=datetime.fromisoformat(data["expires_UTC"]):
                raise prep.PreparationError("whole truth/scoring fresh deadline reached")
            if now-last_disk>2:
                used_disk = s.resource_guard(data)
                last_disk = now
            total_rss = rss(os.getpid())
            active = []
            for cid,item in list(running.items()):
                process = item["process"]
                memory = rss(process.pid)
                total_rss += memory
                max_worker_rss = max(max_worker_rss,memory)
                if memory>data["worker_rss_limit_bytes"] or now-item["started"]>data["worker_wall_seconds"]:
                    raise prep.PreparationError("own worker RSS/condition wall cap reached: "+cid)
                f = private/"workers"/cid/"current_phase.json"
                progress = prep.read(f) if f.exists() else {}
                coordinate_start = progress.get("coordinate_started_UTC")
                if coordinate_start is not None and (datetime.now(timezone.utc)-datetime.fromisoformat(coordinate_start)).total_seconds()>data["direct_coordinate_wall_seconds"]:
                    raise prep.PreparationError("direct coordinate 1800 s cap reached: "+cid)
                active.append({"condition_id":cid,"pid":process.pid,"RSS_bytes":memory,**progress})
                code = process.poll()
                if code is not None:
                    item["log"].close()
                    if code != 0:
                        raise prep.PreparationError("condition worker failed; no retry: "+cid)
                    if not (private/"workers"/cid/"result.json").exists():
                        raise prep.PreparationError("worker result missing: "+cid)
                    completed.append(cid)
                    del running[cid]
            max_total_rss = max(max_total_rss,total_rss)
            if total_rss>data["usable_ram_bytes"] or rss(os.getpid())>data["coordinator_reserved_ram_bytes"]:
                raise prep.PreparationError("own total/coordinator RAM cap reached")
            if now-last_report>10:
                status(private,"prospective_truth_running",workers=int(data["workers"]),completed_conditions=len(completed),
                       ready_conditions=13,active_workers=active,elapsed_seconds=now-started,cumulative_disk_bytes=used_disk,
                       starts_UTC=data["starts_UTC"],expires_UTC=data["expires_UTC"],max_worker_RSS_bytes=max_worker_rss)
                last_report = now
            time.sleep(.2)
        records=[]
        for spec in specs:
            cid=spec["condition_id"]
            if cid in p.TERMINAL:
                records.append({"condition_id":cid,"condition":spec,"status":p.TERMINAL[cid],"ground":None,"points":[],
                                "resource":{"counts":{}},"truth_attempted":False})
            else:
                records.append(prep.read(private/"workers"/cid/"result.json"))
        counts=Counter({key:0 for key in (*s.LIMITS,*s.ZERO,"target_phase_gap_diagnostics")})
        for record in records:
            counts.update(record["resource"]["counts"])
        if any(counts[key]>cap for key,cap in s.LIMITS.items()) or any(counts[key] for key in s.ZERO):
            raise prep.PreparationError("aggregate action ceiling/forbidden action failed")
        truth={"prediction_origin_result_commit":s.BASE,"prediction_sha256":s.PREDICTION_SHA,"attempted_conditions":16,
               "family_units":4,"candidate_ready_conditions":13,"frozen_coordinates":39,"conditions":records,
               "all_attempt_or_terminal_records_present":True,"prediction_modified":False}
        source=s.source_gate(root)[-1]
        resource={"new_actions":dict(counts),"fresh_allocation_sha256":prep.sha_file(allocation),"authority":data["authority"],
                  "starts_UTC":data["starts_UTC"],"expires_UTC":data["expires_UTC"],"deadline_renewed":False,
                  "concurrent_worker_maximum":int(data["workers"]),"BLAS_threads_per_worker":1,
                  "actual_worker_peak_RSS_bytes":max_worker_rss,"actual_total_peak_RSS_bytes":max_total_rss,
                  "acquisition_wall_seconds":time.monotonic()-started,"cumulative_disk_bytes":s.resource_guard(data),
                  "disk_quota_bytes":data["writable_disk_quota_bytes"],"stop_reserve_bytes":data["reserved_disk_bytes"],
                  "resource_monitor_limit":"own-process periodic checks and external own-process-group wall/RSS watchdog; no native cgroup certificate"}
        access={"workers":{r["condition_id"]:r.get("access") for r in records if r["condition_id"] not in p.TERMINAL},
                "terminal_condition_ground_truth_reads":0,"prediction_modified":False,"historical_truth_array_reads":0}
        status(private,"prospective_truth_freezing",new_actions=dict(counts))
        directory=root/s.OUTPUT/"truth"
        names=s.write_bundle(directory,"truth.json","TRUTH_FROZEN.json",truth,source,resource,access,
              {"pre_truth_gate.json":gate,"pre_tests.json":prep.read(private/"pre_tests.json"),
               "pre_tests.log":(private/"pre_tests.log").read_bytes()})
        truth_commit=s.commit_bundle(root,directory,names,"Freeze prospective same-H ground and direct Schur truth before scoring")
        prep.write(private/"truth_commit.json",{"commit":truth_commit})
        # The commit/blob gate is the only path into the immutable scorer.
        s.verify_bundle(root,directory,truth_commit)
        prediction,protocol,*_=s.source_gate(root)
        frozen_truth=prep.read(directory/"truth.json")
        status(private,"prospective_immutable_scoring",truth_commit=truth_commit)
        scored=s.score_all(prediction,frozen_truth,protocol)
        s.resource_guard(data)
        post=tests(root,private,"post")
        s.verify_bundle(root,directory,truth_commit)
        source=s.source_gate(root)[-1]
        preservation=root_preservation(root,private)
        summary=summary_markdown(scored,truth_commit,resource)
        handoff=("# Prospective truth/scoring handoff\n\n"
                 f"Status: `{s.SUCCESS}`. Prediction: `{s.BASE}`. Truth freeze: `{truth_commit}`.\n\n"
                 "Final result commit is the commit containing this handoff (manifest excludes itself).\n\n"
                 "Read summary.md, COMPLETE.json, scoring.json, ../truth/TRUTH_FROZEN.json, ../truth/truth.json, "
                 "source_audit.json, resource_audit.json, access_audit.json, test_audit.json, manifest.json.\n\n"
                 "GPT review: assess frozen B0/B1 safety and cost-free oracle headroom; compare raw M1 point/width/branch "
                 "diagnostics while preserving all abstentions and h_ritz failures; retain all denominators and CH2 scope. "
                 "PF/H decomposition is indeterminate without confirmed absolute-target correspondence. "
                 "No new molecules, times, rescue, width/rank/gamma/gate changes or certificates are authorized.\n")
        final=root/s.OUTPUT/"final"
        complete={"status":s.SUCCESS,"truth_origin_result_commit":truth_commit,"prediction_origin_result_commit":s.BASE,
                  "denominators":scored["denominators"],"new_actions":dict(counts),"prediction_modified":False,
                  "M1_adoption_modified":False,"next_science_authorized":False,"publication_requires_remote_SHA_verification":True,
                  "root_preservation":preservation}
        names=s.write_bundle(final,"scoring.json","SCORING_FROZEN.json",scored,{**source,"truth_origin_result_commit":truth_commit},
                             {**resource,"cumulative_disk_bytes_at_scoring":s.resource_guard(data)},access,
                             {"COMPLETE.json":complete,"summary.md":summary,"handoff.md":handoff,
                              "test_audit.json":{"pre":prep.read(private/"pre_tests.json"),"post":post,"legacy_molecular_truth_tests":0},
                              "post_tests.json":post,"post_tests.log":(private/"post_tests.log").read_bytes()})
        final_commit=s.commit_bundle(root,final,names,"Freeze immutable prospective truth scoring; stop for review")
        s.source_gate(root)
        s.verify_bundle(root,directory,truth_commit)
        s.verify_bundle(root,final,final_commit)
        preservation=root_preservation(root,private)
        status(private,s.SUCCESS,truth_commit=truth_commit,result_commit=final_commit,denominators=scored["denominators"],
               new_actions=dict(counts),focused_tests={"pre":gate["focused_tests"]["passed"],"post":post["passed"]},
               root_preservation=preservation,blob_hash_gate="PASS",next_science_authorized=False,
               cumulative_disk_bytes=s.resource_guard(data),publication_status="pending")
        publication=publish(root,final_commit,private) if do_push else {"remote_SHA_verified":False,"push_status":"not_requested"}
        status(private,s.SUCCESS,truth_commit=truth_commit,result_commit=final_commit,denominators=scored["denominators"],
               new_actions=dict(counts),focused_tests={"pre":gate["focused_tests"]["passed"],"post":post["passed"]},
               root_preservation=preservation,blob_hash_gate="PASS",next_science_authorized=False,
               cumulative_disk_bytes=s.resource_guard(data),publication=publication)
    except BaseException as error:
        for item in running.values():
            stop_owned(item["process"])
            item["log"].close()
        status(private,"prospective_truth_scoring_stopped_review_required",reason=str(error),completed_conditions=completed,
               scientific_retry=False,technical_retries_used=0,next_science_authorized=False)
        raise


def summary_markdown(scored,truth_commit,resource):
    d=scored["denominators"]
    lines=["# Prospective truth/scoring results", "", f"Status: `{s.SUCCESS}`.", "",
           f"Prediction commit: `{s.BASE}`. Truth freeze: `{truth_commit}`.", "",
           f"Attempted conditions {d['attempted_conditions']} / family units {d['family_units']}; candidate ready {d['candidate_ready_conditions']} / frozen coordinates {d['frozen_coordinates']}.",
           f"Ground attempted/valid: {d['ground_attempted_conditions']}/{d['ground_valid_conditions']}; truth attempted/valid coordinates: {d['truth_attempted_coordinates']}/{d['truth_valid_coordinates']}; scored conditions/coordinates: {d['scored_conditions']}/{d['scored_coordinates']}.", "",
           "| Frozen arm | Safe | Unsafe | Indeterminate/abstain | Safe target met |", "|---|---:|---:|---:|---:|"]
    for arm,row in scored["B0_B1_evidence_axes"].items():
        lines.append(f"| {arm} | {row['safe']} | {row['unsafe']} | {row['indeterminate_or_abstain']} | {row['safe_target_met']} |")
    lines += ["", "M1 package adoption remains 39/39 coordinate abstentions and 13/13 condition abstentions; accepted M1 performance count is zero.",
              f"Raw valid-truth diagnostics: empirical width covers {scored['empirical_width_diagnostic_covered']}; shift/gap compatibility {scored['branch_gap_diagnostic_compatible']}.",
              "CH2_R1.40_r1.2 and CH2_R1.70_r1.0 retain pre-truth h_ritz_residual failures. Raw diagnostics do not rescue adoption.",
              "PF/H-reference decomposition remains indeterminate because the frozen empirical M1 package does not confirm physical absolute-target correspondence.", "",
              "Oracle values describe cost-free same-time headroom and the frozen native three-candidate set, not operational intervention. Incomplete truth is never a complete oracle.",
              "B0 is a benchmark whose safety is measured, never assumed to be a safe fallback. No gamma, width, rank, budget or candidate was changed after truth.",
              "LiH_R1.40, LiH_R2.60 and LiF_R2.60 remain terminal and received no ground/truth actions.",
              "CH2 retains repository_tracked_family_unseen and (5,3) fixed-population-sector scope; no global molecular ground or pure-spin claim.",
              "Four families are the sampling units; three times and within-family geometries are not independent samples.", "",
              f"New action counts: `{json.dumps(resource['new_actions'],sort_keys=True)}`.",
              "Matrices, unitaries, eigenvectors and exact states are private and are not in this result commit. All focused tests and integrity checks must pass before publication.",
              "Stop for GPT review. No additional scientific acquisition, rescue or certificate is authorized."]
    return "\n".join(lines)+"\n"


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase",choices=("seal-source","verify-source","tests","preflight","worker","execute"))
    parser.add_argument("--project-root",type=Path,default=Path.cwd())
    parser.add_argument("--runtime-root",type=Path)
    parser.add_argument("--allocation",type=Path)
    parser.add_argument("--condition")
    parser.add_argument("--label",choices=("pre","post"))
    parser.add_argument("--push",action="store_true")
    args=parser.parse_args(argv)
    root=args.project_root.resolve();output,private=paths(root)
    private.mkdir(parents=True,exist_ok=True)
    if args.phase == "seal-source":
        s.seal_source(root)
    elif args.phase == "verify-source":
        source=s.source_gate(root)[-1]
        print(json.dumps({"status":"PASS","source":source,"science_actions":0},sort_keys=True))
    elif args.phase == "tests":
        s.source_gate(root)
        if args.label is None: parser.error("tests requires --label")
        tests(root,private,args.label)
    elif args.phase == "preflight":
        preflight(root,private,args.runtime_root,args.allocation)
    elif args.phase == "worker":
        if args.condition is None: parser.error("worker requires --condition")
        worker(root,private,args.runtime_root,args.allocation,args.condition)
    else:
        execute(root,private,args.runtime_root,args.allocation,args.push)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (prep.PreparationError,FileExistsError,subprocess.CalledProcessError,KeyError,ValueError,subprocess.TimeoutExpired) as error:
        print("STOP:",error,file=sys.stderr,flush=True)
        raise SystemExit(2)
