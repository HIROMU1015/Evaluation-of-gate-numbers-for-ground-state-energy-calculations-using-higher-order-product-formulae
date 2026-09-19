# Full-electron NH3 higher-term diagnosis

Status: complete

## Main conclusion

Category 3: No PF passes both geometries even with the three-term model; the low-order polynomial model or coefficient search must be revisited.

## Passes on both geometries

| model | passing PFs |
|---|---|
| one_term | none |
| two_term | none |
| three_term | none |
| legacy_two_term_0p1_0p3 | none |

## Per-condition metrics

| geometry | PF | model | pass | eta* | eta_min | eta_t | max residual/eps | direct cost at predicted time | stages | rotations |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| equilibrium | yoshida4 | n/a | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| equilibrium | paper_new4 | n/a | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| equilibrium | m5_best | n/a | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| equilibrium | two_term_center | one_term | False | 0.00991205 | 0.00803019 | 0.0909091 | 0.0564941 | 2.9461487e+09 | 7 | 85900 |
| equilibrium | two_term_center | two_term | False | n/a | n/a | 0.0526316 | 2.22746 | n/a | 7 | 85900 |
| equilibrium | two_term_center | three_term | False | 0.219054 | 0.0038307 | 0.130435 | 0.64617 | 2.9258693e+09 | 7 | 85900 |
| equilibrium | two_term_center | legacy_two_term_0p1_0p3 | False | n/a | n/a | n/a | 1.91552 | n/a | 7 | 85900 |
| equilibrium | joint_refine_r0_s0046 | one_term | False | 0.01379 | 0 | 0 | 0.0275795 | 6.5325301e+09 | 7 | 85900 |
| equilibrium | joint_refine_r0_s0046 | two_term | True | 7.38929e-05 | 0 | 0 | 6.23829e-05 | 6.5244559e+09 | 7 | 85900 |
| equilibrium | joint_refine_r0_s0046 | three_term | True | 0.000100696 | 0 | 0 | 0.000515717 | 6.5244572e+09 | 7 | 85900 |
| equilibrium | joint_refine_r0_s0046 | legacy_two_term_0p1_0p3 | True | 0.00010299 | 0 | 0 | 9.38278e-05 | 6.5244559e+09 | 7 | 85900 |
| equilibrium | yoshida6_m3 | n/a | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| stretch150 | yoshida4 | one_term | False | 0.022349 | 0.0033196 | 0.047619 | 0.0443154 | 3.2106001e+09 | 3 | 35560 |
| stretch150 | yoshida4 | two_term | True | 0.000825267 | 0 | 0 | 0.00196262 | 3.1994829e+09 | 3 | 35560 |
| stretch150 | yoshida4 | three_term | True | 0.000184889 | 0 | 0 | 0.000748725 | 3.1994642e+09 | 3 | 35560 |
| stretch150 | yoshida4 | legacy_two_term_0p1_0p3 | True | 0.00115781 | 0 | 0 | 0.00258832 | 3.1994983e+09 | 3 | 35560 |
| stretch150 | paper_new4 | n/a | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| stretch150 | m5_best | n/a | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| stretch150 | two_term_center | one_term | False | 0.717875 | 2.88375 | 0.0526316 | 0.974288 | 7.6976499e+09 | 7 | 82792 |
| stretch150 | two_term_center | two_term | False | 0.115276 | 0.121103 | 0.130435 | 0.261863 | 2.3717264e+09 | 7 | 82792 |
| stretch150 | two_term_center | three_term | False | 0.0832803 | 0.12991 | 0.130435 | 0.306238 | 2.6768327e+09 | 7 | 82792 |
| stretch150 | two_term_center | legacy_two_term_0p1_0p3 | False | 0.356212 | 0.042069 | 0.047619 | 1.94937 | 1.9702518e+09 | 7 | 82792 |
| stretch150 | joint_refine_r0_s0046 | one_term | False | 0.035671 | 0.0291889 | 0.047619 | 0.0552196 | 4.2134852e+09 | 7 | 82792 |
| stretch150 | joint_refine_r0_s0046 | two_term | False | 0.0262218 | 0.0072121 | 0.111111 | 0.0205209 | 4.3245424e+09 | 7 | 82792 |
| stretch150 | joint_refine_r0_s0046 | three_term | False | 0.000431594 | 0.00783352 | 0.0526316 | 0.0111932 | 4.2144226e+09 | 7 | 82792 |
| stretch150 | joint_refine_r0_s0046 | legacy_two_term_0p1_0p3 | False | 0.0167342 | 0.0211791 | 0.0526316 | 0.0130922 | 4.2810466e+09 | 7 | 82792 |
| stretch150 | yoshida6_m3 | n/a | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

PF direct cost and model prediction accuracy are reported separately.
The legacy two-term model uses only 0.1, 0.2, and 0.3 t_ana.
All other direct models use 0.1 through 0.5 t_ana.
