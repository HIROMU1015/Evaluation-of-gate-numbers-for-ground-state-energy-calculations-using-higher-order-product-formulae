# B01: time-evolution sign, unit, and constant audit

Status: complete

The current dense/component PF path is numerically consistent with `exp(+i H tau)`. The native Qiskit `PauliEvolutionGate` uses `exp(-i H tau)`; current Qiskit diagnostics that target the repository convention explicitly pass `-tau`. These two conventions must not be mixed without the corresponding phase-reference change.

## Numerical checks

- Small-matrix sign/negative-time checks: 8/8 passed; maximum ordinary residual 1.85e-11.
- Constant-shift checks: 2/2 passed; maximum corrected bias change 6.62e-16 Hartree.
- Hartree/atomic-time checks: 3/3 passed.
- Angstrom/Bohr and nuclear restoration checks: 7/7 passed; maximum residual 1.7e-11.

For `H -> H + c I`, the PF unitary acquires `exp(+i c tau)` and the signed PF eigenvalue bias is unchanged when the reference energy is also shifted by `c`. Omitting that energy correction reproduces the constant shift, confirming that it would remain observable in a controlled-unitary phase.

## Unit and constant interpretation

The coordinate sentinel used H2/STO-3G at 0.74 Angstrom = 1.398397332178146 Bohr. Nuclear repulsion was removed and restored independently in an FCI calculation. Evolution times are atomic time units (`Hartree^-1` with hbar=1); one unit is 2.4188843265857e-17 seconds.

The current molecular runner explicitly sets `molecule.unit = "Angstrom"`, removes the complete JW identity coefficient from every PF group, uses the matching constant-free ground energy, and records the removed coefficient. Nuclear repulsion and the final JW identity coefficient are conceptually distinct because fermion-to-qubit transformation can add further identity contributions.

## Caveats

- Many saved fields are named only `time`; their atomic-unit meaning is implicit rather than encoded in every field name.
- Legacy Qiskit plotting uses the native `-i` convention consistently, while current direct-eigenphase work uses `+i`. Cross-path data require an explicit convention tag.
- This B01 test validates conventions and exact constant cancellation, not PF accuracy on an additional molecule.

## Files

- `small_matrix_checks.csv`: sign, negative-time, and Qiskit sentinels.
- `constant_shift_checks.csv`: corrected and uncorrected identity shifts.
- `energy_time_unit_checks.csv`: Hartree and atomic-time conversion.
- `coordinate_nuclear_checks.csv`: Angstrom/Bohr and nuclear restoration.
- `implementation_paths.csv`: source paths, conventions, and hashes.
- `audit.json` and `manifest.json`: complete summary and provenance.
