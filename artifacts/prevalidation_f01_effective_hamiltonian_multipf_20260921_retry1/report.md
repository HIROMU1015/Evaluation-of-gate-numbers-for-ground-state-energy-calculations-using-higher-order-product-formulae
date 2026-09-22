# F01 multi-PF effective-Hamiltonian audit

Status: **complete**

H2/H4の固定Hamiltonian分割に対し、4種類の既存4次PFを同じ有限時刻窓で検証した。これはF01の小系最小検証であり、F02の状態混合分解やHF holdoutの機構診断は含まない。

## Gate checks

| check | measured | threshold | pass |
|---|---:|---:|:---:|
| h0_frobenius_error | 2.365780e-15 | 5.000000e-13 | yes |
| forbidden_order_max_frobenius | 3.089325e-13 | 1.000000e-10 | yes |
| h2_numpy_relative_difference_d4_d6_d8 | 1.244581e-09 | 1.000000e-07 | yes |
| reference_relative_hermiticity_d4_d6_d8 | 5.952438e-09 | 1.000000e-08 | yes |
| fit_relative_error_d4 | 5.042533e-07 | 1.000000e-05 | yes |
| fit_relative_error_d6 | 7.889562e-05 | 1.000000e-03 | yes |
| fit_relative_error_d8 | 8.453421e-03 | 1.000000e-02 | yes |
| window_pair_relative_difference_d8 | 8.302898e-03 | 1.500000e-02 | yes |
| holdout_fit_relative_to_correction | 1.163168e-05 | 1.000000e-03 | yes |
| log_unitary_reconstruction_frobenius | 1.864029e-12 | 1.000000e-10 | yes |
| minimum_branch_cut_margin_radians | 1.672320e+00 | 5.000000e-01 | yes |

## D4 structure

| system | PF | ||D4||F | <0|D4|0> | ||Q D4|0>|| | diagonal fraction | coupling fraction |
|---|---|---:|---:|---:|---:|---:|
| H2 | yoshida4 | 1.591500e-03 | -1.002177e-03 | 5.119342e-04 | 0.6297 | 0.3217 |
| H2 | current_m3 | 3.033319e-05 | -2.738412e-06 | 2.127328e-05 | 0.0903 | 0.7013 |
| H2 | two_term_center | 2.276081e-05 | -4.656046e-06 | 1.540612e-05 | 0.2046 | 0.6769 |
| H2 | m5_best | 1.371419e-05 | -2.404951e-07 | 9.694411e-06 | 0.0175 | 0.7069 |
| H4 | yoshida4 | 2.926920e-02 | -4.711579e-03 | 3.771453e-03 | 0.1610 | 0.1289 |
| H4 | current_m3 | 5.016506e-04 | -1.287421e-05 | 1.717622e-04 | 0.0257 | 0.3424 |
| H4 | two_term_center | 3.818149e-04 | -2.188967e-05 | 1.300013e-04 | 0.0573 | 0.3405 |
| H4 | m5_best | 2.257184e-04 | -1.130650e-06 | 7.631173e-05 | 0.0050 | 0.3381 |

## Finite-log recovery and energy correlation

| system | PF | max rel D4 | max rel D6 | max rel D8 | min branch margin | D8 energy-series corr. |
|---|---|---:|---:|---:|---:|---:|
| H2 | yoshida4 | 4.152e-09 | 7.806e-07 | 2.356e-04 | 2.522 | 1.00000000 |
| H2 | current_m3 | 3.624e-08 | 2.133e-05 | 4.643e-03 | 2.523 | 1.00000000 |
| H2 | two_term_center | 4.880e-08 | 3.200e-05 | 7.074e-03 | 2.523 | 1.00000000 |
| H2 | m5_best | 6.943e-08 | 3.849e-05 | 8.453e-03 | 2.523 | 1.00000000 |
| H4 | yoshida4 | 4.540e-07 | 3.650e-05 | 1.535e-03 | 1.672 | 1.00000000 |
| H4 | current_m3 | 4.745e-07 | 7.221e-05 | 3.484e-03 | 1.674 | 1.00000000 |
| H4 | two_term_center | 5.043e-07 | 7.890e-05 | 3.694e-03 | 1.674 | 1.00000000 |
| H4 | m5_best | 4.353e-07 | 6.704e-05 | 3.317e-03 | 1.674 | 1.00000000 |

## Interpretation

D4の基底状態期待値は演算子Frobeniusノルムの0.501%–62.971%、基底状態から励起空間への結合ノルムは12.885%–70.689%である。したがって、全演算子ノルム、固有値シフト、状態混合を同一量とは扱えない。

全8条件で共通の3窓からD4/D6/D8を回収し、最悪D8相対誤差は0.845%、最小位相枝余裕は1.672 radだった。

The finite-log fits use identical windows for every PF. H2 also cross-checks the complex128 formal series against 70- and 100-decimal-digit ordered-product logarithms. H4 uses complex128 formal series, independently checked by finite-time matrix logs; this backend limitation is retained in the audit metadata.

## Decision

F01の小系・複数PFゲートは合格とする。次は同じ保存済みD4/D6/D8を使い、F02でa8を直接D8期待値とD4による二次状態混合へ分離する。

## Files

- `audit.json`: complete machine-readable summary.
- `formula_registry.csv`: exact PF weights and expanded S2 metadata.
- `reference_validation.csv`: formal-series precision/backend checks.
- `window_recovery.csv`: D4/D6/D8 recovery in the three common windows.
- `holdout_validation.csv`: interlaced unseen-time operator/eigenvalue checks.
- `operator_decomposition.csv`: diagonal and off-diagonal operator diagnostics.
- `effective_operators.npz`: complex D4/D6/D8 matrices plus the exact Hamiltonian, ground state, ground energy, and group matrices in the same stored basis.
- `manifest.json`: source hashes, environment, runtime, and artifact hashes.
