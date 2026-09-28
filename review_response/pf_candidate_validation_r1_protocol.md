# D2R R1 protocol: selected-coordinate cause decomposition

This protocol freezes the stopping point requested on 2026-09-28: run R0 and
R1, write the cause-decomposition report, and stop before designing R2.

## Preserved result

The closed second study remains `complete_no_benefit`. LiF/HCl were independent
at that time, but are development data for D2R and cannot be reused as D2R's
independent evaluation.

## Fixed scope

- Ten already scored selected coordinates: 2 LiF equilibrium, 2 LiF stretch,
  3 HCl equilibrium, and 3 HCl stretch.
- Reuse five byte-identified saved CISD proxies.
- Compute the five missing selected-time CISD proxies.
- Regenerate the same four systems and four exact ground states if no matching
  local cache exists, then compute ten exact-state proxies.
- Read the ten corresponding direct shifts from the closed Phase B artifact.
- Do not compute a new direct PF eigenpair or coordinate.
- Use one CPU process and no GPU allocation or kernel.

## Fixed decomposition

For the signed prediction `f`, CISD proxy `g_cisd`, exact-state proxy
`g_exact`, and saved direct signed shift `delta`, report

```text
f - delta
  = (f - g_cisd)
  + (g_cisd - g_exact)
  + (g_exact - delta).
```

The three terms are labelled model/extrapolation, state substitution, and
proxy--eigenvalue. The original strategy's actual `guarded_error` remains the
budget error; it is not silently replaced by `abs(f)`.

A component is material when its magnitude exceeds the original budget's
allowed underestimation. A sole dominant component must additionally be at
least twice the second largest component. Otherwise the attribution is
`mixed_or_none`. Signed values and cancellation are always retained.

Local CISD- and exact-proxy budget substitutions are post-hoc mechanism
diagnostics. They are not a new operational method, do not revise old budgets,
and cannot be called an independent success.

## Stop rule

Completion requires 10 coordinate rows, 16 strategy rows, five reused CISD
proxies, five new CISD proxies, ten new exact-state proxies, zero new direct
truth, and zero GPU work. The terminal status is
`r1_complete_stop_for_research_direction_review`. R2 is not authorized.
