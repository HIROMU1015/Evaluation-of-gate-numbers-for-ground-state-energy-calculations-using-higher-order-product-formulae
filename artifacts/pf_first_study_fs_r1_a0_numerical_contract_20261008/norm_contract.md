# Vector norm and echo contract

Input |l2 norm−1|≤1e-12; PF output and exact-H reference |l2 norm−1|≤1e-10. Inclusive comparisons use the computed binary64 norm error, with no hidden renormalization, rtol or extra ULP slack.
The future adapter adds the requested norm gate instead of retaining v1's stricter squared-norm predicate. The Phase05 MGS/Ritz arithmetic is unchanged; no invalid state is normalized away.
Reference exp(+iHt)psi is the bra representation of the exp(−iHt) echo. Both evolutions have the same mathematical norm; sign convention is unchanged.
Echo real/imag/magnitude must be finite. Cauchy bound uses tau_round=64 eps N max(norm_reference norm_PF,1), frozen before any observation.
At N=1568 this inherited guard scale exceeds gamma_(8N)=8N eps/(1−8N eps), the standard conservative complex-dot accumulation scale. It audits arithmetic sanity, not propagation error or truth.
