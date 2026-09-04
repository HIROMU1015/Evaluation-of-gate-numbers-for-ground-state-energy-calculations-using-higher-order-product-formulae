# GPU template phase and reuse validation

Status: **complete**

## H6 fixed t=0 global-phase correction

Correction phase: `3.1415926535853376` rad. The same parameterized template was built/transpiled once and bound at all three times.

| t/t_ana | t | raw phase (rad) | corrected relative 2-norm | phase drift (rad) | Aer run (s) | result |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 0 | 3.14159265359 | 1.642e-12 | -0.000e+00 | 11.076 | PASS |
| 0.5 | 1.04021617097 | 3.14159265359 | 1.510e-12 | -9.725e-15 | 11.033 | PASS |
| 0.7 | 1.45630263936 | 3.14159265359 | 1.403e-12 | -1.189e-14 | 10.9561 | PASS |

## H8 parameterized-template reuse

The H6 validated analytic time remains a runtime-only surrogate because no saved H8-specific t_ana exists. No dense H8 PF unitary was built.

| run | t/t_ana | t | bind (s) | Aer run (s) | bind+run (s) | state norm |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.5 | 1.04021617097 | 1.72657 | 42.401 | 44.1279 | 0.999999999996 |
| 2 | 0.7 | 1.45630263936 | 1.72187 | 42.8557 | 44.5778 | 0.999999999996 |

Template build/transpile count: `1`; parameter-bind runs: `2`.
Warm-up was recorded separately (`1.130033494962845` s) and is excluded from the measured total.
Device-wide sampled peaks were H6 `861 MiB` and H8 `2063 MiB`. Per-process samples were unavailable, and unrelated jobs started while this run was active, so these are upper bounds rather than attributable benchmark memory.

This validates state application and timing only; it is not a PF eigenphase or e_direct calculation.
