# F01/F02/F05 HF bridge retry-1 numerical remediation

The first server run at commit `005c04b` correctly stopped with
`failed_numerical_validation`.  It reproduced the frozen Hamiltonians and
direct shifts, but two numerical conventions were not adequate for the fixed
gates:

1. the formal logarithm formed cancellations at effective order seven between
   coefficients on the D8 scale using only IEEE extended precision;
2. the principal matrix logarithm used an energy-origin-dependent cut even
   when the full PF spectrum wrapped around the unit circle.

Retry-1 does not change the frozen PF coefficients, time grids, thresholds,
Hamiltonians, committed pass/fail labels, or direct truth points.

## Formal-series reference

- D4, D6, and D8 are evaluated with 128-bit Arb complex ball matrices through
  `python-flint==0.9.0`.
- The required `complex128`/`clongdouble` comparison is retained.  Before that
  comparison, the scalar spectral midpoint of each grouped Hamiltonian is
  removed and its sum is restored only to H0.  Higher PF error operators are
  invariant under these commuting identity shifts.
- The Arb result is also compared directly with the `clongdouble` result.
- Artificial-matrix tests check invariance under large independent identity
  shifts and suppression of symmetry-forbidden orders.

## Finite-time logarithm

At each frozen time, PF Schur vectors are assigned to exact-H eigenvectors by a
global maximum-overlap assignment.  Exact energies choose only the integer
multiple of `2*pi` for each PF phase.  The unwrapped PF phases themselves form
the effective Hamiltonian.  The reported branch margin is the distance of the
PF-minus-exact relative phase from `+-pi`, which is invariant under a common
energy-origin shift.

The principal-log cut margin remains in the CSV as a diagnostic.  It is not
used as the retry gate because it changes under an arbitrary scalar shift of
the Hamiltonian.  An artificial test verifies that the reference-unwrapped
operator and margin are invariant under such a shift.

All three predeclared finite-log windows remain in the report.  Their recovery
errors are descriptive stability diagnostics; no window is selected after
seeing the result, and none replaces the formal Arb operators.
