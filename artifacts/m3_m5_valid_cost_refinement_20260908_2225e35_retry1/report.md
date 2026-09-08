# Predictable-cost refinement for fixed m3 and m5

| System | m5 10% boundary [pass, fail] | m5 C_valid* | m3 t*/t_ana | m3 C(t_ana) | m3 C(t*) | schedule increase | m3/m5 C_valid* |
|---|---|---:|---:|---:|---:|---:|---:|
| H2 | [0.6375, 0.64375] | 5.8841371e+05 | 1.02 | 5.4410013e+05 | 5.4372168e+05 | 0.070% | 0.924047 |
| H4 | [0.5875, 0.59375] | 2.2712200e+07 | 1.02 | 1.8919144e+07 | 1.8899505e+07 | 0.104% | 0.832130 |
| H5 | [0.4875, 0.49375] | 6.2919507e+07 | 1.03 | 4.3670123e+07 | 4.3576335e+07 | 0.215% | 0.692573 |
| H6 | [0.525, 0.53125] | 1.5754722e+08 | 1.03 | 1.1745275e+08 | 1.1725546e+08 | 0.168% | 0.744256 |
| H7 | [0.525, 0.53125] | 2.9024089e+08 | 1.03 | 2.1621059e+08 | 2.1583503e+08 | 0.174% | 0.743641 |
| H8 | [0.51875, 0.525] | 5.7039703e+08 | 1.03 | 4.1918815e+08 | 4.1832617e+08 | 0.206% | 0.733395 |
| H9 | [0.5125, 0.51875] | 9.2167731e+08 | 1.03 | 6.6923730e+08 | 6.6771893e+08 | 0.227% | 0.724461 |

Cancellation points outside each contiguous 10% model-valid range are excluded from C_valid*.

No coefficient search, H10 calculation, molecule extension, or target-error change was performed.
