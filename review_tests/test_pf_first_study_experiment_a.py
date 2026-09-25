from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from review_response._pf_first_study_experiment_a_support import (
    formula_registry,
    load_h2_system,
    load_protocol,
    pf_unitary,
    pf_unitary_high_precision,
    two_level_systems,
)
from review_response.pf_first_study_experiment_a import track_direct_branch


PROTOCOL = Path("PF_first_study_protocol_20260925.json")
ARTIFACT = Path("artifacts/pf_first_study_experiment_a_20260925_d3fadde")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_rows(filename: str) -> list[dict[str, str]]:
    with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_frozen_protocol_and_h2_source_identity() -> None:
    protocol, digest = load_protocol(PROTOCOL)
    assert digest == "410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565"
    system, source = load_h2_system(Path.cwd(), protocol)
    assert source["file_sha256"] == protocol["source_identity"]["f01_bundle"]["sha256"]
    assert system["hamiltonian"].shape == (4, 4)
    assert len(system["groups"]) == 2
    np.testing.assert_allclose(sum(system["groups"]), system["hamiltonian"], atol=1e-14, rtol=0.0)


def test_formulae_are_the_exact_frozen_sequences() -> None:
    protocol, _ = load_protocol(PROTOCOL)
    registry = formula_registry(protocol)
    assert [entry["formula_id"] for entry in registry] == protocol["scope"]["included_formula_ids"]
    for entry in registry:
        expected = protocol["formulae"][entry["formula_id"]]["s2_sequence"]
        np.testing.assert_array_equal(entry["sequence"], expected)
        sequence = np.asarray(entry["sequence"])
        assert abs(float(np.sum(sequence)) - 1.0) <= 1e-12
        assert abs(float(np.sum(sequence**3))) <= 1e-12
        np.testing.assert_array_equal(sequence, sequence[::-1])


def test_commuting_control_and_high_precision_reference() -> None:
    protocol, _ = load_protocol(PROTOCOL)
    system = two_level_systems()["two_level_commuting"]
    sequence = formula_registry(protocol)[0]["sequence"]
    unitary = pf_unitary(system["groups"], sequence, 0.27)
    reference = pf_unitary_high_precision(system["groups"], sequence, 0.27, 80)
    assert np.max(np.abs(unitary - reference)) <= 1e-12
    energies, vectors = np.linalg.eigh(system["hamiltonian"])
    exact = (vectors * np.exp(1j * 0.27 * energies)[None, :]) @ vectors.conj().T
    assert np.max(np.abs(unitary - exact)) <= 1e-12


def test_signed_branches_are_started_independently_from_zero() -> None:
    protocol, _ = load_protocol(PROTOCOL)
    system = two_level_systems()["two_level_noncommuting"]
    sequence = formula_registry(protocol)[0]["sequence"]
    for sign in (-1, 1):
        times = [sign * value for value in (0.05, 0.08, 0.12)]
        unitaries = [pf_unitary(system["groups"], sequence, value) for value in times]
        rows = track_direct_branch(
            unitaries,
            times,
            system["ground_state"],
            system["energy"],
            protocol["phase_and_branch_policy"]["degenerate_phase_gap_radians"],
        )
        assert abs(
            rows[0]["previous_branch_overlap_probability"]
            - rows[0]["ground_state_overlap_probability"]
        ) <= 1e-14


def test_experiment_a_artifact_is_complete_and_reconciled() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete_validation"
    assert audit["passed"] is True
    assert all(check["passed"] for check in audit["checks"])
    assert (ARTIFACT / "COMPLETE").is_file()
    assert audit["scope"] == {
        "experiment": "A",
        "scientific_generality_result": False,
        "system_count": 3,
        "formula_count": 4,
        "observable_row_count": 336,
        "branch_row_count": 144,
        "decomposition_row_count": 336,
    }
    for filename, expected in manifest["artifact_sha256"].items():
        assert _sha256(ARTIFACT / filename) == expected
    assert len(_csv_rows("observables.csv")) == 336
    assert len(_csv_rows("branch_audit.csv")) == 144
    assert len(_csv_rows("error_decomposition.csv")) == 336


def test_three_way_closure_and_even_odd_leading_structure() -> None:
    decomposition = _csv_rows("error_decomposition.csv")
    assert max(abs(float(row["closure_residual_hartree"])) for row in decomposition) <= 1e-12

    formal = _csv_rows("formal_proxy_coefficients.csv")
    below_four = [
        abs(float(row["coefficient"]))
        for row in formal
        if int(row["proxy_power"]) < 4
    ]
    assert max(below_four) <= 1e-12
    real_odd = [
        abs(float(row["coefficient"]))
        for row in formal
        if row["system_id"] == "two_level_noncommuting"
        and row["state_id"] in {"exact_ground", "real_q001"}
        and int(row["proxy_power"]) in {5, 7}
    ]
    assert max(real_odd) <= 1e-12
    complex_t5 = [
        abs(float(row["coefficient"]))
        for row in formal
        if row["system_id"] == "two_level_noncommuting"
        and row["state_id"] == "complex_q001"
        and int(row["proxy_power"]) == 5
    ]
    assert len(complex_t5) == 4
    assert min(complex_t5) > 1e-6

    branches = _csv_rows("branch_audit.csv")
    pairs: dict[tuple[str, str, str], dict[int, float]] = {}
    for row in branches:
        key = (row["system_id"], row["formula_id"], row["absolute_time"])
        pairs.setdefault(key, {})[int(row["sign"])] = float(row["direct_shift_hartree"])
    assert max(abs(pair[1] - pair[-1]) for pair in pairs.values()) <= 1e-12
