"""Locally refine the promising fourth-order m=3 two-term PF.

Candidates are projected onto the exact fourth-order manifold, screened on
H2, and shortlisted on H4/H5 using the signed ``a4*t**4 + a6*t**6`` model.
Non-H-chain molecules and H6/H7 remain outside this coefficient-generation
stage.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from scipy.stats import qmc

from rank_two_term_pf_m3_m4 import (
    CURRENT_M3,
    _candidate_summary,
    _jsonable,
    _report,
    _select,
)
from search_pf_cost_predictability_m2_m3 import (
    _candidate,
    _deduplicate,
    evaluate_candidate_system,
)
from sweep_direct_scaling_h6_h7 import _write_json
from trotterlib.optimal_trotter import solve_nonprocessed_4th_moment_coefficients
from validate_asymptotic_cost_small_systems import _prepare_system
from validate_pf_cost_predictability import DEFAULT_FIT_TIMES, DEFAULT_RELATIVE_TIMES


CENTER_NAME = "m3_local_c2_r1_s016"
CENTER_WEIGHTS = (
    -0.5479746372736223,
    0.41306657348431686,
    0.18646792289888503,
    0.1744528222536092,
)
CURRENT_WEIGHTS = (
    -0.4737318199452465,
    0.3316118001935053,
    0.20922466907827963,
    0.19602944070083841,
)
DEFAULT_OUTPUT = Path("artifacts/two_term_pf_m3_refinement_local_20260909")


def generate_candidates(
    *, radii: Sequence[float], samples_per_radius: int, seed: int
) -> list[dict[str, Any]]:
    candidates = []
    for name, source, weights in (
        ("current_m3", CURRENT_M3, CURRENT_WEIGHTS),
        ("two_term_center", CENTER_NAME, CENTER_WEIGHTS),
    ):
        solved = solve_nonprocessed_4th_moment_coefficients(
            kernel_m=3, initial=weights[1:], max_nfev=4000
        )
        packed = _candidate(name, f"reference:{source}", solved.w_tail)
        if packed is None:
            raise RuntimeError(f"could not project {name}")
        candidates.append(packed)

    center = np.asarray(CENTER_WEIGHTS[1:], dtype=float)
    exponent = int(math.ceil(math.log2(max(1, int(samples_per_radius)))))
    for radius_index, radius in enumerate(radii):
        sampler = qmc.Sobol(
            d=3,
            scramble=True,
            seed=int(seed) + 1000 * radius_index,
        )
        unit = sampler.random_base2(exponent)[: int(samples_per_radius)]
        offsets = qmc.scale(unit, [-float(radius)] * 3, [float(radius)] * 3)
        for sample_index, offset in enumerate(offsets):
            solved = solve_nonprocessed_4th_moment_coefficients(
                kernel_m=3,
                initial=center + offset,
                max_nfev=4000,
            )
            packed = _candidate(
                f"m3_two_term_r{radius_index}_s{sample_index:03d}",
                f"sobol:radius={float(radius):.6g}:center={CENTER_NAME}",
                solved.w_tail,
            )
            if packed is not None:
                candidates.append(packed)
    return _deduplicate(candidates)


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = output_dir / "refinement_results.json"
    candidates = generate_candidates(
        radii=args.radii,
        samples_per_radius=int(args.samples_per_radius),
        seed=int(args.seed),
    )
    systems = {name: _prepare_system(int(name[1:])) for name in ("H2", "H4", "H5")}
    payload: dict[str, Any] = {
        "status": "running",
        "method": {
            "model": "signed a4*t^4 + a6*t^6",
            "center": CENTER_NAME,
            "radii": list(args.radii),
            "samples_per_radius": int(args.samples_per_radius),
            "selection_systems": ["H2", "H4", "H5"],
            "reserved_systems": ["H6", "H7", "non-H-chain molecules"],
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    _write_json(checkpoint, _jsonable(payload))

    for index, candidate in enumerate(candidates, start=1):
        print(f"H2 {index}/{len(candidates)} {candidate['name']}", flush=True)
        candidate["systems"]["H2"] = evaluate_candidate_system(
            candidate,
            system_name="H2",
            system=systems["H2"],
            fit_times=DEFAULT_FIT_TIMES,
            relative_times=DEFAULT_RELATIVE_TIMES,
        )
        candidate["two_term"] = _candidate_summary(candidate)
        if index % 10 == 0:
            _write_json(checkpoint, _jsonable(payload))

    h2_shortlist = _select(
        candidates,
        maximum=int(args.h2_shortlist),
        required=("current_m3", "two_term_center"),
    )
    payload["h2_shortlist"] = [candidate["name"] for candidate in h2_shortlist]
    for candidate in h2_shortlist:
        for system_name in ("H4", "H5"):
            print(f"{candidate['name']} {system_name}", flush=True)
            candidate["systems"][system_name] = evaluate_candidate_system(
                candidate,
                system_name=system_name,
                system=systems[system_name],
                fit_times=DEFAULT_FIT_TIMES,
                relative_times=DEFAULT_RELATIVE_TIMES,
            )
        candidate["two_term"] = _candidate_summary(candidate)
        _write_json(checkpoint, _jsonable(payload))

    molecular_shortlist = _select(
        h2_shortlist,
        maximum=int(args.molecular_shortlist),
        required=("current_m3", "two_term_center"),
    )
    payload["molecular_shortlist"] = [
        candidate["name"] for candidate in molecular_shortlist
    ]
    payload["status"] = "complete"
    _write_json(checkpoint, _jsonable(payload))

    formulas = {
        candidate["name"]: {"formal_order": 4, "weights": candidate["weights"]}
        for candidate in molecular_shortlist
    }
    (output_dir / "cross_molecule_formulas.json").write_text(
        json.dumps(_jsonable(formulas), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_payload = {"finalists": molecular_shortlist}
    _report(output_dir / "hchain_report.md", report_payload)
    print(f"saved: {output_dir}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radii", type=float, nargs="+", default=[0.005, 0.015, 0.04])
    parser.add_argument("--samples-per-radius", type=int, default=48)
    parser.add_argument("--h2-shortlist", type=int, default=24)
    parser.add_argument("--molecular-shortlist", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260909)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
