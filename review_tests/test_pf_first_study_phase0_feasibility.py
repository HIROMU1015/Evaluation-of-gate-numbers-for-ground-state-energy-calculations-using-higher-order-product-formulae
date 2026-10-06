"""Boundary and independent algebra tests; no scientific computation or imports."""
import ast
import importlib.util
import json
import math
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO / "review_response/audit_pf_first_study_phase0_feasibility.py"
spec = importlib.util.spec_from_file_location("phase0_scalar_audit", BUILDER_PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def scalar_row(fit, state, proxy, direct=4.0):
    total = fit + state + proxy
    r = {k: None for k in audit.META}
    r.update(source_row=2, experiment_id="B", case_id="synthetic_scalar", formula_id="fixed",
        state_id="cisd", state_family="cisd", sign=1, absolute_time=0.125,
        model_status="fit_ok", quality_class="resolved", primary_eligible=True,
        original_case_dominance="mixed", fhat_approx_hartree=direct+total, delta_direct_hartree=direct)
    for name, value in [("fit", fit), ("state", state), ("proxy", proxy), ("total", total)]:
        r[f"E_{name}_signed_hartree"] = value
    return r


def test_signed_error_and_absolute_risk_are_distinct_with_both_signs():
    positive = scalar_row(0.25, -1.5, 0.25)
    negative = scalar_row(-0.25, 1.5, -0.25, direct=-4)
    _, budgets = audit.oracle_and_budget([positive, negative])
    assert budgets[0]["signed_total_error_hartree"] == -1
    assert budgets[1]["signed_total_error_hartree"] == 1
    for b in budgets:
        assert b["underestimation_hartree"] == 1
        assert b["u_state_hartree"] == 1.5
        assert b["u_fit_hartree"] == b["u_proxy_hartree"] == -0.25
        assert b["largest_positive_unsafe_component"] == "state"


def test_sign_crossing_never_has_additive_component_attribution():
    row = scalar_row(1, 1, 1, direct=-2)
    _, budgets = audit.oracle_and_budget([row])
    b = budgets[0]
    assert b["sign_crossing"] is True
    assert b["underestimation_hartree"] == 1
    for name in ["fit", "state", "proxy"]:
        assert b[f"u_{name}_hartree"] is None
    assert b["underestimation_attribution_closure_hartree"] is None


def test_state_removal_can_worsen_error_and_risk_by_removing_cancellation():
    row = scalar_row(-3, 4, 0, direct=10)
    oracle, budgets = audit.oracle_and_budget([row])
    assert oracle[0]["original_total_abs_hartree"] == 1
    assert oracle[0]["no_state_abs_hartree"] == 3
    assert oracle[0]["abs_reduction_ratio"] == -2
    assert budgets[0]["underestimation_hartree"] == -1
    assert budgets[0]["no_state_underestimation_hartree"] == 3


def test_zero_error_denominator_is_null_not_infinite_or_clipped():
    oracle, _ = audit.oracle_and_budget([scalar_row(1, -1, 0)])
    assert oracle[0]["abs_retention_ratio"] is None
    assert oracle[0]["abs_reduction_ratio"] is None


def make_quartets():
    rows = []
    for q in [0.001, 0.01, 0.05]:
        for index in range(4):
            phase = index * math.pi/2
            state = 2*q + math.sqrt(q*(1-q)) * (3*math.cos(phase)+4*math.sin(phase))
            r = scalar_row(0, state, 0)
            r.update(q=q, phase_radians=phase, state_family="controlled", g_exact_hartree=0.02,
                g_approx_hartree=0.02+state, state_id=f"controlled_q{q}_phi{phase}")
            rows.append(r)
    return rows


def test_phase_quartet_separates_linear_population_and_interference():
    expanded, quartets, scaling = audit.phase_analysis(make_quartets())
    assert len(expanded) == 12
    assert len(quartets) == 3
    assert len(scaling) == 1
    for r in quartets:
        assert r["phase_average_state_error_hartree"] == pytest.approx(2*r["q"])
        assert r["mean_interference_hartree"] == pytest.approx(0, abs=1e-15)
        assert r["interference_rms_over_sqrt_q_one_minus_q_hartree"] == pytest.approx(5/math.sqrt(2))
        assert r["pythagorean_closure_hartree_squared"] == pytest.approx(0, abs=1e-15)
    assert scaling[0]["averaged_over_q_relative_range"] < 1e-12


def test_incomplete_or_duplicate_phase_quartet_is_rejected():
    rows = make_quartets()
    with pytest.raises(ValueError, match="quartet"):
        audit.phase_analysis(rows[1:])
    rows[0]["phase_radians"] = rows[1]["phase_radians"]
    with pytest.raises(ValueError, match="quartet"):
        audit.phase_analysis(rows)


def test_truth_free_bound_has_no_direct_error_argument():
    # Any nonnegative e and allowed t satisfy the algebraic lower cost bound.
    beta, rotations, cap, epsilon, b0 = 1.2, 7, 2.0, 0.01, 1000.0
    upper_saving = audit.truth_free_bound(beta, rotations, cap, epsilon, b0)
    for t in [0.2, 1, 2]:
        for direct_error in [0, 0.001, 0.005]:
            cost = beta*rotations/(t*(epsilon-direct_error))
            assert 1-cost/b0 <= upper_saving + 1e-15
    with pytest.raises(ValueError):
        audit.truth_free_bound(beta, rotations, 0, epsilon, b0)


def test_margin_capacity_equals_budget_safety_without_tuning_gamma():
    for c, e in [(0.002, 0.003), (0.003, 0.002)]:
        epsilon, gamma = 0.01, 1.01
        u = e-c
        capacity = (1-1/gamma)*(epsilon-c)
        expected_energy_margin = epsilon-e-(epsilon-c)/gamma
        assert capacity-u == pytest.approx(expected_energy_margin)
        gamma_req = (epsilon-c)/(epsilon-e)
        assert (capacity-u >= 0) == (gamma >= gamma_req)


def test_builder_uses_only_auditable_stdlib_and_readonly_git():
    tree = ast.parse(BUILDER_PATH.read_text())
    allowed = {"__future__", "argparse", "csv", "hashlib", "json", "math", "re", "statistics", "subprocess", "collections", "pathlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(name.name in allowed for name in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module in allowed
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
             and node.func.value.id == "subprocess"]
    assert len(calls) == 1
    assert calls[0].func.attr == "check_output"
    assert isinstance(calls[0].args[0], ast.List)
    assert calls[0].args[0].elts[0].value == "git"


def test_saved_data_reproduction_and_protected_source_identity(tmp_path):
    output = tmp_path / "new_audit"
    verification = audit.build(REPO, output)
    assert verification["original_formal_state_dominant_cases"] == 79
    assert verification["original_formal_mixed_cases"] == 49
    assert verification["primary_eligible_row_counts"] == {"B": 588, "C": 720}
    assert verification["all_six_saved_safety_decisions_match"]
    assert verification["sign_crossing_attribution_always_null"]
    committed_output = REPO / "artifacts/pf_first_study_phase0_feasibility_20261006"
    for path in output.iterdir():
        assert path.read_bytes() == (committed_output / path.name).read_bytes(), path.name
    registry = json.loads((output / "source_registry.json").read_text())
    assert len(registry["sources"]) == 31
    phase_source = next(r for r in registry["sources"] if r["path"].endswith("error_decomposition.csv"))
    assert phase_source["origin_result_commit"] == "d13f49dc8923b0553f8c8596de3c44c8a7a6f14f"
    assert phase_source["verified_snapshot_commit"] == audit.SNAPSHOT


def test_existing_output_is_never_overwritten(tmp_path):
    existing = tmp_path / "frozen_output"
    existing.mkdir()
    sentinel = existing / "prediction.txt"
    sentinel.write_text("frozen")
    with pytest.raises(FileExistsError):
        audit.build(REPO, existing)
    assert sentinel.read_text() == "frozen"
