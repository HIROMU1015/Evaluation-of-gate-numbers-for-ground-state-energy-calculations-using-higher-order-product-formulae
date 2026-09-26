#!/usr/bin/env python3
"""Render frozen first-study paper figures and table-ready CSV files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


DEFAULT_PROTOCOL = Path("review_response/pf_first_study_paper_figures_protocol.json")


class PaperFigureError(RuntimeError):
    """Raised when a frozen source or rendering gate fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise PaperFigureError(f"refusing to write empty table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _base_is_ancestor(project_root: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=project_root,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def _configure_matplotlib(protocol: dict[str, Any]) -> None:
    rendering = protocol["rendering"]
    plt.rcParams.update(
        {
            "font.family": rendering["font_family"],
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.22,
            "grid.linewidth": 0.6,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.compression": 9,
            "svg.hashsalt": rendering["svg_hashsalt"],
        }
    )


def _save_figure(
    figure: plt.Figure, root: Path, stem: str, protocol: dict[str, Any]
) -> list[Path]:
    outputs: list[Path] = []
    for extension in protocol["rendering"]["formats"]:
        path = root / f"{stem}.{extension}"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.stem}.tmp-{os.getpid()}{path.suffix}")
        if extension == "pdf":
            metadata: dict[str, Any] = {
                "Creator": "run_pf_first_study_paper_figures.py",
                "Producer": "Matplotlib",
                "CreationDate": None,
                "ModDate": None,
            }
        elif extension == "svg":
            metadata = {"Creator": "run_pf_first_study_paper_figures.py", "Date": None}
        else:
            metadata = {"Software": "run_pf_first_study_paper_figures.py"}
        figure.savefig(
            temporary,
            format=extension,
            dpi=int(protocol["rendering"]["png_dpi"]),
            bbox_inches="tight",
            metadata=metadata,
        )
        if extension == "svg":
            svg_text = temporary.read_text(encoding="utf-8")
            temporary.write_text(
                "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
                encoding="utf-8",
            )
        temporary.replace(path)
        outputs.append(path)
    plt.close(figure)
    return outputs


def _validate_source(
    project_root: Path, protocol: dict[str, Any]
) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    source = protocol["source"]
    checks: dict[str, bool] = {}
    source_hashes: dict[str, str] = {}
    for prefix in ("numbers", "matrix", "manifest"):
        relative = source[f"{prefix}_path"]
        path = project_root / relative
        checks[f"{prefix}_exists"] = path.is_file()
        if path.is_file():
            actual = sha256_file(path)
            source_hashes[relative] = actual
            checks[f"{prefix}_sha256"] = actual == source[f"{prefix}_sha256"]
    checks["base_commit_is_ancestor"] = _base_is_ancestor(
        project_root, protocol["base_commit"]
    )
    evidence_manifest_path = project_root / source["manifest_path"]
    if evidence_manifest_path.is_file():
        evidence_manifest = _load_json(evidence_manifest_path)
        checks["evidence_status"] = (
            evidence_manifest.get("status") == "complete_existing_evidence_package"
        )
        checks["evidence_source_identity"] = (
            evidence_manifest.get("source_identity_all_passed") is True
        )
        checks["evidence_numbers_hash"] = (
            evidence_manifest.get("outputs", {}).get("paper_numbers.csv")
            == source["numbers_sha256"]
        )
        checks["evidence_had_no_new_computation"] = all(
            value == 0
            for value in evidence_manifest.get("new_computation", {}).values()
        )
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise PaperFigureError(f"source identity gate failed: {failed}")
    rows = _read_csv(project_root / source["numbers_path"])
    by_metric: dict[str, dict[str, str]] = {}
    for row in rows:
        metric_id = row["metric_id"]
        if metric_id in by_metric:
            raise PaperFigureError(f"duplicate metric_id: {metric_id}")
        by_metric[metric_id] = row
    if not by_metric:
        raise PaperFigureError("paper_numbers.csv is empty")
    return by_metric, {"checks": checks, "source_sha256": source_hashes}


def _metric(by_metric: dict[str, dict[str, str]], metric_id: str) -> dict[str, str]:
    try:
        return by_metric[metric_id]
    except KeyError as exc:
        raise PaperFigureError(f"missing evidence metric: {metric_id}") from exc


def _float(by_metric: dict[str, dict[str, str]], metric_id: str) -> float:
    value = float(_metric(by_metric, metric_id)["value"])
    if not math.isfinite(value):
        raise PaperFigureError(f"non-finite value for {metric_id}")
    return value


def _text(by_metric: dict[str, dict[str, str]], metric_id: str) -> str:
    return _metric(by_metric, metric_id)["value"]


def _bool(by_metric: dict[str, dict[str, str]], metric_id: str) -> bool:
    value = _text(by_metric, metric_id).lower()
    if value == "true":
        return True
    if value == "false":
        return False
    raise PaperFigureError(f"invalid Boolean for {metric_id}: {value}")


def _condition_label(condition: str) -> str:
    return {
        "N2_active_eq_sto3g": r"N$_2$ eq",
        "N2_active_stretch150_sto3g": r"N$_2$ stretch",
        "CO_active_eq_sto3g": "CO eq",
        "CO_active_stretch150_sto3g": "CO stretch",
        "HF_full_eq_sto3g": "HF eq",
        "HF_full_stretch150_sto3g": "HF stretch",
    }[condition]


def _build_table_1(
    protocol: dict[str, Any], by_metric: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fields = (
        "rotations",
        "proxy_analytic_time",
        "original_relative_time_min",
        "original_relative_time_max",
        "original_time_min",
        "original_time_max",
        "fallback_triggered",
        "fallback_reasons",
        "allowed_relative_time_max",
        "allowed_time_cap",
        "formula_optimum_relative_time",
        "formula_optimum_time",
        "formula_optimum_predicted_error_hartree",
        "formula_optimum_predicted_cost",
        "at_optimization_boundary",
        "eligible",
        "selected_formula",
        "condition_selection_reason",
    )
    for condition in protocol["scope"]["conditions"]:
        for formula in protocol["scope"]["formulas"]:
            prefix = f"decision_trace.{condition}.{formula}"
            reference = _metric(by_metric, f"{prefix}.proxy_analytic_time")
            record: dict[str, Any] = {
                "condition": condition,
                "evaluation_group": reference["evaluation_group"],
                "formula": formula,
            }
            for field in fields:
                record[field] = _text(by_metric, f"{prefix}.{field}")
            rows.append(record)
    return rows


def _selected_formula(
    condition: str, protocol: dict[str, Any], by_metric: dict[str, dict[str, str]]
) -> str:
    selected = [
        formula
        for formula in protocol["scope"]["formulas"]
        if _bool(by_metric, f"decision_trace.{condition}.{formula}.selected_formula")
    ]
    if len(selected) != 1:
        raise PaperFigureError(f"expected one selected formula for {condition}: {selected}")
    return selected[0]


def _build_table_2(
    protocol: dict[str, Any], by_metric: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    resource_fields = (
        "selected_time",
        "c_star_reference_grid",
        "c_selected_formula_star_reference_grid",
        "c_required_selected_time",
        "c_hat",
        "b_frozen",
        "factor_model",
        "factor_margin",
        "factor_calibration",
        "factor_total",
        "energy_margin_gamma_1_01_hartree",
    )
    domain_fields = (
        "factor_within_lower",
        "factor_within_upper",
        "factor_domain_lower",
        "factor_domain_upper",
    )
    for condition in protocol["scope"]["conditions"]:
        reference = _metric(by_metric, f"resource.{condition}.factor_total")
        record: dict[str, Any] = {
            "condition": condition,
            "evaluation_group": reference["evaluation_group"],
            "selected_formula": _selected_formula(condition, protocol, by_metric),
            "coverage_status": reference["coverage_status"],
        }
        for field in resource_fields:
            record[field] = _float(by_metric, f"resource.{condition}.{field}")
        record["factor_pf_selection"] = _float(
            by_metric, f"resource.{condition}.factor_pf_selection"
        )
        for field in domain_fields:
            record[field] = _float(by_metric, f"domain.{condition}.{field}")
        rows.append(record)
    return rows


def _build_table_3(
    protocol: dict[str, Any], by_metric: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for strategy in protocol["scope"]["strategies"]:
        prefix = f"s4_beta_audit.{strategy}"
        safe = _metric(by_metric, f"{prefix}.consistent_safe_count")
        rows.append(
            {
                "strategy": strategy,
                "corrected_safe_count": int(safe["value"]),
                "condition_count": int(safe["denominator"]),
                "mean_original_grid_regret": _float(
                    by_metric, f"{prefix}.mean_original_grid_regret"
                ),
                "maximum_original_grid_regret": _float(
                    by_metric, f"{prefix}.maximum_original_grid_regret"
                ),
                "minimum_corrected_energy_margin_hartree": _float(
                    by_metric,
                    f"{prefix}.minimum_consistent_energy_margin_hartree",
                ),
                "coverage_status": safe["coverage_status"],
            }
        )
    return rows


def _figure_1(protocol: dict[str, Any]) -> plt.Figure:
    primary = protocol["rendering"]["primary_color"]
    stress = protocol["rendering"]["stress_color"]
    figure, axis = plt.subplots(figsize=(10.4, 3.2))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    boxes = [
        (0.02, "Classical inputs", "Hamiltonian structure\n+ approximate state"),
        (0.22, "Proxy calibration", "No direct PF\neigenvalue truth"),
        (0.42, "Decision", "Choose $(\\hat P,\\hat t)$\ninside admissible domain"),
        (0.62, "Frozen budget", "$B=1.01\\,\\widehat C$\nselection is committed"),
        (0.82, "Scoring only", "Branch-connected\ndirect truth"),
    ]
    width, height, y = 0.16, 0.34, 0.34
    for index, (x, title, body) in enumerate(boxes):
        scoring = index == len(boxes) - 1
        color = stress if scoring else primary
        axis.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                linewidth=1.6,
                edgecolor=color,
                facecolor="#fff7f0" if scoring else "#f2f7fc",
            )
        )
        axis.text(x + width / 2, y + 0.235, title, ha="center", va="center", weight="bold")
        axis.text(x + width / 2, y + 0.115, body, ha="center", va="center", linespacing=1.25)
        if index < len(boxes) - 1:
            axis.add_patch(
                FancyArrowPatch(
                    (x + width + 0.006, y + height / 2),
                    (boxes[index + 1][0] - 0.006, y + height / 2),
                    arrowstyle="-|>",
                    mutation_scale=12,
                    linewidth=1.2,
                    color="#444444",
                )
            )
    axis.text(0.40, 0.82, "Phase A: truth-blind selection and freeze", ha="center", color=primary, weight="bold")
    axis.plot([0.02, 0.78], [0.77, 0.77], color=primary, linewidth=2.0)
    axis.text(0.90, 0.82, "Phase B", ha="center", color=stress, weight="bold")
    axis.plot([0.82, 0.98], [0.77, 0.77], color=stress, linewidth=2.0)
    axis.axvline(0.795, ymin=0.12, ymax=0.88, color="#333333", linestyle="--", linewidth=1.2)
    axis.text(0.795, 0.10, "truth boundary", ha="center", va="center", bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none"})
    axis.set_title("Finite-time PF/QPE decision pipeline", pad=8, weight="bold")
    return figure


def _figure_2(
    protocol: dict[str, Any], by_metric: dict[str, dict[str, str]]
) -> plt.Figure:
    primary = protocol["rendering"]["primary_color"]
    mixed = protocol["rendering"]["mixed_color"]
    state = [
        int(_text(by_metric, "s1_s2.h4.state_dominant_count")),
        int(_text(by_metric, "s1_s2.two_level.state_dominant_count")),
    ]
    mixed_counts = [
        int(_text(by_metric, "s1_s2.h4.mixed_count")),
        int(_text(by_metric, "s1_s2.two_level.mixed_count")),
    ]
    figure, axis = plt.subplots(figsize=(6.4, 4.1))
    x = [0, 1]
    axis.bar(x, state, width=0.58, color=primary, label="State-substitution dominant")
    axis.bar(x, mixed_counts, width=0.58, bottom=state, color=mixed, label="Mixed")
    for index, (state_count, mixed_count) in enumerate(zip(state, mixed_counts)):
        total = state_count + mixed_count
        axis.text(index, state_count / 2, f"{state_count}/{total}", ha="center", va="center", color="white", weight="bold")
        axis.text(index, state_count + mixed_count / 2, f"{mixed_count}/{total}", ha="center", va="center", color="white", weight="bold")
        axis.text(index, total + 2.0, f"n={total}", ha="center", va="bottom")
    axis.set_xticks(x, ["H4", "Controlled\ntwo-level"])
    axis.set_ylabel("Fixed development cases")
    axis.set_ylim(0, 80)
    axis.set_title("Frozen three-error decomposition outcomes", weight="bold")
    axis.legend(loc="upper left", frameon=False)
    figure.tight_layout()
    return figure


def _figure_3(
    protocol: dict[str, Any], by_metric: dict[str, dict[str, str]]
) -> plt.Figure:
    primary = protocol["rendering"]["primary_color"]
    stress = protocol["rendering"]["stress_color"]
    figure, axis = plt.subplots(figsize=(7.2, 4.7))
    for condition in protocol["scope"]["conditions"]:
        margin = 1e6 * _float(
            by_metric, f"resource.{condition}.energy_margin_gamma_1_01_hartree"
        )
        factor = _float(by_metric, f"resource.{condition}.factor_total")
        is_stress = condition in protocol["scope"]["stress_conditions"]
        axis.scatter([margin], [factor], s=70, marker="D" if is_stress else "o", color=stress if is_stress else primary, edgecolor="white", linewidth=0.8, zorder=3)
        offset = (5, -12) if condition == "N2_active_stretch150_sto3g" else (5, 5)
        axis.annotate(_condition_label(condition), (margin, factor), xytext=offset, textcoords="offset points")
    axis.axhline(1.0, color="#333333", linestyle="--", linewidth=1.0, label="Saved-grid reference")
    axis.set_xscale("log")
    axis.set_xlabel(r"Corrected energy margin at $\gamma=1.01$ ($\mu E_h$)")
    axis.set_ylabel(r"Frozen-budget factor $F_{\mathrm{total}}$")
    axis.set_ylim(0.95, 2.30)
    axis.set_title("All selections are safe, but resource overhead varies", weight="bold")
    axis.scatter([], [], s=55, marker="o", color=primary, label="Active-space primary")
    axis.scatter([], [], s=55, marker="D", color=stress, label="Full-electron HF stress")
    axis.legend(frameon=False, loc="upper right")
    figure.tight_layout()
    return figure


def _range_panel(
    axis: plt.Axes,
    protocol: dict[str, Any],
    by_metric: dict[str, dict[str, str]],
    prefix: str,
    title: str,
) -> None:
    conditions = protocol["scope"]["conditions"]
    positions = list(reversed(range(len(conditions))))
    for position, condition in zip(positions, conditions):
        lower = _float(by_metric, f"domain.{condition}.{prefix}_lower")
        upper = _float(by_metric, f"domain.{condition}.{prefix}_upper")
        midpoint = (lower + upper) / 2.0
        is_stress = condition in protocol["scope"]["stress_conditions"]
        color = protocol["rendering"]["stress_color" if is_stress else "primary_color"]
        axis.errorbar(midpoint, position, xerr=[[midpoint - lower], [upper - midpoint]], fmt="D" if is_stress else "o", color=color, ecolor=color, capsize=4, markersize=6, linewidth=1.8, markeredgecolor="white", markeredgewidth=0.7, zorder=3)
    axis.axvline(1.0, color="#333333", linestyle="--", linewidth=1.0)
    axis.set_yticks(positions, [_condition_label(condition) for condition in conditions])
    axis.set_xlabel("Multiplicative cost factor")
    axis.set_title(title, weight="bold")


def _figure_4(
    protocol: dict[str, Any], by_metric: dict[str, dict[str, str]]
) -> plt.Figure:
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.7), sharey=True)
    _range_panel(axes[0], protocol, by_metric, "factor_within", r"Within-domain factor $F_{\mathrm{within}}$")
    _range_panel(axes[1], protocol, by_metric, "factor_domain", r"Domain factor $F_{\mathrm{domain}}$")
    axes[0].set_xlim(0.985, 1.26)
    axes[1].set_xlim(0.96, 2.22)
    axes[0].scatter([], [], marker="o", color=protocol["rendering"]["primary_color"], label="Saved-grid exact")
    axes[0].scatter([], [], marker="D", color=protocol["rendering"]["stress_color"], label="HF analytic bound")
    axes[0].legend(frameon=False, loc="lower right")
    figure.suptitle("Time-selection loss separates into within-domain and domain terms", weight="bold")
    figure.subplots_adjust(left=0.17, right=0.98, bottom=0.14, top=0.84, wspace=0.18)
    return figure


def _captions() -> str:
    return """# First-study figure captions and table notes

## Figure 1 — Decision pipeline and truth boundary

Finite-time product-formula/QPE decision pipeline. Phase A uses only the
Hamiltonian structure, approximate-state information, and proxy actions to choose
a formula and time and freeze the predicted cost with a 1% safety multiplier.
Branch-connected direct PF eigenvalue truth is opened only in Phase B for scoring.

## Figure 2 — Three-error decomposition

Dominant-error classification for the preregistered H4 and controlled two-level
development cases. State substitution is singly dominant in 49 of 56 H4 cases and
30 of 72 two-level cases; the remaining 7 and 42 cases, respectively, are mixed.
These fixed development cases do not establish universal state dominance.

## Figure 3 — Safety versus efficiency

Corrected energy margin at the 1% frozen budget versus total frozen-budget factor
for the six molecular development conditions. All six selections are safe at the
exact selected time, yet the two full-electron HF stress cases require roughly
twice the original two-PF saved-grid reference cost. The cost is a continuous
resource proxy, and the reference is not a continuous-time global oracle.

## Figure 4 — Within-domain and domain loss

Separation of the time-selection factor into within-domain and admissible-domain
components. N2/CO markers are exact only with respect to the saved truth grid. HF
intervals are analytic bounds at the frozen cap: they do not establish safety
beyond the cap or a continuous-time optimum. The HF domain factor, rather than the
within-domain factor, accounts for most of the observed time loss.

## Table 1 — Frozen decision trace

Six conditions by two candidate formulas, including rotation counts, analytic
time, original search interval, fallback status, admissible cap, predicted optimum,
and the frozen selection decision.

## Table 2 — Resource-factor decomposition

Cost factors for the selected formula and time. `C_star_reference_grid` is the
minimum on the original two-PF saved truth grid. Coverage must be reported as
`exact_saved_grid_only` for N2/CO and `analytic_bound_at_cap` for HF.

## Table 3 — S4 fixed negative result

Corrected beta=1.2 safety count and original-grid regret for each of seven frozen
strategies. The 42 audited rows are six development conditions times seven
strategies, not 42 independent conditions. Raw S4 absolute phase-error and margin
values computed with beta=0.105 are superseded by the corrected audit.
"""


def _all_outputs(
    figures: Iterable[Path], tables: Iterable[Path], captions: Path
) -> list[Path]:
    return sorted([*figures, *tables, captions])


def run(
    project_root: Path, protocol_path: Path, output_root: Path | None = None
) -> dict[str, Any]:
    project_root = project_root.resolve()
    protocol_path = (
        protocol_path if protocol_path.is_absolute() else project_root / protocol_path
    )
    output_root = project_root if output_root is None else output_root.resolve()
    protocol = _load_json(protocol_path)
    by_metric, source_audit = _validate_source(project_root, protocol)
    _configure_matplotlib(protocol)
    figure_root = output_root / protocol["output"]["figure_directory"]
    table_root = output_root / protocol["output"]["table_directory"]
    captions_path = output_root / protocol["output"]["captions"]
    manifest_path = output_root / protocol["output"]["manifest"]

    table_rows = {
        "table_1_decision_trace.csv": _build_table_1(protocol, by_metric),
        "table_2_resource_factors.csv": _build_table_2(protocol, by_metric),
        "table_3_s4_strategy_summary.csv": _build_table_3(protocol, by_metric),
    }
    table_paths: list[Path] = []
    for name, rows in table_rows.items():
        path = table_root / name
        _write_csv(path, rows)
        table_paths.append(path)

    figure_builders = (
        ("figure_1_decision_pipeline", _figure_1(protocol)),
        ("figure_2_three_error_decomposition", _figure_2(protocol, by_metric)),
        ("figure_3_safety_vs_efficiency", _figure_3(protocol, by_metric)),
        ("figure_4_within_vs_domain_loss", _figure_4(protocol, by_metric)),
    )
    figure_paths: list[Path] = []
    for stem, figure in figure_builders:
        figure_paths.extend(_save_figure(figure, figure_root, stem, protocol))
    _atomic_write_text(captions_path, _captions())

    outputs = _all_outputs(figure_paths, table_paths, captions_path)
    runner_path = Path(__file__).resolve()
    manifest = {
        "schema_version": 1,
        "status": "complete_paper_figure_package",
        "base_commit": protocol["base_commit"],
        "protocol": {
            "path": str(protocol_path.relative_to(project_root)),
            "sha256": sha256_file(protocol_path),
        },
        "generator": {
            "path": str(runner_path.relative_to(project_root)),
            "sha256": sha256_file(runner_path),
        },
        "matplotlib_version": matplotlib.__version__,
        "source": protocol["source"],
        "source_audit": source_audit,
        "scope": protocol["scope"],
        "figure_count": len(protocol["figures"]),
        "figure_asset_count": len(figure_paths),
        "table_count": len(table_paths),
        "outputs": {
            str(path.relative_to(output_root)): sha256_file(path) for path in outputs
        },
        "new_computation": {
            "direct_truth_coordinates": 0,
            "hamiltonians": 0,
            "states": 0,
            "fits": 0,
            "selector_changes": 0,
            "manuscript_sections": 0,
        },
        "interpretation_gates": {
            "six_condition_safety_distinct_from_s4_42_rows": True,
            "s4_absolute_values_use_beta_1_2_audit": True,
            "active_saved_grid_distinct_from_hf_bounds": True,
            "hf_cap_external_safety_not_claimed": True,
        },
    }
    _write_json(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    manifest = run(args.project_root, args.protocol, args.output_root)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
