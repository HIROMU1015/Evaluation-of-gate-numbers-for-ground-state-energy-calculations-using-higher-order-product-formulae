"""Approved P3 primitives: new input + reference only, never candidate/truth.

The command wrapper supplies frozen identities and verified allocation. Numerical
imports are CPU-only. Molecular kernels are lazy and never invoked by import.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
from contextlib import contextmanager, redirect_stdout
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import time

import numpy as np
from scipy.sparse import csr_matrix, load_npz, save_npz
from scipy.sparse.linalg import expm_multiply, norm as sparse_norm

from trotterlib.component_sector_pf import (
    component_exponential, diagonalize_components, qubit_operator_sector_matrix,
)
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.pf_decomposition import iter_s2_sequence_steps

DOC = Path("docs/second_study_v2/prospective_core_protocol_20261005")
P1_COMMIT = "dc10db0e2b9be860239cb18b0c9275bdd24617d2"
ZERO_KEYS = ("candidate_cheap_actions", "M1_actions", "exact_ground_solves",
             "full_PF_materializations", "direct_truth_actions", "gap_actions",
             "performance_scoring", "GPU_operations")


class PreparationError(RuntimeError):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temp.replace(path)


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def array_hash(value):
    value = np.ascontiguousarray(value)
    digest = hashlib.sha256(value.dtype.str.encode() + b"\n" +
                            json.dumps(list(value.shape), separators=(",", ":")).encode() + b"\n")
    digest.update(memoryview(value).cast("B"))
    return digest.hexdigest()


def dense_hash(matrix):
    """Same numpy_v1 identity without materializing a full dense group."""
    matrix = csr_matrix(matrix, dtype=np.complex128)
    digest = hashlib.sha256(matrix.dtype.str.encode() + b"\n" +
                            json.dumps(list(matrix.shape), separators=(",", ":")).encode() + b"\n")
    for index in range(matrix.shape[0]):
        digest.update(memoryview(matrix[index:index + 1].toarray()).cast("B"))
    return digest.hexdigest()


def primary_rank(dimension):
    ranks = [m for m in (1, 2, 4, 8) if m <= dimension]
    if not ranks:
        raise PreparationError("empty sector")
    return {"primary": max(ranks), "prefixes": ranks,
            "actual_breakdown": "abstain_no_lower_prefix_rescue"}


def validate_grid(grid):
    expected = np.geomspace(0.02, 1.8, 34)
    if len(grid) != 34:
        raise PreparationError("frozen reference grid must have exactly 34 points")
    for i, (row, t) in enumerate(zip(grid, expected, strict=True)):
        if row["index"] != i or float(row["time"]).hex() != row["time_hex"] or row["time_hex"] != float(t).hex():
            raise PreparationError("reference grid binary64 identity mismatch")
    return [float.fromhex(row["time_hex"]) for row in grid]


def fit_function(root, registry):
    source = next(s for s in registry["sources"] if s["path"].endswith("pf_first_study_phase_common.py"))
    path = Path(root) / source["path"]
    if sha_file(path) != source["sha256"]:
        raise PreparationError("historical leading_fit source mismatch")
    tree = ast.parse(path.read_text())
    body = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "leading_fit")
    namespace = {"np": np, "rolling_loglog_fits": rolling_loglog_fits}
    exec(compile(ast.Module(body=[body], type_ignores=[]), str(path), "exec", dont_inherit=True,
                 flags=__import__("__future__").annotations.compiler_flag), namespace)
    return namespace["leading_fit"]


def reference_summary(points, times, protocol, leading_fit):
    if len(points) != 34 or len(times) != 34:
        raise PreparationError("all 34 reference points required before fit")
    for row, t in zip(points, times, strict=True):
        if row["time_hex"] != float(t).hex() or not math.isfinite(row["delta_C_hartree"]):
            raise PreparationError("reference point identity/finite gate")
    fit = leading_fit(times, [row["delta_C_hartree"] for row in points], protocol["reference"]["fit"], 4)
    if not fit["qualified"]:
        return {"status": "reference_scale_unavailable_under_frozen_protocol", "leading_fit": fit,
                "candidate_plan": []}
    alpha = float(fit["selected_window"]["fixed_order_alpha"])
    if not math.isfinite(alpha) or alpha <= 0:
        raise PreparationError("nonpositive/nonfinite fixed alpha")
    t_ref = float((protocol["resource"]["epsilon_E"] / (5 * alpha)) ** .25)
    candidates = []
    for ratio in (.8, 1., 1.2):
        t = float(ratio * t_ref)
        candidates.append({"ratio": ratio, "ratio_hex": ratio.hex(), "time": t,
                           "time_hex": t.hex(), "t_ref": t_ref, "t_ref_hex": t_ref.hex()})
    eligible = all(.02 <= row["time"] <= 1.8 for row in candidates)
    return {"status": "reference_candidate_plan_ready" if eligible else "candidate_time_domain_ineligible",
            "alpha_C": alpha, "t_ref": t_ref, "t_ref_hex": t_ref.hex(), "leading_fit": fit,
            "candidate_plan": candidates, "candidate_eligible": eligible,
            "clipping_or_extension": False}


def environment_readiness():
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        if os.environ.get(key) != "1":
            raise PreparationError(f"{key}=1 required before numeric imports")
    if os.environ.get("PYTHONNOUSERSITE") != "1" or os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
        raise PreparationError("isolated no-user-site/no-bytecode process required")
    import scipy
    from scipy.linalg import expm
    import pyscf
    from pyscf import lib, scf
    import openfermion
    # Synthetic readiness operations, not molecular SCF/H/PF acquisitions.
    if not np.allclose(np.eye(2) @ np.ones(2), 1) or not np.allclose(expm(np.zeros((2, 2))), np.eye(2)):
        raise PreparationError("NumPy/SciPy synthetic readiness failed")
    if not callable(scf.RHF) or not callable(scf.ROHF) or lib.num_threads() != 1:
        raise PreparationError("PySCF RHF/ROHF/thread readiness failed")
    if not openfermion.jordan_wigner(openfermion.FermionOperator("0^ 0")).terms:
        raise PreparationError("OpenFermion readiness failed")
    backends = []
    paths = {line.split()[-1] for line in Path("/proc/self/maps").read_text().splitlines()
             if "openblas" in line.lower() and line.split()[-1].startswith("/")}
    for path in sorted(paths):
        library = ctypes.CDLL(path)
        symbol = next((name for name in ("openblas_get_num_threads", "openblas_get_num_threads64_",
                                        "scipy_openblas_get_num_threads", "scipy_openblas_get_num_threads64_")
                       if hasattr(library, name)), None)
        if symbol is None:
            raise PreparationError("loaded BLAS backend thread count unverifiable; no science")
        count = int(getattr(library, symbol)())
        if count != 1:
            raise PreparationError("loaded BLAS backend not single-thread")
        backends.append({"library": Path(path).name, "thread_query": symbol, "threads": count})
    if not backends:
        raise PreparationError("no verifiable loaded OpenBLAS backend; implement/test backend gate before science")
    return {"python": __import__("sys").version, "numpy": np.__version__, "scipy": scipy.__version__,
            "pyscf": pyscf.__version__, "openfermion": openfermion.__version__, "BLAS": backends,
            "pyscf_threads": lib.num_threads(), "molecular_science_actions": 0,
            "synthetic_readiness_operations": ["numpy_dot", "scipy_expm_2x2", "OpenFermion_algebra"]}


def allocation_gate(payload, output, *, evidence_root):
    required = ("verified", "authority", "usable_cpu_quota", "usable_ram_bytes", "job_wall_seconds",
                "writable_disk_quota_bytes", "approved_output_root", "workers", "worker_rss_limit_bytes",
                "worker_wall_seconds", "coordinator_reserved_ram_bytes", "evidence", "expires_UTC")
    if any(key not in payload for key in required) or payload["verified"] is not True:
        raise PreparationError("actual allocation unverified; host totals cannot authorize science")
    if payload["authority"] not in ("scheduler_allocation", "user_explicit_quota"):
        raise PreparationError("allocation authority must be scheduler or explicit user quota")
    for key in required[2:6] + ("workers", "worker_rss_limit_bytes", "worker_wall_seconds"):
        if not isinstance(payload[key], (int, float)) or not math.isfinite(payload[key]) or payload[key] <= 0:
            raise PreparationError("invalid allocation quota")
    if int(payload["workers"]) != payload["workers"] or payload["workers"] > min(payload["usable_cpu_quota"], len(os.sched_getaffinity(0))):
        raise PreparationError("worker count exceeds usable CPU quota/affinity")
    if payload["workers"] * payload["worker_rss_limit_bytes"] + payload["coordinator_reserved_ram_bytes"] > payload["usable_ram_bytes"]:
        raise PreparationError("worker memory reservations exceed allocation")
    if payload["worker_wall_seconds"] > payload["job_wall_seconds"] or payload["coordinator_reserved_ram_bytes"] < 0:
        raise PreparationError("wall/RAM reservation gate failed")
    expiration = datetime.fromisoformat(payload["expires_UTC"])
    if expiration.tzinfo is None or expiration <= datetime.now(timezone.utc):
        raise PreparationError("allocation expired or timezone missing")
    approved = Path(payload["approved_output_root"]).resolve()
    if Path(output).resolve() != approved:
        raise PreparationError("output must equal approved allocation location")
    if not payload["evidence"]:
        raise PreparationError("allocation evidence required, not a self-declared host capacity")
    for row in payload["evidence"]:
        path = Path(evidence_root) / row["path"]
        if sha_file(path) != row["sha256"]:
            raise PreparationError("allocation evidence hash mismatch")
    approved.mkdir(parents=True, exist_ok=True)
    disk = os.statvfs(approved)
    if min(payload["writable_disk_quota_bytes"], disk.f_bavail * disk.f_frsize) < payload.get("reserved_disk_bytes", payload["writable_disk_quota_bytes"]):
        raise PreparationError("approved writable disk reservation not available")
    return payload


def remaining_worker_wall(allocation):
    remaining = (datetime.fromisoformat(allocation["expires_UTC"]) - datetime.now(timezone.utc)).total_seconds()
    if remaining <= 0:
        raise PreparationError("allocation expired")
    return min(float(allocation["worker_wall_seconds"]), remaining)


class ReferenceLedger:
    def __init__(self, rss_limit_bytes, *, checkpoint=None):
        self.counts = Counter({key: 0 for key in ZERO_KEYS})
        self.timings = defaultdict(float)
        self.rss_limit_bytes = int(rss_limit_bytes)
        self.checkpoint = checkpoint
        self.peak_rss_bytes = 0
        self.max_pf_norm_residual = 0.
        self.max_h_exp_norm_residual = 0.
        self.check_memory()

    def check_memory(self):
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
        if rss > self.rss_limit_bytes:
            raise PreparationError("own-process peak RSS exceeds allocated worker limit")

    def charge(self, name):
        if name not in ("reference_pf_actions", "reference_h_exponential_actions"):
            raise PreparationError("candidate/M1/truth access is absent from preparation ledger")
        if self.counts[name] >= 34:
            raise PreparationError("per-condition cumulative reference action cap reached")
        self.counts[name] += 1  # count attempted action before dispatch
        self.check_memory()
        if self.checkpoint:
            write(self.checkpoint, self.payload())

    def payload(self):
        self.check_memory()
        return {"counts": dict(self.counts), "named_stage_wall_seconds": dict(self.timings),
                "peak_rss_bytes": self.peak_rss_bytes,
                "internal_expm_multiply_H_matvecs": "unknown_not_counted_as_one",
                "max_pf_norm_residual": self.max_pf_norm_residual,
                "max_H_exp_norm_residual": self.max_h_exp_norm_residual,
                "native_workspace_allocations": "not_instrumented"}


@contextmanager
def bounded_process(ledger, wall_seconds):
    """Own process only: periodic RSS watchdog and absolute per-command wall cap."""
    started = time.monotonic()
    def watch(signum, frame):
        ledger.check_memory()
        if time.monotonic() - started > wall_seconds:
            raise PreparationError("allocated worker wall limit exceeded")
    old = signal.signal(signal.SIGALRM, watch)
    signal.setitimer(signal.ITIMER_REAL, 1., 1.)
    try:
        yield
        watch(None, None)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def cisd_state(hamiltonian, indices, reference):
    """Only the determinant-CISD subspace is dense/eigensolved."""
    positions = np.asarray([i for i, idx in enumerate(indices)
                            if (int(idx) ^ int(reference)).bit_count() // 2 <= 2], dtype=np.int64)
    subspace = csr_matrix(hamiltonian)[positions][:, positions].toarray()
    eigenvalues, eigenvectors = np.linalg.eigh(subspace)
    state = np.zeros(len(indices), dtype=np.complex128)
    state[positions] = eigenvectors[:, 0]
    state /= np.linalg.norm(state)
    phase = state[int(np.argmax(np.abs(state)))]
    state *= np.exp(-1j * np.angle(phase))
    residual = float(np.linalg.norm(subspace @ eigenvectors[:, 0] - eigenvalues[0] * eigenvectors[:, 0]))
    if abs(np.linalg.norm(state) - 1) > 1e-12 or residual > 1e-10:
        raise PreparationError("CISD subspace numerical gate failed")
    return state, {"positions": positions.tolist(), "dimension": len(positions),
                   "lowest_subspace_energy_hartree": float(eigenvalues[0]),
                   "subspace_eigenpair_residual": residual, "full_H_ground_solve": False}


def create_input(spec, runtime, ledger):
    """RHF/ROHF -> active integrals -> inherited grouping -> determinant CISD.

    CASCI is used ONLY for get_h1eff; no CASCI/FCI kernel or exact-ground tail.
    Groups are stored/hashed one CSR at a time; no full dense group ensemble.
    """
    from pyscf import ao2mo, gto, mcscf, scf
    from openfermion import FermionOperator, QubitOperator, jordan_wigner
    from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
    runtime = Path(runtime)
    runtime.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    mol = gto.Mole()
    mol.atom, mol.unit, mol.basis = spec["atoms"], "Angstrom", "sto-3g"
    mol.spin, mol.charge, mol.symmetry = spec["spin"], 0, False
    mol.verbose, mol.output = 3, str(runtime / "SCF.log")
    mol.build()
    if spec["reference"] not in ("RHF", "ROHF"):
        raise PreparationError("unapproved state recipe")
    mf = scf.RHF(mol) if spec["reference"] == "RHF" else scf.ROHF(mol)
    mf.conv_tol, mf.max_cycle = 1e-12, 200
    ledger.counts["SCF_attempts"] += 1
    mf.kernel()
    ncore, norb = spec["frozen_core_orbitals"], spec["active_orbitals"]
    na, nb = spec["populations"]
    if not mf.converged or mol.nelectron != spec["active_electrons"] + 2 * ncore or mf.mo_coeff.shape[1] != norb + ncore:
        raise PreparationError("SCF convergence/electron/orbital gate; no recipe switch")
    expected_occ = np.array([2.] * ncore + [float((i < na) + (i < nb)) for i in range(norb)])
    if not np.array_equal(np.asarray(mf.mo_occ), expected_occ):
        raise PreparationError("canonical MO occupation order differs; no reorder rescue")
    cas = mcscf.CASCI(mf, norb, (na, nb))
    cas.ncore = ncore
    ledger.counts["Hamiltonian_generation_attempts"] += 1
    h1, core_energy = cas.get_h1eff(mf.mo_coeff)
    orbitals = mf.mo_coeff[:, ncore:ncore + norb]
    eri = ao2mo.restore(1, ao2mo.kernel(mol, orbitals), norb)
    with (runtime / "grouping.log").open("w") as log, redirect_stdout(log):
        grouper = Almost_optimal_grouper(float(core_energy), np.asarray(h1),
            np.asarray(eri.transpose(0, 2, 3, 1), order="C"), jordan_wigner, validation=True)
    groups = grouper.group_term_list
    groups[0].insert(0, FermionOperator("", grouper._const_fermion))
    # Up-then-down MSB sector indices; no ground-derived symmetry restriction.
    indices = np.asarray([index for index in range(1 << (2 * norb))
        if (index >> norb).bit_count() == na and (index & ((1 << norb) - 1)).bit_count() == nb], dtype=np.int64)
    reference = sum(1 << (2 * norb - 1 - pos) for pos in [*range(na), *(norb + i for i in range(nb))])
    h = csr_matrix((len(indices), len(indices)), dtype=np.complex128)
    identities, term_records, counts, removed = [], [], [], 0.
    summed_operator = QubitOperator()
    for i, group in enumerate(groups):
        op = jordan_wigner(sum(group, FermionOperator()))
        real_op, record = QubitOperator(), []
        for term, coefficient in op.terms.items():
            coefficient = complex(coefficient)
            if abs(coefficient.imag) > 1e-9:
                raise PreparationError("imaginary Pauli coefficient gate")
            real_op += QubitOperator(term, float(coefficient.real))
            record.append({"term": [[int(q), p] for q, p in term], "coefficient_hex": float(coefficient.real).hex()})
        summed_operator += real_op
        removed += float(real_op.terms.get((), 0.))
        counts.append(sum(bool(term) for term in real_op.terms))
        term_records.append(record)
        matrix = qubit_operator_sector_matrix(real_op, 2 * norb, indices, remove_constant=True)
        if sparse_norm(matrix - matrix.getH()) > 1e-12:
            raise PreparationError("group Hermiticity gate")
        path = runtime / f"group_{i:03d}.npz"
        save_npz(path, matrix)
        identities.append({"path": path.name, "sha256": sha_file(path), "dense_numpy_v1": dense_hash(matrix)})
        h = h + matrix
        ledger.check_memory()
    original = jordan_wigner(grouper.ham_fermion_upthendown_original)
    difference = summed_operator - original
    if max((abs(v) for v in difference.terms.values()), default=0.) > 1e-10:
        raise PreparationError("ordered groups fail original Hamiltonian coefficient identity")
    ledger.counts["Hamiltonian_generations"] += 1
    if sparse_norm(h - h.getH()) > 1e-12:
        raise PreparationError("Hamiltonian Hermiticity gate")
    ledger.counts["CISD_subspace_eigensolve_attempts"] += 1
    state, cisd = cisd_state(h, indices, reference)
    ledger.counts["CISD_subspace_eigensolves"] += 1
    save_npz(runtime / "hamiltonian.npz", h)
    np.savez_compressed(runtime / "state.npz", cisd=state, sector_indices=indices)
    sequence = [.1960294407008384, .2092246690782796, .3316118001935053, -.4737318199452465,
                .3316118001935053, .2092246690782796, .1960294407008384]
    k = sum(counts[i] for i, _ in iter_s2_sequence_steps(len(counts), sequence))
    ledger.timings["SCF_H_group_CISD_input"] += time.perf_counter() - started
    files = identities + [{"path": name, "sha256": sha_file(runtime / name)}
                          for name in ("hamiltonian.npz", "state.npz")]
    return {"status": "input_eligible", "condition": spec, "runtime_files": files,
            "H_dense_numpy_v1": dense_hash(h), "CISD_numpy_v1": array_hash(state),
            "sector_indices_numpy_v1": array_hash(indices), "MO_coeff_numpy_v1": array_hash(mf.mo_coeff),
            "MO_occupations_numpy_v1": array_hash(mf.mo_occ), "ordered_pauli_groups_sha256": sha_json(term_records),
            "ordered_pauli_groups": term_records, "sector_dimension": len(indices), "CISD": cisd,
            "reference_integer": reference, "SCF_energy_hartree": float(mf.e_tot),
            "removed_scalar_hartree": removed, "constant_policy": "same_scalar_free_H_all_groups",
            "K": int(k), "group_count": len(groups), "nonidentity_pauli_counts": counts,
            "PF_sequence_hex": [float(w).hex() for w in sequence], "future_M1_rank": primary_rank(len(indices))}


def load_input(identity, runtime):
    runtime = Path(runtime)
    files = identity["runtime_files"]
    expected = {"hamiltonian.npz", "state.npz"} | {f"group_{i:03d}.npz" for i in range(identity["group_count"])}
    if {f["path"] for f in files} != expected or len(files) != len(expected):
        raise PreparationError("predictor runtime manifest is not exact allowlist")
    for row in files:
        if sha_file(runtime / row["path"]) != row["sha256"]:
            raise PreparationError("frozen runtime bytes changed")
    with np.load(runtime / "state.npz", allow_pickle=False) as archive:
        if set(archive.files) != {"cisd", "sector_indices"}:
            raise PreparationError("state runtime contains non-allowlisted/truth field")
        state, indices = archive["cisd"], archive["sector_indices"]
    h = load_npz(runtime / "hamiltonian.npz").tocsr()
    if dense_hash(h) != identity["H_dense_numpy_v1"] or array_hash(state) != identity["CISD_numpy_v1"] or array_hash(indices) != identity["sector_indices_numpy_v1"]:
        raise PreparationError("individual input H/state/sector identity mismatch")
    if h.shape != (len(indices), len(indices)) or state.shape != (len(indices),) or abs(np.linalg.norm(state) - 1) > 1e-12:
        raise PreparationError("input dimension/state norm gate")
    def groups():
        for i in range(identity["group_count"]):
            matrix = load_npz(runtime / f"group_{i:03d}.npz")
            if dense_hash(matrix) != files[i]["dense_numpy_v1"]:
                raise PreparationError("individual group identity mismatch")
            yield matrix
    return h, state, groups()


class ReferenceAdapter:
    """Vector-only +it PF/H, no candidate scope and no H matvec/Arnoldi API."""
    def __init__(self, h, groups, sequence, ledger):
        self.h, self.ledger = csr_matrix(h), ledger
        self.spectra = []
        for group in groups:
            spectrum = diagonalize_components(csr_matrix(group))
            self.spectra.append(spectrum)
            ledger.counts["group_component_eigh_batches"] += sum(batch.eigenvectors is not None for batch in spectrum.batches)
            ledger.counts["group_spectrum_preparations"] += 1
            ledger.check_memory()
        self.steps = tuple(iter_s2_sequence_steps(len(self.spectra), sequence))

    def point(self, state, t):
        state = np.asarray(state, dtype=np.complex128)
        if state.shape != (self.h.shape[0],) or not np.all(np.isfinite(state)) or not math.isfinite(t) or t <= 0:
            raise PreparationError("reference adapter requires one finite vector and positive time")
        self.ledger.charge("reference_pf_actions")
        started = time.perf_counter()
        current, gates = state.copy(), {}
        for index, weight in self.steps:
            key = (index, weight)
            if key not in gates:
                gates[key] = component_exponential(self.spectra[index], float(t * weight))
                self.ledger.counts["component_gate_materializations"] += 1
            current = gates[key] @ current
            self.ledger.counts["sparse_state_multiplies"] += 1
        self.ledger.timings["reference_PF_vector_actions"] += time.perf_counter() - started
        self.ledger.max_pf_norm_residual = max(self.ledger.max_pf_norm_residual, abs(float(np.linalg.norm(current)) - float(np.linalg.norm(state))))
        if self.ledger.max_pf_norm_residual > 1e-10:
            raise PreparationError("reference PF norm gate failed")
        self.ledger.charge("reference_h_exponential_actions")
        started = time.perf_counter()
        reference = np.asarray(expm_multiply(1j * float(t) * self.h, state), dtype=np.complex128)
        self.ledger.timings["reference_H_exponential_actions"] += time.perf_counter() - started
        self.ledger.max_h_exp_norm_residual = max(self.ledger.max_h_exp_norm_residual, abs(float(np.linalg.norm(reference)) - float(np.linalg.norm(state))))
        if self.ledger.max_h_exp_norm_residual > 1e-10:
            raise PreparationError("reference H-exponential norm gate failed")
        echo = complex(np.vdot(reference, current))
        self.ledger.check_memory()
        return {"time": float(t), "time_hex": float(t).hex(), "delta_C_hartree": float(echo.imag / t),
                "echo": [echo.real, echo.imag]}
