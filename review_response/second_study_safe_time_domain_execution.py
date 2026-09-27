"""Shared execution helpers for the frozen second-study protocol.

The functions in this module are deliberately split into oracle-free Phase A
selection and truth-only Phase B scoring.  Importing the module performs no
molecular construction, filesystem discovery, GPU allocation, or truth access.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

import numpy as np

from review_response import second_study_safe_time_domain_guard as guard


PHASE_A_SCHEMA = "second_study_safe_time_domain_phase_a_predictions_v1"
PHASE_A_INPUT_SCHEMA = "second_study_safe_time_domain_phase_a_input_v1"
PHASE_B_BRANCH_RULE_VERSION = "anchor_ground_then_previous_overlap_v1"
PHASE_B_RESULT_SCHEMA = "second_study_safe_time_domain_phase_b_result_v1"
FORMULA_ID = "current_m3"


class ExecutionError(RuntimeError):
    """Raised when a frozen execution or integrity rule is violated."""


def now() -> str:
    return datetime.now().astimezone().isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(encoded)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def git_output(project_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def load_frozen_protocol(protocol_path: Path) -> tuple[dict[str, Any], str]:
    """Load a caller-supplied protocol only when it is byte-identical."""

    bundled, expected = guard.load_protocol()
    path = protocol_path.resolve()
    if not path.is_file():
        raise ExecutionError(f"protocol does not exist: {path}")
    actual = sha256_file(path)
    if actual != expected:
        raise ExecutionError(
            f"protocol SHA-256 mismatch: expected {expected}, obtained {actual}"
        )
    supplied = load_json(path)
    if supplied != bundled:
        raise ExecutionError("protocol JSON differs despite matching sidecar")
    return supplied, actual


def condition_names(protocol: Mapping[str, Any]) -> list[str]:
    return [
        str(row["name"])
        for row in protocol["data_partition"]["independent_evaluation"][
            "conditions"
        ]
    ]


def condition_specs(protocol: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["name"]): dict(row)
        for row in protocol["data_partition"]["independent_evaluation"][
            "conditions"
        ]
    }


def formula_sequence(protocol: Mapping[str, Any]) -> tuple[float, ...]:
    if protocol["scope"]["formulae"] != [FORMULA_ID]:
        raise ExecutionError("frozen PF scope changed")
    return tuple(float(value) for value in protocol["formula"]["s2_sequence"])


def formula_sha256(protocol: Mapping[str, Any]) -> str:
    return canonical_json_sha256(
        {
            "id": protocol["formula"]["id"],
            "formal_order": protocol["formula"]["formal_order"],
            "s2_sequence": list(formula_sequence(protocol)),
        }
    )


def fit_signed_power_model(
    times: Sequence[float],
    values: Sequence[float],
    powers: Sequence[int] = (4, 6),
) -> dict[str, Any]:
    """Fit a signed power model using a scaled design matrix."""

    x = np.asarray(times, dtype=float)
    y = np.asarray(values, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or x.size != y.size or x.size < len(powers):
        raise ExecutionError("invalid signed-fit inputs")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)) or np.any(x <= 0):
        raise ExecutionError("non-finite signed-fit inputs")
    design = np.column_stack([x ** int(power) for power in powers])
    norms = np.linalg.norm(design, axis=0)
    if np.any(norms == 0.0):
        raise ExecutionError("degenerate signed-fit design")
    scaled_design = design / norms[None, :]
    scaled_coefficients = np.linalg.lstsq(
        scaled_design, y, rcond=None
    )[0]
    coefficients = scaled_coefficients / norms
    prediction = design @ coefficients
    return {
        "coefficient_powers": [int(power) for power in powers],
        "coefficient_values": [float(value) for value in coefficients],
        "coefficient_signs": [int(np.sign(value)) for value in coefficients],
        "scaled_design_condition_number": float(np.linalg.cond(scaled_design)),
        "maximum_absolute_residual_hartree": float(
            np.max(np.abs(prediction - y))
        ),
        "training_times_hartree_inverse": [float(value) for value in x],
    }


def evaluate_model(model: Mapping[str, Any], time_value: float) -> float:
    return float(
        sum(
            float(coefficient) * float(time_value) ** int(power)
            for power, coefficient in zip(
                model["coefficient_powers"],
                model["coefficient_values"],
                strict=True,
            )
        )
    )


def required_cost(
    time_value: float,
    error_hartree: float,
    rotations: int,
    epsilon: float,
    beta: float,
) -> float | None:
    if (
        not math.isfinite(float(time_value))
        or not math.isfinite(float(error_hartree))
        or float(time_value) <= 0.0
        or float(error_hartree) < 0.0
        or float(error_hartree) >= float(epsilon)
    ):
        return None
    return float(
        float(beta)
        * int(rotations)
        / (float(time_value) * (float(epsilon) - float(error_hartree)))
    )


def frozen_budget(
    time_value: float,
    predicted_error_hartree: float,
    rotations: int,
    epsilon: float,
    beta: float,
    gamma: float,
) -> float | None:
    cost = required_cost(
        time_value, predicted_error_hartree, rotations, epsilon, beta
    )
    return None if cost is None else float(gamma) * cost


def _strategy_record(
    *,
    strategy: str,
    status: str,
    time_value: float,
    t_ana: float,
    signed_prediction: float,
    guarded_error: float,
    rotations: int,
    protocol: Mapping[str, Any],
    selection_source: str,
    operational: bool,
    extension_selected: bool,
) -> dict[str, Any]:
    epsilon = float(protocol["scope"]["target_error_hartree"])
    beta = float(protocol["cost_model"]["beta"])
    gamma = float(protocol["scope"]["budget_multiplier_gamma"])
    cost = required_cost(time_value, guarded_error, rotations, epsilon, beta)
    budget = frozen_budget(
        time_value, guarded_error, rotations, epsilon, beta, gamma
    )
    if cost is None or budget is None:
        raise ExecutionError(f"{strategy}: selected an infeasible prediction")
    return {
        "strategy": strategy,
        "status": status,
        "selected_time_hartree_inverse": float(time_value),
        "selected_relative_to_t_ana": float(time_value / t_ana),
        "predicted_signed_shift_hartree": float(signed_prediction),
        "predicted_error_hartree": float(abs(signed_prediction)),
        "guarded_error_hartree": float(guarded_error),
        "predicted_required_pauli_rotations": float(cost),
        "frozen_pauli_rotation_budget": float(budget),
        "rotation_count_per_pf_step": int(rotations),
        "selection_source": selection_source,
        "operational": bool(operational),
        "extension_selected": bool(extension_selected),
    }


def _continuous_model_optimum(
    model: Mapping[str, Any],
    t_ana: float,
    rotations: int,
    protocol: Mapping[str, Any],
    maximum_relative: float | None,
) -> tuple[float, float, float]:
    spec = protocol["phase_a"]["original_current_m3_rule"]
    lower, upper = (float(value) for value in spec["optimization_relative_interval"])
    if maximum_relative is not None:
        upper = min(upper, float(maximum_relative))
    relative = np.linspace(lower, upper, int(spec["optimization_grid_points"]))
    times = relative * float(t_ana)
    signed = np.asarray([evaluate_model(model, value) for value in times])
    epsilon = float(protocol["scope"]["target_error_hartree"])
    beta = float(protocol["cost_model"]["beta"])
    costs = np.full(times.shape, np.inf)
    valid = np.abs(signed) < epsilon
    costs[valid] = beta * int(rotations) / (
        times[valid] * (epsilon - np.abs(signed[valid]))
    )
    selected = int(np.argmin(costs))
    if not np.isfinite(costs[selected]):
        raise ExecutionError("no feasible current_m3 model point")
    return float(times[selected]), float(signed[selected]), float(costs[selected])


def select_phase_a_strategies(
    *,
    t_ana: float,
    observations_by_relative_time: Mapping[float, Mapping[str, Any]],
    pooled_extra_points: Sequence[Mapping[str, Any]] = (),
    rotations: int,
    protocol: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Apply all four frozen strategies to oracle-free proxy observations.

    ``observations_by_relative_time`` must contain the fixed five base points
    and may contain a prefix of the eight extension candidates.  Each value
    contains at least ``proxy_hartree`` and ``cancellation_index``.
    """

    if not math.isfinite(float(t_ana)) or float(t_ana) <= 0.0:
        raise ExecutionError("proxy analytic time must be positive and finite")
    phase_a = protocol["phase_a"]
    original = phase_a["original_current_m3_rule"]
    extension = phase_a["extension"]
    epsilon = float(protocol["scope"]["target_error_hartree"])
    sign_floor = max(1e-12, 1e-6 * epsilon)

    def point(relative: float) -> Mapping[str, Any]:
        try:
            value = observations_by_relative_time[float(relative)]
        except KeyError as exc:
            raise ExecutionError(f"missing proxy observation at {relative} t_ana") from exc
        measured = float(value["proxy_hartree"])
        if not math.isfinite(measured):
            raise ExecutionError(f"non-finite proxy observation at {relative} t_ana")
        return value

    training_relative = [
        float(value) for value in original["model_training_relative_to_t_ana"]
    ]
    training_times = [relative * float(t_ana) for relative in training_relative]
    training_values = [float(point(relative)["proxy_hartree"]) for relative in training_relative]
    original_model = fit_signed_power_model(training_times, training_values)

    primary_relative = float(original["cancellation_primary_relative_to_t_ana"])
    robust_relative = float(original["cancellation_robustness_relative_to_t_ana"])
    sentinel_relative = float(original["sentinel_relative_to_t_ana"])
    primary = point(primary_relative)
    robust = point(robust_relative)
    sentinel = point(sentinel_relative)
    sentinel_value = float(sentinel["proxy_hartree"])
    sentinel_prediction = evaluate_model(
        original_model, sentinel_relative * float(t_ana)
    )
    sentinel_residual = abs(sentinel_value - sentinel_prediction)
    sign_indeterminate = (
        abs(sentinel_value) <= sign_floor
        or abs(sentinel_prediction) <= sign_floor
    )
    sign_mismatch = (
        False
        if sign_indeterminate
        else bool(np.sign(sentinel_value) != np.sign(sentinel_prediction))
    )
    cancellation_fallback = float(primary["cancellation_index"]) < float(
        original["cancellation_fallback_below"]
    )
    residual_fallback = sentinel_residual > float(
        original["sentinel_residual_fallback_over_epsilon"]
    ) * epsilon
    fallback = bool(
        cancellation_fallback
        or residual_fallback
        or sign_indeterminate
        or sign_mismatch
    )
    maximum = (
        float(original["fallback_cap_relative_to_t_ana"])
        if fallback
        else None
    )
    current_time, current_signed, _ = _continuous_model_optimum(
        original_model, t_ana, rotations, protocol, maximum
    )
    current = _strategy_record(
        strategy="current_fallback",
        status="selected_fallback_cap" if fallback else "selected_uncapped_current_rule",
        time_value=current_time,
        t_ana=t_ana,
        signed_prediction=current_signed,
        guarded_error=abs(current_signed),
        rotations=rotations,
        protocol=protocol,
        selection_source="original_three_point_model",
        operational=True,
        extension_selected=False,
    )
    strategies: dict[str, dict[str, Any]] = {"current_fallback": current}
    diagnostic: dict[str, Any] = {
        "original_model": original_model,
        "cancellation_index_primary": float(primary["cancellation_index"]),
        "cancellation_index_robustness": float(robust["cancellation_index"]),
        "sentinel_measured_proxy_hartree": sentinel_value,
        "sentinel_model_prediction_hartree": sentinel_prediction,
        "sentinel_residual_hartree": float(sentinel_residual),
        "sign_noise_floor_hartree": float(sign_floor),
        "fallback_reasons": {
            "cancellation": cancellation_fallback,
            "sentinel_residual": residual_fallback,
            "sign_indeterminate": sign_indeterminate,
            "sign_mismatch": sign_mismatch,
        },
        "fallback_triggered": fallback,
        "extension_evaluations": [],
    }

    phase_b_grid = [
        float(value) for value in protocol["phase_b"]["fixed_candidate_grid_relative_to_t_ana"]
    ]
    counterfactual_candidates: list[tuple[float, float, float]] = []
    for relative in phase_b_grid:
        time_value = relative * float(t_ana)
        signed = evaluate_model(original_model, time_value)
        cost = required_cost(
            time_value,
            abs(signed),
            rotations,
            epsilon,
            float(protocol["cost_model"]["beta"]),
        )
        if cost is not None:
            counterfactual_candidates.append((cost, time_value, signed))
    if counterfactual_candidates:
        _, counter_time, counter_signed = min(counterfactual_candidates)
        strategies["uncapped_counterfactual"] = _strategy_record(
            strategy="uncapped_counterfactual",
            status="selected_diagnostic_only",
            time_value=counter_time,
            t_ana=t_ana,
            signed_prediction=counter_signed,
            guarded_error=abs(counter_signed),
            rotations=rotations,
            protocol=protocol,
            selection_source="original_three_point_model_fixed_candidate_grid",
            operational=False,
            extension_selected=bool(counter_time > 0.5 * float(t_ana)),
        )
    else:
        strategies["uncapped_counterfactual"] = {
            **current,
            "strategy": "uncapped_counterfactual",
            "status": "no_feasible_counterfactual_return_current",
            "selection_source": "current_fallback",
            "operational": False,
        }

    if not fallback:
        for strategy in ("equal_information_pooled_fit", "multiple_window_rule"):
            strategies[strategy] = {
                **current,
                "strategy": strategy,
                "status": "extension_not_applicable_return_current",
                "selection_source": "current_fallback",
            }
        diagnostic["acquired_extension_relative_times"] = []
        return strategies, diagnostic

    candidate_sequence = [
        float(value) for value in extension["candidate_sequence_relative_to_t_ana"]
    ]
    base_sequence = [
        float(value) for value in extension["base_window_points_relative_to_t_ana"]
    ]
    acquired = list(base_sequence)
    eligible: list[tuple[float, float, float, float]] = []
    stop_reason: str | None = None
    width = int(extension["window_width_points"])
    residual_limit = float(extension["one_step_residual_over_epsilon_maximum"])
    disagreement_limit = float(
        extension["adjacent_window_disagreement_over_epsilon_maximum"]
    )
    reduction_minimum = float(
        extension["minimum_predicted_budget_reduction_relative_to_current_fallback"]
    )
    for relative in candidate_sequence:
        if relative not in observations_by_relative_time:
            break
        measured = float(point(relative)["proxy_hartree"])
        previous_relative = acquired[-width:]
        current_relative = (acquired + [relative])[-width:]
        previous_model = fit_signed_power_model(
            [value * float(t_ana) for value in previous_relative],
            [float(point(value)["proxy_hartree"]) for value in previous_relative],
        )
        current_model = fit_signed_power_model(
            [value * float(t_ana) for value in current_relative],
            [
                measured if value == relative else float(point(value)["proxy_hartree"])
                for value in current_relative
            ],
        )
        candidate_time = relative * float(t_ana)
        previous_prediction = evaluate_model(previous_model, candidate_time)
        current_prediction = evaluate_model(current_model, candidate_time)
        one_step = abs(measured - previous_prediction) / epsilon
        disagreements = [
            abs(
                evaluate_model(previous_model, value * float(t_ana))
                - evaluate_model(current_model, value * float(t_ana))
            )
            / epsilon
            for value in current_relative
        ]
        maximum_disagreement = max(disagreements)
        values_for_sign = (measured, previous_prediction, current_prediction)
        sign_pass = all(abs(value) > sign_floor for value in values_for_sign) and len(
            {int(np.sign(value)) for value in values_for_sign}
        ) == 1
        guarded = max(abs(value) for value in values_for_sign)
        finite = all(math.isfinite(value) for value in (
            measured,
            previous_prediction,
            current_prediction,
            one_step,
            maximum_disagreement,
            guarded,
        ))
        feasibility = guarded < epsilon
        consistency_pass = bool(
            finite
            and one_step <= residual_limit
            and maximum_disagreement <= disagreement_limit
            and sign_pass
            and feasibility
        )
        budget = frozen_budget(
            candidate_time,
            guarded,
            rotations,
            epsilon,
            float(protocol["cost_model"]["beta"]),
            float(protocol["scope"]["budget_multiplier_gamma"]),
        )
        reduction = (
            None
            if budget is None
            else 1.0 - float(budget) / float(current["frozen_pauli_rotation_budget"])
        )
        is_eligible = bool(
            consistency_pass
            and reduction is not None
            and reduction >= reduction_minimum
        )
        diagnostic["extension_evaluations"].append(
            {
                "candidate_relative_to_t_ana": relative,
                "candidate_time_hartree_inverse": candidate_time,
                "previous_window_relative_times": previous_relative,
                "current_window_relative_times": current_relative,
                "measured_proxy_hartree": measured,
                "previous_window_prediction_hartree": previous_prediction,
                "current_window_prediction_hartree": current_prediction,
                "one_step_residual_over_epsilon": one_step,
                "maximum_adjacent_window_disagreement_over_epsilon": maximum_disagreement,
                "sign_pass": sign_pass,
                "guarded_error_hartree": guarded,
                "finite_numeric_pass": finite,
                "feasibility_pass": feasibility,
                "consistency_pass": consistency_pass,
                "predicted_frozen_budget": budget,
                "predicted_budget_reduction_relative_to_current_fallback": reduction,
                "eligible": is_eligible,
            }
        )
        acquired.append(relative)
        if not consistency_pass:
            failures = []
            if not finite:
                failures.append("numeric")
            if one_step > residual_limit:
                failures.append("one_step_residual")
            if maximum_disagreement > disagreement_limit:
                failures.append("adjacent_window_disagreement")
            if not sign_pass:
                failures.append("sign")
            if not feasibility:
                failures.append("feasibility")
            stop_reason = "+".join(failures) or "indeterminate"
            break
        if is_eligible:
            assert budget is not None
            eligible.append((budget, candidate_time, measured, guarded))

    if eligible:
        _, selected_time, selected_measured, selected_guarded = min(eligible)
        strategies["multiple_window_rule"] = _strategy_record(
            strategy="multiple_window_rule",
            status="selected_extension",
            time_value=selected_time,
            t_ana=t_ana,
            signed_prediction=selected_measured,
            guarded_error=selected_guarded,
            rotations=rotations,
            protocol=protocol,
            selection_source="multiple_window_guarded_candidate",
            operational=True,
            extension_selected=True,
        )
    else:
        strategies["multiple_window_rule"] = {
            **current,
            "strategy": "multiple_window_rule",
            "status": "no_eligible_extension_return_current",
            "selection_source": "current_fallback",
        }

    acquired_candidates = [
        value for value in acquired if value in candidate_sequence
    ]
    pooled_relative = sorted(
        set(base_sequence + [robust_relative] + acquired_candidates)
    )
    pooled_by_time = {
        float(point["time_hartree_inverse"]).hex(): (
            float(point["time_hartree_inverse"]),
            float(point["proxy_hartree"]),
        )
        for point in pooled_extra_points
    }
    for relative in pooled_relative:
        absolute = relative * float(t_ana)
        pooled_by_time[absolute.hex()] = (
            absolute,
            float(point(relative)["proxy_hartree"]),
        )
    pooled_training = [
        pooled_by_time[key]
        for key in sorted(pooled_by_time, key=lambda item: pooled_by_time[item][0])
    ]
    pooled_model = fit_signed_power_model(
        [value[0] for value in pooled_training],
        [value[1] for value in pooled_training],
    )
    pooled_candidates: list[tuple[float, float, float]] = []
    for relative in acquired_candidates:
        candidate_time = relative * float(t_ana)
        signed = evaluate_model(pooled_model, candidate_time)
        budget = frozen_budget(
            candidate_time,
            abs(signed),
            rotations,
            epsilon,
            float(protocol["cost_model"]["beta"]),
            float(protocol["scope"]["budget_multiplier_gamma"]),
        )
        if budget is not None:
            pooled_candidates.append((budget, candidate_time, signed))
    if pooled_candidates:
        _, pooled_time, pooled_signed = min(pooled_candidates)
        strategies["equal_information_pooled_fit"] = _strategy_record(
            strategy="equal_information_pooled_fit",
            status="selected_observed_candidate",
            time_value=pooled_time,
            t_ana=t_ana,
            signed_prediction=pooled_signed,
            guarded_error=abs(pooled_signed),
            rotations=rotations,
            protocol=protocol,
            selection_source="pooled_fit_same_acquired_proxy_points",
            operational=True,
            extension_selected=bool(pooled_time > 0.5 * float(t_ana)),
        )
    else:
        strategies["equal_information_pooled_fit"] = {
            **current,
            "strategy": "equal_information_pooled_fit",
            "status": "no_feasible_observed_candidate_return_current",
            "selection_source": "current_fallback",
        }
    diagnostic.update(
        {
            "acquired_extension_relative_times": acquired_candidates,
            "extension_stop_reason": stop_reason,
            "eligible_extension_count": len(eligible),
            "pooled_model": pooled_model,
            "pooled_training_relative_times": pooled_relative,
            "pooled_training_absolute_times": [
                value[0] for value in pooled_training
            ],
            "pooled_training_point_count": len(pooled_training),
        }
    )
    if set(strategies) != guard.STRATEGIES:
        raise ExecutionError("strategy set changed")
    return strategies, diagnostic


def phase_b_cache_key(
    *,
    protocol_sha256: str,
    prediction_sha256: str,
    condition: str,
    hamiltonian_sha256: str,
    formula_sha256_value: str,
    time_value: float,
    backend: str,
    previous_vector_sha256: str | None,
) -> dict[str, Any]:
    return {
        "protocol_sha256": protocol_sha256,
        "prediction_sha256": prediction_sha256,
        "condition": condition,
        "hamiltonian_sha256": hamiltonian_sha256,
        "formula_sha256": formula_sha256_value,
        "absolute_time_hex": float(time_value).hex(),
        "backend": str(backend),
        "dtype": "complex128",
        "branch_rule_version": PHASE_B_BRANCH_RULE_VERSION,
        "previous_vector_sha256": previous_vector_sha256,
    }


def score_phase_b(
    *,
    predictions: Mapping[str, Any],
    direct_points_by_condition: Mapping[str, Sequence[Mapping[str, Any]]],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    """Score frozen strategies using only already-computed direct points."""

    guard.validate_phase_a_predictions(dict(predictions))
    beta = float(protocol["cost_model"]["beta"])
    epsilon = float(protocol["scope"]["target_error_hartree"])
    rows: list[dict[str, Any]] = []
    candidate_oracles: dict[str, float] = {}
    for condition_row in predictions["conditions"]:
        condition = str(condition_row["condition"])
        points = list(direct_points_by_condition[condition])
        candidate_points = [
            point for point in points if any(
                str(role).startswith("candidate_") for role in point["roles"]
            )
        ]
        finite_candidate_costs = [
            float(point["direct_required_cost"])
            for point in candidate_points
            if point.get("direct_required_cost") is not None
        ]
        if not finite_candidate_costs:
            raise ExecutionError(f"{condition}: candidate-grid oracle is infinite")
        oracle = min(finite_candidate_costs)
        candidate_oracles[condition] = oracle
        for strategy_name in sorted(guard.STRATEGIES):
            strategy = condition_row["strategies"][strategy_name]
            selected_time = float(strategy["selected_time_hartree_inverse"])
            matches = [
                point
                for point in points
                if math.isclose(
                    float(point["time_hartree_inverse"]),
                    selected_time,
                    rel_tol=2e-12,
                    abs_tol=1e-14,
                )
            ]
            if len(matches) != 1:
                raise ExecutionError(
                    f"{condition}/{strategy_name}: selected coordinate missing"
                )
            point = matches[0]
            direct_cost = point.get("direct_required_cost")
            frozen = float(strategy["frozen_pauli_rotation_budget"])
            rotations = int(strategy["rotation_count_per_pf_step"])
            qpe_error = beta * rotations / (selected_time * frozen)
            total_error = float(point["direct_error_hartree"]) + qpe_error
            rows.append(
                {
                    "condition": condition,
                    "strategy": strategy_name,
                    "operational": bool(strategy["operational"]),
                    "selected_time_hartree_inverse": selected_time,
                    "selected_relative_to_t_ana": float(
                        strategy["selected_relative_to_t_ana"]
                    ),
                    "extension_selected": bool(strategy["extension_selected"]),
                    "direct_error_hartree": float(point["direct_error_hartree"]),
                    "direct_required_cost": direct_cost,
                    "frozen_pauli_rotation_budget": frozen,
                    "qpe_error_implied_by_frozen_budget_hartree": float(qpe_error),
                    "total_error_hartree": total_error,
                    "accuracy_target_met": bool(total_error <= epsilon),
                    "unsafe_execution": bool(total_error > epsilon),
                    "candidate_grid_oracle_cost": oracle,
                    "selection_regret": (
                        None if direct_cost is None else float(direct_cost) / oracle - 1.0
                    ),
                    "frozen_budget_regret": frozen / oracle - 1.0,
                }
            )

    def strategy_rows(name: str) -> list[dict[str, Any]]:
        return [row for row in rows if row["strategy"] == name]

    current = strategy_rows("current_fallback")
    pooled = strategy_rows("equal_information_pooled_fit")
    new = strategy_rows("multiple_window_rule")
    new_regrets = [float(row["selection_regret"]) for row in new if row["selection_regret"] is not None]
    pooled_regrets = [float(row["selection_regret"]) for row in pooled if row["selection_regret"] is not None]
    if len(new_regrets) != len(new) or len(pooled_regrets) != len(pooled):
        mean_better = max_not_above = per_condition_bound = False
    else:
        mean_better = float(np.mean(new_regrets)) < float(np.mean(pooled_regrets))
        max_not_above = max(new_regrets) <= max(pooled_regrets)
        per_condition_bound = max(
            float(new_row["selection_regret"])
            - float(pooled_row["selection_regret"])
            for new_row, pooled_row in zip(new, pooled, strict=True)
        ) <= float(
            protocol["decision"]["complete_with_benefit_requires_all"]
            ["maximum_per_condition_regret_increase_new_minus_equal_information"]
        )
    budget_ratio = sum(float(row["frozen_pauli_rotation_budget"]) for row in new) / sum(
        float(row["frozen_pauli_rotation_budget"]) for row in current
    )
    benefit = {
        "new_rule_unsafe_execution_count_zero": sum(
            int(row["unsafe_execution"]) for row in new
        ) == 0,
        "new_rule_execution_coverage_4_of_4": sum(
            row["direct_required_cost"] is not None for row in new
        ) == 4,
        "new_rule_extension_selection_count_minimum": sum(
            int(row["extension_selected"]) for row in new
        ) >= int(
            protocol["decision"]["complete_with_benefit_requires_all"]
            ["new_rule_extension_selection_count_minimum"]
        ),
        "aggregate_frozen_budget_ratio_pass": budget_ratio <= float(
            protocol["decision"]["complete_with_benefit_requires_all"]
            ["aggregate_frozen_budget_ratio_new_over_current_fallback_maximum"]
        ),
        "mean_selection_regret_better_than_equal_information": mean_better,
        "maximum_selection_regret_not_above_equal_information": max_not_above,
        "per_condition_regret_increase_bound": per_condition_bound,
        "classical_information_counts_equal": all(
            prediction["information_counts"]["multiple_window_rule"]
            == prediction["information_counts"]["equal_information_pooled_fit"]
            for prediction in predictions["conditions"]
        ),
    }
    strategy_summary = {}
    for strategy_name in sorted(guard.STRATEGIES):
        selected = strategy_rows(strategy_name)
        finite_regrets = [
            float(row["selection_regret"])
            for row in selected
            if row["selection_regret"] is not None
        ]
        strategy_summary[strategy_name] = {
            "condition_count": len(selected),
            "accuracy_target_miss_count": sum(
                int(not row["accuracy_target_met"]) for row in selected
            ),
            "unsafe_execution_count": sum(
                int(row["unsafe_execution"]) for row in selected
            ),
            "execution_coverage_count": sum(
                row["direct_required_cost"] is not None for row in selected
            ),
            "extension_selection_count": sum(
                int(row["extension_selected"]) for row in selected
            ),
            "aggregate_frozen_pauli_rotation_budget": sum(
                float(row["frozen_pauli_rotation_budget"]) for row in selected
            ),
            "mean_selection_regret": (
                None
                if len(finite_regrets) != len(selected)
                else float(np.mean(finite_regrets))
            ),
            "maximum_selection_regret": (
                None
                if len(finite_regrets) != len(selected)
                else max(finite_regrets)
            ),
            "mean_frozen_budget_regret": float(
                np.mean([row["frozen_budget_regret"] for row in selected])
            ),
            "maximum_frozen_budget_regret": max(
                float(row["frozen_budget_regret"]) for row in selected
            ),
        }
    regret_differences = [
        {
            "condition": new_row["condition"],
            "new_minus_equal_information_selection_regret": (
                None
                if new_row["selection_regret"] is None
                or pooled_row["selection_regret"] is None
                else float(new_row["selection_regret"])
                - float(pooled_row["selection_regret"])
            ),
        }
        for new_row, pooled_row in zip(new, pooled, strict=True)
    ]
    return {
        "schema": PHASE_B_RESULT_SCHEMA,
        "rows": rows,
        "strategy_summary": strategy_summary,
        "regret_difference_from_equal_information": regret_differences,
        "candidate_grid_oracle_costs": candidate_oracles,
        "aggregate_frozen_budget_ratio_new_over_current_fallback": budget_ratio,
        "benefit_checks": benefit,
        "benefit": all(benefit.values()),
    }
