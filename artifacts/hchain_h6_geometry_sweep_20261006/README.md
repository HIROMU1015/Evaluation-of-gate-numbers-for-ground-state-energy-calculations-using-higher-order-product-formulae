# Track G — incomplete geometry sweep; implementation incident, no recovery

The four new geometries did **not** reach a usable input freeze. This is an
implementation failure, not evidence of molecular/reference/PF ineligibility.
Only the identity-verified R=1.00 anchor has scalar analysis. Do not treat the
anchor-only figure or table as a completed geometry sweep.

The runner returned `hchain_h6_geometry_sweep_complete_review_required` after
serializing terminal records. That historical status means the workflow stopped;
it does **not** mean the requested new-geometry scientific validation succeeded.
The new-geometry scientific work remains incomplete and requires separate review.

## Read in this order

1. `implementation_incident_audit.json`: cause, consumed action caps and stop.
2. `inputs/prediction.json`: all four failed workers, exact resource/access records.
3. `input_closure/prediction.json`: reused R1 H/state/sector/group/origin closure.
4. `prediction/`: global prediction freeze containing the anchor and four failures.
5. `truth/`: three saved anchor truth coordinates reused **after** that freeze.
6. `analysis/`: immutable anchor-only diagnostics, tests and resource monitoring.
7. `tables_figures/primary_scalars.csv` and `mechanism.svg`: anchor-only display.
8. `docs/second_study_v2/hchain_supplement_execution_20261006/`: approved
   execution, authorization, implementation source seal and pre-execution tests.

## Incident and scope

All four workers completed the unchanged RHF/H/group/CISD recipe and input
numerical checks. The hash-verified extracted generator then called `write_json`,
but the extraction namespace did not provide that helper. Each worker stopped
with `NameError: name 'write_json' is not defined`, before returning arrays to the
new wrapper or writing the sanitized predictor input. No new reference, candidate,
M1, ground or direct-truth action was started. This is a wrapper defect; the
generator science body, frozen numerical rules and original artifacts are unchanged.

The focused tests exercised the geometry AST change and rank/margin/barrier logic,
but did not exercise the generator's complete serialization namespace. Their
68-pass result must not be interpreted as full generation-path coverage.

New H generations=4, CISD generations=4, input verification H matvecs=4. These
consumed the preregistered generation caps. Scientific retry=0, technical retry=0.
No correction, regeneration, equivalent-input reconstruction or post-failure
checkpoint resume was attempted. Any recovery needs separate authorization and
an amendment/incident record; it must not be silently mixed into this run.

## Resources and freezes

Local logical CPUs=32, physical cores=24, physical RAM=62.49 GiB. Initial available
RAM=51.17 GiB, reserved RAM=9.37 GiB. Swap=2 GiB total, observed used=0.
Initial output filesystem free=488.13 GiB; reserve=9.25 GiB. GPU presence was
recorded using sysfs only; GPU queries/allocations/kernels=0.

New generation workers=4, BLAS/PySCF threads=1 each. Concurrent coordinator+worker
RSS peak=1,616,867,328 bytes (1.506 GiB), sampled every 0.2 s. Individual worker
peaks and timings are in the frozen input records. Named scientific workflow wall
time=7.1584 s, excluding the final figure/export/publication overhead.

- Source seal commit: `11647e2e109a395791ef2151d0db5edcc477b111`.
- Prediction commit: `41c231c33e0cab456169f216bef6382810b3b2b6`.
- Prediction SHA-256: `5e1a11c957f872cd181ec9e254c5a9dea08ac554463730c798060afa0fac73ee`.
- Truth reuse commit: `37c0f0e177c7d7bc4d1c131f79b655cb8cab2a01`.
- Truth SHA-256: `3897bbff7f023437fff97b601eb65887e617cbafdccdf1dedfa9db85de41c4ec`.
- Analysis commit: `094410fd18e5132dafa3472407b50bb6fc90306c`.
- Focused tests: 68 passed before and after, fail/skip=0.

Branch: `pf-study2-hchain-h6-geometry-sweep-20261006`.
The final handoff commit is the commit containing this report and the lightweight
handoff manifest. It is intentionally not embedded as a self-referential hash.
Original source/result origins and verified snapshots remain separate in the
source and truth registries. The handoff manifest excludes itself.

## Claims and review stop

The reused R1 benchmark and all four fixed-cheap gamma selections are safe; this
reproduces existing scalar evidence only. At gamma=1.01 the selected R1 budget
ratio to its benchmark is 0.6703472; it is not a new geometry result.

No geometry-dependent trend, applicability boundary, new rank/width result, safety
generalization, certificate, independent-sample claim or net cost advantage follows
from Track G. The four implementation failures are not scientific negative results.
Prospective general-molecule runtime/partial truth/scoring reads=0. Shared
environment and original root-worktree edits were not changed.

Private `.runtime/` is excluded from Git. GPT should review the incident and
decide whether a separately preregistered recovery is needed. No additional
geometry/rank/system or scientific retry is authorized by this handoff.
