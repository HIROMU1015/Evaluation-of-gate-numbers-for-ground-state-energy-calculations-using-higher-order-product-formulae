from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
from openfermion.ops import QubitOperator

from benchmark_sparse_pf_smoke import (
    _deserialize_groups,
    _phase_aligned_difference,
    _serialize_groups,
    attach_external_memory,
)


def test_phase_aligned_difference_removes_only_global_phase() -> None:
    reference = np.asarray([1.0, 2.0j, -0.25], dtype=np.complex128)
    reference /= np.linalg.norm(reference)
    candidate = np.exp(0.73j) * reference

    result = _phase_aligned_difference(reference, candidate)

    assert result["passes_1e-10"]
    assert result["relative_2_norm_difference"] < 1e-14


def test_phase_aligned_difference_detects_non_phase_error() -> None:
    reference = np.asarray([1.0, 0.0], dtype=np.complex128)
    candidate = np.asarray([np.sqrt(1.0 - 1e-6), 1e-3], dtype=np.complex128)

    result = _phase_aligned_difference(reference, candidate)

    assert not result["passes_1e-10"]
    assert result["relative_2_norm_difference"] > 1e-4


def test_group_serialization_preserves_shared_hamiltonian() -> None:
    original = [
        [QubitOperator("X0 Y2", 0.25) + QubitOperator((), -0.5)],
        [QubitOperator("Z1", -0.75)],
    ]

    restored = _deserialize_groups(_serialize_groups(original))

    assert [group[0].terms for group in restored] == [
        group[0].terms for group in original
    ]


def test_external_memory_includes_cuda_initialization(tmp_path) -> None:
    result = tmp_path / "result.json"
    samples = tmp_path / "memory.csv"
    result.write_text(json.dumps({"status": "complete"}), encoding="utf-8")
    samples.write_text("1, 40960\n425, 40960\n427, 40960\n", encoding="utf-8")

    status = attach_external_memory(
        SimpleNamespace(
            result_json=result,
            samples_csv=samples,
            physical_gpu_id=2,
            interval_ms=200,
        )
    )

    payload = json.loads(result.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["external_gpu_memory"]["baseline_device_used_mib"] == 1
    assert payload["external_gpu_memory"]["peak_device_used_mib"] == 427
    assert payload["external_gpu_memory"]["peak_device_delta_mib"] == 426
