"""H8 storage/lifetime extension; inherited vector and decision bodies unchanged."""
from __future__ import annotations

import hashlib
import json
import resource
import time
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, load_npz
from scipy.sparse.linalg import norm as sparse_norm

from review_response.hchain_input_reference_preparation import (
    PreparationError, VectorAdapter, diagonalize_components, iter_s2_sequence_steps,
    sha_array, sha_file, write_json,
)
from review_response.hchain_odd_extension import (
    SystemLedger, commit_files, file_entry, git, plan_rows as old_plan_rows,
)
from review_response.hchain_prediction_phase import check_remote, require_clean, verify_blob, verify_entries

BASE = "50b73a363fa581f8534c399f087b35cb38a4cb70"
DOC = "docs/second_study_v2/hchain_h8_memory_safe_20261004"
OUT = "artifacts/hchain_h8_memory_safe_extension_20261004"
BRANCH = "pf-second-study-v2-hchain-h8-memory-safe-extension-20261004"
STATUS = "hchain_h8_extension_complete_review_required"
SOURCES = (f"{DOC}/protocol.json", f"{DOC}/memory_design.md", f"{DOC}/source_registry.json",
    "review_response/hchain_h8_memory_safe.py", "review_response/run_hchain_h8_memory_safe.py",
    "review_tests/test_hchain_h8_memory_safe.py")


def read(path):
    return json.loads(Path(path).read_text())


def array_digest_stream(array):
    """Exactly numpy_v1 hash, without array.tobytes' full-sized copy."""
    array = np.asarray(array)
    if not array.flags.c_contiguous:
        raise PreparationError("stream hash requires contiguous frozen representation")
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode()+b"\n")
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode()+b"\n")
    digest.update(memoryview(array).cast("B"))
    return digest.hexdigest()


def dense_digest_stream(matrix):
    """Dense numpy_v1 identity from one CSR row at a time, not a dense group."""
    matrix = csr_matrix(matrix, dtype=np.complex128)
    digest = hashlib.sha256()
    digest.update(matrix.dtype.str.encode()+b"\n")
    digest.update(json.dumps(list(matrix.shape), separators=(",", ":")).encode()+b"\n")
    for index in range(matrix.shape[0]):
        digest.update(memoryview(matrix[index:index+1].toarray()).cast("B"))
    return digest.hexdigest()


def csr_bytes(matrix):
    return sum(a.nbytes for a in (matrix.data, matrix.indices, matrix.indptr))


def current_memory():
    fields = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:", "VmSwap:")):
            name, value, _ = line.split()
            fields[name.rstrip(":")+"_bytes"] = int(value)*1024
    return fields


class H8Ledger(SystemLedger):
    def __init__(self, primary=8):
        super().__init__(primary)
        self.memory_events = []

    def snapshot(self, stage, *, largest_object_bytes=0, live_dense_matrices=0,
                 explicit_large_allocations=0):
        self.check_memory()
        row = {"stage": stage, **current_memory(), "largest_object_bytes": int(largest_object_bytes),
            "simultaneously_live_full_sector_dense_matrices": live_dense_matrices,
            "explicit_large_allocation_count": explicit_large_allocations,
            "allocation_count_scope": "instrumented Python-owned full-sector objects; native temporaries unobserved"}
        if row.get("VmSwap_bytes", 0):
            raise PreparationError("own-process swap use; do not rely on swap")
        self.memory_events.append(row)
        return row

    def payload(self):
        return {**super().payload(), "memory_events": self.memory_events,
                "native_workspace_allocation_count": "unknown_not_instrumented"}


class StreamingVectorAdapter(VectorAdapter):
    """Only __init__ changes: consume one group CSR and retain component spectra.

    pf/h_exp/h_matvec/cheap are inherited unchanged, including per-time gate
    cache, component eigensolver, thresholds, ordering and counters.
    """
    def __init__(self, hamiltonian, groups, group_count, sequence, ledger, *, allowed_kinds=("reference",)):
        self.h = csr_matrix(hamiltonian, dtype=np.complex128)
        self.sequence = tuple(float(item) for item in sequence)
        self.ledger, self.allowed_kinds = ledger, frozenset(allowed_kinds)
        if not self.allowed_kinds <= {"reference", "candidate", "m1"}:
            raise PreparationError("unknown adapter action scope")
        self.spectra = []
        started = time.perf_counter()
        self.maximum_group_csr_bytes = 0
        self.maximum_component_batch_bytes = 0
        for group in groups:
            group = csr_matrix(group, dtype=np.complex128)
            self.maximum_group_csr_bytes = max(self.maximum_group_csr_bytes, csr_bytes(group))
            spectrum = diagonalize_components(group)
            self.spectra.append(spectrum)
            self.maximum_component_batch_bytes = max(self.maximum_component_batch_bytes,
                max((0 if b.eigenvectors is None else b.eigenvectors.nbytes for b in spectrum.batches), default=0))
            ledger.check_memory()
            del group, spectrum
        if len(self.spectra) != group_count:
            raise PreparationError("group stream count mismatch")
        ledger.counts["group_spectrum_preparations"] += group_count
        ledger.counts["group_component_eigh_batches"] += sum(
            b.eigenvectors is not None for s in self.spectra for b in s.batches)
        ledger.timings["group_spectrum_preprocessing"] += time.perf_counter()-started
        self.steps = tuple(iter_s2_sequence_steps(group_count, self.sequence))
        self.gates, self.time_hex = {}, None

    def storage_profile(self):
        arrays = []
        for spectrum in self.spectra:
            for batch in spectrum.batches:
                arrays.extend((batch.indices, batch.eigenvalues))
                if batch.eigenvectors is not None:
                    arrays.append(batch.eigenvectors)
        return {"Hamiltonian_CSR_bytes": csr_bytes(self.h),
            "retained_component_array_bytes": sum(a.nbytes for a in arrays),
            "maximum_one_group_CSR_bytes": self.maximum_group_csr_bytes,
            "maximum_component_batch_bytes": self.maximum_component_batch_bytes,
            "simultaneous_full_sector_dense_group_matrices": 0,
            "maximum_simultaneous_input_group_CSR": 1}


def seal(root):
    check_remote(root)
    require_clean(root)
    content = git(root, "rev-parse", "HEAD").decode().strip()
    git(root, "merge-base", "--is-ancestor", BASE, content)
    entries = [{**file_entry(root, root/name), "origin_result_commit": content,
                "verified_snapshot_commit": content} for name in SOURCES]
    for name in SOURCES:
        verify_blob(root, name, content)
    write_json(root/DOC/"implementation_manifest.json", {
        "content_commit": content, "base_verified_snapshot": BASE,
        "files": entries, "manifest_self_excluded": True})


def source_gate(root):
    check_remote(root)
    require_clean(root)
    manifest_path = root/DOC/"implementation_manifest.json"
    verify_blob(root, str(manifest_path.relative_to(root)), "HEAD")
    sealed = read(manifest_path)
    git(root, "merge-base", "--is-ancestor", BASE, sealed["content_commit"])
    git(root, "merge-base", "--is-ancestor", sealed["content_commit"], "HEAD")
    if {r["path"] for r in sealed["files"]} != set(SOURCES):
        raise PreparationError("source file set mismatch")
    verify_entries(root, sealed["files"])
    for row in sealed["files"]:
        verify_blob(root, row["path"], sealed["content_commit"])
    registry = read(root/DOC/"source_registry.json")
    verify_entries(root, registry["sources"])
    for row in registry["sources"]:
        verify_blob(root, row["path"], BASE)
    for line in git(root, "diff", "--name-status", BASE, "HEAD").decode().splitlines():
        kind, name = line.split("\t")
        if kind != "A" or (name not in SOURCES and not name.startswith((DOC+"/", OUT+"/"))):
            raise PreparationError("existing scientific source/artifact changed")
    new_files = list(sealed["files"])
    regression = root/DOC/"implementation_equivalence.json"
    if regression.exists():
        verify_blob(root, str(regression.relative_to(root)), "HEAD")
        new_files.append(file_entry(root, regression))
    return {"execution_HEAD": git(root, "rev-parse", "HEAD").decode().strip(),
        "content_commit": sealed["content_commit"], "verified_base_snapshot": BASE,
        "implementation_manifest_sha256": sha_file(manifest_path),
        "new_files": new_files, "inherited_sources": registry["sources"],
        "inherited_artifacts_modified": False}


def runtime_gate(out, inputs, *, allow_ground=False):
    runtime = out/".runtime"
    found = {str(p.relative_to(runtime)) for p in runtime.rglob("*") if p.is_file()}
    if allow_ground:
        found -= {"H8_ground.npz"}
    if found != {r["path"] for r in inputs["runtime_files"]} or runtime.is_symlink():
        raise PreparationError("runtime exact file set mismatch")
    if any(p.is_symlink() for p in runtime.rglob("*")):
        raise PreparationError("linked runtime forbidden")
    verify_entries(runtime, inputs["runtime_files"])


def load_system(out, inputs, name, ledger, members, sequence, scopes, *, allow_ground=False):
    if name != "H8":
        raise PreparationError("H8-only execution")
    runtime_gate(out, inputs, allow_ground=allow_ground)
    spec, private = inputs["input_identity"][name], out/".runtime"
    h = load_npz(private/"H8_H.npz")
    with np.load(private/"H8_state.npz", allow_pickle=False) as archive:
        if set(archive.files) != {"cisd", "sector_indices"}:
            raise PreparationError("sanitized state keys mismatch")
        state, indices = archive["cisd"].copy(), archive["sector_indices"].copy()
    if (dense_digest_stream(h) != spec["H_sha256_numpy_v1"]
            or sha_array(state) != spec["CISD_sha256_numpy_v1"]
            or sha_array(indices) != spec["sector_indices_sha256_numpy_v1"]):
        raise PreparationError("input identity mismatch")
    members.extend({"archive": str(private/"H8_state.npz"), "key": key, "sha256": sha_array(value)}
                   for key, value in (("cisd", state), ("sector_indices", indices)))
    def groups():
        for index, expected in enumerate(spec["group_sha256_numpy_v1"]):
            path = private/f"H8_group_{index:03d}.npz"
            group = load_npz(path)
            if dense_digest_stream(group) != expected:
                raise PreparationError("group dense-equivalent identity mismatch")
            members.append({"archive": str(path), "key": "CSR_group", "dense_numpy_v1_sha256": expected})
            yield group
            del group
    adapter = StreamingVectorAdapter(h, groups(), spec["group_count"], sequence, ledger, allowed_kinds=scopes)
    ledger.snapshot("streamed_component_preprocessing", largest_object_bytes=adapter.maximum_component_batch_bytes)
    return {"state": state, "adapter": adapter}


def plan_rows(references, identity):
    # Original implementation's body, with only its requested system inventory parameterized.
    import review_response.hchain_odd_extension as inherited
    original = inherited.SYSTEMS
    try:
        inherited.SYSTEMS = ("H8",)
        return old_plan_rows(references, identity)
    finally:
        inherited.SYSTEMS = original


def validate_plan(rows, references, identity):
    if rows != plan_rows(references, identity):
        raise PreparationError("exact binary64 candidate plan mismatch")
    return rows


def truth_feasibility(dimension, retained_rss_bytes, h7_timings, group_step_ratio):
    """Planning arithmetic, NOT a measured H8 truth benchmark/certified bound."""
    one = dimension**2*16
    memory = retained_rss_bytes+9*one
    scale = dimension/735
    schur = h7_timings["truth_Schur_branch_gap"]/3*scale**3
    pf = h7_timings["truth_full_PF_construction"]/3*scale**2*group_step_ratio
    ground = h7_timings["H7_same_H_ground"]*scale**3
    return {"dense_matrix_bytes": one, "budgeted_simultaneous_dense_objects": 9,
        "required_objects": ["U", "Schur_T", "Schur_vectors", "identity", "conjugate_U",
                             "Gram", "difference", "two_native_copy_workspace_reserves"],
        "predicted_memory_bytes": memory, "retained_rss_bytes": retained_rss_bytes,
        "memory_ceiling_bytes": 4*1024**3,
        "predicted_one_coordinate_seconds": pf+schur,
        "predicted_same_H_ground_seconds": ground,
        "predicted_three_coordinate_seconds": 3*(pf+schur),
        "estimate_class": "post_hoc_complexity_extrapolation_not_a_bound",
        "native_workspace_requirement_certified": False,
        "feasible": memory < 4*1024**3 and pf+schur < 1800 and ground < 1800}
