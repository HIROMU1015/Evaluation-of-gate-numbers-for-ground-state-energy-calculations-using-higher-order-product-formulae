from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from review_response import pf_spectral_recoverability_d2 as d2
from review_response import run_pf_spectral_recoverability_d2_a_scorer as scorer


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "review_response/pf_spectral_recoverability_d2_protocol_draft.json"
AUTHORIZATION = ROOT / "review_response/pf_spectral_recoverability_d2_a_authorization.json"
PREDICTOR = ROOT / "review_response/run_pf_spectral_recoverability_d2_a_predictor.py"
SCORER = ROOT / "review_response/run_pf_spectral_recoverability_d2_a_scorer.py"


def rules(**overrides: float) -> dict[str, float | int]:
    value: dict[str, float | int] = {
        "modified_gram_schmidt_passes": 2,
        "relative_breakdown_tolerance": 1e-12,
        "overlap_ambiguity_tolerance": 1e-10,
        "energy_ambiguity_tolerance_hartree": 1e-10,
        "basis_orthogonality_frobenius_residual_maximum": 1e-10,
        "pf_action_norm_residual_maximum": 1e-10,
        "full_u_ritz_residual_maximum": 0.05,
        "full_h_ritz_residual_hartree_maximum": 0.05,
    }
    value.update(overrides)
    return value


def test_diagonal_truth_free_chain_recovers_connected_branch() -> None:
    hamiltonian = np.diag([-1.0, 1.0]).astype(np.complex128)
    time_value = 0.2
    unitary = np.diag(np.exp(1j * np.array([-1.0, 1.0]) * time_value))
    start = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    counts = {"u": 0, "h": 0}

    def apply_u(vector: np.ndarray) -> np.ndarray:
        counts["u"] += 1
        return unitary @ vector

    def apply_h(vector: np.ndarray) -> np.ndarray:
        counts["h"] += 1
        return hamiltonian @ vector

    prediction, vector = d2.analyze_coordinate(
        start=start,
        apply_u=apply_u,
        apply_h=apply_h,
        time_value=time_value,
        prefix_dimensions=[1, 2],
        primary_dimension=2,
        previous_vector=None,
        numerical_rules=rules(),
        epsilon_hartree=0.1,
        beta=1.2,
        rotations_per_step=10,
    )
    assert vector is not None
    assert counts == {"u": 2, "h": 2}
    assert prediction["claim_class"] == "empirical_estimate"
    assert prediction["abstained"] is False
    assert abs(prediction["signed_shift_estimate_hartree"]) < 1e-12
    primary = next(row for row in prediction["prefixes"] if row["dimension"] == 2)
    assert primary["h_reference_claim"] == "empirical_lowest_ritz_candidate"
    assert primary["branch_status"] == "empirical_branch_candidate"


def test_invisible_lower_block_is_not_called_certified_ground() -> None:
    hamiltonian = np.diag([-2.0, 1.0]).astype(np.complex128)
    time_value = 0.1
    unitary = np.diag(np.exp(1j * np.array([-2.0, 1.0]) * time_value))
    start = np.array([0.0, 1.0], dtype=np.complex128)
    chain = d2.build_arnoldi_chain(
        start,
        lambda vector: unitary @ vector,
        lambda vector: hamiltonian @ vector,
        maximum_dimension=1,
        reorthogonalization_passes=2,
        relative_breakdown_tolerance=1e-12,
    )
    row, _ = d2.analyze_prefix(
        chain,
        1,
        time_value,
        previous_vector=None,
        overlap_ambiguity_tolerance=1e-10,
        energy_ambiguity_tolerance_hartree=1e-10,
    )
    assert row["h_reference_energy_hartree"] == pytest.approx(1.0)
    assert row["h_reference_claim"] == "empirical_lowest_ritz_candidate"
    assert "certified" not in row["h_reference_claim"]


def test_exact_breakdown_does_not_restart_or_hide_action_counts() -> None:
    counts = {"u": 0, "h": 0}
    start = np.array([1.0, 0.0], dtype=np.complex128)

    def apply_u(vector: np.ndarray) -> np.ndarray:
        counts["u"] += 1
        return vector.copy()

    def apply_h(vector: np.ndarray) -> np.ndarray:
        counts["h"] += 1
        return vector.copy()

    chain = d2.build_arnoldi_chain(
        start,
        apply_u,
        apply_h,
        maximum_dimension=8,
        reorthogonalization_passes=2,
        relative_breakdown_tolerance=1e-12,
    )
    assert chain.breakdown is True
    assert chain.dimension == 1
    assert counts == {"u": 1, "h": 1}


def test_equal_branch_scores_are_indeterminate() -> None:
    hamiltonian = np.zeros((2, 2), dtype=np.complex128)
    time_value = 0.2
    unitary = np.diag(np.exp(1j * np.array([-0.5, 0.5]) * time_value))
    start = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    chain = d2.build_arnoldi_chain(
        start,
        lambda vector: unitary @ vector,
        lambda vector: hamiltonian @ vector,
        maximum_dimension=2,
        reorthogonalization_passes=2,
        relative_breakdown_tolerance=1e-12,
    )
    row, _ = d2.analyze_prefix(
        chain,
        2,
        time_value,
        previous_vector=None,
        overlap_ambiguity_tolerance=1e-10,
        energy_ambiguity_tolerance_hartree=1e-10,
    )
    assert row["overlap_ambiguous"] is True
    assert row["branch_status"] == "branch_indeterminate"


def test_prefixes_share_one_chain_and_stay_within_eight_actions() -> None:
    phases = np.linspace(-0.7, 0.7, 8)
    unitary = np.diag(np.exp(1j * phases))
    hamiltonian = np.diag(np.linspace(-2.0, 2.0, 8)).astype(np.complex128)
    start = np.arange(1, 9, dtype=np.complex128)
    start /= np.linalg.norm(start)
    counts = {"u": 0, "h": 0}

    def apply_u(vector: np.ndarray) -> np.ndarray:
        counts["u"] += 1
        return unitary @ vector

    def apply_h(vector: np.ndarray) -> np.ndarray:
        counts["h"] += 1
        return hamiltonian @ vector

    prediction, _ = d2.analyze_coordinate(
        start=start,
        apply_u=apply_u,
        apply_h=apply_h,
        time_value=0.3,
        prefix_dimensions=[1, 2, 4, 8],
        primary_dimension=8,
        previous_vector=None,
        numerical_rules=rules(
            full_u_ritz_residual_maximum=2.0,
            full_h_ritz_residual_hartree_maximum=2.0,
        ),
        epsilon_hartree=10.0,
        beta=1.2,
        rotations_per_step=10,
    )
    assert counts == {"u": 8, "h": 8}
    assert [row["dimension"] for row in prediction["prefixes"]] == [1, 2, 4, 8]


@pytest.mark.parametrize(
    ("branch_count", "abstained", "unsafe", "lower", "expected"),
    [
        (6, 0, 0, 1, "d2_a_complete_prototype_candidate_stop"),
        (6, 2, 0, 0, "d2_a_complete_information_cost_limit_stop"),
        (5, 0, 0, 6, "d2_a_complete_close_spectral_route_stop"),
    ],
)
def test_scoring_statuses_are_mutually_exclusive_and_stop(
    branch_count: int,
    abstained: int,
    unsafe: int,
    lower: int,
    expected: str,
) -> None:
    rows = []
    for index in range(6):
        rows.append({
            "branch_correct": index < branch_count,
            "abstained": index < abstained,
            "frozen_budget_safe": False if index < unsafe else True,
            "quantum_budget_lower_than_main_baseline": index < lower,
        })
    status, summary = scorer.choose_status(rows)
    assert status == expected
    assert summary["coordinate_count"] == 6


def test_protocol_separates_three_k_symbols_and_keeps_d2b_closed() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["notation"]["forbid_symbol_collision"] is True
    assert protocol["prediction_and_budget"]["qpe_rotation_constant_symbol"] == "K_current_m3"
    assert protocol["completion"]["d2_b_authorized"] is False
    text = json.dumps(protocol, sort_keys=True)
    assert "beta*K/(t*B)" not in text


def test_authorization_is_one_run_and_no_d2b() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    assert authorization["authorization"]["maximum_completed_predictor_runs"] == 1
    assert authorization["authorization"]["maximum_completed_scorer_runs"] == 1
    assert authorization["not_authorized"]["d2_b"] is True
    assert authorization["not_authorized"]["truth_access_before_prediction_freeze"] is True


def test_predictor_import_graph_and_paths_exclude_truth() -> None:
    source = PREDICTOR.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not any("phase_b" in value for value in imported)
    assert not any("scorer" in value for value in imported)
    assert "direct_points.csv" not in source
    assert "coordinate_summary.csv" not in source
    assert "exact_ground_pair" not in source
    assert "_build_unitary" not in source
    scorer_source = SCORER.read_text(encoding="utf-8")
    assert "direct_points.csv" in scorer_source
    assert "coordinate_summary.csv" in scorer_source


def test_prediction_hash_tamper_is_rejected(tmp_path: Path) -> None:
    prediction = tmp_path / "prediction.json"
    prediction.write_text(json.dumps({
        "status": "d2_a_prediction_frozen_truth_not_opened",
        "truth_open_count": 0,
        "predictions": [{}, {}, {}, {}, {}, {}],
    }) + "\n", encoding="utf-8")
    digest = hashlib.sha256(prediction.read_bytes()).hexdigest()
    (tmp_path / "prediction.sha256").write_text(
        f"{digest}  prediction.json\n", encoding="utf-8"
    )
    (tmp_path / "PREDICTION_FROZEN.json").write_text(json.dumps({
        "prediction_sha256": digest,
        "scoring_authorized_only_after_this_marker": True,
    }) + "\n", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "files": [{
            "path": "prediction.json",
            "bytes": prediction.stat().st_size,
            "sha256": digest,
        }],
    }) + "\n", encoding="utf-8")
    loaded, actual = scorer.verify_prediction(tmp_path)
    assert actual == digest
    assert loaded["truth_open_count"] == 0
    prediction.write_text("{}\n", encoding="utf-8")
    with pytest.raises(scorer.ScorerError, match="manifest mismatch"):
        scorer.verify_prediction(tmp_path)
