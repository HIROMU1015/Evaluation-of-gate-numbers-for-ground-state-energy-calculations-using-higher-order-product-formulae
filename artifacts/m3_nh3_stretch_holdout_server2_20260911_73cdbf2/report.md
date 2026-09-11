# Fixed m=3 PF validation on bond-stretched NH3

Source result commit: 73cdbf200d348cc610d4c20f45a3208ce7ad2e7e
Status: complete

## Backend pilot

Pilot: NH3_r125_631g, two_term_center at t=t_ana. CPU time 23.7967 s; GPU attempt skipped_no_idle_gpu; selected cpu. Projected wall time 1760.86 s.

A GPU was used only if it passed the idle-resource gate. Existing processes were neither stopped nor displaced.

## Model results

| condition | PF | model | a4 | a6 | t_ana | t_pred | R_max | eta_C | eta_min | eta_t | pass |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| NH3_r125_631g | current_m3 | original_one_term | -6.06822e-06 | 0 | 1.51386 | 1.51386 | 0.0201608 | 0.012612 | 0.000929668 | 0.0170493 | False |
| NH3_r125_631g | current_m3 | refit_one_term | -6.05638e-06 | 0 | 1.51386 | 1.5146 | 0.0195487 | 0.0121624 | 0.000885358 | 0.0165692 | False |
| NH3_r125_631g | current_m3 | two_term | -6.0694e-06 | 1.2173e-07 | 1.51386 | 1.54012 | 0.00216208 | 0.00139093 | 0 | 0 | True |
| NH3_r125_631g | two_term_center | original_one_term | -1.03185e-05 | 0 | 1.32571 | 1.32571 | 0.00740094 | 0.0049384 | 0.000130928 | 0.00683299 | True |
| NH3_r125_631g | two_term_center | refit_one_term | -1.03102e-05 | 0 | 1.32571 | 1.32597 | 0.0071611 | 0.00474517 | 0.000123926 | 0.00663503 | True |
| NH3_r125_631g | two_term_center | two_term | -1.03195e-05 | 1.12619e-07 | 1.32571 | 1.33483 | 0.000348691 | 0.000182404 | 0 | 0 | True |
| NH3_r125_ccpvdz | current_m3 | original_one_term | -5.20853e-06 | 0 | 1.5728 | 1.5728 | 0.0180204 | 0.0107565 | 0.00128459 | 0.0145307 | False |
| NH3_r125_ccpvdz | current_m3 | refit_one_term | -5.19969e-06 | 0 | 1.5728 | 1.57347 | 0.0174936 | 0.0104349 | 0.00117803 | 0.0141122 | False |
| NH3_r125_ccpvdz | current_m3 | two_term | -5.2093e-06 | 8.32642e-08 | 1.5728 | 1.59599 | 0.00276912 | 0.0016762 | 0 | 0 | True |
| NH3_r125_ccpvdz | two_term_center | original_one_term | -8.85664e-06 | 0 | 1.37732 | 1.37732 | 0.0053773 | 0.00360003 | 6.80378e-05 | 0.00484145 | True |
| NH3_r125_ccpvdz | two_term_center | refit_one_term | -8.85152e-06 | 0 | 1.37732 | 1.37752 | 0.00520448 | 0.00345846 | 6.43583e-05 | 0.00469738 | True |
| NH3_r125_ccpvdz | two_term_center | two_term | -8.85716e-06 | 6.37116e-08 | 1.37732 | 1.38402 | 0.000416645 | 0.000212388 | 0 | 0 | True |
| NH3_r150_631g | current_m3 | original_one_term | -3.84683e-06 | 0 | 1.69659 | 1.69659 | 0.0240809 | 0.0146944 | 0.00130276 | 0.0209277 | False |
| NH3_r150_631g | current_m3 | refit_one_term | -3.83756e-06 | 0 | 1.69659 | 1.69761 | 0.0233131 | 0.0141563 | 0.00123008 | 0.0203371 | False |
| NH3_r150_631g | current_m3 | two_term | -3.84755e-06 | 7.43583e-08 | 1.69659 | 1.73285 | 0.00175964 | 0.00108961 | 0 | 0 | True |
| NH3_r150_631g | two_term_center | original_one_term | -6.54115e-06 | 0 | 1.48573 | 1.48573 | 0.0100929 | 0.00666334 | 0.000229326 | 0.00964605 | True |
| NH3_r150_631g | two_term_center | refit_one_term | -6.53367e-06 | 0 | 1.48573 | 1.48615 | 0.00974518 | 0.00638893 | 0.000216206 | 0.00936301 | True |
| NH3_r150_631g | two_term_center | two_term | -6.54184e-06 | 7.92241e-08 | 1.48573 | 1.5002 | 8.51733e-05 | 8.26189e-06 | 0 | 0 | True |
| NH3_r150_ccpvdz | current_m3 | original_one_term | -3.80043e-06 | 0 | 1.70174 | 1.70174 | 0.0193986 | 0.011971 | 0.000828824 | 0.0164209 | False |
| NH3_r150_ccpvdz | current_m3 | refit_one_term | -3.79302e-06 | 0 | 1.70174 | 1.70257 | 0.0187884 | 0.0115196 | 0.000786911 | 0.0159407 | False |
| NH3_r150_ccpvdz | current_m3 | two_term | -3.8009e-06 | 5.82851e-08 | 1.70174 | 1.73015 | 0.0020572 | 0.00107123 | 0 | 0 | True |
| NH3_r150_ccpvdz | two_term_center | original_one_term | -6.46193e-06 | 0 | 1.49026 | 1.49026 | 0.00693757 | 0.00470602 | 0.000114348 | 0.00664061 | True |
| NH3_r150_ccpvdz | two_term_center | refit_one_term | -6.45695e-06 | 0 | 1.49026 | 1.49055 | 0.00670594 | 0.00451883 | 0.000108047 | 0.00644923 | True |
| NH3_r150_ccpvdz | two_term_center | two_term | -6.46258e-06 | 5.42674e-08 | 1.49026 | 1.50022 | 0.000123856 | 7.35616e-05 | 0 | 0 | True |

## Pass counts

- two_term_center:
  - original_one_term: 4/4
  - refit_one_term: 4/4
  - two_term: 4/4
- current_m3:
  - original_one_term: 0/4
  - refit_one_term: 0/4
  - two_term: 4/4

Original one-term failed but two-term passed: [{'condition': 'NH3_r125_631g', 'formula': 'current_m3'}, {'condition': 'NH3_r125_ccpvdz', 'formula': 'current_m3'}, {'condition': 'NH3_r150_631g', 'formula': 'current_m3'}, {'condition': 'NH3_r150_ccpvdz', 'formula': 'current_m3'}]
Refitted one-term failed but two-term passed: [{'condition': 'NH3_r125_631g', 'formula': 'current_m3'}, {'condition': 'NH3_r125_ccpvdz', 'formula': 'current_m3'}, {'condition': 'NH3_r150_631g', 'formula': 'current_m3'}, {'condition': 'NH3_r150_ccpvdz', 'formula': 'current_m3'}]

## Direct PF-cost comparison

| condition | direct cost ratio new/current |
|---|---:|
| NH3_r125_631g | 1.15157 |
| NH3_r125_ccpvdz | 1.15147 |
| NH3_r150_631g | 1.15227 |
| NH3_r150_ccpvdz | 1.15099 |

## Branch and resource diagnostics

- Branch gate: True; minimum ground overlap 0.999991; minimum adjacent-time overlap 0.999988; maximum eigenpair residual 4.3195e-14.

| condition | elapsed s | preparation s | peak CPU RSS KiB | peak GPU delta MiB |
|---|---:|---:|---:|---:|
| NH3_r125_631g | 547.024 | 15.835 | 937960 | NA |
| NH3_r125_ccpvdz | 578.37 | 16.0138 | 935316 | NA |
| NH3_r150_631g | 579.637 | 16.0383 | 941668 | NA |
| NH3_r150_ccpvdz | 545.237 | 16.1015 | 955560 | NA |

## Conclusions

The fixed new PF plus the two-term model passes all four stretched NH3 basis/geometry holdouts.

Adding the sixth-order term is required for full declared coverage or stable prediction accuracy.

The new PF is not lower-cost than current_m3 in every stretched condition at each PF's own two-term optimum.

The equilibrium NH3 records from 73cdbf2 are reused only as a reference and are not included in the new four-condition pass count.
All eta_t and eta_min values are resolved on the frozen local grid; they do not establish a continuous optimum.
