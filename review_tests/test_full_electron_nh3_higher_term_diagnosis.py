import numpy as np

import run_full_electron_nh3_higher_term_diagnosis as diagnosis
from trotterlib.pf_decomposition import symmetric_s2_sequence


def test_fixed_formulae_and_stage_order():
    formulae = diagnosis._formulae()
    assert tuple(formulae["paper_new4"]["weights"]) == diagnosis.PAPER_NEW4
    assert tuple(formulae["joint_refine_r0_s0046"]["weights"]) == diagnosis.JOINT_REFINE
    assert symmetric_s2_sequence(diagnosis.YOSHIDA6_M3) == [
        diagnosis.YOSHIDA6_M3[3],
        diagnosis.YOSHIDA6_M3[2],
        diagnosis.YOSHIDA6_M3[1],
        diagnosis.YOSHIDA6_M3[0],
        diagnosis.YOSHIDA6_M3[1],
        diagnosis.YOSHIDA6_M3[2],
        diagnosis.YOSHIDA6_M3[3],
    ]
    assert len(symmetric_s2_sequence(formulae["yoshida4"]["weights"])) == 3
    assert len(symmetric_s2_sequence(formulae["paper_new4"]["weights"])) == 5
    assert len(symmetric_s2_sequence(formulae["m5_best"]["weights"])) == 11


def test_stretched_geometry_fixes_nitrogen_and_scales_bonds():
    equilibrium = diagnosis._geometry("equilibrium")
    stretched = diagnosis._geometry("stretch150")
    nitrogen = np.asarray(equilibrium[0][1])
    assert np.array_equal(np.asarray(stretched[0][1]), nitrogen)
    for original, extended in zip(equilibrium[1:], stretched[1:]):
        old_vector = np.asarray(original[1]) - nitrogen
        new_vector = np.asarray(extended[1]) - nitrogen
        assert np.allclose(new_vector, 1.5 * old_vector, atol=1e-14, rtol=0.0)


def test_declared_fit_rule_selects_earliest_window():
    times = diagnosis.FIT_GRID[:5]
    errors = [2.5e-4 * time**4 for time in times]
    fit = diagnosis._qualify_fit(times, errors, 4)
    assert fit["qualified"]
    assert fit["selected_window"]["start_index"] == 0
    assert abs(fit["selected_window"]["fixed_order_alpha"] - 2.5e-4) < 1e-14


def test_declared_fit_rule_does_not_relax_noise_floor():
    times = diagnosis.FIT_GRID
    errors = [0.5 * diagnosis.FIT_NOISE_FLOOR for _ in times]
    fit = diagnosis._qualify_fit(times, errors, 4)
    assert not fit["qualified"]
    assert fit["selected_window"] is None


def test_three_term_fit_recovers_signed_coefficients():
    analytic_time = 0.9
    powers = [4, 6, 8]
    expected = [-2.0e-5, 8.0e-6, -1.0e-6]
    points = []
    for relative in diagnosis.TRAINING_RELATIVE_TIMES:
        time_value = relative * analytic_time
        shift = sum(coefficient * time_value**power for coefficient, power in zip(expected, powers))
        points.append({"time": time_value, "signed_direct_shift_hartree": shift})
    fitted = diagnosis._fit_model(points, 4, analytic_time, powers, "three_term")
    assert np.allclose(fitted["coefficient_values"], expected, atol=1e-16, rtol=1e-10)


def test_model_validation_records_invalid_direct_cost_without_crashing(monkeypatch):
    optimum = {
        "time": 1.0,
        "cost": 100.0,
        "at_optimization_boundary": False,
    }
    monkeypatch.setattr(diagnosis, "_model_optimum", lambda *args: optimum)

    def fake_direct_point(
        system, sequence, time_value, rotations, backend, gpu_id, previous_vector
    ):
        direct_cost = None if np.isclose(time_value, 1.0) else 105.0
        return {
            "time": time_value,
            "direct_cost": direct_cost,
            "signed_direct_shift_hartree": 0.0,
            "ground_overlap_probability": 1.0,
            "adjacent_selected_vector_overlap_probability": 1.0,
            "eigenpair_residual_2_norm": 1e-14,
        }, np.ones(1)

    monkeypatch.setattr(diagnosis, "_direct_point", fake_direct_point)
    model = {
        "name": "one_term",
        "coefficient_powers": [4],
        "coefficient_values": [0.0],
    }
    result = diagnosis._validate_model({}, [], 1, model, 1.0, "cpu", 5)

    assert result["invalid_cost_at_model_optimum"]
    assert result["metrics"]["eta_star"] is None
    assert result["metrics"]["eta_min"] is None
    assert not result["checks"]["eta_star"]
    assert not result["passed"]
    assert result["direct_grid_minimum"]["direct_cost"] == 105.0


def test_model_validation_handles_no_finite_direct_cost(monkeypatch):
    optimum = {
        "time": 1.0,
        "cost": 100.0,
        "at_optimization_boundary": False,
    }
    monkeypatch.setattr(diagnosis, "_model_optimum", lambda *args: optimum)

    def fake_direct_point(
        system, sequence, time_value, rotations, backend, gpu_id, previous_vector
    ):
        return {
            "time": time_value,
            "direct_cost": None,
            "signed_direct_shift_hartree": 0.0,
            "ground_overlap_probability": 1.0,
            "adjacent_selected_vector_overlap_probability": 1.0,
            "eigenpair_residual_2_norm": 1e-14,
        }, np.ones(1)

    monkeypatch.setattr(diagnosis, "_direct_point", fake_direct_point)
    model = {
        "name": "one_term",
        "coefficient_powers": [4],
        "coefficient_values": [0.0],
    }
    result = diagnosis._validate_model({}, [], 1, model, 1.0, "cpu", 5)

    assert result["direct_grid_minimum"] is None
    assert result["metrics"]["eta_t"] is None
    assert not result["checks"]["direct_local_minimum_bracketed"]
    assert not result["passed"]
