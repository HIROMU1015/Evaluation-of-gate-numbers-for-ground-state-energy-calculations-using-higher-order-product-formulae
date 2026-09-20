# Existing-PF unified finite-time NH3 comparison

Status: complete

This is a development comparison on the NH3 data used to select the short-time grid; it is not an independent hold-out.

## Main result

The following fixed PF/model pairs pass all four conditions: yoshida4 (two_term, three_term), yoshida6_m3 (three_term)

## Fixed-model predictability and cost

| PF | best fixed model | conditions passed | all four | active both | full-electron both | post-hoc per-condition selection | mean cost/m5 | worst cost/m5 | Pareto |
|---|---|---:|---:|---|---|---:|---:|---:|---:|
| yoshida4 | two_term | 4/4 | True | short_time_asymptotic_one_term, direct_refit_one_term, two_term, three_term | two_term, three_term | True | 3.1552 | 3.6717 | True |
| paper_new4 | two_term | 2/4 | False | two_term, three_term | none | False | 1.7478 | 2.0599 | False |
| m5_best | short_time_asymptotic_one_term | 0/4 | False | none | none | False | 1 | 1 | True |
| current_m3 | two_term | 2/4 | False | two_term, three_term | none | False | 1.4973 | 1.9258 | True |
| two_term_center | direct_refit_one_term | 2/4 | False | direct_refit_one_term, two_term, three_term | none | False | 1.8515 | 2.2178 | False |
| joint_refine_r0_s0046 | two_term | 3/4 | False | short_time_asymptotic_one_term, direct_refit_one_term, two_term, three_term | none | False | 4.1339 | 4.8787 | False |
| yoshida6_m3 | three_term | 4/4 | True | short_time_asymptotic_one_term, direct_refit_one_term, two_term, three_term | three_term | True | 3.518 | 4.1568 | False |
| morales_y8m10b | short_time_asymptotic_one_term | 0/4 | False | none | none | False | 1.7458 | 2.1747 | False |

## Per-condition model checks

| condition | PF | model | fine | pass | stable | eta* | eta_min | eta_t | max residual/eps | cond(X) | direct-grid min cost |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| active_equilibrium | yoshida4 | short_time_asymptotic_one_term | True | True | True | 0.0021239 | 0 | 0 | 0.0030177 | 1 | 1.0655509e+09 |
| active_equilibrium | yoshida4 | direct_refit_one_term | True | True | True | 0.0016591 | 0 | 0 | 0.0024747 | 1 | 1.0655443e+09 |
| active_equilibrium | yoshida4 | two_term | True | True | True | 4.8461e-06 | 0 | 0 | 9.0403e-06 | 29.209 | 1.0655268e+09 |
| active_equilibrium | yoshida4 | three_term | True | True | True | 2.3727e-06 | 0 | 0 | 4.4338e-06 | 875.1 | 1.0655268e+09 |
| active_equilibrium | paper_new4 | short_time_asymptotic_one_term | False | False | True | 0.013842 | 0 | 0 | 0.025796 | 1 | 6.0344828e+08 |
| active_equilibrium | paper_new4 | direct_refit_one_term | False | False | True | 0.010892 | 0 | 0 | 0.021795 | 1 | 6.0327608e+08 |
| active_equilibrium | paper_new4 | two_term | True | True | True | 0.00020247 | 0 | 0 | 0.00038067 | 29.209 | 6.0281993e+08 |
| active_equilibrium | paper_new4 | three_term | True | True | True | 1.3599e-05 | 0 | 0 | 3.2067e-05 | 875.1 | 6.0281967e+08 |
| active_equilibrium | m5_best | short_time_asymptotic_one_term | False | False | True | 0.07425 | 0.13583 | 0.13043 | 0.19861 | 1 | 3.9830623e+08 |
| active_equilibrium | m5_best | direct_refit_one_term | False | False | True | 0.065707 | 0.27972 | 0.13043 | 0.29853 | 1 | 3.5113795e+08 |
| active_equilibrium | m5_best | two_term | False | False | True | n/a | n/a | n/a | 8.6207 | 29.209 | n/a |
| active_equilibrium | m5_best | three_term | False | False | True | n/a | n/a | 0.17647 | 6.5539 | 875.1 | 3.2541789e+08 |
| active_equilibrium | current_m3 | short_time_asymptotic_one_term | True | True | True | 0.0098816 | 0.00047571 | 0.019608 | 0.014209 | 1 | 5.6229995e+08 |
| active_equilibrium | current_m3 | direct_refit_one_term | True | True | True | 0.0078377 | 0.00037162 | 0.009901 | 0.011851 | 1 | 5.6227993e+08 |
| active_equilibrium | current_m3 | two_term | True | True | True | 0.00037806 | 0 | 0 | 0.00073411 | 29.209 | 5.6226929e+08 |
| active_equilibrium | current_m3 | three_term | True | True | True | 5.7899e-05 | 0 | 0 | 0.00014137 | 875.1 | 5.6226842e+08 |
| active_equilibrium | two_term_center | short_time_asymptotic_one_term | True | True | True | 0.0049996 | 0.00010904 | 0.009901 | 0.0071075 | 1 | 6.4552521e+08 |
| active_equilibrium | two_term_center | direct_refit_one_term | True | True | True | 0.0038543 | 5.0701e-05 | 0.009901 | 0.0057751 | 1 | 6.45538e+08 |
| active_equilibrium | two_term_center | two_term | True | True | True | 5.4137e-05 | 0 | 0 | 0.00010454 | 29.209 | 6.4551341e+08 |
| active_equilibrium | two_term_center | three_term | True | True | True | 7.4296e-06 | 0 | 0 | 1.7724e-05 | 875.1 | 6.4551339e+08 |
| active_equilibrium | joint_refine_r0_s0046 | short_time_asymptotic_one_term | True | True | True | 0.0026824 | 0 | 0 | 0.0038023 | 1 | 1.4175701e+09 |
| active_equilibrium | joint_refine_r0_s0046 | direct_refit_one_term | True | True | True | 0.0020709 | 0 | 0 | 0.0030885 | 1 | 1.4175554e+09 |
| active_equilibrium | joint_refine_r0_s0046 | two_term | True | True | True | 7.3836e-06 | 0 | 0 | 1.3746e-05 | 29.209 | 1.4175192e+09 |
| active_equilibrium | joint_refine_r0_s0046 | three_term | True | True | True | 5.462e-07 | 0 | 0 | 1.0164e-06 | 875.1 | 1.4175192e+09 |
| active_equilibrium | yoshida6_m3 | short_time_asymptotic_one_term | True | True | True | 0.0075364 | 0.00034798 | 0.009901 | 0.013842 | 1 | 8.9662882e+08 |
| active_equilibrium | yoshida6_m3 | direct_refit_one_term | True | True | True | 0.0059106 | 0.00023569 | 0.009901 | 0.011406 | 1 | 8.9663511e+08 |
| active_equilibrium | yoshida6_m3 | two_term | True | True | True | 0.00013603 | 0 | 0 | 0.00032792 | 45.797 | 8.9662881e+08 |
| active_equilibrium | yoshida6_m3 | three_term | True | True | True | 1.0198e-05 | 0 | 0 | 2.5139e-05 | 2269 | 8.9662862e+08 |
| active_equilibrium | morales_y8m10b | n/a | False | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| active_stretch150 | yoshida4 | short_time_asymptotic_one_term | True | True | True | 0.0067031 | 0.00022702 | 0.009901 | 0.0094635 | 1 | 6.9432558e+08 |
| active_stretch150 | yoshida4 | direct_refit_one_term | True | True | True | 0.0051923 | 0.00015294 | 0.009901 | 0.0077088 | 1 | 6.94331e+08 |
| active_stretch150 | yoshida4 | two_term | True | True | True | 0.00012101 | 0 | 0 | 0.00022348 | 29.209 | 6.9432558e+08 |
| active_stretch150 | yoshida4 | three_term | True | True | True | 5.2341e-07 | 0 | 0 | 2.0951e-06 | 875.1 | 6.9432548e+08 |
| active_stretch150 | paper_new4 | short_time_asymptotic_one_term | False | False | True | 0.024808 | 0.0034214 | 0.047619 | 0.045827 | 1 | 3.8958169e+08 |
| active_stretch150 | paper_new4 | direct_refit_one_term | False | False | True | 0.019667 | 0.0021588 | 0.047619 | 0.039039 | 1 | 3.8970435e+08 |
| active_stretch150 | paper_new4 | two_term | True | True | True | 0.00012755 | 0 | 0 | 0.00020934 | 29.209 | 3.8952251e+08 |
| active_stretch150 | paper_new4 | three_term | True | True | True | 4.8398e-05 | 0 | 0 | 0.000112 | 875.1 | 3.8952246e+08 |
| active_stretch150 | m5_best | short_time_asymptotic_one_term | True | False | True | 0.20341 | 0.094364 | 0.090909 | 0.25061 | 1 | 2.4157403e+08 |
| active_stretch150 | m5_best | direct_refit_one_term | True | False | True | 0.12257 | 0.084739 | 0.074074 | 0.47057 | 1 | 2.5511604e+08 |
| active_stretch150 | m5_best | two_term | False | False | True | 0.97824 | 29.412 | 0.13043 | 7.885 | 29.209 | 2.4071379e+08 |
| active_stretch150 | m5_best | three_term | True | False | True | 0.39999 | 0.63201 | 0.020408 | 6.1152 | 875.1 | 1.8910108e+08 |
| active_stretch150 | current_m3 | short_time_asymptotic_one_term | False | False | True | 0.019342 | 0.0013642 | 0.047619 | 0.036261 | 1 | 3.6445135e+08 |
| active_stretch150 | current_m3 | direct_refit_one_term | False | False | True | 0.015322 | 0.00034396 | 0.047619 | 0.030911 | 1 | 3.6461641e+08 |
| active_stretch150 | current_m3 | two_term | True | True | True | 0.00030721 | 0 | 0 | 0.00072321 | 29.209 | 3.6417167e+08 |
| active_stretch150 | current_m3 | three_term | True | True | True | 0.00018289 | 0 | 0 | 0.00049557 | 875.1 | 3.6417135e+08 |
| active_stretch150 | two_term_center | short_time_asymptotic_one_term | False | False | True | 0.012254 | 0 | 0 | 0.022488 | 1 | 4.1971239e+08 |
| active_stretch150 | two_term_center | direct_refit_one_term | True | True | True | 0.0094187 | 0.00049465 | 0.019608 | 0.014001 | 1 | 4.1940609e+08 |
| active_stretch150 | two_term_center | two_term | True | True | True | 0.00020146 | 0 | 0 | 0.00035788 | 29.209 | 4.1938484e+08 |
| active_stretch150 | two_term_center | three_term | True | True | True | 2.6132e-05 | 0 | 0 | 6.2636e-05 | 875.1 | 4.1938468e+08 |
| active_stretch150 | joint_refine_r0_s0046 | short_time_asymptotic_one_term | True | True | True | 0.0083725 | 0.000344 | 0.009901 | 0.011802 | 1 | 9.2258156e+08 |
| active_stretch150 | joint_refine_r0_s0046 | direct_refit_one_term | True | True | True | 0.0064637 | 0.00025009 | 0.009901 | 0.0095903 | 1 | 9.2257025e+08 |
| active_stretch150 | joint_refine_r0_s0046 | two_term | True | True | True | 0.00017092 | 0 | 0 | 0.00031482 | 29.209 | 9.2257039e+08 |
| active_stretch150 | joint_refine_r0_s0046 | three_term | True | True | True | 5.0182e-06 | 0 | 0 | 1.1301e-05 | 875.1 | 9.225701e+08 |
| active_stretch150 | yoshida6_m3 | short_time_asymptotic_one_term | True | True | True | 0.0088151 | 0.00046097 | 0.009901 | 0.01611 | 1 | 6.1584417e+08 |
| active_stretch150 | yoshida6_m3 | direct_refit_one_term | True | True | True | 0.0067552 | 0.00031776 | 0.009901 | 0.01303 | 1 | 6.1583584e+08 |
| active_stretch150 | yoshida6_m3 | two_term | True | True | True | 0.0001749 | 0 | 0 | 0.00041848 | 45.797 | 6.1583598e+08 |
| active_stretch150 | yoshida6_m3 | three_term | True | True | True | 6.4533e-06 | 0 | 0 | 1.9015e-05 | 2269 | 6.1583576e+08 |
| active_stretch150 | morales_y8m10b | short_time_asymptotic_one_term | True | False | True | 0.085773 | 0.061767 | 0.090909 | 0.29076 | 1 | 2.7290297e+08 |
| active_stretch150 | morales_y8m10b | direct_refit_one_term | False | False | True | 0.093169 | 0.052721 | 0.090909 | 2.2029 | 1 | 2.6111877e+08 |
| active_stretch150 | morales_y8m10b | two_term | True | False | True | 0.036708 | 0.12217 | 0.090909 | 1.6064 | 71.156 | 2.490062e+08 |
| active_stretch150 | morales_y8m10b | three_term | True | False | True | 0.020105 | 0.082075 | 0.047619 | 0.82969 | 6084.1 | 2.7155955e+08 |
| full_equilibrium | yoshida4 | short_time_asymptotic_one_term | False | False | True | 0.011948 | 0 | 0 | 0.022993 | 1 | 4.9245108e+09 |
| full_equilibrium | yoshida4 | direct_refit_one_term | False | False | True | 0.010864 | 0 | 0 | 0.02152 | 1 | 4.9240347e+09 |
| full_equilibrium | yoshida4 | two_term | True | True | True | 0.0001491 | 0 | 0 | 0.00026918 | 29.209 | 4.9203924e+09 |
| full_equilibrium | yoshida4 | three_term | True | True | True | 2.0256e-05 | 0 | 0 | 4.3461e-05 | 875.1 | 4.9203916e+09 |
| full_equilibrium | paper_new4 | short_time_asymptotic_one_term | False | False | True | 0.45067 | 0.52768 | 0.13043 | 2.2256 | 1 | 3.3951088e+09 |
| full_equilibrium | paper_new4 | direct_refit_one_term | False | False | True | 0.30269 | 0.27466 | 0.13043 | 1.043 | 1 | 2.9696607e+09 |
| full_equilibrium | paper_new4 | two_term | False | False | True | 0.4612 | 0.42899 | 0.17647 | 1.6802 | 29.209 | 3.1373444e+09 |
| full_equilibrium | paper_new4 | three_term | False | False | True | 0.41422 | 0.52554 | 0.17647 | 0.99631 | 875.1 | 3.002614e+09 |
| full_equilibrium | m5_best | short_time_asymptotic_one_term | True | False | True | 0.76111 | 4.3367 | 0.090909 | 2.0034 | 1 | 1.7781655e+09 |
| full_equilibrium | m5_best | direct_refit_one_term | True | False | True | 0.15322 | 0.1076 | 0.029126 | 2.3192 | 1 | 1.6160539e+09 |
| full_equilibrium | m5_best | two_term | False | False | True | 0.064982 | 0.080229 | 0.047619 | 0.40941 | 29.209 | 2.1183336e+09 |
| full_equilibrium | m5_best | three_term | True | False | True | 0.056456 | 0.057034 | 0.065421 | 0.13835 | 875.1 | 2.956084e+09 |
| full_equilibrium | current_m3 | short_time_asymptotic_one_term | False | False | True | 0.086367 | 0.2062 | 0.090909 | 0.44459 | 1 | 2.026324e+09 |
| full_equilibrium | current_m3 | direct_refit_one_term | True | False | True | 0.12661 | 0.15729 | 0.047619 | 1.011 | 1 | 1.876615e+09 |
| full_equilibrium | current_m3 | two_term | False | False | True | 0.0403 | 0.29807 | 0.13043 | 0.33851 | 29.209 | 1.9544334e+09 |
| full_equilibrium | current_m3 | three_term | False | False | True | 0.0038278 | 0.10834 | 0.13043 | 0.44915 | 875.1 | 2.6406321e+09 |
| full_equilibrium | two_term_center | short_time_asymptotic_one_term | False | False | True | 0.025002 | 0.013028 | 0.090909 | 0.071124 | 1 | 2.9219576e+09 |
| full_equilibrium | two_term_center | direct_refit_one_term | False | False | True | 0.010304 | 0.0081414 | 0.090909 | 0.056869 | 1 | 2.9226384e+09 |
| full_equilibrium | two_term_center | two_term | False | False | True | n/a | n/a | 0.17647 | 2.2571 | 29.209 | 4.2954405e+09 |
| full_equilibrium | two_term_center | three_term | False | False | True | 0.22244 | 0.006099 | 0.13043 | 0.6464 | 875.1 | 2.9073255e+09 |
| full_equilibrium | joint_refine_r0_s0046 | short_time_asymptotic_one_term | False | False | True | 0.016857 | 0.00041252 | 0.047619 | 0.031698 | 1 | 6.5323042e+09 |
| full_equilibrium | joint_refine_r0_s0046 | direct_refit_one_term | False | False | True | 0.013862 | 0 | 0 | 0.027675 | 1 | 6.5326076e+09 |
| full_equilibrium | joint_refine_r0_s0046 | two_term | True | True | True | 7.5503e-05 | 0 | 0 | 6.4606e-05 | 29.209 | 6.5244559e+09 |
| full_equilibrium | joint_refine_r0_s0046 | three_term | True | True | True | 0.0001033 | 0 | 0 | 0.00028562 | 875.1 | 6.5244571e+09 |
| full_equilibrium | yoshida6_m3 | short_time_asymptotic_one_term | False | False | True | 0.039484 | 0.011387 | 0.047619 | 0.101 | 1 | 6.725664e+09 |
| full_equilibrium | yoshida6_m3 | direct_refit_one_term | False | False | True | 0.033469 | 0.0094124 | 0.047619 | 0.090549 | 1 | 6.7203575e+09 |
| full_equilibrium | yoshida6_m3 | two_term | True | True | True | 0.0095733 | 0.000938 | 0.020408 | 0.0218 | 45.797 | 6.7177686e+09 |
| full_equilibrium | yoshida6_m3 | three_term | True | True | True | 0.00061905 | 0 | 0 | 0.0018036 | 2269 | 6.7176564e+09 |
| full_equilibrium | morales_y8m10b | short_time_asymptotic_one_term | True | False | True | 0.11697 | 0 | 0 | 1.4394 | 1 | 3.5144685e+09 |
| full_equilibrium | morales_y8m10b | direct_refit_one_term | False | False | True | n/a | n/a | 0.090909 | 4.2497 | 1 | 1.2829421e+12 |
| full_equilibrium | morales_y8m10b | two_term | False | False | True | 0.053059 | 0.11863 | 0.090909 | 1.9609 | 71.156 | 3.8401759e+09 |
| full_equilibrium | morales_y8m10b | three_term | False | False | True | 0.042215 | 0.14804 | 0.13043 | 0.4625 | 6084.1 | 4.1254435e+09 |
| full_stretch150 | yoshida4 | short_time_asymptotic_one_term | False | False | True | 0.02672 | 0.0043702 | 0.047619 | 0.050035 | 1 | 3.1995359e+09 |
| full_stretch150 | yoshida4 | direct_refit_one_term | False | False | True | 0.022634 | 0.003389 | 0.047619 | 0.044689 | 1 | 3.1999364e+09 |
| full_stretch150 | yoshida4 | two_term | True | True | True | 0.00084543 | 0 | 0 | 0.0014288 | 29.209 | 3.1994832e+09 |
| full_stretch150 | yoshida4 | three_term | True | True | True | 0.00015574 | 0 | 0 | 0.00039017 | 875.1 | 3.1994638e+09 |
| full_stretch150 | paper_new4 | short_time_asymptotic_one_term | True | False | True | 0.24567 | 0.0030879 | 0.009901 | 0.55623 | 1 | 1.5101517e+09 |
| full_stretch150 | paper_new4 | direct_refit_one_term | False | False | True | n/a | n/a | n/a | 13.589 | 1 | n/a |
| full_stretch150 | paper_new4 | two_term | False | False | True | 0.02451 | 0.17305 | 0.13043 | 0.39477 | 29.209 | 1.806421e+09 |
| full_stretch150 | paper_new4 | three_term | False | False | True | 0.024507 | 0.18045 | 0.13043 | 1.355 | 875.1 | 2.059601e+09 |
| full_stretch150 | m5_best | short_time_asymptotic_one_term | True | False | True | 0.17877 | 0.047223 | 0.038462 | 3.9789 | 1 | 1.2165611e+09 |
| full_stretch150 | m5_best | direct_refit_one_term | False | False | True | 0.052905 | 0.30865 | 0.13043 | 0.71775 | 1 | 1.2446023e+09 |
| full_stretch150 | m5_best | two_term | False | False | True | 0.13687 | 0.050108 | 0.090909 | 0.2865 | 29.209 | 1.8630414e+09 |
| full_stretch150 | m5_best | three_term | False | False | True | 0.065334 | 0.16597 | 0.13043 | 2.9679 | 875.1 | 1.9208844e+09 |
| full_stretch150 | current_m3 | short_time_asymptotic_one_term | False | False | True | 0.0032684 | 0.23368 | 0.13043 | 0.60801 | 1 | 1.4296694e+09 |
| full_stretch150 | current_m3 | direct_refit_one_term | False | False | True | 0.003226 | 0.23429 | 0.13043 | 0.48572 | 1 | 1.4286322e+09 |
| full_stretch150 | current_m3 | two_term | False | False | True | 0.11441 | 0.17711 | 0.13043 | 0.31885 | 29.209 | 1.8110292e+09 |
| full_stretch150 | current_m3 | three_term | False | False | True | 0.064476 | 0.14044 | 0.13043 | 0.33435 | 875.1 | 2.1985685e+09 |
| full_stretch150 | two_term_center | short_time_asymptotic_one_term | True | False | True | 0.11874 | 0.33295 | 0.052632 | 2.2606 | 1 | 1.7099189e+09 |
| full_stretch150 | two_term_center | direct_refit_one_term | False | False | True | 0.21321 | 0.12892 | 0.13043 | 0.397 | 1 | 2.3400976e+09 |
| full_stretch150 | two_term_center | two_term | False | False | True | 0.081805 | 0.1487 | 0.13043 | 0.33614 | 29.209 | 2.8644687e+09 |
| full_stretch150 | two_term_center | three_term | False | False | True | n/a | n/a | 0.13043 | 1.0385 | 875.1 | 2.9411621e+09 |
| full_stretch150 | joint_refine_r0_s0046 | short_time_asymptotic_one_term | False | False | True | 0.038728 | 0 | 0 | 0.056521 | 1 | 4.235167e+09 |
| full_stretch150 | joint_refine_r0_s0046 | direct_refit_one_term | True | False | True | 0.035682 | 0.061404 | 0.038462 | 0.07957 | 1 | 3.9703584e+09 |
| full_stretch150 | joint_refine_r0_s0046 | two_term | False | False | True | 0.02517 | 0.0061369 | 0.11111 | 0.019697 | 29.209 | 4.2934894e+09 |
| full_stretch150 | joint_refine_r0_s0046 | three_term | False | False | True | 0.0024956 | 0.010414 | 0.052632 | 0.010884 | 875.1 | 4.1833463e+09 |
| full_stretch150 | yoshida6_m3 | short_time_asymptotic_one_term | False | False | True | 0.060788 | 0.037141 | 0.13043 | 0.15045 | 1 | 4.7487445e+09 |
| full_stretch150 | yoshida6_m3 | direct_refit_one_term | False | False | True | 0.051888 | 0.028288 | 0.090909 | 0.13631 | 1 | 4.7533378e+09 |
| full_stretch150 | yoshida6_m3 | two_term | False | False | True | 0.60856 | 0.49017 | 0.17647 | 2.3562 | 45.797 | 5.0243779e+09 |
| full_stretch150 | yoshida6_m3 | three_term | True | True | True | 0.0054356 | 0.00049833 | 0.009901 | 0.015072 | 2269 | 4.7483495e+09 |
| full_stretch150 | morales_y8m10b | n/a | False | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Protocol notes

- The four declared checks alone determine formal pass/fail; model conditioning is reported separately.
- `post-hoc per-condition selection` is diagnostic and is not the general-candidate criterion.
- Direct minima are minima on actually calculated grids, not continuous-time exact minima.
- Short-time proxy fits and signed direct eigenphase errors remain separate quantities.
- The baseline in cost ratios is `m5_best` under the same Hamiltonian condition.

<!-- unified-nh3-diagnostics -->

## Numerical and execution audit

- Stage 1: 32 PF/Hamiltonian records (30 model-validations, 2 fixed-protocol short-time-fit failures).
- Stage 2: 26 fine-grid tasks, 1023 new direct eigenphase points, and 320 reused bit-matched stage-1 times.
- Stage-2 elapsed wall time: 34.19 min; summed point wall time: 3.16 h.
- Peak per-process CPU RSS: 1.580 GiB; maximum observed GPU use: 2657 MiB (peak increment 2543 MiB).
- Across all new points, maximum eigenpair residual was 2.763e-13.
- Across the 50 formally passing rows, minimum ground-state overlap was 0.999999625, minimum available adjacent-time overlap was 0.999999982, and maximum eigenpair residual was 6.398e-14.
- Maximum training design condition number was 6084.07; no row exceeded the declared diagnostic threshold of 1e8.

### Eigenbranch warnings

All warnings below belong to formally failing models; none changes the passing set.

| condition | PF | model | final pass | minimum ground overlap |
|---|---|---|---:|---:|
| active_equilibrium | m5_best | two_term | False | 0.532623 |
| active_equilibrium | m5_best | three_term | False | 0.828182 |
| active_stretch150 | m5_best | short_time_asymptotic_one_term | False | 0.850747 |
| active_stretch150 | m5_best | two_term | False | 0.447446 |
| active_stretch150 | m5_best | three_term | False | 0.625294 |
| active_stretch150 | morales_y8m10b | direct_refit_one_term | False | 0.518257 |
| active_stretch150 | morales_y8m10b | two_term | False | 0.6824 |
| active_stretch150 | morales_y8m10b | three_term | False | 0.789054 |
| full_equilibrium | current_m3 | direct_refit_one_term | False | 0.881446 |
| full_equilibrium | morales_y8m10b | direct_refit_one_term | False | 0.889043 |
| full_equilibrium | morales_y8m10b | two_term | False | 0.852339 |
| full_stretch150 | paper_new4 | direct_refit_one_term | False | 0.59972 |
| full_stretch150 | m5_best | short_time_asymptotic_one_term | False | 0.703595 |
| full_stretch150 | m5_best | three_term | False | 0.545046 |
| full_stretch150 | two_term_center | three_term | False | 0.893943 |

## Interpretation

1. **A fixed existing PF and a fixed model order can predict all four NH3 conditions.** Yoshida 4th passes with both the two-term and three-term models; Yoshida 6th m=3 passes with the three-term model.
2. **Adding finite-time terms helps, but coefficients still matter.** The common two-/three-term fits rescue Yoshida 4th, whereas m5_best passes no condition and the other fixed fourth-order candidates do not pass both full-electron geometries.
3. **Active-space success is substantially easier than full-electron transfer.** Several fourth-order PFs pass both active-space geometries, but only Yoshida 4th and Yoshida 6th m=3 retain one fixed model across both full-electron geometries.
4. **Predictability has a direct-cost premium relative to m5_best.** Yoshida 4th has mean/worst direct-grid cost ratios 3.155/3.672; Yoshida 6th m=3 has 3.518/4.157.
5. **Recommended next step:** freeze Yoshida 4th (two-term primary, three-term cross-check) and Yoshida 6th m=3 (three-term) and move them to an unused molecular hold-out before starting an m=4 coefficient search. Yoshida 4th is the lower-cost predictive choice in this development comparison.

Morales Y8m10b is not a four-condition candidate under the fixed protocol because its short-time fit fails for active-space equilibrium and full-electron stretch150; the thresholds were not changed post hoc.

## Reproducibility

- Stage-1 code commit(s): `e692360191e5dc2f499409eb3eb9afa60a36ca35`
- Stage-2 code commit(s): `a2763a59f9fca10468587a5861bb41334e2ed73d`
- Python: `3.12.3`
- NumPy/SciPy/PySCF/CuPy: `1.26.4` / `1.14.1` / `2.7.0` / `13.6.0`
