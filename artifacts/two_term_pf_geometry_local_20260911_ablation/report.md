# One-term versus two-term m=3 PF error models

Source result commit: 73cdbf200d348cc610d4c20f45a3208ce7ad2e7e
Pre-validation baseline: d2360f49f9a754d1850eab60cd483f684bd8bffb

All models use the same three training points (0.1, 0.2, 0.3) t_ana. Those points are excluded from validation. Within each condition/PF, all three models use the same adaptive five-to-seven-point saved local direct grid.

The refitted one-term model uses the same normalized least-squares objective as the stored two-term model. Therefore the comparison isolates the effect of adding the t^6 term.

Before accepting added schedule points, each saved two-term optimum was recomputed as a reproduction sentinel. 24 sentinels passed; the maximum signed-shift difference was 3.23946e-15 Ha and the maximum direct-cost relative difference was 2.54791e-11.

Exact grouping-structure hashes, active-space metadata, dimensions, and energies were gated. The coefficient-inclusive hash may differ when rerunning SCF because of last-bit floating-point variation; the direct sentinel is the additional numerical equivalence check.

## Model coefficients and predicted schedules

| condition | PF | model | a4 | a6 | train t/t_ana | unseen t/t_* | t_pred | sampled accepted t/t_ana |
|---|---|---|---:|---:|---|---|---:|---|
| BeH2_stretch125 | two_term_center | original_one_term | -5.02647e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.58685 | 0.912978-1.11586 (7/7) |
| BeH2_stretch125 | two_term_center | refit_one_term | -5.01805e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.58752 | 0.912978-1.11586 (7/7) |
| BeH2_stretch125 | two_term_center | two_term | -5.02713e-06 | 7.72237e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.60974 | 0.912978-1.11586 (7/7) |
| BeH2_stretch125 | current_m3 | original_one_term | -2.95622e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.81204 | 0.919589-1.12394 (7/7) |
| BeH2_stretch125 | current_m3 | refit_one_term | -2.94885e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.81317 | 0.919589-1.12394 (7/7) |
| BeH2_stretch125 | current_m3 | two_term | -2.95665e-06 | 5.09358e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.85148 | 0.919589-1.12394 (7/7) |
| BeH2_stretch150 | two_term_center | original_one_term | -3.01944e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.80248 | 0.912744-1.11558 (7/7) |
| BeH2_stretch150 | two_term_center | refit_one_term | -3.01434e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.80324 | 0.912744-1.11558 (7/7) |
| BeH2_stretch150 | two_term_center | two_term | -3.01971e-06 | 3.53899e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.828 | 0.912744-1.11558 (7/7) |
| BeH2_stretch150 | current_m3 | original_one_term | -1.77583e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.05827 | 0.917716-1.12165 (7/7) |
| BeH2_stretch150 | current_m3 | refit_one_term | -1.77174e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.05946 | 0.917716-1.12165 (7/7) |
| BeH2_stretch150 | current_m3 | two_term | -1.77601e-06 | 2.16063e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.09879 | 0.917716-1.12165 (7/7) |
| H2O_stretch125 | two_term_center | original_one_term | -3.89786e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.950924 | 0.90824-1.11007 (7/7) |
| H2O_stretch125 | two_term_center | refit_one_term | -3.89423e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.951145 | 0.90824-1.11007 (7/7) |
| H2O_stretch125 | two_term_center | two_term | -3.89882e-05 | 1.08694e-06 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.95963 | 0.90824-1.11007 (7/7) |
| H2O_stretch125 | current_m3 | original_one_term | -2.29234e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.08588 | 0.913972-1.11708 (7/7) |
| H2O_stretch125 | current_m3 | refit_one_term | -2.28859e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.08633 | 0.913972-1.11708 (7/7) |
| H2O_stretch125 | current_m3 | two_term | -2.29304e-05 | 8.08166e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.10274 | 0.913972-1.11708 (7/7) |
| H2O_stretch150 | two_term_center | original_one_term | -1.66901e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.17554 | 0.909936-1.11214 (7/7) |
| H2O_stretch150 | two_term_center | refit_one_term | -1.66698e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.1759 | 0.909936-1.11214 (7/7) |
| H2O_stretch150 | two_term_center | two_term | -1.66933e-05 | 3.63733e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.18852 | 0.909936-1.11214 (7/7) |
| H2O_stretch150 | current_m3 | original_one_term | -9.81566e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.34237 | 0.916663-1.12037 (7/7) |
| H2O_stretch150 | current_m3 | refit_one_term | -9.79561e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.34306 | 0.916663-1.12037 (7/7) |
| H2O_stretch150 | current_m3 | two_term | -9.81801e-06 | 2.66349e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.36722 | 0.916663-1.12037 (7/7) |
| BeH2_stretch150_631g | two_term_center | original_one_term | -6.12312e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.68602 | 0.918711-1.12287 (7/7) |
| BeH2_stretch150_631g | two_term_center | refit_one_term | -6.10816e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.68766 | 0.918711-1.12287 (7/7) |
| BeH2_stretch150_631g | two_term_center | two_term | -6.12364e-07 | 4.59502e-09 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.74186 | 0.918711-1.12287 (7/7) |
| BeH2_stretch150_631g | current_m3 | original_one_term | -3.60122e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.06718 | 0.92731-1.13338 (7/7) |
| BeH2_stretch150_631g | current_m3 | refit_one_term | -3.58882e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.06983 | 0.92731-1.13338 (7/7) |
| BeH2_stretch150_631g | current_m3 | two_term | -3.60157e-07 | 2.90473e-09 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.16026 | 0.92731-1.13338 (7/7) |
| BeH2_stretch150_ccpvdz | two_term_center | original_one_term | -3.70975e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.0445 | 0.919589-1.12394 (7/7) |
| BeH2_stretch150_ccpvdz | two_term_center | refit_one_term | -3.69995e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.04652 | 0.919589-1.12394 (7/7) |
| BeH2_stretch150_ccpvdz | two_term_center | two_term | -3.70973e-07 | 2.26123e-09 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.11077 | 0.919589-1.12394 (7/7) |
| BeH2_stretch150_ccpvdz | current_m3 | original_one_term | -2.18198e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.47648 | 0.930879-1.13774 (7/7) |
| BeH2_stretch150_ccpvdz | current_m3 | refit_one_term | -2.17327e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.47996 | 0.930879-1.13774 (7/7) |
| BeH2_stretch150_ccpvdz | current_m3 | two_term | -2.18186e-07 | 1.52181e-09 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.59576 | 0.930879-1.13774 (7/7) |
| H2O_stretch150_631g | two_term_center | original_one_term | -1.26499e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.25988 | 0.906017-1.10735 (7/7) |
| H2O_stretch150_631g | two_term_center | refit_one_term | -1.26401e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.26013 | 0.906017-1.10735 (7/7) |
| H2O_stretch150_631g | two_term_center | two_term | -1.26511e-05 | 1.48378e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.26831 | 0.906017-1.10735 (7/7) |
| H2O_stretch150_631g | current_m3 | original_one_term | -7.43984e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.43867 | 0.908649-1.11057 (7/7) |
| H2O_stretch150_631g | current_m3 | refit_one_term | -7.43149e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.43907 | 0.908649-1.11057 (7/7) |
| H2O_stretch150_631g | current_m3 | two_term | -7.44068e-06 | 9.51023e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.4525 | 0.908649-1.11057 (7/7) |
| H2O_stretch150_ccpvdz | two_term_center | original_one_term | -1.19886e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.27691 | 0.906075-1.10743 (7/7) |
| H2O_stretch150_ccpvdz | two_term_center | refit_one_term | -1.19793e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.27716 | 0.906075-1.10743 (7/7) |
| H2O_stretch150_ccpvdz | two_term_center | two_term | -1.19898e-05 | 1.3832e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.28553 | 0.906075-1.10743 (7/7) |
| H2O_stretch150_ccpvdz | current_m3 | original_one_term | -7.05107e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.4581 | 0.90859-1.1105 (7/7) |
| H2O_stretch150_ccpvdz | current_m3 | refit_one_term | -7.04311e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.45852 | 0.90859-1.1105 (7/7) |
| H2O_stretch150_ccpvdz | current_m3 | two_term | -7.05171e-06 | 8.66609e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.47202 | 0.90859-1.1105 (7/7) |
| LiH_CAS2e4o | two_term_center | original_one_term | -4.16908e-08 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 5.25826 | 0.924268-1.12966 (7/7) |
| LiH_CAS2e4o | two_term_center | refit_one_term | -4.15351e-08 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 5.26318 | 0.924268-1.12966 (7/7) |
| LiH_CAS2e4o | two_term_center | two_term | -4.16675e-08 | 1.0261e-10 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 5.40005 | 0.924268-1.12966 (7/7) |
| LiH_CAS2e4o | current_m3 | original_one_term | -2.45083e-08 | 0 | 0.1,0.2,0.3 | 0.9,1,1.1,1.15,1.2 | 6.00516 | 0.965862 (1/5) |
| LiH_CAS2e4o | current_m3 | refit_one_term | -2.43329e-08 | 0 | 0.1,0.2,0.3 | 0.9,1,1.1,1.15,1.2 | 6.01595 | 0.965862 (1/5) |
| LiH_CAS2e4o | current_m3 | two_term | -2.45074e-08 | 1.03707e-10 | 0.1,0.2,0.3 | 0.9,1,1.1,1.15,1.2 | 6.44461 | 0.965862-1.07318 (2/5) |
| BeH2_CAS4e4o | two_term_center | original_one_term | -2.36936e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.40561 | 0.922864-1.12795 (7/7) |
| BeH2_CAS4e4o | two_term_center | refit_one_term | -2.36229e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.40815 | 0.922864-1.12795 (7/7) |
| BeH2_CAS4e4o | two_term_center | two_term | -2.36947e-07 | 1.32661e-09 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 3.49213 | 0.922864-1.12795 (7/7) |
| BeH2_CAS4e4o | current_m3 | original_one_term | -1.39347e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,1,1.025,1.05,1.075,1.1 | 3.88891 | 0.951822-1.05758 (3/7) |
| BeH2_CAS4e4o | current_m3 | refit_one_term | -1.38528e-07 | 0 | 0.1,0.2,0.3 | 0.9,0.95,1,1.025,1.05,1.075,1.1 | 3.89465 | 0.951822-1.08402 (4/7) |
| BeH2_CAS4e4o | current_m3 | two_term | -1.39361e-07 | 1.18102e-09 | 0.1,0.2,0.3 | 0.9,0.95,1,1.025,1.05,1.075,1.1 | 4.11283 | 0.951822-1.16334 (7/7) |
| BeH2_CAS4e5o | two_term_center | original_one_term | -2.30966e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.92737 | 0.915142-1.11851 (7/7) |
| BeH2_CAS4e5o | two_term_center | refit_one_term | -2.30507e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.92833 | 0.915142-1.11851 (7/7) |
| BeH2_CAS4e5o | two_term_center | two_term | -2.30989e-06 | 2.77849e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.9598 | 0.915142-1.11851 (7/7) |
| BeH2_CAS4e5o | current_m3 | original_one_term | -1.35834e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.2009 | 0.932283-1.13946 (7/7) |
| BeH2_CAS4e5o | current_m3 | refit_one_term | -1.353e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.20307 | 0.932283-1.13946 (7/7) |
| BeH2_CAS4e5o | current_m3 | two_term | -1.35856e-06 | 2.45613e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 2.27985 | 0.932283-1.13946 (7/7) |
| H2O_CAS8e5o | two_term_center | original_one_term | -1.83957e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.14729 | 0.908415-1.11028 (7/7) |
| H2O_CAS8e5o | two_term_center | refit_one_term | -1.83769e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.14758 | 0.908415-1.11028 (7/7) |
| H2O_CAS8e5o | two_term_center | two_term | -1.8399e-05 | 3.59309e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.15802 | 0.908415-1.11028 (7/7) |
| H2O_CAS8e5o | current_m3 | original_one_term | -1.08168e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.31017 | 0.929826-1.13645 (7/7) |
| H2O_CAS8e5o | current_m3 | refit_one_term | -1.07799e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.31129 | 0.929826-1.13645 (7/7) |
| H2O_CAS8e5o | current_m3 | two_term | -1.08214e-05 | 5.17089e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.35359 | 0.929826-1.13645 (7/7) |

## Accuracy and pass/fail

| condition | PF | model | R_max | eta_C(t_pred) | eta_min | eta_t | pass |
|---|---|---|---:|---:|---:|---:|---|
| BeH2_stretch125 | two_term_center | original_one_term | 0.0148111 | 0.00958955 | 0.000478989 | 0.014215 | True |
| BeH2_stretch125 | two_term_center | refit_one_term | 0.0142922 | 0.00919459 | 0.000451525 | 0.0138021 | True |
| BeH2_stretch125 | two_term_center | two_term | 8.47157e-05 | 5.47121e-05 | 0 | 0 | True |
| BeH2_stretch125 | current_m3 | original_one_term | 0.0234982 | 0.014421 | 0.00114569 | 0.0213014 | False |
| BeH2_stretch125 | current_m3 | refit_one_term | 0.022702 | 0.0138506 | 0.00108368 | 0.0206901 | False |
| BeH2_stretch125 | current_m3 | two_term | 0.000735194 | 0.000383818 | 0 | 0 | True |
| BeH2_stretch150 | two_term_center | original_one_term | 0.0145364 | 0.00943569 | 0.000462108 | 0.0139623 | True |
| BeH2_stretch150 | two_term_center | refit_one_term | 0.0140139 | 0.00903723 | 0.000434912 | 0.0135461 | True |
| BeH2_stretch150 | two_term_center | two_term | 0.000115423 | 6.91009e-05 | 0 | 0 | True |
| BeH2_stretch150 | current_m3 | original_one_term | 0.0207938 | 0.0129899 | 0.000909575 | 0.019305 | False |
| BeH2_stretch150 | current_m3 | refit_one_term | 0.020064 | 0.0124575 | 0.000858201 | 0.0187389 | False |
| BeH2_stretch150 | current_m3 | two_term | 0.000296618 | 0.000154552 | 0 | 0 | True |
| H2O_stretch125 | two_term_center | original_one_term | 0.00932564 | 0.00621597 | 0.000198062 | 0.00907195 | True |
| H2O_stretch125 | two_term_center | refit_one_term | 0.00904314 | 0.00599192 | 0.000188094 | 0.00884137 | True |
| H2O_stretch125 | two_term_center | two_term | 3.5849e-05 | 2.77632e-05 | 0 | 0 | True |
| H2O_stretch125 | current_m3 | original_one_term | 0.0168081 | 0.0106623 | 0.000615653 | 0.0152877 | False |
| H2O_stretch125 | current_m3 | refit_one_term | 0.0162987 | 0.0102794 | 0.000585318 | 0.0148846 | False |
| H2O_stretch125 | current_m3 | two_term | 0.000747555 | 0.000398296 | 0 | 0 | True |
| H2O_stretch150 | two_term_center | original_one_term | 0.0112685 | 0.00743192 | 0.000284506 | 0.0109194 | True |
| H2O_stretch150 | two_term_center | refit_one_term | 0.0108971 | 0.00714169 | 0.000269011 | 0.0106191 | True |
| H2O_stretch150 | two_term_center | two_term | 7.00065e-05 | 5.28638e-05 | 0 | 0 | True |
| H2O_stretch150 | current_m3 | original_one_term | 0.0207669 | 0.0127763 | 0.000915991 | 0.0181784 | False |
| H2O_stretch150 | current_m3 | refit_one_term | 0.0201232 | 0.012305 | 0.000870209 | 0.0176764 | False |
| H2O_stretch150 | current_m3 | two_term | 0.00150178 | 0.000733879 | 0 | 0 | True |
| BeH2_stretch150_631g | two_term_center | original_one_term | 0.0214762 | 0.0134099 | 0.000958044 | 0.0203666 | False |
| BeH2_stretch150_631g | two_term_center | refit_one_term | 0.0206995 | 0.0128469 | 0.000902245 | 0.0197674 | False |
| BeH2_stretch150_631g | two_term_center | two_term | 0.000201 | 0.000123393 | 0 | 0 | True |
| BeH2_stretch150_631g | current_m3 | original_one_term | 0.0332936 | 0.0193612 | 0.00215321 | 0.0294513 | False |
| BeH2_stretch150_631g | current_m3 | refit_one_term | 0.0321574 | 0.0185993 | 0.0020385 | 0.0286141 | False |
| BeH2_stretch150_631g | current_m3 | two_term | 0.00115853 | 0.00055996 | 0 | 0 | True |
| BeH2_stretch150_ccpvdz | two_term_center | original_one_term | 0.0226771 | 0.0140569 | 0.00106087 | 0.0213014 | False |
| BeH2_stretch150_ccpvdz | two_term_center | refit_one_term | 0.0218341 | 0.0134507 | 0.000997598 | 0.0206541 | False |
| BeH2_stretch150_ccpvdz | two_term_center | two_term | 0.000102896 | 7.92361e-05 | 0 | 0 | True |
| BeH2_stretch150_ccpvdz | current_m3 | original_one_term | 0.0392007 | 0.0219308 | 0.00288205 | 0.0331719 | False |
| BeH2_stretch150_ccpvdz | current_m3 | refit_one_term | 0.0378626 | 0.0210638 | 0.00273018 | 0.0322044 | False |
| BeH2_stretch150_ccpvdz | current_m3 | two_term | 0.00261485 | 0.0011901 | 0 | 0 | True |
| H2O_stretch150_631g | two_term_center | original_one_term | 0.00678882 | 0.00459772 | 0.000106777 | 0.00664061 | True |
| H2O_stretch150_631g | two_term_center | refit_one_term | 0.00655659 | 0.00440986 | 0.000100672 | 0.00644875 | True |
| H2O_stretch150_631g | two_term_center | two_term | 4.79098e-05 | 3.42315e-05 | 0 | 0 | True |
| H2O_stretch150_631g | current_m3 | original_one_term | 0.0104438 | 0.00681699 | 0.000247596 | 0.00951853 | True |
| H2O_stretch150_631g | current_m3 | refit_one_term | 0.0101025 | 0.00654795 | 0.000234197 | 0.00924052 | True |
| H2O_stretch150_631g | current_m3 | two_term | 0.0005502 | 0.000254827 | 0 | 0 | True |
| H2O_stretch150_ccpvdz | two_term_center | original_one_term | 0.00684993 | 0.0046403 | 0.00010861 | 0.00670474 | True |
| H2O_stretch150_ccpvdz | two_term_center | refit_one_term | 0.00661717 | 0.00445211 | 0.00010244 | 0.00651251 | True |
| H2O_stretch150_ccpvdz | two_term_center | two_term | 5.86643e-05 | 3.85989e-05 | 0 | 0 | True |
| H2O_stretch150_ccpvdz | current_m3 | original_one_term | 0.010305 | 0.00673126 | 0.000240959 | 0.00945475 | True |
| H2O_stretch150_ccpvdz | current_m3 | refit_one_term | 0.00996186 | 0.00646057 | 0.000227671 | 0.00917518 | True |
| H2O_stretch150_ccpvdz | current_m3 | two_term | 0.000531408 | 0.000244298 | 0 | 0 | True |
| LiH_CAS2e4o | two_term_center | original_one_term | 0.0344283 | 0.0193626 | 0.00231862 | 0.026257 | False |
| LiH_CAS2e4o | two_term_center | refit_one_term | 0.0332124 | 0.0185421 | 0.00218856 | 0.0253461 | False |
| LiH_CAS2e4o | two_term_center | two_term | 0.00596183 | 0.00288445 | 0 | 0 | True |
| LiH_CAS2e4o | current_m3 | original_one_term | 0.503905 | 0.053125 | 0.457946 | 0.223492 | False |
| LiH_CAS2e4o | current_m3 | refit_one_term | 0.499968 | 0.0520195 | 0.45686 | 0.222096 | False |
| LiH_CAS2e4o | current_m3 | two_term | 0.364667 | 0.0328863 | 0.418222 | 0.166667 | False |
| BeH2_CAS4e4o | two_term_center | original_one_term | 0.0287421 | 0.0170429 | 0.00167103 | 0.0247756 | False |
| BeH2_CAS4e4o | two_term_center | refit_one_term | 0.0277761 | 0.0163732 | 0.00158245 | 0.0240467 | False |
| BeH2_CAS4e4o | two_term_center | two_term | 0.00201123 | 0.00104102 | 0 | 0 | True |
| BeH2_CAS4e4o | current_m3 | original_one_term | 0.0831695 | 0.0375805 | 0.0122967 | 0.0775074 | False |
| BeH2_CAS4e4o | current_m3 | refit_one_term | 0.081015 | 0.0364684 | 0.0118896 | 0.0761459 | False |
| BeH2_CAS4e4o | current_m3 | two_term | 0.0196617 | 0.00975753 | 0.00152552 | 0.0243902 | True |
| BeH2_CAS4e5o | two_term_center | original_one_term | 0.0180585 | 0.0114186 | 0.000702652 | 0.0165466 | False |
| BeH2_CAS4e5o | two_term_center | refit_one_term | 0.0174363 | 0.0109552 | 0.000663457 | 0.0160573 | False |
| BeH2_CAS4e5o | two_term_center | two_term | 0.000588484 | 0.000315723 | 0 | 0 | True |
| BeH2_CAS4e5o | current_m3 | original_one_term | 0.0435615 | 0.0238795 | 0.00355005 | 0.0346279 | False |
| BeH2_CAS4e5o | current_m3 | refit_one_term | 0.0422372 | 0.023041 | 0.00338485 | 0.0336776 | False |
| BeH2_CAS4e5o | current_m3 | two_term | 0.00527448 | 0.00280356 | 0 | 0 | True |
| H2O_CAS8e5o | two_term_center | original_one_term | 0.011229 | 0.00718482 | 0.000285665 | 0.00926339 | True |
| H2O_CAS8e5o | two_term_center | refit_one_term | 0.0109187 | 0.00694095 | 0.000272438 | 0.00901033 | True |
| H2O_CAS8e5o | two_term_center | two_term | 0.00165092 | 0.000874114 | 0 | 0 | True |
| H2O_CAS8e5o | current_m3 | original_one_term | 0.0472206 | 0.0248706 | 0.00436586 | 0.0556848 | False |
| H2O_CAS8e5o | current_m3 | refit_one_term | 0.0460845 | 0.0241565 | 0.00420931 | 0.0548791 | False |
| H2O_CAS8e5o | current_m3 | two_term | 0.0120059 | 0.00610384 | 0.000282832 | 0.0243902 | True |

## Pass counts

- two_term_center:
  - original_one_term: 7/12
  - refit_one_term: 7/12
  - two_term: 12/12
- current_m3:
  - original_one_term: 2/12
  - refit_one_term: 2/12
  - two_term: 11/12

Original one-term failed but two-term passed: [{'condition': 'BeH2_stretch125', 'formula': 'current_m3'}, {'condition': 'BeH2_stretch150', 'formula': 'current_m3'}, {'condition': 'H2O_stretch125', 'formula': 'current_m3'}, {'condition': 'H2O_stretch150', 'formula': 'current_m3'}, {'condition': 'BeH2_stretch150_631g', 'formula': 'two_term_center'}, {'condition': 'BeH2_stretch150_631g', 'formula': 'current_m3'}, {'condition': 'BeH2_stretch150_ccpvdz', 'formula': 'two_term_center'}, {'condition': 'BeH2_stretch150_ccpvdz', 'formula': 'current_m3'}, {'condition': 'LiH_CAS2e4o', 'formula': 'two_term_center'}, {'condition': 'BeH2_CAS4e4o', 'formula': 'two_term_center'}, {'condition': 'BeH2_CAS4e4o', 'formula': 'current_m3'}, {'condition': 'BeH2_CAS4e5o', 'formula': 'two_term_center'}, {'condition': 'BeH2_CAS4e5o', 'formula': 'current_m3'}, {'condition': 'H2O_CAS8e5o', 'formula': 'current_m3'}]
Refitted one-term failed but two-term passed: [{'condition': 'BeH2_stretch125', 'formula': 'current_m3'}, {'condition': 'BeH2_stretch150', 'formula': 'current_m3'}, {'condition': 'H2O_stretch125', 'formula': 'current_m3'}, {'condition': 'H2O_stretch150', 'formula': 'current_m3'}, {'condition': 'BeH2_stretch150_631g', 'formula': 'two_term_center'}, {'condition': 'BeH2_stretch150_631g', 'formula': 'current_m3'}, {'condition': 'BeH2_stretch150_ccpvdz', 'formula': 'two_term_center'}, {'condition': 'BeH2_stretch150_ccpvdz', 'formula': 'current_m3'}, {'condition': 'LiH_CAS2e4o', 'formula': 'two_term_center'}, {'condition': 'BeH2_CAS4e4o', 'formula': 'two_term_center'}, {'condition': 'BeH2_CAS4e4o', 'formula': 'current_m3'}, {'condition': 'BeH2_CAS4e5o', 'formula': 'two_term_center'}, {'condition': 'BeH2_CAS4e5o', 'formula': 'current_m3'}, {'condition': 'H2O_CAS8e5o', 'formula': 'current_m3'}]

## PF direct-cost comparison

These ratios compare the new PF with current_m3 at each PF's own two-term predicted optimum. They are separate from model accuracy.

| condition | direct cost ratio new/current |
|---|---:|
| BeH2_stretch125 | 1.14814 |
| BeH2_stretch150 | 1.14644 |
| H2O_stretch125 | 1.14745 |
| H2O_stretch150 | 1.1487 |
| BeH2_stretch150_631g | 1.14998 |
| BeH2_stretch150_ccpvdz | 1.15285 |
| H2O_stretch150_631g | 1.14459 |
| H2O_stretch150_ccpvdz | 1.14443 |
| LiH_CAS2e4o | 1.21011 |
| BeH2_CAS4e4o | 1.17554 |
| BeH2_CAS4e5o | 1.15928 |
| H2O_CAS8e5o | 1.16643 |

## Conclusion

Category 3: Adding the t^6 term is required to stabilize declared coverage or prediction accuracy on these holdouts.

Conclusions apply only to the eight frozen-core symmetric-stretch holdouts (STO-3G, 6-31G, or cc-pVDZ as declared) and four nested active-space holdouts evaluated here; they are not a claim for arbitrary molecules or continuous time.

eta_t and eta_min use the frozen saved local grid and do not establish a continuous optimum.
