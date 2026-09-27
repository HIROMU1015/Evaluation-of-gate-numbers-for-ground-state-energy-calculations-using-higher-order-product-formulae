# H5 backend-parity comparison amendment v1.2

The first identity-amended H5/m5 run built all 31 GPU direct points, but its
parity checker compared them with parent CPU points at the same relative-grid
index rather than the same physical time. The fresh and parent short-time fits
gave analytic times differing by about `2.79e-6`, so the paired physical times
differed by as much as `4.75e-6` and the rapidly varying direct shift differed
by up to `1.73e-7 Ha`.

The exact GPU and CPU unitaries differed by only `9.71e-16` at the fixed
unitary-parity time. A diagnostic reconstruction of all 31 CPU points at the
identical physical times used by the GPU gave a maximum direct-shift
difference of `3.37e-15 Ha`, with all maximum-ground/continuous identity
relations matching.

This amendment fixes the parity implementation to compare GPU and fresh exact
CPU shifts at identical physical times. The `1e-9 Ha` shift threshold,
`1e-10` unitary threshold, fresh short-time fit, grid, branch rules, and every
scientific gate remain unchanged. The parent-raw comparison remains recorded
as a schedule-difference diagnostic. The failed-parity raw is preserved but
is not reused as cache; a new Phase A commit and new H5 output are required.
