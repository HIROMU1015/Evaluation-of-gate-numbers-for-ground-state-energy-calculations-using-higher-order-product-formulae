from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from review_response import run_d03_target_accuracy_parallel_rechecks as parallel


def test_parallel_protocol_uses_all_server_cores_without_oversubscription() -> None:
    protocol = parallel.parallel_protocol()
    execution = protocol["parallelism"]
    assert protocol["frozen_before_parallel_direct_computation"] is True
    assert protocol["scientific_protocol_is_unchanged"] is True
    assert protocol["numerical_gates_are_unchanged"] is True
    assert execution["worker_processes"] == 16
    assert execution["blas_threads_per_worker"] == 8
    assert execution["worker_processes"] * execution["blas_threads_per_worker"] == 128
    cpus = set()
    for field in execution["cpu_affinity"]:
        start, stop = map(int, field.split("-"))
        group = set(range(start, stop + 1))
        assert not cpus.intersection(group)
        cpus.update(group)
    assert cpus == set(range(128))


def test_equivalence_gate_is_frozen_and_covers_every_group() -> None:
    protocol = parallel.parallel_protocol()
    gate = protocol["equivalence_gate"]
    assert gate["required_before_parallel_results_are_promoted"] is True
    assert gate["failure_action"] == "reject_all_parallel_results_and_leave_run_incomplete"
    assert len(gate["concurrent_representative_physical_ids"]) == 16
    assert len(set(gate["concurrent_representative_physical_ids"])) == 16
    assert gate["unitary_relative_frobenius_maximum"] == 1e-10
    assert gate["state_action_relative_2_norm_maximum"] == 1e-10
    assert gate["signed_shift_absolute_tolerance_hartree"] == 1e-10
    assert gate["ground_overlap_probability_absolute_tolerance"] == 1e-6
    assert gate["eigenpair_residual_2_norm_maximum"] == 1e-8


def test_partition_is_deterministic_and_complete() -> None:
    items = [
        {"physical_id": "a", "dataset": "nh3", "condition": "full_equilibrium"},
        {"physical_id": "b", "dataset": "nh3", "condition": "active_stretch150"},
        {"physical_id": "c", "dataset": "p03", "condition": "HF_full_stretch150_sto3g"},
    ]
    first = parallel.partition(items, 2)
    second = parallel.partition(list(reversed(items)), 2)
    assert first == second
    assert sorted(item["physical_id"] for shard in first for item in shard) == ["a", "b", "c"]


def test_direct_comparison_uses_frozen_numerical_gates() -> None:
    gates = {
        "cpu_gpu_signed_shift_absolute_tolerance_hartree": 1e-10,
        "cpu_gpu_ground_overlap_probability_absolute_tolerance": 1e-6,
        "pf_eigenpair_residual_2_norm_maximum": 1e-8,
    }
    expected = {
        "signed_direct_shift_hartree": 0.1,
        "ground_overlap_probability": 0.9,
        "phase_unwrap_integer": 0,
    }
    observed = {
        "signed_direct_shift_hartree": 0.1 + 0.5e-10,
        "ground_overlap_probability": 0.9 + 0.5e-6,
        "eigenpair_residual_2_norm": 0.5e-8,
        "phase_unwrap_integer": 0,
    }
    assert parallel.compare_direct(observed, expected, gates)["passed"] is True
    observed["phase_unwrap_integer"] = 1
    assert parallel.compare_direct(observed, expected, gates)["passed"] is False


def test_valid_main_point_requires_a_loadable_vector(tmp_path: Path) -> None:
    item = {
        "physical_id": "point",
        "dataset": "p03",
        "condition": "HF_full_stretch150_sto3g",
        "formula": "current_m3",
        "time": 0.25,
    }
    identity = {"hamiltonian_identity_sha256": "ham"}
    identities = {(item["dataset"], item["condition"]): identity}
    expected_key = parallel.base.cache_key(item, identity, "cpu")
    point_path = parallel.base.point_path(tmp_path, "independent_rechecks", item)
    point_path.parent.mkdir(parents=True)
    required = {field: 0 for field in parallel.base.REQUIRED_POINT_FIELDS}
    required.update({"status": "complete", "cache_key": expected_key})
    point_path.write_text(json.dumps(required), encoding="utf-8")
    assert parallel.valid_main_point(tmp_path, item, identities) is False
    vector = parallel.main_vector_path(tmp_path, item["physical_id"])
    vector.parent.mkdir(parents=True)
    np.save(vector, np.zeros(20, dtype=np.complex128))
    assert parallel.valid_main_point(tmp_path, item, identities) is True
