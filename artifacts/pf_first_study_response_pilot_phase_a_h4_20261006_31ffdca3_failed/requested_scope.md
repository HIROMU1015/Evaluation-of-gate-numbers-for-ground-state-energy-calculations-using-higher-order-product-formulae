第1研究のresponse-corrected calibration pilotについて、**H4 Phase A science execution** を実行してください。

今回は **Phase Aのみ** です。

**Phase Bのsaved direct truth / exact proxyは絶対に開かないでください。**

Phase Aのprediction・fit・numerical diagnostics・action countsをfreezeし、commit/hash/remote identityを確認した時点で停止してください。

---

# 0. 起点

Phase 0.6は以下で完了しています。

- Repository
  `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

- Branch
  `pf-first-study-response-pilot-phase06-preflight-20261006`

- Commit
  `6fae17723f888a62a998f90436516785a67651c6`

- Artifact
  `artifacts/pf_first_study_response_pilot_phase06_preflight_20261006/`

Phase 0.6では、

- production adapter
- source identity
- PF backend
- response / Ritz
- fit
- truth barrier
- cold replay
- action counter

までproduction接続済みで、

`production_execution_ready=true`

です。

今回、GPT/ユーザー判断として

\[
\boxed{\text{H4 Phase A science executionのみ承認}}
\]

します。

**Phase Bは未承認です。**

---

# 1. Normative authority

以下をauthorityとして使用してください。

## Phase 0.5

1. `artifacts/pf_first_study_response_pilot_phase05_20261006/response_pilot_protocol.json`
2. `response_pilot_protocol.md`
3. `algorithm_design.md`
4. `cost_accounting.md`
5. `user_amendments.json`

特に、

`response_pilot_protocol.json`

がscience specificationのnormative authorityです。

## Phase 0.6

6. `artifacts/pf_first_study_response_pilot_phase06_preflight_20261006/README.md`
7. `verification.json`
8. `GO_NO_GO_FOR_H4_SCIENCE.json`
9. `production_source_identity.json`
10. `expected_vs_implemented_action_counts.json`
11. `truth_access_audit.json`
12. `phase_a_schema.json`
13. `preflight_protocol.json`

science specification、threshold、m、fit、outcome logicを変更しないでください。

---

# 2. 今回のscience scope

対象は固定されています。

- System: H4
- Geometry: 元Phase Bと同一
- Basis: STO-3G
- Sector: 元Phase Bと同一
- Input state: saved CISD
- PF: `current_m3`
- Hamiltonian / ordered groups: saved production source
- Response m:
  - primary: 8
  - diagnostics: 1, 2, 4
- Ritz m:
  - primary: 8
  - diagnostics: 1, 2, 4

## Training absolute times

\[
T_{\rm train}
=
\{0.10,0.15,0.20,0.25,0.30\}
\]

## Evaluation absolute times

\[
T_{\rm eval}
=
\{0.125,0.175,0.225,0.275,0.35,0.40\}
\]

## Signs

正負を独立に実行。

合計

- training signed coordinates: 10
- evaluation signed coordinates: 12
- total signed coordinates: 22

です。

---

# 3. 今回許可するscience actions

Phase 0.6で固定したPhase A actionだけを許可します。

nominal rank8・initial pass + full cold replayでは、

- H matvec: 18
- PF forward: 220
- PF adjoint: 44
- response SVD factorization: 8
- response RHS solve: 176
- small projected Ritz eigensolve: 8
- fit: 27

です。

actual retained rankが8未満の場合は、凍結済みrank-stop formulaに従ってactual countを下げてください。

**別direction追加やm増加は禁止です。**

---

# 4. 今回禁止するもの

Phase A中は以下を禁止します。

- saved direct PF truth access
- saved exact proxy access
- exact ground state access
- exact ground energyをalgorithm inputへ使用
- error_decomposition.csvのtruth情報参照
- branch_auditのdirect truth参照
- controlled state参照
- D4 / D6 / D8参照
- past H4 success / failure label参照
- direct PF eigensolve
- Schur solve
- full H ground eigensolve
- new truth
- new molecule / geometry / PF / state
- gamma変更
- fit変更
- m変更
- rank threshold変更
- SVD cutoff変更
- regularization追加
- response formula変更
- Ritz comparator変更
- outcome rule変更
- numerical resultを見た救済処理

Phase A moduleからPhase B readerを呼ばないでください。

---

# 5. Science authorization record

Phase 0.6で実装したauthorization mechanismに従い、

**Phase Aのみ有効なscience authorization record**

を作成してください。

このrecordは、

- exact repository
- exact base commit
- exact protocol SHA
- Phase A only
- truth access prohibited
- H4/current_m3/CISD only
- fixed 22 coordinates

を明記してください。

Phase B authorizationを含めないでください。

---

# 6. Source identity gate

science action前に必ず、

- H4 Hamiltonian
- 13 ordered groups
- CISD state
- dtype
- shape
- canonical hash
- group order
- sector metadata
- current_m3 identity
- protocol hash
- code hash

を確認してください。

Phase 0.6のidentityと一致しなければscienceを開始せず停止してください。

---

# 7. Response basis construction

凍結仕様どおり、

\[
E_\psi
=
\mathrm{Re}\langle\psi|H|\psi\rangle
\]

\[
Q=I-|\psi\rangle\langle\psi|
\]

\[
r=Q(H-E_\psi)|\psi\rangle
\]

を構築し、

\[
\mathcal Z_m
=
\operatorname{span}
\{r,Lr,L^2r,\ldots\}
\]

\[
L=Q(H-E_\psi)Q
\]

のArnoldi/Krylov basisを作ってください。

数値規則：

- complex128
- MGS exactly 2 passes
- deterministic phase rule
- frozen rank threshold
- first rejected directionでstop
- replacement directionなし
- m追加なし

actual retained rankを必ず保存してください。

---

# 8. Response solve

各signed timeで、

\[
A_t
=
\frac{W(t)-W^\dagger(t)}{2it}
\]

\[
a_t=QA_t|\psi\rangle
\]

を作り、

\[
B_m=LZ_m
\]

に対して、

\[
c_m
=
\arg\min_c
\|a_t-B_mc\|_2
\]

をfull residual truncated-SVDで解いてください。

primary estimator:

\[
g_{\rm resp}^{(m)}
=
g_{\rm base}
-
2\operatorname{Re}\langle z_m|r\rangle
\]

\[
z_m=Z_mc_m.
\]

`L_m=Z†LZ`によるGalerkin solveへ変更しないでください。

---

# 9. Response diagnostics

各22 signed coordinate ×各有効mについて少なくとも、

- requested m
- actual prefix rank
- SVD effective rank
- singular values
- SVD threshold
- retained condition number
- full condition number / singular status
- `||z||`
- `||d||`
- relative response residual
- projected `L_m`
- projected `a_m`
- numerical status

を保存してください。

\[
d=a-Lz
\]

です。

response residualをaccuracy certificateとは呼ばないでください。

---

# 10. Ritz comparator

同じKrylov basisを使い、

\[
V_m=[\psi,Z_m]
\]

\[
H_m=V_m^\dagger HV_m
\]

のlowest projected Ritz stateを作ってください。

- same prefix information
- same retained rank
- m=8 primary
- m=1/2/4 diagnostic

です。

small projected matrixのHermiticity / tie / deterministic phase ruleはprotocolのまま。

---

# 11. PF / echo computation

Phase 0.6でfreezeしたbackendを変更せず使用してください。

\[
W(t)=e^{-iHt}U_P(t)
\]

\[
W^\dagger(t)=U_P(t)^\dagger e^{+iHt}
\]

です。

正負時刻を独立構築してください。

`W(-t)=W(t)^\dagger`

という置換は禁止です。

---

# 12. Phase A arms

以下を計算してください。

## A0 baseline

saved CISD state上のbare proxy。

## A1 response

m=8 primary。

m=1/2/4 diagnostics。

## A2 Ritz

m=8 primary。

m=1/2/4 diagnostics。

## A3

**Phase Aでは計算・読み込み禁止。**

exact proxyはPhase B referenceのみです。

---

# 13. Cold replay

Phase 0.5/0.6でfreezeされたcomplete cold replayを必ず実行してください。

cold replayでは、

- response basis
- H actions
- PF backend
- response solves
- Ritz states
- proxies

を初回passから独立に再構築してください。

cacheを初回passと共有しないでください。

cold replay actionをすべて再計上してください。

---

# 14. Noise / quality

protocolのnoise ruleを変更しないでください。

各arm / timeで、

- first proxy
- cold replay proxy
- replay difference
- PF unitarity contribution
- numerical noise
- rho
- quality class

を保存してください。

response residualをnoise estimateへ混ぜないでください。

---

# 15. Fit

cold replay確認後、frozen ruleでfitしてください。

各arm / mについて、

\[
f(t)=a_4t^4+a_6t^6
\]

主fit：

positive 5 training points。

ルール：

- no intercept
- unweighted OLS
- column 2-norm scaling
- same condition-number gate
- same quality requirement

diagnosticとして、

- evenized 4/6
- odd 5/7

も保存してください。

合計fit scopeはprotocolどおり27。

---

# 16. Evaluation predictions

evaluation truthはまだ開かず、

12 signed evaluation coordinatesについて、

各arm / mの

- frozen fitted prediction
- sign
- absolute predicted magnitude
- fit status
- proxy quality
- response numerical diagnostics

を保存してください。

Phase A時点では、

- direct error
- total error
- underestimation
- improvement
- outcome A/B/C/D

を計算しないでください。

truthが必要だからです。

---

# 17. Phase Aで確認するnumerical gates

Phase A終了前に、少なくとも以下を報告してください。

## Basis

- actual max rank
- prefix stop有無
- orthogonality residual

## Response

- SVD rank
- condition numbers
- max / median `||z||`
- response residual
- residual convergence across m

## Ritz

- projected dimensions
- projected Hermiticity
- Ritz eigenvalues
- tie status

## PF

- maximum unitarity residual
- ±time audit
- cold replay

## Fit

各arm/mの

- fit_ok / not_identifiable
- a4
- a6
- scaled condition
- training residual

---

# 18. Important: Phase Aで科学的成功判定をしない

Phase Aだけを見て、

- response successful
- Ritz superior
- state correction useful
- Outcome A/B/C/D

などを確定しないでください。

Phase Aで判断してよいのは、

> **numerically valid / invalid / unstable / fit-identifiable / not-identifiable**

までです。

truth-dependentなaccuracy判断は禁止です。

---

# 19. Phase A artifact

Phase 0.6でfreezeされたstrict schemaに従い、新しいcreate-only artifact directoryへ保存してください。

例：

`artifacts/pf_first_study_response_pilot_h4_phase_a_20261006_<id>/`

最低限、

1. `README.md`
2. `protocol.json`
3. `authorization.json`
4. `source_manifest.json`
5. `source_identity.json`
6. `action_counts.json`
7. `basis_diagnostics.json/csv`
8. `response_diagnostics.csv`
9. `ritz_diagnostics.csv`
10. `proxy_values.csv`
11. `fit_results.csv`
12. `predictions.json`
13. `prediction.sha256`
14. `cold_replay_audit.json`
15. `numerical_gates.json`
16. `verification.json`
17. `publication_manifest.json`
18. `PHASE_A_FROZEN`

を保存してください。

binary state/vector/basis/response arraysはpublic artifactに入れず、既存privacy policyに従ってください。

---

# 20. Action-count audit

actual retained rankに応じて、expected formulaと実測counterが一致することを確認してください。

nominal rank8なら、

- H matvec = 18
- PF forward = 220
- PF adjoint = 44
- response SVD = 8
- response RHS = 176
- Ritz solve = 8
- fit = 27

です。

rank stop時はPhase 0.6のformulaに従う。

counter mismatch時はPhase Aを`failed_action_accounting`として停止し、prediction freezeしないでください。

---

# 21. Phase A freeze

全numerical/source/action gatesが通った場合のみ、

1. artifact完成
2. prediction SHA-256確定
3. protocol/source/code hash確定
4. `PHASE_A_FROZEN`作成
5. git commit
6. push
7. remote commit SHA確認
8. remote blob/hash確認

を行ってください。

full 40-char commit SHAを保存してください。

prediction artifactをfreeze後に変更しないでください。

---

# 22. Phase Bを開かない

非常に重要です。

Phase A commit/hash/remote verificationが完了しても、

**今回はPhase Bを実行しないでください。**

以下を読まないでください。

- saved direct truth 12 rows
- saved exact proxy 22 rows
- A3 exact reference
- truth-containing CSV

Phase A完了後に停止してください。

---

# 23. Phase A終了時の判断

Phase A終了時に、次の3択を報告してください。

### `PHASE_A_NUMERICALLY_READY`

- source / action / numerical gates pass
- primary response / Ritz / baseline fitsが評価可能
- frozen prediction作成済み

### `PHASE_A_NUMERICALLY_WEAK`

- 実行自体は完了したが、
  - low retained rank
  - poor response conditioning
  - residual nonconvergence
  - primary fit not_identifiable
  などtruth前にmethod viability上の重要な問題がある

ただしpredictionはprotocol上freeze可能な場合のみfreeze。

### `PHASE_A_FAILED`

- identity
- action count
- numerical gate
- cold replay
- artifact integrity

などのhard failure。

---

# 24. 最終報告

Phase A完了後、次を簡潔に報告してください。

1. actual retained Krylov rank
2. primary response SVD rank / condition range
3. response residual convergence状況
4. primary Ritz dimension / numerical status
5. baseline / response / Ritzのfit status
6. cold replay最大差
7. actual action counts
8. prediction SHA-256
9. Phase A commit SHA
10. remote/blob verification
11. `PHASE_A_NUMERICALLY_READY / WEAK / FAILED`
12. saved truth access count = 0
13. Phase B未実行であること

---

# 25. 停止条件

Phase A freeze・commit・push・remote verification後に必ず停止してください。

**Phase Bへ自動的に進まないでください。**

次の判断はGPT/ユーザーが行います。

第1研究formal result、Phase 0、Phase 0.5、Phase 0.6、S4の結果は変更しないでください。
