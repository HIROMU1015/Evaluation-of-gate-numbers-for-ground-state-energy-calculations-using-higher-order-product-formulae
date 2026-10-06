# H6 geometry recovery failure review

Status: `hchain_h6_geometry_sweep_recovery_failed_review_required`.
The single authorized serialization recovery produced all four frozen inputs, references,
predictions and same-H grounds. A new truth-side import failure stopped the run before any
new full PF, Schur, direct shift or gap acquisition. This is an implementation failure, not
scientific ineligibility. No second recovery, resume or scientific rule change was performed.

## Read order

1. This handoff and [recovery_incident_audit.json](recovery_incident_audit.json).
2. [Approved recovery](../../docs/second_study_v2/hchain_geometry_recovery_20261006/approved_recovery.txt),
   [authorization](../../docs/second_study_v2/hchain_geometry_recovery_20261006/authorization.json),
   [serialization audit](../../docs/second_study_v2/hchain_geometry_recovery_20261006/serialization_audit.json).
3. [Input freeze](inputs/prediction.json), [reference and exact candidate times](reference_time/prediction.json),
   [global prediction](prediction/prediction.json), [ground freeze](ground/prediction.json).
4. [Truth failures and saved anchor reuse](truth/prediction.json), [formal stop](STOPPED/prediction.json).
5. [Five geometry status](geometry_status.json), [prediction scalars](prediction_scalars.csv),
   [prediction-only figure](prediction_only.png), [packaging source](build_review_audit.py).
6. [Source identity](../../docs/second_study_v2/hchain_geometry_recovery_20261006/source_freeze.json)
   and [pre-science tests](../../docs/second_study_v2/hchain_geometry_recovery_20261006/focused_tests.json).

## Immutable commit identities

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`.
Branch: `pf-study2-hchain-h6-geometry-recovery-20261006`.
Publication commit: the commit containing this handoff; its full hash is reported externally,
not embedded as a self-referential field.

| Record | Commit |
|---|---|
| Accepted Track R, unchanged | `0c40a3d7987e0961262bfd38bbb214a9e2946824` |
| Original failed Track G, preserved | `e74fdec5e5085fd7c4f7a39fb4d59cec052f68f4` |
| Recovery amendment and implementation | `5770d9625bfb88c81bab01ea0806ac372b1d9dc6` |
| Source and test freeze | `8895102258f9e4d9e93cf96fcc8c4b7a51fdfae3` |
| Saved anchor input closure | `2a09b085fc1470695ad638c5baa48f13ba5ad31b` |
| Global five geometry input freeze | `afbf22d063199ccc573c6664d7198acea1990a3f` |
| Reference and exact candidate freeze | `cd5488902e46bc1320d6fc983f2d6e76d5aa4010` |
| Global prediction freeze | `61ae95edce8c4a25167521c0e6e95a83c3cbc4bb` |
| Ground freeze | `1e5d66a4914bc50a8afa55baa578cca55a227979` |
| Failed truth stage and saved anchor truth reuse | `33d2d795a251758e29507b600145ebd7e21a8812` |
| Failed recovery formal stop | `1633120317567e388a90c185fc7856439bb04819` |

Each seven-file stage was verified against its origin commit and the stopped snapshot.
The audit retains origin/result and verified snapshot as separate fields. Stage and handoff
manifests explicitly exclude themselves. Original failed-run artifacts and frozen science
helpers are byte-identical to their prior records, apart from the authorized extractor binding.

## Serialization correction and tests

The only change to the original scientific implementation module is:

```python
"write_json": write_json,
```

It binds the existing helper in the extracted generator namespace. The scientific generator
file SHA remains `0a2fce70ba9af6f2892b31b4c21febf6ddccbe3fbeec116e324212992a082d3f`.
The generator body and extraction logic are unchanged except for the already approved single
`mol.atom` distance multiplication. The separate recovery coordinator provides new output/source
routing, an all-four-input barrier, explicit one-run accounting and failure stop handling; it
reuses the original worker, methods and scorers rather than replacing scientific algorithms.

Focused pre- and post-science tests: **76 passed each, fail/error/skip 0**.
These comprise the existing 68 tests plus eight new tests covering all four namespace bindings,
exact serialization-only diff/AST, the unchanged real generator path with mock chemistry through
an actual `write_json`, sanitized NPZ rereading/hash freezing, and partial/duplicate input rejection.
Mock chemistry is not molecular recovery evidence. No truth-bearing legacy test was run.
The new tests did not cover the later truth-worker import under the repository access guard.

## Geometry status

| R in Angstrom | t_ref | Input and prediction | Ground | Direct truth |
|---:|---:|---|---|---|
| 0.80 | 0.8138093666863689 | frozen | frozen | technical failure, 0 new |
| 1.00 | 1.0864029909482193 | saved anchor reused | saved metadata reused | 3 saved coordinates reused |
| 1.20 | 1.3656419490338083 | frozen | frozen | technical failure, 0 new |
| 1.40 | 1.607437626173532 | frozen | frozen | technical failure, 0 new |
| 1.60 | 1.7509022345019551 | frozen | frozen | technical failure, 0 new |

All four new references passed the original first-window/native time contract; all twelve new
candidates are the exact frozen `.5/.65/.8 * t_ref` coordinates. All twelve new M1 predictions
abstained under the unchanged rank8/width/gates; the three saved anchor predictions also abstained.
The B1 frontier selects `.8*t_ref` for each geometry and each gamma. These are frozen predictor
decisions, not demonstrated safe budgets. No B2/H1, rank rescue, changed gamma, or geometry rescue.

## Separate failed and recovery accounting

| Action | Original failed run | Authorized recovery |
|---|---:|---:|
| H generation attempts | 4 | 4 |
| CISD generation attempts | 4 | 4 |
| Input verification H matvec | 4 | 4 |
| Reference PF vector actions / H exponential | 0 / 0 | 136 / 136 |
| Candidate cheap PF / H exponential | 0 / 0 | 12 / 12 |
| M1 PF vector actions / H matvec | 0 / 0 | 96 / 96 |
| Same-H ground solves | 0 | 4 |
| Full PF / direct Schur / direct truth / target gap | 0 | 0 |

Cumulative H and CISD attempts are eight each for **four unique new geometries**, not eight
independent cases. The denominator including the saved anchor remains five geometries.
The three saved anchor truth points were reused only after the recovery prediction commit/blob gate.
No new performance scoring was performed, including no partial anchor rescoring.

Preprocessing is separately counted: 456 group-spectrum preparations, 1,048 component eigensolve
batches, four CISD-subspace solves, 36,480 component gate materializations, 191,540 sparse-state
multiplies and four ground verification H matvecs. Internal `expm_multiply` matvec counts remain
unknown; H exponential actions are not silently interpreted as one matvec. The ledger's aggregated
`PySCF_threads=21` field is repeated metadata across worker invocations, not 21 concurrent threads.

Maximum geometry worker concurrency was four; BLAS/PySCF threads were one each. Measured run wall
was 16.836 seconds, including post tests and most freeze operations but not final handoff preparation.
Sampled concurrent coordinator-plus-worker peak RSS was 1.8275 GiB (0.2-second sampling, not a summed
peak or an exact continuous maximum). Swap used was zero at allocation checks; own-process swap was
checked during execution. Final runtime payload is 4,304,772 bytes and remains private. No GPU
query/allocation/kernel or shared-environment/other-job changes occurred.

## New failure and review boundary

All four truth workers stopped while importing `hchain_truth_scoring`. Python requested:

```text
review_response/__pycache__/hchain_truth_scoring.cpython-311.pyc
```

That cache path is not allowlisted. The `.py` source is itself sealed and allowlisted.
`PYTHONDONTWRITEBYTECODE=1` was set but does not prevent attempted bytecode-cache reads.
The guard rejected the request before full-PF construction, Schur, new direct truth or gaps.
The four denials are retained; none is represented as a scientific ineligible condition.

New-geometry safety, gamma_req, oracle headroom, point accuracy, width coverage, physical branch,
and PF/H-reference error decomposition are **not evaluated**. The supplied figure shows only
frozen cheap shifts and empirical widths and supports none of those missing truth-based claims.

GPT/user decision required: whether to separately authorize a truth-import infrastructure correction
and a bounded continuation from these existing committed prediction and ground freezes, without
regenerating inputs, reference, cheap or M1. This handoff does not grant that authority. No second
recovery or continuation will run automatically, and no overall research-direction change is made.

The lightweight source, tests, scalars, hashes, audits and figure are publication targets. Runtime,
integrals, H/group matrices, CISD/ground vectors and unitary arrays remain excluded from Git.
