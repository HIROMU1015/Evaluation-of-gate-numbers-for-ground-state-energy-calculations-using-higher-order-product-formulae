# H-chain direct optimal-time scaling: partial result through H6

- Status: `failed_numerical_or_boundary_validation`
- Decision: `not_scorable_due_to_numerical_or_boundary_gate`
- Parent protocol SHA-256: `12d10562cf481b836242786462184d8a6ffb342153404c9bf84ff4d5ca836ab9`
- Sector amendment SHA-256: `5ca0ea30f9ad08bc7e4a54fcd8bab8f50195752dcaf3717c219281a458b0122e`
- Partial-stop amendment SHA-256: `526bdede05c1b39d0fab21e062b39a48284a1338fd51bc3c94fd3488732c70ff`
- Scope: H2/H4/H6 form the even-family scaling analysis; H5 is descriptive only; H7 has zero completed direct points.

## Direct grid optima

| system | family | PF | t_ana | t_grid* | t_grid*/t_ana | min cost | 1% interval | zero-crossing assisted | status |
|---|---|---|---:|---:|---:|---:|---|---|---|
| H2 | even_neutral_singlet | m5 | 3.39638459 | 4.75493843 | 1.400 | 270589.811 | [1.400, 1.400] | True | scorable |
| H2 | even_neutral_singlet | y8 | 6.08764057 | 7.00078665 | 1.150 | 343114.212 | [1.150, 1.200] | False | scorable |
| H4 | even_neutral_singlet | m5 | 2.31036235 | 3.46554352 | 1.500 | 10516195.5 | [1.500, 1.500] | True | scorable |
| H4 | even_neutral_singlet | y8 | 4.62400672 | 6.24240907 | 1.350 | 9838600.92 | [1.350, 1.350] | True | scorable |
| H5 | odd_cation_triplet | m5 | 2.59399773 | 3.50189693 | 1.350 | 22801399.4 | [1.350, 1.350] | True | scorable |
| H5 | odd_cation_triplet | y8 | 5.10023598 | 6.37529497 | 1.250 | 23987813.7 | [1.250, 1.250] | True | not_scorable_gate_failure |
| H6 | even_neutral_singlet | m5 | 2.08465064 | 2.81427836 | 1.350 | 62602997.5 | [1.350, 1.350] | True | scorable |
| H6 | even_neutral_singlet | y8 | 3.81154325 | 4.76442907 | 1.250 | 70502735.8 | [1.250, 1.250] | True | scorable |
| H7 | odd_cation_triplet | m5 | — | — | — | — | — | — | not_executed_user_stop |
| H7 | odd_cation_triplet | y8 | — | — | — | — | — | — | not_executed_user_stop |

## Even-family scaling decisions

| PF | exponent b | power-law LOO max error | constant LOO max error | decision |
|---|---:|---:|---:|---|
| m5 | -0.475133 | 4.034% | 44.242% | small_system_predictable_requires_H8_holdout |
| y8 | -0.330392 | 41.515% | 38.752% | no_predictable_power_law_on_current_sizes |

## Limits

- This is partial completion through H6, not completion of the parent H2/H4/H5/H6/H7 protocol.
- `t_grid*` is a discrete minimum in the fixed 0.20–1.70 `t_ana` domain, not a global optimum over all positive time.
- H5 is not pooled with the even neutral singlet family, and one odd-family size cannot support a scaling fit.
- H7 and H8 were not executed. The H2/H4/H6 relation is retrospective small-system evidence only.
- The cost is the repository continuous QPE precision-allocation proxy, not a complete end-to-end QPE implementation cost.
