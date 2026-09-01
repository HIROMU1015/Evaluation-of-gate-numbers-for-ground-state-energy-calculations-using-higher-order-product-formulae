# H9--H11 GPU overlap-phase cost validation

Status: complete_with_documented_skips

| System | PF | alpha | t_ana | e_pert | e_ov | C_ov/C_model | survival | peak GPU MiB |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| H9 | 4th(m5_best) | 1.928162e-06 | 2.01635 | 2.005640e-05 | 1.558037e+00 | - | 0.999983039 | 1073 |
| H9 | 8th(Morales-Y8m10b) | 9.724491e-10 | 3.40827 | 1.061859e-05 | 9.217457e-01 | - | 0.999978345 | 859 |
| H10 | 4th(m5_best) | 2.532678e-06 | 1.88346 | 1.887814e-05 | 1.667968e+00 | - | 0.999984141 | 931 |
| H10 | 8th(Morales-Y8m10b) | 3.025628e-09 | 2.95743 | 1.229220e-05 | 1.062257e+00 | - | 0.999990067 | 931 |
| H11 | 4th(m5_best) | 2.233800e-06 | 1.94353 | 1.888838e-05 | 1.616417e+00 | - | 0.999982386 | 1157 |
| H11 | 8th(Morales-Y8m10b) | 2.520808e-09 | 3.02569 | 1.121428e-05 | 1.038294e+00 | - | 0.999988833 | 1157 |

C_ov is an overlap-phase proxy, not a direct PF eigenvalue cost.
No direct PF-unitary diagonalization was performed.
