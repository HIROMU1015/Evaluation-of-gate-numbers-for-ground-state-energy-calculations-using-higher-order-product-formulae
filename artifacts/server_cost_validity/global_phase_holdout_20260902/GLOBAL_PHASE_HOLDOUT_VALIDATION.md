# Global-phase and finite-time proxy validation

Commit: `bbfa757169bfe819e8433ce89f91ab4403957e57`

The uncorrected overlap phase is retained only as raw diagnostic data and is not used for physical costs.

## Priority 1: H9--H11 same-template phase correction

| System | PF | raw t=0 phase | t_ana | e_pert/model | e_proxy/model | C_proxy/C_model | survival | status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| H9 | 4th(m5_best) | 3.141593 | 2.016353 | 0.62928 | 0.62928 | 0.9151819968070867 | 0.99998304 | complete |
| H9 | 8th(Morales-Y8m10b) | 3.141593 | 3.408268 | 0.59969 | 0.5997 | 0.9523469703160108 | 0.99997835 | complete |
| H10 | 4th(m5_best) | 3.141593 | 1.883464 | 0.59231 | 0.59232 | 0.9075058685192307 | 0.99998414 | complete |
| H10 | 8th(Morales-Y8m10b) | 3.141593 | 2.957435 | 0.69421 | 0.69421 | 0.9631840658079804 | 0.99999007 | complete |
| H11 | 4th(m5_best) | 3.141593 | 1.94353 | 0.59263 | 0.59264 | 0.9075721047000262 | 0.99998239 | complete |
| H11 | 8th(Morales-Y8m10b) | 3.141593 | 3.025691 | 0.63333 | 0.63334 | 0.9561758544600316 | 0.99998883 | complete |

## Priority 2: 10% hold-out calibration

| System | PF | proxy cap | direct t_valid | proxy status | direct status |
|---|---|---:|---:|---|---|
| H2 | 4th(m5_best) | 2.004999190556493 | 2.004999190556493 | pass | pass |
| H2 | 8th(Morales-Y8m10b) | 1.6315022863829147 | 1.6315022863829147 | pass | pass |
| H4 | 4th(m5_best) | 1.347607168248673 | 1.347607168248673 | pass | pass |
| H4 | 8th(Morales-Y8m10b) | 1.4663845686659487 | 1.4663845686659487 | pass | pass |
| H5 | 4th(m5_best) | 1.154672461623965 | 1.154672461623965 | pass | pass |
| H5 | 8th(Morales-Y8m10b) | 1.6290527179160472 | 1.6290527179160472 | pass | pass |
| H6 | 4th(m5_best) | None | None | not validated | not validated |
| H6 | 8th(Morales-Y8m10b) | None | None | not validated | not validated |
| H7 | 4th(m5_best) | None | None | not validated | not validated |
| H7 | 8th(Morales-Y8m10b) | None | None | not validated | not validated |

| PF | training -> held-out | predicted cap | held-out direct | result |
|---|---|---:|---:|---|
| 4th(m5_best) | H2,H4 -> H5 | 1.347607168248673 | 1.154672461623965 | failed |
| 4th(m5_best) | H2,H4,H5 -> H6 | 1.154672461623965 | None | not validated |
| 4th(m5_best) | H2,H4,H5,H6 -> H7 | None | None | not validated |
| 8th(Morales-Y8m10b) | H2,H4 -> H5 | 1.4663845686659487 | 1.6290527179160472 | pass |
| 8th(Morales-Y8m10b) | H2,H4,H5 -> H6 | 1.4663845686659487 | None | not validated |
| 8th(Morales-Y8m10b) | H2,H4,H5,H6 -> H7 | None | None | not validated |

## Priority 3 and 4

- H8 direct-like diagnosis: **not validated**. H6/H7 do not provide a continuous direct t_valid on the short-to-analytic interval, and no calibrated moment/Ritz implementation with <=10% H6/H7 error is present; H8 was therefore not run
- H9--H11 safe-time expansion: **not validated** because the complete hold-out prerequisite did not pass; no additional expansion was launched.

## Final classification

- 4th(m5_best): `short-time/asymptotic reference only`
- 8th(Morales-Y8m10b): `short-time/asymptotic reference only`
