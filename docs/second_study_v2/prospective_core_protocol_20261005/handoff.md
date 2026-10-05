# 16-condition prospective protocol / implementation handoff

Status: `prospective_protocol_implementation_ready_server_preparation_required`.
**P1/P2 are complete locally; P3 molecular preparation has NOT been run.**
The authorized P3 is conditional on the server history, actual allocation and
environment/readiness gates. Direction C/RQ/claim scope remains GPT's approved scope.

- Branch: `pf-study2-prospective-preparation-20261005`
- Preflight origin / verified snapshot: `f5e737699e66731fcdd26c434652c4e62ca6b3c3`
- P1 protocol origin / verified freeze: `dc10db0e2b9be860239cb18b0c9275bdd24617d2`
- P2 code/test origin / verified snapshot: `e9b0981ec4e809c0dbcc77bfcf5a6efa653f7bdc`
- Publication snapshot: the commit containing this document (no self-referential embedded SHA).
- Original GPT attachment SHA-256: `f2e20c32d8ecbdd3961da782264d82e45a469c284e95bb1ccf7b7f7b367e316c`.
  The archived review is LF-normalized, with a different file hash.

## What is fixed

16 conditions: LiH/LiF/BeH2 four each (used-family new condition/contract) plus
CH2 nominal triplet ROHF four (conditional repository-tracked family-unseen).
HCN is excluded/deferred. Fixed (5,3) populations mean an Ms=1 sector, not a pure
total-spin or global molecular ground-state certificate. No unapproved spin diagnostic added.

Canonical current_m3, per-condition K, determinant CISD, frozen 34-point grid
0.02–1.8 Ha^-1, first qualifying window5/order4/R²0.999/floor5e-12 Ha,
t_ref leading-fit rule, ratios0.8/1.0/1.2, all-three domain gate and no rescue.
B0 is future benchmark only; current B2/H1 is not executed. Future M1 compares
all eligible candidates; candidate/M1 and truth/scoring require separate approvals.

P3 wrapper: input workers -> all16 terminal identities -> input commit/byte freeze ->
reference-only workers -> all34 points then fit -> candidate-plan/hex -> review stop.
Reference caps are cumulative 34/34 per condition, 544/544 total.
Same-condition atomic STARTED prevents duplicate/repeated molecular execution.
Allocation-reserved independent workers can be queued by a server supervisor;
the CLI itself never launches unbounded parallel jobs.
Runtime CSR/state files stay private under the new output's `.runtime`; Git contains hashes/scalars only.

## Verification and limits

Focused synthetic/stub tests: **41 passed, fail/skip0**.
NumPy/SciPy/PySCF/OpenFermion readiness and all three loaded OpenBLAS backends
were actually exercised locally with thread count1. Source/commit/hash gate: **42 files PASS**.
No packages/shared environment changed. No GPU queried.
Molecular SCF/H/CISD/reference/candidate/M1/ground/direct/gap/scoring counts: **all0**.
Synthetic small matrices, fit fixtures and stub integrations are implementation checks,
not experimental molecules or prospective validation results.

History: root Git store333 reachable commits/3034 text blobs; worktree store initially
332/3005, then333/3015 including P1. Expanded aliases and literal C/H/H atom lists/strings
found no prior tracked CH2 science; additional matches are this turn's governance/design.
Private/untracked/archive/binary/unreachable/opaque dynamic geometry are not certified absent.
The server's extra local-only refs still require its own full content audit/manual match review.

Server CPU/RAM/wall/disk allocation is **not established**. Host128CPU/~1TB is not a quota.
Server molecular ROHF generation, fit success, eligible candidate count and actual
classical costs have not been tested. Legacy truth-reading tests remain deferred.

## Server next action / GPT reading order

Send `review_response/gpu_pf_study2_prospective_preparation_prompt_20261005.md`
at this publication commit to server Codex. It contains the precise gates/commands,
private allocation/history schemas, freeze order, caps, publish policy and P3 stop.

Read: this handoff -> protocol.json/conditions.json -> CH2_history_geometry_supplement.json ->
P2_validation.json/implementation_manifest.json -> server prompt.
The source registry preserves origin versus verified snapshots separately.
`bundle_manifest.json` excludes itself and `.runtime` explicitly.

P3 stopping status, only AFTER server preparation:
`prospective_input_reference_preparation_complete_review_required`.
Then GPT reviews fit/eligibility/time/sector/K/resource/failures.
Do not execute candidate cheap, M1, truth/gap or performance scoring before their separate approvals.
