"""Synthetic/stub P2 verification only; no molecular SCF/input/reference science."""
import ast
from collections import Counter
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from scipy.sparse import csr_matrix

import prospective_input_reference as core
import run_prospective_input_reference as runner
from audit_prospective_ch2_history import inventory, literal_geometry_hits

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = core.read(ROOT / core.DOC / "protocol.json")
CONDITIONS = core.read(ROOT / core.DOC / "conditions.json")
GRID = core.read(ROOT / core.DOC / "reference_grid.json")


@pytest.fixture
def fit():
    return core.fit_function(ROOT, core.read(ROOT / core.DOC / "source_registry.json"))


def points_for(alpha, exponent=4):
    times = core.validate_grid(GRID)
    return times, [{"time_hex": t.hex(), "delta_C_hartree": alpha * t ** exponent} for t in times]


def test_frozen_scope():
    assert len(CONDITIONS) == 16
    assert Counter(c["family"] for c in CONDITIONS) == {"LiH": 4, "LiF": 4, "BeH2": 4, "CH2": 4}
    assert all(c["family"] != "HCN" for c in CONDITIONS)
    assert PROTOCOL["reference"]["ratios"] == [.8, 1., 1.2]
    assert PROTOCOL["resource"]["gammas"] == [1.01, 1.02, 1.05, 1.10]
    assert PROTOCOL["resource"]["B2_H1"] == "not_executed"
    assert PROTOCOL["reference"]["fit"]["noise_floor_hartree"] == 5e-12
    assert all(float(v).hex() == h for v, h in zip(PROTOCOL["PF"]["s2_sequence"], PROTOCOL["PF"]["canonical_sequence_hex"]))


@pytest.mark.parametrize("family,population,ncore,reference", [
    ("LiH", [2,2], 0, "RHF"), ("LiF", [4,4], 2, "RHF"),
    ("BeH2", [3,3], 0, "RHF"), ("CH2", [5,3], 0, "ROHF")])
def test_population_contract(family, population, ncore, reference):
    for c in (c for c in CONDITIONS if c["family"] == family):
        assert c["populations"] == population
        assert c["frozen_core_orbitals"] == ncore
        assert c["reference"] == reference
        assert sum(population) == c["active_electrons"]
        assert population[0] - population[1] == c["spin"]


def test_CH2_design_geometry():
    for c in (c for c in CONDITIONS if c["family"] == "CH2"):
        a, b = np.asarray(c["atoms"][1][1]), np.asarray(c["atoms"][2][1])
        assert np.linalg.norm(a) == pytest.approx(c["distance_angstrom"], abs=1e-14)
        assert np.degrees(np.arccos(np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b)))) == pytest.approx(102.)


def test_grid_exact_and_complete():
    assert core.validate_grid(GRID) == list(np.geomspace(.02, 1.8, 34))
    bad = [*GRID]
    bad[0] = {**bad[0], "time_hex": float(.021).hex()}
    with pytest.raises(core.PreparationError):
        core.validate_grid(bad)
    with pytest.raises(core.PreparationError):
        core.validate_grid(GRID[:5])


@pytest.mark.parametrize("dimension,primary,prefixes", [(1,1,[1]), (3,2,[1,2]), (4,4,[1,2,4]), (7,4,[1,2,4]), (735,8,[1,2,4,8])])
def test_future_rank(dimension, primary, prefixes):
    result = core.primary_rank(dimension)
    assert result["primary"] == primary and result["prefixes"] == prefixes
    assert result["actual_breakdown"] == "abstain_no_lower_prefix_rescue"


def test_fit_first_window_and_candidate_binary64(fit):
    times, points = points_for(1e-4)
    result = core.reference_summary(points, times, PROTOCOL, fit)
    assert result["leading_fit"]["selected_window"]["start_index"] == 0
    assert result["alpha_C"] == pytest.approx(1e-4)
    assert result["status"] == "reference_candidate_plan_ready"
    for ratio, row in zip((.8, 1., 1.2), result["candidate_plan"]):
        assert row["time_hex"] == float(ratio * result["t_ref"]).hex()
    with pytest.raises(core.PreparationError):
        core.reference_summary(points[:5], times[:5], PROTOCOL, fit)


@pytest.mark.parametrize("alpha,exponent,status", [(1e-16,4,"reference_scale_unavailable_under_frozen_protocol"),
    (1e-4,2,"reference_scale_unavailable_under_frozen_protocol"), (1e-7,4,"candidate_time_domain_ineligible")])
def test_reference_failures_no_rescue(fit, alpha, exponent, status):
    times, points = points_for(alpha, exponent)
    result = core.reference_summary(points, times, PROTOCOL, fit)
    assert result["status"] == status
    assert result.get("clipping_or_extension", False) is False


def test_floor_strictly_greater_and_first_eligible(fit):
    times, points = points_for(1e-4)
    points[0]["delta_C_hartree"] = 5e-12
    result = core.reference_summary(points, times, PROTOCOL, fit)
    assert result["leading_fit"]["selected_window"]["start_index"] == 1


def test_sparse_CISD_recipe_matches_historical_function():
    # Synthetic H has a triple determinant with much lower energy. It MUST NOT
    # enter the reference/singles/doubles subspace or become an exact-ground input.
    indices = np.array([0b111000,0b110001,0b100011,0b000111], dtype=np.int64)
    h = csr_matrix(np.diag([1.,.1,.2,-100.]))
    state, meta = core.cisd_state(h, indices, int(indices[0]))
    assert meta["positions"] == [0,1,2]
    assert meta["lowest_subspace_energy_hartree"] == .1
    assert state[3] == 0 and meta["full_H_ground_solve"] is False
    source = ROOT / "review_response/audit_h01_approximate_state_pilot.py"
    tree = ast.parse(source.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("determinant_excitation_rank", "determinant_cisd_state")]
    namespace = {"np": np, "time": __import__("time")}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec", flags=__import__("__future__").annotations.compiler_flag), namespace)
    old, old_meta = namespace["determinant_cisd_state"](h.toarray(), indices, int(indices[0]))
    assert np.abs(np.vdot(old, state)) == pytest.approx(1.)
    assert old_meta["subspace_dimension"] == meta["dimension"]


def test_dense_hash_equivalence():
    value = np.array([[1,2j],[-2j,3]], dtype=np.complex128)
    matrix = csr_matrix(value)
    # CSR->dense has its own frozen signed-zero bytes; do not equate it with
    # an independently formed ndarray even when numerical values coincide.
    assert core.dense_hash(matrix) == core.array_hash(matrix.toarray())


def test_action_caps_and_forbidden_interfaces(tmp_path):
    ledger = core.ReferenceLedger(2**40, checkpoint=tmp_path / "counts.json")
    for _ in range(34):
        ledger.charge("reference_pf_actions")
    with pytest.raises(core.PreparationError):
        ledger.charge("reference_pf_actions")
    for key in core.ZERO_KEYS:
        with pytest.raises(core.PreparationError):
            ledger.charge(key)
    assert ledger.counts["reference_pf_actions"] == 34
    assert not hasattr(core.ReferenceAdapter, "h_matvec") and not hasattr(core.ReferenceAdapter, "candidate")


def test_reference_echo_sign_and_action_accounting():
    # Synthetic commuting 2x2 input exercises CPU primitives only.
    h = csr_matrix(np.diag([.5,-.5]), dtype=np.complex128)
    ledger = core.ReferenceLedger(2**40)
    adapter = core.ReferenceAdapter(h, [h], [1.], ledger)
    state = np.array([1.,0.], dtype=np.complex128)
    point = adapter.point(state, .4)
    assert abs(point["delta_C_hartree"]) < 1e-13
    assert ledger.counts["reference_pf_actions"] == 1
    assert ledger.counts["reference_h_exponential_actions"] == 1
    assert all(ledger.counts[k] == 0 for k in core.ZERO_KEYS)
    with pytest.raises(core.PreparationError):
        adapter.point(np.eye(2), .4)


def test_no_ground_call_graph():
    tree = ast.parse(Path(core.__file__).read_text())
    prohibited = {"_prepare_system", "eigsh", "get_ground_state", "full_unitary", "exact_ground", "run_pyscf"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            assert name not in prohibited
            if name == "kernel":
                assert isinstance(node.func.value, ast.Name) and node.func.value.id in ("mf", "ao2mo")
    assert "run_hchain_truth_scoring" not in Path(core.__file__).read_text()


def test_scf_reference_dispatch_failure_no_fallback(monkeypatch, tmp_path):
    from pyscf import gto, scf
    calls = []
    class Mol:
        def build(self):
            pass
    class MF:
        converged = False
        def kernel(self):
            pass
    monkeypatch.setattr(gto, "Mole", Mol)
    monkeypatch.setattr(scf, "RHF", lambda mol: (calls.append("RHF") or MF()))
    monkeypatch.setattr(scf, "ROHF", lambda mol: (calls.append("ROHF") or MF()))
    for family, expected in (("LiH","RHF"), ("CH2","ROHF")):
        spec = next(c for c in CONDITIONS if c["family"] == family)
        with pytest.raises(core.PreparationError):
            core.create_input(spec, tmp_path / family, core.ReferenceLedger(2**40))
        assert calls[-1] == expected
    assert calls == ["RHF","ROHF"]  # no real SCF, no UHF or alternate state


def test_marker_one_shot(tmp_path):
    path = tmp_path / "STARTED.json"
    runner.marker(path, {"attempt": 1})
    with pytest.raises(core.PreparationError):
        runner.marker(path, {"attempt": 2})


def allocation(tmp_path):
    evidence = tmp_path / "explicit_quota.txt"
    evidence.write_text("synthetic allocation fixture, not permission for real science\n")
    return {"verified": True, "authority": "user_explicit_quota", "usable_cpu_quota": 1,
        "usable_ram_bytes": 2**30, "job_wall_seconds": 60, "writable_disk_quota_bytes": 1024,
        "approved_output_root": str(tmp_path / "output"), "workers": 1,
        "worker_rss_limit_bytes": 2**29, "worker_wall_seconds": 30,
        "coordinator_reserved_ram_bytes": 2**28, "reserved_disk_bytes": 1024,
        "expires_UTC": "2099-01-01T00:00:00+00:00",
        "evidence": [{"path": evidence.name, "sha256": core.sha_file(evidence)}]}


@pytest.mark.parametrize("change", [{"verified":False}, {"authority":"host_totals"}, {"workers":2},
    {"worker_rss_limit_bytes":2**31}, {"worker_wall_seconds":100}, {"evidence":[]},
    {"expires_UTC":"2000-01-01T00:00:00+00:00"}])
def test_allocation_fail_closed(tmp_path, change):
    a = {**allocation(tmp_path), **change}
    with pytest.raises(core.PreparationError):
        core.allocation_gate(a, a["approved_output_root"], evidence_root=tmp_path)


def test_allocation_positive_and_output_binding(tmp_path):
    a = allocation(tmp_path)
    assert core.allocation_gate(a, a["approved_output_root"], evidence_root=tmp_path)["workers"] == 1
    with pytest.raises(core.PreparationError):
        core.allocation_gate(a, tmp_path / "other", evidence_root=tmp_path)


def test_environment_readiness():
    result = core.environment_readiness()
    assert result["molecular_science_actions"] == 0
    assert all(b["threads"] == 1 for b in result["BLAS"])


def test_history_removed_middle_commit_is_scanned(tmp_path):
    # Fresh synthetic repository tests the all-history content barrier.
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args])
    git("init", "-q")
    git("config", "user.email", "synthetic@example.invalid")
    git("config", "user.name", "Synthetic Test")
    path = tmp_path / "registry.json"
    path.write_text('{"system":"CH2", "science_executed":true}\n')
    git("add", "registry.json")
    git("commit", "-qm", "synthetic middle execution evidence")
    old = git("rev-parse", "HEAD").decode().strip()
    path.write_text('{"system":"unrelated"}\n')
    git("add", "registry.json")
    git("commit", "-qm", "remove name at tip")
    result = inventory(tmp_path)
    assert result["reachable_commits"] == 2
    assert result["matches"][0]["example_snapshot_commit"] == old
    assert result["certificate"] == "pending_manual_classification"
    assert result["scientific_actions"] == result["numerical_imports"] == 0


@pytest.mark.parametrize("text,path", [
    ('mol.atom = [("C", (0,0,0)), ("H", (1,0,0)), ("H", (-1,0,0))]', "input.py"),
    ('{"atoms":[["C",[0,0,0]],["H",[1,0,0]],["H",[-1,0,0]]]}', "source_registry.json"),
    ('mol.atom = "C 0 0 0; H 1 0 0; H -1 0 0"', "input.py")])
def test_history_literal_geometry_without_family_name(text, path):
    assert literal_geometry_hits(text, [path])


def test_truth_field_manifest_rejected(tmp_path):
    with pytest.raises(core.PreparationError):
        core.load_input({"runtime_files":[{"path":"exact_state.npz"}], "group_count":0}, tmp_path)


def test_reference_commit_required(tmp_path):
    with pytest.raises(core.PreparationError):
        runner.frozen_inputs(ROOT, tmp_path, None)


def test_synthetic_integral_group_K_input_roundtrip(monkeypatch, tmp_path):
    from pyscf import ao2mo, gto, mcscf, scf
    class Mol:
        nelectron = 2
        def build(self):
            pass
    class MF:
        converged = True
        mo_coeff = np.eye(4)
        mo_occ = np.array([2.,0.,0.,0.])
        e_tot = 1.
        def kernel(self):
            pass
    class CAS:
        def get_h1eff(self, coeff):
            return np.diag([.5,1.,1.5,2.]), 0.
        def kernel(self):
            raise AssertionError("CASCI/FCI kernel forbidden even in test")
    monkeypatch.setattr(gto, "Mole", Mol)
    monkeypatch.setattr(scf, "RHF", lambda mol: MF())
    monkeypatch.setattr(mcscf, "CASCI", lambda *args: CAS())
    monkeypatch.setattr(ao2mo, "kernel", lambda *args: np.zeros((4,4,4,4)))
    monkeypatch.setattr(ao2mo, "restore", lambda symmetry, eri, norb: eri)
    spec = {"condition_id":"SYNTHETIC_NOT_MOLECULAR", "atoms":[], "reference":"RHF", "spin":0,
            "frozen_core_orbitals":0, "active_electrons":2, "active_orbitals":4, "populations":[1,1]}
    ledger = core.ReferenceLedger(2**40)
    runtime = tmp_path / "runtime"
    identity = core.create_input(spec, runtime, ledger)
    h, state, groups = core.load_input(identity, runtime)
    assert h.shape == (16,16) and identity["sector_dimension"] == 16
    assert identity["K"] > 0 and identity["CISD"]["dimension"] == 16
    assert abs(np.linalg.norm(state) - 1) < 1e-12
    matrices = list(groups)
    assert core.dense_hash(sum(matrices[1:], matrices[0])) == identity["H_dense_numpy_v1"]
    assert all(ledger.counts[k] == 0 for k in core.ZERO_KEYS)
    np.savez_compressed(runtime / "state.npz", cisd=state, sector_indices=np.arange(16), exact_state=state)
    # Even updating the container hash cannot authorize an extra truth member.
    for row in identity["runtime_files"]:
        if row["path"] == "state.npz":
            row["sha256"] = core.sha_file(runtime / "state.npz")
    with pytest.raises(core.PreparationError, match="truth field"):
        core.load_input(identity, runtime)


def test_cli_has_no_candidate_or_truth_commands():
    result = subprocess.run([sys.executable, str(ROOT / "review_response/run_prospective_input_reference.py"), "--help"],
                            capture_output=True, text=True, check=True)
    assert "{input,seal-inputs,references,seal-references}" in result.stdout
    assert "scorer" not in result.stdout
