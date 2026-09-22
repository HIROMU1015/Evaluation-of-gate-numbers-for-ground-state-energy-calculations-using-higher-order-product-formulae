# F01/F02/F05 full-electron HF mechanism bridge

Status: **failed_numerical_validation**

The committed Yoshida-4/two-term labels are reused unchanged: HF equilibrium passes and HF stretch150 fails. New truth points: **0**. The new matrix-log and eigendecomposition work is predeclared, diagnostic-only mechanism computation.

## Source identity

- H01 artifact: `/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8`
- Both pickle Hamiltonian hashes and the reconstructed group sums passed.
- Hamiltonians were not regenerated.

## Controlled Yoshida-4 comparison

| condition | committed label | |a4|/||D4|| | ||QD4|0>||/||D4|| | mixing fraction | a8 cancellation | minimum phase compression |
|---|---|---:|---:|---:|---:|---:|
| HF_full_eq_sto3g | pass | 2.4274e-03 | 1.3655e-01 | 3.2969e-01 | 1.0000e+00 | 1.0000e+00 |
| HF_full_stretch150_sto3g | fail | 7.0242e-04 | 6.9153e-02 | 2.6088e-01 | 1.0000e+00 | 1.0000e+00 |

## Predeclared mechanism reading

- The largest equilibrium-to-stretch magnitude ratio among the four requested Yoshida-4 components is **D4 coupling** (0.4768x).
- State-mixing flag at stretch: `True`; strong-a8-cancellation flag: `False`.
- The physical gap changes by a factor of 0.3115; the minimum normalized phase-gap ratio changes from 1 to 1.
- These flags are controlled-pair explanatory candidates, not a proof of a unique cause. Physical gap, PF phase gap, and polynomial order are not interpreted alone.
- current_m3 is diagnostic control only. N2/CO rows are external success context; no dense N2/CO D8 operator was constructed.

## Numerical gates

| gate | measured | threshold | pass |
|---|---:|---:|:---:|
| source_identity:HF_full_eq_sto3g:internal_protocol_hash | True | True | yes |
| source_identity:HF_full_eq_sto3g:internal_hamiltonian_hash | True | True | yes |
| source_identity:HF_full_eq_sto3g:metadata_hamiltonian_hash | True | True | yes |
| source_identity:HF_full_eq_sto3g:metadata_complete | True | True | yes |
| source_identity:HF_full_eq_sto3g:group_sum | 8.036906368975326e-18 | 1e-12 | yes |
| source_identity:HF_full_stretch150_sto3g:internal_protocol_hash | True | True | yes |
| source_identity:HF_full_stretch150_sto3g:internal_hamiltonian_hash | True | True | yes |
| source_identity:HF_full_stretch150_sto3g:metadata_hamiltonian_hash | True | True | yes |
| source_identity:HF_full_stretch150_sto3g:metadata_complete | True | True | yes |
| source_identity:HF_full_stretch150_sto3g:group_sum | 8.902400366068217e-18 | 1e-12 | yes |
| HF_full_eq_sto3g:yoshida4:h0_relative_frobenius | 2.2180623291502834e-16 | 1e-11 | yes |
| HF_full_eq_sto3g:yoshida4:forbidden_order_relative_frobenius | 4.033443450560797e-06 | 1e-08 | no |
| HF_full_eq_sto3g:yoshida4:precision_d4 | 3.7767993025957555e-11 | 1e-10 | yes |
| HF_full_eq_sto3g:yoshida4:precision_d6 | 7.671948904308422e-10 | 1e-08 | yes |
| HF_full_eq_sto3g:yoshida4:precision_d8 | 2.4332130370791426e-08 | 1e-06 | yes |
| HF_full_eq_sto3g:current_m3:h0_relative_frobenius | 5.591352544506747e-17 | 1e-11 | yes |
| HF_full_eq_sto3g:current_m3:forbidden_order_relative_frobenius | 4.036046926150755e-06 | 1e-08 | no |
| HF_full_eq_sto3g:current_m3:precision_d4 | 2.6678510643022286e-10 | 1e-10 | no |
| HF_full_eq_sto3g:current_m3:precision_d6 | 4.735100587122649e-09 | 1e-08 | yes |
| HF_full_eq_sto3g:current_m3:precision_d8 | 1.1368515776523714e-07 | 1e-06 | yes |
| HF_full_stretch150_sto3g:yoshida4:h0_relative_frobenius | 2.219284725712502e-16 | 1e-11 | yes |
| HF_full_stretch150_sto3g:yoshida4:forbidden_order_relative_frobenius | 3.918877633074129e-06 | 1e-08 | no |
| HF_full_stretch150_sto3g:yoshida4:precision_d4 | 4.1331821856847787e-11 | 1e-10 | yes |
| HF_full_stretch150_sto3g:yoshida4:precision_d6 | 1.0189031357389327e-09 | 1e-08 | yes |
| HF_full_stretch150_sto3g:yoshida4:precision_d8 | 2.5803528979246494e-08 | 1e-06 | yes |
| HF_full_stretch150_sto3g:current_m3:h0_relative_frobenius | 5.61322207909061e-17 | 1e-11 | yes |
| HF_full_stretch150_sto3g:current_m3:forbidden_order_relative_frobenius | 3.9242531817937336e-06 | 1e-08 | no |
| HF_full_stretch150_sto3g:current_m3:precision_d4 | 3.065081759501395e-10 | 1e-10 | no |
| HF_full_stretch150_sto3g:current_m3:precision_d6 | 5.711021224436329e-09 | 1e-08 | yes |
| HF_full_stretch150_sto3g:current_m3:precision_d8 | 2.0392746319307648e-07 | 1e-06 | yes |
| HF_full_eq_sto3g:yoshida4:a8_decomposition_relative_identity | 5.81059451965245e-15 | 1e-09 | yes |
| HF_full_eq_sto3g:current_m3:a8_decomposition_relative_identity | 2.746284935699193e-13 | 1e-09 | yes |
| HF_full_stretch150_sto3g:yoshida4:a8_decomposition_relative_identity | 1.0280135213037634e-14 | 1e-09 | yes |
| HF_full_stretch150_sto3g:current_m3:a8_decomposition_relative_identity | 2.263070306754738e-13 | 1e-09 | yes |
| finite_log_minimum_branch_cut_margin_radians | 0.0005434471725132006 | 0.3 | no |
| f05_minimum_selected_branch_overlap_probability | 0.9754537496768746 | 0.9 | yes |
| f05_maximum_eigenpair_residual_2_norm | 1.0879419816954628e-14 | 1e-09 | yes |
| reused_committed_shift_absolute_hartree | 4.602123432994031e-14 | 1e-09 | yes |
| diagnostic_nonleakage | True | True | yes |

## Diagnostic accounting

- `new_direct_truth_point_count = 0`
- `reused_committed_direct_point_count = 20`
- `new_f05_diagnostic_eigendecomposition_count = 36`
- `new_finite_log_diagnostic_unitary_count = 164`
- Diagnostic-to-fit/cost/PF-selection leakage check: `True`.
