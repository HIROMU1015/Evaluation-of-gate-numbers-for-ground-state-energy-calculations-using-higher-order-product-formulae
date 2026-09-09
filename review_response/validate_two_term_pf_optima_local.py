"""Directly check two-term-model optima for shortlisted molecular PFs.

This local driver reuses the exact component-sector implementation from a
prepared validation worktree.  It does not use the overlap phase as the final
label: every reported cost is obtained from the ground-connected eigenphase
of the explicitly constructed PF unitary.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np


DEFAULT_ANALYSIS = Path(
    "artifacts/two_term_pf_m3_m4_local_20260909/cross_molecule_analysis.json"
)
DEFAULT_RAW = Path(
    "artifacts/two_term_pf_m3_m4_local_20260909/cross_molecule"
)
DEFAULT_OUTPUT = Path(
    "artifacts/two_term_pf_m3_m4_local_20260909/optimum_direct_checks.json"
)
DEFAULT_RUNNER_ROOT = Path("/tmp/pf-valid-review-3f47b59")
DEFAULT_FORMULAS = (
    "m3_m3_local_c1_r2_s007",
    "m3_m3_local_c2_r1_s016",
    "m4_m4_global_0098",
    "m4_m4_global_0035",
)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_runner(root: Path) -> ModuleType:
    source_root = root / "src"
    script = root / "review_response" / "validate_m3_nonhchain_local.py"
    if not script.exists():
        raise FileNotFoundError(f"validation runner is absent: {script}")
    sys.path.insert(0, str(source_root))
    spec = importlib.util.spec_from_file_location("nonhchain_exact_runner", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args: argparse.Namespace) -> dict[str, Any]:
    runner = _load_runner(args.runner_root)
    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    selected = set(args.formulas)
    analysis_records = {
        (str(row["system"]["name"]), str(row["formula"])): row
        for row in analysis["records"]
        if str(row["formula"]) in selected
    }
    raw_files = sorted(
        path
        for path in args.raw_dir.glob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("status") == "complete"
    )
    payload: dict[str, Any] = {
        "status": "running",
        "method": {
            "labels": "direct ground-connected PF eigenphases",
            "relative_to_predicted_optimum": [0.9, 1.0, 1.1],
            "runner_root": str(args.runner_root),
        },
        "formulas": list(args.formulas),
        "records": [],
    }
    _write(args.output, payload)
    for raw_path in raw_files:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        metadata = raw["system"]
        system_name = str(metadata["name"])
        print(f"prepare {system_name}", flush=True)
        system, check_metadata = runner._prepare_system(
            system_name + "_optimum_check",
            metadata["geometry_angstrom"],
            processes=int(args.processes),
            frozen_core_orbitals=int(metadata["frozen_core_spatial_orbitals"]),
            locked_core_orbitals=int(metadata["locked_core_spatial_orbitals"]),
            active_orbitals=int(metadata["active_spatial_orbitals"]),
            basis=str(metadata["basis"]),
        )
        hashes_match = {
            key: check_metadata[key] == metadata[key]
            for key in (
                "ordered_grouping_structure_sha256",
                "unordered_grouping_structure_sha256",
                "hamiltonian_term_order_sha256",
            )
        }
        for formula_name in args.formulas:
            key = (system_name, formula_name)
            if key not in analysis_records:
                raise KeyError(f"missing analysis record: {key}")
            model = analysis_records[key]
            formula = raw["formulas"][formula_name]
            predicted = model["two_term_model_optimum"]
            optimum_relative = float(predicted["relative_to_one_term_analytic_time"])
            relative_grid = [0.9 * optimum_relative, optimum_relative, 1.1 * optimum_relative]
            sequence = runner.symmetric_s2_sequence(formula["weights"])
            rotations = runner._rotation_count(system, sequence)
            print(f"{system_name} {formula_name} at two-term optimum", flush=True)
            points = runner._direct_points(
                system,
                sequence,
                float(formula["alpha"]),
                float(formula["analytic_time"]),
                rotations,
                relative_grid,
                int(formula["formal_order"]),
            )
            center = points[1]
            actual_cost = center["direct_cost"]
            predicted_cost = float(predicted["cost"])
            finite = [point for point in points if point["direct_cost"] is not None]
            neighborhood_minimum = min(finite, key=lambda point: point["direct_cost"])
            payload["records"].append(
                {
                    "source": str(raw_path),
                    "system": system_name,
                    "formula": formula_name,
                    "weights": formula["weights"],
                    "s2_stage_count": int(formula["s2_stage_count"]),
                    "rotations_per_pf_step": rotations,
                    "one_term_analytic_time": float(formula["analytic_time"]),
                    "two_term_predicted_optimum": predicted,
                    "direct_points": points,
                    "direct_cost_at_predicted_optimum": actual_cost,
                    "predicted_to_direct_cost_relative_error": (
                        None
                        if actual_cost is None
                        else abs(predicted_cost / float(actual_cost) - 1.0)
                    ),
                    "neighborhood_direct_minimum": {
                        "relative_to_one_term_analytic_time": neighborhood_minimum[
                            "relative_time"
                        ],
                        "cost": neighborhood_minimum["direct_cost"],
                    },
                    "predicted_optimum_to_neighborhood_minimum_cost_ratio": (
                        None
                        if actual_cost is None
                        else float(actual_cost)
                        / float(neighborhood_minimum["direct_cost"])
                    ),
                    "hamiltonian_and_grouping_hashes_match": hashes_match,
                }
            )
            _write(args.output, payload)
    aggregates = {}
    for formula_name in args.formulas:
        rows = [row for row in payload["records"] if row["formula"] == formula_name]
        aggregates[formula_name] = {
            "record_count": len(rows),
            "maximum_predicted_to_direct_cost_relative_error": max(
                float(row["predicted_to_direct_cost_relative_error"])
                for row in rows
                if row["predicted_to_direct_cost_relative_error"] is not None
            ),
            "maximum_predicted_optimum_to_neighborhood_minimum_cost_ratio": max(
                float(row["predicted_optimum_to_neighborhood_minimum_cost_ratio"])
                for row in rows
                if row["predicted_optimum_to_neighborhood_minimum_cost_ratio"] is not None
            ),
            "minimum_ground_overlap_probability": min(
                float(point["ground_overlap_probability"])
                for row in rows
                for point in row["direct_points"]
            ),
            "maximum_eigenpair_residual_2_norm": max(
                float(point["eigenpair_residual_2_norm"])
                for row in rows
                for point in row["direct_points"]
            ),
            "all_hashes_match": all(
                all(row["hamiltonian_and_grouping_hashes_match"].values()) for row in rows
            ),
        }
    payload["aggregates"] = aggregates
    payload["status"] = "complete"
    _write(args.output, payload)
    print(f"saved: {args.output}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--runner-root", type=Path, default=DEFAULT_RUNNER_ROOT)
    parser.add_argument("--formulas", nargs="+", default=list(DEFAULT_FORMULAS))
    parser.add_argument("--processes", type=int, default=4)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
