# Unused-molecule frozen hold-out

Status: numerical calculation complete; post-run audit complete on 2026-09-22

Unfinished or nonconforming items from the original execution protocol are listed in **Post-run audit and limitations** below. The audit did not change any numerical raw JSON.

## Provenance and fixed specification

- Base result commit: `46a7ed165650cb80506be14d997380e0bf333680`
- Hold-out plan commit: `b2e0c49f1873b44ef7021afe60e02d6b0750713e`
- Prevalidation audit commit: `2ba6174b6f9617d51766579c775a77132f3c7f57`
- Runner implementation commit: `d288797a544c5e0ffac7bf1c46d7308de90fd9fb`
- Numerical result commit: `33a761d44a24022ad61192c41a196dd4cb3afbca`
- Instruction SHA-256: `6b8e66042e79edc91b3cd159073eed60d515c8beedcea7af29ed655bac1175ac`
- Protocol SHA-256: `b0fc69d3ef89fcae28172ae1bd89ca0b192154ff86eed34410f73cdc2a770a56`
- Independence audit: no prior HF/N2/CO PF-error or QPE-cost numerical result was identified before this run; the recorded matches were planning and protocol references.

The six Hamiltonians passed the frozen metadata checks. N2 and CO used STO-3G, two frozen core spatial orbitals, CAS(10e,8o), `n_alpha=n_beta=5`, and population-sector dimension 3136 before an additional exact diagonal-Z2 restriction. HF used all 10 electrons in 6 spatial orbitals, `n_alpha=n_beta=5`, and population-sector dimension 36 before the same type of exact restriction. Equilibrium and uniformly 1.5-times-stretched geometries were evaluated for each molecule.

## Execution and resource summary

- Recorded execution span: 965.98 s (about 16.1 min), based on the earliest and latest committed timestamps.
- Maximum recorded CPU RSS: 994836 KiB (about 0.95 GiB).
- Maximum recorded GPU-memory increment: 773 MiB.
- Executed direct-point backend: GPU dense PF construction followed by CPU Schur decomposition.
- Direct calibration: five signed PF-eigenvalue points per Hamiltonian/PF for the primary models; the fixed three-point ablation was retained separately.

The required CPU-only versus GPU pilot comparison was not saved. Therefore the selected backend is documented as the executed route, not as a demonstrated fastest route.

The five-point direct calibration is oracle-assisted; this does not validate a cheap practical estimator.

## Pre-registered primary comparison

| PF | primary conditions passed | all four | frozen budget | budget with 1% cost margin |
|---|---:|---:|---:|---:|
| yoshida4 | 4/4 | True | 1/4 | 4/4 |
| current_m3 | 4/4 | True | 4/4 | 4/4 |
| two_term_center | 4/4 | True | 2/4 | 4/4 |
| m5_best | 0/4 | False | 1/4 | 1/4 |
| yoshida6_m3 | 4/4 | True | 3/4 | 4/4 |

Among the PF/model pairs that passed all four primary conditions, `current_m3` had the lowest direct grid-minimum cost. Relative to `current_m3`, the observed ranges over the four primary conditions were 1.148--1.161 for `two_term_center`, 1.900--1.936 for Yoshida 4th order, and 1.587--1.770 for Yoshida 6th order. The fixed 1% cost margin repaired all frozen-budget misses for these four passing PFs. The largest required margin inferred for Yoshida 4th order or `two_term_center` was only about 0.032%.

For the auxiliary full-electron HF conditions, Yoshida 4th order plus the primary two-term model passed the four model criteria at equilibrium. No fixed primary PF/model pair passed all four criteria at the 1.5-times-stretched HF geometry. Thus the main conclusion is restricted to the frozen-core active-space N2/CO conditions and does not establish full-electron universality.

## Per-condition metrics

| condition | PF | model | primary | fine | pass | eta* | eta_min | eta_t | residual/eps | budget | +1% budget |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| N2_active_eq_sto3g | yoshida4 | three_term_5point | False | True | True | 8.921e-08 | 0 | 0 | 1.3896e-07 | True | True |
| N2_active_eq_sto3g | yoshida4 | two_term_3point | False | True | True | 5.4971e-06 | 0 | 0 | 8.7901e-06 | True | True |
| N2_active_eq_sto3g | yoshida4 | two_term_5point | True | True | True | 2.1167e-06 | 0 | 0 | 3.9168e-06 | True | True |
| N2_active_eq_sto3g | current_m3 | two_term_3point | False | True | True | 0.00050409 | 0 | 0 | 0.0009203 | True | True |
| N2_active_eq_sto3g | current_m3 | two_term_5point | True | True | True | 0.00039022 | 0 | 0 | 0.00075605 | True | True |
| N2_active_eq_sto3g | two_term_center | two_term_3point | False | True | True | 9.3342e-05 | 0 | 0 | 0.00016776 | True | True |
| N2_active_eq_sto3g | two_term_center | two_term_5point | True | True | True | 7.0282e-05 | 0 | 0 | 0.00013439 | True | True |
| N2_active_eq_sto3g | m5_best | two_term_3point | False | True | False | 0.086376 | 0.25991 | 0.074074 | 0.79806 | True | True |
| N2_active_eq_sto3g | m5_best | two_term_5point | True | False | False | 0.10324 | 0.15157 | 0.13043 | 8.1672 | True | True |
| N2_active_eq_sto3g | yoshida6_m3 | three_term_5point | True | True | True | 3.9207e-05 | 0 | 0 | 9.5459e-05 | True | True |
| N2_active_stretch150_sto3g | yoshida4 | three_term_5point | False | True | True | 6.3866e-07 | 0 | 0 | 1.5543e-06 | True | True |
| N2_active_stretch150_sto3g | yoshida4 | two_term_3point | False | True | True | 8.3496e-05 | 0 | 0 | 0.00014774 | False | True |
| N2_active_stretch150_sto3g | yoshida4 | two_term_5point | True | True | True | 6.6477e-05 | 0 | 0 | 0.00012305 | False | True |
| N2_active_stretch150_sto3g | current_m3 | two_term_3point | False | True | True | 0.0010313 | 0.0073421 | 0.029126 | 0.0081398 | True | True |
| N2_active_stretch150_sto3g | current_m3 | two_term_5point | True | True | True | 0.00091364 | 0.0085995 | 0.029126 | 0.0090172 | True | True |
| N2_active_stretch150_sto3g | two_term_center | two_term_3point | False | True | True | 7.0507e-05 | 0 | 0 | 8.2817e-05 | False | True |
| N2_active_stretch150_sto3g | two_term_center | two_term_5point | True | True | True | 4.3531e-05 | 0 | 0 | 4.6937e-05 | False | True |
| N2_active_stretch150_sto3g | m5_best | two_term_3point | False | False | False | n/a | n/a | 0.090909 | 10.499 | False | False |
| N2_active_stretch150_sto3g | m5_best | two_term_5point | True | False | False | n/a | n/a | 0.047619 | 2.5606 | False | False |
| N2_active_stretch150_sto3g | yoshida6_m3 | three_term_5point | True | True | True | 3.9345e-05 | 0 | 0 | 0.00011665 | True | True |
| CO_active_eq_sto3g | yoshida4 | three_term_5point | False | True | True | 2.0372e-06 | 0 | 0 | 3.728e-06 | False | True |
| CO_active_eq_sto3g | yoshida4 | two_term_3point | False | True | True | 1.6181e-05 | 0 | 0 | 2.8487e-05 | False | True |
| CO_active_eq_sto3g | yoshida4 | two_term_5point | True | True | True | 1.2313e-05 | 0 | 0 | 2.2879e-05 | False | True |
| CO_active_eq_sto3g | current_m3 | two_term_3point | False | True | True | 0.00069263 | 0 | 0 | 0.0012828 | True | True |
| CO_active_eq_sto3g | current_m3 | two_term_5point | True | True | True | 0.00054482 | 0 | 0 | 0.0010698 | True | True |
| CO_active_eq_sto3g | two_term_center | two_term_3point | False | True | True | 0.00010465 | 0 | 0 | 0.00019425 | True | True |
| CO_active_eq_sto3g | two_term_center | two_term_5point | True | True | True | 8.2538e-05 | 0 | 0 | 0.00016221 | True | True |
| CO_active_eq_sto3g | m5_best | two_term_3point | False | False | False | 0.34726 | 0.2832 | 0.11111 | 3.7392 | False | False |
| CO_active_eq_sto3g | m5_best | two_term_5point | True | False | False | 0.47228 | 0.2832 | 0.11111 | 4.0139 | False | False |
| CO_active_eq_sto3g | yoshida6_m3 | three_term_5point | True | True | True | 9.4201e-06 | 0 | 0 | 2.525e-05 | False | True |
| CO_active_stretch150_sto3g | yoshida4 | three_term_5point | False | True | True | 6.6013e-06 | 0 | 0 | 1.5355e-05 | True | True |
| CO_active_stretch150_sto3g | yoshida4 | two_term_3point | False | True | True | 0.00037135 | 0 | 0 | 0.00064956 | False | True |
| CO_active_stretch150_sto3g | yoshida4 | two_term_5point | True | True | True | 0.00027394 | 0 | 0 | 0.00050804 | False | True |
| CO_active_stretch150_sto3g | current_m3 | two_term_3point | False | True | True | 0.0013066 | 0.0012758 | 0.029126 | 0.0037379 | True | True |
| CO_active_stretch150_sto3g | current_m3 | two_term_5point | True | True | True | 0.0012222 | 0.0013161 | 0.029126 | 0.0036994 | True | True |
| CO_active_stretch150_sto3g | two_term_center | two_term_3point | False | True | True | 0.00045315 | 0 | 0 | 0.00064946 | False | True |
| CO_active_stretch150_sto3g | two_term_center | two_term_5point | True | True | True | 0.00031422 | 0 | 0 | 0.00045965 | False | True |
| CO_active_stretch150_sto3g | m5_best | two_term_3point | False | False | False | n/a | n/a | 0.052632 | 2.4472 | False | False |
| CO_active_stretch150_sto3g | m5_best | two_term_5point | True | False | False | n/a | n/a | 0.13043 | 2.4419 | False | False |
| CO_active_stretch150_sto3g | yoshida6_m3 | three_term_5point | True | True | True | 0.00016032 | 0 | 0 | 0.00046214 | True | True |
| HF_full_eq_sto3g | yoshida4 | three_term_5point | False | True | True | 0.00053994 | 0 | 0 | 0.0013643 | True | True |
| HF_full_eq_sto3g | yoshida4 | two_term_3point | False | True | True | 0.0017358 | 0 | 0 | 0.0025009 | False | True |
| HF_full_eq_sto3g | yoshida4 | two_term_5point | True | True | True | 0.0011932 | 0 | 0 | 0.0017374 | False | True |
| HF_full_eq_sto3g | current_m3 | two_term_3point | False | True | False | 0.035175 | 0.13367 | 0.090909 | 0.8902 | False | False |
| HF_full_eq_sto3g | current_m3 | two_term_5point | True | False | False | n/a | n/a | 0.13043 | 2.6425 | False | False |
| HF_full_eq_sto3g | two_term_center | two_term_3point | False | False | False | 0.16907 | 0.28412 | 0.13043 | 0.39631 | False | False |
| HF_full_eq_sto3g | two_term_center | two_term_5point | True | True | False | 0.11668 | 0.15401 | 0.090909 | 0.25932 | True | True |
| HF_full_eq_sto3g | m5_best | two_term_3point | False | False | False | 0.13056 | 0.15887 | 0.13043 | 0.32533 | True | True |
| HF_full_eq_sto3g | m5_best | two_term_5point | True | True | False | 0.064647 | 0.097083 | 0.090909 | 1.0196 | True | True |
| HF_full_eq_sto3g | yoshida6_m3 | three_term_5point | True | False | False | 0.010107 | 0.0014292 | 0.047619 | 0.048426 | True | True |
| HF_full_stretch150_sto3g | yoshida4 | three_term_5point | False | True | False | 0.1348 | 0.12169 | 0.009901 | 1.2698 | True | True |
| HF_full_stretch150_sto3g | yoshida4 | two_term_3point | False | False | False | 0.71897 | 0.60204 | 0.13043 | 1.5705 | False | False |
| HF_full_stretch150_sto3g | yoshida4 | two_term_5point | True | False | False | 0.70532 | 0.60204 | 0.13043 | 1.4765 | False | False |
| HF_full_stretch150_sto3g | current_m3 | two_term_3point | False | False | False | 0.12604 | 0.15426 | 0.13043 | 3.5534 | True | True |
| HF_full_stretch150_sto3g | current_m3 | two_term_5point | True | True | False | 0.09085 | 0.080521 | 0.056604 | 0.1639 | True | True |
| HF_full_stretch150_sto3g | two_term_center | two_term_3point | False | False | False | 0.087895 | 0.13233 | 0.13043 | 0.38657 | True | True |
| HF_full_stretch150_sto3g | two_term_center | two_term_5point | True | False | False | 0.11621 | 0.070701 | 0.13043 | 6.7855 | False | False |
| HF_full_stretch150_sto3g | m5_best | two_term_3point | False | False | False | 0.14056 | 0.15284 | 0.13043 | 0.32419 | True | True |
| HF_full_stretch150_sto3g | m5_best | two_term_5point | True | True | False | 0.045882 | 0.11266 | 0.090909 | 0.36966 | True | True |
| HF_full_stretch150_sto3g | yoshida6_m3 | three_term_5point | True | False | False | 0.039548 | 0.059111 | 0.13043 | 0.18669 | True | True |

Local-grid minima are minima over calculated points, not exact continuous-time minima.
The run stops after the six frozen conditions; no coefficient or molecule adaptation was performed.

## Post-run audit and limitations

An independent checkout of result commit `33a761d` passed the five dedicated tests and all 82 `review_tests`. Re-aggregation from the committed raw JSON reproduced every status, pass/fail result, budget decision, and displayed metric. Four residual values differed at the last floating-point digits only; the maximum absolute difference was `4.3e-17`.

The direct eigensolver selected, at each time independently, the eigenvector having maximum overlap with the exact Hamiltonian ground state. The previous-time selected vector was used to record adjacent overlap but did not determine the selected branch. This is not a literal implementation of continuous tracking from `t -> 0`. For the four passing active-space primary pairs, the minimum recorded adjacent overlap was at least 0.99997 and the maximum eigenpair residual was below `2.9e-14`, so no branch-switch symptom affects their reported pass result. This caveat remains part of the method definition and must be corrected in future runners.

The original result package also lacked the requested CPU-only pilot, some runner-specific preflight tests, content-validated resume keys, and portable stage-2 source paths. These are provenance and restartability limitations. They do not change the preserved raw numerical result, but this branch should not be used as a template for a new computation without addressing them.

After these results were inspected, N2, CO, and HF became development/diagnostic systems. Any HF/CISD proxy rule, model rule, or safety margin selected using this result requires a newly frozen molecule-level hold-out for its final evaluation.
