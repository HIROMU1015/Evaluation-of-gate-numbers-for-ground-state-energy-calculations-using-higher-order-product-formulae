# One-term versus two-term m=3 PF error models

Source result commit: 92df2dbda9de5f41183af551b7acec06d88a3ada
Pre-validation baseline: d2360f49f9a754d1850eab60cd483f684bd8bffb

All models use the same three training points (0.1, 0.2, 0.3) t_ana. Those points are excluded from validation. The primary unseen set is the same seven saved local direct points for all three models.

The refitted one-term model uses the same normalized least-squares objective as the stored two-term model. Therefore the comparison isolates the effect of adding the t^6 term.

Before accepting added schedule points, each saved two-term optimum was recomputed as a reproduction sentinel. 10 sentinels passed; the maximum signed-shift difference was 7.84523e-15 Ha and the maximum direct-cost relative difference was 6.17142e-11.

Exact grouping-structure hashes, active-space metadata, dimensions, and energies were gated. The coefficient-inclusive hash may differ when rerunning SCF because of last-bit floating-point variation; the direct sentinel is the additional numerical equivalence check.

## Model coefficients and predicted schedules

| condition | PF | model | a4 | a6 | train t/t_ana | unseen t/t_* | t_pred | sampled accepted t/t_ana |
|---|---|---|---:|---:|---|---|---:|---|
| H6 | two_term_center | original_one_term | -3.32008e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.989841 | 0.913329-1.11629 (7/7) |
| H6 | two_term_center | refit_one_term | -3.31506e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.990215 | 0.913329-1.11629 (7/7) |
| H6 | two_term_center | two_term | -3.32124e-05 | 1.35093e-06 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.0045 | 0.913329-1.11629 (7/7) |
| H6 | current_m3 | original_one_term | -1.9525e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.13033 | 0.922864-1.12795 (7/7) |
| H6 | current_m3 | refit_one_term | -1.94743e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.13106 | 0.922864-1.12795 (7/7) |
| H6 | current_m3 | two_term | -1.95337e-05 | 9.96695e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.15904 | 0.922864-1.12795 (7/7) |
| H7 | two_term_center | original_one_term | -2.80199e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.03273 | 0.913563-1.11658 (7/7) |
| H7 | two_term_center | refit_one_term | -2.79762e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.03313 | 0.913563-1.11658 (7/7) |
| H7 | two_term_center | two_term | -2.80292e-05 | 1.06478e-06 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.04829 | 0.913563-1.11658 (7/7) |
| H7 | current_m3 | original_one_term | -1.64785e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.1793 | 0.92304-1.12816 (7/7) |
| H7 | current_m3 | refit_one_term | -1.64346e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.18008 | 0.92304-1.12816 (7/7) |
| H7 | current_m3 | two_term | -1.6485e-05 | 7.76966e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.20949 | 0.92304-1.12816 (7/7) |
| NH3_sto3g | two_term_center | original_one_term | -8.942e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.772669 | 0.906309-1.10771 (7/7) |
| NH3_sto3g | two_term_center | refit_one_term | -8.93635e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.772791 | 0.906309-1.10771 (7/7) |
| NH3_sto3g | two_term_center | two_term | -8.94457e-05 | 2.94887e-06 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.778086 | 0.906309-1.10771 (7/7) |
| NH3_sto3g | current_m3 | original_one_term | -5.25845e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.882344 | 0.912744-1.11558 (7/7) |
| NH3_sto3g | current_m3 | refit_one_term | -5.25132e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.882643 | 0.912744-1.11558 (7/7) |
| NH3_sto3g | current_m3 | two_term | -5.26072e-05 | 2.58794e-06 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 0.894838 | 0.912744-1.11558 (7/7) |
| NH3_631g | two_term_center | original_one_term | -1.15223e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.28964 | 0.905548-1.10678 (7/7) |
| NH3_631g | two_term_center | refit_one_term | -1.15143e-05 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.28986 | 0.905548-1.10678 (7/7) |
| NH3_631g | two_term_center | two_term | -1.15235e-05 | 1.18921e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.29759 | 0.905548-1.10678 (7/7) |
| NH3_631g | current_m3 | original_one_term | -6.77611e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.47268 | 0.917015-1.1208 (7/7) |
| NH3_631g | current_m3 | refit_one_term | -6.76166e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.47346 | 0.917015-1.1208 (7/7) |
| NH3_631g | current_m3 | two_term | -6.77743e-06 | 1.55738e-07 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.50052 | 0.917015-1.1208 (7/7) |
| NH3_ccpvdz | two_term_center | original_one_term | -7.76766e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.42325 | 0.904554-1.10557 (7/7) |
| NH3_ccpvdz | two_term_center | refit_one_term | -7.76304e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.42346 | 0.904554-1.10557 (7/7) |
| NH3_ccpvdz | two_term_center | two_term | -7.76814e-06 | 5.40348e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.43045 | 0.904554-1.10557 (7/7) |
| NH3_ccpvdz | current_m3 | original_one_term | -4.56799e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.62525 | 0.916839-1.12058 (7/7) |
| NH3_ccpvdz | current_m3 | refit_one_term | -4.55829e-06 | 0 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.62612 | 0.916839-1.12058 (7/7) |
| NH3_ccpvdz | current_m3 | two_term | -4.56882e-06 | 8.54092e-08 | 0.1,0.2,0.3 | 0.9,0.95,0.975,1,1.025,1.05,1.1 | 1.65566 | 0.916839-1.12058 (7/7) |

## Accuracy and pass/fail

| condition | PF | model | R_max | eta_C(t_pred) | eta_min | eta_t | pass |
|---|---|---|---:|---:|---:|---:|---|
| H6 | two_term_center | original_one_term | 0.0153894 | 0.00990068 | 0.00051669 | 0.0145939 | True |
| H6 | two_term_center | refit_one_term | 0.0149204 | 0.00954516 | 0.000490951 | 0.0142215 | True |
| H6 | two_term_center | two_term | 7.01393e-05 | 2.58686e-05 | 0 | 0 | True |
| H6 | current_m3 | original_one_term | 0.0282326 | 0.0169842 | 0.00167839 | 0.0247756 | False |
| H6 | current_m3 | refit_one_term | 0.0273925 | 0.0164021 | 0.00160119 | 0.0241418 | False |
| H6 | current_m3 | two_term | 0.00151566 | 0.00102 | 0 | 0 | True |
| H7 | two_term_center | original_one_term | 0.0156465 | 0.0100524 | 0.000532958 | 0.0148463 | False |
| H7 | two_term_center | refit_one_term | 0.0151617 | 0.00968568 | 0.000505988 | 0.0144619 | True |
| H7 | two_term_center | two_term | 4.14805e-05 | 5.89684e-06 | 0 | 0 | True |
| H7 | current_m3 | original_one_term | 0.0290102 | 0.017103 | 0.00171846 | 0.024961 | False |
| H7 | current_m3 | refit_one_term | 0.0281475 | 0.0165062 | 0.00163867 | 0.0243108 | False |
| H7 | current_m3 | two_term | 0.00210023 | 0.0010589 | 0 | 0 | True |
| NH3_sto3g | two_term_center | original_one_term | 0.0073078 | 0.00491095 | 0.000124108 | 0.0069612 | True |
| NH3_sto3g | two_term_center | refit_one_term | 0.0071177 | 0.00475772 | 0.000118716 | 0.00680441 | True |
| NH3_sto3g | two_term_center | two_term | 0.000119954 | 6.47358e-05 | 0 | 0 | True |
| NH3_sto3g | current_m3 | original_one_term | 0.0154908 | 0.00987635 | 0.000529306 | 0.0139623 | True |
| NH3_sto3g | current_m3 | refit_one_term | 0.0150706 | 0.00955739 | 0.000505864 | 0.0136277 | True |
| NH3_sto3g | current_m3 | two_term | 0.000853922 | 0.00046093 | 0 | 0 | True |
| NH3_631g | two_term_center | original_one_term | 0.00702661 | 0.00462232 | 0.000115519 | 0.00612723 | True |
| NH3_631g | two_term_center | refit_one_term | 0.00681667 | 0.0044524 | 0.00010972 | 0.00595333 | True |
| NH3_631g | two_term_center | two_term | 0.000746744 | 0.000378528 | 0 | 0 | True |
| NH3_631g | current_m3 | original_one_term | 0.0247635 | 0.0147425 | 0.00122376 | 0.0185542 | False |
| NH3_631g | current_m3 | refit_one_term | 0.0240905 | 0.0142627 | 0.00116299 | 0.0180303 | False |
| NH3_631g | current_m3 | two_term | 0.00506323 | 0.00270511 | 0 | 0 | True |
| NH3_ccpvdz | two_term_center | original_one_term | 0.00598949 | 0.00397877 | 9.07847e-05 | 0.00503453 | True |
| NH3_ccpvdz | two_term_center | refit_one_term | 0.00581179 | 0.00383387 | 8.63954e-05 | 0.00488654 | True |
| NH3_ccpvdz | two_term_center | two_term | 0.000862127 | 0.000499135 | 0 | 0 | True |
| NH3_ccpvdz | current_m3 | original_one_term | 0.0401079 | 0.0150719 | 0.00152758 | 0.0183664 | False |
| NH3_ccpvdz | current_m3 | refit_one_term | 0.0394381 | 0.0145971 | 0.00146377 | 0.0178444 | False |
| NH3_ccpvdz | current_m3 | two_term | 0.0206075 | 0.00346067 | 0 | 0 | True |

## Pass counts

- two_term_center:
  - original_one_term: 4/5
  - refit_one_term: 5/5
  - two_term: 5/5
- current_m3:
  - original_one_term: 1/5
  - refit_one_term: 1/5
  - two_term: 5/5

Original one-term failed but two-term passed: [{'condition': 'H6', 'formula': 'current_m3'}, {'condition': 'H7', 'formula': 'two_term_center'}, {'condition': 'H7', 'formula': 'current_m3'}, {'condition': 'NH3_631g', 'formula': 'current_m3'}, {'condition': 'NH3_ccpvdz', 'formula': 'current_m3'}]
Refitted one-term failed but two-term passed: [{'condition': 'H6', 'formula': 'current_m3'}, {'condition': 'H7', 'formula': 'current_m3'}, {'condition': 'NH3_631g', 'formula': 'current_m3'}, {'condition': 'NH3_ccpvdz', 'formula': 'current_m3'}]

## PF direct-cost comparison

These ratios compare the new PF with current_m3 at each PF's own two-term predicted optimum. They are separate from model accuracy.

| condition | direct cost ratio new/current |
|---|---:|
| H6 | 1.15127 |
| H7 | 1.15126 |
| NH3_sto3g | 1.14805 |
| NH3_631g | 1.15471 |
| NH3_ccpvdz | 1.15621 |

## Conclusion

Category 3: Adding the t^6 term is required to stabilize declared coverage or prediction accuracy on these holdouts.

Conclusions apply only to H6/H7 and NH3 in three bases over the saved finite-time neighborhood; they are not a claim for arbitrary molecules or continuous time.

eta_t and eta_min use the frozen saved local grid and do not establish a continuous optimum.
