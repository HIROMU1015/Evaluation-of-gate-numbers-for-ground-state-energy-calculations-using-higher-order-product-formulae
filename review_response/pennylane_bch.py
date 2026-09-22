"""Adapter from repository S2 sequences to PennyLane's experimental BCH API."""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Sequence
from functools import lru_cache
from typing import Any

import numpy as np


def _api():
    try:
        from pennylane.labs.trotter_error import ProductFormula, bch_expansion
    except ImportError as error:  # pragma: no cover - depends on optional extras
        raise ImportError(
            "PennyLane BCH support is optional; install requirements-bch.txt"
        ) from error
    return ProductFormula, bch_expansion


def symmetric_pf_product_formula(
    num_fragments: int, s2_sequence: Sequence[float]
) -> Any:
    """Build a recursive PennyLane PF matching the repository multiplication.

    The repository left-applies blocks while iterating.  PennyLane's matrix
    representation multiplies terms from left to right, so the S2 block order
    is reversed here.  Each S2 block itself is palindromic.
    """

    if num_fragments < 1:
        raise ValueError("num_fragments must be positive")
    if not s2_sequence:
        raise ValueError("s2_sequence must not be empty")
    ProductFormula, _ = _api()
    labels = list(range(num_fragments - 1))
    labels += [num_fragments - 1]
    labels += list(reversed(range(num_fragments - 1)))
    coefficients = [0.5] * (num_fragments - 1)
    coefficients += [1.0]
    coefficients += [0.5] * (num_fragments - 1)
    def balanced_product(items: Sequence[Any]) -> Any:
        if len(items) == 1:
            return items[0]
        middle = len(items) // 2
        return balanced_product(items[:middle]) @ balanced_product(items[middle:])

    elementary = [
        ProductFormula([label], [coefficient], label=f"E{label}")
        for label, coefficient in zip(labels, coefficients, strict=True)
    ]
    s2 = balanced_product(elementary)
    s2.label = "S2"
    stages = [s2(float(weight)) for weight in reversed(s2_sequence)]
    formula = balanced_product(stages)
    formula.label = "PF"
    return formula


def bch_expansion_for_symmetric_pf(
    num_fragments: int,
    s2_sequence: Sequence[float],
    maximum_commutator_order: int,
) -> list[dict[tuple[Hashable, ...], complex]]:
    if maximum_commutator_order < 1:
        raise ValueError("maximum_commutator_order must be positive")
    _, bch_expansion = _api()
    product_formula = symmetric_pf_product_formula(num_fragments, s2_sequence)
    return bch_expansion(product_formula, int(maximum_commutator_order))


def _matrix_nested_commutator(
    commutator: tuple[Any, ...], group_matrices: Sequence[np.ndarray]
) -> np.ndarray:
    def evaluate(value: Any) -> np.ndarray:
        if isinstance(value, tuple):
            return _matrix_nested_commutator(value, group_matrices)
        return np.asarray(group_matrices[int(value)], dtype=np.complex128)

    if len(commutator) == 1:
        return evaluate(commutator[0])
    head = evaluate(commutator[0])
    tail = _matrix_nested_commutator(tuple(commutator[1:]), group_matrices)
    return head @ tail - tail @ head


def effective_hamiltonian_matrices_from_bch(
    expansion: Sequence[dict[tuple[Hashable, ...], complex]],
    group_matrices: Sequence[np.ndarray],
) -> list[np.ndarray]:
    """Evaluate BCH commutators as coefficients of ``log(U)/(i*t)``."""

    if not group_matrices:
        raise ValueError("group_matrices must not be empty")
    dimension = int(np.asarray(group_matrices[0]).shape[0])
    coefficients = []
    for commutator_order, terms in enumerate(expansion, start=1):
        matrix = np.zeros((dimension, dimension), dtype=np.complex128)
        for commutator, coefficient in terms.items():
            matrix += complex(coefficient) * _matrix_nested_commutator(
                tuple(commutator), group_matrices
            )
        coefficients.append((1j ** (commutator_order - 1)) * matrix)
    return coefficients


def _multiply_word_expansions(
    left: Counter[tuple[Hashable, ...]],
    right: Counter[tuple[Hashable, ...]],
) -> Counter[tuple[Hashable, ...]]:
    result: Counter[tuple[Hashable, ...]] = Counter()
    for left_word, left_coefficient in left.items():
        for right_word, right_coefficient in right.items():
            result[left_word + right_word] += left_coefficient * right_coefficient
    return result


@lru_cache(maxsize=None)
def _commutator_words(commutator: tuple[Any, ...]) -> Counter[tuple[Hashable, ...]]:
    def evaluate(value: Any) -> Counter[tuple[Hashable, ...]]:
        if isinstance(value, tuple):
            return _commutator_words(value)
        return Counter({(value,): 1})

    if len(commutator) == 1:
        return evaluate(commutator[0])
    head = evaluate(commutator[0])
    tail = _commutator_words(tuple(commutator[1:]))
    result = _multiply_word_expansions(head, tail)
    reverse = _multiply_word_expansions(tail, head)
    for word, coefficient in reverse.items():
        result[word] -= coefficient
    return Counter(
        {word: coefficient for word, coefficient in result.items() if coefficient != 0}
    )


def bch_word_coefficients(
    expansion: Sequence[dict[tuple[Hashable, ...], complex]],
    effective_hamiltonian_order: int,
    *,
    coefficient_tolerance: float = 1e-16,
) -> Counter[tuple[Hashable, ...]]:
    """Expand one BCH coefficient into ordered group-operator words.

    The returned coefficients already include the ``i**order`` convention for
    ``log(U)/(i*t)``.  No group or commutator matrix is constructed.
    """

    order = int(effective_hamiltonian_order)
    if order < 0 or order >= len(expansion):
        raise ValueError("effective-Hamiltonian order is outside the expansion")
    if coefficient_tolerance < 0.0:
        raise ValueError("coefficient tolerance must be non-negative")
    words: Counter[tuple[Hashable, ...]] = Counter()
    for commutator, coefficient in expansion[order].items():
        for word, word_coefficient in _commutator_words(tuple(commutator)).items():
            words[word] += complex(coefficient) * word_coefficient
    phase = 1j**order
    return Counter(
        {
            word: phase * coefficient
            for word, coefficient in words.items()
            if abs(phase * coefficient) > coefficient_tolerance
        }
    )


def effective_hamiltonian_action_from_bch(
    expansion: Sequence[dict[tuple[Hashable, ...], complex]],
    group_matrices: Sequence[np.ndarray],
    state: np.ndarray,
    effective_hamiltonian_order: int,
    *,
    cache_prefixes: bool = False,
    coefficient_tolerance: float = 1e-16,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Evaluate ``D_order |state>`` without constructing ``D_order``.

    ``cache_prefixes=False`` streams every operator word and needs only a
    constant number of logical statevector slots.  ``cache_prefixes=True``
    reuses common application-order prefixes, reducing group actions at the
    cost of retaining those intermediate statevectors.
    """

    if not group_matrices:
        raise ValueError("group_matrices must not be empty")
    vector = np.asarray(state, dtype=np.complex128).reshape(-1)
    if vector.size == 0:
        raise ValueError("state must not be empty")
    vector = vector / np.linalg.norm(vector)
    matrices = [np.asarray(matrix, dtype=np.complex128) for matrix in group_matrices]
    if any(matrix.shape != (vector.size, vector.size) for matrix in matrices):
        raise ValueError("group matrix and state dimensions differ")
    words = bch_word_coefficients(
        expansion,
        effective_hamiltonian_order,
        coefficient_tolerance=coefficient_tolerance,
    )
    action = np.zeros_like(vector)
    naive_group_actions = int(sum(len(word) for word in words))

    if cache_prefixes:
        cache: dict[tuple[Hashable, ...], np.ndarray] = {(): vector}
        for word, coefficient in words.items():
            application_order = tuple(reversed(word))
            for length in range(1, len(application_order) + 1):
                prefix = application_order[:length]
                if prefix not in cache:
                    label = int(prefix[-1])
                    if label < 0 or label >= len(matrices):
                        raise IndexError(f"invalid group label {label}")
                    cache[prefix] = matrices[label] @ cache[prefix[:-1]]
            action += coefficient * cache[application_order]
        group_actions = len(cache) - 1
        logical_peak_vector_count = len(cache) + 1
        cached_prefix_count = len(cache) - 1
    else:
        for word, coefficient in words.items():
            applied = vector
            for raw_label in reversed(word):
                label = int(raw_label)
                if label < 0 or label >= len(matrices):
                    raise IndexError(f"invalid group label {label}")
                applied = matrices[label] @ applied
            action += coefficient * applied
        group_actions = naive_group_actions
        logical_peak_vector_count = 3
        cached_prefix_count = 0

    dimension = int(vector.size)
    complex_bytes = int(np.dtype(np.complex128).itemsize)
    diagnostics = {
        "effective_hamiltonian_order": int(effective_hamiltonian_order),
        "unique_operator_word_count": len(words),
        "maximum_operator_word_length": max(map(len, words), default=0),
        "naive_group_action_count": naive_group_actions,
        "actual_group_action_count": int(group_actions),
        "reused_group_action_count": int(naive_group_actions - group_actions),
        "group_action_reuse_fraction": (
            float((naive_group_actions - group_actions) / naive_group_actions)
            if naive_group_actions
            else 0.0
        ),
        "cached_prefix_count": int(cached_prefix_count),
        "logical_peak_statevector_count": int(logical_peak_vector_count),
        "logical_peak_statevector_bytes": int(
            logical_peak_vector_count * dimension * complex_bytes
        ),
        "dense_coefficient_matrix_bytes_avoided": int(
            dimension * dimension * complex_bytes
        ),
        "input_group_matrix_bytes": int(sum(matrix.nbytes for matrix in matrices)),
        "coefficient_l1_norm": float(sum(abs(value) for value in words.values())),
        "coefficient_tolerance": float(coefficient_tolerance),
        "cache_prefixes": bool(cache_prefixes),
    }
    return action, diagnostics


def effective_hamiltonian_expectations_from_bch(
    expansion: Sequence[dict[tuple[Hashable, ...], complex]],
    group_matrices: Sequence[np.ndarray],
    state: np.ndarray,
) -> tuple[list[complex], list[int]]:
    """Evaluate BCH coefficients through state actions, without commutator matrices."""

    vector = np.asarray(state, dtype=np.complex128).reshape(-1)
    vector /= np.linalg.norm(vector)
    expectations: list[complex] = []
    unique_word_counts: list[int] = []
    for commutator_order, terms in enumerate(expansion, start=1):
        words: Counter[tuple[Hashable, ...]] = Counter()
        for commutator, coefficient in terms.items():
            for word, word_coefficient in _commutator_words(
                tuple(commutator)
            ).items():
                words[word] += complex(coefficient) * word_coefficient
        words = Counter(
            {
                word: coefficient
                for word, coefficient in words.items()
                if abs(coefficient) > 1e-16
            }
        )
        expectation = 0.0j
        for word, coefficient in words.items():
            applied = vector
            for label in reversed(word):
                applied = np.asarray(group_matrices[int(label)]) @ applied
            expectation += coefficient * np.vdot(vector, applied)
        expectations.append((1j ** (commutator_order - 1)) * expectation)
        unique_word_counts.append(len(words))
    return expectations, unique_word_counts
