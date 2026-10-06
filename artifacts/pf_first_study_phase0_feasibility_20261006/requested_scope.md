第1研究を、現在の理解からさらに発展させるための **Phase 0 feasibility audit** を行ってください。

今回の目的は、第1研究のformal resultを変更したり、既存結果を後付けで救済したりすることではありません。

第1研究では、

- model / extrapolation error
- state substitution error
- exact-state proxy–PF eigenvalue error

の三分解を行い、固定128 caseではstate substitutionが79 caseでdominantでした。

一方、その後の第2研究v2から、

- signed prediction accuracyとbudget safetyは別
- point accuracyとresource valueは別
- same-time calibration headroomが小さければ、calibrationを完全に改善してもresource gainは小さい
- time-domain restrictionがresource lossを支配する場合がある

ことが分かっています。

そこで今回まず確認したいのは、

> **第1研究で観測されたstate substitution errorは、実際に介入する価値のあるfailure modeなのか。**
>
> つまり、state substitutionを抑えた場合に、
> 1. PF shift predictionは本当に改善するのか
> 2. budget underestimation riskも改善するのか
> 3. resource decisionを改善できる余地が残っているのか
>
> を、新規science calculationなしで既存保存値から評価してください。

---

# 0. 実行境界

今回は **既存データの読み取り専用再解析** です。

以下は禁止です。

- 新規Hamiltonian生成
- 新規ground-state solve
- 新規PF action
- 新規direct PF truth
- 新規Schur/eigensolve
- 新規state生成
- 新規fit用science point取得
- 新PF探索
- 新分子追加
- 新geometry追加
- gamma / threshold / selector ruleの後付け変更
- S4の再設計
- 第1研究formal resultの変更

既存artifact・prediction・truth・protocolは変更しないでください。

新しいoutput directoryを作り、既存scalar/CSV/JSONを読み取るだけにしてください。

---

# 1. Authority

まず以下を読んでください。

1. `docs/current_research_status.md`
2. `PF_first_study_paper_claim_ledger_20260926.md`
3. `PF_first_study_final_synthesis_20260925.md`
4. `PF_first_study_final_decision_20260925.json`
5. `PF_first_study_results_20260925.md`
6. `PF_first_study_protocol_20260925.md`
7. `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/report.md`
8. `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/error_decomposition.csv`
9. `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/allocation_scoring.csv`
10. `artifacts/pf_first_study_regret_decomposition_20260925_7f0b30d/report.md`
11. `artifacts/pf_first_study_completion_analysis_20260926_940ee7f/report.md`
12. `artifacts/pf_first_study_completion_analysis_20260926_940ee7f/calibration_precision.csv`
13. `artifacts/pf_first_study_completion_analysis_20260926_940ee7f/cost_factor_decomposition.csv`
14. `artifacts/pf_first_study_completion_analysis_20260926_940ee7f/decision_trace.csv`

第2研究v2から、今回の解釈に必要なものとして、

15. `docs/second_study_v2/evidence_integration_20261006/README.md`
16. `docs/second_study_v2/evidence_integration_20261006/evidence_map.md`

も読んでください。

古い途中方針ではなく、first-studyのfinal synthesis / claim ledger / completion analysisをauthorityにしてください。

---

# 2. 今回の研究質問

今回のPhase 0では、次の4つに答えてください。

## RQ0-1
第1研究でdominantだったstate substitution errorは、

> 大きいだけなのか、それともPF error magnitudeをunsafe方向へ過小評価させる主要因なのか。

## RQ0-2
state substitution errorを理想的に除去した場合、

> model error / proxy–eigenvalue errorがどの程度残るか。

つまりstate correctionに十分なheadroomがあるか。

## RQ0-3
state substitution errorのうち、

> coherent interferenceに由来する部分と、diagonal population由来の部分を分けられるか。

特にcontrolled-stateのphase quartetを利用してください。

## RQ0-4
仮にstate-related calibrationを完全に改善できたとして、

> 実際のresource decisionを改善できる余地がどの程度あるか。

same-time calibration headroomと、time/domain/PF lossを分けてください。

---

# 3. Analysis A：controlled-state phase quartet

Experiment Bのcontrolled statesは

\[
|\psi(q,\phi)\rangle
=
\sqrt{1-q}|0\rangle
+
e^{i\phi}\sqrt q|\chi\rangle
\]

で、

\[
q\in\{10^{-3},10^{-2},5\times10^{-2}\}
\]

\[
\phi\in\{0,\pi/2,\pi,3\pi/2\}
\]

です。

同一

- experiment
- formula
- \(q\)
- absolute time
- sign

について4 phaseを対応させ、

\[
\bar g_q
=
\frac14
\sum_{\phi}
g_{\psi(q,\phi)}
\]

を計算してください。

理論的にはphase averageにより、状態置換誤差のうち位相依存するcross/interference成分が消えます。

既存 `error_decomposition.csv` の

- `g_approx_hartree`
- `g_exact_hartree`
- `E_state_signed_hartree`

を使って、

### 3.1
元の各phaseの

\[
E_{\rm state}(\phi)=g_{\psi(q,\phi)}-g_0
\]

### 3.2
phase averaged

\[
E_{\rm state}^{\rm avg}
=
\bar g_q-g_0
\]

### 3.3
interference component

\[
E_{\rm int}(\phi)
=
E_{\rm state}(\phi)-E_{\rm state}^{\rm avg}
\]

を計算してください。

確認したいのは、

- \(|E_{\rm state}^{\rm avg}|\) が元の \(|E_{\rm state}|\) よりどの程度小さいか
- phase依存成分がstate errorの何割を占めるか
- \(q\) に対して
  - interference componentが概ね \(O(\sqrt q)\)
  - averaged componentが概ね \(O(q)\)
  に対応する傾向が保存値から見えるか
- PF依存性
- time依存性

です。

ただし、厳密なpower-law claimは、保存3点のqだけから一般化しないでください。

---

# 4. Analysis B：oracle state-removal headroom

既存分解は

\[
E_{\rm total}
=
E_{\rm fit}
+
E_{\rm state}
+
E_{\rm proxy}
\]

です。

formal resultは変更せず、post-hoc diagnosticとして

\[
E_{\rm no-state}^{\rm signed}
=
E_{\rm fit}^{\rm signed}
+
E_{\rm proxy}^{\rm signed}
\]

を計算してください。

これは、

> state substitution errorだけを理想的に完全除去できた場合に残るsigned prediction error

のoracle diagnosticです。

以下を集計してください。

- 元の \(|E_{\rm total}|\)
- oracle state-removal後の \(|E_{\rm no-state}|\)
- reduction ratio
- state-removal後のdominant residual component
- fit / proxy が次のbottleneckになる割合
- H4とtwo-level Experiment Cを分けた結果
- PF別
- state family別
- time別

重要：

元の79/128 dominance分類は変更しないでください。

これは新しいformal dominance resultではなく、

> **もしstate componentを除去できたら、残りの問題がどの程度か**

を見る別解析です。

---

# 5. Analysis C：budget-risk directionへの射影

第2研究v2では、

\[
e=|\delta_{\rm direct}|,
\qquad
c=|\delta_C|
\]

に対して、

\[
u=e-c
\]

をbudget underestimationとして扱っています。

第1研究の各保存rowでも可能な範囲で、

\[
u
=
|\delta_{\rm direct}|
-
|\hat\delta|
\]

を計算してください。

ここで

\[
\hat\delta=f_{\rm approx}
\]

に対応する保存量を、既存protocol / column definitionを確認して使ってください。

signed total error

\[
E_{\rm total}^{\rm signed}
=
\hat\delta-\delta
\]

と、

\[
u
\]

を混同しないでください。

### 同符号row

\[
\operatorname{sgn}(\hat\delta)
=
\operatorname{sgn}(\delta)
\]

の場合は、

\[
u_k
=
-\operatorname{sgn}(\delta)
E_k^{\rm signed}
\]

として、

- model
- state
- proxy

の各componentがunsafe方向／conservative方向のどちらへ寄与したかを診断してください。

### sign-crossing row

\[
\operatorname{sgn}(\hat\delta)
\ne
\operatorname{sgn}(\delta)
\]

の場合は、絶対値が非線形になるのでcomponentwise additive attributionをしないでください。

`sign_crossing`として別分類してください。

確認したいこと：

- state substitutionはabsolute dominanceだけでなくunderestimation方向でもdominantなのか
- state errorが大きいがconservative方向へ働いているcaseはどの程度あるか
- model / proxy componentがunsafe方向を支配するcaseはあるか

---

# 6. Analysis D：margin-capacityとの接続

S0 / completion analysisの6条件では、

\[
e=|\delta_{\rm direct}|,
\qquad
c=|\delta_C|
\]

として、

\[
u=e-c
\]

\[
M_\gamma
=
\left(1-\frac1\gamma\right)(\epsilon_E-c)
\]

\[
S_\gamma=M_\gamma-u
\]

を再計算してください。

\(\gamma=1.01\)について、保存済み

`energy_margin_gamma_1_01_hartree`

と一致することを確認してください。

また、

\[
\gamma_{\rm req}
=
\frac{\epsilon_E-c}
{\epsilon_E-e}
\]

をpost-hoc diagnosticとして計算してください。

ただし、

- gamma_reqをoperational policyにしない
- truth後にgammaを変更しない
- formal resultを変更しない

こと。

出力表には少なくとも、

- condition
- c
- e
- e-c
- M_1.01
- safety slack
- gamma_req
- original safety

を含めてください。

---

# 7. Analysis E：same-time calibration headroom

既存completion analysisから、

\[
F_{\rm calibration}
=
F_{\rm model}F_{\rm margin}
\]

が得られます。

same-timeでcalibrationをperfectにした場合の最大resource savingを、

\[
H_{\rm cal}
=
1-\frac1{F_{\rm calibration}}
\]

として計算してください。

各6条件について、

- \(H_{\rm cal}\)
- \(F_{\rm time}\)
- \(F_{\rm within}\)
- \(F_{\rm domain}\)
- \(F_{\rm PF}\)
- \(F_{\rm total}\)

を同じ表へ整理してください。

目的は、

> calibrationを完全に改善した場合でも、どの条件ではresource lossの大部分が残るか

を見ることです。

特にHFでは、

\[
F_{\rm total}\approx2.1
\]

に対してsame-time calibration headroomが小さいはずなので、

- calibration-limited
- time/domain-limited
- mixed

を区別してください。

分類thresholdは勝手に新設せず、まず連続値を提示してください。

---

# 8. Analysis F：truth-free resource-improvement upper bound

同じPF・許容時刻域

\[
0<t\le T
\]

の中では、

\[
C(P,t)
=
\frac{\beta K_P}
{t(\epsilon_E-e_P(t))}
\]

かつ \(e_P(t)\ge0\) なので、

\[
C(P,t)
\ge
\frac{\beta K_P}{T\epsilon_E}
\]

です。

したがって現在のbudget \(B_0\) に対し、

\[
H_{\max}^{\rm domain}
=
1-
\frac{\beta K_P}
{T\epsilon_E B_0}
\]

を、

> 同じPF・同じ許容時刻域のままcalibrationだけを改善したときのtruth-free maximum saving upper bound

として計算してください。

これは特にHFのcap条件で重要です。

この値と、

- post-hoc same-time oracle headroom
- actual total regret
- \(F_{\rm domain}\)

を並べてください。

この解析では、

- cap外がsafeとは言わない
- PF変更まで含むupper boundとは言わない
- continuous global oracleとは言わない

こと。

---

# 9. Phase 0の最終判断

今回の目的は、新方式を成功と判定することではありません。

次のPhaseで

> response-corrected calibration / phase-averaged calibration

の小規模pilotへ進む科学的価値があるかを判断してください。

以下の観点ごとに、結果を整理してください。

## A. Mechanism headroom

state substitutionをphase-averageまたはoracle removalすると、誤差はmaterialに減るか。

## B. Safety relevance

state substitutionはbudget underestimation \(e-c\) のunsafe方向にも重要か。

absolute errorが大きいだけでは不十分です。

## C. Resource headroom

calibrationを改善したとして、resource savingの余地が存在するか。

## D. Residual bottleneck

state componentを除去した直後に、

- model error
- proxy–eigenvalue error
- time-domain restriction

が支配的にならないか。

---

# 10. Go / No-Go判断

最終reportでは、最低でも以下の3択で判断してください。

### GO_response_pilot

state-error介入に十分なmechanism headroomがあり、
budget-risk relevanceも確認され、
少なくとも一部の実分子条件でresource improvement余地がある。

→ 次段でresponse-corrected calibrationの最小pilotを設計する価値あり。

### GO_mechanism_only

state correctionはpredictionを改善しそうだが、
resource headroomが小さい、またはtime/domainが支配する。

→ resource-improvement methodではなく、
state-robust calibrationのmechanism studyとしてのみ価値あり。

### NO_GO_state_correction

state removal後もresidual errorが同程度、
あるいはstate errorがbudget-risk方向に重要でない、
あるいはresource headroomがほぼない。

→ state correctionを第1研究の主要発展方向にはしない。

判定thresholdを結果を見て後付けで作らないでください。

定量thresholdが必要なら、まず今回の結果は連続値で提示し、
threshold候補は「future preregistration proposal」として別に書いてください。

---

# 11. 必須成果物

新しいoutput directoryを作り、少なくとも以下を保存してください。

1. `README.md`
   - 目的
   - science boundary
   - source identity
   - 結論
   - Go / No-Go判断

2. `phase_average_analysis.csv`
   - q / phase / PF / time
   - original state error
   - phase-averaged state error
   - interference component
   - reduction metrics

3. `oracle_state_removal.csv`
   - original total error
   - no-state residual
   - fit / state / proxy component
   - residual bottleneck

4. `budget_direction_attribution.csv`
   - direct / predicted shift
   - sign crossing
   - underestimation
   - component directionality

5. `margin_capacity_first_study.csv`
   - c
   - e
   - e-c
   - M_gamma
   - slack
   - gamma_req
   - saved safety

6. `resource_headroom.csv`
   - F_model
   - F_margin
   - F_calibration
   - F_within
   - F_domain
   - F_PF
   - F_total
   - same-time calibration headroom
   - truth-free within-domain maximum saving bound where applicable

7. `feasibility_decision.json`
   - formal first-study results unchanged: true
   - new science calculation count: 0
   - outcome
   - reasons
   - remaining unknowns
   - recommendation for next stage

8. `report.md`
   - 論文として何が新しく見えるか
   - response-corrected calibrationへ進む価値
   - phase averagingの役割
   - resource改善へ接続できるか
   - 追加scienceが必要な最小範囲

9. source manifest / verification / tests

---

# 12. reportで必ず議論してほしいこと

単なる集計結果ではなく、研究として次を考察してください。

## 論文の意図

第1研究を

> 「state substitution errorが大きいことを発見した研究」

から、

> 「finite-time PF calibrationにおけるstate-induced biasを分解し、
> そのうち介入可能な成分と、resource decision上価値のある成分を特定した研究」

へ発展させる余地があるか。

## 新規性

今回のPhase 0自体を新規アルゴリズムとは呼ばないこと。

ただし、結果が支持するなら、

> exact-ground targetを変えずにstate sensitivityを抑える
> response-corrected PF calibration

を次段のalgorithmic contribution候補として評価してください。

## 到達点

次段の最終到達点候補を、

1. state-robust PF calibration mechanism
2. resource-improving calibration method
3. calibration improvementが無価値になるresource boundary

の3段階に分けてください。

現時点のevidenceから、どこまで狙うのが妥当か判断してください。

---

# 13. 重要な制約

今回の解析結果を使って、

- 既存第1研究のformal claimを書き換えない
- 79/128 dominance resultを書き換えない
- S4 no-benefitを書き換えない
- 1% marginのformal resultを書き換えない
- development setをholdoutと呼ばない
- Phase 0のpost-hoc resultをprospective validationと呼ばない

でください。

formal resultと今回のfollow-up feasibility analysisを明確に分離してください。

---

完了後は、新規science calculationを開始せず停止してください。

最後に、

1. Phase 0の主要結果
2. `GO_response_pilot / GO_mechanism_only / NO_GO_state_correction`
3. 次に行うなら何を最小pilotにすべきか
4. そのpilotで必要な新規science actionの種類と概数

を報告してください。
