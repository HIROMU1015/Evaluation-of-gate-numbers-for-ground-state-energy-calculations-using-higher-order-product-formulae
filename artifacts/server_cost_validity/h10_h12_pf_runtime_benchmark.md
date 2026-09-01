# H10/H12 PF GPU runtime benchmark

Recorded on 2026-09-01 with an NVIDIA A100-SXM4-40GB, Python 3.12.3,
Qiskit 1.3.0, and Qiskit Aer GPU 0.15.1. Aer used the statevector method in
double precision with one GPU per worker. The evolved state was consumed by
computing its norm and its overlap with the initial Hartree-Fock basis state;
the benchmark was therefore not an empty circuit loop.

All entries below use `t = 1.0`. The reported runtime is the median measured
wall-clock time after one warm-up execution. Peak memory is the total observed
GPU memory use (the pre-run baseline was 1 MiB).

| System | PF | r | Measured repeats | Initialization (s) | Transpile (s) | Median evolution (s) | Peak GPU memory (MiB) | Merged Pauli rotations | Norm | Initial-state overlap probability |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H10 (20 qubits) | `4th(m5_best)` | 2 | 1 | 45.323 | 111.960 | 284.506 | 443 | 310,146 | 0.999999999967 | 0.817213044059 |
| H10 (20 qubits) | `8th(Morales-Y8m10b)` | 2 | 1 | 46.392 | 212.878 | 543.508 | 443 | 591,906 | 0.999999999937 | 0.817210166018 |
| H12 (24 qubits) | `4th(m5_best)` | 1 | 2 | 201.854 | 131.531 | 2,721.092 | 683 | 324,822 | 0.999999999965 | 0.785873404770 |
| H12 (24 qubits) | `8th(Morales-Y8m10b)` | 1 | 2 | 200.559 | 248.562 | 5,193.491 | 683 | 619,842 | 0.999999999932 | 0.785809947178 |

H10 used one warm-up and one measured execution at `r = 2`. H12 used one
warm-up and two measured executions. Both H12 workers were intentionally
stopped after their successful `r = 1` results were saved, following the
instruction to stop before `r = 2`; consequently their raw JSON records retain
the top-level status `running`, while `results[0].success` is `true` and each
contains both completed measurements. For the same reason, the merged H12 JSON
has status `failed_or_partial`; this describes the unexecuted higher `r` values,
not a failure of either recorded `r = 1` calculation.

Raw records:

- `h10_pf_runtime_benchmark_workers/H10_m5_best_r2.json`
- `h10_pf_runtime_benchmark_workers/H10_y8m10b_r2.json`
- `h12_pf_runtime_benchmark.json`
- `h12_pf_runtime_benchmark_workers/H12_m5_best.json`
- `h12_pf_runtime_benchmark_workers/H12_y8m10b.json`
