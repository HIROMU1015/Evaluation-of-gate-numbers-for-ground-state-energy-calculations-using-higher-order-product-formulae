# H-chain truth/scoring technical stop — not a scientific result

Status: `hchain_truth_or_scoring_failure_stop`.

The new wrapper failed its repository access gate **after three same-H ground solves and
before the formal ground freeze, direct truth, target gaps or scoring**. No scientific retry,
alternative output, policy/width/threshold adjustment or prediction modification was attempted.

## Cause

The wrapper allowed the preparation source manifest entries and the prediction documentation,
but omitted the prediction-phase source paths introduced after preparation. The next source
checkpoint correctly attempted to hash `review_response/hchain_prediction_phase.py`; the Python
open guard denied that read because it was missing from the allowlist. This is an implementation
error in the newly added wrapper, not a changed source blob, incorrect scientific value or
negative calibration result. The source/access gate was not ignored.

Preflight (before installing the open guard) had passed, and all 82 relevant synthetic/source
tests passed. Those tests did not cover the composed source-gate-plus-runtime-access-guard path;
their success is not evidence that this integration gate passed.

## Preserved progress

- Prediction commit: `858265dacd304c844029ce2576b4559221f0c7c1`; all 38 published prediction files
  reverified byte-identical after the stop. All decisions, budgets and abstentions are unchanged.
- Scorer implementation: `139b5e9650e8609ea06e0dc15c636c7bd0935940`.
- Scorer source seal/execution commit: `e1cc452e11bb481f7275deaa9a769a7887da18a5`.
- Original input runtime: seven files / 913581 bytes, unchanged and reverified.
- New same-H ground solves: 3 (population sectors H2/H4/H6 = 4/36/400). Ground normalization,
  nondegeneracy and residual gates passed in the original loop; their numeric in-memory summary
  records were not written before the later source checkpoint failed. No scalar values are
  fabricated here. Full-H ground solves were not repeated to reconstruct those summaries.
- New ground vectors/energies: three NPZ files / 4628 bytes retained in this output's `.runtime`,
  excluded from Git. `ground_runtime_preservation.json` records exact file hashes and bytes;
  it is a preservation inventory, not the missing formal `GROUND_FROZEN` result.
- Ground verification H matvecs: 3; group spectra/component eigensolve batches: 72/149.
- Ground numerical stage: 0.03104258794337511 s; input/component stage: 0.7098580240271986 s.
  These are named-stage wall times, not total CLI time. Peak RSS: 414532 KiB.
- Full PF builds, direct Schur solves, direct truth, target gap, scoring, cheap/M1/reference
  reacquisition and GPU operations: all 0. No ground/truth/result freeze commit was created.
- Root worktree dirty status and original preparation/prediction branches remain unchanged.
- No push, legacy full tests, post-stop scientific run or numerical rescue.

## Needed next authorization

Do not run the current command again: its output-exists gate intentionally rejects a rerun.
A narrowly scoped execution amendment must authorize all of the following before continuation:

1. Correct only the new wrapper's frozen-source allowlist and add an integration regression test
   exercising the actual source checkpoint under the read guard before scientific actions.
2. Freeze that source-only correction with old/current source hashes; keep all prediction,
   Hamiltonian, PF, method, candidate, threshold and budget identities unchanged.
3. Resume **the same output/run**, checking the three preserved ground NPZ hashes first; reuse
   those states instead of any additional ground eigensolve. Recover energies from their saved
   scalar members and separately account for bounded normalization/H-residual revalidation.
4. Formally freeze the reused ground sources, then acquire only the still-uncomputed nine direct
   truth/gap points, freeze truth, and run the unchanged immutable scoring arithmetic once.

No research-direction conclusion follows from this technical stop. Safety/accuracy/coverage
and q=0 interpretation remain unassessed. Preserve the original `FAILURE.json` and this stop
record unchanged during any separately authorized continuation. Stop here pending direction.
