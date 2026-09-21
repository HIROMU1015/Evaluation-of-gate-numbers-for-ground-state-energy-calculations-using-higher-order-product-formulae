"""B02 audit of PF coefficient rounding and complete formal order conditions.

For every non-processed S2 composition used by the unified comparison, this
script compares the exact noncommutative word series with exp(t(X+Y)).  The
word-basis check is deliberately stronger than checking only odd power sums.
"""

from __future__ import annotations

import argparse
import ast
import csv
from datetime import datetime
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import subprocess
from typing import Any, Sequence

import mpmath as mp
import numpy as np

from compare_existing_pf_low_order_models_local import (
    CURRENT_M3_WEIGHTS,
    TWO_TERM_CENTER_WEIGHTS,
    YOSHIDA6_M3_WEIGHTS,
)
from search_pf_cost_predictability_m2_m3 import projected_reference_candidate
from trotterlib.product_formula import (
    actual_circuit_optimized_4th_m5_list,
    morales_2025_y8m10b_list,
    new_4th_m2_list,
    yoshida_4th_list,
    yoshida_8th_list,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/prevalidation_b02_coefficient_order_conditions_20260921_retry2"
PRODUCT_FORMULA_SOURCE = ROOT / "src/trotterlib/product_formula.py"
COMPARISON_SOURCE = ROOT / "review_response/compare_existing_pf_low_order_models_local.py"
JOINT_SOURCE = ROOT / "artifacts/m3_joint_full_frozen_refinement_20260913/refinement_results.json"
FORMAL_DECIMAL_DIGITS = 80
HARD_RESIDUAL_TOLERANCE_TEXT = "1e-12"
NONZERO_RESIDUAL_FLOOR = mp.mpf("1e-70")
ROUNDING_DIGITS = (6, 8, 10, 12, 14, 16)
MOMENT_ONLY_CONTROL_WEIGHTS = (
    1.8393538271753733,
    0.4366685773222603,
    -1.8770339063148536,
    1.3793212734856748,
    1.846017927337793,
    -1.6624060206577964,
    0.4569916054669742,
    -0.999236370227739,
)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, mp.mpf):
        return mp.nstr(value, FORMAL_DECIMAL_DIGITS)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _git_state() -> dict[str, Any]:
    def run(*command: str) -> str:
        return subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, check=False
        ).stdout.strip()

    status = run("git", "status", "--porcelain").splitlines()
    return {
        "commit": run("git", "rev-parse", "HEAD") or None,
        "branch": run("git", "branch", "--show-current") or None,
        "dirty": bool(status),
        "status": status,
    }


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _literal_list_in_function(
    path: Path, function_name: str, variable_name: str
) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Assign):
                continue
            if not any(
                isinstance(target, ast.Name) and target.id == variable_name
                for target in child.targets
            ):
                continue
            if not isinstance(child.value, (ast.List, ast.Tuple)):
                raise TypeError(f"{function_name}:{variable_name} is not a literal list")
            return [
                str(ast.get_source_segment(source, element))
                for element in child.value.elts
            ]
    raise KeyError(f"literal list not found: {path}:{function_name}:{variable_name}")


def _literal_module_sequence(path: Path, variable_name: str) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(
            isinstance(target, ast.Name) and target.id == variable_name
            for target in targets
        ):
            continue
        value = node.value
        if not isinstance(value, (ast.List, ast.Tuple)):
            raise TypeError(f"{variable_name} is not a literal sequence")
        return [str(ast.get_source_segment(source, element)) for element in value.elts]
    raise KeyError(f"module literal not found: {path}:{variable_name}")


def _significant_digits(text: str) -> int:
    mantissa = text.strip().lower().lstrip("+-").split("e", 1)[0]
    digits = "".join(character for character in mantissa if character.isdigit())
    digits = digits.lstrip("0")
    return len(digits) if digits else 1


def _mp_from_float(value: float) -> mp.mpf:
    return mp.mpf(float(value))


def _weights_from_tail_literals(literals: Sequence[str]) -> list[mp.mpf]:
    tail = [mp.mpf(value) for value in literals]
    return [mp.mpf(1) - 2 * mp.fsum(tail), *tail]


def _weights_from_all_literals(literals: Sequence[str]) -> list[mp.mpf]:
    return [mp.mpf(value) for value in literals]


def formula_definitions() -> list[dict[str, Any]]:
    product_hash = _source_sha256(PRODUCT_FORMULA_SOURCE)
    comparison_hash = _source_sha256(COMPARISON_SOURCE)
    joint_payload = json.loads(JOINT_SOURCE.read_text(encoding="utf-8"))
    joint = joint_payload["ranked_candidates"][0]
    projected = projected_reference_candidate(2)

    function_sources = {
        "paper_new4_printed_registry": (
            "new_4th_m2_list",
            "w1to2",
        ),
        "m5_best": (
            "actual_circuit_optimized_4th_m5_list",
            "w1to5",
        ),
        "yoshida8": ("yoshida_8th_list", "w_1to7"),
        "morales_y8m10b": ("morales_2025_y8m10b_list", "w1to10"),
    }
    function_literals = {
        name: _literal_list_in_function(PRODUCT_FORMULA_SOURCE, *location)
        for name, location in function_sources.items()
    }
    tuple_literals = {
        name: _literal_module_sequence(COMPARISON_SOURCE, variable)
        for name, variable in (
            ("current_m3", "CURRENT_M3_WEIGHTS"),
            ("two_term_center", "TWO_TERM_CENTER_WEIGHTS"),
            ("yoshida6_m3", "YOSHIDA6_M3_WEIGHTS"),
        )
    }
    with mp.workdps(FORMAL_DECIMAL_DIGITS):
        cube_root_two = mp.root(2, 3)
        yoshida4_reference = [
            -cube_root_two / (2 - cube_root_two),
            1 / (2 - cube_root_two),
        ]

        definitions = [
            {
                "formula_id": "yoshida4",
                "display_name": "Yoshida 4th",
                "formal_order": 4,
                "stored_weights": list(map(float, yoshida_4th_list())),
                "reference_weights": yoshida4_reference,
                "reference_variant": "analytic_high_precision",
                "source_decimal_digits": None,
                "w0_policy": "explicit_analytic",
                "production_role": "unified comparison candidate",
                "provenance": "src/trotterlib/product_formula.py:yoshida_4th_list",
                "source_sha256": product_hash,
            },
            {
                "formula_id": "paper_new4_printed_registry",
                "display_name": "4th(new_2), printed registry",
                "formal_order": 4,
                "stored_weights": list(map(float, new_4th_m2_list())),
                "reference_weights": _weights_from_tail_literals(
                    function_literals["paper_new4_printed_registry"]
                ),
                "reference_variant": "exact_printed_decimal_literals",
                "source_decimal_digits": [
                    _significant_digits(value)
                    for value in function_literals["paper_new4_printed_registry"]
                ],
                "w0_policy": "computed_from_tail",
                "production_role": "public registry value; not used unprojected by unified comparison",
                "provenance": "src/trotterlib/product_formula.py:new_4th_m2_list",
                "source_sha256": product_hash,
            },
            {
                "formula_id": "paper_new4_projected",
                "display_name": "4th(new_2), projected comparison value",
                "formal_order": 4,
                "stored_weights": list(map(float, projected["weights"])),
                "reference_weights": None,
                "reference_variant": None,
                "source_decimal_digits": None,
                "w0_policy": "explicit_projected_float",
                "production_role": "actual unified comparison candidate",
                "provenance": "search_pf_cost_predictability_m2_m3.py:projected_reference_candidate(2)",
                "source_sha256": _source_sha256(
                    ROOT / "review_response/search_pf_cost_predictability_m2_m3.py"
                ),
            },
            {
                "formula_id": "m5_best",
                "display_name": "4th(m5_best)",
                "formal_order": 4,
                "stored_weights": list(
                    map(float, actual_circuit_optimized_4th_m5_list())
                ),
                "reference_weights": _weights_from_tail_literals(
                    function_literals["m5_best"]
                ),
                "reference_variant": "exact_printed_decimal_literals",
                "source_decimal_digits": [
                    _significant_digits(value)
                    for value in function_literals["m5_best"]
                ],
                "w0_policy": "computed_from_tail",
                "production_role": "unified comparison candidate",
                "provenance": "src/trotterlib/product_formula.py:actual_circuit_optimized_4th_m5_list",
                "source_sha256": product_hash,
            },
            {
                "formula_id": "current_m3",
                "display_name": "current_m3",
                "formal_order": 4,
                "stored_weights": list(map(float, CURRENT_M3_WEIGHTS)),
                "reference_weights": _weights_from_all_literals(
                    tuple_literals["current_m3"]
                ),
                "reference_variant": "exact_saved_decimal_literals",
                "source_decimal_digits": [
                    _significant_digits(value) for value in tuple_literals["current_m3"]
                ],
                "w0_policy": "explicit_saved_tuple",
                "production_role": "unified comparison candidate",
                "provenance": "compare_existing_pf_low_order_models_local.py:CURRENT_M3_WEIGHTS",
                "source_sha256": comparison_hash,
            },
            {
                "formula_id": "two_term_center",
                "display_name": "two_term_center",
                "formal_order": 4,
                "stored_weights": list(map(float, TWO_TERM_CENTER_WEIGHTS)),
                "reference_weights": _weights_from_all_literals(
                    tuple_literals["two_term_center"]
                ),
                "reference_variant": "exact_saved_decimal_literals",
                "source_decimal_digits": [
                    _significant_digits(value)
                    for value in tuple_literals["two_term_center"]
                ],
                "w0_policy": "explicit_saved_tuple",
                "production_role": "unified comparison candidate",
                "provenance": "compare_existing_pf_low_order_models_local.py:TWO_TERM_CENTER_WEIGHTS",
                "source_sha256": comparison_hash,
            },
            {
                "formula_id": str(joint["name"]),
                "display_name": str(joint["name"]),
                "formal_order": 4,
                "stored_weights": list(map(float, joint["weights"])),
                "reference_weights": None,
                "reference_variant": None,
                "source_decimal_digits": None,
                "w0_policy": "explicit_json_float",
                "production_role": "unified comparison candidate",
                "provenance": str(JOINT_SOURCE.relative_to(ROOT)),
                "source_sha256": _source_sha256(JOINT_SOURCE),
            },
            {
                "formula_id": "yoshida6_m3",
                "display_name": "Yoshida 6th m=3",
                "formal_order": 6,
                "stored_weights": list(map(float, YOSHIDA6_M3_WEIGHTS)),
                "reference_weights": _weights_from_all_literals(
                    tuple_literals["yoshida6_m3"]
                ),
                "reference_variant": "exact_saved_decimal_literals",
                "source_decimal_digits": [
                    _significant_digits(value)
                    for value in tuple_literals["yoshida6_m3"]
                ],
                "w0_policy": "explicit_saved_tuple",
                "production_role": "unified comparison candidate",
                "provenance": "compare_existing_pf_low_order_models_local.py:YOSHIDA6_M3_WEIGHTS",
                "source_sha256": comparison_hash,
            },
            {
                "formula_id": "yoshida8",
                "display_name": "Yoshida 8th",
                "formal_order": 8,
                "stored_weights": list(map(float, yoshida_8th_list())),
                "reference_weights": _weights_from_tail_literals(
                    function_literals["yoshida8"]
                ),
                "reference_variant": "exact_printed_decimal_literals",
                "source_decimal_digits": [
                    _significant_digits(value) for value in function_literals["yoshida8"]
                ],
                "w0_policy": "computed_from_tail",
                "production_role": "unified comparison candidate",
                "provenance": "src/trotterlib/product_formula.py:yoshida_8th_list",
                "source_sha256": product_hash,
            },
            {
                "formula_id": "morales_y8m10b",
                "display_name": "Morales Y8m10b",
                "formal_order": 8,
                "stored_weights": list(map(float, morales_2025_y8m10b_list())),
                "reference_weights": _weights_from_tail_literals(
                    function_literals["morales_y8m10b"]
                ),
                "reference_variant": "published_decimal_literals_high_precision",
                "source_decimal_digits": [
                    _significant_digits(value)
                    for value in function_literals["morales_y8m10b"]
                ],
                "w0_policy": "computed_from_tail",
                "production_role": "unified comparison candidate",
                "provenance": "src/trotterlib/product_formula.py:morales_2025_y8m10b_list",
                "source_sha256": product_hash,
            },
        ]
    return definitions


def _symmetric_sequence(weights: Sequence[mp.mpf]) -> list[mp.mpf]:
    values = list(weights)
    return list(reversed(values[1:])) + [values[0]] + values[1:]


def _s2_factors(weights: Sequence[mp.mpf]) -> list[tuple[int, mp.mpf]]:
    factors: list[tuple[int, mp.mpf]] = []
    for coefficient in _symmetric_sequence(weights):
        for bit, value in (
            (0, coefficient / 2),
            (1, coefficient),
            (0, coefficient / 2),
        ):
            if factors and factors[-1][0] == bit:
                factors[-1] = (bit, factors[-1][1] + value)
            else:
                factors.append((bit, value))
    return factors


def word_series_residuals(
    weights: Sequence[mp.mpf], maximum_degree: int
) -> dict[int, list[tuple[str, mp.mpf]]]:
    maximum_degree = int(maximum_degree)
    series: dict[tuple[int, ...], mp.mpf] = {(): mp.mpf(1)}
    for bit, coefficient in _s2_factors(weights):
        updated: dict[tuple[int, ...], mp.mpf] = {}
        for word, amplitude in series.items():
            coefficient_power = mp.mpf(1)
            for power in range(maximum_degree - len(word) + 1):
                if power:
                    coefficient_power *= coefficient / power
                destination = word + (bit,) * power
                updated[destination] = (
                    updated.get(destination, mp.mpf(0))
                    + amplitude * coefficient_power
                )
        series = updated
    result: dict[int, list[tuple[str, mp.mpf]]] = {}
    for degree in range(maximum_degree + 1):
        target = mp.mpf(1) / mp.factorial(degree)
        result[degree] = []
        for word in itertools.product((0, 1), repeat=degree):
            label = "".join("X" if bit == 0 else "Y" for bit in word) or "I"
            result[degree].append((label, series.get(word, mp.mpf(0)) - target))
    return result


def _degree_summary(
    residuals: dict[int, list[tuple[str, mp.mpf]]], degree: int
) -> dict[str, Any]:
    values = [value for _, value in residuals[int(degree)]]
    absolute = [abs(value) for value in values]
    maximum_index = int(np.argmax([float(value) for value in absolute]))
    return {
        "degree": int(degree),
        "word_count": len(values),
        "l1": mp.fsum(absolute),
        "l2": mp.sqrt(mp.fsum(value * value for value in absolute)),
        "linf": absolute[maximum_index],
        "maximum_word": residuals[int(degree)][maximum_index][0],
        "maximum_signed_residual": values[maximum_index],
    }


def analyze_variant(
    *,
    formula_id: str,
    display_name: str,
    formal_order: int,
    variant: str,
    weights: Sequence[mp.mpf],
    provenance: str,
    production_role: str,
    source_decimal_digits: Sequence[int] | None,
    w0_policy: str,
    save_words: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    order = int(formal_order)
    weights = [mp.mpf(value) for value in weights]
    residuals = word_series_residuals(weights, order + 1)
    degrees = [_degree_summary(residuals, degree) for degree in range(order + 2)]
    hard = max((row["linf"] for row in degrees[: order + 1]), default=mp.mpf(0))
    leading = degrees[order + 1]["linf"]
    crossover_candidates = []
    for row in degrees[1 : order + 1]:
        if row["linf"] <= NONZERO_RESIDUAL_FLOOR or leading <= 0:
            continue
        exponent = mp.mpf(1) / (order + 1 - int(row["degree"]))
        crossover_candidates.append(
            (mp.power(row["linf"] / leading, exponent), int(row["degree"]))
        )
    crossover, crossover_degree = (
        max(crossover_candidates, key=lambda item: item[0])
        if crossover_candidates
        else (mp.mpf(0), None)
    )
    moments = {
        power: weights[0] ** power
        + 2 * mp.fsum(value**power for value in weights[1:])
        - (1 if power == 1 else 0)
        for power in range(1, order, 2)
    }
    summary = {
        "formula_id": formula_id,
        "display_name": display_name,
        "formal_order": order,
        "variant": variant,
        "production_role": production_role,
        "provenance": provenance,
        "w0_policy": w0_policy,
        "compact_weight_count": len(weights),
        "s2_block_count": 2 * len(weights) - 1,
        "minimum_source_decimal_digits": (
            min(source_decimal_digits) if source_decimal_digits else None
        ),
        "maximum_source_decimal_digits": (
            max(source_decimal_digits) if source_decimal_digits else None
        ),
        "weights": [mp.nstr(value, FORMAL_DECIMAL_DIGITS) for value in weights],
        "normalization_residual": mp.nstr(moments[1], FORMAL_DECIMAL_DIGITS),
        "cubic_moment_residual": mp.nstr(moments.get(3, mp.nan), FORMAL_DECIMAL_DIGITS),
        "fifth_moment_residual": mp.nstr(moments.get(5, mp.nan), FORMAL_DECIMAL_DIGITS),
        "seventh_moment_residual": mp.nstr(moments.get(7, mp.nan), FORMAL_DECIMAL_DIGITS),
        "complete_word_hard_linf": mp.nstr(hard, FORMAL_DECIMAL_DIGITS),
        "complete_word_hard_l2": mp.nstr(
            mp.sqrt(mp.fsum(row["l2"] ** 2 for row in degrees[: order + 1])),
            FORMAL_DECIMAL_DIGITS,
        ),
        "degree_p_plus_1_linf": mp.nstr(leading, FORMAL_DECIMAL_DIGITS),
        "lower_order_crossover_tau": mp.nstr(crossover, FORMAL_DECIMAL_DIGITS),
        "crossover_contamination_degree": crossover_degree,
        "hard_condition_tolerance": HARD_RESIDUAL_TOLERANCE_TEXT,
        "hard_conditions_passed": bool(
            hard <= mp.mpf(HARD_RESIDUAL_TOLERANCE_TEXT)
        ),
    }
    degree_rows = [
        {
            "formula_id": formula_id,
            "formal_order": order,
            "variant": variant,
            "degree": row["degree"],
            "word_count": row["word_count"],
            "l1": mp.nstr(row["l1"], FORMAL_DECIMAL_DIGITS),
            "l2": mp.nstr(row["l2"], FORMAL_DECIMAL_DIGITS),
            "linf": mp.nstr(row["linf"], FORMAL_DECIMAL_DIGITS),
            "maximum_word": row["maximum_word"],
            "maximum_signed_residual": mp.nstr(
                row["maximum_signed_residual"], FORMAL_DECIMAL_DIGITS
            ),
        }
        for row in degrees
    ]
    word_rows = []
    if save_words:
        for degree in range(order + 1):
            for word, residual in residuals[degree]:
                word_rows.append(
                    {
                        "formula_id": formula_id,
                        "formal_order": order,
                        "variant": variant,
                        "degree": degree,
                        "word": word,
                        "signed_residual": mp.nstr(
                            residual, FORMAL_DECIMAL_DIGITS
                        ),
                        "absolute_residual": mp.nstr(
                            abs(residual), FORMAL_DECIMAL_DIGITS
                        ),
                    }
                )
    return summary, degree_rows, word_rows


def _round_significant(value: mp.mpf, digits: int) -> mp.mpf:
    return mp.mpf(mp.nstr(value, int(digits), strip_zeros=False))


def _rounded_weights(
    weights: Sequence[mp.mpf], digits: int, w0_policy: str
) -> list[mp.mpf]:
    rounded = [_round_significant(mp.mpf(value), digits) for value in weights]
    if w0_policy == "computed_from_tail":
        rounded[0] = mp.mpf(1) - 2 * mp.fsum(rounded[1:])
    return rounded


def rounding_sensitivity(
    definitions: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for definition in definitions:
        base = definition["reference_weights"] or [
            _mp_from_float(value) for value in definition["stored_weights"]
        ]
        for digits in ROUNDING_DIGITS:
            weights = _rounded_weights(base, digits, definition["w0_policy"])
            summary, _, _ = analyze_variant(
                formula_id=definition["formula_id"],
                display_name=definition["display_name"],
                formal_order=definition["formal_order"],
                variant=f"rounded_{digits}_significant_digits",
                weights=weights,
                provenance=definition["provenance"],
                production_role=definition["production_role"],
                source_decimal_digits=definition["source_decimal_digits"],
                w0_policy=definition["w0_policy"],
                save_words=False,
            )
            rows.append(
                {
                    "formula_id": definition["formula_id"],
                    "formal_order": definition["formal_order"],
                    "significant_digits": digits,
                    "w0_policy": definition["w0_policy"],
                    "normalization_residual": summary["normalization_residual"],
                    "complete_word_hard_linf": summary[
                        "complete_word_hard_linf"
                    ],
                    "degree_p_plus_1_linf": summary["degree_p_plus_1_linf"],
                    "lower_order_crossover_tau": summary[
                        "lower_order_crossover_tau"
                    ],
                    "crossover_contamination_degree": summary[
                        "crossover_contamination_degree"
                    ],
                    "hard_conditions_passed": summary[
                        "hard_conditions_passed"
                    ],
                }
            )
    return rows


def _mp_matrix_norm(matrix: mp.matrix) -> mp.mpf:
    return mp.sqrt(
        mp.fsum(abs(matrix[row, column]) ** 2 for row in range(matrix.rows) for column in range(matrix.cols))
    )


def _direct_two_term_pf(
    weights: Sequence[mp.mpf], time_value: mp.mpf
) -> mp.matrix:
    x = mp.matrix([[0, 1], [1, 0]])
    y = mp.matrix([[0, -1j], [1j, 0]])
    z = mp.matrix([[1, 0], [0, -1]])
    first = mp.mpf("0.31") * x + mp.mpf("0.11") * z
    second = mp.mpf("0.47") * z - mp.mpf("0.07") * y
    result = mp.eye(2)
    for bit, coefficient in _s2_factors(weights):
        generator = first if bit == 0 else second
        result = mp.expm(1j * time_value * coefficient * generator) * result
    exact = mp.expm(1j * time_value * (first + second))
    return result - exact


def projection_comparison(definitions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    printed = next(
        definition
        for definition in definitions
        if definition["formula_id"] == "paper_new4_printed_registry"
    )
    projected = next(
        definition
        for definition in definitions
        if definition["formula_id"] == "paper_new4_projected"
    )
    printed_weights = [_mp_from_float(value) for value in printed["stored_weights"]]
    projected_weights = [
        _mp_from_float(value) for value in projected["stored_weights"]
    ]
    maximum_delta = max(
        abs(left - right)
        for left, right in zip(printed_weights, projected_weights, strict=True)
    )
    rows = []
    for time_text in ("0.0001", "0.001", "0.02", "0.1", "0.5"):
        time_value = mp.mpf(time_text)
        printed_error = _mp_matrix_norm(
            _direct_two_term_pf(printed_weights, time_value)
        )
        projected_error = _mp_matrix_norm(
            _direct_two_term_pf(projected_weights, time_value)
        )
        rows.append(
            {
                "time": time_text,
                "printed_unitary_error_frobenius": mp.nstr(
                    printed_error, FORMAL_DECIMAL_DIGITS
                ),
                "projected_unitary_error_frobenius": mp.nstr(
                    projected_error, FORMAL_DECIMAL_DIGITS
                ),
                "projected_over_printed_error_ratio": mp.nstr(
                    projected_error / printed_error, FORMAL_DECIMAL_DIGITS
                ),
                "maximum_coefficient_change": mp.nstr(
                    maximum_delta, FORMAL_DECIMAL_DIGITS
                ),
                "note": "deterministic two-noncommuting-term sentinel",
            }
        )
    return rows


def moment_only_control() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    weights = [_mp_from_float(value) for value in MOMENT_ONLY_CONTROL_WEIGHTS]
    summary, degrees, _ = analyze_variant(
        formula_id="moment_only_eighth_order_control",
        display_name="moment-only eighth-order control",
        formal_order=8,
        variant="stored_float_binary",
        weights=weights,
        provenance="deterministic diagnostic vector; not a repository PF candidate",
        production_role="negative control only",
        source_decimal_digits=None,
        w0_policy="explicit_diagnostic_tuple",
        save_words=False,
    )
    rows = []
    for power in (1, 3, 5, 7):
        value = weights[0] ** power + 2 * mp.fsum(
            coefficient**power for coefficient in weights[1:]
        ) - (1 if power == 1 else 0)
        rows.append(
            {
                "condition": f"power_sum_{power}",
                "residual": mp.nstr(value, FORMAL_DECIMAL_DIGITS),
                "odd_moment_tolerance": "1e-12",
                "odd_moment_passed": bool(abs(value) <= mp.mpf("1e-12")),
                "complete_word_hard_linf": summary["complete_word_hard_linf"],
                "complete_word_conditions_passed": summary[
                    "hard_conditions_passed"
                ],
            }
        )
    return rows, degrees


def _make_report(output: Path, result: dict[str, Any]) -> None:
    stored = {
        row["formula_id"]: row
        for row in result["_variant_rows"]
        if row["variant"] == "stored_float_binary"
    }
    paper_raw = stored["paper_new4_printed_registry"]
    paper_projected = stored["paper_new4_projected"]
    yoshida8 = stored["yoshida8"]
    morales8 = stored["morales_y8m10b"]
    production_stored = [
        row
        for row in stored.values()
        if row["production_role"].endswith("unified comparison candidate")
    ]
    projection_last = result["_projection_rows"][-1]
    minimum_digits = result["minimum_passing_significant_digits"]
    lines = [
        "# B02: PF coefficient rounding and formal-order audit",
        "",
        f"Status: {result['status']}",
        "",
        "The audit expands each symmetric S2 composition in the complete "
        "noncommutative X/Y word basis through its declared order. Thus all "
        "operator order conditions are checked; odd power sums are retained "
        "only as diagnostics.",
        "",
        "## Stored coefficients",
        "",
        "| formula | order | complete hard linf | p+1 linf | lower-order crossover tau | pass |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in stored.values():
        lines.append(
            f"| {row['display_name']} | {row['formal_order']} | "
            f"{float(row['complete_word_hard_linf']):.6g} | "
            f"{float(row['degree_p_plus_1_linf']):.6g} | "
            f"{float(row['lower_order_crossover_tau']):.6g} | "
            f"{row['hard_conditions_passed']} |"
        )
    lines += [
        "",
        f"All {sum(row['hard_conditions_passed'] for row in production_stored)}/"
        f"{len(production_stored)} coefficient sets actually used by the unified "
        "comparison pass the declared `1e-12` complete-word threshold.",
        "",
        "The public printed `4th(new_2)` registry value is the exception outside "
        "that production set: its complete hard residual is "
        f"{float(paper_raw['complete_word_hard_linf']):.6g}, whereas the explicitly "
        "projected comparison value is "
        f"{float(paper_projected['complete_word_hard_linf']):.6g}. The maximum "
        "coefficient correction is only "
        f"{float(projection_last['maximum_coefficient_change']):.6g}.",
        "",
        "## Higher-order findings",
        "",
        "The stored Yoshida eighth-order literals have complete hard residual "
        f"{float(yoshida8['complete_word_hard_linf']):.6g}, close to the audit "
        "threshold, while stored Morales Y8m10b has "
        f"{float(morales8['complete_word_hard_linf']):.6g}. The exact published "
        "decimal-literal variants are reported separately and are never silently "
        "substituted for the float coefficients executed by Python.",
        "",
        "In the explicit decimal-rounding sweep, Yoshida eighth order first "
        f"passes at {minimum_digits['yoshida8']} significant digits; Yoshida "
        f"sixth order at {minimum_digits['yoshida6_m3']}, and Morales Y8m10b "
        f"at {minimum_digits['morales_y8m10b']}. The eight-digit printed "
        "`new_2` source never passes without constraint projection.",
        "",
        "The moment-only negative control satisfies normalization and the 3rd, "
        "5th, and 7th power sums within `1e-12`, yet has an order-condition "
        f"residual of {result['moment_only_complete_word_hard_linf']:.6g}. This "
        "directly confirms that odd moments alone do not establish sixth or "
        "eighth order.",
        "",
        "## Interpretation",
        "",
        f"The largest normalized-generator algebraic crossover among production "
        f"candidates is {result['maximum_production_crossover_tau']:.6g}. This "
        "uses formal generators with unit coefficient scale. A molecular "
        "crossover also depends on Hamiltonian-group norms and word contractions, "
        "so it must not be compared directly with the physical short-time grid "
        "minimum `0.02`. The audit finds no failed production coefficient set, "
        "but does not by itself rule coefficient rounding in or out as the cause "
        "of a molecule-specific breakdown.",
        "",
        "Projection changes the deterministic two-term sentinel most strongly at "
        "very small time; at `t=0.5` its projected/printed unitary-error ratio is "
        f"{float(projection_last['projected_over_printed_error_ratio']):.9g}. "
        "The projected PF remains a separately labeled coefficient set.",
        "",
        "## Files",
        "",
        "- `formula_variants.csv`: stored and source/high-precision summaries.",
        "- `degree_residuals.csv`: complete word residual norms by degree.",
        "- `word_condition_residuals.csv`: every checked hard-order word.",
        "- `rounding_sensitivity.csv`: 6--16 significant-digit sweep.",
        "- `projection_comparison.csv`: printed versus projected `new_2`.",
        "- `moment_only_control.csv`: proof that odd moments are insufficient.",
        "- `audit.json` and `manifest.json`: summary and provenance.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    with mp.workdps(FORMAL_DECIMAL_DIGITS):
        definitions = formula_definitions()
        variant_rows: list[dict[str, Any]] = []
        degree_rows: list[dict[str, Any]] = []
        word_rows: list[dict[str, Any]] = []
        for definition in definitions:
            stored, stored_degrees, stored_words = analyze_variant(
                formula_id=definition["formula_id"],
                display_name=definition["display_name"],
                formal_order=definition["formal_order"],
                variant="stored_float_binary",
                weights=[
                    _mp_from_float(value) for value in definition["stored_weights"]
                ],
                provenance=definition["provenance"],
                production_role=definition["production_role"],
                source_decimal_digits=definition["source_decimal_digits"],
                w0_policy=definition["w0_policy"],
                save_words=True,
            )
            variant_rows.append(stored)
            degree_rows.extend(stored_degrees)
            word_rows.extend(stored_words)
            if definition["reference_weights"] is not None:
                reference, reference_degrees, reference_words = analyze_variant(
                    formula_id=definition["formula_id"],
                    display_name=definition["display_name"],
                    formal_order=definition["formal_order"],
                    variant=str(definition["reference_variant"]),
                    weights=definition["reference_weights"],
                    provenance=definition["provenance"],
                    production_role=definition["production_role"],
                    source_decimal_digits=definition["source_decimal_digits"],
                    w0_policy=definition["w0_policy"],
                    save_words=True,
                )
                variant_rows.append(reference)
                degree_rows.extend(reference_degrees)
                word_rows.extend(reference_words)
        rounding_rows = rounding_sensitivity(definitions)
        projection_rows = projection_comparison(definitions)
        moment_rows, moment_degrees = moment_only_control()

        stored_production = [
            row
            for row in variant_rows
            if row["variant"] == "stored_float_binary"
            and row["production_role"].endswith("unified comparison candidate")
        ]
        status = "complete" if all(
            row["hard_conditions_passed"] for row in stored_production
        ) and all(row["odd_moment_passed"] for row in moment_rows) and not any(
            row["complete_word_conditions_passed"] for row in moment_rows
        ) else "failed"
        result = {
            "status": status,
            "scope": "B02 PF coefficient rounding and complete order-condition audit",
            "created_at": datetime.now().astimezone().isoformat(),
            "formal_decimal_digits": FORMAL_DECIMAL_DIGITS,
            "hard_residual_tolerance": HARD_RESIDUAL_TOLERANCE_TEXT,
            "formula_count": len(definitions),
            "variant_count": len(variant_rows),
            "degree_summary_count": len(degree_rows),
            "hard_word_condition_count": len(word_rows),
            "rounding_row_count": len(rounding_rows),
            "minimum_passing_significant_digits": {
                definition["formula_id"]: min(
                    (
                        int(row["significant_digits"])
                        for row in rounding_rows
                        if row["formula_id"] == definition["formula_id"]
                        and row["hard_conditions_passed"]
                    ),
                    default=None,
                )
                for definition in definitions
            },
            "production_stored_count": len(stored_production),
            "production_stored_passed": sum(
                bool(row["hard_conditions_passed"]) for row in stored_production
            ),
            "maximum_production_hard_linf": max(
                float(row["complete_word_hard_linf"])
                for row in stored_production
            ),
            "maximum_production_hard_linf_formula": max(
                stored_production,
                key=lambda row: float(row["complete_word_hard_linf"]),
            )["formula_id"],
            "maximum_production_crossover_tau": max(
                float(row["lower_order_crossover_tau"])
                for row in stored_production
            ),
            "maximum_production_crossover_formula": max(
                stored_production,
                key=lambda row: float(row["lower_order_crossover_tau"]),
            )["formula_id"],
            "crossover_time_basis": (
                "formal noncommutative generators with unit coefficient scale; "
                "not a molecule-specific physical time"
            ),
            "printed_new2_passed": next(
                row["hard_conditions_passed"]
                for row in variant_rows
                if row["formula_id"] == "paper_new4_printed_registry"
                and row["variant"] == "stored_float_binary"
            ),
            "projected_new2_passed": next(
                row["hard_conditions_passed"]
                for row in variant_rows
                if row["formula_id"] == "paper_new4_projected"
                and row["variant"] == "stored_float_binary"
            ),
            "moment_only_odd_moments_passed": all(
                row["odd_moment_passed"] for row in moment_rows
            ),
            "moment_only_complete_word_conditions_passed": all(
                row["complete_word_conditions_passed"] for row in moment_rows
            ),
            "moment_only_complete_word_hard_linf": float(
                moment_rows[0]["complete_word_hard_linf"]
            ),
            "short_time_grid_minimum_for_context": 0.02,
            "rounding_explains_prior_breakdown_on_current_grid": (
                "not_determined_from_normalized_word_series_alone"
            ),
            "source_hashes": {
                str(PRODUCT_FORMULA_SOURCE.relative_to(ROOT)): _source_sha256(
                    PRODUCT_FORMULA_SOURCE
                ),
                str(COMPARISON_SOURCE.relative_to(ROOT)): _source_sha256(
                    COMPARISON_SOURCE
                ),
                str(JOINT_SOURCE.relative_to(ROOT)): _source_sha256(JOINT_SOURCE),
            },
            "environment": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "mpmath": mp.__version__,
            },
            "git": _git_state(),
            "_variant_rows": variant_rows,
            "_degree_rows": degree_rows,
            "_word_rows": word_rows,
            "_rounding_rows": rounding_rows,
            "_projection_rows": projection_rows,
            "_moment_rows": moment_rows,
            "_moment_degree_rows": moment_degrees,
        }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output_dir
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    result = run_analysis()
    _write_csv(output / "formula_variants.csv", result["_variant_rows"])
    _write_csv(output / "degree_residuals.csv", result["_degree_rows"])
    _write_csv(output / "word_condition_residuals.csv", result["_word_rows"])
    _write_csv(output / "rounding_sensitivity.csv", result["_rounding_rows"])
    _write_csv(output / "projection_comparison.csv", result["_projection_rows"])
    _write_csv(output / "moment_only_control.csv", result["_moment_rows"])
    _write_csv(
        output / "moment_only_degree_residuals.csv",
        result["_moment_degree_rows"],
    )
    machine = {key: value for key, value in result.items() if not key.startswith("_")}
    _write_json(output / "audit.json", machine)
    _write_json(
        output / "manifest.json",
        {
            "status": result["status"],
            "scope": result["scope"],
            "created_at": result["created_at"],
            "git": result["git"],
            "source_hashes": result["source_hashes"],
            "complete_noncommutative_word_conditions_checked": True,
            "odd_moments_used_as_sufficient_test": False,
            "coefficient_search_performed": False,
            "projected_coefficients_relabelled_separately": True,
            "existing_artifacts_overwritten": False,
            "gpu_used": False,
        },
    )
    _make_report(output, result)
    print(output)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
