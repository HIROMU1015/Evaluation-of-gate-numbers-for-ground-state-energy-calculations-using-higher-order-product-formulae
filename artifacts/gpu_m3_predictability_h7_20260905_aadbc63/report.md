# Frozen m=3 H7 GPU direct validation

Status: **complete**

The PF unitary was constructed exactly on GPU in an exact symmetry block; the complete block was then diagonalized by CPU complex Schur. No iterative or projected eigensolver was used.

## H6 GPU/CPU gate

| Passed | signed-shift abs. difference (Ha) | cost relative difference | total time (s) |
|---|---:|---:|---:|
| True | 8.281e-16 | 6.387e-12 | 1.34 |

## H7 candidates

| Candidate | alpha | t_ana | t_pass/t_ana | first fail | grid-min t/t_ana | grid-min cost | pass | elapsed (s) |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| `m3_local_c1_r2_s007` | 1.647881e-05 | 1.179291 | 1.1 | 1.2 | 1.0 | 2.162107e+08 | True | 4.87 |
| `m3_local_c3_r2_s000` | 1.837262e-05 | 1.147650 | 1.2 | 1.4 | 1.0 | 2.227361e+08 | True | 21.69 |
| `m3_local_c2_r0_s000` | 2.344137e-05 | 1.079833 | 1.4 | None | 1.0 | 2.374543e+08 | True | 21.70 |

## Branch reliability

- `m3_local_c1_r2_s007`: min ground overlap 0.998301150706, min adjacent overlap 0.998290690035, max eigenpair residual 6.018e-14.
- `m3_local_c3_r2_s000`: min ground overlap 0.999970962039, min adjacent overlap 0.999966920108, max eigenpair residual 5.258e-14.
- `m3_local_c2_r0_s000`: min ground overlap 0.999140860494, min adjacent overlap 0.999136574480, max eigenpair residual 1.004e-14.

## Timing breakdown

- H6 preparation: 2.05 s; population sector 400, exact Z2 block 200.
- H7 preparation: 4.73 s; population sector 735, exact Z2 block 372.
- `m3_local_c1_r2_s007`: short-time fit 0.56 s, nine-point direct grid 4.87 s (GPU unitary builds 3.14 s, CPU Schur 1.30 s), GPU baseline/peak/delta 1/463/462 MiB.
- `m3_local_c3_r2_s000`: short-time fit 0.56 s, nine-point direct grid 21.69 s (GPU unitary builds 19.49 s, CPU Schur 1.69 s), GPU baseline/peak/delta 8655/9115/460 MiB.
- `m3_local_c2_r0_s000`: short-time fit 0.57 s, nine-point direct grid 21.70 s (GPU unitary builds 19.68 s, CPU Schur 1.47 s), GPU baseline/peak/delta 16847/17307/460 MiB.

## Scope and next estimate

This run stops at the fixed H7 grid. It does not refine the optimum, change coefficients or thresholds, run H8+, or use an approximate eigensolver.
For another H7 candidate on the same nine-point grid, the observed candidate elapsed time is the relevant estimate. The three candidates were assigned to physical GPUs 0--2 concurrently; GPUs 1 and 2 acquired other-process loads during the final run, and no process was stopped. From cubic scaling of the exact block operations, an H8 representative point should be budgeted at roughly 0.5--2 minutes and a nine-point candidate grid at roughly 5--15 minutes, pending an H8 timing probe. Any optimum refinement or H8 run requires confirmation.
