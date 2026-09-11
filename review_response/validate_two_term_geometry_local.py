"""Run exact two-term PF holdouts on small molecular perturbations.

This is a thin local driver around the frozen server validation protocol from
commit 73cdbf2.  It changes only the holdout Hamiltonians; PF coefficients,
fit grids, model construction, direct-eigenphase labels, and pass thresholds
remain those of the committed protocol.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import numpy as np


DEFAULT_RUNNER_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ROOT = Path(
    "artifacts/nonhchain_active_space_local_20260908/inputs"
)
DEFAULT_OUTPUT = Path(
    "artifacts/two_term_pf_geometry_local_20260911"
)


def _load_runner(root: Path) -> ModuleType:
    source_root = root / "src"
    response_root = root / "review_response"
    script = response_root / "run_two_term_pf_m3_holdout_server2.py"
    if not script.exists():
        raise FileNotFoundError(f"missing frozen validation runner: {script}")
    sys.path[:0] = [str(source_root), str(response_root)]
    spec = importlib.util.spec_from_file_location("frozen_two_term_runner", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_xyz(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    atom_count = int(lines[0])
    geometry = []
    for line in lines[2 : 2 + atom_count]:
        fields = line.split()
        geometry.append(
            (fields[0], tuple(float(value) for value in fields[1:4]))
        )
    if len(geometry) != atom_count:
        raise ValueError(f"could not read {atom_count} atoms from {path}")
    return geometry


def _stretch_xh(geometry, factor: float):
    heavy = [np.asarray(position) for symbol, position in geometry if symbol != "H"]
    if len(heavy) != 1:
        raise ValueError("the local geometry holdout expects one heavy atom")
    center = heavy[0]
    result = []
    for symbol, position in geometry:
        vector = np.asarray(position, dtype=float)
        if symbol == "H":
            vector = center + float(factor) * (vector - center)
        result.append((symbol, tuple(float(value) for value in vector)))
    return result


def _conditions(input_root: Path):
    geometry_specifications = {
        "BeH2_stretch125": ("beh2_reference.xyz", 1.25, 6, "sto-3g"),
        "BeH2_stretch150": ("beh2_reference.xyz", 1.50, 6, "sto-3g"),
        "H2O_stretch125": ("h2o_qm9_reference.xyz", 1.25, 6, "sto-3g"),
        "H2O_stretch150": ("h2o_qm9_reference.xyz", 1.50, 6, "sto-3g"),
        "BeH2_stretch150_631g": ("beh2_reference.xyz", 1.50, 6, "6-31g"),
        "BeH2_stretch150_ccpvdz": (
            "beh2_reference.xyz", 1.50, 6, "cc-pvdz"
        ),
        "H2O_stretch150_631g": (
            "h2o_qm9_reference.xyz", 1.50, 6, "6-31g"
        ),
        "H2O_stretch150_ccpvdz": (
            "h2o_qm9_reference.xyz", 1.50, 6, "cc-pvdz"
        ),
    }
    result = {}
    for name, (
        xyz_name,
        factor,
        active_orbitals,
        basis,
    ) in geometry_specifications.items():
        geometry = _stretch_xh(_read_xyz(input_root / xyz_name), factor)
        result[name] = {
            "geometry": geometry,
            "basis": basis,
            "multiplicity": 1,
            "charge": 0,
            "frozen_core_spatial_orbitals": 1,
            "active_spatial_orbitals": int(active_orbitals),
            "selection_role": (
                "unused symmetric X-H stretch holdout; coefficients frozen"
            ),
        }
    active_space_specifications = {
        "LiH_CAS2e3o": ("lih_reference.xyz", 3),
        "LiH_CAS2e4o": ("lih_reference.xyz", 4),
        "BeH2_CAS4e3o": ("beh2_reference.xyz", 3),
        "BeH2_CAS4e4o": ("beh2_reference.xyz", 4),
        "BeH2_CAS4e5o": ("beh2_reference.xyz", 5),
        "H2O_CAS8e5o": ("h2o_qm9_reference.xyz", 5),
    }
    for name, (xyz_name, active_orbitals) in active_space_specifications.items():
        result[name] = {
            "geometry": _read_xyz(input_root / xyz_name),
            "basis": "sto-3g",
            "multiplicity": 1,
            "charge": 0,
            "frozen_core_spatial_orbitals": 1,
            "active_spatial_orbitals": int(active_orbitals),
            "selection_role": (
                "unused nested active-space holdout; coefficients frozen"
            ),
        }
    return result


def _write_report(output_dir: Path, summary: dict) -> None:
    lines = [
        "# Fixed m=3 two-term PF: local geometry and active-space holdouts",
        "",
        f"Status: {summary['status']}",
        "",
        (
            "The `two_term_center` coefficients were kept fixed. Stretched "
            "geometries and the smaller nested active spaces were not used "
            "to select these coefficients."
        ),
        "",
        (
            "| condition | formula | eta_* | eta_min | eta_t | "
            "max unseen residual / epsilon | new/current direct cost | pass |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for condition, record in summary["records"].items():
        cost_ratio = record["comparison"][
            "direct_cost_at_each_formulas_own_predicted_optimum_ratio_new_over_current"
        ]
        for formula_name, formula in record["formula_summaries"].items():
            metrics = formula.get("metrics") or {}
            lines.append(
                f"| {condition} | {formula_name} | "
                f"{metrics.get('eta_star', float('nan')):.6g} | "
                f"{metrics.get('eta_min', float('nan')):.6g} | "
                f"{metrics.get('eta_t', float('nan')):.6g} | "
                f"{metrics.get('maximum_unseen_residual_over_epsilon', float('nan')):.6g} | "
                f"{cost_ratio:.6g} | {formula.get('passed')} |"
            )
    lines.extend(
        [
            "",
            (
                "The cost ratio is reported separately from prediction "
                "accuracy and compares each PF at its own two-term predicted optimum."
            ),
            (
                "eta_t is resolved only on the declared local grid and is "
                "not a continuous-optimum claim."
            ),
            (
                "Three-active-orbital cases are excluded because the frozen "
                "grouping implementation requires at least four active orbitals; "
                "changing the grouping would change the tested PF decomposition."
            ),
            "",
        ]
    )
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    runner = _load_runner(args.runner_root)
    available = _conditions(args.input_root)
    unknown = [name for name in args.conditions if name not in available]
    if unknown:
        raise ValueError(f"unknown conditions: {unknown}")
    runner.CONDITIONS = {name: available[name] for name in args.conditions}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for condition in runner.CONDITIONS:
        output = args.output_dir / f"{condition}.json"
        if output.exists() and runner._read_status(output).get("status") == "complete":
            print(f"{condition}: reuse complete result", flush=True)
        else:
            worker_args = argparse.Namespace(
                condition=condition,
                output=output,
                blas_threads=int(args.blas_threads),
                component_processes=int(args.component_processes),
            )
            return_code = runner.worker(worker_args)
            if return_code:
                raise RuntimeError(f"{condition} failed with status {return_code}")
        record = runner.json.loads(output.read_text(encoding="utf-8"))
        record["selection_provenance"] = {
            "candidate_narrowing": ["H2", "H4", "H5"],
            "final_selection": [
                "LiH x 3 bases at reference geometry",
                "BeH2 x 3 bases at reference geometry",
                "H2O x 3 bases at reference geometry",
            ],
            "unused_holdout_evaluated_here": condition,
        }
        runner._atomic_json(output, record)
    summary = runner._aggregate(args.output_dir)
    summary["new_candidate_all_declared_conditions_passed"] = summary.pop(
        "new_candidate_all_five_conditions_passed"
    )
    summary["excluded_conditions"] = {
        "LiH_CAS2e3o": "grouping implementation requires >= 4 active orbitals",
        "BeH2_CAS4e3o": "grouping implementation requires >= 4 active orbitals",
    }
    runner._atomic_json(args.output_dir / "summary.json", summary)
    _write_report(args.output_dir, summary)
    print(f"saved: {args.output_dir}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-root", type=Path, default=DEFAULT_RUNNER_ROOT)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=[
            "BeH2_stretch125",
            "BeH2_stretch150",
            "H2O_stretch125",
            "H2O_stretch150",
            "BeH2_stretch150_631g",
            "BeH2_stretch150_ccpvdz",
            "H2O_stretch150_631g",
            "H2O_stretch150_ccpvdz",
            "LiH_CAS2e4o",
            "BeH2_CAS4e4o",
            "BeH2_CAS4e5o",
            "H2O_CAS8e5o",
        ],
    )
    parser.add_argument("--blas-threads", type=int, default=4)
    parser.add_argument("--component-processes", type=int, default=4)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
