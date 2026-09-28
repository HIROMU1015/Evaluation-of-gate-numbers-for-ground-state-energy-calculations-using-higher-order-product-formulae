from __future__ import annotations

import copy
import inspect
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from review_response import second_study_safe_time_domain_execution as execution
from review_response import second_study_safe_time_domain_guard as guard
from review_response import run_second_study_safe_time_domain_phase_a as phase_a
from review_response import run_second_study_safe_time_domain_phase_b as phase_b


def _protocol() -> dict:
    return guard.load_protocol()[0]


def _observations(
    coefficient: float = 1.0e-5,
    *,
    fallback: bool = True,
) -> dict[float, dict[str, float]]:
    protocol = _protocol()
    relative = {
        0.05,
        0.1,
        0.2,
        0.3,
        0.5,
        *protocol["phase_a"]["extension"][
            "candidate_sequence_relative_to_t_ana"
        ],
    }
    rows = {
        float(value): {
            "proxy_hartree": coefficient * float(value) ** 4,
            "cancellation_index": 0.5,
        }
        for value in relative
    }
    rows[0.1]["cancellation_index"] = 0.01 if fallback else 0.5
    return rows


def _strategy(
    name: str,
    time_value: float,
    *,
    budget: float = 1.0e8,
    extension_selected: bool = False,
) -> dict:
    return {
        "strategy": name,
        "status": "selected",
        "selected_time_hartree_inverse": time_value,
        "selected_relative_to_t_ana": time_value,
        "predicted_signed_shift_hartree": 1.0e-6,
        "predicted_error_hartree": 1.0e-6,
        "guarded_error_hartree": 1.0e-6,
        "predicted_required_pauli_rotations": budget / 1.01,
        "frozen_pauli_rotation_budget": budget,
        "rotation_count_per_pf_step": 100,
        "selection_source": "synthetic",
        "operational": name != "uncapped_counterfactual",
        "extension_selected": extension_selected,
    }


def _predictions(selected_time: float = 0.65) -> dict:
    protocol, protocol_sha = guard.load_protocol()
    rows = []
    for item in protocol["data_partition"]["independent_evaluation"][
        "conditions"
    ]:
        strategies = {
            name: _strategy(
                name,
                selected_time,
                budget=8.0e7 if name == "multiple_window_rule" else 1.0e8,
                extension_selected=name == "multiple_window_rule",
            )
            for name in guard.STRATEGIES
        }
        rows.append(
            {
                "condition": item["name"],
                "proxy_analytic_time_hartree_inverse": 1.0,
                "strategies": strategies,
                "information_counts": {
                    "multiple_window_rule": {"proxy_points": 7},
                    "equal_information_pooled_fit": {"proxy_points": 7},
                },
            }
        )
    return {
        "schema": execution.PHASE_A_SCHEMA,
        "protocol_sha256": protocol_sha,
        "oracle_access": {key: 0 for key in guard.ORACLE_ACCESS_COUNTERS},
        "conditions": rows,
    }


def test_phase_a_source_has_no_truth_eigensolver_or_direct_builder() -> None:
    source = Path(phase_a.__file__).read_text(encoding="utf-8")
    assert "eigh(" not in source
    assert "eigsh(" not in source
    assert "schur(" not in source
    assert "_build_gpu(" not in source
    assert "_build_cpu(" not in source
    assert "def exact_" not in source


def test_formula_identity_is_protocol_derived() -> None:
    protocol = _protocol()
    assert execution.formula_sequence(protocol) == tuple(
        protocol["formula"]["s2_sequence"]
    )
    changed = copy.deepcopy(protocol)
    changed["scope"]["formulae"] = ["another_pf"]
    with pytest.raises(execution.ExecutionError, match="PF scope"):
        execution.formula_sequence(changed)


def test_multiple_window_rule_uses_extension_and_pooled_uses_same_points() -> None:
    short_points = [
        {"time_hartree_inverse": 0.025, "proxy_hartree": 1.0e-5 * 0.025**4},
        {"time_hartree_inverse": 0.04, "proxy_hartree": 1.0e-5 * 0.04**4},
    ]
    strategies, diagnostic = execution.select_phase_a_strategies(
        t_ana=1.0,
        observations_by_relative_time=_observations(),
        pooled_extra_points=short_points,
        rotations=100,
        protocol=_protocol(),
    )
    assert diagnostic["fallback_triggered"] is True
    assert diagnostic["extension_stop_reason"] is None
    assert diagnostic["acquired_extension_relative_times"] == [
        0.65,
        0.8,
        0.95,
        1.1,
        1.25,
        1.4,
        1.55,
        1.7,
    ]
    assert 0.05 in diagnostic["pooled_training_relative_times"]
    assert 0.025 in diagnostic["pooled_training_absolute_times"]
    assert 0.04 in diagnostic["pooled_training_absolute_times"]
    assert strategies["multiple_window_rule"]["extension_selected"] is True
    assert (
        strategies["multiple_window_rule"]["selected_time_hartree_inverse"]
        > 0.5
    )
    assert strategies["uncapped_counterfactual"]["operational"] is False


def test_multiple_window_stops_at_first_failure_and_hides_later_points() -> None:
    rows = _observations()
    rows[0.65]["proxy_hartree"] *= -50.0
    strategies, diagnostic = execution.select_phase_a_strategies(
        t_ana=1.0,
        observations_by_relative_time=rows,
        rotations=100,
        protocol=_protocol(),
    )
    assert diagnostic["acquired_extension_relative_times"] == [0.65]
    assert diagnostic["extension_stop_reason"] is not None
    assert (
        strategies["multiple_window_rule"]["status"]
        == "no_eligible_extension_return_current"
    )


def test_extension_is_not_applied_without_original_fallback() -> None:
    strategies, diagnostic = execution.select_phase_a_strategies(
        t_ana=1.0,
        observations_by_relative_time=_observations(fallback=False),
        rotations=100,
        protocol=_protocol(),
    )
    assert diagnostic["fallback_triggered"] is False
    assert diagnostic["acquired_extension_relative_times"] == []
    assert strategies["multiple_window_rule"]["selection_source"] == (
        "current_fallback"
    )
    assert strategies["equal_information_pooled_fit"]["selection_source"] == (
        "current_fallback"
    )


def test_strategy_selection_never_accepts_nonfinite_proxy() -> None:
    rows = _observations()
    rows[0.5]["proxy_hartree"] = math.nan
    with pytest.raises(execution.ExecutionError, match="non-finite"):
        execution.select_phase_a_strategies(
            t_ana=1.0,
            observations_by_relative_time=rows,
            rotations=100,
            protocol=_protocol(),
        )


def test_guard_requires_complete_strategy_budget_payload() -> None:
    predictions = _predictions()
    guard.validate_phase_a_predictions(predictions)
    del predictions["conditions"][0]["strategies"]["multiple_window_rule"][
        "frozen_pauli_rotation_budget"
    ]
    with pytest.raises(guard.ProtocolBoundaryError, match="frozen budget"):
        guard.validate_phase_a_predictions(predictions)


def test_phase_b_cache_key_has_all_frozen_identity_fields() -> None:
    key = execution.phase_b_cache_key(
        protocol_sha256="a" * 64,
        prediction_sha256="b" * 64,
        condition="LiF_active_eq_sto3g",
        hamiltonian_sha256="c" * 64,
        formula_sha256_value="d" * 64,
        time_value=0.5,
        backend="gpu",
        previous_vector_sha256=None,
    )
    required = set(_protocol()["cache_and_artifact_policy"][
        "cache_key_required_fields"
    ])
    assert required <= set(key)
    assert key["absolute_time_hex"] == float(0.5).hex()
    assert key["branch_rule_version"] == execution.PHASE_B_BRANCH_RULE_VERSION


def test_direct_point_anchor_and_continuation_use_distinct_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    time_value = 0.25
    unitary = np.diag(
        [
            np.exp(1j * 0.1 * time_value),
            np.exp(1j * 0.7 * time_value),
        ]
    )

    def fake_build(*args, **kwargs):
        return unitary.copy(), {"backend": "synthetic"}

    monkeypatch.setattr(phase_b, "_build_unitary", fake_build)
    system = {
        "hamiltonian": csr_matrix(np.diag([0.1, 0.7])),
        "component_spectra": [object()],
    }
    exact = np.asarray([1.0, 0.0], dtype=np.complex128)
    anchor, vector, shift = phase_b.direct_point(
        system=system,
        exact_energy=0.1,
        exact_state=exact,
        sequence=(1.0,),
        rotations=10,
        time_value=time_value,
        roles=["anchor"],
        backend="cpu",
        gpu_id=0,
        previous_vector=None,
        previous_unwrapped_shift=None,
        epsilon=1.0,
        beta=1.2,
    )
    assert anchor["selection_rule"] == "anchor_maximum_exact_ground_overlap"
    assert anchor["ground_overlap_probability"] == pytest.approx(1.0)
    assert anchor["unitarity_residual_frobenius"] < 1e-14
    continued, _, _ = phase_b.direct_point(
        system=system,
        exact_energy=0.1,
        exact_state=exact,
        sequence=(1.0,),
        rotations=10,
        time_value=time_value,
        roles=["candidate_00"],
        backend="cpu",
        gpu_id=0,
        previous_vector=vector,
        previous_unwrapped_shift=shift,
        epsilon=1.0,
        beta=1.2,
    )
    assert continued["selection_rule"].startswith("ascending_time")
    assert continued["previous_vector_overlap_probability"] == pytest.approx(1.0)


def test_numerical_gate_rejects_branch_disagreement() -> None:
    point = {
        "roles": ["anchor"],
        "eigenpair_residual_2_norm": 1e-12,
        "unitarity_residual_frobenius": 1e-12,
        "ground_overlap_probability": 0.99,
        "previous_vector_overlap_probability": None,
        "phase_gap_radian": 0.2,
        "branch_selection_disagrees_with_independent_rule": False,
    }
    later = {
        **point,
        "roles": ["candidate_00"],
        "previous_vector_overlap_probability": 0.99,
        "branch_selection_disagrees_with_independent_rule": True,
    }
    result = phase_b.validate_numerical_gates(
        {"LiF_active_eq_sto3g": [point, later]},
        _protocol(),
    )
    assert result["passed"] is False
    assert result["checks"]["branch_disagreement"] is False


def test_phase_b_scoring_uses_fixed_grid_and_frozen_selection_only() -> None:
    predictions = _predictions()
    direct = {}
    for row in predictions["conditions"]:
        direct[row["condition"]] = [
            {
                "time_hartree_inverse": relative,
                "roles": [f"candidate_{index:02d}"],
                "direct_error_hartree": 1.0e-6,
                "direct_required_cost": 5.0e7 + index,
            }
            for index, relative in enumerate(
                _protocol()["phase_b"]["fixed_candidate_grid_relative_to_t_ana"]
            )
        ]
    result = execution.score_phase_b(
        predictions=predictions,
        direct_points_by_condition=direct,
        protocol=_protocol(),
    )
    assert len(result["rows"]) == 16
    assert set(result["candidate_grid_oracle_costs"]) == {
        row["condition"] for row in predictions["conditions"]
    }
    assert all(
        row["selected_time_hartree_inverse"] == 0.65
        for row in result["rows"]
    )
    assert all("interpol" not in key for key in result)


def test_phase_b_parser_requires_phase_a_commit_boundary() -> None:
    actions = {
        action.dest
        for action in phase_b._parser()._actions
        if action.required
    }
    assert {
        "phase_a_root",
        "phase_a_commit",
        "phase_a_artifact_relative",
        "preflight_root",
    } <= actions


def test_phase_a_runner_has_no_truth_path_argument() -> None:
    destinations = {
        action.dest for action in phase_a._parser()._actions
    }
    assert "truth_root" not in destinations
    assert "phase_b_root" not in destinations
    assert "h01_root" not in destinations
    assert "p03_root" not in destinations


def test_phase_a_mock_run_freezes_all_outputs_without_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol, protocol_sha = guard.load_protocol()
    monkeypatch.setattr(
        phase_a,
        "validate_process_environment",
        lambda project_root: {"status": "synthetic"},
    )
    monkeypatch.setattr(
        phase_a,
        "validate_preflight",
        lambda project_root, preflight_root: {
            "status": "preflight_pass_phase_a_not_authorized",
            "result_commit": phase_a.PREFLIGHT_RESULT_COMMIT,
        },
    )

    def fake_prepare(spec, protocol_sha256, work_dir, processes):
        condition = spec["name"]
        system = {
            "schema": "second_study_safe_time_domain_phase_a_system_v1",
            "condition": condition,
            "protocol_sha256": protocol_sha256,
            "hamiltonian_sha256": execution.sha256_bytes(
                condition.encode("utf-8")
            ),
            "hamiltonian": csr_matrix(np.eye(2)),
            "component_spectra": [],
            "term_counts": [10],
            "cisd_state": np.asarray([1.0, 0.0]),
            "rhf_state": np.asarray([1.0, 0.0]),
            "restricted_basis": np.asarray([0, 1]),
            "num_qubits": 1,
        }
        return system, {
            "condition": condition,
            "exact_diagonalization_count": 0,
            "direct_pf_eigenpair_count": 0,
        }

    def fake_selector(
        *,
        condition,
        system,
        protocol,
        **kwargs,
    ):
        strategies = {
            name: _strategy(name, 0.49)
            for name in guard.STRATEGIES
        }
        counts = {
            "state_generations": 1,
            "group_spectrum_builds": 1,
            "proxy_points": 5,
            "hamiltonian_exponential_actions": 5,
            "current_m3_pf_state_actions": 5,
            "explicit_hamiltonian_vector_actions_for_state_diagnostics": 1,
        }
        return {
            "condition": condition,
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "proxy_analytic_time_hartree_inverse": 1.0,
            "proxy_scale_fit": {"synthetic": True},
            "rotation_count_per_pf_step": 100,
            "strategies": strategies,
            "selector_diagnostics": {"synthetic": True},
            "information_counts": {
                "current_fallback": counts,
                "equal_information_pooled_fit": counts,
                "multiple_window_rule": counts,
                "uncapped_counterfactual": counts,
            },
            "proxy_cache_counts": {"computed": 5, "reused": 0},
            "proxy_unique_coordinate_count": 5,
        }, [
            {
                "condition": condition,
                "point_role": "synthetic",
                "relative_to_t_ana": 0.1,
                "time_hartree_inverse": 0.1,
                "proxy_hartree": 1e-9,
            }
        ]

    monkeypatch.setattr(phase_a, "prepare_condition", fake_prepare)
    monkeypatch.setattr(phase_a, "run_condition_selector", fake_selector)
    output = tmp_path / "phase_a"
    audit = phase_a.run(
        project_root=Path.cwd(),
        protocol_path=Path(
            "review_response/second_study_safe_time_domain_protocol.json"
        ),
        preflight_root=tmp_path / "preflight",
        processes=1,
        output_dir=output,
    )
    assert audit["status"] == "phase_a_frozen_phase_b_not_authorized"
    assert audit["oracle_access"] == {
        key: 0 for key in guard.ORACLE_ACCESS_COUNTERS
    }
    assert audit["phase_b_coordinate_count"] == 44
    assert not (output / "COMPLETE").exists()
    marker = guard.verify_phase_a_freeze(output)
    assert marker["condition_count"] == 4
    manifest = execution.load_json(output / "manifest.json")
    assert {
        row["path"] for row in manifest["files"]
    } == set(protocol["phase_a"]["freeze"]["required_files"])
    frozen_predictions = execution.load_json(output / "predictions.json")
    assert frozen_predictions["new_direct_truth_coordinate_count"] == 0
    assert frozen_predictions["exact_diagonalization_count"] == 0


def test_phase_b_mock_run_preserves_negative_result_and_completes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    predictions = _predictions()
    phase_a_root = tmp_path / "phase_a"
    phase_a_root.mkdir()
    prediction_path = phase_a_root / guard.PREDICTION_FILE
    prediction_path.write_text(
        __import__("json").dumps(predictions, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prediction_sha = execution.sha256_file(prediction_path)
    monkeypatch.setattr(
        phase_a,
        "validate_process_environment",
        lambda project_root: {"status": "synthetic"},
    )
    monkeypatch.setattr(
        phase_a,
        "validate_preflight",
        lambda project_root, preflight_root: {"status": "passed"},
    )
    monkeypatch.setattr(
        phase_b,
        "verify_phase_a_commit",
        lambda **kwargs: {
            "commit": "a" * 40,
            "prediction_sha256": prediction_sha,
        },
    )
    monkeypatch.setattr(
        phase_b,
        "verify_phase_a_runtime_inventory",
        lambda root: {
            "inventory_sha256": "b" * 64,
            "all_files_byte_identical": True,
        },
    )
    monkeypatch.setattr(
        phase_b,
        "load_phase_a_systems",
        lambda root, protocol, protocol_sha: {
            condition: {
                "condition": condition,
                "hamiltonian_sha256": execution.sha256_bytes(
                    condition.encode()
                ),
            }
            for condition in execution.condition_names(protocol)
        },
    )
    monkeypatch.setattr(
        phase_b,
        "exact_ground_pair",
        lambda system: (0.0, np.asarray([1.0, 0.0]), 1e-13),
    )
    monkeypatch.setattr(phase_a, "_rotation_count", lambda system, sequence: 100)

    def fake_cached_direct_point(*, time_value, roles, **kwargs):
        point = {
            "time_hartree_inverse": float(time_value),
            "roles": list(roles),
            "direct_error_hartree": 1.0e-6,
            "direct_required_cost": 5.0e7 + float(time_value),
            "eigenpair_residual_2_norm": 1.0e-13,
            "unitarity_residual_frobenius": 1.0e-13,
            "ground_overlap_probability": 0.99,
            "previous_vector_overlap_probability": (
                None if "anchor" in roles else 0.99
            ),
            "phase_gap_radian": 0.2,
            "branch_selection_disagrees_with_independent_rule": False,
        }
        return point, np.asarray([1.0, 0.0]), 1.0e-6, False

    monkeypatch.setattr(
        phase_b, "cached_direct_point", fake_cached_direct_point
    )
    output = tmp_path / "phase_b"
    decision = phase_b.run(
        project_root=Path.cwd(),
        protocol_path=Path(
            "review_response/second_study_safe_time_domain_protocol.json"
        ),
        preflight_root=tmp_path / "preflight",
        phase_a_root=phase_a_root,
        phase_a_commit="a" * 40,
        phase_a_artifact_relative=Path("artifacts/synthetic_phase_a"),
        backend="gpu",
        gpu_id=0,
        processes=1,
        output_dir=output,
    )
    assert decision["status"] == "complete_no_benefit"
    assert (output / "COMPLETE").is_file()
    assert execution.load_json(output / "strategy_scoring.json")[
        "benefit"
    ] is False
    assert (output / ".runtime" / "run_identity.json").is_file()
    assert not (output / ".runtime" / "direct_cache").exists()
    manifest = execution.load_json(output / "manifest.json")
    assert "COMPLETE" in {row["path"] for row in manifest["files"]}


def test_phase_b_runtime_inventory_gate_is_exact(tmp_path: Path) -> None:
    phase_a_root = tmp_path / "phase_a"
    runtime_root = phase_a_root / ".runtime"
    cache = runtime_root / "system_cache" / "condition.pkl"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"fixed-runtime-cache")
    inventory = {
        "schema": (
            "second_study_safe_time_domain_phase_a_runtime_hash_inventory_v1"
        ),
        "runtime_root": str(runtime_root.resolve()),
        "file_count": 1,
        "total_bytes": cache.stat().st_size,
        "files": [
            {
                "path": "system_cache/condition.pkl",
                "absolute_path": str(cache.resolve()),
                "bytes": cache.stat().st_size,
                "sha256": execution.sha256_file(cache),
            }
        ],
    }
    (phase_a_root / "runtime_hash_inventory.json").write_text(
        __import__("json").dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    verified = phase_b.verify_phase_a_runtime_inventory(phase_a_root)
    assert verified["file_count"] == 1
    assert verified["all_files_byte_identical"] is True
    cache.write_bytes(b"fIxed-runtime-cache")
    with pytest.raises(execution.ExecutionError, match="SHA-256 mismatch"):
        phase_b.verify_phase_a_runtime_inventory(phase_a_root)


def test_phase_b_output_resume_requires_exact_identity_and_cache_only(
    tmp_path: Path,
) -> None:
    output = tmp_path / "phase_b"
    identity = {
        "schema": "second_study_safe_time_domain_phase_b_run_identity_v1",
        "protocol_sha256": "a" * 64,
        "prediction_sha256": "b" * 64,
    }
    first = phase_b.prepare_phase_b_output(output, identity)
    assert first["resumed"] is False
    cache = output / ".runtime" / "direct_cache" / "condition" / "x.pkl"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"cache")
    resumed = phase_b.prepare_phase_b_output(output, identity)
    assert resumed["resumed"] is True
    assert resumed["preexisting_direct_cache_files"] == 1
    with pytest.raises(execution.ExecutionError, match="identity mismatch"):
        phase_b.prepare_phase_b_output(
            output, {**identity, "prediction_sha256": "c" * 64}
        )
    (output / "unexpected.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(execution.ExecutionError, match="unexpected file"):
        phase_b.prepare_phase_b_output(output, identity)


def test_phase_a_and_phase_b_main_do_not_run_on_import() -> None:
    assert inspect.isfunction(phase_a.main)
    assert inspect.isfunction(phase_b.main)


def test_gpu_phase_a_prompt_pins_reviewed_bundle_and_boundary() -> None:
    prompt = (
        Path(__file__).parents[1]
        / "review_response"
        / "gpu_second_study_safe_time_domain_phase_a_execution_prompt.md"
    ).read_text(encoding="utf-8")
    for value in (
        "804331ecc976b83ae880940719706c11999247bc",
        "a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b",
        "e86e694805e8fcbc63659f7073eea95f67b8f435",
        "bbc063a05074260930860ef862d7e24bd81e3878",
        "2b37191594d7f79565314a5dad0d889f78aec504",
        "11dc5630d6bf21ec14f024e07ee272fc8c43c68ce1ce0fbcd2b0ab0cea393032",
        "107f362e63eb7fa2e7b03e37cfa357026eb07c18b032a3eafc4d1a0faf4b4363",
        "2e5cc1e8f476393c1e6dff4ed481bf723a83545d4a50f432cfb229215e71bf2d",
    ):
        assert value in prompt
    assert "run_second_study_safe_time_domain_phase_a.py" in prompt
    assert "--processes 1" in prompt
    assert "PHASE_A_FROZEN" in prompt
    assert "phase_a_frozen_phase_b_not_authorized" in prompt
    assert "Phase B、direct truth" in prompt
    assert "run_second_study_safe_time_domain_phase_b.py" not in prompt
    assert "/home/AbeHiromu/venvs/trotter-common/bin/python" in prompt
    assert "gpu-second-study-safe-time-domain-phase-a-20260927" in prompt


def test_committed_phase_a_boundary_audit_authorizes_only_fixed_phase_b() -> None:
    audit = execution.load_json(
        Path(__file__).parents[1]
        / "review_response"
        / "second_study_safe_time_domain_phase_a_boundary_audit.json"
    )
    assert audit["phase_a_result_commit"] == (
        "efea5fe0718c2c2623935949460498da066bdec3"
    )
    assert audit["identity"]["prediction_sha256"] == (
        "3406d2f69237d95b14be298059f777df3fbd5043446add2c31559bf902a34b83"
    )
    assert audit["freeze_checks"]["phase_b_coordinate_count"] == 42
    assert audit["freeze_checks"]["phase_b_coordinate_limit"] == 44
    assert all(
        value in (0, False)
        for value in audit["prohibited_operation_counts"].values()
    )
    assert audit["runtime_inventory"] == {
        "runtime_root": (
            "/home/AbeHiromu/worktrees/"
            "gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/"
            "server_second_study_safe_time_domain_phase_a_20260927_e86e694/"
            ".runtime"
        ),
        "file_count": 56,
        "total_bytes": 113469289,
        "committed": False,
        "copied_from_other_run": False,
        "phase_b_gate": (
            "all files, relative paths, absolute paths, byte counts, total "
            "bytes, and SHA-256 values must match before exact/direct "
            "calculation"
        ),
    }
    assert audit["decision"] == {
        "phase_a_boundary_status": "verified",
        "phase_a_predictions_mutable": False,
        "phase_a_runtime_mutable": False,
        "phase_b_authorization": "one_fixed_evaluation_only",
        "phase_b_output_must_be_new": True,
        "post_evaluation_retuning_allowed": False,
        "additional_pf_or_molecule_allowed": False,
    }
    assert not audit["unresolved_blockers"]


def test_gpu_phase_b_prompt_pins_one_frozen_evaluation() -> None:
    prompt = (
        Path(__file__).parents[1]
        / "review_response"
        / "gpu_second_study_safe_time_domain_phase_b_execution_prompt.md"
    ).read_text(encoding="utf-8")
    for value in (
        "804331ecc976b83ae880940719706c11999247bc",
        "efea5fe0718c2c2623935949460498da066bdec3",
        "1de4813915cdfb5d74a6813349f58983f9cdf8c8",
        "d4dd42fd107ac9fb90547a190a0c7080484ee667",
        "3406d2f69237d95b14be298059f777df3fbd5043446add2c31559bf902a34b83",
        "4b3de286c350afea2c00e822799edd54b52864bbbd219de3c389eece6639fc1a",
        "0bfefe181421171395572de8d25f441577bde604c18dcdd5d851def9a86a3d50",
        "5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91",
    ):
        assert value in prompt
    assert "run_second_study_safe_time_domain_phase_b.py" in prompt
    assert "--backend gpu" in prompt
    assert "--gpu-id 0" in prompt
    assert "--processes 1" in prompt
    assert "42 coordinates" in prompt
    assert "uniform new anchor" in prompt
    assert "complete_no_benefit" in prompt
    assert "failed_numerical_validation" in prompt
    assert "Phase A再実行" in prompt
    assert "run_second_study_safe_time_domain_phase_a.py" not in prompt


def test_second_study_completion_closes_as_fixed_negative_result() -> None:
    root = Path(__file__).parents[1]
    audit = execution.load_json(
        root
        / "review_response"
        / "second_study_safe_time_domain_completion_audit.json"
    )
    assert audit["status"] == "complete_no_benefit"
    assert audit["git_identity"]["phase_b_result_commit"] == (
        "4691ac1ea7423d3c3f5a0496c41c98b9dcba360f"
    )
    assert audit["artifact_identity"]["prediction_sha256"] == (
        "3406d2f69237d95b14be298059f777df3fbd5043446add2c31559bf902a34b83"
    )
    validation = audit["independent_validation"]
    assert validation["coordinate_plan_exact_match"] is True
    assert validation["numerical_gates_recomputed_exact_match"] is True
    assert validation["strategy_rows_recomputed_exact_match"] is True
    assert validation["benefit_decision_recomputed_exact_match"] is True
    assert validation["scoring_representation_note"]["ulp_difference"] == 1.0
    assert (
        validation["scoring_representation_note"][
            "scientific_or_decision_impact"
        ]
        is False
    )
    assert audit["execution"]["direct_cache_computed"] == 22
    assert audit["execution"]["direct_cache_reused"] == 20
    assert audit["execution"]["old_or_foreign_cache_reused"] == 0
    assert audit["numerical_validation"]["passed"] is True
    assert audit["strategy_summary"]["multiple_window_rule"]["safe_count"] == 3
    assert audit["benefit_checks"]["new_rule_unsafe_execution_count_zero"] is False
    conclusion = audit["conclusion"]
    assert conclusion["adopt_new_rule"] is False
    assert conclusion["claim_strict_out_of_cap_safety"] is False
    assert conclusion["negative_result_complete"] is True
    assert conclusion["further_retuning_or_experiment_authorized"] is False
    report = (
        root
        / "review_response"
        / "second_study_safe_time_domain_completion_report.md"
    ).read_text(encoding="utf-8")
    assert "complete_no_benefit" in report
    assert "negative result" in report
    assert "1 ULP" in report
    assert "第三研究は自動的に開始しません" in report


def test_committed_phase_b_result_recomputes_from_frozen_inputs() -> None:
    root = Path(__file__).parents[1]
    artifact = (
        root
        / "artifacts"
        / "server_second_study_safe_time_domain_phase_b_20260928_d4dd42f"
    )
    manifest = execution.load_json(artifact / "manifest.json")
    assert len(manifest["files"]) == 17
    for row in manifest["files"]:
        path = artifact / row["path"]
        assert path.stat().st_size == row["bytes"]
        assert execution.sha256_file(path) == row["sha256"]
    predictions = execution.load_json(
        root
        / "artifacts"
        / "server_second_study_safe_time_domain_phase_a_20260927_e86e694"
        / "predictions.json"
    )
    points = execution.load_json(artifact / "direct_points.json")["points"]
    protocol = _protocol()
    by_condition = {
        condition: [
            {key: value for key, value in point.items() if key != "condition"}
            for point in points
            if point["condition"] == condition
        ]
        for condition in execution.condition_names(protocol)
    }
    expected_plan = guard.derive_phase_b_coordinate_plan(predictions)
    for row in expected_plan:
        actual = by_condition[row["condition"]]
        assert [
            (point["time_hartree_inverse"], point["roles"])
            for point in actual
        ] == [
            (point["time_hartree_inverse"], point["roles"])
            for point in row["coordinates"]
        ]
    decision = execution.load_json(artifact / "decision.json")
    assert phase_b.validate_numerical_gates(by_condition, protocol) == decision[
        "numerical_validation"
    ]
    recomputed = execution.score_phase_b(
        predictions=predictions,
        direct_points_by_condition=by_condition,
        protocol=protocol,
    )
    stored = execution.load_json(artifact / "strategy_scoring.json")
    for key in (
        "schema",
        "rows",
        "regret_difference_from_equal_information",
        "candidate_grid_oracle_costs",
        "aggregate_frozen_budget_ratio_new_over_current_fallback",
        "benefit_checks",
        "benefit",
    ):
        assert recomputed[key] == stored[key]
    for strategy, summary in recomputed["strategy_summary"].items():
        if strategy != "uncapped_counterfactual":
            assert summary == stored["strategy_summary"][strategy]
            continue
        committed = stored["strategy_summary"][strategy]
        for key, value in summary.items():
            if key == "aggregate_frozen_pauli_rotation_budget":
                # The completion audit observed a one-ULP representation
                # difference, while Python 3.12 can reproduce the stored sum
                # exactly.  Both satisfy the fixed scientific identity.
                assert abs(value - committed[key]) <= math.ulp(committed[key])
            else:
                assert value == committed[key]
    assert decision["status"] == "complete_no_benefit"
    assert (artifact / "COMPLETE").read_text(encoding="utf-8").splitlines()[
        0
    ] == "status=complete_no_benefit"
    assert not (artifact / ".runtime").exists()
