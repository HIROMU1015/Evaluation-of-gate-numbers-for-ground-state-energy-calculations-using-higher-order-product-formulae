"""Frozen decision rules for the second-study-v2 HF domain pilot.

This module is intentionally free of molecular-cache and truth loaders.  It
contains only protocol arithmetic, selection, freeze verification, and scoring
classification shared by the two process boundaries.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class HFPilotError(RuntimeError):
    """Raised when a frozen pilot rule or identity is violated."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": float(value.real), "imaginary": float(value.imag)}
    if hasattr(value, "item"):
        return jsonable(value.item())
    if isinstance(value, Mapping):
        return {str(key): jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(child) for child in value]
    return str(value)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(jsonable(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def continuous_budget(
    *, beta: float, rotations: int, time_value: float,
    error_hartree: float, epsilon_hartree: float,
) -> float | None:
    values = (beta, time_value, error_hartree, epsilon_hartree)
    if not all(math.isfinite(float(value)) for value in values):
        return None
    if rotations <= 0 or time_value <= 0.0 or error_hartree < 0.0:
        return None
    if error_hartree >= epsilon_hartree:
        return None
    return float(beta * int(rotations) / (time_value * (epsilon_hartree - error_hartree)))


def target_allowance(
    *, epsilon_hartree: float, beta: float, rotations: int,
    time_value: float, baseline_budget: float, eta: float,
) -> float:
    target = (1.0 - float(eta)) * float(baseline_budget)
    if not 0.0 < eta < 1.0 or target <= 0.0 or time_value <= 0.0:
        raise HFPilotError("invalid target allowance inputs")
    return float(epsilon_hartree - beta * int(rotations) / (time_value * target))


def m1_arm_row(
    *, candidate_id: str, time_value: float, factor_of_t0: float,
    prediction: Mapping[str, Any], allowance_hartree: float,
    beta: float, rotations: int, epsilon_hartree: float,
) -> dict[str, Any]:
    e_use = float(prediction["e_use_hartree"])
    abstained = bool(prediction["abstained"])
    structural = allowance_hartree <= 0.0
    eligible = bool(
        factor_of_t0 > 1.0
        and not structural
        and not abstained
        and e_use <= allowance_hartree
    )
    budget = continuous_budget(
        beta=beta, rotations=rotations, time_value=time_value,
        error_hartree=e_use, epsilon_hartree=epsilon_hartree,
    )
    return {
        "arm": "M1_fixed_D2A_spectral",
        "candidate_id": candidate_id,
        "time_hartree_inverse": float(time_value),
        "factor_of_T0": float(factor_of_t0),
        "structurally_rejected": structural,
        "abstained": abstained,
        "failure_reasons": list(prediction.get("failure_reasons", [])),
        "signed_shift_estimate_hartree": float(
            prediction["signed_shift_estimate_hartree"]
        ),
        "width_hartree": float(prediction["empirical_width_hartree"]),
        "e_use_hartree": e_use,
        "allowance_hartree": float(allowance_hartree),
        "eligible": eligible,
        "continuous_budget": budget,
        "continuous_budget_hex": None if budget is None else float(budget).hex(),
        "budget_model": "continuous_rotation_cost_proxy",
    }


def b1_arm_rows(
    *, candidate_id: str, time_value: float, factor_of_t0: float,
    signed_proxy_hartree: float, allowance_hartree: float,
    gammas: Sequence[float], beta: float, rotations: int,
    epsilon_hartree: float,
) -> list[dict[str, Any]]:
    proxy_error = abs(float(signed_proxy_hartree))
    base = continuous_budget(
        beta=beta, rotations=rotations, time_value=time_value,
        error_hartree=proxy_error, epsilon_hartree=epsilon_hartree,
    )
    rows: list[dict[str, Any]] = []
    for gamma in gammas:
        budget = None if base is None else float(gamma) * base
        rows.append({
            "arm": "B1_local_CISD_proxy",
            "gamma": float(gamma),
            "candidate_id": candidate_id,
            "time_hartree_inverse": float(time_value),
            "factor_of_T0": float(factor_of_t0),
            "structurally_rejected": allowance_hartree <= 0.0,
            "abstained": base is None,
            "signed_shift_estimate_hartree": float(signed_proxy_hartree),
            "proxy_error_hartree": proxy_error,
            "allowance_hartree": float(allowance_hartree),
            "eligible": bool(
                factor_of_t0 > 1.0
                and allowance_hartree > 0.0
                and budget is not None
                and budget <= continuous_budget(
                    beta=beta, rotations=rotations, time_value=time_value,
                    error_hartree=max(0.0, allowance_hartree),
                    epsilon_hartree=epsilon_hartree,
                )
            ),
            "continuous_unmargined_budget": base,
            "continuous_budget": budget,
            "continuous_budget_hex": None if budget is None else float(budget).hex(),
            "budget_model": "continuous_rotation_cost_proxy",
        })
    return rows


def select_condition(
    rows: Iterable[Mapping[str, Any]], *, arm: str, gamma: float | None,
    fallback_candidate_id: str, fallback_time: float, fallback_budget: float,
) -> dict[str, Any]:
    matching = [
        dict(row) for row in rows
        if row.get("arm") == arm
        and (gamma is None or float(row.get("gamma")) == float(gamma))
        and bool(row.get("eligible"))
        and row.get("continuous_budget") is not None
    ]
    if not matching:
        return {
            "arm": arm,
            "gamma": gamma,
            "selected_candidate": fallback_candidate_id,
            "selected_time_hartree_inverse": float(fallback_time),
            "frozen_continuous_budget": float(fallback_budget),
            "frozen_continuous_budget_hex": float(fallback_budget).hex(),
            "fallback": True,
            "fallback_reason": "no_eligible_cap_exterior_candidate",
            "eligible_count": 0,
            "eligible_candidates": [],
        }
    selected = min(
        matching,
        key=lambda row: (
            float(row["continuous_budget"]),
            float(row["time_hartree_inverse"]),
            str(row["candidate_id"]),
        ),
    )
    return {
        "arm": arm,
        "gamma": gamma,
        "selected_candidate": str(selected["candidate_id"]),
        "selected_time_hartree_inverse": float(selected["time_hartree_inverse"]),
        "frozen_continuous_budget": float(selected["continuous_budget"]),
        "frozen_continuous_budget_hex": float(selected["continuous_budget"]).hex(),
        "fallback": False,
        "fallback_reason": None,
        "eligible_count": len(matching),
        "eligible_candidates": [str(row["candidate_id"]) for row in matching],
    }


def direct_budget_safe(
    *, direct_shift_hartree: float, beta: float, rotations: int,
    time_value: float, frozen_budget: float, epsilon_hartree: float,
) -> bool:
    lhs = abs(float(direct_shift_hartree)) + (
        float(beta) * int(rotations) / (float(time_value) * float(frozen_budget))
    )
    return bool(lhs <= float(epsilon_hartree))


def physical_branch_correct(
    *, predicted_shift_hartree: float, direct_shift_hartree: float,
    truth_phase_gap_radians: float, time_value: float,
) -> bool:
    if time_value <= 0.0 or truth_phase_gap_radians <= 0.0:
        return False
    separation_hartree = float(truth_phase_gap_radians) / float(time_value)
    return bool(
        abs(float(predicted_shift_hartree) - float(direct_shift_hartree))
        < 0.5 * separation_hartree
    )


def t0_reproduction_pass(
    *, abstained: bool, branch_correct: bool,
    predicted_shift_hartree: float, width_hartree: float,
    direct_shift_hartree: float,
) -> bool:
    return bool(
        not abstained
        and branch_correct
        and abs(float(predicted_shift_hartree) - float(direct_shift_hartree))
        <= float(width_hartree)
    )


def choose_completion_status(condition_rows: Sequence[Mapping[str, Any]]) -> str:
    if len(condition_rows) != 2:
        raise HFPilotError("completion requires exactly two conditions")
    if any(not bool(row.get("evaluable", False)) for row in condition_rows):
        return "not_evaluable_source_or_truth"
    if any(
        not bool(row.get("T0_reproduction_pass", False))
        or not bool(row.get("selected_branch_valid", False))
        for row in condition_rows
    ):
        return "reference_or_branch_failure"
    if any(bool(row.get("unsafe_selected_intervention", False)) for row in condition_rows):
        return "unsafe_frozen_budget"
    if any(bool(row.get("cheap_proxy_matches_or_dominates", False)) for row in condition_rows):
        return "cheap_proxy_sufficient"
    strong = sum(bool(row.get("spectral_strong_signal", False)) for row in condition_rows)
    if strong == 2:
        return "robust_signal"
    if strong == 1:
        return "limited_signal"
    if any(bool(row.get("fixed_width_blocked", False)) for row in condition_rows):
        return "fixed_width_no_benefit"
    return "no_benefit_on_frozen_grid"


def verify_prediction_files(
    root: Path, expected_commit: str | None = None,
) -> tuple[dict[str, Any], str]:
    prediction = root / "prediction.json"
    marker = root / "PREDICTION_FROZEN.json"
    checksum = root / "prediction.sha256"
    if not prediction.is_file() or not marker.is_file() or not checksum.is_file():
        raise HFPilotError("prediction freeze artifact is incomplete")
    digest = sha256_file(prediction)
    checksum_digest = checksum.read_text(encoding="utf-8").split()[0]
    marker_data = load_json(marker)
    if digest != checksum_digest or marker_data.get("prediction_sha256") != digest:
        raise HFPilotError("prediction hash mismatch")
    payload = load_json(prediction)
    if payload.get("truth_open_count") != 0:
        raise HFPilotError("prediction is not truth-free")
    if expected_commit is not None and marker_data.get("prediction_commit") not in (
        None, expected_commit
    ):
        raise HFPilotError("prediction commit mismatch")
    return payload, digest
