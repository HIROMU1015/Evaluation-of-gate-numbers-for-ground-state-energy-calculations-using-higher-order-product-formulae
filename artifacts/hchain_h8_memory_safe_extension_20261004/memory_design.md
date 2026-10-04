# H8 memory-safe extension: storage/lifetime only

Authority: the user's H8 memory-safe independent-validation extension request,
with base snapshot `50b73a363fa581f8534c399f087b35cb38a4cb70`.
No push, GPU, new system, estimator, selector, margin or threshold is authorized.

The neutral singlet H8 input uses centered linear 1-Angstrom geometry, STO-3G,
RHF/CASCI integral extraction without a CASCI/FCI kernel, the inherited ordered
Almost_optimal_grouper, population (4,4), and determinant CISD. Dimensions are
4900 / 361. K and all numerical identities are measured, not inherited by name.

## Object lifetimes

Generate one group CSR, hash its dense-equivalent bytes row-by-row, save the CSR,
add it to H, and release it. No dense group ensemble is allocated. The same
component diagonalizer is applied one group at a time. Retain only its compact
component spectra. The inherited PF vector method, exponential signs, gate
cache, component cutoff and matvec methods are unchanged.

CISD uses one full dense H to call the unmodified determinant helper. Release H
immediately after the 361-dimensional CISD solve. Predictor uses CSR H, vectors,
small Arnoldi matrices and component spectra only.

Truth keeps one coordinate at a time. The ground solver remains dense scipy
eigh(driver=evd), and direct branch selection remains the frozen Schur helper.
Copy only the chosen ground/continuation vector before releasing the full
eigenvector/Schur array. Delete the previous U before constructing the next U.
No dense solver replacement is authorized by this implementation.

## Equivalence and access

One original H7 r=0.5 coordinate is used as implementation regression only.
Read the original input NPZ's Hamiltonian, CISD and groups; never its exact state.
Compare old and streamed PF action, cheap scalar, M1 point/width and residuals.
Existing strict regression conventions are frozen before this run: absolute
1e-14, relative 1e-12; the complete old/new M1 JSON must additionally be exact.
Saved prediction scalars are regression expectations, not policy inputs.

All scientific source and original artifacts stay byte-identical. Only newly
added source/docs/output paths are permitted. Origin/result commit and verified
snapshot commit remain separate. Python open auditing is not an OS sandbox.
Source hashing and saved H7 resource accounting do not transfer truth to the
predictor. Phase-specific ledgers do not hide preflight actions in the grid.

## Gates and accounting

Real H8 input, component preparation, cold PF, H exponential, warm M1 PF and
H matvec are profiled before any reference/candidate campaign. Record wall,
own-process RSS, explicit full-sector object allocations and cache/component
bytes. Native allocations cannot be counted exactly and are marked unknown.
The input ensemble has zero simultaneously live full-sector dense group matrices.

Reference/prediction runtime estimates use a disclosed twofold planning
allowance on measured primitives, not a rigorous runtime bound. Truth estimates
use saved H7 stage times, cubic dense-solver and quadratic matrix-action scaling,
and the ratio of PF sequence lengths. They are planning arithmetic, not H8 truth.
Memory planning budgets nine dense complex128 matrices plus measured resident
storage: U, Schur T/vectors, identity, conjugate U, Gram, difference and two
native copy/workspace reserves. Unknown native workspace is explicitly noted.
Actual RSS and swap checks remain authoritative. Named-stage wall ceiling is
1800 seconds and memory ceiling is 4 GiB. Preflight infeasibility stops without
reference or prediction; no partial prediction run is used to bypass truth gate.

## Freeze order and stop

Implementation -> equivalence -> input -> preflight gates -> reference/coordinates
-> cheap/q commit -> conditional M1 -> H1 commit -> comparator completion ->
prediction commit -> same-H ground commit -> direct truth/gap commit -> immutable
scoring -> `hchain_h8_extension_complete_review_required`.

If a gate fails, publish only reached stages and its blocked status, not empty
future artifacts. Private runtime is retained in this worktree and never staged.
No result licenses H9/H10, a revised width, policy fitting or another experiment.
