from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from review_response import run_pf_spectral_information_pilot_d1 as d1


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = (
    ROOT / "review_response/pf_spectral_information_pilot_protocol_draft.json"
)
D0_AUTHORIZATION_PATH = (
    ROOT / "review_response/pf_spectral_information_pilot_authorization.json"
)
D1_AUTHORIZATION_PATH = (
    ROOT / "review_response/pf_spectral_information_pilot_d1_authorization.json"
)
PHASE_A_AMENDMENT_PATH = (
    ROOT / "review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_d1_authorization_is_narrow_and_stops_before_d2() -> None:
    protocol = _load(PROTOCOL_PATH)
    authorization = _load(D1_AUTHORIZATION_PATH)
    assert protocol["status"] == "d0_protocol_frozen_d1_not_authorized"
    assert protocol["scope"]["coordinate_count"] == 6
    assert {row["condition"] for row in protocol["scope"]["coordinates"]} == {
        "HCl_full_eq_sto3g",
        "HCl_full_stretch150_sto3g",
    }
    assert authorization["status"] == "d1_authorized_once_d2_not_authorized"
    assert authorization["execution"] == {
        "d1_spectral_pilot_authorized": True,
        "maximum_completed_runs": 1,
        "resume_same_run_identity_and_output_only": True,
        "cpu_only": True,
        "processes": 1,
        "new_direct_coordinate_count": 0,
        "existing_coordinate_full_pf_unitary_rebuild_count_maximum": 6,
        "existing_coordinate_pf_eigendecomposition_count_maximum": 6,
        "same_h_exact_ground_regeneration_count_maximum": 2,
    }
    assert all(authorization["not_authorized"].values())


def test_source_identity_accepts_only_the_frozen_d0_inputs() -> None:
    source = d1.verify_source_identity(
        ROOT,
        PROTOCOL_PATH,
        D0_AUTHORIZATION_PATH,
        D1_AUTHORIZATION_PATH,
        PHASE_A_AMENDMENT_PATH,
    )
    assert source["verified_source_count"] == len(d1.EXPECTED_HASHES)
    assert source["d1_authorization"]["not_authorized"]["d2"] is True
    assert source["protocol"]["authorization"]["d2_authorized"] is False


def test_phase_clustering_uses_circular_distance_at_wrap() -> None:
    phases = [np.pi - 2e-10, -np.pi + 2e-10, 0.0]
    clusters = d1.phase_clusters(phases, 1e-8)
    assert any(set(cluster) == {0, 1} for cluster in clusters)
    assert any(cluster == [2] for cluster in clusters)
    assert d1.circular_distance(phases[0], phases[1]) < 1e-8


def test_synthetic_spectral_decomposition_closes_and_reconstructs_echo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = _load(PROTOCOL_PATH)
    time_value = 0.5
    shift = 0.04
    phases = np.array([time_value * shift, 0.2, -0.3], dtype=float)
    weights = np.array([0.97, 0.02, 0.01], dtype=float)
    unitary = np.diag(np.exp(1j * phases)).astype(np.complex128)
    exact_state = np.sqrt(weights).astype(np.complex128)
    echo = complex(np.sum(weights * np.exp(1j * phases)))
    exact_proxy = float(echo.imag / time_value)

    def fake_build(*_args, **_kwargs):
        return unitary.copy(), {"total": 0.0}

    monkeypatch.setattr(d1.phase_b, "_build_unitary", fake_build)
    result = d1.analyze_coordinate(
        condition="synthetic",
        time_value=time_value,
        time_hex=time_value.hex(),
        system={},
        exact_energy=0.0,
        exact_state=exact_state,
        exact_ground_residual=0.0,
        sequence=[1.0],
        saved_direct={
            "signed_direct_shift_hartree": repr(shift),
            "ground_overlap_probability": repr(weights[0]),
            "branch_selection_disagrees_with_independent_rule": "False",
        },
        saved_r1={
            "exact_echo_real": repr(echo.real),
            "exact_echo_imaginary": repr(echo.imag),
            "exact_proxy_signed_hartree": repr(exact_proxy),
        },
        allowance=1.0,
        protocol=protocol,
    )
    coordinate = result["coordinate"]
    assert coordinate["all_numerical_gates_pass"] is True
    assert coordinate["saved_branch_selection_disagreement"] is False
    assert coordinate["decomposition_closure_residual_hartree"] == pytest.approx(
        0.0, abs=1e-14
    )
    assert coordinate["exact_proxy_signed_hartree"] == pytest.approx(exact_proxy)
    assert sum(row["weight"] for row in result["components"]) == pytest.approx(1.0)
    assert len(result["top_k"]) == 10
    assert all(
        row["omitted_cluster_count"] == 0
        for row in result["top_k"]
        if row["k"] == "all"
    )


def _outcome_inputs(
    protocol: dict,
    *,
    numerical: bool = True,
    weight_actual: bool = True,
    weight_conservative: bool = True,
    oracle_actual: bool = True,
) -> tuple[list[dict], list[dict]]:
    coordinates = [
        {
            "condition": row["condition"],
            "time_hex": row["time_hex"],
            "all_numerical_gates_pass": numerical,
        }
        for row in protocol["scope"]["coordinates"]
    ]
    top_k = []
    for row in protocol["scope"]["coordinates"]:
        common = {"condition": row["condition"], "time_hex": row["time_hex"]}
        top_k.extend([
            {
                **common,
                "ranking": "weight_ranked",
                "k": 4,
                "actual_gate_pass": weight_actual,
                "conservative_gate_pass": weight_conservative,
            },
            {
                **common,
                "ranking": "oracle_contribution_ranked",
                "k": 8,
                "actual_gate_pass": oracle_actual,
                "conservative_gate_pass": False,
            },
        ])
    return coordinates, top_k


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, "d1_complete_prototype_candidate_stop"),
        (
            {"weight_conservative": False},
            "d1_complete_information_cost_limit_stop",
        ),
        (
            {"weight_actual": False, "oracle_actual": False},
            "d1_complete_close_spectral_route_stop",
        ),
        ({"numerical": False}, "failed_numerical_validation"),
    ],
)
def test_frozen_decision_tree(kwargs: dict, expected: str) -> None:
    protocol = _load(PROTOCOL_PATH)
    coordinates, top_k = _outcome_inputs(protocol, **kwargs)
    status, decision = d1.choose_outcome(protocol, coordinates, top_k)
    assert status == expected
    assert decision["d2_authorized"] is False
    assert decision["truth_free_route"]["uses_direct_truth_operationally"] is False
    assert decision["truth_free_route"]["implemented_or_validated_in_d1"] is False


def test_decision_tree_rejects_any_coordinate_substitution() -> None:
    protocol = _load(PROTOCOL_PATH)
    coordinates, top_k = _outcome_inputs(protocol)
    coordinates.pop()
    with pytest.raises(d1.PilotError, match="exact six frozen coordinates"):
        d1.choose_outcome(protocol, coordinates, top_k)
