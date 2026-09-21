# B02: PF coefficient rounding and formal-order audit

Status: complete

The audit expands each symmetric S2 composition in the complete noncommutative X/Y word basis through its declared order. Thus all operator order conditions are checked; odd power sums are retained only as diagnostics.

## Stored coefficients

| formula | order | complete hard linf | p+1 linf | lower-order crossover tau | pass |
|---|---:|---:|---:|---:|---|
| Yoshida 4th | 4 | 2.22045e-16 | 0.10418 | 0.000214864 | True |
| 4th(new_2), printed registry | 4 | 1.22436e-09 | 0.00444279 | 0.000524959 | False |
| 4th(new_2), projected comparison value | 4 | 1.91379e-15 | 0.00444279 | 6.56325e-07 | True |
| 4th(m5_best) | 4 | 6.63022e-18 | 0.000362215 | 1.35295e-07 | True |
| current_m3 | 4 | 9.31573e-16 | 0.00106344 | 0.000477988 | True |
| two_term_center | 4 | 1.53943e-15 | 0.0010949 | 0.000474517 | True |
| joint_refine_r0_s0046 | 4 | 1.53557e-15 | 0.011267 | 0.000362376 | True |
| Yoshida 6th m=3 | 6 | 1.10436e-15 | 0.00574672 | 0.000662099 | True |
| Yoshida 8th | 8 | 7.84355e-13 | 6.59285 | 0.00893223 | True |
| Morales Y8m10b | 8 | 5.06579e-18 | 9.53783e-07 | 0.0132089 | True |

All 9/9 coefficient sets actually used by the unified comparison pass the declared `1e-12` complete-word threshold.

The public printed `4th(new_2)` registry value is the exception outside that production set: its complete hard residual is 1.22436e-09, whereas the explicitly projected comparison value is 1.91379e-15. The maximum coefficient correction is only 9.3684e-09.

## Higher-order findings

The stored Yoshida eighth-order literals have complete hard residual 7.84355e-13, close to the audit threshold, while stored Morales Y8m10b has 5.06579e-18. The exact published decimal-literal variants are reported separately and are never silently substituted for the float coefficients executed by Python.

In the explicit decimal-rounding sweep, Yoshida eighth order first passes at 16 significant digits; Yoshida sixth order at 14, and Morales Y8m10b at 12. The eight-digit printed `new_2` source never passes without constraint projection.

The moment-only negative control satisfies normalization and the 3rd, 5th, and 7th power sums within `1e-12`, yet has an order-condition residual of 1.78475. This directly confirms that odd moments alone do not establish sixth or eighth order.

## Interpretation

The largest normalized-generator algebraic crossover among production candidates is 0.0132089. This uses formal generators with unit coefficient scale. A molecular crossover also depends on Hamiltonian-group norms and word contractions, so it must not be compared directly with the physical short-time grid minimum `0.02`. The audit finds no failed production coefficient set, but does not by itself rule coefficient rounding in or out as the cause of a molecule-specific breakdown.

Projection changes the deterministic two-term sentinel most strongly at very small time; at `t=0.5` its projected/printed unitary-error ratio is 1.00000321. The projected PF remains a separately labeled coefficient set.

## Files

- `formula_variants.csv`: stored and source/high-precision summaries.
- `degree_residuals.csv`: complete word residual norms by degree.
- `word_condition_residuals.csv`: every checked hard-order word.
- `rounding_sensitivity.csv`: 6--16 significant-digit sweep.
- `projection_comparison.csv`: printed versus projected `new_2`.
- `moment_only_control.csv`: proof that odd moments are insufficient.
- `audit.json` and `manifest.json`: summary and provenance.
