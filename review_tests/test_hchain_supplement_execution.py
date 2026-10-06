"""Synthetic/contract-only tests: never open molecular runtime or truth."""
from pathlib import Path
from copy import deepcopy
import json
import numpy as np
import pytest
from scipy.linalg import expm

import hchain_supplement_execution as implementation
from hchain_supplement_execution import (
    AccessGuard, EPS, GAMMAS, PreparationError, ScienceLedger, analyze_cached,
    budget, cheap_decisions, geometry_generator, rank8_control, rank_diagnostics,
    reproduction, safety_mechanism, truth_comparison,
)
from pf_spectral_recoverability_d2 import analyze_coordinate, build_arnoldi_chain
from hchain_cached_prefix import cached_prefix, PREFIXES
from hchain_prediction_phase import make_bundle

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / implementation.OLD / "rank_aware_M1_amendment.json").read_text())["numerical_rules"]


def toy():
    rng = np.random.default_rng(327)
    matrix = rng.normal(size=(40, 40)) + 1j * rng.normal(size=(40, 40))
    h = (matrix + matrix.conj().T) / 20
    perturbation = np.diag(np.linspace(-.002, .003, 40))
    state = rng.normal(size=40) + 1j * rng.normal(size=40)
    state /= np.linalg.norm(state)
    return h, perturbation, state


def test_one_shared_chain_actions_and_old_rank8_control():
    h, perturbation, state = toy()
    previous_control, previous_old = None, None
    calls = {"PF": 0, "H": 0}
    for t in (.3, .4, .5):
        unitary = expm(1j * t * (h + perturbation))
        def apply_u(vector):
            calls["PF"] += 1
            return unitary @ vector
        def apply_h(vector):
            calls["H"] += 1
            return h @ vector
        chain = build_arnoldi_chain(state, apply_u, apply_h, maximum_dimension=32,
            reorthogonalization_passes=2, relative_breakdown_tolerance=1e-12)
        before = calls.copy()
        control, previous_control = rank8_control(chain, t, previous_control, RULES, 14344)
        assert calls == before
        old, previous_old = analyze_coordinate(start=state, apply_u=lambda v: unitary @ v,
            apply_h=lambda v: h @ v, time_value=t, prefix_dimensions=(1, 2, 4, 8),
            primary_dimension=8, previous_vector=previous_old, numerical_rules=RULES,
            epsilon_hartree=EPS, beta=1.2, rotations_per_step=14344)
        assert reproduction(control, {"core_prediction": old}, {"scalar_absolute": 1e-10, "scalar_relative": 1e-8})["passed"]
    assert calls == {"PF": 96, "H": 96}


def test_rank_own_previous_vector_not_shared(monkeypatch):
    h, _, state = toy()
    u = expm(.3j * h)
    chain = build_arnoldi_chain(state, lambda v: u @ v, lambda v: h @ v,
        maximum_dimension=32, reorthogonalization_passes=2, relative_breakdown_tolerance=1e-12)
    histories = {m: np.eye(40, dtype=complex)[:, index] for index, m in enumerate(PREFIXES)}
    seen = {}
    original = implementation.analyze_prefix
    def spy(chain, m, t, *, previous_vector, **kwargs):
        seen[m] = previous_vector
        return original(chain, m, t, previous_vector=previous_vector, **kwargs)
    monkeypatch.setattr(implementation, "analyze_prefix", spy)
    analyze_cached(chain, PREFIXES, .3, histories, RULES)
    assert all(seen[m] is histories[m] for m in PREFIXES)
    assert seen[8] is not seen[32]


@pytest.mark.parametrize("m", [4, 8, 16, 32])
def test_adjacent_prefix_width(m):
    h, _, state = toy()
    unitary = expm(.3j * h)
    chain = build_arnoldi_chain(state, lambda v: unitary @ v, lambda v: h @ v,
        maximum_dimension=32, reorthogonalization_passes=2, relative_breakdown_tolerance=1e-12)
    raw, _ = analyze_cached(chain, PREFIXES, .3, {}, RULES)
    data = rank_diagnostics(raw, RULES)
    assert data[m]["prefix_width_hartree"] == abs(raw[m]["signed_shift_estimate_hartree"] - raw[m//2]["signed_shift_estimate_hartree"])
    assert data[m]["empirical_width_hartree"] == max(data[m]["prefix_width_hartree"], data[m]["local_residual_width_hartree"])


def test_breakdown_missing_not_accepted_lower_prefix():
    state = np.array([1., 0.], dtype=complex)
    chain = build_arnoldi_chain(state, lambda v: v, lambda v: v,
        maximum_dimension=32, reorthogonalization_passes=2, relative_breakdown_tolerance=1e-12)
    raw, _ = analyze_cached(chain, PREFIXES, .3, {}, RULES)
    result = rank_diagnostics(raw, RULES)
    for m in (4, 8, 16, 32):
        assert result[m]["status"] == "missing_actual_rank_breakdown"
        assert "empirical_width_hartree" not in result[m]
    control, _ = rank8_control(chain, .3, None, RULES, 14344)
    assert control["abstained"]


def test_geometry_only_generator_is_callable_no_science():
    function = geometry_generator(ROOT, 1.2)
    assert callable(function)
    assert function.__globals__["distance"] == 1.2
    assert function.__code__.co_names.count("kernel") == 1


@pytest.mark.parametrize("gamma", [1., *GAMMAS])
@pytest.mark.parametrize("e", [0., EPS/3, EPS*.9, EPS*1.1])
def test_margin_matches_continuous_budget_safety(gamma, e):
    c = EPS/4
    mechanism = safety_mechanism(c, e, gamma)
    frozen = gamma * budget(.5, c, 100)
    direct_slack = EPS - (e + 1.2 * 100/(.5 * frozen))
    assert mechanism["safety_slack"] == pytest.approx(direct_slack, abs=1e-18)
    if gamma == 1:
        assert mechanism["margin_ratio"] is None
    if e >= EPS:
        assert mechanism["gamma_req"] is None


def test_cheap_selector_earliest_exact_tie_and_all_gammas():
    # Choose errors producing an exact budget tie (continuous algebra).
    points = [{"candidate_id": "early", "time": .5, "delta_C_hartree": 0.},
              {"candidate_id": "late", "time": 1., "delta_C_hartree": EPS/2}]
    result = cheap_decisions(points, 100)
    assert len(result["B1_frontier"]) == 4
    assert all(arm["selected"]["candidate_id"] == "early" for arm in result["B1_frontier"])
    assert not result["B0"]["assumed_safe"]
    assert not result["B2_H1_executed"]


def test_no_positive_allowance_no_selector_rescue():
    result = cheap_decisions([{"candidate_id": "bad", "time": .5, "delta_C_hartree": EPS}], 100)
    assert all(arm["selected"] is None for arm in result["B1_frontier"])
    assert result["B0"]["budget"] is None


def test_rank32_counter_replaces_old_60_cap():
    ledger = ScienceLedger(32)
    for _ in range(96):
        ledger.charge("m1_pf_vector_actions", 60)
    with pytest.raises(PreparationError, match="action cap"):
        ledger.charge("m1_pf_vector_actions", 60)


def test_audit_blocks_truth_and_other_worktree(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    output = workspace / "approved_output"
    output.mkdir()
    source = workspace / "source.py"
    source.write_text("pass")
    guard = AccessGuard(workspace, output, [source])
    guard.hook("open", (str(source), "r", 0))
    assert str(source) in guard.reads
    for name in ("truth.json", ".worktrees/prospective/truth.json", "ground.npz"):
        with pytest.raises(PreparationError, match="unallowlisted"):
            guard.hook("open", (str(workspace / name), "r", 0))


def test_freeze_does_not_overwrite(tmp_path):
    directory = tmp_path / "prediction"
    digest = make_bundle(directory, {"truth_reads": 0}, {}, {}, {}, {})
    assert len(digest) == 64
    assert json.loads((directory / "manifest.json").read_text())["manifest_self_excluded"]
    with pytest.raises(PreparationError, match="already exists"):
        make_bundle(directory, {}, {}, {}, {}, {})


@pytest.mark.parametrize("valid", [True, False])
def test_decomposition_requires_same_physical_branch(valid):
    point = {"signed_shift_estimate_hartree": 2e-6, "selected_unwrapped_energy_hartree": -2 + 3e-6,
             "h_reference_energy_hartree": -2 + 1e-6, "empirical_width_hartree": 1e-5, "e_use_hartree": 1.2e-5}
    truth = {"signed_direct_shift_hartree": 1e-6, "minimum_selected_phase_gap_radians": .1,
             "quality": {"physical_branch_valid": valid}}
    result = truth_comparison(point, 1e-6, truth, -2, 100, .5)
    assert (result["PF_side_error_hartree"] is not None) == valid
    if valid:
        assert result["decomposition_closure_residual"] == pytest.approx(0, abs=1e-15)
    else:
        assert result["physical_branch_correct"] is None
