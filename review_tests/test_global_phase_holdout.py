import numpy as np

from analyze_global_phase_holdout import strict_leading_validity


def test_strict_leading_validity_brackets_first_failure():
    times = np.array([0.1, 0.2, 0.3, 0.4])
    model = np.ones(4)
    errors = np.array([1.01, 1.05, 1.11, 1.0])
    result = strict_leading_validity(
        times, errors, model, noise_floor=0.0, fit_start=0.1
    )
    assert result["status"] == "pass"
    assert result["cap_candidate"] == 0.2
    assert result["first_failure_time"] == 0.3


def test_strict_leading_validity_does_not_accept_later_reentry():
    times = np.array([0.1, 0.2, 0.3])
    model = np.ones(3)
    errors = np.array([1.2, 1.0, 1.0])
    result = strict_leading_validity(
        times, errors, model, noise_floor=0.0, fit_start=0.1
    )
    assert result["status"] == "failed"
    assert result["cap_candidate"] is None


def test_strict_leading_validity_respects_fit_window_and_floor():
    times = np.array([0.1, 0.2, 0.3])
    model = np.array([1e-12, 1.0, 1.0])
    errors = np.array([9e-12, 1.0, 1.0])
    result = strict_leading_validity(
        times, errors, model, noise_floor=1e-10, fit_start=0.2
    )
    assert result["status"] == "not validated"
    assert result["last_valid_time"] == 0.3
    assert result["right_censored"] is True
