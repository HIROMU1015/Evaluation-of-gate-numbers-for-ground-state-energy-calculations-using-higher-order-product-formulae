from __future__ import annotations

import ast
import csv
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from review_response._pf_first_study_experiment_a_support import (
    load_protocol,
)
from review_response.pf_first_study_phase_common import (
    load_h4_source,
    scaled_power_fit,
)
from review_response.run_pf_first_study_phase_a import run as run_phase_a
from review_response.run_pf_first_study_phase_b import _verify_phase_a


PROTOCOL = Path("PF_first_study_protocol_20260925.json")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def phase_a_result(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("pf-first-study-phase-a") / "result"
    run_phase_a(Path.cwd(), PROTOCOL.resolve(), output)
    return output


def test_h4_source_identity_matches_frozen_protocol() -> None:
    protocol, digest = load_protocol(PROTOCOL)
    system, manifest = load_h4_source(Path.cwd(), protocol)
    assert digest == "410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565"
    assert system["hamiltonian"].shape == (36, 36)
    assert len(system["groups"]) == 13
    assert len(system["controlled_state_ids"]) == 12
    assert manifest["group_sum_residual_frobenius"] <= 1e-12
    assert manifest["exact_eigenpair_residual_2_norm"] <= 1e-10


def test_phase_a_never_emits_exact_or_direct_truth(
    phase_a_result: Path,
) -> None:
    audit = json.loads((phase_a_result / "audit.json").read_text(encoding="utf-8"))
    predictions = json.loads(
        (phase_a_result / "predictions.json").read_text(encoding="utf-8")
    )
    observations = _rows(phase_a_result / "phase_a_proxy_observables.csv")
    assert audit["oracle_barrier_passed"] is True
    assert audit["exact_ground_proxy_row_count"] == 0
    assert audit["direct_truth_point_count"] == 0
    assert predictions["truth_opened"] is False
    assert not any(row["state_id"] == "exact" for row in observations)
    assert "direct_shift" not in (phase_a_result / "predictions.json").read_text(
        encoding="utf-8"
    )


def test_phase_a_uses_five_training_points_and_freezes_four_grids(
    phase_a_result: Path,
) -> None:
    predictions = json.loads(
        (phase_a_result / "predictions.json").read_text(encoding="utf-8")
    )
    formulae = predictions["experiment_B"]["formula_predictions"]
    assert len(formulae) == 4
    assert all(row["eligible"] for row in formulae)
    assert all(len(row["selection_grid_hartree_inverse"]) == 401 for row in formulae)
    selected = predictions["experiment_B"]["selection"]
    chosen = next(row for row in formulae if row["formula_id"] == selected["selected_formula"])
    assert selected["selected_time_hartree_inverse"] in chosen[
        "selection_grid_hartree_inverse"
    ]

    observations = _rows(phase_a_result / "phase_a_proxy_observables.csv")
    models = _rows(phase_a_result / "phase_a_proxy_models.csv")
    for formula_id in predictions["experiment_B"]["truth_reference_grids_frozen"]:
        training = sorted(
            (
                row
                for row in observations
                if row["experiment_id"] == "B"
                and row["formula_id"] == formula_id
                and row["state_id"] == "cisd"
                and int(row["sign"]) == 1
                and float(row["absolute_time"]) in {0.10, 0.15, 0.20, 0.25, 0.30}
            ),
            key=lambda row: float(row["absolute_time"]),
        )
        expected = scaled_power_fit(
            [float(row["absolute_time"]) for row in training],
            [float(row["proxy_imag_hartree"]) for row in training],
            (4, 6),
        )["coefficients"]
        stored = next(
            row
            for row in models
            if row["experiment_id"] == "B"
            and row["formula_id"] == formula_id
            and row["state_id"] == "cisd"
            and row["model_id"] == "raw_positive_even_two_term"
        )
        np.testing.assert_allclose(
            ast.literal_eval(stored["coefficients"]), expected, atol=0.0, rtol=1e-15
        )


def test_phase_b_verifier_rejects_modified_prediction(
    phase_a_result: Path, tmp_path: Path
) -> None:
    protocol, digest = load_protocol(PROTOCOL)
    del protocol
    _verify_phase_a(phase_a_result, digest)
    copied = tmp_path / "phase_a"
    shutil.copytree(phase_a_result, copied)
    prediction = copied / "predictions.json"
    prediction.write_bytes(prediction.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="prediction SHA-256 mismatch"):
        _verify_phase_a(copied, digest)
