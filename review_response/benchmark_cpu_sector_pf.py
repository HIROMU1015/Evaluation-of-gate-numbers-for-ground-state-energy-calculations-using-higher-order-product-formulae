"""Benchmark exact CPU builders for the conserved-sector PF unitary."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import schur

from run_large_hchain_moment_phase import (
    M5_LABEL,
    Y8_LABEL,
    _prepare_sparse_sector_system,
)
from trotterlib.product_formula import _get_s2_sequence
from trotterlib.sector_pf import build_sector_pf_unitary


LABELS = {"m5": M5_LABEL, "y8": Y8_LABEL}


def _timed_builds(
    system: dict[str, Any],
    label: str,
    evolution_time: float,
    method: str,
    repeats: int,
) -> tuple[np.ndarray, list[float]]:
    durations: list[float] = []
    unitary: np.ndarray | None = None
    sequence = _get_s2_sequence(label)
    for _ in range(repeats):
        started = time.perf_counter()
        unitary = build_sector_pf_unitary(
            system["group_spectra"],
            sequence,
            evolution_time,
            method=method,
        )
        durations.append(time.perf_counter() - started)
    assert unitary is not None
    return unitary, durations


def _selected_branch(
    unitary: np.ndarray, system: dict[str, Any], evolution_time: float
) -> dict[str, float]:
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    eigenvalues = np.diag(triangular)
    probabilities = np.abs(vectors.conj().T @ system["state"]) ** 2
    selected = int(np.argmax(probabilities))
    rotated = np.exp(-1j * system["energy"] * evolution_time) * eigenvalues
    shift = float(np.angle(rotated[selected]) / evolution_time)
    return {
        "signed_energy_shift_hartree": shift,
        "direct_error_hartree": abs(shift),
        "ground_overlap_probability": float(probabilities[selected]),
    }


def run(
    h_chains: list[int],
    formula_keys: list[str],
    times: list[float],
    repeats: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "CPU conserved-sector PF unitary build benchmark",
        "python": sys.version,
        "repeats": repeats,
        "results": [],
    }
    for h_chain in h_chains:
        print(f"prepare H{h_chain}", flush=True)
        system = _prepare_sparse_sector_system(h_chain)
        for formula_key in formula_keys:
            label = LABELS[formula_key]
            sequence = _get_s2_sequence(label)
            for evolution_time in times:
                print(
                    f"H{h_chain} {formula_key} t={evolution_time:g}", flush=True
                )
                sequential, sequential_times = _timed_builds(
                    system,
                    label,
                    evolution_time,
                    "sequential",
                    repeats,
                )
                cached, cached_times = _timed_builds(
                    system,
                    label,
                    evolution_time,
                    "s2-cache",
                    repeats,
                )
                sequential_median = statistics.median(sequential_times)
                cached_median = statistics.median(cached_times)
                sequential_branch = _selected_branch(
                    sequential, system, evolution_time
                )
                cached_branch = _selected_branch(cached, system, evolution_time)
                payload["results"].append(
                    {
                        "system": f"H{h_chain}",
                        "sector_dimension": int(system["sector"]["dimension"]),
                        "formula_key": formula_key,
                        "label": label,
                        "time": evolution_time,
                        "s2_stages": len(sequence),
                        "unique_s2_stages": len(set(sequence)),
                        "sequential_seconds": sequential_times,
                        "cached_s2_seconds": cached_times,
                        "sequential_median_seconds": sequential_median,
                        "cached_s2_median_seconds": cached_median,
                        "speedup": sequential_median / cached_median,
                        "relative_unitary_frobenius_difference": float(
                            np.linalg.norm(cached - sequential)
                            / np.linalg.norm(sequential)
                        ),
                        "sequential_branch": sequential_branch,
                        "cached_s2_branch": cached_branch,
                        "signed_shift_absolute_difference_hartree": abs(
                            cached_branch["signed_energy_shift_hartree"]
                            - sequential_branch["signed_energy_shift_hartree"]
                        ),
                    }
                )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h-chains", nargs="+", type=int, default=[6])
    parser.add_argument(
        "--formulas", nargs="+", choices=sorted(LABELS), default=sorted(LABELS)
    )
    parser.add_argument("--times", nargs="+", type=float, default=[1.0])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.repeats < 1:
        raise ValueError("repeats must be positive")
    payload = run(args.h_chains, args.formulas, args.times, args.repeats)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
