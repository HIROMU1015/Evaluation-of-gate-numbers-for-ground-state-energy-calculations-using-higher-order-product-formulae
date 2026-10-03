# H-chain T0/B0 contract review

Status: **not established** for H2, H4, or H6 under the required `current_m3` selective-calibration contract.

The [first-study protocol](../../../PF_first_study_protocol_20260925.json) includes H2 validation and H4 mechanism work, including `current_m3` and an H4 CISD state hash. It does not define a native H2/H4/H6 `T0/B0` pair in the required sense; it also forbids automatic H6 expansion. This is a finding about the inspected normative protocol, not proof that no other historical value exists.

The H-chain direct optimal-time scaling protocol at `4b1ca6be834ae728e4e153c91a1f9bdb3be40219` uses `m5` and `Y8`, with `t_grid_star` selected on a grid defined relative to `t_ana`. Neither `t_grid_star` nor `t_ana` is a `current_m3` baseline `T0`, and its direct budget is not the inherited `B0`.

Consequently `{T0,1.3*T0,1.6*T0}` remains a symbolic proposal. No absolute or hex times, budgets, allowances, or matched truth coordinates were fabricated. A separate research-direction review must choose whether a new H-chain baseline contract is worth defining; the preflight cannot make that choice.
