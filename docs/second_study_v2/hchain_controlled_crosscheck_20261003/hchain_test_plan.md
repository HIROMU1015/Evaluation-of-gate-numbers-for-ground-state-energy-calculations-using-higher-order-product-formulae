# Preflight and future test plan

Preflight checks: verify exact Git commits and SHA-256 of relied-upon metadata; assert S1A formal classification D; assert the H-chain scaling PF list is m5/Y8; assert H-chain `T0/B0` are not silently set equal to `t_grid_star` or `t_ana`; assert all proposed candidate absolute times remain unresolved; validate CSV/JSON schemas, file hashes, zero scientific-action counters, and terminal status.

Future separately authorized execution needs synthetic unit tests for B2/H1 rule semantics, missing four-gamma frontier, q-based M1 access, candidate exact-time identity, source/cost mismatch rejection, and prediction-commit byte identity. No future test may silently open truth before prediction freeze. Those tests and execution are **not** run or implemented here.

This preflight uses Git metadata, protocol/source text, and artifact names. It does not inspect raw direct-shift values or rerun existing science.
