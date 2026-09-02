# PF cost-model rejection tests

The same tests are applied to m5 and Y8m10b. A failure does not deny the formal short-time order; it limits finite-time absolute cost claims.

## Decision rules

- Direct validity: `abs(e_direct/(alpha*t^p)-1) <= 0.10` on a contiguous interval from the short-time regime.
- Analytic schedule: `t_ana <= t_valid`.
- Conservative cap: a predicted cap must not exceed held-out direct `t_valid`.
- Expanded model: test the `p`, `p+2`, and `p+4` terms without using finite-time direct data to fit the large-system prediction.

## Current target (0.1 kcal/mol)

| System | PF | t_valid | t_ana/t_valid | t_ana directly valid | cost penalty at t_use |
|---|---|---:|---:|---:|---:|
| H2 | m5 | 2.0050 | 1.694 | no | 1.389 |
| H2 | Y8m10b | 1.6315 | 3.731 | no | 3.317 |
| H4 | m5 | 1.3476 | 1.714 | no | 1.404 |
| H4 | Y8m10b | 1.4664 | 3.153 | no | 2.803 |
| H5 | m5 | 1.1547 | 2.247 | no | 1.811 |
| H5 | Y8m10b | 1.6291 | 3.131 | no | 2.783 |
| H6 | m5 | 1.0423 | 2.000 | no | 1.620 |
| H6 | Y8m10b | 1.8105 | 2.105 | no | 1.872 |

## Dense direct-boundary overrides

The conservative direct cap is the last passing sampled time; the next sampled time is the first failure.

| System | PF | previous cap | t_pass | t_fail | ratio at pass | ratio at fail |
|---|---|---:|---:|---:|---:|---:|
| H6 | Y8m10b | 1.3340 | 1.8105 | 1.9058 | 1.0238 | 0.6835 |
| H7 | Y8m10b | 0.8758 | 1.4232 | 1.5327 | 0.9556 | 1.3508 |

## Target-error domain

| PF | direct-valid analytic schedules | total schedules |
|---|---:|---:|
| m5 | 6 | 24 |
| Y8m10b | 0 | 24 |

## Rolling size-law holdouts

The safety factor for each row uses only residuals from earlier rows, never the held-out target itself.

| PF | target | training | cap | t_pass | t_fail | cap/pass | status |
|---|---:|---|---:|---:|---:|---:|---|
| m5 | H5 | H2,H4 | 1.1858 | 1.1547 | 1.4158 | 1.027 | unresolved_bracket |
| m5 | H6 | H2,H4,H5 | 1.0182 | 1.0423 | 1.4593 | 0.977 | verified_safe |
| m5 | H7 | H2,H4,H5,H6 | 0.9271 | 1.0871 | 1.5220 | 0.853 | verified_safe |
| Y8m10b | H5 | H2,H4 | 1.4169 | 1.6291 | 1.8340 | 0.870 | verified_safe |
| Y8m10b | H6 | H2,H4,H5 | 1.5406 | 1.8105 | 1.9058 | 0.851 | verified_safe |
| Y8m10b | H7 | H2,H4,H5,H6 | 1.6874 | 1.4232 | 1.5327 | 1.186 | failed |

## Short-time expansion validity relative to t_ana

| System | PF | p only | p and p+2 | p through p+4 |
|---|---|---:|---:|---:|
| H2 | m5 | 0.65 | 1.10 | 1.20 |
| H2 | Y8m10b | 0.35 | 0.65 | 0.85 |
| H4 | m5 | 0.60 | 0.95 | 1.00 |
| H4 | Y8m10b | 0.35 | 0.55 | 0.60 |
| H5 | m5 | 0.50 | 0.75 | 0.80 |
| H5 | Y8m10b | 0.30 | 0.55 | 0.65 |
| H6 | m5 | 0.55 | 0.80 | 0.80 |
| H6 | Y8m10b | 0.45 | 0.45 | 0.45 |

The expansion table uses direct short-time coefficients as a best-case diagnostic. The separately stored one-overlap fits show the same qualitative limitation.

## Local behavior around t_ana

A local order is only a diagnostic here. Near a signed-error cancellation it can become very large or negative.

| System | PF | e_direct/e_model at t_ana | median local order | local range | sign changes | local cost max/min |
|---|---|---:|---:|---:|---:|---:|
| H2 | m5 | 0.723 | 2.98 | 2.1 to 3.4 | 0 | 1.051 |
| H2 | Y8m10b | 0.024 | 19.13 | -52.9 to 34.9 | 1 | 1.103 |
| H4 | m5 | 0.583 | 1.13 | -21.0 to 43.5 | 0 | 1.095 |
| H4 | Y8m10b | 1.265 | 16.97 | -92.3 to 116.5 | 6 | 1.183 |
| H5 | m5 | 0.852 | 0.60 | -31.6 to 80.4 | 4 | 1.582 |
| H5 | Y8m10b | 1.883 | 3.08 | -33.8 to 68.6 | 2 | 1.859 |
| H6 | m5 | 0.377 | 2.86 | -2.3 to 8.0 | 0 | - |
| H6 | Y8m10b | 3.355 | 5.51 | -5.7 to 16.7 | 2 | - |
| H7 | m5 | 0.495 | 1.77 | 1.6 to 1.9 | 0 | - |
| H7 | Y8m10b | 0.141 | 11.10 | -3.9 to 26.1 | 0 | - |

## Interpretation

- At 0.1 kcal/mol, neither formula has `t_ana` inside the directly validated leading-power interval on H2/H4/H5/H6.
- For m5 H5, the predicted cap is about 2.7% later than the last confirmed pass but earlier than the first sampled failure. This is unresolved, not a demonstrated model failure; one direct calculation at the predicted cap can decide it.
- For Y8m10b, the dense H6 boundary removes the safety reduction that had been caused by the old coarse H6 cap. Recomputing the rule raises the H7 cap to 1.6874, later than the first sampled failure at 1.5327, so the H7 holdout fails.
- Adding the next one or two even powers does not extend the Y8m10b model to `t_ana` on H2--H6; on H6 it does not extend the 10% range at all.
- A subdivided reference removes reference-PF error but does not remove the intrinsic difference between one-overlap phase and the ground-connected PF eigenphase at large times.

This integration reassesses only the direct size-law step. A large-system proxy check at each predicted cap is still required before a cap-constrained estimate is promoted to a main result.

Integrated cap-rule status: m5 is **unresolved** at H5; Y8m10b **failed** at H7. Neither has a fully certified large-system cap under the current common rule.
