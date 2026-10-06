# Track R — H6/H7/H8 rank convergence, immutable diagnostic

Status: `hchain_m1_rank_convergence_complete_review_required`.
All nine preregistered coordinates completed one shared maximum-rank32 chain.
Old rank8 reproduction control passed **9/9**, with all compared scalar
differences exactly zero; its branch status, failure set and abstention agree.
Original formal decisions, widths, budgets and artifacts were not changed.

## Read in this order

1. `handoff_audit.json`: caps, source/blob gates, exact coordinates, privacy and resources.
2. `analysis/prediction.json`: immutable scalar analysis and post-execution tests.
3. `tables_figures/primary_scalars.csv` and `mechanism.svg`: 36 primary rank rows.
4. `prediction/prediction.json`: raw prefixes1/2/4/8/16/32, rank-local metrics,
   rank-specific continuation, old-rank8 control and action accounting.
5. `truth_reuse/prediction.json`: nine exact-coordinate saved truth points, same-H
   ground energy/sector closure, source origin and verified snapshot commits.
6. `input_closure/`: input H/CISD/sector/ordered-group/energy-origin identity checks.
7. `docs/second_study_v2/hchain_supplement_execution_20261006/`: authorization,
   approved execution text, source seal and pre-execution tests.

## Main scalar findings

The following are coordinate diagnostics, **not independent samples**.

| Primary rank | Available | Point error below cheap | Positive QPE allowance | Width covers / branch agrees | Budget below same-time cheap |
|---|---:|---:|---:|---:|---:|
| 4 | 9/9 | 0/9 | 0/9 | 9/9 / 9/9 | 0/9 |
| 8 | 9/9 | 3/9 | 0/9 | 9/9 / 9/9 | 0/9 |
| 16 | 9/9 | 9/9 | 2/9 | 9/9 / 9/9 | 0/9 |
| 32 | 9/9 | 9/9 | 6/9 | 9/9 / 9/9 | 0/9 |

Positive allowance at rank16 occurs only at H6 r=.5/.65. At rank32 it occurs
at r=.5/.65 in all three systems. All r=.8 rank32 rows still abstain because
the empirical width plus absolute point estimate exceeds epsilon.

Rank32 point error ranges from 2.8020e-10 to 2.4569e-8 Ha. Its widths are
2.7315e-5 to 2.5766e-4 Ha, while the same-time gamma1.01 cheap-budget decision
windows are only about 1.724e-6 to 4.067e-6 Ha. Thus point accuracy improves
strongly, but these frozen widths do not produce a budget advantage over cheap.
Where no finite M1 budget exists, the comparison is unavailable, not a fabricated
safe fallback. The six finite rank32 budgets are all larger than same-time cheap.

For all 36 primary rows, saved physical-branch diagnostics resolve and permit
same-H/energy-origin PF-side and H-reference error decomposition. The largest
algebraic closure residual is 2.136e-16 Ha. PF-side errors become very small at
rank32; H-reference error remains the larger component. This is an empirical
mechanistic observation, not an exact-ground certificate.

The rank8 primary diagnostic and the legacy-continuation control happened to be
identical in this dataset. The rules remain separate: each new prefix uses its
own previous-time vector, while every legacy-control prefix uses the previous
control-primary8 vector. No claimed branch-policy effect is inferred from zero
observed difference.

## Inputs, science boundary and resources

- H6: neutral singlet, fixed populations3/3, sector400, CISD118, K14344.
- H7: **charge+1, multiplicity3**, fixed populations4/2, sector735, CISD171,
  K27552; not a neutral H7 molecular-ground claim.
- H8: neutral singlet, fixed populations4/4, sector4900, CISD361, K47932.
- All nine saved absolute times and binary64 hex are unchanged.
- New PF vector actions=288, H matvecs=288, Arnoldi chains=9.
- Rank8 control uses cached UQ/HQ; extra PF/H actions=0.
- New reference/cheap/ground/full-PF/Schur/direct-truth/gap actions=0.
- Saved direct truth reused=9; ground **scalar** records reused=3; exact-state
  vector/archive reads=0. Saved truth opened only after the new prediction
  commit and seven-file byte gate.
- Component spectra preprocessing=267 groups / 808 connected-component eigensolve
  batches; component gate materializations=3204; sparse vector multiplies=355104.
  These are reported separately, not hidden under the PF/H action count.

Local CPU inventory:32 logical /24 physical cores, affinity32. RAM62.49 GiB,
initial available51.16 GiB, reserved9.37 GiB. Swap2 GiB total, observed used0.
Initial output filesystem free488.13 GiB, reserve9.25 GiB. Sysfs recorded GPU
presence only; GPU query/allocation/kernel and CuPy operations=0.

Actual concurrency3 independent systems, ordered three times inside each. Each
worker uses one BLAS thread. Concurrent coordinator+worker RSS peak=2,167,472,128
bytes (2.019 GiB), sampled every0.2 s; this is **not** the sum of individual peaks.
Individual prediction-worker peaks: H6 408936 KiB, H7 1165004 KiB, H8 672328 KiB.
Prediction worker walls:1.6513 /5.5911 /39.8753 s. Closure stage27.1273 s;
prediction stage40.9536 s. Scientific workflow total70.0009 s, excluding final
figure/export/publication overhead. Filesystem usage is recorded in handoff audit.

Focused synthetic/source-contract tests:68 passed before,68 passed after,
fail/skip0. Scientific retry0; technical retry0. Full legacy truth-bearing tests
were not run. Existing runtime was read-only, and private output `.runtime/` is
excluded from Git. Root-worktree edits and the shared environment were preserved.

## Freeze identities

- Base: `f54db03a6a619b978a38152ff15fcce9963f676f`.
- Implementation: `51c3b91512209ddabb4a1475294bd2cdf705acf7`.
- Source seal: `45fec99d4d7e10299ad309a7ac52df8a625403b3`.
- Input closure: `c1b6d16ef096c8a59f5dad723b74ba4d252644ae`.
- Prediction: `8a2ad09d0ebca2b372e82fd7847803867ea4c3d0`.
- Prediction SHA-256: `d5f2e69344ac5f1833a501c5b052b45583d28886a31c5eb66352ad8a712016e5`.
- Truth reuse: `3b2e48666718264bd9f2cd8ff96e1e36fe43457e`.
- Truth SHA-256: `3b2569b0b60f6ac7b0b9cf24985f8ef660005433607dff3ba06d9841c9d3a662`.
- Analysis: `e0869b2b9402491a45df9447491d4c445de8a45c`.
- Analysis SHA-256: `ae841b7859adf9116d52527ff48e096cc4ef013cdbd018266a4fc53c0370b3d5`.

Branch: `pf-study2-hchain-m1-rank-convergence-20261006`.
The final publication commit is the commit containing this handoff; no
self-referential hash is embedded. Source origin/result commits and verified
snapshot commits remain distinct. All manifests explicitly exclude themselves.

## Scope and GPT review

Direction C and the approved RQ/claim scope remain unchanged. No B2/H1/q1 policy
was executed or retuned. There is no new operational selector, rank rescue,
certificate, scaling/generalization claim or combined classical+quantum net-cost
claim. No prospective general-molecule runtime, partial truth or scoring was read.

Please judge how the point-accuracy/width/decision-window separation affects the
approved paper evidence, and whether any future measurement is actually needed.
No additional rank/system/geometry calculation is authorized by this handoff.

The separate Track G run encountered a serialization-namespace implementation
failure after all four H/CISD generations and was not retried. It is not a
completed scientific geometry sweep. That helper is not invoked anywhere in
Track R; the R input identity, action caps, reproduction and truth gates all passed.
Its independent incident record must accompany any combined review.
