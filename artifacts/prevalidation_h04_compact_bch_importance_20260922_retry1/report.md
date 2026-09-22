# H04: compact BCH and importance-selection audit

Status: **complete_with_findings**

## Outcome

The grouped partial-sum representation reproduces all stored H2/H4 D4 state actions with maximum relative error 1.406e-11. For H4/Yoshida, the representation reduces the leading grouped objects from 168560 raw commutators to 456 grouped terms (369.6x fewer).

This removes the H03 symbolic-generation blocker. It does not remove dense input group matrices or the exponential statevector representation.

## Method comparison

| system | PF | raw BCH terms | raw symbolic time (s) | grouped terms | grouped full action time (s, median over states) | max action rel. error |
|---|---|---:|---:|---:|---:|---:|
| H2 | yoshida4 | 6 | 0.022375 | 5 | 0.000218 | 6.642e-15 |
| H2 | current_m3 | 6 | 0.046453 | 5 | 0.000213 | 3.498e-15 |
| H2 | two_term_center | 6 | 0.046137 | 5 | 0.000213 | 5.196e-15 |
| H2 | m5_best | 6 | 0.083365 | 5 | 0.000216 | 8.934e-16 |
| H4 | yoshida4 | 168560 | 75.848738 | 456 | 0.034679 | 4.400e-13 |
| H4 | current_m3 | n/a | n/a | 456 | 0.034341 | 1.965e-12 |
| H4 | two_term_center | n/a | n/a | 456 | 0.034518 | 1.083e-11 |
| H4 | m5_best | n/a | n/a | 456 | 0.034544 | 1.406e-11 |

## Importance truncation

The norm-product heuristic is not monotone in signed-error accuracy: 13 of 24 PF/state curves worsen at least once when more terms are added. This is caused by cancellation between signed grouped components, so top-k truncation needs an a-posteriori remainder or sign-stability check.

The largest grouped-component cancellation ratio was 7.748e+00. The maximum exact-state direct formula-choice regret attributable to truncation was 14.90%. All PF choices match the full grouped result from 4/5 H2 terms and 25/456 H4 terms onward, but this rank stability is not an error bound.

## Literature and applicability

The grouped Y3/Y5 recurrence and norm-product importance score follow Maxwell et al., *Practical Estimation of Trotter Error for Hamiltonian Simulation*, arXiv:2606.30738v1, Eqs. (19)--(21). The paper derives the compact form for symmetric BCH and recursively defined formulas. Yoshida4 fits that setting. The three optimized repository formulas are arbitrary palindromic S2 compositions, so this audit derives their universal fifth-order composition coefficients independently and validates them against F01; it does not assume that their labels imply Suzuki recursion.

The paper's electronic-structure application uses CDF fragments with a strong norm hierarchy. The present H-chain groups and PF-selection target do not share that partition assumption. Failure of aggressive top-k pruning here does not contradict the paper's application result.

## Decision

Adopt the full grouped representation as the H03/H04 D2 backend candidate. Do not use norm-only top-k pruning as a selector guarantee. If pruning is needed at larger scale, require signed partial-sum convergence and PF-ranking stability, or evaluate a certified remainder.

## Files

- `audit.json`: protocol, checks, summaries, and conclusions.
- `method_comparison.csv`: naive versus grouped counts, time, and accuracy.
- `state_action_summary.csv`: full compact action validation.
- `grouped_components.csv`: signed grouped contributions and importance ranks.
- `importance_truncation.csv`: top-k accuracy and cancellation diagnostics.
- `selection_regret.csv`: top-k PF choice and regret.
- `manifest.json`: source, input, and artifact hashes.
