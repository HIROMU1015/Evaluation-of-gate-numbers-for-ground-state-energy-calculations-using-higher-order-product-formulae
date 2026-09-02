# Global-phase hold-out validation: superseded partial snapshot

The partial snapshot is now complete: all 16 same-template GPU sweeps finished.
Each JSON in `same_template_sweeps/` evaluates `t=0` and all diagnostic times
with the same transpiled parameterized circuit, and records both raw and
global-phase-corrected overlaps.

Use `GLOBAL_PHASE_HOLDOUT_VALIDATION.md` for the human-readable final report
and `global_phase_holdout_validation.json` for the complete machine-readable
aggregation.  The final status is `complete with failed/not validated
prerequisites`; both PFs are classified as `short-time/asymptotic reference
only`.

Server execution logs and the earlier separately-transpiled `t=0` diagnostics
are intentionally excluded from the committed result set.
