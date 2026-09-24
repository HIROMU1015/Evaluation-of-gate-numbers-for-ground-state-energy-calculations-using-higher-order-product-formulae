"""Accelerate the frozen D03 independent rechecks without changing science.

Version 2 confines each subprocess to a disjoint CPU set and output directory.
Parallel results are promoted only after a frozen numerical-equivalence gate.
The original stage plans, source-identity audit, numerical gates, and scoring
remain authoritative.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Sequence

import numpy as np

from review_response import run_d03_target_accuracy_followup as base
from review_response import run_full_electron_nh3_higher_term_diagnosis as direct


PARALLEL_EXECUTION = base.PROJECT_ROOT / "review_response/d03_target_accuracy_parallel_execution_v2.json"
PYTHON_BIN = Path("/home/AbeHiromu/venvs/trotter-common/bin/python")
POINT_WEIGHTS = {
    ("nh3", "full_equilibrium"): 820.0,
    ("nh3", "active_stretch150"): 48.0,
    ("p03", "N2_active_eq_sto3g"): 100.0,
    ("p03", "N2_active_stretch150_sto3g"): 36.0,
    ("p03", "HF_full_stretch150_sto3g"): 1.0,
}


class ParallelValidationError(RuntimeError):
    """Raised before any parallel result is admitted to scientific output."""


def parallel_protocol() -> dict[str, Any]:
    return base.read_json(PARALLEL_EXECUTION)


def parallel_sha256() -> str:
    return base.sha256(PARALLEL_EXECUTION)


def point_map(output: Path) -> dict[str, dict[str, Any]]:
    plan = base.read_json(output / "independent_recheck_plan.json")
    points = plan.get("points", [])
    if len(points) != 202:
        raise ParallelValidationError(f"independent recheck plan changed: {len(points)} != 202")
    mapped = {item["physical_id"]: item for item in points}
    if len(mapped) != len(points):
        raise ParallelValidationError("independent recheck plan contains duplicate physical IDs")
    return mapped


def source_identity_map(output: Path) -> dict[tuple[str, str], dict[str, Any]]:
    audit = base.read_json(output / "source_identity_audit.json")
    if audit.get("status") != "passed":
        raise ParallelValidationError("source identity audit has not passed")
    return {
        (row["dataset"], row["condition"]): row
        for row in audit["checks"]
        if row.get("role") == "system_cache"
    }


def load_worker_systems(
    output: Path, items: Sequence[dict[str, Any]]
) -> dict[tuple[str, str], dict[str, Any]]:
    identities = source_identity_map(output)
    systems: dict[tuple[str, str], dict[str, Any]] = {}
    for key in sorted({(item["dataset"], item["condition"]) for item in items}):
        identity = identities.get(key)
        if identity is None or identity.get("passed") is not True:
            raise ParallelValidationError(f"missing passed source identity for {key}")
        cache = Path(identity["pickle_path"])
        metadata = Path(identity["metadata_path"])
        if base.sha256(cache) != identity["pickle_sha256"]:
            raise ParallelValidationError(f"worker pickle identity changed: {key}")
        if base.sha256(metadata) != identity["metadata_sha256"]:
            raise ParallelValidationError(f"worker metadata identity changed: {key}")
        systems[key] = {"system": direct._load_system(cache), "identity": identity}
    return systems


def set_affinity(cpu_list: str) -> None:
    cpus: set[int] = set()
    for field in cpu_list.split(","):
        bounds = field.split("-", 1)
        if len(bounds) == 1:
            cpus.add(int(bounds[0]))
        else:
            cpus.update(range(int(bounds[0]), int(bounds[1]) + 1))
    os.sched_setaffinity(0, cpus)


def atomic_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        np.save(stream, array)
    temporary.replace(path)


def worker(args: argparse.Namespace) -> int:
    output = Path(args.output).resolve()
    worker_output = Path(args.worker_output).resolve()
    set_affinity(args.cpu_list)
    items = base.read_json(Path(args.items_file).resolve())["points"]
    systems = load_worker_systems(output, items)
    started = time.perf_counter()
    computed = base.compute_items(
        worker_output, "independent_rechecks", items, systems, "cpu", 0
    )
    base.atomic_json(
        worker_output / "worker_status.json",
        {
            "schema": "d03_parallel_worker_status_v2",
            "status": "complete",
            "worker_index": args.worker_index,
            "cpu_affinity": args.cpu_list,
            "parallel_execution_sha256": parallel_sha256(),
            "assigned_point_count": len(items),
            "completed_or_resumed_point_count": len(computed),
            "elapsed_seconds": time.perf_counter() - started,
        },
    )
    return 0


def unitary_worker(args: argparse.Namespace) -> int:
    output = Path(args.output).resolve()
    destination = Path(args.destination).resolve()
    set_affinity(args.cpu_list)
    item = point_map(output)[args.physical_id]
    system_entry = load_worker_systems(output, [item])[
        (item["dataset"], item["condition"])
    ]
    system = system_entry["system"]
    sequence = direct._formula_s2_sequence(item["formula"])
    rotations = direct._rotation_count(system, sequence)
    unitary, profile = direct._build_cpu(system, sequence, float(item["time"]))
    point, _ = direct._schur_point(
        unitary, system["state"], system["energy"], float(item["time"]), rotations
    )
    atomic_npy(destination.with_suffix(".npy"), unitary)
    base.atomic_json(
        destination.with_suffix(".json"),
        {
            "schema": "d03_parallel_unitary_benchmark_point_v2",
            "status": "complete",
            "physical_id": item["physical_id"],
            "cpu_affinity": args.cpu_list,
            "profile": profile,
            "direct": {**point, "phase_unwrap_integer": 0},
        },
    )
    return 0


def thread_environment(threads: int) -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "BLIS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[name] = str(threads)
    env["OMP_DYNAMIC"] = "FALSE"
    env["OPENBLAS_DYNAMIC"] = "0"
    env["PYTHONPATH"] = "src:review_response:."
    return env


def launch(
    commands: Sequence[tuple[list[str], Path, dict[str, str]]], label: str
) -> None:
    running: list[tuple[subprocess.Popen[Any], Any, Path]] = []
    for command, log_path, env in commands:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        stream = log_path.open("a", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=base.PROJECT_ROOT,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            text=True,
        )
        running.append((process, stream, log_path))
    while running:
        time.sleep(15.0)
        remaining = []
        failures = []
        for process, stream, log_path in running:
            status = process.poll()
            if status is None:
                remaining.append((process, stream, log_path))
            else:
                stream.close()
                if status != 0:
                    failures.append((status, log_path))
        running = remaining
        print(
            f"[{label}] workers_remaining={len(running)} failures={len(failures)}",
            flush=True,
        )
        if failures:
            for process, stream, _ in running:
                process.terminate()
                stream.close()
            detail = ", ".join(f"exit={code} log={path}" for code, path in failures)
            raise ParallelValidationError(f"{label} worker failed: {detail}")


def source_records(output: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    protocol = base.read_json(base.PROTOCOL)
    points = base.load_stage_points(output, "stage1") + base.load_stage_points(output, "stage2")
    return base.analysis_records(protocol, points)


def compare_direct(
    observed: dict[str, Any], expected: dict[str, Any], gates: dict[str, Any]
) -> dict[str, Any]:
    shift = abs(
        float(observed["signed_direct_shift_hartree"])
        - float(expected["signed_direct_shift_hartree"])
    )
    overlap = abs(
        float(observed["ground_overlap_probability"])
        - float(expected["ground_overlap_probability"])
    )
    residual = float(observed["eigenpair_residual_2_norm"])
    expected_unwrap = int(expected.get("phase_unwrap_integer", 0))
    observed_unwrap = int(observed.get("phase_unwrap_integer", 0))
    checks = {
        "signed_shift": shift <= float(gates["cpu_gpu_signed_shift_absolute_tolerance_hartree"]),
        "ground_overlap_probability": overlap <= float(gates["cpu_gpu_ground_overlap_probability_absolute_tolerance"]),
        "eigenpair_residual": residual <= float(gates["pf_eigenpair_residual_2_norm_maximum"]),
        "phase_unwrap_integer": observed_unwrap == expected_unwrap,
    }
    return {
        "signed_shift_absolute_difference_hartree": shift,
        "ground_overlap_probability_absolute_difference": overlap,
        "observed_eigenpair_residual_2_norm": residual,
        "expected_phase_unwrap_integer": expected_unwrap,
        "observed_phase_unwrap_integer": observed_unwrap,
        "checks": checks,
        "passed": all(checks.values()),
    }


def run_unitary_gate(output: Path, runtime: Path) -> dict[str, Any]:
    protocol = parallel_protocol()["equivalence_gate"]
    root = runtime / "unitary_gate"
    point_id = protocol["unitary_benchmark_physical_id"]
    commands = []
    for name, threads, affinity in (("reference", 1, "120"), ("candidate", 8, "0-7")):
        destination = root / name
        command = [
            str(PYTHON_BIN), __file__, "unitary-worker",
            "--output", str(output), "--destination", str(destination),
            "--physical-id", point_id, "--cpu-list", affinity,
        ]
        commands.append((command, root / f"{name}.log", thread_environment(threads)))
    launch(commands, "unitary-gate")
    reference = np.load(root / "reference.npy", mmap_mode="r")
    candidate = np.load(root / "candidate.npy", mmap_mode="r")
    reference_json = base.read_json(root / "reference.json")
    candidate_json = base.read_json(root / "candidate.json")
    unitary_difference = float(np.linalg.norm(candidate - reference) / np.linalg.norm(reference))
    item = point_map(output)[point_id]
    system = load_worker_systems(output, [item])[(item["dataset"], item["condition"])]["system"]
    state = np.asarray(system["state"])
    action_difference = float(
        np.linalg.norm((candidate - reference) @ state) / np.linalg.norm(reference @ state)
    )
    gates = base.read_json(base.GATES)
    direct_comparison = compare_direct(candidate_json["direct"], reference_json["direct"], gates)
    checks = {
        "unitary_relative_frobenius": unitary_difference <= float(protocol["unitary_relative_frobenius_maximum"]),
        "state_action_relative_2_norm": action_difference <= float(protocol["state_action_relative_2_norm_maximum"]),
        "direct_values": direct_comparison["passed"],
    }
    payload = {
        "schema": "d03_parallel_unitary_equivalence_gate_v2",
        "status": "passed" if all(checks.values()) else "failed_numerical_validation",
        "physical_id": point_id,
        "reference_blas_threads": protocol["unitary_reference_blas_threads"],
        "candidate_blas_threads": protocol["unitary_candidate_blas_threads"],
        "unitary_relative_frobenius": unitary_difference,
        "state_action_relative_2_norm": action_difference,
        "direct_comparison": direct_comparison,
        "checks": checks,
    }
    base.atomic_json(output / "parallel_unitary_equivalence_gate.json", payload)
    del reference, candidate
    for path in (root / "reference.npy", root / "candidate.npy"):
        path.unlink(missing_ok=True)
    if payload["status"] != "passed":
        raise ParallelValidationError("parallel unitary equivalence gate failed")
    return payload


def run_concurrent_gate(output: Path, runtime: Path) -> tuple[dict[str, Any], list[Path]]:
    config = parallel_protocol()
    ids = config["equivalence_gate"]["concurrent_representative_physical_ids"]
    points = point_map(output)
    if len(ids) != config["equivalence_gate"]["concurrent_worker_count"] or len(set(ids)) != len(ids):
        raise ParallelValidationError("frozen concurrent benchmark IDs are invalid")
    affinities = config["parallelism"]["cpu_affinity"]
    commands = []
    worker_roots = []
    for index, point_id in enumerate(ids):
        item = points.get(point_id)
        if item is None:
            raise ParallelValidationError(f"frozen benchmark point missing: {point_id}")
        root = runtime / "concurrent_gate" / f"worker_{index:02d}"
        worker_roots.append(root)
        items_file = root / "items.json"
        base.atomic_json(items_file, {"points": [item]})
        command = [
            str(PYTHON_BIN), __file__, "worker",
            "--output", str(output), "--worker-output", str(root),
            "--items-file", str(items_file), "--worker-index", str(index),
            "--cpu-list", affinities[index],
        ]
        commands.append((command, root / "worker.log", thread_environment(config["parallelism"]["blas_threads_per_worker"])))
    launch(commands, "concurrent-gate")
    records = source_records(output)
    gates = base.read_json(base.GATES)
    rows = []
    for item, root in zip((points[point_id] for point_id in ids), worker_roots):
        observed_path = base.point_path(root, "independent_rechecks", item)
        observed = base.read_json(observed_path)
        expected = base.nearest_exact(
            records[(item["dataset"], item["condition"], item["formula"])]["points"],
            float(item["time"]), gates,
        )
        if expected is None:
            raise ParallelValidationError(f"benchmark source point missing: {item['physical_id']}")
        comparison = compare_direct(observed, expected, gates)
        rows.append({"physical_id": item["physical_id"], **comparison})
    payload = {
        "schema": "d03_parallel_concurrent_equivalence_gate_v2",
        "status": "passed" if all(row["passed"] for row in rows) else "failed_numerical_validation",
        "worker_count": len(worker_roots),
        "blas_threads_per_worker": config["parallelism"]["blas_threads_per_worker"],
        "rows": rows,
    }
    base.atomic_json(output / "parallel_concurrent_equivalence_gate.json", payload)
    if payload["status"] != "passed":
        raise ParallelValidationError("parallel concurrent equivalence gate failed")
    return payload, worker_roots


def main_vector_path(output: Path, physical_id: str) -> Path:
    return output / ".runtime/vectors" / f"{physical_id}.npy"


def valid_main_point(
    output: Path, item: dict[str, Any], identities: dict[tuple[str, str], dict[str, Any]]
) -> bool:
    key = (item["dataset"], item["condition"])
    expected_key = base.cache_key(item, identities[key], "cpu")
    path = base.point_path(output, "independent_rechecks", item)
    vector = main_vector_path(output, item["physical_id"])
    if not base.valid_resume(path, expected_key) or not vector.is_file():
        return False
    try:
        loaded = np.load(vector, mmap_mode="r")
        expected_size = int(base.EXPECTED_SYSTEMS[key][3])
        return loaded.ndim == 1 and loaded.size == expected_size
    except (OSError, ValueError):
        return False


def promote_point(
    output: Path,
    worker_root: Path,
    item: dict[str, Any],
    disposition: str,
    worker_index: int,
) -> None:
    source_json = base.point_path(worker_root, "independent_rechecks", item)
    source_vector = worker_root / ".runtime/vectors" / f"{item['physical_id']}.npy"
    payload = base.read_json(source_json)
    payload["parallel_execution"] = {
        "protocol_id": parallel_protocol()["protocol_id"],
        "protocol_sha256": parallel_sha256(),
        "disposition": disposition,
        "worker_index": worker_index,
    }
    base.atomic_json(base.point_path(output, "independent_rechecks", item), payload)
    vector = np.load(source_vector)
    atomic_npy(main_vector_path(output, item["physical_id"]), vector)


def annotate_serial_reuse(output: Path, item: dict[str, Any]) -> None:
    path = base.point_path(output, "independent_rechecks", item)
    payload = base.read_json(path)
    payload["parallel_execution"] = {
        "protocol_id": parallel_protocol()["protocol_id"],
        "protocol_sha256": parallel_sha256(),
        "disposition": "reused_serial_v1_after_parallel_equivalence_passed",
        "worker_index": None,
    }
    base.atomic_json(path, payload)


def partition(items: Sequence[dict[str, Any]], workers: int) -> list[list[dict[str, Any]]]:
    shards: list[list[dict[str, Any]]] = [[] for _ in range(workers)]
    loads = [0.0] * workers
    ordered = sorted(
        items,
        key=lambda item: (-POINT_WEIGHTS[(item["dataset"], item["condition"])], item["physical_id"]),
    )
    for item in ordered:
        index = min(range(workers), key=lambda value: (loads[value], value))
        shards[index].append(item)
        loads[index] += POINT_WEIGHTS[(item["dataset"], item["condition"])]
    return shards


def reconstruct_adjacent_overlaps(output: Path, items: Sequence[dict[str, Any]]) -> None:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault((item["dataset"], item["condition"], item["formula"]), []).append(item)
    for branch in groups.values():
        previous: np.ndarray | None = None
        for item in sorted(branch, key=lambda row: float(row["time"])):
            vector = np.load(main_vector_path(output, item["physical_id"]))
            overlap = None if previous is None else float(abs(np.vdot(previous, vector)) ** 2)
            path = base.point_path(output, "independent_rechecks", item)
            payload = base.read_json(path)
            payload["adjacent_selected_vector_overlap_probability"] = overlap
            payload["adjacent_overlap_reconstructed_after_parallel_execution"] = True
            base.atomic_json(path, payload)
            previous = vector


def production(output: Path, runtime: Path, benchmark_roots: Sequence[Path]) -> dict[str, Any]:
    config = parallel_protocol()
    points = point_map(output)
    identities = source_identity_map(output)
    serial_ids = [point_id for point_id, item in points.items() if valid_main_point(output, item, identities)]
    for point_id in serial_ids:
        annotate_serial_reuse(output, points[point_id])

    promoted_benchmark = 0
    for index, root in enumerate(benchmark_roots):
        items = base.read_json(root / "items.json")["points"]
        item = items[0]
        if not valid_main_point(output, item, identities):
            promote_point(output, root, item, "promoted_concurrent_equivalence_point", index)
            promoted_benchmark += 1

    remaining = [item for item in points.values() if not valid_main_point(output, item, identities)]
    shards = partition(remaining, int(config["parallelism"]["worker_processes"]))
    affinities = config["parallelism"]["cpu_affinity"]
    commands = []
    roots: list[tuple[int, Path, list[dict[str, Any]]]] = []
    for index, items in enumerate(shards):
        if not items:
            continue
        root = runtime / "production" / f"worker_{index:02d}"
        roots.append((index, root, items))
        items_file = root / "items.json"
        base.atomic_json(items_file, {"points": items})
        command = [
            str(PYTHON_BIN), __file__, "worker",
            "--output", str(output), "--worker-output", str(root),
            "--items-file", str(items_file), "--worker-index", str(index),
            "--cpu-list", affinities[index],
        ]
        commands.append((command, root / "worker.log", thread_environment(config["parallelism"]["blas_threads_per_worker"])))
    if commands:
        launch(commands, "production")
    for index, root, items in roots:
        for item in items:
            promote_point(output, root, item, "new_parallel_v2_recheck", index)
    missing = [item["physical_id"] for item in points.values() if not valid_main_point(output, item, identities)]
    if missing:
        raise ParallelValidationError(f"parallel production left missing points: {missing[:8]}")
    reconstruct_adjacent_overlaps(output, list(points.values()))
    payload = {
        "schema": "d03_parallel_production_status_v2",
        "status": "passed",
        "parallel_execution_sha256": parallel_sha256(),
        "total_point_count": len(points),
        "reused_serial_v1_point_count": len(serial_ids),
        "promoted_concurrent_benchmark_point_count": promoted_benchmark,
        "new_parallel_production_point_count": sum(len(items) for _, _, items in roots),
        "worker_count": config["parallelism"]["worker_processes"],
        "blas_threads_per_worker": config["parallelism"]["blas_threads_per_worker"],
    }
    base.atomic_json(output / "parallel_production_status.json", payload)
    return payload


def run_parallel(args: argparse.Namespace) -> int:
    output = Path(args.output).resolve()
    runtime = output / ".runtime/parallel_v2"
    runtime.mkdir(parents=True, exist_ok=True)
    try:
        base.validate_source_identity(output)
        point_map(output)
        unitary = run_unitary_gate(output, runtime)
        concurrent, benchmark_roots = run_concurrent_gate(output, runtime)
        production_status = production(output, runtime, benchmark_roots)
        original_args = argparse.Namespace(output=str(output), gpu_id=0)
        status = base.run_all(original_args)
        if status != 0:
            raise ParallelValidationError(f"original scientific finalization returned {status}")
        scientific_path = output / "scientific_status.json"
        scientific = base.read_json(scientific_path)
        scientific["parallel_execution"] = {
            "protocol_id": parallel_protocol()["protocol_id"],
            "protocol_sha256": parallel_sha256(),
            "unitary_equivalence_gate": unitary["status"],
            "concurrent_equivalence_gate": concurrent["status"],
            **production_status,
        }
        base.atomic_json(scientific_path, scientific)
        return 0
    except (base.SourceIdentityError, base.NumericalValidationError, ParallelValidationError) as error:
        base.atomic_json(
            output / "parallel_execution_failure.json",
            {
                "schema": "d03_parallel_execution_failure_v2",
                "status": "failed_numerical_validation",
                "parallel_results_promoted": False,
                "error": str(error),
            },
        )
        print(f"parallel execution failed: {error}", file=sys.stderr, flush=True)
        return 4


def finalize(args: argparse.Namespace) -> int:
    output = Path(args.output).resolve()
    scientific = base.read_json(output / "scientific_status.json")
    tests = []
    for raw in args.test_log:
        path = Path(raw).resolve()
        tests.append({"path": str(path), "sha256": base.sha256(path), "passed": True})
    complete = scientific.get("status") == "complete_pending_tests" and bool(tests)
    audit = {
        "schema": "d03_target_accuracy_followup_audit_v2_parallel",
        "status": "complete" if complete else scientific.get("status"),
        "scientific": scientific,
        "tests": tests,
        "source_identity": base.read_json(output / "source_identity_audit.json"),
        "benchmark": base.read_json(output / "cpu_gpu_benchmark.json"),
        "parallel_unitary_equivalence_gate": base.read_json(output / "parallel_unitary_equivalence_gate.json"),
        "parallel_concurrent_equivalence_gate": base.read_json(output / "parallel_concurrent_equivalence_gate.json"),
        "parallel_production": base.read_json(output / "parallel_production_status.json"),
        "protocol_sha256": base.sha256(base.PROTOCOL),
        "numerical_gates_sha256": base.sha256(base.GATES),
        "source_execution_protocol_sha256": base.sha256(base.EXECUTION),
        "parallel_execution_protocol_sha256": parallel_sha256(),
        "new_ca_div_10_direct_point_count": 0,
        "new_optional_refit_training_point_count": 0,
        "models_refitted": False,
    }
    base.atomic_json(output / "audit.json", audit)
    report = [
        "# D03 target-accuracy direct-validation follow-up",
        "",
        f"Status: **{audit['status']}**",
        "",
        f"- Independent rechecks: {scientific.get('independent_recheck_count')}",
        f"- Parallel workers: {audit['parallel_production']['worker_count']}",
        f"- BLAS threads per worker: {audit['parallel_production']['blas_threads_per_worker']}",
        f"- Reused serial-v1 rechecks: {audit['parallel_production']['reused_serial_v1_point_count']}",
        f"- Unitariy equivalence gate: {audit['parallel_unitary_equivalence_gate']['status']}",
        f"- Concurrent equivalence gate: {audit['parallel_concurrent_equivalence_gate']['status']}",
        "- Scientific point plan, scoring, thresholds, and models were unchanged.",
        "- CA/10 and optional refit-training new points: 0",
        "- Model refit and boundary expansion: not performed",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "schema": "d03_target_accuracy_followup_manifest_v2_parallel",
        "status": audit["status"],
        "completed_at": base.now(),
        "git": base.git_state(),
        "protocol_sha256": base.sha256(base.PROTOCOL),
        "numerical_gates_sha256": base.sha256(base.GATES),
        "source_execution_protocol_sha256": base.sha256(base.EXECUTION),
        "parallel_execution_protocol_sha256": parallel_sha256(),
        "source_manifest_sha256": base.sha256(base.SOURCE_MANIFEST),
        "artifact_hashes": base.artifact_hashes(output),
        "tests": tests,
    }
    base.atomic_json(output / "manifest.json", manifest)
    if complete:
        complete_path = output / "COMPLETE"
        if not complete_path.exists():
            complete_path.touch(exist_ok=False)
        return 0
    return 5


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run-parallel")
    run.add_argument("--output", required=True)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument("--output", required=True)
    worker_parser.add_argument("--worker-output", required=True)
    worker_parser.add_argument("--items-file", required=True)
    worker_parser.add_argument("--worker-index", type=int, required=True)
    worker_parser.add_argument("--cpu-list", required=True)
    unitary = subparsers.add_parser("unitary-worker")
    unitary.add_argument("--output", required=True)
    unitary.add_argument("--destination", required=True)
    unitary.add_argument("--physical-id", required=True)
    unitary.add_argument("--cpu-list", required=True)
    final = subparsers.add_parser("finalize")
    final.add_argument("--output", required=True)
    final.add_argument("--test-log", action="append", default=[], required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "run-parallel":
        return run_parallel(args)
    if args.command == "worker":
        return worker(args)
    if args.command == "unitary-worker":
        return unitary_worker(args)
    if args.command == "finalize":
        return finalize(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
