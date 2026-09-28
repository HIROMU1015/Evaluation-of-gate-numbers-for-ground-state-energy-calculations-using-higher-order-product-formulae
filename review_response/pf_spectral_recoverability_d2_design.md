# D2-A implementation design

## Boundary

This document designs D2-A but does not authorize or run it. The implementation is split into a predictor and scorer. No module containing scorer truth loaders may be imported by the predictor entry point.

## Existing reusable paths

- `run_second_study_safe_time_domain_phase_b.verify_phase_a_runtime_inventory`: verify the original Phase A runtime before opening a system cache.
- `run_pf_spectral_information_pilot_d1.load_hcl_systems`: reference for cache identity checks only. D2 will load an allowlisted view rather than expose the full dictionary to estimator code.
- `run_h01_approximate_state_calibration._apply_pf_cpu`: existing PF state-action semantics. It may be wrapped, but not used as a block-action accounting shortcut.
- `second_study_safe_time_domain_execution.formula_sequence`: fixed `current_m3` coefficient ordering.
- `system["hamiltonian"] @ vector`: Hamiltonian action.
- `run_second_study_safe_time_domain_phase_b._build_unitary`: explicitly forbidden in the predictor.
- `run_second_study_safe_time_domain_phase_b.exact_ground_pair`: explicitly forbidden in the predictor.

The existing `_apply_pf_cpu` creates a run-local component-gate dictionary inside each call. Sequential Arnoldi calls therefore rematerialize gates. The future implementation must either introduce a coordinate-local action object that caches those gates and reports its memory, or record every materialization. The scientific PF ordering and component exponentials must remain byte-identical in meaning.

## Sanitized access object

Estimator code receives a `PredictorSystemView`, not the Phase A pickle dictionary. Its public interface is limited to:

- immutable condition and Hamiltonian identities;
- normalized CISD start vector;
- `apply_pf(vector)`;
- `apply_h(vector)`;
- dimension, time, PF sequence and rotation count;
- resource-counter snapshot.

It exposes no exact vector, exact energy, direct point, D1 cluster, D1 weight, target ID, true gap or scoring label. Construction validates the source dictionary once and drops all non-allowlisted references before calling estimator code.

## Arnoldi chain

For each fixed coordinate:

1. Normalize the original CISD vector as `q_0`.
2. For `j=0..7`, evaluate one PF action `w=Uq_j`.
3. Apply two passes of modified Gram-Schmidt against the current basis.
4. If the relative remainder is at most `1e-12`, record exact/numerical breakdown and stop without restart.
5. Store `Q`, every `Uq_j`, and one `Hq_j` per available basis vector.
6. Form `T_m=Q_m^*UQ_m` and `H_m=Q_m^*HQ_m` for prefixes `m=1,2,4,8` that exist.

The maximum is eight PF per-vector actions and eight H matvecs. Prefixes reuse the same chain. A block function call is also counted per vector.

## Reference and branch candidate

For every prefix, take the lowest eigenpair of Hermitian `H_m` as an empirical H-reference candidate. It is not a global-ground certificate.

Diagonalize `T_m`. For each projected U candidate:

- project its eigenvalue to the unit circle only for the reported phase;
- calculate the full-action residual using stored `UQ_m`;
- calculate squared overlap with the H-reference Ritz vector in the common Q basis;
- unwrap its phase to the energy closest to the H-reference Ritz value.

Rank candidates by the frozen rule in the protocol. The first time has no assumed correct anchor. Later fixed times may use the preceding frozen projector as a secondary score, never truth.

The predicted signed finite-time shift is selected PF energy minus the H-reference Ritz energy. Save all prefix candidates; use `m=8` as primary when available. Do not choose the best prefix after scoring.

## Prediction artifact and hard close

The predictor writes only truth-free outputs to a new directory and finally writes `prediction.json` followed by `prediction.sha256` and `PREDICTION_FROZEN.json`. The prediction file includes branch, unwrap, shift, residuals, claim class, `e_use`, budget, counters and abstention.

After the marker exists, predictor re-entry is refused. The scorer is a separate command that:

1. verifies source, authorization and prediction hashes;
2. verifies the predictor resource/access audit;
3. opens only the committed existing-truth artifacts;
4. scores without changing any frozen field;
5. writes a separate result directory and completion status.

This process boundary is the primary leakage control. Unit tests must also monkeypatch forbidden loaders and fail if predictor code reaches them.

## Cost and outcome

The QPE rotation constant is always named `K_current_m3`; D1 top-K and Arnoldi `m` never use `K` in cost expressions.

For a non-abstained point, the predictor uses

`e_use = abs(delta_hat) + max(local_residual_width, prefix_width)`

and freezes

`B = beta*K_current_m3/[t*(epsilon_E-e_use)]`.

The scorer checks the inherited safety inequality with saved direct error. Classical seconds and Pauli rotations remain separate Pareto axes. The main fixed-margin baseline is local-CISD plus `gamma=1.02`; `1.01,1.05,1.10` are sensitivity points.

Every complete D2-A status stops. D2-B remains unauthorized.
