# H01 pilot: exact versus HF/CISD state-dependent PF selection

Status: **pilot_complete_with_findings**

This is the exact/HF/determinant-space-CISD subset of H01. Selected-CI, MPS convergence, and the H01 dependency F03 are not completed here.
Approximate-state D-operator expectations are selector diagnostics, not PF eigenvalue shifts.

## State quality

| system | state | subspace dimension | energy error | variance | exact overlap | generation time (s) |
|---|---|---:|---:|---:|---:|---:|
| H2 | exact | 4 | 2.331468e-15 | 5.573124e-32 | 1.00000000 | n/a |
| H2 | hf | 1 | 3.504168e-02 | 3.872653e-02 | 0.96926702 | 1.582084e-06 |
| H2 | cisd | 4 | 2.220446e-15 | 1.825249e-32 | 1.00000000 | 9.429804e-05 |
| H4 | exact | 36 | 3.108624e-15 | 2.139794e-30 | 1.00000000 | n/a |
| H4 | hf | 1 | 6.784151e-02 | 8.001674e-02 | 0.93646386 | 1.276145e-06 |
| H4 | cisd | 27 | 1.355607e-03 | 3.628241e-03 | 0.99946684 | 2.274020e-04 |

## PF selection

| system | state | candidates | selected | exact-state selection | leading-model regret | direct formula regret | direct PF+time regret |
|---|---|---|---|---|---:|---:|---:|
| H2 | exact | all_f01_four | m5_best | m5_best | 0.0000% | n/a | n/a |
| H2 | hf | all_f01_four | two_term_center | m5_best | 38.1362% | n/a | n/a |
| H2 | cisd | all_f01_four | m5_best | m5_best | 0.0000% | n/a | n/a |
| H2 | exact | operational_x02_three | current_m3 | current_m3 | 0.0000% | 0.0000% | 0.0673% |
| H2 | hf | operational_x02_three | two_term_center | current_m3 | 14.1904% | 14.7589% | 21.7977% |
| H2 | cisd | operational_x02_three | current_m3 | current_m3 | 0.0000% | 0.0000% | 0.0673% |
| H4 | exact | all_f01_four | m5_best | m5_best | 0.0000% | n/a | n/a |
| H4 | hf | all_f01_four | two_term_center | m5_best | 34.1724% | n/a | n/a |
| H4 | cisd | all_f01_four | m5_best | m5_best | 0.0000% | n/a | n/a |
| H4 | exact | operational_x02_three | current_m3 | current_m3 | 0.0000% | 0.0000% | 0.0985% |
| H4 | hf | operational_x02_three | two_term_center | current_m3 | 14.1904% | 14.9047% | 24.1083% |
| H4 | cisd | operational_x02_three | current_m3 | current_m3 | 0.0000% | 0.0000% | 0.2429% |

## Findings

HF selected two_term_center instead of the exact-state current_m3 in both operational candidate sets. Formula-only direct sampled regret was 14.76%–14.90%; including the HF-predicted time raised the sampled regret to 21.80%–24.11%.

Determinant-space CISD recovered the exact-state selected PF in 4/4 system/candidate-set comparisons. H4 CISD used 27/36 determinants and had exact-state overlap above 0.9994.

The four-formula leading model selects m5_best but has no common X02 direct curve for m5_best, so direct regret is intentionally reported only for the predeclared operational three-formula set.

## Decision

HF alone is not sufficient for the state-dependent selector in this pilot. CISD recovers the exact-state PF choice on both systems, so H02 should next separate energy error, variance, and D4-expectation error using controlled states.
Do not interpret this two-system result as a molecule-independent selector guarantee.

## Files

- `audit.json`: complete pilot summary.
- `state_metrics.csv`: norm, energy, variance, overlap, timing.
- `operator_expectations.csv`: signed D4/D6/D8 expectations and errors.
- `selection_summary.csv`: leading-model and direct sampled regrets.
- `states.npz`: exact/HF/CISD states and determinant subspaces.
- `manifest.json`: source, input, and artifact hashes.
