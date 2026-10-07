第1研究について、**FS-R1 Phase A：production prediction execution** を実施してください。

今回は、new regenerated source上で4-arm predictionを実際に計算し、結果をfreezeする段階です。

\[
\boxed{\text{Phase B direct truthは絶対に実行しない}}
\]

Phase A完了後、commit/pushして停止し、GPT/userレビューへ戻してください。

---

# 0. 起点

Repository:

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

FS-R0.1:

- Branch  
  `pf-first-study-fs-r01-branch-extension-20261007`

- Commit  
  `dd41c5eaad4a88339f7bbb69267bfdace9fb86e5`

- Artifact  
  `artifacts/pf_first_study_fs_r01_branch_extension_20261007/`

Current preflight status:

`GO_FOR_FS_R1_PHASE_A`

Protocol:

`FS-R1-20261007-v2`

---

# 1. 今回のscope

今回実行するのはPhase Aだけです。

実行対象：

- N2 equilibrium
- CO equilibrium
- new regenerated sanitized operational source
- M00′
- M10′
- M01′
- M11′
- initial production pass
- one complete cold replay
- scalar fits
- predicted budgets
- numerical diagnostics
- cost accounting
- prediction freeze
- commit / push / independent remote verification

実行しない：

- direct PF truth
- branch ladder
- Schur truth solve
- branch matching
- exact-ground truth selector
- safety scoring
- primary_gain/local_gain/state_increment/safety_repair final判定
- FS-R1 Phase B

---

# 2. Authority

最低限以下を読み、変更しないでください。

## FS-R0.1

- `README.md`
- `GO_NO_GO_FOR_FS_R1_PHASE_A.json`
- `fs_r1_protocol_v2.json`
- `branch_ladder.json`
- `branch_contract.md`
- `phase_barrier_v2.md`
- `truth_executor_contract.md`
- `predicted_action_budget_v2.json`
- `verification.json`

## FS-R0

- new source identities
- sanitized exports
- 4-arm contract
- scoring contract
- cost contract
- recovery contract

## Ritz numerical rules

H4 Phase 0.5の固定protocolをauthorityとして使用。

結果を見てrank / basis / fit / timesを変えないこと。

---

# 3. Source identity

Phase Aはsanitized operational sourceのみ使用。

## N2

Condition:

`N2_active_eq_sto3g`

H SHA:

`f4a08b755a4e903f4e9611fee394d6101a5d27279a1bd8af567b97920da5402e`

source identity:

`6b93735a56638c40a2bcd35e504f1ee823cfdbe396441fce15fd5e02502b044d`

operational archive SHA:

`16fcd3966b3ab5d900601318e4911e82bcd49934cc34184f4cbd8e8ec1512dc3`

---

## CO

Condition:

`CO_active_eq_sto3g`

H SHA:

`27ed246b354c754a506541dac81650aafdfa413b375fadf0b736822c171fb4c5`

source identity:

`ed9ec93d6945a11bd144d2531ffedaf67da829383334b47206b78c11aee34f17`

operational archive SHA:

`483ad1f91127a7d4ba45c8b2c56f7cb60392366c2bc5a70321e421ba387ff6a4`

---

# 4. Truth barrier

Phase A execution environmentから以下へアクセスしないでください。

- exact ground vector
- direct PF eigenvalues
- direct shift
- branch ladder outputs
- historical direct truth
- historical branch IDs
- Phase B files

Phase A operational sourceにoracle fieldが無いことを実行前に再確認してください。

truth access count:

\[
\boxed{0}
\]

を維持。

---

# 5. Fixed coordinates — N2

Training coordinates for M00′ and M10′:

```text
0.06263494343795273
0.12526988687590546
0.18790483031385818
```

Fixed t0:

```text
0.5983202971910435
```

K:

```text
19176
```

fit scale t_ref:

```text
0.6263494343795273
```

---

# 6. Fixed coordinates — CO

Training coordinates:

```text
0.06546804264781796
0.1309360852956359
0.19640412794345388
```

Fixed t0:

```text
0.6127481451622522
```

K:

```text
37936
```

fit scale t_ref:

```text
0.6546804264781796
```

---

# 7. M00′

For each condition:

State:

new-source CISD

Compute local imag-echo proxy at the three fixed training coordinates.

Fit:

\[
f_0'(t)=a_4t^4+a_6t^6
\]

fixed rule:

- powers [4,6]
- no intercept
- unweighted OLS
- historical H01 numerical fit implementation
- times/t_ref scaling
- values/max(abs(values)) scaling
- `numpy.linalg.lstsq(..., rcond=None)`
- coefficients unscaled back

Evaluate:

\[
M00'(t_0)=f_0'(t_0)
\]

Do not use 0.5t_ref.

Do not use 0.4.

Do not optimize t0.

---

# 8. M10′ — Ritz8 state intervention

Construct residual Krylov Ritz state from the same new-source CISD.

Primary rank:

\[
m=8
\]

Fixed rules:

- MGS passes = 2
- prefix rank stop
- no replacement direction
- no rank rescue
- no result-dependent rank selection
- no exact-ground input
- deterministic phase convention
- projected dimension ≤9
- lowest projected Ritz pair

If actual retained rank \(k<8\), use the first retained prefix and record it.

Do not extend the basis to force rank8.

---

# 9. Ritz diagnostics

At minimum save:

- requested m
- retained rank
- rank-stop reason
- basis orthogonality residual
- Ritz normalization
- projected Hamiltonian Hermiticity residual
- Ritz energy
- Ritz residual norm
- phase convention diagnostic
- explicit H matvec count
- small Ritz solve count

Do not evaluate exact-ground overlap.

---

# 10. M10′ fit

Using the same three absolute training coordinates as M00′, compute Ritz-state proxy.

Fit:

\[
f_8'(t)=a_4t^4+a_6t^6
\]

with exactly the same fit implementation.

Evaluate at the same t0.

No new \(t_{\rm ref}\).

No Ritz-specific coordinate optimization.

---

# 11. M01′

State:

new-source CISD

At t0 only, compute:

\[
g_{\rm CISD}'(t_0)
\]

No fit.

---

# 12. M11′

State:

same Ritz state as M10′

At t0 only:

\[
g_{\rm Ritz}'(t_0)
\]

No fit.

M11′ remains preregistered primary arm.

M01′ remains cheaper challenger.

---

# 13. Echo definition

Use:

\[
g_\psi(t)
=
\frac{
\operatorname{Im}
\langle\psi|
e^{-iHt}U_P(t)
|\psi\rangle
}{t}
\]

Maintain:

- same energy origin
- same current_m3
- same group order
- same sign convention
- complex128
- same vector normalization convention

---

# 14. PF configuration

Use the fixed current_m3 sequence only.

Do not compare PFs.

Do not optimize PF coefficients.

Do not add yoshida4 or other formulas.

---

# 15. PF numerical diagnostics

For every production PF/echo coordinate, record at least:

- input state norm
- PF output norm
- PF norm error
- exact-H evolved/reference norm
- echo amplitude real/imag
- proxy
- wall seconds
- peak RSS where available
- group applications
- group materializations

If nonfinite value appears, stop affected run.

---

# 16. New baseline B0′

After M00′ prediction is obtained:

\[
c_{00}=|M00'(t_0)|
\]

compute:

\[
B_0'
=
\frac{
\gamma\beta K
}{
t_0(\epsilon_E-c_{00})
}
\]

Constants:

\[
\epsilon_E=0.00015936001019904
\]

\[
\beta=1.2
\]

\[
\gamma=1.01
\]

If:

\[
c_{00}\ge\epsilon_E
\]

mark M00′ infeasible and stop scientific budget interpretation for that condition.

Do not clip denominator.

---

# 17. Other arm budgets

For:

- M01′
- M10′
- M11′

use the same formula with each arm magnitude.

Save:

- signed estimate
- absolute estimate
- denominator
- budget
- valid/infeasible status

---

# 18. Phase A must not score safety

Do NOT calculate final:

- safe/unsafe
- energy slack against direct truth
- primary_gain
- local_gain
- state_increment
- safety_repair

because direct truth is still unopened.

If schema requires fields, set:

`PENDING_PHASE_B`

or null with explicit reason.

---

# 19. Pre-truth descriptive budget ratios

It is acceptable to store purely prediction-side ratios such as:

\[
B_{01}'/B_0'
\]

\[
B_{10}'/B_0'
\]

\[
B_{11}'/B_0'
\]

provided they are clearly labelled:

`prediction_only_not_truth_scored`

Do not call them resource success.

---

# 20. Initial pass

Perform the complete production Phase A once.

Both conditions must be included from the beginning.

Do not execute N2 first and decide based on its result whether CO should run.

---

# 21. Cold replay

After successful initial Phase A, perform one complete independent cold replay.

Cold replay must independently reconstruct:

- source load
- CISD state access
- Ritz basis
- Ritz state
- PF
- echo
- proxies
- fits
- predicted budgets

No scientific intermediate cache sharing.

Immutable source bytes may be re-read.

---

# 22. Cold replay comparison

Save differences for:

- every raw proxy value
- every fit coefficient
- M00′ prediction
- M10′ prediction
- M01′
- M11′
- budgets
- Ritz diagnostics where deterministic
- retained rank

Do not silently average initial/cold results.

Initial production result remains primary if replay passes.

---

# 23. Cold replay gate

Use preregistered numerical contract only.

Do not invent tolerance after seeing differences.

If the existing protocol lacks a required physical-production tolerance, stop as:

`PHASE_A_NUMERICAL_CONTRACT_UNCLOSED`

instead of selecting a convenient tolerance.

---

# 24. Expected logical actions

Nominal planned values from FS-R0.1:

- PF forward vector actions: 32
- exact-H echo actions: 32
- explicit Ritz H matvec: nominal 36
- small Ritz solve: nominal 4
- scalar fits: 8

These are planned values.

Record actual counts.

If prefix rank stop changes actual H actions/solve count, report actual values rather than forcing nominal counts.

---

# 25. Cost accounting

For each pass/system/arm record separately:

## Classical

- source load
- explicit H matvec
- PF vector action
- exact-H echo action
- group application
- gate materialization
- small Ritz solve
- scalar fit
- wall seconds
- peak RSS
- thread settings
- software versions

## QPE prediction

- predicted PF rotations/budget

Do not sum CPU seconds and QPE rotations into one scalar.

---

# 26. expm_multiply internal work

If internal matvec/matmat/norm-estimation counts are unavailable:

```text
null
```

with status:

`unknown`

Do not report zero.

---

# 27. Recovery snapshot

Immediately after production scientific return and before public schema validation:

create private scalar recovery snapshot.

It must contain enough to recover without rerunning science:

- all proxies
- Ritz diagnostics
- fits
- estimates
- budgets
- actual action counts
- cost scalars
- source/protocol/code hashes

fsync and hash it.

---

# 28. Serialization failure policy

If public artifact serialization/schema validation fails after successful science return:

- preserve private recovery snapshot
- do NOT automatically rerun production science
- repair serialization only under the frozen result
- if scientific computation itself must change, stop and return to GPT/user

---

# 29. RUN_STARTED lease

Use the preregistered exclusive run lease.

A completed or partially executed production run must not accidentally be launched a second time from the same authorization.

---

# 30. Technical failure policy

If any of the following occurs:

- source identity mismatch
- Ritz numerical failure
- PF/echo nonfinite
- norm failure
- memory/resource failure
- cold replay failure
- numerical contract failure

stop as technical Phase A failure.

Do NOT rescue by:

- lowering m
- changing times
- changing fit
- changing backend
- changing source
- dropping CO
- dropping an arm

---

# 31. Phase A success condition

Phase A is numerically complete only if:

- both source identities pass
- N2 all four arms complete
- CO all four arms complete
- Ritz gates pass
- PF/echo gates pass
- all fits complete where required
- budgets valid/infeasible statuses deterministically resolved
- cold replay passes
- recovery snapshot valid
- actual costs/actions recorded
- truth access remains zero

---

# 32. Prediction freeze artifact

On Phase A success, create a dedicated prediction artifact.

Example:

`artifacts/pf_first_study_fs_r1_phase_a_20261007_<id>/`

It should contain at minimum:

1. `README.md`
2. `phase_a_protocol_snapshot.json`
3. `source_identity.json`
4. `production_results.json`
5. `proxy_values.csv`
6. `ritz_diagnostics.json`
7. `fit_results.json`
8. `predicted_budgets.json`
9. `cold_replay.json`
10. `cost_ledger.json`
11. `action_counts.json`
12. `truth_access_audit.json`
13. `private_recovery_receipt.json`
14. `prediction_manifest.json`
15. `prediction.sha256`
16. `tests.log`
17. `verification.json`
18. `GO_NO_GO_FOR_PHASE_B.json`

Private recovery data/vector/source binariesはGitへ公開しない。

---

# 33. Prediction hash

Create one canonical prediction package hash.

The prediction hash must bind at least:

- M00′/M10′/M01′/M11′ estimates
- fits
- budgets
- source identities
- protocol ID/hash
- code identities
- coordinates
- Ritz retained ranks
- numerical status

Phase B must later require this exact hash.

---

# 34. Git freeze

Phase A resultsを通常commitしてください。

Commit後：

- normal push
- remote tip exact match
- independent remote fetch
- committed blobs hash verification
- prediction manifest verification

を実施してください。

---

# 35. Phase B authorization barrier

Phase A artifactでは、Phase Bをまだauthorizeしない。

Final statusは例えば：

## `PHASE_A_FROZEN_READY_FOR_GPT_REVIEW`

全production prediction + cold replay + commit freeze成功。

## `PHASE_A_TECHNICAL_FAILURE`

scientific interpretationなし。

## `PHASE_A_NUMERICAL_FAILURE`

numerical gate fail。

## `PHASE_A_RECOVERY_ONLY`

science return済みだがpublic serialization等でrecovery artifactから復旧待ち。

適切なstatusを使ってください。

---

# 36. Truth access audit

Phase A終了時に以下がすべて0であることを保存。

```text
direct_truth_reads = 0
branch_solves = 0
truth_schur = 0
exact_ground_operational_reads = 0
historical_truth_reads = 0
```

truth-only original sourceを開かないこと。

---

# 37. Tests before execution

production実行前に既存260 testsを再実行してください。

さらにPhase A-specific testsがある場合は含める。

tests failure時はscience開始禁止。

---

# 38. Environment

Thread/settings/softwareを固定・記録。

少なくとも：

- Python
- NumPy
- SciPy
- PySCF if loaded
- BLAS
- OMP
- MKL
- hostname/device metadata where appropriate

新しいdependency versionへ自動upgradeしない。

---

# 39. Result-dependent changes forbidden

Phase A結果を見た後で以下を変更しない。

- m
- training times
- t0
- current_m3
- fit
- gamma
- beta
- epsilon
- eta
- source
- state
- group order
- success rules

---

# 40. Phase A result interpretation

Phase A completion時点では、

> which arm predicts a smaller budget

は記述可能。

しかし、

> which arm is actually safe / resource-improving

はまだ結論しない。

direct truthが未取得だからです。

---

# 41. No Phase B

Phase Aが完全成功しても、

\[
\boxed{\text{Phase Bは実行禁止}}
\]

です。

branch ladder12点を1点も計算しない。

`GO_NO_GO_FOR_PHASE_B.json`

を作ってGPT/userへ戻してください。

---

# 42. 最終報告

完了時は簡潔に以下を報告してください。

1. Phase A final status
2. N2 retained Ritz rank
3. CO retained Ritz rank
4. M00′ prediction
5. M10′ prediction
6. M01′ local proxy
7. M11′ local proxy
8. B0′ / B01′ / B10′ / B11′
9. prediction-only budget ratios
10. cold replay maximum differences
11. numerical gates
12. actual action counts
13. wall/RSS
14. truth access count = 0
15. direct truth count = 0
16. prediction SHA
17. branch / commit
18. push / independent remote verification
19. GO/NO-GO for GPT Phase B review

---

# 43. 停止

Phase A publication/freeze完了後は必ず停止してください。

次の順序は：

\[
\boxed{
\text{FS-R1 Phase A}
\rightarrow
\text{GPT review}
\rightarrow
\text{separate Phase B authorization}
\rightarrow
\text{12-point branch truth}
}
\]

です。

FS-R0/R0.1、historical first-study、Phase0、H4、FS-C0/C0.5/C0.6の既存artifactは変更しないでください。