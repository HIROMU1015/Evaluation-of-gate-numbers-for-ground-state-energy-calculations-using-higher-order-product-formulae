import json
from pathlib import Path

import run_unused_molecule_frozen_holdout as runner


def test_frozen_protocol_matches_runner():
    protocol = runner._protocol()
    assert protocol["base_result_commit"].startswith("46a7ed1")
    assert tuple(item["name"] for item in protocol["conditions"]) == tuple(
        runner._condition_map()
    )
    assert runner.FORMULAE == (
        "yoshida4", "current_m3", "two_term_center", "m5_best", "yoshida6_m3"
    )
    assert protocol["frozen_budget_cost_multipliers"] == [1.0, 1.01]


def test_expected_population_dimensions():
    conditions = runner._condition_map()
    for name in (
        "N2_active_eq_sto3g", "N2_active_stretch150_sto3g",
        "CO_active_eq_sto3g", "CO_active_stretch150_sto3g",
    ):
        assert runner._expected_dimension(conditions[name]) == 3136
    for name in ("HF_full_eq_sto3g", "HF_full_stretch150_sto3g"):
        assert runner._expected_dimension(conditions[name]) == 36


def test_formula_model_sets_use_frozen_training_information(monkeypatch):
    calls = []

    def fake_fit(points, order, analytic_time, powers, name):
        calls.append((len(points), order, tuple(powers), name))
        return {"name": name}

    monkeypatch.setattr(runner.diagnosis, "_fit_model", fake_fit)
    points = [{"time": value} for value in range(5)]
    models = runner._formula_models("yoshida4", points, 4, 1.0)
    assert tuple(models) == ("two_term_5point", "two_term_3point", "three_term_5point")
    assert calls == [
        (5, 4, (4, 6), "two_term_5point"),
        (3, 4, (4, 6), "two_term_3point"),
        (5, 4, (4, 6, 8), "three_term_5point"),
    ]


def test_stage2_candidate_rule_is_fixed():
    thresholds = runner._protocol()["pass_thresholds"]
    result = {
        "passed": False,
        "metrics": {
            "eta_star": thresholds["eta_star"] / 2,
            "eta_min": thresholds["eta_min"] / 2,
            "eta_t": 1.5 * thresholds["eta_t"],
            "maximum_unseen_residual_over_epsilon": (
                thresholds["maximum_unseen_residual_over_epsilon"] / 2
            ),
        },
        "direct_validation_points": [
            {"direct_cost": 10.0}, {"direct_cost": 9.9}, {"direct_cost": 10.0}
        ],
    }
    assert runner._candidate_reasons(result) == ["eta_t_only_within_twice_threshold"]


def test_protocol_file_is_valid_json():
    payload = json.loads(Path(runner.PROTOCOL_PATH).read_text(encoding="utf-8"))
    assert payload["protocol_id"] == "unused_molecule_frozen_holdout_v1"
