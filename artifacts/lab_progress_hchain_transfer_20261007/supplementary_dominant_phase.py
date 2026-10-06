"""Independent dominant-ground-overlap phase at the frozen global selections.

This supplemental diagnostic never changes the formal continuation-branch
classification, prediction, PF/time choice, model, or budget.
"""
import json
import time

import numpy as np
from scipy.linalg import schur

from review_response import run_lab_progress_hchain_transfer_20261007 as base


def run():
    protocol = base.verify_protocol()
    marker = base.OUT / "SUPPLEMENTARY_PHASE_PROTOCOL.json"
    if marker.exists():
        raise FileExistsError("supplement already started")
    selected = []
    for name in base.SYSTEMS:
        predictions = [json.loads(path.read_text()) for path in (base.OUT / name).glob("prediction_*.json")]
        eligible = [row for row in predictions if row["eligible"]]
        if eligible:
            chosen = min(eligible, key=lambda row: row["selection"]["cost"])
            selected.append({"system": name, "formula": chosen["formula"],
                             "time": chosen["selection"]["time"], "time_hex": chosen["selection"]["time"].hex(),
                             "budget": chosen["selection"]["budget"], "K": chosen["K"],
                             "prediction_file_sha256": base.sha(base.OUT / name / f"prediction_{chosen['formula']}.json")})
    specification = {"utc": base.utc(), "authorization": "parent-approved dominant-phase supplement at existing global selected points",
                     "coordinates": selected, "coordinate_count": len(selected),
                     "method": "complex Schur, independently select maximum overlap with H ground; unwrap nearest E0*t",
                     "fixed_ground_overlap_gate": .9, "eigenpair_residual_gate": 1e-10,
                     "epsilon": base.EPSILON, "beta": base.BETA,
                     "formal_result_or_selection_modified": False, "runner_sha256": base.sha(__file__),
                     "original_protocol_sha256": base.sha(base.OUT / "protocol.json"),
                     "prediction_freeze_sha256": base.sha(base.OUT / "PREDICTIONS_FROZEN.json")}
    base.write_json(marker, specification)
    started = time.perf_counter()
    records = []
    for point in selected:
        action = base.MolecularActions(point["system"], protocol)
        with np.load(base.PRIVATE / f"{point['system']}_ground.npz", allow_pickle=False) as data:
            exact, energy = data["state"], float(data["energy"])
        unitary = action.unitary(protocol["formulae"][point["formula"]]["s2_sequence"], point["time"])
        triangle, vectors = schur(unitary, output="complex", check_finite=False)
        eigenvalues = np.diag(triangle)
        weights = np.abs(vectors.conj().T @ exact) ** 2
        index = int(np.argmax(weights))
        phase = float(np.angle(eigenvalues[index]))
        unwrap = int(np.rint((energy * point["time"] - phase) / (2 * np.pi)))
        shift = (phase + 2 * np.pi * unwrap) / point["time"] - energy
        residual = float(np.linalg.norm(unitary @ vectors[:, index] - eigenvalues[index] * vectors[:, index]))
        error = abs(shift) + base.BETA * point["K"] / (point["time"] * point["budget"])
        valid = bool(weights[index] >= .9 and residual <= 1e-10)
        records.append({**point, "maximum_ground_overlap": float(weights[index]),
                        "second_largest_ground_overlap": float(np.sort(weights)[-2]),
                        "dominant_phase_principal": phase, "unwrap_integer": unwrap,
                        "dominant_phase_shift": float(shift), "eigenpair_residual": residual,
                        "supplementary_phase_valid": valid, "frozen_budget_total_error": error,
                        "supplementary_precision_met": bool(error <= base.EPSILON) if valid else None,
                        "formal_continuation_result_unchanged": True})
    base.write_json(base.OUT / "supplementary_dominant_phase.json", {
        "protocol_sha256": base.sha(marker), "records": records,
        "elapsed_seconds": time.perf_counter() - started,
        "continuation_results_or_selection_modified": False, "new_grid_or_fit_count": 0,
    })
    print(json.dumps(records), flush=True)


if __name__ == "__main__":
    run()
