# Bounded odd-chain independent-validation extension

The user's H3/H5/H7 + H8-preflight attachment authorizes one extension. The base
is `5a9226a94fad0b578df1a53edd1a29e3571ad8c3`. Its remote-tip gate is verified by
the user's pasted live `git ls-remote` output, not an independent network check
by this agent. No push is authorized. Existing H2/H4/H6 sources/artifacts and
root user changes must remain unchanged.

## Canonical identity audit

Priority current_m3 source `run_two_term_pf_m3_holdout_server2.py` explicitly
uses H7 charge +1 and multiplicity 3. The main size-series uses
`chemistry_hamiltonian.call_geometry`, which returns +1/triplet for every odd
chain. These two priority sources agree; a historical alternative H7 identity
is not automatically inherited. All chains are centered, linear, 1 Angstrom
spacing, STO-3G, all spatial orbitals active, no frozen core. H3 uses the main
small-system interleaved JW/minimal commuting-greedy grouping convention;
H5/H7 use the H4/H6/H7 half-spin Almost_optimal_grouper convention. Each path
retains native insertion order; no alternative grouping is tested.

Canonical populations/dimensions fixed before science:

| System | charge / multiplicity | alpha / beta | sector / CISD | primary rank |
|---|---|---|---|---|
| H3 | +1 / 3 | 2 / 0 | 3 / 3 | 2 |
| H5 | +1 / 3 | 3 / 1 | 50 / 38 | 8 |
| H7 | +1 / 3 | 4 / 2 | 735 / 171 | 8 |

SCF uses the previous newly generated H6 recipe's `scf.RHF`, conv_tol=1e-12,
max_cycle=200, symmetry=False. Installed PySCF 2.7 dispatches nonzero spin to
ROHF. CASCI.get_h1eff obtains integrals only; no CASCI kernel/FCI is run. H3's
OpenFermion spin-orbital expansion is identical in convention to the main
small-system JW path. Coefficient/orbital bytes are new snapshots, not claims
of byte-identical historical caches. Hamiltonian/CISD/group hashes and K are
frozen at input commit before any reference acquisition. Removing every scalar
identity follows the inherited energy convention. The CISD subspace solve is
explicitly counted even when its dimension equals H3's population sector;
it is not hidden ground-truth input or a claimed ground certificate.

## Frozen calculation and decision rules

`protocol.json` pins binary64 PF coefficients/grid, environment and ceilings.
The inherited leading_fit, rank-aware Arnoldi, empirical width, B0, B1,
no-fit B2/H1 and shift/gap immutable scorer functions are used unchanged.
H3 fit failure is recorded without changing the grid, noise floor, precision,
window or state. Qualified H5/H7 proceed independently, as authorized; any
unqualified system has no candidate/truth calculations and no invented B0.

Stages: input commit -> reference/coordinate commit -> cheap -> q commit ->
q=1 M1 -> H1 commit -> q=0 comparator M1 -> prediction commit -> ground commit
-> direct truth/gap commit -> immutable arithmetic scoring -> review stop.
Every freeze is an actual explicit-file Git commit and byte/hash gate. M1
primary deficiency remains abstention; nonfinite width is unavailable, never
replaced with a narrower finite width. Truth warnings remain indeterminate.
The first direct point uses exact-ground overlap; remaining points use prior
selected-vector continuation. No new/lower-time anchors are introduced.

Each system has one H/CISD generation, at most 34 reference pairs, 3 candidate
cheap pairs, 3*primary M1 PF/H actions, one same-H ground solve, 3 full PF/Schur/
direct/gap evaluations. Each named input/reference/cheap/M1/ground/direct stage
has a 1800s wall ceiling and process peak RSS <=4GiB. CPU process and BLAS
threads are one. H3/H5/H7 share no oracle state, and H8 is not an executable
runner choice. No retry, alternate cache/backend, reordering or rescue.

Python open audit permits method source/protocol and this run's own outputs,
not historical truth artifacts. It is an audited boundary, not an OS-hermetic
sandbox. Runtime NPZs are allowlisted, member/hash validated and untracked.
All numeric gates/phase resource counts must pass before formal completion.
Legacy truth-reading/full tests are deferred until odd prediction commit.

## Interpretation and publication

Safety uses abs(direct shift) + beta*K/(t*B_frozen) <= epsilon; target also
requires t>T0 and B<=0.9B0. Unwrap integers from different origins are never
compared. Empirical width coverage is not a spectral certificate. The unit
of interpretation is each system, not independent samples at each time.
Charge and spin change with parity: no isolated parity theorem, statistical
significance or asymptotic scaling claim is permitted.

Resource ledgers are phase/system-specific. Constructor group preprocessing,
component eigensolves, gates and sparse multiplies are counted separately.
Expm_multiply internal H matvec count remains unknown. Process high-water RSS
is not an independently measured per-system peak and peaks are not summed.
Combined H1 scheduled time includes q/H1 Git freeze overhead; net acquisition
time and shared preprocessing remain separate, not a rigorous cost envelope.

Origin/result and verified snapshot commits are separate. Content is committed
before provenance manifests; manifests self-exclude. Required top-level aliases
are created once at final publication and point to the immutable stage bundles.
H8 preflight can use combinatorial dimensions, existing metadata and measured
stage costs, but cannot run H8 construction, reference, M1, ground or truth.
Absent exact input identities are marked unverified, not assumed reusable.

Stop at `hchain_h3_h5_h7_extension_complete_review_required`. No further
research phase or H8 execution is authorized.
