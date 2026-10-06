第1研究のresponse-corrected calibrationについて、**Phase 0.6：production adapter実装＋science直前preflight** を進めてください。

今回は **production実装とpreflightのみ** です。

**H4 science calculationはまだ実行しないでください。science action countは0のまま停止してください。**

---

# 0. 起点

Phase 0.5は以下でdesign freeze済みです。

- Repository
  `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

- Branch
  `pf-first-study-response-pilot-phase05-20261006`

- Commit
  `48f3d889d096f2fe3af55c200a757747df384941`

- Artifact
  `artifacts/pf_first_study_response_pilot_phase05_20261006/`

Phase 0.5では、

- response estimator
- full residual least-squares
- Krylov response subspace
- m=1/2/4/8
- m=8 primary
- Ritz comparator
- refit rule
- Phase A / Phase B truth barrier
- evaluation metrics
- outcome logic
- action accounting

までfreezeされています。

**今回これらのscience specificationを変更しないでください。**

---

# 1. 今回の目的

次のH4 pilotを安全に実行できるよう、

> **Phase 0.5でfreezeしたsynthetic-only implementationを、保存済みH4 production inputへ接続するadapter/backendを実装し、truthを開かずにproduction execution readinessを確認する**

ことが目的です。

今回の終了時点では、

- production adapterが実装済み
- source identityが閉じている
- Phase Aがtruth-freeで実行できることが確認済み
- action counterがprotocolと整合
- cold replay経路が実装済み
- Phase B readerがPhase A freezeなしでは実行不能
- production H4 science自体は未実行

という状態にしてください。

---

# 2. Authority

まず以下を読んでください。

## Phase 0.5 authority

1. `artifacts/pf_first_study_response_pilot_phase05_20261006/README.md`
2. `response_pilot_protocol.json`
3. `response_pilot_protocol.md`
4. `algorithm_design.md`
5. `cost_accounting.md`
6. `novelty_review.md`
7. `GO_NO_GO_FOR_SCIENCE.json`
8. `source_identity_phase_a.json`
9. `saved_truth_join_contract.json`
10. `expected_action_counts.json`
11. `user_amendments.json`

**Normative authorityは `response_pilot_protocol.json` です。**

code / prose / inherited implementationと競合した場合は、scienceを実行せず停止してください。

## 元H4 source authority

Phase 0.5で固定されたsource identityに従い、

- H4 Hamiltonian
- H4 13 ordered groups
- CISD state
- sector metadata
- current_m3 definition

のみをPhase Aで使用してください。

---

# 3. 今回の禁止事項

今回は以下を禁止します。

- H4 Phase A science execution
- H4 Phase B scoring
- production H matvecによるscience result取得
- production PF actionによるscience result取得
- response vectorのproduction計算
- Ritz stateのproduction計算
- production proxy値の取得
- fitのproduction実行
- saved direct truth access
- exact-ground state access
- exact-ground energyをalgorithm入力へ使用
- controlled state access
- D4 / D6 / D8等のtruth/mechanism operator access
- Schur solve
- eigensolveによるfull H ground取得
- new direct truth
- new Hamiltonian
- new state
- new PF
- new molecule / geometry
- gamma変更
- m変更
- SVD threshold変更
- response formula変更
- outcome logic変更
- science resultを見たparameter tuning

Phase 0.6では **science calculation count = 0** を維持してください。

---

# 4. Production input adapter

Phase A専用のallowlist adapterを実装してください。

Phase Aから読み込めるproduction dataは、明示的に以下だけに限定してください。

1. saved H4 Hamiltonian
2. saved 13 ordered groups
3. saved CISD state
4. sector / basis / ordering metadata
5. current_m3 coefficients / sequence
6. fixed train/eval times
7. fixed numerical constants

以下はPhase A adapterからアクセス不能にしてください。

- exact state
- exact ground energyをtruthとして使う経路
- direct PF truth
- branch audit truth
- error decomposition
- controlled states
- saved exact proxy
- direct optimum
- past success/failure labels
- Phase B scoring artifact

既存loaderがこれらをまとめて読む設計なら、そのloaderを流用せず、**専用allowlist loader**を実装してください。

---

# 5. Source identity gate

production bytesをdecodeする前後で、

- file SHA-256
- expected blob identity
- array hash
- dtype
- shape
- ordered group identity
- group sequence
- Hamiltonian identity
- CISD identity
- sector metadata

をPhase 0.5のfreezeと照合してください。

不一致時は

`failed_source_identity`

として停止してください。

「数値的に同じだから再生成して使う」は禁止です。

---

# 6. Production PF backend

Phase 0.5 protocolで固定されたPF backendをproduction H4へ接続してください。

重要：

\[
W(t)=e^{-iHt}U_P(t)
\]

\[
W^\dagger(t)=U_P(t)^\dagger e^{+iHt}
\]

です。

**`W(-t)=W(t)^\dagger` と置かないでください。**

正負時刻は独立に構築してください。

## current_m3

Phase 0.5 protocolに固定されたcurrent_m3 sequenceをそのまま使用してください。

係数やstep orderingを再構成・最適化しないでください。

## backend

Phase 0.5でfreezeした

- scipy / Padé
- S2 block cache
- ordered group sequence

を維持してください。

---

# 7. PF backend preflight

production scienceを実行せずに、synthetic / mock inputで以下を確認してください。

- forward action
- adjoint action
- positive / negative time independence
- `U(-t)` vs `U(t)†` audit
- unitarity residual
- block ordering
- cache scope
- cold replayでcache共有されないこと
- action counter

production H4 arrayへ対するPF output vector自体は今回は生成しないでください。

production bytesのidentity checkまでで止めてください。

---

# 8. Response production adapter

Phase 0.5でfreeze済みの式をそのままproduction dimensionへ接続してください。

\[
E_\psi=\mathrm{Re}\langle\psi|H|\psi\rangle
\]

\[
Q=I-|\psi\rangle\langle\psi|
\]

\[
r=Q(H-E_\psi)|\psi\rangle
\]

\[
L=Q(H-E_\psi)Q
\]

\[
a_t=QA_t|\psi\rangle
\]

response basisは

\[
\mathcal Z_m
=
\mathrm{span}\{r,Lr,L^2r,\dots\}
\]

のArnoldi/Krylov implementation。

mは固定：

\[
m\in\{1,2,4,8\}
\]

- primary = 8
- 1/2/4 = diagnostic

---

# 9. Numerical rulesを変更しない

Phase 0.5の以下をそのままproduction implementationへ使用してください。

- complex128 / float64
- MGS exactly 2 passes
- psi projection
- deterministic phase fixing
- machine-precision-based rank threshold
- first rank failureでprefix stop
- replacement direction禁止
- third MGS pass禁止
- full residual LS
- thin SVD
- truncated SVD
- ridge禁止
- parameter search禁止

primary solveは

\[
B=LZ
\]

に対して、

\[
c=\arg\min_c\|a-Bc\|_2
\]

です。

\[
L_m=Z^\dagger LZ,\quad a_m=Z^\dagger a
\]

はdiagnosticのみ。

Galerkin solveへ切り替えないでください。

---

# 10. Response estimator

\[
z=Zc
\]

\[
\boxed{
g_{\rm resp}
=
g_{\rm base}
-
2\operatorname{Re}\langle z|r\rangle
}
\]

を維持してください。

Phase 0.6ではproduction H4についてこの値を実際に計算しないでください。

synthetic testとproduction execution pathの接続だけ行ってください。

---

# 11. Ritz comparator production adapter

同じsubspace informationから

\[
V=[\psi,Z_m]
\]

\[
H_m=V^\dagger HV
\]

を作り、lowest projected Ritz pairを求めるproduction pathを実装してください。

primary m=8。

m=1/2/4はdiagnostic。

production H4で実際のRitz stateを生成するscience runはまだ行わないでください。

small-matrix synthetic testで、

- Hermiticity gate
- tie handling
- deterministic phase
- zero-rank fallback

を確認してください。

---

# 12. Baseline / response / Ritz共通proxy interface

production implementationで、次の3 armが同じinterfaceを使えるようにしてください。

- A0: bare CISD
- A1: response m8
- A2: Ritz m8

diagnostic:

- response m1/2/4
- Ritz m1/2/4

A3 exact-state referenceはPhase B専用なので、Phase A production moduleからimport・参照できない設計にしてください。

---

# 13. Fit adapter

Phase 0.5でfreeze済みのfitをproduction prediction pathへ接続してください。

\[
f(t)=a_4t^4+a_6t^6
\]

- no intercept
- unweighted OLS
- column 2-norm scaling
- positive five training points primary
- same quality rule
- same condition number gate
- evenized / oddはdiagnostic

今回はproduction proxyを生成しないため、fit executionはsynthetic inputだけで確認してください。

---

# 14. Phase A artifact schema

science実行時にPhase Aが出すartifact schemaを、今回完全に固定してください。

最低限、

## Source

- protocol hash
- code hash
- source hash
- input array identities

## Basis

- requested m
- actual rank
- rank thresholds
- orthogonality residual
- basis build status

## Response

各time / m:

- g_base
- g_response
- d_norm
- relative residual
- z_norm
- effective SVD rank
- singular values
- SVD threshold
- condition number

## Ritz

- projected dimension
- projected Hermiticity residual
- Ritz eigenvalue
- proxy
- tie status

## Fit

- coefficients
- condition number
- fit status
- training residual

## Cost

全action counter。

## Noise

- first pass
- cold replay
- replay difference
- quality class

## Prediction

evaluation signed coordinateごとのfrozen prediction。

Phase A artifactにはtruth fieldを入れないでください。

---

# 15. Phase A freeze mechanism

将来science実行時は、

1. Phase A execution
2. artifact write
3. prediction SHA-256
4. source/code/protocol hashes
5. git commit
6. remote / local identity verification
7. 40-char commit freeze

まで完了しない限りPhase Bへ進めない設計にしてください。

Phase A artifactを後から上書きする方式は禁止です。

---

# 16. Phase B truth barrier

Phase B production readerは、

- frozen Phase A commit
- exact prediction blob
- prediction SHA-256
- protocol hash
- source identity

を確認しない限りtruthを読めないようにしてください。

Phase Bで読めるものはPhase 0.5 contract通り、

- saved direct truth: 12 evaluation coordinates
- saved exact proxy: 22 signed coordinates

のみ。

欠損・duplicate・identity mismatch・unreliable branchなら停止。

新truth取得は禁止。

Phase B scoring code自体は実装してよいですが、今回はtruthを開いて実行しないでください。

---

# 17. Cold replay

Phase 0.5 protocol通り、science時には1 complete cold replayを行います。

今回、

- independent basis rebuild
- independent PF backend reconstruction
- independent response solve
- independent Ritz solve
- independent proxy reconstruction

ができるcode pathを実装してください。

初回passから、

- basis cache
- PF matrix cache
- response factor
- Ritz state
- proxy vector

を共有しないこと。

source bytesそのものの再読込可否はprotocolに従ってください。

---

# 18. Action counter preflight

expected action countsとproduction code pathが一致することを、scienceを回さず静的・syntheticに確認してください。

nominal rank8 + diagnostics + cold replayでは、

- H matvec: 18
- PF forward: 220
- PF adjoint: 44
- response SVD factorization: 8
- response RHS solve: 176
- small Ritz solve: 8

がPhase 0.5のexpected countです。

rank stop時の式も確認してください。

counter mismatchがあればscience前に停止。

数値結果を見てcounter scopeを変えないこと。

---

# 19. Synthetic / integration tests

最低限以下を追加・維持してください。

## Input boundary

1. Phase A loaderがexact stateを読めない
2. Phase A loaderがdirect truthを読めない
3. Phase A loaderがcontrolled statesを読めない
4. hash mismatchでproduction load停止

## PF

5. forward ordering
6. adjoint ordering
7. ±time independent construction
8. `W(-t)`を`W†(t)`として使わない
9. unitarity gate
10. cache boundary

## Response

11. full residual LS
12. projected Galerkinと異なるsynthetic反例
13. identity observableでcorrection zero
14. exact input eigenstateでcorrection zero
15. commuting counterexampleで非zero correctionを許容
16. rank stop
17. SVD truncation
18. residual convergence calculation

## Ritz

19. same prefix information
20. Hermiticity gate
21. tie rule
22. zero rank fallback

## Fit

23. all arms same fit
24. invalid quality → not_identifiable
25. no truth dependency

## Truth barrier

26. Phase A commit/hashなしでPhase B停止
27. altered prediction blobでPhase B停止
28. missing truth rowで停止
29. duplicate truth rowで停止

## Cost

30. nominal action count matches expected contract
31. rank-stop action count matches formula
32. cold replay actions are counted again

既存22 testsも維持してください。

---

# 20. Production data preflight

重要です。

今回はproduction H4 scienceを行いませんが、次のpreflightは行って構いません。

### 許可

- repository source file existence確認
- byte/hash確認
- metadata確認
- array header / dtype / shape identity確認
- allowlist path resolution確認
- loaderが禁止fieldを読まないことの確認

### 禁止

- H4 Hamiltonianを使ったmatvec
- H4 groupsを使ったPF evolution
- H4 CISDからresponse basis構築
- H4 proxy計算
- H4 Ritz solve
- H4 fit

つまりproduction inputを**identity確認のためにdecodeする最小範囲**は許可しますが、科学量を生成する演算は0にしてください。

---

# 21. `production_execution_ready`

Phase 0.6完了時に、

`production_execution_ready=true/false`

を判定してください。

true条件：

- adapter complete
- source identity complete
- truth barrier complete
- backend integration complete
- counter contract complete
- cold replay path complete
- all preflight tests pass
- science action count = 0
- unresolved implementation issue = 0

trueはscience実行許可を意味しません。

---

# 22. 必須成果物

新しいartifact directoryを作ってください。

例：

`artifacts/pf_first_study_response_pilot_phase06_preflight_20261006/`

最低限以下を保存してください。

1. `README.md`
2. `production_adapter_design.md`
3. `phase_a_schema.json`
4. `phase_b_truth_barrier.md`
5. `preflight_protocol.json`
6. `expected_vs_implemented_action_counts.json`
7. `production_source_identity.json`
8. `truth_access_audit.json`
9. `cold_replay_design.md`
10. `preflight_tests.log`
11. `verification.json`
12. `source_manifest.json`
13. `publication_manifest.json`
14. `GO_NO_GO_FOR_H4_SCIENCE.json`

implementation code / testsもcommitしてください。

---

# 23. `GO_NO_GO_FOR_H4_SCIENCE.json`

最低限、

- `phase06_complete`
- `science_action_count`
- `production_execution_ready`
- `science_authorized=false`
- `source_identity_passed`
- `truth_barrier_passed`
- `action_count_contract_passed`
- `cold_replay_ready`
- `all_tests_passed`
- `unresolved_issues`
- `exact_H4_science_actions_if_approved`

を含めてください。

---

# 24. 最終報告

完了時は次だけ簡潔に報告してください。

1. production adapter実装状況
2. truth barrier状況
3. preflight test数 / 結果
4. expected action countsとの一致
5. production source identity結果
6. `production_execution_ready=true/false`
7. unresolved issue
8. trueなら、次のscience実行で何を何回計算するか
9. science action countが0であること
10. commit / branch / push状況

---

# 25. 停止条件

Phase 0.6完了後は必ず停止してください。

**H4 Phase A scienceを自動開始しないでください。**

特に、

- production_execution_ready=true
- tests all pass
- source identity pass

であっても、science実行には別途GPT/ユーザー承認が必要です。

commit/pushして停止してください。

第1研究formal result、Phase 0、Phase 0.5、S4の結果は変更しないでください。
