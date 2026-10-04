# H3/H5/H7 independent-validation extension — review stop

Status: `hchain_h3_h5_h7_extension_complete_review_required`.
Attempted systems: three. Applicable reference scales: two. Scored coordinates:
six on H5/H7, not nine independent samples. H3 is an explicit protocol
applicability failure, not silently omitted success. No H8 science or push.

## Result

H5/H7 both have q=0; H1=B2 and select 0.8*t_ref. Both are safe and meet
the frozen 10% target. Relative to the benchmark B0, continuous rotation-cost
proxy reductions are 33.0049% and 32.8709%.
Fixed cheap gamma=1.01 chooses exactly the same actions/budgets and is safe.
All four frozen gamma arms are safe on both systems. Thus this extension
does NOT demonstrate adaptive-cheap improvement, spectral incremental
resource benefit, or q=1 conditional performance.

Always-M1 retains B0 fallback on H5/H7. M1 branch diagnostics and empirical
width coverage pass 6/6; four policy abstentions remain unchanged.
M1 is not uniformly more accurate: it improves point error only at the first
two H5 coordinates, not the third H5 coordinate, and none of the H7 coordinates.

H3 has no qualifying window under the unchanged 34-point grid, 5e-13 Ha
noise floor, order4/tolerance0.2/R2>=0.999 rule. Status:
`H3_reference_scale_unavailable_under_frozen_protocol`.
No substitute reference, candidate, B0, M1, ground or truth was generated.

## Canonical convention and integrated table

Priority current_m3 H7 and main size-series sources agree on odd cation
triplets: charge +1, multiplicity3. Even chains are neutral singlets.
This is NOT an isolated parity experiment. Grouping follows the canonical
small-H3 versus integral H5/H7 dispatch, with ordered-group/term and matrix
hashes frozen before reference acquisition. Coefficients are exact canonical
current_m3 binary64, not legacy new_3 or an ULP variant.

| System | charge/multiplicity | sector/CISD | t_ref | q | selected r | B/B0 | B2/H1 safe | min safe gamma | M1 policy | branch | width |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H2 | 0/1 | 4/4 | 1.8470023167315772 | 0 | 0.8 | 0.6705717434 | PASS | 1.01 | B0_fallback | 3/3 | 3/3 |
| H3 | 1/3 | 3/3 | unavailable | — | — | — | not scored | — | not_executed_reference_unavailable | 0/0 | 0/0 |
| H4 | 0/1 | 36/27 | 1.237648718781152 | 0 | 0.8 | 0.6716956053 | PASS | 1.01 | B0_fallback | 3/3 | 3/3 |
| H5 | 1/3 | 50/38 | 1.4108552969899706 | 0 | 0.8 | 0.6699509060 | PASS | 1.01 | B0_fallback | 3/3 | 3/3 |
| H6 | 0/1 | 400/118 | 1.0864029909482193 | 0 | 0.8 | 0.6703472188 | PASS | 1.01 | B0_fallback | 3/3 | 3/3 |
| H7 | 1/3 | 735/171 | 1.1581877773296543 | 0 | 0.8 | 0.6712914474 | PASS | 1.01 | B0_fallback | 3/3 | 3/3 |

H2/H4/H6 are read-only saved results from 5a9226a94fad0b578df1a53edd1a29e3571ad8c3.
Their runtime/ground/matrices were never opened or recalculated here.
The integrated denominator is six attempted systems: five eligible/scored,
one reference unavailable. Eligible five all have q=0, safe target decisions
identical to fixed gamma=1.01; no statistical significance, scaling exponent,
unused-holdout generalization, or parity theorem is claimed.
See h2_h7_integrated_summary.csv and integrated_source_registry.json.

New dimensions/group count/K: H3=3/7/700, H5=50/43/6656, H7=735/105/27552.
CISD residuals: H3=1.00974e-28, H5=0.0149065760, H7=0.0802406401 Ha.
H3 CISD fills its population sector; that authorized input-subspace solve
is counted explicitly, not hidden external exact-ground input.

## New coordinate diagnostics

All shifts/errors/widths are Ha; ratios use the frozen reference.
Safety always uses abs(direct shift), not the signed diagnostic quantity.
No absolute unwrap integer was compared to a relative unwrap integer.

| System | r | direct signed shift | cheap point error | M1 point error | empirical width | original abstain |
|---|---|---|---|---|---|---|
| H5 | 0.5 | -1.9731444680e-6 | 1.0537959698e-8 | 7.6241235295e-10 | 4.9718982973e-5 | no |
| H5 | 0.65 | -5.5619811154e-6 | 2.0316859032e-8 | 7.4396340956e-9 | 1.3806045746e-4 | no |
| H5 | 0.8 | -1.2543333340e-5 | 2.0018827459e-8 | 4.5585589686e-8 | 3.2949754010e-4 | allowance |
| H7 | 0.5 | -1.8244081966e-6 | 1.6614301092e-7 | 4.1576372471e-7 | 4.0688847133e-3 | allowance |
| H7 | 0.65 | -5.1515629436e-6 | 5.0466444641e-7 | 1.1645288132e-6 | 5.1088128234e-3 | allowance |
| H7 | 0.8 | -1.1646325874e-5 | 1.1962331379e-6 | 3.4118761398e-6 | 6.8387256652e-3 | allowance |

H5/H7 frozen B0: 72655064.29739687 / 366426028.97149634.
Frozen B2/H1: 48675326.15022335 / 245978659.33625528.
Their safety headrooms are 1.4338098427e-6 / 2.6469009714e-6 Ha.
The unchanged safety rule is abs(delta_direct)+1.2*K/(t*B_frozen)<=epsilon_E,
epsilon_E=0.00015936001019904 Ha, with no ceil/discrete model.
Branch correctness is strict E_M<g_phase/(2*t); empirical E_M<=w_M is not a
spectral certificate. g_rho_others remains unacquired, not replaced by a
target chord gap. Root coordinate_scoring.csv retains exact times/hex,
physical lift diagnostics, original abstentions, gaps and numerical quality.

## Freeze and provenance

Base: 5a9226a94fad0b578df1a53edd1a29e3571ad8c3.
Remote gate: user-observed live ls-remote output; not independently network
verified by this agent. Source content: 85c33f0951aa04635ca440c7fd9689013dbe55d2.
Source/provenance seal: 3f93701b83d875e156dfb398ae5e341b3566ed2a.

- inputs: 49ec2de066ee8c0f63e99c77b94a52cf2aa73ccd
- reference: 6c063dd2578109b204c0a1346581b2016c724957
- acquisition: c7fc4112aac98518f06607dfc8d8f81e53c2c5fe
- h1: cd9c4f22857e17870462a60d0d6c9d2005e6f891
- prediction: 747868eb3527261fff74c515221b0ea4235bbcbf
- ground: 5b06be4aa6201eb6ace1da352d125d7495481355
- truth: db504bf8b9902a31aa14fa97d84cab9da82bdee4
- scored: 2065a4b2d5a0aef2db52135b549be299793c3c0b

Each stage commits exactly seven lightweight files, verifies commit blobs,
and self-excludes its manifest. Prediction SHA-256:
1779b177ed25f665537370dd050cc76c54e50d505127e01cbcf27ec2c88268ae.
Protocol SHA-256: a60c3f8385f4bdeb6bdc74ae9bb187de1127e7e8d8204c774c8521097e53ff55.
Implementation manifest SHA-256: e131a0e1d7ddd4d58c4c651996a2d94c7df2bc23913ce25eeff168385921308d.

q and H1 froze before q=0 comparator acquisition. The predictor had zero
exact-ground inputs, full PF construction, direct/gap actions and truth reads.
Grounds froze before direct acquisition; truth froze before immutable scoring.
Top-level FREEZE aliases are publication pointers to the actual earlier
stage commits, not a second freeze. Origin/result and verified-snapshot
commits remain separate fields. Content and publication provenance are
separate commits; the publication commit does not self-reference its hash.

## Resources, gates and tests

New H/CISD generations: 3/3; input-verification H actions:3.
Reference PF/H exponential pairs:102/102 (34 per system).
Candidate cheap PF/H exponential pairs:6/6.
M1 PF/H actions:48/48, six chains with shared prefixes (8 each);
all are comparator-only, conditional M1 acquisitions=0.
Same-H full-H ground solves:2; ground verification matvecs:2.
Full PF / complex Schur / direct coordinates / target gaps:6/6/6/6.
Group/CISD subspace solves are separately recorded, not included in the
claim of zero predictor ground/truth solves.
GPU query/allocation/kernel/CuPy import:0.

Maximum process high-water RSS: 1178636 KiB (~1.124 GiB).
Process-body elapsed seconds: inputs 7.810667,
reference 5.743927, prediction 4.249829,
truth 9.509930. CLI imports/startup are excluded.
Every per-system named stage is under1800s; peak is under4GiB.
Nested action/preprocessing/stage timers are NOT additive, and system
peak fields are process high-water, not independently isolated peaks.
Warm shared-path H1 timing, Git freeze overhead and comparator completion
are separated in prediction/payload.json; comparator work is not H1 work.
Expm_multiply internal H matvecs remain unknown, not counted as one.

Max eigenpair residual 1.0277234983230683e-14;
max unitarity Frobenius residual 5.742227618541128e-12;
min phase gap 0.07417838010782883 rad.
Minimum ground/continuation overlaps:
0.9999999773551039 / 0.9999999920397287.
All new truth quality gates resolve. No budget/action/width was repaired.

Focused pre-freeze / post-prediction / post-result tests:106/106/106 passed;
fail/skip0. The full legacy suite was not run in this scoped extension.
Temporary Matplotlib caches and a scipy graph-casting ComplexWarning occurred.
The unchanged component helper builds a real binary adjacency graph from
abs(matrix.data); this warning is not an imaginary PF coefficient truncation.
No package/environment/GPU settings were changed.

## H8 preflight and stop

H8 status: `H8_extension_contract_blocked`.
Physical recipe is neutral singlet STO-3G, populations4/4, sector4900 and
determinant-CISD361. Dense complex128 matrix storage is384160000 bytes
(~0.358GiB) EACH. More than eleven such matrices alone exceed4GiB.
The current loader materializes all dense groups before compact preprocessing.
H8 group/state/H identities and verified current_m3 K are not frozen;
legacy47932 is only a structural candidate, not PF byte identity or truth reuse.
There is no measured H8 wall/RAM range or certified CPU/GPU feasibility.
See docs/second_study_v2/hchain_h8_extension_preflight_20261004/preflight.json.
No H8 Hamiltonian, state, reference, M1, ground or truth was generated.

Stop for research-direction review. This supports cheap sufficiency on
five eligible tested systems with one explicit applicability failure,
not selective incremental value, certified safety, or universal cheap
sufficiency. H1 q=1 performance remains unobserved. No next phase,
H8 run, margin/width/rank change, new molecule/PF or push is authorized.
