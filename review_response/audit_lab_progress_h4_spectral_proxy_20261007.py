"""Post-hoc fixed-point spectral explanation of exact-state proxy bias."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.linalg import schur

from review_response._pf_first_study_experiment_a_support import atomic_json, sha256_file, write_csv
from review_response.run_lab_progress_h4_state_checks_20261007 import (
    OLD_B, ROOT, DEFAULT_OUTPUT, inputs, read_csv, proxy_rows,
)


def freeze(output: Path) -> None:
    target = output / "spectral_protocol.json"
    if target.exists():
        raise RuntimeError("spectral protocol already frozen")
    atomic_json(target, {
        "protocol_id": "h4_exact_state_proxy_spectral_audit_20261007",
        "post_hoc": True,
        "question": "Does exact-state proxy bias at reliable original m5 points come from sine nonlinearity or weight on other PF eigenstates?",
        "formula_id": "m5_best",
        "times": [0.4, 2.1466061014866242, 3.5175172132783867],
        "states": ["archived_exact_H_ground_state"],
        "input_snapshot_commit": json.loads((output / "protocol.json").read_text())["input_snapshot_commit"],
        "source_prior_origin_policy": "original source origin and verified snapshot inherited without modification from protocol.json",
        "input_protocol_sha256": sha256_file(output / "protocol.json"),
        "input_predictions_sha256": sha256_file(output / "predictions.json"),
        "input_direct_grid_sha256": sha256_file(output / "direct_grid.csv"),
        "runner_sha256": sha256_file(Path(__file__)),
        "truth_access": "three already observed reliable coordinates; select the PF branch matching the previously tracked phase, no new branch search or choice",
        "formula": "g0(t)=sum_j |<v_j(t)|psi0>|^2 sin(theta_j(t)-E0*t)/t; ground component is the previously reliable tracked PF branch",
        "maximum_new_diagonalizations": 3,
        "stop": "spectral weights and signed contributions at these three fixed points only; no selection/model changes",
        "publication": "scalar weights, phases, contributions and residuals only; no eigenvectors, exact states, matrices or unitaries",
    })


def run(output: Path) -> None:
    specification = json.loads((output / "spectral_protocol.json").read_text())
    for filename, field in (("protocol.json", "input_protocol_sha256"),
                            ("predictions.json", "input_predictions_sha256"),
                            ("direct_grid.csv", "input_direct_grid_sha256")):
        if sha256_file(output / filename) != specification[field]:
            raise AssertionError("spectral input changed after freeze")
    if sha256_file(Path(__file__)) != specification["runner_sha256"]:
        raise AssertionError("spectral runner changed after freeze")
    protocol, system, _ = inputs(output)
    formula = next(f for f in protocol["formulas"] if f["formula_id"] == "m5_best")
    direct_rows = read_csv(output / "direct_grid.csv")
    originals = read_csv(ROOT / OLD_B / "branch_audit.csv")
    components, summaries = [], []
    for t in specification["times"]:
        if t == 0.4:
            tracked = next(r for r in originals if r["experiment_id"] == "B"
                           and r["formula_id"] == "m5_best" and float(r["time_hartree_inverse"]) == t)
        else:
            tracked = next(r for r in direct_rows if r["formula_id"] == "m5_best"
                           and float(r["time_hartree_inverse"]) == t)
        if tracked["branch_reliable"] != "True":
            raise AssertionError("spectral audit includes unreliable point")
        unitary, proxy_points = proxy_rows(system, formula, t)
        triangular, vectors = schur(unitary, output="complex", check_finite=False)
        phases = np.angle(np.diag(triangular))
        weights = np.abs(vectors.conj().T @ system["states"]["exact"]) ** 2
        distance = np.abs(np.angle(np.exp(1j * (phases - float(tracked["principal_phase_radians"])))))
        selected = int(np.argmin(distance))
        relative_phases = np.angle(np.exp(1j * (phases - system["energy"] * t)))
        contributions = weights * np.sin(relative_phases) / t
        delta = float(tracked["direct_shift_hartree"])
        exact_proxy = next(r["proxy_hartree"] for r in proxy_points if r["state_id"] == "exact")
        for index, (weight, relative, contribution) in enumerate(zip(weights, relative_phases, contributions, strict=True)):
            components.append({"time_hartree_inverse": t, "eigencomponent_index": index,
                               "is_tracked_ground_branch": index == selected,
                               "overlap_probability": float(weight),
                               "relative_phase_modulo_2pi": float(relative),
                               "signed_proxy_contribution_hartree": float(contribution)})
        other = float(np.sum(np.delete(contributions, selected)))
        ground = float(contributions[selected])
        sine_bias = float(np.sin(t * delta) / t - delta)
        weight_bias = float((weights[selected] - 1.0) * np.sin(t * delta) / t)
        summaries.append({"time_hartree_inverse": t, "tracked_shift_hartree": delta,
            "exact_proxy_hartree": exact_proxy, "proxy_minus_tracked_shift_hartree": exact_proxy - delta,
            "tracked_branch_weight": float(weights[selected]), "other_branch_weight": float(1.0 - weights[selected]),
            "tracked_branch_proxy_contribution": ground, "other_branch_proxy_contribution": other,
            "sine_nonlinearity_bias": sine_bias, "weight_loss_bias": weight_bias,
            "spectral_sum_closure_residual": abs(float(np.sum(contributions)) - exact_proxy),
            "bias_decomposition_closure_residual": abs(sine_bias + weight_bias + other - (exact_proxy - delta)),
            "sum_weight_residual": abs(float(np.sum(weights)) - 1.0),
            "tracked_phase_matching_distance": float(distance[selected]),
            "maximum_schur_eigenvector_residual": float(max(np.linalg.norm(unitary @ vectors[:, j] - np.diag(triangular)[j] * vectors[:, j]) for j in range(36)))})
    if max(r["spectral_sum_closure_residual"] for r in summaries) > 1e-12:
        raise AssertionError("spectral sum failed")
    if max(r["bias_decomposition_closure_residual"] for r in summaries) > 1e-12:
        raise AssertionError("spectral bias split failed")
    write_csv(output / "spectral_components.csv", components)
    write_csv(output / "spectral_proxy_summary.csv", summaries)
    atomic_json(output / "spectral_checks.json", {
        "spectral_protocol_sha256": sha256_file(output / "spectral_protocol.json"),
        "new_pf_diagonalizations": len(summaries), "scalar_eigencomponent_rows": len(components),
        "summaries": summaries,
    })
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("freeze", "run"), required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    {"freeze": freeze, "run": run}[args.phase](args.output)
