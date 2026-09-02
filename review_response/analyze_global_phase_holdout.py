"""Aggregate same-template phase correction and conservative hold-out checks."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

from trotterlib.config import BETA, TARGET_ERROR
from validate_global_phase_corrected_cost import LABELS, _atomic_json, _cost


THRESHOLD = 0.10
SMALL_CHAINS = (2, 4, 5, 6, 7)
LARGE_CHAINS = (9, 10, 11)


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:
        return None


def strict_leading_validity(
    times: np.ndarray,
    errors: np.ndarray,
    model: np.ndarray,
    *,
    noise_floor: float,
    fit_start: float,
    threshold: float = THRESHOLD,
) -> dict[str, Any]:
    """Return the leading valid interval without accepting later re-entry.

    Values before the fit window or below the numerical floor are excluded.
    Once the first eligible value fails, later accidental crossings are never
    promoted to a validity interval.
    """
    times = np.asarray(times, dtype=float)
    errors = np.asarray(errors, dtype=float)
    model = np.asarray(model, dtype=float)
    if not (times.shape == errors.shape == model.shape):
        raise ValueError("times, errors, and model must have identical shapes")
    eligible = (
        np.isfinite(times)
        & np.isfinite(errors)
        & np.isfinite(model)
        & (times >= float(fit_start) - 1e-13)
        & (errors >= float(noise_floor))
        & (model >= float(noise_floor))
        & (model > 0)
    )
    eligible_indices = np.flatnonzero(eligible)
    if eligible_indices.size == 0:
        return {
            "status": "not validated",
            "reason": "no eligible points above the numerical floor",
            "first_eligible_time": None,
            "last_valid_time": None,
            "cap_candidate": None,
            "first_failure_time": None,
            "right_censored": False,
        }
    start = int(eligible_indices[0])
    ratios = errors / model
    deviations = np.abs(ratios - 1.0)
    valid_indices: list[int] = []
    failure_index: int | None = None
    gap_index: int | None = None
    for index in range(start, times.size):
        if not eligible[index]:
            gap_index = index
            break
        if deviations[index] > float(threshold):
            failure_index = index
            break
        valid_indices.append(index)
    if not valid_indices:
        return {
            "status": "failed",
            "reason": "the first eligible short-time point exceeds tolerance",
            "first_eligible_time": float(times[start]),
            "first_eligible_ratio": float(ratios[start]),
            "last_valid_time": None,
            "cap_candidate": None,
            "first_failure_time": float(times[failure_index or start]),
            "first_failure_ratio": float(ratios[failure_index or start]),
            "right_censored": False,
        }
    last = valid_indices[-1]
    right_censored = failure_index is None and gap_index is None
    cap_candidate = None if right_censored else float(times[last])
    reason = (
        "all sampled eligible points pass; upper boundary is not bracketed"
        if right_censored
        else "first failure bracketed after a leading valid interval"
    )
    if gap_index is not None:
        reason = "eligible grid ended before a tolerance failure was bracketed"
    return {
        "status": "pass" if not right_censored and gap_index is None else "not validated",
        "reason": reason,
        "first_eligible_time": float(times[start]),
        "first_eligible_ratio": float(ratios[start]),
        "last_valid_time": float(times[last]),
        "last_valid_ratio": float(ratios[last]),
        "cap_candidate": cap_candidate,
        "first_failure_time": (
            None if failure_index is None else float(times[failure_index])
        ),
        "first_failure_ratio": (
            None if failure_index is None else float(ratios[failure_index])
        ),
        "right_censored": bool(right_censored),
        "num_leading_valid_points": len(valid_indices),
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sweep_path(sweep_dir: Path, h_chain: int, slug: str) -> Path:
    return sweep_dir / f"H{h_chain}_{slug}_same_template.json"


def _point_arrays(sweep: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    times = np.asarray([item["time"] for item in sweep["points"]], dtype=float)
    errors = np.asarray(
        [item["e_proxy_corrected_hartree"] for item in sweep["points"]],
        dtype=float,
    )
    return times, errors


def _small_fit(
    *,
    root: Path,
    wide: dict[str, Any],
    h_chain: int,
    label: str,
) -> tuple[float, int, float, float, dict[str, Any]]:
    if h_chain <= 5:
        fit = wide["results"][f"H{h_chain}"][label]["initial_fit"]
        return (
            float(fit["alpha"]),
            int(fit["formal_order"]),
            float(fit["noise_floor_hartree"]),
            float(fit["fit_window"]["t_start"]),
            fit,
        )
    direct_path = (
        root
        / "artifacts/server_cost_validity/h6_h7_analytic_schedule"
        / (
            "H6_analytic_direct_validation.json"
            if h_chain == 6
            else "fci_checked/H7_analytic_direct_validation_fci_checked.json"
        )
    )
    case = _load_json(direct_path)["results"][label]
    fit = case["alpha_fit"]
    selected = fit["selected_window"]
    return (
        float(case["alpha"]),
        int(case["formal_order"]),
        float(fit["noise_floor_hartree"]),
        float(selected["t_start"]),
        fit,
    )


def _direct_case(
    *,
    root: Path,
    h_chain: int,
    label: str,
    alpha: float,
    order: int,
    noise_floor: float,
    fit_start: float,
) -> dict[str, Any]:
    if h_chain <= 5:
        path = root / f"artifacts/server_cost_validity/H{h_chain}_wide_direct_validation.json"
        case = _load_json(path)["results"][label]
        times = np.asarray(case["times"], dtype=float)
        errors = np.asarray(case["direct_errors_hartree"], dtype=float)
        model = alpha * times**order
        validity = strict_leading_validity(
            times,
            errors,
            model,
            noise_floor=noise_floor,
            fit_start=fit_start,
        )
        return {
            "status": "complete",
            "source": str(path),
            "grid_kind": "wide direct PF eigenphase",
            "validity": validity,
            "minimum_selected_ground_state_overlap_probability": float(
                case["minimum_selected_ground_state_overlap_probability"]
            ),
            "maximum_unitarity_residual_frobenius_norm": float(
                case["maximum_unitarity_residual_frobenius_norm"]
            ),
        }
    path = (
        root
        / "artifacts/server_cost_validity/h6_h7_analytic_schedule"
        / (
            "H6_analytic_direct_validation.json"
            if h_chain == 6
            else "fci_checked/H7_analytic_direct_validation_fci_checked.json"
        )
    )
    case = _load_json(path)["results"][label]
    schedule = case["local_schedule"]
    times = np.asarray([item["time"] for item in schedule], dtype=float)
    errors = np.asarray([item["direct_error_hartree"] for item in schedule], dtype=float)
    ratios = errors / (alpha * times**order)
    maximum_residual = max(
        float(item["point"]["unitarity_residual_frobenius_norm"])
        for item in schedule
    )
    return {
        "status": "not validated",
        "source": str(path),
        "grid_kind": "three-point analytic-time schedule",
        "reason": (
            "the direct grid has a gap between the short-time fit window and "
            "0.9*t_ana, so a leading continuous direct t_valid cannot be established"
        ),
        "times": [float(value) for value in times],
        "direct_over_model": [float(value) for value in ratios],
        "maximum_unitarity_residual_frobenius_norm": maximum_residual,
        "validity": {
            "status": "not validated",
            "last_valid_time": None,
            "cap_candidate": None,
        },
    }


def analyze(
    *,
    root: Path,
    sweep_dir: Path,
    h9_source_dir: Path,
    output_json: Path,
    output_markdown: Path,
) -> dict[str, Any]:
    if output_json.exists() or output_markdown.exists():
        raise FileExistsError("refusing to overwrite aggregate outputs")
    wide_path = root / "artifacts/server_cost_validity/wide_time_cost_analysis.json"
    wide = _load_json(wide_path)
    schedule_path = h9_source_dir / "analytic_schedule.json"
    schedule = _load_json(schedule_path)

    priority1: dict[str, Any] = {}
    p1_all_phase_pass = True
    for h_chain in LARGE_CHAINS:
        priority1[f"H{h_chain}"] = {}
        for slug, label in LABELS.items():
            sweep_path = _sweep_path(sweep_dir, h_chain, slug)
            sweep = _load_json(sweep_path)
            source_path = h9_source_dir / f"H{h_chain}_{'h9_h11_m5_tana' if slug == 'm5' else 'h9_h11_y8_tana'}.json"
            source = _load_json(source_path)
            source_case = next(item for item in source["results"] if item["label"] == label)
            task = schedule["tasks"][f"H{h_chain}"][label]
            alpha = float(task["alpha"])
            order = int(task["formal_order"])
            t_ana = float(task["t_ana"])
            legacy_perturbative = np.asarray(
                source_case["errors_hartree"], dtype=float
            )
            if len(legacy_perturbative) != len(sweep["points"]):
                raise ValueError(f"H{h_chain} {label}: sweep/source length mismatch")
            rows = []
            for index, point in enumerate(sweep["points"]):
                time_value = float(point["time"])
                model = float(alpha * time_value**order)
                proxy = float(point["e_proxy_corrected_hartree"])
                corrected_overlap = point["corrected_phase_rotated_overlap"]
                pert = float(
                    abs(float(corrected_overlap["imag"]) / time_value)
                )
                rotations = int(sweep["product_formula"]["pauli_rotations_per_step"])
                rows.append(
                    {
                        **point,
                        "time_over_t_ana": float(time_value / t_ana),
                        "e_model_hartree": model,
                        "e_pert_hartree": pert,
                        "legacy_separate_template_e_pert_hartree": float(
                            legacy_perturbative[index]
                        ),
                        "e_pert_over_e_model": float(pert / model),
                        "e_proxy_over_e_model": float(proxy / model),
                        "C_model": _cost(time_value, model, rotations=rotations),
                        "C_pert": _cost(time_value, pert, rotations=rotations),
                        "C_proxy_corrected": _cost(time_value, proxy, rotations=rotations),
                    }
                )
            at_t_ana = min(rows, key=lambda item: abs(item["time"] - t_ana))
            phase_pass = bool(
                sweep["phase_checks"]["zero_phase_pass"]
                and sweep["phase_checks"]["continuity_pass"]
            )
            p1_all_phase_pass &= phase_pass
            priority1[f"H{h_chain}"][label] = {
                "status": "complete" if phase_pass else "failed",
                "source_same_template_sweep": str(sweep_path),
                "source_perturbative_json": str(source_path),
                "fixed_order_alpha": alpha,
                "formal_order": order,
                "t_ana": t_ana,
                "pauli_rotations_per_step": int(
                    sweep["product_formula"]["pauli_rotations_per_step"]
                ),
                "t0_calibration": sweep["calibration"],
                "phase_checks": sweep["phase_checks"],
                "points": rows,
                "at_t_ana": at_t_ana,
                "uncorrected_overlap_phase_cost_used": False,
            }

    small: dict[str, Any] = {}
    for h_chain in SMALL_CHAINS:
        small[f"H{h_chain}"] = {}
        for slug, label in LABELS.items():
            sweep_path = _sweep_path(sweep_dir, h_chain, slug)
            sweep = _load_json(sweep_path)
            alpha, order, noise, fit_start, fit_details = _small_fit(
                root=root, wide=wide, h_chain=h_chain, label=label
            )
            times, proxy = _point_arrays(sweep)
            model = alpha * times**order
            proxy_validity = strict_leading_validity(
                times,
                proxy,
                model,
                noise_floor=noise,
                fit_start=fit_start,
            )
            direct = _direct_case(
                root=root,
                h_chain=h_chain,
                label=label,
                alpha=alpha,
                order=order,
                noise_floor=noise,
                fit_start=fit_start,
            )
            points = []
            for point, model_value in zip(sweep["points"], model, strict=True):
                points.append(
                    {
                        **point,
                        "e_model_hartree": float(model_value),
                        "e_proxy_over_e_model": float(
                            point["e_proxy_corrected_hartree"] / model_value
                        ),
                    }
                )
            small[f"H{h_chain}"][label] = {
                "status": (
                    "complete"
                    if sweep["phase_checks"]["zero_phase_pass"]
                    and sweep["phase_checks"]["continuity_pass"]
                    else "failed"
                ),
                "source_same_template_sweep": str(sweep_path),
                "formal_order": order,
                "fixed_order_alpha": alpha,
                "noise_floor_hartree": noise,
                "fit_window_start": fit_start,
                "fit_details": fit_details,
                "t0_calibration": sweep["calibration"],
                "phase_checks": sweep["phase_checks"],
                "proxy_validity": proxy_validity,
                "direct_validation": direct,
                "points": points,
            }

    folds_spec = [
        ((2, 4), 5),
        ((2, 4, 5), 6),
        ((2, 4, 5, 6), 7),
    ]
    folds: dict[str, list[dict[str, Any]]] = {label: [] for label in LABELS.values()}
    all_folds_pass: dict[str, bool] = {}
    for label in LABELS.values():
        for training, held_out in folds_spec:
            training_caps = {
                f"H{h}": small[f"H{h}"][label]["proxy_validity"]["cap_candidate"]
                for h in training
            }
            held_cap = small[f"H{held_out}"][label]["direct_validation"]["validity"].get(
                "cap_candidate"
            )
            if any(value is None for value in training_caps.values()):
                status = "not validated"
                predicted = None
                reason = "at least one training proxy upper boundary is not bracketed"
            elif held_cap is None:
                status = "not validated"
                predicted = float(min(training_caps.values()))
                reason = "held-out direct t_valid is not continuously established"
            else:
                predicted = float(min(training_caps.values()))
                status = "pass" if predicted <= float(held_cap) else "failed"
                reason = (
                    "minimum training proxy cap does not exceed held-out direct cap"
                    if status == "pass"
                    else "predicted proxy cap exceeds held-out direct cap"
                )
            folds[label].append(
                {
                    "training_systems": [f"H{value}" for value in training],
                    "held_out_system": f"H{held_out}",
                    "common_rule": "minimum training proxy cap at 10% tolerance",
                    "training_proxy_caps": training_caps,
                    "predicted_conservative_cap": predicted,
                    "held_out_direct_t_valid": held_cap,
                    "status": status,
                    "reason": reason,
                }
            )
        all_folds_pass[label] = all(item["status"] == "pass" for item in folds[label])

    priority3 = {
        "status": "not validated",
        "reason": (
            "H6/H7 do not provide a continuous direct t_valid on the short-to-analytic "
            "interval, and no calibrated moment/Ritz implementation with <=10% H6/H7 "
            "error is present; H8 was therefore not run"
        ),
        "H8_computation_started": False,
    }
    priority4 = {
        label: {
            "status": "not validated",
            "reason": "the complete H2-H7 conservative hold-out prerequisite did not pass",
            "new_safe_time_search_started": False,
        }
        for label in LABELS.values()
    }
    final_classification = {
        label: (
            "cap-constrained sensitivity only"
            if all_folds_pass[label]
            else "short-time/asymptotic reference only"
        )
        for label in LABELS.values()
    }
    payload = {
        "schema_version": 1,
        "purpose": "global-phase correction, overlap-proxy hold-out calibration, and finite-time support classification",
        "created_at": _now(),
        "git_commit": _git_commit(),
        "status": "complete with failed/not validated prerequisites",
        "rules": {
            "relative_tolerance": THRESHOLD,
            "leading_interval": (
                "begin at the fit window after numerical-floor masking; stop at the first failure; never accept later re-entry"
            ),
            "holdout_prediction": "minimum bracketed training proxy cap",
            "same_threshold_for_both_product_formulae": True,
        },
        "sources": {
            "wide_time_analysis": str(wide_path),
            "h9_h11_schedule": str(schedule_path),
            "same_template_sweeps": str(sweep_dir),
        },
        "priority1_h9_h11_global_phase": {
            "status": "complete" if p1_all_phase_pass else "failed",
            "results": priority1,
            "uncorrected_overlap_phase_cost_used": False,
        },
        "priority2_holdout_calibration": {
            "status": (
                "pass"
                if all(all_folds_pass.values())
                else "failed/not validated"
            ),
            "systems": small,
            "folds": folds,
            "all_folds_pass": all_folds_pass,
        },
        "priority3_h8_direct_like": priority3,
        "priority4_h9_h11_safe_time_search": priority4,
        "final_classification": final_classification,
        "cost_model": {
            "formula": "BETA*N_rotation/[t*(epsilon_E-e(t))]",
            "BETA": float(BETA),
            "epsilon_E_hartree": float(TARGET_ERROR),
        },
    }
    _atomic_json(output_json, payload)

    lines = [
        "# Global-phase and finite-time proxy validation",
        "",
        f"Commit: `{payload['git_commit']}`",
        "",
        "The uncorrected overlap phase is retained only as raw diagnostic data and is not used for physical costs.",
        "",
        "## Priority 1: H9--H11 same-template phase correction",
        "",
        "| System | PF | raw t=0 phase | t_ana | e_pert/model | e_proxy/model | C_proxy/C_model | survival | status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for h_chain in LARGE_CHAINS:
        for label in LABELS.values():
            case = priority1[f"H{h_chain}"][label]
            point = case["at_t_ana"]
            cost_ratio = (
                None
                if point["C_proxy_corrected"] is None or point["C_model"] is None
                else point["C_proxy_corrected"] / point["C_model"]
            )
            lines.append(
                f"| H{h_chain} | {label} | {case['t0_calibration']['raw_phase_rad']:.7g} | "
                f"{case['t_ana']:.7g} | {point['e_pert_over_e_model']:.5g} | "
                f"{point['e_proxy_over_e_model']:.5g} | "
                f"{cost_ratio if cost_ratio is not None else 'invalid'} | "
                f"{point['ground_state_survival_probability']:.8f} | {case['status']} |"
            )
    lines.extend(
        [
            "",
            "## Priority 2: 10% hold-out calibration",
            "",
            "| System | PF | proxy cap | direct t_valid | proxy status | direct status |",
            "|---|---|---:|---:|---|---|",
        ]
    )
    for h_chain in SMALL_CHAINS:
        for label in LABELS.values():
            case = small[f"H{h_chain}"][label]
            proxy_valid = case["proxy_validity"]
            direct_valid = case["direct_validation"]["validity"]
            lines.append(
                f"| H{h_chain} | {label} | {proxy_valid.get('cap_candidate')} | "
                f"{direct_valid.get('cap_candidate')} | {proxy_valid['status']} | "
                f"{direct_valid['status']} |"
            )
    lines.extend(
        [
            "",
            "| PF | training -> held-out | predicted cap | held-out direct | result |",
            "|---|---|---:|---:|---|",
        ]
    )
    for label, entries in folds.items():
        for item in entries:
            lines.append(
                f"| {label} | {','.join(item['training_systems'])} -> {item['held_out_system']} | "
                f"{item['predicted_conservative_cap']} | {item['held_out_direct_t_valid']} | "
                f"{item['status']} |"
            )
    lines.extend(
        [
            "",
            "## Priority 3 and 4",
            "",
            f"- H8 direct-like diagnosis: **{priority3['status']}**. {priority3['reason']}",
            "- H9--H11 safe-time expansion: **not validated** because the complete hold-out prerequisite did not pass; no additional expansion was launched.",
            "",
            "## Final classification",
            "",
        ]
    )
    lines.extend(f"- {label}: `{classification}`" for label, classification in final_classification.items())
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved: {output_json}")
    print(f"saved: {output_markdown}")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--sweep-dir", type=Path, required=True)
    parser.add_argument("--h9-source-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analyze(
        root=args.root.resolve(),
        sweep_dir=args.sweep_dir.resolve(),
        h9_source_dir=args.h9_source_dir.resolve(),
        output_json=args.output_json.resolve(),
        output_markdown=args.output_markdown.resolve(),
    )


if __name__ == "__main__":
    main()
