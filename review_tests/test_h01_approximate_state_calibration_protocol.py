import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "review_response" / "h01_approximate_state_calibration_protocol.json"
SOURCE = (
    ROOT
    / "artifacts"
    / "server_unused_molecule_frozen_holdout_20260921_d288797"
)


def _protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_h01_protocol_hash_and_source_are_frozen():
    protocol = _protocol()
    assert hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == (
        "e0e2649db1f8d109779ab1db26822f45c92c2a660569caa643f5f363e3ce27a6"
    )
    assert protocol["source"]["numerical_result_commit"].startswith("33a761d")
    assert protocol["source"]["oracle_protocol_sha256"] == (
        "b0fc69d3ef89fcae28172ae1bd89ca0b192154ff86eed34410f73cdc2a770a56"
    )
    assert (SOURCE / "aggregate" / "summary.json").is_file()


def test_h01_conditions_formulae_and_states_are_fixed():
    protocol = _protocol()
    assert protocol["conditions"]["primary_development"] == [
        "N2_active_eq_sto3g",
        "N2_active_stretch150_sto3g",
        "CO_active_eq_sto3g",
        "CO_active_stretch150_sto3g",
    ]
    assert protocol["conditions"]["auxiliary_failure_diagnostic"] == [
        "HF_full_eq_sto3g",
        "HF_full_stretch150_sto3g",
    ]
    assert [(item["pf"], item["model_powers"]) for item in protocol["formulae"]] == [
        ("current_m3", [4, 6]),
        ("yoshida4", [4, 6]),
    ]
    assert [item["id"] for item in protocol["state_methods"]] == [
        "exact_ground",
        "rhf_determinant",
        "cisd",
    ]


def test_h01_primary_proxy_points_and_thresholds_are_fixed():
    protocol = _protocol()
    assert protocol["proxy"]["primary_signed_quantity"] == (
        "continuous_unwrapped_arg(z_echo(t))/t"
    )
    assert protocol["calibration"]["primary_relative_to_source_t_ana"] == [
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
    ]
    assert protocol["calibration"]["information_ablation_relative_to_source_t_ana"] == [
        0.1,
        0.2,
        0.3,
    ]
    assert protocol["pass_thresholds"] == {
        "eta_star": 0.01,
        "eta_min": 0.01,
        "eta_t": 0.05,
        "maximum_unseen_residual_over_epsilon": 0.05,
    }
    assert protocol["frozen_budget_cost_multipliers"] == [1.0, 1.01]


def test_h01_keeps_oracle_time_scale_and_forbids_scope_expansion():
    protocol = _protocol()
    assert "source run's analytic time" in protocol["information_access"][
        "oracle_analytic_time_use"
    ]
    forbidden = set(protocol["scope"]["forbidden"])
    assert "change PF coefficients" in forbidden
    assert "add molecules or bases" in forbidden
    assert "claim end-to-end cheap calibration" in forbidden


def test_source_primary_result_supports_the_h01_branch_decision():
    summary = json.loads(
        (SOURCE / "aggregate" / "summary.json").read_text(encoding="utf-8")
    )
    by_formula = {row["formula"]: row for row in summary["primary_summary"]}
    assert by_formula["current_m3"]["primary_conditions_passed"] == 4
    assert by_formula["yoshida4"]["primary_conditions_passed"] == 4
    assert by_formula["current_m3"]["base_budget_conditions_met"] == 4
