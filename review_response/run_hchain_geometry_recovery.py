"""One authorized serialization recovery; reuse frozen Track G science unchanged."""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import hchain_supplement_execution as core
import run_hchain_supplement as legacy

FAILED_COMMIT = "e74fdec5e5085fd7c4f7a39fb4d59cec052f68f4"
TRACK_R_COMMIT = "0c40a3d7987e0961262bfd38bbb214a9e2946824"
DOC = "docs/second_study_v2/hchain_geometry_recovery_20261006"
OLD_DOC = "docs/second_study_v2/hchain_supplement_execution_20261006"
DISTANCES = (.8, 1.2, 1.4, 1.6)
TESTS = (*legacy.TEST_FILES, "review_tests/test_hchain_geometry_recovery.py")
SUCCESS = "hchain_h6_geometry_sweep_recovery_complete_review_required"
FAILURE = "hchain_h6_geometry_sweep_recovery_failed_review_required"


def activate():
    """Technical output/source routing only, including spawned child processes."""
    core.DOC = DOC
    legacy.DOC = DOC
    legacy.TEST_FILES = TESTS
    legacy.worker = recovery_worker


def recovery_worker(task):
    activate()
    return core.worker(task)


def serialization_audit(root):
    root = Path(root)
    path = "review_response/hchain_supplement_execution.py"
    before = core.git(root, "show", f"{FAILED_COMMIT}:{path}").decode()
    after = (root / path).read_text()
    line = '                 "write_json": write_json,\n'
    if after.count(line) != 1 or after.replace(line, "", 1) != before:
        raise core.PreparationError("only one write_json namespace binding is authorized")
    recipe = root / "review_response/run_hchain_input_reference_preparation.py"
    if core.sha_file(recipe) != core.GENERATOR_SHA:
        raise core.PreparationError("science generator source changed")
    function = next(n for n in ast.parse(recipe.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "generate_h6")
    science_dump = ast.dump(function)
    sites = 0
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                and t.value.id == "mol" and t.attr == "atom" for t in node.targets):
            expected = ast.parse('[("H", (0.0, 0.0, float(i - 2.5))) for i in range(6)]', mode="eval").body
            if ast.dump(node.value) != ast.dump(expected):
                raise core.PreparationError("preapproved geometry site changed")
            node.value = ast.parse('[("H", (0.0, 0.0, float(i - 2.5) * distance)) for i in range(6)]', mode="eval").body
            sites += 1
    if sites != 1:
        raise core.PreparationError("geometry modification count")
    return {"original_failed_commit": FAILED_COMMIT, "science_source_sha256": core.GENERATOR_SHA,
        "extractor_before_sha256": hashlib.sha256(before.encode()).hexdigest(),
        "extractor_after_sha256": hashlib.sha256(after.encode()).hexdigest(),
        "exact_one_line_namespace_binding_only": True, "other_extractor_AST_unchanged": True,
        "science_generator_original_file_unchanged": True, "geometry_AST_modifications": sites,
        "science_function_AST_sha256": hashlib.sha256(science_dump.encode()).hexdigest(),
        "geometry_function_AST_sha256": hashlib.sha256(ast.dump(function).encode()).hexdigest(),
        "distance_variable_only": True, "science_recipe_changed": False,
        "diff": core.git(root, "diff", FAILED_COMMIT, "--", path).decode()}


def require_inputs(rows):
    expected = {f"H6_R{d:.2f}" for d in DISTANCES}
    if len(rows) != 4 or {r["unit"] for r in rows} != expected or any(r["status"] != "complete" or "input" not in r for r in rows):
        raise core.PreparationError("all four recovery inputs must succeed before any reference; no second recovery")


def original_accounting(root):
    """Read failed-run resource metadata, not its truth/analysis or runtime."""
    path = "artifacts/hchain_h6_geometry_sweep_20261006/inputs/prediction.json"
    data = (root / path).read_bytes()
    if data != core.git(root, "show", f"{FAILED_COMMIT}:{path}"):
        raise core.PreparationError("original failed input record changed")
    counts = Counter()
    records = json.loads(data)["workers"]
    for row in records:
        counts.update(row["resource"]["counts"])
    return {"origin_result_commit": FAILED_COMMIT, "verified_snapshot_commit": FAILED_COMMIT,
        "path": path, "sha256": hashlib.sha256(data).hexdigest(), "counts": dict(counts),
        "generation_attempts": 4, "CISD_attempts": 4, "usable_sanitized_inputs": 0,
        "failure": "NameError: name 'write_json' is not defined",
        "independent_new_geometries": 4, "original_runtime_read": False}


def seal(root):
    activate()
    core.clean_gate(root)
    core.remote_gate(root)
    audit = serialization_audit(root)
    test = legacy.focused_tests(root)
    content = core.git(root, "rev-parse", "HEAD").decode().strip()
    core.git(root, "merge-base", "--is-ancestor", FAILED_COMMIT, content)
    old = core.read(root / OLD_DOC / "source_freeze.json")
    paths = {r["path"] for r in old["files"]}
    paths.update({"review_response/run_hchain_geometry_recovery.py", *TESTS})
    paths.update(str(p.relative_to(root)) for p in (root / DOC).iterdir() if p.is_file())
    rows = []
    for name in sorted(paths):
        data = (root / name).read_bytes()
        if data != core.git(root, "show", f"{content}:{name}"):
            raise core.PreparationError("uncommitted recovery dependency: " + name)
        origin = core.git(root, "log", "-1", "--format=%H", content, "--", name).decode().strip()
        if data != core.git(root, "show", f"{origin}:{name}"):
            raise core.PreparationError("origin byte identity failed")
        original = next((r for r in old["files"] if r["path"] == name), None)
        if original and name != "review_response/hchain_supplement_execution.py" and hashlib.sha256(data).hexdigest() != original["sha256"]:
            raise core.PreparationError("unapproved frozen source change: " + name)
        rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "origin_result_commit": origin, "verified_snapshot_commit": content,
            "role": "recovery_dependency" if not original else original["role"]})
    target = root / DOC / "source_freeze.json"
    if target.exists():
        raise core.PreparationError("recovery seal already exists")
    core.write_json(target, {**{k:v for k,v in old.items() if k not in ("files", "content_commit")},
        "content_commit": content, "recovery_amendment_commit": content, "files": rows,
        "original_failed_commit": FAILED_COMMIT, "Track_R_accepted_commit": TRACK_R_COMMIT,
        "serialization_audit": audit, "manifest_self_excluded": True})
    core.write_json(root / DOC / "focused_tests.json", test)
    names = [DOC + "/source_freeze.json", DOC + "/focused_tests.json"]
    core.git(root, "add", "--", *names)
    core.git(root, "commit", "-m", "Freeze one-shot geometry recovery source and serialization regression gate")
    print("SOURCE_FREEZE_COMMIT=" + core.git(root, "rev-parse", "HEAD").decode().strip(), flush=True)


def fail_on_worker_errors(rows, stage_name, *, allow_domain=False):
    for row in rows:
        if row["status"] == "complete":
            continue
        # A preregistered fit/domain rejection is terminal, not an implementation retry.
        reason = row.get("failure_reason", "")
        scientific_reference = allow_domain and row.get("failure_type") == "PreparationError" and (
            reason in ("candidate_time_domain_ineligible", "hchain_cisd_reference_scale_unavailable"))
        if not scientific_reference:
            raise core.PreparationError(f"{stage_name} recovery failed at {row['unit']}: {reason}; no retry")


def run(root):
    activate()
    legacy.assert_environment()
    source = core.source_gate(root)
    serialization_audit(root)
    author = core.read(root / DOC / "authorization.json")
    out = root / author["output_root"]
    if out.exists() and any(p.name != ".gitignore" for p in out.iterdir()):
        raise core.PreparationError("recovery output exists; second recovery forbidden")
    out.mkdir(parents=True, exist_ok=True)
    (out / ".runtime").mkdir()
    started, start_utc = time.perf_counter(), core.utc()
    freezes, monitors, all_workers = {}, [], []
    analysis = None
    failure = None
    original = original_accounting(root)

    def stage(name, tasks):
        rows, resource = legacy.stage(root, out, name, tasks, [2] * len(tasks))
        all_workers.extend(rows)
        monitors.append(resource)
        return rows, resource

    def freeze(name, payload, resource):
        freezes[name] = legacy.freeze(root, out, name, payload, resource)
        core.verify_bundle(root, out / name, freezes[name])
        return freezes[name]

    try:
        closures, resource = stage("closure", [{"unit": "H6"}])
        freeze("input_closure", {"workers": closures, "new_reference_truth_reads": 0}, resource)
        fail_on_worker_errors(closures, "closure")
        inputs, resource = stage("G_inputs", [{"unit": f"H6_R{d:.2f}", "distance": d} for d in DISTANCES])
        freeze("inputs", {"workers": inputs, "anchor_closure": closures[0],
            "global_geometry_units": ["H6_R1.00", *[r["unit"] for r in inputs]],
            "global_inputs_complete": len(inputs) == 4 and all(r["status"] == "complete" for r in inputs),
            "original_failed_accounting": original, "recovery_generation_authorized_once": True,
            "reference_truth_reads_before_this_freeze": 0}, resource)
        require_inputs(inputs)
        input_map = {r["unit"]: r["input"] for r in inputs}
        references, resource = stage("G_reference", [{"unit": r["unit"], "input": r["input"]} for r in inputs])
        freeze("reference_time", {"workers": references, "anchor_plan": core.frozen_plan(root, "H6")}, resource)
        fail_on_worker_errors(references, "reference", allow_domain=True)
        usable = [r for r in references if r["status"] == "complete"]
        predictions, resource = stage("G_prediction", [{"unit": r["unit"], "input": input_map[r["unit"]], "plan": r["candidate_plan"]} for r in usable])
        terminal = [r for r in references if r["status"] != "complete"]
        prediction = {"workers": sorted([legacy.saved_anchor(root), *predictions, *terminal], key=lambda r:r["unit"]),
            "denominator_geometries": 5, "new_truth_reads": 0, "saved_truth_reads": 0,
            "global_input_freeze_commit": freezes["inputs"], "reference_time_freeze_commit": freezes["reference_time"]}
        freeze("prediction", prediction, resource)
        fail_on_worker_errors(predictions, "prediction")
        if len(prediction["workers"]) != 5:
            raise core.PreparationError("global five-geometry prediction incomplete")
        prediction = core.read(out / "prediction/prediction.json")
        grounds, resource = stage("G_ground", [{"unit": r["unit"], "input": input_map[r["unit"]]} for r in usable])
        freeze("ground", {"workers": grounds, "prediction_commit": freezes["prediction"]}, resource)
        fail_on_worker_errors(grounds, "ground")
        ground_map = {r["unit"]: r for r in grounds}
        truths, resource = stage("G_truth", [{"unit": r["unit"], "input": input_map[r["unit"]], "plan": r["candidate_plan"], "ground": ground_map[r["unit"]]} for r in usable])
        # Anchor truth is read only after this recovery's committed global prediction.
        core.verify_bundle(root, out / "prediction", freezes["prediction"])
        anchor = legacy.saved_truth(root, ("H6",))
        truth = {"systems": {"H6_R1.00": anchor["systems"]["H6"], **{r["unit"]: {"ground": ground_map[r["unit"]]["ground"], "points": r["points"], "new_truth": 3} for r in truths if r["status"] == "complete"}},
            "workers": truths, "source_registry": anchor["source_registry"], "prediction_commit": freezes["prediction"]}
        freeze("truth", truth, resource)
        fail_on_worker_errors(truths, "truth")
        analysis = legacy.analyze_G(prediction, core.read(out / "truth/prediction.json"))
        core.verify_bundle(root, out / "prediction", freezes["prediction"])
    except Exception as error:
        failure = {"type": type(error).__name__, "reason": str(error), "second_recovery_authorized": False}
    tests = legacy.focused_tests(root)
    actions = Counter()
    for row in all_workers:
        actions.update(row["resource"]["counts"])
    limits = {"H6_Hamiltonian_generations": 4, "H6_CISD_generations": 4, "input_verification_h_matvecs": 4,
        "reference_pf_actions": 136, "reference_h_exponential_actions": 136,
        "candidate_cheap_pf_actions": 12, "candidate_h_exponential_actions": 12,
        "m1_pf_vector_actions": 96, "m1_h_matvecs": 96, "full_H_ground_solves": 4,
        "full_pf_unitary_builds": 12, "direct_Schur_solves": 12, "direct_truth_coordinates": 12, "target_phase_gaps": 12}
    if any(actions[k] > v for k,v in limits.items()):
        raise core.PreparationError("recovery global action ceiling exceeded")
    final = {"status": FAILURE if failure else SUCCESS, "failure": failure, "analysis": analysis,
        "original_failed_run": original, "recovery_actions": dict(actions), "recovery_caps": limits,
        "cumulative_generation_attempts": original["generation_attempts"] + actions["H6_Hamiltonian_generations"],
        "cumulative_CISD_attempts": original["CISD_attempts"] + actions["H6_CISD_generations"],
        "independent_new_geometries": 4, "denominator_geometries_including_anchor": 5,
        "Track_R_accepted_unchanged": TRACK_R_COMMIT, "recovery_amendment_commit": source["content_commit"],
        "freezes": dict(freezes), "post_tests": tests, "started_utc": start_utc, "ended_utc": core.utc(),
        "total_wall_seconds": time.perf_counter() - started, "scientific_retry": 0, "technical_retry": 0,
        "authorized_recovery_run_number": 1, "old_formal_packages_changed": False,
        "prospective_runtime_partial_truth_access": 0, "GPU_science_operations": 0,
        "claim_scope": "preregistered empirical mechanism; no certificate, scaling, independent-sample or joint net-cost claim"}
    freeze("analysis" if analysis is not None else "STOPPED", final,
        {"monitors": monitors, "final_machine_inventory": core.machine_inventory(out)})
    if analysis is not None:
        legacy.render(out, "G", analysis)
    print(json.dumps({"status": final["status"], "freezes": freezes, "recovery_actions": dict(actions), "failure": failure}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("seal", "run"))
    args = parser.parse_args()
    (seal if args.command == "seal" else run)(Path.cwd().resolve())


if __name__ == "__main__":
    main()
