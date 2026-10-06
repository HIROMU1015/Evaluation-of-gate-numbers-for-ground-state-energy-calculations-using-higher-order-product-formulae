"""Bounded same-H truth and immutable scoring for the frozen prospective study."""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
from types import SimpleNamespace

import numpy as np
from scipy.linalg import eigh, schur

import prospective_candidate_prediction as p
import prospective_input_reference as prep
import run_prospective_candidate_prediction as prediction_runner

BASE = "533a52ca9eb20c5ab2281a9c4efbf37ff21fd838"
PREDICTION_SHA = "ac70d9d3fc02ce538f75678a5977be3aca507d2271a652487ae4b6d73bf3447d"
CHEAP_COMMIT = "7ab0887aa19ee3446de66724dc2a866ecd0c3064"
HELPER = "review_response/_pf_first_study_s0_exact_time_scoring_base.py"
HELPER_SHA = "a4b32ba8456d74acb072601b4dee0f3a6162be5d591ff4d79f08378f32250619"
DOC = "docs/second_study_v2/prospective_truth_scoring_20261006"
OUTPUT = "artifacts/prospective_truth_scoring_20261006"
MANIFEST = "implementation_manifest_v2.json"
SUCCESS = "prospective_truth_scoring_complete_review_required"
SOURCES = (f"{DOC}/approved_truth_scoring_authorization.md", f"{DOC}/authorization.json",
           f"{DOC}/method.json", f"{DOC}/protocol.md",
           "review_response/prospective_truth_scoring.py",
           "review_response/run_prospective_truth_scoring.py",
           "review_tests/test_prospective_truth_scoring.py")
TRUTH_FILES = ("truth.json", "TRUTH_FROZEN.json", "source_audit.json", "resource_audit.json",
               "access_audit.json", "pre_truth_gate.json", "pre_tests.json", "pre_tests.log")
FINAL_FILES = ("scoring.json", "SCORING_FROZEN.json", "COMPLETE.json", "summary.md", "handoff.md",
               "source_audit.json", "resource_audit.json", "access_audit.json", "test_audit.json",
               "post_tests.json", "post_tests.log")
LIMITS = {"exact_ground_solves": 13, "full_PF_materializations": 39, "direct_Schur_solves": 39}
ZERO = ("new_candidate_cheap_actions", "new_M1_actions", "new_reference_actions",
        "new_geometry_time_PF_rank", "gap_eigensolves", "certificate_gap_acquisitions",
        "scientific_retries", "technical_retries", "GPU_operations", "historical_truth_array_reads")
EXCLUDED_M1 = {"CH2_R1.40_r1.2", "CH2_R1.70_r1.0"}


def prediction_gate(root):
    root = Path(root)
    inherited = p.source_gate(root)
    p.git(root, "merge-base", "--is-ancestor", BASE, "HEAD")
    directory = root / p.OUTPUT
    paths = p.git(root, "ls-tree", "-r", "--name-only", BASE, p.OUTPUT).decode().splitlines()
    if len(paths) != 28 or set(paths) != set(p.git(root, "ls-files", "--", p.OUTPUT).decode().splitlines()):
        raise prep.PreparationError("frozen prediction file set changed")
    for name in paths:
        p.verify_blob(root, name, BASE)
    for phase, names in (("cheap", prediction_runner.CHEAP_FILES), ("m1", prediction_runner.M1_FILES),
                         ("global", prediction_runner.FINAL_FILES)):
        p.require_members(p.verify_package(root, directory / phase, BASE), names)
    cheap = prediction_runner.frozen_phase(root, directory, "cheap", CHEAP_COMMIT)
    m1 = prediction_runner.frozen_phase(root, directory, "m1", BASE)
    protocol, specs, plan, identities = p.preparation_gate(root)
    p.check_rows(cheap["rows"], plan)
    p.check_rows(m1["rows"], plan)
    marker = prep.read(directory / "global/PREDICTION_FROZEN.json")
    prediction = prep.read(directory / "global/prediction.json")
    if (prep.sha_file(directory / "global/prediction.json") != PREDICTION_SHA or
            marker["prediction_sha256"] != PREDICTION_SHA or marker["truth_opened"] is not False or
            marker["status"] != p.SUCCESS or marker["condition_count"] != 16 or
            marker["family_units"] != 4 or marker["ready_count"] != 13 or marker["coordinate_count"] != 39):
        raise prep.PreparationError("prediction hash/count/truth barrier changed")
    rebuilt = p.global_prediction(root, protocol, specs, plan, identities, cheap, m1)
    if rebuilt != prediction or prediction["M1_candidate_abstentions"] != 39 or prediction["M1_condition_abstentions"] != 13:
        raise prep.PreparationError("frozen gamma/rank/width/adoption/prediction differs")
    for point in m1["rows"]:
        if point["coordinate_id"] in EXCLUDED_M1 and "h_ritz_residual" not in point["failure_reasons"]:
            raise prep.PreparationError("pre-truth h_ritz_residual failure changed")
    return prediction, protocol, specs, plan, identities, {
        **inherited, "prediction_origin_result_commit": BASE, "verified_prediction_snapshot_commit": BASE,
        "prediction_sha256": PREDICTION_SHA, "prediction_files_verified": 28,
        "candidate_plan_sha256": prep.sha_file(directory / "global/candidate_plan.json"),
        "cheap_manifest_sha256": prep.sha_file(directory / "cheap/manifest.json"),
        "M1_manifest_sha256": prep.sha_file(directory / "m1/manifest.json"),
        "global_manifest_sha256": prep.sha_file(directory / "global/manifest.json"),
        "truth_opened_at_prediction_freeze": False, "prediction_modified": False}


def source_gate(root):
    values = prediction_gate(root)
    manifest_path = Path(root) / DOC / MANIFEST
    p.verify_blob(root, str(manifest_path.relative_to(root)), "HEAD")
    manifest = prep.read(manifest_path)
    if manifest.get("manifest_self_excluded") is not True or {r["path"] for r in manifest["files"]} != set(SOURCES):
        raise prep.PreparationError("truth/scorer source manifest membership differs")
    content = manifest["content_commit"]
    p.git(root, "merge-base", "--is-ancestor", BASE, content)
    p.git(root, "merge-base", "--is-ancestor", content, "HEAD")
    p.verify_manifest(root, manifest["files"])
    for row in manifest["files"]:
        p.verify_blob(root, row["path"], content)
    p.verify_blob(root, HELPER, BASE)
    if prep.sha_file(Path(root) / HELPER) != HELPER_SHA:
        raise prep.PreparationError("direct helper source differs")
    method = prep.read(Path(root) / DOC / "method.json")
    if method["ground_solver"] != "scipy.linalg.eigh(driver='evd', check_finite=True)" or method["truth_gates"] != values[1]["truth_future"]:
        raise prep.PreparationError("same-H solver or frozen numerical contract differs")
    audit = {**values[-1], "truth_implementation_origin_commit": content,
             "verified_truth_source_snapshot_commit": p.git(root, "rev-parse", "HEAD").decode().strip(),
             "truth_sources": manifest["files"], "truth_manifest_sha256": prep.sha_file(manifest_path),
             "pre_action_source_revision": manifest.get("pre_action_source_revision"),
             "direct_helper_sha256": HELPER_SHA, "method_sha256": prep.sha_file(Path(root) / DOC / "method.json")}
    return (*values[:-1], audit)


def seal_source(root):
    p.require_clean(root)
    p.check_remote(root)
    content = p.git(root, "rev-parse", "HEAD").decode().strip()
    p.git(root, "merge-base", "--is-ancestor", BASE, content)
    rows = []
    for name in SOURCES:
        p.verify_blob(root, name, content)
        rows.append({"path": name, "sha256": prep.sha_file(Path(root) / name),
                     "bytes": (Path(root) / name).stat().st_size,
                     "origin_result_commit": p.git(root,"log","-1","--format=%H",content,"--",name).decode().strip(),
                     "verified_snapshot_commit": content})
    path = Path(root) / DOC / MANIFEST
    if path.exists():
        raise prep.PreparationError("implementation seal already exists")
    revision_path = Path(root)/OUTPUT/".private/pre_action_source_revision_audit.json"
    revision = prep.read(revision_path) if revision_path.exists() else None
    prep.write(path, {"content_commit": content, "prediction_commit": BASE,
                      "manifest_self_excluded": True, "files": rows, "pre_action_source_revision": revision})


def disk_bytes(roots):
    seen, total = set(), 0
    for directory in roots:
        for parent, dirs, files in os.walk(directory, followlinks=False):
            links = [Path(parent)/d for d in dirs if (Path(parent)/d).is_symlink()]
            dirs[:] = [d for d in dirs if not (Path(parent) / d).is_symlink()]
            for path in [*links, *(Path(parent)/name for name in files)]:
                try:
                    stat = path.lstat() if path.is_symlink() else path.stat()
                except FileNotFoundError:
                    continue  # atomic checkpoint replacement during monitoring
                inode = (stat.st_dev, stat.st_ino)
                if inode not in seen:
                    total += max(stat.st_size, stat.st_blocks * 512)
                    seen.add(inode)
    return total


def allocation_gate(data, output, evidence_root, expected_roots):
    prep.allocation_gate(data, output, evidence_root=evidence_root)
    if (data.get("allocation_phase") != "prospective_truth_scoring" or data.get("fresh_allocation") is not True or
            data.get("prediction_allocation_inherited") is not False or data.get("deadline_renewed") is not False):
        raise prep.PreparationError("fresh truth allocation required; no inheritance or renewal")
    ceilings = {"usable_cpu_quota": 16, "usable_ram_bytes": 128*2**30, "workers": 4,
                "worker_rss_limit_bytes": 12*2**30, "worker_wall_seconds": 7200,
                "direct_coordinate_wall_seconds": 1800, "job_wall_seconds": 43200,
                "writable_disk_quota_bytes": 2*2**30}
    for key, maximum in ceilings.items():
        if not isinstance(data.get(key), (int, float)) or not 0 < data[key] <= maximum:
            raise prep.PreparationError("truth allocation ceiling invalid: " + key)
    if data["coordinator_reserved_ram_bytes"] != 32*2**30 or data.get("reserved_disk_bytes", 0) < 128*2**20:
        raise prep.PreparationError("coordinator/stop reserve invalid")
    starts = datetime.fromisoformat(data["starts_UTC"])
    expires = datetime.fromisoformat(data["expires_UTC"])
    now = datetime.now(timezone.utc)
    if starts.tzinfo is None or starts > now or expires <= now or (expires-starts).total_seconds() > data["job_wall_seconds"]:
        raise prep.PreparationError("fresh start/deadline invalid")
    roots = {Path(s).resolve() for s in data["cumulative_disk_roots"]}
    if roots != {Path(s).resolve() for s in expected_roots}:
        raise prep.PreparationError("cumulative disk roots incomplete")
    return data


def resource_guard(data):
    if datetime.now(timezone.utc) >= datetime.fromisoformat(data["expires_UTC"]):
        raise prep.PreparationError("fresh allocation deadline reached")
    used = disk_bytes(data["cumulative_disk_roots"])
    reserve = data["reserved_disk_bytes"]
    fs = os.statvfs(data["approved_output_root"])
    if used + reserve > data["writable_disk_quota_bytes"] or fs.f_bavail*fs.f_frsize < reserve:
        raise prep.PreparationError("cumulative disk quota/128 MiB stop reserve reached")
    return used


class TruthLedger(prep.ReferenceLedger):
    def __init__(self, rss_limit=12*2**30, checkpoint=None, guard=lambda: None):
        self.guard = guard
        super().__init__(rss_limit)
        self.counts = Counter({key: 0 for key in (*LIMITS, *ZERO, "target_phase_gap_diagnostics")})
        self.checkpoint = checkpoint

    def charge(self, name):
        local = {"exact_ground_solves": 1, "full_PF_materializations": 3, "direct_Schur_solves": 3}
        if name not in local or self.counts[name] >= local[name]:
            raise prep.PreparationError("per-condition attempted scientific action cap reached")
        self.guard()
        self.counts[name] += 1
        if self.checkpoint:
            prep.write(self.checkpoint, self.payload())

    def check_memory(self):
        self.guard()
        super().check_memory()


def direct_helper(root):
    path = Path(root) / HELPER
    if prep.sha_file(path) != HELPER_SHA:
        raise prep.PreparationError("direct helper hash mismatch")
    definitions = {n.name: n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef)}
    nodes = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    nodes += [definitions[name] for name in ("_phase_distance", "direct_branch_point")]
    scope = {"np": np, "time": time, "schur": schur,
             "practical": SimpleNamespace(_cost=lambda *args: None)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), "exec"), scope)
    return scope["direct_branch_point"]


def ground_point(h, identity, rule, ledger):
    dense = np.asarray(h.toarray() if hasattr(h, "toarray") else h, dtype=np.complex128)
    if dense.shape != (identity["sector_dimension"],)*2 or not np.all(np.isfinite(dense)) or prep.array_hash(dense) != identity["H_dense_numpy_v1"]:
        raise prep.PreparationError("same-H finite matrix identity gate failed")
    ledger.charge("exact_ground_solves")
    clock = time.perf_counter()
    values, vectors = eigh(dense, driver="evd", check_finite=True)
    energy, vector = float(values[0]), np.asarray(vectors[:, 0], dtype=np.complex128)
    gap = float(values[1]-values[0]) if len(values) > 1 else None
    norm = abs(float(np.linalg.norm(vector))-1.)
    residual = float(np.linalg.norm(dense@vector-energy*vector))
    ledger.counts["ground_verification_H_matvecs"] += 1
    reasons = []
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(vector)):
        reasons.append("nonfinite_ground")
    if gap is None or gap <= rule["ground_ambiguity_hartree"]:
        reasons.append("ground_ambiguity")
    if not math.isfinite(norm) or norm > rule["norm"]:
        reasons.append("ground_norm")
    if not math.isfinite(residual) or residual > rule["ground_residual_hartree"]:
        reasons.append("ground_eigenpair_residual")
    record = {"status": "ground_indeterminate" if reasons else "same_H_ground_valid", "failure_reasons": reasons,
              "energy_hartree": energy, "first_excitation_gap_hartree": gap,
              "normalization_residual": norm, "eigenpair_residual_hartree": residual,
              "ground_vector_numpy_v1": prep.array_hash(vector), "H_dense_numpy_v1": identity["H_dense_numpy_v1"],
              "sector_indices_numpy_v1": identity["sector_indices_numpy_v1"],
              "sector_dimension": identity["sector_dimension"], "condition": identity["condition"],
              "removed_scalar_hartree": identity["removed_scalar_hartree"], "constant_policy": identity["constant_policy"],
              "solver": "scipy.linalg.eigh(driver='evd', check_finite=True)",
              "solver_seconds": time.perf_counter()-clock, "computed": True, "reused": False,
              "ground_claim": "same_H_fixed_population_sector_only_not_global_molecular_ground"}
    ledger.check_memory()
    return record, None if reasons else vector


def full_unitary(adapter, t, ledger):
    ledger.charge("full_PF_materializations")
    clock = time.perf_counter()
    unitary = np.eye(adapter.h.shape[0], dtype=np.complex128)
    gates = {}
    for index, weight in adapter.steps:
        key = (index, weight)
        if key not in gates:
            gates[key] = prep.component_exponential(adapter.spectra[index], float(t*weight))
            ledger.counts["truth_component_gate_materializations"] += 1
        unitary = gates[key] @ unitary
        ledger.counts["truth_sparse_matrix_dense_matrix_multiplies"] += 1
        ledger.check_memory()
    if not np.all(np.isfinite(unitary)):
        raise prep.PreparationError("full PF finite gate failed")
    ledger.timings["full_PF_materialization"] += time.perf_counter()-clock
    return unitary


def truth_quality(point, rule):
    required = ("signed_direct_shift_hartree", "minimum_selected_phase_gap_radians",
                "ground_state_overlap_probability", "previous_branch_overlap_probability",
                "unitarity_residual_frobenius", "eigenpair_residual_2_norm")
    reasons = ["nonfinite_or_missing_"+key for key in required if not finite(point.get(key))]
    if not reasons:
        for key, ceiling in (("unitarity_residual_frobenius", rule["unitarity_frobenius"]),
                             ("eigenpair_residual_2_norm", rule["eigenpair_residual"])):
            if point[key] > ceiling:
                reasons.append(key)
        if point["minimum_selected_phase_gap_radians"] <= rule["phase_cluster_ambiguity_rad"] or point.get("phase_cluster_size", 1) != 1:
            reasons.append("unresolved_phase_cluster")
        for key in ("ground_state_overlap_probability", "previous_branch_overlap_probability"):
            if point[key] < rule["overlap_minimum"]:
                reasons.append(key)
    return {"status": "truth_branch_indeterminate" if reasons else "resolved",
            "physical_branch_valid": not reasons, "failure_reasons": reasons}


def missing_point(coordinate, reason):
    return {**coordinate, "attempted": False, "status": "missing_indeterminate", "reason": reason,
            "quality": {"status": "missing_indeterminate", "physical_branch_valid": False,
                        "failure_reasons": [reason]}, "signed_direct_shift_hartree": None}


def finite(value):
    return value is not None and isinstance(value, (int, float, np.number)) and math.isfinite(float(value))


def check_coordinate(cheap, m1, truth):
    if cheap["coordinate_id"] != m1["coordinate_id"] or m1["coordinate_id"] != truth["coordinate_id"]:
        raise prep.PreparationError("scoring exact coordinate identity mismatch")
    for row in (cheap, m1, truth):
        if float(row["time"]).hex() != truth["time_hex"] or row["time_hex"] != truth["time_hex"]:
            raise prep.PreparationError("scoring exact binary64 time mismatch")


def score_coordinate(cheap, m1, truth, ground, protocol):
    check_coordinate(cheap, m1, truth)
    epsilon = protocol["resource"]["epsilon_E"]
    valid = truth["quality"]["physical_branch_valid"]
    direct = truth.get("signed_direct_shift_hartree")
    c = abs(cheap["delta_C_hartree"])
    e = abs(direct) if finite(direct) else None
    e_c = abs(cheap["delta_C_hartree"]-direct) if finite(direct) else None
    delta, width = m1["delta_M_hartree"], m1["width_M_hartree"]
    e_m = abs(delta-direct) if finite(delta) and finite(direct) else None
    gap = truth.get("minimum_selected_phase_gap_radians")
    t = truth["time"]
    branch = bool(e_m < gap/(2*t)) if valid and e_m is not None and finite(gap) and gap > 0 else None
    coverage = bool(e_m <= width) if valid and e_m is not None and finite(width) and width >= 0 else None
    gamma_req = (epsilon-c)/(epsilon-e) if valid and e is not None and epsilon>c and epsilon>e else None
    core = m1["core_prediction"]
    primary = next((r for r in core["prefixes"] if r["dimension"] == core["primary_dimension_used"]), {})
    h_ritz = primary.get("h_reference_energy_hartree")
    absolute_estimate = primary.get("selected_unwrapped_energy_hartree")
    e0 = ground.get("energy_hartree") if ground else None
    absolute_target = e0+direct if valid and finite(e0) and finite(direct) else None
    absolute_difference = absolute_estimate-absolute_target if finite(absolute_estimate) and finite(absolute_target) else None
    same_lift_diagnostic = valid and absolute_difference is not None and abs(absolute_difference)<math.pi/t
    # A small point/gap error does not certify the identity of an empirical Ritz
    # branch. The frozen package provides no exact PF-vector correspondence.
    decomposition = {"status": "indeterminate", "reason": "frozen_M1_has_no_confirmed_physical_absolute_target_correspondence",
                     "PF_component_hartree": None, "H_reference_component_hartree": None,
                     "same_H_and_sector_verified": bool(valid and ground and ground["status"] == "same_H_ground_valid"),
                     "physical_branch_confirmed_for_decomposition": False}
    return {"condition_id": cheap["condition_id"], "coordinate_id": cheap["coordinate_id"], "time": t,
            "time_hex": truth["time_hex"], "truth_valid": valid, "truth_status": truth["quality"]["status"],
            "delta_C_hartree": cheap["delta_C_hartree"], "delta_M_hartree": delta,
            "delta_direct_hartree": direct, "e_hartree": e, "c_hartree": c,
            "underestimation_hartree": None if e is None else e-c,
            "gamma_req_truth_diagnostic": gamma_req, "gamma_req_changes_policy": False,
            "cheap_point_error_hartree": e_c, "M1_point_error_hartree": e_m,
            "M1_vs_cheap_point_error_difference_hartree": None if e_m is None or e_c is None else e_m-e_c,
            "width_M_hartree": width, "width_nonfinite_provenance": m1["nonfinite_fields"],
            "empirical_width_covers": coverage, "branch_gap_compatibility_diagnostic": branch,
            "g_phase_rad": gap, "g_E_hartree": gap/t if finite(gap) else None,
            "g_chord": 2*math.sin(gap/2) if finite(gap) else None, "g_rho_others": None,
            "M1_frozen_abstained": not m1["eligible"], "M1_failure_reasons_preserved": list(m1["failure_reasons"]),
            "M1_accepted_performance": False, "M1_pre_truth_h_ritz_failure": cheap["coordinate_id"] in EXCLUDED_M1,
            "diagnostics_do_not_change_adoption": True, "H_Ritz_reference_hartree": h_ritz,
            "absolute_PF_estimate_hartree": absolute_estimate, "absolute_PF_target_hartree": absolute_target,
            "absolute_difference_hartree": absolute_difference if same_lift_diagnostic else None,
            "same_lift_compatibility_diagnostic": bool(same_lift_diagnostic),
            "absolute_lift_is_confirmed_physical_branch": False, "unwrap_integers_compared": False,
            "PF_H_reference_decomposition": decomposition,
            "same_time_cost_free_oracle_budget": p.budget(t, e, cheap["K"], protocol) if valid and e is not None else None}


def score_decision(condition_id, arm, action, gamma, cheap, truth, protocol):
    epsilon, beta = protocol["resource"]["epsilon_E"], protocol["resource"]["beta"]
    if action is None:
        return {"condition_id": condition_id, "arm": arm, "gamma": gamma, "status": "frozen_abstention",
                "safe": None, "unsafe": None, "safe_target_met": None, "fallback": False}
    t, budget = action["time"], action["budget"]
    if float(t).hex() != truth["time_hex"] or action["time_hex"] != truth["time_hex"]:
        raise prep.PreparationError("frozen selected decision time mismatch")
    if not finite(budget) or budget <= 0 or not finite(t) or t <= 0:
        raise prep.PreparationError("invalid frozen budget; never repair or ceil")
    if action.get("budget_hex", float(budget).hex()) != float(budget).hex():
        raise prep.PreparationError("frozen budget binary64 identity differs")
    point = next(r for r in cheap["cheap"] if r["time_hex"] == truth["time_hex"])
    valid = truth["quality"]["physical_branch_valid"]
    direct = truth.get("signed_direct_shift_hartree")
    c = abs(point["delta_C_hartree"])
    e = abs(direct) if finite(direct) else None
    margin = (1-1/gamma)*(epsilon-c)
    slack = margin-(e-c) if e is not None else None
    qpe = beta*point["K"]/(t*budget)
    total = e+qpe if e is not None else None
    safe = bool(total <= epsilon) if valid and total is not None else None
    anchor = cheap["B0"]
    target = finite(anchor["budget"]) and t>anchor["time"] and budget<=.9*anchor["budget"]
    return {"condition_id": condition_id, "arm": arm, "gamma": gamma, "time": t, "time_hex": truth["time_hex"],
            "coordinate_id": point["coordinate_id"], "frozen_budget": budget, "frozen_budget_hex": float(budget).hex(),
            "e_hartree": e, "c_hartree": c, "underestimation_hartree": None if e is None else e-c,
            "M_gamma_hartree": margin, "safety_slack_hartree": slack, "qpe_error_hartree": qpe,
            "total_error_hartree": total, "epsilon_E_hartree": epsilon, "safe": safe,
            "unsafe": None if safe is None else not safe, "safe_target_met": bool(safe and target) if safe is not None else None,
            "truth_valid": valid, "raw_arithmetic_safe": bool(total <= epsilon) if total is not None else None,
            "B_over_B0": budget/anchor["budget"] if finite(anchor["budget"]) and anchor["budget"]>0 else None,
            "fallback": False, "benchmark_only": arm == "B0", "budget_or_policy_modified": False}


def native_oracle(coordinates):
    complete = len(coordinates) == 3 and all(r["truth_valid"] for r in coordinates)
    candidates = [r for r in coordinates if finite(r["same_time_cost_free_oracle_budget"])]
    best = min(candidates, key=lambda r: (r["same_time_cost_free_oracle_budget"], r["time"])) if candidates else None
    choice = None if best is None else {"coordinate_id": best["coordinate_id"], "time": best["time"],
                                       "time_hex": best["time_hex"], "budget": best["same_time_cost_free_oracle_budget"]}
    return {"complete_native_3_candidate_oracle": complete, "complete_oracle": choice if complete else None,
            "available_truth_minimum_diagnostic": choice, "cost_free_truth_headroom_only": True,
            "operational_intervention": False, "classical_acquisition_cost_included": False}


def verify_truth_identity(record, tr, protocol):
    identity = record["input_identity"]
    ground = tr.get("ground")
    if ground is None or tr.get("condition") != record["condition"] or ground["condition"] != record["condition"]:
        raise prep.PreparationError("truth same-condition/ground provenance incomplete")
    for key in ("H_dense_numpy_v1", "sector_indices_numpy_v1", "sector_dimension", "removed_scalar_hartree", "constant_policy"):
        if ground.get(key) != identity[key]:
            raise prep.PreparationError("same-H ground/source identity mismatch: "+key)
    if ground["solver"] != "scipy.linalg.eigh(driver='evd', check_finite=True)":
        raise prep.PreparationError("ground solver changed after freeze")
    if ground["status"] == "same_H_ground_valid":
        rule = protocol["truth_future"]
        if (not finite(ground["normalization_residual"]) or ground["normalization_residual"]>rule["norm"] or
                not finite(ground["eigenpair_residual_hartree"]) or ground["eigenpair_residual_hartree"]>rule["ground_residual_hartree"] or
                not finite(ground["first_excitation_gap_hartree"]) or ground["first_excitation_gap_hartree"]<=rule["ground_ambiguity_hartree"]):
            raise prep.PreparationError("ground validity conflicts with frozen numerical gates")
    cheap = record["predictions"]["cheap"]
    if [r["coordinate_id"] for r in tr["points"]] != [r["coordinate_id"] for r in cheap]:
        raise prep.PreparationError("truth frozen coordinate order differs")
    for point, coordinate in zip(tr["points"], cheap, strict=True):
        for key in ("condition_id", "coordinate_id", "time", "time_hex", "ratio", "ratio_hex", "t_ref", "t_ref_hex", "K"):
            if point[key] != coordinate[key]:
                raise prep.PreparationError("truth coordinate/source identity mismatch: "+key)
        if not point["attempted"]:
            if point["quality"]["physical_branch_valid"] or point.get("signed_direct_shift_hartree") is not None:
                raise prep.PreparationError("unattempted truth received valid/scalar label")
            continue
        for key in ("H_dense_numpy_v1", "sector_indices_numpy_v1", "removed_scalar_hartree", "PF_sequence_hex", "ordered_pauli_groups_sha256"):
            if point.get(key) != identity[key]:
                raise prep.PreparationError("direct PF/source identity mismatch: "+key)
        if point["input_identity_sha256"] != record["input_identity_sha256"] or point["ground_vector_numpy_v1"] != ground["ground_vector_numpy_v1"]:
            raise prep.PreparationError("direct input/ground state hash mismatch")
        quality = truth_quality(point, protocol["truth_future"])
        if point["quality"]["physical_branch_valid"] != quality["physical_branch_valid"]:
            raise prep.PreparationError("truth validity conflicts with frozen direct gates")
        if point["quality"]["physical_branch_valid"] and ground["status"] != "same_H_ground_valid":
            raise prep.PreparationError("valid direct branch lacks valid same-H ground")


def score_all(prediction, truth, protocol):
    before = (prep.sha_json(prediction), prep.sha_json(truth))
    expected = {r["coordinate_id"] for c in prediction["conditions"] if c["predictions"] for r in c["predictions"]["cheap"]}
    points = {r["coordinate_id"]: r for c in truth["conditions"] for r in c.get("points", [])}
    if len(expected) != 39 or len(points) != 39 or set(points) != expected or len(truth["conditions"]) != 16:
        raise prep.PreparationError("immutable scoring requires all 16 condition/39 terminal coordinate records")
    by_condition = {r["condition_id"]: r for r in truth["conditions"]}
    if len(by_condition) != 16 or set(by_condition) != {c["condition"]["condition_id"] for c in prediction["conditions"]}:
        raise prep.PreparationError("truth denominator/conditions differ")
    coordinate_scores, decisions, conditions = [], [], []
    for record in prediction["conditions"]:
        spec = record["condition"]
        cid = spec["condition_id"]
        tr = by_condition[cid]
        frozen = record["predictions"]
        if frozen is None:
            if tr.get("points") or tr.get("ground") or any(tr.get("resource", {}).get("counts", {}).values()):
                raise prep.PreparationError("science performed for ineligible terminal condition")
            conditions.append({"condition": spec, "status": record["status"], "new_science_actions": 0,
                               "truth_status": "not_attempted_ineligible", "scored": False})
            continue
        verify_truth_identity(record, tr, protocol)
        m1_by_id = {r["coordinate_id"]: r for r in frozen["M1"]}
        rows = [score_coordinate(point, m1_by_id[point["coordinate_id"]], points[point["coordinate_id"]],
                                 tr.get("ground"), protocol) for point in frozen["cheap"]]
        coordinate_scores.extend(rows)
        anchor_point = next(r for r in frozen["cheap"] if r["ratio"] == .8)
        b0 = frozen["B0"]
        action = b0 if finite(b0["budget"]) else None
        decision_rows = [score_decision(cid, "B0", action, b0["gamma"], frozen, points[anchor_point["coordinate_id"]], protocol)]
        for arm in frozen["B1"]:
            action = arm["decision"]["selected"]
            selected_truth = points[action["coordinate_id"]] if action else points[anchor_point["coordinate_id"]]
            decision_rows.append(score_decision(cid, f"B1_gamma_{arm['gamma']}", action, arm["gamma"], frozen, selected_truth, protocol))
        decisions.extend(decision_rows)
        conditions.append({"condition": spec, "status": "immutable_scored", "truth_status": tr["status"],
                           "truth_valid_coordinates": sum(r["truth_valid"] for r in rows),
                           "scored": any(r["truth_valid"] for r in rows), "native_oracle": native_oracle(rows),
                           "M1_frozen_condition_abstention": frozen["M1_decision"]["selected"] is None,
                           "M1_accepted_performance_count": 0})
    if before != (prep.sha_json(prediction), prep.sha_json(truth)):
        raise prep.PreparationError("scorer modified immutable inputs")
    arms = ["B0", *[f"B1_gamma_{g}" for g in protocol["resource"]["gammas"]]]
    axes = {arm: {"attempted_condition_denominator": 16, "candidate_ready_denominator": 13,
                  "safe": sum(r.get("safe") is True for r in decisions if r["arm"] == arm),
                  "unsafe": sum(r.get("safe") is False for r in decisions if r["arm"] == arm),
                  "indeterminate_or_abstain": sum(r.get("safe") is None for r in decisions if r["arm"] == arm),
                  "safe_target_met": sum(r.get("safe_target_met") is True for r in decisions if r["arm"] == arm)} for arm in arms}
    ready = [r for r in truth["conditions"] if r["condition_id"] not in p.TERMINAL]
    denominator = {"attempted_conditions": 16, "family_units": 4, "candidate_ready_conditions": 13,
                   "frozen_coordinates": 39, "ground_attempted_conditions": sum(r["resource"]["counts"]["exact_ground_solves"] for r in ready),
                   "ground_valid_conditions": sum(r.get("ground", {}).get("status") == "same_H_ground_valid" for r in ready),
                   "truth_attempted_conditions": sum(r["resource"]["counts"]["full_PF_materializations"]>0 for r in ready),
                   "truth_attempted_coordinates": sum(r["resource"]["counts"]["direct_Schur_solves"] for r in ready),
                   "truth_valid_coordinates": sum(r["truth_valid"] for r in coordinate_scores),
                   "truth_complete_valid_conditions": sum(all(q["quality"]["physical_branch_valid"] for q in r["points"]) for r in ready),
                   "scored_coordinates": sum(r["truth_valid"] for r in coordinate_scores),
                   "scored_conditions": sum(r["scored"] for r in conditions)}
    return {"status": SUCCESS, "denominators": denominator, "coordinate_scores": coordinate_scores,
            "decision_scores": decisions, "conditions": conditions, "B0_B1_evidence_axes": axes,
            "M1_candidate_abstentions_preserved": 39, "M1_condition_abstentions_preserved": 13,
            "M1_accepted_performance_count": 0, "pre_truth_h_ritz_exclusions": sorted(EXCLUDED_M1),
            "empirical_width_diagnostic_covered": sum(r["empirical_width_covers"] is True for r in coordinate_scores),
            "branch_gap_diagnostic_compatible": sum(r["branch_gap_compatibility_diagnostic"] is True for r in coordinate_scores),
            "prediction_modified": False, "truth_modified": False, "basic_units": "four families; within-family geometries and three times are not independent samples",
            "CH2_stratum": "repository_tracked_family_unseen", "CH2_ground_claim": "(5,3) fixed-population sector only",
            "width_is_certificate": False, "oracle_is_operational_intervention": False,
            "next_science_authorized": False}


def write_bundle(directory, payload_name, marker_name, payload, source, resource, access, extra):
    if directory.exists():
        raise prep.PreparationError("immutable bundle already exists; no overwrite")
    directory.mkdir(parents=True)
    prep.write(directory / payload_name, payload)
    prep.write(directory / marker_name, {"created_UTC": prep.utc(), "prediction_origin_result_commit": BASE,
                                        "payload_sha256": prep.sha_file(directory / payload_name), "payload_name": payload_name})
    for name, data in (("source_audit.json", source), ("resource_audit.json", resource), ("access_audit.json", access)):
        prep.write(directory / name, data)
    for name, value in extra.items():
        if isinstance(value, bytes):
            (directory/name).write_bytes(value)
        elif isinstance(value, str):
            (directory/name).write_text(value)
        else:
            prep.write(directory/name, value)
    names = (*TRUTH_FILES,) if payload_name == "truth.json" else (*FINAL_FILES,)
    if set(f.name for f in directory.iterdir()) != set(names):
        raise prep.PreparationError("exact public bundle members required")
    p.make_manifest(directory, names)
    return [*names, "manifest.json"]


def commit_bundle(root, directory, names, message):
    p.require_clean(root)
    p.check_remote(root)
    paths = [str((directory/name).relative_to(root)) for name in names]
    p.git(root, "add", "--", *paths)
    if set(p.git(root, "diff", "--cached", "--name-only").decode().splitlines()) != set(paths):
        raise prep.PreparationError("unexpected staged file set")
    p.git(root, "commit", "-m", message)
    commit = p.git(root, "rev-parse", "HEAD").decode().strip()
    if set(p.git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).decode().splitlines()) != set(paths):
        raise prep.PreparationError("unexpected committed file set")
    verify_bundle(root, directory, commit)
    return commit


def verify_bundle(root, directory, commit):
    manifest = p.verify_package(root, directory, commit)
    names = TRUTH_FILES if (directory/"TRUTH_FROZEN.json").exists() else FINAL_FILES
    p.require_members(manifest, names)
    marker = prep.read(directory/("TRUTH_FROZEN.json" if names == TRUTH_FILES else "SCORING_FROZEN.json"))
    if marker["payload_sha256"] != prep.sha_file(directory/marker["payload_name"]):
        raise prep.PreparationError("frozen payload hash changed")
