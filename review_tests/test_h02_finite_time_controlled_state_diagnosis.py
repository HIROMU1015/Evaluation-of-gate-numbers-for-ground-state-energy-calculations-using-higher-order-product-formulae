from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

import run_h02_finite_time_controlled_state_diagnosis as h02


ARTIFACT = Path(
    "artifacts/h02_finite_time_controlled_state_20260922_568f002"
)


def test_h02_fixed_protocol_hash_and_scope() -> None:
    observed = hashlib.sha256(h02.PROTOCOL_PATH.read_bytes()).hexdigest()
    assert observed == h02.EXPECTED_PROTOCOL_SHA256
    protocol = h02._protocol()
    assert protocol["formulae"] == ["current_m3", "yoshida4"]
    assert len(protocol["conditions"]) == 4
    assert protocol["calibration"]["model_powers"] == [4, 6]
    assert protocol["source"]["direct_truth_policy"].startswith("Reuse H01")


def test_controlled_phase_states_have_identical_scalar_quality() -> None:
    hamiltonian = np.diag([-1.0, 2.0]).astype(np.complex128)
    ground = np.asarray([1.0, 0.0], dtype=np.complex128)
    direction = np.asarray([0.0, 1.0], dtype=np.complex128)
    rows = []
    for phase in (0.0, 0.5 * np.pi, np.pi, 1.5 * np.pi):
        state = h02.controlled_state(ground, direction, 0.1, phase)
        rows.append(h02.state_metrics(hamiltonian, state, ground, -1.0))
    for key in (
        "energy_error_hartree",
        "energy_variance_hartree2",
        "hamiltonian_residual_2_norm",
        "exact_ground_overlap_probability",
    ):
        assert np.ptp([row[key] for row in rows]) < 1e-14


def test_orthogonal_component_removes_ground_and_preserves_direction() -> None:
    ground = np.asarray([1.0, 0.0], dtype=np.complex128)
    approximate = np.asarray([1.0j, 0.2], dtype=np.complex128)
    approximate /= np.linalg.norm(approximate)
    direction, overlap = h02.orthogonal_component(ground, approximate)
    assert abs(np.vdot(ground, direction)) < 1e-14
    assert np.isclose(np.linalg.norm(direction), 1.0)
    assert 0.0 < overlap < 1.0


def test_h02_local_reconstruction_failure_is_not_complete() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (ARTIFACT / "manifest.json").read_text(encoding="utf-8")
    )
    assert audit["status"] == "failed_numerical_validation"
    assert audit["checks_passed"] is False
    assert audit["checks"]["exact_echo_reproduction"] is False
    assert not (ARTIFACT / "COMPLETE").exists()
    assert audit["scope"]["new_direct_pf_points"] == 0
    assert audit["summary"]["controlled_state_count"] == 128
    assert audit["summary"]["proxy_model_count"] == 256
    assert audit["summary"]["phase_group_count"] == 32
    assert audit["summary"][
        "scalar_metrics_sufficient_for_finite_time_calibration"
    ] is None
    for path_text, expected in manifest["artifact_files"].items():
        path = Path(path_text)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
