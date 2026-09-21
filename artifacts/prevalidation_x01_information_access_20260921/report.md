# X01 A06: information-access audit

Status: complete

The saved workflow is separated into oracle evaluation, target-specific calibration, and transfer-only selection. No new PF or molecular calculation was run.

## Direct dependency audit

- Raw conditions checked: 17.
- PF/condition formula records checked: 34.
- Evaluated short-time points: 171; selected-window points: 170.
- Direct training points: 102.
- Direct local validation points: 236.
- Direct points using the exact-ground-overlap branch rule: 338.

Every short-time fit uses `exp(-i E0 t)<psi0|U_PF(t)|psi0>` and every saved direct training/validation point selects the PF eigenbranch by maximum overlap with the exact ground state. The fitted coefficients and selected time therefore depend on exact-state information before evaluation begins.

## Performance by access tier

| tier | method | status | choices | frozen pass | oracle agreement | calibration points | exact state required |
|---|---|---|---:|---:|---:|---:|---|
| 1_oracle_evaluation | minimum direct required cost over the two model-selected schedules | measured evaluation upper bound | 17 | n/a | 17 | n/a | True |
| 2_oracle_assisted_target_calibration | fit both PFs on each target and choose smaller predicted two-term cost | measured but not cheap-state-independent calibration | 17 | 17 | 17 | 273 | True |
| 2_oracle_assisted_target_calibration | pre-fix current_m3 and calibrate only its two-term model | measured fixed-PF strategy | 0 | 17 | 17 | 137 | True |
| 2_practical_target_calibration | few target-specific evaluations without exact E0 or exact ground-state vector | not implemented / not evaluated | 0 | n/a | n/a | n/a | False |
| 3_transfer_only | choose PF/model/time from cheap descriptors on an unused system | not implemented / not evaluated | 0 | n/a | n/a | 0 | False |

The saved two-PF calibrated selector chooses `current_m3` on all 17 conditions, agrees with the oracle comparison over the same two predicted schedules on 17/17, and meets the strict frozen budget on 17/17. Its direct-cost selection regret is zero on this candidate set, but it requires 273 exact-state-assisted calibration points and 424.145 saved PF-specific seconds because both PFs are calibrated before choosing.

Pre-fixing `current_m3` avoids the unused second-PF calibration and uses 137 points and 211.535 s on the same conditions. This is still oracle-assisted target calibration; it is not a descriptor-only transfer result.

## Leakage boundary

The three direct fit points are excluded from saved validation scoring, so the finite-time residual test is not numerically fitted on its own validation grid. However, the calibration inputs themselves use exact ground-state and direct PF-eigenvalue information. The A05 safety multiplier additionally uses all 17 development truths and is post-hoc; it cannot be treated as a prospective safety guarantee.

## A06 conclusion

Current performance establishes an oracle-assisted, target-specific upper bound. It does not yet establish a practical cheap calibration method or an unused-system transfer selector. The observed 17/17 fixed-current frozen budget result remains useful for mechanism and strategy comparison, but the information-access qualification must accompany it.

Before claiming deployable PF/time selection, the next missing evidence is either (a) replacement of exact E0/|psi0>/branch overlaps by an approximate state or measurable surrogate, or (b) a frozen descriptor-to-choice rule tested on a genuinely unused molecular family.

## Files

- `information_access_table.csv`: input-by-input access classification.
- `performance_by_access_tier.csv`: measured and missing tier performance.
- `condition_selection.csv`: calibrated versus oracle candidate choices.
- `dependency_audit.json`: raw and implementation dependency counts.
- `raw_sources.csv`: hashes of all raw condition files.
- `analysis.json` and `manifest.json`: summary and provenance.
