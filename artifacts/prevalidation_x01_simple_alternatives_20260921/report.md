# X01 A08: simple-alternative comparison

Status: complete

All rules are scored on the same 17 saved development conditions. The fixed 1% budget multiplier and 0.9*t_star cap are declared before inspecting condition outcomes. Direct-point searches are reported separately because they consume exact PF-error truth.

## Results

| strategy | pass | basket cost ratio | min/median/max condition ratio | base points | extra direct points | validation truth used |
|---|---:|---:|---:|---:|---:|---|
| current_m3 two-term at model t_star | 17/17 | 1.000000 | 1.000000/1.000000/1.000000 | 137 | 0 | False |
| current_m3 two-term plus fixed 1% budget margin | 17/17 | 1.010000 | 1.010000/1.010000/1.010000 | 137 | 0 | False |
| current_m3 two-term at fixed 0.9 t_star cap | 17/17 | 1.022537 | 1.020491/1.022427/1.022845 | 137 | 0 | False |
| current_m3 plus one direct check at t_star | 17/17 | 0.998476 | 0.968161/0.998981/0.999845 | 137 | 17 | True |
| current_m3 direct search at 0.9,1.0,1.1 t_star | 17/17 | 0.998422 | 0.913991/0.998981/0.999845 | 137 | 51 | True |
| current_m3 full saved adaptive-grid oracle reference | 17/17 | 0.998186 | 0.682658/0.998981/0.999845 | 137 | 117 | True |
| two_term_center two-term plus fixed 1% budget margin | 17/17 | 1.161160 | 1.155545/1.161547/1.186710 | 136 | 0 | False |

## Inputs, complexity, and worst saved case

| strategy | implementation | required input | worst condition cost ratio |
|---|---|---|---:|
| current_m3 two-term at model t_star | low | saved exact-state short-time proxy and three signed direct fit points | 1.000000 (`BeH2_CAS4e4o`) |
| current_m3 two-term plus fixed 1% budget margin | low | current two-term calibration plus a fixed scalar cost margin | 1.010000 (`BeH2_CAS4e4o`) |
| current_m3 two-term at fixed 0.9 t_star cap | low | current two-term calibration; no validation truth for the decision | 1.022845 (`H2O_stretch150_631g`) |
| current_m3 plus one direct check at t_star | moderate | current two-term calibration plus one exact direct PF point | 0.999845 (`BeH2_stretch150`) |
| current_m3 direct search at 0.9,1.0,1.1 t_star | moderate | current two-term calibration plus three exact direct PF points | 0.999845 (`BeH2_stretch150`) |
| current_m3 full saved adaptive-grid oracle reference | high diagnostic reference | current calibration plus the complete saved adaptive direct grid | 0.999845 (`BeH2_stretch150`) |
| two_term_center two-term plus fixed 1% budget margin | moderate | separate PF implementation and calibration plus a fixed cost margin | 1.186710 (`LiH_CAS2e4o`) |

## Pre-fixed rules without validation truth

The unmodified `current_m3` two-term schedule already passes the strict saved frozen budget on 17/17. Adding a fixed 1% QPE-budget margin also passes 17/17 at an exact basket premium of 1%. The fixed 0.9*t_star cap passes 17/17 but costs 2.25369% more in the equal-one-run basket. Neither simple safeguard is needed to repair a saved baseline failure, but both remain much cheaper than changing PF.

Applying the same pre-fixed 1% budget margin to `two_term_center` also passes 17/17, with basket cost ratio 1.161160 relative to unmodified `current_m3` two-term.

## Additional direct-point alternatives

One exact direct check at t_star permits direct budget repair and has basket ratio 0.998476, but adds 17 exact PF-eigenvalue points. The three-point search adds 51 points and changes the selected time only on 1 condition. That condition is `LiH_CAS2e4o`, where it selects 1.1*t_star and reduces cost to 0.913991 of the model-schedule baseline.

The full adaptive saved grid finds the LiH endpoint at 1.2*t_star with ratio 0.682658, but this is an oracle finite-grid reference with many extra exact points, not a simple model-only rule or a continuous optimum claim.

## Higher-order baseline

A one-order-higher PF is not scored here because no complete result exists on the same 17 Hamiltonians with the same target, calibration budget, and direct scoring protocol. Results from different H-chain or probe sets are not mixed into this comparison.

## A08 conclusion

On the saved development conditions, the new PF does not beat the simplest strong baseline. `current_m3` plus the two-term model is already 17/17 under the operational frozen-budget score and is cheaper than both pre-fixed safety variants and the safety-adjusted new PF. Additional direct points can lower cost, especially for LiH, but they rely on the exact-state oracle identified in A06 and increase classical calibration effort.

This is not an unseen-system guarantee: the rules are scored on correlated development conditions, and the absence of a common high-order dataset leaves the order-raising alternative unresolved.

## Files

- `strategy_rows.csv`: condition-level scores and information budgets.
- `strategy_summary.csv`: aggregate simple-baseline comparison.
- `baseline_availability.csv`: completed and unavailable baselines.
- `simple_alternatives.png`: quantum cost versus extra direct information.
- `raw_sources.csv`: hashes of the 17 reused raw files.
- `analysis.json` and `manifest.json`: summary and provenance.
