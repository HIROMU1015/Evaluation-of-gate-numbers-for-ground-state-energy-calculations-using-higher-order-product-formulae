"""One truth-only continuation from existing prediction and ground commits."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import time

import hchain_supplement_execution as core
import run_hchain_supplement as legacy
from hchain_truth_continuation import (
    BASE, DOC, RECOVERY, RECOVERY_DOC, SUCCESS, FAILURE, FORBIDDEN, DISTANCES,
    PREDICTION_COMMIT, GROUND_COMMIT, INPUT_COMMIT, REFERENCE_COMMIT,
    import_entries, truth_worker, verified_runtime_records,
)

TESTS = ("review_tests/test_hchain_supplement_preflight.py", "review_tests/test_hchain_supplement_execution.py",
         "review_tests/test_hchain_geometry_recovery.py", "review_tests/test_hchain_truth_continuation.py")


def activate():
    core.DOC = legacy.DOC = DOC
    legacy.TEST_FILES = TESTS
    legacy.worker = truth_worker


def seal(root):
    activate()
    core.clean_gate(root)
    core.remote_gate(root)
    legacy.assert_environment()
    test = legacy.focused_tests(root)
    content = core.git(root, "rev-parse", "HEAD").decode().strip()
    core.git(root, "merge-base", "--is-ancestor", BASE, content)
    old = core.read(root / RECOVERY_DOC / "source_freeze.json")
    paths = {r["path"] for r in import_entries(root)}
    paths.update({"review_response/hchain_truth_continuation.py", "review_response/run_hchain_truth_continuation.py", *TESTS})
    paths.update(str(p.relative_to(root)) for p in (root / DOC).iterdir() if p.is_file())
    rows = []
    for name in sorted(paths):
        data = (root / name).read_bytes()
        if data != core.git(root, "show", f"{content}:{name}"):
            raise core.PreparationError("uncommitted truth continuation dependency")
        previous = next((r for r in old["files"] if r["path"] == name), None)
        if previous and hashlib.sha256(data).hexdigest() != previous["sha256"]:
            raise core.PreparationError("frozen science/source changed: " + name)
        origin = core.git(root, "log", "-1", "--format=%H", content, "--", name).decode().strip()
        if data != core.git(root, "show", f"{origin}:{name}"):
            raise core.PreparationError("source origin/blob mismatch")
        rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "origin_result_commit": origin, "verified_snapshot_commit": content,
            "role": "truth_continuation_infrastructure" if previous is None else previous["role"]})
    if (root / DOC / "source_freeze.json").exists():
        raise core.PreparationError("truth continuation source seal exists")
    core.write_json(root / DOC / "source_freeze.json", {"content_commit": content, "files": rows,
        "manifest_self_excluded": True, "base_commit": BASE, "science_code_changes": 0,
        "inherited_source_files_unchanged": len(old["files"]),
        "dependencies": {name: version(name) for name in ("numpy", "scipy", "pyscf", "openfermion", "pytest")},
        "prediction_commit": PREDICTION_COMMIT, "ground_commit": GROUND_COMMIT})
    core.write_json(root / DOC / "focused_tests.json", test)
    names = [DOC + "/source_freeze.json", DOC + "/focused_tests.json"]
    core.git(root, "add", "--", *names)
    core.git(root, "commit", "-m", "Freeze truth-only continuation infrastructure and guarded source import tests")
    print("SOURCE_FREEZE_COMMIT=" + core.git(root, "rev-parse", "HEAD").decode().strip(), flush=True)


def run(root):
    activate()
    legacy.assert_environment()
    source = core.source_gate(root)
    auth = core.read(root / DOC / "authorization.json")
    if str(root) != auth["worktree"] or core.git(root, "branch", "--show-current").decode().strip() != auth["branch"]:
        raise core.PreparationError("authorized continuation worktree/branch mismatch")
    out = root / auth["output_root"]
    if out.exists() and any(p.name != ".gitignore" for p in out.iterdir()):
        raise core.PreparationError("one truth-only continuation; existing output forbids repeat")
    # Existing predictor/ground stage files and runtimes are verified before science.
    prediction, tasks, runtime_checks = verified_runtime_records(root)
    old_stopped = core.read(root / RECOVERY / "STOPPED/prediction.json")
    if any(old_stopped["recovery_actions"].get(k, 0) for k in ("full_pf_unitary_builds", "direct_Schur_solves", "direct_truth_coordinates", "target_phase_gaps")):
        raise core.PreparationError("truth already acquired in failed recovery; continuation scope mismatch")
    cache = root / "review_response/__pycache__/hchain_truth_scoring.cpython-311.pyc"
    if cache.exists():
        raise core.PreparationError("fresh worktree cache not isolated; stop before truth")
    out.mkdir(parents=True, exist_ok=True)
    (out / ".runtime").mkdir()
    started, started_utc = time.perf_counter(), core.utc()
    freezes, monitors, workers = {}, [], []
    failure, analysis = None, None

    def freeze(name, payload, resources):
        freezes[name] = legacy.freeze(root, out, name, payload, resources)
        core.verify_bundle(root, out / name, freezes[name])

    freeze("readiness", {"existing_prediction_commit": PREDICTION_COMMIT, "existing_ground_commit": GROUND_COMMIT,
        "original_input_commit": INPUT_COMMIT, "original_reference_commit": REFERENCE_COMMIT,
        "runtime_checks": runtime_checks, "denominator_geometries": 5, "new_front_end_actions": 0,
        "source_only_import": True, "pyc_allowlist_added": False, "target_pyc_present": False,
        "science_changes": 0, "continuation_run_number": 1}, {"inventory": core.machine_inventory(out)})
    try:
        workers, resource = legacy.stage(root, out, "G_truth", tasks, [2] * len(tasks))
        monitors.append(resource)
        # Reuse the already recorded R1 scalar truth; do not re-acquire it.
        anchor = legacy.saved_truth(root, ("H6",))
        truth = {"systems": {"H6_R1.00": anchor["systems"]["H6"],
            **{r["unit"]: {"ground": r["ground"]["ground"], "points": w["points"], "new_truth": 3}
                for r in tasks for w in workers if w["unit"] == r["unit"] and w["status"] == "complete"}},
            "workers": workers, "source_registry": anchor["source_registry"],
            "prediction_commit": PREDICTION_COMMIT, "ground_commit": GROUND_COMMIT,
            "new_truth_coordinates": sum(len(w.get("points", [])) for w in workers), "anchor_truth_reused": 3}
        freeze("truth", truth, resource)
        if len(workers) != 4 or any(r["status"] != "complete" for r in workers):
            raise core.PreparationError("truth continuation worker failed; no repair or repeat")
        if len(truth["systems"]) != 5 or truth["new_truth_coordinates"] != 12:
            raise core.PreparationError("five geometry / twelve new truth completeness gate failed")
        core.verify_bundle(root, root / RECOVERY / "prediction", PREDICTION_COMMIT)
        before = hashlib.sha256((root / RECOVERY / "prediction/prediction.json").read_bytes()).hexdigest()
        # Original frozen scalar scorer, same budgets/widths/gates; no selector updates.
        analysis = legacy.analyze_G(prediction, core.read(out / "truth/prediction.json"))
        if before != hashlib.sha256((root / RECOVERY / "prediction/prediction.json").read_bytes()).hexdigest():
            raise core.PreparationError("immutable scorer changed prediction")
        verified_runtime_records(root)
    except Exception as error:
        failure = {"type": type(error).__name__, "reason": str(error), "further_continuation_authorized": False}
    tests = legacy.focused_tests(root)
    actions = Counter()
    for row in workers:
        actions.update(row["resource"]["counts"])
    if any(actions[k] for k in FORBIDDEN) or any(actions[k] > 12 for k in
        ("full_pf_unitary_builds", "direct_Schur_solves", "direct_truth_coordinates", "target_phase_gaps")):
        raise core.PreparationError("truth-only global resource gate failed")
    result = {"status": FAILURE if failure else SUCCESS, "failure": failure, "analysis": analysis,
        "truth_only_actions": dict(actions), "forbidden_front_end_actions": {k:actions[k] for k in FORBIDDEN},
        "prior_original_failed_accounting": old_stopped["original_failed_run"],
        "prior_recovery_accounting": old_stopped["recovery_actions"],
        "cumulative_H_CISD_generation_attempts": {"H": 8, "CISD": 8}, "unique_new_geometries": 4,
        "denominator_geometries": 5, "Track_R_unchanged_commit": "0c40a3d7987e0961262bfd38bbb214a9e2946824",
        "input_commit": INPUT_COMMIT, "reference_commit": REFERENCE_COMMIT,
        "prediction_commit": PREDICTION_COMMIT, "ground_commit": GROUND_COMMIT,
        "continuation_implementation_commit": source["content_commit"], "freezes": dict(freezes),
        "post_tests": tests, "started_utc": started_utc, "ended_utc": core.utc(),
        "run_wall_seconds": time.perf_counter() - started, "technical_retry": 0, "scientific_retry": 0,
        "old_frozen_records_changed": False, "research_direction_changed": False,
        "prospective_partial_truth_access": 0, "GPU_operations": 0,
        "truth_quality_indeterminate_count": sum(not p["quality"]["physical_branch_valid"] for w in workers for p in w.get("points", [])),
        "claim_scope": "empirical geometry mechanism; no certificate or independent-sample or net-cost claim"}
    freeze("analysis" if analysis is not None else "STOPPED", result,
        {"monitors": monitors, "final_machine_inventory": core.machine_inventory(out)})
    if analysis is not None:
        legacy.render(out, "G", analysis)
    print(json.dumps({"status": result["status"], "actions": dict(actions), "freezes": freezes, "failure": failure}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("seal", "run"))
    args = parser.parse_args()
    (seal if args.command == "seal" else run)(Path.cwd().resolve())


if __name__ == "__main__":
    main()
