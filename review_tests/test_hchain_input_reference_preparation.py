"""Truth-free preparation tests. No molecular candidate/truth acquisitions."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.linalg import expm

from review_response.hchain_input_reference_preparation import (
    AllowlistedArchive, Ledger, PreparationError, VectorAdapter, candidate_rows,
    canonical_hash, checked_functions, reference_result, sha_array, sha_file,
    state_identity,
)
from review_response.hchain_selective_calibration_schedule import (
    EPSILON, GAMMAS, budget, cheap_policy, h1_final, run_shared_schedule, spectral_policy,
)
from review_response.run_hchain_input_reference_preparation import DOC, OLD, INPUT_FILES
import review_response.run_hchain_input_reference_preparation as runner


ROOT = Path(__file__).resolve().parents[1]


def specification():
    return json.loads((ROOT / OLD / "cheap_reference_scale_contract.json").read_text())


def helpers():
    item = json.loads((ROOT / DOC / "authorization.json").read_text())["determinant_helpers"]
    return checked_functions(ROOT / item["path"], item["sha256"],
                             ("sector_basis_indices", "hartree_fock_full_basis_index", "determinant_excitation_rank"))


def cheap_points(*, unstable=False, unusable=False):
    values = [1e-6, 2e-6, -3e-6 if unstable else 3e-6]
    if unusable:
        values[1:] = [2 * EPSILON, 2 * EPSILON]
    return [{"candidate_id": f"r{i}", "time": t, "delta_C_hartree": delta}
            for i, t, delta in zip(range(3), (0.5, 0.65, 0.8), values, strict=True)]


def spectral_rows(points, *, abstain=False, error=1e-6):
    return [{"candidate_id": row["candidate_id"], "time": row["time"],
             "e_use": error, "abstain": abstain} for row in points]


def test_fixed_grid_exact_generator_and_hex():
    frozen = json.loads((ROOT / DOC / "reference_grid.json").read_text())["points"]
    generated = np.geomspace(0.02, 1.8, 34)
    assert len(frozen) == 34
    assert [row["hex"] for row in frozen] == [float(value).hex() for value in generated]
    assert all(float(row["time"]).hex() == row["hex"] for row in frozen)


@pytest.mark.parametrize("system,n,kind,pop,dim,reference,cisd_dim", [
    ("H2", 4, "fixed_interleaved_spin_populations", [1, 1], 4, 12, 4),
    ("H4", 8, "fixed_half_populations", [2, 2], 36, 204, 27),
    ("H6", 12, "fixed_half_populations", [3, 3], 400, 3640, 118),
])
def test_population_reference_and_cisd_combinatorics(system, n, kind, pop, dim, reference, cisd_dim):
    functions = helpers()
    indices = functions["sector_basis_indices"](n, kind, pop)
    ref = functions["hartree_fock_full_basis_index"](n, kind, pop)
    assert len(indices) == dim
    assert ref == reference
    assert np.all(np.diff(indices) > 0)
    positions = [index for index in indices if functions["determinant_excitation_rank"](int(index), ref) <= 2]
    assert len(positions) == cisd_dim


def test_function_extraction_does_not_execute_top_level(tmp_path):
    source = tmp_path / "dangerous.py"
    source.write_text("raise RuntimeError('top-level imported')\ndef selected(x):\n    return x+1\n")
    functions = checked_functions(source, sha_file(source), ["selected"])
    assert functions["selected"](1) == 2
    with pytest.raises(PreparationError, match="source changed"):
        checked_functions(source, "0" * 64, ["selected"])
    with pytest.raises(PreparationError, match="missing"):
        checked_functions(source, sha_file(source), ["absent"])


def test_archive_only_named_member_deserialized(tmp_path):
    path = tmp_path / "mixed.npz"
    np.savez(path, H2_cisd_state=np.array([1, 0]), H2_exact_state=np.array([99, 99]))
    accesses = []
    archive = AllowlistedArchive(path, sha_file(path), ["H2_cisd_state"], accesses)
    assert np.array_equal(archive.read("H2_cisd_state"), [1, 0])
    with pytest.raises(PreparationError, match="outside allowlist"):
        archive.read("H2_exact_state")
    archive.close()
    assert [row["key"] for row in accesses] == ["H2_cisd_state"]


@pytest.mark.parametrize("key", ["H6_exact_state", "ground_energy", "H4_D4", "H2_D6", "H4_D8"])
def test_truth_or_oracle_member_cannot_be_allowlisted(tmp_path, key):
    path = tmp_path / "mixed.npz"
    np.savez(path, vector=np.array([1, 0]))
    with pytest.raises(PreparationError, match="truth/oracle"):
        AllowlistedArchive(path, sha_file(path), [key], [])


def test_archive_byte_mismatch_fails_before_load(tmp_path, monkeypatch):
    path = tmp_path / "mixed.npz"
    path.write_bytes(b"not-an-archive")
    monkeypatch.setattr(np, "load", lambda *a, **k: pytest.fail("deserialization before hash gate"))
    with pytest.raises(PreparationError, match="identity mismatch"):
        AllowlistedArchive(path, "0" * 64, ["cisd"], [])


def toy_adapter(ledger=None, **kwargs):
    x = np.array([[0, 0.2], [0.2, 0]], dtype=np.complex128)
    z = np.diag(np.array([0.3, -0.3], dtype=np.complex128))
    ledger = ledger or Ledger()
    return VectorAdapter(x + z, [x, z], [1.0], ledger, **kwargs), ledger, x, z


def test_vector_pf_echo_and_separate_resource_counts():
    adapter, ledger, x, z = toy_adapter()
    psi = np.array([1, 0], dtype=np.complex128)
    t = 0.3
    point = adapter.cheap(psi, t)
    direct_vector = expm(1j * t / 2 * x) @ expm(1j * t * z) @ expm(1j * t / 2 * x) @ psi
    echo = np.vdot(expm(1j * t * (x + z)) @ psi, direct_vector)
    assert point["delta_C_hartree"] == pytest.approx(echo.imag / t, abs=1e-14)
    assert ledger.counts["reference_pf_actions"] == 1
    assert ledger.counts["reference_h_exponential_actions"] == 1
    assert ledger.counts["component_gate_materializations"] == 2
    assert ledger.counts["sparse_state_multiplies"] == 3
    assert ledger.counts["m1_h_matvecs"] == 0
    assert ledger.payload()["H_exponential_internal_matvec_count"].startswith("unknown")


def test_pf_cache_reused_only_at_identical_time():
    adapter, ledger, _, _ = toy_adapter()
    psi = np.array([1, 0], dtype=np.complex128)
    adapter.pf(psi, 0.3)
    adapter.pf(psi, 0.3)
    assert ledger.counts["component_gate_materializations"] == 2
    adapter.pf(psi, np.nextafter(0.3, 1.0))
    assert ledger.counts["component_gate_materializations"] == 4
    assert ledger.maximum_gate_cache_bytes > 0


@pytest.mark.parametrize("kind", ["candidate", "m1", "other"])
def test_preparation_adapter_rejects_candidate_actions(kind):
    adapter, ledger, _, _ = toy_adapter()
    with pytest.raises(PreparationError, match="not authorized"):
        adapter.pf(np.array([1, 0]), 0.3, kind=kind)
    assert ledger.counts["reference_pf_actions"] == 0
    assert ledger.counts["m1_pf_vector_actions"] == 0
    with pytest.raises(PreparationError, match="not authorized"):
        adapter.h_matvec(np.array([1, 0]))


def test_future_candidate_instrumentation_with_unit_test_vectors_only():
    adapter, ledger, x, z = toy_adapter(allowed_kinds=("candidate", "m1"))
    psi = np.array([1, 0], dtype=np.complex128)
    adapter.cheap(psi, 0.3, kind="candidate")
    adapter.pf(psi, 0.3, kind="m1")
    assert np.allclose(adapter.h_matvec(psi), (x + z) @ psi)
    assert ledger.counts["candidate_cheap_pf_actions"] == 1
    assert ledger.counts["candidate_h_exponential_actions"] == 1
    assert ledger.counts["m1_pf_vector_actions"] == 1
    assert ledger.counts["m1_h_matvecs"] == 1
    assert ledger.counts["component_gate_materializations"] == 2
    assert ledger.counts["reference_pf_actions"] == 0


def test_single_vector_and_action_ceiling_fail_closed():
    adapter, ledger, _, _ = toy_adapter()
    with pytest.raises(PreparationError, match="single finite vector"):
        adapter.pf(np.eye(2), 0.3)
    ledger.counts["reference_pf_actions"] = 68
    with pytest.raises(PreparationError, match="ceiling"):
        adapter.pf(np.array([1, 0]), 0.3)
    assert ledger.counts["reference_pf_actions"] == 68


def test_state_gate_preserves_bytes_and_counts_diagnostic_action():
    h = np.diag(np.array([1.0, 2.0], dtype=np.complex128))
    state = np.array([1j, 0], dtype=np.complex128)
    before = sha_array(state)
    ledger = Ledger()
    identity = state_identity(h, [h], state, np.array([0, 3]), 0, ledger)
    assert before == sha_array(state) == identity["CISD_sha256_numpy_v1"]
    assert identity["H_expectation_residual_hartree"] == 0
    assert ledger.counts["input_verification_h_matvecs"] == 1
    assert not identity["phase_alignment_to_exact_performed"]


def test_input_norm_failure_is_not_renormalized():
    h = np.eye(2, dtype=np.complex128)
    with pytest.raises(PreparationError, match="state-norm"):
        state_identity(h, [h], np.array([2, 0]), np.array([0, 3]), 0, Ledger())


def test_leading_fit_reused_earliest_window_and_alpha():
    contract = specification()
    source = contract["fit_function"]
    function = checked_functions(ROOT / source["path"], source["sha256"], ["leading_fit"])["leading_fit"]
    times = np.geomspace(0.02, 1.8, 34)
    values = -1e-4 * times**4  # analytical unit-test data, not a molecular experiment
    result = reference_result(times, [{"delta_C_hartree": float(value)} for value in values],
                              function, contract["fit_rules"], EPSILON)
    assert result["leading_fit"]["selected_window"]["start_index"] == 0
    assert result["alpha_C"] == pytest.approx(1e-4, rel=1e-12)
    assert result["t_ref"] == (EPSILON / (5 * result["alpha_C"]))**0.25


def test_reference_failure_stops_without_alternative():
    with pytest.raises(PreparationError, match="reference_scale_unavailable"):
        reference_result([1], [{"delta_C_hartree": 0}], lambda *args: {"qualified": False}, {}, EPSILON)


def test_nine_candidate_single_multiply_hex_and_rank():
    references = {name: {"t_ref": t} for name, t in zip(("H2", "H4", "H6"), (0.73, 1.237648718781152, 1.18))}
    rows = candidate_rows(references)
    assert len(rows) == 9
    for row in rows:
        assert row["time_hex"] == (row["ratio"] * references[row["system"]]["t_ref"]).hex()
        assert row["primary_m"] == (4 if row["system"] == "H2" else 8)
    assert rows[4]["time_hex"] == "0x1.9be3b5da6e877p-1"
    with pytest.raises(PreparationError, match="no subset rescue"):
        candidate_rows({"H4": references["H4"]})


@pytest.mark.parametrize("error", [-1, float("nan"), EPSILON, 2*EPSILON])
def test_budget_bad_denominator_or_nonfinite(error):
    assert budget(1.0, error, 108) is None


def test_gamma_is_cost_multiplier_and_stable_cheap_uses_low_gamma():
    points = cheap_points()
    policy = cheap_policy(points, 108)
    assert tuple(arm["gamma"] for arm in policy["B1_frontier"]) == GAMMAS
    for arm in policy["B1_frontier"]:
        assert arm["rows"][2]["budget"] == arm["gamma"] * budget(0.8, abs(points[2]["delta_C_hartree"]), 108)
    assert policy["q"] == 0
    assert policy["B2_gamma"] == 1.01
    assert h1_final(policy)["action"] == policy["B2"]
    with pytest.raises(PreparationError, match="must not see"):
        h1_final(policy, spectral_rows(points))


def test_sign_instability_escalates_without_truth_or_spectral():
    points = cheap_points(unstable=True)
    policy = cheap_policy(points, 108)
    assert policy["q"] == 1
    assert policy["B2_gamma"] == 1.10
    assert policy["instability"]["proxy_sign_instability"]
    outcome = h1_final(policy, spectral_rows(points))
    assert outcome["consistency"] is True
    assert outcome["action"]["budget"] < policy["B2"]["budget"]


def test_unusable_M1_retains_nonfallback_cheap():
    points = cheap_points(unstable=True)
    policy = cheap_policy(points, 108)
    outcome = h1_final(policy, spectral_rows(points, abstain=True))
    assert outcome["source"] == "M1_unusable"
    assert outcome["action"] == policy["B2"]
    assert outcome["consistency"] == "indeterminate"


def test_fallback_escalates_and_invalid_baseline_stops():
    policy = cheap_policy(cheap_points(unusable=True), 108)
    assert policy["B2"]["fallback"] and policy["q"] == 1
    points = cheap_points()
    points[0]["delta_C_hartree"] = EPSILON
    with pytest.raises(PreparationError, match="no replacement anchor"):
        cheap_policy(points, 108)


def test_H1_rejects_missing_and_one_ulp_time_mismatch():
    points = cheap_points(unstable=True)
    policy = cheap_policy(points, 108)
    with pytest.raises(PreparationError, match="exact candidate"):
        spectral_policy(spectral_rows(points)[:2], policy)
    rows = spectral_rows(points)
    rows[2]["time"] = float(np.nextafter(rows[2]["time"], 1.0))
    with pytest.raises(PreparationError, match="time hex"):
        spectral_policy(rows, policy)


def test_combined_schedule_freezes_q_and_H1_before_comparator_completion():
    events = []
    stored = {}
    def cheap(system):
        events.append(f"cheap:{system}")
        return cheap_points(unstable=system == "escalate"), 108
    def spectral(system):
        events.append(f"M1:{system}")
        assert "ACQUISITION_FROZEN" in stored
        if system == "skip":
            assert "H1_FROZEN" in stored
        return spectral_rows(cheap_points(unstable=system == "escalate"))
    def freeze(label, payload, digest):
        assert canonical_hash(payload) == digest
        stored[label] = deepcopy(payload)
        events.append(label)
    outcome = run_shared_schedule(["skip", "escalate"], cheap, spectral, freeze)
    assert events == ["cheap:skip", "cheap:escalate", "ACQUISITION_FROZEN", "M1:escalate", "H1_FROZEN", "M1:skip"]
    assert outcome["H1"]["skip"]["action"] == outcome["cheap"]["skip"]["B2"]
    assert events.count("M1:escalate") == 1
    assert outcome["resource"]["standalone_cold_always_M1_wall"] == "not_measured"
    assert "comparator_completion_wall_seconds_excluded_from_H1" in outcome["resource"]


def test_preparation_permission_and_scorer_method_are_separate():
    auth = json.loads((ROOT / DOC / "authorization.json").read_text())
    for key in ("candidate_cheap", "candidate_M1", "exact_ground", "direct_truth", "target_phase_gap", "performance_scoring", "push"):
        assert not auth["permissions"][key]
    method = json.loads((ROOT / DOC / "truth_scoring_method.json").read_text())
    assert not method["scientific_execution_authorized"]
    assert method["ground_solver"]["sector_dimensions"]["H6"] == 400
    assert not method["direct_branch"]["absolute_unwrap_integer_compared_to_relative_unwrap_integer"]
    sanitized = json.loads((ROOT / DOC / "archived_input_contract.json").read_text())
    assert sanitized["exact_state_ground_energy_oracle_fields"] == 0
    assert not any("ground_energy" in key for arrays in sanitized["source_identity"].values() for key in arrays)
    assert len(INPUT_FILES) == 6


def test_exact_combined_cost_excludes_q_zero_comparator_work():
    class Clock:
        value = 0.0
        def __call__(self):
            return self.value
    clock = Clock()
    def cheap(system):
        clock.value += 2
        return cheap_points(unstable=system == "escalate"), 108
    def spectral(system):
        clock.value += 7 if system == "escalate" else 100
        return spectral_rows(cheap_points(unstable=system == "escalate"))
    def freeze(*args):
        clock.value += 1
    result = run_shared_schedule(["skip", "escalate"], cheap, spectral, freeze, clock=clock)
    assert result["resource"]["H1_combined_wall_seconds"] == 13
    assert result["resource"]["comparator_completion_wall_seconds_excluded_from_H1"] == 100
    assert result["resource"]["per_system"]["skip"]["conditional_spectral_seconds"] == 0


def test_freeze_mutation_is_rejected_before_any_spectral():
    def mutate(label, payload, digest):
        payload["skip"]["q"] = 1
    with pytest.raises(PreparationError, match="mutated frozen payload"):
        run_shared_schedule(["skip"], lambda system: (cheap_points(), 108),
                            lambda system: pytest.fail("spectral opened before valid q freeze"), mutate)


def test_unresolved_gap_and_truth_barrier_are_method_not_current_computation():
    method = json.loads((ROOT / DOC / "truth_scoring_method.json").read_text())
    assert method["ground_solver"]["new_ground_states_authorized_now"] == 0
    assert method["unitary"]["builds_authorized_now"] == 0
    assert method["prediction_required_before_truth"]
    assert "indeterminate" in method["direct_branch"]["warning_handling"]
    assert "strict inequality" in method["scoring"]["branch_diagnostic"]


def test_wrong_input_freeze_HEAD_stops_before_any_runtime_read(tmp_path):
    with pytest.raises(PreparationError, match="exact input freeze commit"):
        runner.frozen_input_gate(tmp_path, tmp_path / "artifacts", "a" * 40, {"commit": "b" * 40})


def test_input_freeze_extra_committed_file_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "git", lambda root, *args:
                        b"parent\n" if args[0] == "rev-parse" else b"artifacts/run/extra.npy\n")
    with pytest.raises(PreparationError, match="exactly six lightweight"):
        runner.frozen_input_gate(tmp_path, tmp_path / "artifacts/run", "a" * 40, {"commit": "a" * 40})


def test_existing_output_rejection_does_not_write_failure_marker(tmp_path, monkeypatch):
    import sys
    output = tmp_path / "artifacts/existing"
    output.mkdir(parents=True)
    sentinel = output / "existing.json"
    sentinel.write_text('{"unchanged":true}')
    monkeypatch.setattr(sys, "argv", ["prepare", "--stage", "inputs", "--project-root", str(tmp_path),
                                      "--output-dir", "artifacts/existing"])
    with pytest.raises(PreparationError, match="left unchanged"):
        runner.main()
    assert list(output.iterdir()) == [sentinel]
    assert sentinel.read_text() == '{"unchanged":true}'
