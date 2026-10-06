"""Only synthetic fixtures and preregistration; no molecular truth reads."""

from copy import deepcopy
import json
from pathlib import Path
import zipfile

import numpy as np
import pytest

from hchain_cached_prefix import cached_prefix
from hchain_supplement_preflight import (
    DOC, PreflightError, allocation_gate, digest, exact_coordinates,
    npz_member_inventory, safe_file, verify_runtime,
)
from pf_spectral_recoverability_d2 import ArnoldiChain, build_arnoldi_chain


ROOT = Path(__file__).resolve().parents[1]


def test_preregistration_does_not_authorize_science():
    spec = json.loads((ROOT / DOC / "preregistration.json").read_text())
    assert not spec["execution_gates"]["science_job_start_allowed_now"]
    assert spec["track_R"]["continuation_rule_status"] == "unresolved_requires_review"
    assert not spec["governance"]["research_strategy_changes_authorized"]
    assert not spec["governance"]["prospective_partial_truth_access"]
    assert spec["track_G"]["anchor_R1"]["new_science_actions"] == 0
    assert spec["track_G"]["reference"]["noise_floor_hartree"] == 5e-13
    assert spec["track_G"]["new_science_caps"]["M1_PF_vector_actions"] == 96
    assert spec["track_R"]["new_science_caps"]["PF_vector_actions"] == 288
    assert spec["track_R"]["new_science_caps"]["new_truth_coordinates"] == 0
    assert spec["track_R"]["prefixes"] == [1, 2, 4, 8, 16, 32]


def plan_text():
    rows = ["system,candidate_id,ratio,ratio_hex,t_ref,t_ref_hex,time,time_hex,K,primary_m"]
    for ratio in (.5, .65, .8):
        rows.append(f"H6,H6_r{ratio},{ratio},{ratio.hex()},1.0,{(1.).hex()},{ratio},{ratio.hex()},14344,8")
    return "\n".join(rows) + "\n"


def test_exact_plan_preserves_binary64_without_neighbor_replacement():
    rows = exact_coordinates(plan_text(), "H6")
    assert len(rows) == 3
    assert [row["time_hex"] for row in rows] == [r.hex() for r in (.5, .65, .8)]


@pytest.mark.parametrize("bad", [
    lambda s: s.replace((.65).hex(), (.6500000000000001).hex()),
    lambda s: s.replace("H6_r0.65", "H6_r0.5"),
    lambda s: s.replace("14344,8", "14345,8", 1),
    lambda s: s.replace("0.65,0x", "nan,0x", 1),
    lambda s: s.replace("0.8,0x1.999999999999ap-1", "1.9,0x1.e666666666666p+0"),
    lambda s: s.splitlines()[0] + "\n" + "\n".join(s.splitlines()[1:3]),
])
def test_invalid_coordinates_stop(bad):
    with pytest.raises(PreflightError):
        exact_coordinates(bad(plan_text()), "H6")


@pytest.mark.parametrize("relative", ["../escape", "/absolute", "dir/../../escape"])
def test_unsafe_relative_names_rejected(tmp_path, relative):
    with pytest.raises(PreflightError, match="unsafe"):
        safe_file(tmp_path, relative)


def test_linked_input_rejected(tmp_path):
    (tmp_path / "data").write_bytes(b"input")
    (tmp_path / "link").symlink_to(tmp_path / "data")
    with pytest.raises(PreflightError, match="linked"):
        safe_file(tmp_path, "link")


def test_runtime_mismatch_stops_before_archive_inspection(tmp_path):
    path = tmp_path / "fixture.npz"
    path.write_bytes(b"not a zip")
    entries = [{"path": path.name, "bytes": 9, "sha256": "0" * 64}]
    with pytest.raises(PreflightError, match="byte identity"):
        verify_runtime(tmp_path, entries, {path.name: {"cisd"}})


def test_archive_inventory_does_not_deserialize_members(tmp_path):
    path = tmp_path / "fixture.npz"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("cisd.npy", b"deliberately invalid NPY bytes")
    entries = [{"path": path.name, "bytes": path.stat().st_size, "sha256": digest(path.read_bytes())}]
    assert verify_runtime(tmp_path, entries, {path.name: {"cisd"}})[0]["byte_identity_pass"]
    with pytest.raises(PreflightError, match="member set"):
        npz_member_inventory(path, {"ground"})


def test_extra_ground_member_is_not_sanitized(tmp_path):
    path = tmp_path / "fixture.npz"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("cisd.npy", b"x")
        archive.writestr("ground.npy", b"y")
    with pytest.raises(PreflightError, match="member set"):
        npz_member_inventory(path, {"cisd"})


def synthetic_allocation():
    return {"status": "approved_independent_local_allocation", "independent_from_prospective": True,
            "BLAS_threads": 1, "approved_output": "/synthetic/output", "CPU_maximum": 1,
            "workers_maximum": 1, "total_RAM_GiB": 12, "wall_hours": 12, "disk_GiB": 2}


@pytest.mark.parametrize("key,value", [
    ("status", "host_free_memory_observed"), ("independent_from_prospective", False),
    ("BLAS_threads", 2), ("approved_output", None), ("CPU_maximum", 0),
    ("total_RAM_GiB", float("nan")), ("wall_hours", True), ("disk_GiB", None),
    ("workers_maximum", 2),
])
def test_resource_gate_fail_closed(key, value):
    allocation = deepcopy(synthetic_allocation())
    allocation[key] = value
    assert not allocation_gate(allocation, "approved_frozen")


def test_resources_cannot_close_unresolved_scientific_rule():
    assert not allocation_gate(synthetic_allocation(), "unresolved_requires_review")
    assert allocation_gate(synthetic_allocation(), "approved_frozen")


def toy_chain(dimension):
    q = np.eye(dimension, dtype=complex)
    return ArnoldiChain(q, q.copy(), q.copy(), [1.] * (dimension - 1), False, 0., 0.)


@pytest.mark.parametrize("dimension", [1, 2, 4, 8, 16, 32])
def test_prefix_metrics_and_action_views_are_rank_local(dimension):
    chain = toy_chain(32)
    if dimension < 32:
        chain.basis[:, -1] = chain.basis[:, 0]
        chain.u_basis[:, -1] *= 2
    prefix = cached_prefix(chain, dimension)
    assert np.shares_memory(prefix.basis, chain.basis)
    assert len(prefix.relative_remainders) == dimension - 1
    assert prefix.orthogonality_residual_frobenius == 0
    assert prefix.maximum_pf_norm_residual == 0


def test_unavailable_prefix_after_breakdown_is_not_rescued():
    chain = toy_chain(7)
    chain.breakdown = True
    assert cached_prefix(chain, 8) is None
    assert cached_prefix(chain, 4).dimension == 4
    assert not cached_prefix(chain, 4).breakdown
    with pytest.raises(ValueError):
        cached_prefix(chain, 64)


def test_shared_chain_rank8_basis_reproduces_standalone_toy_chain():
    # Synthetic action call counts only. No saved molecular runtime is opened.
    values = np.linspace(-1.3, 1.7, 64)
    start = np.ones(64, dtype=complex)
    counts = {"u": 0, "h": 0}
    def u(v):
        counts["u"] += 1
        return np.exp(1j * values) * v
    def h(v):
        counts["h"] += 1
        return values * v
    shared = build_arnoldi_chain(start, u, h, maximum_dimension=32,
                                reorthogonalization_passes=2, relative_breakdown_tolerance=1e-12)
    assert counts == {"u": 32, "h": 32}
    prefix = cached_prefix(shared, 8)
    assert counts == {"u": 32, "h": 32}
    standalone = build_arnoldi_chain(start, u, h, maximum_dimension=8,
                                    reorthogonalization_passes=2, relative_breakdown_tolerance=1e-12)
    np.testing.assert_array_equal(prefix.basis, standalone.basis)
    np.testing.assert_array_equal(prefix.u_basis, standalone.u_basis)
    np.testing.assert_array_equal(prefix.h_basis, standalone.h_basis)
    assert prefix.maximum_pf_norm_residual == standalone.maximum_pf_norm_residual
    assert prefix.orthogonality_residual_frobenius == standalone.orthogonality_residual_frobenius
