from __future__ import annotations

import math

from trotterlib.config import DECOMPO_NUM, PF_RZ_LAYER, normalize_pf_label, pf_order
from trotterlib.pf_decomposition import (
    inverse_s2_sequence,
    iter_pf_steps,
    iter_s2_sequence_steps,
)
from trotterlib.product_formula import (
    _get_kernel_s2_sequence,
    _get_processor_s2_sequence,
    _get_s2_sequence,
    _get_w_list,
    morales_2025_y8m10b_list,
    morales_2025_10th_m17_list,
    morales_2025_yp8m8_kernel_list,
    morales_2025_yp8m8_processor_gamma_list,
    morales_8th_list,
)
from trotterlib.processed_cost import morales_yp8m8_hchain_costs


LABEL = "8th(Morales-Y8m10b)"


def test_y8m10b_uses_published_m10_coefficients() -> None:
    weights = morales_2025_y8m10b_list()

    assert len(weights) == 11
    assert weights != morales_8th_list()
    assert weights == _get_w_list(LABEL)
    assert math.isclose(weights[0] + 2 * sum(weights[1:]), 1.0, abs_tol=1e-15)


def test_y8m10b_satisfies_necessary_eighth_order_moments() -> None:
    w0, *tail = morales_2025_y8m10b_list()

    for power in (3, 5, 7):
        residual = w0**power + 2 * sum(value**power for value in tail)
        assert abs(residual) < 2e-15


def test_y8m10b_label_and_symmetric_stage_count() -> None:
    weights = morales_2025_y8m10b_list()
    num_terms = 3

    # Eq. (17) of Morales et al. (QIC 2025): (4m+2)(J-1)+1.
    expected = (4 * 10 + 2) * (num_terms - 1) + 1
    assert len(list(iter_pf_steps(num_terms, weights))) == expected
    assert normalize_pf_label("Y8m10b") == LABEL
    assert pf_order(LABEL) == 8


def test_y8m10b_cost_tables_are_present() -> None:
    assert DECOMPO_NUM["H2"][LABEL] == 304
    assert PF_RZ_LAYER["H2"][LABEL] == 109


def test_published_tenth_order_m17_coefficients_and_costs_are_present() -> None:
    label = "10th(Morales-QIC-m17)"
    weights = morales_2025_10th_m17_list()
    w0, *tail = weights

    assert len(weights) == 18
    assert weights == _get_w_list(label)
    assert math.isclose(w0 + 2 * sum(tail), 1.0, abs_tol=2e-15)
    for power in (3, 5, 7, 9):
        residual = w0**power + 2 * sum(value**power for value in tail)
        assert abs(residual) < 5e-14
    assert normalize_pf_label("Y10m17") == label
    assert pf_order(label) == 10
    assert DECOMPO_NUM["H2"][label] == 500
    assert PF_RZ_LAYER["H2"][label] == 179


def test_new_fourth_order_candidate_cost_tables_are_present() -> None:
    assert DECOMPO_NUM["H2"]["4th(m5_best)"] == 164
    assert DECOMPO_NUM["H2"]["4th(m6)"] == 192
    assert PF_RZ_LAYER["H2"]["4th(m5_best)"] == 59
    assert PF_RZ_LAYER["H2"]["4th(m6)"] == 69


def test_new_fourth_order_candidates_cancel_the_cubic_moment() -> None:
    old_w0, *old_tail = _get_w_list("4th(new_2)")
    old_residual = old_w0**3 + 2 * sum(value**3 for value in old_tail)
    assert abs(old_residual) > 1e-10

    for label in ("4th(m5_best)", "4th(m6)"):
        w0, *tail = _get_w_list(label)
        residual = w0**3 + 2 * sum(value**3 for value in tail)
        assert abs(residual) < 2e-15


def test_yp8m8_published_coefficients_are_recorded_completely() -> None:
    kernel = morales_2025_yp8m8_kernel_list()
    gamma = morales_2025_yp8m8_processor_gamma_list()

    assert len(kernel) == 9
    assert math.isclose(kernel[0] + 2 * sum(kernel[1:]), 1.0, abs_tol=1e-15)
    assert len(gamma) == 10
    assert math.isclose(sum(gamma), 0.0, abs_tol=1e-15)


def test_yp8m8_full_processed_sequence_has_p_k_p_inverse_structure() -> None:
    label = "8th(Morales-YP8m8)"
    kernel = _get_kernel_s2_sequence(label)
    processor = _get_processor_s2_sequence(label)
    complete = _get_s2_sequence(label)

    assert len(kernel) == 17
    assert len(processor) == 20
    assert len(complete) == 57
    assert complete == processor + kernel + inverse_s2_sequence(processor)
    assert pf_order(label) == 8
    assert normalize_pf_label("YP8m8") == label


def test_arbitrary_s2_expansion_preserves_existing_symmetric_expansion() -> None:
    weights = morales_8th_list()
    compact_steps = list(iter_pf_steps(4, weights))
    explicit_steps = list(
        iter_s2_sequence_steps(4, _get_kernel_s2_sequence("8th(Morales)"))
    )

    assert explicit_steps == compact_steps


def test_yp8m8_cost_separates_repeated_kernel_from_processor_overhead() -> None:
    costs = morales_yp8m8_hchain_costs("H2")
    rotations = costs["pauli_rotations"]
    rz_depth = costs["rz_layer_depth"]

    assert rotations.kernel == 248
    assert rotations.processor_pair_overhead == 560
    assert rotations.full_single_step == 808
    assert rotations.total(100, processor_pair_count=1) == 100 * 248 + 560
    assert rz_depth.kernel == 89
    assert rz_depth.processor_pair_overhead == 200
    assert rz_depth.full_single_step == 289
