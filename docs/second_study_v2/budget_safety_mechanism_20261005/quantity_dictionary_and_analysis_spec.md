# Quantity dictionary / fixed analysis rules

All energies and widths are in Hartree; t is Hartree inverse. beta=1.2 and
epsilon=0.00015936001019904 are inherited, not fitted. K is the native PF rotation count,
not a classical matvec count. All rows retain native candidate ID and exact binary64 time.

## Cheap safety

delta is the signed truth PF shift; e=abs(delta) is the error entering an uncorrected QPE
budget. c=abs(delta_C) is cheap magnitude. Signed point error abs(delta_C-delta) is not e-c.
a=beta*K. B_gamma=gamma*a/[t*(epsilon-c)] for c<epsilon, positive t,K,gamma.
Fixed historical gamma={1.01,1.02,1.05,1.10}; gamma=1 is a labelled arithmetic diagnostic.

M_gamma=(1-1/gamma)*(epsilon-c).
slack=M_gamma-(e-c)=epsilon-e-(epsilon-c)/gamma.
Underestimation e-c may be negative. At gamma=1, M=0 and the ratio is undefined;
never divide by zero or substitute a large/small finite ratio. Use slack for every gamma.
For e,c<epsilon, gamma_req=(epsilon-c)/(epsilon-e), and the restricted gamma>=1
requirement is max(1,gamma_req). This is an oracle diagnostic, not a new chosen gamma.
c>=epsilon invalidates the cheap formula; e>=epsilon admits no finite safe uncorrected
budget. Missing/nonfinite input is indeterminate, not an optimistic fallback.

For any actually frozen budget B, use
capacity_B=epsilon-c-a/(t*B), slack_B=capacity_B-(e-c)=epsilon-e-a/(t*B).
HF inherited B0 need not equal a newly evaluated T0 B_1.01. Do not silently replace it.
Reconcile every historical selected decision against its saved safety result; use no
tolerance to turn an unsafe row into safe. Arithmetic reconciliation tolerance checks
floating evaluation differences only (relative 1e-12, absolute 1e-15 Hartree).

## Spectral width and branch

E_M=abs(delta_M-delta), E_C=abs(delta_C-delta). Coverage E_M<=w is empirical.
Budget denominator epsilon-abs(delta_M)-w, finite non-abstained M1 budget, rank gate,
candidate eligibility and selected-action fallback are separate fields.

At the same candidate and a named safe comparator B_C, derive
w_win(eta)=epsilon-abs(delta_M)-a/[t*(1-eta)*B_C], eta in {0,0.10}.
eta=0 means budget noninferiority, eta=.10 is the inherited 10% arithmetic target;
neither changes the frozen selection or becomes a fitted practical-effect threshold.
Negative w_win means no nonnegative width can attain the named target. Eligibility/rank
gates remain independent even when a scalar window is nonnegative.
Comparators are native baseline (HF B0, H-chain B0, HCl main same-time gamma1.02) and
all already frozen fixed-cheap same-time gamma rows. Unsafe comparators are labelled
invalid for a safe-resource comparison, not used as a spectral success benchmark.
Widths are never shrunk. Physical branch evidence is reused, raw unwrap labels are not compared.

## PF/H-reference error decomposition

Only after verifying saved prediction/ground/truth Hamiltonian hashes, sector identity,
ground-vector linkage, exact coordinate, resolved same physical energy lift, and matching
saved absolute PF target E0+delta, report
A=Ehat_PF-E_PF, R=Ehat_H-E0, delta_M-delta=A-R.
Use the actually used primary prefix (including rank-reduced prefixes), not the requested rank.
Report closure rounding residual separately; do not clamp it to zero. Energy-scale ULP
rounding allowance is numerical reconciliation, not an uncertainty width/certificate.
Absent independent same-H E0/absolute target metadata is indeterminate. In particular,
HCl audit's truth_target_on_h_reference is not a replacement for E0+delta.
The decomposition does not identify the causal source of a state/rank failure.

## Native-contract oracles and H-chain leading model

B_truth(t)=a/[t*(epsilon-e)] for saved valid e<epsilon.
B*_native=min over that condition's three frozen candidates only; missing truth would
make an incomplete-candidate oracle, never interpolation or continuous-time optimization.
Savings relative to a named frozen safe reference are descriptive only. No cost-free
oracle is called an attainable operational intervention.

For H-chain c=alpha*t^4 and t_ref=(epsilon/(5*alpha))^(1/4), the fixed r=.5 -> .8 model
ratio is [.5*(1-.5^4/5)]/[.8*(1-.8^4/5)]. Other factors are held fixed.
Record model arithmetic ratio, saved selected/B0 ratio, percentage-point difference and
saved safe status separately. The difference is not an additive causal explanation.
Common positive gamma cannot change argmin on a fixed eligible set; this says nothing
about gamma-dependent eligibility/fallback. No new selector or fit is performed.

## Costs, evidence and validation

Read only the frozen source registry of tracked JSON/CSV/Markdown, never .runtime, cache,
pickle, vector, matrix, unitary or exact state. Registry separates first byte-identical
artifact commit at this path from verified snapshot commit; numerical origin is not
inferred from a republishing commit. Saved resource leaves are copied with original
field path and unit/scope, not summed. Overlapping wall timers and process RSS peaks
are not rigorous envelopes. Internal expm matvec unknown remains unknown.
Synthetic stdlib tests precede the real scalar run. Verify source identity before and
after, cross-check scalar joins and all saved safety/coverage flags, and inspect outputs.
Do not run legacy tests that execute molecular science. Output manifests self-exclude
explicitly. New scientific acquisition counters remain 0; scalar arithmetic is not 0.
