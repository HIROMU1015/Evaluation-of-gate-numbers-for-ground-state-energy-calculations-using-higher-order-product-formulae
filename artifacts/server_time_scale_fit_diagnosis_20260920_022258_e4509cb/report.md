# NH3 short-time fit time-scale diagnosis

Status: complete

This is a development diagnostic, not an independent hold-out.

## Interpretation and limits

- The shared molecular overlap-proxy fit (0.06–0.80, 15 geometric times; five-point windows; 5e-13 Hartree floor) passes all 12 active-space cases but only 5 of 12 full-electron cases. The shorter-time 0.02–1.8 sensitivity grid with its separate 5e-12 floor passes all 24. This supports a time-window mismatch, not a universal replacement protocol.
- Signed direct PF eigenphase shifts were analyzed separately, without reusing the proxy floor. Of 24 condition/PF ladders at t=0.0075, 0.015, 0.03, 0.06, 17 encounter the estimated direct numerical floor, 3 show a sign reversal, and 4 reach formal order without either flag. A floor flag at the earliest point does not rule out a plateau at later times.
- The exact-sector Hamiltonian half-width is 1.94–2.97 for active-space NH3 versus 18.82–19.44 for full-electron NH3; the group half-width sum is 18.47–19.34 versus 42.35–43.65. The same absolute time therefore samples different dimensionless times. None of the three scales is validated as universal on an unused molecule.
- For stretched full-electron NH3 with joint_refine_r0_s0046, the model predicts t*=0.18866224145335106. The post-hoc fine-grid minimum is at 1.01 t*, with direct cost 3.561404593e9 versus 4.214422593e9 at t*. The time error drops to 0.9901%, but the cost loss is 18.336% and the maximum unused signed-error residual is 0.142855 epsilon_E. Thus the post-hoc diagnostic still fails.
- The 1.01 t* cost is an isolated dip: costs at 1.00 and 1.02 t* are 4.214e9 and 4.350e9. Its eigenpair residual is 4.49e-14, exact-ground-state overlap probability 0.998987, and adjacent selected-vector overlap probability 0.998938. These checks do not establish whether the dip is physical or a branch/numerical issue; independently repeat and inspect branch continuity before interpreting it.


## Protocol comparison

| condition | PF | shared protocol | legacy sensitivity | direct diagnosis |
|---|---|---:|---:|---|
| active_equilibrium | yoshida4 | True | True | direct_small_time_values_reach_numerical_floor |
| active_equilibrium | paper_new4 | True | True | direct_small_time_values_reach_numerical_floor |
| active_equilibrium | m5_best | True | True | direct_small_time_values_reach_numerical_floor |
| active_equilibrium | two_term_center | True | True | direct_small_time_values_reach_numerical_floor |
| active_equilibrium | joint_refine_r0_s0046 | True | True | direct_small_time_values_reach_numerical_floor |
| active_equilibrium | yoshida6_m3 | True | True | sign_reversal_or_cancellation_on_direct_ladder |
| active_stretch150 | yoshida4 | True | True | direct_small_time_values_reach_numerical_floor |
| active_stretch150 | paper_new4 | True | True | direct_small_time_values_reach_numerical_floor |
| active_stretch150 | m5_best | True | True | sign_reversal_or_cancellation_on_direct_ladder |
| active_stretch150 | two_term_center | True | True | direct_small_time_values_reach_numerical_floor |
| active_stretch150 | joint_refine_r0_s0046 | True | True | direct_small_time_values_reach_numerical_floor |
| active_stretch150 | yoshida6_m3 | True | True | direct_small_time_values_reach_numerical_floor |
| full_equilibrium | yoshida4 | False | True | direct_effective_order_reaches_formal_order_4 |
| full_equilibrium | paper_new4 | False | True | direct_small_time_values_reach_numerical_floor |
| full_equilibrium | m5_best | False | True | direct_small_time_values_reach_numerical_floor |
| full_equilibrium | two_term_center | True | True | direct_small_time_values_reach_numerical_floor |
| full_equilibrium | joint_refine_r0_s0046 | True | True | direct_effective_order_reaches_formal_order_4 |
| full_equilibrium | yoshida6_m3 | False | True | direct_small_time_values_reach_numerical_floor |
| full_stretch150 | yoshida4 | True | True | direct_effective_order_reaches_formal_order_4 |
| full_stretch150 | paper_new4 | False | True | direct_small_time_values_reach_numerical_floor |
| full_stretch150 | m5_best | False | True | sign_reversal_or_cancellation_on_direct_ladder |
| full_stretch150 | two_term_center | True | True | direct_small_time_values_reach_numerical_floor |
| full_stretch150 | joint_refine_r0_s0046 | True | True | direct_effective_order_reaches_formal_order_4 |
| full_stretch150 | yoshida6_m3 | False | True | direct_small_time_values_reach_numerical_floor |

## Fine-grid post-hoc diagnosis

- eta_star: 0.043159%
- eta_min: 18.335968%
- eta_t: 0.990099%
- maximum unseen residual / epsilon_E: 0.142855
- result: False
- reuse precision check: True

The proxy-fit and direct-eigenphase diagnostics are reported separately.
No PF coefficients were changed and no new molecule was evaluated.
