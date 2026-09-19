import numpy as np

import run_nh3_time_scale_fit_diagnosis as diagnosis


def test_condition_specs_distinguish_active_and_full_spaces():
    active = diagnosis.condition_spec("active_equilibrium")
    full = diagnosis.condition_spec("full_equilibrium")
    assert active["frozen_core_spatial_orbitals"] == 1
    assert active["active_spatial_orbitals"] == 7
    assert full["frozen_core_spatial_orbitals"] == 0
    assert full["active_spatial_orbitals"] == 8


def test_historical_protocols_remain_distinct():
    shared = diagnosis.PROTOCOLS["shared_molecular"]
    legacy = diagnosis.PROTOCOLS["legacy_molecular_sensitivity"]
    assert np.allclose(shared["grid"], np.geomspace(0.06, 0.80, 15))
    assert shared["noise_floor"] == 5e-13
    assert np.allclose(legacy["grid"], np.geomspace(0.02, 1.8, 34))
    assert legacy["noise_floor"] == 5e-12
    assert "sensitivity" in legacy["role"]


def test_qualification_uses_selected_protocol_floor():
    times = np.geomspace(0.06, 0.80, 15)
    errors = 0.2 * times**4
    result = diagnosis.qualify(times, errors, 4, 5e-13)
    assert result["qualified"]
    assert result["selected_window"]["start_index"] == 0
    assert result["noise_floor"] == 5e-13


def test_failure_reason_separates_order_and_r2():
    times = np.geomspace(0.06, 0.80, 15)
    signed = 0.2 * times**3
    points = [
        {
            "proxy_error_hartree": abs(value),
            "signed_proxy_shift_hartree": value,
        }
        for value in signed
    ]
    fit = diagnosis.qualify(times, np.abs(signed), 4, 5e-13)
    reasons = diagnosis.failure_reasons(points, fit, 4, 5e-13)
    assert not fit["qualified"]
    assert any("fitted order" in reason for reason in reasons)


def test_fine_grid_and_added_points_are_preregistered():
    assert diagnosis.FINE_RATIOS == tuple(
        float(round(0.90 + 0.01 * i, 2)) for i in range(16)
    )
    assert diagnosis.ADDED_FINE_RATIOS == (0.91, 1.03, 1.04)
    assert diagnosis.DIRECT_TIMES == (0.0075, 0.015, 0.03, 0.06)
