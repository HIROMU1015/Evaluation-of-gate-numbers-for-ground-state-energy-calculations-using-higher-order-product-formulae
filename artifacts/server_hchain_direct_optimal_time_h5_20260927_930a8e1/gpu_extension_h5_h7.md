# H-chain GPU direct extension: H5 and H7 interim scope

This extension records the user's 2026-09-27 instruction to execute only H5
and H7 for now. It narrows the server handoff derived from parent result
`c27e31e82ca55fc404ed33123cfd5d2c6a76bc35`; it does not change the fixed
grid, formulas, cost, branch rule, numerical gates, or precision.

The GPU backend constructs the complete conserved-sector PF unitary with
resident complex128 group eigensystems and exact dense cached S2 blocks. The
resulting unitary is transferred to the host and passed to the unchanged
complex128 SciPy Schur and continuous-branch implementation. Approximation,
rank reduction, truncation, projection, grid thinning, and lower precision
are forbidden.

H5/m5 is run first and checked against the parent CPU result and a direct
GPU-versus-CPU unitary comparison. H5/Y8 must reproduce the known branch-gate
failure without changing branch selection. H7/m5 and H7/Y8 may run only if
backend parity passes. H8 and H9 are outside this interim scope, so no H8
holdout decision or odd-family three-size fit is made. Execution stops after
H7.
