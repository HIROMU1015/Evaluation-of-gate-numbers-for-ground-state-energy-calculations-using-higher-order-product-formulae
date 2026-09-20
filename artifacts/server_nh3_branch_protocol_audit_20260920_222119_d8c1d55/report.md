# NH3 branch and short-time protocol audit

Status: complete. This is a post-hoc development audit, not an independent hold-out.

## A. 2x2 ablation

| Grid | Floor 5e-13 | Floor 5e-12 |
|---|---:|---:|
| Shared 0.06-0.80 | 17/24 | 17/24 |
| Shorter 0.02-1.8 | 24/24 | 24/24 |

Both grids use the same overlap-derived error, rolling window, order tolerance, and R2 criterion.
Changing only the grid changes 7/24 fit statuses; changing only the floor changes 0/24.
The grid-only changes are: full_equilibrium/yoshida4; full_equilibrium/paper_new4; full_equilibrium/m5_best; full_equilibrium/yoshida6_m3; full_stretch150/paper_new4; full_stretch150/m5_best; full_stretch150/yoshida6_m3.
The improvement is due to the time grid in this 2x2 audit, not to raising the noise floor.
The alternate grid/floor is a development sensitivity check only.

## B. Direct effective-order intervals

Interval rows: 72; two-interval plateau candidates: 12.
A whole-PF numerical-floor flag is not interpreted as failure of every interval.
Full four-condition scale comparisons available: 4.
yoshida4, absolute_time: log-center variance 0.0300283; common interval [0.015, 0.06].
yoshida4, lambda_h_sector_centered_half_width: log-center variance 0.771129; common interval None.
yoshida4, lambda_group_half_width_sum: log-center variance 0.0568437; common interval [0.327368662426783, 1.1083715174902637].
yoshida4, lambda_pauli_nonidentity_l1: log-center variance 0.0450324; common interval [0.5602628840372147, 2.0483472130618705].
Only Yoshida 4 has four-condition plateau coverage; these data do not establish a generally transferable dimensionless-time scale.

## C. Eigenbranch and direct cost

Independent PF builds at 0.97 and 1.01 t* passed: True.
Continuous paths choose the maximum-ground branch at 1.01 t*: True.
Minimum adjacent selected-branch overlap probability: 0.998811.
Branch differences elsewhere on the cost grid: 0.
Isolated 1.01 t* dip remains a physical finite-time candidate: True.
The dip is a reproducible same-branch grid-local result, not proof of a smooth or global optimum.

### independent_maximum_ground_overlap

- eta_star: 0.043159%
- eta_min: 18.335968%
- eta_t: 0.990099%
- maximum unseen signed residual / epsilon_E: 0.142855
- all four thresholds passed: False

### short_time_greedy_continuous

- eta_star: 0.043159%
- eta_min: 18.335968%
- eta_t: 0.990099%
- maximum unseen signed residual / epsilon_E: 0.142855
- all four thresholds passed: False

### short_time_global_continuous

- eta_star: 0.043159%
- eta_min: 18.335968%
- eta_t: 0.990099%
- maximum unseen signed residual / epsilon_E: 0.142855
- all four thresholds passed: False

All three branch rules agree on this grid. The three-term model fails the cost-loss and unseen-residual thresholds.

All other PF coefficients and Hamiltonians were unchanged.
No coefficient search or new molecule was run.
