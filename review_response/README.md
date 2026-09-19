# Reviewer-response calculations

The first correction addresses the central reviewer objection: the submitted
manuscript compared against an obsolete Morales product formula.

## Morales 8th-order formulae

- `8th(Morales)` is retained as the legacy arXiv-v2, m=8 formula so that old
  artifacts remain identifiable.
- `8th(Morales-Y8m10b)` is the non-processed, 21-stage formula selected for
  eigenvalue error in Table 1 of the published QIC 2025 paper
  (DOI `10.2478/qic-2025-0001`).
- The published YP8m8 kernel and processor coefficients are recorded in
  `src/trotterlib/product_formula.py`. The circuit implementation keeps the
  17-block repeated kernel separate from the 20-block processor on each side,
  and constructs the full formula as `P K^r P^-1`.
- `10th(Morales-QIC-m17)` is the published Table 3 formula selected for
  eigenvalue error. `10th(Morales)` is retained as the legacy arXiv-v2 m=16
  formula so previous artifacts are not silently reinterpreted.

## H2 smoke validation

Run:

```bash
PYTHONPATH=src .venv-req/bin/python review_response/validate_morales_y8m10b_h2.py
```

For grouped H2/STO-3G, direct diagonalization gives a fitted order of 7.990
for Y8m10b. Its fitted eigenvalue-error coefficient is about 67 times smaller
than the legacy formula. Including the increase from 248 to 304 Pauli
rotations per step, the fixed-target product-formula cost is 0.725 times the
legacy cost, a reduction of about 27.5%. The compact result is stored in
`morales_y8m10b_h2_validation.json`.

For YP8m8, the full processed circuit gives matching direct-diagonalization
and perturbative error coefficients on H2. Applying the kernel alone is valid
for its eigenvalues, but not for the state-overlap perturbative estimator.
Consequently, numerical perturbation checks use the full processed circuit,
while the asymptotic repeated-step cost reports the kernel plus a separate
additive processor overhead.

The affine processed-cost model is implemented in
`src/trotterlib/processed_cost.py`. The number of processor pairs is an
explicit argument because it depends on how the controlled QPE powers are
organized; the code does not assume that a processor pair is paid for every
kernel repetition.

For resumable perturbative H-chain calculations, use for example:

```bash
PYTHONPATH=src .venv-req/bin/python \
  review_response/run_morales_y8m10b_hchain.py \
  --h-chains 2 4 \
  --labels '8th(Morales)' '8th(Morales-Y8m10b)'
```

The runner writes one raw-data JSON file per H-chain under
`artifacts/reviewer_response/morales_qic2025/` and skips completed systems
unless `--force` is specified.

The same runner can record a candidate comparison under a separate run name.
For example, the new fourth-order candidates are evaluated with:

```bash
PYTHONPATH=src .venv-req/bin/python \
  review_response/run_morales_y8m10b_hchain.py \
  --h-chains 2 4 \
  --labels '4th(new_2)' '4th(m5_best)' '4th(m6)' \
  --t-start 0.12 --t-stop 0.8 --num-times 18 \
  --run-name new_fourth_candidates \
  --baseline-label '4th(new_2)' \
  --output-dir artifacts/reviewer_response/new_fourth
```

The original printed m=2 coefficients leave a cubic-moment residual of about
`7.35e-9`. Both searched candidates satisfy that condition at floating-point
precision. On the current H2 and H4 checks, the m=5 candidate reduces the
fixed-target fourth-order PF cost proxy by about 25.8% and 21.1%, respectively,
and the H5 reduction is about 20.7%. The m=6 candidate is worse on H4, so m=5
is the current candidate for the expanded validation.

The published tenth-order m=17 formula has also been checked against the
legacy m=16 formula. It reduces the fixed-target proxy by about 31.7% on H2
and 17.9% on H4. For the eighth-order comparison, Y8m10b reduces the proxy by
about 27.5%, 39.4%, and 44.4% on H2, H4, and H5, respectively.

The processed YP8m8 H4 check illustrates why its costs must remain affine.
Ignoring the one-time processor pair, its repeated-kernel proxy is about 2.8%
below Y8m10b, but the processor pair costs 14,400 additional rotations. Its
free fit over the current time window is also close to tenth order, so this
preliminary comparison is not yet used for a manuscript-level conclusion.

## Perturbative-estimator validation

Run:

```bash
PYTHONPATH=src .venv-req/bin/python \
  review_response/validate_perturbation_orders_h2.py
```

This compares direct diagonalization with the phase-rotated overlap estimator
on H2 for second, standard and new fourth, published processed and
non-processed eighth, and published tenth order. The raw data and figure are
written under `artifacts/reviewer_response/perturbation_validation/`; the same
figure is generated in the manuscript appendix. Together with the existing
H2--H6 second-order check, this tests both the system-size and formula-order
directions requested by Reviewer 1.

The H4 common-window check can be reproduced with:

```bash
PYTHONPATH=src venv/bin/python \
  review_response/validate_hchain_perturbative_estimator.py \
  --sweep-json \
    artifacts/server_pf_window_validation/gpu_4th/H4_pf4_window.json \
    artifacts/server_pf_window_validation/gpu_8th/H4_pf8_window.json \
  --noise-analysis-json \
    artifacts/server_pf_window_validation/pf_window_analysis.json \
  --output \
    artifacts/server_cost_validity/H4_current_window_direct_validation.json
```

It passes the preregistered 5% pointwise/alpha and 2% cost-ratio thresholds.
The maximum pointwise perturbative/direct difference is about 3.9%, the maximum
fixed-order-alpha difference is about 1.4%, and the maximum same-order PF
cost-ratio difference is about 0.18%.

## Wide-time cost validity

The wide-time GPU and sector-diagonalization results are under
`artifacts/server_cost_validity/`. They test whether the short-time model
`e_PF(t) = alpha * t**p` and the overlap estimator remain valid near the
analytic QPE cost optimum.

At the current target error of `1.5936001019904e-4` Hartree, none of the six
H2/H4/H5 x m5/Y8 analytic optimal times lies in the primary short-time interval
where the measured error agrees with the fitted power law to 10%. Evaluating
the direct eigenvalue error at those analytic schedules nevertheless changes
the predicted cost by no more than about 11%. The direct Y8m10b/m5 cost ratios
at the respective analytic schedules are approximately 0.890, 0.938, and 0.981
for H2, H4, and H5.

This does not extend to unconstrained minimization over the full direct-error
curves. The signed direct errors cross zero 1/3/7 times for m5 and 1/6/8 times
for Y8m10b on H2/H4/H5. These system-specific cancellations produce global
direct-minimum cost ratios of approximately 1.324, 0.843, and 1.205, reversing
the ranking on H2 and H5. They must not be confused with a smooth continuation
of the asymptotic power law.

Regenerate the wide-time analysis with:

```bash
PYTHONPATH=src venv/bin/python \
  review_response/analyze_wide_time_cost.py \
  --wide-json \
    artifacts/server_cost_validity/wide_gpu/H2_m5_wide_refined.json \
    artifacts/server_cost_validity/wide_gpu/H2_y8m10b_wide_refined.json \
    artifacts/server_cost_validity/wide_gpu/H4_m5_wide_refined.json \
    artifacts/server_cost_validity/wide_gpu/H4_y8m10b_wide_refined.json \
    artifacts/server_cost_validity/wide_gpu/H5_m5_wide_refined.json \
    artifacts/server_cost_validity/wide_gpu/H5_y8m10b_wide_refined.json \
  --fit-analysis-json \
    artifacts/server_pf_window_validation/pf_window_analysis.json \
  --h2-reference-json \
    artifacts/server_pf_window_validation/H2_direct_diagonalization.json \
  --direct-json \
    artifacts/server_cost_validity/H2_wide_direct_validation.json \
    artifacts/server_cost_validity/H4_wide_direct_validation.json \
    artifacts/server_cost_validity/H5_wide_direct_validation.json \
  --output artifacts/server_cost_validity/wide_time_cost_analysis.json
```

The analysis records both perturbative and direct power-law validity intervals,
the direct signed-error zero crossings, values at the analytic schedules, and
separate ranking-agreement flags. The defensible interpretation is that the
estimator validates short-time asymptotic coefficients; wide-time cost claims
require either direct small-system checks or an explicit sensitivity analysis.

## Costs outside the product formula

`src/trotterlib/end_to_end_cost.py` implements the explicit extension

```text
C_expected = C_once
           + (C_prep + c_rotation F + C_QPE_other)
             / (ground-state overlap * conditional QPE success).
```

The denominator follows from the mean number of independent attempts in a
geometric distribution. The revised appendix derives this equation and
explains that common non-PF components preserve the ranking by `F`; uncertain
formula-dependent components must instead be supplied as sensitivity inputs.
