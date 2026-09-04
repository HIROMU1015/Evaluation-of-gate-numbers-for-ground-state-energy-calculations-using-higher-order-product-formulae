# Sparse-style PF smoke benchmark

Only one `4th(m5_best)` PF application was measured. No iterative, moment/Ritz, Krylov, or dense-PF eigenvalue solver was run. H8 uses the H6 analytic time as a documented runtime-only surrogate because no H8-specific saved `t_ana` exists.

The H6 orbital basis, Hamiltonian, ground state, sector, and group spectra were prepared once and shared by all three methods. Shared preparation time: `7.96269 s` (not repeated per method).

| 系 | 方式 | 前処理 (s) | 構築 (s) | PF作用 (s) | 総時間 (s) | GPUメモリ | H6相対差 |
|---|---|---:|---:|---:|---:|---:|---:|
| H6 | CPU dense | 0.123907 | 5.43236 | 0.000149879 | 5.56239 | n/a | n/a |
| H6 | GPU dense | 0.149635 | 0.0986783 | 8.383e-05 | 1.82203 | 703 MiB peak (702 MiB delta) | 9.004e-15 |
| H6 | GPU matrix-free | 6.39709 | n/a | 11.1864 | 19.5202 | 427 MiB peak (426 MiB delta) | 1.509e-12 |
| H8 | GPU matrix-free | 29.9798 | n/a | 42.5889 | 75.1873 | 427 MiB peak (426 MiB delta) | n/a |

## Speed ratios

```json
{
  "cpu_dense_build_plus_matvec_over_matrix_free_run": 0.48563566875388736,
  "cpu_dense_cold_total_over_matrix_free_total": 0.284955284113997,
  "cpu_dense_reused_matvec_over_matrix_free_run": 1.3398338781351083e-05,
  "gpu_dense_build_plus_matvec_over_matrix_free_run": 0.008828778669865856,
  "gpu_dense_reused_matvec_over_matrix_free_run": 7.493926655397546e-06
}
```

## Conclusions

1. H6 GPU matrix-free versus dense reference: **PASS** at relative 2-norm tolerance `1e-10` after global-phase alignment.
2. Fastest H6 reused action: **GPU dense reused matvec**. Fastest action including dense-unitary construction: **GPU dense build + matvec**.
3. H8 matrix-free: **completed**; PF action `42.5889 s`, total `75.1873 s`, GPU memory `427 MiB peak (426 MiB delta)`. This one-action smoke test is not an `e_direct` result.
