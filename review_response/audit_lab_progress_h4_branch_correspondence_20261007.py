"""Fixed-point maximum-H-ground-overlap PF phase diagnostic, not a scorer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.linalg import schur

from review_response._pf_first_study_experiment_a_support import atomic_json, sha256_file, write_csv
from review_response.run_lab_progress_h4_state_checks_20261007 import (
    ROOT, DEFAULT_OUTPUT, inputs, read_csv, proxy_rows,
)


def freeze(output: Path) -> None:
    path = output / "branch_diagnostic_protocol.json"
    if path.exists():
        raise RuntimeError("branch diagnostic protocol already frozen")
    protocol = json.loads((output / "protocol.json").read_text())
    predictions = json.loads((output / "predictions.json").read_text())
    selections = {r["state_id"]: r for r in predictions["selections"]}
    coordinates = []
    for state, t, role in (
        ("cisd", 3.5175172132783867, "original_reliable_grid_minimum_control"),
        ("exact", 4.219457387007943, "exact_model_frozen_selection"),
        ("cisdt", 4.3081171560399, "cisdt_model_frozen_selection"),
    ):
        if role.endswith("frozen_selection"):
            assert selections[state]["choice"]["time"] == t
        coordinates.append({"time": t, "state_model_id": state, "role": role,
                            "frozen_budget": selections[state]["budget"],
                            "budget_source": "original state-control predictions.json; unchanged",
                            "control_budget_note": "CISD budget evaluated at grid-minimum time as fixed-point counterfactual only" if state == "cisd" else None})
    prior_manifest = output / "manifest.json"
    revision_manifest = output / "manifest_before_branch_diagnostic.json"
    if revision_manifest.exists():
        raise RuntimeError("manifest revision already recorded")
    revision_manifest.write_bytes(prior_manifest.read_bytes())
    atomic_json(path, {
        "protocol_id": "h4_m5_fixed_point_branch_correspondence_diagnostic_20261007",
        "post_hoc": True,
        "question": "Does continuation lose the H-ground-corresponding PF phase at the two unscorable selections, or is the dominant-overlap PF phase itself too inaccurate for the frozen budget?",
        "input_snapshot_commit": protocol["input_snapshot_commit"],
        "input_source_registry": "protocol.json: original source origin_result_commit and verified_snapshot_commit retained separately",
        "coordinates": coordinates,
        "formula_id": "m5_best",
        "state_for_overlap": "archived exact H ground state; diagnostic truth only",
        "selection_rule": "at each fixed point choose the Schur eigenvector maximizing |<psi0|v_j>|^2; phase cluster information is also reported",
        "phase_unwrap": "for this chosen eigenphase, pick integer k minimizing |(theta+2pi*k)/t-E0|; do not claim continuation",
        "comparison": "compare with original continued PF branch at the exact same frozen coordinate",
        "auxiliary_budget_evaluation": "absolute chosen fixed-point shift + beta*K/(t*unchanged frozen budget); this is not replacement formal scoring or an operational selector",
        "constants": protocol["constants"], "step_cost": 3996,
        "input_protocol_sha256": sha256_file(output / "protocol.json"),
        "input_predictions_sha256": sha256_file(output / "predictions.json"),
        "input_direct_grid_sha256": sha256_file(output / "direct_grid.csv"),
        "input_classification_sha256": sha256_file(output / "classification_and_audit.json"),
        "runner_sha256": sha256_file(Path(__file__)),
        "manifest_revision": {"previous_manifest_path": "manifest_before_branch_diagnostic.json",
                              "previous_manifest_sha256": sha256_file(revision_manifest)},
        "maximum_new_pf_diagonalizations": 3,
        "stop": "three fixed points and scalar diagnostics only; no re-selection, no budget/model changes, no replacement scoring policy",
        "claim_limit": "maximum-overlap fixed-point correspondence is auxiliary evidence, not proof of continuous eigenbranch identity",
        "publication": "scalar phases, overlaps, residuals, energy shifts and auxiliary bounds; no eigenvectors/matrices/unitaries",
    })


def run(output: Path) -> None:
    specification = json.loads((output / "branch_diagnostic_protocol.json").read_text())
    if sha256_file(Path(__file__)) != specification["runner_sha256"]:
        raise AssertionError("branch diagnostic runner changed after freeze")
    for filename, field in (("protocol.json", "input_protocol_sha256"),
                            ("predictions.json", "input_predictions_sha256"),
                            ("direct_grid.csv", "input_direct_grid_sha256"),
                            ("classification_and_audit.json", "input_classification_sha256")):
        if sha256_file(output / filename) != specification[field]:
            raise AssertionError("branch diagnostic input changed after freeze")
    protocol, system, _ = inputs(output)
    formula = next(f for f in protocol["formulas"] if f["formula_id"] == "m5_best")
    continued = read_csv(output / "direct_grid.csv")
    epsilon = specification["constants"]["epsilon_E_hartree"]
    beta = specification["constants"]["beta"]
    rows = []
    for coordinate in specification["coordinates"]:
        t = coordinate["time"]
        unitary, _ = proxy_rows(system, formula, t)
        triangular, vectors = schur(unitary, output="complex", check_finite=False)
        eigenvalues = np.diag(triangular)
        phases = np.angle(eigenvalues)
        weights = np.abs(vectors.conj().T @ system["states"]["exact"]) ** 2
        selected = int(np.argmax(weights))
        phase = float(phases[selected])
        unwrap_integer = int(np.rint((system["energy"] * t - phase) / (2 * np.pi)))
        energy = float((phase + 2 * np.pi * unwrap_integer) / t)
        shift = energy - system["energy"]
        saved = next(r for r in continued if r["formula_id"] == "m5_best" and float(r["time_hartree_inverse"]) == t)
        saved_phase = float(saved["principal_phase_radians"])
        phase_distances = np.abs(np.angle(np.exp(1j * (phases - saved_phase))))
        saved_component = int(np.argmin(phase_distances))
        eigenpair = float(np.linalg.norm(unitary @ vectors[:, selected] - eigenvalues[selected] * vectors[:, selected]))
        cluster = np.abs(np.angle(np.exp(1j * (phases - phase)))) <= 1e-8
        qpe = beta * specification["step_cost"] / (t * coordinate["frozen_budget"])
        total = abs(shift) + qpe
        rows.append({
            "time_hartree_inverse": t, "model_state_id": coordinate["state_model_id"], "coordinate_role": coordinate["role"],
            "maximum_overlap_component_index": selected,
            "maximum_H_ground_overlap_probability": float(weights[selected]),
            "maximum_overlap_cluster_probability": float(np.sum(weights[cluster])),
            "maximum_overlap_cluster_count": int(np.sum(cluster)),
            "principal_phase_radians": phase, "unwrap_nearest_E0_integer": unwrap_integer,
            "nearest_E0_energy_hartree": energy, "auxiliary_shift_hartree": shift,
            "eigenpair_residual": eigenpair,
            "continued_component_index_in_this_schur": saved_component,
            "continued_H_ground_overlap_probability": float(weights[saved_component]),
            "continued_original_overlap_probability": float(saved["ground_state_overlap_probability"]),
            "continued_raw_shift_hartree": float(saved["direct_shift_hartree"]),
            "continued_branch_reliable": saved["branch_reliable"] == "True",
            "same_PF_eigencomponent_as_continuation": selected == saved_component,
            "same_phase_cluster_as_continuation": bool(cluster[saved_component]),
            "phase_matching_distance_for_continuation": float(phase_distances[saved_component]),
            "frozen_budget": coordinate["frozen_budget"], "qpe_error_from_frozen_budget": qpe,
            "auxiliary_total_error_hartree": total, "auxiliary_target_met": total <= epsilon,
            "auxiliary_energy_margin_hartree": epsilon - total,
            "is_replacement_formal_scoring": False,
        })
    if max(r["eigenpair_residual"] for r in rows) > 1e-10:
        raise AssertionError("maximum-overlap PF eigenpair residual failed")
    write_csv(output / "branch_correspondence_diagnostic.csv", rows)
    atomic_json(output / "branch_diagnostic_checks.json", {
        "protocol_sha256": sha256_file(output / "branch_diagnostic_protocol.json"),
        "new_pf_diagonalizations": len(rows), "rows": rows,
        "formal_classification_preserved": True,
        "maximum_overlap_is_auxiliary_not_continuation_proof": True,
    })
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("freeze", "run"), required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    {"freeze": freeze, "run": run}[args.phase](args.output)
