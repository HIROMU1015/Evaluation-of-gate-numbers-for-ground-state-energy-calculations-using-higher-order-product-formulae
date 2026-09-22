# Practical calibration minimal: frozen selector/scorer design

The sanitizer is the only component that opens an H01 pickle. It emits a
strict allow-list pickle containing the Hamiltonian, grouped component
spectra, term counts, normalized CISD state, and identity hashes. Exact-state
fields and all direct-truth fields are absent.

The selector accepts only the sanitized directory, its manifest, and the
frozen protocol. It derives a CISD/proxy analytic scale using the preregistered
short-time grid, fits signed `echo_imag_3point`, evaluates the cancellation
diagnostic and sentinel, applies the frozen fallback, and writes continuous
selected times. Existing direct-time coordinates are not an input.

After `predictions.json` is hashed and `SELECTION_FROZEN` is written, the
scorer verifies both hashes before it can open H01/P0-3 truth artifacts. It
maps each continuous selection to the nearest saved point within 0.5%, never
interpolates, and reports selected and scored times separately. Scoring cannot
change the frozen prediction file.

All selection, scoring, fallback, abstention, matching, schema, and decision
rules are committed in Phase A. Phase B only supplies caches and saved truth
to these frozen implementations.
