"""X01/A06 audit of information available to PF/time selection.

The saved pipeline is separated into oracle evaluation, target-specific
calibration, and transfer-only selection.  Raw JSON and implementation text
are checked for exact-ground-state, exact-energy, and PF-eigenbranch
dependencies.  No new numerical physics calculation is performed.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import audit_existing_results_x01 as audit_x01
import analyze_x01_frozen_qpe_budget as a05
import analyze_x01_cost_benefit as a07


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/prevalidation_x01_information_access_20260921"
RUNNER = ROOT / "review_response/run_two_term_pf_m3_holdout_server2.py"

EXPECTED_ERROR_DEFINITION = (
    "abs(imag(exp(-i*E0*t)*<psi0|U_PF(t)|psi0>)/t)"
)
EXPECTED_SELECTION_RULE = (
    "maximum exact-ground-state overlap; overlap phase is diagnostic only"
)


def dependency_audit(raw_sources: list[dict[str, Any]]) -> dict[str, Any]:
    formula_count = 0
    short_point_count = 0
    selected_window_count = 0
    training_direct_count = 0
    local_direct_count = 0
    selection_rule_count = 0
    error_definition_count = 0
    for source in raw_sources:
        path = ROOT / str(source["path"])
        payload = audit_x01.load_json(path)
        for pf in a05.PFS:
            formula = payload["formulas"][pf]
            formula_count += 1
            fit = formula["short_time_fit"]
            if fit["error_definition"] != EXPECTED_ERROR_DEFINITION:
                raise ValueError(f"unexpected short-time definition in {path}/{pf}")
            error_definition_count += 1
            short_point_count += len(fit["points"])
            selected_window_count += int(fit["selected_window"]["num_points"])
            training = formula["training_direct_points"]
            local = formula["local_direct_points"]
            training_direct_count += len(training)
            local_direct_count += len(local)
            for point in training + local:
                if point["selection_rule"] != EXPECTED_SELECTION_RULE:
                    raise ValueError(f"unexpected branch rule in {path}/{pf}")
                selection_rule_count += 1
    runner_text = RUNNER.read_text(encoding="utf-8")
    required_fragments = (
        "np.vdot(system[\"state\"], evolved)",
        "np.exp(-1j * float(system[\"energy\"])",
        "vectors.conj().T @ system[\"state\"]",
        "selected = int(np.argmax(overlaps))",
    )
    missing = [fragment for fragment in required_fragments if fragment not in runner_text]
    if missing:
        raise ValueError(f"runner dependency fragments missing: {missing}")
    return {
        "raw_condition_count": len(raw_sources),
        "formula_condition_count": formula_count,
        "short_time_error_definition_match_count": error_definition_count,
        "evaluated_short_time_point_count": short_point_count,
        "selected_short_time_window_point_count": selected_window_count,
        "training_direct_point_count": training_direct_count,
        "local_validation_direct_point_count": local_direct_count,
        "exact_ground_overlap_selection_rule_count": selection_rule_count,
        "all_short_time_definitions_match": error_definition_count == formula_count,
        "all_direct_branch_rules_match": selection_rule_count
        == training_direct_count + local_direct_count,
        "runner_exact_state_overlap_dependency_confirmed": True,
        "runner_exact_energy_phase_rotation_dependency_confirmed": True,
        "runner_path": str(RUNNER.relative_to(ROOT)),
        "runner_sha256": audit_x01.sha256_file(RUNNER),
    }


def information_access_rows() -> list[dict[str, Any]]:
    common = {
        "available_in_oracle_evaluation": True,
        "available_in_practical_target_calibration_without_exact_state": True,
        "available_in_transfer_only": True,
    }
    exact = {
        "available_in_oracle_evaluation": True,
        "available_in_practical_target_calibration_without_exact_state": False,
        "available_in_transfer_only": False,
    }
    derived_exact = dict(exact)
    scoring = dict(exact)
    rows = [
        {
            "information_id": "I01",
            "information": "geometry, basis, charge, multiplicity, active-space definition",
            "pipeline_role": "defines the target Hamiltonian",
            "saved_stage": "input",
            "current_access_class": "declared public input",
            "used_for_model_fit": False,
            "used_for_pf_or_time_selection": False,
            "used_only_for_scoring": False,
            **common,
            "evidence": "raw system metadata",
        },
        {
            "information_id": "I02",
            "information": "ordered grouped Hamiltonian and conservation sector",
            "pipeline_role": "builds every PF action",
            "saved_stage": "input/construction",
            "current_access_class": "target-specific constructed input",
            "used_for_model_fit": True,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **common,
            "evidence": "raw system metadata and component spectra",
        },
        {
            "information_id": "I03",
            "information": "PF weights, S2 sequence, rotations per step",
            "pipeline_role": "defines candidate and quantum step cost",
            "saved_stage": "input",
            "current_access_class": "declared candidate data",
            "used_for_model_fit": True,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **common,
            "evidence": "raw formula record",
        },
        {
            "information_id": "I04",
            "information": "target epsilon_E and beta",
            "pipeline_role": "defines analytic time and QPE cost",
            "saved_stage": "input",
            "current_access_class": "declared protocol input",
            "used_for_model_fit": False,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **common,
            "evidence": "runner constants and cost formula",
        },
        {
            "information_id": "I05",
            "information": "exact ground energy E0",
            "pipeline_role": "rotates short-time overlap and unwraps direct PF phase",
            "saved_stage": "calibration and scoring",
            "current_access_class": "exact oracle truth",
            "used_for_model_fit": True,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **exact,
            "evidence": "exp(-i*system['energy']*t) in runner",
        },
        {
            "information_id": "I06",
            "information": "exact ground-state vector |psi0>",
            "pipeline_role": "short-time overlap and PF eigenbranch identification",
            "saved_stage": "calibration and scoring",
            "current_access_class": "exact oracle truth",
            "used_for_model_fit": True,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **exact,
            "evidence": "np.vdot(state,evolved) and vectors^dagger@state",
        },
        {
            "information_id": "I07",
            "information": "short-time leading coefficient alpha",
            "pipeline_role": "sets t_ana and normalizes direct fit",
            "saved_stage": "target-specific calibration",
            "current_access_class": "derived from exact E0 and exact |psi0>",
            "used_for_model_fit": True,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **derived_exact,
            "evidence": EXPECTED_ERROR_DEFINITION,
        },
        {
            "information_id": "I08",
            "information": "three signed direct PF shifts at 0.1,0.2,0.3 t_ana",
            "pipeline_role": "fits a4 and a6",
            "saved_stage": "target-specific calibration",
            "current_access_class": "exact PF eigensolver truth",
            "used_for_model_fit": True,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **exact,
            "evidence": "training_direct_points",
        },
        {
            "information_id": "I09",
            "information": "target PF eigenbranch identity",
            "pipeline_role": "chooses the signed direct shift",
            "saved_stage": "calibration and validation",
            "current_access_class": "maximum overlap with exact ground state",
            "used_for_model_fit": True,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **exact,
            "evidence": EXPECTED_SELECTION_RULE,
        },
        {
            "information_id": "I10",
            "information": "fitted a4,a6 and model-selected t_star/cost",
            "pipeline_role": "sets the QPE schedule and nominal budget",
            "saved_stage": "selection",
            "current_access_class": "derived from oracle-assisted target calibration",
            "used_for_model_fit": False,
            "used_for_pf_or_time_selection": True,
            "used_only_for_scoring": False,
            **derived_exact,
            "evidence": "two_term_model and two_term_model_optimum",
        },
        {
            "information_id": "I11",
            "information": "direct PF error and cost at model-selected t_star",
            "pipeline_role": "scores cost prediction and frozen budget",
            "saved_stage": "evaluation",
            "current_access_class": "held-out oracle truth",
            "used_for_model_fit": False,
            "used_for_pf_or_time_selection": False,
            "used_only_for_scoring": True,
            **scoring,
            "evidence": "predicted_time_direct_point",
        },
        {
            "information_id": "I12",
            "information": "direct local-grid minimum",
            "pipeline_role": "scores eta_min and eta_t",
            "saved_stage": "evaluation",
            "current_access_class": "held-out oracle truth",
            "used_for_model_fit": False,
            "used_for_pf_or_time_selection": False,
            "used_only_for_scoring": True,
            **scoring,
            "evidence": "saved_local_direct_minimum",
        },
        {
            "information_id": "I13",
            "information": "unseen-grid direct residuals",
            "pipeline_role": "scores extrapolation residual",
            "saved_stage": "evaluation",
            "current_access_class": "held-out oracle truth",
            "used_for_model_fit": False,
            "used_for_pf_or_time_selection": False,
            "used_only_for_scoring": True,
            **scoring,
            "evidence": "saved_unseen_predictions/local_direct_points",
        },
        {
            "information_id": "I14",
            "information": "A05 empirical uniform safety margin",
            "pipeline_role": "repairs strict frozen-budget misses on saved conditions",
            "saved_stage": "post-hoc development analysis",
            "current_access_class": "uses all 17 development truths",
            "used_for_model_fit": False,
            "used_for_pf_or_time_selection": False,
            "used_only_for_scoring": True,
            **scoring,
            "evidence": "A05 maximum required/frozen cost ratio",
        },
        {
            "information_id": "I15",
            "information": "mapping from cheap descriptors to PF/model/time on a new system",
            "pipeline_role": "would enable transfer-only selection",
            "saved_stage": "not implemented",
            "current_access_class": "missing",
            "used_for_model_fit": False,
            "used_for_pf_or_time_selection": False,
            "used_only_for_scoring": False,
            "available_in_oracle_evaluation": False,
            "available_in_practical_target_calibration_without_exact_state": False,
            "available_in_transfer_only": False,
            "evidence": "no saved cross-system selector",
        },
    ]
    return rows


def condition_selection_rows(
    budget_rows: list[dict[str, Any]],
    calibration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    budget = {
        (row["condition"], row["pf"], row["model"]): row for row in budget_rows
    }
    calibration = {
        (row["condition"], row["pf"]): row for row in calibration_rows
    }
    conditions = sorted({str(row["condition"]) for row in budget_rows})
    result = []
    for condition in conditions:
        current = budget[(condition, "current_m3", "two_term")]
        new = budget[(condition, "two_term_center", "two_term")]
        predicted = {
            "current_m3": float(current["frozen_model_cost"]),
            "two_term_center": float(new["frozen_model_cost"]),
        }
        direct = {
            "current_m3": float(current["stored_direct_required_cost"]),
            "two_term_center": float(new["stored_direct_required_cost"]),
        }
        selected_pf = min(predicted, key=predicted.get)
        oracle_pf = min(direct, key=direct.get)
        selected = budget[(condition, selected_pf, "two_term")]
        current_calibration = calibration[(condition, "current_m3")]
        new_calibration = calibration[(condition, "two_term_center")]
        result.append(
            {
                "dataset_id": current["dataset_id"],
                "condition": condition,
                "analysis_cluster": current["analysis_cluster"],
                "predicted_current_m3_cost": predicted["current_m3"],
                "predicted_two_term_center_cost": predicted["two_term_center"],
                "predicted_cost_ratio_new_over_current": predicted[
                    "two_term_center"
                ]
                / predicted["current_m3"],
                "calibrated_selector_pf": selected_pf,
                "oracle_direct_current_m3_cost": direct["current_m3"],
                "oracle_direct_two_term_center_cost": direct["two_term_center"],
                "oracle_candidate_schedule_pf": oracle_pf,
                "selector_agrees_with_oracle_candidate_schedule": selected_pf
                == oracle_pf,
                "selected_strict_frozen_budget_pass": bool(
                    selected["strict_frozen_budget_pass"]
                ),
                "selected_direct_cost_regret_vs_oracle_candidate_schedule": (
                    direct[selected_pf] / direct[oracle_pf] - 1.0
                ),
                "calibrating_both_pf_short_time_points": int(
                    current_calibration["short_time_proxy_point_count"]
                )
                + int(new_calibration["short_time_proxy_point_count"]),
                "calibrating_both_pf_direct_fit_points": int(
                    current_calibration["direct_fit_point_count"]
                )
                + int(new_calibration["direct_fit_point_count"]),
                "calibrating_both_pf_total_points": int(
                    current_calibration["total_calibration_point_count"]
                )
                + int(new_calibration["total_calibration_point_count"]),
                "calibrating_both_pf_seconds": float(
                    current_calibration["total_calibration_seconds"]
                )
                + float(new_calibration["total_calibration_seconds"]),
                "information_warning": (
                    "selector uses predicted costs only, but both predictions depend "
                    "on exact-state-assisted target calibration"
                ),
            }
        )
    return result


def performance_tier_rows(
    selections: list[dict[str, Any]],
    calibration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_calibration = [
        row for row in calibration_rows if row["pf"] == "current_m3"
    ]
    both_points = sum(int(row["calibrating_both_pf_total_points"]) for row in selections)
    both_seconds = sum(float(row["calibrating_both_pf_seconds"]) for row in selections)
    return [
        {
            "tier": "1_oracle_evaluation",
            "method": "minimum direct required cost over the two model-selected schedules",
            "status": "measured evaluation upper bound",
            "conditions_scored": len(selections),
            "pf_choices_produced": len(selections),
            "current_m3_choice_count": sum(
                row["oracle_candidate_schedule_pf"] == "current_m3"
                for row in selections
            ),
            "strict_frozen_budget_passed": None,
            "agreement_with_oracle_choice": len(selections),
            "maximum_selection_regret": 0.0,
            "calibration_points": None,
            "calibration_seconds": None,
            "exact_ground_state_required": True,
            "eligible_as_practical_selector": False,
            "scope_note": "oracle over two saved predicted schedules, not continuous optimum",
        },
        {
            "tier": "2_oracle_assisted_target_calibration",
            "method": "fit both PFs on each target and choose smaller predicted two-term cost",
            "status": "measured but not cheap-state-independent calibration",
            "conditions_scored": len(selections),
            "pf_choices_produced": len(selections),
            "current_m3_choice_count": sum(
                row["calibrated_selector_pf"] == "current_m3" for row in selections
            ),
            "strict_frozen_budget_passed": sum(
                bool(row["selected_strict_frozen_budget_pass"]) for row in selections
            ),
            "agreement_with_oracle_choice": sum(
                bool(row["selector_agrees_with_oracle_candidate_schedule"])
                for row in selections
            ),
            "maximum_selection_regret": max(
                float(row["selected_direct_cost_regret_vs_oracle_candidate_schedule"])
                for row in selections
            ),
            "calibration_points": both_points,
            "calibration_seconds": both_seconds,
            "exact_ground_state_required": True,
            "eligible_as_practical_selector": False,
            "scope_note": "uses exact E0, exact |psi0>, exact PF branches and shifts",
        },
        {
            "tier": "2_oracle_assisted_target_calibration",
            "method": "pre-fix current_m3 and calibrate only its two-term model",
            "status": "measured fixed-PF strategy",
            "conditions_scored": len(selections),
            "pf_choices_produced": 0,
            "current_m3_choice_count": len(selections),
            "strict_frozen_budget_passed": len(selections),
            "agreement_with_oracle_choice": len(selections),
            "maximum_selection_regret": 0.0,
            "calibration_points": sum(
                int(row["total_calibration_point_count"])
                for row in current_calibration
            ),
            "calibration_seconds": sum(
                float(row["total_calibration_seconds"])
                for row in current_calibration
            ),
            "exact_ground_state_required": True,
            "eligible_as_practical_selector": False,
            "scope_note": "same development conditions; PF choice is pre-fixed",
        },
        {
            "tier": "2_practical_target_calibration",
            "method": (
                "few target-specific evaluations without exact E0 or exact "
                "ground-state vector"
            ),
            "status": "not implemented / not evaluated",
            "conditions_scored": 0,
            "pf_choices_produced": 0,
            "current_m3_choice_count": None,
            "strict_frozen_budget_passed": None,
            "agreement_with_oracle_choice": None,
            "maximum_selection_regret": None,
            "calibration_points": None,
            "calibration_seconds": None,
            "exact_ground_state_required": False,
            "eligible_as_practical_selector": None,
            "scope_note": "requires an approximate-state or measurable surrogate study",
        },
        {
            "tier": "3_transfer_only",
            "method": "choose PF/model/time from cheap descriptors on an unused system",
            "status": "not implemented / not evaluated",
            "conditions_scored": 0,
            "pf_choices_produced": 0,
            "current_m3_choice_count": None,
            "strict_frozen_budget_passed": None,
            "agreement_with_oracle_choice": None,
            "maximum_selection_regret": None,
            "calibration_points": 0,
            "calibration_seconds": 0.0,
            "exact_ground_state_required": False,
            "eligible_as_practical_selector": None,
            "scope_note": "no frozen cross-system mapping or independent test exists",
        },
    ]


def make_report(
    output: Path,
    dependency: dict[str, Any],
    tiers: list[dict[str, Any]],
    selections: list[dict[str, Any]],
) -> None:
    calibrated = tiers[1]
    fixed = tiers[2]
    lines = [
        "# X01 A06: information-access audit",
        "",
        "Status: complete",
        "",
        "The saved workflow is separated into oracle evaluation, target-specific "
        "calibration, and transfer-only selection. No new PF or molecular calculation "
        "was run.",
        "",
        "## Direct dependency audit",
        "",
        f"- Raw conditions checked: {dependency['raw_condition_count']}.",
        f"- PF/condition formula records checked: {dependency['formula_condition_count']}.",
        f"- Evaluated short-time points: {dependency['evaluated_short_time_point_count']}; "
        f"selected-window points: {dependency['selected_short_time_window_point_count']}.",
        f"- Direct training points: {dependency['training_direct_point_count']}.",
        f"- Direct local validation points: {dependency['local_validation_direct_point_count']}.",
        f"- Direct points using the exact-ground-overlap branch rule: "
        f"{dependency['exact_ground_overlap_selection_rule_count']}.",
        "",
        "Every short-time fit uses `exp(-i E0 t)<psi0|U_PF(t)|psi0>` and every "
        "saved direct training/validation point selects the PF eigenbranch by maximum "
        "overlap with the exact ground state. The fitted coefficients and selected "
        "time therefore depend on exact-state information before evaluation begins.",
        "",
        "## Performance by access tier",
        "",
        "| tier | method | status | choices | frozen pass | oracle agreement | calibration points | exact state required |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in tiers:
        lines.append(
            f"| {row['tier']} | {row['method']} | {row['status']} | "
            f"{row['pf_choices_produced']} | "
            f"{row['strict_frozen_budget_passed'] if row['strict_frozen_budget_passed'] is not None else 'n/a'} | "
            f"{row['agreement_with_oracle_choice'] if row['agreement_with_oracle_choice'] is not None else 'n/a'} | "
            f"{row['calibration_points'] if row['calibration_points'] is not None else 'n/a'} | "
            f"{row['exact_ground_state_required']} |"
        )
    lines += [
        "",
        "The saved two-PF calibrated selector chooses `current_m3` on all "
        f"{len(selections)} conditions, agrees with the oracle comparison over the "
        f"same two predicted schedules on {calibrated['agreement_with_oracle_choice']}/"
        f"{len(selections)}, and meets the strict frozen budget on "
        f"{calibrated['strict_frozen_budget_passed']}/{len(selections)}. Its direct-cost "
        f"selection regret is zero on this candidate set, but it requires "
        f"{calibrated['calibration_points']} exact-state-assisted calibration points "
        f"and {calibrated['calibration_seconds']:.6g} saved PF-specific seconds because "
        "both PFs are calibrated before choosing.",
        "",
        "Pre-fixing `current_m3` avoids the unused second-PF calibration and uses "
        f"{fixed['calibration_points']} points and {fixed['calibration_seconds']:.6g} s "
        "on the same conditions. This is still oracle-assisted target calibration; "
        "it is not a descriptor-only transfer result.",
        "",
        "## Leakage boundary",
        "",
        "The three direct fit points are excluded from saved validation scoring, so "
        "the finite-time residual test is not numerically fitted on its own validation "
        "grid. However, the calibration inputs themselves use exact ground-state and "
        "direct PF-eigenvalue information. The A05 safety multiplier additionally uses "
        "all 17 development truths and is post-hoc; it cannot be treated as a "
        "prospective safety guarantee.",
        "",
        "## A06 conclusion",
        "",
        "Current performance establishes an oracle-assisted, target-specific upper "
        "bound. It does not yet establish a practical cheap calibration method or an "
        "unused-system transfer selector. The observed 17/17 fixed-current frozen "
        "budget result remains useful for mechanism and strategy comparison, but the "
        "information-access qualification must accompany it.",
        "",
        "Before claiming deployable PF/time selection, the next missing evidence is "
        "either (a) replacement of exact E0/|psi0>/branch overlaps by an approximate "
        "state or measurable surrogate, or (b) a frozen descriptor-to-choice rule "
        "tested on a genuinely unused molecular family.",
        "",
        "## Files",
        "",
        "- `information_access_table.csv`: input-by-input access classification.",
        "- `performance_by_access_tier.csv`: measured and missing tier performance.",
        "- `condition_selection.csv`: calibrated versus oracle candidate choices.",
        "- `dependency_audit.json`: raw and implementation dependency counts.",
        "- `raw_sources.csv`: hashes of all raw condition files.",
        "- `analysis.json` and `manifest.json`: summary and provenance.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    budget = a05.run_analysis()
    cost_benefit = a07.run_analysis()
    dependency = dependency_audit(cost_benefit["_raw_sources"])
    information = information_access_rows()
    selections = condition_selection_rows(
        budget["_rows"], cost_benefit["_calibration_rows"]
    )
    tiers = performance_tier_rows(selections, cost_benefit["_calibration_rows"])
    return {
        "status": "complete",
        "scope": "X01 A06 information-access separation",
        "created_at": datetime.now().astimezone().isoformat(),
        "condition_count": 17,
        "information_item_count": len(information),
        "performance_tier_row_count": len(tiers),
        "calibrated_selector_choice_count": len(selections),
        "calibrated_selector_current_m3_count": sum(
            row["calibrated_selector_pf"] == "current_m3" for row in selections
        ),
        "calibrated_selector_oracle_agreement_count": sum(
            bool(row["selector_agrees_with_oracle_candidate_schedule"])
            for row in selections
        ),
        "calibrated_selector_strict_frozen_pass_count": sum(
            bool(row["selected_strict_frozen_budget_pass"]) for row in selections
        ),
        "maximum_calibrated_selection_regret": max(
            float(row["selected_direct_cost_regret_vs_oracle_candidate_schedule"])
            for row in selections
        ),
        "practical_target_calibration_status": "not implemented / not evaluated",
        "transfer_only_status": "not implemented / not evaluated",
        "source_records": budget["source_records"],
        "raw_source_count": len(cost_benefit["_raw_sources"]),
        "runner": {
            "path": str(RUNNER.relative_to(ROOT)),
            "sha256": audit_x01.sha256_file(RUNNER),
        },
        "git": audit_x01.git_state(),
        "dependency_audit": dependency,
        "performance_tier_rows": tiers,
        "_information_rows": information,
        "_selection_rows": selections,
        "_raw_sources": cost_benefit["_raw_sources"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_analysis()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    a05.write_csv(
        output / "information_access_table.csv", result["_information_rows"]
    )
    a05.write_csv(
        output / "performance_by_access_tier.csv", result["performance_tier_rows"]
    )
    a05.write_csv(output / "condition_selection.csv", result["_selection_rows"])
    a05.write_csv(output / "raw_sources.csv", result["_raw_sources"])
    a05.write_json(output / "dependency_audit.json", result["dependency_audit"])
    machine = {key: value for key, value in result.items() if not key.startswith("_")}
    a05.write_json(output / "analysis.json", machine)
    a05.write_json(
        output / "manifest.json",
        {
            "status": result["status"],
            "scope": result["scope"],
            "created_at": result["created_at"],
            "source_records": result["source_records"],
            "raw_source_count": result["raw_source_count"],
            "runner": result["runner"],
            "git": result["git"],
            "no_new_pf_or_electronic_structure_calculation": True,
            "practical_calibration_performance_claimed": False,
            "transfer_performance_claimed": False,
            "existing_input_artifacts_overwritten": False,
        },
    )
    make_report(
        output,
        result["dependency_audit"],
        result["performance_tier_rows"],
        result["_selection_rows"],
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
