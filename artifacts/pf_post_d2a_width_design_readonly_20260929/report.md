# Post-D2A C0 width-design report

Status: `post_d2a_width_design_complete_review_required`

## What C0 established

- Frozen D2-A point estimates remain unchanged.
- `e_direct=abs(delta_direct)` is the only direct PF error used in the uncorrected budget.
- `g_target` and `g_rho_others` are separate quantities; the residual bound needs the latter.
- Chord, principal phase, and unwrapped energy gaps have conditional, explicit conversions.
- One candidate bound was specified for an original normal operator and a lifted vector.
- Missing target, separation, branch, or action-error information produces `indeterminate`.
- No fallback to a small empirical width is allowed for an unmet certificate condition.

## Saved scalar arithmetic

- Coordinates: 6 existing HCl development coordinates.
- `K_current_m3`: 98,672 for all rows.
- Current width determinant: local residual width, 6/6.
- Explicit numerical action bound in the saved formula: 0; this is not a rigorous forward-error certificate.
- Same-time perfect-calibration saving range: 0.327975% to 2.286462%.
- Current width / `w_win(t;0)` range: 1.106196 to 167.491453.
- Coordinates whose current width is below `w_win(t;0)`: 0/6.

These values are post-hoc development arithmetic, not a new method result or an independent validation.

## Main unresolved condition

The candidate quadratic residual bound is mathematically usable only with a valid full-space
`g_rho_others` lower bound and target identity. No truth-free operational acquisition route is currently
established. A projected Ritz gap or D1 true gap may not silently fill this input.

## C1 draft boundary

C1 remains unauthorized. If later approved, it should use one fixed operational width method, one separate
oracle sensitivity arm, the saved six HCl coordinates, and fixed synthetic controls. It must not rerun
Arnoldi or molecular PF/H actions under the present draft. Prediction and width must freeze before truth.

## Stop

No new Arnoldi, PF/H action, gap calculation, toy experiment, LiF, D2-B, holdout, or GPU operation was run.
The next action is a full research-direction review.
