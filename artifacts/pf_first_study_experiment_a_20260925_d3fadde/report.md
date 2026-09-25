# First-study Experiment A validation

Status: **complete_validation**

This is an implementation validation, not evidence of molecular generality.

| gate | measured | threshold | pass |
|---|---:|---:|:---:|
| source_state_normalization | 1.110223e-16 | 1.000000e-12 | yes |
| source_ground_energy | 2.441549e-15 | 1.000000e-10 | yes |
| source_hermiticity | 0.000000e+00 | 1.000000e-12 | yes |
| source_group_sum | 0.000000e+00 | 1.000000e-12 | yes |
| sequence_normalization | 2.220446e-16 | 1.000000e-12 | yes |
| sequence_third_moment | 9.405671e-15 | 1.000000e-12 | yes |
| sequence_palindrome | 0.000000e+00 | 1.000000e-12 | yes |
| high_precision_two_level | 2.625507e-15 | 1.000000e-12 | yes |
| commuting_exact_control | 1.667776e-15 | 1.000000e-12 | yes |
| time_reversal | 8.551006e-16 | 1.000000e-10 | yes |
| unitarity | 1.041794e-14 | 1.000000e-10 | yes |
| eigenpair_residual | 2.860979e-16 | 1.000000e-10 | yes |
| three_way_closure | 1.323489e-23 | 1.593600e-12 | yes |
| direct_shift_even_parity | 0.000000e+00 | 1.000000e-12 | yes |
| proxy_no_power_below_four | 1.020560e-15 | 1.000000e-12 | yes |
| stored_coefficient_precision_no_lower_order | 4.970968e-15 | 1.000000e-12 | yes |
| cold_repeatability | 0.000000e+00 | 1.000000e-12 | yes |

The commuting control, complex128/80-digit comparison, signed-time branch tracking, formal low-order cancellation, and three-way closure were evaluated before Experiment B/C.

Elapsed wall time: 1.092 s. Peak RSS: 269716 KiB.
