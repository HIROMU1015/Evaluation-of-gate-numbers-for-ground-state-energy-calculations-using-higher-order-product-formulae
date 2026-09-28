"""Truth-free small-subspace primitives for the fixed D2-A development pilot.

This module contains no filesystem truth loaders and no full eigensolver for a
molecular Hamiltonian or product-formula matrix.  It operates only through
explicit vector-action callables supplied by the predictor boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Mapping, Sequence

import numpy as np


class D2Error(RuntimeError):
    """Raised when a frozen D2 numerical or access rule is violated."""


VectorAction = Callable[[np.ndarray], np.ndarray]


@dataclass
class ArnoldiChain:
    """One explicit-vector chain and the actions already paid for."""

    basis: np.ndarray
    u_basis: np.ndarray
    h_basis: np.ndarray
    relative_remainders: list[float]
    breakdown: bool
    orthogonality_residual_frobenius: float
    maximum_pf_norm_residual: float

    @property
    def dimension(self) -> int:
        return int(self.basis.shape[1])


def _normalized(vector: np.ndarray) -> np.ndarray:
    value = np.asarray(vector, dtype=np.complex128).reshape(-1)
    norm = float(np.linalg.norm(value))
    if not math.isfinite(norm) or norm == 0.0:
        raise D2Error("cannot normalize a zero or non-finite vector")
    return value / norm


def _checked_action(action: VectorAction, vector: np.ndarray, label: str) -> np.ndarray:
    result = np.asarray(action(vector), dtype=np.complex128).reshape(-1)
    if result.shape != vector.shape or not np.all(np.isfinite(result)):
        raise D2Error(f"{label} returned an invalid vector")
    return result


def build_arnoldi_chain(
    start: np.ndarray,
    apply_u: VectorAction,
    apply_h: VectorAction,
    *,
    maximum_dimension: int,
    reorthogonalization_passes: int,
    relative_breakdown_tolerance: float,
) -> ArnoldiChain:
    """Build one U-Arnoldi chain while storing matching U and H actions."""

    if maximum_dimension < 1:
        raise D2Error("maximum_dimension must be positive")
    if reorthogonalization_passes != 2:
        raise D2Error("D2 requires exactly two modified Gram-Schmidt passes")
    q_values = [_normalized(start)]
    uq_values: list[np.ndarray] = []
    hq_values: list[np.ndarray] = []
    remainders: list[float] = []
    breakdown = False
    maximum_norm_residual = 0.0
    for index in range(maximum_dimension):
        q = q_values[index]
        uq = _checked_action(apply_u, q, "PF action")
        hq = _checked_action(apply_h, q, "Hamiltonian action")
        uq_values.append(uq)
        hq_values.append(hq)
        maximum_norm_residual = max(
            maximum_norm_residual, abs(float(np.linalg.norm(uq)) - 1.0)
        )
        if index + 1 == maximum_dimension:
            break
        remainder = uq.copy()
        for _ in range(reorthogonalization_passes):
            for existing in q_values:
                remainder -= existing * np.vdot(existing, remainder)
        denominator = max(float(np.linalg.norm(uq)), np.finfo(float).tiny)
        relative = float(np.linalg.norm(remainder) / denominator)
        remainders.append(relative)
        if relative <= relative_breakdown_tolerance:
            breakdown = True
            break
        q_values.append(remainder / np.linalg.norm(remainder))
    basis = np.column_stack(q_values)
    u_basis = np.column_stack(uq_values)
    h_basis = np.column_stack(hq_values)
    if not (basis.shape == u_basis.shape == h_basis.shape):
        raise D2Error("action arrays do not match the Arnoldi basis")
    gram = basis.conj().T @ basis
    orthogonality = float(
        np.linalg.norm(gram - np.eye(basis.shape[1]), ord="fro")
    )
    return ArnoldiChain(
        basis=basis,
        u_basis=u_basis,
        h_basis=h_basis,
        relative_remainders=remainders,
        breakdown=breakdown,
        orthogonality_residual_frobenius=orthogonality,
        maximum_pf_norm_residual=maximum_norm_residual,
    )


def unwrap_energy(
    eigenvalue: complex,
    time_value: float,
    reference_energy: float,
    ambiguity_tolerance_hartree: float,
) -> tuple[float, int, bool]:
    """Unwrap one U~=exp(+iHt) phase to the energy nearest a reference."""

    if time_value <= 0.0:
        raise D2Error("time must be positive")
    principal = float(np.angle(eigenvalue) / time_value)
    period = float(2.0 * np.pi / time_value)
    integer = int(round((float(reference_energy) - principal) / period))
    energy = float(principal + integer * period)
    remainder = float(reference_energy - energy)
    ambiguous = (
        abs(abs(remainder) - 0.5 * period) <= ambiguity_tolerance_hartree
    )
    return energy, integer, ambiguous


def _phase_radius_hartree(residual: float, time_value: float) -> float:
    chord = min(2.0, max(0.0, float(residual)))
    return float(2.0 * math.asin(chord / 2.0) / float(time_value))


def analyze_prefix(
    chain: ArnoldiChain,
    dimension: int,
    time_value: float,
    *,
    previous_vector: np.ndarray | None,
    overlap_ambiguity_tolerance: float,
    energy_ambiguity_tolerance_hartree: float,
) -> tuple[dict[str, Any], np.ndarray]:
    """Analyze one fixed prefix without access to an exact state or truth."""

    if dimension < 1 or dimension > chain.dimension:
        raise D2Error("requested prefix is unavailable")
    q = chain.basis[:, :dimension]
    uq = chain.u_basis[:, :dimension]
    hq = chain.h_basis[:, :dimension]
    projected_h = q.conj().T @ hq
    projected_h = 0.5 * (projected_h + projected_h.conj().T)
    h_values, h_vectors = np.linalg.eigh(projected_h)
    h_index = int(np.argmin(h_values))
    h_energy = float(h_values[h_index])
    h_coefficients = _normalized(h_vectors[:, h_index])
    h_vector = _normalized(q @ h_coefficients)
    h_residual = float(np.linalg.norm(hq @ h_coefficients - h_energy * h_vector))

    projected_u = q.conj().T @ uq
    raw_values, raw_vectors = np.linalg.eig(projected_u)
    candidates: list[dict[str, Any]] = []
    physical_vectors: list[np.ndarray] = []
    for index in range(len(raw_values)):
        coefficients = _normalized(raw_vectors[:, index])
        vector = _normalized(q @ coefficients)
        physical_vectors.append(vector)
        raw = complex(raw_values[index])
        phase_value = complex(np.exp(1j * np.angle(raw)))
        u_residual = float(np.linalg.norm(uq @ coefficients - phase_value * vector))
        h_overlap = float(abs(np.vdot(h_vector, vector)) ** 2)
        previous_overlap = (
            None
            if previous_vector is None
            else float(abs(np.vdot(_normalized(previous_vector), vector)) ** 2)
        )
        energy, unwrap_integer, unwrap_ambiguous = unwrap_energy(
            phase_value,
            time_value,
            h_energy,
            energy_ambiguity_tolerance_hartree,
        )
        candidates.append({
            "projected_index": index,
            "projected_eigenvalue_real": float(raw.real),
            "projected_eigenvalue_imaginary": float(raw.imag),
            "projected_eigenvalue_magnitude": float(abs(raw)),
            "unit_circle_eigenvalue_real": float(phase_value.real),
            "unit_circle_eigenvalue_imaginary": float(phase_value.imag),
            "h_reference_overlap_probability": h_overlap,
            "previous_projector_overlap_probability": previous_overlap,
            "unwrapped_energy_hartree": energy,
            "phase_unwrap_integer": unwrap_integer,
            "unwrap_ambiguous": unwrap_ambiguous,
            "full_u_ritz_residual_2_norm": u_residual,
            "absolute_energy_distance_to_h_reference_hartree": abs(energy - h_energy),
        })

    order = sorted(
        range(len(candidates)),
        key=lambda item: (
            -float(candidates[item]["h_reference_overlap_probability"]),
            -float(candidates[item]["previous_projector_overlap_probability"] or 0.0),
            float(candidates[item]["absolute_energy_distance_to_h_reference_hartree"]),
            int(candidates[item]["projected_index"]),
        ),
    )
    selected_position = order[0]
    selected = candidates[selected_position]
    top_score = float(selected["h_reference_overlap_probability"])
    second_score = (
        float(candidates[order[1]]["h_reference_overlap_probability"])
        if len(order) > 1
        else -math.inf
    )
    overlap_ambiguous = (
        len(order) > 1
        and top_score - second_score <= overlap_ambiguity_tolerance
    )
    selected_vector = physical_vectors[selected_position]
    signed_shift = float(selected["unwrapped_energy_hartree"] - h_energy)
    phase_width = _phase_radius_hartree(
        float(selected["full_u_ritz_residual_2_norm"]), time_value
    )
    local_width = float(h_residual + phase_width)
    row = {
        "dimension": dimension,
        "h_reference_energy_hartree": h_energy,
        "h_reference_full_residual_2_norm_hartree": h_residual,
        "h_reference_claim": "empirical_lowest_ritz_candidate",
        "selected_projected_index": int(selected["projected_index"]),
        "selected_h_reference_overlap_probability": top_score,
        "second_h_reference_overlap_probability": (
            None if not math.isfinite(second_score) else second_score
        ),
        "overlap_ambiguous": overlap_ambiguous,
        "unwrap_ambiguous": bool(selected["unwrap_ambiguous"]),
        "selected_previous_projector_overlap_probability": selected[
            "previous_projector_overlap_probability"
        ],
        "selected_projected_eigenvalue_magnitude": selected[
            "projected_eigenvalue_magnitude"
        ],
        "selected_unit_circle_eigenvalue_real": selected[
            "unit_circle_eigenvalue_real"
        ],
        "selected_unit_circle_eigenvalue_imaginary": selected[
            "unit_circle_eigenvalue_imaginary"
        ],
        "selected_full_u_ritz_residual_2_norm": selected[
            "full_u_ritz_residual_2_norm"
        ],
        "selected_unwrapped_energy_hartree": selected["unwrapped_energy_hartree"],
        "selected_phase_unwrap_integer": selected["phase_unwrap_integer"],
        "signed_shift_estimate_hartree": signed_shift,
        "phase_residual_width_hartree": phase_width,
        "local_residual_width_hartree": local_width,
        "branch_status": (
            "branch_indeterminate"
            if overlap_ambiguous or bool(selected["unwrap_ambiguous"])
            else "empirical_branch_candidate"
        ),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    return row, selected_vector


def analyze_coordinate(
    *,
    start: np.ndarray,
    apply_u: VectorAction,
    apply_h: VectorAction,
    time_value: float,
    prefix_dimensions: Sequence[int],
    primary_dimension: int,
    previous_vector: np.ndarray | None,
    numerical_rules: Mapping[str, Any],
    epsilon_hartree: float,
    beta: float,
    rotations_per_step: int,
) -> tuple[dict[str, Any], np.ndarray | None]:
    """Run the frozen truth-free estimator for one coordinate."""

    chain = build_arnoldi_chain(
        start,
        apply_u,
        apply_h,
        maximum_dimension=primary_dimension,
        reorthogonalization_passes=int(
            numerical_rules["modified_gram_schmidt_passes"]
        ),
        relative_breakdown_tolerance=float(
            numerical_rules["relative_breakdown_tolerance"]
        ),
    )
    prefixes: list[dict[str, Any]] = []
    vectors: dict[int, np.ndarray] = {}
    for dimension in prefix_dimensions:
        if int(dimension) > chain.dimension:
            continue
        row, vector = analyze_prefix(
            chain,
            int(dimension),
            time_value,
            previous_vector=previous_vector,
            overlap_ambiguity_tolerance=float(
                numerical_rules["overlap_ambiguity_tolerance"]
            ),
            energy_ambiguity_tolerance_hartree=float(
                numerical_rules["energy_ambiguity_tolerance_hartree"]
            ),
        )
        prefixes.append(row)
        vectors[int(dimension)] = vector
    if not prefixes:
        raise D2Error("no requested Arnoldi prefix is available")
    by_dimension = {int(row["dimension"]): row for row in prefixes}
    available_primary = primary_dimension in by_dimension
    primary_dimension_used = primary_dimension if available_primary else max(by_dimension)
    primary = by_dimension[primary_dimension_used]
    lower = [value for value in by_dimension if value < primary_dimension_used]
    prefix_width = (
        abs(
            float(primary["signed_shift_estimate_hartree"])
            - float(by_dimension[max(lower)]["signed_shift_estimate_hartree"])
        )
        if lower
        else math.inf
    )
    local_width = float(primary["local_residual_width_hartree"])
    empirical_width = max(local_width, prefix_width)
    e_use = float(abs(float(primary["signed_shift_estimate_hartree"])) + empirical_width)
    failures: list[str] = []
    if not available_primary:
        failures.append("primary_dimension_unavailable")
    if primary["branch_status"] == "branch_indeterminate":
        failures.append("branch_indeterminate")
    if chain.orthogonality_residual_frobenius > float(
        numerical_rules["basis_orthogonality_frobenius_residual_maximum"]
    ):
        failures.append("basis_orthogonality")
    if chain.maximum_pf_norm_residual > float(
        numerical_rules["pf_action_norm_residual_maximum"]
    ):
        failures.append("pf_action_norm")
    if float(primary["selected_full_u_ritz_residual_2_norm"]) > float(
        numerical_rules["full_u_ritz_residual_maximum"]
    ):
        failures.append("u_ritz_residual")
    if float(primary["h_reference_full_residual_2_norm_hartree"]) > float(
        numerical_rules["full_h_ritz_residual_hartree_maximum"]
    ):
        failures.append("h_ritz_residual")
    if not math.isfinite(e_use) or e_use >= epsilon_hartree:
        failures.append("no_positive_qpe_allowance")
    budget = (
        None
        if failures
        else float(
            beta
            * int(rotations_per_step)
            / (time_value * (epsilon_hartree - e_use))
        )
    )
    prediction = {
        "available_dimension": chain.dimension,
        "requested_primary_dimension": primary_dimension,
        "primary_dimension_used": primary_dimension_used,
        "breakdown": chain.breakdown,
        "relative_remainders": chain.relative_remainders,
        "basis_orthogonality_frobenius_residual": (
            chain.orthogonality_residual_frobenius
        ),
        "maximum_pf_action_norm_residual": chain.maximum_pf_norm_residual,
        "prefixes": prefixes,
        "signed_shift_estimate_hartree": primary["signed_shift_estimate_hartree"],
        "prefix_width_hartree": prefix_width,
        "local_residual_width_hartree": local_width,
        "empirical_width_hartree": empirical_width,
        "e_use_hartree": e_use,
        "gamma": 1.0,
        "K_current_m3": int(rotations_per_step),
        "frozen_pauli_rotation_budget": budget,
        "claim_class": (
            "indeterminate" if failures else "empirical_estimate"
        ),
        "abstained": bool(failures),
        "failure_reasons": failures,
    }
    selected_vector = vectors.get(primary_dimension_used)
    return prediction, selected_vector
