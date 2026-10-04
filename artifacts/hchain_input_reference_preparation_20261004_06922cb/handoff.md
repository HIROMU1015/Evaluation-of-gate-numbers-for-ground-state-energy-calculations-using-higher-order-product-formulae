# Preparation completion handoff — local runtime, no candidate authorization

Status: `hchain_input_reference_preparation_complete_execution_ready`.
The user's bounded preparation request is complete. Existing blocked/formal decisions remain untouched.
This is input/coordinate/method readiness, not candidate performance or permission to execute candidates.

Worktree:
`/home/abe/myproject/Evaluation_numGate_highorder/.worktrees/pf-second-study-v2-hchain-input-reference-preparation-20261004`

Branch: `pf-second-study-v2-hchain-input-reference-preparation-20261004`

- Base remote snapshot: `99791c0271c8972e90d5fb486ab03f603196bd89`
- Source/protocol/grid/method commit: `06922cbdf43c837eac1b5095684fe235e923cac3`
- Implementation identity/provenance commit: `0bd531a8a468b08988fe1db9b52502861b569a77`
- Input freeze commit (six files only): `ed8b77ffb2d446283a079a6a6c9083c0a22886de`
- Result publication commit: the commit containing this handoff (do not embed a self-referential hash).

## What is fixed

| System | sector / CISD dimensions | t_ref | reference source |
|---|---:|---:|---|
| H2 | 4 / 4 | 1.8470023167315772 | 34 new CISD echo points |
| H4 | 36 / 27 | 1.237648718781152 | identity-verified saved cheap reference |
| H6 | 400 / 118 | 1.0864029909482193 | 34 new CISD echo points |

`candidate_plan.csv` freezes nine `r*t_ref` absolute times and exact binary64 hex.
`input_identity.json` freezes every H/CISD/group/sector identity and RHF reference integer.
H2/H4 saved CISD bytes are unchanged. H6 is a newly frozen same-recipe H/CISD snapshot;
the historical 200-dimensional exact/Z2 state is not used. H6 group structure and K=14344 match.

The acquisition adapter separately counts reference/candidate/M1 vector actions, H exponential
actions and M1 H matvecs, materializations, sparse multiplies, cache bytes, wall and RSS. The
preparation runner only enables reference scope. No-fit B1/B2/H1 and conditional-first combined
schedule are implemented and stub-tested; they are not validated policies or measured molecular H1.
`truth_scoring_method.json` fixes the scorer method only. New truth/ground/gap computation is not authorized.

## Evidence and limits

New H6 H/CISD: 1 each; input verification H matvecs: 3.
New reference PF actions / H exponential actions: 68 / 68. H4 new reference actions: 0.
Reference group spectra: 59; connected-component eigensolve batches: 132; CISD subspace eigensolve: 1.
Component gate materializations: 8024; sparse state multiplies: 27200.
Input numerical stage: 1.1977149872109294 s. Reference numerical stage: 1.5941334059461951 s.
These are measured named-stage wall times, not total CLI startup/import/provenance overhead.
Peak RSS: input 358364 KiB; reference 419500 KiB (do not sum peaks).
PF norm residual maximum: 6.261657858885883e-14; H exponential norm residual: 2.220446049250313e-16.
Internal `expm_multiply` H matvec count is unknown, not silently counted as one.

Pre / post truth-free tests: 41 / 41 passed, fail/skip 0. Detailed logs are separate from the
runner manifest, which is not rewritten. Pre-test UTC timestamps were not separately captured;
post-test timestamps are recorded. Full legacy tests remain deferred behind the future candidate
prediction freeze because they read existing truth.

Candidate cheap/M1/Arnoldi, full PF, full-H ground solve, direct truth, target gap, performance
scoring, GPU query/allocation/kernel: all 0. Group/CISD eigensolves are not hidden under that claim.
Old 47 registry sources and 15 manifest entries are unchanged. Root worktree dirty state is preserved.

## Stop / next authorization

Do not automatically execute the nine candidates or score B1/B2/M1/H1. Review this freeze first.
The future separately authorized order remains:

cheap candidates -> B1/B2/q freeze -> q=1 M1 -> H1 freeze -> q=0 always-M1 completion ->
prediction commit/byte gate -> same-H exact ground/direct/gap -> immutable scoring -> review stop.

B0 numerical values and q/final decisions are intentionally not yet acquired; their rules are fixed.
M1 accuracy, branch correctness, empirical width coverage, safe budgets and combined H1 cost
are not established by preparation. No holdout/scaling/certification claim is made.

Sanitized `.runtime` (7 files, 913581 bytes) is retained ONLY in this worktree, excluded from Git.
Lightweight Git artifacts alone are not an operational input copy on a different server. A server
transfer of this exact runtime would need explicit approval and full byte/hash checks; do not
regenerate H6 or reconstruct an equivalent cache to bypass its frozen identity.

No push is authorized by this preparation scope. A later user-authorized non-force push command:

```bash
cd /home/abe/myproject/Evaluation_numGate_highorder/.worktrees/pf-second-study-v2-hchain-input-reference-preparation-20261004
git push -u origin pf-second-study-v2-hchain-input-reference-preparation-20261004
```
