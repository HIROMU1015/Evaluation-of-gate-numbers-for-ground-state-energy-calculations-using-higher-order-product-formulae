# D2-A test plan

These tests are designed during D2-Prep. Scientific D2-A execution is not part of this commit.

## Pure synthetic unit tests

1. Diagonal H/U with a known sign, global shift and unwrap integer.
2. A small-residual U eigenpair connected to an excited H state is not labeled certified ground.
3. A block-diagonal H with an invisible lower block returns only an empirical reference claim.
4. Nearly dependent Krylov vectors trigger deterministic breakdown without restart.
5. Close overlap scores inside the fixed numerical tolerance return `branch_indeterminate`.
6. A nonunitary projected `T_m` uses the full-action residual after unit-circle projection.
7. `U_P(t)^l` is not replaced by `U_P(l*t)`.
8. `Q^*HQ` is formed from H actions and is not treated as Toeplitz.
9. An exact `U=exp(iHt)` control reports projection-induced false shift rather than silently calling it PF error.
10. Prefixes `m=1,2,4,8` reuse one chain and never exceed eight PF actions or eight H matvecs.

## Access and leakage tests

1. Estimator accepts only `PredictorSystemView`.
2. Predictor import graph excludes D1 truth tables, Phase B direct tables, full eigensolvers and scorer modules.
3. Attempts to access exact E0, exact vectors, target IDs, true gaps, `q_omit`, direct shifts or scoring labels fail.
4. Predictor output is byte-frozen before scorer can open truth.
5. Scorer detects any changed prediction hash, branch, unwrap, `e_use` or B.
6. Existing source/runtime identities must match before the predictor opens a system cache.

## Resource tests

1. Count PF per-vector actions independently of Python/block calls.
2. Count component-gate materializations and sparse multiplies.
3. Count H matvec and H exponential action separately.
4. Gate-cache and basis memory are recorded independently.
5. Restart, a new state, a new anchor or a seventh coordinate is rejected.
6. Full-H diagonalization and full-PF construction/eigendecomposition are zero in predictor tests.
7. GPU import/query/allocation/kernel counts remain zero.

## Scoring tests

1. `K_current_m3` is the only K appearing in QPE cost calculations.
2. Truth cannot rescue predictor abstention or ambiguity.
3. Unsafe points are reported before budget comparison.
4. The fixed baseline frontier is unchanged after scoring.
5. Prototype, information-cost-limit and close-route statuses are mutually exclusive and all stop with D2-B false.

## Test order for a later authorized bundle

1. Static JSON/schema/source-manifest checks.
2. Synthetic estimator and leakage tests only.
3. Existing review tests that do not invoke molecular science.
4. Predictor preflight against the Phase A runtime identity, without truth.
5. One predictor execution on the fixed six coordinates.
6. Freeze and independently hash prediction artifacts.
7. One scorer execution using existing truth.
8. Repeat non-scientific tests and verify manifests.

No threshold may be changed in response to D2-A scores.
