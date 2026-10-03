# Resource accounting plan

Keep quantum budget and classical information cost separate. A future authorized replay would record cheap PF actions, cheap H actions, M1 PF vector actions, M1 H matvecs, wall time, peak RSS, and shared/cache work for each H2/H4/H6 condition and exact candidate time. Distinct action types must never be collapsed to one scalar.

The fixed S1A planning convention is `C_C` for saved cheap-arm wall time, `C_S` for saved standalone M1 wall time, and a **saved-arm replay envelope** `[max(C_C,C_S), C_C+C_S]` if `q=1`. That interval is not measured combined H1 runtime or a certified wall-clock bound. Here no matched per-arm costs exist for the still-unfixed candidate coordinates, so `combined_cost_not_evaluable` is the only defensible preflight value.

Do not infer information efficiency from old m5/Y8 direct-solver timings or from unmeasured cache sharing. No resource calculation or action was performed in this preflight.
