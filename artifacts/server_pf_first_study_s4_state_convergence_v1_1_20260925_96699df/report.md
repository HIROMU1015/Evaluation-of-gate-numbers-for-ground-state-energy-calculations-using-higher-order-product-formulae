# First-study S4 state-convergence diagnostic

Status: **complete_no_benefit**

This is a fixed development comparison, not an independent holdout.
The truncated/full-CISD disagreement is a local CISD-tail diagnostic and not a rigorous exact-state error bound.

- Frozen prediction SHA-256: `47cdef9b52ea73feef0c005229cb9a482ee8e95afff87f038ff8461549f1c729`.
- New direct truth coordinates: 72.
- Inserted direct coordinates: 60.
- New uniform anchor coordinates: 12.
- Saved-anchor recomputations: 0.
- Decision: **no_benefit**.
- Targeted gamma=1.01 unsafe count: 0.
- Targeted mean original-grid regret: 0.4284159472315503.

S5 is permitted only when the fixed S4 outcome is benefit.

## v1.1 anchor amendment

The parent Phase-A predictions were reused byte-for-byte. The v1 saved-anchor availability preflight failed before direct calculation. All 12 condition/formula groups therefore use the preregistered new anchor at 0.5 times their minimum inserted coordinate; each anchor is counted as a new direct coordinate.
