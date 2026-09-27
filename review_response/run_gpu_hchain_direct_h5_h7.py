#!/usr/bin/env python3
"""Freeze, run, gate, and report the H5/H7 exact GPU direct extension."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

# Truth processes are constrained before NumPy/SciPy are imported.
for _thread_variable in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_variable] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np

import hchain_direct_sector_v1_1 as sector_v1_1
import run_hchain_direct_optimal_time_scaling as parent
import sweep_direct_scaling_h6_h7 as direct
from trotterlib.product_formula import _get_s2_sequence
from trotterlib.sector_pf import build_sector_pf_unitary
from trotterlib.sector_pf_gpu import GpuSectorPFBuilder


PARENT_RESULT_COMMIT = "c27e31e82ca55fc404ed33123cfd5d2c6a76bc35"
PARENT_PROTOCOL_SHA256 = (
    "12d10562cf481b836242786462184d8a6ffb342153404c9bf84ff4d5ca836ab9"
)
SECTOR_AMENDMENT_SHA256 = (
    "5ca0ea30f9ad08bc7e4a54fcd8bab8f50195752dcaf3717c219281a458b0122e"
)
PARTIAL_AMENDMENT_SHA256 = (
    "526bdede05c1b39d0fab21e062b39a48284a1338fd51bc3c94fd3488732c70ff"
)
EXPECTED_REMOTE_SUFFIX = (
    "HIROMU1015/"
    "Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-"
    "higher-order-product-formulae.git"
)
PROTOCOL = Path("review_response/hchain_direct_optimal_time_scaling_protocol.json")
SECTOR_AMENDMENT = Path(
    "review_response/hchain_direct_optimal_time_scaling_amendment_v1_1.json"
)
PARTIAL_AMENDMENT = Path(
    "review_response/hchain_direct_optimal_time_scaling_partial_stop_amendment_v1_2.json"
)
EXTENSION = Path("review_response/hchain_direct_gpu_h5_h7_extension.json")
EXTENSION_MD = Path("review_response/hchain_direct_gpu_h5_h7_extension.md")
PARENT_RAW_ROOT = Path(
    "artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961/raw"
)
SYSTEMS = {
    5: {
        "id": "H5",
        "family": "odd_cation_triplet",
        "population_counts": [3, 1],
        "dimension": 50,
        "group_count": 45,
    },
    7: {
        "id": "H7",
        "family": "odd_cation_triplet",
        "population_counts": [4, 2],
        "dimension": 735,
        "group_count": 105,
    },
}
FORMULAS = {
    "m5": {
        "label": direct.M5_LABEL,
        "unique_s2_weights": 6,
        "fit_times": direct.DEFAULT_M5_TIMES,
    },
    "y8": {
        "label": direct.Y8_LABEL,
        "unique_s2_weights": 11,
        "fit_times": direct.DEFAULT_Y8_TIMES,
    },
}
SOURCE_PATHS = (
    Path("src/trotterlib/sector_pf_gpu.py"),
    Path("src/trotterlib/sector_pf.py"),
    Path("review_response/run_gpu_hchain_direct_h5_h7.py"),
    Path("review_response/run_hchain_direct_optimal_time_scaling.py"),
    Path("review_response/sweep_direct_scaling_h6_h7.py"),
    Path("review_response/hchain_direct_sector_v1_1.py"),
    Path("review_response/hchain_direct_gpu_h5_h7_extension.json"),
    Path("review_response/hchain_direct_gpu_h5_h7_extension.md"),
    Path("review_tests/test_gpu_hchain_direct_h5_h7.py"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_command(args: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git_value(*args: str) -> str:
    return run_command(["git", *args]).stdout.strip()


def verify_parent_identity() -> dict[str, str]:
    paths_and_hashes = {
        PROTOCOL: PARENT_PROTOCOL_SHA256,
        SECTOR_AMENDMENT: SECTOR_AMENDMENT_SHA256,
        PARTIAL_AMENDMENT: PARTIAL_AMENDMENT_SHA256,
    }
    for relative, expected in paths_and_hashes.items():
        actual = sha256(PROJECT_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"fixed identity mismatch for {relative}: {actual}")
    remote = git_value("remote", "get-url", "origin")
    normalized = remote.rstrip("/")
    if not normalized.endswith(EXPECTED_REMOTE_SUFFIX):
        raise RuntimeError(f"unexpected origin remote: {remote}")
    run_command(["git", "cat-file", "-e", f"{PARENT_RESULT_COMMIT}^{{commit}}"])
    ancestor = run_command(
        ["git", "merge-base", "--is-ancestor", PARENT_RESULT_COMMIT, "HEAD"],
        check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError("HEAD is not descended from the fixed parent result commit")
    return {
        "origin": remote,
        "parent_result_commit": PARENT_RESULT_COMMIT,
        "protocol_sha256": PARENT_PROTOCOL_SHA256,
        "sector_amendment_sha256": SECTOR_AMENDMENT_SHA256,
        "partial_stop_amendment_sha256": PARTIAL_AMENDMENT_SHA256,
    }


def fixed_grid() -> list[float]:
    protocol = load_json(PROJECT_ROOT / PROTOCOL)
    grid = parent._grid_from_protocol(protocol)
    if grid != [round(0.20 + 0.05 * index, 12) for index in range(31)]:
        raise RuntimeError("parent protocol no longer defines the fixed 31-point grid")
    return grid


def _meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        key, raw = line.split(":", 1)
        values[key] = int(raw.strip().split()[0]) * 1024
    return {
        "total_bytes": values["MemTotal"],
        "available_bytes": values["MemAvailable"],
    }


def gpu_snapshot(physical_gpu: int) -> dict[str, Any]:
    fields = (
        "index,name,uuid,driver_version,memory.total,memory.free,memory.used,"
        "utilization.gpu"
    )
    result = run_command(
        [
            "nvidia-smi",
            f"--id={int(physical_gpu)}",
            f"--query-gpu={fields}",
            "--format=csv,noheader,nounits",
        ]
    )
    values = [item.strip() for item in result.stdout.strip().split(",")]
    if len(values) != 8:
        raise RuntimeError(f"unexpected nvidia-smi output: {result.stdout!r}")
    processes_result = run_command(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_gpu_memory,gpu_uuid",
            "--format=csv,noheader,nounits",
        ],
        check=False,
    )
    processes = [
        line.strip()
        for line in processes_result.stdout.splitlines()
        if line.strip()
    ]
    return {
        "physical_gpu_id": int(values[0]),
        "name": values[1],
        "uuid": values[2],
        "driver_version": values[3],
        "total_bytes": int(values[4]) * 2**20,
        "free_bytes": int(values[5]) * 2**20,
        "used_bytes": int(values[6]) * 2**20,
        "utilization_percent": int(values[7]),
        "existing_compute_processes_all_gpus": processes,
    }


def resource_estimate(h_chain: int, formula_key: str) -> dict[str, Any]:
    system = SYSTEMS[h_chain]
    dimension = int(system["dimension"])
    groups = int(system["group_count"])
    unique_blocks = int(FORMULAS[formula_key]["unique_s2_weights"])
    f64 = 8
    c128 = 16
    d2 = dimension * dimension
    arrays = [
        {"name": "group_eigenvalues", "shape": [groups, dimension], "dtype": "float64", "bytes": groups * dimension * f64, "placement": "host_and_device"},
        {"name": "group_eigenvectors", "shape": [groups, dimension, dimension], "dtype": "complex128", "bytes": groups * d2 * c128, "placement": "host_and_device"},
        {"name": "hamiltonian", "shape": [dimension, dimension], "dtype": "complex128", "bytes": d2 * c128, "placement": "host"},
        {"name": "state", "shape": [dimension], "dtype": "complex128", "bytes": dimension * c128, "placement": "host"},
        {"name": "unique_s2_block_cache", "shape": [unique_blocks, dimension, dimension], "dtype": "complex128", "bytes": unique_blocks * d2 * c128, "placement": "device"},
        {"name": "pf_unitary", "shape": [dimension, dimension], "dtype": "complex128", "bytes": d2 * c128, "placement": "host_and_device"},
        {"name": "gpu_gemm_scratch_upper_bound", "shape": [6, dimension, dimension], "dtype": "complex128", "bytes": 6 * d2 * c128, "placement": "device"},
        {"name": "cpu_schur_triangular_vectors_workspace_upper_bound", "shape": [12, dimension, dimension], "dtype": "complex128", "bytes": 12 * d2 * c128, "placement": "host"},
        {"name": "cuda_context_and_library_reserve", "shape": None, "dtype": "bytes", "bytes": 512 * 2**20, "placement": "device"},
    ]
    host_peak = sum(
        row["bytes"] for row in arrays if row["placement"] in ("host", "host_and_device")
    )
    # Sector construction temporarily holds two additional dense host matrices.
    host_peak += 2 * d2 * c128
    device_peak = sum(
        row["bytes"] for row in arrays if row["placement"] in ("device", "host_and_device")
    )
    s2_group_steps = 2 * groups - 1
    dense_n3_units_per_point = (
        unique_blocks * s2_group_steps * 2 * dimension**3
        + len(_get_s2_sequence(str(FORMULAS[formula_key]["label"]))) * dimension**3
    )
    return {
        "system": f"H{h_chain}",
        "formula_key": formula_key,
        "dimension": dimension,
        "group_count": groups,
        "unique_s2_blocks": unique_blocks,
        "resident_arrays": arrays,
        "host_peak_upper_bound_bytes": int(host_peak),
        "device_peak_upper_bound_bytes": int(device_peak),
        "host_required_with_20_percent_margin_bytes": int(np.ceil(1.2 * host_peak)),
        "device_required_with_20_percent_margin_bytes": int(np.ceil(1.2 * device_peak)),
        "dense_n3_units_per_direct_point": int(dense_n3_units_per_point),
        "dense_n3_units_for_31_direct_points": int(31 * dense_n3_units_per_point),
        "wall_time_gate_role": "record_only_for_H5_H7; the registered 72-hour automatic gate applied to H8/H9, which are outside this user-limited run",
        "exact_complex128_plan_preserved": True,
    }


def resource_preflight(h_chain: int, formula_key: str, physical_gpu: int) -> dict[str, Any]:
    estimate = resource_estimate(h_chain, formula_key)
    host = _meminfo()
    gpu = gpu_snapshot(physical_gpu)
    host_pass = host["available_bytes"] >= estimate["host_required_with_20_percent_margin_bytes"]
    device_pass = gpu["free_bytes"] >= estimate["device_required_with_20_percent_margin_bytes"]
    return {
        "captured_at_utc": utc_now(),
        "before_hamiltonian_generation_and_device_allocation": True,
        "host": host,
        "gpu": gpu,
        "estimate": estimate,
        "gates": {
            "host_20_percent_margin": host_pass,
            "device_20_percent_margin": device_pass,
            "complex128_exact_plan": True,
            "pass": host_pass and device_pass,
        },
    }


def package_identity() -> dict[str, Any]:
    packages: dict[str, str | None] = {}
    for distribution in (
        "numpy",
        "scipy",
        "pyscf",
        "openfermion",
        "cupy-cuda12x",
    ):
        try:
            packages[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            packages[distribution] = None
    import cupy as cp

    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "packages": packages,
        "cupy_module": str(Path(cp.__file__).resolve()),
        "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
        "cuda_device_count_visible": int(cp.cuda.runtime.getDeviceCount()),
    }


def focused_test_args() -> list[str]:
    return [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "review_tests/test_gpu_hchain_direct_h5_h7.py",
        "review_tests/test_hchain_direct_optimal_time_scaling.py",
        "review_tests/test_hchain_direct_optimal_time_scaling_partial_v1_2.py",
        "review_tests/test_hchain_direct_sector_v1_1.py",
        "review_tests/test_sector_pf.py",
    ]


def execute_tests(kind: str, log_path: Path) -> dict[str, Any]:
    args = focused_test_args() if kind == "focused" else [sys.executable, "-m", "pytest", "-q", "review_tests"]
    started = time.perf_counter()
    result = run_command(args, check=False)
    elapsed = time.perf_counter() - started
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "$ " + " ".join(args) + "\n\n" + result.stdout + result.stderr,
        encoding="utf-8",
    )
    summary = {
        "kind": kind,
        "returncode": result.returncode,
        "elapsed_seconds": elapsed,
        "log": str(log_path),
    }
    if result.returncode != 0:
        raise RuntimeError(f"{kind} tests failed; see {log_path}")
    return summary


def predictions_payload() -> dict[str, Any]:
    return {
        "schema_version": "hchain_direct_gpu_h5_h7_predictions_v1",
        "frozen_before_new_truth": True,
        "scope": ["H5/m5", "H5/y8", "H7/m5", "H7/y8"],
        "H5": {
            "m5": {
                "analytic_time": 2.5939977275727855,
                "selected_relative_time": 1.35,
                "selected_grid_time": 3.5018969322232607,
                "expected_gate": "scorable",
            },
            "y8": {
                "apparent_selected_relative_time": 1.25,
                "expected_gate": "not_scorable_branch_shift_disagreement",
                "known_maximum_branch_shift_disagreement_hartree": 0.01341058883834719,
            },
        },
        "H7": {
            "m5": {"quantitative_optimum_prediction": None, "role": "new odd-family descriptive point"},
            "y8": {"quantitative_optimum_prediction": None, "role": "new odd-family descriptive point"},
        },
        "analysis_predictions": {
            "odd_m5_fit": "not_performed_because_H9_is_out_of_scope",
            "odd_y8_fit": "not_performed_because_H9_is_out_of_scope_and_H5_y8_is_expected_to_fail",
            "H8_holdout": "not_run_by_user_scope",
        },
    }


def freeze_phase_a(output: Path, physical_gpu: int) -> None:
    if output.exists():
        raise RuntimeError(f"refusing to overwrite Phase A output: {output}")
    identity = verify_parent_identity()
    fixed_grid()
    extension = load_json(PROJECT_ROOT / EXTENSION)
    if extension["scope_change"]["included_systems_in_order"] != ["H5", "H7"]:
        raise RuntimeError("extension scope is not exactly H5/H7")
    if extension["scope_change"]["excluded_from_this_run"] != ["H8", "H9"]:
        raise RuntimeError("extension does not explicitly exclude H8/H9")
    output.mkdir(parents=True)
    test_summary = execute_tests("focused", output / "focused_tests.log")
    predictions = predictions_payload()
    write_json(output / "predictions.json", predictions)
    prediction_hash = sha256(output / "predictions.json")
    (output / "prediction.sha256").write_text(
        f"{prediction_hash}  predictions.json\n", encoding="utf-8"
    )
    for source, destination in (
        (PROTOCOL, Path("protocol.json")),
        (SECTOR_AMENDMENT, Path("amendment_v1_1.json")),
        (PARTIAL_AMENDMENT, Path("amendment_partial_v1_2.json")),
        (EXTENSION, Path("gpu_extension_h5_h7.json")),
        (EXTENSION_MD, Path("gpu_extension_h5_h7.md")),
    ):
        shutil.copyfile(PROJECT_ROOT / source, output / destination)
    source_files = []
    for relative in SOURCE_PATHS:
        path = PROJECT_ROOT / relative
        if not path.exists():
            raise RuntimeError(f"required source file missing: {relative}")
        source_files.append({"path": str(relative), "sha256": sha256(path)})
    source_manifest = {
        "schema_version": "hchain_direct_gpu_h5_h7_source_manifest_v1",
        "created_at_utc": utc_now(),
        "git_head_before_phase_a_commit": git_value("rev-parse", "HEAD"),
        "git_branch": git_value("branch", "--show-current"),
        "parent_identity": identity,
        "files": source_files,
    }
    write_json(output / "source_manifest.json", source_manifest)
    source_manifest_hash = sha256(output / "source_manifest.json")
    feasibility = {
        "schema_version": "hchain_direct_gpu_h5_h7_resource_feasibility_v1",
        "phase": "A_no_truth",
        "targets": {
            f"H{h_chain}_{formula_key}": resource_preflight(h_chain, formula_key, physical_gpu)
            for h_chain in (5, 7)
            for formula_key in ("m5", "y8")
        },
        "H8_H9": "not_estimated_or_executed_by_user_scope",
    }
    write_json(output / "resource_feasibility.json", feasibility)
    environment = package_identity()
    audit = {
        "schema_version": "hchain_direct_gpu_h5_h7_phase_a_audit_v1",
        "status": "phase_a_frozen_no_truth_generated",
        "created_at_utc": utc_now(),
        "parent_identity": identity,
        "extension_sha256": sha256(PROJECT_ROOT / EXTENSION),
        "prediction_sha256": prediction_hash,
        "source_manifest_sha256": source_manifest_hash,
        "environment": environment,
        "focused_tests": test_summary,
        "truth_generation": {
            "hamiltonian": 0,
            "state": 0,
            "group_spectrum": 0,
            "short_time_fit": 0,
            "pf_unitary": 0,
            "direct_points": 0,
        },
    }
    write_json(output / "audit.json", audit)
    marker = {
        "status": "PHASE_A_FROZEN",
        "parent_protocol_sha256": PARENT_PROTOCOL_SHA256,
        "sector_amendment_sha256": SECTOR_AMENDMENT_SHA256,
        "partial_stop_amendment_sha256": PARTIAL_AMENDMENT_SHA256,
        "extension_sha256": audit["extension_sha256"],
        "prediction_sha256": prediction_hash,
        "source_manifest_sha256": source_manifest_hash,
        "direct_truth_points_at_freeze": 0,
    }
    write_json(output / "PHASE_A_FROZEN", marker)
    files = sorted(path for path in output.iterdir() if path.is_file())
    parent._manifest(
        output,
        files,
        {
            "schema_version": "hchain_direct_gpu_h5_h7_phase_a_manifest_v1",
            "status": "phase_a_frozen_no_truth_generated",
            "created_at_utc": utc_now(),
        },
    )


def validate_phase_a(phase_a: Path) -> dict[str, Any]:
    marker_path = phase_a / "PHASE_A_FROZEN"
    if not marker_path.exists():
        raise RuntimeError("PHASE_A_FROZEN is missing")
    marker = load_json(marker_path)
    required = {
        "parent_protocol_sha256": PARENT_PROTOCOL_SHA256,
        "sector_amendment_sha256": SECTOR_AMENDMENT_SHA256,
        "partial_stop_amendment_sha256": PARTIAL_AMENDMENT_SHA256,
        "extension_sha256": sha256(PROJECT_ROOT / EXTENSION),
        "prediction_sha256": sha256(phase_a / "predictions.json"),
        "source_manifest_sha256": sha256(phase_a / "source_manifest.json"),
    }
    for key, expected in required.items():
        if marker.get(key) != expected:
            raise RuntimeError(f"Phase A marker mismatch for {key}")
    if marker.get("direct_truth_points_at_freeze") != 0:
        raise RuntimeError("Phase A marker is not truth-free")
    prediction_line = (phase_a / "prediction.sha256").read_text(encoding="utf-8").split()[0]
    if prediction_line != required["prediction_sha256"]:
        raise RuntimeError("prediction.sha256 mismatch")
    source_manifest = load_json(phase_a / "source_manifest.json")
    for row in source_manifest["files"]:
        current = sha256(PROJECT_ROOT / row["path"])
        if current != row["sha256"]:
            raise RuntimeError(f"frozen source changed: {row['path']}")
    verify_parent_identity()
    return marker


def initialize_output(output: Path, phase_a: Path, h_chain: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    identity_file = output / "phase_a_identity.json"
    payload = {
        "phase_a_path": str(phase_a.resolve()),
        "system": f"H{h_chain}",
        "phase_a_marker_sha256": sha256(phase_a / "PHASE_A_FROZEN"),
    }
    if identity_file.exists():
        if load_json(identity_file) != payload:
            raise RuntimeError("output belongs to a different Phase A or system")
    else:
        write_json(identity_file, payload)
    copies = (
        "protocol.json",
        "amendment_v1_1.json",
        "amendment_partial_v1_2.json",
        "gpu_extension_h5_h7.json",
        "gpu_extension_h5_h7.md",
        "predictions.json",
        "prediction.sha256",
        "PHASE_A_FROZEN",
        "source_manifest.json",
    )
    for name in copies:
        destination = output / name
        source = phase_a / name
        if destination.exists():
            if sha256(destination) != sha256(source):
                raise RuntimeError(f"fixed output identity mismatch: {destination}")
        else:
            shutil.copyfile(source, destination)


def cache_key(phase_a: Path, h_chain: int, formula_key: str) -> tuple[str, dict[str, Any]]:
    extension = load_json(PROJECT_ROOT / EXTENSION)
    material = {
        "parent_protocol_sha256": PARENT_PROTOCOL_SHA256,
        "sector_amendment_sha256": SECTOR_AMENDMENT_SHA256,
        "partial_stop_amendment_sha256": PARTIAL_AMENDMENT_SHA256,
        "gpu_extension_sha256": sha256(PROJECT_ROOT / EXTENSION),
        "prediction_sha256": sha256(phase_a / "predictions.json"),
        "source_manifest_sha256": sha256(phase_a / "source_manifest.json"),
        "system": f"H{h_chain}",
        "sector_identity": extension["expected_sector_identity"][f"H{h_chain}"],
        "formula_key": formula_key,
        "formula_label": FORMULAS[formula_key]["label"],
        "relative_grid": fixed_grid(),
        "backend": "gpu_exact_dense_sector_unitary_cpu_complex128_schur",
        "dtype": "complex128",
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest(), material


def validate_system_identity(system: dict[str, Any], h_chain: int) -> None:
    expected = SYSTEMS[h_chain]
    sector = system["sector"]
    observed = {
        "population_counts": list(sector["population_counts"]),
        "dimension": int(sector["dimension"]),
        "group_count": int(system["num_groups"]),
    }
    for key, value in observed.items():
        if value != expected[key]:
            raise RuntimeError(
                f"H{h_chain} sector identity mismatch for {key}: {value} != {expected[key]}"
            )


class GpuMemoryMonitor:
    def __init__(self, physical_gpu: int, interval: float = 0.2):
        self.gpu = int(physical_gpu)
        self.interval = float(interval)
        self.values: list[int] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _query(self) -> None:
        while not self._stop.is_set():
            result = run_command(
                [
                    "nvidia-smi",
                    f"--id={self.gpu}",
                    "--query-gpu=memory.used",
                    "--format=csv,noheader,nounits",
                ],
                check=False,
            )
            try:
                self.values.append(int(result.stdout.strip().splitlines()[0]))
            except (ValueError, IndexError):
                pass
            self._stop.wait(self.interval)

    def __enter__(self) -> "GpuMemoryMonitor":
        self._thread = threading.Thread(target=self._query, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def summary(self) -> dict[str, Any]:
        return {
            "physical_gpu_id": self.gpu,
            "sample_count": len(self.values),
            "minimum_used_mib": min(self.values) if self.values else None,
            "maximum_used_mib": max(self.values) if self.values else None,
            "peak_increment_mib": (
                max(self.values) - min(self.values) if self.values else None
            ),
        }


def formula_result(payload: dict[str, Any], h_chain: int, formula_key: str) -> dict[str, Any]:
    return payload["results"][f"H{h_chain}"]["results"][str(FORMULAS[formula_key]["label"])]


def selected_summary(payload: dict[str, Any], h_chain: int, formula_key: str) -> dict[str, Any]:
    protocol = load_json(PROJECT_ROOT / PROTOCOL)
    return parent.summarize_formula(formula_result(payload, h_chain, formula_key), protocol)


def parent_cpu_raw(formula_key: str) -> dict[str, Any]:
    return load_json(PROJECT_ROOT / PARENT_RAW_ROOT / f"H5_{formula_key}.json")


def compare_raw_to_parent(gpu: dict[str, Any], formula_key: str) -> dict[str, Any]:
    cpu = parent_cpu_raw(formula_key)
    gpu_points = formula_result(gpu, 5, formula_key)["points"]
    cpu_points = formula_result(cpu, 5, formula_key)["points"]
    if len(gpu_points) != 31 or len(cpu_points) != 31:
        raise RuntimeError("H5 parity requires 31 CPU and GPU points")
    differences: list[float] = []
    identity_matches: list[bool] = []
    for gpu_point, cpu_point in zip(gpu_points, cpu_points):
        for branch, shift_key in (
            ("maximum_ground_overlap_branch", "energy_shift_hartree"),
            ("continuously_tracked_branch", "unwrapped_energy_shift_hartree"),
        ):
            differences.append(
                abs(
                    float(gpu_point[branch][shift_key])
                    - float(cpu_point[branch][shift_key])
                )
            )
        gpu_same = abs(
            float(gpu_point["maximum_ground_overlap_branch"]["energy_shift_hartree"])
            - float(gpu_point["continuously_tracked_branch"]["unwrapped_energy_shift_hartree"])
        ) <= 1e-10
        cpu_same = abs(
            float(cpu_point["maximum_ground_overlap_branch"]["energy_shift_hartree"])
            - float(cpu_point["continuously_tracked_branch"]["unwrapped_energy_shift_hartree"])
        ) <= 1e-10
        identity_matches.append(gpu_same == cpu_same)
    return {
        "formula_key": formula_key,
        "point_count": 31,
        "maximum_absolute_direct_shift_difference_hartree": max(differences),
        "direct_shift_tolerance_hartree": 1e-9,
        "all_maximum_ground_vs_continuous_identity_relations_match": all(identity_matches),
        "pass": max(differences) <= 1e-9 and all(identity_matches),
    }


def update_h5_parity(output: Path, formula_key: str, unitary_result: dict[str, Any] | None) -> dict[str, Any]:
    path = output / "backend_parity.json"
    parity = load_json(path) if path.exists() else {
        "schema_version": "hchain_direct_gpu_h5_backend_parity_v1",
        "status": "incomplete",
    }
    raw = load_json(output / "raw" / f"H5_{formula_key}.json")
    comparison = compare_raw_to_parent(raw, formula_key)
    summary = selected_summary(raw, 5, formula_key)
    parity[formula_key] = {
        "raw_comparison": comparison,
        "summary": summary,
    }
    if unitary_result is not None:
        parity["unitary_gpu_cpu"] = unitary_result
    m5 = parity.get("m5")
    if m5 is not None:
        selected_pass = m5["summary"].get("relative_t_grid_star") == 1.35
        parity["m5"]["selected_relative_time_pass"] = selected_pass
        parity["m5"]["pass"] = bool(
            selected_pass
            and m5["raw_comparison"]["pass"]
            and parity.get("unitary_gpu_cpu", {}).get("pass", False)
        )
    y8 = parity.get("y8")
    if y8 is not None:
        disagreement = y8["summary"]["numerical"]["maximum_branch_shift_disagreement_hartree"]
        y8["known_branch_disagreement_reproduced"] = disagreement > 1e-10
        y8["pass"] = bool(
            y8["raw_comparison"]["pass"]
            and y8["known_branch_disagreement_reproduced"]
            and y8["summary"]["status"] == "not_scorable_gate_failure"
        )
    parity["overall_pass"] = bool(
        parity.get("m5", {}).get("pass", False)
        and parity.get("y8", {}).get("pass", False)
    )
    parity["status"] = "passed" if parity["overall_pass"] else "incomplete_or_failed"
    parity["updated_at_utc"] = utc_now()
    write_json(path, parity)
    return parity


def ensure_h5_parity_pass(h5_output: Path) -> None:
    path = h5_output / "backend_parity.json"
    if not path.exists() or not load_json(path).get("overall_pass"):
        raise RuntimeError("failed_backend_parity: H5 parity must pass before H7")


def _update_resource_file(output: Path, key: str, payload: dict[str, Any]) -> None:
    path = output / "resource_feasibility.json"
    current = load_json(path) if path.exists() else {
        "schema_version": "hchain_direct_gpu_h5_h7_resource_feasibility_v1",
        "cells": {},
    }
    current["cells"][key] = payload
    current["updated_at_utc"] = utc_now()
    write_json(path, current)


def run_cell(
    phase_a: Path,
    output: Path,
    h_chain: int,
    formula_key: str,
    physical_gpu: int,
    h5_output: Path | None,
) -> dict[str, Any]:
    validate_phase_a(phase_a)
    if h_chain not in SYSTEMS or formula_key not in FORMULAS:
        raise ValueError("only H5/H7 and m5/y8 are allowed")
    if h_chain == 7:
        if h5_output is None:
            raise RuntimeError("H7 requires --h5-output")
        ensure_h5_parity_pass(h5_output)
    if formula_key == "y8" and not (output / "raw" / f"H{h_chain}_m5.json").exists():
        raise RuntimeError(f"H{h_chain}/m5 must complete before H{h_chain}/y8")
    initialize_output(output, phase_a, h_chain)
    raw_root = output / "raw"
    raw_root.mkdir(exist_ok=True)
    destination = raw_root / f"H{h_chain}_{formula_key}.json"
    expected_cache_key, cache_material = cache_key(phase_a, h_chain, formula_key)
    if destination.exists():
        existing = load_json(destination)
        if (
            existing.get("status") == "complete"
            and existing.get("gpu_extension", {}).get("cache_key") == expected_cache_key
        ):
            return {"status": "reused_same_cell_complete", "path": str(destination)}
        raise RuntimeError(f"refusing to overwrite non-reusable cell: {destination}")
    runtime_root = output / ".runtime"
    runtime_root.mkdir(exist_ok=True)
    runtime = runtime_root / f"H{h_chain}_{formula_key}.json"
    if runtime.exists():
        raise RuntimeError(f"incomplete runtime preserved; choose a new output: {runtime}")
    preflight = resource_preflight(h_chain, formula_key, physical_gpu)
    if not preflight["gates"]["pass"]:
        _update_resource_file(output, f"H{h_chain}_{formula_key}", preflight)
        raise RuntimeError("not_run_resource_infeasible")

    os.environ["CUDA_VISIBLE_DEVICES"] = str(int(physical_gpu))
    preparation_started = time.perf_counter()
    system = sector_v1_1.prepare_sparse_sector_system_v1_1(h_chain)
    preparation_seconds = time.perf_counter() - preparation_started
    validate_system_identity(system, h_chain)
    label = str(FORMULAS[formula_key]["label"])
    unitary_parity: dict[str, Any] | None = None
    original_prepare = direct._prepare_sparse_sector_system
    original_build = direct._build_pf_unitary
    run_started = time.perf_counter()
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    builder: GpuSectorPFBuilder | None = None
    try:
        with GpuMemoryMonitor(physical_gpu) as monitor:
            builder = GpuSectorPFBuilder(system["group_spectra"], logical_device=0)
            if h_chain == 5 and formula_key == "m5":
                parity_time = 0.125
                sequence = _get_s2_sequence(label)
                gpu_unitary = builder.build(sequence, parity_time)
                cpu_unitary = build_sector_pf_unitary(
                    system["group_spectra"], sequence, parity_time, method="s2-cache"
                )
                difference = float(np.linalg.norm(gpu_unitary - cpu_unitary))
                unitary_parity = {
                    "formula_key": "m5",
                    "time": parity_time,
                    "frobenius_difference": difference,
                    "tolerance": 1e-10,
                    "gpu_dtype": str(gpu_unitary.dtype),
                    "cpu_dtype": str(cpu_unitary.dtype),
                    "pass": difference <= 1e-10
                    and gpu_unitary.dtype == np.complex128
                    and cpu_unitary.dtype == np.complex128,
                }
                builder.clear_metrics()
            direct._prepare_sparse_sector_system = lambda requested: system

            def gpu_build(
                passed_system: dict[str, Any],
                passed_label: str,
                evolution_time: float,
                build_method: str = "s2-cache",
            ) -> np.ndarray:
                if passed_system is not system:
                    raise RuntimeError("GPU builder received an unexpected system")
                if build_method != "s2-cache":
                    raise RuntimeError("only the fixed exact s2-cache method is allowed")
                assert builder is not None
                return builder.build(_get_s2_sequence(passed_label), evolution_time)

            direct._build_pf_unitary = gpu_build
            payload = direct.run(
                [h_chain],
                [formula_key],
                fixed_grid(),
                direct.DEFAULT_M5_TIMES,
                direct.DEFAULT_Y8_TIMES,
                5e-12,
                0.00015936001019904,
                runtime,
                "s2-cache",
            )
        monitor_summary = monitor.summary()
        builder_metrics = list(builder.metrics)
        backend_identity = builder.identity()
    finally:
        direct._prepare_sparse_sector_system = original_prepare
        direct._build_pf_unitary = original_build
        if builder is not None:
            builder.close()
    result = formula_result(payload, h_chain, formula_key)
    if len(result["points"]) != 31 or len(builder_metrics) != 31:
        raise RuntimeError("GPU direct point or metric count differs from 31")
    for point, metric in zip(result["points"], builder_metrics):
        point["gpu_backend"] = metric
    elapsed = time.perf_counter() - run_started
    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    preflight["observed"] = {
        "system_preparation_seconds": preparation_seconds,
        "cell_wall_seconds": elapsed,
        "maximum_cpu_rss_kib": int(max(rss_before, rss_after)),
        "gpu_memory_monitor": monitor_summary,
        "backend_identity": backend_identity,
    }
    preflight["observed"]["one_point_wall_seconds"] = float(
        np.mean([row["build_seconds"] for row in builder_metrics])
    )
    preflight["observed"]["31_point_gpu_build_wall_seconds"] = float(
        sum(row["build_seconds"] for row in builder_metrics)
    )
    payload["registered_protocol"] = {
        "sha256": PARENT_PROTOCOL_SHA256,
        "h_chain": h_chain,
        "formula_key": formula_key,
        "prior_direct_results_reused": False,
    }
    payload["registered_amendments"] = {
        "sector_v1_1_sha256": SECTOR_AMENDMENT_SHA256,
        "partial_v1_2_sha256": PARTIAL_AMENDMENT_SHA256,
        "gpu_h5_h7_extension_sha256": sha256(PROJECT_ROOT / EXTENSION),
    }
    payload["gpu_extension"] = {
        "cache_key": expected_cache_key,
        "cache_key_material": cache_material,
        "backend": backend_identity,
        "resource": preflight["observed"],
        "other_run_direct_cache_points_reused": 0,
        "other_cell_direct_cache_points_reused": 0,
        "parent_cpu_raw_used_as_cache": False,
        "completed_at_utc": utc_now(),
    }
    write_json(destination, payload)
    runtime.unlink()
    _update_resource_file(output, f"H{h_chain}_{formula_key}", preflight)
    if h_chain == 5:
        parity = update_h5_parity(output, formula_key, unitary_parity)
        if formula_key == "m5" and not parity.get("m5", {}).get("pass"):
            raise RuntimeError("failed_backend_parity")
        if formula_key == "y8" and not parity.get("overall_pass"):
            raise RuntimeError("failed_backend_parity")
    return {
        "status": "complete",
        "path": str(destination),
        "wall_seconds": elapsed,
        "summary": selected_summary(payload, h_chain, formula_key),
    }


def _scoring_rows(outputs: dict[int, Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for h_chain, output in sorted(outputs.items()):
        for formula_key in ("m5", "y8"):
            raw = load_json(output / "raw" / f"H{h_chain}_{formula_key}.json")
            summary = selected_summary(raw, h_chain, formula_key)
            numerical = summary.get("numerical", {})
            rows.append(
                {
                    "system": f"H{h_chain}",
                    "family": "odd_cation_triplet",
                    "formula_key": formula_key,
                    "status": summary.get("status"),
                    "direct_point_count": summary.get("point_count"),
                    "t_ana": summary.get("analytic_optimal_time"),
                    "t_grid_star": summary.get("t_grid_star"),
                    "relative_t_grid_star": summary.get("relative_t_grid_star"),
                    "selected_direct_error_hartree": summary.get("direct_error_at_t_grid_star_hartree"),
                    "minimum_cost": summary.get("minimum_direct_cost"),
                    "cost_ratio_vs_nearest_t_ana": summary.get("direct_to_analytic_time_cost_ratio"),
                    "near_optimal_relative_width": summary.get("near_optimal_component", {}).get("relative_time_width"),
                    "well_localized": summary.get("near_optimal_component", {}).get("well_localized"),
                    "maximum_unitarity_residual": numerical.get("maximum_unitarity_frobenius_residual"),
                    "maximum_schur_residual": numerical.get("maximum_schur_off_diagonal_frobenius_residual"),
                    "maximum_branch_shift_disagreement_hartree": numerical.get("maximum_branch_shift_disagreement_hartree"),
                    "minimum_ground_overlap": numerical.get("minimum_ground_overlap"),
                    "gate_results": json.dumps(summary.get("gate_results", {}), sort_keys=True),
                    "neighbor_bracket": json.dumps(summary.get("neighbor_bracket", {}), sort_keys=True),
                    "sign_change_intervals": json.dumps(summary.get("signed_error_zero_crossing_intervals", []), sort_keys=True),
                }
            )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze_outputs(
    phase_a: Path,
    h5_output: Path,
    h7_output: Path | None,
    full_test_log: Path | None,
) -> dict[str, Any]:
    validate_phase_a(phase_a)
    outputs = {5: h5_output}
    if h7_output is not None:
        outputs[7] = h7_output
    for h_chain, output in outputs.items():
        initialize_output(output, phase_a, h_chain)
        for formula_key in ("m5", "y8"):
            if not (output / "raw" / f"H{h_chain}_{formula_key}.json").exists():
                raise RuntimeError(f"missing completed cell H{h_chain}/{formula_key}")
    parity = load_json(h5_output / "backend_parity.json")
    if not parity.get("overall_pass"):
        raise RuntimeError("failed_backend_parity")
    rows = _scoring_rows(outputs)
    scaling = {
        "schema_version": "hchain_direct_gpu_h5_h7_scaling_v1",
        "odd_cation_triplet": {
            "available_sizes": [5] if h7_output is None else [5, 7],
            "required_sizes_for_registered_exploratory_fit": [5, 7, 9],
            "m5": {"fit_performed": False, "reason": "H9 is outside the user-limited scope"},
            "y8": {"fit_performed": False, "reason": "H9 is outside scope and H5/Y8 fails the unchanged branch gate"},
        },
        "H8_holdout": {"performed": False, "reason": "H8 is outside the user-limited scope"},
    }
    status = (
        "complete_H5_H7_interim_scope"
        if h7_output is not None
        else "complete_H5_before_H7"
    )
    maximums = {
        "unitarity": max(float(row["maximum_unitarity_residual"]) for row in rows),
        "schur": max(float(row["maximum_schur_residual"]) for row in rows),
        "branch": max(float(row["maximum_branch_shift_disagreement_hartree"]) for row in rows),
    }
    minimum_overlap = min(float(row["minimum_ground_overlap"]) for row in rows)
    audit = {
        "schema_version": "hchain_direct_gpu_h5_h7_audit_v1",
        "status": status,
        "created_at_utc": utc_now(),
        "git_head": git_value("rev-parse", "HEAD"),
        "git_branch": git_value("branch", "--show-current"),
        "phase_a_marker_sha256": sha256(phase_a / "PHASE_A_FROZEN"),
        "protocol_sha256": PARENT_PROTOCOL_SHA256,
        "sector_amendment_sha256": SECTOR_AMENDMENT_SHA256,
        "partial_stop_amendment_sha256": PARTIAL_AMENDMENT_SHA256,
        "gpu_extension_sha256": sha256(PROJECT_ROOT / EXTENSION),
        "prediction_sha256": sha256(phase_a / "predictions.json"),
        "environment": package_identity(),
        "H5_backend_parity": parity,
        "direct_point_count": sum(int(row["direct_point_count"]) for row in rows),
        "short_time_fit_point_count": sum(len(FORMULAS[row["formula_key"]]["fit_times"]) for row in rows),
        "maximum_unitarity_frobenius_residual": maximums["unitarity"],
        "maximum_schur_off_diagonal_frobenius_residual": maximums["schur"],
        "maximum_branch_shift_disagreement_hartree": maximums["branch"],
        "minimum_ground_overlap": minimum_overlap,
        "H8_H9": "not_run_or_estimated_by_user_scope",
    }
    report_lines = [
        "# H-chain exact GPU direct optimum: H5/H7 interim report",
        "",
        f"- Status: `{status}`",
        f"- Branch: `{audit['git_branch']}`",
        f"- H5 backend parity: `{'passed' if parity['overall_pass'] else 'failed'}`",
        "- H8/H9: not run or estimated in this user-limited execution.",
        "- Odd-family scaling: not fit; the registered exploratory fit requires H5/H7/H9.",
        "",
        "| system | PF | status | points | t_ana | t_grid* | t_grid*/t_ana | cost ratio vs t_ana | max branch difference (Ha) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        report_lines.append(
            f"| {row['system']} | {row['formula_key']} | {row['status']} | "
            f"{row['direct_point_count']} | {float(row['t_ana']):.12g} | "
            f"{float(row['t_grid_star']):.12g} | {float(row['relative_t_grid_star']):.6g} | "
            f"{float(row['cost_ratio_vs_nearest_t_ana']):.12g} | "
            f"{float(row['maximum_branch_shift_disagreement_hartree']):.12g} |"
        )
    report_lines.extend(
        [
            "",
            "The reported optimum is the minimum on the fixed discrete grid; it is not claimed as a continuous optimum.",
            "The H5/Y8 value is retained as a failed-gate artifact and is not used scientifically.",
        ]
    )
    for output in outputs.values():
        _write_csv(output / "scoring.csv", rows)
        write_json(output / "scaling.json", scaling)
        write_json(output / "audit.json", audit)
        (output / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
        if full_test_log is not None:
            shutil.copyfile(full_test_log, output / "all_review_tests.log")
        if h7_output is not None:
            (output / "COMPLETE_H5_H7").write_text(status + "\n", encoding="utf-8")
        public = sorted(
            path
            for path in output.rglob("*")
            if path.is_file()
            and ".runtime" not in path.parts
            and path.name != "manifest.json"
        )
        parent._manifest(
            output,
            public,
            {
                "schema_version": "hchain_direct_gpu_h5_h7_manifest_v1",
                "status": status,
                "created_at_utc": utc_now(),
            },
        )
    return {"status": status, "rows": rows, "audit": audit, "scaling": scaling}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze-phase-a")
    freeze.add_argument("--output", type=Path, required=True)
    freeze.add_argument("--gpu", type=int, default=1)
    cell = subparsers.add_parser("run-cell")
    cell.add_argument("--phase-a", type=Path, required=True)
    cell.add_argument("--output", type=Path, required=True)
    cell.add_argument("--system", type=int, choices=[5, 7], required=True)
    cell.add_argument("--formula", choices=["m5", "y8"], required=True)
    cell.add_argument("--gpu", type=int, default=1)
    cell.add_argument("--h5-output", type=Path)
    tests = subparsers.add_parser("run-tests")
    tests.add_argument("--kind", choices=["focused", "all"], required=True)
    tests.add_argument("--log", type=Path, required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--phase-a", type=Path, required=True)
    analyze.add_argument("--h5-output", type=Path, required=True)
    analyze.add_argument("--h7-output", type=Path)
    analyze.add_argument("--full-test-log", type=Path)
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def main() -> None:
    args = parse_args()
    if args.command == "freeze-phase-a":
        freeze_phase_a(resolved(args.output), args.gpu)
        result: Any = {"status": "phase_a_frozen", "output": str(resolved(args.output))}
    elif args.command == "run-cell":
        result = run_cell(
            resolved(args.phase_a),
            resolved(args.output),
            args.system,
            args.formula,
            args.gpu,
            resolved(args.h5_output) if args.h5_output else None,
        )
    elif args.command == "run-tests":
        result = execute_tests(args.kind, resolved(args.log))
    elif args.command == "analyze":
        result = analyze_outputs(
            resolved(args.phase_a),
            resolved(args.h5_output),
            resolved(args.h7_output) if args.h7_output else None,
            resolved(args.full_test_log) if args.full_test_log else None,
        )
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
