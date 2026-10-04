"""Bounded, CPU-only H-chain preparation; no truth or Arnoldi acquisition.

Only named Hamiltonian/group/CISD members of mixed historical archives may be
extracted. Group-component diagonalization and the H6 determinant-CISD solve
belong to input preparation, not a full-H ground solve. Historical runner
modules are never imported: the four pure determinant helpers and leading_fit
are extracted from hash-verified source, with their bodies unchanged.
"""
from __future__ import annotations

import ast
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import resource
import signal
import time

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

from trotterlib.component_sector_pf import component_exponential, diagonalize_components
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.pf_decomposition import iter_s2_sequence_steps


class PreparationError(RuntimeError):
    pass


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha_array(value):
    array = np.ascontiguousarray(np.asarray(value))
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode() + b"\n")
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode() + b"\n")
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def canonical_hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False).encode()).hexdigest()


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def checked_functions(path, expected_sha, names, namespace=None):
    """Compile ONLY selected function ASTs, never imports/top-level runner code."""
    path = Path(path)
    if sha_file(path) != expected_sha:
        raise PreparationError(f"frozen helper source changed: {path}")
    definitions = {node.name: node for node in ast.parse(path.read_text()).body
                   if isinstance(node, ast.FunctionDef)}
    if set(names) - definitions.keys():
        raise PreparationError("frozen helper is missing")
    nodes = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    nodes.extend(definitions[name] for name in names)
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    scope = {"np": np, "time": time, "rolling_loglog_fits": rolling_loglog_fits}
    scope.update(namespace or {})
    exec(compile(module, str(path), "exec"), scope)
    return {name: scope[name] for name in names}


class AllowlistedArchive:
    """Byte validation followed by lazy named-member reads; no pickle."""
    def __init__(self, path, expected_sha, allowed_keys, access_log):
        self.path = Path(path)
        if sha_file(path) != expected_sha:
            raise PreparationError(f"archive identity mismatch: {path}")
        self.allowed_keys = frozenset(allowed_keys)
        if any(any(word in key.lower() for word in ("exact", "ground", "_d4", "_d6", "_d8"))
               for key in self.allowed_keys):
            raise PreparationError("truth/oracle archive member cannot be allowlisted")
        self.access_log = access_log
        self.archive = np.load(path, allow_pickle=False)

    def read(self, key):
        if key not in self.allowed_keys:
            raise PreparationError(f"archive access outside allowlist: {key}")
        value = self.archive[key].copy()
        self.access_log.append({"archive": str(self.path), "key": key, "sha256": sha_array(value)})
        return value

    def close(self):
        self.archive.close()


@dataclass
class Ledger:
    counts: Counter = field(default_factory=Counter)
    timings: Counter = field(default_factory=Counter)
    maximum_gate_cache_bytes: int = 0
    maximum_pf_norm_residual: float = 0.0
    maximum_h_exp_norm_residual: float = 0.0
    peak_rss_limit_bytes: int = 4 * 1024**3

    def check_memory(self):
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > self.peak_rss_limit_bytes:
            raise PreparationError("CPU RSS ceiling exceeded")

    def charge(self, key, maximum):
        if self.counts[key] >= maximum:
            raise PreparationError(f"action ceiling exceeded before action: {key}")
        self.counts[key] += 1
        self.check_memory()

    def payload(self):
        zero_keys = ("candidate_cheap_pf_actions", "candidate_h_exponential_actions",
                     "m1_pf_vector_actions", "m1_h_matvecs", "Arnoldi_chains",
                     "full_pf_unitary_builds", "full_H_ground_solves", "direct_truth_coordinates",
                     "target_phase_gaps", "GPU_queries", "GPU_allocations", "GPU_kernels",
                     "truth_array_reads")
        return {"counts": {**dict.fromkeys(zero_keys, 0), **dict(self.counts)},
                "timings_seconds": dict(self.timings),
                "peak_RSS_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "maximum_gate_cache_bytes": self.maximum_gate_cache_bytes,
                "maximum_pf_norm_residual": self.maximum_pf_norm_residual,
                "maximum_h_exp_norm_residual": self.maximum_h_exp_norm_residual,
                "H_exponential_internal_matvec_count": "unknown_not_exposed_by_CSR_expm_multiply",
                "CPU_processes": 1, "BLAS_threads": 1,
                "combined_H1_cost": "not_measured_preparation_only",
                "quantum_K_not_classical_action_count": True}


@contextmanager
def bounded_stage(ledger, name, seconds=1800):
    def timeout(signum, frame):
        raise PreparationError(f"stage wall ceiling exceeded: {name}")
    previous = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    started = time.perf_counter()
    try:
        yield
        ledger.check_memory()
    finally:
        ledger.timings[name] += time.perf_counter() - started
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


class VectorAdapter:
    """Vector-only PF and H actions with distinct observable/action accounting.

Cache is per coordinate, with explicit materialization cost. No dense PF is
assembled. H exponential retains the inherited CSR expm_multiply semantics;
its internal matvecs are unknown, NOT counted as one Hamiltonian matvec.
"""
    def __init__(self, hamiltonian, groups, sequence, ledger, *, allowed_kinds=("reference",)):
        self.h = csr_matrix(hamiltonian, dtype=np.complex128)
        self.sequence = tuple(float(item) for item in sequence)
        self.ledger = ledger
        self.allowed_kinds = frozenset(allowed_kinds)
        if not self.allowed_kinds <= {"reference", "candidate", "m1"}:
            raise PreparationError("unknown adapter action scope")
        started = time.perf_counter()
        self.spectra = [diagonalize_components(csr_matrix(group, dtype=np.complex128)) for group in groups]
        ledger.counts["group_spectrum_preparations"] += len(self.spectra)
        ledger.counts["group_component_eigh_batches"] += sum(
            batch.eigenvectors is not None for spectrum in self.spectra for batch in spectrum.batches)
        ledger.timings["group_spectrum_preprocessing"] += time.perf_counter() - started
        self.steps = tuple(iter_s2_sequence_steps(len(groups), self.sequence))
        self.gates = {}
        self.time_hex = None

    def _vector(self, state):
        result = np.asarray(state, dtype=np.complex128)
        if result.shape != (self.h.shape[0],) or not np.all(np.isfinite(result)):
            raise PreparationError("adapter accepts a single finite vector, not a matrix/block")
        return result

    def pf(self, state, t, *, kind="reference"):
        state = self._vector(state)
        if not math.isfinite(t) or t <= 0:
            raise PreparationError("positive finite PF time required")
        if kind not in self.allowed_kinds:
            raise PreparationError("candidate/M1 science not authorized in preparation adapter")
        counter, ceiling = {"reference": ("reference_pf_actions", 68),
                            "candidate": ("candidate_cheap_pf_actions", 9),
                            "m1": ("m1_pf_vector_actions", 60)}[kind]
        self.ledger.charge(counter, ceiling)
        if float(t).hex() != self.time_hex:
            self.gates.clear()
            self.time_hex = float(t).hex()
        current = state.copy()
        started = time.perf_counter()
        for index, weight in self.steps:
            key = (int(index), float(weight))
            gate = self.gates.get(key)
            if gate is None:
                gate_started = time.perf_counter()
                gate = component_exponential(self.spectra[index], float(t) * float(weight))
                self.gates[key] = gate
                self.ledger.counts["component_gate_materializations"] += 1
                self.ledger.timings["component_gate_materialization"] += time.perf_counter() - gate_started
            current = gate @ current
            self.ledger.counts["sparse_state_multiplies"] += 1
        self.ledger.timings["PF_vector_action"] += time.perf_counter() - started
        cache_bytes = sum(g.data.nbytes + g.indices.nbytes + g.indptr.nbytes for g in self.gates.values())
        self.ledger.maximum_gate_cache_bytes = max(self.ledger.maximum_gate_cache_bytes, cache_bytes)
        residual = abs(float(np.linalg.norm(current)) - float(np.linalg.norm(state)))
        self.ledger.maximum_pf_norm_residual = max(self.ledger.maximum_pf_norm_residual, residual)
        if residual > 1e-10:
            raise PreparationError("PF vector norm gate failed")
        return current

    def h_exp(self, state, t, *, kind="reference"):
        state = self._vector(state)
        if not math.isfinite(t) or t <= 0:
            raise PreparationError("positive finite H exponential time required")
        if kind not in self.allowed_kinds or kind not in ("reference", "candidate"):
            raise PreparationError("H exponential action outside adapter scope")
        counter, ceiling = {"reference": ("reference_h_exponential_actions", 68),
                            "candidate": ("candidate_h_exponential_actions", 9)}[kind]
        self.ledger.charge(counter, ceiling)
        started = time.perf_counter()
        result = np.asarray(expm_multiply((1j * float(t)) * self.h, state), dtype=np.complex128)
        self.ledger.timings["H_exponential_action"] += time.perf_counter() - started
        residual = abs(float(np.linalg.norm(result)) - float(np.linalg.norm(state)))
        self.ledger.maximum_h_exp_norm_residual = max(self.ledger.maximum_h_exp_norm_residual, residual)
        if residual > 1e-10:
            raise PreparationError("H exponential vector norm gate failed")
        return result

    def h_matvec(self, state):
        state = self._vector(state)
        if "m1" not in self.allowed_kinds:
            raise PreparationError("M1 H matvec not authorized in preparation adapter")
        self.ledger.charge("m1_h_matvecs", 60)
        started = time.perf_counter()
        result = self.h @ state
        self.ledger.timings["M1_H_matvec"] += time.perf_counter() - started
        return result

    def cheap(self, state, t, *, kind="reference"):
        pf_state = self.pf(state, t, kind=kind)
        h_state = self.h_exp(state, t, kind=kind)
        echo = complex(np.vdot(h_state, pf_state))
        return {"time": float(t), "time_hex": float(t).hex(),
                "delta_C_hartree": float(echo.imag / float(t)),
                "echo": [float(echo.real), float(echo.imag)]}


def state_identity(hamiltonian, groups, state, indices, reference, ledger):
    h = np.asarray(hamiltonian)
    if h.shape != (len(indices), len(indices)) or not np.all(np.isfinite(h)):
        raise PreparationError("Hamiltonian dimension/finite gate failed")
    if np.asarray(state).shape != (len(indices),) or not np.all(np.isfinite(state)):
        raise PreparationError("CISD dimension/finite gate failed")
    hermitian = float(np.linalg.norm(h - h.conj().T))
    group_sum = float(np.linalg.norm(sum(groups, np.zeros_like(h)) - h))
    norm = float(np.linalg.norm(state))
    if hermitian > 1e-12 or group_sum > 1e-12 or abs(norm - 1) > 1e-12:
        raise PreparationError("input Hermiticity/group-sum/state-norm gate failed")
    ledger.charge("input_verification_h_matvecs", 3)
    action = h @ state
    expectation = float(np.vdot(state, action).real / (norm * norm))
    residual = float(np.linalg.norm(action - expectation * state))
    positions = [i for i, index in enumerate(indices) if (int(index) ^ reference).bit_count() // 2 <= 2]
    if any(abs(state[i]) > 1e-12 for i in range(len(state)) if i not in positions):
        raise PreparationError("state support outside determinant-CISD subspace")
    return {"H_sha256_numpy_v1": sha_array(h), "CISD_sha256_numpy_v1": sha_array(state),
            "group_sha256_numpy_v1": [sha_array(group) for group in groups],
            "sector_indices_sha256_numpy_v1": sha_array(indices),
            "sector_dimension": len(indices), "RHF_reference_integer": reference,
            "CISD_positions": positions, "CISD_subspace_dimension": len(positions),
            "state_norm": norm, "H_expectation_hartree": expectation,
            "H_expectation_residual_hartree": residual,
            "H_hermiticity_residual": hermitian, "group_sum_residual": group_sum,
            "phase_alignment_to_exact_performed": False}


def reference_result(times, points, fit_function, specification, epsilon):
    fit = fit_function(times, [row["delta_C_hartree"] for row in points], specification, 4)
    if not fit["qualified"]:
        raise PreparationError("hchain_cisd_reference_scale_unavailable")
    alpha = float(fit["selected_window"]["fixed_order_alpha"])
    if not math.isfinite(alpha) or alpha <= 0:
        raise PreparationError("hchain_cisd_reference_scale_unavailable")
    t_ref = float((float(epsilon) / (5 * alpha)) ** 0.25)
    if not math.isfinite(t_ref) or t_ref <= 0:
        raise PreparationError("hchain_cisd_reference_scale_unavailable")
    return {"alpha_C": alpha, "t_ref": t_ref, "t_ref_hex": t_ref.hex(), "leading_fit": fit,
            "source": "new_fixed_grid_vector_only_cheap", "is_oracle_time": False}


def candidate_rows(references):
    if set(references) != {"H2", "H4", "H6"}:
        raise PreparationError("all three reference scales required; no subset rescue")
    rows = []
    for system in ("H2", "H4", "H6"):
        t_ref = float(references[system]["t_ref"])
        if not math.isfinite(t_ref) or t_ref <= 0:
            raise PreparationError("invalid reference scale")
        for ratio, label in zip((0.5, 0.65, 0.8), (1.0, 1.3, 1.6), strict=True):
            t = float(ratio) * t_ref
            rows.append({"system": system, "candidate_id": f"{system}_r{ratio}",
                         "ratio": ratio, "ratio_hex": ratio.hex(), "factor_of_T0_label": label,
                         "t_ref": t_ref, "t_ref_hex": t_ref.hex(), "time": t,
                         "time_hex": t.hex(), "T0": 0.5 * t_ref,
                         "primary_m": 4 if system == "H2" else 8,
                         "K": {"H2": 108, "H4": 2556, "H6": 14344}[system]})
    return rows
