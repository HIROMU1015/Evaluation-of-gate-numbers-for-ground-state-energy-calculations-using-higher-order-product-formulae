# First-study S0 exact-time practical scoring

Status: **failed_numerical_validation**

The frozen practical selector was not rerun or modified. Each selected time was scored directly at the fixed 0.99/1.00/1.01 triplet.

- Conditions: 6/6.
- New direct truth coordinates: 18.
- Saved lower-anchor recomputations: 6 (not new coordinates).
- Maximum exact-time joint regret: 114.153436%.
- Gamma=1.01 successes: 6/6.

Primary regret uses the original two-PF saved grid. The extended-grid comparator is reported separately.

The frozen prediction SHA-256 remained byte-identical at `fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e`.

| Condition | Group | selected time | signed shift (Ha) | direct cost | same-PF regret | original joint regret | extended regret | old nearest minus exact regret (percentage points) | gamma=1.0 margin (Ha) / success | gamma=1.01 margin (Ha) / success |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| N2_active_eq_sto3g | primary | 0.5983202971910435 | -2.1708888669736095e-05 | 279399598.0082803 | 2.133755% | 2.133755% | 2.133755% | -0.010322 | 8.639508481271096e-06 / pass | 9.91685118471698e-06 / pass |
| N2_active_stretch150_sto3g | primary | 0.8303584711475099 | -8.568591745727244e-06 | 181632703.25691193 | 22.759988% | 22.759988% | 22.759988% | -0.332514 | 1.9496042580493606e-05 / pass | 2.0795996797056158e-05 / pass |
| CO_active_eq_sto3g | primary | 0.6127481451622522 | -1.9985413741073726e-05 | 533049026.39082205 | 3.184296% | 3.184296% | 3.184296% | -0.019629 | 9.771294136444881e-06 / pass | 1.1054495149529268e-05 / pass |
| CO_active_stretch150_sto3g | primary | 0.8652659966787087 | -1.5196991115556401e-05 | 362791668.83297205 | 7.181965% | 7.181965% | 7.181965% | +0.065454 | 1.3390329835439484e-05 / pass | 1.4685108936905272e-05 / pass |
| HF_full_eq_sto3g | stress | 0.148871685974198 | -1.9998854262236836e-06 | 466549222.40975195 | 114.153436% | 114.153436% | 114.153436% | +0.001210 | -9.247852725467428e-07 / fail | 6.423920546350928e-07 / pass |
| HF_full_stretch150_sto3g | stress | 0.20600464713499966 | -5.140509990558424e-07 | 334003547.0930502 | 107.636129% | 107.636129% | 107.636129% | +0.009832 | 4.3297642894759647e-07 / pass | 2.001421802918287e-06 / pass |

The old-nearest difference is `old nearest-grid regret - exact-time regret`; negative values mean exact-time scoring increased the measured regret.

- Gamma=1.0: 5/6 overall, comprising 4/4 primary and 1/2 HF stress conditions.
- Gamma=1.01: 6/6 overall, comprising 4/4 primary and 2/2 HF stress conditions.
- The four N2/CO primary conditions pass both frozen-budget settings; their exact-time regrets range from 2.133755% to 22.759988%.
- The two HF stress conditions both exceed 100% regret. One fails at gamma=1.0, while both pass at gamma=1.01; they remain stress tests and are not pooled with the primary interpretation.

## Numerical validation

- All 18 new direct coordinates and all 6 separate saved-anchor recomputations completed.
- Source identities, prediction/protocol hashes, eigenpair residuals, unitarity residuals, branch overlaps, phase gaps, and requested-condition accounting passed.
- Anchor reproduction failed: `CO_active_eq_sto3g` differed by `1.0414120648186197e-07 Ha`, exceeding the frozen `1e-9 Ha` limit. The other five anchor differences were at most `6.61150381133218e-15 Ha`.
- Maximum eigenpair residual: `2.8205796799578092e-14`; maximum unitarity Frobenius residual: `9.886583680065354e-12`.
- Minimum previous-branch overlap probability: `0.9999999919683507`; minimum ground-state overlap probability: `0.9999996340938037`; minimum phase gap: `0.03252669041934374 rad`.
- Initial scientific pass: `181.64859204902314 s`, peak CPU RSS `1008800 KiB`, maximum observed GPU memory `701 MiB`. A later cache-only manifest refresh reused all 24 computed records and performed no new direct calculation.
