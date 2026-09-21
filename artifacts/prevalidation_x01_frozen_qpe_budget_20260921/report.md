# X01 A05: frozen QPE budget audit

Status: complete

The model-selected time and continuous QPE cost are frozen before the saved direct PF eigenvalue error is substituted. No schedule or budget is repaired using the direct value.

## Definition

For frozen model cost `C_model`, the implied QPE error is `beta*N_rot/(t*C_model)`. The strict score is `abs(deltaE_direct) + epsilon_QPE <= epsilon_E`, with `epsilon_E=0.00015936001019904` Hartree and `beta=1.2`. This is the repository's additive continuous-cost proxy, not a stochastic QPE run or a hardware-level success guarantee.

## Results

| PF | model | four-metric pass | eta* pass | frozen-budget pass | conservative / underestimated | max target excess / eps | max extra cost needed | max avoidable overbudget |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| current_m3 | original_one_term | 3/17 | 3/17 | 17/17 | 17 / 0 | 0 | 0% | 5.3125% |
| current_m3 | refit_one_term | 3/17 | 3/17 | 17/17 | 17 / 0 | 0 | 0% | 5.20195% |
| current_m3 | two_term | 16/17 | 16/17 | 17/17 | 17 / 0 | 0 | 0% | 3.28863% |
| two_term_center | original_one_term | 11/17 | 11/17 | 17/17 | 17 / 0 | 0 | 0% | 1.93626% |
| two_term_center | refit_one_term | 12/17 | 12/17 | 17/17 | 17 / 0 | 0 | 0% | 1.85421% |
| two_term_center | two_term | 17/17 | 17/17 | 9/17 | 9 / 8 | 9.81066e-05 | 0.0123408% | 0.288445% |

Across all 102 rows, 40 fail the symmetric 1% cost-prediction test but still meet the strict frozen additive budget because their PF error was overestimated. Conversely, 8 pass the 1% test but miss the strict frozen budget because even a small underestimation consumes more than the allocated PF-error share.

All 51 `current_m3` rows are conservative and meet the frozen budget, even though many fail the prediction criteria. The `two_term_center` one-term rows are also conservative. For `two_term_center` plus the two-term model, 9/17 pass strictly and 8/17 underestimate the PF error.

All eight strict misses occur in stretched BeH2 or H2O conditions, including their basis variants; the saved equilibrium, active-space, H-chain, and NH3 conditions do not show this under-budget direction.

The worst strict miss is `BeH2_stretch150_631g`: target excess 1.56343e-08 Hartree (9.81066e-05 epsilon), requiring only 0.0123408% more continuous cost than frozen. Over all 17 saved conditions, a uniform multiplier of 1.000123408 would remove these strict misses. This is an empirical margin for these saved conditions, not an unseen-system guarantee.

## A05 conclusion

The symmetric prediction thresholds do not directly measure operational harm. Many formally failed, conservative predictions remain safe but spend up to about 5.3% extra cost. The most accurate PF/model cell has the opposite issue: tiny one-sided underestimates create strict budget misses, although their maximum repair cost is about 0.0124%. Therefore model ranking should report direction and frozen-budget margin, not only absolute cost error.

## Scope

The 17 conditions are five correlated development clusters. QPE integer rounding, synthesis error, stochastic success probability, and state preparation are outside this saved-data audit.

## Files

- `frozen_budget_rows.csv`: all 102 frozen allocations and direct scores.
- `aggregate.csv`: PF/model outcomes and required empirical margins.
- `decision_contingency.csv`: prediction-pass versus frozen-pass tables.
- `frozen_budget_failures.csv`: the strict budget misses.
- `safe_prediction_rejections.csv`: prediction failures that remain safe.
- `cluster_summary.csv`: correlated-cluster summaries.
- `frozen_budget_outcomes.png`: lightweight comparison figure.
- `analysis.json` and `manifest.json`: summary and provenance.
