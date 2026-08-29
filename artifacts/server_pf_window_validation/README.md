# PF time-window validation on the GPU server

These files record the H4/H5 CPU/GPU sweeps and H2 direct-diagonalization
checks used to choose numerical-noise-aware fit windows for the new product
formulas. The complete machine-readable analysis is
[`pf_window_analysis.json`](pf_window_analysis.json).

## Environment

- GPU: NVIDIA A100-SXM4-40GB (40,960 MiB), driver 560.35.05
- CUDA: 12.6 (`nvidia-smi` reported compatibility version)
- Python: 3.12.3
- Qiskit: 1.3.0
- Qiskit Aer GPU: 0.15.1
- Aer devices: `CPU`, `GPU`
- Aer method/precision: `statevector`, `double`
- One process and one visible GPU per GPU job

The existing server virtual environment at
`/home/AbeHiromu/venvs/trotter-common` was used. No system package, CUDA
driver, shared Conda environment, or other user's process was changed.

## Sweeps and results

The fourth-order comparison used 15 linearly spaced points over
`t=0.12--0.8`. Five-point rolling fits recover fourth order for both
systems. The fixed-order coefficients and ratios are:

| System | `4th(new_2)` | `4th(m5_best)` | new_2 / m5_best |
| --- | ---: | ---: | ---: |
| H4 | 6.59316e-5 | 1.12515e-6 | 58.60 |
| H5 | 4.15406e-5 | 7.07413e-7 | 58.72 |

The eighth-order comparison used 16 points over `t=0.9--1.2`. The best
five-point rolling fits have slopes 7.964/8.004 for H4 and 7.963/8.019 for
H5 (legacy Morales/Y8m10b). The fixed-order coefficient improvement is
306.2x for H4 and 658.4x for H5 in favor of Y8m10b.

YP8m8 was additionally sampled at 11 points over `t=0.8--1.05`, and QIC
m=17 at 15 points over `t=0.9--1.25`. At H4/H5 precision, the formal-order
asymptotic region is below the GPU numerical floor. Once the error is safely
above the floor, the observed local slopes have already moved to roughly
10--11 for YP8m8 and 12 for QIC m=17. These GPU windows should therefore not
be used to infer the formal order.

The independent dense H2 diagonalization provides the small-system check:

| PF | Selected H2 window | Free-fit order | R2 |
| --- | ---: | ---: | ---: |
| `8th(Morales-YP8m8)` | 0.55557--0.61564 | 7.9605 | 0.999935 |
| `10th(Morales-QIC-m17)` | 0.77055--0.81709 | 9.8223 | 0.983291 |

The 10th-order H2 window is narrow and close to double-precision noise, so
its fitted order is less stable than the YP8m8 result. The published
coefficient/order-condition tests remain the primary algebraic validation;
the H2 diagonalization is an independent numerical cross-check.

## Noise-floor rule

There is no global `min_fit_error=5e-15` cutoff. For each H-chain/PF pair,
the three lowest-signal points of matching CPU and GPU sweeps are selected.
The mask floor is five times the maximum absolute CPU/GPU difference among
those points (and at least machine epsilon). H2 uses the analogous
direct-diagonalization/perturbative-estimator difference. A rolling window
is eligible only when all five errors exceed that pair-specific floor.

The resulting H4/H5 floors span approximately `6.0e-12--7.2e-11` Ha; see
`noise_floor_hartree`, `noise_floor_method`, and each selected window in the
analysis JSON.

## File layout

- `cpu_4th/`, `gpu_4th/`: H4/H5 fourth-order comparison
- `cpu_8th/`, `gpu_8th/`: H4/H5 eighth-order comparison
- `cpu_high_order/`: CPU reference for the broad YP8m8/QIC m=17 GPU sweep
- `gpu_yp8_targeted/`, `gpu_10th_targeted/`: targeted high-order GPU grids
- `H2_high_order_dense_diagonalization.json`: dense H2 cross-check
- `H2_direct_diagonalization.json`: earlier broad H2 cross-check retained for
  provenance
- `pf_window_analysis.json`: merged floors, masks, rolling fits, and source
  paths

All recorded GPU errors are finite and strictly positive. The raw scripts
write `min_fit_error=0` intentionally; masking is performed afterward with
the per-system/PF rule above so the original data remain available.
