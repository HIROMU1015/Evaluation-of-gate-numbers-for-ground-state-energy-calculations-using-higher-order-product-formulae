# Direct PF solver benchmark

Commit: `7d1938bacb3b392643295819daa135ad16ac17fe`

The matrix-free result is not called `e_direct` unless every H6/H7 calibration condition passes the fixed criteria.

| System | PF | raw status | CPU stage reuse | GPU dense |
|---|---|---|---|---|
| H4 | 4th(m5_best) | complete | True | True |
| H4 | 8th(Morales-Y8m10b) | complete | True | True |
| H6 | 4th(m5_best) | complete | True | True |
| H6 | 8th(Morales-Y8m10b) | complete | True | True |
| H7 | 4th(m5_best) | complete | True | True |
| H7 | 8th(Morales-Y8m10b) | complete | True | True |

## Matrix-free calibration

Status: `calibration evaluated`

Pointwise tests are necessary but not sufficient: final proxy acceptance also requires pair-cost-ratio and last-three-K stability.

H8 and larger systems must not be started until the complete H6/H7 direct-substitute or calibrated-proxy rules pass and the selected K/cutoff are frozen.
