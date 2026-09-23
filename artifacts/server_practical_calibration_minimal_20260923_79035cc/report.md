# Oracle-free practical calibration minimal

Status: **complete_with_findings**

This is a fixed development evaluation on previously observed conditions, not an independent holdout.

## Oracle barrier

The selector received only sanitized Hamiltonian/group/CISD inputs. Exact ground states, exact gaps, direct shifts, direct optima, prior labels, and existing direct-time coordinates were unavailable to selection.

## Primary N2/CO

- Coverage: 4/4 (100.0%).
- Abstentions: 0.
- 1% safe-budget accuracy among scored executions: 1.0.
- Unsafe executions: 0.
- Maximum selection regret: 0.2242747381000174.

## HF stress test

- Coverage: 2/2.
- Abstentions: 0.
- Unsafe executions: 0.

## Diagnostics

The 0.1 proxy-time cancellation index is selection-active. The 0.05 value is recorded only as a numerical robustness check. The signed 0.5 proxy-time sentinel can trigger fallback through residual, sign mismatch, or an indeterminate-sign noise floor.

## Accounting

- New direct truth points: 0.
- Direct interpolation: none.
- Predictions remained byte-identical after freezing and scoring.
