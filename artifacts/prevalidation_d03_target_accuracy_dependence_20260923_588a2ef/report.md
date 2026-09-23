# D03 target-accuracy dependence: existing-curve audit

Status: **complete_existing_curve_audit_requires_additional_direct_points**

This is a retrospective fixed-model transfer and coverage audit, not an independent holdout. No new direct PF eigenvalue point was computed.

## Existing-curve coverage

| dataset | target | complete source rows | fully covered | fixed-model passes |
|---|---|---:|---:|---:|
| nh3 | CA | 14 | 1 | 0 |
| nh3 | CA_div_10 | 14 | 13 | 10 |
| nh3 | CA_div_100 | 14 | 1 | 0 |
| p03 | CA | 24 | 0 | 0 |
| p03 | CA_div_10 | 24 | 19 | 17 |
| p03 | CA_div_100 | 24 | 0 | 0 |

A row is fully covered only when a saved direct point lies within 0.5% of the transferred model optimum, at least three unseen points cover 0.85--1.15 of that optimum, and the observed direct-grid minimum is bracketed by saved neighbors no farther than 3% in time. Sparse-grid minima are not called continuous global minima.

## Covered direct rankings

| dataset | condition | target | best covered PF | coverage status |
|---|---|---|---|---|
| nh3 | active_equilibrium | CA | not determined | insufficient_existing_curve |
| nh3 | active_equilibrium | CA_div_10 | current_m3 | partial_coverage |
| nh3 | active_equilibrium | CA_div_100 | not determined | insufficient_existing_curve |
| nh3 | active_stretch150 | CA | morales_y8m10b | partial_coverage |
| nh3 | active_stretch150 | CA_div_10 | morales_y8m10b | complete_all_declared_formulas |
| nh3 | active_stretch150 | CA_div_100 | morales_y8m10b | partial_coverage |
| nh3 | full_equilibrium | CA | current_m3 | partial_coverage |
| nh3 | full_equilibrium | CA_div_10 | current_m3 | complete_all_declared_formulas |
| nh3 | full_equilibrium | CA_div_100 | current_m3 | partial_coverage |
| nh3 | full_stretch150 | CA | not determined | insufficient_existing_curve |
| nh3 | full_stretch150 | CA_div_10 | yoshida4 | partial_coverage |
| nh3 | full_stretch150 | CA_div_100 | not determined | insufficient_existing_curve |
| p03 | CO_active_eq_sto3g | CA | not determined | insufficient_existing_curve |
| p03 | CO_active_eq_sto3g | CA_div_10 | current_m3 | complete_all_declared_formulas |
| p03 | CO_active_eq_sto3g | CA_div_100 | not determined | insufficient_existing_curve |
| p03 | CO_active_stretch150_sto3g | CA | not determined | insufficient_existing_curve |
| p03 | CO_active_stretch150_sto3g | CA_div_10 | current_m3 | complete_all_declared_formulas |
| p03 | CO_active_stretch150_sto3g | CA_div_100 | not determined | insufficient_existing_curve |
| p03 | HF_full_eq_sto3g | CA | not determined | insufficient_existing_curve |
| p03 | HF_full_eq_sto3g | CA_div_10 | yoshida4 | partial_coverage |
| p03 | HF_full_eq_sto3g | CA_div_100 | not determined | insufficient_existing_curve |
| p03 | HF_full_stretch150_sto3g | CA | not determined | insufficient_existing_curve |
| p03 | HF_full_stretch150_sto3g | CA_div_10 | current_m3 | partial_coverage |
| p03 | HF_full_stretch150_sto3g | CA_div_100 | current_m3 | partial_coverage |
| p03 | N2_active_eq_sto3g | CA | not determined | insufficient_existing_curve |
| p03 | N2_active_eq_sto3g | CA_div_10 | current_m3 | complete_all_declared_formulas |
| p03 | N2_active_eq_sto3g | CA_div_100 | not determined | insufficient_existing_curve |
| p03 | N2_active_stretch150_sto3g | CA | not determined | insufficient_existing_curve |
| p03 | N2_active_stretch150_sto3g | CA_div_10 | current_m3 | complete_all_declared_formulas |
| p03 | N2_active_stretch150_sto3g | CA_div_100 | not determined | insufficient_existing_curve |

## Additional-point decision

- Recommended coarse direct points for a conclusive follow-up: **138**.
- Optional target-specific refit points inventoried but not authorized: **371**.
- Fine 1% grids remain deferred until the coarse points identify a local minimum.
- Morales Y8m10b has no N2/CO direct curve in the source holdout and is audited only where the NH3 source run qualified its fixed short-time protocol.

## Interpretation limit

Only targets with full saved-curve coverage support a PF ranking or fixed-model pass/fail statement. Other rows are missing-data findings, not model failures. The next step is the recommended coarse-point manifest, preferably on the GPU server; coefficients, molecules, bases, and thresholds remain frozen.
