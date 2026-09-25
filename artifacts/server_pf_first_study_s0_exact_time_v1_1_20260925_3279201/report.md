# First-study S0 exact-time practical scoring

Status: **complete_exact_time_scoring**

The frozen practical selector was not rerun or modified. Each selected time was scored directly at the fixed 0.99/1.00/1.01 triplet.

- Conditions: 6/6.
- New direct truth coordinates: 18.
- Saved lower-anchor recomputations: 6 (not new coordinates).
- Maximum exact-time joint regret: 114.153436%.
- Gamma=1.01 successes: 6/6.

Primary regret uses the original two-PF saved grid. The extended-grid comparator is reported separately.

## S0 v1.1 anchor-source amendment

The six branch anchors were selected only from H01-native saved truth records with provenance `new_h01_continuous_branch_calculation`, matching the H01 pickle used to reconstruct each PF unitary. The failed v1.0 result remains preserved; no frozen selector output, time, budget, threshold, truth triplet, or regret reference changed.

The v1.0 run failed because `CO_active_eq_sto3g` used a P03-only saved point as an anchor while rebuilding its PF unitary from the H01 pickle. The resulting cross-source shift difference was `1.0414120648186197e-07 Ha`, above the frozen `1e-9 Ha` gate; its scientific result is not used here.

The sole v1.1 change was the anchor source-identity rule. The frozen prediction hash remained byte-identical at `fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e`.

## Exact-time scoring

| Condition | Group | selected time | signed shift (Ha) | direct cost | same/joint/extended regret | old nearest minus exact (percentage points) | gamma=1.0 margin / result | gamma=1.01 margin / result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| N2_active_eq_sto3g | primary | 0.5983202971910435 | -2.1708888669736095e-05 | 279399598.0082803 | 2.133755% | -0.010322 | 8.639508481271096e-06 / pass | 9.91685118471698e-06 / pass |
| N2_active_stretch150_sto3g | primary | 0.8303584711475099 | -8.568591745727244e-06 | 181632703.25691193 | 22.759988% | -0.332514 | 1.9496042580493606e-05 / pass | 2.0795996797056158e-05 / pass |
| CO_active_eq_sto3g | primary | 0.6127481451622522 | -1.998541374977085e-05 | 533049026.4240849 | 3.184296% | -0.019629 | 9.771294127747736e-06 / pass | 1.1054495140832123e-05 / pass |
| CO_active_stretch150_sto3g | primary | 0.8652659966787087 | -1.5196991115748711e-05 | 362791668.8334559 | 7.181965% | +0.065454 | 1.3390329835247201e-05 / pass | 1.4685108936712989e-05 / pass |
| HF_full_eq_sto3g | stress | 0.148871685974198 | -1.9998854262236836e-06 | 466549222.40975195 | 114.153436% | +0.001210 | -9.247852725467428e-07 / fail | 6.423920546350928e-07 / pass |
| HF_full_stretch150_sto3g | stress | 0.20600464713499966 | -5.140509990558424e-07 | 334003547.0930502 | 107.636129% | +0.009832 | 4.3297642894759647e-07 / pass | 2.001421802918287e-06 / pass |

The old-nearest difference is `old nearest-grid regret - exact-time regret`; negative values mean exact-time scoring increased the measured regret.

- Gamma=1.0: 5/6 overall, comprising 4/4 primary and 1/2 HF stress conditions.
- Gamma=1.01: 6/6 overall, comprising 4/4 primary and 2/2 HF stress conditions.
- The four N2/CO primary conditions pass both frozen-budget settings; exact-time regrets range from 2.133755% to 22.759988%.
- The two HF stress conditions both exceed 100% regret. One fails at gamma=1.0, while both pass at gamma=1.01; they remain stress tests and are not pooled with the primary interpretation.

## Anchor and numerical validation

| Condition | H01-native anchor time | shift reproduction difference (Ha) |
| --- | ---: | ---: |
| N2_active_eq_sto3g | 0.5721861616352092 | 2.5951937539063497e-15 |
| N2_active_stretch150_sto3g | 0.806176425611238 | 5.586190757471583e-15 |
| CO_active_eq_sto3g | 0.5886807290771116 | 1.367331066621548e-14 |
| CO_active_stretch150_sto3g | 0.8563682148339049 | 2.333904418469132e-15 |
| HF_full_eq_sto3g | 0.14715507960862567 | 0.0 |
| HF_full_stretch150_sto3g | 0.20109906745049325 | 0.0 |

All anchors have source domain `H01-native` and provenance `new_h01_continuous_branch_calculation`. All 18 new direct coordinates and all 6 separate anchor recomputations completed with zero cache reuse.

- Maximum anchor shift reproduction difference: `1.367331066621548e-14 Ha`.
- Maximum eigenpair residual: `3.1031929127542307e-14`; maximum unitarity Frobenius residual: `9.886689538770388e-12`.
- Minimum previous-branch overlap probability: `0.9999999919683533`; minimum ground-state overlap probability: `0.9999996340938037`; minimum phase gap: `0.03252669041934374 rad`.
- Runtime: `121.92925047967583 s`; peak CPU RSS: `1011716 KiB`; maximum observed GPU memory: `701 MiB`.

No threshold, selector output, truth triplet, budget, or regret reference was changed. All completion gates passed.
