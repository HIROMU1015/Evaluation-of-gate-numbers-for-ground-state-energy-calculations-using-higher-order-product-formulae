"""Compact grouped-commutator actions for symmetric S2 compositions.

The base-S2 recurrences implement Eqs. (19)--(20) of Maxwell et al.,
arXiv:2606.30738v1.  Leaves are linear combinations of the repository's
Hamiltonian groups and commutators are evaluated on a state without building
the resulting error-operator matrix.

For a palindromic composition of S2 blocks, the fifth-order logarithm has the
universal form

    c5 * Y5 + c13 * [Y1, [Y1, Y3]].

The two scalar coefficients are extracted from a small non-commutative formal
series, so this adapter also covers the stored optimized compositions that are
not members of the standard Suzuki recursion.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import math
import time
from typing import Any, TypeAlias

import numpy as np


Leaf: TypeAlias = tuple[str, tuple[float, ...]]
Commutator: TypeAlias = tuple[str, "Expression", "Expression"]
Expression: TypeAlias = Leaf | Commutator
GroupedTerm: TypeAlias = tuple[complex, Expression, str]
WordPolynomial: TypeAlias = dict[tuple[str, ...], float]
WordSeries: TypeAlias = list[WordPolynomial]


def _leaf(coefficients: Sequence[float]) -> Leaf:
    values = tuple(0.0 if abs(float(value)) < 1e-16 else float(value) for value in coefficients)
    return ("leaf", values)


def _commutator(left: Expression, right: Expression) -> Commutator:
    return ("comm", left, right)


def _add_leaf(left: Leaf, right: Leaf, right_scale: float = 1.0) -> Leaf:
    return _leaf(
        [
            first + float(right_scale) * second
            for first, second in zip(left[1], right[1], strict=True)
        ]
    )


def _scale_leaf(leaf: Leaf, scale: float) -> Leaf:
    return _leaf([float(scale) * value for value in leaf[1]])


def _multiply_word_polynomials(
    left: WordPolynomial, right: WordPolynomial
) -> WordPolynomial:
    result: defaultdict[tuple[str, ...], float] = defaultdict(float)
    for left_word, left_value in left.items():
        for right_word, right_value in right.items():
            result[left_word + right_word] += float(left_value) * float(right_value)
    return {
        word: value for word, value in result.items() if abs(float(value)) > 1e-15
    }


def _multiply_word_series(
    left: WordSeries, right: WordSeries, maximum_degree: int
) -> WordSeries:
    result: list[defaultdict[tuple[str, ...], float]] = [
        defaultdict(float) for _ in range(maximum_degree + 1)
    ]
    for degree in range(maximum_degree + 1):
        for left_degree in range(degree + 1):
            right_degree = degree - left_degree
            for word, value in _multiply_word_polynomials(
                left[left_degree], right[right_degree]
            ).items():
                result[degree][word] += value
    return [
        {word: value for word, value in terms.items() if abs(value) > 1e-15}
        for terms in result
    ]


def _exponential_word_series(generator: WordSeries, maximum_degree: int) -> WordSeries:
    identity: WordPolynomial = {(): 1.0}
    result: WordSeries = [dict() for _ in range(maximum_degree + 1)]
    result[0] = dict(identity)
    power: WordSeries = [dict() for _ in range(maximum_degree + 1)]
    power[0] = dict(identity)
    factorial = 1
    for exponent in range(1, maximum_degree + 1):
        power = _multiply_word_series(power, generator, maximum_degree)
        factorial *= exponent
        for degree in range(1, maximum_degree + 1):
            for word, value in power[degree].items():
                result[degree][word] = result[degree].get(word, 0.0) + value / factorial
    return result


def composition_log5_coefficients(s2_sequence: Sequence[float]) -> dict[str, float]:
    """Return the universal fifth-order coefficients for an S2 composition."""

    weights = tuple(float(value) for value in s2_sequence)
    if not weights:
        raise ValueError("s2_sequence must not be empty")
    maximum_degree = 5
    identity: WordPolynomial = {(): 1.0}
    product: WordSeries = [dict() for _ in range(maximum_degree + 1)]
    product[0] = dict(identity)
    for weight in weights:
        generator: WordSeries = [dict() for _ in range(maximum_degree + 1)]
        generator[1] = {("X",): weight}
        generator[3] = {("A",): weight**3}
        generator[5] = {("B",): weight**5}
        exponential = _exponential_word_series(generator, maximum_degree)
        product = _multiply_word_series(exponential, product, maximum_degree)

    x_series = [{**terms} for terms in product]
    x_series[0][()] = x_series[0].get((), 0.0) - 1.0
    logarithm: WordSeries = [dict() for _ in range(maximum_degree + 1)]
    power = [{**terms} for terms in x_series]
    for exponent in range(1, maximum_degree + 1):
        scale = (1.0 if exponent % 2 else -1.0) / exponent
        for degree in range(1, maximum_degree + 1):
            for word, value in power[degree].items():
                logarithm[degree][word] = (
                    logarithm[degree].get(word, 0.0) + scale * value
                )
        if exponent != maximum_degree:
            power = _multiply_word_series(power, x_series, maximum_degree)

    fifth = logarithm[5]
    c5 = float(fifth.get(("B",), 0.0))
    commutator_words = {
        ("X", "X", "A"): 1.0,
        ("X", "A", "X"): -2.0,
        ("A", "X", "X"): 1.0,
    }
    c13 = float(
        sum(
            coefficient * fifth.get(word, 0.0)
            for word, coefficient in commutator_words.items()
        )
        / sum(value * value for value in commutator_words.values())
    )
    modeled = {("B",): c5}
    for word, coefficient in commutator_words.items():
        modeled[word] = modeled.get(word, 0.0) + c13 * coefficient
    residual_words = set(fifth) | set(modeled)
    residual_l1 = float(
        sum(abs(fifth.get(word, 0.0) - modeled.get(word, 0.0)) for word in residual_words)
    )
    third_order_l1 = float(sum(abs(value) for value in logarithm[3].values()))
    first_order_x = float(logarithm[1].get(("X",), 0.0))
    return {
        "c5": c5,
        "c13": c13,
        "first_order_x": first_order_x,
        "third_order_l1": third_order_l1,
        "fifth_order_model_residual_l1": residual_l1,
        "fifth_order_word_count": int(len(fifth)),
    }


def compact_s2_base_terms(
    num_fragments: int,
) -> tuple[list[GroupedTerm], list[GroupedTerm], Leaf]:
    """Construct grouped Y3/Y5 terms for one symmetric S2 block.

    Repository groups are traversed from the central S2 fragment to the outer
    fragment so that the ordering matches the symmetric BCH recurrence.
    """

    count = int(num_fragments)
    if count < 1:
        raise ValueError("num_fragments must be positive")
    units = []
    for index in range(count):
        coefficients = [0.0] * count
        coefficients[index] = 1.0
        units.append(_leaf(coefficients))

    partial_sum = units[-1]
    y3_terms: list[GroupedTerm] = []
    y5_terms: list[GroupedTerm] = []
    for fragment_index in reversed(range(count - 1)):
        fragment = units[fragment_index]
        old_y3 = list(y3_terms)
        old_sum = partial_sum

        for coefficient, expression, _ in old_y3:
            y5_terms.extend(
                [
                    (
                        -coefficient / 24.0,
                        _commutator(_commutator(expression, fragment), fragment),
                        "y5_from_y3_ff",
                    ),
                    (
                        -coefficient / 12.0,
                        _commutator(_commutator(expression, fragment), old_sum),
                        "y5_from_y3_fs",
                    ),
                    (
                        -coefficient / 12.0,
                        _commutator(_commutator(old_sum, fragment), expression),
                        "y5_from_sf_y3",
                    ),
                ]
            )

        sf = _commutator(old_sum, fragment)
        y5_terms.extend(
            [
                (
                    1.0 / 180.0,
                    _commutator(
                        _commutator(
                            _commutator(sf, _add_leaf(_scale_leaf(old_sum, 0.25), fragment)),
                            old_sum,
                        ),
                        old_sum,
                    ),
                    "y5_quintic_sss",
                ),
                (
                    7.0 / 1440.0,
                    _commutator(
                        _commutator(_commutator(sf, fragment), fragment),
                        _add_leaf(old_sum, _scale_leaf(fragment, 0.25)),
                    ),
                    "y5_quintic_fff",
                ),
                (
                    -1.0 / 120.0,
                    _commutator(
                        _commutator(
                            sf,
                            _add_leaf(
                                _scale_leaf(old_sum, 1.0 / 3.0),
                                fragment,
                                right_scale=-0.25,
                            ),
                        ),
                        sf,
                    ),
                    "y5_quintic_cross",
                ),
            ]
        )
        y3_terms.extend(
            [
                (
                    -1.0 / 12.0,
                    _commutator(sf, old_sum),
                    "y3_partial_sum",
                ),
                (
                    -1.0 / 24.0,
                    _commutator(sf, fragment),
                    "y3_fragment",
                ),
            ]
        )
        partial_sum = _add_leaf(old_sum, fragment)
    return y3_terms, y5_terms, partial_sum


def compact_composed_d4_terms(
    num_fragments: int, s2_sequence: Sequence[float]
) -> tuple[list[GroupedTerm], dict[str, Any]]:
    """Return grouped terms for D4 of an arbitrary fourth-order S2 composition."""

    y3_terms, y5_terms, y1 = compact_s2_base_terms(num_fragments)
    coefficients = composition_log5_coefficients(s2_sequence)
    terms: list[GroupedTerm] = []
    for coefficient, expression, kind in y5_terms:
        terms.append(
            (
                complex(coefficient * coefficients["c5"] / 1j),
                expression,
                f"base_y5:{kind}",
            )
        )
    for coefficient, expression, kind in y3_terms:
        terms.append(
            (
                complex(coefficient * coefficients["c13"] / 1j),
                _commutator(y1, _commutator(y1, expression)),
                f"composition_mixing:{kind}",
            )
        )
    diagnostics = {
        **coefficients,
        "base_y3_grouped_term_count": len(y3_terms),
        "base_y5_grouped_term_count": len(y5_terms),
        "composed_d4_grouped_term_count": len(terms),
        "expected_base_y3_grouped_term_count": 2 * (int(num_fragments) - 1),
        "expected_base_y5_grouped_term_count": 3 * (int(num_fragments) - 1) ** 2,
    }
    return terms, diagnostics


def expression_leaves(expression: Expression) -> set[Leaf]:
    if expression[0] == "leaf":
        return {expression}
    return expression_leaves(expression[1]) | expression_leaves(expression[2])


def expression_importance(
    expression: Expression, fragment_weights: Sequence[float]
) -> float:
    """Norm-product heuristic corresponding to Eq. (21) of Maxwell et al."""

    if expression[0] == "leaf":
        return float(
            sum(
                abs(coefficient) * float(weight)
                for coefficient, weight in zip(
                    expression[1], fragment_weights, strict=True
                )
            )
        )
    return 2.0 * expression_importance(
        expression[1], fragment_weights
    ) * expression_importance(expression[2], fragment_weights)


@dataclass
class ActionCounter:
    linear_combination_actions: int = 0
    equivalent_fragment_actions: int = 0


def _apply_expression(
    expression: Expression,
    vector: np.ndarray,
    leaf_matrices: dict[Leaf, np.ndarray],
    counter: ActionCounter,
) -> np.ndarray:
    if expression[0] == "leaf":
        counter.linear_combination_actions += 1
        counter.equivalent_fragment_actions += sum(
            abs(coefficient) > 1e-16 for coefficient in expression[1]
        )
        return leaf_matrices[expression] @ vector
    left, right = expression[1], expression[2]
    right_vector = _apply_expression(right, vector, leaf_matrices, counter)
    left_right = _apply_expression(left, right_vector, leaf_matrices, counter)
    left_vector = _apply_expression(left, vector, leaf_matrices, counter)
    right_left = _apply_expression(right, left_vector, leaf_matrices, counter)
    return left_right - right_left


def evaluate_grouped_terms(
    terms: Sequence[GroupedTerm],
    group_matrices: Sequence[np.ndarray],
    state: np.ndarray,
) -> tuple[list[np.ndarray], list[complex], list[dict[str, int]], dict[str, Any]]:
    """Evaluate every grouped D4 component on one normalized state."""

    if not terms or not group_matrices:
        raise ValueError("terms and group_matrices must not be empty")
    vector = np.asarray(state, dtype=np.complex128).reshape(-1)
    vector = vector / np.linalg.norm(vector)
    matrices = [np.asarray(matrix, dtype=np.complex128) for matrix in group_matrices]
    dimension = int(vector.size)
    if any(matrix.shape != (dimension, dimension) for matrix in matrices):
        raise ValueError("group matrix and state dimensions differ")

    leaves: set[Leaf] = set()
    for _, expression, _ in terms:
        leaves.update(expression_leaves(expression))
    construction_started = time.perf_counter()
    leaf_matrices: dict[Leaf, np.ndarray] = {}
    addition_count = 0
    for leaf in leaves:
        matrix = np.zeros_like(matrices[0])
        nonzero_count = 0
        for coefficient, group in zip(leaf[1], matrices, strict=True):
            if abs(coefficient) > 1e-16:
                matrix += (1j * coefficient) * group
                nonzero_count += 1
        addition_count += max(0, nonzero_count - 1)
        leaf_matrices[leaf] = matrix
    leaf_construction_seconds = time.perf_counter() - construction_started

    actions: list[np.ndarray] = []
    expectations: list[complex] = []
    term_counts: list[dict[str, int]] = []
    evaluation_started = time.perf_counter()
    for coefficient, expression, _ in terms:
        counter = ActionCounter()
        action = coefficient * _apply_expression(
            expression, vector, leaf_matrices, counter
        )
        actions.append(action)
        expectations.append(complex(np.vdot(vector, action)))
        term_counts.append(
            {
                "linear_combination_actions": counter.linear_combination_actions,
                "equivalent_fragment_actions": counter.equivalent_fragment_actions,
            }
        )
    evaluation_seconds = time.perf_counter() - evaluation_started
    diagnostics = {
        "grouped_term_count": len(terms),
        "expectation_evaluation_count": len(terms),
        "unique_partial_sum_operator_count": len(leaves),
        "partial_sum_operator_addition_count": int(addition_count),
        "partial_sum_operator_bytes": int(sum(matrix.nbytes for matrix in leaf_matrices.values())),
        "component_action_vector_bytes": int(len(actions) * vector.nbytes),
        "linear_combination_action_count": int(
            sum(row["linear_combination_actions"] for row in term_counts)
        ),
        "equivalent_fragment_action_count": int(
            sum(row["equivalent_fragment_actions"] for row in term_counts)
        ),
        "partial_sum_construction_seconds": float(leaf_construction_seconds),
        "component_evaluation_seconds": float(evaluation_seconds),
    }
    return actions, expectations, term_counts, diagnostics


def rank_terms_by_norm_bound(
    terms: Sequence[GroupedTerm], group_matrices: Sequence[np.ndarray]
) -> tuple[list[int], list[float]]:
    fragment_weights = [
        float(np.linalg.norm(np.asarray(matrix), ord=2)) for matrix in group_matrices
    ]
    scores = [
        float(abs(coefficient) * expression_importance(expression, fragment_weights))
        for coefficient, expression, _ in terms
    ]
    ranking = sorted(range(len(terms)), key=lambda index: (-scores[index], index))
    return ranking, scores


def summed_components(
    actions: Sequence[np.ndarray], indices: Iterable[int]
) -> np.ndarray:
    if not actions:
        raise ValueError("actions must not be empty")
    result = np.zeros_like(np.asarray(actions[0], dtype=np.complex128))
    for index in indices:
        result += np.asarray(actions[int(index)], dtype=np.complex128)
    return result
