# D04: equal classical-budget comparison

Status: **complete_with_findings**

This is a cost audit on the existing H2/H4 development data. The H05 time designs and coefficients were not changed. All direct methods remain oracle-assisted because the saved branch rule uses the exact ground state.

## End-to-end method summary

| method | direct points | residual pass | worst residual/epsilon | median warm s | median cold s | median PF exponentials | median estimated peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| direct_fixed_a4_2_tail | 2 | 8/8 | 2.8295e-02 | 2.1762e-02 | 2.4315e-01 | 96 | 0.4039 |
| direct_fixed_a4_3_tail | 3 | 8/8 | 3.3577e-02 | 2.3510e-02 | 2.4490e-01 | 144 | 0.4039 |
| direct_fixed_a4_5_tail | 5 | 8/8 | 3.5292e-02 | 2.6891e-02 | 2.4828e-01 | 240 | 0.4039 |
| direct_free_3_tail | 3 | 7/8 | 5.1427e-02 | 5.2295e-03 | 2.2662e-01 | 144 | 0.2997 |
| direct_free_5_tail | 5 | 8/8 | 4.7418e-02 | 8.5570e-03 | 2.2995e-01 | 240 | 0.2997 |
| dense_bch_order8 | 0 | 8/8 | 2.4590e-12 | 5.9836e-02 | 2.8123e-01 | 0 | 0.8703 |

## Same-point comparison

| points | fixed-a4 method | free method | fixed/free median-time ratio | fixed/free worst residual |
|---:|---|---|---:|---:|
| 3 | direct_fixed_a4_3_tail | direct_free_3_tail | 4.4956 | 3.3577e-02 / 5.1427e-02 |
| 5 | direct_fixed_a4_5_tail | direct_free_5_tail | 3.1426 | 3.5292e-02 / 4.7418e-02 |

## Findings

The fixed-a4 two-point design retains the H05 result of 8/8 residual passes. After charging compact-D4 acquisition, it is faster than the free five-point fit in 1/8 conditions and uses no more estimated peak memory in 0/8.

At the same three direct points, fixed a4 passes 8/8 versus 7/8 for the free fit, but the fixed route has median wall-time ratio 4.496. The extra prior coefficient is therefore an additional classical resource, not a free reduction in information.

The zero-direct-point dense order-8 BCH route passes 8/8, but its median marginal time is 6.99 times the free five-point route and it materializes dense operator series. This is a small-system mechanism reference, not a scalable acquisition route.

## Decision

The fixed-a4 two-point route is a valid few-direct-point claim, but it is not a uniform end-to-end resource reduction after charging a4 acquisition. Use point count, wall time, and memory as separate claims and carry the two-point design only as a preregistered future hold-out candidate.

Report point-count, warm-cache time, cold preparation-inclusive time, PF exponential count, compact group-matvec count, and estimated memory separately. Do not convert unlike group matvecs and matrix exponentials into a single operation count.

## Scope

The two-point time design was selected on these same H-chain development conditions. Timing it does not turn it into an independent hold-out result. The measured CPU results do not override or retrofit the frozen P0-3 protocol.

## Files

- `direct_point_timing.csv`: repeated unitary-build and Schur timings.
- `method_resources.csv`: condition-level end-to-end resource ledger.
- `method_summary.csv`: method-level accuracy/resource summary.
- `same_point_comparison.csv`: fixed versus free fits at equal point count.
- `equal_time_frontier.csv`: best method under predeclared method budgets.
- `dense_bch_timing.csv`: D4/D6/D8 dense construction timing and checks.
- `audit.json`, `manifest.json`: machine-readable conclusions and hashes.
