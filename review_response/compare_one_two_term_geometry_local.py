"""Compare one- and two-term models on local molecular holdouts.

The implementation delegates all numerical definitions and thresholds to the
frozen comparison code at commit 73cdbf2.  Only the source directory and the
set of small stretched/nested-active-space Hamiltonians are changed.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from validate_two_term_geometry_local import _conditions


DEFAULT_RUNNER_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("artifacts/two_term_pf_geometry_local_20260911")
DEFAULT_OUTPUT = Path("artifacts/two_term_pf_geometry_local_20260911_ablation")
DEFAULT_CONDITIONS = (
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
)


def _complete(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("status") == "complete"
    except (OSError, ValueError):
        return False


def _install_adaptive_grid_comparison(comparison, holdout) -> None:
    """Accept the frozen runner's adaptive five-to-seven-point local grid."""

    def compare_saved(condition: str, formula_name: str, formula: dict):
        definitions = comparison._model_definitions(formula)
        validation = sorted(
            formula["local_direct_points"], key=lambda point: float(point["time"])
        )
        if len(validation) < 5:
            raise RuntimeError(f"{condition}/{formula_name}: local grid is too small")
        direct_minimum = min(
            (point for point in validation if point["direct_cost"] is not None),
            key=lambda point: float(point["direct_cost"]),
        )
        model_records = {}
        for model_name, definition in definitions.items():
            predictions = []
            for point in validation:
                predicted_shift = comparison._model_shift(
                    definition, float(point["time"])
                )
                predicted_cost = holdout._cost(
                    float(point["time"]),
                    abs(predicted_shift),
                    int(formula["rotations_per_pf_step"]),
                )
                direct_cost = point["direct_cost"]
                predictions.append(
                    {
                        "time": float(point["time"]),
                        "relative_to_t_ana": float(point["relative_to_t_ana"]),
                        "relative_to_t_star": float(point["relative_to_t_star"]),
                        "signed_direct_shift_hartree": float(
                            point["signed_direct_shift_hartree"]
                        ),
                        "signed_model_shift_hartree": predicted_shift,
                        "signed_residual_hartree": float(
                            point["signed_direct_shift_hartree"] - predicted_shift
                        ),
                        "residual_over_epsilon": float(
                            abs(
                                float(point["signed_direct_shift_hartree"])
                                - predicted_shift
                            )
                            / holdout.EPSILON_E
                        ),
                        "direct_cost": direct_cost,
                        "model_cost": predicted_cost,
                        "cost_relative_error": (
                            None
                            if direct_cost is None or predicted_cost is None
                            else abs(float(predicted_cost) - float(direct_cost))
                            / float(direct_cost)
                        ),
                    }
                )
            maximum_residual = max(
                float(point["residual_over_epsilon"]) for point in predictions
            )
            model_records[model_name] = {
                "definition": definition,
                "saved_unseen_predictions": predictions,
                "maximum_saved_unseen_residual_over_epsilon": maximum_residual,
                "maximum_saved_unseen_cost_relative_error": max(
                    float(point["cost_relative_error"])
                    for point in predictions
                    if point["cost_relative_error"] is not None
                ),
                "accepted_sampled_time_range": comparison._accepted_sampled_intervals(
                    predictions,
                    comparison.PASS_THRESHOLDS[
                        "maximum_saved_unseen_residual_over_epsilon"
                    ],
                ),
                "formal_predicted_time_direct_evaluation": (
                    "already_saved"
                    if model_name == "two_term"
                    else "additional_exact_direct_point_required"
                ),
            }
        return {
            "condition": condition,
            "formula": formula_name,
            "weights": formula["weights"],
            "rotations_per_pf_step": int(formula["rotations_per_pf_step"]),
            "training_points_relative_to_t_ana": list(
                holdout.TRAINING_RELATIVE_TIMES
            ),
            "training_points_excluded_from_validation": True,
            "saved_unseen_grid_relative_to_t_star": [
                float(point["relative_to_t_star"]) for point in validation
            ],
            "saved_unseen_point_count": len(validation),
            "saved_local_direct_minimum": {
                "time": float(direct_minimum["time"]),
                "relative_to_t_ana": float(direct_minimum["relative_to_t_ana"]),
                "relative_to_t_star": float(direct_minimum["relative_to_t_star"]),
                "direct_cost": float(direct_minimum["direct_cost"]),
            },
            "models": model_records,
        }

    comparison._saved_model_comparison = compare_saved


def run(args: argparse.Namespace) -> None:
    sys.path[:0] = [
        str(args.runner_root / "src"),
        str(args.runner_root / "review_response"),
    ]
    holdout = importlib.import_module("run_two_term_pf_m3_holdout_server2")
    comparison = importlib.import_module("compare_one_two_term_models_server2")
    available = _conditions(args.input_root)
    unknown = [name for name in args.conditions if name not in available]
    if unknown:
        raise ValueError(f"unknown conditions: {unknown}")
    holdout.CONDITIONS = {name: available[name] for name in args.conditions}
    comparison.holdout.CONDITIONS = holdout.CONDITIONS
    _install_adaptive_grid_comparison(comparison, holdout)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    additions = args.output_dir / "additional_direct"
    additions.mkdir(exist_ok=True)
    saved_path = args.output_dir / "saved_point_reaggregation.json"
    saved = comparison.reaggregate_saved(args.source_dir, saved_path)
    for condition in holdout.CONDITIONS:
        output = additions / f"{condition}.json"
        if _complete(output):
            print(f"{condition}: reuse complete ablation points", flush=True)
            continue
        worker_args = argparse.Namespace(
            condition=condition,
            source_dir=args.source_dir,
            output=output,
            blas_threads=int(args.blas_threads),
            component_processes=int(args.component_processes),
        )
        return_code = comparison.additional_worker(worker_args)
        if return_code:
            raise RuntimeError(f"{condition}: ablation worker failed")
    summary = comparison.aggregate_final(args.source_dir, args.output_dir, saved)
    summary["source_commit"] = "73cdbf200d348cc610d4c20f45a3208ce7ad2e7e"
    summary["scope_limit"] = (
        "Conclusions apply only to the eight frozen-core symmetric-stretch "
        "holdouts (STO-3G, 6-31G, or cc-pVDZ as declared) and four nested "
        "active-space holdouts evaluated here; they are not a claim for "
        "arbitrary molecules or continuous time."
    )
    summary["protocol"]["primary_common_unseen_points"] = (
        "the adaptive five-to-seven-point saved local direct grid within each "
        "condition/PF; all three models use the same points and denominators"
    )
    comparison._atomic_json(args.output_dir / "summary.json", summary)
    comparison.write_report(args.output_dir, summary)
    report_path = args.output_dir / "report.md"
    report = report_path.read_text(encoding="utf-8").replace(
        "The primary unseen set is the same seven saved local direct points "
        "for all three models.",
        "Within each condition/PF, all three models use the same adaptive "
        "five-to-seven-point saved local direct grid.",
    )
    report_path.write_text(report, encoding="utf-8")
    print(f"saved: {args.output_dir}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-root", type=Path, default=DEFAULT_RUNNER_ROOT)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("artifacts/nonhchain_active_space_local_20260908/inputs"),
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--conditions", nargs="+", default=list(DEFAULT_CONDITIONS))
    parser.add_argument("--blas-threads", type=int, default=4)
    parser.add_argument("--component-processes", type=int, default=4)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
