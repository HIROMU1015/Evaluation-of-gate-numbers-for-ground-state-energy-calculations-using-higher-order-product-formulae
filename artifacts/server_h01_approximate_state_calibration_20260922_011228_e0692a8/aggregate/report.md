# H01 approximate-state calibration

## Conclusion

- Exact-ground echo sanity: **PASS**. Both PFs reproduce the source conclusion in all four primary conditions.
- CISD state substitution: **FAIL** under the frozen all-four-condition rule.
- CISD nevertheless meets the frozen 1.01 budget in all four primary conditions for both PFs.
- RHF state substitution fails the frozen transfer rule for both PFs.
- Because neither approximate-state method makes both PFs feasible under all four checks, approximate-state PF selection is not validated.
- HF is auxiliary only. HF stretch retains the known failure and is not misclassified as a primary success.
- This is an oracle-time development diagnostic; it is not end-to-end cheap calibration.

## Primary echo-phase five-point results

| Condition | PF | State | pass | 1.01 budget | eta_star | eta_min | eta_t | max residual/eps |
|---|---|---|---:|---:|---:|---:|---:|---:|
| N2_active_eq_sto3g | current_m3 | exact_ground | True | True | 0.0002217 | 0 | 0 | 0.0005152 |
| N2_active_eq_sto3g | current_m3 | rhf_determinant | False | False | 0.7518 | 1.045 | 0.1765 | 3.803 |
| N2_active_eq_sto3g | current_m3 | cisd | False | True | 0.06445 | 0.01884 | 0.09091 | 0.1051 |
| N2_active_eq_sto3g | yoshida4 | exact_ground | True | True | 1.121e-06 | 0 | 0 | 2.461e-06 |
| N2_active_eq_sto3g | yoshida4 | rhf_determinant | False | True | 0.03887 | 0.003876 | 0.04762 | 0.05369 |
| N2_active_eq_sto3g | yoshida4 | cisd | False | True | 0.01055 | 0.0002791 | 0.009901 | 0.01229 |
| N2_active_stretch150_sto3g | current_m3 | exact_ground | True | True | 0.0004733 | 0.0005177 | 0.009901 | 0.0009679 |
| N2_active_stretch150_sto3g | current_m3 | rhf_determinant | False | False | 0.2318 | 0.001239 | 0.05263 | 2.556 |
| N2_active_stretch150_sto3g | current_m3 | cisd | False | True | 0.1484 | 0.09805 | 0.1304 | 0.242 |
| N2_active_stretch150_sto3g | yoshida4 | exact_ground | True | True | 6.134e-05 | 0 | 0 | 0.0001084 |
| N2_active_stretch150_sto3g | yoshida4 | rhf_determinant | False | False | 0.01371 | 0.0009759 | 0.02041 | 0.01982 |
| N2_active_stretch150_sto3g | yoshida4 | cisd | False | True | 0.04571 | 0.005603 | 0.04762 | 0.06265 |
| CO_active_eq_sto3g | current_m3 | exact_ground | True | True | 0.0003327 | 0 | 0 | 0.0007637 |
| CO_active_eq_sto3g | current_m3 | rhf_determinant | False | False | 0.5991 | 0.4401 | 0.1765 | 2.865 |
| CO_active_eq_sto3g | current_m3 | cisd | False | True | 0.07188 | 0.02505 | 0.09091 | 0.1202 |
| CO_active_eq_sto3g | yoshida4 | exact_ground | True | True | 1.529e-05 | 0 | 0 | 2.711e-05 |
| CO_active_eq_sto3g | yoshida4 | rhf_determinant | False | True | 0.03087 | 0.001776 | 0.04762 | 0.04261 |
| CO_active_eq_sto3g | yoshida4 | cisd | False | True | 0.01054 | 0.0002914 | 0.009901 | 0.01243 |
| CO_active_stretch150_sto3g | current_m3 | exact_ground | True | True | 0.0009336 | 0.002436 | 0.02913 | 0.004339 |
| CO_active_stretch150_sto3g | current_m3 | rhf_determinant | False | False | 0.8975 | 3.326 | 0.1765 | 3.455 |
| CO_active_stretch150_sto3g | current_m3 | cisd | False | True | 0.1045 | 0.06551 | 0.1304 | 0.1838 |
| CO_active_stretch150_sto3g | yoshida4 | exact_ground | True | True | 0.0003252 | 0 | 0 | 0.000583 |
| CO_active_stretch150_sto3g | yoshida4 | rhf_determinant | False | False | n/a | n/a | 0.1765 | 2.374 |
| CO_active_stretch150_sto3g | yoshida4 | cisd | False | True | 0.01035 | 0.0004508 | 0.009901 | 0.01433 |

## Transfer summary

| State | PF | four-condition pass | 1.01 budget in all four |
|---|---|---:|---:|
| exact_ground | current_m3 | True | True |
| exact_ground | yoshida4 | True | True |
| cisd | current_m3 | False | True |
| cisd | yoshida4 | False | True |
| rhf_determinant | current_m3 | False | False |
| rhf_determinant | yoshida4 | False | False |

## Runtime and numerical audit

- CPU/GPU representative PF-state difference: `3.171e-15`.
- Representative CPU PF action: `0.228` s; GPU PF action: `1.084` s. CPU was selected for echo calibration.
- New direct-truth points audited: `783`; source-reused appearances: `127`.
- Sum of per-point direct timings (parallel work, not elapsed time): `2719.2` s.
- Maximum recorded CPU RSS: `748.2` MiB.
- Maximum recorded GPU memory used: `701` MiB; maximum per-process increment: `697` MiB.
- Continuous-branch vs independent maximum-ground-overlap disagreements: `0`.
- The duplicate reuse aggregation issue was fixed without recomputing valid points; retry used hash-validated time-level checkpoints.

## Files and scope

- `metrics.csv`: all state/PF/model decisions.
- `state_diagnostics.csv`: norms, energies, variances, residuals, and evaluation-only exact overlaps.
- `direct_timing_and_branch_audit.csv`: unique truth timing and branch audit rows.
- Server-only Hamiltonian pickles and selected-vector `.npy` checkpoints are excluded from Git; final truth JSONs retain the numerical results.
- No PF coefficients, thresholds, molecules, model powers, or time grids were adapted.
