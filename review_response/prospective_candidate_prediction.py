"""Fixed prospective candidate policies, vector actions, and integrity gates.

No ground/truth/scoring loader is provided. P3 sources remain unchanged.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import time

import numpy as np

import prospective_input_reference as prep
import pf_spectral_recoverability_d2 as d2

BASE = "ec87adf35a5f8c2812557812ece34f3d41be3da1"
INPUT_COMMIT = "d7a8295b33977afe557975284b0103353416d706"
PREP = "artifacts/prospective_input_reference_preparation_20261005"
DOC = "docs/second_study_v2/prospective_prediction_20261006"
OUTPUT = "artifacts/prospective_candidate_M1_prediction_20261006"
SUCCESS = "prospective_candidate_M1_prediction_freeze_complete_review_required"
NEW_SOURCES = (
    f"{DOC}/approved_prediction_authorization.md",
    f"{DOC}/authorization.json",
    "review_response/prospective_candidate_prediction.py",
    "review_response/run_prospective_candidate_prediction.py",
    "review_tests/test_prospective_candidate_prediction.py",
    "review_response/gpu_pf_study2_prospective_prediction_prompt_20261006.md",
)
FORBIDDEN = (
    "exact_ground_solves", "full_PF_materializations", "direct_truth_actions",
    "gap_actions", "performance_scoring", "truth_array_reads", "GPU_operations",
    "B2_actions", "H1_actions", "reference_pf_actions", "reference_h_exponential_actions",
)
TERMINAL = {
    "LiH_R1.40": "candidate_time_domain_ineligible",
    "LiH_R2.60": "candidate_time_domain_ineligible",
    "LiF_R2.60": "input_reference_ineligible",
}
LIMITS = {"candidate_pf_vector_actions": 39, "candidate_h_exponential_actions": 39,
          "M1_pf_vector_actions": 312, "M1_h_matvecs": 312}


def git(root, *args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(root), *args])


def require_clean(root):
    if git(root, "diff", "--name-only").strip() or git(root, "diff", "--cached", "--name-only").strip():
        raise prep.PreparationError("tracked/staged files must be unchanged")


def check_remote(root):
    expected = "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
    allowed = {"https://github.com/" + expected, "git@github.com:" + expected}
    for args in (("remote", "get-url", "--all", "origin"),
                 ("remote", "get-url", "--push", "--all", "origin")):
        urls = git(root, *args).decode().splitlines()
        if not urls or any(url.removesuffix(".git") not in allowed for url in urls):
            raise prep.PreparationError("unexpected repository fetch/push URL")
    branch = git(root, "branch", "--show-current").decode().strip()
    if not branch or branch in {"main", "master"}:
        raise prep.PreparationError("dedicated research branch required")
    return branch


def verify_blob(root, relative, commit):
    path = Path(root) / relative
    if path.is_symlink() or path.read_bytes() != git(root, "show", f"{commit}:{relative}"):
        raise prep.PreparationError("commit blob differs: " + relative)


def safe_member(directory, relative):
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise prep.PreparationError("unsafe manifest member")
    directory = Path(directory)
    path = directory / relative
    for parent in (directory, path, *path.parents):
        if parent.is_symlink():
            raise prep.PreparationError("linked frozen input/manifest member")
    if not path.is_file():
        raise prep.PreparationError("missing frozen input/manifest member")
    return path


def verify_manifest(directory, entries):
    if len(entries) != len({row["path"] for row in entries}):
        raise prep.PreparationError("duplicate manifest entry")
    for row in entries:
        path = safe_member(directory, row["path"])
        if prep.sha_file(path) != row["sha256"] or ("bytes" in row and path.stat().st_size != row["bytes"]):
            raise prep.PreparationError("manifest hash/size mismatch: " + row["path"])


def source_gate(root):
    root = Path(root)
    require_clean(root)
    check_remote(root)
    git(root, "merge-base", "--is-ancestor", BASE, "HEAD")
    inherited_path = root / prep.DOC / "implementation_manifest.json"
    verify_blob(root, str(prep.DOC / "implementation_manifest.json"), BASE)
    inherited = prep.read(inherited_path)
    verify_manifest(root, inherited["files"])
    for row in inherited["files"]:
        verify_blob(root, row["path"], BASE)
    sealed_path = f"{DOC}/implementation_manifest.json"
    verify_blob(root, sealed_path, "HEAD")
    sealed = prep.read(root / sealed_path)
    if {r["path"] for r in sealed["files"]} != set(NEW_SOURCES):
        raise prep.PreparationError("new implementation manifest membership differs")
    git(root, "merge-base", "--is-ancestor", BASE, sealed["content_commit"])
    git(root, "merge-base", "--is-ancestor", sealed["content_commit"], "HEAD")
    verify_manifest(root, sealed["files"])
    for row in sealed["files"]:
        verify_blob(root, row["path"], sealed["content_commit"])
    return {"execution_snapshot_commit": git(root, "rev-parse", "HEAD").decode().strip(),
            "origin_implementation_commit": sealed["content_commit"],
            "verified_source_snapshot_commit": git(root, "rev-parse", "HEAD").decode().strip(),
            "preparation_result_snapshot_commit": BASE, "input_origin_result_commit": INPUT_COMMIT,
            "protocol_origin_commit": prep.P1_COMMIT, "verified_protocol_snapshot_commit": BASE,
            "inherited_files_verified": len(inherited["files"]),
            "new_files": sealed["files"], "implementation_manifest_sha256": prep.sha_file(root / sealed_path)}


def preparation_gate(root):
    root = Path(root)
    directory = root / PREP
    verify_blob(root, f"{PREP}/review_bundle_manifest.json", BASE)
    review_manifest = prep.read(directory / "review_bundle_manifest.json")
    verify_manifest(directory, review_manifest["files"])
    for row in review_manifest["files"]:
        verify_blob(root, f"{PREP}/{row['path']}", BASE)
    if prep.read(directory / "COMPLETE.json")["status"] != "prospective_input_reference_preparation_complete_review_required":
        raise prep.PreparationError("P3 preparation status differs")
    seal = prep.read(directory / "INPUT_FROZEN.json")
    for name in ["INPUT_FROZEN.json", *seal["input_files"]]:
        verify_blob(root, f"{PREP}/{name}", INPUT_COMMIT)
    protocol = prep.read(root / prep.DOC / "protocol.json")
    specifications = prep.read(root / prep.DOC / "conditions.json")
    plan = prep.read(directory / "candidate_plan.json")
    validate_plan(plan, specifications)
    identities = {}
    for spec in specifications:
        cid = spec["condition_id"]
        identity = prep.read(directory / "conditions" / cid / "input_identity.json")
        reference = prep.read(directory / "conditions" / cid / "reference_result.json")
        if identity["condition"] != spec:
            raise prep.PreparationError("condition identity differs")
        if reference["input_identity_sha256"] != prep.sha_file(directory / "conditions" / cid / "input_identity.json"):
            raise prep.PreparationError("reference/input hash differs")
        identities[cid] = identity
        rows = [r for r in plan["candidates"] if r["condition_id"] == cid]
        if rows and (identity["status"] != "input_eligible" or reference["status"] != "reference_candidate_plan_ready"):
            raise prep.PreparationError("ineligible condition entered candidate plan")
        for row in rows:
            if row["K"] != identity["K"] or row["t_ref_hex"] != reference["t_ref_hex"]:
                raise prep.PreparationError("candidate K/reference identity differs")
            if not any(all(row[k] == r[k] for k in r) for r in reference["candidate_plan"]):
                raise prep.PreparationError("candidate differs from P3 frozen reference")
    return protocol, specifications, plan, identities


def validate_plan(plan, specifications):
    ids = [s["condition_id"] for s in specifications]
    if len(ids) != 16 or len(set(ids)) != 16 or Counter(s["family"] for s in specifications) != {"LiH": 4, "LiF": 4, "BeH2": 4, "CH2": 4}:
        raise prep.PreparationError("16 attempted / four family inventory required")
    states = {r["condition_id"]: r["status"] for r in plan["all_conditions"]}
    if len(plan["all_conditions"]) != 16 or set(states) != set(ids):
        raise prep.PreparationError("terminal conditions missing/duplicated")
    if any(states.get(cid) != status for cid, status in TERMINAL.items()):
        raise prep.PreparationError("fixed ineligible statuses differ")
    ready = [cid for cid in ids if cid not in TERMINAL]
    expected = [(cid, ratio) for cid in ready for ratio in (.8, 1., 1.2)]
    if plan["candidate_count"] != 39 or [(r["condition_id"], r["ratio"]) for r in plan["candidates"]] != expected:
        raise prep.PreparationError("exact ordered 39-coordinate plan required")
    if any(states[cid] != "reference_candidate_plan_ready" for cid in ready):
        raise prep.PreparationError("ready classification differs")
    for row in plan["candidates"]:
        for key in ("time", "ratio", "t_ref"):
            value = float.fromhex(row[key + "_hex"])
            if not math.isfinite(value) or value <= 0 or value.hex() != float(row[key]).hex():
                raise prep.PreparationError("candidate binary64 identity differs")
        if float(row["ratio"] * row["t_ref"]).hex() != row["time_hex"] or not .02 <= row["time"] <= 1.8:
            raise prep.PreparationError("candidate arithmetic/domain differs")
    return ready


def budget(time_value, error, k, protocol, gamma=1.):
    epsilon = protocol["resource"]["epsilon_E"]
    allowance = epsilon - error
    if not all(math.isfinite(v) for v in (time_value, error, allowance, gamma)) or time_value <= 0 or error < 0 or allowance <= 0:
        return None
    # Gamma multiplies the budget, not c or e_use. Preserve inherited operation order.
    base = float(protocol["resource"]["beta"] * k / (time_value * allowance))
    value = float(gamma * base)
    return value if math.isfinite(value) and value > 0 else None


def select(rows, abstention):
    eligible = [r for r in rows if r["eligible"] and r["budget"] is not None and math.isfinite(r["budget"]) and r["budget"] > 0]
    if not eligible:
        return {"status": abstention, "selected": None, "fallback": False}
    best = min(eligible, key=lambda r: (r["budget"], r["time"]))
    return {"status": "selected", "selected": best, "fallback": False}


def cheap_decisions(points, protocol):
    arms = []
    for gamma in protocol["resource"]["gammas"]:
        rows = []
        for point in points:
            value = budget(point["time"], abs(point["delta_C_hartree"]), point["K"], protocol, gamma)
            rows.append({"coordinate_id": point["coordinate_id"], "time": point["time"],
                         "time_hex": point["time_hex"], "gamma": gamma, "budget": value,
                         "budget_hex": None if value is None else value.hex(), "eligible": value is not None,
                         "c_hartree": abs(point["delta_C_hartree"]),
                         "positive_allowance_hartree": protocol["resource"]["epsilon_E"] - abs(point["delta_C_hartree"])})
        arms.append({"gamma": gamma, "candidate_rows": rows, "decision": select(rows, "B1_abstain_no_eligible_candidate")})
    anchor = next(p for p in points if p["ratio"] == .8)
    anchor_budget = budget(anchor["time"], abs(anchor["delta_C_hartree"]), anchor["K"], protocol, 1.10)
    return {"B1": arms, "B0": {"role": "benchmark_only_not_safe_or_fallback", "time": anchor["time"],
            "time_hex": anchor["time_hex"], "gamma": 1.10, "budget": anchor_budget,
            "budget_hex": None if anchor_budget is None else anchor_budget.hex(),
            "status": "defined" if anchor_budget is not None else "benchmark_unavailable", "safety": "not_evaluated"}}


def numerical_rules(protocol):
    m = protocol["M1_future"]
    return {"modified_gram_schmidt_passes": 2, "relative_breakdown_tolerance": m["relative_breakdown"],
            "overlap_ambiguity_tolerance": m["overlap_ambiguity"],
            "energy_ambiguity_tolerance_hartree": m["energy_ambiguity_hartree"],
            "basis_orthogonality_frobenius_residual_maximum": m["orthogonality_frobenius"],
            "pf_action_norm_residual_maximum": m["pf_norm_residual"],
            "full_u_ritz_residual_maximum": m["u_ritz_residual"],
            "full_h_ritz_residual_hartree_maximum": m["h_ritz_residual_hartree"]}


def finite_json(value, missing, path=""):
    if isinstance(value, dict):
        return {k: finite_json(v, missing, path + "/" + k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [finite_json(v, missing, path + "/" + str(i)) for i, v in enumerate(value)]
    if isinstance(value, (float, np.floating)) and not math.isfinite(value):
        missing.append({"path": path, "original": str(value), "serialized": None})
        return None
    return value.item() if isinstance(value, np.generic) else value


class ReadBoundary:
    """Python open audit; explicitly NOT an OS hermeticity certificate."""
    def __init__(self, root, runtime, allowed, output):
        self.runtime = Path(runtime).resolve()
        # Runtime is under P3-worktree/artifacts/P3/.runtime. Also deny unrelated
        # molecular reads elsewhere in that original worktree.
        original_root = self.runtime.parents[2] if self.runtime.parent.name == Path(PREP).name else self.runtime.parent
        self.roots = (Path(root).resolve(), original_root)
        self.allowed = {Path(p).resolve() for p in allowed}
        self.output = Path(output).resolve()
        self.enabled = True
        self.reads, self.denied = set(), []

    def hook(self, event, args):
        if not self.enabled or event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        in_output = path.is_relative_to(self.output)
        if not in_output and not any(path.is_relative_to(p) for p in self.roots):
            return  # standard interpreter/library/platform I/O, not molecular data
        if (writing and not in_output) or (not writing and not in_output and path not in self.allowed):
            self.denied.append(str(path))
            raise prep.PreparationError("data access outside the frozen allowlist")
        if not writing:
            self.reads.add(str(path))

    def payload(self):
        def public(path):
            value = Path(path)
            if value.is_relative_to(self.runtime):
                return "${P3_RUNTIME}/" + value.relative_to(self.runtime).as_posix()
            if value.is_relative_to(self.roots[1]) and not value.is_relative_to(self.roots[0]):
                return "${P3_WORKTREE}/" + value.relative_to(self.roots[1]).as_posix()
            return "${WORKTREE}/" + value.relative_to(self.roots[0]).as_posix()
        return {"mechanism": "Python open audit and exact NPZ member/hash gates", "OS_hermeticity_claim": False,
                "reads": sorted(public(p) for p in self.reads), "denied_accesses": [public(p) for p in self.denied],
                "truth_array_reads": 0, "legacy_truth_runner_calls": 0, "GPU_operations": 0}


class ActionLedger(prep.ReferenceLedger):
    def __init__(self, rss_limit, phase, checkpoint, guard=lambda: None):
        super().__init__(rss_limit)
        self.phase, self.checkpoint, self.guard = phase, Path(checkpoint), guard
        self.counts = Counter({key: 0 for key in (*LIMITS, *FORBIDDEN)})
        self.coordinate_counts = Counter()

    def check_memory(self):
        if hasattr(self, "guard"):
            self.guard()
        super().check_memory()

    def new_coordinate(self):
        self.coordinate_counts.clear()

    def charge(self, name):
        alias = {"reference_pf_actions": "candidate_pf_vector_actions",
                 "reference_h_exponential_actions": "candidate_h_exponential_actions"}
        name = alias.get(name, name) if self.phase == "cheap" else name
        allowed = set(LIMITS) - ({"M1_pf_vector_actions", "M1_h_matvecs"} if self.phase == "cheap" else {"candidate_pf_vector_actions", "candidate_h_exponential_actions"})
        if name not in allowed:
            raise prep.PreparationError("action not authorized in this phase")
        per_coordinate = 1 if self.phase == "cheap" else 8
        if self.counts[name] >= LIMITS[name] or self.coordinate_counts[name] >= per_coordinate:
            raise prep.PreparationError("attempted action ceiling reached")
        self.guard()
        self.counts[name] += 1
        self.coordinate_counts[name] += 1
        self.check_memory()
        # Charge and persist attempted actions BEFORE dispatch. Never reset on failure.
        prep.write(self.checkpoint, self.payload())


class CandidateAdapter(prep.ReferenceAdapter):
    def __init__(self, h, groups, sequence, ledger):
        super().__init__(h, groups, sequence, ledger)
        self.cache, self.cache_time = {}, None

    def pf(self, vector, t):
        vector = np.asarray(vector, dtype=np.complex128)
        if vector.shape != (self.h.shape[0],) or not np.all(np.isfinite(vector)):
            raise prep.PreparationError("M1 PF accepts one finite vector only")
        self.ledger.charge("M1_pf_vector_actions")
        before = time.perf_counter()
        if self.cache_time != float(t).hex():
            self.cache, self.cache_time = {}, float(t).hex()
        current = vector.copy()
        for index, weight in self.steps:
            key = (index, weight)
            if key not in self.cache:
                self.cache[key] = prep.component_exponential(self.spectra[index], float(t * weight))
                self.ledger.counts["component_gate_materializations"] += 1
            current = self.cache[key] @ current
            self.ledger.counts["sparse_state_multiplies"] += 1
        self.ledger.timings["M1_PF_vector_actions"] += time.perf_counter() - before
        self.ledger.check_memory()
        return current

    def h_matvec(self, vector):
        vector = np.asarray(vector, dtype=np.complex128)
        if vector.shape != (self.h.shape[0],) or not np.all(np.isfinite(vector)):
            raise prep.PreparationError("M1 H accepts one finite vector only")
        self.ledger.charge("M1_h_matvecs")
        before = time.perf_counter()
        value = np.asarray(self.h @ vector, dtype=np.complex128)
        self.ledger.timings["M1_H_matvecs"] += time.perf_counter() - before
        return value


def spectral_coordinate(adapter, state, coordinate, protocol, previous):
    rank = prep.primary_rank(len(state))
    adapter.ledger.new_coordinate()
    prediction, vector = d2.analyze_coordinate(
        start=state, apply_u=lambda v: adapter.pf(v, coordinate["time"]), apply_h=adapter.h_matvec,
        time_value=coordinate["time"], prefix_dimensions=rank["prefixes"], primary_dimension=rank["primary"],
        previous_vector=previous, numerical_rules=numerical_rules(protocol),
        epsilon_hartree=protocol["resource"]["epsilon_E"], beta=protocol["resource"]["beta"],
        rotations_per_step=coordinate["K"])
    counts = adapter.ledger.coordinate_counts
    # Completed projected prefix diagnostics use one H-eigh and one U-eig each.
    # Failed/incomplete prefix diagnostics are not silently counted as complete.
    adapter.ledger.counts["completed_projected_H_eigh"] += len(prediction["prefixes"])
    adapter.ledger.counts["completed_projected_U_eig"] += len(prediction["prefixes"])
    if counts["M1_pf_vector_actions"] != counts["M1_h_matvecs"] or counts["M1_pf_vector_actions"] != prediction["available_dimension"]:
        raise prep.PreparationError("shared-prefix action accounting differs")
    if prediction["primary_dimension_used"] != rank["primary"] and not prediction["abstained"]:
        raise prep.PreparationError("lower-rank primary rescue prohibited")
    missing = []
    core = finite_json(prediction, missing, coordinate["coordinate_id"])
    row = {**coordinate, "primary_rank": rank["primary"], "prefixes": rank["prefixes"],
           "actual_M1_rank": prediction["available_dimension"], "core_prediction": core,
           "claim_class": "empirical_feasibility_only_not_certificate", "nonfinite_fields": missing,
           "delta_M_hartree": core["signed_shift_estimate_hartree"], "width_M_hartree": core["empirical_width_hartree"],
           "budget": core["frozen_pauli_rotation_budget"], "eligible": not core["abstained"],
           "failure_reasons": core["failure_reasons"], "actions": dict(counts)}
    return row, vector


def coordinate_rows(plan):
    return [{**row, "coordinate_id": row["condition_id"] + "_r" + str(row["ratio"])} for row in plan["candidates"]]


def make_manifest(directory, names):
    directory = Path(directory)
    entries = [{"path": name, "sha256": prep.sha_file(directory / name), "bytes": (directory / name).stat().st_size} for name in names]
    prep.write(directory / "manifest.json", {"files": entries, "manifest_self_excluded": True})
    return prep.sha_file(directory / "manifest.json")


def verify_package(root, directory, commit=None):
    directory = Path(directory)
    manifest = prep.read(directory / "manifest.json")
    if manifest.get("manifest_self_excluded") is not True:
        raise prep.PreparationError("package manifest must explicitly exclude itself")
    verify_manifest(directory, manifest["files"])
    if commit:
        git(root, "merge-base", "--is-ancestor", commit, "HEAD")
        for name in ["manifest.json", *[r["path"] for r in manifest["files"]]]:
            verify_blob(root, (directory / name).relative_to(root).as_posix(), commit)
    return manifest


def require_members(manifest, names):
    if {r["path"] for r in manifest["files"]} != set(names):
        raise prep.PreparationError("sealed package membership differs")


def check_rows(rows, plan):
    expected = coordinate_rows(plan)
    if len(rows) != 39:
        raise prep.PreparationError("all 39 predictions required")
    for row, coordinate in zip(rows, expected, strict=True):
        if any(row.get(k) != v for k, v in coordinate.items()):
            raise prep.PreparationError("prediction coordinate differs from P3")


def global_prediction(root, protocol, specifications, plan, identities, cheap, spectral):
    check_rows(cheap["rows"], plan)
    check_rows(spectral["rows"], plan)
    conditions = []
    for spec in specifications:
        cid = spec["condition_id"]
        identity = identities[cid]
        reference = prep.read(Path(root) / PREP / "conditions" / cid / "reference_result.json")
        record = {"condition": spec, "status": TERMINAL.get(cid, "candidate_prediction_frozen"),
                  "input_identity": identity, "reference_result": reference,
                  "input_identity_sha256": prep.sha_file(Path(root) / PREP / "conditions" / cid / "input_identity.json"),
                  "ground_claim": "fixed_population_sector_only_not_global_molecular_ground",
                  "predictions": None}
        if cid not in TERMINAL:
            points = [r for r in cheap["rows"] if r["condition_id"] == cid]
            m1 = [r for r in spectral["rows"] if r["condition_id"] == cid]
            frozen_decisions = cheap["decisions"][cid]
            if frozen_decisions != cheap_decisions(points, protocol):
                raise prep.PreparationError("cheap decisions differ from frozen rule")
            record["predictions"] = {"cheap": points, **frozen_decisions, "M1": m1,
                                     "M1_decision": select(m1, "M1_condition_abstention")}
        else:
            record["terminal_reason"] = identity.get("failure_reason", reference["status"])
            record["new_candidate_actions"] = 0
        conditions.append(record)
    return {"status": SUCCESS, "attempted_conditions": 16, "family_units": 4,
            "candidate_ready_conditions": 13, "candidate_coordinates": 39,
            "terminal_conditions": dict(TERMINAL), "conditions": conditions,
            "M1_candidate_abstentions": sum(not r["eligible"] for r in spectral["rows"]),
            "M1_condition_abstentions": sum(r["predictions"] is not None and
                r["predictions"]["M1_decision"]["selected"] is None for r in conditions),
            "missing_candidate_predictions": 0, "B2_H1_execution": "not_authorized_not_run",
            "safety_branch_accuracy_width_coverage": "not_evaluated_truth_not_opened"}
