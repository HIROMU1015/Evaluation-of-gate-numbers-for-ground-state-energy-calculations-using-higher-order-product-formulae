# Fixed m=3 two-term PF: local geometry and active-space holdouts

Status: complete

The `two_term_center` coefficients were kept fixed. Stretched geometries and the smaller nested active spaces were not used to select these coefficients.

| condition | formula | eta_* | eta_min | eta_t | max unseen residual / epsilon | new/current direct cost | pass |
|---|---|---:|---:|---:|---:|---:|---|
| BeH2_stretch125 | current_m3 | 0.000383818 | 0 | 0 | 0.000735194 | 1.14814 | True |
| BeH2_stretch125 | two_term_center | 5.47121e-05 | 0 | 0 | 8.47157e-05 | 1.14814 | True |
| BeH2_stretch150 | current_m3 | 0.000154552 | 0 | 0 | 0.000296618 | 1.14644 | True |
| BeH2_stretch150 | two_term_center | 6.91009e-05 | 0 | 0 | 0.000115423 | 1.14644 | True |
| H2O_stretch125 | current_m3 | 0.000398296 | 0 | 0 | 0.000747555 | 1.14745 | True |
| H2O_stretch125 | two_term_center | 2.77632e-05 | 0 | 0 | 3.5849e-05 | 1.14745 | True |
| H2O_stretch150 | current_m3 | 0.000733879 | 0 | 0 | 0.00150178 | 1.1487 | True |
| H2O_stretch150 | two_term_center | 5.28638e-05 | 0 | 0 | 7.00065e-05 | 1.1487 | True |
| BeH2_stretch150_631g | current_m3 | 0.00055996 | 0 | 0 | 0.00115853 | 1.14998 | True |
| BeH2_stretch150_631g | two_term_center | 0.000123393 | 0 | 0 | 0.000201 | 1.14998 | True |
| BeH2_stretch150_ccpvdz | current_m3 | 0.0011901 | 0 | 0 | 0.00261485 | 1.15285 | True |
| BeH2_stretch150_ccpvdz | two_term_center | 7.92361e-05 | 0 | 0 | 0.000102896 | 1.15285 | True |
| H2O_stretch150_631g | current_m3 | 0.000254827 | 0 | 0 | 0.0005502 | 1.14459 | True |
| H2O_stretch150_631g | two_term_center | 3.42315e-05 | 0 | 0 | 4.79098e-05 | 1.14459 | True |
| H2O_stretch150_ccpvdz | current_m3 | 0.000244298 | 0 | 0 | 0.000531408 | 1.14443 | True |
| H2O_stretch150_ccpvdz | two_term_center | 3.85989e-05 | 0 | 0 | 5.86643e-05 | 1.14443 | True |
| LiH_CAS2e4o | current_m3 | 0.0328863 | 0.418222 | 0.166667 | 0.364667 | 1.21011 | False |
| LiH_CAS2e4o | two_term_center | 0.00288445 | 0 | 0 | 0.00596183 | 1.21011 | True |
| BeH2_CAS4e4o | current_m3 | 0.00975753 | 0.00152552 | 0.0243902 | 0.0196617 | 1.17554 | True |
| BeH2_CAS4e4o | two_term_center | 0.00104102 | 0 | 0 | 0.00201123 | 1.17554 | True |
| BeH2_CAS4e5o | current_m3 | 0.00280356 | 0 | 0 | 0.00527448 | 1.15928 | True |
| BeH2_CAS4e5o | two_term_center | 0.000315723 | 0 | 0 | 0.000588484 | 1.15928 | True |
| H2O_CAS8e5o | current_m3 | 0.00610384 | 0.000282832 | 0.0243902 | 0.0120059 | 1.16643 | True |
| H2O_CAS8e5o | two_term_center | 0.000874114 | 0 | 0 | 0.00165092 | 1.16643 | True |

The cost ratio is reported separately from prediction accuracy and compares each PF at its own two-term predicted optimum.
eta_t is resolved only on the declared local grid and is not a continuous-optimum claim.
Three-active-orbital cases are excluded because the frozen grouping implementation requires at least four active orbitals; changing the grouping would change the tested PF decomposition.
