# Codex指示書｜第1研究 FS-R1 Phase A Production Execution

## 0. 今回の実行承認と目的

第1研究について、**FS-R1 Phase A production prediction executionを1回だけ実施してください。**

FS-R1-A0で数値契約・実行順序・lease・recoveryのpreflightが完了し、`GO_FOR_FS_R1_PHASE_A_PRODUCTION` を得ています。

今回の目的は、固定されたnew regenerated source上で、N₂・COそれぞれの4-arm予測を実際に計算し、数値的再現性を確認したうえで、**truth-free predictionをGit commit/hashによって固定すること**です。

**本指示が許可するのはFS-R1 Phase A productionの単一実行のみです。Phase Bは未承認です。**

次の制約を厳守してください。

- Phase A science：今回1回だけ承認
- Phase B science：禁止
- new direct PF truth：0
- branch ladder実行：0
- ground-state oracleへのoperational access：0
- 再実行によるscience rescue：禁止
- protocol・数値閾値・source・PF・rank・timeの事後変更：禁止

Phase Aが成功しても、Phase Bへ自動移行せず、必ず停止してください。

---

## 1. Repository / 起点

Repository:

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

起点branch：

`pf-first-study-fs-r1-a0-numerical-contract-20261008`

固定commit：

`7a7234c9c5412c7209e3559aadfb71b30ad727fc`

Authority directory：

`artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008/`

実行protocol：

`FS-R1-20261007-v3`

作業用には、新しいbranchを作成してください。

推奨：

`pf-first-study-fs-r1-phase-a-production-20261008`

既存branchや旧artifactを上書きしないでください。

## 2. 実行前に確認するauthority

最低限、次を読んでください。

FS-R1-A0：

- `README.md`
- `GO_NO_GO_FOR_PHASE_A_PRODUCTION.json`
- `fs_r1_protocol_v3.json`
- `fs_r1_numerical_contract_v1.json`
- `fit_uncertainty_propagation.json`
- `norm_contract.md`
- `replay_contract.md`
- `ritz_replay_contract.md`
- `phase_a_orchestration.md`
- `run_lease_contract.md`
- `recovery_contract_v2.md`
- `budget_uncertainty_contract.md`
- `execution_code_identity.json`
- `verification.json`

FS-R0 / R0.1：

- frozen source identity
- sanitized operational exports
- four-arm contract
- branch ladder
- truth barrier
- recovery / publication contracts

既存のsource/backend・Ritz計算コードと、これらの契約をauthorityとして使用してください。

## 3. Frozen code/protocol integrity

production開始前に、実際のGit blobとローカルファイルを照合してください。

FS-R1-A0で記録されたidentityは以下です。

**v3 protocol SHA-256**

`b1d37961484b212a6f2fab8b38092e56e640bac85c2369ab4cb29ba4ec383884`

**Numerical contract SHA-256**

`16067176e0d1b211c5c43bd85287741cc93719977a57b675d5e2547b84dae573`

**Execution code bundle SHA-256**

`abb832afdd8de951e005d3104d2f7e1644329d86612607b61820e1f15ec1d9e4`

実際のauthorityファイルから再計算し、完全一致を確認してください。

execution bundleは、`execution_code_identity.json` のparsed JSONをcompact/sorted形式＋末尾newlineでcanonical化する既存規則を使用します。

一致しない場合はproductionを開始せず停止してください。

コード修正によって結果を合わせることは禁止です。

---

## 4. Production entrypoint

既に実装されている以下を使用してください。

`artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008/phase_a_wrapper.py`

Production entrypoint：

`execute_phase_a(authorization, run_id, public_path)`

内部では、固定されたproduction adapterとorchestrationを使用してください。

**今回のユーザー指示を、FS-R1 Phase Aに限る別の明示的science authorizationとして扱ってください。**

authorizationには、既存実装が要求する次の情報を正しく含めてください。

- `explicit_science_authorization = true`
- `phase = FS-R1-Phase-A`
- 一意の`authorization_id`
- 実際のv3 protocol SHA
- 実際のexecution code bundle SHA

authorizationはsource/code/protocolにbindし、private実行記録に残してください。

`authorization_id`は同一実行内で固定し、run IDを変更して再利用しないでください。

既存のproduction guard、lease、truth barrierを回避して独自runnerを作らないでください。

---

## 5. Production source identity

Phase Aでは、FS-R0でfreeze済みのsanitized operational sourceだけを使用してください。

### N₂

Condition：

`N2_active_eq_sto3g`

Hamiltonian SHA：

`f4a08b755a4e903f4e9611fee394d6101a5d27279a1bd8af567b97920da5402e`

Source identity：

`6b93735a56638c40a2bcd35e504f1ee823cfdbe396441fce15fd5e02502b044d`

Operational archive SHA：

`16fcd3966b3ab5d900601318e4911e82bcd49934cc34184f4cbd8e8ec1512dc3`

### CO

Condition：

`CO_active_eq_sto3g`

Hamiltonian SHA：

`27ed246b354c754a506541dac81650aafdfa413b375fadf0b736822c171fb4c5`

Source identity：

`ed9ec93d6945a11bd144d2531ffedaf67da829383334b47206b78c11aee34f17`

Operational archive SHA：

`483ad1f91127a7d4ba45c8b2c56f7cb60392366c2bc5a70321e421ba387ff6a4`

両条件ともrestricted sector dimensionは1568です。

Source/H/CISD/group order/sector/energy originの固定identityを確認してください。

historical H01 sourceへ戻さないでください。

Hamiltonian・CISD・groupsの再生成も禁止します。

---

## 6. Fixed science design

対象はN₂ equilibriumとCO equilibriumの2条件で固定します。

PFは`current_m3`のみです。

時間・fit・state・rankの再最適化は禁止します。

### N₂

Training absolute times：

`[0.06263494343795273, 0.12526988687590546, 0.18790483031385818]`

Evaluation time：

`t0 = 0.5983202971910435`

Fit scaling：

`t_ref = 0.6263494343795273`

Rotations per PF step：

`K = 19176`

### CO

Training absolute times：

`[0.06546804264781796, 0.1309360852956359, 0.19640412794345388]`

Evaluation time：

`t0 = 0.6127481451622522`

Fit scaling：

`t_ref = 0.6546804264781796`

Rotations per PF step：

`K = 37936`

表示値を再生成するのではなく、v3 protocol内の固定binary64値をauthorityとして使ってください。

---

## 7. Four-arm production

各conditionで、以下の4 armを計算してください。

| Arm | State | Prediction |
|---|---|---|
| M00′ | new-source CISD | 3-point \(t^4+t^6\) fit |
| M10′ | Ritz8 | 同一3点のfit |
| M01′ | new-source CISD | \(t_0\) local proxy |
| M11′ | 同一Ritz8 | \(t_0\) local proxy |

M11′ remains primary。

M01′ remains cheaper challenger。

同一condition内でRitz8 stateをM10′とM11′の間で共有してよいですが、initialとcoldの間で科学的intermediateを共有しないでください。

### Proxy definition

\[
g_\psi(t)=
\frac{\operatorname{Im}\langle\psi|
e^{-iHt}U_P(t)|\psi\rangle}{t}
\]

既存native PF/echo backendを使用し、sign convention・complex128・group orderingを維持してください。

### Fit

M00′/M10′：

\[
f(t)=a_4t^4+a_6t^6
\]

- trainingは固定3点のみ
- no intercept
- unweighted OLS
- historical H01 numerical scaling
- `numpy.linalg.lstsq(..., rcond=None)`
- 同じ\(t_0\)で評価

0.4/0.5 relative coordinatesをfitへ追加しないでください。

---

## 8. Ritz8 numerical contract

H4 Phase 0.5で固定した計算規則を変更しないでください。

- Primary \(m=8\)
- Exactly two MGS passes
- Residual Krylov basis
- Prefix rank stop
- No replacement direction
- No rank rescue
- Lowest projected Ritz state
- Deterministic phase/tie rule
- No exact-ground input

必ず保存する診断：

- requested rank
- retained rank
- rank-stop index/reason
- projected dimension
- orthogonality residual
- projected Hermiticity residual
- Ritz energy
- Ritz residual norm
- Ritz normalization
- phase pivot/tie branch
- explicit H matvec count
- small Ritz solve count

rankが8未満で停止しても、契約どおりのprefixを使用し、恣意的な追加basisを作らないでください。

---

## 9. Numerical gates — v3を厳守

### State norm

\[
|\|\psi\|_2-1|\le10^{-12}
\]

### PF output norm

\[
|\|U_P(t)\psi\|_2-1|\le10^{-10}
\]

### Exact-H reference norm

\[
|\|e^{-iHt}\psi\|_2-1|\le10^{-10}
\]

### Raw proxy cold replay

\[
|g_{\rm cold}-g_{\rm initial}|
\le10^{-11}\ \mathrm{Ha}
\]

Relative toleranceは使用しないでください。

echo amplitudeの有限性・Cauchy bound・Ritzの既存数値gateもすべて適用してください。

**今回のproduction結果を見て数値許容差を変更することは禁止です。**

---

## 10. Fit uncertainty propagation

FS-R1-A0で計算済みの固定linear mapを使用してください。

Raw proxy replay tolerance：

\[
\tau_g=10^{-11}\ \mathrm{Ha}
\]

Fit coefficient uncertainty：

\[
\tau_{a_j}
=
\tau_g\sum_i|P_{ji}|
\]

Prediction uncertainty：

\[
\tau_{\rm fit}(t_0)
=
\tau_g\sum_i|(q(t_0)P)_i|
\]

固定値：

| Condition | \(\tau_{\rm fit}(t_0)\) |
|---|---:|
| N₂ | \(1.1122914179929199\times10^{-7}\) Ha |
| CO | \(9.800205391365774\times10^{-8}\) Ha |

M00′/M10′のpredictionと係数は、この解析的誤差伝播によってreplay判定してください。

M01′/M11′はfitしないため、\(\tau_p=10^{-11}\) Haです。

これらは**再現性の数値幅**であり、true PF errorのcertificateではありません。

---

## 11. Budget calculation

Constants：

\[
\epsilon_E=0.00015936001019904
\]

\[
\beta=1.2,\quad\gamma=1.01
\]

各armのsigned estimateを\(p_j\)として、

\[
B_j'=
\frac{\gamma\beta K}{t_0(\epsilon_E-|p_j|)}
\]

を使用してください。

M00′から作る\(B_0'\)が新baselineです。

historical B0を使わないでください。

### Numerical budget interval

\[
c_{\min}=\max(0,|p_j|-\tau_j)
\]

\[
c_{\max}=|p_j|+\tau_j
\]

**\(c_{\max}\ge\epsilon_E\)なら：**

`NUMERICALLY_INDETERMINATE_BUDGET`

とし、nominal/B_min/B_maxをnullにしてください。

有限budgetを強制生成しないでください。

それ以外では、v3の解析的budget intervalを計算してください。

予測比率は`prediction_only_not_truth_scored`として保存します。

両passでindeterminate statusが安定している場合も、finite-budget coverageはfalseのままです。数値的にundefinedなbudgetを成功扱いしないでください。

---

## 12. Ritz cold replay acceptance

initial/coldで以下の完全一致を要求してください。

- retained rank
- rank-stop index
- rank-stop reason
- projected dimension
- phase pivot index
- tie-resolution branch
- zero/nonzero rank status

各passでRitzの既存continuous numerical gatesも満たすこと。

Ritz energy/residualの差は保存しますが、独自の新しいabsolute toleranceを追加しないでください。

Downstream proxy replayも必須です。

---

## 13. Production execution order

既存v3 orchestrationに従い、以下の順序で実行してください。

**Step 1 — N₂ initial**

N₂で全4-arm predictionを取得。

**Step 2 — CO initial**

COで全4-arm predictionを取得。

**Step 3 — Initial aggregate recovery**

N₂/CO initialのscalar recoveryをdurableに保存。

**Step 4 — N₂ cold replay**

新しいsource load・Ritz・PF・echo・fit・budgetを独立に実行。

**Step 5 — CO cold replay**

同様に独立に実行。

N₂の科学的予測が良い・悪いという理由でCOをskipしないでください。

数値的/技術的failureの場合だけ、v3契約に従って停止してください。

---

## 14. Exclusive run lease

本番開始前に、固定済みのauthorization-keyed exclusive leaseを使用してください。

Leaseに保存するもの：

- authorization ID/hash
- run ID
- protocol hash
- execution code hash
- source identities
- `RUN_STARTED`
- host/process/time
- execution state

同一authorizationで2回目のscienceを実行してはいけません。

failed/partial/completed/public-failedのいずれも再実行禁止です。

---

## 15. Private recovery

各scientific return直後、public validationより前にscalar recovery snapshotを保存してください。

Recoveryには少なくとも以下を含めます。

- raw proxy values
- fit coefficients
- predictions
- prediction uncertainty
- nominal/interval budgets
- Ritz diagnostics
- rank/stop information
- actual action counts
- wall/RSS
- source/protocol/code identities

Create-only、fsync、SHA-256、lease bindingを維持してください。

Public schema/serializationが失敗した場合は、保存済みscalar bytesからだけ復旧し、PF/echo/Ritzを再実行しないでください。

---

## 16. Planned action budget

FS-R0.1/v3の予定値は以下です。

| Action | Planned |
|---|---:|
| PF forward vector actions | 32 |
| Exact-H echo actions | 32 |
| Explicit Ritz H matvec | nominal 36 |
| Small Ritz solve | nominal 4 |
| Scalar fits | 8 |

これらは予定量です。

必ずactual countsを記録し、rank stop等による差を明示してください。

Group applications / materializationsも計上してください。

`expm_multiply`内部のwork数が取得できない場合は`unknown/null`とし、0にしないでください。

Classical calibration costとpredicted QPE rotationsを分離してください。

---

## 17. Truth barrier

今回、以下はすべて禁止です。

- new direct PF eigenvalue truth
- Schur truth solve
- branch continuation
- 12-point truth ladder
- exact ground operational reads
- historical truth reuse
- direct optimal time search
- Phase B scoring

Phase A終了時には、以下がすべて0であることを監査してください。

```text
direct_truth_reads = 0
branch_solves = 0
truth_schur = 0
exact_ground_operational_reads = 0
historical_truth_reads = 0
new_direct_truth_coordinates = 0
```

---

## 18. Production前の最終チェック

Science lease作成前に以下を検証してください。

- exact base commit/protocol
- execution code bundle hash
- numerical contract hash
- frozen source SHA
- source sanitization
- operational oracle absence
- authorization binding
- private recovery directory
- available resource/backend
- existing317 tests PASS

この段階で失敗した場合は、science lease作成前のpreflight failureとして停止してください。

合格して初めてPhase Aを開始してください。

既存のnumerical codeやscience contractを変更しないでください。

---

## 19. Failure policy

以下を区別して報告してください。

### `PHASE_A_NUMERICAL_FAILURE`

Norm/Ritz/echo/replay等の数値gateに不合格。

### `PHASE_A_TECHNICAL_FAILURE`

Source/interface/memory/backend/実行環境などの技術的失敗。

### `PHASE_A_RECOVERY_ONLY`

Science return後にpublication/schemaが失敗し、private scalar recoveryからの復旧が必要。

### `PHASE_A_BUDGET_INDETERMINATE`

数値計算は成立しているが、必要なbudgetがnumerically indeterminateで、資源比較を確定できない状態。

### `PHASE_A_FROZEN_READY_FOR_GPT_REVIEW`

両条件の全arm、cold replay、数値gate、必要なbudget処理、prediction freeze、GitHub公開検証が完了。

必要なら既存machine-readable status名へ対応づけてください。既存authorityの意味を変更してはいけません。

失敗時にrank・fit・time・source・toleranceを変更して救済しないでください。

---

## 20. Prediction freeze

両条件のPhase Aが正常完了した場合のみ、prediction artifactをfreezeしてください。

Freezeするもの：

- all four arm signed predictions
- all raw proxies
- fits/coefficients
- \(B_0',B_{01}',B_{10}',B_{11}'\)
- budget intervals
- prediction-only ratios
- Ritz diagnostics
- initial/cold differences
- numeric-gate outcomes
- actual action/cost ledger
- source identity
- v3 protocol hash
- execution code hash

Canonical prediction manifestとSHA-256を作成してください。

**後から科学的値を編集しないでください。**

Source/code/protocol/resultを同じfreezeで追跡できるようにしてください。

---

## 21. 新しい成果物

新しいartifact directoryを作成してください。

例：

`artifacts/pf_first_study_fs_r1_phase_a_production_20261008/`

最低限必要な成果物：

1. `README.md`
2. `phase_a_protocol_snapshot.json`
3. `source_identity.json`
4. `authorization_receipt.json`
5. `production_results.json`
6. `proxy_values.csv`
7. `ritz_diagnostics.json`
8. `fit_results.json`
9. `predicted_budgets.json`
10. `prediction_intervals.json`
11. `cold_replay.json`
12. `numerical_gate_audit.json`
13. `action_counts.json`
14. `cost_ledger.json`
15. `truth_access_audit.json`
16. `private_recovery_receipt.json`
17. `prediction_manifest.json`
18. `prediction.sha256`
19. `tests.log`
20. `verification.json`
21. `source_manifest.json`
22. `publication_manifest.json`
23. `GO_NO_GO_FOR_PHASE_B.json`

Failureの場合は、取得できた情報だけを正直に保存し、存在しないprediction/recoveryを作らないでください。

Private source、state vector、matrix、unitary、recovery binaryはGitへ公開しないでください。

---

## 22. Git commit / push

Phase A終了後、結果または停止監査を新規commitしてください。

通常pushを行い、独立に以下を確認してください。

- remote tip SHA一致
- committed source/protocol/code identity
- new artifact blob SHA
- prediction manifest SHA
- prediction SHA（freeze成立時のみ）
- 旧science artifactsが変更されていないこと

Remote検証結果をfinal handoffに記録してください。

---

## 23. Phase B判定

Phase A成功後も、CodexがPhase Bを承認してはいけません。

`GO_NO_GO_FOR_PHASE_B.json` には、

- Phase A numerical completeness
- budget validity/indeterminate coverage
- prediction freeze status
- actual prediction SHA
- remote verification
- truth access=0
- **Phase B authorization=false**

を保存してください。

GPT/userによる後続レビューを要求してください。

---

## 24. 最終報告

以下の形式で報告してください。

### Status

- Phase A final status
- Production started/completed
- Numerical gates passed/failed
- Cold replay passed/failed
- Prediction frozen/unfrozen

### Scientific predictions

N₂とCOのそれぞれについて、

| Arm | Signed prediction (Ha) | Prediction uncertainty (Ha) | Nominal budget | Budget interval |
|---|---:|---:|---:|---|
| M00′ | | | | |
| M10′ | | | | |
| M01′ | | | | |
| M11′ | | | | |

取得されていない値は`NOT_RUN`、indeterminateはそのstatusを記載してください。

### Ritz / replay

- N₂ retained rank
- CO retained rank
- rank-stop diagnostics
- 最大raw proxy cold difference
- 最大coefficient/prediction replay difference
- norm/echo/Ritz gate
- budget numerical status

### Resources

- actual PF actions
- actual echo actions
- actual H matvec
- actual Ritz solves
- actual fits
- wall seconds
- peak RSS

### Provenance

- truth access count
- new direct truth count
- prediction SHA
- branch
- commit
- remote verification
- Phase B GO/NO-GO for GPT review

---

## 25. 最終停止条件

**Phase A prediction freeze・GitHub公開・独立検証まで完了したら必ず停止してください。**

Phase Bの12-point branch truthは1点も計算しないでください。

進行順序は、

\[
\boxed{
\text{Codex: FS-R1 Phase A production}
\rightarrow
\text{GPT: prediction/numerical review}
\rightarrow
\text{別承認: FS-R1 Phase B}
}
\]

です。

**今回の最重要要件は、固定済みv3数値契約のままproductionを1回実行し、その結果をtruth-freeでimmutableにfreezeすることです。**

旧formal first-study、Phase0、H4、FS-C0/C0.5/C0.6、FS-R0/R0.1/A0の既存artifactは変更しないでください。