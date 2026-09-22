"""Minimal fourth-order moment projection for saved PF coefficients.

This module intentionally contains only the scalar fourth-order condition
needed to reconstruct already published symmetric S2 compositions.  It is
not a coefficient-search pipeline.
"""

from __future__ import annotations

from typing import NamedTuple, Sequence

import numpy as np
from scipy.optimize import least_squares


class FourthOrderProjectionResult(NamedTuple):
    """Result of projecting a fixed coefficient tail onto the order condition."""

    w0: float
    w_tail: np.ndarray
    moment_residual: np.ndarray
    scipy_result: object


def fourth_order_moment_residual_float64(
    w_tail: Sequence[float],
) -> np.ndarray:
    """Return ``w0**3 + 2 sum(wi**3)`` for ``w0=1-2 sum(wi)``."""

    tail = np.asarray(w_tail, dtype=float)
    w0 = 1.0 - 2.0 * np.sum(tail)
    return np.asarray([w0**3 + 2.0 * np.sum(tail**3)], dtype=float)


def _fourth_order_moment_jacobian_float64(
    w_tail: Sequence[float],
) -> np.ndarray:
    tail = np.asarray(w_tail, dtype=float)
    w0 = 1.0 - 2.0 * np.sum(tail)
    return np.asarray([6.0 * (tail**2 - w0**2)], dtype=float)


def solve_nonprocessed_4th_moment_coefficients(
    *,
    kernel_m: int,
    initial: Sequence[float],
    method: str = "trf",
    xtol: float = 2.5e-14,
    ftol: float = 2.5e-14,
    gtol: float = 2.5e-14,
    max_nfev: int = 5000,
) -> FourthOrderProjectionResult:
    """Project one fixed tail onto the symmetric fourth-order manifold."""

    tail = np.asarray(initial, dtype=float)
    if tail.ndim != 1 or tail.size != int(kernel_m):
        raise ValueError(
            f"initial must contain exactly {int(kernel_m)} tail coefficients"
        )
    if not np.all(np.isfinite(tail)):
        raise ValueError("initial coefficients must be finite")
    result = least_squares(
        fourth_order_moment_residual_float64,
        tail,
        jac=_fourth_order_moment_jacobian_float64,
        method=method,
        xtol=float(xtol),
        ftol=float(ftol),
        gtol=float(gtol),
        max_nfev=int(max_nfev),
    )
    projected = np.asarray(result.x, dtype=float)
    return FourthOrderProjectionResult(
        w0=float(1.0 - 2.0 * np.sum(projected)),
        w_tail=projected,
        moment_residual=fourth_order_moment_residual_float64(projected),
        scipy_result=result,
    )
