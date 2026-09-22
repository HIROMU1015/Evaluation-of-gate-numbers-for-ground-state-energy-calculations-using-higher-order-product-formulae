# H02 finite-time controlled-state diagnosis

Status: **complete_with_findings**

This is an oracle mechanism diagnostic built on the fixed H01 N2/CO result. It changes only the calibration state and adds no direct PF eigenvalue points.

## Result

- Controlled states: `128`; finite-time proxy models: `256`.
- Scalar-invariant phase groups: `32`.
- Constructive counterexample groups: `32`.
- Groups changing the selected PF: `0`.
- Maximum direct PF-choice regret: `0.0000%`.
- Scalar metrics sufficient for finite-time calibration: **False**.

Each phase quartet has the same state energy error, variance, residual norm, and exact-ground overlap by construction. Its scientific interpretation is accepted only if every numerical check below passes.

## Numerical checks

- protocol_hash_matches: **PASS**
- exact_echo_reproduction: **PASS**
- all_phase_groups_have_four_states: **PASS**
- phase_group_scalar_invariance: **PASS**
- no_new_direct_truth: **PASS**

## Interpretation and scope

- This directly bridges the earlier H2/H4 leading-order H02 counterexample to the H01 finite-time two-term N2/CO setting.
- Energy error, variance, residual norm, or overlap alone must not qualify an approximate state for PF cost calibration.
- The result does not yet provide an operational qualifier; an error-operator-sensitive diagnostic is still required.
- H01 oracle analytic times and exact direct costs remain evaluation-only inputs, so this is not end-to-end cheap calibration.
