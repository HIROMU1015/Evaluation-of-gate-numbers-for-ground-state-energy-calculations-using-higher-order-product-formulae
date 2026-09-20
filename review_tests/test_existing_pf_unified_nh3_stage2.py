from __future__ import annotations

import run_existing_pf_unified_nh3_stage2 as stage2


def result(eta_star=0.001, eta_min=0.001, eta_t=0.01, residual=0.001, passed=False):
    costs = [10.1, 10.0, 10.1]
    return {
        "passed": passed,
        "metrics": {
            "eta_star": eta_star,
            "eta_min": eta_min,
            "eta_t": eta_t,
            "maximum_unseen_residual_over_epsilon": residual,
        },
        "direct_validation_points": [
            {"direct_cost": cost} for cost in costs
        ],
    }


def test_formal_pass_is_selected():
    assert "all_four_coarse_checks_passed" in stage2._candidate_reasons(result(passed=True))


def test_only_one_near_miss_check_may_fail():
    reasons = stage2._candidate_reasons(result(eta_t=0.075))
    assert reasons == ["eta_t_only_within_twice_threshold"]
    assert not stage2._candidate_reasons(result(eta_t=0.075, eta_min=0.015))


def test_isolated_drop_requires_two_percent_prominence():
    shallow = result()
    shallow["direct_validation_points"] = [
        {"direct_cost": 10.1}, {"direct_cost": 10.0}, {"direct_cost": 10.1}
    ]
    assert not stage2._isolated_cost_drop(shallow)
    sharp = result()
    sharp["direct_validation_points"] = [
        {"direct_cost": 12.0}, {"direct_cost": 10.0}, {"direct_cost": 11.0}
    ]
    assert stage2._isolated_cost_drop(sharp)


def test_time_matching_does_not_merge_distinct_one_percent_points():
    assert stage2._same_time(1.0, 1.0 + 1e-13)
    assert not stage2._same_time(1.0, 1.0001)
