# Unused-molecule frozen hold-out

Status: complete

The five-point direct calibration is oracle-assisted; this does not validate a cheap practical estimator.

## Pre-registered primary comparison

| PF | primary conditions passed | all four | frozen budget | budget with 1% cost margin |
|---|---:|---:|---:|---:|
| yoshida4 | 4/4 | True | 1/4 | 4/4 |
| current_m3 | 4/4 | True | 4/4 | 4/4 |
| two_term_center | 4/4 | True | 2/4 | 4/4 |
| m5_best | 0/4 | False | 1/4 | 1/4 |
| yoshida6_m3 | 4/4 | True | 3/4 | 4/4 |

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
