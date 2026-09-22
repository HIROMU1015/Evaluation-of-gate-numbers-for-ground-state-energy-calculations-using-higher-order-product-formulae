# N2/CO three-point versus five-point two-term reanalysis

Status: **complete**

This is a reanalysis of the pre-specified information-count ablation in the frozen N2/CO holdout. No new PF points were computed.

| PF | three-point pass | five-point pass | base budget (3/5) | +1% budget (3/5) |
|---|---:|---:|---:|---:|
| `yoshida4` | 4/4 | 4/4 | 1/4; 1/4 | 4/4; 4/4 |
| `current_m3` | 4/4 | 4/4 | 4/4; 4/4 | 4/4; 4/4 |
| `two_term_center` | 4/4 | 4/4 | 2/4; 2/4 | 4/4; 4/4 |
| `m5_best` | 0/4 | 0/4 | 1/4; 1/4 | 1/4; 1/4 |

All 16 PF/condition pass decisions, base-budget decisions, and 1% margin decisions agree between the three- and five-point fits. Yoshida 4th order, `current_m3`, and `two_term_center` pass 4/4 with both fits; `m5_best` passes 0/4 with both.

## Decision

Freeze the three-point two-term fit at `0.1, 0.2, 0.3 t_ana` as the reduced-calibration candidate for the current frozen-core active-space scope. Retain the five-point fit as the reference and audit rule.

This does not show that three points are sufficient for full-electron systems or arbitrary molecules. The comparison uses the same holdout as the five-point result, although the three-point ablation was fixed before those results were inspected.
