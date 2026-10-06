# Native backend inspection (no production calls)

`review_response/run_h01_approximate_state_calibration.py:_apply_pf_cpu` lines 445–474 takes `states` explicitly; its sparse group-gate product supports any compatible vector or column block. It uses the original ordered compact group eigensystems and merged `iter_s2_sequence_steps`, complex128, left multiplications, per-call sparse gate cache. No final dense full-PF matrix is required for this action.

`component_exponential` materializes small-component spectral exponentials as CSR. Fresh preprocessing uses component eigensolves (maximum saved block sizes N2 32 / CO 64); their costs and array identities must be audited separately. H01 `prepare_condition` also performs full-ground diagonalization and CISD construction: **do not use it to restore missing runtime inputs**.

H01 `_echo_points` explicitly computes expm_multiply(-i*t*H, U*state). Practical `proxy_point` computes <exp(+i*t*H)state|U*state>; algebraically the same imaginary echo with an arbitrary state substituted, but its current function hardcodes `system['cisd_state']`. An adapter would have to take an explicit state and preserve signed convention. No such production adapter is executed or declared ready by FS-C0.

SciPy CSR `expm_multiply` internal H matvecs/norm estimation are not exposed by these old counters. Saved exact-H action seconds are not a count of H matvecs. A future instrumented compatible wrapper or explicit unknown status and accepted cost contract is necessary. Error/uncertainty for arbitrary Ritz input and memory/wall caps remain unresolved. Historical H01/P03 spectral preprocessing is counted as inherited or cold preparation, never free total work.

Metadata-only inspection verifies 1568-dimensional sources, N2 81 groups / CO 99 groups, H/cache digests, fixed sector and energy origin. This does **not** verify currently missing production arrays. Runtime/backend readiness is false.
