"""Cost helpers for processed product formulae.

Processed costs are affine rather than purely multiplicative:

    cost(r kernel steps) = r * kernel_cost + processor_pair_count * overhead.

The number of processor pairs depends on how controlled QPE powers are
organized, so callers must provide it explicitly instead of silently charging
the processor once per kernel step.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import DECOMPO_NUM, PF_RZ_LAYER


@dataclass(frozen=True)
class ProcessedCostComponents:
    kernel: int
    processor_pair_overhead: int

    @property
    def full_single_step(self) -> int:
        return self.kernel + self.processor_pair_overhead

    def total(self, kernel_steps: int, *, processor_pair_count: int) -> int:
        if kernel_steps < 1:
            raise ValueError("kernel_steps must be at least 1")
        if processor_pair_count < 1:
            raise ValueError("processor_pair_count must be at least 1")
        return (
            int(kernel_steps) * self.kernel
            + int(processor_pair_count) * self.processor_pair_overhead
        )


def _sequence_cost_from_reference(
    second_order_cost: int,
    reference_cost: int,
    *,
    reference_blocks: int,
    target_blocks: int,
) -> int:
    """Infer a merged S2-sequence cost from a known reference sequence."""
    numerator = reference_blocks * second_order_cost - reference_cost
    denominator = reference_blocks - 1
    boundary_cost, remainder = divmod(numerator, denominator)
    if remainder:
        raise ValueError("Reference costs do not imply an integral boundary cost.")
    return target_blocks * second_order_cost - (target_blocks - 1) * boundary_cost


def morales_yp8m8_hchain_costs(
    h_chain: int | str,
) -> dict[str, ProcessedCostComponents]:
    """Return Pauli-rotation and RZ-depth components for published YP8m8.

    The kernel has 17 S2 blocks, identical in length to the legacy m=8
    Morales formula.  The complete one-step formula has 57 blocks: a
    20-block processor, the 17-block kernel, and a 20-block inverse processor.
    """
    label = str(h_chain)
    if not label.startswith("H"):
        label = f"H{label}"

    output: dict[str, ProcessedCostComponents] = {}
    for metric, table in (
        ("pauli_rotations", DECOMPO_NUM),
        ("rz_layer_depth", PF_RZ_LAYER),
    ):
        row = table[label]
        kernel = row["8th(Morales)"]
        full = _sequence_cost_from_reference(
            row["2nd"],
            kernel,
            reference_blocks=17,
            target_blocks=57,
        )
        output[metric] = ProcessedCostComponents(
            kernel=kernel,
            processor_pair_overhead=full - kernel,
        )
    return output
