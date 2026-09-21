# X01 existing-results audit: A01 and A02

Status: complete

This audit performs no new electronic-structure or PF calculation. It independently recomputes the declared metrics from saved direct points.

## Reproduction result

- Condition/model rows recomputed: 319.
- Metric rows matching the stored values: 318/318 eligible rows.
- Rows without stored metrics because the source calculation failed: 1.
- Source rows without metrics: `current_m3 / BeH2_full_eq` (failed).
- Pass/fail rows matching the stored decisions: 319/319.
- Cost ratios matching the stored values: 17/17.
- Joint candidate summaries matching the stored values: 31/31.
- Maximum metric absolute reproduction difference: 0.

## Saved holdout pass counts

| dataset | PF | model | pass | worst eta* | worst eta_min | worst eta_t | worst residual/eps |
|---|---|---|---:|---:|---:|---:|---:|
| five_condition_holdout | current_m3 | original_one_term | 1/5 | 0.017103 | 0.00171846 | 0.024961 | 0.0401079 |
| five_condition_holdout | current_m3 | refit_one_term | 1/5 | 0.0165062 | 0.00163867 | 0.0243108 | 0.0394381 |
| five_condition_holdout | current_m3 | two_term | 5/5 | 0.00346067 | 0 | 0 | 0.0206075 |
| five_condition_holdout | two_term_center | original_one_term | 4/5 | 0.0100524 | 0.000532958 | 0.0148463 | 0.0156465 |
| five_condition_holdout | two_term_center | refit_one_term | 5/5 | 0.00968568 | 0.000505988 | 0.0144619 | 0.0151617 |
| five_condition_holdout | two_term_center | two_term | 5/5 | 0.000499135 | 0 | 0 | 0.000862127 |
| twelve_condition_holdout | current_m3 | original_one_term | 2/12 | 0.053125 | 0.457946 | 0.223492 | 0.503905 |
| twelve_condition_holdout | current_m3 | refit_one_term | 2/12 | 0.0520195 | 0.45686 | 0.222096 | 0.499968 |
| twelve_condition_holdout | current_m3 | two_term | 11/12 | 0.0328863 | 0.418222 | 0.166667 | 0.364667 |
| twelve_condition_holdout | two_term_center | original_one_term | 7/12 | 0.0193626 | 0.00231862 | 0.026257 | 0.0344283 |
| twelve_condition_holdout | two_term_center | refit_one_term | 7/12 | 0.0185421 | 0.00218856 | 0.0253461 | 0.0332124 |
| twelve_condition_holdout | two_term_center | two_term | 12/12 | 0.00288445 | 0 | 0 | 0.00596183 |

## Combined 17-condition development holdouts

| PF | model | pass | worst eta* | worst eta_min | worst eta_t | worst residual/eps |
|---|---|---:|---:|---:|---:|---:|
| current_m3 | original_one_term | 3/17 | 0.053125 | 0.457946 | 0.223492 | 0.503905 |
| current_m3 | refit_one_term | 3/17 | 0.0520195 | 0.45686 | 0.222096 | 0.499968 |
| current_m3 | two_term | 16/17 | 0.0328863 | 0.418222 | 0.166667 | 0.364667 |
| two_term_center | original_one_term | 11/17 | 0.0193626 | 0.00231862 | 0.026257 | 0.0344283 |
| two_term_center | refit_one_term | 12/17 | 0.0185421 | 0.00218856 | 0.0253461 | 0.0332124 |
| two_term_center | two_term | 17/17 | 0.00288445 | 0 | 0 | 0.00596183 |

## Joint full-/frozen-electron training search

The top ranked candidate `joint_refine_r0_s0046` passes 6/7 training conditions. Its failing condition is H2O_full_stretch150.
No ranked candidate passes all seven training conditions. This is training/search evidence, not holdout evidence.

## Direct-cost premium

At each PF's own two-term predicted optimum, the `two_term_center/current_m3` direct-cost ratio over the 17 saved holdouts ranges from 1.144428 to 1.210110, with median 1.151258.
These ratios are not continuous-time oracle-minimum comparisons.

## Claim-evidence matrix

| ID | classification | evidence role | result |
|---|---|---|---|
| X01-C01 | supported | coefficient-fixed holdout | current_m3 5/5; two_term_center 5/5 |
| X01-C02 | not identified by the five-condition pass counts | paired PF-by-model comparison | Both PFs pass 5/5 after adding the same t^6 term; the model change rescues the baseline too. |
| X01-C03 | supported with one-condition incremental coverage | coefficient-fixed holdout | two_term_center 12/12; current_m3 11/12 |
| X01-C04 | supported for two_term_center under the saved protocol | combined saved holdouts | two_term_center two-term 17/17; current_m3 two-term 16/17 |
| X01-C05 | contradicted | coefficient-search training | Best ranked candidate joint_refine_r0_s0046 passes 6/7 training conditions. |
| X01-C06 | approximately supported for five conditions, broader range on all 17 | each PF at its own two-term predicted optimum | Across all 17 saved holdouts: min=1.144428, median=1.151258, max=1.210110. |

## A01/A02 conclusion

All stored metrics and pass/fail decisions are exactly reproducible under their declared definitions. Adding the same two-term model substantially improves both PFs. `two_term_center` adds one pass over `current_m3` across the twelve geometry/active-space holdouts and is the only one of the two to pass all 17 accumulated development holdouts, but it carries a 14.4%--21.0% direct-cost premium at the saved predicted schedules. The present pass counts therefore establish incremental coverage, not yet practical necessity for new coefficients.

The next X01 step is A03/A04: paired PF-by-model effect sizes and separate threshold sensitivities. No new molecule, PF coefficient search, or direct PF point is started by this audit.

## Files

- `manifest.json`: protocol and immutable source hashes.
- `condition_metrics.csv`: every independently recomputed condition/model row.
- `aggregate_metrics.csv`: per-dataset PF/model summaries.
- `combined_holdout_metrics.csv`: combined 17-condition development summary.
- `joint_candidate_summary.csv`: all ranked joint-search candidates.
- `cost_ratios.csv`: condition-level direct-cost ratios and reproduction differences.
- `claim_evidence_matrix.csv`: A01 claim classifications.
- `audit.json`: complete machine-readable audit summary.
