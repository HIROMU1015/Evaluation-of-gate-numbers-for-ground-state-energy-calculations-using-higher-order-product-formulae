# H-chain exact GPU direct optimum: H5/H7 interim report

- Status: `complete_H5_H7_interim_scope`
- Branch: `gpu-hchain-direct-optimal-time-scaling-h5-h7-20260927`
- H5 backend parity: `passed`
- H8/H9: not run or estimated in this user-limited execution.
- Odd-family scaling: not fit; the registered exploratory fit requires H5/H7/H9.

| system | PF | status | points | t_ana | t_grid* | t_grid*/t_ana | cost ratio vs t_ana | max branch difference (Ha) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| H5 | m5 | scorable | 31 | 2.59399493279 | 3.50189315927 | 1.35 | 0.624886839724 | 0 |
| H5 | y8 | not_scorable_gate_failure | 31 | 5.10035078486 | 6.37543848108 | 1.25 | 0.647768997707 | 0.0134158260484 |
| H7 | m5 | scorable | 31 | 2.17422823128 | 3.15263093535 | 1.45 | 0.638511699204 | 0 |
| H7 | y8 | scorable | 31 | 4.37921269414 | 4.81713396355 | 1.1 | 0.911038733496 | 0 |

The reported optimum is the minimum on the fixed discrete grid; it is not claimed as a continuous optimum.
The H5/Y8 value is retained as a failed-gate artifact and is not used scientifically.

Identity amendment v1.1 corrected only the expected H5 group count from 45 to 43. Parity amendment v1.2 compares exact CPU and GPU shifts at identical physical times without changing the 1e-9 Ha threshold.
