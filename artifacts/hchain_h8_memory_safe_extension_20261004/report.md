# H8 memory-safe independent-validation extension — review stop

Status: `hchain_h8_extension_complete_review_required`.
H8 scientific execution and required focused gates are complete. The optional broader
legacy suite is **not green**; its environment/provenance failures are preserved below.
No rerun, rescue, new threshold, GPU operation, package change or push was performed.

## Main result

H8 B2/H1 chose `0.8*t_ref` with q=0, safely meeting the predeclared 10% target.
Continuous frozen budget fell from **744,895,606.0657071** (B0) to
**498,379,575.8523817**, ratio **0.669059626334297**, a **33.0940%** reduction.
This is a saved, frozen-decision effect in the continuous rotation-cost model,
not a discrete query-count result or end-to-end quantum/classical cost saving.

All four B1 gamma arms (1.01 / 1.02 / 1.05 / 1.10) are also safe and meet the target.
Their B/B0 ratios are 0.669060 / 0.675684 / 0.695557 / 0.728679.
The smallest fixed-frontier safe gamma is 1.01; B2/H1 equal that cheap arm.
H8 does not demonstrate an incremental adaptive-cheap or spectral benefit over it.

M1 has m=8 available at all points, correct physical branch at 3/3, empirical width
coverage at 3/3, and abstention at 3/3 due to no positive QPE allowance. Always-M1
therefore preserves the B0 fallback. Its point error is larger than cheap's error
at all three points. This is not just a width bottleneck in H8: the fixed m=8 point
estimator also does not improve the cheap point estimate here.

| r | signed cheap shift [Ha] | signed M1 shift [Ha] | direct shift [Ha] | E_C [Ha] | E_M [Ha] | M1 width [Ha] |
|---|---:|---:|---:|---:|---:|---:|
| 0.5 | -1.955078636e-6 | -4.785906445e-6 | -1.519055794e-6 | 4.360228423e-7 | 3.266850651e-6 | 0.01190746645 |
| 0.65 | -5.495489791e-6 | -1.464382033e-5 | -4.288153671e-6 | 1.207336120e-6 | 1.035566666e-5 | 0.01540553861 |
| 0.8 | -1.232067565e-5 | -4.564591307e-5 | -9.692096141e-6 | 2.628579514e-6 | 3.595381693e-5 | 0.02067324392 |

All safety uses abs(direct shift), never the signed quantity:
`abs(delta_direct)+1.2*K/(t*B_frozen) <= epsilon_E`.
H8 selected-action total error is 0.00015527559568953009 Ha, below
epsilon_E=0.00015936001019904 Ha; headroom is 4.084414509509924e-6 Ha.
No unwrap integers in different coordinate systems were compared.

## Implementation and input gates

The original H7 r=0.5 regression matches old/streamed PF vector, cheap, M1 point,
width and residuals with differences exactly zero. All old/new M1 fields are exact.
It reads original H7 sanitized members only, not an exact state or truth values.
Strict regression tolerances were fixed before execution, not adjusted afterward.

Neutral singlet H8: linear centered 1-Angstrom spacing, STO-3G, populations (4,4).
Sector 4900; determinant CISD 361; 105 groups; independently counted K=47932.
State norm=1; CISD H-expectation residual=0.14757700840452884 Ha.
The CISD state is not a ground certificate. Ordered groups, coefficients, MO, RHF
integer, basis order, H, CISD and exact binary64 times are frozen in input artifacts.

- H numpy_v1 SHA-256: `b442bb86f29e187c9f63dc3e59463fa655997165aceec2c08c50c257fd365454`
- CISD numpy_v1 SHA-256: `86b7e4f78782476521f8b10d3ebc14798b4562bd09d7d561babffeefc3b5cee7`
- Truth-free alpha_C: 3.3054581991064024e-5; t_ref: 0.9909332903963247
- Times: 0.49546664519816236 / 0.6441066387576111 / 0.7927466323170598
- Hex: `0x1.fb5b9bb58a2e7p-2` / `0x1.49c85869336b0p-1` / `0x1.95e2e2f7a1becp-1`

The earliest fixed five-point reference window qualified; no window/rule was rescued.
No full-sector dense group ensemble was created. Only one group CSR is consumed at
a time into the unchanged component eigensolver. Vector/action/policy bodies remain
inherited. One dense H is used for unchanged CISD; ground/Schur methods are unchanged.
Selected vectors are copied to avoid retaining full eigenvector matrices by views.

## Freeze provenance

Branch: `pf-second-study-v2-hchain-h8-memory-safe-extension-20261004`.

| Stage | origin/result commit |
|---|---|
| Base verified snapshot | 50b73a363fa581f8534c399f087b35cb38a4cb70 |
| Scientific source/protocol | 2e2d4d6 (full identity in implementation manifest) |
| Implementation seal | c93d9fd |
| Equivalence | ca13ecc |
| Input | 5bab841352ec68dc0e2f5e56063b57304cab2721 |
| Resource gates | 958da64 |
| Reference/coordinates | 31387402550cfbda28ebff6a1dea19410b56c60c |
| Acquisition/q | 511315fd1dc134486071c5074ad40d7171319ded |
| H1 | 56afe10164f2d0da9413565965c26a26080706f2 |
| Prediction | b0a67843d3f3f9e17bdd4ed2a078b63ca11a703e |
| Same-H ground | 392e58fb737142bbba862a23e2189242174835ea |
| Truth | 944291272c561a59e42e2b03c25d82353ea2506d |
| Immutable scoring | 12052e9ec3bfa93e6678fe8d494ea01201290f93 |

Publication commit is the commit containing this report; its hash is not embedded
self-referentially. A separate publication provenance record identifies that content
commit. Source registries distinguish origin/result from verified snapshot commits.
Every stage bundle's seven blobs was reverified. No frozen bundle was rewritten.

- Prediction SHA-256: `18b935a0b33b9ed3cf55dabfa9bdc3cc317df4d647a7f8d4245b318d26d83815`
- Truth manifest SHA-256: `69e1f53bf5afa3d920333c1fd7719da91651a4de3a14f6e280258a413294b552`
- Scored manifest SHA-256: `f68433bdc26c7950f421f384d46c155cea615bead303076da7b1e817b2f4ed28`

## Numerical truth and resources

Same-H numerical ground energy=-3.989600634256086 Ha; first gap=0.1386138457940671 Ha;
ground residual=8.541587471422243e-15 Ha. Ground is frozen before PF truth.
All three physical branches resolved. Minimum phase gap=0.06867864851887921 rad;
maximum unitary Frobenius residual=1.433220607251438e-11;
maximum eigenpair residual=8.296626888698614e-15.
Empirical width coverage is diagnostic, not a rigorously certified operational bound.
g_rho_others was not additionally acquired or substituted for the target phase gap.

Measured named-stage wall seconds:

| Stage | seconds |
|---|---:|
| H/group input | 34.7124 |
| Component preprocessing, preflight | 31.7082 |
| Fixed 34-point reference, including loader | 47.3947 |
| Prediction shared preprocessing | 32.4792 |
| Candidate cheap 3 points | 1.2451 |
| M1 comparator 3 chains | 2.3354 |
| Ground, including loader | 125.7555 |
| Truth r=0.5 | 478.5752 |
| Truth r=0.65 | 478.4976 |
| Truth r=0.8 | 480.1973 |

Direct coordinate stages total 1437.2701 s; every named stage is below 1800 s.
Peak RSS=2,507,060 KiB, approximately 2.39 GiB, below 4 GiB. Peaks are not summed.
Preflight estimated truth time 226.5231 s/coordinate underestimated measured ~479 s;
that estimate was planning arithmetic, not a bound, and remains unchanged in the audit.
Truth planning reserved nine dense matrices plus resident storage (3.84 GiB).
Explicit object counts are instrumented Python objects; native allocation counts remain
unknown. An own-process RSS/swap watchdog was active; no resource-stop event occurred.

H8 acquisition counts, phase-separated:
input H/CISD generation 1/1, CISD subspace eigensolve 1, input H verification 1;
preflight PF cold/warm 1/1, H exponential 1, H matvec 1;
reference PF/H exponential 34/34; candidate cheap PF/H exponential 3/3;
M1 PF/H matvec 24/24, chains 3; full H ground 1; full PF/Schur/direct/gap 3 each.
Summed reference counters are 35, and summed M1 counters 25, because preflight is
explicitly included. H-exponential internal matvecs remain unknown, not counted as one.

H1 measured combined decision path=1.46987894 s, plus separately accounted shared
preprocessing=32.47917915 s. q=0 conditional spectral cost is zero.
Comparator completion=2.35916629 s is excluded from H1. Cold standalone always-M1
was not measured; upstream input/reference and reusable cache costs are separate.
Quantum budgets and classical time/memory are not added as unlike units.

## Tests and unresolved repository-wide checks

Six timestamped per-stage focused gates each passed 118 tests, fail/skip 0.
Two initial development runs also passed 118, without separately recorded UTC.
Commands, environment identity, timestamps and complete logs are in execution_audit.json.

The additional full legacy run did NOT pass:
collection failed on missing optional python-flint (`flint`) in
`test_f_hf_mechanism_bridge.py`; pennylane produced one known dependency skip.
A diagnostic partition excluding only that flint-dependent module yielded
**484 passed, 7 failed, 1 skipped**. The seven failures require unavailable old
H2/H4/H6 private runtime (two cases), or an artifact path absent from historical
commit cc3626a8135b647fe283fc60c963de70c5f6b2a5 (five cases).
Those legacy sources/tests are unchanged from the base snapshot.
No package install, old runtime copy, history repair, test expectation relaxation or
further filtered rerun was performed. These are review blockers for a global green
suite, not suppressed failures or new H8 scientific gate passes.

The original truth execution audit's nested access template reports zero while its
explicit top-level counter and truth freeze audit report one ground-array read.
The publication access audit preserves the original template value and records the
explicit counter as authoritative. No original audit or freeze was rewritten.

## H2–H8 evidence and review limits

The integrated saved-scalar table has H2/H4/H5/H6/H7/H8 eligible: 6/6 B2/H1 safe
and meeting the 10% target, all q=0; always-M1 preserves B0 fallback in all six.
H3 retains its original reference-scale-unavailable status and is not a scored sample.
The 18 eligible coordinates are not 18 independent samples.
Odd systems are cation triplets and even systems neutral singlets, so this is not
an isolated parity experiment or general holdout/scaling result.

This controlled family supports cheap-only resource decisions under the frozen rules.
It does not establish a useful q=1 conditional spectral path, operational gap
certification, or general selective-policy performance. Future direction is a
governance review decision, not automatically inferred scientific evidence.

Stop here. H9/H10, new molecules/PF, fitting, margin/width/q changes, C1/D2-B, runtime
transfer and further execution are unauthorized. Private runtime is retained only
in this worktree, excluded from Git. Local result publication only; no push.
