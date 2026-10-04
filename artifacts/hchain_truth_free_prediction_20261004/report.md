# H-chain nine-coordinate truth-free prediction completion

Status: `hchain_truth_free_prediction_complete_review_required`.
**Prediction phase only. Truth, ground states, target gaps and performance scoring remain unopened/uncomputed.**

The separately authorized run used the original seven-file runtime (913,581 bytes) in the
same preparation worktree, on branch `pf-second-study-v2-hchain-prediction-20261004`.
No input regeneration/transfer, reference reacquisition, fitting, numerical-rule adjustment,
extra coordinate, GPU operation or scientific rescue was performed.

## Actual freeze sequence

- Preparation verified snapshot: `a03bd71415cac6deb3b653c131905f32b744cec5`.
- Input origin/result freeze: `ed8b77ffb2d446283a079a6a6c9083c0a22886de` (kept separate).
- Prediction implementation/authorization: `3d30421177b871e080012e21feb8d9655df5fa77`.
- Source identity seal: `2b04db53f9d8fde52107bb956ea27ba9d7c36cc1`.
- B0/B1/B2/q freeze: `c96d9f289fb85fe532591e97045d05a198039780` (exact seven-file commit).
- H1 freeze: `38da86a59d70df52d2888bef5b1257f3459b616f` (exact seven-file commit).
- Final prediction publication: the commit containing this report (no self-reference).

All q decisions were zero. Accordingly, no conditional M1 ran. H1 was committed while M1 PF/H
actions and chains were still zero. Only afterwards did the always-M1 comparator acquire all
nine coordinates. q/H1 bundle bytes were rechecked against their commits after completion.

## Frozen cheap/B2/H1 decisions

Budgets are the inherited continuous Pauli-rotation cost proxy, not integer QPE counts or measured safety.
All four B1 gamma arms selected r=0.8, with identical eligibility sets and negative exterior proxy
signs. Therefore all three instability flags are false, B2 gamma=1.01 and q=0 in every system.

| System | B0 | B2/H1 selected ratio | B2/H1 frozen budget | q | B2/H1 fallback |
|---|---:|---:|---:|---:|---|
| H2 | 900552.7007472287 | 0.8 | 603885.1945698304 | 0 | false |
| H4 | 31811311.77571516 | 0.8 | 21367518.317609176 | 0 | false |
| H6 | 203352921.03190777 | 0.8 | 136317065.0533369 | 0 | false |

These are predicted decisions, **not established quantum savings or safe budgets**.

## Comparator M1 — unchanged rank/width rules

| Coordinate | Available / requested rank | signed M1 shift [Ha] | empirical width [Ha] | Abstention |
|---|---:|---:|---:|---|
| H2 r=0.5 | 4 / 4 | -1.9692301294e-6 | 1.6754912018e-15 | no |
| H2 r=0.65 | 2 / 4 | -5.5794313921e-6 | 1.3682630584e-9 | primary unavailable |
| H2 r=0.8 | 2 / 4 | -1.2671556176e-5 | 6.2940385126e-9 | primary unavailable |
| H4 r=0.5 | 8 / 8 | -1.8634567200e-6 | 2.0381875480e-5 | no |
| H4 r=0.65 | 8 / 8 | -5.2732840021e-6 | 3.8703206849e-5 | no |
| H4 r=0.8 | 8 / 8 | -1.1958345199e-5 | 9.2320455179e-5 | no |
| H6 r=0.5 | 8 / 8 | -1.7782321855e-6 | 2.3104579737e-3 | no positive QPE allowance |
| H6 r=0.65 | 8 / 8 | -5.0139874506e-6 | 2.8933273815e-3 | no positive QPE allowance |
| H6 r=0.8 | 8 / 8 | -1.1639961040e-5 | 4.0694868718e-3 | no positive QPE allowance |

Always-M1 selected the B0 fallback for all systems: H2 exterior points abstained; H4 exterior
width-inclusive e_use exceeded the intervention allowances; H6 e_use exceeded epsilon_E.
H2 primary equals its finite sector dimension but uses the same permitted projected algorithm,
not an externally supplied exact state. No lower-rank rescue or narrower width was accepted.
All widths remain empirical, not spectral/ground certificates. No truth-based accuracy comparison is made.

## Resources and gates

- Cheap PF / H exponential actions: 9 / 9. Internal H-exponential matvec counts: unknown.
- M1 PF / H matvec actions: 56 / 56, across nine single chains; conditional H1 actions: 0 / 0.
- H2 actions: 4,2,2 per coordinate; H4/H6: 8 each. No prefix/comparator chain rerun.
- Shared group spectra / component eigensolve batches: 72 / 149; these are not hidden full-H/PF truth solves.
- Component gate materializations / sparse state multiplies: 1728 / 25923.
- Shared input/group preprocessing: 0.7051912429742515 s; cheap numerical stages: 0.09846175368875265 s;
  M1 numerical stages, entirely comparator-only: 0.17586242407560349 s.
- Measured H1 shared schedule interval: 0.701519520021975 s, excluding prior shared preprocessing but
  including q/H1 freeze, Git and source verification. Comparator completion: 0.23815433029085398 s,
  excluded from H1. The stored net-of-recorded-freeze value (0.3303226148709655 s) still includes
  post-freeze source verification overhead; **it is not pure numerical acquisition cost**.
- Recorded process-body time before final write: 1.963207266293466 s; not total CLI startup/import time.
- Peak RSS: 414136 KiB (process high-water mark; do not sum stage peaks).
- Maximum PF norm residual: 5.950795411990839e-14; H exponential norm residual: 2.220446049250313e-16.
- CPU process / BLAS threads: 1 / 1; GPU query/allocation/kernel and CuPy imports: 0.
- Exact-ground solves, direct truth coordinates, target gaps, full PF builds, truth-array reads: 0.
- Pre/post truth-free tests: 57 / 57 passed, fail/skip 0. Legacy full tests remain deferred.
- Frozen inputs, nine binary64 times, 53 inherited sources and old formal artifacts are unchanged.
  Root-worktree dirty status is preserved.

## Stop and review

Final prediction SHA-256: `a830300b3a90bd9947951a2369b6bcbd01dcd96dfe13db8e24390a3f9c7b8e6f`.
Final manifest SHA-256: `24f8001bce5fb6b63e809428d9e713f4e4322f5e747770fd9f76108c85b640f3`.
Runner manifest is self-excluded and unchanged; this report/test/publication audit are separate.

Stop here. No ground/direct/gap acquisition, branch correctness, width coverage, safety scoring,
holdout, policy retuning or push is authorized by this scope. A future separate approval must
review this prediction commit and then authorize the already frozen same-H truth/scorer method.
The all-zero q realization supplies no molecular evidence about the conditional q=1 H1 path.
Cold independent always-M1 timing and rigorous combined cost envelopes were not measured.
