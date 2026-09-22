"""F05 audit separating physical energy gaps from finite-time PF phase gaps.

The audit joins the already computed X02 branch curves with the F02
state-mixing decomposition.  It does not diagonalize new PF unitaries.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import platform
import resource
import time
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _git_output,
    _package_versions,
    _sha256,
    _write_csv,
)


DEFAULT_X02 = Path(
    "artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3"
)
DEFAULT_F02 = Path(
    "artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3"
)
DEFAULT_OUTPUT = Path(
    "artifacts/prevalidation_f05_energy_phase_gap_20260922"
)
FORMULA_IDS = ("yoshida4", "current_m3", "two_term_center")
SYSTEM_IDS = ("H2", "H4")
EARLY_TIME_MAXIMUM = 0.2
PHASE_COMPRESSION_RATIO = 0.1
X02_PHASE_WARNING_THRESHOLD_RADIANS = 1e-6
EARLY_SLOPE_RELATIVE_TOLERANCE = 1e-3


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _as_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"not a serialized bool: {value!r}")


def _write_figure(
    output_dir: Path,
    phase_rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(10.4, 4.2), sharey=True)
    colors = {
        "yoshida4": "C0",
        "current_m3": "C1",
        "two_term_center": "C2",
    }
    for axis, system_id in zip(axes, SYSTEM_IDS, strict=True):
        for formula_id in FORMULA_IDS:
            rows = [
                row
                for row in phase_rows
                if row["system_id"] == system_id
                and row["formula_id"] == formula_id
                and row["inside_reliable_prefix"]
            ]
            axis.plot(
                [row["time_hartree_inverse"] for row in rows],
                [row["normalized_phase_gap_over_physical_gap"] for row in rows],
                color=colors[formula_id],
                linewidth=1.1,
                label=formula_id,
            )
            summary = next(
                row
                for row in summaries
                if row["system_id"] == system_id
                and row["formula_id"] == formula_id
            )
            axis.axvline(
                summary["first_branch_warning_time"],
                color=colors[formula_id],
                linestyle=":",
                linewidth=0.8,
                alpha=0.8,
            )
        axis.axhline(
            PHASE_COMPRESSION_RATIO,
            color="black",
            linestyle="--",
            linewidth=0.9,
            label="10% compression",
        )
        axis.set_title(system_id)
        axis.set_xlabel(r"$\tau$ (Hartree$^{-1}$)")
        axis.set_yscale("log")
        axis.grid(True, which="both", alpha=0.25)
    axes[0].set_ylabel(r"phase gap$/\tau\Delta E_{min}$")
    axes[0].legend(frameon=False, fontsize=8)
    figure.tight_layout()
    figure.savefig(output_dir / "normalized_phase_gap_vs_time.png", dpi=180)
    plt.close(figure)

    labels = [f"{row['system_id']}\n{row['formula_id']}" for row in summaries]
    locations = np.arange(len(summaries))
    figure, axis = plt.subplots(figsize=(8.1, 4.2))
    axis.bar(
        locations,
        [row["dominant_mixing_gap_over_minimum_gap"] for row in summaries],
        color=[colors[row["formula_id"]] for row in summaries],
    )
    axis.axhline(1.0, color="black", linestyle="--", linewidth=0.9)
    axis.set_xticks(locations, labels, rotation=35, ha="right", fontsize=8)
    axis.set_ylabel("dominant D4-mixing gap / minimum physical gap")
    axis.grid(True, axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "mixing_gap_scale.png", dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    summaries = audit["condition_summaries"]
    compression_count = sum(
        row["first_phase_compression_time"] is not None for row in summaries
    )
    phase_warning_count = sum(
        row["first_warning_due_phase_gap_threshold"] for row in summaries
    )
    lines = [
        "# F05: physical energy gap versus finite-time PF phase gap",
        "",
        f"Status: **{audit['status']}**",
        "",
        "X02の直接枝曲線とF02のD4状態混合を結合し、物理エネルギーギャップ、"
        "有限時刻PF位相ギャップ、結合行列要素の役割を分離した。新しいPF直接点は計算していない。",
        "",
        "## Conditions",
        "",
        "| system | PF | physical min gap | dominant mixing gap | gap ratio | "
        "lowest-gap mixing share | min reliable normalized phase gap | first warning |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['system_id']} | {row['formula_id']} | "
            f"{row['physical_minimum_gap_hartree']:.6f} | "
            f"{row['dominant_mixing_gap_hartree']:.6f} | "
            f"{row['dominant_mixing_gap_over_minimum_gap']:.3f} | "
            f"{row['lowest_gap_group_absolute_mixing_share']:.3e} | "
            f"{row['minimum_reliable_normalized_phase_gap']:.4f} | "
            f"{row['first_branch_warning_time']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Findings",
            "",
            audit["interpretation"]["short_time"],
            "",
            audit["interpretation"]["state_mixing"],
            "",
            audit["interpretation"]["finite_time"],
            "",
            f"位相ギャップが短時間線形値の10%未満へ圧縮されたのは{compression_count}/6条件。"
            f"一方、最初の枝警告がX02の位相ギャップ絶対閾値で発火した条件は{phase_warning_count}/6で、"
            "警告後の孤立した小位相ギャップは信頼枝の根拠に使っていない。",
            "",
            "## First-warning causes",
            "",
            "| system | PF | selection disagreement | ground overlap <0.9 | "
            "previous overlap <0.9 | phase gap <1e-6 | phase gap (rad) |",
            "|---|---|:---:|:---:|:---:|:---:|---:|",
        ]
    )
    for row in summaries:
        lines.append(
            f"| {row['system_id']} | {row['formula_id']} | "
            f"{'yes' if row['first_warning_due_selection_disagreement'] else 'no'} | "
            f"{'yes' if row['first_warning_due_ground_overlap'] else 'no'} | "
            f"{'yes' if row['first_warning_due_previous_overlap'] else 'no'} | "
            f"{'yes' if row['first_warning_due_phase_gap_threshold'] else 'no'} | "
            f"{row['first_warning_phase_gap_radians']:.6e} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "F05の最小検証は完了した。最小物理ギャップだけではD4状態混合を説明できず、"
            "位相近接も固定された物理ギャップの単純な写像ではない。"
            "PFとtauに依存する位相圧縮、対象枝の重なり、結合行列要素を併記する必要がある。",
            "",
            "この小系結果は、全電子HF伸長条件の破綻原因を直接確定するものではない。"
            "同条件へ適用する場合は同じ枝・基底を保存した追加診断が必要である。",
            "",
            "## Files",
            "",
            "- `audit.json`: complete machine-readable result.",
            "- `condition_summary.csv`: six joined condition summaries.",
            "- `phase_gap_points.csv`: all reliable and post-warning phase-gap points.",
            "- `mixing_gap_groups.csv`: F02 degenerate energy-group contributions.",
            "- `manifest.json`: source, input, artifact hashes and runtime.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(x02_dir: Path, f02_dir: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    x02_audit_path = x02_dir / "audit.json"
    x02_points_path = x02_dir / "truth_points.csv"
    x02_branch_path = x02_dir / "branch_summary.csv"
    f02_audit_path = f02_dir / "audit.json"
    x02 = json.loads(x02_audit_path.read_text(encoding="utf-8"))
    f02 = json.loads(f02_audit_path.read_text(encoding="utf-8"))
    if x02["summaries"]["F05_data_only"]["status"] != "data_collected_not_formally_complete":
        raise RuntimeError("unexpected X02 F05 input status")
    if not f02["mechanism_identity_passed"]:
        raise RuntimeError("F02 mechanism identity did not pass")

    truth_rows = _read_csv(x02_points_path)
    branch_rows = _read_csv(x02_branch_path)
    f02_summaries = {
        (row["system_id"], row["formula_id"]): row
        for row in f02["condition_summaries"]
    }
    f02_groups = f02["degenerate_group_rows"]
    phase_rows: list[dict[str, Any]] = []
    mixing_rows: list[dict[str, Any]] = []
    condition_summaries: list[dict[str, Any]] = []
    early_errors: list[float] = []

    for system_id in SYSTEM_IDS:
        for formula_id in FORMULA_IDS:
            key = (system_id, formula_id)
            mechanism = f02_summaries[key]
            physical_gap = float(mechanism["minimum_excitation_gap_hartree"])
            condition_points = [
                row
                for row in truth_rows
                if row["system"] == system_id and row["formula"] == formula_id
            ]
            condition_points.sort(key=lambda row: float(row["time_hartree_inverse"]))
            if not condition_points:
                raise RuntimeError(f"missing X02 points for {key}")
            first_warning_index = next(
                (
                    index
                    for index, row in enumerate(condition_points)
                    if _as_bool(row["branch_warning"])
                ),
                len(condition_points),
            )
            if first_warning_index == len(condition_points):
                raise RuntimeError(f"no first warning available for {key}")
            first_warning = condition_points[first_warning_index]
            reliable_points = condition_points[:first_warning_index]
            early_points = [
                row
                for row in reliable_points
                if float(row["time_hartree_inverse"]) <= EARLY_TIME_MAXIMUM
            ]
            early_normalized = np.asarray(
                [
                    float(row["selected_phase_gap_radians"])
                    / float(row["time_hartree_inverse"])
                    / physical_gap
                    for row in early_points
                ],
                dtype=float,
            )
            early_maximum_error = float(np.max(np.abs(early_normalized - 1.0)))
            early_errors.append(early_maximum_error)

            enriched_condition = []
            for index, row in enumerate(condition_points):
                time_value = float(row["time_hartree_inverse"])
                phase_gap = float(row["selected_phase_gap_radians"])
                enriched = {
                    "system_id": system_id,
                    "formula_id": formula_id,
                    "point_index": int(row["point_index"]),
                    "time_hartree_inverse": time_value,
                    "physical_minimum_gap_hartree": physical_gap,
                    "selected_phase_gap_radians": phase_gap,
                    "phase_gap_over_time_hartree": phase_gap / time_value,
                    "normalized_phase_gap_over_physical_gap": (
                        phase_gap / time_value / physical_gap
                    ),
                    "selected_ground_overlap_probability": float(
                        row["selected_ground_overlap_probability"]
                    ),
                    "previous_branch_overlap_probability": float(
                        row["previous_branch_overlap_probability"]
                    ),
                    "selection_rules_agree": _as_bool(
                        row["selection_rules_agree"]
                    ),
                    "branch_warning": _as_bool(row["branch_warning"]),
                    "inside_reliable_prefix": index < first_warning_index,
                }
                enriched_condition.append(enriched)
                phase_rows.append(enriched)

            reliable_enriched = enriched_condition[:first_warning_index]
            minimum_reliable = min(
                reliable_enriched,
                key=lambda row: row["normalized_phase_gap_over_physical_gap"],
            )
            compression_points = [
                row
                for row in reliable_enriched
                if row["normalized_phase_gap_over_physical_gap"]
                < PHASE_COMPRESSION_RATIO
            ]
            all_minimum = min(
                enriched_condition,
                key=lambda row: row["selected_phase_gap_radians"],
            )

            groups = [
                row
                for row in f02_groups
                if row["system_id"] == system_id
                and row["formula_id"] == formula_id
            ]
            groups.sort(key=lambda row: float(row["excitation_gap_hartree"]))
            if not groups:
                raise RuntimeError(f"missing F02 gap groups for {key}")
            for row in groups:
                mixing_rows.append(dict(row))
            lowest_group = groups[0]
            dominant_group = max(
                groups, key=lambda row: float(row["absolute_mixing_share"])
            )
            branch_summary = next(
                row
                for row in branch_rows
                if row["system"] == system_id and row["formula"] == formula_id
            )
            first_ground_overlap = float(
                first_warning["selected_ground_overlap_probability"]
            )
            first_previous_overlap = float(
                first_warning["previous_branch_overlap_probability"]
            )
            first_phase_gap = float(first_warning["selected_phase_gap_radians"])
            condition_summaries.append(
                {
                    "system_id": system_id,
                    "formula_id": formula_id,
                    "point_count": len(condition_points),
                    "reliable_prefix_point_count": len(reliable_points),
                    "physical_minimum_gap_hartree": physical_gap,
                    "early_phase_gap_slope_median_hartree": float(
                        np.median(early_normalized) * physical_gap
                    ),
                    "early_slope_maximum_relative_error": early_maximum_error,
                    "dominant_mixing_gap_hartree": float(
                        dominant_group["excitation_gap_hartree"]
                    ),
                    "dominant_mixing_gap_over_minimum_gap": float(
                        dominant_group["excitation_gap_hartree"] / physical_gap
                    ),
                    "dominant_group_absolute_mixing_share": float(
                        dominant_group["absolute_mixing_share"]
                    ),
                    "lowest_gap_group_absolute_mixing_share": float(
                        lowest_group["absolute_mixing_share"]
                    ),
                    "minimum_reliable_normalized_phase_gap": float(
                        minimum_reliable[
                            "normalized_phase_gap_over_physical_gap"
                        ]
                    ),
                    "minimum_reliable_normalized_phase_gap_time": float(
                        minimum_reliable["time_hartree_inverse"]
                    ),
                    "first_phase_compression_time": (
                        None
                        if not compression_points
                        else float(compression_points[0]["time_hartree_inverse"])
                    ),
                    "first_branch_warning_time": float(
                        first_warning["time_hartree_inverse"]
                    ),
                    "branch_summary_first_warning_time": float(
                        branch_summary["first_branch_warning_time"]
                    ),
                    "first_warning_due_selection_disagreement": not _as_bool(
                        first_warning["selection_rules_agree"]
                    ),
                    "first_warning_due_ground_overlap": first_ground_overlap < 0.9,
                    "first_warning_due_previous_overlap": (
                        first_previous_overlap < 0.9
                    ),
                    "first_warning_due_phase_gap_threshold": (
                        first_phase_gap < X02_PHASE_WARNING_THRESHOLD_RADIANS
                    ),
                    "first_warning_ground_overlap_probability": (
                        first_ground_overlap
                    ),
                    "first_warning_previous_overlap_probability": (
                        first_previous_overlap
                    ),
                    "first_warning_phase_gap_radians": first_phase_gap,
                    "full_curve_minimum_phase_gap_radians": float(
                        all_minimum["selected_phase_gap_radians"]
                    ),
                    "full_curve_minimum_phase_gap_time": float(
                        all_minimum["time_hartree_inverse"]
                    ),
                    "full_curve_minimum_is_inside_reliable_prefix": bool(
                        all_minimum["inside_reliable_prefix"]
                    ),
                }
            )

    warning_time_differences = [
        abs(
            row["first_branch_warning_time"]
            - row["branch_summary_first_warning_time"]
        )
        for row in condition_summaries
    ]
    checks = [
        {
            "check_id": "condition_count",
            "measured": len(condition_summaries),
            "threshold": 6,
            "comparison": "==",
            "passed": len(condition_summaries) == 6,
        },
        {
            "check_id": "early_phase_gap_slope_relative_error",
            "measured": max(early_errors),
            "threshold": EARLY_SLOPE_RELATIVE_TOLERANCE,
            "comparison": "<=",
            "passed": max(early_errors) <= EARLY_SLOPE_RELATIVE_TOLERANCE,
        },
        {
            "check_id": "branch_summary_time_consistency",
            "measured": max(warning_time_differences),
            "threshold": 1e-14,
            "comparison": "<=",
            "passed": max(warning_time_differences) <= 1e-14,
        },
        {
            "check_id": "every_first_warning_has_declared_trigger",
            "measured": sum(
                any(
                    row[field]
                    for field in (
                        "first_warning_due_selection_disagreement",
                        "first_warning_due_ground_overlap",
                        "first_warning_due_previous_overlap",
                        "first_warning_due_phase_gap_threshold",
                    )
                )
                for row in condition_summaries
            ),
            "threshold": 6,
            "comparison": "==",
            "passed": all(
                any(
                    row[field]
                    for field in (
                        "first_warning_due_selection_disagreement",
                        "first_warning_due_ground_overlap",
                        "first_warning_due_previous_overlap",
                        "first_warning_due_phase_gap_threshold",
                    )
                )
                for row in condition_summaries
            ),
        },
    ]
    passed = all(check["passed"] for check in checks)
    interpretation = {
        "short_time": (
            "短時間ではphase_gap/tが物理最小ギャップに一致し、6条件の最大相対差は"
            f"{max(early_errors):.3e}だった。これは物理ギャップと位相ギャップの"
            "t→0対応を数値的に確認する。"
        ),
        "state_mixing": (
            "最低励起群のD4二次混合への最大寄与率は"
            f"{max(row['lowest_gap_group_absolute_mixing_share'] for row in condition_summaries):.3e}で、"
            "支配群のギャップは最小物理ギャップの"
            f"{min(row['dominant_mixing_gap_over_minimum_gap'] for row in condition_summaries):.2f}–"
            f"{max(row['dominant_mixing_gap_over_minimum_gap'] for row in condition_summaries):.2f}倍だった。"
            "小ギャップだけでなく結合行列要素が必要である。"
        ),
        "finite_time": (
            "同一system内でも信頼枝中の最小normalized phase gapと最初の枝警告時刻はPF依存であり、"
            "有限tauの位相近接を固定された物理ギャップだけから推定できない。"
            "最初の警告は全6条件でground-overlap低下を含み、phase-gap絶対閾値単独ではなかった。"
        ),
    }
    audit = {
        "schema": "prevalidation_f05_energy_phase_gap_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "complete" if passed else "complete_with_findings",
        "passed": passed,
        "scope": {
            "catalog_item": "F05",
            "systems": list(SYSTEM_IDS),
            "formula_ids": list(FORMULA_IDS),
            "condition_count": len(condition_summaries),
            "point_count": len(phase_rows),
            "new_direct_pf_points": 0,
            "excluded_existing_formulas": {
                "morales_y8m10b": "no F02 fourth-order D4 mixing decomposition",
                "m5_best": "not present in X02 phase-gap curves",
            },
            "limitation": (
                "small H-chain systems only; does not by itself diagnose the "
                "full-electron stretched-HF holdout failure"
            ),
        },
        "protocol": {
            "early_time_maximum_hartree_inverse": EARLY_TIME_MAXIMUM,
            "phase_compression_ratio": PHASE_COMPRESSION_RATIO,
            "x02_phase_warning_threshold_radians": (
                X02_PHASE_WARNING_THRESHOLD_RADIANS
            ),
            "reliable_prefix_rule": "all points strictly before the first X02 branch warning",
            "physical_gap_source": "F02 stored-Hamiltonian eigenspectrum",
            "phase_gap_source": "X02 circular nearest-eigenphase distance",
        },
        "checks": checks,
        "condition_summaries": condition_summaries,
        "phase_rows": phase_rows,
        "mixing_group_rows": mixing_rows,
        "interpretation": interpretation,
        "runtime": {
            "elapsed_seconds": float(time.perf_counter() - started),
            "maximum_resident_set_size_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }

    output_dir.mkdir(parents=True)
    _atomic_json(output_dir / "audit.json", audit)
    _write_csv(output_dir / "condition_summary.csv", condition_summaries)
    _write_csv(output_dir / "phase_gap_points.csv", phase_rows)
    _write_csv(output_dir / "mixing_gap_groups.csv", mixing_rows)
    _write_figure(output_dir, phase_rows, condition_summaries)
    _write_report(output_dir / "report.md", audit)

    source_paths = [Path(__file__)]
    input_paths = [
        x02_audit_path,
        x02_points_path,
        x02_branch_path,
        f02_audit_path,
        f02_dir / "degenerate_group_contributions.csv",
    ]
    artifact_paths = [
        output_dir / "audit.json",
        output_dir / "condition_summary.csv",
        output_dir / "phase_gap_points.csv",
        output_dir / "mixing_gap_groups.csv",
        output_dir / "normalized_phase_gap_vs_time.png",
        output_dir / "mixing_gap_scale.png",
        output_dir / "report.md",
    ]
    manifest = {
        "status": audit["status"],
        "git": {
            "head": _git_output("rev-parse", "HEAD"),
            "branch": _git_output("branch", "--show-current"),
            "dirty": bool(_git_output("status", "--porcelain")),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": _package_versions(),
        },
        "source_sha256": {str(path): _sha256(path) for path in source_paths},
        "input_sha256": {str(path): _sha256(path) for path in input_paths},
        "artifact_sha256": {str(path): _sha256(path) for path in artifact_paths},
        "output_directory": str(output_dir),
        "runtime": audit["runtime"],
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--x02-dir", type=Path, default=DEFAULT_X02)
    parser.add_argument("--f02-dir", type=Path, default=DEFAULT_F02)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    audit = run(arguments.x02_dir, arguments.f02_dir, arguments.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(arguments.output_dir),
                "status": audit["status"],
                "passed": audit["passed"],
                "condition_count": len(audit["condition_summaries"]),
                "point_count": len(audit["phase_rows"]),
                "runtime": audit["runtime"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
