"""Phase-boundary guards for the second-study safe-time-domain protocol.

This module deliberately contains no Hamiltonian, proxy, or direct-truth
calculation.  It validates the oracle-free selector payload, freezes Phase A
predictions, and derives the preregistered Phase B coordinate plan without
opening a truth source.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


PROTOCOL_PATH = Path(__file__).with_name(
    "second_study_safe_time_domain_protocol.json"
)
PROTOCOL_HASH_PATH = PROTOCOL_PATH.with_suffix(PROTOCOL_PATH.suffix + ".sha256")
FREEZE_MARKER = "PHASE_A_FROZEN.json"
PREDICTION_FILE = "predictions.json"
PREDICTION_HASH_FILE = "prediction.sha256"

ALLOWED_PHASE_A_TOP_LEVEL_FIELDS = {
    "schema",
    "condition",
    "protocol_sha256",
    "hamiltonian_sha256",
    "hamiltonian",
    "component_spectra",
    "term_counts",
    "cisd_state",
    "current_m3",
    "target_error_hartree",
    "measurement_costs",
    "runtime_cache_key",
}

FORBIDDEN_SELECTOR_KEY_FRAGMENTS = {
    "direct_pf",
    "direct_shift",
    "direct_truth",
    "exact_gap",
    "exact_ground",
    "ground_energy",
    "ground_overlap",
    "oracle",
    "pass_fail",
    "past_label",
    "phase_b_output",
    "truth_file",
    "truth_path",
}

ORACLE_ACCESS_COUNTERS = {
    "exact_ground_open_count",
    "direct_truth_open_count",
    "truth_path_exposed_count",
    "past_label_access_count",
}

STRATEGIES = {
    "current_fallback",
    "equal_information_pooled_fit",
    "multiple_window_rule",
    "uncapped_counterfactual",
}


class ProtocolBoundaryError(ValueError):
    """Raised when the Phase A/B information boundary is violated."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_protocol_sha256() -> str:
    fields = PROTOCOL_HASH_PATH.read_text(encoding="utf-8").split()
    if len(fields) < 1 or len(fields[0]) != 64:
        raise ProtocolBoundaryError("invalid protocol SHA-256 sidecar")
    return fields[0]


def load_protocol() -> tuple[dict[str, Any], str]:
    expected = expected_protocol_sha256()
    actual = sha256_file(PROTOCOL_PATH)
    if actual != expected:
        raise ProtocolBoundaryError(
            f"protocol SHA-256 mismatch: expected {expected}, obtained {actual}"
        )
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8")), actual


def forbidden_selector_key_paths(value: Any, prefix: str = "") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            lowered = str(key).lower()
            if any(token in lowered for token in FORBIDDEN_SELECTOR_KEY_FRAGMENTS):
                failures.append(path)
            failures.extend(forbidden_selector_key_paths(child, path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            failures.extend(
                forbidden_selector_key_paths(child, f"{prefix}[{index}]")
            )
    return failures


def _condition_names(protocol: dict[str, Any]) -> list[str]:
    return [
        str(item["name"])
        for item in protocol["data_partition"]["independent_evaluation"][
            "conditions"
        ]
    ]


def validate_phase_a_selector_payload(payload: dict[str, Any]) -> None:
    protocol, protocol_sha = load_protocol()
    unexpected = set(payload) - ALLOWED_PHASE_A_TOP_LEVEL_FIELDS
    if unexpected:
        raise ProtocolBoundaryError(
            "unexpected Phase A top-level fields: " + ", ".join(sorted(unexpected))
        )
    missing = {
        "schema",
        "condition",
        "protocol_sha256",
        "hamiltonian_sha256",
        "hamiltonian",
        "component_spectra",
        "term_counts",
        "cisd_state",
        "current_m3",
        "target_error_hartree",
    } - set(payload)
    if missing:
        raise ProtocolBoundaryError(
            "missing Phase A fields: " + ", ".join(sorted(missing))
        )
    if payload["condition"] not in _condition_names(protocol):
        raise ProtocolBoundaryError("condition is not in the frozen evaluation set")
    if payload["protocol_sha256"] != protocol_sha:
        raise ProtocolBoundaryError("selector payload protocol hash mismatch")
    failures = forbidden_selector_key_paths(payload)
    if failures:
        raise ProtocolBoundaryError(
            "forbidden selector fields: " + ", ".join(sorted(failures))
        )


def validate_phase_a_predictions(predictions: dict[str, Any]) -> None:
    protocol, protocol_sha = load_protocol()
    if predictions.get("protocol_sha256") != protocol_sha:
        raise ProtocolBoundaryError("prediction protocol hash mismatch")
    access = predictions.get("oracle_access")
    if not isinstance(access, dict) or set(access) != ORACLE_ACCESS_COUNTERS:
        raise ProtocolBoundaryError("oracle-access counters are missing or changed")
    nonzero = {key: access[key] for key in access if access[key] != 0}
    if nonzero:
        raise ProtocolBoundaryError(f"Phase A oracle access was nonzero: {nonzero}")

    rows = predictions.get("conditions")
    if not isinstance(rows, list):
        raise ProtocolBoundaryError("prediction conditions must be a list")
    expected_names = _condition_names(protocol)
    observed_names = [row.get("condition") for row in rows]
    if observed_names != expected_names:
        raise ProtocolBoundaryError("prediction condition order or identity changed")
    for row in rows:
        t_ana = row.get("proxy_analytic_time_hartree_inverse")
        if not isinstance(t_ana, (int, float)) or not math.isfinite(t_ana):
            raise ProtocolBoundaryError("invalid proxy analytic time")
        if float(t_ana) <= 0.0:
            raise ProtocolBoundaryError("proxy analytic time must be positive")
        strategies = row.get("strategies")
        if not isinstance(strategies, dict) or set(strategies) != STRATEGIES:
            raise ProtocolBoundaryError("frozen strategy set changed")
        current = strategies["current_fallback"]
        selected_time = current.get("selected_time_hartree_inverse")
        if not isinstance(selected_time, (int, float)):
            raise ProtocolBoundaryError("current fallback selected time is missing")
        if not math.isfinite(selected_time) or float(selected_time) <= 0.0:
            raise ProtocolBoundaryError("current fallback selected time is invalid")


def derive_phase_b_coordinate_plan(
    predictions: dict[str, Any],
) -> list[dict[str, Any]]:
    """Derive all Phase B coordinates from frozen Phase A values only."""

    validate_phase_a_predictions(predictions)
    protocol, _ = load_protocol()
    relative_grid = protocol["phase_b"][
        "fixed_candidate_grid_relative_to_t_ana"
    ]
    coordinate_spec = protocol["phase_b"]["truth_coordinate_plan"]
    rtol = float(
        coordinate_spec["absolute_time_deduplication_relative_tolerance"]
    )
    atol = float(
        coordinate_spec["absolute_time_deduplication_absolute_tolerance"]
    )
    result: list[dict[str, Any]] = []
    for row in predictions["conditions"]:
        t_ana = float(row["proxy_analytic_time_hartree_inverse"])
        current_time = float(
            row["strategies"]["current_fallback"][
                "selected_time_hartree_inverse"
            ]
        )
        candidate_times = [float(relative) * t_ana for relative in relative_grid]
        scoring_times = candidate_times + [current_time]
        anchor = 0.5 * min(scoring_times)
        labelled = [("anchor", anchor)] + [
            (f"candidate_{index:02d}", value)
            for index, value in enumerate(candidate_times)
        ]
        labelled.append(("current_fallback", current_time))
        unique: list[dict[str, Any]] = []
        for role, value in sorted(labelled, key=lambda item: item[1]):
            match = next(
                (
                    item
                    for item in unique
                    if math.isclose(
                        float(item["time_hartree_inverse"]),
                        value,
                        rel_tol=rtol,
                        abs_tol=atol,
                    )
                ),
                None,
            )
            if match is None:
                unique.append(
                    {
                        "time_hartree_inverse": value,
                        "roles": [role],
                    }
                )
            else:
                match["roles"].append(role)
        result.append(
            {
                "condition": row["condition"],
                "anchor_time_hartree_inverse": anchor,
                "coordinates": unique,
            }
        )
    maximum = int(
        coordinate_spec["maximum_total_new_direct_truth_coordinates"]
    )
    count = sum(len(row["coordinates"]) for row in result)
    if count > maximum:
        raise ProtocolBoundaryError(
            f"Phase B coordinate plan exceeds frozen maximum: {count}/{maximum}"
        )
    return result


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def freeze_phase_a(output_dir: Path, phase_a_parent_commit: str) -> dict[str, Any]:
    prediction_path = output_dir / PREDICTION_FILE
    if (output_dir / FREEZE_MARKER).exists():
        raise ProtocolBoundaryError("Phase A freeze marker already exists")
    predictions = json.loads(prediction_path.read_text(encoding="utf-8"))
    validate_phase_a_predictions(predictions)
    plan = derive_phase_b_coordinate_plan(predictions)
    protocol, protocol_sha = load_protocol()
    prediction_sha = sha256_file(prediction_path)
    (output_dir / PREDICTION_HASH_FILE).write_text(
        prediction_sha + "  " + PREDICTION_FILE + "\n", encoding="utf-8"
    )
    marker = {
        "schema": protocol["phase_a"]["freeze"]["required_marker_schema"],
        "protocol_sha256": protocol_sha,
        "prediction_sha256": prediction_sha,
        "phase_a_parent_commit": str(phase_a_parent_commit),
        "oracle_access": predictions["oracle_access"],
        "condition_count": len(predictions["conditions"]),
        "phase_b_coordinate_count": sum(
            len(row["coordinates"]) for row in plan
        ),
        "phase_b_coordinate_plan": plan,
    }
    _atomic_write_json(output_dir / FREEZE_MARKER, marker)
    return marker


def verify_phase_a_freeze(output_dir: Path) -> dict[str, Any]:
    marker_path = output_dir / FREEZE_MARKER
    if not marker_path.is_file():
        raise ProtocolBoundaryError("missing Phase A freeze marker")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    protocol, protocol_sha = load_protocol()
    if marker.get("schema") != protocol["phase_a"]["freeze"][
        "required_marker_schema"
    ]:
        raise ProtocolBoundaryError("Phase A freeze schema mismatch")
    if marker.get("protocol_sha256") != protocol_sha:
        raise ProtocolBoundaryError("frozen protocol SHA-256 mismatch")
    prediction_path = output_dir / PREDICTION_FILE
    prediction_sha = sha256_file(prediction_path)
    if marker.get("prediction_sha256") != prediction_sha:
        raise ProtocolBoundaryError("prediction SHA-256 mismatch")
    sidecar = (output_dir / PREDICTION_HASH_FILE).read_text(
        encoding="utf-8"
    ).split()
    if not sidecar or sidecar[0] != prediction_sha:
        raise ProtocolBoundaryError("prediction sidecar mismatch")
    predictions = json.loads(prediction_path.read_text(encoding="utf-8"))
    validate_phase_a_predictions(predictions)
    expected_plan = derive_phase_b_coordinate_plan(predictions)
    if marker.get("phase_b_coordinate_plan") != expected_plan:
        raise ProtocolBoundaryError("Phase B coordinate plan changed")
    return marker
