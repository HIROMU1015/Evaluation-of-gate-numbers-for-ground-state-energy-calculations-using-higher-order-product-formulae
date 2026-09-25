# F03: small a4 versus small D4 operator

Status: **complete_with_findings**

## Molecular H-chain conditions

| system | PF | |a4| | ||D4||2 | |a4|/||D4||2 | ||(D4-a4)|0>||/|a4| | a6 t_ana^6 / epsilon | a8 t_ana^8 / epsilon | direct error / epsilon |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| H2 | yoshida4 | 1.002177e-03 | 1.125360e-03 | 0.8905 | 0.511 | 0.0030 | -0.0000 | 0.1970 |
| H2 | current_m3 | 2.738412e-06 | 2.144880e-05 | 0.1277 | 7.768 | 0.0090 | 0.0002 | 0.1908 |
| H2 | two_term_center | 4.656046e-06 | 1.609432e-05 | 0.2893 | 3.309 | 0.0056 | -0.0000 | 0.1944 |
| H2 | m5_best | 2.404951e-07 | 9.697393e-06 | 0.0248 | 40.310 | 0.0453 | 0.0064 | 0.1441 |
| H4 | yoshida4 | 4.711579e-03 | 1.271635e-02 | 0.3705 | 0.800 | 0.0035 | -0.0000 | 0.1965 |
| H4 | current_m3 | 1.287421e-05 | 2.131099e-04 | 0.0604 | 13.342 | 0.0106 | 0.0003 | 0.1890 |
| H4 | two_term_center | 2.188967e-05 | 1.580265e-04 | 0.1385 | 5.939 | 0.0065 | 0.0000 | 0.1934 |
| H4 | m5_best | 1.130650e-06 | 9.643771e-05 | 0.0117 | 67.494 | 0.0536 | 0.0103 | 0.1182 |

The optimized PFs reduce the ground-state expectation much more than the full D4 norm. In particular, m5_best has a centered D4 action 40--67 times larger than |a4|, so its small leading energy coefficient is not a globally small error operator.

At the one-term analytic time, the m5_best a6 contribution reaches 0.0453--0.0536 of epsilon. Its direct error is below the one-term value through higher-order cancellation, not because those terms are absent.

## Exact/HF/CISD state comparison

HF changes the D4 expectation substantially for the optimized PFs, whereas CISD remains much closer to exact. The maximum relative D4 expectation error is 14.943 for HF and 0.309 for CISD.
Approximate-state expectations remain diagnostics and are not labelled as direct PF eigenvalue shifts.

## Artificial split-Hamiltonian family

The family uses A(lambda)=X+lambda Z and B=Z with Yoshida fourth order. The fitted a4 zero is lambda=-2.577350269189636. As lambda approaches this point, ||D4|| remains finite while t_ana and higher-order contributions grow.

At |lambda-lambda0|=0.03 the direct error at the one-term time is 0.925--1.361 epsilon; by distance 0.01 it exceeds 5 epsilon on both sides. At the closest sampled distance 0.001 it reaches 104.5--105.0 epsilon.
All artificial-family direct points retained continuous/maximum-ground branch agreement, so this growth is not a branch-selection artifact.

## Decision

Treat |a4|, ||D4||, and ||(D4-a4)|psi>|| as distinct diagnostics. A PF with small |a4| should not receive an enlarged one-term time unless the next contributions or a direct calibration bound are also checked.

## Scope

The molecular conclusions cover the stored H2/H4 partitions and four fourth-order PFs. The artificial family establishes a constructive mechanism, not a frequency estimate for molecular Hamiltonians.

## Files

- `audit.json`: checks, rows, and findings.
- `exact_condition_metrics.csv`: exact-state operator and finite-time diagnostics.
- `state_operator_metrics.csv`: exact/HF/CISD D4 diagnostics.
- `artificial_family.csv`: continuous a4-zero approach.
- `manifest.json`: source, input, and artifact hashes.
