第1研究のFS-C1へ進む前に、**FS-C0.5：source/backend execution closure** を実施してください。

今回はscience executionではありません。

目的は、

1. historical baselineを正しい3-point定義へ修正してprotocolを閉じる  
2. N2/COの元production sourceをidentity-preservingに回収できるか確認する  
3. native PF/echo backendの再現性・数値契約・費用会計を閉じる  

ことです。

\[
\boxed{\text{FS-C0.5ではproduction science action = 0}}
\]

を維持してください。

FS-C1はまだ実行しないでください。

---

# 0. 起点

Repository:

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

現在のFS-C0:

- Branch  
  `pf-first-study-fs-c0-20261007`

- Commit  
  `9accc300ba7b8049ae9a1ef870ca4e7c0032e6ae`

- Artifact  
  `artifacts/pf_first_study_fs_c0_20261007/`

現在の判定:

`NO_GO_FOR_FS_C1`

NO-GOはscience failureではなくexecution closure不足です。

FS-C0のformal/history/resultは変更しないでください。

---

# 1. 今回GPT側で確定する修正

FS-C0の「元5点training」は誤りでした。

元S0 / practical calibrationのhistorical baselineは、

`echo_imag_3point`

であり、

\[
\boxed{
T_{\rm train}
=
\{0.1,0.2,0.3\}\,t_{\rm ref}^{\rm historical}
}
\]

です。

## historical baseline上の役割

- `0.1 × t_ref`：training
- `0.2 × t_ref`：training
- `0.3 × t_ref`：training
- `0.4 × t_ref`：historical M00 trainingではない
- `0.5 × t_ref`：sentinel / selection diagnosticでありtrainingではない

したがって、FS-C1で「historical M00/B0」を再現する際に、

- 0.4を補う
- 0.5をtrainingへ追加する
- H01の別5-point modelをM00へ置換する

ことは禁止です。

---

# 2. 修正後の4-arm定義

FS-C1の4 armを以下へ固定してください。

## M00 — Historical baseline

- State: historical CISD
- Estimate at historical selected \(t_0\):
  historical `echo_imag_3point`
- Training:
  historical 3 absolute coordinates
- Fit:
  \[
  f(t)=a_4t^4+a_6t^6
  \]
- M00のprimary value/B0はhistorical saved resultをimmutable referenceとして保持

M00は新backendで作った値へ置き換えません。

新backendによるM00再計算は、

> historical baselineを同じsource/backend contractで再現できるか

を確認するvalidation gateです。

---

## M10 — Ritz state + same 3-point fit

- State: residual Krylov Ritz, primary \(m=8\)
- Training coordinates:
  **M00と同じ3 absolute times**
- Fit:
  M00と同じ \(t^4+t^6\)、no intercept、unweighted
- Evaluate fit at the same historical selected \(t_0\)

Ritz stateから新しい\(t_{\rm ref}\)を作らないでください。

Ritz結果を見てtraining timeを移動しないでください。

---

## M01 — CISD local selected-time proxy

- State: historical CISD
- Coordinate: historical selected \(t_0\)
- Quantity:
  \[
  g_{\rm CISD}(t_0)
  \]
- no fit

---

## M11 — Ritz local selected-time proxy

- State: same Ritz8 state as M10
- Coordinate: same historical selected \(t_0\)
- Quantity:
  \[
  g_{\rm Ritz}(t_0)
  \]
- no fit

M11 remains the preregistered primary arm.

M01 remains the cheaper challenger.

---

# 3. 対象条件

今回closureする対象は固定です。

### N2 equilibrium

`N2_active_eq_sto3g`

Historical current_m3 selected time:

\[
t_0=0.5983202971910435
\]

Historical B0:

`301091225.69005436`

Historical source pickle expected SHA-256:

`ccf3056cda01c5750eb3412c065d50b5f1009fd5a2a5b705e077d06f839735b7`

Expected Hamiltonian SHA-256:

`62ed51d7bd47f6596a1a6a40cc0330e4727dc51f42114bd05226dcef1f884be7`

---

### CO equilibrium

`CO_active_eq_sto3g`

Historical current_m3 selected time:

\[
t_0=0.6127481451622522
\]

Historical B0:

`578970030.3225045`

Historical source pickle expected SHA-256:

`91ad971f1fa68dd145686e8f2758cf69cd7d5b08d6537995a5fbadde62b17233`

Expected Hamiltonian SHA-256:

`1fed49b19bd97eef281089589112128fe46914ef8ed843e739e8588714290224`

実装時は表示値を再生成せず、authority artifactの保存値を読むこと。

---

# 4. Authority

最低限以下を確認してください。

## FS-C0

- `artifacts/pf_first_study_fs_c0_20261007/README.md`
- `GO_NO_GO_FOR_FS_C1.json`
- `source_and_backend_closure.json`
- `research_decision.md`
- `four_arm_design.md`
- `fs_c1_protocol.json`
- `fs_c1_protocol.md`
- `backend_review.md`
- `cost_dictionary.md`
- `predicted_action_budget.json`

## Historical practical calibration

- `artifacts/server_practical_calibration_minimal_20260923_79035cc/protocol.json`

特に、

`selector.proxy_model.name = echo_imag_3point`

かつ、

`training_relative_to_proxy_t_ana = [0.1, 0.2, 0.3]`

をhistorical baseline authorityとして扱ってください。

## H01 / source provenance

- `artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/...`
- `artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/...`
- Phase0 source registry
- completion analysis source manifests

を参照してください。

---

# 5. 今回行ってよいこと

今回許可するのは、

- source path/file探索
- hash計算
- metadata decode
- recovered pickleのidentity-only decode
- canonical array export
- source/backend adapter実装
- synthetic tests
- saved scalarを用いる再現性テスト
- code/static inspection
- backend instrumentationの実装
- serialization/recovery処理
- action/cost counter設計
- documentation
- commit/push

です。

---

# 6. 今回禁止するscience actions

以下をすべて0にしてください。

- new H matvec on production N2/CO science vector
- new Ritz basis production build
- new Ritz solve
- new PF evolution for new science coordinate
- new selected-time proxy science evaluation
- new fit using newly computed production Ritz/CISD proxy
- new direct truth
- full-H ground solve
- Schur
- eigensolve
- Hamiltonian regeneration
- CISD regeneration
- molecule regeneration
- new PF
- new time selection

source validationのためのidentity-only array decodeはscience actionに含めませんが、内容を使ってscientific observableを計算しないでください。

---

# 7. Source recovery — read-only探索

まず、元pickleをread-onlyで探索してください。

対象:

### N2

`N2_active_eq_sto3g.pkl`

expected SHA:

`ccf3056cda01c5750eb3412c065d50b5f1009fd5a2a5b705e077d06f839735b7`

### CO

`CO_active_eq_sto3g.pkl`

expected SHA:

`91ad971f1fa68dd145686e8f2758cf69cd7d5b08d6537995a5fbadde62b17233`

---

# 8. 探索対象

少なくとも以下を調べてください。

- repository root
- current worktrees
- old worktrees
- `.runtime`
- `.runtime/sanitized`
- H01 artifact directories
- P03 / unused-molecule artifact directories
- server artifacts
- local project copies
- user-owned backup/locationでrepository historyから参照されているpaths

historical metadataで確認されている例:

- `artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/cache/...`
- `artifacts/server_practical_calibration_minimal_20260923_79035cc/.runtime/sanitized/...`
- `artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/cache/...`

ただしpathが書かれているだけで存在すると仮定しないこと。

---

# 9. Source recoveryのhard rule

pickleが見つかった場合は、

**まずファイル全体SHA-256を確認してください。**

expected SHAと完全一致した場合のみidentity sourceとして採用。

不一致の場合、

- 内容が似ている
- H hashが一致する
- 数値が近い

という理由で置換しないでください。

---

# 10. 元pickleが見つからなかった場合

非常に重要です。

元pickleが見つからない場合、

\[
\boxed{\text{FS-C1はNO-GOのまま}}
\]

としてください。

以下をしてはいけません。

- PySCFからHamiltonian再生成
- CISD再生成
- group eigensystem再生成
- old `prepare_condition`でsourceを作り直す
- ground solveを使って似たsourceを作る

その場合は、

`SOURCE_NOT_RECOVERABLE_UNDER_IDENTITY_CONTRACT`

として停止してください。

新source再生成を許可するかは別のGPT/user判断です。

---

# 11. pickleが回収できた場合のcanonical export

expected whole-pickle SHAが一致した場合のみ、identity-preserving exportを作ってください。

少なくとも:

- restricted Hamiltonian
- ordered group representation
- ordered group component spectra / required compact representation
- CISD vector
- restricted basis / sector mapping metadata
- removed constant
- PF/group ordering metadata

をexport。

各array/fileに、

- dtype
- shape
- bytes
- SHA-256
- canonical serialization rule
- source pickle SHA
- source member/key

を保存してください。

---

# 12. Canonical source manifest

N2/COごとに、

`canonical_source_identity.json`

相当を作り、

最低限、

- whole pickle SHA
- Hamiltonian SHA
- CISD SHA
- restricted basis SHA
- ordered-group identity SHA
- each group/component SHA
- sector metadata SHA
- dtype / shape
- source path
- source recovery timestamp
- source provenance commit

を保存してください。

---

# 13. Hamiltonian identity check

FS-C0で期待されていたH SHAと一致することを確認してください。

N2:

`62ed51d7bd47f6596a1a6a40cc0330e4727dc51f42114bd05226dcef1f884be7`

CO:

`1fed49b19bd97eef281089589112128fe46914ef8ed843e739e8588714290224`

不一致ならstop。

---

# 14. Group ordering identity

groupは集合として一致すればよいのではなく、**ordered identity**を確認してください。

- group count
- group order
- each group hash
- component ordering
- step application ordering

がhistorical metadataと一致すること。

sortして合わせることは禁止です。

---

# 15. CISD identity

standalone CISD SHAを今回新たに固定してください。

ただし、

- exact ground overlap
- exact ground phase alignment
- true gap

を使ってCISDを修正しないこと。

global phaseに関するcanonicalizationを行う場合は、scientific quantityに影響しない固定ruleを事前に明記してください。

---

# 16. Historical M00 reproduction contract

M00はhistorical saved valueをprimary baselineとします。

新backendによるreproductionはvalidation用です。

M00 reproductionでは、

- same CISD
- same current_m3
- same three absolute training times
- same imag echo definition
- same powers 4,6
- same no-intercept unweighted fit
- historical numerical/scaling convention

を再現してください。

---

# 17. 3 absolute training coordinates

M10は、historical M00と**同じabsolute time values**を使ってください。

relative coordinateをRitz側の新しいanalytic timeへ掛け直さないこと。

FS-C0 `fs_c1_protocol.json` に保存されている、

`historical_training_times`

をauthorityとしてください。

---

# 18. historical coefficients

既存saved historical coefficientsとpredictionはimmutable referenceです。

N2/COそれぞれについて、

- saved coefficients
- saved selected-time prediction
- saved B0

を再現対象として保存。

再計算値でhistoryを上書きしないこと。

---

# 19. M00 reproduction toleranceを事前固定

今回重要です。

**結果を見た後にtoleranceを決めないでください。**

reproduction toleranceは、

1. historical saved numerical diagnostics
2. cold replay variability
3. floating-point/backend numerical bound

から、production再現を実行する前に決めてください。

単に、

`1e-8で十分そう`

などと任意に設定しないこと。

---

# 20. tolerance設計

可能であれば、

\[
\tau_{\rm repro}
=
\max(
\tau_{\rm historical},
\tau_{\rm backend},
\tau_{\rm roundoff}
)
\]

のように構成してください。

各成分の由来を明示。

historical residualをそのままbackend error certificateに流用しないこと。

もしsource-backedにtoleranceを閉じられない場合は、

`M00_REPRODUCTION_TOLERANCE_UNCLOSED`

としてFS-C1 NO-GOのまま停止してください。

---

# 21. Native PF backend adapter

既存native PF関数は任意compatible vectorを受けることが確認されています。

production-ready adapterでは、

- explicit state/vector input
- fixed group order
- fixed current_m3 coefficients
- complex128
- same left multiplication order
- same component exponential convention

を維持してください。

---

# 22. Echo definition

local proxyは、

\[
g_\psi(t)
=
\frac{
\operatorname{Im}
\langle \psi |
e^{-iHt}U_P(t)
|\psi\rangle
}{t}
\]

です。

同値な実装として、

\[
\langle e^{+iHt}\psi|U_P(t)\psi\rangle
\]

を使う場合でも、

- sign convention
- time orientation
- state
- energy origin

が同一であることをsyntheticとhistorical scalarで確認してください。

---

# 23. Backend reproduction tests

production science前に、saved H01 historical proxy valuesを使ってbackendを検証できるようにしてください。

可能ならhistorical CISD training coordinatesについて、

- saved proxy
- newly reproduced proxy
- absolute difference
- relative difference
- allowed tolerance

を比較。

これはscience resultではなくbackend reproduction validationとして扱う。

---

# 24. Ritz-input backend validation

Ritz stateそのものをproduction N2/COでまだ構築しないでください。

synthetic/fixture compatible vectorで、

- arbitrary vector input
- normalization
- PF norm preservation
- echo sign
- state independence of interface

を確認してください。

production Ritz vectorを使うscience callはFS-C1まで禁止です。

---

# 25. Exact-H `expm_multiply` cost contract

SciPy内部のH matvec回数を無理に1 actionへ換算しないでください。

FS-C1用cost contractでは、最低限以下を必須にしてください。

## 必須

- logical exact-H echo action count
- explicit Ritz H matvec count
- PF forward action count
- group application count
- small Ritz solve count
- wall seconds
- peak RSS
- software versions
- thread settings

## 取得可能なら保存

- `expm_multiply` internal matvec/matmat/rmatvec
- norm-estimation operations

## 取得不可能なら

`null / unknown`

と記録。

**0としない。**

---

# 26. Classical vs quantum cost

引き続き、

- classical wall/RSS
- logical calibration actions
- predicted QPE PF rotations

を別単位で保存してください。

CPU秒とQPE rotationを足したsingle scalar net costを作らないこと。

---

# 27. Cold replay contract

FS-C1ではcomplete cold replayを行えるようにしてください。

cold replayでは、

- source load
- state refinement
- PF action
- exact-H echo
- proxy
- fit

を独立に再構築。

初回passからscientific cacheを共有しない。

ただしimmutable source file bytesの再利用そのものと、science intermediate cacheの共有を区別してください。

---

# 28. Serialization / recovery

H4で起きたartifact lossを再発させないでください。

FS-C1 execution pathは、

\[
\text{science return}
\rightarrow
\text{private recovery snapshot}
\rightarrow
\text{public validation}
\rightarrow
\text{freeze}
\]

としてください。

FS-C0.5ではsynthetic testだけ実施。

---

# 29. 修正版FS-C1 protocol

`fs_c1_protocol.json` を直接上書きするのではなく、

**versioned amendment/new protocol**

を作ってください。

例:

`FS-C1-20261007-v2`

変更理由:

`historical baseline corrected from erroneous five-point assumption to source-backed echo_imag_3point training`

と明記。

旧v1を履歴として保持。

---

# 30. v2で必須なfield

最低限、

```text
historical_baseline_model = echo_imag_3point
historical_training_relative = [0.1, 0.2, 0.3]
historical_training_absolute = source-backed values
sentinel_relative = 0.5
sentinel_in_fit = false
relative_0_4_role = none
M00_primary = immutable historical saved baseline
M00_reproduction = execution validation only
M10_training_absolute = identical to historical M00
```

を固定してください。

---

# 31. Science-zero preflight

FS-C0.5で実行してよいproduction-related operationは、

- recovered source hash validation
- identity-only decode
- saved scalar reproduction using already saved scalar data
- metadata/backend synthetic tests

までです。

N2/COの新PF evolutionやnew echoは実行しないでください。

---

# 32. Tests

最低限以下を追加してください。

## Baseline

1. historical baseline is 3-point
2. 0.5 sentinel excluded from fit
3. 0.4 absent from historical training
4. M10 uses exact same absolute 3 times
5. H01 5-point model cannot silently replace M00

## Source

6. wrong whole-pickle SHA rejected
7. missing pickle produces NO-GO
8. wrong H hash rejected
9. wrong CISD hash rejected
10. group reorder rejected
11. regenerated source rejected

## Backend

12. arbitrary vector interface
13. echo sign convention
14. PF norm audit
15. historical saved scalar reproduction fixture
16. cold replay fixture
17. unknown internal expm work stored null, not zero

## Cost

18. classical/QPE cost units remain separate
19. logical echo actions counted correctly
20. rank-stop action formulas

## Truth barrier

21. FS-C1 truth cannot open in C0.5
22. direct truth not used in reproduction tolerance
23. exact-ground data not used in source construction

## Recovery

24. private recovery precedes public validation
25. serialization failure does not authorize science rerun

既存74 testsも壊さないこと。

---

# 33. FS-C0.5 completion states

最終的に以下のどれか1つを出してください。

## `GO_FOR_FS_C1`

条件:

- 3-point baseline contract closed
- exact source pickle recovered for both N2/CO
- whole-pickle hashes match
- canonical array identities closed
- H/order/CISD/sector identity pass
- M00 reproduction tolerance preregistered
- native backend reproduction passes
- echo numeric uncertainty contract closed
- cost ledger closed
- cold replay/recovery path ready
- all tests pass
- production science action count = 0

---

## `NO_GO_SOURCE_MISSING`

元pickleをidentity-preservingに回収できない。

---

## `NO_GO_SOURCE_IDENTITY`

pickleはあるがexpected identityに一致しない。

---

## `NO_GO_BACKEND_CONTRACT`

sourceは閉じたがM00 reproduction / echo / cost contractが閉じない。

---

## `NO_GO_OTHER`

上記以外。理由を具体的に保存。

---

# 34. Source missing時の停止

source missingなら、

**FS-C1 runnerを実装完成させてscience開始しないでください。**

source regenerationの設計も自動で始めないでください。

GPT/userへ戻してください。

---

# 35. 必須成果物

新しいartifact directoryを作成してください。

例:

`artifacts/pf_first_study_fs_c05_execution_closure_20261007/`

最低限:

1. `README.md`
2. `research_amendment.md`
3. `fs_c1_protocol_v2.json`
4. `fs_c1_protocol_v2.md`
5. `baseline_contract.json`
6. `source_recovery_audit.json`
7. `canonical_source_identity.json`
8. `backend_contract.md`
9. `backend_reproduction_preflight.json`
10. `echo_numerical_contract.json`
11. `cost_contract.json`
12. `cold_replay_contract.md`
13. `recovery_contract.md`
14. `truth_access_audit.json`
15. `tests.log`
16. `verification.json`
17. `source_manifest.json`
18. `publication_manifest.json`
19. `GO_NO_GO_FOR_FS_C1.json`

pickleやprivate working arraysを無承認でGitへcommitしないでください。

canonical public exportの可否はサイズ・privacy・既存policyに従い、必要ならhash/manifestのみ公開。

---

# 36. 最終報告

完了時は簡潔に以下を報告してください。

1. historical baselineを3-pointへ修正したこと
2. M00/M10 training coordinates
3. N2 source pickle回収可否・SHA
4. CO source pickle回収可否・SHA
5. canonical array identity closure
6. M00 reproduction tolerance
7. backend reproduction結果
8. echo numerical contract
9. internal expm work count status
10. cost ledger status
11. total tests
12. production science action count = 0
13. final GO/NO-GO
14. branch / commit / push / remote verification

---

# 37. 停止条件

FS-C0.5 completion後に必ず停止してください。

**`GO_FOR_FS_C1`であってもFS-C1を自動実行しないでください。**

次のscience authorizationはGPT/userが行います。

formal first-study、Phase0、H4 response/Ritz pilot、FS-C0の既存artifactは変更しないでください。