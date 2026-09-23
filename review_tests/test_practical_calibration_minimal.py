from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.linalg import expm
from scipy.sparse import csr_matrix

import run_practical_calibration_minimal as pcm
from trotterlib.component_sector_pf import diagonalize_components
from trotterlib.pf_decomposition import iter_s2_sequence_steps


def test_protocol_hash_and_fixed_rules() -> None:
    freeze = json.loads(
        Path("review_response/practical_calibration_phase_a_freeze.json").read_text()
    )
    assert hashlib.sha256(pcm.PROTOCOL_PATH.read_bytes()).hexdigest() == freeze["protocol_sha256"]
    protocol = pcm._protocol()
    assert protocol["time_coordinate_policy"]["maximum_relative_time_difference"] == 0.005
    assert protocol["selector"]["cancellation_index"]["primary_relative_to_proxy_t_ana"] == 0.1
    assert protocol["selector"]["cancellation_index"]["robustness_is_selection_inert"] is True
    assert protocol["selector"]["sentinel"]["relative_to_proxy_t_ana"] == 0.5
    assert protocol["oracle_barrier"]["new_direct_truth_point_count"] == 0


def test_sanitized_allowlist_rejects_forbidden_fields() -> None:
    allowed = {
        "schema": pcm.SANITIZED_SCHEMA,
        "condition": "synthetic",
        "protocol_sha256": "a" * 64,
        "source_pickle_sha256": "b" * 64,
        "hamiltonian_sha256": "c" * 64,
        "hamiltonian": object(),
        "component_spectra": [],
        "term_counts": [],
        "cisd_state": np.asarray([1.0]),
    }
    assert pcm._forbidden_key_paths(allowed) == []
    assert pcm._forbidden_key_paths({**allowed, "exact_ground_state": [1.0]})
    assert pcm._forbidden_key_paths({**allowed, "direct_truth": 0.0})


def test_selector_signature_has_no_truth_or_source_path() -> None:
    parameters = set(inspect.signature(pcm.run_selector).parameters)
    assert parameters == {"output_dir"}
    source = inspect.getsource(pcm.run_selector)
    assert "h01_root" not in source
    assert "p03_root" not in source


def test_formula_sequences_match_existing_registry() -> None:
    for formula in pcm.FORMULAE:
        expected = pcm._protocol()["formulae"][formula]["s2_sequence"]
        assert pcm._formula_sequence(formula) == expected


def test_cpu_component_action_matches_dense_unitary() -> None:
    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    z = np.asarray([[0.7, 0.0], [0.0, -0.7]], dtype=np.complex128)
    groups = [x, z]
    spectra = [diagonalize_components(csr_matrix(group)) for group in groups]
    sequence = [0.31, -0.17, 0.31]
    state = np.asarray([1.0, 1.0j], dtype=np.complex128) / np.sqrt(2.0)
    time_value = 0.23
    actual, _ = pcm.h01._apply_pf_cpu(
        {"component_spectra": spectra}, sequence, time_value, state[:, None]
    )
    expected = state.copy()
    for group_index, weight in iter_s2_sequence_steps(len(groups), sequence):
        expected = expm(1j * time_value * weight * groups[group_index]) @ expected
    assert np.linalg.norm(actual[:, 0] - expected) < 2e-14


def test_cancellation_index_distinguishes_diagonal_and_offdiagonal_error() -> None:
    delta = 1e-4
    exact = np.asarray([1.0, 0.0], dtype=np.complex128)
    diagonal = np.asarray([np.exp(1j * delta), 0.0], dtype=np.complex128)
    offdiagonal = np.asarray([np.cos(delta), np.sin(delta)], dtype=np.complex128)
    diagonal_index = abs(np.vdot(exact, diagonal).imag) / np.linalg.norm(diagonal - exact)
    offdiagonal_index = abs(np.vdot(exact, offdiagonal).imag) / np.linalg.norm(offdiagonal - exact)
    assert diagonal_index > 0.99
    assert offdiagonal_index == 0.0


def test_fallback_constraint_and_pf_rejection() -> None:
    model = {"coefficient_powers": [4, 6], "coefficient_values": [1e-3, 1e-3]}
    optimum = pcm._model_optimum(model, 1.0, 10, maximum_relative=0.5)
    assert optimum is not None
    assert optimum["relative_to_proxy_t_ana"] <= 0.5
    infeasible = {"coefficient_powers": [0], "coefficient_values": [1.0]}
    assert pcm._model_optimum(infeasible, 1.0, 10, maximum_relative=0.5) is None


def test_both_rejected_yields_abstention(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pcm._write_json(tmp_path / "sanitized_input_manifest.json", {
        "truth_paths_exposed_to_selector": False,
        "entries": [{"condition": "synthetic", "sanitized_sha256": "x"}],
    })
    monkeypatch.setattr(pcm, "_load_sanitized", lambda *_: {})
    monkeypatch.setattr(pcm, "_proxy_analytic_scale", lambda *args, **kwargs: (None, {"qualified": False}, []))
    monkeypatch.setattr(pcm, "_formula_sequence", lambda formula: [1.0])
    monkeypatch.setattr(pcm, "_rotation_count", lambda *args: 1)
    monkeypatch.setattr(pcm, "_git_output", lambda *args: "f" * 40)
    monkeypatch.setattr(pcm, "_conditions", lambda protocol: ["synthetic"])
    protocol = pcm._protocol()
    protocol["conditions"] = {"primary": ["synthetic"], "stress_test": []}
    monkeypatch.setattr(pcm, "_protocol", lambda: protocol)
    predictions = pcm.run_selector(tmp_path)
    assert predictions["conditions"][0]["selection"]["status"] == "abstain"


def test_scorer_requires_freeze_and_rejects_hash_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "predictions.json").write_text("{}\n")
    with pytest.raises(pcm.FreezeError, match="SELECTION_FROZEN"):
        pcm.verify_freeze(tmp_path)
    monkeypatch.setattr(pcm, "_git_output", lambda *args: "f" * 40)
    pcm.freeze_predictions(tmp_path)
    (tmp_path / "predictions.json").write_text('{"changed": true}\n')
    with pytest.raises(pcm.FreezeError, match="hash mismatch"):
        pcm.verify_freeze(tmp_path)


def test_completed_proxy_point_is_reused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}
    def fake_point(*args):
        calls["count"] += 1
        return {"time": 0.2, "echo_imag_hartree": 1e-8}
    monkeypatch.setattr(pcm, "proxy_point", fake_point)
    counters = {"computed": 0, "reused": 0}
    first = pcm._cached_proxy_point(
        tmp_path, "c", "f", "p", {}, [], 0.2, "s", counters
    )
    second = pcm._cached_proxy_point(
        tmp_path, "c", "f", "p", {}, [], 0.2, "s", counters
    )
    assert first == second
    assert calls["count"] == 1
    assert counters == {"computed": 1, "reused": 1}


def test_new_direct_truth_is_structurally_zero() -> None:
    protocol = pcm._protocol()
    assert protocol["oracle_barrier"]["new_direct_truth_point_count"] == 0
    source = inspect.getsource(pcm.run_scorer)
    assert "_direct_point" not in source
    assert "interpol" not in source.lower()


def test_output_bootstrap_accepts_only_driver_logs(tmp_path: Path) -> None:
    accepted = tmp_path / "accepted"
    accepted.mkdir()
    (accepted / "driver.log").write_text("driver started\n")
    (accepted / "computation.log").write_text("")
    pcm._prepare_output_directory(accepted)
    assert (accepted / ".gitignore").read_text() == ".runtime/\ndriver.log\n"

    rejected = tmp_path / "rejected"
    rejected.mkdir()
    (rejected / "unexpected.txt").write_text("must be rejected\n")
    with pytest.raises(FileExistsError, match="refusing non-empty output"):
        pcm._prepare_output_directory(rejected)
