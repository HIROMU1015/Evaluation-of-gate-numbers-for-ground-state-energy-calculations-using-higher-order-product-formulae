from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from review_response import audit_d03_target_accuracy_dependence as d03
from review_response import run_d03_target_accuracy_followup as runner


def test_frozen_input_hashes_match() -> None:
    for path, expected in runner.EXPECTED_SHA256.items():
        assert runner.sha256(path) == expected


def test_stage1_manifest_is_exactly_the_authorized_subset() -> None:
    rows = runner.selected_stage1_rows()
    assert len(rows) == 138
    assert {row["target_name"] for row in rows} == {"CA", "CA_div_100"}
    assert all(row["point_role"] == "direct_coarse_validation" for row in rows)
    assert all(row["recommended_stage1"] is True for row in rows)
    assert not any(row["point_role"] == "optional_target_specific_refit_training" for row in rows)
    assert not any(row["target_name"] == "CA_div_10" for row in rows)


def test_requested_time_is_preserved_in_physical_plan() -> None:
    protocol = runner.read_json(runner.PROTOCOL)
    gates = runner.read_json(runner.GATES)
    rows = runner.selected_stage1_rows()
    plan = runner.make_plan(protocol, gates)
    observed = sorted(
        float(request["requested_time"])
        for point in plan["points"]
        for request in point["logical_requests"]
    )
    assert observed == sorted(float(row["requested_time"]) for row in rows)
    assert plan["logical_point_count"] == 138


def test_time_matching_uses_both_frozen_tolerances() -> None:
    gates = runner.read_json(runner.GATES)
    base = 0.75
    assert runner.same_time(base, base * (1.0 + 1.0e-12), gates)
    assert not runner.same_time(base, base * (1.0 + 4.0e-12), gates)
    assert runner.same_time(0.0, 0.5e-14, gates)
    assert not runner.same_time(0.0, 2.0e-14, gates)


def test_qpe_cost_does_not_clip_infeasible_budget() -> None:
    assert d03.qpe_cost(1.0, 0.01, 10, 0.01, 1.2) is None
    assert d03.qpe_cost(1.0, 0.02, 10, 0.01, 1.2) is None
    assert d03.qpe_cost(1.0, 0.005, 10, 0.01, 1.2) == 2400.0


def test_resume_requires_status_key_and_all_fields(tmp_path: Path) -> None:
    path = tmp_path / "point.json"
    payload = {field: 0 for field in runner.REQUIRED_POINT_FIELDS}
    payload.update({"status": "complete", "cache_key": "expected"})
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert runner.valid_resume(path, "expected")
    assert not runner.valid_resume(path, "different")
    del payload["formula"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert not runner.valid_resume(path, "expected")


def test_component_spectrum_action_matches_dense_matrix() -> None:
    theta = 0.37
    vectors = np.asarray(
        [[[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]],
        dtype=np.complex128,
    )
    values = np.asarray([[1.5, -0.25]])
    batch = SimpleNamespace(
        indices=np.asarray([[0, 1]]), eigenvalues=values, eigenvectors=vectors
    )
    spectrum = SimpleNamespace(batches=(batch,))
    state = np.asarray([0.6 + 0.1j, -0.2 + 0.7j])
    dense = vectors[0] @ np.diag(values[0]) @ vectors[0].conj().T
    np.testing.assert_allclose(runner.spectrum_action(spectrum, state), dense @ state)


def test_execution_protocol_forbids_refit_and_boundary_expansion() -> None:
    execution = runner.read_json(runner.EXECUTION)
    assert execution["forbidden_new_points"]["optional_target_specific_refit_training"] == 0
    assert execution["forbidden_new_points"]["CA_div_10"] == 0
    assert execution["stage2"]["do_not_expand_boundary"] is True
    assert execution["cost"]["infeasible_error_budget_is_not_clipped"] is True
