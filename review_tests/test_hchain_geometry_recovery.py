"""Serialization regression tests with MOCK chemistry; no molecular acquisition."""
import ast
import builtins
from copy import deepcopy
import dis
import json
from pathlib import Path
import sys
from types import CodeType, ModuleType, SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import eye

import hchain_supplement_execution as core
import run_hchain_geometry_recovery as recovery

ROOT = Path(__file__).resolve().parents[1]


def global_names(code):
    names = {i.argval for i in dis.get_instructions(code) if i.opname == "LOAD_GLOBAL"}
    for child in code.co_consts:
        if isinstance(child, CodeType):
            names.update(global_names(child))
    return names


@pytest.mark.parametrize("distance", [.8, 1.2, 1.4, 1.6])
def test_extracted_namespace_has_every_global(distance):
    function = core.geometry_generator(ROOT, distance)
    assert global_names(function.__code__) <= set(function.__globals__) | set(vars(builtins))
    assert function.__globals__["write_json"] is core.write_json
    assert function.__globals__["distance"] == distance


def test_serialization_only_diff_and_science_ast():
    audit = recovery.serialization_audit(ROOT)
    assert audit["exact_one_line_namespace_binding_only"]
    assert audit["science_generator_original_file_unchanged"]
    assert audit["other_extractor_AST_unchanged"]
    assert audit["geometry_AST_modifications"] == 1
    assert len(audit["science_function_AST_sha256"]) == 64


@pytest.fixture
def serialized_mock(tmp_path, monkeypatch):
    """Execute the unchanged real generator and wrapper, replacing chemistry only."""
    calls = {"mock_RHF": 0, "write_json": [], "geometry": [], "threads": []}

    class Fermion:
        def __init__(self, term=None, coefficient=None, *, ids=()):
            self.ids = list(ids)
        def __add__(self, other):
            return Fermion(ids=self.ids + other.ids)

    class Qubit:
        def __init__(self, term=None, coefficient=0):
            self.terms = {} if term is None else {term: coefficient}
        def __iadd__(self, other):
            self.terms.update(other.terms)
            return self

    def jw(fermion):
        op = Qubit()
        for i in fermion.ids:
            op += Qubit(((i % 12, "Z"),), float(i + 1))
        return op

    class Mole:
        nelectron = 6
        def build(self):
            calls["geometry"].append(self.atom)

    class RHF:
        converged = True
        mo_coeff = np.eye(6)
        e_tot = 0.
        def __init__(self, mol):
            pass
        def kernel(self):
            calls["mock_RHF"] += 1

    class CASCI:
        def __init__(self, *args):
            pass
        def get_h1eff(self, mo):
            return np.eye(6), 0.

    class Grouper:
        def __init__(self, *args, **kwargs):
            self.group_term_list = [[Fermion(ids=(i,))] for i in range(57)]
            self._const_fermion = 0.

    def install(name, **attributes):
        module = ModuleType(name)
        module.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, module)

    install("pyscf", lib=SimpleNamespace(num_threads=lambda n: calls["threads"].append(n)),
            gto=SimpleNamespace(Mole=Mole), scf=SimpleNamespace(RHF=RHF),
            mcscf=SimpleNamespace(CASCI=CASCI),
            ao2mo=SimpleNamespace(kernel=lambda *args: np.zeros((6, 6, 6, 6)),
                                  restore=lambda n, eri, norb: eri))
    install("openfermion", FermionOperator=Fermion, QubitOperator=Qubit, jordan_wigner=jw)
    install("trotterlib.Almost_optimal_grouping", Almost_optimal_grouper=Grouper)
    install("trotterlib.component_sector_pf", qubit_operator_sector_matrix=lambda op, n, indices, **kw:
            eye(len(indices), format="csr", dtype=complex) * sum(op.terms.values()) / 57)
    install("trotterlib.pf_decomposition", iter_s2_sequence_steps=lambda *args: [(0, 1.)] * 14344)

    structure = [[[[i % 12, "Z"]]] for i in range(57)]
    real_read = core.read
    def mocked_read(path):
        value = real_read(path)
        if str(path).endswith("system_and_pf_contract.json"):
            value = deepcopy(value)
            next(s for s in value["systems"] if s["system"] == "H6")["ordered_group_structure_sha256"] = core.canonical_hash(structure)
        return value
    monkeypatch.setattr(core, "read", mocked_read)
    original_checked = core.checked_functions
    def mocked_helpers(path, digest, names, *args):
        helpers = original_checked(path, digest, names, *args)
        def mock_cisd(h, indices, reference):
            vector = np.zeros(len(indices), dtype=complex)
            vector[list(indices).index(reference)] = 1.
            return vector, {"lowest_subspace_energy_hartree": float(h[0, 0].real), "state_generation_seconds": 0.}
        helpers["determinant_cisd_state"] = mock_cisd
        return helpers
    monkeypatch.setattr(core, "checked_functions", mocked_helpers)
    actual_write = core.write_json
    def write_spy(path, payload):
        actual_write(path, payload)
        calls["write_json"].append(str(path))
    monkeypatch.setattr(core, "write_json", write_spy)
    ledger = core.ScienceLedger(8)
    record = core.new_geometry_input(ROOT, tmp_path, 1.2, ledger)
    h, state, indices, adapter = core.load_new_input(record, ROOT, ledger, ())
    return record, calls, h, state, indices, ledger, tmp_path


def test_mock_generator_serializes_with_actual_helper(serialized_mock):
    record, calls, h, state, indices, ledger, directory = serialized_mock
    assert calls["mock_RHF"] == 1 and calls["threads"] == [1]
    assert len(calls["write_json"]) == 1
    stored = json.loads((directory / "h6_group_operators.json").read_text())
    assert len(stored["groups"]) == 57 and stored["Pauli_counts"] == [1] * 57
    assert calls["geometry"][0] == [("H", (0., 0., float(i - 2.5) * 1.2)) for i in range(6)]
    assert (directory / "h6_orbitals_integrals.npz").exists()
    assert ledger.counts["H6_Hamiltonian_generations"] == 1  # synthetic counters only
    assert ledger.counts["H6_CISD_generations"] == 1


def test_sanitized_roundtrip_and_identity_freeze(serialized_mock):
    record, calls, h, state, indices, ledger, directory = serialized_mock
    assert h.shape == (400, 400) and state.shape == indices.shape == (400,)
    assert record["identity"]["CISD_subspace_dimension"] == 118
    assert record["K"] == record["identity"]["K"] == 14344
    assert core.sha_array(h) == record["identity"]["H_sha256_numpy_v1"]
    assert core.sha_array(state) == record["identity"]["CISD_sha256_numpy_v1"]
    assert core.sha_array(indices) == record["identity"]["sector_indices_sha256_numpy_v1"]
    assert len(record["identity"]["group_sha256_numpy_v1"]) == 57
    target = directory / "synthetic_identity_freeze.json"
    core.write_json(target, record)
    assert json.loads(target.read_text()) == record
    with np.load(record["runtime_file"], allow_pickle=False) as archive:
        assert set(archive.files) == {"hamiltonian", "cisd", "sector_indices"} | {f"group_{i:03d}" for i in range(57)}


def test_input_global_barrier_rejects_partial_and_repeated_generation():
    good = [{"unit": f"H6_R{d:.2f}", "status": "complete", "input": {}} for d in recovery.DISTANCES]
    recovery.require_inputs(good)
    with pytest.raises(core.PreparationError):
        recovery.require_inputs(good[:-1])
    bad = deepcopy(good)
    bad[0]["status"] = "terminal_failure_no_scientific_retry"
    with pytest.raises(core.PreparationError):
        recovery.require_inputs(bad)
    with pytest.raises(core.PreparationError):
        recovery.require_inputs(good + good[:1])
