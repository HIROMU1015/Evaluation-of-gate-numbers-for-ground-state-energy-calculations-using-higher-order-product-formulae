import numpy as np

import run_full_electron_nh3_followup_diagnostics as followup


def test_effective_orders_recover_power_law():
    times = np.geomspace(0.01, 0.06, 7)
    errors = 3.2e-3 * times**4
    observed = followup.effective_orders(times, errors)
    assert observed[0] is None
    assert np.allclose(observed[1:], 4.0, atol=1e-12, rtol=0.0)


def test_extended_grid_uses_same_declared_fit_criteria():
    times = followup.EXTENDED_SHORT_GRID
    errors = [3.2e-3 * time**4 for time in times]
    result = followup.qualify_extended(times, errors, 4)
    assert result["qualified"]
    assert result["selected_window"]["start_index"] == 0
    assert result["noise_floor"] == 5e-13
    assert result["order_tolerance"] == 0.2
    assert result["minimum_r2"] == 0.999


def test_fine_grid_is_fixed_before_execution():
    assert len(followup.FINE_RATIOS) == 11
    assert np.allclose(followup.FINE_RATIOS, np.arange(0.92, 1.021, 0.01))
    assert followup.ratio_key(0.92) == "r092"
    assert followup.ratio_key(1.02) == "r102"
