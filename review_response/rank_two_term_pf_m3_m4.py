"""Re-rank existing fourth-order m=3/m=4 candidates with a two-term model.

The original searches used the leading ``alpha*t**4`` law.  This script
keeps their exact direct-eigenphase data and evaluates the signed model

    delta_E(t) = a4*t**4 + a6*t**6.

All candidates are first screened on H2.  A small Pareto-oriented subset is
then evaluated on H4/H5 when those records are absent.  The final output is a
small coefficient list for cross-molecule validation.  H6/H7 and non-H-chain
molecules are not used for coefficient selection here.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from search_pf_cost_predictability_m2_m3 import evaluate_candidate_system
from sweep_direct_scaling_h6_h7 import _write_json
from trotterlib.config import BETA, TARGET_ERROR
from validate_asymptotic_cost_small_systems import _prepare_system
from validate_pf_cost_predictability import DEFAULT_FIT_TIMES, DEFAULT_RELATIVE_TIMES


DEFAULT_M3 = Path(
    "artifacts/pf_cost_predictability_m3_refinement/refinement_results.json"
)
DEFAULT_M4 = Path(
    "artifacts/pf_cost_predictability_m4_m5_search/search_results.json"
)
DEFAULT_OUTPUT = Path("artifacts/two_term_pf_m3_m4_local_20260909")
CURRENT_M3 = "m3_local_c1_r2_s007"
KNOWN_M4 = ("m4_global_0098", "m4_global_0084")
FIT_MAXIMUM_RELATIVE_TIME = 0.30
VALIDATION_MAXIMUM_RELATIVE_TIME = 1.20


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


def _cost(time_value: float, error: float, rotations: int) -> float | None:
    if time_value <= 0.0 or error >= float(TARGET_ERROR):
        return None
    return float(
        BETA * int(rotations) / (time_value * (float(TARGET_ERROR) - error))
    )


def analyze_system(record: dict[str, Any]) -> dict[str, Any] | None:
    """Fit and validate the signed two-term model for one saved system."""

    points = sorted(record.get("direct_points", []), key=lambda row: row["relative_time"])
    training = [
        row
        for row in points
        if float(row["relative_time"]) <= FIT_MAXIMUM_RELATIVE_TIME + 1e-12
    ]
    schedule = next(
        (row for row in points if abs(float(row["relative_time"]) - 1.0) < 1e-12),
        None,
    )
    if len(training) < 3 or schedule is None:
        return None
    analytic_time = float(record["analytic_optimal_time"])
    rotations = int(record["pauli_rotations_per_step"])
    relative_training = np.asarray(
        [float(row["relative_time"]) for row in training], dtype=float
    )
    signed_training = np.asarray(
        [float(row["signed_direct_shift_hartree"]) for row in training], dtype=float
    )
    design = np.column_stack(
        [np.power(relative_training, 4), np.power(relative_training, 6)]
    )
    c4, c6 = (float(value) for value in np.linalg.lstsq(design, signed_training, rcond=None)[0])

    evaluated = []
    for point in points:
        relative_time = float(point["relative_time"])
        prediction_signed = c4 * relative_time**4 + c6 * relative_time**6
        prediction_error = abs(prediction_signed)
        actual_signed = float(point["signed_direct_shift_hartree"])
        model_cost = _cost(float(point["time"]), prediction_error, rotations)
        actual_cost = point["direct_cost"]
        evaluated.append(
            {
                "relative_time": relative_time,
                "time": float(point["time"]),
                "actual_signed_error_hartree": actual_signed,
                "predicted_signed_error_hartree": prediction_signed,
                "signed_residual_hartree": actual_signed - prediction_signed,
                "residual_over_epsilon": abs(actual_signed - prediction_signed)
                / float(TARGET_ERROR),
                "actual_cost": actual_cost,
                "model_cost": model_cost,
            }
        )
    schedule_evaluated = next(
        row for row in evaluated if abs(row["relative_time"] - 1.0) < 1e-12
    )
    schedule_cost_error = None
    if (
        schedule_evaluated["actual_cost"] is not None
        and schedule_evaluated["model_cost"] is not None
    ):
        schedule_cost_error = abs(
            float(schedule_evaluated["model_cost"])
            / float(schedule_evaluated["actual_cost"])
            - 1.0
        )
    validation = [
        row
        for row in evaluated
        if FIT_MAXIMUM_RELATIVE_TIME < row["relative_time"]
        <= VALIDATION_MAXIMUM_RELATIVE_TIME + 1e-12
    ]
    finite_direct = [row for row in evaluated if row["actual_cost"] is not None]
    direct_minimum = min(finite_direct, key=lambda row: float(row["actual_cost"]))

    dense_relative = np.linspace(0.10, 1.40, 26001)
    dense_time = analytic_time * dense_relative
    dense_error = np.abs(c4 * dense_relative**4 + c6 * dense_relative**6)
    dense_cost = np.full(dense_relative.shape, np.inf)
    valid = dense_error < float(TARGET_ERROR)
    dense_cost[valid] = (
        float(BETA)
        * rotations
        / (dense_time[valid] * (float(TARGET_ERROR) - dense_error[valid]))
    )
    optimum = int(np.argmin(dense_cost))
    return {
        "fit_maximum_relative_time": FIT_MAXIMUM_RELATIVE_TIME,
        "normalized_coefficients": {"c4": c4, "c6": c6},
        "absolute_coefficients": {
            "a4": c4 / analytic_time**4,
            "a6": c6 / analytic_time**6,
        },
        "rho6_at_one_term_analytic_time": abs(c6 / c4),
        "schedule_cost_relative_error": schedule_cost_error,
        "maximum_validation_residual_over_epsilon": max(
            row["residual_over_epsilon"] for row in validation
        ),
        "direct_grid_minimum": {
            "relative_time": direct_minimum["relative_time"],
            "cost": direct_minimum["actual_cost"],
        },
        "two_term_model_optimum": {
            "relative_time": float(dense_relative[optimum]),
            "time": float(dense_time[optimum]),
            "cost": float(dense_cost[optimum]),
        },
        "evaluated_points": evaluated,
    }


def _candidate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    analyses = {
        name: analyze_system(record)
        for name, record in candidate.get("systems", {}).items()
    }
    analyses = {name: row for name, row in analyses.items() if row is not None}
    if not analyses:
        return {"systems": {}, "objective": None}
    cost_errors = [
        float(row["schedule_cost_relative_error"])
        for row in analyses.values()
        if row["schedule_cost_relative_error"] is not None
    ]
    return {
        "systems": analyses,
        "objective": {
            "system_count": len(analyses),
            "worst_schedule_cost_relative_error": max(cost_errors),
            "worst_validation_residual_over_epsilon": max(
                float(row["maximum_validation_residual_over_epsilon"])
                for row in analyses.values()
            ),
            "median_direct_grid_minimum_cost": float(
                np.median(
                    [
                        float(row["direct_grid_minimum"]["cost"])
                        for row in analyses.values()
                    ]
                )
            ),
        },
    }


def _objectives(candidate: dict[str, Any]) -> tuple[float, float, float]:
    objective = candidate["two_term"]["objective"]
    if objective is None:
        return (math.inf, math.inf, math.inf)
    return (
        float(objective["worst_schedule_cost_relative_error"]),
        float(objective["worst_validation_residual_over_epsilon"]),
        float(objective["median_direct_grid_minimum_cost"]),
    )


def pareto_front(candidates: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [candidate for candidate in candidates if candidate["two_term"]["objective"]]
    result = []
    for candidate in eligible:
        values = _objectives(candidate)
        dominated = any(
            all(other_value <= value for other_value, value in zip(_objectives(other), values))
            and any(other_value < value for other_value, value in zip(_objectives(other), values))
            for other in eligible
            if other is not candidate
        )
        if not dominated:
            result.append(candidate)
    return sorted(result, key=_objectives)


def _select(
    candidates: Sequence[dict[str, Any]], *, maximum: int, required: Iterable[str] = ()
) -> list[dict[str, Any]]:
    """Keep Pareto extremes and a normalized-objective knee."""

    eligible = [candidate for candidate in candidates if candidate["two_term"]["objective"]]
    by_name = {str(candidate["name"]): candidate for candidate in eligible}
    selected: list[dict[str, Any]] = []

    def add(candidate: dict[str, Any] | None) -> None:
        if candidate is not None and candidate not in selected and len(selected) < maximum:
            selected.append(candidate)

    for name in required:
        add(by_name.get(name))
    front = pareto_front(eligible)
    for objective_index in range(3):
        add(min(front, key=lambda row: _objectives(row)[objective_index], default=None))
    if front:
        matrix = np.asarray([_objectives(row) for row in front], dtype=float)
        minima = matrix.min(axis=0)
        spans = matrix.max(axis=0) - minima
        spans[spans == 0.0] = 1.0
        distances = np.linalg.norm((matrix - minima) / spans, axis=1)
        for index in np.argsort(distances):
            add(front[int(index)])
    for candidate in sorted(eligible, key=_objectives):
        add(candidate)
    return selected


def _load(path: Path, m: int) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [candidate for candidate in payload["candidates"] if int(candidate["m"]) == int(m)]


def _report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# 4次PF m=3/m=4 二項モデル再探索（ローカル）",
        "",
        "保存済みの全候補をH2の符号付き直接誤差で再順位付けし、上位候補のみH4/H5を追加評価した。係数選択にはH6/H7および非H-chain分子を使っていない。",
        "",
        "## 最終候補",
        "",
        "| m | 候補 | 検証系数 | 最大コスト予測誤差 | 最大残差 / 目標誤差 | 直接格子最小コスト中央値 |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for candidate in payload["finalists"]:
        objective = candidate["two_term"]["objective"]
        lines.append(
            f"| {candidate['m']} | {candidate['name']} | {objective['system_count']} | "
            f"{100.0*objective['worst_schedule_cost_relative_error']:.3f}% | "
            f"{objective['worst_validation_residual_over_epsilon']:.4f} | "
            f"{objective['median_direct_grid_minimum_cost']:.6g} |"
        )
    lines.extend(
        [
            "",
            "最大コスト予測誤差は各PF自身の一項モデル解析時刻で評価した。最大残差は二項フィットに使わなかった $0.4$〜$1.2t_{\\mathrm{ana}}$ の計算点に対する値である。",
            "",
            "次段階では、これらの係数をLiH、BeH2、H2Oの複数基底へ適用し、二項モデルが予測した最適時刻とその前後を直接PF固有値誤差で検査する。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates_by_m = {3: _load(args.m3_input, 3), 4: _load(args.m4_input, 4)}
    for candidates in candidates_by_m.values():
        for candidate in candidates:
            candidate["two_term"] = _candidate_summary(candidate)

    h2_shortlists = {
        3: _select(candidates_by_m[3], maximum=args.h2_shortlist, required=(CURRENT_M3,)),
        4: _select(candidates_by_m[4], maximum=args.h2_shortlist, required=KNOWN_M4),
    }
    systems = {name: _prepare_system(int(name[1:])) for name in ("H4", "H5")}
    checkpoint = output_dir / "search_results.json"
    for m, shortlist in h2_shortlists.items():
        for candidate in shortlist:
            for system_name, system in systems.items():
                existing = candidate.get("systems", {}).get(system_name, {})
                if not existing.get("direct_points"):
                    print(f"m={m} {candidate['name']} {system_name}", flush=True)
                    candidate.setdefault("systems", {})[system_name] = evaluate_candidate_system(
                        candidate,
                        system_name=system_name,
                        system=system,
                        fit_times=DEFAULT_FIT_TIMES,
                        relative_times=DEFAULT_RELATIVE_TIMES,
                    )
            candidate["two_term"] = _candidate_summary(candidate)
            _write_json(
                checkpoint,
                _jsonable(
                    {
                        "status": "running",
                        "h2_shortlists": {
                            str(key): [row["name"] for row in value]
                            for key, value in h2_shortlists.items()
                        },
                        "evaluated": h2_shortlists[3] + h2_shortlists[4],
                    }
                ),
            )

    finalists = []
    finalists.extend(
        _select(h2_shortlists[3], maximum=args.finalists_per_m, required=(CURRENT_M3,))
    )
    finalists.extend(
        _select(h2_shortlists[4], maximum=args.finalists_per_m, required=(KNOWN_M4[0],))
    )
    formula_payload = {
        f"m{candidate['m']}_{candidate['name']}": {
            "formal_order": 4,
            "weights": candidate["weights"],
        }
        for candidate in finalists
    }
    (output_dir / "cross_molecule_formulas.json").write_text(
        json.dumps(_jsonable(formula_payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    payload = {
        "status": "complete",
        "method": {
            "model": "signed a4*t^4 + a6*t^6",
            "fit_relative_times": [0.1, 0.2, 0.3],
            "validation_relative_interval": [0.4, 1.2],
            "selection_systems": ["H2", "H4", "H5"],
            "reserved_systems": ["H6", "H7", "non-H-chain molecules"],
        },
        "candidate_counts": {
            "m3": len(candidates_by_m[3]),
            "m4": len(candidates_by_m[4]),
        },
        "h2_shortlists": {
            str(key): [row["name"] for row in value]
            for key, value in h2_shortlists.items()
        },
        "finalists": finalists,
    }
    _write_json(checkpoint, _jsonable(payload))
    _report(output_dir / "report.md", payload)
    print(f"saved: {output_dir}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3-input", type=Path, default=DEFAULT_M3)
    parser.add_argument("--m4-input", type=Path, default=DEFAULT_M4)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--h2-shortlist", type=int, default=8)
    parser.add_argument("--finalists-per-m", type=int, default=3)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
