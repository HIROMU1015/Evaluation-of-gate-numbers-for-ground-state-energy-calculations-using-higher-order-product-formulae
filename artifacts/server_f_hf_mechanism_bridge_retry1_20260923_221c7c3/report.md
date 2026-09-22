# F01/F02/F05 full-electron HF mechanism bridge

Status: **complete_with_findings**

The committed Yoshida-4/two-term labels are reused unchanged: HF equilibrium passes and HF stretch150 fails. New truth points: **0**. The new matrix-log and eigendecomposition work is predeclared, diagnostic-only mechanism computation.

## Retry-1 numerical remediation

- Formal D4/D6/D8 operators use 128-bit Arb ball arithmetic. The required complex128/clongdouble comparison is evaluated after removing each group's scalar spectral midpoint; the scalar sum is restored to H0.
- Finite-time matrix logarithms use exact-H eigenbranches only to choose phase unwrap integers. This convention is invariant under a global energy-origin shift; principal-log margins remain diagnostic fields.
- Frozen PFs, time grids, thresholds, committed labels, and truth points are unchanged from the original protocol.

## Source identity

- H01 artifact: `/home/abe/myproject/pf_external_cache/h01_hf_mechanism_transfer_20260922_VY56wx`
- Both pickle Hamiltonian hashes and the reconstructed group sums passed.
- Hamiltonians were not regenerated.

## Controlled Yoshida-4 comparison

| condition | committed label | t_ana | |a4|/||D4|| | ||QD4|0>||/||D4|| | mixing fraction | |t8/(t4+t6)| at t_ana | minimum phase compression |
|---|---|---:|---:|---:|---:|---:|---:|
| HF_full_eq_sto3g | pass | 6.8243e-02 | 2.4274e-03 | 1.3655e-01 | 3.2969e-01 | 7.6720e-03 | 1.0000e+00 |
| HF_full_stretch150_sto3g | fail | 9.4445e-02 | 7.0242e-04 | 6.9153e-02 | 2.6088e-01 | 3.7141e-02 | 1.0000e+00 |

## Predeclared mechanism reading

- The largest multiplicative equilibrium-to-stretch change among the four requested Yoshida-4 components is **D4 mixing** (stretch/equilibrium=0.2382, change factor=4.198x).
- Stretch/equilibrium component ratios: D4 diagonal=0.2725, D4 coupling=0.4768, D8 direct=0.3319, D4 mixing=0.2382.
- State-mixing flag at stretch: `True`; strong-a8-cancellation flag: `False`.
- The physical gap changes by a factor of 0.3115; the minimum normalized phase-gap ratio changes from 1 to 1.
- The smaller stretched a4 increases t_ana by 1.384x. At t_ana, the formal |t8/(t4+t6)| ratio changes from 0.007672 to 0.03714.
- These flags are controlled-pair explanatory candidates, not a proof of a unique cause. Physical gap, PF phase gap, and polynomial order are not interpreted alone.
- current_m3 is diagnostic control only. N2/CO rows are external success context; no dense N2/CO D8 operator was constructed.

## Finite-log window audit

All three frozen windows are shown; no favorable window is selected post hoc. Large recovery errors mark finite-window instability and do not replace the Arb formal operators.

| condition | PF | window | D4 rel. error | D6 rel. error | D8 rel. error | fit residual | unwrap margin |
|---|---|---|---:|---:|---:|---:|---:|
| HF_full_eq_sto3g | yoshida4 | lower | 1.9046e-05 | 1.1092e-03 | 2.2063e-02 | 2.8749e-10 | 3.1415e+00 |
| HF_full_eq_sto3g | yoshida4 | middle | 8.0911e-04 | 2.4467e-02 | 2.5160e-01 | 5.5737e-08 | 3.1413e+00 |
| HF_full_eq_sto3g | yoshida4 | upper | 2.5946e-02 | 4.5777e-01 | 2.7488e+00 | 4.6477e-06 | 3.1407e+00 |
| HF_full_eq_sto3g | current_m3 | lower | 9.4738e+01 | 1.8729e+02 | 1.5311e+02 | 8.1681e-01 | 3.1387e+00 |
| HF_full_eq_sto3g | current_m3 | middle | 1.0928e+02 | 1.3613e+02 | 5.8036e+01 | 2.5614e+00 | 3.1402e+00 |
| HF_full_eq_sto3g | current_m3 | upper | 1.2228e+02 | 9.7945e+01 | 2.6461e+01 | 3.3919e+00 | 3.1382e+00 |
| HF_full_stretch150_sto3g | yoshida4 | lower | 9.2213e-04 | 2.7553e-02 | 2.7907e-01 | 5.2363e-08 | 3.1412e+00 |
| HF_full_stretch150_sto3g | yoshida4 | middle | 1.0511e-01 | 1.5939e+00 | 8.0818e+00 | 3.1186e-05 | 3.1402e+00 |
| HF_full_stretch150_sto3g | yoshida4 | upper | 1.8554e+02 | 1.5716e+03 | 4.4051e+03 | 2.4630e-01 | 3.1378e+00 |
| HF_full_stretch150_sto3g | current_m3 | lower | 2.3521e+02 | 2.4438e+02 | 8.1088e+01 | 6.1370e+00 | 3.1391e+00 |
| HF_full_stretch150_sto3g | current_m3 | middle | 4.7241e+01 | 3.1483e+01 | 6.7995e+00 | 3.8707e+00 | 3.1387e+00 |
| HF_full_stretch150_sto3g | current_m3 | upper | 7.4743e+01 | 2.9154e+01 | 4.9194e+00 | 1.0509e+01 | 3.1090e+00 |

## Numerical gates

| gate | measured | threshold | pass |
|---|---:|---:|:---:|
| source_identity:HF_full_eq_sto3g:internal_protocol_hash | True | True | yes |
| source_identity:HF_full_eq_sto3g:internal_hamiltonian_hash | True | True | yes |
| source_identity:HF_full_eq_sto3g:metadata_hamiltonian_hash | True | True | yes |
| source_identity:HF_full_eq_sto3g:metadata_complete | True | True | yes |
| source_identity:HF_full_eq_sto3g:group_sum | 8.022870513280765e-18 | 1e-12 | yes |
| source_identity:HF_full_stretch150_sto3g:internal_protocol_hash | True | True | yes |
| source_identity:HF_full_stretch150_sto3g:internal_hamiltonian_hash | True | True | yes |
| source_identity:HF_full_stretch150_sto3g:metadata_hamiltonian_hash | True | True | yes |
| source_identity:HF_full_stretch150_sto3g:metadata_complete | True | True | yes |
| source_identity:HF_full_stretch150_sto3g:group_sum | 8.93689406437858e-18 | 1e-12 | yes |
| HF_full_eq_sto3g:yoshida4:h0_relative_frobenius | 1.9688400606863153e-16 | 1e-11 | yes |
| HF_full_eq_sto3g:yoshida4:forbidden_order_relative_frobenius | 3.0220270481861e-16 | 1e-08 | yes |
| HF_full_eq_sto3g:yoshida4:precision_d4 | 6.044420607161221e-12 | 1e-10 | yes |
| HF_full_eq_sto3g:yoshida4:arb_reference_d4 | 9.591695838078262e-13 | 1e-10 | yes |
| HF_full_eq_sto3g:yoshida4:precision_d6 | 7.92280269910564e-11 | 1e-08 | yes |
| HF_full_eq_sto3g:yoshida4:arb_reference_d6 | 3.8993553327647515e-11 | 1e-08 | yes |
| HF_full_eq_sto3g:yoshida4:precision_d8 | 2.149126344974688e-09 | 1e-06 | yes |
| HF_full_eq_sto3g:yoshida4:arb_reference_d8 | 1.1809332187256336e-10 | 1e-06 | yes |
| HF_full_eq_sto3g:current_m3:h0_relative_frobenius | 4.144103854649558e-17 | 1e-11 | yes |
| HF_full_eq_sto3g:current_m3:forbidden_order_relative_frobenius | 1.5615274820092007e-15 | 1e-08 | yes |
| HF_full_eq_sto3g:current_m3:precision_d4 | 5.606791790717599e-11 | 1e-10 | yes |
| HF_full_eq_sto3g:current_m3:arb_reference_d4 | 6.6484159175301585e-12 | 1e-10 | yes |
| HF_full_eq_sto3g:current_m3:precision_d6 | 6.505804938640226e-10 | 1e-08 | yes |
| HF_full_eq_sto3g:current_m3:arb_reference_d6 | 2.6588983023367146e-10 | 1e-08 | yes |
| HF_full_eq_sto3g:current_m3:precision_d8 | 1.0951661254921655e-08 | 1e-06 | yes |
| HF_full_eq_sto3g:current_m3:arb_reference_d8 | 8.365542916782922e-10 | 1e-06 | yes |
| HF_full_stretch150_sto3g:yoshida4:h0_relative_frobenius | 1.9484991026191268e-16 | 1e-11 | yes |
| HF_full_stretch150_sto3g:yoshida4:forbidden_order_relative_frobenius | 2.898458399688086e-16 | 1e-08 | yes |
| HF_full_stretch150_sto3g:yoshida4:precision_d4 | 6.9559150919835464e-12 | 1e-10 | yes |
| HF_full_stretch150_sto3g:yoshida4:arb_reference_d4 | 1.067824172159804e-12 | 1e-10 | yes |
| HF_full_stretch150_sto3g:yoshida4:precision_d6 | 1.52827516669094e-10 | 1e-08 | yes |
| HF_full_stretch150_sto3g:yoshida4:arb_reference_d6 | 4.3920629740540083e-11 | 1e-08 | yes |
| HF_full_stretch150_sto3g:yoshida4:precision_d8 | 1.1277900961451865e-09 | 1e-06 | yes |
| HF_full_stretch150_sto3g:yoshida4:arb_reference_d8 | 1.3518135943221775e-10 | 1e-06 | yes |
| HF_full_stretch150_sto3g:current_m3:h0_relative_frobenius | 3.8275208944468643e-17 | 1e-11 | yes |
| HF_full_stretch150_sto3g:current_m3:forbidden_order_relative_frobenius | 1.4977111927936093e-15 | 1e-08 | yes |
| HF_full_stretch150_sto3g:current_m3:precision_d4 | 5.668168574212712e-11 | 1e-10 | yes |
| HF_full_stretch150_sto3g:current_m3:arb_reference_d4 | 7.38484348910571e-12 | 1e-10 | yes |
| HF_full_stretch150_sto3g:current_m3:precision_d6 | 9.058894534972896e-10 | 1e-08 | yes |
| HF_full_stretch150_sto3g:current_m3:arb_reference_d6 | 3.019809468312315e-10 | 1e-08 | yes |
| HF_full_stretch150_sto3g:current_m3:precision_d8 | 1.2515486065909175e-08 | 1e-06 | yes |
| HF_full_stretch150_sto3g:current_m3:arb_reference_d8 | 9.601826116450541e-10 | 1e-06 | yes |
| HF_full_eq_sto3g:yoshida4:a8_decomposition_relative_identity | 2.1221423418927672e-14 | 1e-09 | yes |
| HF_full_eq_sto3g:current_m3:a8_decomposition_relative_identity | 3.616157086600544e-13 | 1e-09 | yes |
| HF_full_stretch150_sto3g:yoshida4:a8_decomposition_relative_identity | 1.1748919071491776e-14 | 1e-09 | yes |
| HF_full_stretch150_sto3g:current_m3:a8_decomposition_relative_identity | 3.6626111288897727e-13 | 1e-09 | yes |
| finite_log_minimum_branch_cut_margin_radians | 3.109016101017611 | 0.3 | yes |
| f05_minimum_selected_branch_overlap_probability | 0.9754537496768753 | 0.9 | yes |
| f05_maximum_eigenpair_residual_2_norm | 1.1079199069025142e-14 | 1e-09 | yes |
| reused_committed_shift_absolute_hartree | 1.35269540793354e-13 | 1e-09 | yes |
| diagnostic_nonleakage | True | True | yes |

## Diagnostic accounting

- `new_direct_truth_point_count = 0`
- `reused_committed_direct_point_count = 20`
- `new_f05_diagnostic_eigendecomposition_count = 36`
- `new_finite_log_diagnostic_unitary_count = 164`
- Diagnostic-to-fit/cost/PF-selection leakage check: `True`.
