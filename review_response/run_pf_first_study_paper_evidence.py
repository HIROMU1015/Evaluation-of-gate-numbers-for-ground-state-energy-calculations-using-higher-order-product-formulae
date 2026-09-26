#!/usr/bin/env python3
"""Build a paper-facing evidence package from committed first-study results only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_PROTOCOL = Path("review_response/pf_first_study_paper_evidence_protocol.json")
DEFAULT_OUTPUT = Path("paper/evidence")


class PaperEvidenceError(RuntimeError):
    """Raised when a frozen source or evidence-package gate fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise PaperEvidenceError("refusing to write an empty evidence CSV")
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


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise PaperEvidenceError(f"invalid Boolean value: {value!r}")


def _git_blob(project_root: Path, commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=project_root,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise PaperEvidenceError(
            f"cannot read {relative_path} at source commit {commit}: {stderr}"
        )
    return result.stdout


def _base_is_ancestor(project_root: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=project_root,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def _validate_sources(
    project_root: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Path]]:
    records: dict[str, Any] = {}
    roots: dict[str, Path] = {}
    failed: list[str] = []
    for stage, spec in protocol["sources"].items():
        root = project_root / spec["artifact"]
        roots[stage] = root
        complete = root / "COMPLETE"
        stage_record: dict[str, Any] = {
            "artifact": spec["artifact"],
            "result_commit": spec["result_commit"],
            "complete_exists": complete.is_file(),
            "files": {},
        }
        if not complete.is_file():
            failed.append(f"{stage}:COMPLETE")
        for name, expected in spec["files"].items():
            path = root / name
            relative = str(path.relative_to(project_root))
            if not path.is_file():
                failed.append(f"{stage}:{name}:missing")
                continue
            actual = sha256_file(path)
            committed = _sha256_bytes(
                _git_blob(project_root, spec["result_commit"], relative)
            )
            current_matches = actual == expected
            commit_matches = committed == expected
            if not current_matches:
                failed.append(f"{stage}:{name}:working-tree-sha256")
            if not commit_matches:
                failed.append(f"{stage}:{name}:source-commit-sha256")
            stage_record["files"][name] = {
                "path": relative,
                "sha256": actual,
                "expected_sha256": expected,
                "source_commit_blob_sha256": committed,
                "working_tree_matches": current_matches,
                "source_commit_matches": commit_matches,
            }
        records[stage] = stage_record
    if not _base_is_ancestor(project_root, protocol["base_commit"]):
        failed.append("base_commit_not_ancestor_of_head")
    if failed:
        raise PaperEvidenceError(f"source identity gate failed: {sorted(failed)}")
    return records, roots


def _source_fields(
    protocol: dict[str, Any], stage: str, filename: str
) -> dict[str, str]:
    spec = protocol["sources"][stage]
    return {
        "source_path": f"{spec['artifact']}/{filename}",
        "source_sha256": spec["files"][filename],
        "source_commit": spec["result_commit"],
    }


def _value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PaperEvidenceError(f"non-finite evidence value: {value}")
        return repr(value)
    return str(value)


def _build_numbers(
    protocol: dict[str, Any], roots: dict[str, Path]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(
        claim_id: str,
        metric_id: str,
        value: Any,
        unit: str,
        scope: str,
        evaluation_group: str,
        coverage_status: str,
        stage: str,
        filename: str,
        limitation: str,
        *,
        numerator: Any = "",
        denominator: Any = "",
        supersedes: str = "none",
    ) -> None:
        rows.append(
            {
                "claim_id": claim_id,
                "metric_id": metric_id,
                "value": _value(value),
                "unit": unit,
                "numerator": _value(numerator) if numerator != "" else "",
                "denominator": _value(denominator) if denominator != "" else "",
                "scope": scope,
                "evaluation_group": evaluation_group,
                "coverage_status": coverage_status,
                **_source_fields(protocol, stage, filename),
                "supersedes": supersedes,
                "limitation": limitation,
            }
        )

    # C1: branch-connected direct truth and numerical reproduction.
    s0_audit = _load_json(roots["s0"] / "audit.json")
    c1_limitation = (
        "Numerical reproducibility for six development conditions; not a general "
        "branch-tracking guarantee."
    )
    extrema = s0_audit["extrema"]
    c1_metrics = {
        "maximum_anchor_shift_reproduction_difference": (
            extrema["maximum_anchor_shift_reproduction_difference_hartree"],
            "hartree",
        ),
        "maximum_eigenpair_residual_2_norm": (
            extrema["maximum_eigenpair_residual_2_norm"],
            "dimensionless",
        ),
        "maximum_unitarity_residual_frobenius": (
            extrema["maximum_unitarity_residual_frobenius"],
            "dimensionless",
        ),
        "minimum_previous_branch_overlap_probability": (
            extrema["minimum_inserted_previous_branch_overlap_probability"],
            "probability",
        ),
        "minimum_ground_state_overlap_probability": (
            extrema["minimum_inserted_ground_state_overlap_probability"],
            "probability",
        ),
        "minimum_phase_gap": (
            extrema["minimum_inserted_phase_gap_radians"],
            "radian",
        ),
    }
    for metric, (value, unit) in c1_metrics.items():
        add(
            "C1",
            f"s0.{metric}",
            value,
            unit,
            "six molecular development conditions; selected current_m3 branches",
            "primary_plus_stress",
            "exact_selected_time_v1_1",
            "s0",
            "audit.json",
            c1_limitation,
        )
    for row in _read_csv(roots["s0"] / "scoring.csv"):
        condition = row["condition"]
        group = row["evaluation_group"]
        for suffix, field in (
            ("signed_direct_shift", "exact_time_direct_signed_shift_hartree"),
            ("absolute_direct_error", "exact_time_direct_error_hartree"),
        ):
            add(
                "C1",
                f"s0.{condition}.{suffix}",
                float(row[field]),
                "hartree",
                condition,
                group,
                "exact_selected_time_v1_1",
                "s0",
                "scoring.csv",
                c1_limitation,
            )

    # C2: frozen three-way error decomposition.
    dominance = _read_csv(roots["s1_s2"] / "dominance_summary.csv")
    total_counts = Counter(row["dominant_component"] for row in dominance)
    h4 = [row for row in dominance if row["case_id"] == "H4"]
    two_level = [row for row in dominance if row["case_id"] != "H4"]
    c2_limitation = (
        "Fixed H4 and controlled two-level development cases; no universal "
        "dominance claim."
    )
    for prefix, subset in (("all", dominance), ("h4", h4), ("two_level", two_level)):
        counts = Counter(row["dominant_component"] for row in subset)
        for label, component in (
            ("state_dominant", "E_state_hartree"),
            ("mixed", "mixed"),
        ):
            add(
                "C2",
                f"s1_s2.{prefix}.{label}_count",
                counts[component],
                "cases",
                prefix,
                "development",
                "fixed_case_set",
                "s1_s2",
                "dominance_summary.csv",
                c2_limitation,
                numerator=counts[component],
                denominator=len(subset),
            )
    singly_fit_or_proxy = sum(
        total_counts[name] for name in ("E_fit_hartree", "E_proxy_hartree")
    )
    add(
        "C2",
        "s1_s2.all.fit_or_proxy_singly_dominant_count",
        singly_fit_or_proxy,
        "cases",
        "all 128 fixed cases",
        "development",
        "fixed_case_set",
        "s1_s2",
        "dominance_summary.csv",
        c2_limitation,
        numerator=singly_fit_or_proxy,
        denominator=len(dominance),
    )
    s1_s2_audit = _load_json(roots["s1_s2"] / "audit.json")
    add(
        "C2",
        "s1_s2.maximum_three_way_closure",
        s1_s2_audit["extrema"]["maximum_three_way_closure_hartree"],
        "hartree",
        "all resolved S1/S2 decomposition rows",
        "development",
        "fixed_case_set",
        "s1_s2",
        "audit.json",
        c2_limitation,
    )

    # C3: exact-time safety and the frozen decision trace.
    s0_rows = _read_csv(roots["s0"] / "scoring.csv")
    c3_limitation = (
        "Six development conditions; not an independent-molecule or universal "
        "safety guarantee."
    )
    for gamma in ("1_00", "1_01"):
        safe_count = sum(_as_bool(row[f"success_gamma_{gamma}"]) for row in s0_rows)
        add(
            "C3",
            f"s0.gamma_{gamma}.safe_condition_count",
            safe_count,
            "conditions",
            "six molecular development conditions",
            "primary_plus_stress",
            "exact_selected_time_v1_1",
            "s0",
            "scoring.csv",
            c3_limitation,
            numerator=safe_count,
            denominator=len(s0_rows),
        )
    decision_trace = _read_csv(roots["completion"] / "decision_trace.csv")
    trace_fields = (
        ("proxy_analytic_time", "hartree^-1"),
        ("allowed_time_cap", "hartree^-1"),
        ("formula_optimum_time", "hartree^-1"),
        ("formula_optimum_predicted_cost", "continuous_cost_proxy"),
        ("fallback_triggered", "boolean"),
        ("selected_formula", "boolean"),
    )
    for row in decision_trace:
        for field, unit in trace_fields:
            raw: Any = row[field]
            if unit not in {"boolean"}:
                raw = float(raw)
            else:
                raw = _as_bool(raw)
            add(
                "C3",
                f"decision_trace.{row['condition']}.{row['formula']}.{field}",
                raw,
                unit,
                f"{row['condition']} / {row['formula']}",
                row["evaluation_group"],
                "frozen_phase_a_decision",
                "completion",
                "decision_trace.csv",
                c3_limitation,
            )

    # C4-C6: total resource factors, PF selection, and domain bounds.
    factors = _read_csv(roots["completion"] / "cost_factor_decomposition.csv")
    c4_limitation = (
        "Continuous cost proxy with C_star defined on the original two-PF saved "
        "truth grid."
    )
    c5_limitation = "Only current_m3 and yoshida4 on the original saved truth grid."
    for row in factors:
        add(
            "C4",
            f"resource.{row['condition']}.factor_total",
            float(row["factor_total"]),
            "factor",
            row["condition"],
            row["evaluation_group"],
            row["coverage_status"],
            "completion",
            "cost_factor_decomposition.csv",
            c4_limitation,
        )
        add(
            "C5",
            f"resource.{row['condition']}.factor_pf_selection",
            float(row["factor_pf"]),
            "factor",
            row["condition"],
            row["evaluation_group"],
            row["coverage_status"],
            "completion",
            "cost_factor_decomposition.csv",
            c5_limitation,
        )
    pf_loss_count = sum(float(row["factor_pf"]) > 1.0 + 1e-12 for row in factors)
    add(
        "C5",
        "resource.pf_selection_loss_condition_count",
        pf_loss_count,
        "conditions",
        "six molecular development conditions",
        "primary_plus_stress",
        "original_two_pf_saved_grid",
        "completion",
        "cost_factor_decomposition.csv",
        c5_limitation,
        numerator=pf_loss_count,
        denominator=len(factors),
    )
    boundary = _load_json(roots["completion"] / "boundary_bounds.json")
    c6_limitation = (
        "HF analytic bound at the frozen cap; safety beyond the cap and the "
        "continuous-time oracle are unproved."
    )
    for row in boundary["rows"]:
        for field in (
            "t_cap",
            "reference_grid_oracle_time",
            "factor_within_lower",
            "factor_within_upper",
            "factor_domain_lower",
            "factor_domain_upper",
        ):
            unit = "hartree^-1" if field.endswith("time") or field == "t_cap" else "factor"
            add(
                "C6",
                f"domain.{row['condition']}.{field}",
                float(row[field]),
                unit,
                row["condition"],
                "stress_test",
                "analytic_bound_at_cap",
                "completion",
                "boundary_bounds.json",
                c6_limitation,
            )

    # C7: dominant source of primary-set resource regret.
    regret = _read_csv(roots["regret"] / "regret_decomposition.csv")
    primary_regret = [row for row in regret if row["evaluation_group"] == "primary"]
    c7_limitation = (
        "Four active-space primary conditions with original saved-grid accounting."
    )
    for row in primary_regret:
        add(
            "C7",
            f"regret.{row['condition']}.dominant_component",
            row["dominant_component"],
            "category",
            row["condition"],
            "primary",
            row["coverage_status"],
            "regret",
            "regret_decomposition.csv",
            c7_limitation,
        )
    regret_counts = Counter(row["dominant_component"] for row in primary_regret)
    for component in ("calibration", "time_selection", "pf_selection"):
        add(
            "C7",
            f"regret.primary.{component}_dominant_count",
            regret_counts[component],
            "conditions",
            "four active-space primary conditions",
            "primary",
            "complete_existing_truth",
            "regret",
            "regret_decomposition.csv",
            c7_limitation,
            numerator=regret_counts[component],
            denominator=len(primary_regret),
        )

    # C8: resource-side calibration precision.
    calibration = _read_csv(roots["completion"] / "calibration_precision.csv")
    c8_limitation = (
        "Applies to the fixed cost model where the remaining error budget is positive."
    )
    for row in calibration:
        for field, unit in (
            ("direct_error_hartree", "hartree"),
            ("predicted_error_hartree", "hartree"),
            ("signed_absolute_error_bias_hartree", "hartree"),
            ("relative_bias_to_direct_error", "ratio"),
            ("absolute_bias_over_remaining_budget", "ratio"),
            ("factor_model_from_bias_identity", "factor"),
        ):
            add(
                "C8",
                f"calibration.{row['condition']}.{field}",
                float(row[field]),
                unit,
                row["condition"],
                row["evaluation_group"],
                "exact_selected_time_v1_1",
                "completion",
                "calibration_precision.csv",
                c8_limitation,
            )

    # C9: frozen diagnostic triggers and its negative resource result.
    s4_predictions = _load_json(roots["s4"] / "predictions.json")
    c9_limitation = (
        "One preregistered operator-sensitive diagnostic on six development conditions; "
        "not a claim that all diagnostics are ineffective."
    )
    risk_count = 0
    for condition_record in s4_predictions["conditions"]:
        condition = condition_record["condition"]
        group = condition_record["evaluation_group"]
        for formula, risk in sorted(condition_record["state_risk_by_formula"].items()):
            risk_count += bool(risk)
            add(
                "C9",
                f"s4.{condition}.{formula}.state_risk",
                bool(risk),
                "boolean",
                f"{condition} / {formula}",
                group,
                "frozen_phase_a_diagnostic",
                "s4",
                "predictions.json",
                c9_limitation,
            )
        truncation = condition_record["truncation"]
        add(
            "C9",
            f"s4.{condition}.retained_coefficient_count",
            int(truncation["retained_coefficient_count"]),
            "coefficients",
            condition,
            group,
            "frozen_phase_a_diagnostic",
            "s4",
            "predictions.json",
            c9_limitation,
            numerator=int(truncation["retained_coefficient_count"]),
            denominator=int(truncation["total_coefficient_count"]),
        )
    add(
        "C9",
        "s4.state_risk_positive_group_count",
        risk_count,
        "condition_formula_groups",
        "six conditions times two formulas",
        "primary_plus_stress",
        "frozen_phase_a_diagnostic",
        "s4",
        "predictions.json",
        c9_limitation,
        numerator=risk_count,
        denominator=12,
    )
    s4_decision = _load_json(roots["s4"] / "decision.json")
    for strategy in ("practical_baseline", "state_targeted_fallback"):
        summary = s4_decision["strategy_summary"][strategy]
        for field in ("mean_regret", "maximum_regret"):
            add(
                "C9",
                f"s4.{strategy}.{field}",
                float(summary[field]),
                "regret",
                "six molecular development conditions",
                "primary_plus_stress",
                "original_two_pf_saved_grid",
                "s4",
                "decision.json",
                c9_limitation,
            )
    add(
        "C9",
        "s4.fixed_outcome",
        s4_decision["outcome"],
        "category",
        "seven frozen strategies",
        "primary_plus_stress",
        "fixed_benefit_gate",
        "s4",
        "decision.json",
        c9_limitation,
    )

    # C10: corrected S4 cost-definition audit. Never quote raw S4 absolute margins.
    s4_corrected = _load_json(roots["completion"] / "s4_cost_definition_audit.json")
    c10_limitation = (
        "The 42 rows are six development conditions times seven frozen strategies; "
        "they are not 42 independent conditions."
    )
    for metric, value, unit in (
        ("practical_cost_beta", s4_corrected["practical_cost_beta"], "dimensionless"),
        ("stored_scoring_beta", s4_corrected["s4_saved_scoring_beta"], "dimensionless"),
        ("corrected_safe_row_count", s4_corrected["consistent_safe_row_count"], "strategy_condition_rows"),
        ("success_changed_row_count", s4_corrected["success_changed_row_count"], "strategy_condition_rows"),
        ("minimum_corrected_energy_margin", s4_corrected["minimum_consistent_energy_margin_hartree"], "hartree"),
        ("corrected_outcome", s4_corrected["consistent_outcome"], "category"),
    ):
        kwargs: dict[str, Any] = {}
        if metric == "corrected_safe_row_count":
            kwargs = {"numerator": value, "denominator": s4_corrected["row_count"]}
        add(
            "C10",
            f"s4_beta_audit.{metric}",
            value,
            unit,
            "six development conditions times seven frozen strategies",
            "primary_plus_stress",
            "beta_1.2_corrected_audit",
            "completion",
            "s4_cost_definition_audit.json",
            c10_limitation,
            supersedes=(
                "S4 stored absolute phase-error and energy-margin values"
                if metric in {"practical_cost_beta", "minimum_corrected_energy_margin"}
                else "none"
            ),
            **kwargs,
        )
    for strategy, summary in sorted(s4_corrected["strategy_summary"].items()):
        for field, unit in (
            ("consistent_safe_count", "conditions"),
            ("mean_original_grid_regret", "regret"),
            ("maximum_original_grid_regret", "regret"),
            ("minimum_consistent_energy_margin_hartree", "hartree"),
        ):
            value = summary[field]
            kwargs = {}
            if field == "consistent_safe_count":
                kwargs = {"numerator": value, "denominator": summary["condition_count"]}
            add(
                "C10",
                f"s4_beta_audit.{strategy}.{field}",
                value,
                unit,
                f"strategy {strategy} across six development conditions",
                "primary_plus_stress",
                "beta_1.2_corrected_audit",
                "completion",
                "s4_cost_definition_audit.json",
                c10_limitation,
                supersedes=(
                    "S4 stored absolute energy-margin values"
                    if field == "minimum_consistent_energy_margin_hartree"
                    else "none"
                ),
                **kwargs,
            )
    return rows


CLAIMS = [
    {
        "id": "C1",
        "claim": "Direct PF error is reproducible as the signed eigenvalue shift of the branch connected continuously to the exact ground state.",
        "evidence": "S0 v1.1 branch audit and six exact-time signed shifts.",
        "allowed": "Numerical implementation is reproducible for the fixed six-condition scope.",
        "limitation": "Do not generalize branch reliability beyond the tested six conditions and fixed PF implementation.",
    },
    {
        "id": "C2",
        "claim": "State substitution is a major calibration-error axis: 79/128 fixed cases are state-dominant and 49/128 are mixed.",
        "evidence": "S1/S2 frozen three-way decomposition; S3 retrospective synthesis.",
        "allowed": "State substitution is often important in this fixed development set.",
        "limitation": "Do not claim universal state dominance; H4 and controlled two-level cases have different mixtures.",
    },
    {
        "id": "C3",
        "claim": "The 1% frozen safety margin succeeds at the exact selected time in 6/6 development conditions.",
        "evidence": "S0 exact-time v1.1 scoring and the frozen decision trace.",
        "allowed": "Development-set safety for gamma=1.01.",
        "limitation": "Not an independent-molecule or universal safety guarantee.",
    },
    {
        "id": "C4",
        "claim": "Safety and efficiency differ; total frozen-budget factors reach about 2.15 and 2.10 for the two HF stress cases.",
        "evidence": "Completion-analysis cost-factor decomposition.",
        "allowed": "safe != efficient under the continuous cost proxy.",
        "limitation": "C_star is the original two-PF saved-grid minimum, not a continuous-time global oracle.",
    },
    {
        "id": "C5",
        "claim": "PF-selection loss is zero in all six conditions on the original two-PF saved grid.",
        "evidence": "Regret and completion decompositions.",
        "allowed": "PF redesign is not the observed bottleneck in this candidate set.",
        "limitation": "Do not generalize beyond current_m3, yoshida4, and the saved grid.",
    },
    {
        "id": "C6",
        "claim": "For HF, the time loss is dominated by the admissible-domain restriction rather than within-domain selection.",
        "evidence": "Completion-analysis analytic bounds at the frozen cap.",
        "allowed": "F_domain lower bounds are 2.114659 (eq) and 2.069664 (stretch).",
        "limitation": "No claim that cap-external times are safe or that the saved-grid oracle is continuous-global.",
    },
    {
        "id": "C7",
        "claim": "Among the four primary active-space conditions, calibration dominates three and time selection dominates N2 stretch.",
        "evidence": "Frozen regret decomposition on the original saved grid.",
        "allowed": "The observed resource loss has more than one improvement axis.",
        "limitation": "Primary four conditions and saved-grid accounting only.",
    },
    {
        "id": "C8",
        "claim": "Calibration precision is resource-relevant through |b|/(epsilon-e), not only through |b|/e.",
        "evidence": "Analytic cost identity reproduced in all six completion-analysis rows.",
        "allowed": "Use the remaining-budget-normalized bias as a resource-side calibration metric.",
        "limitation": "Requires the fixed cost model and a positive remaining error budget.",
    },
    {
        "id": "C9",
        "claim": "The preregistered operator-sensitive two-state diagnostic detects HF/current_m3 risk but does not improve resource regret over baseline.",
        "evidence": "S4 frozen predictions and fixed no_benefit decision.",
        "allowed": "A valid negative result for this diagnostic and decision rule.",
        "limitation": "Do not claim that operator-sensitive diagnostics in general cannot help.",
    },
    {
        "id": "C10",
        "claim": "After correcting S4 absolute cost accounting to beta=1.2, all 42 strategy-condition rows remain safe, zero labels change, and no_benefit is unchanged.",
        "evidence": "Completion-analysis S4 cost-definition audit.",
        "allowed": "The qualitative S4 conclusion is robust to the beta-definition correction.",
        "limitation": "42 means 6 development conditions x 7 strategies; raw S4 absolute margins are superseded.",
    },
]


def _build_matrix(protocol: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    counts = Counter(row["claim_id"] for row in rows)
    lines = [
        "# 第一研究：論文用 evidence matrix",
        "",
        "**status:** `complete_existing_evidence_package`",
        "",
        f"**integration snapshot:** `{protocol['base_commit']}`",
        "",
        "**new direct truth / Hamiltonian / state / fit:** `0 / 0 / 0 / 0`",
        "",
        "この文書は論文本文ではなく、主張と保存済み証拠を結ぶ監査用台帳である。",
        "数値の正本は `paper_numbers.csv`、file/commit/hashの正本は",
        "`paper_source_manifest.json` とする。",
        "",
        "## 主張と証拠",
        "",
        "| ID | 固定主張 | 主要証拠 | 許される表現 | 必須の限定 | 数値行 |",
        "|---|---|---|---|---|---:|",
    ]
    for claim in CLAIMS:
        cells = [
            claim["id"],
            claim["claim"],
            claim["evidence"],
            claim["allowed"],
            claim["limitation"],
            str(counts[claim["id"]]),
        ]
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |")

    lines.extend(
        [
            "",
            "## 図の固定順序（このtaskでは作図しない）",
            "",
            "1. **Decision pipeline** — proxy入力、PF/時刻選択、凍結予算、truth採点の情報境界。",
            "2. **Three-error decomposition** — state substitution、proxy–eigenvalue、model fit。",
            "3. **Safety versus efficiency** — S0/completionの6条件のみ。S4の42行監査とは混ぜない。",
            "4. **Within-domain versus domain loss** — N2/COのsaved-grid会計とHFの解析的boundsを描き分ける。",
            "",
            "## 表の固定内容",
            "",
            "- **Table 1:** 6条件 x 2 PFのdecision trace。`decision_trace.*`行を使用する。",
            "- **Table 2:** `F_model`, `F_margin`, `F_within`, `F_domain`, `F_PF`, `F_total`。coverage statusを必ず併記する。",
            "- **Table 3:** 7 strategyのcorrected安全数、平均・最大regret、corrected最小margin。",
            "",
            "## 出典の優先順位とsupersession",
            "",
            "1. completion analysisをC4–C10の正本とする。",
            "2. S0 exact-time v1.1をC1/C3の正本とする。",
            "3. S1/S2とS3をC2の機構証拠に使う。",
            "4. S4原成果物はrisk matrix・相対regret・`no_benefit`に使う。",
            "5. S4原成果物の絶対phase-error/marginは引用せず、beta=1.2のcorrected auditで置換する。",
            "",
            "## Coverageを混同しないための規則",
            "",
            "- `exact_saved_grid_only`: N2/COの保存済み2-PF truth grid上の厳密会計。",
            "- `analytic_bound_at_cap`: HFでcap点と保存grid参照から得た上下界。",
            "- `C_star`は常にoriginal two-PF saved-grid minimumと書き、continuous oracleとは呼ばない。",
            "- `42/42 safe`は6 development conditions x 7 frozen strategiesであり、独立42条件ではない。",
            "",
            "## Reverse fact audit（本文完成後に実施）",
            "",
            "- [ ] 本文の全数値が `paper_numbers.csv` の `metric_id`へ逆引きできる。",
            "- [ ] 各数値のscope、evaluation group、coverage status、limitationが本文またはcaptionに反映される。",
            "- [ ] S4の絶対margin/phase-errorはcorrected auditだけから引用される。",
            "- [ ] 6条件のS0安全性と6 x 7行のS4 strategy監査を同じ標本数として扱っていない。",
            "- [ ] HF boundsをcap外安全性やcontinuous-time global optimumの証拠として使っていない。",
            "- [ ] negative resultを診断一般の無効性へ拡張していない。",
            "",
            "## 停止条件",
            "",
            "このpackage作成では、新規計算、図作成、本文執筆、selector変更、S5、新分子、",
            "新PF、別基底、別精度、追加diagnosticを行わない。",
        ]
    )
    return "\n".join(lines) + "\n"


def _audit_rows(protocol: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    expected_claims = set(protocol["scope"]["claim_ids"])
    actual_claims = {row["claim_id"] for row in rows}
    if actual_claims != expected_claims:
        raise PaperEvidenceError(
            f"claim coverage mismatch: expected {expected_claims}, got {actual_claims}"
        )
    metric_ids = [row["metric_id"] for row in rows]
    if len(metric_ids) != len(set(metric_ids)):
        duplicates = sorted(name for name, count in Counter(metric_ids).items() if count > 1)
        raise PaperEvidenceError(f"duplicate metric_id values: {duplicates}")
    required = {
        "source_path",
        "source_sha256",
        "source_commit",
        "scope",
        "evaluation_group",
        "coverage_status",
        "limitation",
    }
    for row in rows:
        missing = sorted(key for key in required if not str(row.get(key, "")).strip())
        if missing:
            raise PaperEvidenceError(f"{row['metric_id']}: blank required fields {missing}")
    expectations = protocol["fixed_expectations"]
    lookup = {row["metric_id"]: row for row in rows}
    exact = {
        "s1_s2.all.state_dominant_count": expectations["s1_s2_state_dominant_count"],
        "s1_s2.all.mixed_count": expectations["s1_s2_mixed_count"],
        "s0.gamma_1_01.safe_condition_count": expectations["s0_gamma_1_01_safe_count"],
        "resource.pf_selection_loss_condition_count": expectations["pf_selection_loss_count"],
        "s4_beta_audit.corrected_safe_row_count": expectations["s4_consistent_safe_row_count"],
        "s4_beta_audit.success_changed_row_count": expectations["s4_success_changed_row_count"],
        "s4_beta_audit.corrected_outcome": expectations["s4_consistent_outcome"],
    }
    for metric_id, expected in exact.items():
        actual = lookup[metric_id]["value"]
        if isinstance(expected, int):
            passed = int(actual) == expected
        else:
            passed = actual == str(expected)
        if not passed:
            raise PaperEvidenceError(
                f"fixed expectation failed for {metric_id}: {actual!r} != {expected!r}"
            )


def run(project_root: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    protocol_path = (
        protocol_path if protocol_path.is_absolute() else project_root / protocol_path
    )
    output = output if output.is_absolute() else project_root / output
    protocol = _load_json(protocol_path)
    source_records, roots = _validate_sources(project_root, protocol)
    rows = _build_numbers(protocol, roots)
    _audit_rows(protocol, rows)

    numbers_path = output / protocol["output"]["numbers"]
    matrix_path = output / protocol["output"]["matrix"]
    manifest_path = output / protocol["output"]["manifest"]
    _write_csv(numbers_path, rows)
    _atomic_write_text(matrix_path, _build_matrix(protocol, rows))

    runner_path = Path(__file__).resolve()
    manifest = {
        "schema_version": 1,
        "status": "complete_existing_evidence_package",
        "integration_snapshot_commit": protocol["base_commit"],
        "integration_snapshot_is_ancestor_of_head": True,
        "protocol": {
            "path": str(protocol_path.relative_to(project_root)),
            "sha256": sha256_file(protocol_path),
        },
        "generator": {
            "path": str(runner_path.relative_to(project_root)),
            "sha256": sha256_file(runner_path),
        },
        "scope": protocol["scope"],
        "figure_order": protocol["figure_order"],
        "supersession_rules": protocol["supersession_rules"],
        "source_identity_all_passed": True,
        "sources": source_records,
        "evidence": {
            "claim_count": len(set(row["claim_id"] for row in rows)),
            "metric_row_count": len(rows),
            "metric_rows_by_claim": dict(sorted(Counter(row["claim_id"] for row in rows).items())),
        },
        "outputs": {
            numbers_path.name: sha256_file(numbers_path),
            matrix_path.name: sha256_file(matrix_path),
        },
        "new_computation": {
            "direct_truth_coordinates": 0,
            "hamiltonians": 0,
            "states": 0,
            "fits": 0,
            "figures": 0,
            "manuscript_sections": 0,
        },
    }
    _write_json(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = run(args.project_root, args.protocol, args.output)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
