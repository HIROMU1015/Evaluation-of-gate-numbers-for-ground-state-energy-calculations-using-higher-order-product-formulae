# H8/H9 fixed m=3 direct-cost validation

## Scope

The three fourth-order m=3 candidates selected using H2/H4/H5 were kept
fixed and tested on H8 and H9. Each system used the declared short-time fit
protocol (`geomspace(0.06, 0.80, 15)`, consecutive five-point windows,
noise floor `5e-13` Hartree, free order within `4 +/- 0.2`, and
`R^2 >= 0.999`). The earliest eligible window determined `alpha` and
`t_ana`. Direct PF eigenvalue errors were then evaluated on

`t/t_ana = 0.1, 0.3, 0.5, 0.7, 0.9, 1.0, 1.1, 1.2, 1.4`.

The PF unitary was assembled on an NVIDIA A100-SXM4-40GB and the compact
symmetry block was diagonalized on the CPU. Independent candidates were run
on separate GPUs. The execution commit was
`a5f9512acb640f255cca5df21032a71aab10959a`; the recorded dirty state consists
only of untracked result and diagnostic files.

## Results

| System | Candidate role | Candidate | fit | alpha | t_ana | direct grid minimum | model-cost difference | eta_choice | 10% model range | pass |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| H8 | cost priority | `m3_local_c1_r2_s007` | yes | 2.561286e-5 | 1.056180 | 4.191882e8 | 1.90% | 0 | through 1.1 t_ana | yes |
| H8 | balanced | `m3_local_c3_r2_s000` | yes | 2.855766e-5 | 1.027831 | 4.318551e8 | 1.64% | 0 | through 1.2 t_ana | yes |
| H8 | predictability priority | `m3_local_c2_r0_s000` | yes | 3.643626e-5 | 0.967094 | 4.603531e8 | 1.34% | 0 | through 1.2 t_ana | yes |
| H9 | cost priority | `m3_local_c1_r2_s007` | yes | 2.209128e-5 | 1.095966 | 6.692373e8 | 1.94% | 0 | through 1.1 t_ana | yes |
| H9 | balanced | `m3_local_c3_r2_s000` | yes | 2.463112e-5 | 1.066550 | 6.894761e8 | 1.67% | 0 | through 1.2 t_ana | yes |
| H9 | predictability priority | `m3_local_c2_r0_s000` | yes | 3.142663e-5 | 1.003524 | 7.350494e8 | 1.36% | 0 | through 1.2 t_ana | yes |

All six cases selected the first five-point fit window, from `t=0.06` to
`0.1257657306`. The free-fit orders were 3.99886--3.99907 and all fit
`R^2` values exceeded 0.999999997.

For every candidate the directly evaluated grid minimum occurred at
`t=t_ana`, hence `eta_choice=0` on this fixed grid. This does not establish
that the continuous optimum is exactly `t_ana`; it establishes that the
analytic choice was optimal at the requested grid resolution. The direct
error at `t_ana` was 92.25--94.64% of the fourth-order model error, while the
corresponding minimum-cost prediction error remained only 1.34--1.94%.

## Numerical reliability and resources

All selected branches were also the maximum-ground-overlap branches. Across
all points, the maximum eigenpair residual was `1.255e-13`. The minimum
ground-overlap probability was 0.97659; the isolated lower value did not alter
branch selection. No signed-error zero crossing was observed near the
analytic schedule.

| System | time per candidate | peak GPU allocation above baseline |
|---|---:|---:|
| H8 | 162.6--177.0 s | 996 MiB |
| H9 | 1039.4--1073.5 s | 3012 MiB |

The cost-priority candidate remained the lowest-cost member of this frozen
m=3 set on both H8 and H9. It also had the narrowest verified 10% scaling
range (through `1.1 t_ana`, failing at `1.2 t_ana`); the other two candidates
passed through `1.2 t_ana` and failed at `1.4 t_ana`.

The machine-readable source of record is `summary.json`; the six per-candidate
JSON files retain all direct points, timings, branch diagnostics, environment
information, and GPU-memory samples.
