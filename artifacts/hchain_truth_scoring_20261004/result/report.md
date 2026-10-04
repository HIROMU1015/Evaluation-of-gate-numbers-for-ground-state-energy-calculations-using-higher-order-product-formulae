# H-chain same-H truth and immutable scoring — review stop

Status: `hchain_independent_validation_complete_review_required`.
This is the authorized continuation of the original stopped run, not a new calibration run.
Prediction, original sources, original stop publication and both original runtimes remain unchanged.
No next stage or push is authorized. Nine coordinates are diagnostics on three systems, not nine
independent samples, an unused holdout, a scaling law or a rigorous safety certificate.

## Main result

Cheap-only B2/H1 is safe and meets the frozen 10% budget-reduction target on all three systems.
All q=0, so H1=B2. B1 at fixed gamma=1.01 has exactly the same final action and budget as B2/H1;
the other three frozen gamma arms are also safe. This result does **not** demonstrate an adaptive
cheap advantage over fixed-cheap gamma=1.01, nor a positive spectral incremental effect.

| System | q | Selected ratio | B0 | Frozen B2/H1 budget | B/B0 | Reduction vs B0 | Safe / target |
|---|---:|---:|---:|---:|---:|---:|---|
| H2 | 0 | 0.8 | 900552.7007472287 | 603885.1945698304 | 0.6705717434 | 32.9428% | PASS / PASS |
| H4 | 0 | 0.8 | 31811311.77571516 | 21367518.317609176 | 0.6716956053 | 32.8304% | PASS / PASS |
| H6 | 0 | 0.8 | 203352921.03190777 | 136317065.0533369 | 0.6703472188 | 32.9653% | PASS / PASS |

B0 and always-M1 fallback are safe in 3/3 systems, but achieve the target in 0/3. Always-M1
retains its frozen B0 fallback in all systems. No truth-based decision/budget/width repair was made.
No new signal taxonomy such as `robust_signal` is introduced for this validation.

Safety uses the unchanged continuous proxy: `abs(delta_direct)+1.2*K/(t*B_frozen)<=epsilon_E`,
with epsilon_E=0.00015936001019904 Ha. Target additionally requires t>T0 and B<=0.90*B0.
Selected-action safety headroom is 1.4461290784e-6, 2.4278972385e-6, 3.3682339572e-6 Ha
for H2/H4/H6, respectively. All four gamma arms (1.01/1.02/1.05/1.10) are safe in each system.
The minimum safe gamma in the fixed frontier is 1.01; no new gamma was fit.

## Coordinate diagnostics (Ha except phase gap)

Every truth record has resolved numerical/overlap quality. Branch comparison uses physical
signed shift and the phase-gap separation, not the predictor's absolute unwrap integer.
All nine M1 point estimates select the target branch and satisfy empirical E_M<=w_M.
Five original policy abstentions are retained, not reversed by these diagnostics.

| System | r | Direct signed shift | E_C | E_M | Frozen w_M | Original M1 abstain |
|---|---:|---:|---:|---:|---:|---|
| H2 | 0.5 | -1.9692301289e-6 | 1.8480219231e-10 | 4.7262786743e-16 | 1.6754912018e-15 | no |
| H2 | 0.65 | -5.5794313921e-6 | 1.3682704077e-9 | 4.1739242542e-17 | 1.3682630584e-9 | yes: rank |
| H2 | 0.8 | -1.2671556176e-5 | 6.2941710873e-9 | 1.5411933882e-16 | 6.2940385126e-9 | yes: rank |
| H4 | 0.5 | -1.8633546817e-6 | 1.2935670183e-7 | 1.0203831558e-10 | 2.0381875480e-5 | no |
| H4 | 0.65 | -5.2727803924e-6 | 4.0197969861e-7 | 5.0360972906e-10 | 3.8703206849e-5 | no |
| H4 | 0.8 | -1.1954606105e-5 | 9.7812216999e-7 | 3.7390933136e-9 | 9.2320455179e-5 | no |
| H6 | 0.5 | -1.6749699077e-6 | 3.0069769521e-7 | 1.0326227778e-7 | 2.3104579737e-3 | yes: allowance |
| H6 | 0.65 | -4.7323400327e-6 | 8.5667756083e-7 | 2.8164741788e-7 | 2.8933273815e-3 | yes: allowance |
| H6 | 0.8 | -1.0706917326e-5 | 1.9153853681e-6 | 9.3304371452e-7 | 4.0694868718e-3 | yes: allowance |

See `coordinate_scoring.csv` for exact absolute times/float.hex, gaps in rad/Ha/chord units,
absolute PF matching-lift diagnostics and all original failure reasons. `g_rho_others` was not
acquired or substituted into a new width. Width coverage is empirical, not certification.
See `decision_scoring.csv` for all 24 frozen arm actions and continuous safety calculations.

## Ground reuse, numerical gates and the technical stop

Population-sector dimensions: H2/H4/H6=4/36/400; H6 historical 200-dimensional Z2 ground not used.
Three same-H grounds were computed in the first process and preserved as three NPZs (4,628 bytes).
This continuation verified those committed file hashes and revalidated their norm/residual with
three matvecs; **zero ground eigensolves were repeated**. Saved ground energies are
-0.7735421405578098, -1.8349096352179535, -2.9112247438296115 Ha.
Maximum recovered ground residual is 3.9438025096e-15 Ha; maximum norm residual 1.1102230246e-16.

The original checked solver passed nondegeneracy before each file write, as documented by
the byte-identical source/execution/failure witness. Its first-excitation gap and per-system solve
time were not serialized before the original stop: they remain explicitly null/unavailable.
No missing scalar was guessed or recovered by another eigensolve. This does not provide
a newly measured gap value or an external predictor ground certificate.

Maximum PF eigenpair residual: 2.8696818477e-14; maximum unitarity Frobenius residual:
2.8782297010e-12; minimum target phase gap: 0.09427115634 rad. Minimum exact-ground
overlap: 0.9999999906391561; minimum previous-branch overlap: 0.9999999968706532.
Selected-versus-maximum-ground-overlap comparator disagreements: 0. No numerical gate was relaxed.

Original `STARTED.json`, `FAILURE.json`, `STOPPED.json`, preservation inventory and stop manifest
are unchanged at their original paths. `RESUME_STARTED.json` records the separately approved
continuation. There was no second continuation or alternate output. The old stop report describes
that earlier creation-time state; this report describes the completed state.

## Resources and tests

Same-run totals: ground solves 3 (resume 0), ground verification matvecs 6 (resume 3), full PF
builds 9, complex Schur solves 9, direct coordinates 9, target gaps 9, immutable scorer calls 1.
New cheap/M1/reference/Arnoldi acquisitions: 0. GPU query/allocation/kernel and CuPy import: 0.
Grounds and matrix/vector data remain local, untracked; only lightweight scalar records are committed.

Component spectra were not serialized by the stopped process. Their necessary scorer preprocessing
was repeated and accounted: 144 group preparations / 298 component eigh batches cumulatively,
72 / 149 on resume. Truth component gate materializations: 864; sparse-matrix/dense-matrix
multiplies: 2,907. These component solves are not disguised as zero eigensolvers.

Resume process body before final write: 3.2998101721 s (excludes Python imports/startup).
Resume preprocessing: 0.7142395983 s; ground revalidation: 0.0034624096 s;
nine direct/gap coordinates: 1.1797432113 s; immutable arithmetic: 0.0040811431 s.
Nested timers must not be summed as disjoint wall time. Maximum RSS across the two processes:
415100 KiB, below 4 GiB; CPU process/thread 1/1. Original calibration costs stay in the original
prediction audits and are not reclassified as scorer costs.

Pre/post relevant tests: 91 / 91 passed, fail/skip 0. They include the active-boundary source/runtime
regression, saved-ground recovery tests, unchanged synthetic scorer tests and earlier preparation/
prediction tests. Full legacy review_tests were not run: they can execute additional molecular
actions outside this bounded scope. The separate test logs/audits preserve command, environment,
UTC timestamps and exact log hashes. Runner manifests were verified, not rewritten.

## Identity and commits

Branch: `pf-second-study-v2-hchain-truth-scoring-20261004` in the original preparation/runtime worktree.
Result publication commit: the commit containing this report (no self-referential hash).

- Prediction: `858265dacd304c844029ce2576b4559221f0c7c1`; all 38 files unchanged.
- Original scorer implementation: `139b5e9650e8609ea06e0dc15c636c7bd0935940`.
- Original execution: `e1cc452e11bb481f7275deaa9a769a7887da18a5`.
- Original stop publication: `e8407f60756c4e3efb23ec7c4d6087e8f5d5e5e0`.
- Resume implementation: `ee91221e9db5b4e8cb664063319369336bfb1e56`.
- Resume source seal / execution: `2a8f376f447261613c17c0863b05d549edfc8f57`.
- Ground freeze: `4c9014f0a0c851e36e23992e833ece2b1e020e37`.
- Truth freeze: `ae585e2c1a1b8f49bee3d8ca3fcb55901e45cf35`.
- Prediction SHA-256: `a830300b3a90bd9947951a2369b6bcbd01dcd96dfe13db8e24390a3f9c7b8e6f`.
- Frozen scoring method SHA-256: `a30afdee106d34c3fe4395bed5aa3459763413f68beea12a601b15d22e772e0e`.
- Resume authorization SHA-256: `2a23bde0cc83525a4d9625465841271a9261e70485fbf71f73d997134337c481`.
- Resume source manifest SHA-256: `e7f553ccf4b5946349b99e9c3c9f0855a26aa3d80f2ba54678e1999069a886b0`.
- Ground manifest SHA-256: `34ec9e0f832199eefdddd309a762042447dc5b8dc7720b46d2d534d5a250e887`.
- Truth manifest SHA-256: `ee06893fb2ec61341204133cb9dacfd0fcaef34adf4d7dc66988358dde7dffa5`.
- Runner result manifest SHA-256: `c7e980c0f679e91f11c632ba8c425289d5dfc57273a7206d5017b4e63fd5685c`.

Original sanitized runtime: 7 files, 913581 bytes, fully byte/hash identical. Ground/truth stage
manifests and blobs, all seven runner result entries, preserved ground NPZs and original eight
stop entries passed rehash. Full provenance and publication-file coverage are in
`execution_audit.json` and the separate `../publication_manifest.json`.

## Research-direction review boundary

On these three fixed systems, cheap-only decisions safely reduce budget approximately 33% versus
the benchmark anchor. The identical gamma=1.01 B1 arm can achieve the same result. Thus the
present evidence supports cheap sufficiency here; it does not establish selective acquisition's
incremental value. q=1 conditional spectral performance remains unmeasured.

M1 improves point accuracy but the fixed rank/width policy yields fallback rather than additional
budget benefit. In H6 the width is 14.5–25.5 times epsilon_E despite E_M<=9.34e-7 Ha. Keep point
accuracy, uncertainty overhead, policy abstention and resource value distinct.
Generalization, practical combined-path comparisons beyond q=0, rigorous width certification,
new inputs/times/thresholds and future directions require a separate review/authorization.
Stop here; no next-stage calculation, push, holdout or policy rescue.
