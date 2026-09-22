# H05: a6/a8 acquisition-method comparison

Status: **complete_with_findings**

No new direct PF eigenvalue points were generated. Existing signed F01 points, stored F01 D6/D8 operators, H01 states, F02 mechanism references, and the H04 compact D4 action backend were reused.

## Method summary

| method | direct points | a6 signs | a8 signs | residual pass | worst residual/epsilon | median residual/epsilon |
|---|---:|---:|---:|---:|---:|---:|
| bch_cisd_response | 0 | 8/8 | 8/8 | 7/8 | 5.181e+00 | 2.774e-05 |
| bch_exact_d8_diagonal | 0 | 8/8 | 7/8 | 6/8 | 8.117e-01 | 2.530e-04 |
| bch_exact_response | 0 | 8/8 | 8/8 | 8/8 | 2.459e-12 | 7.196e-16 |
| bch_hf_response | 0 | 2/8 | 3/8 | 4/8 | 7.845e+01 | 6.233e-02 |
| direct_fixed_a4_2_tail | 2 | 8/8 | 8/8 | 8/8 | 2.829e-02 | 4.079e-06 |
| direct_fixed_a4_3_tail | 3 | 8/8 | 8/8 | 8/8 | 3.358e-02 | 5.338e-06 |
| direct_fixed_a4_5_tail | 5 | 8/8 | 8/8 | 8/8 | 3.529e-02 | 5.685e-06 |
| direct_free_3_tail | 3 | 8/8 | 8/8 | 7/8 | 5.143e-02 | 8.241e-06 |
| direct_free_5_tail | 5 | 8/8 | 8/8 | 8/8 | 4.742e-02 | 7.718e-06 |
| direct_order12_16 | 16 | 8/8 | 7/8 | 7/8 | 1.456e+00 | 2.787e-05 |

## Findings

The exact-state BCH plus projected response route reproduces a6/a8 in 8/8 conditions and its largest response residual is 2.429e-18. The response equation therefore supplies the D4-mixing part of a8 without constructing D4, but it still assumes that D6 and D8 are available.

Using <D8> alone passes the finite-time residual threshold in only 6/8 conditions. State mixing cannot be dropped uniformly.

Among the direct methods, the best declared few-point method is `direct_fixed_a4_2_tail` with 8/8 residual passes. Its worst residual is 2.829e-02 epsilon. This is a promising reduced-point calibration, but it requires an exact leading a4 and two direct PF eigenvalue points. The high-tail design was chosen and assessed on the same H-chain development data, so this is not an unused-system guarantee.

The free five-point fit also passes 8/8, but its worst residual is 4.742e-02 epsilon, close to the 0.05 threshold. By contrast, the 16-point order-12 fit passes only 7/8 because adding points and coefficients does not cure the cancellation-sensitive far extrapolation.

HF response passes 4/8 and CISD response passes 7/8. Approximate-state energy quality therefore does not by itself guarantee higher-order coefficient quality, consistent with H01/H02.

## Cost boundary

The saved online timings cover grouped D4 state action, dense D6/D8 matrix-vector products, and the small projected solve. They exclude the classical construction of D6/D8 and the original cost of the reused direct PF eigenvalue points. Consequently they are diagnostic timings, not a fair end-to-end wall-time ranking.

## Decision

The response identity is accepted as the correct inexpensive mixing correction. For practical calibration, freeze the exact-a4 plus two-high-time-point design as the next holdout candidate. Do not call it universally validated until it is tested without retuning on unused Hamiltonians. Pure BCH acquisition still lacks an end-to-end cheap route because D8 construction remains the bottleneck.

## Files

- `audit.json`: protocol, checks, summaries, and conclusions.
- `method_comparison.csv`: condition-level coefficient and t* residual results.
- `method_summary.csv`: per-method worst cases and pass counts.
- `response_diagnostics.csv`: compact-D4 response solves for exact/HF/CISD.
- `direct_fit_diagnostics.csv`: reused point designs, conditioning, and fit residuals.
- `reference_tstar.csv`: exact three-term model evaluation times.
- `manifest.json`: source, input, and artifact hashes.
