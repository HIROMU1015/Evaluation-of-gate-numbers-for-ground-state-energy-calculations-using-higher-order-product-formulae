# Prospective prediction implementation handoff

Status: **implementation/test/instruction preparation complete; server science not executed here**.
The containing publication commit identifies this handoff. This is not a candidate
prediction result or a `PREDICTION_FROZEN` package.

## Read in this order

1. [Approved scope](approved_prediction_authorization.md) and [machine contract](authorization.json).
2. [GPU-server execution instructions](../../../review_response/gpu_pf_study2_prospective_prediction_prompt_20261006.md).
3. [Local validation record](local_validation.json) and the sealed implementation manifest.
4. Base `ec87adf35a5f8c2812557812ece34f3d41be3da1`'s
   `artifacts/prospective_input_reference_preparation_20261005/review/preparation_summary.json`,
   `candidate_plan.json`, `INPUT_FROZEN.json`, and `review_bundle_manifest.json`.

Inherited 42 source/protocol files and all 54 P3 review entries are unchanged and
verified. P3 keeps 16 attempted = 13 ready + 2 domain-ineligible + 1 input-ineligible.
The new branch contains implementation, tests and instructions only. Root edits
and unrelated worktrees are not included.

## Server-only work remaining

Verify fresh allocation and the original private P3 runtime. Run pre-focused
tests, cheap39, cheap commit, mid-focused tests, unconditional M1 on all39,
post-focused tests, global seal, prediction commit/blob checks, non-force push
and remote SHA confirmation. Then stop for GPT review, truth/scoring still zero.
No frozen runtime or allocation renewal is provided by this Git publication.

Original P3 input origin is `d7a8295b33977afe557975284b0103353416d706`;
verified preparation snapshot is `ec87adf35a5f8c2812557812ece34f3d41be3da1`.
The new source-content origin is recorded separately in implementation_manifest.json;
the publication snapshot is the commit containing that manifest and this README.
The manifest explicitly excludes itself to avoid a self-referential hash.
