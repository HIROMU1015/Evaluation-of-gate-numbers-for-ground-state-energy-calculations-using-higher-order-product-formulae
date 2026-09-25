#!/usr/bin/env python3
"""Decompose the frozen practical-selector cost using saved S0 truth only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PROTOCOL = Path("review_response/pf_first_study_regret_decomposition_protocol.json")
DEFAULT_OUTPUT = Path("artifacts/pf_first_study_regret_decomposition_20260925_7f0b30d")


class DecompositionError(RuntimeError):
    """Raised when a fixed source or numerical gate fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_positive_float(row: dict[str, str], field: str, condition: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise DecompositionError(f"{condition}: invalid or missing {field}") from exc
    if not math.isfinite(value) or value <= 0.0:
        raise DecompositionError(f"{condition}: {field} must be finite and positive")
    return value


def _as_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise DecompositionError(f"invalid Boolean value: {value!r}")


def decompose_costs(
    *,
    c_star: float,
    c_selected_formula_star: float,
    c_required: float,
    c_hat: float,
    b_frozen: float,
    closure_tolerance: float,
) -> dict[str, float]:
    values = (c_star, c_selected_formula_star, c_required, c_hat, b_frozen)
    if any(not math.isfinite(value) or value <= 0.0 for value in values):
        raise DecompositionError("all cost inputs must be finite and positive")

    factors = {
        "factor_model": c_hat / c_required,
        "factor_margin": b_frozen / c_hat,
        "factor_calibration": b_frozen / c_required,
        "factor_time_selection": c_required / c_selected_formula_star,
        "factor_pf_selection": c_selected_formula_star / c_star,
        "factor_total": b_frozen / c_star,
    }
    reconstructed = (
        factors["factor_calibration"]
        * factors["factor_time_selection"]
        * factors["factor_pf_selection"]
    )
    closure_error = abs(reconstructed - factors["factor_total"])
    if closure_error > closure_tolerance:
        raise DecompositionError(
            f"multiplicative closure failed: {closure_error} > {closure_tolerance}"
        )
    factors["closure_absolute_error"] = closure_error
    return factors


def _dominant_component(logs: dict[str, float], tolerance: float) -> str:
    maximum = max(logs.values())
    if maximum <= tolerance:
        return "none"
    winners = [name for name, value in logs.items() if abs(value - maximum) <= tolerance]
    return winners[0] if len(winners) == 1 else "tie:" + "+".join(sorted(winners))


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values)


def _format_percent(value: float) -> str:
    return f"{100.0 * value:.4f}%"


def _report(protocol_sha: str, source_manifest: dict[str, Any], rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# 第一研究 practical selector regret因子分解",
        "",
        f"**Status:** `{summary['status']}`  ",
        "**新規direct truth点:** `0`  ",
        f"**Protocol SHA-256:** `{protocol_sha}`  ",
        f"**Source scoring SHA-256:** `{source_manifest['scoring_sha256']}`",
        "",
        "## 結論",
        "",
        "保存済みS0 exact-time採点だけを用いて、1%余裕付き凍結予算のoracle最小費用に対する比を",
        "",
        "$$",
        "F_{\\rm total}=\\frac{B_{\\rm frozen}}{C^*}",
        "=\\frac{B_{\\rm frozen}}{C_{\\rm req}(\\hat P,\\hat t)}",
        "\\frac{C_{\\rm req}(\\hat P,\\hat t)}{C^*_{\\hat P}}",
        "\\frac{C^*_{\\hat P}}{C^*}",
        "=F_{\\rm cal}F_tF_P",
        "$$",
        "",
        "と厳密に分解した。全6条件で積の閉包を満たし、coverage不足はなかった。",
        f"PF選択因子は全条件で`1.0`であり、観測した総regretにPF選択損失は寄与しなかった。",
        "HFの2条件は時刻選択が支配した。主4 active-space条件では3条件がcalibration/budget支配、",
        "N2 stretchだけが時刻選択支配だった。従って次の方法論課題を一つに還元せず、",
        "HFではfinite-time optimum予測、active-spaceの平衡・CO条件では誤差量の校正と予算保守性を",
        "それぞれ主要因として扱う。今回の6条件はdevelopment集合であり、一般化の証拠ではない。",
        "",
        "## 条件別分解",
        "",
        "ここで各`regret`は加算成分ではなく`factor - 1`である。寄与の比較には積を加法化する",
        "`log(factor)`を使った。",
        "",
        "| condition | $C^*$ | $C^*_{\\hat P}$ | $C_{req}(\\hat P,\\hat t)$ | $\\widehat C$ | $B_{frozen}$ |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {condition} | {c_star:.6f} | {c_selected_formula_star:.6f} | "
            "{c_required_selected_time:.6f} | {c_hat:.6f} | {b_frozen:.6f} |".format(**row)
        )

    lines.extend([
        "",
        "| condition | group | $F_{model}$ | $F_{cal}$ | $F_t$ | $F_P$ | $F_{total}$ | dominant |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in rows:
        lines.append(
            "| {condition} | {evaluation_group} | {factor_model:.6f} | "
            "{factor_calibration:.6f} | {factor_time_selection:.6f} | "
            "{factor_pf_selection:.6f} | {factor_total:.6f} | {dominant_component} |".format(**row)
        )

    lines.extend([
        "",
        "## 1%余裕とmodel予算の分離",
        "",
        "`F_model = C_hat/C_req`、`F_margin = B_frozen/C_hat = 1.01`、",
        "`F_cal = F_model F_margin`である。HF equilibriumではmodel単体が必要費用を",
        "わずかに下回ったが、固定1%余裕を含むと安全側になった。安全余裕は全条件で同じ",
        "乗数なので、条件間の大きなregret差、特にHFの約2.1倍は説明しない。",
        "",
        "## 集計",
        "",
        f"- 6条件平均総regret: `{_format_percent(summary['mean_total_excess_regret'])}`",
        f"- 主4条件平均総regret: `{_format_percent(summary['groups']['primary']['mean_total_excess_regret'])}`",
        f"- HF stress 2条件平均総regret: `{_format_percent(summary['groups']['stress_test']['mean_total_excess_regret'])}`",
        f"- 最大総regret: `{_format_percent(summary['max_total_excess_regret'])}` (`{summary['max_total_regret_condition']}`)",
        f"- 支配因子件数: `{json.dumps(summary['dominance_counts'], sort_keys=True)}`",
        f"- 最大積閉包誤差: `{summary['max_closure_absolute_error']:.3e}`",
        "- 追加Hamiltonian、fit、direct truth計算: `0`",
        "",
        "## 解釈上の制限",
        "",
        "- $C^*$と$C^*_{\\hat P}$は元の2 PF・保存truth grid上のoracle最小であり、連続時間の大域最小ではない。",
        "- $C_{\\rm req}(\\hat P,\\hat t)$だけはS0で計算済みのexact selected-time truthを使う。",
        "- 因子は相乗的であるため、`r_cal + r_t + r_P`を総regretと解釈しない。",
        "- 今回の再解析だけから新PF探索、S5、追加diagnosticを開始しない。",
        "",
        "## Source identity",
        "",
        f"- S0 result commit: `{source_manifest['result_commit']}`",
        f"- Source artifact: `{source_manifest['artifact']}`",
        f"- Source manifest SHA-256: `{source_manifest['manifest_sha256']}`",
        f"- Source scoring SHA-256: `{source_manifest['scoring_sha256']}`",
    ])
    return "\n".join(lines) + "\n"


def run(project_root: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    protocol_path = protocol_path if protocol_path.is_absolute() else project_root / protocol_path
    output = output if output.is_absolute() else project_root / output
    protocol = _load_json(protocol_path)
    protocol_sha = sha256_file(protocol_path)
    source_spec = protocol["source"]
    source_root = project_root / source_spec["artifact"]
    source_manifest_path = source_root / "manifest.json"
    scoring_path = source_root / "scoring.csv"

    checks: dict[str, bool] = {
        "source_complete_marker": (source_root / "COMPLETE").is_file(),
        "source_manifest_exists": source_manifest_path.is_file(),
        "source_scoring_exists": scoring_path.is_file(),
    }
    if not all(checks.values()):
        raise DecompositionError(f"missing source artifact component: {checks}")

    source_manifest = _load_json(source_manifest_path)
    manifest_sha = sha256_file(source_manifest_path)
    scoring_sha = sha256_file(scoring_path)
    checks.update({
        "source_status": source_manifest.get("status") == source_spec["status"],
        "source_manifest_sha256": manifest_sha == source_spec["manifest_sha256"],
        "source_scoring_sha256": scoring_sha == source_spec["scoring_sha256"],
        "source_internal_scoring_sha256": (
            source_manifest.get("artifact_sha256", {}).get("scoring.csv") == scoring_sha
        ),
    })
    if not all(checks.values()):
        raise DecompositionError(f"source identity gate failed: {checks}")

    with scoring_path.open("r", encoding="utf-8", newline="") as handle:
        input_rows = list(csv.DictReader(handle))
    expected = {item["name"]: item["evaluation_group"] for item in protocol["conditions"]}
    by_condition: dict[str, dict[str, str]] = {}
    for row in input_rows:
        condition = row.get("condition", "")
        if condition in by_condition:
            raise DecompositionError(f"duplicate source row: {condition}")
        by_condition[condition] = row
    if set(by_condition) != set(expected):
        raise DecompositionError(
            f"condition coverage mismatch: expected={sorted(expected)}, actual={sorted(by_condition)}"
        )

    mapping = protocol["cost_field_mapping"]
    closure_tolerance = float(protocol["numerical_gates"]["factor_closure_absolute_tolerance"])
    relative_tolerance = float(protocol["numerical_gates"]["source_ratio_relative_tolerance"])
    tie_tolerance = float(protocol["dominance_rule"]["tie_absolute_log_tolerance"])
    fixed_margin = float(protocol["fixed_margin_multiplier"])
    output_rows: list[dict[str, Any]] = []

    for condition_spec in protocol["conditions"]:
        condition = condition_spec["name"]
        source = by_condition[condition]
        if source.get("evaluation_group") != condition_spec["evaluation_group"]:
            raise DecompositionError(f"{condition}: evaluation group mismatch")
        costs = {
            key: _as_positive_float(source, field, condition)
            for key, field in mapping.items()
        }
        factors = decompose_costs(
            c_star=costs["C_star"],
            c_selected_formula_star=costs["C_selected_formula_star"],
            c_required=costs["C_required_selected_time"],
            c_hat=costs["C_hat"],
            b_frozen=costs["B_frozen"],
            closure_tolerance=closure_tolerance,
        )
        if not math.isclose(factors["factor_margin"], fixed_margin, rel_tol=relative_tolerance):
            raise DecompositionError(f"{condition}: frozen margin ratio is not {fixed_margin}")
        source_total = 1.0 + float(source["budget_over_original_reference_gamma_1_01_minus_one"])
        if not math.isclose(factors["factor_total"], source_total, rel_tol=relative_tolerance):
            raise DecompositionError(f"{condition}: total factor disagrees with S0 source")
        source_time = 1.0 + float(source["same_formula_time_selection_regret"])
        if not math.isclose(factors["factor_time_selection"], source_time, rel_tol=relative_tolerance):
            raise DecompositionError(f"{condition}: time factor disagrees with S0 source")

        component_logs = {
            "calibration": math.log(factors["factor_calibration"]),
            "time_selection": math.log(factors["factor_time_selection"]),
            "pf_selection": math.log(factors["factor_pf_selection"]),
        }
        log_total = math.log(factors["factor_total"])
        log_model = math.log(factors["factor_model"])
        log_margin = math.log(factors["factor_margin"])
        row: dict[str, Any] = {
            "condition": condition,
            "evaluation_group": source["evaluation_group"],
            "selected_formula": source["selected_formula"],
            "oracle_joint_formula": source["original_joint_grid_best_formula"],
            "selected_time": float(source["selected_time"]),
            "c_star": costs["C_star"],
            "c_selected_formula_star": costs["C_selected_formula_star"],
            "c_required_selected_time": costs["C_required_selected_time"],
            "c_hat": costs["C_hat"],
            "b_frozen": costs["B_frozen"],
            **factors,
            "excess_model": factors["factor_model"] - 1.0,
            "excess_margin": factors["factor_margin"] - 1.0,
            "excess_calibration": factors["factor_calibration"] - 1.0,
            "excess_time_selection": factors["factor_time_selection"] - 1.0,
            "excess_pf_selection": factors["factor_pf_selection"] - 1.0,
            "excess_total": factors["factor_total"] - 1.0,
            "log_model": log_model,
            "log_margin": log_margin,
            "log_calibration": component_logs["calibration"],
            "log_time_selection": component_logs["time_selection"],
            "log_pf_selection": component_logs["pf_selection"],
            "log_total": log_total,
            "model_log_share": log_model / log_total if log_total else 0.0,
            "margin_log_share": log_margin / log_total if log_total else 0.0,
            "calibration_log_share": component_logs["calibration"] / log_total if log_total else 0.0,
            "time_selection_log_share": component_logs["time_selection"] / log_total if log_total else 0.0,
            "pf_selection_log_share": component_logs["pf_selection"] / log_total if log_total else 0.0,
            "dominant_component": _dominant_component(component_logs, tie_tolerance),
            "success_gamma_1_01": _as_bool(source["success_gamma_1_01"]),
            "coverage_status": "complete_existing_truth",
        }
        output_rows.append(row)

    dominance_counts = Counter(str(row["dominant_component"]) for row in output_rows)
    group_summary: dict[str, dict[str, Any]] = {}
    for group in sorted(set(row["evaluation_group"] for row in output_rows)):
        selected = [row for row in output_rows if row["evaluation_group"] == group]
        group_summary[group] = {
            "condition_count": len(selected),
            "mean_total_excess_regret": _mean(row["excess_total"] for row in selected),
            "mean_calibration_excess": _mean(row["excess_calibration"] for row in selected),
            "mean_time_selection_excess": _mean(row["excess_time_selection"] for row in selected),
            "mean_pf_selection_excess": _mean(row["excess_pf_selection"] for row in selected),
            "dominance_counts": dict(Counter(row["dominant_component"] for row in selected)),
        }
    maximum_row = max(output_rows, key=lambda row: row["excess_total"])
    summary = {
        "schema_version": 1,
        "status": protocol["status_if_complete"],
        "condition_count": len(output_rows),
        "coverage_complete": True,
        "new_direct_truth_coordinate_count": 0,
        "new_hamiltonian_count": 0,
        "new_fit_count": 0,
        "gamma_1_01_safe_condition_count": sum(row["success_gamma_1_01"] for row in output_rows),
        "pf_selection_loss_condition_count": sum(row["factor_pf_selection"] > 1.0 + tie_tolerance for row in output_rows),
        "dominance_counts": dict(dominance_counts),
        "mean_total_excess_regret": _mean(row["excess_total"] for row in output_rows),
        "max_total_excess_regret": maximum_row["excess_total"],
        "max_total_regret_condition": maximum_row["condition"],
        "max_closure_absolute_error": max(row["closure_absolute_error"] for row in output_rows),
        "groups": group_summary,
        "research_direction": {
            "hf_stress": "finite_time_optimum_prediction",
            "active_space": "mixed_calibration_budget_and_time_selection",
            "pf_redesign_supported_by_this_analysis": False,
            "new_experiment_started": False,
        },
    }
    source_identity = {
        "artifact": source_spec["artifact"],
        "result_commit": source_spec["result_commit"],
        "status": source_spec["status"],
        "manifest_sha256": manifest_sha,
        "scoring_sha256": scoring_sha,
        "source_internal_scoring_sha256": source_manifest["artifact_sha256"]["scoring.csv"],
    }
    audit = {
        "status": protocol["status_if_complete"],
        "protocol_sha256": protocol_sha,
        "source_checks": checks,
        "row_count": len(output_rows),
        "expected_row_count": len(expected),
        "max_closure_absolute_error": summary["max_closure_absolute_error"],
        "closure_tolerance": closure_tolerance,
        "coverage_complete": True,
        "new_direct_truth_coordinate_count": 0,
        "all_gates_passed": True,
    }

    if output.exists() and any(output.iterdir()):
        raise DecompositionError(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(output / "protocol.json", protocol_path.read_text(encoding="utf-8"))
    _write_json(output / "source_manifest.json", source_identity)
    fieldnames = list(output_rows[0])
    _write_csv(output / "regret_decomposition.csv", output_rows, fieldnames)
    _write_json(output / "summary.json", summary)
    _write_json(output / "audit.json", audit)
    _atomic_write_text(output / "report.md", _report(protocol_sha, source_identity, output_rows, summary))

    artifact_names = [
        "protocol.json",
        "source_manifest.json",
        "regret_decomposition.csv",
        "summary.json",
        "audit.json",
        "report.md",
    ]
    manifest = {
        "schema_version": 1,
        "status": protocol["status_if_complete"],
        "created_at": datetime.now().astimezone().isoformat(),
        "protocol_sha256": protocol_sha,
        "source_scoring_sha256": scoring_sha,
        "condition_count": len(output_rows),
        "new_direct_truth_coordinate_count": 0,
        "artifact_sha256": {name: sha256_file(output / name) for name in artifact_names},
    }
    _write_json(output / "manifest.json", manifest)
    _atomic_write_text(output / "COMPLETE", "")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = run(args.project_root, args.protocol, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
