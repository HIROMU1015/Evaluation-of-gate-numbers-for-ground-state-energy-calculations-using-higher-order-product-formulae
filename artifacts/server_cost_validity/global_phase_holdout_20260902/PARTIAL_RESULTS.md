# Global-phase hold-out validation: partial results

This snapshot contains 15 completed same-template GPU sweeps.  Each JSON in
`same_template_sweeps/` evaluates `t=0` and all diagnostic times with the same
transpiled parameterized circuit, and records both raw and global-phase-
corrected overlaps.

Completed systems and product formulas:

- H2, H4, H5, H6, H7, and H9: `4th(m5_best)` and
  `8th(Morales-Y8m10b)`
- H10: `4th(m5_best)` and `8th(Morales-Y8m10b)`
- H11: `4th(m5_best)`

Not included in this partial snapshot:

- H11 `8th(Morales-Y8m10b)`, which was still running
- the final hold-out aggregation and finite-time-support classification
- server execution logs and separately-transpiled `t=0` diagnostic results

Consequently, these files are raw validation inputs rather than a completed
scientific conclusion.  The final aggregation must be generated after both H11
sweeps finish.
