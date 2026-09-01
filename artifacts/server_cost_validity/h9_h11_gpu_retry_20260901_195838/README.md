# H9--H11 GPU validation: partial checkpoint

This directory is a checkpoint of the completed pilot calculations as of
2026-09-01.  It is intentionally incomplete: the H11
`8th(Morales-Y8m10b)` pilot and all analytic-time refinement calculations were
still running or pending when this checkpoint was committed.

Only the completed JSON result files are versioned.  Live tmux logs, GPU-memory
sampling CSV files, and timing sidecars remain server-local.

| H chain | PF | fixed-order alpha | free-fit order | free-fit R^2 | PF elapsed (s) | rotations/step | FCI residual |
|---:|---|---:|---:|---:|---:|---:|---:|
| 9 | `4th(m5_best)` | 1.960961e-6 | 3.897535 | 0.999811 | 484.014 | 124724 | 8.389e-11 |
| 9 | `8th(Morales-Y8m10b)` | 1.040994e-9 | 7.473830 | 0.999130 | 922.738 | 237954 | 8.389e-11 |
| 10 | `4th(m5_best)` | 2.584070e-6 | 3.873974 | 0.999725 | 1571.013 | 192160 | 5.272e-11 |
| 10 | `8th(Morales-Y8m10b)` | 3.151885e-9 | 7.658341 | 0.999763 | 3123.706 | 366660 | 5.272e-11 |
| 11 | `4th(m5_best)` | 2.356144e-6 | 3.828295 | 0.999259 | 6038.569 | 282876 | 6.076e-11 |

The ground states were obtained with PySCF FCI and passed the configured
`1e-10` residual check.  SciPy `eigsh` was not used.  For H9, the recorded
worker visibility (`1,1`) shows that both logical workers were accidentally
mapped to physical GPU 1; the mapping bug was fixed after these runs.  The H9
numerical results remain usable, but its elapsed times are not representative
of two-GPU scaling.  H10 and H11 pilot timings also include contention from
concurrent validation work and should not be treated as isolated performance
benchmarks.

These are short-time pilot fits, not the final cost-validity analysis.
`C_ov/C_model` and analytic-optimum refinement results must be taken from the
later completed analysis rather than inferred from this checkpoint.
