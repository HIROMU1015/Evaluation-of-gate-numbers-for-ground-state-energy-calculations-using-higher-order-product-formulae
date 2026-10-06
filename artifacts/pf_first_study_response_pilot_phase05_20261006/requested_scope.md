第1研究のPhase 0 feasibility auditを踏まえ、次段の **response-corrected calibration pilot** の仕様を設計・事前固定してください。

今回は **Phase 0.5：algorithm / comparator / metric / protocol design** のみです。

**science calculationはまだ実行しないでください。**

---

# 0. Phase 0結果と今回の位置付け

Phase 0は以下で完了しています。

- Repository:
  `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- Branch:
  `pf-first-study-phase0-feasibility-20261006`
- Commit:
  `1b7b2fc959185ca1be06581682a67d28e02db21c`
- Artifact:
  `artifacts/pf_first_study_phase0_feasibility_20261006/`

Phase 0の推奨は

`GO_response_pilot`

でした。

主なevidenceは、

- H4 fit_ok/resolved 588行でoracle state-removalによりabsolute prediction error総和が89.2808%減少
- H4 same-sign underestimated 356行中340行でstate componentが最大のunsafe寄与
- H4 CISDだけでもoracle state-removalで98.9020%減少
- N2/CO same-time calibration headroom 7.20–13.79%
- HFはsame-PF/cap内のmaximum saving upper boundが約1.58–1.66%でtime-domain-limited
- state removal後はH4 527/588行でfit componentが次の最大residual

でした。

ただし、

- 実際にoracle-freeなstate correctionが可能か
- correction後にfitまで含むtotal calibration errorが改善するか
- ordinary state improvementよりresponse correctionが有利か
- resource improvementにつながるか

は未検証です。

今回の目的は、

> **H4 / current_m3 / CISD に限定した最小response pilotを、結果を見る前に実行可能な仕様へ落とし込み、比較対象・数式・数値gate・cost accounting・停止規則までfreezeすること**

です。

---

# 1. 今回の実行境界

今回は設計とprotocol freezeのみです。

以下は禁止です。

- 新規Hamiltonian生成
- Hamiltonian matvecによるscience data取得
- 新規PF action
- 新規ground solve
- 新規Schur/eigensolve
- 新規direct truth
- 新規state preparation
- response vectorの実計算
- Krylov basisの実計算
- Ritz stateの実計算
- 新しいfitのscience実行
- evaluation truthを使ったalgorithm tuning
- m値、regularization、thresholdのpost-hoc tuning
- N2/CO/HFへのscience extension
- 新PF探索
- 新分子・geometry追加
- gamma変更
- 第1研究formal result変更

既存artifactはread-onlyとしてください。

今回は

`protocol / implementation skeleton / synthetic tests / source identity / action accounting design`

までです。

---

# 2. Authority

まず以下を読んでください。

## 第1研究formal authority

1. `docs/current_research_status.md`
2. `PF_first_study_paper_claim_ledger_20260926.md`
3. `PF_first_study_final_synthesis_20260925.md`
4. `PF_first_study_final_decision_20260925.json`
5. `PF_first_study_protocol_20260925.md`

## Phase 0

6. `artifacts/pf_first_study_phase0_feasibility_20261006/README.md`
7. `artifacts/pf_first_study_phase0_feasibility_20261006/report.md`
8. `artifacts/pf_first_study_phase0_feasibility_20261006/feasibility_decision.json`
9. `artifacts/pf_first_study_phase0_feasibility_20261006/oracle_state_removal.csv`
10. `artifacts/pf_first_study_phase0_feasibility_20261006/budget_direction_attribution.csv`
11. `artifacts/pf_first_study_phase0_feasibility_20261006/mechanism_and_budget_summary.csv`

## 元H4 protocol / source

12. `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/protocol.json`
13. `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/error_decomposition.csv`
14. `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/observables.csv`
15. `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/branch_audit.csv`

古いdraftではなく、上記をauthorityとしてください。

---

# 3. Pilotの研究質問

次のpilotで答える研究質問を固定してください。

## RQ1

近似CISD状態をそのまま使うbare PF calibrationに比べ、

> **response-corrected observable estimatorは、exact-ground calibration targetを変えずにstate-induced biasを減らせるか。**

## RQ2

response correctionによりstate-level proxy errorが減った場合、

> **同じfixed fit ruleを再適用した後のtotal finite-time calibration errorも減るか。**

Phase 0ではstate componentだけをoracle除去しfitを固定したため、この点は未検証です。

## RQ3

同じ追加subspace informationを使って普通にstateを改善する方法と比較したとき、

> **response correction固有の利点が存在するか。**

## RQ4

response correctionは、

- absolute prediction error
- PF error magnitude underestimation
- sign crossing

のどれを改善し、どれを改善しないか。

---

# 4. Pilot対象を固定

対象は次だけにしてください。

- system: `H4`
- Hamiltonian: 元Phase Bの保存済みH4 Hamiltonian
- state: `CISD`
- PF: `current_m3`
- basis / sector / constant policy / qubit ordering:
  元Phase Bと完全一致

新しいPF、状態、分子を追加しないでください。

## Training times

\[
T_{\rm train}
=
\{0.10,0.15,0.20,0.25,0.30\}\ {\rm Ha}^{-1}
\]

## Evaluation times

\[
T_{\rm eval}
=
\{0.125,0.175,0.225,0.275,0.35,0.40\}\ {\rm Ha}^{-1}
\]

## Signs

\[
t\in\{\pm |t|\}
\]

元Phase Bと同じ正負branch policyを使用してください。

evaluation truthはprediction freeze後にのみ開くprotocolにしてください。

既存truthを再利用してよいですが、algorithm設計・parameter選択へevaluation truthを使用しないでください。

---

# 5. Bare calibration observable

元のdecision proxyと同じ量を使用します。

PF error operatorを

\[
W_P(t)
\]

とし、

\[
A_P(t)
=
\frac{W_P(t)-W_P(t)^\dagger}{2it}
\]

と定義します。

CISD stateを

\[
|\psi\rangle
\]

として、

\[
g_{\rm base}(P,t)
=
\langle\psi|A_P(t)|\psi\rangle
\]

をbaseline observableとします。

保存実装との一致を確認し、

\[
g_{\rm base}
=
\frac{\operatorname{Im}\langle\psi|W_P(t)|\psi\rangle}{t}
\]

と数値的に同じ定義になることをsynthetic/unit testしてください。

---

# 6. Response-corrected estimator

今回の主algorithm candidateは以下です。

CISD状態について、

\[
E_\psi
=
\langle\psi|H|\psi\rangle
\]

\[
Q
=
I-|\psi\rangle\langle\psi|
\]

\[
r
=
Q(H-E_\psi)|\psi\rangle
\]

を定義します。

各PF/timeについて、

\[
a_t
=
QA_P(t)|\psi\rangle
\]

とします。

さらに、

\[
L
=
Q(H-E_\psi)Q
\]

を使います。

response vector \(z_t\) はfull-space inverseではなく、固定したsmall response subspace

\[
\mathcal Z_m
\]

内のleast-squares問題

\[
\boxed{
z_t^{(m)}
=
\arg\min_{z\in\mathcal Z_m}
\|
a_t-Lz
\|_2
}
\]

で求める仕様にしてください。

response-corrected estimatorは

\[
\boxed{
g_{\rm resp}^{(m)}(t)
=
g_{\rm base}(t)
-
2\operatorname{Re}
\langle z_t^{(m)}|r\rangle
}
\]

です。

---

# 7. Response subspace

response subspaceは結果後に変更しないよう、今回freezeしてください。

候補はresidual Krylov subspace

\[
\mathcal Z_m
=
\operatorname{span}
\{
r,
QHr,
QH^2r,
\dots,
QH^{m-1}r
\}
\]

とします。

ただし、実装時は数値安定性のためorthonormalizationしてください。

## 固定m

\[
m\in\{1,2,4,8\}
\]

としてください。

- primary response arm: `m=8`
- `m=1,2,4`: convergence diagnosticのみ
- evaluation resultを見てmを変更しない

こと。

basis constructionはtime-independentとし、11 absolute timesで共通利用してください。

---

# 8. Numerical construction

以下をprotocolで明示してください。

## 8.1 Projection

各basis vectorはCISD stateに対して直交化し、

\[
Qv=v-|\psi\rangle\langle\psi|v\rangle
\]

を適用する。

## 8.2 Orthonormalization

modified Gram-SchmidtまたはQRのどちらを採用するか固定してください。

再直交化の有無も固定してください。

## 8.3 Rank deficiency

新vector normが事前固定したnumerical threshold未満なら、

- 勝手に別directionを追加しない
- 実効rankを記録
- そのprefixで停止

すること。

thresholdはmachine precisionとvector norm scaleに基づいて事前設定し、science resultを見て変更しないでください。

## 8.4 Least-squares

subspace basisを \(Z_m\) として、

\[
L_m
=
Z_m^\dagger L Z_m
\]

\[
a_m
=
Z_m^\dagger a_t
\]

を作る。

直接inverseを使わず、SVDまたはrank-revealing least squaresを使う仕様にしてください。

## 8.5 Small singular values

regularizationを入れる場合は、今回のprotocolで完全に固定してください。

できればpilotでは、

> singular-value threshold以下をtruncated SVDで除外

とし、thresholdをrelative matrix norm / machine precisionから決める方針を推奨します。

結果依存のridge parameter searchは禁止です。

---

# 9. Response residual

各time / mについて、

\[
d_t^{(m)}
=
a_t-Lz_t^{(m)}
\]

を計算し、

\[
R_{\rm resp}
=
\frac{\|d_t^{(m)}\|}
{\max(\|a_t\|,\epsilon_{\rm num})}
\]

を保存してください。

これはcertificateではなく、response equationをどこまで解けたかのnumerical diagnosticです。

mに対して、

- \(\|d\|\)
- relative residual
- \(\|z\|\)
- effective rank
- condition number

を保存してください。

---

# 10. Exact-target invariance test

response estimatorの理論上重要な性質として、

\[
X
=
|z\rangle\langle\psi|
-
|\psi\rangle\langle z|
\]

\[
\widetilde A
=
A-[H,X]
\]

を考えます。

任意のexact eigenstate \(|E_n\rangle\)について、

\[
\langle E_n|[H,X]|E_n\rangle=0
\]

なので、

\[
\langle E_n|\widetilde A|E_n\rangle
=
\langle E_n|A|E_n\rangle
\]

です。

この恒等式をsynthetic matrix testで必ず検証してください。

ただしscience execution時にexact groundをresponse estimatorの入力には使わないこと。

exact stateはPhase B scoringのみです。

---

# 11. Equal-information state-improvement comparator

response correctionだけを評価してはいけません。

同じKrylov informationを使ったstate-improvement comparatorを固定してください。

subspace

\[
\mathcal V_m
=
\operatorname{span}
\{
|\psi\rangle,
\mathcal Z_m
\}
\]

にHamiltonianを射影し、

\[
H_m=V_m^\dagger HV_m
\]

を作る。

このsmall projected Hamiltonianのlowest Ritz pairを求め、

\[
|\psi_{\rm Ritz}^{(m)}\rangle
\]

を作ります。

比較proxyは

\[
g_{\rm Ritz}^{(m)}(t)
=
\langle
\psi_{\rm Ritz}^{(m)}
|
A_P(t)
|
\psi_{\rm Ritz}^{(m)}
\rangle.
\]

primary state-improvement armも `m=8`。

`m=1,2,4` はconvergence diagnosticとしてください。

---

# 12. 重要：情報・actionのfair comparison

response armとRitz armで、

- H matvec
- PF action
- state/vector storage
- small dense solve
- orthogonalization
- extra observable evaluation

を別々に数えてください。

単に「同じmだからequal cost」と扱わないこと。

特に、

response methodは同じCISD state上のPF actionを使える一方、

Ritz-state methodは新しいstateに対して \(A_t\) expectationを取るため、
追加PF actionが必要になる可能性があります。

この差を隠さないでください。

---

# 13. Pilot arms

最低限以下を比較してください。

## A0: baseline

original CISD calibration

\[
g_{\rm base}
\]

## A1: response

\[
g_{\rm resp}^{(8)}
\]

## A2: Ritz state improvement

\[
g_{\rm Ritz}^{(8)}
\]

## A3: exact-state oracle

元保存済みexact-ground proxy。

scoring/referenceのみ。

algorithm入力には使用禁止。

## Diagnostics

A1/A2について

\[
m=1,2,4
\]

も保存。

phase-average controlled-state resultはPhase 0のmechanism referenceとして引用してよいですが、今回のoperational armには追加しないでください。

---

# 14. Fit rule

非常に重要です。

response/Ritzでtraining proxyが変わるので、それぞれ独立に同じ固定fitを再実行するprotocolにしてください。

元Phase Bと同じ、

\[
f(t)
=
a_4t^4+a_6t^6
\]

を使用してください。

- no intercept
- same training times
- same positive/evenized policy
- same design scaling
- same numerical validity rule

を使用。

baseline / response / Ritzでfit ruleを変えないこと。

fit結果として、

- \(a_4\)
- \(a_6\)
- condition number
- training residual
- model status

を保存してください。

---

# 15. Evaluation metrics

## 15.1 Point/proxy error

\[
E_{\rm state-like}
=
g_{\rm method}-g_{\rm exact}
\]

ただしこれはmechanism diagnostic。

## 15.2 Total prediction error

evaluation timeで、

\[
E_{\rm total}^{\rm method}
=
\hat f_{\rm method}(t)
-
\delta_{\rm direct}(t)
\]

を主metricとしてください。

## 15.3 Absolute total error

\[
|E_{\rm total}^{\rm method}|
\]

## 15.4 Underestimation

\[
u_{\rm method}
=
|\delta_{\rm direct}|
-
|\hat f_{\rm method}|
\]

## 15.5 Positive underestimation

\[
u_+
=
\max(0,u)
\]

## 15.6 Sign crossing

\[
\operatorname{sgn}(\hat f)
\neq
\operatorname{sgn}(\delta)
\]

を別に数えてください。

---

# 16. Primary aggregate metrics

evaluation 6 absolute times ×両signについて、

各armで少なくとも以下を集計してください。

### Total absolute prediction error

\[
S_{\rm abs}
=
\sum_{t\in T_{\rm eval,\pm}}
|
E_{\rm total}(t)
|
\]

### Positive underestimation severity

\[
S_{\rm under}
=
\sum_t
\max(0,u(t))
\]

### Worst-case absolute error

\[
E_{\max}
=
\max_t |E_{\rm total}(t)|
\]

### Sign crossing count

### improved / worsened row count

### response residual statistics

### information/action cost

meanだけに依存せず、全12 evaluation rowsを保存してください。

---

# 17. Primary success logic

今回はmechanism pilotなので、結果後に数値thresholdを追加しないでください。

以下の論理判定を事前固定してください。

## Outcome A: response_specific_support

以下をすべて満たす場合：

1. responseでbaselineより
   \[
   S_{\rm abs}
   \]
   が低下
2. responseでbaselineより
   \[
   S_{\rm under}
   \]
   が低下
3. m増加に対してresponse residualが概ね収束方向
4. responseがRitz comparatorに対し、
   少なくとも
   - calibration error
   - unsafe severity
   - action cost
   の組で独自の利点を示す

→ response-specific algorithmic follow-upを支持。

## Outcome B: generic_state_improvement

responseもRitzもbaselineより改善するが、
response固有の利点がない。

→ 「state improvement is useful」は支持するが、
response-specific noveltyは弱い。

## Outcome C: point_only

proxy/state-level errorは改善するが、
refit後のtotal prediction errorやunderestimationが改善しない。

→ Phase 0で予想されたfit bottleneckが顕在化。
resource methodへは進まない。

## Outcome D: no_benefit

response / Ritzともにbaselineをmaterialに改善しない、
または数値的に不安定。

→ state-correction algorithm方向を停止候補。

---

# 18. “material”という語の扱い

結果後に5%、10%などの新しいthresholdを勝手に作らないでください。

今回のpilotでは、

- continuous ratios
- absolute values
- rowwise results
- action counts

を提示してください。

resource-stageへ進むためのquantitative thresholdは、
pilot結果を見た後にfuture preregistrationとして別途決めます。

---

# 19. Synthetic tests

science実行前に、少なくとも以下をsynthetic testしてください。

1. exact eigenstateではresponse correctionがtarget expectationを変えない
2. \(A\) がHと可換なら不要な補正を生成しない
3. known 2×2系でfull response subspaceが一次state sensitivityを除く
4. truncated responseでresidualが正しく計算される
5. rank-deficient Krylov basisで停止規則が働く
6. sign crossing attributionをcomponentwiseに行わない
7. baseline / response / Ritzでfit ruleが同一
8. evaluation truthがPhase A prediction builderへ流入できない
9. source hash不一致で停止
10. science action counterがPhase 0.5では0のまま

---

# 20. Implementation skeleton

実際のscienceを回さず、以下のコード経路だけ作成してください。

例えば、

- `build_response_basis(...)`
- `solve_response_least_squares(...)`
- `compute_response_proxy(...)`
- `solve_ritz_state(...)`
- `compute_proxy_for_state(...)`
- `fit_two_term_model(...)`
- `score_saved_truth(...)`

など。

synthetic/random small matricesでtest可能にしてください。

H4 production arraysを読み込んで実計算する処理は、
science authorization前には呼ばないでください。

production runnerには、

`--phase-a`

`--phase-b`

のような明確なtruth boundaryを設けることを推奨します。

---

# 21. Phase A / Phase B境界

## Phase A

入力可能：

- saved H4 Hamiltonian
- saved CISD state
- current_m3 definition
- fixed train/eval time list
- epsilon / beta
- algorithm parameters frozen in this protocol

Phase Aで作るもの：

- response basis
- response proxy training/evaluation prediction
- Ritz comparator prediction
- fitted coefficients
- frozen predictions
- hashes
- action counts

ただしevaluation direct truthは開かない。

## Phase B

Phase A commit/hashを固定後に、

既存保存済みdirect truthだけを読み、

- total error
- underestimation
- sign crossing
- outcome

を採点する。

predictionを変更しない。

---

# 22. Cost accounting

次段で必ず必要になるため、今回のprotocolに以下のcounterを定義してください。

## State/Hamiltonian side

- `H_matvec_count`
- `projection_count`
- `orthogonalization_count`
- `response_basis_dimension`
- `response_effective_rank`
- `small_dense_response_solve_count`
- `small_dense_ritz_eigh_count`

## PF side

- `PF_forward_action_count`
- `PF_adjoint_action_count`
- `unique_PF_time_coordinate_count`
- `PF_action_on_original_state_count`
- `PF_action_on_ritz_state_count`

## Truth side

- `new_direct_truth_count`
- `saved_direct_truth_read_count`

pilotではnew direct truth = 0の予定。

## Preparation/storage

- original state reuse
- new vector/state preparation count
- stored response vector count

Wall time/RSSを計測する場合も、
action countとは別に保存してください。

---

# 23. Novelty review

今回のPhase 0.5で、先行研究とのnovelty positioningも整理してください。

少なくとも以下を調べてください。

- zero-variance / zero-bias improved estimators
- response-property / coupled-perturbed methods
- quantum subspace expansion / subspace diagonalization
- eigenstate property correction
- Trotter / product-formula eigenvalue error estimation
- Trotter error mitigation / extrapolation
- perturbative corrections to approximate eigenstates or observables

目的は「似たものがない」と証明することではなく、

> 今回のresponse-corrected finite-time PF calibrationのどこを新規性候補として置けるか

を限定することです。

現時点では、

- commutator expectationがeigenstateで0
- response equation
- Krylov subspace
- Ritz improvement

自体を新規性とは扱わないでください。

新規性候補は、

> **finite-time PF error calibrationに特化して、
> approximate-state biasをresponse correctionで抑え、
> ordinary state improvementとfair comparisonし、
> QPE budget underestimationまで評価する統合方法**

です。

これが既存研究と十分区別できるかをレビューしてください。

---

# 24. 論文としての到達点候補

Phase 0.5 reportでは、pilot結果次第で論文がどこまで進められるかも整理してください。

## Level 1

**State-robust calibration mechanism**

response correctionでstate sensitivityを抑制できる。

## Level 2

**Response-specific calibration algorithm**

ordinary state improvementより有利なresponse-specific tradeoffがある。

## Level 3

**Resource-improving calibration**

N2/CO等でfrozen QPE budget / selected time / resource costまで改善する。

Phase 1 pilotはLevel 1〜2の判定が目的。

Level 3は今回まだ実行しない。

---

# 25. 必須成果物

新しいartifact directoryを作り、少なくとも以下を保存してください。

1. `README.md`
   - Phase 0からの引継ぎ
   - 今回のscope
   - science未実行
   - protocol status

2. `response_pilot_protocol.md`
   - 数式
   - arms
   - train/eval split
   - phase boundary
   - numerical rules
   - outcomes

3. `response_pilot_protocol.json`
   - machine-readable normative protocol

4. `algorithm_design.md`
   - response correction
   - Ritz comparator
   - theoretical target invariance
   - known limitations

5. `cost_accounting.md`
   - action counters
   - fair-comparison rules

6. `novelty_review.md`
   - related methods
   - overlap
   - proposed novelty
   - novelty uncertainty

7. implementation skeleton

8. synthetic tests

9. source manifest

10. verification

11. `GO_NO_GO_FOR_SCIENCE.json`
   - science_ready true/false
   - unresolved design issues
   - exact next science actions if approved

---

# 26. 完了条件

Phase 0.5は以下を満たしたら完了としてください。

- response estimatorが一意に定義されている
- response subspaceが固定されている
- mが固定されている
- numerical rank / SVD ruleが固定されている
- Ritz comparatorが固定されている
- train/eval timeが固定されている
- fit ruleが固定されている
- evaluation metricsが固定されている
- outcome logicが固定されている
- cost accountingが固定されている
- synthetic testsが通る
- source identityが閉じている
- science action count = 0
- Phase A / Phase B境界が実装上分離されている

その後停止してください。

---

# 27. 最終報告

最後に、

1. response estimatorの最終仕様
2. Ritz comparatorの最終仕様
3. numerical stabilization rule
4. expected science action count
5. novelty上の最も強い候補
6. novelty上の懸念
7. `science_ready=true/false`
8. science_readyなら、次のH4 pilotで実際に何を何回計算するか

を報告してください。

**science runは開始せず、commit/push後に停止してください。**

第1研究のformal result、Phase 0 result、S4 resultは変更しないでください。
