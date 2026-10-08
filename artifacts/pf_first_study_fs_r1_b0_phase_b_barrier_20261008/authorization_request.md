# Codex指示書｜第1研究 FS-R1-B0 Phase B Barrier Closure / Preflight

## 0. 今回の目的と実行範囲

第1研究について、**FS-R1-B0：Phase B execution barrier closure / preflight** を実施してください。

FS-R1 Phase A productionは正常終了し、N₂・COの4-arm prediction、数値gate、cold replay、prediction freeze、GitHub公開・独立検証が完了しています。

今回の目的は、**Phase Aの固定済みv3 predictionを、Phase Bの12点direct PF truth計算およびresource scoringへ正しく接続すること**です。

今回許可するのは、実装・契約固定・synthetic tests・read-only検証・GitHub公開のみです。

**FS-R1 Phase B production scienceはまだ承認しません。**

厳守事項：

- Phase A predictionの再計算：禁止
- Phase A prediction/budgetの変更：禁止
- Production Ritz/PF/echo：禁止
- N₂・CO direct truth：0
- Production Schur：0
- Production branch continuation：0
- Exact-ground oracleのdecode：禁止
- 固定済みbranch ladderの変更：禁止
- 数値gateの緩和：禁止
- Phase Bの自動実行：禁止

B0がGOになっても、GPT/userによる別承認まで停止してください。

---

## 1. Repositoryと起点

Repository：

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

Phase A branch：

`pf-first-study-fs-r1-phase-a-production-20261008`

Phase A prediction freeze commit：

`89c091e885c07b7c02883b1479a143c23f51df3c`

Final handoff commit：

`e00ebc2024f72272cec64ebfd20c771d03665e95`

Phase A artifact：

`artifacts/pf_first_study_fs_r1_phase_a_production_20261008/`

B0用に新規branchを作成してください。

推奨：

`pf-first-study-fs-r1-b0-phase-b-barrier-20261008`

既存artifactおよび既存branchは変更しないでください。

## 2. 今回固定するauthority

### Phase A prediction

Prediction SHA-256：

`d1f95e5ee38e72cc5cb04cfb805c0ae441060104828c18268574acda5d2215a9`

これは**canonical prediction_manifest.jsonのSHA**です。

`production_results.json`単体のSHAと混同しないでください。

Production results SHA：

`899046840755e57531fac06ff4946fe947544040b3006963b28aeab0e241a4d1`

### v3 protocol

Protocol ID：

`FS-R1-20261007-v3`

Protocol SHA-256：

`b1d37961484b212a6f2fab8b38092e56e640bac85c2369ab4cb29ba4ec383884`

### Numerical contract

SHA-256：

`16067176e0d1b211c5c43bd85287741cc93719977a57b675d5e2547b84dae573`

### Phase A execution code bundle

SHA-256：

`abb832afdd8de951e005d3104d2f7e1644329d86612607b61820e1f15ec1d9e4`

上記は手入力の文字列だけを信用せず、GitHub上のactual committed bytesおよび既存manifestから独立に確認してください。

---

## 3. 最初に読む資料

### Phase A

以下を最低限確認してください。

- `README.md`
- `GO_NO_GO_FOR_PHASE_B.json`
- `prediction_manifest.json`
- `prediction.sha256`
- `production_results.json`
- `predicted_budgets.json`
- `prediction_intervals.json`
- `cold_replay.json`
- `numerical_gate_audit.json`
- `truth_access_audit.json`
- `private_recovery_receipt.json`
- `remote_verification.json`
- `verification.json`

### FS-R1-A0

- `fs_r1_protocol_v3.json`
- `fs_r1_numerical_contract_v1.json`
- `execution_code_identity.json`
- `budget_uncertainty_contract.md`
- `recovery_contract_v2.md`

### FS-R0.1

- `fs_r1_protocol_v2.json`
- `branch_ladder.json`
- `branch_contract.md`
- `truth_executor_contract.md`
- `truth_only_source_contract.md`
- `phase_barrier_v2.md`
- `r01_barrier.py`
- `scoring_bridge.py`
- `truth_executor.py`
- `branch_math.py`

### FS-R0

- new source registry/identities
- source sanitization contract
- four-arm contract
- scoring contract
- cost contract

旧v2をそのままPhase Bのauthorityとして使用するのではなく、**v2 branch rulesとv3 Phase A freezeの役割を分離**してください。

---

# Part I — v3 Phase A Freeze Binding

## 4. 現在の不整合を解消する

既存`r01_barrier.py`はv2用の実装です。

具体的には、

- v2 protocol SHA
- v2 Phase A manifest schema
- v2 execution-code identity
- v2 prediction structure
- v2 recovery reference

を前提としています。

しかし実際のPhase A productionはv3でfreezeされています。

また、v3 `prediction_manifest.json` の`files`はファイルレコード配列であり、v2の役割別辞書ではありません。

これらを**新しいv3専用barrier adapter**で解消してください。

旧v2実装を上書きして、過去のhashを壊さないでください。

## 5. v3 barrierの検証対象

Phase B truth callbackを開く前に、最低限以下の全項目を検証する実装を作ってください。

1. Phase A science-origin commit
2. 最終handoff commit
3. Actual committed prediction manifest
4. Canonical prediction SHA
5. Production results SHA
6. v3 protocol SHA
7. Numerical contract SHA
8. Phase A execution code bundle SHA
9. 全execution code memberのactual blob
10. N₂/CO source identities
11. Operational archive identities
12. Cold replay PASS
13. Numerical gates PASS
14. All eight budget intervals finite
15. Truth access zero
16. Private recovery receiptのintegrity evidence
17. 独立remote verification evidence
18. Source/protocol/code/result間の整合性

一つでも不一致なら、oracle sourceを開く前にfail closedしてください。

## 6. Commit lineage

以下を混同しないこと。

**Science origin commit**

`89c091e885c07b7c02883b1479a143c23f51df3c`

**Handoff commit**

`e00ebc2024f72272cec64ebfd20c771d03665e95`

Predictionの固定根拠はscience-origin commitです。

Handoff commitはremote receiptや判定資料を追加した後続commitです。

B0では、

- science-origin commitの凍結blob
- handoff commitの検証証拠
- 両commitの祖先・差分関係

を正しく確認してください。

Handoff commitにscienceの変更が混入していないことも監査してください。

GitHubのREADMEだけを信用するのではなく、actual Git blobを検証してください。

## 7. Prediction manifestの取り扱い

`prediction_manifest.json`は自己参照を避けるため、自身と`prediction.sha256`を対象外にしています。

この既存ルールを維持してください。

予測manifestに記録された各ファイルについて、

- path
- SHA256
- byte length
- committed blob
- local bytes

を検証してください。

Manifest内のprediction payload、protocol、code、source、recoveryの各identityを照合してください。

**Prediction SHAを再計算して、新しいSHAへ置き換えることは禁止します。**

不一致なら停止してください。

## 8. Remote receipt

既存`remote_verification.json`の実際のschemaを読み、独立remote fetchで検証された証拠を確認してください。

単に

`status = PASS`

が記録されているだけでは不十分です。

少なくとも、

- verification対象commit
- independent fetch
- manifest SHA
- 対象blob SHA
- authority identities

を検証してください。

既存receiptとv3 barrierの期待schemaが異なる場合、**追加のread-only verification adapter**を作ってください。

既存receiptを改変しないこと。

## 9. Recovery integrity

Phase A private recovery receiptについて、

- recovery SHA
- saved-before-public evidence
- authorization binding
- run lease identity
- source/protocol/code binding
- public resultとの一致

を検証してください。

Private snapshotそのものが必要なvalidationは、存在する場合のみread-onlyで行ってください。

Snapshotが不在で検証不能なら、架空のPASSにせず明示的なNO-GOにしてください。

Phase A scienceを再実行してsnapshotを再作成してはいけません。

---

# Part II — v3 Prediction / Scoring Bridge

## 10. 固定済み4-arm predictionを使用

Phase Bでは、Phase Aでfreezeされた以下の4 armだけを使用します。

| Arm | Definition |
|---|---|
| M00′ | CISD 3-point fit |
| M10′ | Ritz8 3-point fit |
| M01′ | CISD local at t₀ |
| M11′ | Ritz8 local at t₀ |

M11′ primary、M01′ challengerを維持してください。

Phase Bではpredictionを計算し直しません。

## 11. Frozen budgets

Phase A initial passの保存値をbudgetのauthorityとして使用してください。

Budget単位はPF rotationsです。

### N₂

| Arm | Nominal budget |
|---|---:|
| M00′ | 299615772.6844654 |
| M10′ | 281102281.27839935 |
| M01′ | 296038849.9350435 |
| M11′ | 281025694.41568553 |

### CO

| Arm | Nominal budget |
|---|---:|
| M00′ | 573991663.7360073 |
| M10′ | 536483867.9660144 |
| M01′ | 565590825.9010235 |
| M11′ | 536347072.94336736 |

上記表示値は確認用です。

実装では必ずactual committed `predicted_budgets.json` / `production_results.json`を読み、保存されたfull precisionを使用してください。

## 12. Frozen budgetの検証と使用を分ける

Budget算出式：

\[
B_j'=
\frac{\gamma\beta K}
{t_0(\epsilon_E-|p_j|)}
\]

Constants：

\[
\epsilon_E=0.00015936001019904
\]

\[
\beta=1.2,\qquad\gamma=1.01
\]

B0では、この式を使って保存budgetのintegrityを検証して構いません。

ただしPhase B scoringで使うのは**検証済みの保存値そのもの**です。

再計算した値で保存予算を上書きしないでください。

小さな丸め差が出た場合も、勝手に許容差を設定せず、既存のcanonical scalar validation契約に従ってください。

## 13. Prediction uncertainty

v3でfreezeされたprediction uncertaintyとbudget intervalを保持してください。

M00′ / M10′：

- N₂：`1.1122914179929199e-7 Ha`
- CO：`9.800205391365774e-8 Ha`

M01′ / M11′：

`1e-11 Ha`

Budget intervalはPhase Aで固定済みです。

Phase Bでtruthを見てから幅を狭めることは禁止します。

これらは数値再現性の幅であり、true errorのcertificateではありません。

## 14. v3 scoring bridge

新しいscoring bridgeを実装してください。

入力：

1. Verified frozen Phase A prediction
2. Verified frozen nominal budgets/intervals
3. Validated new-source direct truth at t₀

出力：

- Direct PF error
- 各armのenergy slack
- Safe/unsafe/indeterminate status
- `primary_gain`
- `local_gain`
- `state_increment`
- `safety_repair`
- 条件別のoutcome
- 2条件全体のstudy interpretation

ただし、B0ではsynthetic truth fixtureによるテストだけを行います。

Actual N₂/CO direct truthは入力しません。

## 15. Safety calculation

Phase Bで得られるsigned direct truthを

\[
d=\delta'_{\rm direct}(t_0)
\]

とします。

\[
e=|d|
\]

各armの固定budget \(B'_j\) について、

\[
S_j=
\epsilon_E-e-\frac{\beta K}{t_0B'_j}
\]

を計算してください。

事前登録されたprimary scoring ruleを維持してください。

Truth側の数値gateに不合格の場合、safe/unsafeの科学判定を行わないでください。

数値誤差の扱いについて、既存契約を超える新しいcertificateや許容差を勝手に導入しないこと。

## 16. Resource outcome

以下の事前登録ルールを維持してください。

### primary_gain

M11′ safe、かつ

\[
B'_{11}\le0.98B'_0
\]

### local_gain

M01′ safe、かつ

\[
B'_{01}\le0.98B'_0
\]

### state_increment

M01′・M11′ともsafe、かつ

\[
B'_{11}\le0.98B'_{01}
\]

### safety_repair

M01′ unsafe、M11′ safe。

N₂・COを独立に判定し、unsafeを平均値で相殺しないでください。

2/2・1/2・0/2のstudy interpretationも既存契約を維持してください。

## 17. Budget interval diagnostics

Phase Aでfreezeしたbudget intervalを保持し、必要であれば数値感度の診断に利用できるようにしてください。

ただし、

- primary outcomeは事前登録のnominal-budget rule
- interval診断は補助的なnumerical robustness
- replay幅はtruth certificateではない

という区別を維持してください。

今回新しいscientific success thresholdを追加しないこと。

---

# Part III — Truth Branch Execution

## 18. Branch ladderは変更しない

Phase Bでは、FS-R0.1で固定した12点を使用します。

各conditionで6点、合計12点です。

最初の5点がbranch certification、最後のt₀だけがscoringです。

### N₂

```text
0.06263494343795273
0.12526988687590546
0.18790483031385818
0.31317471718976365
0.5923370942191331
0.5983202971910435
```

### CO

```text
0.06546804264781796
0.1309360852956359
0.19640412794345388
0.3273402132390898
0.6066206637106297
0.6127481451622522
```

Binary64 authorityは既存`branch_ladder.json`とします。

COの0.99t₀が表示値と乗算値で1 ULP異なることは既に監査済みです。

B0で座標を修正しないでください。

## 19. Branch selection

初点：

`maximum_exact_ground_overlap`

2点目以降：

`maximum_previous_selected_vector_overlap`

退化cluster：

`projector continuity`

固定数値gate：

- previous overlap ≥0.9
- eigenpair residual ≤1e-10
- unitarity residual ≤1e-10
- phase cluster gap <1e-8

既存deterministic tie/phase rulesを維持してください。

Historical branch IDは使用しません。

## 20. Branch namespace

新sourceにbindしたnamespaceを維持します。

`FS-R1:<source_identity_sha>:positive:k<ladder_index>`

N₂・COのsource identityはFS-R0で固定されたものだけです。

Source identity mismatchで停止してください。

## 21. No adaptive rescue

Phase B実行中に以下を行わないこと。

- midpoint追加
- lower anchor追加
- 0.4/0.75追加
- extra truth coordinates
- overlap閾値緩和
- cluster閾値変更
- 別solverへの結果依存切替
- t₀で単独のmaximum-ground-overlap選択
- historical truthへのfallback

Branch failureはtechnical outcomeとして停止し、resource success/failureに数えないでください。

## 22. Existing truth executorのv3接続

既存の`truth_executor.py`、`branch_math.py`はv2 proofを要求します。

これらの数学的なbranch規則を保持しながら、v3 Phase A proofと新しいPhase B authorizationに接続してください。

旧ファイルを改変せず、新しいadapter/controllerを作成する方針を優先してください。

ただし、単に`verified=True`を埋め込むなど、barrierを偽装する実装は禁止します。

v3 proofの本物のhash/commit/source/code/remote検証が完了している場合だけ、truth-only entrypointへ到達できるようにしてください。

## 23. Phase B authorization

B0ではPhase B authorizationを発行しないでください。

将来のPhase Bでは、別の明示承認を必要とするように実装してください。

その承認は最低限以下へbindしてください。

- Phase B authorization ID
- v3 Phase A protocol SHA
- frozen prediction SHA
- science-origin commit SHA
- handoff proof
- full Phase B execution code hash
- branch ladder SHA
- N₂/CO source identities
- truth coordinate budget = 12

Phase Aで消費済みのauthorizationを再利用しないでください。

## 24. Truth-only source isolation

Phase B productionの正しい順序は、

1. Phase B authorization検証
2. Phase A committed freeze検証
3. Independent remote receipt検証
4. Prediction/protocol/code/source/recovery検証
5. Truth execution lease取得
6. Truth-only sourceを開く
7. 12点branch continuation実行

です。

**B0では手順6以降を一切実行しません。**

Exact-ground sourceはPhase B専用であり、prediction/scoring前処理へ渡さないでください。

Original private source bytes、exact ground、energy、state vectorなどをGitへ公開しないでください。

## 25. Truth executor numerical checks

既存のCPU complex128 native PF unitary construction、Schur、branch matching、checkpoint、residual検証を維持してください。

Production dimension：

`1568`

今回のB0では、実1568次元のunitary/Schurを構築しないでください。

実行環境、memory・backendのstatic readinessを確認し、実測数値成立や性能を主張しないこと。

## 26. Failure and checkpoint

将来のPhase B実行では、

- coordinateごとのattempt記録
- scalar recovery
- private selected-vector checkpoint
- SHA/source/time/branch binding
- failure時の残り全truth停止
- science再実行禁止

を維持してください。

Public serialization failureではsaved scalarからのみ復旧します。

Phase A predictionとの整合性を維持してください。

---

# Part IV — B0 Tests

## 27. Science-free tests

B0ではsynthetic/test fixtureを使用し、production truthを計算しないこと。

最低限、以下のテストを追加してください。

### Freeze integrity

1. 正しいv3 prediction freezeを受理
2. Phase A origin commit mismatchを拒否
3. Handoff lineage mismatchを拒否
4. Prediction SHA mismatchを拒否
5. Production result SHA mismatchを拒否
6. Manifest memberのbytes/hash mismatchを拒否
7. Numerical contract mismatchを拒否
8. Execution code bundle/member mismatchを拒否
9. Source identity mismatchを拒否
10. Recovery evidence mismatchを拒否
11. Remote receipt absent/invalidを拒否
12. Cold replay FAILのpackageを拒否
13. Numerical gate FAILのpackageを拒否
14. Truth-containing Phase A predictionを拒否

### v3 scoring bridge

15. Frozen initial nominal budgetを使用
16. Cold resultでinitial budgetを上書きしない
17. Scoring時にbudgetを変更しない
18. 4-arm欠損を拒否
19. Truth-free状態でscoring禁止
20. Valid synthetic truthからslackを計算
21. Safety threshold境界テスト
22. Primary gain判定
23. Local gain判定
24. State increment判定
25. Safety repair判定
26. Unsafeの平均相殺禁止
27. Intermediate branch truthをresource scoringに渡さない
28. Truth不成立時に科学判定しない

### Branch continuation

29. Exactly 12 coordinates
30. Exactly 2 scoring endpoints
31. First ground-overlap selector
32. Later previous-vector selector
33. Projector cluster continuation
34. Overlap failureでSTOP
35. Eigenpair residual failureでSTOP
36. Unitarity failureでSTOP
37. Ambiguous clusterでSTOP
38. Wrong source namespaceを拒否
39. Historical branch IDを拒否
40. Extra coordinateを拒否
41. Nearest-time substitutionを拒否
42. Adaptive rescueを拒否

### Authorization / recovery

43. Phase B承認なしでtruth sourceを開けない
44. v3 proof不足でtruth sourceを開けない
45. 別authorization bindingが必須
46. Phase A authorization再利用を拒否
47. Duplicate Phase B leaseを拒否
48. Recovery integrity mismatchを拒否
49. Serialization failureでscienceを再実行しない
50. B0実行中のproduction truth dispatchを拒否

テスト番号は管理用であり、必要に応じて論理的に分割して構いません。

既存317 testsを壊さないでください。

## 28. Real freezeのread-only verification

Synthetic testsに加えて、今回の実際のPhase A committed packageをread-onlyで検証してください。

ただし、以下を明確に区別すること。

- Real committed Phase A scalar/hash検証：許可
- Real new-source PF/echo/Ritz再計算：禁止
- Real direct PF truth/Schur：禁止
- Oracle source decode：禁止

実際のprediction packageがv3 barrierを通ることを確認し、その後truth-only境界の直前で停止するテストを設けてください。

---

# Part V — Cost / Publication / Decision

## 29. Truth validation cost

将来のPhase B用に、以下のaction/cost ledgerを準備してください。

- truth-only source load
- PF identity block/unitary construction
- Schur decomposition
- branch matching
- eigenpair residual
- unitarity residual
- selected-vector checkpoint
- wall seconds
- peak RSS/GPU memory
- actual completed and attempted coordinates

Planned Phase B：

- 12 truth coordinates
- 10 branch-certification coordinates
- 2 primary-scoring coordinates

Costは、

`truth_validation_cost`

として保存します。

Phase A classical calibration costやpredicted QPE PF rotationsとは別扱いにしてください。

実測していない内部workは`unknown/null`です。

## 30. B0 status

以下の判定を使用してください。

### `GO_FOR_FS_R1_PHASE_B_PRODUCTION`

条件：

- v3 Phase A freeze検証成功
- prediction/protocol/code/source/recovery/remote binding成功
- v3 scoring bridge実装完了
- 12点branch executorとの接続完了
- truth-only authorization barrier完了
- lease/recovery完了
- synthetic tests PASS
- 既存317 tests PASS
- Phase A再計算0
- N₂/CO new truth 0
- production Schur 0
- exact-ground oracle decode 0

これは**preflight GO**であり、Phase B science実行承認ではありません。

### `NO_GO_V3_FREEZE_BINDING`

Actual Phase A freezeとの接続不成立。

### `NO_GO_SCORING_BRIDGE`

固定prediction/budgetとscoringの接続不成立。

### `NO_GO_TRUTH_BARRIER`

Truth-only authorization/provenance/leaseの契約不成立。

### `NO_GO_TRUTH_EXECUTOR`

12点branch execution経路がproduction-readyにならない。

### `NO_GO_OTHER`

理由を具体的に報告。

## 31. 必須成果物

新規artifact directoryを作成してください。

推奨：

`artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/`

最低限、以下を作成してください。

1. `README.md`
2. `GO_NO_GO_FOR_PHASE_B_PRODUCTION.json`
3. `phase_a_v3_freeze_binding_contract.md`
4. `phase_a_freeze_verification.json`
5. `phase_b_bridge_contract.json`
6. `phase_b_authorization_contract.md`
7. `phase_b_execution_plan.json`
8. `v3_scoring_bridge_contract.md`
9. `branch_ladder_binding.json`
10. `truth_only_barrier_contract.md`
11. `truth_executor_readiness.json`
12. `truth_validation_cost_contract.json`
13. `recovery_contract.md`
14. `tests.log`
15. `verification.json`
16. `production_action_audit.json`
17. `source_manifest.json`
18. `publication_manifest.json`

必要な新規Python moduleとtestsも同directory等へ追加してください。

Private vectors/matrices/ground states/source binariesはcommitしないでください。

## 32. Git commit / push

作業完了後に、

- 新規commit
- normal push
- remote tip照合
- independent remote fetch
- 新規artifact blob検証
- authority blob検証
- science-origin freeze blob不変確認

を実施してください。

Prediction hashを変更しないでください。

Commit後にpublication receiptを追加する場合、自己参照になるcommit/hash循環を作らないでください。

## 33. 最終報告

完了時は以下を報告してください。

### A. Final status

- B0 GO/NO-GO
- v3 freeze binding
- scoring bridge
- truth-only barrier
- branch executor readiness
- tests

### B. Phase A freeze

- Science-origin commit
- Handoff commit
- Prediction SHA
- Protocol SHA
- Numerical contract SHA
- Execution code bundle SHA
- Source identities
- Remote proof status

### C. Truth execution contract

- Branch ladder 12点
- Certification 10点
- Scoring 2点
- Selector/gates
- Phase B authorization requirement
- Lease/recovery status

### D. Zero-action audit

- Phase A re-execution = 0
- New direct truth = 0
- Branch production execution = 0
- Production Schur = 0
- Exact-ground oracle decode = 0
- Phase B authorized = false

### E. Provenance

- Branch
- Commit SHA
- GitHub push
- Independent remote verification
- Remaining blockers

---

## 34. 最終停止

FS-R1-B0を完了したら必ず停止してください。

`GO_FOR_FS_R1_PHASE_B_PRODUCTION`でも、N₂・COの12点direct truthを実行してはいけません。

今後の順序は以下です。

\[
\boxed{
\text{FS-R1-B0 implementation/preflight}
\rightarrow
\text{GPT review}
\rightarrow
\text{separate Phase B science authorization}
\rightarrow
\text{12-point direct truth}
\rightarrow
\text{resource/safety scoring}
}
\]

今回の目的は、**既に凍結したPhase A predictionを一切変更せず、Phase Bのtruth-only実行経路とscoringを正しく閉じること**です。

数値gate、source、branch ladder、PF、state、time、予算、outcome ruleを変更しないでください。Phase A、FS-R0/R0.1/A0、historical first-study、H4、FS-C0/C0.5/C0.6の既存artifactも変更禁止です。