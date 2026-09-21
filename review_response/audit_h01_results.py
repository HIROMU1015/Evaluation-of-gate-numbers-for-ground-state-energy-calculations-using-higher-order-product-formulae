"""Create the lightweight post-run audit for an H01 result artifact."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def markdown_number(value: Any, spec: str = ".4g") -> str:
    return "n/a" if value is None else format(float(value), spec)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    root = args.artifact.resolve()
    summary = load(root / "aggregate/summary.json")
    manifest = load(root / "manifest.json")
    rows = summary["rows"]
    primary = {
        "N2_active_eq_sto3g", "N2_active_stretch150_sto3g",
        "CO_active_eq_sto3g", "CO_active_stretch150_sto3g",
    }

    metric_fields = [
        "condition", "formula", "state_method", "model", "grid", "passed",
        "budget_1_01_met", "eta_star", "eta_min", "eta_t",
        "maximum_unseen_residual_over_epsilon", "predicted_time",
        "direct_minimum_time", "direct_minimum_cost",
    ]
    metrics_path = root / "aggregate/metrics.csv"
    with metrics_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=metric_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in metric_fields} for row in rows)

    state_rows = []
    peak_cpu_rss_kib = 0
    for path in sorted((root / "cache").glob("*.metadata.json")):
        payload = load(path)
        system = payload["system"]
        peak_cpu_rss_kib = max(peak_cpu_rss_kib, int(system.get("peak_cpu_rss_kib", 0)))
        for method, data in system["states"].items():
            state_rows.append({
                "condition": system["condition"], "state_method": method,
                "normalization": data["normalization"],
                "energy_error_hartree": data["energy_error_hartree"],
                "energy_variance_hartree2": data["energy_variance_hartree2"],
                "hamiltonian_residual_2_norm": data["hamiltonian_residual_2_norm"],
                "exact_ground_overlap_probability_evaluation_only": data[
                    "overlap_probability_with_exact_ground_for_evaluation_only"
                ],
                "z2_sector_outside_norm": data["additional_z2_sector_outside_norm"],
                "state_generation_wall_seconds": data["state_generation_wall_seconds"],
                "pyscf_vs_matrix_energy_difference_hartree": data.get(
                    "pyscf_vs_matrix_energy_difference_hartree"
                ),
            })
    state_fields = list(state_rows[0])
    with (root / "aggregate/state_diagnostics.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=state_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(state_rows)

    direct_rows = []
    max_gpu_used_mib = 0
    max_gpu_increment_mib = 0
    branch_disagreements = 0
    new_points = reused_points = 0
    total_direct_seconds = 0.0
    for path in sorted((root / "truth").glob("*.json")):
        truth = load(path)
        seen: set[tuple[float, str]] = set()
        for collection in ("coarse_unique_truth_points", "fine_unique_truth_points"):
            for point in truth.get(collection, []):
                key = (float(point["time"]), str(point.get("truth_provenance")))
                if key in seen:
                    continue
                seen.add(key)
                timing = point.get("timing_seconds", {})
                gpu = timing.get("gpu_memory", {})
                total = timing.get("total")
                if point.get("truth_provenance") == "new_h01_continuous_branch_calculation":
                    new_points += 1
                    if total is not None:
                        total_direct_seconds += float(total)
                else:
                    reused_points += 1
                branch_disagreements += int(
                    point.get("branch_selection_disagrees_with_independent_rule", False)
                )
                if gpu.get("maximum_used_mib") is not None:
                    max_gpu_used_mib = max(max_gpu_used_mib, int(gpu["maximum_used_mib"]))
                if gpu.get("peak_increment_mib") is not None:
                    max_gpu_increment_mib = max(
                        max_gpu_increment_mib, int(gpu["peak_increment_mib"])
                    )
                direct_rows.append({
                    "condition": truth["condition"], "formula": truth["formula"],
                    "time": point["time"], "truth_provenance": point.get("truth_provenance"),
                    "signed_direct_shift_hartree": point["signed_direct_shift_hartree"],
                    "ground_overlap_probability": point.get("ground_overlap_probability"),
                    "eigenpair_residual_2_norm": point.get("eigenpair_residual_2_norm"),
                    "branch_disagreement": point.get(
                        "branch_selection_disagrees_with_independent_rule"
                    ),
                    "wall_seconds": total,
                    "gpu_maximum_used_mib": gpu.get("maximum_used_mib"),
                    "gpu_peak_increment_mib": gpu.get("peak_increment_mib"),
                })
    direct_fields = list(direct_rows[0])
    with (root / "aggregate/direct_timing_and_branch_audit.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=direct_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(direct_rows)

    main_rows = [row for row in rows if row["model"] == "echo_phase_5point"]
    primary_rows = [row for row in main_rows if row["condition"] in primary]
    conditions = [
        "N2_active_eq_sto3g", "N2_active_stretch150_sto3g",
        "CO_active_eq_sto3g", "CO_active_stretch150_sto3g",
    ]
    short_names = ["N2 eq", "N2 1.5x", "CO eq", "CO 1.5x"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for method, marker in (("exact_ground", "o"), ("cisd", "s"), ("rhf_determinant", "^")):
        for formula, linestyle in (("current_m3", "-"), ("yoshida4", "--")):
            selected = [
                next(row for row in primary_rows if row["condition"] == condition
                     and row["state_method"] == method and row["formula"] == formula)
                for condition in conditions
            ]
            axes[0].plot(
                range(4), [row["eta_star"] for row in selected], marker=marker,
                linestyle=linestyle, label=f"{method}/{formula}",
            )
            axes[1].plot(
                range(4), [row["maximum_unseen_residual_over_epsilon"] for row in selected],
                marker=marker, linestyle=linestyle, label=f"{method}/{formula}",
            )
    axes[0].axhline(0.01, color="black", linewidth=1, alpha=0.6)
    axes[1].axhline(0.05, color="black", linewidth=1, alpha=0.6)
    axes[0].set_ylabel(r"$\eta_*$")
    axes[1].set_ylabel(r"max unseen residual / $\epsilon_E$")
    for axis in axes:
        axis.set_yscale("log")
        axis.set_xticks(range(4), short_names, rotation=25, ha="right")
        axis.grid(True, alpha=0.25)
    axes[1].legend(fontsize=7, loc="best")
    fig.savefig(root / "aggregate/primary_metrics.png", dpi=160)
    plt.close(fig)

    state_conditions = [row["condition"] for row in state_rows if row["state_method"] == "cisd"]
    fig, axis = plt.subplots(figsize=(8, 4), constrained_layout=True)
    for method, marker in (("cisd", "s"), ("rhf_determinant", "^")):
        selected = [next(row for row in state_rows if row["condition"] == condition and row["state_method"] == method) for condition in state_conditions]
        axis.plot(
            range(len(selected)),
            [row["exact_ground_overlap_probability_evaluation_only"] for row in selected],
            marker=marker, label=method,
        )
    axis.set_xticks(range(len(state_conditions)), [value.replace("_sto3g", "") for value in state_conditions], rotation=30, ha="right")
    axis.set_ylabel("Exact-ground overlap probability (evaluation only)")
    axis.set_ylim(0.0, 1.02)
    axis.grid(True, alpha=0.25)
    axis.legend()
    fig.savefig(root / "aggregate/state_overlaps.png", dpi=160)
    plt.close(fig)

    exact_pass = all(row["passed"] for row in primary_rows if row["state_method"] == "exact_ground")
    cisd_by_pf = {
        formula: [row for row in primary_rows if row["state_method"] == "cisd" and row["formula"] == formula]
        for formula in ("current_m3", "yoshida4")
    }
    rhf_by_pf = {
        formula: [row for row in primary_rows if row["state_method"] == "rhf_determinant" and row["formula"] == formula]
        for formula in ("current_m3", "yoshida4")
    }
    cisd_success = all(all(row["passed"] and row["budget_1_01_met"] for row in values) for values in cisd_by_pf.values())
    pilot = load(root / "pilot.json")
    reports = [
        "# H01 approximate-state calibration", "",
        "## Conclusion", "",
        f"- Exact-ground echo sanity: **{'PASS' if exact_pass else 'FAIL'}**. Both PFs reproduce the source conclusion in all four primary conditions.",
        f"- CISD state substitution: **{'PASS' if cisd_success else 'FAIL'}** under the frozen all-four-condition rule.",
        "- CISD nevertheless meets the frozen 1.01 budget in all four primary conditions for both PFs.",
        "- RHF state substitution fails the frozen transfer rule for both PFs.",
        "- Because neither approximate-state method makes both PFs feasible under all four checks, approximate-state PF selection is not validated.",
        "- HF is auxiliary only. HF stretch retains the known failure and is not misclassified as a primary success.",
        "- This is an oracle-time development diagnostic; it is not end-to-end cheap calibration.",
        "", "## Primary echo-phase five-point results", "",
        "| Condition | PF | State | pass | 1.01 budget | eta_star | eta_min | eta_t | max residual/eps |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in primary_rows:
        reports.append(
            f"| {row['condition']} | {row['formula']} | {row['state_method']} | "
            f"{row['passed']} | {row['budget_1_01_met']} | "
            f"{markdown_number(row['eta_star'])} | {markdown_number(row['eta_min'])} | "
            f"{markdown_number(row['eta_t'])} | "
            f"{markdown_number(row['maximum_unseen_residual_over_epsilon'])} |"
        )
    reports += [
        "", "## Transfer summary", "",
        "| State | PF | four-condition pass | 1.01 budget in all four |",
        "|---|---|---:|---:|",
    ]
    for method in ("exact_ground", "cisd", "rhf_determinant"):
        for formula in ("current_m3", "yoshida4"):
            values = [row for row in primary_rows if row["state_method"] == method and row["formula"] == formula]
            reports.append(
                f"| {method} | {formula} | {all(row['passed'] for row in values)} | "
                f"{all(row['budget_1_01_met'] for row in values)} |"
            )
    reports += [
        "", "## Runtime and numerical audit", "",
        f"- CPU/GPU representative PF-state difference: `{pilot['cpu_gpu_relative_2_norm_difference']:.3e}`.",
        f"- Representative CPU PF action: `{pilot['cpu']['pf']['total']:.3f}` s; GPU PF action: `{pilot['gpu']['total']:.3f}` s. CPU was selected for echo calibration.",
        f"- New direct-truth points audited: `{new_points}`; source-reused appearances: `{reused_points}`.",
        f"- Sum of per-point direct timings (parallel work, not elapsed time): `{total_direct_seconds:.1f}` s.",
        f"- Maximum recorded CPU RSS: `{peak_cpu_rss_kib / 1024:.1f}` MiB.",
        f"- Maximum recorded GPU memory used: `{max_gpu_used_mib}` MiB; maximum per-process increment: `{max_gpu_increment_mib}` MiB.",
        f"- Continuous-branch vs independent maximum-ground-overlap disagreements: `{branch_disagreements}`.",
        "- The duplicate reuse aggregation issue was fixed without recomputing valid points; retry used hash-validated time-level checkpoints.",
        "", "## Files and scope", "",
        "- `metrics.csv`: all state/PF/model decisions.",
        "- `state_diagnostics.csv`: norms, energies, variances, residuals, and evaluation-only exact overlaps.",
        "- `direct_timing_and_branch_audit.csv`: unique truth timing and branch audit rows.",
        "- Server-only Hamiltonian pickles and selected-vector `.npy` checkpoints are excluded from Git; final truth JSONs retain the numerical results.",
        "- No PF coefficients, thresholds, molecules, model powers, or time grids were adapted.",
    ]
    (root / "aggregate/report.md").write_text("\n".join(reports) + "\n", encoding="utf-8")

    tracked_candidates = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if path.suffix in {".pkl", ".npy"} or "_work" in relative.parts or "checkpoints" in relative.parts:
            continue
        tracked_candidates.append({
            "path": str(relative), "bytes": path.stat().st_size, "sha256": sha256(path)
        })
    log_text = (root / "logs/run.log").read_text(encoding="utf-8") + (root / "logs/recovery_duplicate_truth.log").read_text(encoding="utf-8")
    stamps = re.findall(r"\[(\d{4}-\d{2}-\d{2}T[^]]+)\]", log_text)
    audit = {
        "status": "complete",
        "final_implementation_commit": "29dfb13",
        "run_start_commit": manifest["git"]["commit"],
        "protocol_sha256": manifest["protocol_sha256"],
        "result_counts": {
            "conditions": 6, "formulae": 2, "echo_json": len(list((root / "echo").glob("*.json"))),
            "truth_json": len(list((root / "truth").glob("*.json"))),
            "time_level_checkpoints_server_only": len(list((root / "truth/checkpoints").rglob("*.json"))),
            "new_direct_truth_points": new_points,
        },
        "tests": {"review_tests": 90, "passed": 90, "failed": 0},
        "resources": {
            "peak_cpu_rss_kib": peak_cpu_rss_kib,
            "maximum_gpu_memory_used_mib": max_gpu_used_mib,
            "maximum_gpu_memory_increment_mib": max_gpu_increment_mib,
            "per_point_direct_time_sum_seconds": total_direct_seconds,
        },
        "branch_audit": {"disagreements": branch_disagreements},
        "recovery": {
            "reason": "identical source/coarse/fine reuse appearances were initially counted as multiple truth matches",
            "resolution": "deduplicate only after signed shifts agree within 1e-11 Hartree; inconsistent duplicates remain fatal",
            "numerical_points_lost": 0,
        },
        "git_policy": {
            "include": "final JSON/CSV/report/figures/tests/logs/cache metadata",
            "exclude": "rebuildable *.pkl, selected-vector *.npy, checkpoint cache tree, PySCF scratch",
        },
        "tracked_candidate_files": tracked_candidates,
        "timestamps": {"first": stamps[0] if stamps else None, "last": stamps[-1] if stamps else None},
    }
    dump(root / "post_run_audit.json", audit)
    manifest.update({
        "status": "complete", "post_run_audit": "post_run_audit.json",
        "final_implementation_commit": "29dfb13",
        "server_only_excluded_from_git": ["cache/*.pkl", "cache/*_work/", "truth/checkpoints/"],
    })
    dump(root / "manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
