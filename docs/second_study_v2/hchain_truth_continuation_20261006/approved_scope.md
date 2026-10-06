# H6 truth only continuation approval

The user accepts Track R commit `0c40a3d7987e0961262bfd38bbb214a9e2946824` as complete
and authorizes one truth-only Track G continuation based on published snapshot
`1aad415bfaed5503508872c1fa5a8a8c12da4193`. Previous failures remain immutable.

Only the four frozen geometries R=0.80, 1.20, 1.40 and 1.60 Angstrom and their three
exact `.5/.65/.8*t_ref` coordinates may acquire full PF, complex Schur/direct shifts
and phase-gap diagnostics, at most twelve each. Continuation within each geometry is
ascending, starting from the same-H ground and then the previous PF branch, never a
predictor-assisted rescue. R=1.00 truth is identity-verified reuse only.

H/CISD generation, reference, cheap, M1 and ground acquisition must remain zero. Existing
input/coordinate/prediction/ground hashes and binary64 coordinates are unchanged. The
prediction and ground commits are `61ae95edce8c4a25167521c0e6e95a83c3cbc4bb` and
`1e5d66a4914bc50a8afa55baa578cca55a227979`. Private inputs and ground arrays are reused
in place from the recovery worktree, not copied or regenerated.

The import correction is infrastructure only: isolate the target cache, require
`PYTHONDONTWRITEBYTECODE=1`, verify the sealed `.py` hash, and directly test the truth-worker
import under the repository access guard. Removing `.pyc` alone does not prevent Python
from attempting to open it, so a source-only loader explicitly bypasses cache reads.
It never allowlists `.pyc` or modifies scientific function bodies. A focused test fail/skip
blocks science. A new runtime failure terminates this continuation without another repair/run.

After a committed truth freeze, the unchanged scalar scorer reports B0/B1 safety, slack,
gamma_req, cost-free oracle headroom, cheap/M1 point errors, empirical width coverage,
physical branch and gated same-H/energy-origin/physical-branch PF/H-reference decomposition.
The original additive gamma=1 slack rule and empirical feasibility claim scope remain fixed.
No B2/H1, rank/width/gamma/time adjustment, policy rescue or new condition is authorized.

The inherited resource policy permits four geometry processes with BLAS/PySCF=1 and live
CPU/RAM/disk reserves, no swap and no GPU computation. Lightweight source, tests, scalar
tables/figures, provenance and manifests must be committed and non-force pushed to the
allowed HIROMU1015 research branch; runtime and arrays remain private.

Stop at `hchain_h6_geometry_sweep_truth_continuation_complete_review_required` on success,
or `hchain_h6_geometry_sweep_truth_continuation_failed_review_required` on failure.
GPT reviews the geometry safety and M1 accuracy/width/resource-value mechanism afterward;
Codex does not change the overall research direction.
