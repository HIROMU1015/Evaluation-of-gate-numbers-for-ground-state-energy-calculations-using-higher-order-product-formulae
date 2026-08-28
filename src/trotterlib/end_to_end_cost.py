"""Transparent extension from PF rotations to an expected end-to-end cost.

The manuscript's ``F`` counts Pauli rotations in the product-formula part of
QPE.  This module keeps additional assumptions explicit instead of silently
folding approximate state-preparation or synthesis costs into ``F``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedCostModel:
    """Components of an expected repeated-attempt cost in one common unit.

    ``ground_state_overlap_probability`` is |<psi0|phi>|^2.  The QPE success
    probability is conditional on starting in the target eigenstate.  A
    failed measurement is assumed to require a fresh state preparation, so
    the number of attempts is geometrically distributed.
    """

    one_time_cost: float = 0.0
    state_preparation_per_attempt: float = 0.0
    qpe_fixed_per_attempt: float = 0.0
    cost_per_pf_rotation: float = 1.0
    ground_state_overlap_probability: float = 1.0
    conditional_qpe_success_probability: float = 1.0

    def __post_init__(self) -> None:
        for name in (
            "one_time_cost",
            "state_preparation_per_attempt",
            "qpe_fixed_per_attempt",
            "cost_per_pf_rotation",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        for name in (
            "ground_state_overlap_probability",
            "conditional_qpe_success_probability",
        ):
            value = getattr(self, name)
            if not 0 < value <= 1:
                raise ValueError(f"{name} must lie in (0, 1]")

    @property
    def success_probability_per_attempt(self) -> float:
        return (
            self.ground_state_overlap_probability
            * self.conditional_qpe_success_probability
        )

    @property
    def expected_attempts(self) -> float:
        return 1.0 / self.success_probability_per_attempt

    def per_attempt_cost(self, pf_rotation_count: float) -> float:
        if pf_rotation_count < 0:
            raise ValueError("pf_rotation_count must be non-negative")
        return (
            self.state_preparation_per_attempt
            + self.qpe_fixed_per_attempt
            + self.cost_per_pf_rotation * pf_rotation_count
        )

    def expected_cost(self, pf_rotation_count: float) -> float:
        """Return C_once + C_attempt / (overlap * conditional success)."""
        return self.one_time_cost + (
            self.per_attempt_cost(pf_rotation_count)
            * self.expected_attempts
        )
