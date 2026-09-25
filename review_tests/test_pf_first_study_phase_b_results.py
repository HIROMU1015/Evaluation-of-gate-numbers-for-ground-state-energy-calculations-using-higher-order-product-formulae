from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ARTIFACT = Path("artifacts/pf_first_study_phase_b_20260925_5a2f0a2")
PREDICTION_SHA256 = "60058fe333d4b25f1ad4b8f3f5342a3736f2379ce9490b3f2ecde69583beeeda"
PROTOCOL_SHA256 = "410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(filename: str) -> list[dict[str, str]]:
    with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_phase_b_artifact_hashes_and_numerical_gates_reconcile() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))

    assert audit["status"] == "complete_with_findings"
    assert manifest["status"] == audit["status"]
    assert (ARTIFACT / "COMPLETE").is_file()
    assert all(audit["checks"].values())
    assert audit["phase_a_prediction_sha256"] == PREDICTION_SHA256
    assert audit["protocol_sha256"] == PROTOCOL_SHA256
    assert manifest["prediction_sha256"] == PREDICTION_SHA256
    assert manifest["protocol_sha256"] == PROTOCOL_SHA256
    assert audit["phase_a_implementation_commit"] != audit["phase_b_execution_commit"]
    assert audit["extrema"]["maximum_three_way_closure_hartree"] <= 1e-12
    assert audit["extrema"]["maximum_eigenpair_residual_2_norm"] <= 1e-10
    assert audit["extrema"]["maximum_unitarity_residual_frobenius"] <= 1e-10

    for filename, expected in manifest["artifact_sha256"].items():
        assert _sha256(ARTIFACT / filename) == expected


def test_phase_b_row_counts_and_frozen_decision_scoring_reconcile() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert len(_rows("observables.csv")) == audit["counts"]["observable_rows"] == 2256
    assert len(_rows("error_decomposition.csv")) == audit["counts"]["decomposition_rows"] == 1536
    assert len(_rows("branch_audit.csv")) == audit["counts"]["direct_truth_rows"] == 1764

    allocation = _rows("allocation_scoring.csv")
    assert len(allocation) == audit["counts"]["allocation_rows"] == 2
    assert {row["budget_multiplier"] for row in allocation} == {"1.0", "1.01"}
    assert all(row["selected_formula"] == "m5_best" for row in allocation)
    assert all(row["success"] == "True" for row in allocation)
    for row in allocation:
        direct = float(row["direct_cost_at_selection"])
        reference = float(row["joint_grid_best_cost"])
        regret = float(row["joint_selection_regret"])
        assert abs(regret - (direct / reference - 1.0)) <= 1e-14
    assert abs(float(allocation[0]["joint_selection_regret"]) - 0.6451363580703113) <= 1e-14


def test_stopping_outcome_is_case_level_dominance_not_universal_dominance() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    dominance = _rows("dominance_summary.csv")
    counts: dict[str, int] = {}
    for row in dominance:
        component = row["dominant_component"]
        counts[component] = counts.get(component, 0) + 1

    assert len(dominance) == 128
    assert counts == {"E_state_hartree": 79, "mixed": 49}
    assert audit["stopping_outcomes"]["A_single_component_dominates"] is True
    assert audit["stopping_outcomes"]["B_dominant_component_switches"] is False
    assert audit["stopping_outcomes"]["C_material_error_but_resource_robust"] is False
    assert audit["stopping_outcomes"]["null_result"] is False

