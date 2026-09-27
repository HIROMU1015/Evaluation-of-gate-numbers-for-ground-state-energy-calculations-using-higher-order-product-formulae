# H-chain direct optimal-time scaling amendment v1.1

The first execution stopped before any PF unitary was constructed.  The
inherited H6/H7 helper assumed a block alpha/beta state-vector ordering, while
the H2 small-system path produces an interleaved spin-orbital state.

Version 1.1 changes only the conserved-sector identification.  Both supported
conventions are tested against the nonzero support of the exact input state:

1. block alpha/beta positions;
2. interleaved even/odd positions.

Exactly one convention must produce a single population pair.  If neither is
unique, or if both are unique but imply different sector index sets, execution
stops before group spectra or PF action.  The selected convention is recorded
in every system result.

No scientific grid, PF, cost, threshold, branch rule, scaling model, or claim
scope changes.  The failed output is preserved and never reused.
