from __future__ import annotations

from typing import Iterable, Sequence


def symmetric_s2_sequence(w_list: Sequence[float]) -> list[float]:
    """Convert compact ``[w0, ..., wm]`` weights to the 2m+1 S2 sequence."""
    weights = list(w_list)
    if not weights:
        return []
    return list(reversed(weights[1:])) + [weights[0]] + weights[1:]


def inverse_s2_sequence(sequence: Sequence[float]) -> list[float]:
    """Return the S2-block sequence implementing the inverse operator."""
    return [-weight for weight in reversed(sequence)]


def _iter_s2_steps(num_terms: int, w: float) -> Iterable[tuple[int, float]]:
    """単一 w の S2 対称ステップを生成する。"""
    for i in range(num_terms - 1):
        yield i, w / 2
    yield num_terms - 1, w
    for k in reversed(range(0, num_terms - 1)):
        yield k, w / 2


def _iter_left_steps(
    num_terms: int, w_max: float, w_next: float
) -> Iterable[tuple[int, float]]:
    """複数 w の左端ステップを生成する。"""
    for i in range(num_terms - 1):
        yield i, w_max / 2
    yield num_terms - 1, w_max
    for k in reversed(range(1, num_terms - 1)):
        yield k, w_max / 2
    yield 0, (w_max + w_next) / 2


def _iter_middle_steps(
    num_terms: int, w_first: float, w_second: float
) -> Iterable[tuple[int, float]]:
    """隣接する w の中間ステップを生成する。"""
    for i in range(1, num_terms - 1):
        yield i, w_first / 2
    yield num_terms - 1, w_first
    for k in reversed(range(1, num_terms - 1)):
        yield k, w_first / 2
    yield 0, (w_first + w_second) / 2


def _iter_right_steps(num_terms: int, w_last: float) -> Iterable[tuple[int, float]]:
    """複数 w の右端ステップを生成する。"""
    for i in range(1, num_terms - 1):
        yield i, w_last / 2
    yield num_terms - 1, w_last
    for k in reversed(range(0, num_terms - 1)):
        yield k, w_last / 2


def iter_pf_steps(
    num_terms: int,
    w_list: Sequence[float],
) -> Iterable[tuple[int, float]]:
    """Yield (index, weight) steps for symmetric product-formula decomposition."""
    yield from iter_s2_sequence_steps(num_terms, symmetric_s2_sequence(w_list))


def iter_s2_sequence_steps(
    num_terms: int,
    sequence: Sequence[float],
) -> Iterable[tuple[int, float]]:
    """Expand an arbitrary S2-block sequence, merging adjacent equal terms."""
    if num_terms <= 0 or not sequence:
        return

    pending_index: int | None = None
    pending_weight = 0.0
    for block_weight in sequence:
        for term_index, term_weight in _iter_s2_steps(num_terms, block_weight):
            if term_index == pending_index:
                pending_weight += term_weight
                continue
            if pending_index is not None:
                yield pending_index, pending_weight
            pending_index = term_index
            pending_weight = term_weight
    if pending_index is not None:
        yield pending_index, pending_weight
