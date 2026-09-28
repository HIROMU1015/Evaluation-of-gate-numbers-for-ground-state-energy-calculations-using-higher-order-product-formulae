# P-SPEC-6 protocol draft fixed at D0

This document is the human-readable companion to `pf_spectral_information_pilot_protocol_draft.json`. D0 fixes the design; it does not authorize D1.

## Scientific question

At the six already-used HCl coordinates, determine whether the non-target spectral contribution to the finite-time exact-state echo is budget-relevant and compressible with a small amount of spectral information. The pilot must distinguish an oracle compression diagnostic from a truth-free implementable route.

## Fixed scope

- `current_m3` only; HCl equilibrium/stretch150 only.
- Coordinates are exactly `0.5/0.65/0.8 t_ana` using the six fixed `time_hex` values in the JSON protocol.
- No new coordinate, molecule, basis, PF, approximate-state method, proxy campaign, or threshold tuning.
- Existing full-spectrum cache may be reused only after identity verification. Otherwise, a later explicit D1 authorization may permit at most six existing-coordinate PF builds/eigendecompositions and two same-H exact-ground regenerations.

## Spectral and top-K definitions

The target is the circular phase cluster containing the saved branch. The cluster radius is `1e-8 rad`. Non-target contributions are

`c_j = p_j [sin(phi_relative,j) - sin(t delta_target)] / t`.

Two rankings must be reported: weight-ranked (`p_j` descending) and oracle-contribution-ranked (`|c_j|` descending). The latter is diagnostic only. Ties are broken by descending weight, ascending wrapped phase, and ascending cluster index. Evaluate K=`1,2,4,8,all`.

For each coordinate, allowance is the minimum original underestimation allowance among strategies selecting that exact condition/time. Report both the actual omitted signed residual and the conservative bound `2 q_omit/t`.

## Fixed low-dimensional gate

Low-dimensional compression requires K<=4 at all six coordinates, actual omitted residual <=25% of allowance, and the conservative bound <=100% of allowance. A prototype candidate additionally requires the weight-ranked result to pass and a concrete truth-free route with subspace dimension <=8, PF and H actions each <=8 per coordinate, no full dense eigensolve/direct-truth input, and peak memory <=4 GiB.

## Numerical and resource gates

All normalization/reconstruction/eigenpair/unitarity/exact-state/source-match tolerances are `1e-10` in their stated units; phase gap must be strictly above `1e-8 rad`; branch disagreement is zero. D1 is CPU-only, one process, one BLAS thread per backend, <=4 GiB peak memory, <=1800 seconds total, and zero GPU queries/allocations/kernels.

## Stop rule

D1, if separately authorized, must end as exactly one of: prototype candidate, information-cost/limit result, or closure of the spectral route. Every outcome stops with D2 unauthorized. Closed second-study status remains `complete_no_benefit`.
