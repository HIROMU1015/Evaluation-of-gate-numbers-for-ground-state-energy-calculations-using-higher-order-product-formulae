# H-chain direct optimal-time scaling protocol

## Question

For the repository cost proxy

\[
C_{\rm direct}(t)=
\frac{\beta N_{\exp}}
{t\,[\epsilon_E-|\delta E_{\rm direct}(t)|]},
\]

does the time minimizing the cost obtained from direct PF-unitary
diagonalization show a predictable dependence on H-chain size?

The selected quantity is denoted `t_grid_star`, not `t_ana`.  The latter is
reserved for the analytic optimum of the short-time power-law model.

## Status and scope

This is a registered **retrospective** small-system validation.  Existing H-chain
results were inspected before the grid was fixed.  H2, H4, H5, H6, and H7 are
recomputed without reusing prior direct results.  H3 is excluded because its
short-time errors did not clear the pre-existing numerical fitting floor.  H8
is reserved as a future independent holdout.

Even neutral singlets (H2/H4/H6) and odd cation triplets (H5/H7) are different
physical families and are never pooled into one scaling regression.

## Fixed calculation

- PFs: `4th(m5_best)` and `8th(Morales-Y8m10b)`.
- Target: 0.1 kcal/mol = `0.00015936001019904 Ha`.
- Cost safety factor: `beta=1.2`.
- Time grid: every `0.05 t_ana` from `0.20 t_ana` through `1.70 t_ana`,
  inclusive (31 points).
- Backend: conserved-sector dense PF unitary, cached symmetric second-order
  blocks, CPU complex-double Schur decomposition.
- Branch: maximum ground overlap at the first time, then maximum previous-vector
  overlap in increasing-time order.

The analytic time only normalizes and bounds the common search domain.  It does
not choose the minimum within that domain.  The reported result is therefore a
domain-restricted discrete optimum, not an unconstrained global optimum.

## Fixed gates

- Unitarity and Schur off-diagonal Frobenius residuals: at most `1e-10`.
- Continuous and maximum-ground-overlap branch shifts: agreement within
  `1e-10 Ha` at all points.
- Ground overlap at the selected optimum: at least `0.9`.
- A minimum on either time-domain boundary is not scorable.
- Previous-vector overlap below `0.5` is reported as a warning; it is not alone
  a failure when the two branch-selection rules give the same shift.

The connected component containing the selected minimum with cost no more than
1.01 times the minimum defines the near-optimal interval.  Its width and any
intersection with a signed-error zero crossing are reported.

## Scaling decision

For each PF, a constant law and `t=a N^b` are evaluated on H2/H4/H6.  The
power-law assessment uses leave-one-size-out prediction.  Maximum relative
error at most 20% is only `small_system_predictable_requires_H8_holdout`;
it is never a strong scaling claim.  H5/H7 supply a descriptive two-point trend
only.

No threshold, grid boundary, family definition, or PF may be changed after the
new direct results are opened.  A failure to obtain a predictable size law is a
valid endpoint.
