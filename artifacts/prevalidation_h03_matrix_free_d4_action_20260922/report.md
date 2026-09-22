# H03: matrix-free D4 state-action audit

Status: **complete_with_scaling_blocker**

## H2 reference comparison

| PF | symbolic expansion (s) | dense D4 difference | max action rel. error | streaming actions/vectors | cached actions/vectors | reuse |
|---|---:|---:|---:|---:|---:|---:|
| yoshida4 | 0.0224 | 3.771e-18 | 2.469e-15 | 150/3 | 60/62 | 60.0% |
| current_m3 | 0.0465 | 6.061e-20 | 2.325e-15 | 150/3 | 60/62 | 60.0% |
| two_term_center | 0.0461 | 6.451e-20 | 2.977e-15 | 150/3 | 60/62 | 60.0% |
| m5_best | 0.0834 | 1.468e-20 | 1.400e-15 | 150/3 | 60/62 | 60.0% |

All 24 matrix-free action paths agree with stored F01 D4 actions to at most 2.977e-15 relative error; expectations agree to 1.193e-18 Ha.

The streaming route uses 150 group-Hamiltonian actions and three logical statevector slots. Prefix caching reduces this to 60 actions (60% reuse) but retains 62 logical statevectors. Thus action reuse is a time-memory choice, not a free improvement.

## Scaling boundary

| dimension | dense D4 (s) | streaming (s) | cached (s) | dense D4 bytes | stream vectors | cached vectors | input groups |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 6.3405e-05 | 1.3101e-04 | 1.1086e-04 | 256 | 192 | 3968 | 512 |
| 16 | 1.3835e-04 | 1.4128e-04 | 1.1511e-04 | 4096 | 768 | 15872 | 8192 |
| 32 | 5.6638e-04 | 1.8203e-04 | 1.3516e-04 | 16384 | 1536 | 31744 | 32768 |
| 64 | 1.7192e-03 | 4.8614e-04 | 3.1709e-04 | 65536 | 3072 | 63488 | 131072 |
| 128 | 4.7767e-03 | 6.2509e-04 | 3.8925e-04 | 262144 | 6144 | 126976 | 524288 |

For H4/Yoshida with 13 groups, leading-order symbolic generation alone took 75.85 s and produced 168560 raw D4 commutator terms. The predeclared stop threshold was exceeded, so word expansion and state action were not attempted for H4.

## Decision

The state-action backend is numerically valid and avoids the incremental dense D4 matrix, but the naive symbolic BCH generator is already the dominant bottleneck at 13 groups. Proceed to H04 compact/selected representations before claiming an operational D2 estimator.

## Scope and memory boundary

All current group Hamiltonians and statevectors are dense. Avoiding D4 removes one additional O(d^2) matrix, but input group storage remains O(G d^2), and each retained statevector remains O(d), exponential in qubit count when represented densely. No large-system scalability claim is made.

## Files

- `audit.json`: checks, timing, operation counts, and conclusions.
- `h2_formula_summary.csv`: symbolic/dense reference measurements.
- `h2_state_actions.csv`: exact/HF/CISD streaming and cached actions.
- `synthetic_scaling.csv`: dimension scaling benchmark.
- `h4_symbolic_boundary.csv`: 13-group stopping result.
- `manifest.json`: source, input, and artifact hashes.
