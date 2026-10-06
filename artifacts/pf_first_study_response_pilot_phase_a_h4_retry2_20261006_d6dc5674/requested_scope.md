第1研究のresponse-corrected calibration pilotについて、失敗したH4 Phase Aの**serialization-only修正と、1回だけのtechnical retry**を行ってください。

今回は、

> **artifact serialization boundaryの修正 → science action 0のpreflight → 同一science specificationでPhase Aを1回だけ再実行 → prediction freeze → commit/push →停止**

までです。

**Phase Bは未承認です。saved truth / exact proxyは開かないでください。**

---

# 0. 失敗したAttempt 1

前回のPhase Aは以下で停止しました。

- Branch
  `pf-first-study-response-pilot-h4-phase-a-20261006`

- Failed-attempt audit commit
  `3d7a923f2a8d11aff57a05454eca8e142496833e`

- Artifact
  `artifacts/pf_first_study_response_pilot_phase_a_h4_20261006_31ffdca3_failed/`

status:

`PHASE_A_FAILED`

原因はscience methodではなく、

`post_execution_pre_write_schema_validation`

でのserialization mismatchです。

具体的には、

- frozen loader:
  `ordered_group_identity = list(zip(groups, hashes))`
- Python in-memory:
  tuple pair
- strict JSON schema:
  array of arrays

の表現差によってschema validationが失敗しました。

Attempt 1では、

- Phase A science計算1回
- complete cold replay 1回

は実行済みですが、

- prediction freezeなし
- prediction SHAなし
- numerical payload保存なし
- Phase Bなし
- saved truth access 0

です。

Attempt 1は削除・上書きせず、failed technical attemptとしてそのまま保持してください。

---

# 1. 今回の判断

GPT/ユーザー判断として、

\[
\boxed{\text{1回だけのPhase A technical retryを許可}}
\]

します。

ただし、

- science algorithm
- response formula
- Ritz comparator
- times
- m
- SVD rule
- rank threshold
- fit
- noise rule
- action accounting
- truth barrier

は一切変更しないでください。

今回許可する変更は、

1. JSON serialization normalization
2. science結果のprivate recovery snapshot
3. それらに必要なpreflight/tests

のみです。

---

# 2. Science authorityは変更しない

引き続きscience specificationのnormative authorityは、

`artifacts/pf_first_study_response_pilot_phase05_20261006/response_pilot_protocol.json`

です。

そのSHA-256も変更しないでください。

Phase 0.6 production implementationのscience kernelも変更しないでください。

特に以下は変更禁止です。

- `g_resp`
- full residual LS
- Krylov basis
- m=1,2,4,8
- primary m=8
- MGS 2pass
- rank-stop rule
- truncated SVD
- Ritz comparator
- fit functional form
- train/eval split
- evaluation coordinates
- noise / rho
- cold replay
- outcome logic

---

# 3. Serialization修正

今回のprimary bugだけを修正してください。

現状のような、

```python
ordered_group_identity = list(zip(groups, hashes))
```

によるtuple pairを、そのままstrict JSON schema validationへ渡さないでください。

artifact boundaryで、

```python
ordered_group_identity = [
    [group_id, group_hash]
    for group_id, group_hash in ordered_group_identity
]
```

のように**JSON-native representationへcanonicalize**してください。

重要：

- schemaをtuple許容へ緩めない
- loaderのscience/source identity意味を変更しない
- source hashを変更しない
- group orderを変更しない
- group/hash pairingを変更しない

こと。

---

# 4. JSON normalization utility

可能であればartifact metadata全体に対して、明示的な

`to_json_native(...)`

のような純粋関数を用意してください。

対象は少なくとも、

- tuple → list
- numpy scalar → Python scalar
- numpy arrayがmetadataに混入する場合 → list
- Path → string

など。

ただし、binary/vector/matrix payloadまでJSON化する必要はありません。

science scalar artifactに必要なmetadataだけに限定してください。

この関数は、

- science valuesを変更しない
- numeric precisionを意図的に丸めない
- orderを勝手にsortしない

こと。

---

# 5. Science-zero serialization preflight

Phase A technical retryの前に、**science action 0**で次を実行してください。

production H4 identity metadataについて、

1. allowlist loaderでidentity-only decode
2. metadata object構築
3. JSON-native canonicalization
4. strict schema validation
5. `json.dumps(..., allow_nan=False)`
6. `json.loads(...)`
7. schema re-validation
8. canonical representation comparison
9. source hash / array identity unchanged確認

を行ってください。

少なくとも、

- H
- 13 ordered groups
- CISD

のidentity metadataがroundtrip後も完全一致することを確認してください。

---

# 6. Regression test

Attempt 1のfailureを再現するtestと、修正後に通るtestを両方残してください。

最低限：

## Test A

raw Python tuple representationでは旧failureが再現する。

## Test B

JSON-native normalization後は同じmetadataでstrict schema PASS。

## Test C

roundtrip後もgroup order / group hash / source identityが不変。

## Test D

serialization patchによってscience protocol hashが変わらない。

## Test E

Phase B truth barrierに影響しない。

---

# 7. Recovery snapshotを追加

Attempt 1では、

`execute_phase_a()`正常return

のあと、public artifact schema validation前にprocessが停止し、science outputsを失いました。

technical retryでは順序を、

\[
\boxed{
\text{science return}
\rightarrow
\text{private recovery snapshot}
\rightarrow
\text{public artifact validation/write}
}
\]

に変更してください。

---

# 8. Recovery snapshotの性質

private recovery snapshotは以下を満たしてください。

- private runtime path
- create-only
- immutable
- SHA-256保存
- truth fieldなし
- exact-state fieldなし
- Phase B inputとして直接使用禁止
- public `PHASE_A_FROZEN`とは別物
- prediction freeze commitの代替ではない

目的は、

> public serialization/artifact layerが再びtechnical failureした場合でも、science再計算なしでscalar結果を復旧できるようにする

ことです。

---

# 9. Recovery snapshotへ保存するもの

science return直後に、最低限以下を保存してください。

## Basis

- actual rank
- prefix stop
- rank thresholds
- orthogonality diagnostics

## Response

- SVD ranks
- singular values
- conditions
- residuals
- z norms

## Ritz

- dimensions
- projected eigenvalues
- numerical status

## Proxy

- A0/A1/A2
- m diagnostics
- first pass
- cold replay
- replay differences

## Fit

- coefficients
- fit status
- condition numbers
- residuals

## Prediction

- all frozen evaluation predictions

## Actions

- complete actual counter ledger

## Provenance

- protocol SHA
- code SHA
- source identity SHA
- authorization SHA
- attempt number

binary states/vectors/matrices自体をpublicへ保存する必要はありません。

---

# 10. Recovery snapshot validation

private snapshotにも、

- JSON-native serialization
- allow_nan=False
- hash
- schemaまたは最低限のstrict structure validation

を行ってください。

public artifact failure時でも、

`recovery_snapshot_valid=true`

ならscience再実行せず修復可能な設計にしてください。

---

# 11. Retry authorization

新しいauthorization recordを作成してください。

明示的に、

- `execution_attempt = 2`
- `retry_kind = technical_retry`
- `technical_retry_reason = serialization_artifact_boundary`
- previous attempt commit:
  `3d7a923f2a8d11aff57a05454eca8e142496833e`
- previous prediction freeze: false
- previous truth access: 0
- science specification unchanged: true
- allowed science reruns: exactly 1
- cold replay: exactly 1
- Phase B authorized: false

を記録してください。

Attempt 1のauthorizationを上書きしないでください。

---

# 12. Retry前のhard gate

以下が全てPASSするまでscienceを開始しないでください。

- serialization regression tests
- production metadata roundtrip
- source identity
- protocol hash
- code hash
- adapter integrity
- truth barrier
- recovery snapshot synthetic test
- action counter synthetic tests
- cold replay synthetic path
- working tree clean
- exact base/branch identity

1つでも失敗したらscience action 0で停止してください。

---

# 13. Phase A technical retry

preflight PASS後、Attempt 2としてPhase Aを**1回だけ**実行してください。

scopeはAttempt 1と完全に同じです。

- H4
- current_m3
- CISD
- same 22 signed coordinates
- m=1,2,4,8
- complete cold replay 1回

追加science rerunは禁止です。

---

# 14. Science実行中のtruth prohibition

引き続きPhase A中は、

- saved direct truth
- exact proxy
- exact ground
- error decomposition
- controlled states
- branch truth
- Phase B artifact

へアクセスしないでください。

truth access countは0でなければhard failureです。

---

# 15. Attempt 2でtechnical failureした場合

再度technical failureしても、

**追加science再実行は禁止**です。

recovery snapshotが残っていれば、

- science再計算なし
- artifact layerだけ修復可能か監査

までにしてください。

Attempt 3は自動実行しないでください。

---

# 16. Phase A success時

Attempt 2が正常完了した場合、

1. private recovery snapshot確定
2. public payload JSON-native normalization
3. strict schema validation
4. public artifact write
5. prediction SHA-256
6. action count validation
7. numerical gates validation
8. `PHASE_A_FROZEN`
9. git commit
10. push
11. remote SHA確認
12. remote blob/hash確認

まで行ってください。

---

# 17. Attempt historyを残す

final Phase A artifact/reportには必ず、

## Attempt 1

- science executed: yes
- cold replay: yes
- failed at artifact schema boundary
- predictions frozen: no
- numerical output recovered: no
- truth access: 0
- audit commit:
  `3d7a923f2a8d11aff57a05454eca8e142496833e`

## Attempt 2

- technical retry
- same science protocol
- serialization-only patch
- recovery snapshot enabled
- science execution count
- final status

を明示してください。

Attempt 1を「なかったこと」にしないでください。

---

# 18. Phase A numerical review outputs

成功した場合、以下を必ず保存・報告してください。

1. actual retained Krylov rank
2. prefix stop
3. response SVD ranks
4. response condition range
5. response residual convergence
6. z norm range
7. Ritz dimensions
8. Ritz numerical status
9. A0/A1/A2 fit statuses
10. a4/a6 coefficients
11. cold replay maximum difference
12. action counts
13. prediction SHA-256
14. Phase A freeze commit
15. source/code/protocol identity
16. truth access count = 0

---

# 19. Phase A scientific interpretation boundary

retry成功後も、Phase Aでは、

- response improves accuracy
- Ritz improves accuracy
- response beats Ritz
- Outcome A/B/C/D
- resource benefit

を判定しないでください。

truthを使っていないためです。

Phase Aでは、

- numerically ready
- numerically weak
- failed

まで。

---

# 20. Phase A status

以下で判定してください。

### `PHASE_A_NUMERICALLY_READY`

- all hard gates pass
- artifact frozen
- primary fits evaluable
- numerical execution valid
- truth access 0

### `PHASE_A_NUMERICALLY_WEAK`

science/artifactは完了したが、

- severe rank collapse
- response residual nonconvergence
- extreme conditioning
- primary fit not_identifiable

などがある。

predictionはfreezeしたまま結果を隠さない。

### `PHASE_A_FAILED`

- source
- action
- numerical
- cold replay
- serialization
- artifact integrity

等のhard failure。

---

# 21. Phase Bは禁止

Attempt 2が成功し、

- prediction SHAあり
- freeze commitあり
- remote verification済み

でも、

**Phase Bは実行しないでください。**

saved direct 12 rows / exact proxy 22 rowsを開かないでください。

次の承認はGPT/ユーザーが行います。

---

# 22. 必須成果物

新しいcreate-only artifact directoryを作ってください。

例：

`artifacts/pf_first_study_response_pilot_h4_phase_a_retry2_20261006_<id>/`

最低限：

1. `README.md`
2. `authorization_retry2.json`
3. `attempt_history.json`
4. `serialization_fix.md`
5. `serialization_preflight.json`
6. `recovery_snapshot_audit.json`
7. `source_identity.json`
8. `action_counts.json`
9. `basis_diagnostics.*`
10. `response_diagnostics.*`
11. `ritz_diagnostics.*`
12. `proxy_values.*`
13. `fit_results.*`
14. `predictions.json`
15. `prediction.sha256`
16. `cold_replay_audit.json`
17. `numerical_gates.json`
18. `truth_access_audit.json`
19. `verification.json`
20. `publication_manifest.json`
21. `PHASE_A_FROZEN`

失敗時は成功artifactを偽装せず、failure artifactを作って停止してください。

---

# 23. Tests

今回追加したserialization/recovery testsに加え、

- Phase 0.5 tests
- Phase 0.6 tests

を維持してください。

science再実行前に全部PASSが必要です。

最終reportで、

- existing tests
- new tests
- total passed

を報告してください。

---

# 24. 最終報告

完了後、簡潔に以下を報告してください。

1. serialization fix内容
2. retry前preflight結果
3. recovery snapshot実装結果
4. Attempt 2 science execution回数
5. actual retained rank
6. response SVD rank / condition
7. residual convergence
8. Ritz status
9. A0/A1/A2 fit status
10. cold replay最大差
11. actual action counts
12. prediction SHA
13. Phase A freeze commit
14. remote/blob verification
15. truth access 0
16. Phase B未実行
17. `PHASE_A_NUMERICALLY_READY / WEAK / FAILED`

---

# 25. 停止条件

Attempt 2成功・freeze・commit・push・remote verification後に停止してください。

**Phase Bへ進まないでください。**

Attempt 2が失敗した場合も停止し、Attempt 3は実行しないでください。

formal result、Phase 0、Phase 0.5、Phase 0.6、Attempt 1 auditは変更しないでください。
