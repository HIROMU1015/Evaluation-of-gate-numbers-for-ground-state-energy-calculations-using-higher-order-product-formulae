# X01 A03/A04: PF/model factorization and threshold sensitivity

Status: complete

No electronic-structure, PF-unitary, or direct-eigenvalue calculation was run. The inputs are the independently recomputed A01/A02 rows.

## A03: paired PF-by-model result

| PF | original one-term | refit one-term | two-term |
|---|---:|---:|---:|
| current_m3 | 3/17 | 3/17 | 16/17 |
| two_term_center | 11/17 | 12/17 | 17/17 |

The fair nested comparison is refit one-term versus two-term: both use the same three direct training points and the same normalized least-squares loss. It adds 13 passes for `current_m3` and 5 passes for `two_term_center`. Thus the model upgrade explains the larger part of the baseline recovery. At fixed two-term model, changing the PF adds one pass (16/17 to 17/17).

The original one-term model is retained as a legacy reference, not as a same-loss causal contrast: its leading coefficient comes from the frozen short-time perturbative fit. A three-term model is not fitted here because three training points for three coefficients leave zero training-residual degrees of freedom; using saved unseen points for fitting would change the information budget and contaminate this comparison.

## A04: one-at-a-time threshold sensitivity

The canonical thresholds remain the primary decision. Each diagnostic curve varies exactly one threshold; the other three remain canonical. Thresholds are not relaxed simultaneously.

At half the canonical threshold, two-term coverage is:

| varied threshold | current_m3 | two_term_center |
|---|---:|---:|
| eta_star | 14/17 | 17/17 |
| eta_min | 16/17 | 17/17 |
| eta_t | 16/17 | 17/17 |
| maximum_unseen_residual_over_epsilon | 16/17 | 17/17 |

The sole two-term baseline failure, `LiH_CAS2e4o`, fails 4 of 4 criteria: eta_star;eta_min;eta_t;maximum_unseen_residual_over_epsilon. It therefore cannot be rescued by moving only the 1% cost-prediction threshold; the observed 16/17 versus 17/17 difference is not a single near-boundary classification artifact.

## Dependence and scope

The 17 rows form five correlated analysis clusters: H-chain, NH3, BeH2, H2O, and LiH. Condition counts are not treated as 17 independent molecular families, and no population success interval is reported.

## Interpretation

The evidence supports a two-part conclusion. First, adding the t^6 term is the dominant reason both PFs become predictable. Second, the coefficient change retains a real but narrower incremental benefit: it resolves the LiH small-active-space case and produces a wider metric margin, at the previously measured direct-cost premium. Practical necessity is still not established; A05/A07 must test frozen-budget harm and cost-benefit.

## Files

- `factorial_summary.csv`: canonical PF x model cells.
- `paired_pf_model_effects.csv`: all paired PF, model, and interaction effects.
- `effect_summary.csv`: distribution summaries of paired effects.
- `threshold_sensitivity.csv`: one-at-a-time coverage curves.
- `threshold_pairwise.csv`: PF coverage differences and common-pass cost ratios.
- `failure_diagnostics.csv`: failed criteria and normalized margins per row.
- `cluster_summary.csv`: cluster-level counts without independence claims.
- `threshold_sensitivity.png`: lightweight diagnostic figure.
- `analysis.json` and `manifest.json`: machine-readable summary and provenance.
