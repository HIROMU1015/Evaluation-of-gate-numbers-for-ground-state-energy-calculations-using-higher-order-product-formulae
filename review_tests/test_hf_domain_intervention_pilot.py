from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import pickle
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from review_response import hf_domain_intervention_pilot as pilot
from review_response import run_hf_domain_intervention_prepare as prepare
from review_response import run_hf_domain_intervention_predictor as predictor
from trotterlib.component_sector_pf import diagonalize_components


ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "docs/second_study_v2/hf_domain_protocol_20260930/second_study_v2_hf_domain_protocol.json"
AUTH = ROOT / "review_response/hf_domain_intervention_pilot_execution_authorization.json"
PREDICTOR = ROOT / "review_response/run_hf_domain_intervention_predictor.py"
SCORER = ROOT / "review_response/run_hf_domain_intervention_scorer.py"


def test_authorization_closes_all_six_execution_blockers() -> None:
    authorization = json.loads(AUTH.read_text())
    assert hashlib.sha256(P0.read_bytes()).hexdigest() == authorization["parent_protocol"]["sha256"]
    resolved = authorization["resolved_execution_blockers"]
    assert resolved["eta"] == {
        "approved": True,
        "post_result_change_forbidden": True,
        "value": 0.1,
    }
    assert resolved["budget"]["budget_model"] == "continuous_rotation_cost_proxy"
    assert resolved["budget"]["discrete_budget_model"] == "not_defined_in_inherited_study"
    assert resolved["resource_envelope"]["spectral_arm_wall_seconds_maximum"] == 1800
    assert resolved["resource_envelope"]["local_proxy_arm_wall_seconds_maximum"] == 1800
    assert resolved["resource_envelope"]["peak_memory_bytes_maximum"] == 4 * 1024**3
    assert resolved["truth"]["new_cap_exterior_direct_coordinates_maximum"] == 4
    assert resolved["truth"]["authorized_only_after_prediction_freeze"] is True


def test_continuous_budget_and_target_allowance_match_frozen_arithmetic() -> None:
    epsilon = 0.00015936001019904
    beta = 1.2
    rotations = 9108
    t0 = 0.148871685974198
    b0 = 468461625.7375308
    budget = pilot.continuous_budget(
        beta=beta, rotations=rotations, time_value=t0,
        error_hartree=1.0751001536769666e-06,
        epsilon_hartree=epsilon,
    )
    assert budget == pytest.approx(463823391.8193374)
    allowance = pilot.target_allowance(
        epsilon_hartree=epsilon, beta=beta, rotations=rotations,
        time_value=1.3 * t0, baseline_budget=b0, eta=0.1,
    )
    assert allowance == pytest.approx(2.5413230098030428e-05)


def test_m1_selection_uses_only_eligible_exterior_and_falls_back() -> None:
    prediction = {
        "e_use_hartree": 1e-5,
        "abstained": False,
        "failure_reasons": [],
        "signed_shift_estimate_hartree": 2e-6,
        "empirical_width_hartree": 8e-6,
    }
    exterior = pilot.m1_arm_row(
        candidate_id="x", time_value=0.2, factor_of_t0=1.3,
        prediction=prediction, allowance_hartree=2e-5,
        beta=1.2, rotations=9108, epsilon_hartree=1.6e-4,
    )
    control = pilot.m1_arm_row(
        candidate_id="t0", time_value=0.15, factor_of_t0=1.0,
        prediction=prediction, allowance_hartree=-1e-6,
        beta=1.2, rotations=9108, epsilon_hartree=1.6e-4,
    )
    selected = pilot.select_condition(
        [control, exterior], arm="M1_fixed_D2A_spectral", gamma=None,
        fallback_candidate_id="t0", fallback_time=0.15,
        fallback_budget=4e8,
    )
    assert selected["selected_candidate"] == "x"
    assert selected["fallback"] is False
    exterior["eligible"] = False
    fallback = pilot.select_condition(
        [control, exterior], arm="M1_fixed_D2A_spectral", gamma=None,
        fallback_candidate_id="t0", fallback_time=0.15,
        fallback_budget=4e8,
    )
    assert fallback["fallback"] is True
    assert fallback["frozen_continuous_budget"] == 4e8


def test_local_proxy_gamma_is_budget_margin_not_error_margin() -> None:
    rows = pilot.b1_arm_rows(
        candidate_id="x", time_value=0.2, factor_of_t0=1.3,
        signed_proxy_hartree=-2e-6, allowance_hartree=3e-5,
        gammas=[1.01, 1.10], beta=1.2, rotations=9108,
        epsilon_hartree=1.6e-4,
    )
    assert rows[0]["proxy_error_hartree"] == 2e-6
    assert rows[1]["continuous_budget"] / rows[0]["continuous_budget"] == pytest.approx(1.10 / 1.01)


def test_representation_independent_branch_and_t0_control() -> None:
    assert pilot.physical_branch_correct(
        predicted_shift_hartree=5e-6, direct_shift_hartree=5.1e-6,
        truth_phase_gap_radians=0.02, time_value=0.2,
    )
    assert pilot.t0_reproduction_pass(
        abstained=False, branch_correct=True,
        predicted_shift_hartree=5e-6, width_hartree=2e-7,
        direct_shift_hartree=5.1e-6,
    )
    assert not pilot.t0_reproduction_pass(
        abstained=True, branch_correct=True,
        predicted_shift_hartree=5e-6, width_hartree=2e-7,
        direct_shift_hartree=5.1e-6,
    )


def base_score(**changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "evaluable": True,
        "T0_reproduction_pass": True,
        "selected_branch_valid": True,
        "unsafe_selected_intervention": False,
        "cheap_proxy_matches_or_dominates": False,
        "spectral_strong_signal": False,
        "fixed_width_blocked": False,
    }
    row.update(changes)
    return row


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ([base_score(evaluable=False), base_score()], "not_evaluable_source_or_truth"),
        ([base_score(T0_reproduction_pass=False), base_score()], "reference_or_branch_failure"),
        ([base_score(unsafe_selected_intervention=True), base_score()], "unsafe_frozen_budget"),
        ([base_score(cheap_proxy_matches_or_dominates=True), base_score()], "cheap_proxy_sufficient"),
        ([base_score(spectral_strong_signal=True), base_score(spectral_strong_signal=True)], "robust_signal"),
        ([base_score(spectral_strong_signal=True), base_score()], "limited_signal"),
        ([base_score(fixed_width_blocked=True), base_score()], "fixed_width_no_benefit"),
        ([base_score(), base_score()], "no_benefit_on_frozen_grid"),
    ],
)
def test_completion_status_priority(rows: list[dict[str, object]], expected: str) -> None:
    assert pilot.choose_completion_status(rows) == expected


def test_prediction_freeze_rejects_tamper(tmp_path: Path) -> None:
    prediction = tmp_path / "prediction.json"
    prediction.write_text('{"truth_open_count": 0}\n')
    digest = hashlib.sha256(prediction.read_bytes()).hexdigest()
    (tmp_path / "prediction.sha256").write_text(f"{digest}  prediction.json\n")
    (tmp_path / "PREDICTION_FROZEN.json").write_text(json.dumps({"prediction_sha256": digest}) + "\n")
    assert pilot.verify_prediction_files(tmp_path)[1] == digest
    prediction.write_text('{"truth_open_count": 1}\n')
    with pytest.raises(pilot.HFPilotError, match="hash mismatch"):
        pilot.verify_prediction_files(tmp_path)


def test_preflight_adapter_excludes_exact_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_root = tmp_path / "source"
    output_root = tmp_path / "sanitized"
    (cache_root / "cache").mkdir(parents=True)
    fake = {
        "protocol_sha256": "p",
        "hamiltonian_sha256": "h",
        "hamiltonian": csr_matrix(np.eye(2)),
        "component_spectra": [],
        "term_counts": [],
        "states": {"cisd": np.array([1.0, 0.0]), "exact_ground": np.array([0.0, 1.0])},
        "state": np.array([0.0, 1.0]),
        "energy": -1.0,
    }
    for condition in prepare.CONDITIONS:
        path = cache_root / "cache" / f"{condition}.pkl"
        path.write_bytes(b"placeholder")
        (cache_root / "cache" / f"{condition}.metadata.json").write_text("{}\n")
    authorization = json.loads(AUTH.read_text())
    auth_path = tmp_path / "authorization.json"
    auth_path.write_text(json.dumps(authorization))
    expected_hashes = authorization["resolved_execution_blockers"]["cache_preflight"]["pickle_sha256"]
    expected_h = authorization["resolved_execution_blockers"]["cache_preflight"]["hamiltonian_sha256"]
    monkeypatch.setattr(
        prepare,
        "sha256_file",
        lambda path: expected_hashes[path.stem] if path.suffix == ".pkl" else "x",
    )
    def fake_load(path: Path) -> dict[str, object]:
        value = dict(fake)
        value["hamiltonian_sha256"] = expected_h[path.stem]
        return value
    monkeypatch.setattr(prepare.h01, "_load_system", fake_load)
    manifest = prepare.sanitize(cache_root, output_root, auth_path)
    assert manifest["direct_truth_count"] == 0
    for entry in manifest["entries"]:
        with (output_root / entry["sanitized_relative_path"]).open("rb") as stream:
            sanitized = pickle.load(stream)
        assert set(sanitized) == prepare.ALLOWED
        assert "exact_ground" not in sanitized
        assert "state" not in sanitized
        assert "energy" not in sanitized


def test_predictor_source_has_no_truth_loader_and_scorer_has_freeze_gate() -> None:
    predictor = PREDICTOR.read_text()
    tree = ast.parse(predictor)
    imported = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not any("scorer" in value for value in imported)
    assert "direct_points" not in predictor
    assert "exact_ground" not in predictor
    assert "np.linalg.eigh" not in predictor
    scorer = SCORER.read_text()
    assert scorer.index("verify_committed_prediction") < scorer.index("load_truth_systems")
    assert "computed >= 4" in scorer
    assert "nearest_coordinate_substitution" in scorer



def test_truth_free_predictor_synthetic_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sanitized_root = tmp_path / "sanitized"
    runtime = sanitized_root / ".runtime" / "sanitized"
    runtime.mkdir(parents=True)
    hamiltonian = csr_matrix(np.diag([-1.0, 1.0]).astype(np.complex128))
    spectra = [diagonalize_components(hamiltonian)]
    state = np.asarray([1.0, 1e-3], dtype=np.complex128)
    state /= np.linalg.norm(state)
    entries = []
    for condition in predictor.CONDITIONS:
        system = {
            "schema": "hf_domain_intervention_sanitized_system_v1",
            "condition": condition,
            "source_pickle_sha256": condition,
            "protocol_sha256": "synthetic",
            "hamiltonian_sha256": "synthetic",
            "hamiltonian": hamiltonian,
            "component_spectra": spectra,
            "term_counts": [1],
            "cisd_state": state,
        }
        path = runtime / f"{condition}.pkl"
        with path.open("wb") as stream:
            pickle.dump(system, stream)
        entries.append({
            "condition": condition,
            "sanitized_relative_path": str(path.relative_to(sanitized_root)),
            "sanitized_sha256": pilot.sha256_file(path),
            "source_pickle_sha256": condition,
        })
    (sanitized_root / "sanitized_input_manifest.json").write_text(json.dumps({
        "authorization_sha256": pilot.sha256_file(AUTH),
        "entries": entries,
    }) + "\n")
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        monkeypatch.setenv(name, "1")
    output = tmp_path / "prediction"
    payload = predictor.run(SimpleNamespace(
        project_root=ROOT,
        p0_protocol=P0,
        authorization=AUTH,
        source_contract=ROOT / "docs/second_study_v2/hf_domain_protocol_20260930/source_and_coordinate_contract.json",
        candidate_plan=ROOT / "docs/second_study_v2/hf_domain_protocol_20260930/hf_domain_candidate_plan.csv",
        sanitized_root=sanitized_root,
        processes=1,
        output_dir=output,
    ))
    assert payload["truth_open_count"] == 0
    assert payload["direct_truth_count"] == 0
    assert len(payload["conditions"]) == 2
    assert sum(len(row["candidates"]) for row in payload["conditions"]) == 6
    assert (output / "PREDICTION_FROZEN.json").is_file()
    assert pilot.verify_prediction_files(output)[0]["status"] == "hf_domain_prediction_frozen_truth_not_opened"
