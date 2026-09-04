import numpy as np

from validate_gpu_template_phase import _phase_comparison


def test_t0_fixed_phase_removes_same_phase_at_later_time():
    reference = np.asarray([1.0, 2.0j], dtype=np.complex128)
    reference /= np.linalg.norm(reference)
    phase = np.exp(1j * 0.73)
    result = _phase_comparison(reference, phase * reference, phase)
    assert result["passes_1e-10"]
    assert result["fixed_phase_corrected_relative_2_norm"] < 1e-14
    assert abs(result["phase_drift_from_t0_rad"]) < 1e-14


def test_fixed_phase_detects_time_dependent_drift():
    reference = np.asarray([1.0, 0.0], dtype=np.complex128)
    phase0 = np.exp(1j * 0.2)
    candidate = np.exp(1j * 0.3) * reference
    result = _phase_comparison(reference, candidate, phase0)
    assert not result["passes_1e-10"]
    assert np.isclose(result["phase_drift_from_t0_rad"], 0.1)
