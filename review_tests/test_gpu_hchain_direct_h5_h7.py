from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import run_gpu_hchain_direct_h5_h7 as gpu_run
from trotterlib.sector_pf import build_sector_pf_unitary
from trotterlib.sector_pf_gpu import GpuSectorPFBuilder


def test_extension_narrows_scope_without_changing_fixed_science() -> None:
    extension = gpu_run.load_json(gpu_run.PROJECT_ROOT / gpu_run.EXTENSION)
    assert extension["scope_change"]["included_systems_in_order"] == ["H5", "H7"]
    assert extension["scope_change"]["excluded_from_this_run"] == ["H8", "H9"]
    fixed = extension["fixed_scientific_configuration"]
    assert fixed["epsilon_E_hartree"] == 0.00015936001019904
    assert fixed["beta"] == 1.2
    assert fixed["formula_keys_in_order"] == ["m5", "y8"]
    assert fixed["relative_grid"] == {
        "start": 0.2,
        "stop": 1.7,
        "step": 0.05,
        "point_count": 31,
    }
    assert fixed["dtype"] == "complex128"


def test_parent_hashes_and_grid_are_fixed() -> None:
    assert gpu_run.sha256(gpu_run.PROJECT_ROOT / gpu_run.PROTOCOL) == gpu_run.PARENT_PROTOCOL_SHA256
    assert gpu_run.sha256(gpu_run.PROJECT_ROOT / gpu_run.SECTOR_AMENDMENT) == gpu_run.SECTOR_AMENDMENT_SHA256
    assert gpu_run.sha256(gpu_run.PROJECT_ROOT / gpu_run.PARTIAL_AMENDMENT) == gpu_run.PARTIAL_AMENDMENT_SHA256
    assert gpu_run.fixed_grid() == [round(0.2 + 0.05 * index, 12) for index in range(31)]


@pytest.mark.parametrize("h_chain", [5, 7])
@pytest.mark.parametrize("formula_key", ["m5", "y8"])
def test_resource_estimator_lists_exact_resident_arrays(h_chain: int, formula_key: str) -> None:
    estimate = gpu_run.resource_estimate(h_chain, formula_key)
    names = {row["name"] for row in estimate["resident_arrays"]}
    assert {
        "group_eigenvalues",
        "group_eigenvectors",
        "hamiltonian",
        "state",
        "unique_s2_block_cache",
        "pf_unitary",
        "gpu_gemm_scratch_upper_bound",
        "cpu_schur_triangular_vectors_workspace_upper_bound",
        "cuda_context_and_library_reserve",
    } <= names
    assert estimate["exact_complex128_plan_preserved"] is True
    assert estimate["host_required_with_20_percent_margin_bytes"] > estimate["host_peak_upper_bound_bytes"]
    assert estimate["device_required_with_20_percent_margin_bytes"] > estimate["device_peak_upper_bound_bytes"]


def test_h7_group_eigenvector_lower_bound_is_recorded_conservatively() -> None:
    estimate = gpu_run.resource_estimate(7, "m5")
    eigenvectors = next(
        row for row in estimate["resident_arrays"] if row["name"] == "group_eigenvectors"
    )
    assert eigenvectors["shape"] == [105, 735, 735]
    assert eigenvectors["dtype"] == "complex128"
    assert eigenvectors["bytes"] == 105 * 735 * 735 * 16


def test_cache_key_covers_predictions_source_system_formula_grid_backend_and_dtype(tmp_path: Path) -> None:
    phase_a = tmp_path / "phase_a"
    phase_a.mkdir()
    (phase_a / "predictions.json").write_text('{"value": 1}\n', encoding="utf-8")
    (phase_a / "source_manifest.json").write_text('{"source": 1}\n', encoding="utf-8")
    key_5_m5, material = gpu_run.cache_key(phase_a, 5, "m5")
    key_7_m5, _ = gpu_run.cache_key(phase_a, 7, "m5")
    key_5_y8, _ = gpu_run.cache_key(phase_a, 5, "y8")
    assert len({key_5_m5, key_7_m5, key_5_y8}) == 3
    assert material["relative_grid"] == gpu_run.fixed_grid()
    assert material["backend"] == "gpu_exact_dense_sector_unitary_cpu_complex128_schur"
    assert material["dtype"] == "complex128"
    (phase_a / "predictions.json").write_text('{"value": 2}\n', encoding="utf-8")
    changed, _ = gpu_run.cache_key(phase_a, 5, "m5")
    assert changed != key_5_m5


def test_system_identity_gate_rejects_wrong_sector() -> None:
    valid = {
        "num_groups": 45,
        "sector": {"population_counts": [3, 1], "dimension": 50},
    }
    gpu_run.validate_system_identity(valid, 5)
    invalid = json.loads(json.dumps(valid))
    invalid["sector"]["dimension"] = 49
    with pytest.raises(RuntimeError, match="sector identity mismatch"):
        gpu_run.validate_system_identity(invalid, 5)


def test_exact_gpu_builder_matches_cpu_on_synthetic_complete_spectra() -> None:
    rng = np.random.default_rng(20260927)
    spectra: list[tuple[np.ndarray, np.ndarray]] = []
    for _ in range(3):
        raw = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
        hermitian = raw + raw.conj().T
        values, vectors = np.linalg.eigh(hermitian)
        spectra.append((values.astype(np.float64), vectors.astype(np.complex128)))
    sequence = [0.2, -0.1, 0.2]
    cpu = build_sector_pf_unitary(spectra, sequence, 0.37, method="s2-cache")
    builder = GpuSectorPFBuilder(spectra, logical_device=0)
    try:
        gpu = builder.build(sequence, 0.37)
        identity = builder.identity()
    finally:
        builder.close()
    assert gpu.dtype == np.complex128
    assert np.linalg.norm(gpu - cpu) <= 1e-12
    assert identity["backend"] == "gpu_exact_dense_sector_unitary_cpu_schur"
    assert identity["dtype"] == "complex128"


def test_predictions_preclude_unregistered_fit_and_holdout() -> None:
    predictions = gpu_run.predictions_payload()
    assert predictions["scope"] == ["H5/m5", "H5/y8", "H7/m5", "H7/y8"]
    assert predictions["analysis_predictions"]["odd_m5_fit"] == "not_performed_because_H9_is_out_of_scope"
    assert predictions["analysis_predictions"]["H8_holdout"] == "not_run_by_user_scope"
