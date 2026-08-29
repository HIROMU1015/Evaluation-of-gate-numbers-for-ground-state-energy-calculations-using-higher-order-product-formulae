# GPU server validation results (2026-08-29)

This index records the small JSON outputs retained for local review.

## Environment

- GPU: NVIDIA A100-SXM4-40GB
- NVIDIA driver: 560.35.05
- CUDA reported by `nvidia-smi`: 12.6
- Python: 3.12.3
- Qiskit: 1.3.0
- Qiskit Aer GPU: 0.15.1
- Aer devices: `CPU`, `GPU`
- Aer precision: double
- Worker processes per calculation: 1

## Result files

- [H2 CPU smoke](server_cpu_smoke/H2_cpu_smoke.json)
- [H2 GPU smoke](server_gpu_smoke/H2_gpu_smoke.json)
- [H4 GPU calculation](server_gpu_full/H4_gpu_full.json)
- [H5 GPU calculation](server_gpu_full/H5_gpu_full.json)

The H2 CPU/GPU error arrays agree within an absolute tolerance of `1e-13`.
All H2, H4, and H5 error values in these files are finite and positive.
The repository review test suite passed with `21 passed` in this environment.

## Interpretation note

The H4/H5 calculations used ten equally spaced times from `0.5` to `1.2`.
Some high-order free-slope fits do not recover the formal PF order over this
window, particularly for H5. Treat the stored fixed-order coefficients as run
outputs pending a separate fit-window/asymptotic-regime validation, rather than
as final scientific coefficients.
