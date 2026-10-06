"""Coordinator for approved local H-chain supplements; Git barriers are explicit."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import csv
import hashlib
from importlib.metadata import version
import json
import multiprocessing
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from hchain_supplement_execution import *
from hchain_prediction_phase import commit_bundle, BUNDLE_FILES
from hchain_supplement_preflight import METHOD_PATHS, SOURCES, DEFERRED_TRUTH

GROUND_SOURCES = {
    "H6": ("artifacts/hchain_truth_scoring_20261004/ground/ground.json", "5a9226a94fad0b578df1a53edd1a29e3571ad8c3"),
    "H7": ("artifacts/hchain_h3_h5_h7_extension_20261004/ground/payload.json", "5b06be4aa6201eb6ace1da352d125d7495481355"),
    "H8": ("artifacts/hchain_h8_memory_safe_extension_20261004/ground/payload.json", "392e58fb737142bbba862a23e2189242174835ea"),
}
TEST_FILES = ("review_tests/test_hchain_supplement_preflight.py", "review_tests/test_hchain_supplement_execution.py")


def focused_tests(root):
    start = utc()
    command = [sys.executable, "-m", "pytest", "-q", "-rs", *TEST_FILES, "-p", "no:cacheprovider"]
    run = subprocess.run(command, cwd=root, capture_output=True, text=True)
    output = run.stdout + run.stderr
    counts = {word: sum(int(n) for n in re.findall(r"(\d+) " + word, output)) for word in ("passed", "failed", "skipped", "error")}
    print(output, flush=True)
    result = {**counts, "command": command, "started_utc": start, "ended_utc": utc(), "exit_code": run.returncode,
              "output": output, "truth_bearing_legacy_tests_run": False, "molecular_actions": 0}
    if run.returncode or counts["failed"] or counts["skipped"] or counts["error"] or not counts["passed"]:
        raise PreparationError("focused tests fail/skip/error")
    return result


def seal(root):
    clean_gate(root)
    remote_gate(root)
    test = focused_tests(root)
    content = git(root, "rev-parse", "HEAD").decode().strip()
    git(root, "merge-base", "--is-ancestor", BASE, content)
    paths = set(METHOD_PATHS) | {p for p, _, _ in SOURCES}
    paths.update(git(root, "ls-files", "src").decode().splitlines())
    paths.update({"AGENTS.md", INVENTORY, "review_response/hchain_supplement_preflight.py",
        "review_response/hchain_cached_prefix.py", "review_response/hchain_supplement_execution.py",
        "review_response/run_hchain_supplement.py", "review_response/run_hchain_truth_scoring.py",
        "review_response/audit_h01_approximate_state_pilot.py", "review_response/pf_first_study_phase_common.py",
        "review_response/_pf_first_study_s0_exact_time_scoring_base.py", "review_response/pf_spectral_recoverability_d2_protocol_draft.json",
        OLD + "/cheap_reference_scale_contract.json", DOC + "/authorization.json", DOC + "/approved_execution.txt",
        "docs/second_study_v2/hchain_supplement_local_20261006/preregistration.json",
        "docs/second_study_v2/hchain_supplement_local_20261006/approved_request.txt", *TEST_FILES})
    rows = []
    origins = {p: (o, r) for p, o, r in SOURCES}
    for name in sorted(paths):
        data = (root / name).read_bytes()
        if data != git(root, "show", f"{content}:{name}"):
            raise PreparationError("uncommitted source dependency: " + name)
        origin, role = origins.get(name, (git(root, "log", "-1", "--format=%H", content, "--", name).decode().strip(), "source_method_or_dependency"))
        if data != git(root, "show", f"{origin}:{name}"):
            raise PreparationError("origin source no longer identical: " + name)
        rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                     "origin_result_commit": origin, "verified_snapshot_commit": content, "role": role})
    target = root / DOC / "source_freeze.json"
    if target.exists():
        raise PreparationError("source seal already exists")
    write_json(target, {"content_commit": content, "base_commit": BASE, "files": rows, "manifest_self_excluded": True,
        "dependencies": {name: version(name) for name in ("numpy", "scipy", "pyscf", "openfermion", "pytest")},
        "python": sys.executable, "python_version": sys.version})
    write_json(root / DOC / "focused_tests.json", test)
    paths = [DOC + "/source_freeze.json", DOC + "/focused_tests.json"]
    git(root, "add", "--", *paths)
    git(root, "commit", "-m", "Freeze supplement source identity and truth-free test gate")
    print("SOURCE_FREEZE_COMMIT=" + git(root, "rev-parse", "HEAD").decode().strip(), flush=True)


def assert_environment():
    for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE"):
        if os.environ.get(variable) != "1":
            raise PreparationError("required worker environment: " + variable)
    if "cupy" in sys.modules:
        raise PreparationError("CuPy import not authorized")


def stage(root, out, name, tasks, reservations):
    inventory = machine_inventory(out)
    write_json(out / ".runtime" / (name + "_allocation.json"), inventory)
    author = read(root / DOC / "authorization.json")
    workers = min(len(tasks), inventory["worker_CPU_ceiling"], author["maximum_independent_workers"])
    while workers and sum(sorted(reservations, reverse=True)[:workers]) * 1024**3 > inventory["usable_RAM_bytes"]:
        workers -= 1
    if tasks and workers < 1:
        raise PreparationError("local resource reserve insufficient before science")
    if inventory["filesystem_free_bytes"] <= inventory["disk_reserve_bytes"]:
        raise PreparationError("local disk reserve insufficient before science")
    if not tasks:
        return [], {"stage": name, "inventory": inventory, "maximum_worker_concurrency": 0, "stage_wall_seconds": 0, "aggregate_peak_RSS_bytes": owned_process_memory().get("VmRSS", 0)}
    print(json.dumps({"stage_started": name, "workers": workers, "units": [t["unit"] for t in tasks]}), flush=True)
    start = time.perf_counter()
    peak, results, maximum_concurrency = 0, [], 0
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        pending = {pool.submit(worker, {**task, "root": str(root), "output": str(out), "stage": name}) for task in tasks}
        while pending:
            pids = list(pool._processes)  # own child PIDs only; never inspect/control other jobs
            memory = [owned_process_memory(pid) for pid in [os.getpid(), *pids]]
            peak = max(peak, sum(m.get("VmRSS", 0) for m in memory))
            maximum_concurrency = max(maximum_concurrency, len(pids))
            if any(m.get("VmSwap", 0) for m in memory):
                raise PreparationError("own coordinator/worker swap observed")
            completed, pending = wait(pending, timeout=.2, return_when=FIRST_COMPLETED)
            for future in completed:
                result = future.result()
                results.append(result)
                print(json.dumps({"stage": name, "unit": result["unit"], "status": result["status"],
                                  "failure": result.get("failure_reason"), "wall_seconds": result["worker_total_wall_seconds"]}), flush=True)
    return sorted(results, key=lambda row: row["unit"]), {"stage": name, "inventory": inventory,
        "maximum_worker_concurrency": maximum_concurrency, "stage_wall_seconds": time.perf_counter() - start,
        "aggregate_peak_RSS_bytes": peak, "sample_interval_seconds": .2, "scope": "coordinator plus its own worker processes, concurrent RSS not sum of individual peaks"}


def freeze(root, out, stage_name, payload, resources):
    source = source_gate(root)
    accesses = [r.get("access", {}) for r in payload.get("workers", [])]
    directory = out / stage_name
    digest = make_bundle(directory, finite_json(payload), {"stage": stage_name, "created_utc": utc(),
        "truth_opened": stage_name in ("ground", "truth", "truth_reuse", "analysis"),
        "source_manifest_sha256": sha_file(root / DOC / "source_freeze.json")}, source, {"worker_audits": accesses}, resources)
    remote_gate(root)
    commit = commit_bundle(root, directory, "Freeze H-chain supplement " + stage_name)
    print(json.dumps({"freeze": stage_name, "commit": commit, "sha256": digest}), flush=True)
    return commit


def saved_truth(root, systems):
    """Called ONLY after verify_bundle on this track's new prediction commit."""
    inv = read(root / INVENTORY)
    results, sources = {}, []
    for system in systems:
        truth_source = next(row for row in DEFERRED_TRUTH if row["system"] == system)
        entries = [(truth_source["path"], truth_source["origin_result_commit"]), GROUND_SOURCES[system]]
        loaded = []
        for path, origin in entries:
            data = (root / path).read_bytes()
            if data != git(root, "show", f"{origin}:{path}") or data != git(root, "show", f"{BASE}:{path}"):
                raise PreparationError("saved truth/ground origin snapshot byte mismatch")
            sources.append({"path": path, "origin_result_commit": origin, "verified_snapshot_commit": BASE,
                            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
            loaded.append(json.loads(data))
        truth, ground = loaded
        ground = ground["systems"][system]
        identity = inv["input_identity_metadata"][system]
        for key in ("H_sha256_numpy_v1", "sector_indices_sha256_numpy_v1"):
            if ground[key] != identity[key]:
                raise PreparationError("saved ground same-H/sector closure mismatch")
        selected = []
        for plan in frozen_plan(root, system):
            rows = [row for row in truth["points"] if row["candidate_id"] == plan["candidate_id"] and row["time_hex"] == plan["time_hex"]]
            if len(rows) != 1:
                raise PreparationError("saved truth exact coordinate missing/ambiguous")
            point = rows[0]
            if float(point["time"]).hex() != plan["time_hex"]:
                raise PreparationError("saved truth binary64 time mismatch")
            selected.append(point)
        results[system] = {"ground": ground, "points": selected, "new_truth": 0, "reused_truth": 3}
    return {"systems": results, "source_registry": sources, "ground_array_reads": 0}


def saved_anchor(root):
    old = read(root / SAVED_PRED["H6"])
    cheap = old["cheap_B0_B1_B2_q"]["H6"]["points"]
    m1 = old["M1"]["H6"]
    return {"unit": "H6_R1.00", "status": "complete", "anchor_reused": True, "new_science_actions": 0,
            "cheap": cheap, "M1": [{**p, "M1": p["core_prediction"]} for p in m1],
            "decisions": cheap_decisions(cheap, 14344), "candidate_plan": frozen_plan(root, "H6"),
            "source_origin_commit": "858265dacd304c844029ce2576b4559221f0c7c1", "verified_snapshot_commit": BASE}


def analyze_G(prediction, truth):
    rows, summaries = [], []
    for record in prediction["workers"]:
        if record["status"] != "complete" or record["unit"] not in truth["systems"]:
            summaries.append({"geometry": record["unit"], "status": record["status"], "reason": record.get("failure_reason")})
            continue
        unit = record["unit"]
        direct = truth["systems"][unit]
        candidates = []
        for cheap, m1, point in zip(record["cheap"], record["M1"], direct["points"], strict=True):
            if cheap["time_hex"] != point["time_hex"] or m1["time_hex"] != point["time_hex"]:
                raise PreparationError("G immutable scorer exact coordinate mismatch")
            core = m1["M1"]
            if "status" not in core:
                primary = next(p for p in core["prefixes"] if p["dimension"] == 8)
                core = {**primary, **core}
            diagnostic = truth_comparison(core, cheap["delta_C_hartree"], point, direct["ground"]["energy_hartree"], 14344, point["time"])
            oracle = budget(point["time"], abs(point["signed_direct_shift_hartree"]), 14344)
            candidates.append({"candidate_id": point["candidate_id"], "time": point["time"], "budget": oracle})
            for gamma in (1., *GAMMAS):
                formula = safety_mechanism(abs(cheap["delta_C_hartree"]), abs(point["signed_direct_shift_hartree"]), gamma)
                base = budget(point["time"], abs(cheap["delta_C_hartree"]), 14344)
                frozen = None if base is None else gamma * base
                safe = None if frozen is None or not point["quality"]["physical_branch_valid"] else abs(point["signed_direct_shift_hartree"]) + BETA * 14344 / (point["time"] * frozen) <= EPS
                rows.append({"geometry": unit, "candidate_id": point["candidate_id"], "time": point["time"], "time_hex": point["time_hex"],
                    "gamma": gamma, "frozen_budget": frozen, "safe": safe, **formula, **diagnostic,
                    "M1_abstained": core.get("abstained", True), "M1_failure_reasons": core.get("failure_reasons", []),
                    "signed_direct_shift_hartree": point["signed_direct_shift_hartree"], "delta_C_hartree": cheap["delta_C_hartree"],
                    "delta_M_hartree": core["signed_shift_estimate_hartree"], "width_M_hartree": core["empirical_width_hartree"],
                    "same_time_cost_free_truth_headroom": None if frozen is None or oracle is None else 1 - oracle / frozen})
        feasible = [p for p in candidates if p["budget"] is not None]
        native_oracle = min(feasible, key=lambda p: (p["budget"], p["time"])) if feasible else None
        decisions = record["decisions"]
        scored = []
        for decision in [{"gamma": 1.01, "label": "B0", "selected": decisions["B0"]},
                         *[{**d, "label": "B1"} for d in decisions["B1_frontier"]]]:
            chosen = decision["selected"]
            match = None if chosen is None else next(r for r in rows if r["geometry"] == unit and r["candidate_id"] == chosen["candidate_id"] and r["gamma"] == decision["gamma"])
            scored.append({"label": decision["label"], "gamma": decision["gamma"], "decision": chosen,
                           "safe": None if match is None else match["safe"], "budget_ratio_B0": None if chosen is None or decisions["B0"]["budget"] is None else chosen["budget"] / decisions["B0"]["budget"]})
        summaries.append({"geometry": unit, "status": "scored", "decisions": scored, "native_three_candidate_oracle": native_oracle,
                          "M1_role": "diagnostic only; no operational selector or original formal rescoring"})
    return {"rows": rows, "geometry_summaries": summaries, "denominator_geometries": 5, "independent_samples_claim": False}


def analyze_R(prediction, truth):
    rows = []
    for result in prediction["workers"]:
        system = result["unit"]
        direct = truth["systems"][system]
        for coordinate in result["points"]:
            point = next(p for p in direct["points"] if p["time_hex"] == coordinate["time_hex"])
            cheap = next(p for p in result["saved_cheap"] if p["time_hex"] == coordinate["time_hex"])
            for m in (4, 8, 16, 32):
                rank = coordinate["ranks"][str(m)]
                row = {"system": system, "candidate_id": coordinate["candidate_id"], "time": coordinate["time"], "time_hex": coordinate["time_hex"], "rank": m, "actual_rank": coordinate["actual_rank"], "status": rank["status"]}
                if rank["status"] == "available":
                    row.update(truth_comparison(rank, cheap["delta_C_hartree"], point, direct["ground"]["energy_hartree"], coordinate["K"], coordinate["time"]))
                    row.update({"delta_M_hartree": rank["signed_shift_estimate_hartree"], "width_M_hartree": rank["empirical_width_hartree"], "local_width_hartree": rank["local_residual_width_hartree"], "prefix_width_hartree": rank["prefix_width_hartree"], "positive_QPE_allowance": rank["positive_QPE_allowance"], "numerically_usable": rank["numerically_usable"], "failure_reasons": rank["failure_reasons"], "rank8_control_passed": coordinate["reproduction"]["passed"]})
                rows.append(row)
    return {"rows": rows, "new_ground_truth_actions": 0, "reused_truth_coordinates": 9,
            "old_rank8_formal_package_changed": False, "hypothetical_information_value_only": True}


def render(out, track, analysis):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory = out / "tables_figures"
    directory.mkdir()
    rows = analysis["rows"]
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with (directory / "primary_scalars.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    if track == "R":
        figure, axes = plt.subplots(1, 3, figsize=(12, 3.6))
        for axis, system in zip(axes, ("H6", "H7", "H8"), strict=True):
            subset = [r for r in rows if r["system"] == system and r["status"] == "available"]
            for candidate in dict.fromkeys(r["candidate_id"] for r in subset):
                points = [r for r in subset if r["candidate_id"] == candidate]
                axis.plot([r["rank"] for r in points], [max(r["E_M_hartree"], 1e-16) for r in points], "o-", label=candidate + " error")
                axis.plot([r["rank"] for r in points], [max(r["width_M_hartree"], 1e-16) for r in points], ":", label=candidate + " width")
            axis.set(xscale="log", yscale="log", title=system, xlabel="Cached prefix rank", ylabel="Hartree")
            axis.legend(fontsize=6)
    else:
        figure, axes = plt.subplots(1, 2, figsize=(9, 3.6))
        for unit in dict.fromkeys(r["geometry"] for r in rows):
            subset = [r for r in rows if r["geometry"] == unit and r["gamma"] == 1.01]
            axes[0].plot([r["time"] for r in subset], [r["gamma_req"] for r in subset], "o-", label=unit)
            axes[1].plot([r["time"] for r in subset], [r["safety_slack"] for r in subset], "o-", label=unit)
        axes[0].set(xlabel="Frozen time", ylabel="Required gamma")
        axes[1].set(xlabel="Frozen time", ylabel="Safety slack at gamma=1.01 (Ha)")
        axes[1].axhline(0, color="black", linewidth=.5)
        for axis in axes:
            axis.legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(directory / "mechanism.svg")
    figure.savefig(directory / "mechanism.png", dpi=160)
    plt.close(figure)
    return [str(path.relative_to(out.parent.parent)) for path in directory.iterdir()]


def run(root):
    assert_environment()
    source_gate(root)
    authorization = read(root / DOC / "authorization.json")
    track = authorization["track"]
    out = root / authorization["output_root"]
    if out.exists():
        raise PreparationError("output already exists; explicit checkpoint review required; no repeat")
    out.mkdir(parents=True)
    (out / ".runtime").mkdir()
    start, start_utc = time.perf_counter(), utc()
    freezes, monitors = {}, []
    closures, resource = stage(root, out, "closure", [{"unit": s} for s in (("H6",) if track == "G" else ("H6", "H7", "H8"))], [2] if track == "G" else [2, 3, 8])
    monitors.append(resource)
    if any(row["status"] != "complete" for row in closures):
        freeze(root, out, "closure_failed", {"workers": closures, "status": "anchor_identity_mismatch_review_required" if track == "G" else "input_identity_mismatch_review_required"}, resource)
        raise PreparationError("frozen array identity closure failed before new science")
    freezes["input_closure"] = freeze(root, out, "input_closure", {"workers": closures}, resource)
    if track == "R":
        predictions, resource = stage(root, out, "R_prediction", [{"unit": s} for s in ("H6", "H7", "H8")], [2, 3, 8])
        monitors.append(resource)
        prediction = {"workers": predictions, "truth_reads": 0, "rank_continuation": "each rank own previous vector", "primary_ranks": [4, 8, 16, 32]}
    else:
        inputs, resource = stage(root, out, "G_inputs", [{"unit": f"H6_R{r:.2f}", "distance": r} for r in (.8, 1.2, 1.4, 1.6)], [2] * 4)
        monitors.append(resource)
        freezes["inputs"] = freeze(root, out, "inputs", {"workers": inputs, "anchor_closure": closures[0]}, resource)
        ready = [r for r in inputs if r["status"] == "complete"]
        references, resource = stage(root, out, "G_reference", [{"unit": r["unit"], "input": r["input"]} for r in ready], [2] * len(ready))
        monitors.append(resource)
        freezes["reference_time"] = freeze(root, out, "reference_time", {"workers": references, "anchor_plan": frozen_plan(root, "H6")}, resource)
        input_map = {r["unit"]: r["input"] for r in ready}
        usable = [r for r in references if r["status"] == "complete"]
        predictions, resource = stage(root, out, "G_prediction", [{"unit": r["unit"], "input": input_map[r["unit"]], "plan": r["candidate_plan"]} for r in usable], [2] * len(usable))
        monitors.append(resource)
        failed = [r for r in inputs if r["status"] != "complete"] + [r for r in references if r["status"] != "complete"]
        prediction = {"workers": sorted([saved_anchor(root), *predictions, *failed], key=lambda r: r["unit"]),
                      "denominator_geometries": 5, "new_truth_reads": 0, "saved_truth_reads": 0}
    freezes["prediction"] = freeze(root, out, "prediction", prediction, resource)
    verify_bundle(root, out / "prediction", freezes["prediction"])
    prediction = read(out / "prediction/prediction.json")  # scorer always uses committed frozen bytes
    if track == "R" and any(r["status"] != "complete" or not r.get("rank8_reproduction_passed", False) for r in prediction["workers"]):
        status = authorization["rank8_failure_stop_status"]
        freeze(root, out, "STOPPED", {"status": status, "truth_reads": 0, "science_interpretation": "not performed", "prediction_commit": freezes["prediction"]}, {"monitors": monitors})
        return
    if track == "R":
        truth = saved_truth(root, ("H6", "H7", "H8"))
        freezes["truth_reuse"] = freeze(root, out, "truth_reuse", truth, {"new_truth": 0, "reused": 9})
        analysis = analyze_R(prediction, read(out / "truth_reuse/prediction.json"))
    else:
        # Ground freeze occurs after prediction, before any new direct truth.
        successful = [r for r in predictions if r["status"] == "complete"]
        grounds, resource = stage(root, out, "G_ground", [{"unit": r["unit"], "input": input_map[r["unit"]]} for r in successful], [2] * len(successful))
        monitors.append(resource)
        freezes["ground"] = freeze(root, out, "ground", {"workers": grounds}, resource)
        ground_map = {r["unit"]: r for r in grounds if r["status"] == "complete"}
        truths, resource = stage(root, out, "G_truth", [{"unit": r["unit"], "input": input_map[r["unit"]], "plan": r["candidate_plan"], "ground": ground_map[r["unit"]]} for r in usable if r["unit"] in ground_map], [2] * len(ground_map))
        monitors.append(resource)
        anchor = saved_truth(root, ("H6",))
        truth = {"systems": {"H6_R1.00": anchor["systems"]["H6"], **{r["unit"]: {"ground": ground_map[r["unit"]]["ground"], "points": r["points"], "new_truth": 3} for r in truths if r["status"] == "complete"}},
                 "workers": truths, "ground_failures": [r for r in grounds if r["status"] != "complete"], "source_registry": anchor["source_registry"]}
        freezes["truth"] = freeze(root, out, "truth", truth, resource)
        analysis = analyze_G(prediction, read(out / "truth/prediction.json"))
    verify_bundle(root, out / "prediction", freezes["prediction"])
    tests = focused_tests(root)
    status = authorization["stop_status"]
    all_workers = [r for directory in out.iterdir() if directory.is_dir() and (directory / "prediction.json").exists()
                   for r in read(directory / "prediction.json").get("workers", []) if "resource" in r]
    actions = Counter()
    unique_workers = {(r["stage"], r["unit"]): r for r in all_workers}
    for result in unique_workers.values():
        actions.update(result["resource"]["counts"])
    final = {"status": status, "analysis": analysis, "freezes": freezes, "actions": dict(actions),
             "started_utc": start_utc, "ended_utc": utc(), "total_wall_seconds": time.perf_counter() - start,
             "post_tests": tests, "new_scientific_retry": 0, "technical_retry": 0,
             "old_formal_packages_changed": False, "prospective_runtime_partial_truth_access": 0,
             "claim_scope": "empirical mechanism, not certificate/scaling/independent-samples or joint net cost"}
    freezes["analysis"] = freeze(root, out, "analysis", final, {"monitors": monitors, "final_machine_inventory": machine_inventory(out)})
    render(out, track, analysis)
    print(json.dumps({"status": status, "analysis_commit": freezes["analysis"], "actions": dict(actions)}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("seal", "run"))
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if args.command == "seal":
        seal(root)
    else:
        run(root)


if __name__ == "__main__":
    main()
