# H5 group-count identity amendment v1.1

The first post-Phase-A H5/m5 attempt stopped before PF-unitary construction
because the server handoff expected 45 commuting groups while the fresh source
preparation produced 43. Both H5 raw files committed in parent result
`c27e31e82ca55fc404ed33123cfd5d2c6a76bc35` also record 43 groups, with the
same `(3,1)` populations and 50-dimensional sector.

After explicit user approval, this amendment changes only the expected H5
group count from 45 to 43. It does not change the generated Hamiltonian,
grouping procedure, physical identity, formulas, grid, cost, precision,
branch tracking, gates, or H7 identity. The stopped attempt has zero direct
points and zero PF unitaries and is not reusable as cache. A new truth-free
Phase A commit is required before restarting H5/m5 in a new output directory.
