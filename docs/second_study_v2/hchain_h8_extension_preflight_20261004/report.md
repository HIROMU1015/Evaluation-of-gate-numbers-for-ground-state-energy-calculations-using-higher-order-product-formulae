# H8 metadata-only preflight — no scientific execution

Status: `H8_extension_contract_blocked`.

Canonical centered 1-Angstrom STO-3G H8 is neutral singlet, alpha/beta4/4.
Combinatorial sector dimension4900; determinant-CISD dimension361.
One dense complex128 matrix is384160000 bytes (~0.358GiB), a 361-dimensional
CISD matrix is2085136 bytes, one sector vector is78400 bytes.

The current input loader holds every group densely before compact component
spectra are built. Even twelve sector matrices alone exceed4GiB.
Group count, operator bytes, orbitals, CISD, Hamiltonian, candidate references
and runtime manifests are not frozen for H8. Legacy new_3 rotation count47932
is recorded only as an unverified structural candidate, not current_m3 identity.
No matched H8 H/state/PF/truth reuse has been established in the audited Git
metadata. This does not claim that no historical H8 data exists elsewhere.

H7 measured inputs/reference/prediction/truth stage costs are retained in
preflight.json. Dimension/storage/cubic-operation ratios are complexity
arithmetic, NOT measured scaling laws, a wall-time extrapolation or a RAM
bound. All H8 per-stage wall estimates and total peak RAM remain unavailable.
A single PF matrix fitting in RAM does not establish feasibility of the
present dense-group loader or Schur workspace. GPU necessity is unestablished;
GPU execution alone would not solve that CPU input-loader problem.

If separately approved later, work would include34 reference pairs,3 cheap
candidate pairs,24 PF+24 H M1 actions,1 same-H ground and3 PF/Schur/gap points.
None were executed here. Exact input identity and a reviewed memory strategy
are prerequisites; no CPU/server/GPU execution is approved by this preflight.

Sources and their origin/result vs verified snapshot commits are recorded
in preflight.json. Legacy PF errors/ground arrays were not imported as truth.
