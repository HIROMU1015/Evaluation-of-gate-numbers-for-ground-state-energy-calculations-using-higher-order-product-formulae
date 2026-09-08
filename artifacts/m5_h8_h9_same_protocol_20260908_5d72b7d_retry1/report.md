# H8/H9 m5 same-protocol comparison

The m5 short-time fits and nine-point direct sweeps use exactly the same declared protocol as the frozen m=3 validation.

| System | alpha | t_ana | t_pass/t_ana | t_fail/t_ana | eta_schedule | eta_grid | eta_choice | grid min cost | C_valid^min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H8 | 2.2492024e-06 | 1.940194 | 0.5 | 0.7 | 11.944% | 41.841% | 26.707% | 2.5735781e+08 | 5.9077302e+08 |
| H9 | 1.9398028e-06 | 2.013321 | 0.5 | 0.7 | 14.949% | 66.774% | 45.085% | 3.4964052e+08 | 9.4366521e+08 |

## Cost-priority m=3 / m5 ratios

Ratios below one favor the m=3 candidate.

| System | direct cost at each t_ana | nine-point grid minimum | 10% valid-range minimum |
|---|---:|---:|---:|
| H8 | 1.285497 | 1.628815 | 0.709559 |
| H9 | 1.319273 | 1.914072 | 0.709189 |

## Separate H9 wide-time sensitivity

The previously known narrow cancellation point was at old-scale factor 1.24 (absolute t=2.500277), with direct cost 4.0091797e+08. It is not included in the common nine-point comparison.

No optimum refinement or H10 computation was performed.
