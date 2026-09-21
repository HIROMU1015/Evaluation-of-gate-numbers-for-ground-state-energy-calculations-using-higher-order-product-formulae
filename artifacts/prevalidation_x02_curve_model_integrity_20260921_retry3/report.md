# X02 finite-time curve/model integrity batch

- Overall status: **complete_with_findings**
- Formal audit IDs: C01, C06, C08, E01, E02, E03, E04, E06
- Systems: H2 and H4; formulas: Yoshida4, current_m3, two_term_center, Morales Y8m10b
- All direct minima below are sampled-grid minima, not continuous-time global minima.
- No coefficient search and no new molecule were used.

## Shared truth data

Eight molecular PF curves were generated. Total direct points: 4480. Branch warnings: 1351.
Every point stores the signed direct eigenvalue shift, signed Im(z)/t, signed arg(z)/t, ground/previous-branch overlaps, phase gap, unwrap integer, residuals, and timings.
Primary minima and extrapolation scores stop at the first branch warning. The wider curves remain diagnostic data and are not silently treated as reliable target-branch truth.

## C01: proxy versus direct eigenvalue shift

The maximum leading-coefficient relative difference from the direct fit was `0.0082919`. The largest finite direct sampled-grid regret from an estimator's one-term analytic time was `2.43363`.
Estimator coefficients use the same five times selected by the canonical imaginary-proxy rolling window, so the comparison does not give one estimator extra points.

## C06: minima and grid scope

Across 8 PF/system curves, the largest coarse-grid cost regret relative to the refined sampled grid was `0.0492037`. Common reliable-prefix boundary minima: 2. Unrestricted minima outside a formula's reliable branch prefix: 2.
The declared interval and both grids are saved. No interpolation value is promoted to a direct minimum.
Reliable-prefix sign-change brackets were locally refined. At each resulting minimum, the cached and sequential builders agreed within `8.158e-15` Hartree in the selected shift and `3.530e-14` in unitary Frobenius norm.

## C08: singular and boundary controls

Synthetic controls passed 4/4. Infeasible error budgets remain explicit; they are not clipped to a small positive denominator.

## E01/E02: fit-window and conditioning

E01 evaluated 144 window/threshold combinations; 4 did not qualify and remain explicit. E02's maximum scaled design condition number was `18.1404`; the smallest raw/scaled improvement factor was `1`.

## E03/E04/E06: representation, term count, extrapolation

E03/E04 score independent practical holdout points only through `min(1.2*t_ana, branch-reliable-prefix)`. E06 separately follows each model through the full leading branch-reliable prefix.

Signed fitting had the smaller maximum absolute-error residual in 1/24 comparisons. Absolute-error fits produced negative holdout predictions in 1 comparisons.

Holdout pass counts at max signed residual <= 0.05 epsilon:

| model | passes / 8 curves | minimum contiguous validity factor |
|---|---:|---:|
| 1 term | 6/8 | 1.70599 |
| 2 term | 6/8 | 1.70241 |
| 3 term | 6/8 | 1.70599 |

Training-fit/holdout overfit warnings: 6; post-failure pass reentries: 4. A later reentry does not extend the leading validity interval.

## F05 data and next decision

Physical energy and PF phase-gap fields were collected to avoid recomputation, but F05 is not marked complete because F01/F02 remain dependencies. The next choice is between the F01/F02/F05 mechanism batch and the C04/C05 frozen-QPE-budget batch.
