from __future__ import annotations

import numpy as np

from review_response._pf_first_study_experiment_a_support import (
    formula_registry,
    load_protocol,
    two_level_systems,
)
from review_response._pf_first_study_phase_b_base import (
    _decomposition,
    _direct_rows,
    _dominance_rows,
)


def test_phase_b_direct_scorer_tracks_signed_two_level_branches() -> None:
    protocol, _ = load_protocol(
        __import__("pathlib").Path("PF_first_study_protocol_20260925.json")
    )
    system = two_level_systems()["two_level_noncommuting"]
    formula = formula_registry(protocol)[0]
    rows = _direct_rows(
        experiment_id="unit",
        case_id="two_level",
        formula_id=formula["formula_id"],
        spectra=[np.linalg.eigh(group) for group in system["groups"]],
        sequence=formula["sequence"],
        reference_state=system["ground_state"],
        reference_energy=system["energy"],
        magnitudes=(0.05, 0.08, 0.12),
        signs=(-1, 1),
        degeneracy_gap=1e-8,
        target_error=1.0,
        beta=1.2,
        step_cost=7,
        grid_role="unit",
    )
    assert len(rows) == 6
    assert all(row["branch_reliable"] for row in rows)
    assert max(row["eigenpair_residual_2_norm"] for row in rows) <= 1e-12
    pairs = {}
    for row in rows:
        pairs.setdefault(row["absolute_time"], {})[row["sign"]] = row[
            "direct_shift_hartree"
        ]
    assert max(abs(pair[1] - pair[-1]) for pair in pairs.values()) <= 1e-12


def test_phase_b_decomposition_uses_frozen_model_and_closes() -> None:
    phase_a = []
    exact = []
    direct = []
    for sign in (-1, 1):
        phase_a.append(
            {
                "experiment_id": "B",
                "case_id": "H4",
                "formula_id": "yoshida4",
                "state_id": "cisd",
                "sign": str(sign),
                "absolute_time": "0.125",
                "time_hartree_inverse": str(sign * 0.125),
                "proxy_imag_hartree": "2e-5",
                "quality_class": "resolved",
            }
        )
        exact.append(
            {
                "experiment_id": "B",
                "case_id": "H4",
                "formula_id": "yoshida4",
                "state_id": "exact",
                "sign": sign,
                "absolute_time": 0.125,
                "proxy_imag_hartree": 1.5e-5,
            }
        )
        direct.append(
            {
                "experiment_id": "B",
                "case_id": "H4",
                "formula_id": "yoshida4",
                "grid_role": "mechanism_fixed",
                "sign": sign,
                "absolute_time": 0.125,
                "direct_shift_hartree": 1.0e-5,
            }
        )
    models = [
        {
            "experiment_id": "B",
            "case_id": "H4",
            "formula_id": "yoshida4",
            "state_id": "cisd",
            "model_id": "raw_positive_even_two_term",
            "powers": "[4, 6]",
            "coefficients": "[0.05, -0.01]",
            "status": "fit_ok",
        }
    ]
    rows = _decomposition(
        phase_a_observations=phase_a,
        exact_observations=exact,
        model_rows=models,
        direct_rows=direct,
        b_evaluation_times={0.125},
    )
    assert len(rows) == 2
    assert max(abs(row["closure_residual_hartree"]) for row in rows) <= 1e-18


def test_dominance_rule_requires_threefold_majority() -> None:
    rows = []
    for index in range(5):
        rows.append(
            {
                "experiment_id": "B",
                "case_id": "H4",
                "formula_id": "yoshida4",
                "state_id": "cisd",
                "quality_class": "resolved",
                "E_fit_hartree": 4.0 if index < 3 else 1.0,
                "E_state_hartree": 1.0,
                "E_proxy_hartree": 1.0,
            }
        )
    summary = _dominance_rows(rows, target_error=100.0)
    assert summary[0]["dominant_component"] == "E_fit_hartree"
    assert summary[0]["fit_dominant_count"] == 3
