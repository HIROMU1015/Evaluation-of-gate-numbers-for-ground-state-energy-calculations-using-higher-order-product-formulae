# D2R R1 local environment gate

The local reconstruction bridge stopped with
`failed_environment_reconstruction_bridge` before any exact ground state or R1
selected-coordinate result was generated.

- Fixed bridge points: 11
- Passed: 7
- Failed: 4
- Fixed threshold: `1e-10 Ha`
- Maximum absolute difference: `2.591319440669042e-09 Ha`
- New direct truth coordinates: 0
- GPU operations: 0
- R2 authorized: false

The threshold was not relaxed. Local reconstructed systems are not mixed with
the frozen GPU direct shifts. The only allowed continuation is a separate R1
run that verifies and loads the original Phase A runtime cache byte-for-byte.
