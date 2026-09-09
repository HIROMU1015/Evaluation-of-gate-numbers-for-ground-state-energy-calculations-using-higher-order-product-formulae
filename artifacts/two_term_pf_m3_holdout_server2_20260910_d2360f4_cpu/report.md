# Fixed m=3 two-term PF holdout validation

Status: complete

The coefficients were fixed before H6, H7, and NH3 were evaluated. These holdouts were not used for coefficient selection.

| condition | formula | eta_* | eta_min | eta_t | max unseen residual / epsilon | pass |
|---|---|---:|---:|---:|---:|---|
| H6 | current_m3 | 0.00102 | 0 | 0 | 0.00151566 | True |
| H6 | two_term_center | 2.58686e-05 | 0 | 0 | 7.01393e-05 | True |
| H7 | current_m3 | 0.0010589 | 0 | 0 | 0.00210023 | True |
| H7 | two_term_center | 5.89684e-06 | 0 | 0 | 4.14805e-05 | True |
| NH3_sto3g | current_m3 | 0.00046093 | 0 | 0 | 0.000853922 | True |
| NH3_sto3g | two_term_center | 6.47358e-05 | 0 | 0 | 0.000119954 | True |
| NH3_631g | current_m3 | 0.00270511 | 0 | 0 | 0.00506323 | True |
| NH3_631g | two_term_center | 0.000378528 | 0 | 0 | 0.000746744 | True |
| NH3_ccpvdz | current_m3 | 0.00346067 | 0 | 0 | 0.0206075 | True |
| NH3_ccpvdz | two_term_center | 0.000499135 | 0 | 0 | 0.000862127 | True |

eta_t is resolved only on the declared local grid and is not claimed as a continuous optimum.
Costs and prediction errors are retained separately in each condition JSON and in summary.json.
