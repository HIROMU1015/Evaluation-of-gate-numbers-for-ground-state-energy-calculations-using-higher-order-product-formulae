"""Approved H-chain supplement infrastructure, with explicit freeze boundaries.

Worker code has no Git operations. Molecular predictor inputs are allowlisted
and hashed, old runners are never imported, and truth is only exposed by the
coordinator after a prediction commit/blob gate.
"""
from __future__ import annotations

import ast
from collections import Counter
from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np
from scipy.linalg import eigh, schur
from scipy.sparse import csr_matrix, load_npz
from scipy.sparse.linalg import norm as sparse_norm

from hchain_cached_prefix import cached_prefix, PREFIXES
from review_response.hchain_input_reference_preparation import (
    Ledger, PreparationError, VectorAdapter, canonical_hash, checked_functions,
    reference_result, sha_array, sha_file, state_identity, write_json,
)
from hchain_h8_memory_safe import StreamingVectorAdapter, dense_digest_stream
from hchain_prediction_phase import finite_json, make_bundle, verify_bundle
from pf_spectral_recoverability_d2 import analyze_prefix, analyze_coordinate, build_arnoldi_chain

BASE = "f54db03a6a619b978a38152ff15fcce9963f676f"
DOC = "docs/second_study_v2/hchain_supplement_execution_20261006"
INVENTORY = "artifacts/hchain_supplement_local_preparation_20261006/inventory.json"
OLD = "docs/second_study_v2/hchain_independent_validation_20261004"
EPS = 0.00015936001019904
BETA = 1.2
GAMMAS = (1.01, 1.02, 1.05, 1.10)
METHOD = "docs/second_study_v2/hchain_input_reference_preparation_20261004/truth_scoring_method.json"
SAVED_PRED = {
    "H6": "artifacts/hchain_truth_free_prediction_20261004/final/prediction.json",
    "H7": "artifacts/hchain_h3_h5_h7_extension_20261004/prediction/payload.json",
    "H8": "artifacts/hchain_h8_memory_safe_extension_20261004/prediction/payload.json",
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def remote_gate(root):
    for args in (("remote", "get-url", "--all", "origin"),
                 ("remote", "get-url", "--push", "--all", "origin")):
        for url in git(root, *args).decode().splitlines():
            if not url.startswith(("git@github.com:HIROMU1015/", "https://github.com/HIROMU1015/")):
                raise PreparationError("repository publication owner is not permitted")


def clean_gate(root):
    if git(root, "diff", "--name-only").strip() or git(root, "diff", "--cached", "--name-only").strip():
        raise PreparationError("tracked/staged worktree changed")


def source_gate(root):
    root = Path(root)
    clean_gate(root)
    sealed = read(root / DOC / "source_freeze.json")
    for row in sealed["files"]:
        path = root / row["path"]
        if sha_file(path) != row["sha256"] or path.read_bytes() != git(root, "show", f"{sealed['content_commit']}:{row['path']}"):
            raise PreparationError("source freeze/blob changed: " + row["path"])
    if (root / DOC / "source_freeze.json").read_bytes() != git(root, "show", f"HEAD:{DOC}/source_freeze.json"):
        raise PreparationError("uncommitted source seal")
    test = read(root / DOC / "focused_tests.json")
    if test["failed"] or test["skipped"] or not test["passed"]:
        raise PreparationError("focused test gate failed")
    return sealed


def machine_inventory(output):
    mem = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        name, value, *_ = line.split()
        mem[name.rstrip(":")] = int(value) * 1024
    cpus = subprocess.check_output(["lscpu", "-p=SOCKET,CORE"]).decode().splitlines()
    physical = len({line for line in cpus if line and not line.startswith("#")})
    disk = shutil.disk_usage(output)
    cards = []
    for card in sorted(Path("/sys/class/drm").glob("card[0-9]")):
        vendor = card / "device/vendor"
        if vendor.exists():
            cards.append({"card": card.name, "vendor": vendor.read_text().strip()})
    ram_reserve = max(8 * 1024**3, int(.15 * mem["MemTotal"]))
    return {"utc": utc(), "platform": platform.platform(), "logical_CPUs": os.cpu_count(),
            "physical_cores": physical, "affinity_CPUs": len(os.sched_getaffinity(0)),
            "RAM_bytes": mem["MemTotal"], "available_RAM_bytes": mem["MemAvailable"],
            "swap_total_bytes": mem["SwapTotal"], "swap_used_bytes": mem["SwapTotal"] - mem["SwapFree"],
            "filesystem_total_bytes": disk.total, "filesystem_free_bytes": disk.free,
            "RAM_reserve_bytes": ram_reserve, "disk_reserve_bytes": max(2 * 1024**3, disk.total // 100),
            "usable_RAM_bytes": max(0, mem["MemAvailable"] - ram_reserve),
            "worker_CPU_ceiling": max(1, len(os.sched_getaffinity(0)) - 2),
            "GPU_presence_sysfs_reference_only": cards, "GPU_kernel_operations": 0,
            "BLAS_threads_per_worker": 1, "PySCF_threads_per_worker": 1,
            "no_fixed_wall_cap": True, "allocation_independent_local_PC": True}


def owned_process_memory(pid=None):
    fields = {}
    try:
        for line in Path(f"/proc/{pid or 'self'}/status").read_text().splitlines():
            if line.startswith(("VmRSS:", "VmHWM:", "VmSwap:")):
                key, value, *_ = line.split()
                fields[key.rstrip(":")] = int(value) * 1024
    except FileNotFoundError:
        pass
    return fields


class ScienceLedger(Ledger):
    def __init__(self, rank=8):
        super().__init__()
        self.limits = {
            "H6_Hamiltonian_generations": 1, "H6_CISD_generations": 1,
            "input_verification_h_matvecs": 1,
            "reference_pf_actions": 34, "reference_h_exponential_actions": 34,
            "candidate_cheap_pf_actions": 3, "candidate_h_exponential_actions": 3,
            "m1_pf_vector_actions": 3 * rank, "m1_h_matvecs": 3 * rank,
            "Arnoldi_chains": 3, "full_H_ground_solves": 1,
            "full_pf_unitary_builds": 3, "direct_Schur_solves": 3,
            "direct_truth_coordinates": 3, "target_phase_gaps": 3,
        }
        self.events = []

    def charge(self, key, maximum):
        ceiling = self.limits.get(key, maximum)
        self.check_memory()
        if self.counts[key] >= ceiling:
            raise PreparationError("action cap before action: " + key)
        self.counts[key] += 1

    def check_memory(self):
        m = owned_process_memory()
        if m.get("VmSwap", 0):
            raise PreparationError("worker swap usage: stop before next action")
        memory = {line.split()[0].rstrip(":"): int(line.split()[1]) * 1024
                  for line in Path("/proc/meminfo").read_text().splitlines()}
        if memory["MemAvailable"] < max(8 * 1024**3, int(.15 * memory["MemTotal"])):
            raise PreparationError("host RAM reserve depleted: stop before next action")
        if hasattr(self, "output"):
            disk = shutil.disk_usage(self.output)
            if disk.free < max(2 * 1024**3, disk.total // 100):
                raise PreparationError("filesystem reserve depleted: stop before next action")

    def payload(self):
        p = super().payload()
        p.pop("combined_H1_cost", None)
        p["own_process_memory"] = owned_process_memory()
        p["stage_events"] = self.events
        p["worker_pid"] = os.getpid()
        return p


@contextmanager
def timed(ledger, name):
    before = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - before
        ledger.timings[name] += elapsed
        ledger.events.append({"stage": name, "wall_seconds": elapsed, **owned_process_memory()})


class AccessGuard:
    """Python audit barrier over the entire repository and all its worktrees."""
    def __init__(self, workspace, output, allowed):
        self.workspace, self.output = Path(workspace).resolve(), Path(output).resolve()
        self.allowed = {Path(p).resolve() for p in allowed}
        self.reads, self.denials = set(), []
        self.enabled = True

    def hook(self, event, args):
        if not self.enabled or event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        if not path.is_relative_to(self.workspace):
            return
        mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if path.is_relative_to(self.output):
            return
        library = path.is_relative_to(self.workspace / "venv")
        if writing or (not library and path not in self.allowed):
            self.denials.append(str(path))
            raise PreparationError("unallowlisted repository data access: " + str(path))
        if not library:
            self.reads.add(str(path))

    def payload(self):
        return {"allowed_repository_reads": sorted(self.reads), "denials": self.denials,
                "prospective_partial_truth_reads": 0, "GPU_science_operations": 0,
                "OS_hermeticity_claim": False, "mechanism": "Python open audit plus named NPZ members"}


def make_guard(root, out, *, extra=()):
    root = Path(root)
    inv = read(root / INVENTORY)
    allowed = [root / row["path"] for row in read(root / DOC / "source_freeze.json")["files"]]
    allowed += [root / DOC / "source_freeze.json", root / DOC / "focused_tests.json"]
    allowed += [Path(a["root"]) / e["path"] for a in inv["runtime_byte_audit"].values() for e in a["files"]]
    allowed += [root / path for path in SAVED_PRED.values()]
    allowed += list(extra)
    guard = AccessGuard(root.parents[1], out, allowed)
    sys.addaudithook(guard.hook)
    return guard


def frozen_plan(root, system):
    raw = read(Path(root) / INVENTORY)["coordinate_rows"][system]
    return [{**row, "time": float.fromhex(row["time_hex"]), "ratio": float.fromhex(row["ratio_hex"]),
             "t_ref": float.fromhex(row["t_ref_hex"]), "K": int(row["K"])} for row in raw]


def load_frozen_input(root, system, ledger, kinds):
    inv = read(Path(root) / INVENTORY)
    row = inv["runtime_byte_audit"][system]
    metadata = inv["input_identity_metadata"][system]
    runtime = Path(row["root"])
    for item in row["files"]:
        p = runtime / item["path"]
        if p.is_symlink() or p.stat().st_size != item["bytes"] or sha_file(p) != item["sha256"]:
            raise PreparationError("frozen runtime bytes changed")
    if system == "H8":
        h = load_npz(runtime / "H8_H.npz")
        with np.load(runtime / "H8_state.npz", allow_pickle=False) as archive:
            if set(archive.files) != {"cisd", "sector_indices"}:
                raise PreparationError("H8 state archive keys")
            state, indices = archive["cisd"].copy(), archive["sector_indices"].copy()
        def group_iterator():
            for i in range(len(metadata["group_sha256_numpy_v1"])):
                yield load_npz(runtime / f"H8_group_{i:03d}.npz")
    else:
        name = "H6_predictor_input.npz" if system == "H6" else "H7_input.npz"
        with np.load(runtime / name, allow_pickle=False) as archive:
            expected = {"hamiltonian", "cisd", "sector_indices"} | {f"group_{i:03d}" for i in range(len(metadata["group_sha256_numpy_v1"]))}
            if set(archive.files) != expected:
                raise PreparationError("sanitized input key set")
            h, state, indices = archive["hamiltonian"].copy(), archive["cisd"].copy(), archive["sector_indices"].copy()
            groups = [archive[f"group_{i:03d}"].copy() for i in range(len(metadata["group_sha256_numpy_v1"]))]
        def group_iterator():
            yield from groups
    if (dense_digest_stream(h) != metadata["H_sha256_numpy_v1"] or sha_array(state) != metadata["CISD_sha256_numpy_v1"]
            or sha_array(indices) != metadata["sector_indices_sha256_numpy_v1"]):
        raise PreparationError("array H/state/sector identity mismatch")
    if abs(float(np.linalg.norm(state)) - 1) > 1e-12:
        raise PreparationError("frozen state norm")
    total = csr_matrix(h.shape, dtype=np.complex128)
    # Closure uses streamed sparse groups, no full-H eigensolve or H-vector action.
    for group, expected in zip(group_iterator(), metadata["group_sha256_numpy_v1"], strict=True):
        if dense_digest_stream(group) != expected:
            raise PreparationError("ordered group array mismatch")
        total += csr_matrix(group)
    residual = float(sparse_norm(total - csr_matrix(h)))
    if residual > 1e-12 or sparse_norm(csr_matrix(h) - csr_matrix(h).getH()) > 1e-12:
        raise PreparationError("same scalar-removed H/group closure failed")
    sequence = read(Path(root) / OLD / "system_and_pf_contract.json")["PF"]["s2_sequence"]
    closure = {"system": system, "input_origin_commit": row["origin_result_commit"],
               "array_identities": metadata, "ordered_group_sum_residual": residual,
               "energy_origin": "frozen scalar-identity-removed H and groups", "new_H_actions": 0,
               "PF_sequence_hex": [v.hex() for v in sequence], "candidate_time_hex": [p["time_hex"] for p in frozen_plan(root, system)]}
    adapter = None
    if kinds:
        with timed(ledger, "component_spectrum_preprocessing"):
            adapter = StreamingVectorAdapter(h, group_iterator(), len(metadata["group_sha256_numpy_v1"]), sequence, ledger, allowed_kinds=kinds)
    return h, state, indices, adapter, closure


def estimator_rules(root):
    return read(Path(root) / OLD / "rank_aware_M1_amendment.json")["numerical_rules"]


def analyze_cached(chain, dimensions, time_value, previous, rules):
    result, vectors = {}, {}
    for m in dimensions:
        view = cached_prefix(chain, m)
        if view is None:
            result[m] = {"dimension": m, "status": "missing_actual_rank_breakdown", "actual_rank": chain.dimension}
            continue
        point, vector = analyze_prefix(view, m, time_value, previous_vector=previous.get(m),
            overlap_ambiguity_tolerance=rules["overlap_ambiguity_tolerance"],
            energy_ambiguity_tolerance_hartree=rules["energy_ambiguity_tolerance_hartree"])
        point.update({"status": "available", "actual_rank": chain.dimension,
                      "basis_orthogonality_frobenius_residual": view.orthogonality_residual_frobenius,
                      "maximum_pf_action_norm_residual": view.maximum_pf_norm_residual})
        result[m], vectors[m] = point, vector
    return result, vectors


def rank_diagnostics(points, rules):
    result = {}
    for m, p in points.items():
        row = deepcopy(p)
        if p["status"] != "available":
            result[m] = row
            continue
        low = points.get(m // 2)
        prefix = abs(p["signed_shift_estimate_hartree"] - low["signed_shift_estimate_hartree"]) if low and low["status"] == "available" else None
        width = None if prefix is None else max(prefix, p["local_residual_width_hartree"])
        e_use = None if width is None else abs(p["signed_shift_estimate_hartree"]) + width
        failures = []
        for key, maximum, label in (
            ("basis_orthogonality_frobenius_residual", rules["basis_orthogonality_frobenius_residual_maximum"], "basis_orthogonality"),
            ("maximum_pf_action_norm_residual", rules["pf_action_norm_residual_maximum"], "pf_action_norm"),
            ("selected_full_u_ritz_residual_2_norm", rules["full_u_ritz_residual_maximum"], "u_ritz_residual"),
            ("h_reference_full_residual_2_norm_hartree", rules["full_h_ritz_residual_hartree_maximum"], "h_ritz_residual")):
            if p[key] > maximum:
                failures.append(label)
        if p["branch_status"] == "branch_indeterminate":
            failures.append("branch_indeterminate")
        if e_use is None or not math.isfinite(e_use) or e_use >= EPS:
            failures.append("no_positive_qpe_allowance")
        row.update({"prefix_width_hartree": prefix, "empirical_width_hartree": width,
                    "e_use_hartree": e_use, "positive_QPE_allowance": e_use is not None and e_use < EPS,
                    "failure_reasons": failures, "numerically_usable": not failures,
                    "diagnostic_only_no_old_formal_result_change": True})
        result[m] = row
    return result


def rank8_control(chain, t, previous, rules, k):
    points, vectors = analyze_cached(cached_prefix(chain, min(8, chain.dimension)) if chain.dimension >= 8 else chain,
                                      (1, 2, 4, 8), t, dict.fromkeys((1, 2, 4, 8), previous), rules)
    diagnostics = rank_diagnostics(points, rules)
    if diagnostics[8]["status"] != "available":
        return {"status": "missing_rank8", "abstained": True, "failure_reasons": ["primary_dimension_unavailable"]}, None
    p = diagnostics[8]
    p["abstained"] = bool(p["failure_reasons"])
    p["frozen_pauli_rotation_budget"] = None if p["abstained"] else budget(t, p["e_use_hartree"], k)
    p["prefixes"] = [points[m] for m in (1, 2, 4, 8)]
    return p, vectors[8]


def reproduction(new, old, tolerance):
    old = old["core_prediction"]
    if new.get("status") == "missing_rank8":
        return {"passed": False, "mismatches": ["primary_rank8_missing"], "additional_PF_H_actions": 0}
    fields = {"signed_shift_estimate_hartree": "signed_shift_estimate_hartree",
              "empirical_width_hartree": "empirical_width_hartree",
              "prefix_width_hartree": "prefix_width_hartree", "local_residual_width_hartree": "local_residual_width_hartree",
              "h_reference_energy_hartree": None, "selected_unwrapped_energy_hartree": None,
              "selected_h_reference_overlap_probability": None}
    old_primary = next(p for p in old["prefixes"] if p["dimension"] == 8)
    differences, mismatches = {}, []
    for field, top in fields.items():
        a, b = new.get(field), old[top] if top else old_primary[field]
        if a is None or not math.isfinite(float(a)) or not math.isfinite(float(b)):
            mismatches.append(field)
            continue
        differences[field] = float(a - b)
        if not math.isclose(a, b, rel_tol=tolerance["scalar_relative"], abs_tol=tolerance["scalar_absolute"]):
            mismatches.append(field)
    if set(new["failure_reasons"]) != set(old["failure_reasons"]) or new["abstained"] != old["abstained"]:
        mismatches.append("numerical_gate_or_abstention")
    if new.get("branch_status") != old_primary["branch_status"]:
        mismatches.append("branch_status")
    # Compare physical selected phase/energy, never unstable projected eigenindex.
    return {"passed": not mismatches, "mismatches": mismatches, "scalar_differences": differences,
            "old_formal_result_changed": False, "additional_PF_H_actions": 0}


def budget(t, e, k):
    if not math.isfinite(e) or not math.isfinite(t) or t <= 0 or e < 0 or e >= EPS:
        return None
    return BETA * k / (t * (EPS - e))


def cheap_decisions(points, k):
    points = sorted(points, key=lambda p: p["time"])
    b = budget(points[0]["time"], abs(points[0]["delta_C_hartree"]), k)
    b0 = {"candidate_id": points[0]["candidate_id"], "time": points[0]["time"], "budget": None if b is None else 1.01 * b,
          "benchmark_only": True, "assumed_safe": False}
    arms = []
    for gamma in GAMMAS:
        rows = []
        for p in points:
            base = budget(p["time"], abs(p["delta_C_hartree"]), k)
            rows.append({"candidate_id": p["candidate_id"], "time": p["time"], "budget": None if base is None else gamma * base})
        eligible = [r for r in rows if r["budget"] is not None and math.isfinite(r["budget"]) and r["budget"] > 0]
        selected = min(eligible, key=lambda r: (r["budget"], r["time"])) if eligible else None
        arms.append({"gamma": gamma, "rows": rows, "selected": selected})
    return {"B0": b0, "B1_frontier": arms, "B2_H1_executed": False}


def safety_mechanism(c, e, gamma):
    margin = (1.0 - 1.0 / gamma) * (EPS - c)
    slack = margin - (e - c)
    gamma_req = (EPS - c) / (EPS - e) if c < EPS and e < EPS else None
    return {"c": c, "e": e, "underestimation_hartree": e - c, "M_gamma": margin,
            "safety_slack": slack, "gamma_req": gamma_req,
            "gamma_req_status": "finite" if gamma_req is not None else "no_finite_feasible_gamma",
            "margin_ratio": (e-c) / margin if gamma != 1 and margin > 0 else None,
            "gamma1_uses_additive_slack": gamma == 1}


def truth_comparison(point, cheap, truth, energy, k, t):
    delta = truth["signed_direct_shift_hartree"]
    shift = point["signed_shift_estimate_hartree"]
    gap = truth["minimum_selected_phase_gap_radians"]
    valid = truth["quality"]["physical_branch_valid"]
    error = abs(shift - delta)
    physical = bool(error < gap / (2 * t)) if valid else None
    pf_error = point["selected_unwrapped_energy_hartree"] - (energy + delta)
    h_error = point["h_reference_energy_hartree"] - energy
    closure = valid and physical and abs(pf_error) < math.pi / t
    width = point.get("empirical_width_hartree")
    cheap_error = abs(cheap - delta)
    cheap_budget = budget(t, abs(cheap), k)
    cheap_budget = None if cheap_budget is None else 1.01 * cheap_budget
    m1_budget = None if point.get("e_use_hartree") is None else budget(t, point["e_use_hartree"], k)
    allowance = None if cheap_budget is None else EPS - BETA * k / (t * cheap_budget)
    return {"E_M_hartree": error, "E_C_hartree": cheap_error,
            "M1_over_cheap_point_error": None if cheap_error == 0 else error / cheap_error,
            "empirical_width_covers": None if width is None or not valid else error <= width,
            "physical_branch_correct": physical, "truth_valid": valid,
            "PF_side_error_hartree": pf_error if closure else None,
            "H_reference_error_hartree": h_error if closure else None,
            "decomposition_closure_residual": (shift - delta) - (pf_error - h_error) if closure else None,
            "decomposition_status": "closed_same_H_origin_physical_branch" if closure else "indeterminate",
            "same_time_cheap_gamma1_01_budget": cheap_budget,
            "hypothetical_M1_budget": m1_budget,
            "same_time_decision_width_window_hartree": None if allowance is None else allowance - abs(shift),
            "M1_budget_beats_same_time_cheap": None if m1_budget is None or cheap_budget is None else m1_budget < cheap_budget,
            "hypothetical_only_not_formal_rescoring": True}


GENERATOR_SHA = "0a2fce70ba9af6f2892b31b4c21febf6ddccbe3fbeec116e324212992a082d3f"
DETERMINANT_SHA = "3e5cf6a14f1dffcae40d18b25d9325995c9cee2a50fc49ac93bb85b518c48fb9"
FIT_SHA = "4117d68b0a1b87cfcb76805450cb8d5dc1ad3f81a48e9a0f930c5f61be5e741e"
GROUND_SHA = "e65584fee6a3905a05da8f4e9e37e3134ee615bf78611bc4f87ea1752b31aca4"
DIRECT_SHA = "a4b32ba8456d74acb072601b4dee0f3a6162be5d591ff4d79f08378f32250619"


def geometry_generator(root, distance):
    """Hash-verified old generator; ONE approved geometry expression changes."""
    path = Path(root) / "review_response/run_hchain_input_reference_preparation.py"
    if sha_file(path) != GENERATOR_SHA:
        raise PreparationError("generation recipe source hash mismatch")
    function = next(node for node in ast.parse(path.read_text()).body
                    if isinstance(node, ast.FunctionDef) and node.name == "generate_h6")
    modifications = 0
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name) and target.value.id == "mol"
                and target.attr == "atom" for target in node.targets):
            old = '[("H", (0.0, 0.0, float(i - 2.5))) for i in range(6)]'
            if ast.dump(node.value) != ast.dump(ast.parse(old, mode="eval").body):
                raise PreparationError("geometry AST site no longer exact")
            node.value = ast.parse('[("H", (0.0, 0.0, float(i - 2.5) * distance)) for i in range(6)]', mode="eval").body
            modifications += 1
    if modifications != 1:
        raise PreparationError("geometry-only AST modification count")
    namespace = {"np": np, "time": time, "json": json, "redirect_stdout": redirect_stdout,
                 "canonical_hash": canonical_hash, "sha_array": sha_array, "state_identity": state_identity,
                 "PreparationError": PreparationError, "OLD": OLD, "distance": float(distance)}
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), function], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace["generate_h6"]


def new_geometry_input(root, runtime, distance, ledger):
    from pyscf import lib
    lib.num_threads(1)
    helpers = checked_functions(Path(root) / "review_response/audit_h01_approximate_state_pilot.py",
        DETERMINANT_SHA, ("sector_basis_indices", "hartree_fock_full_basis_index",
                          "determinant_excitation_rank", "determinant_cisd_state"))
    spec = next(row for row in read(Path(root) / OLD / "system_and_pf_contract.json")["systems"] if row["system"] == "H6")
    with timed(ledger, "H6_geometry_H_CISD_generation"):
        arrays, identity = geometry_generator(root, distance)(Path(root), runtime, spec, helpers, ledger)
    if identity["sector_dimension"] != 400 or identity["CISD_subspace_dimension"] != 118:
        raise PreparationError("new H6 sector/CISD contract failed")
    archive = runtime / "predictor_input.npz"
    np.savez_compressed(archive, hamiltonian=arrays["hamiltonian"], cisd=arrays["cisd"],
                        sector_indices=arrays["sector_indices"],
                        **{f"group_{i:03d}": value for i, value in enumerate(arrays["groups"])})
    return {"identity": identity, "runtime_file": str(archive), "runtime_sha256": sha_file(archive),
            "runtime_bytes": archive.stat().st_size, "distance_angstrom": distance, "K": 14344,
            "energy_origin": "same scalar-identity-removed H and ordered PF groups",
            "generation_AST_changes": "one mol.atom distance multiplication; all other statements unchanged"}


def load_new_input(record, root, ledger, kinds):
    path = Path(record["runtime_file"])
    if sha_file(path) != record["runtime_sha256"] or path.stat().st_size != record["runtime_bytes"]:
        raise PreparationError("new geometry input bytes changed")
    identity = record["identity"]
    with np.load(path, allow_pickle=False) as archive:
        expected = {"hamiltonian", "cisd", "sector_indices"} | {f"group_{i:03d}" for i in range(57)}
        if set(archive.files) != expected:
            raise PreparationError("new predictor archive member contract")
        h, state, indices = archive["hamiltonian"].copy(), archive["cisd"].copy(), archive["sector_indices"].copy()
        groups = [archive[f"group_{i:03d}"].copy() for i in range(57)]
    if sha_array(h) != identity["H_sha256_numpy_v1"] or sha_array(state) != identity["CISD_sha256_numpy_v1"] or sha_array(indices) != identity["sector_indices_sha256_numpy_v1"]:
        raise PreparationError("new geometry array identity changed")
    if [sha_array(group) for group in groups] != identity["group_sha256_numpy_v1"]:
        raise PreparationError("new geometry ordered group identity changed")
    if np.linalg.norm(sum(groups, np.zeros_like(h)) - h) > 1e-12:
        raise PreparationError("new geometry energy-origin closure changed")
    sequence = read(Path(root) / OLD / "system_and_pf_contract.json")["PF"]["s2_sequence"]
    adapter = None
    if kinds:
        with timed(ledger, "component_spectrum_preprocessing"):
            adapter = VectorAdapter(h, groups, sequence, ledger, allowed_kinds=kinds)
    return h, state, indices, adapter


def acquire_chain(adapter, state, t, rank, rules, ledger):
    ledger.charge("Arnoldi_chains", 3)
    return build_arnoldi_chain(state, lambda vector: adapter.pf(vector, t, kind="m1"),
        adapter.h_matvec, maximum_dimension=rank,
        reorthogonalization_passes=rules["modified_gram_schmidt_passes"],
        relative_breakdown_tolerance=rules["relative_breakdown_tolerance"])


def checkpoint(directory, index, payload):
    path = directory / f"coordinate_{index:03d}.json"
    if path.exists():
        raise PreparationError("coordinate checkpoint exists; no repeat")
    write_json(path, finite_json(payload))


def worker(task):
    """One independent geometry/system, ordered times, no Git or legacy runner."""
    root, output = Path(task["root"]), Path(task["output"])
    runtime = output / ".runtime" / task["stage"] / task["unit"]
    runtime.mkdir(parents=True, exist_ok=False)
    ledger = ScienceLedger(32 if task["stage"] == "R_prediction" else 8)
    ledger.output = output
    ledger.counts["PySCF_threads"] = 1  # environment metadata, not a science action
    start = time.perf_counter()
    guard = make_guard(root, output)
    result = {"unit": task["unit"], "stage": task["stage"], "started_utc": utc()}
    try:
        with (runtime / "worker.log").open("w") as log, redirect_stdout(log):
            stage = task["stage"]
            if stage in ("closure", "R_prediction"):
                system = task["unit"]
                with timed(ledger, "array_identity_closure"):
                    h, state, indices, adapter, closure = load_frozen_input(root, system, ledger, ("m1",) if stage == "R_prediction" else ())
                result["closure"] = closure
                if stage == "R_prediction":
                    old_prediction = read(root / SAVED_PRED[system])
                    old_points = old_prediction["M1"][system]
                    rules = estimator_rules(root)
                    previous, previous_control = {}, None
                    rows = []
                    tolerance = read(root / DOC / "authorization.json")["rank8_reproduction_tolerances"]
                    for index, plan in enumerate(frozen_plan(root, system)):
                        before = time.perf_counter()
                        t = float.fromhex(plan["time_hex"])
                        chain = acquire_chain(adapter, state, t, 32, rules, ledger)
                        raw, vectors = analyze_cached(chain, PREFIXES, t, previous, rules)
                        diagnostics = rank_diagnostics(raw, rules)
                        control, previous_control = rank8_control(chain, t, previous_control, rules, plan["K"])
                        old = next(p for p in old_points if p["time_hex"] == plan["time_hex"])
                        row = {**plan, "actual_rank": chain.dimension, "ranks": diagnostics, "old_rank8_control": control,
                               "reproduction": reproduction(control, old, tolerance), "coordinate_wall_seconds": time.perf_counter() - before}
                        previous.update(vectors)
                        rows.append(row)
                        checkpoint(runtime, index, row)
                    result["points"] = rows
                    result["rank8_reproduction_passed"] = all(p["reproduction"]["passed"] for p in rows)
                    result["saved_cheap"] = old_prediction["cheap_B0_B1_B2_q"][system]["points"]
            elif stage == "G_inputs":
                result["input"] = new_geometry_input(root, runtime, task["distance"], ledger)
            else:
                record = task["input"]
                kinds = {"G_reference": ("reference",), "G_prediction": ("candidate", "m1"),
                         "G_ground": (), "G_truth": ()}[stage]
                h, state, indices, adapter = load_new_input(record, root, ledger, kinds)
                if stage == "G_reference":
                    grid = read(root / "docs/second_study_v2/hchain_input_reference_preparation_20261004/reference_grid.json")["points"]
                    points = []
                    for index, entry in enumerate(grid):
                        before = time.perf_counter()
                        t = float.fromhex(entry["hex"])
                        row = adapter.cheap(state, t, kind="reference")
                        row["coordinate_wall_seconds"] = time.perf_counter() - before
                        points.append(row)
                        checkpoint(runtime, index, row)
                    result["points"] = points
                    fit = checked_functions(root / "review_response/pf_first_study_phase_common.py", FIT_SHA, ("leading_fit",))["leading_fit"]
                    specification = read(root / OLD / "cheap_reference_scale_contract.json")["fit_rules"]
                    reference = reference_result([p["time"] for p in points], points, fit, specification, EPS)
                    candidates = []
                    for ratio in (.5, .65, .8):
                        t = float(ratio) * reference["t_ref"]
                        candidates.append({"candidate_id": f"{task['unit']}_r{ratio}", "system": task["unit"], "ratio": ratio,
                            "ratio_hex": ratio.hex(), "time": t, "time_hex": t.hex(), "t_ref": reference["t_ref"],
                            "t_ref_hex": reference["t_ref_hex"], "K": 14344})
                    result.update({"reference": reference, "candidate_plan": candidates})
                    if any(not (.02 <= p["time"] <= 1.8) for p in candidates):
                        raise PreparationError("candidate_time_domain_ineligible")
                elif stage == "G_prediction":
                    cheap, m1, previous = [], [], None
                    for index, plan in enumerate(task["plan"]):
                        before = time.perf_counter()
                        row = adapter.cheap(state, float.fromhex(plan["time_hex"]), kind="candidate")
                        row.update(plan)
                        row["coordinate_wall_seconds"] = time.perf_counter() - before
                        cheap.append(row)
                        checkpoint(runtime, index, {"cheap": row})
                    write_json(runtime / "CHEAP_HASH_FROZEN.json", {"sha256": canonical_hash(cheap), "M1_not_yet_acquired": True})
                    for index, plan in enumerate(task["plan"]):
                        before = time.perf_counter()
                        chain = acquire_chain(adapter, state, plan["time"], 8, estimator_rules(root), ledger)
                        control, previous = rank8_control(chain, plan["time"], previous, estimator_rules(root), 14344)
                        m1.append({**plan, "M1": control, "actual_rank": chain.dimension, "coordinate_wall_seconds": time.perf_counter() - before})
                        checkpoint(runtime, index + 3, m1[-1])
                    result.update({"cheap": cheap, "M1": m1, "decisions": cheap_decisions(cheap, 14344),
                                   "cheap_acquisition_sha256": canonical_hash(cheap)})
                elif stage == "G_ground":
                    functions = checked_functions(root / "review_response/run_hchain_truth_scoring.py", GROUND_SHA, ("ground_point",),
                        {"eigh": eigh, "sha_array": sha_array, "PreparationError": PreparationError})
                    with timed(ledger, "same_H_ground"):
                        ground, vector = functions["ground_point"](h, record["identity"], read(root / METHOD), ledger)
                    path = runtime / "same_H_ground.npz"
                    np.savez_compressed(path, vector=vector)
                    result.update({"ground": ground, "ground_runtime": str(path), "ground_runtime_sha256": sha_file(path)})
                elif stage == "G_truth":
                    from trotterlib.component_sector_pf import component_exponential
                    from hchain_truth_scoring import truth_quality
                    sequence = read(root / OLD / "system_and_pf_contract.json")["PF"]["s2_sequence"]
                    # Truth-side preprocessing only, no predictor/exact-state feedback.
                    with np.load(record["runtime_file"], allow_pickle=False) as archive:
                        groups = [archive[f"group_{i:03d}"] for i in range(57)]
                    adapter = VectorAdapter(h, groups, sequence, ledger, allowed_kinds=())
                    ground_record = task["ground"]
                    if sha_file(ground_record["ground_runtime"]) != ground_record["ground_runtime_sha256"]:
                        raise PreparationError("ground bytes changed")
                    with np.load(ground_record["ground_runtime"], allow_pickle=False) as archive:
                        vector = archive["vector"]
                    full = checked_functions(root / "review_response/run_hchain_truth_scoring.py", GROUND_SHA, ("full_unitary",),
                        {"component_exponential": component_exponential, "PreparationError": PreparationError})["full_unitary"]
                    direct = checked_functions(root / "review_response/_pf_first_study_s0_exact_time_scoring_base.py", DIRECT_SHA,
                        ("_phase_distance", "direct_branch_point"), {"schur": schur, "practical": SimpleNamespace(_cost=lambda t,e,k,eps: budget(t,e,k))})["direct_branch_point"]
                    points, previous = [], None
                    for index, plan in enumerate(task["plan"]):
                        before = time.perf_counter()
                        unitary = full(adapter, plan["time"], ledger)
                        ledger.charge("direct_Schur_solves", 3)
                        point, previous = direct(unitary, vector, ground_record["ground"]["energy_hartree"], plan["time"], 14344, EPS, previous, 1e-8)
                        ledger.charge("direct_truth_coordinates", 3)
                        ledger.charge("target_phase_gaps", 3)
                        eigenvalue = point["selected_eigenvalue"]
                        point["selected_eigenvalue"] = [float(eigenvalue.real), float(eigenvalue.imag)]
                        point.update(plan)
                        point["quality"] = truth_quality(point, read(root / METHOD))
                        point["coordinate_wall_seconds"] = time.perf_counter() - before
                        points.append(point)
                        checkpoint(runtime, index, point)
                        del unitary
                    result["points"] = points
            result["status"] = "complete"
    except Exception as error:
        result.update({"status": "terminal_failure_no_scientific_retry", "failure_type": type(error).__name__, "failure_reason": str(error)})
    finally:
        result.update({"ended_utc": utc(), "worker_total_wall_seconds": time.perf_counter() - start,
                       "resource": ledger.payload(), "access": guard.payload()})
        guard.enabled = False
        write_json(runtime / "worker_result.json", finite_json(result))
    return finite_json(result)
