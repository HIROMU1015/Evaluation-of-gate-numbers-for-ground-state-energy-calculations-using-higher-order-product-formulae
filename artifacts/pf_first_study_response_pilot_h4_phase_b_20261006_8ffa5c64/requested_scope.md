第1研究のresponse-corrected calibration pilotについて、**H4 Phase B saved-scalar scoring** を実行してください。

今回は、freeze済みPhase A predictionを一切変更せず、既存保存truthだけを開いて採点する段階です。

\[
\boxed{\text{Phase B scoringのみ承認}}
\]

です。

**新規science calculationは禁止です。Phase B完了後はN2/CO/HF等へ進まず停止してください。**

---

# 0. 起点

成功したPhase A Attempt 2は以下です。

- Repository
  `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

- Branch
  `pf-first-study-response-pilot-h4-phase-a-retry2-20261006`

- Phase A freeze commit
  `53a88c28b7587ab61efb93d6ba30974c9d3d6404`

- Artifact
  `artifacts/pf_first_study_response_pilot_phase_a_h4_retry2_20261006_d6dc5674/`

- `predictions.json` SHA-256
  `9ce3d4e7ec89575f1d661515cddb636fab0288c5c4149df1c85dc529adace18f`

- strict `phase_a.json` SHA-256
  `4c10e6e766319c88bf8375c6c1422a43dbb75df8becefb8a5dee4aa4e5b25eb4`

- Phase 0.5 science protocol SHA-256
  `38ddb97f8f3c0bcc155eb9be23fb650772db264b6da0686f905a1d7d8ba482e3`

Phase A status:

`PHASE_A_NUMERICALLY_READY`

主なPhase A numerical facts:

- actual Krylov rank = 8
- prefix stop = false
- response primary SVD rank = 8
- retained condition number ≈ 3.4991704321
- residual convergence = 66/66 PASS
- Ritz8 projected dimension = 9
- A0/A1/A2 primary fits = all `fit_ok`
- cold replay maximum difference = 0
- action counts = frozen contractと一致
- saved truth access = 0
- Phase B = 未実行

Attempt 1のfailed audit commit

`3d7a923f2a8d11aff57a05454eca8e142496833e`

も履歴として保持してください。

---

# 1. 今回の目的

Phase Aでfreezeしたpredictionについて、既存保存truthを一度だけ開き、

1. baseline CISD calibration
2. response-corrected calibration
3. equal-information Ritz state improvement

を比較してください。

主に判断したいのは、

> **state correction自体がfinite-time PF calibrationを改善したか**

と、

> **その改善にresponse固有の価値があるか、それともordinary Ritz state improvementで同等以上か**

です。

Phase 0で示されたoracle state-removalの大きなheadroomが、実際のoracle-free interventionでどこまで回収されたかも確認します。

---

# 2. Normative authority

science specificationは変更しません。

以下をauthorityとしてください。

## Phase 0.5

1. `artifacts/pf_first_study_response_pilot_phase05_20261006/response_pilot_protocol.json`
2. `response_pilot_protocol.md`
3. `algorithm_design.md`
4. `cost_accounting.md`
5. `user_amendments.json`

Normative authorityは `response_pilot_protocol.json`。

## Phase 0.6

6. `artifacts/pf_first_study_response_pilot_phase06_preflight_20261006/phase_b_truth_barrier.md`
7. `GO_NO_GO_FOR_H4_SCIENCE.json`
8. `preflight_protocol.json`
9. `phase_a_schema.json`

## Frozen Phase A

10. `artifacts/pf_first_study_response_pilot_phase_a_h4_retry2_20261006_d6dc5674/PHASE_A_FROZEN`
11. `verification.json`
12. `predictions.json`
13. `prediction.sha256`
14. `phase_a.json`
15. `fit_results.csv`
16. `proxy_values.csv`
17. `action_counts.json`

Phase BではPhase A science outputを変更・再計算しないでください。

---

# 3. Phase B authorization

今回専用のPhase B authorization recordを新規作成してください。

最低限、

- phase = `phase-b`
- science_authorized = true
- phase_a_commit =
  `53a88c28b7587ab61efb93d6ba30974c9d3d6404`
- prediction SHA =
  `9ce3d4e7ec89575f1d661515cddb636fab0288c5c4149df1c85dc529adace18f`
- strict Phase A SHA =
  `4c10e6e766319c88bf8375c6c1422a43dbb75df8becefb8a5dee4aa4e5b25eb4`
- protocol SHA =
  `38ddb97f8f3c0bcc155eb9be23fb650772db264b6da0686f905a1d7d8ba482e3`
- new science calculation count authorized = 0
- saved direct truth read = 12 evaluation coordinates only
- saved exact proxy read = 22 signed coordinates only
- Phase A modification prohibited = true
- N2/CO/HF extension prohibited = true

を明記してください。

---

# 4. Phase B開始前のfreeze verification

truthを開く前に、以下を必ず確認してください。

1. exact Phase A commit SHA
2. remote branch / commit identity
3. `predictions.json` byte identity
4. prediction SHA-256
5. `phase_a.json` byte identity
6. strict Phase A SHA-256
7. protocol SHA
8. code/source hashes
9. `PHASE_A_FROZEN`
10. Phase A publication blob identity

1つでも不一致なら、truthを読まずに

`FAILED_PHASE_A_FREEZE_VERIFICATION`

として停止してください。

---

# 5. 今回許可するtruth

Phase 0.5のsaved truth join contractに従い、既存保存済みの以下だけを読んでください。

## Direct PF truth

Evaluation 6 absolute times ×両sign:

\[
T_{\rm eval}
=
\{0.125,0.175,0.225,0.275,0.35,0.40\}
\]

計12 signed coordinates。

各座標の

\[
\delta_{\rm direct}(t)
\]

を使用。

## Exact-state proxy

Training 5 + evaluation 6 absolute times ×両sign:

計22 signed coordinates。

\[
g_{\rm exact}(t)
\]

をA3 reference / mechanism scoringに使用。

---

# 6. 禁止事項

Phase Bでは以下を禁止します。

- new H action
- new PF forward / adjoint action
- new response solve
- new Ritz solve
- new fit of A0/A1/A2
- Phase A prediction変更
- Phase A coefficient変更
- new direct truth
- new exact proxy
- new Schur/eigensolve
- new ground solve
- new branch continuation
- interpolation
- nearest-time substitution
- missing truth救済
- mの再選択
- response/Ritzのpost-hoc selector
- gamma変更
- threshold変更
- metric変更
- Outcome rule変更
- N2/CO/HF extension
- 新PF
- 新state
- 新geometry
- 新分子

保存truthに欠損やduplicateがあれば停止してください。

---

# 7. A3 exact-state reference

保存済みexact-state proxy22点を使い、Phase 0.5で固定された**同じfit rule**でA3 reference fitを行ってください。

これはPhase B referenceなので許可します。

A3は、

- exact-state proxy
- same training times
- same \(a_4t^4+a_6t^6\) model
- same fit rule

です。

A3をPhase A predictionの代替や救済に使わないでください。

A3 fit countは凍結contract通り3 reference fits。

---

# 8. Primary scoring arms

primary comparisonは、

## A0

bare CISD baseline

## A1

response m=8

## A2

Ritz m=8

です。

m=1/2/4についても保存済みpredictionをdiagnostic scoringして構いませんが、

- primary selectionへ昇格しない
- truth後にbest mを選ばない

こと。

---

# 9. Point/proxy mechanism scoring

保存exact proxyを使い、各22 signed coordinateで、

\[
E_{\rm proxy}^{\rm method}(t)
=
g_{\rm method}(t)-g_{\rm exact}(t)
\]

を計算してください。

各arm/mについて、

- signed error
- absolute error
- improvement vs A0
- worsened vs A0

を保存してください。

ただしpoint/proxy improvementだけでmethod successと判定しないでください。

---

# 10. Total finite-time prediction error

主科学metricです。

各12 evaluation signed coordinateについて、

\[
E_{\rm total}^{\rm method}(t)
=
\widehat f_{\rm method}(t)
-
\delta_{\rm direct}(t)
\]

を計算してください。

以下を保存：

- signed total error
- absolute total error

\[
|E_{\rm total}^{\rm method}|
\]

---

# 11. Magnitude underestimation

budget-safety relevanceとして、

\[
u_{\rm method}(t)
=
|\delta_{\rm direct}(t)|
-
|\widehat f_{\rm method}(t)|
\]

を計算してください。

さらに、

\[
u_{+,\rm method}
=
\max(0,u_{\rm method})
\]

を保存してください。

重要：

- signed prediction errorとuを混同しない
- \(u>0\) はunderestimation方向
- \(u<0\) はconservative方向

です。

---

# 12. Sign crossing

各evaluation rowで、

\[
\operatorname{sgn}(\widehat f_{\rm method})
\neq
\operatorname{sgn}(\delta_{\rm direct})
\]

を記録してください。

sign crossing rowについて、componentwise additive attributionを新しく行わないでください。

---

# 13. Primary aggregate metrics

A0/A1/A2について、12 evaluation rowsで以下を計算してください。

## 13.1 Total absolute prediction error

\[
\boxed{
S_{\rm abs}^{\rm method}
=
\sum_t
|\widehat f_{\rm method}(t)-\delta_{\rm direct}(t)|
}
\]

## 13.2 Positive underestimation severity

\[
\boxed{
S_{\rm under}^{\rm method}
=
\sum_t
\max
\left(
0,
|\delta_{\rm direct}(t)|
-
|\widehat f_{\rm method}(t)|
\right)
}
\]

## 13.3 Worst-case error

\[
E_{\max}^{\rm method}
=
\max_t
|\widehat f_{\rm method}(t)-\delta_{\rm direct}(t)|
\]

## 13.4 Sign crossing count

## 13.5 Baseline relative comparison

A1/A2について、

- S_abs ratio to A0
- S_under ratio to A0
- E_max ratio to A0

を計算。

ただし分母0ならratio=null。

## 13.6 Rowwise

- improved rows vs A0
- worsened rows vs A0
- equal rows

を保存。

---

# 14. Mechanism-to-total bridge

今回特に重要です。

各methodについて、

1. proxy point error
2. refit後total error

を並べてください。

例えば、

\[
\sum|g_{\rm method}-g_{\rm exact}|
\]

と、

\[
S_{\rm abs}^{\rm method}
\]

を別々に提示。

これによって、

> state/proxy correctionは効いたがfitで利益が消えた

のか、

> refit後まで利益が残った

のかを確認します。

Phase 0で予想されたfit bottleneckを必ず検証してください。

---

# 15. Response vs Ritz

Phase A時点でA1とA2のpredictionが非常に近いことは既知ですが、これはtruthを使った優劣ではありません。

Phase Bでは、

- A1 vs A2 S_abs
- A1 vs A2 S_under
- A1 vs A2 E_max
- sign crossing
- rowwise error

を直接比較してください。

さらにPhase 0.5 cost contractから、

### standalone cost vector

Response:

- H actions
- PF forward
- PF adjoint
- small response solver

Ritz:

- H actions
- PF forward
- PF adjoint
- small Ritz eigensolve

を凍結値のまま併記してください。

異種cost unitを1つの恣意的scalarへ足さないでください。

---

# 16. Unique tradeoff判定

Phase 0.5 protocolの定義をそのまま使用してください。

responseがRitzに対して、

\[
(
S_{\rm abs},
S_{\rm under},
\text{standalone H actions},
\text{standalone PF actions}
)
\]

でPareto-dominatedされず、少なくとも1要素でstrictly betterなら、

`response_unique_tradeoff = true`

としてください。

定義を変更しないでください。

solver cost等は別途報告し、結果後に都合よくPareto軸を増減させないでください。

---

# 17. Outcome A/B/C/D

Phase 0.5でfreezeしたlogicをそのまま使ってください。

## Outcome A

`response_specific_support`

条件：

1. A1 responseのS_abs < A0
2. A1 responseのS_under < A0
3. Phase A residual convergence gate = PASS
4. A1がA2 Ritzに対するunique tradeoffあり
5. primary fits適格

## Outcome B

`generic_state_improvement`

- A1 responseもA2 Ritzも、
  - S_abs < A0
  - S_under < A0
- ただしresponse固有tradeoffなし

## Outcome C

`point_only`

- responseのpoint/proxy errorは改善
- しかしrefit後のtotal S_abs / S_underの必要改善を満たさない

→ resource stageへ進まない。

## Outcome D

`no_benefit`

- response / Ritzともtotal/unsafe両方を改善しない
- またはfreeze済みrule上numerically unusable

---

# 18. Mixed / uncovered predicate

Phase 0.5 protocol通り、A/B/C/Dのいずれにも完全一致しない場合、

`inconclusive_mixed_predicates`

として保存してください。

無理に最も近いOutcomeへ分類しないでください。

---

# 19. Numeric thresholdsを追加しない

今回も、

- 5%
- 10%
- chemical accuracy fraction
- arbitrary “material improvement”

等の新thresholdを結果後に導入しないでください。

strict scalar decreaseと凍結predicateのみ使用。

連続値はすべて報告してください。

---

# 20. m diagnostics

response / Ritzの

\[
m=1,2,4,8
\]

についてもtruth scoringを行い、

- proxy error
- total error
- underestimation

がmでどう変わったか保存してください。

ただし、

> truthを見てbest mを選ぶ

ことは禁止です。

primaryは常にm=8。

m diagnosticはmechanism interpretationだけです。

---

# 21. Phase 0 oracle-removalとの比較

Phase 0のoracle resultは、

> state componentを完全除去できた理想headroom

です。

今回の実測A1/A2改善と比較する場合、

- Phase 0 oracle removal
- actual response
- actual Ritz

を明確に別物として示してください。

例えば、

\[
\text{realized fraction of oracle error reduction}
\]

を計算する場合も、定義を明記し、

- oracle headroomを100%実現可能と扱わない
- 同一分母に対応すると確認できる場合だけ計算

してください。

無理に1指標へまとめる必要はありません。

---

# 22. Safety / QPE resourceについて

今回はまだLevel 1–2 mechanism pilotです。

H4 fixed evaluation coordinateにおけるunderestimationは評価しますが、

- new QPE budget
- selected time変更
- PF selection変更
- resource saving

は行わないでください。

Phase B H4結果だけからLevel 3 resource method達成と書かないでください。

---

# 23. New science action accounting

Phase Bは保存scalar scoringのみなので、

以下はすべて0である必要があります。

- H matvec
- PF forward
- PF adjoint
- response solve
- Ritz solve
- new fit A0/A1/A2
- direct truth generation
- ground solve
- Schur
- eigensolve

許可されるのは、

- saved direct truth read = 12 distinct evaluation coordinates
- saved exact proxy read = 22 distinct signed coordinates
- A3 reference fits = 3
- scalar arithmetic / CSV / JSON processing

のみ。

---

# 24. Truth source identity

各saved truth rowについて、

- system
- PF
- sign
- exact time
- branch quality
- source commit
- source hash

をjoin contractと照合してください。

欠損・duplicate・time mismatch・sign mismatch・unreliable branchならhard stop。

nearest-time substitutionは禁止。

---

# 25. Required output tables

最低限以下を作ってください。

## `evaluation_scoring.csv`

12 evaluation × methodsについて、

- method
- m
- time
- prediction
- direct truth
- total signed error
- absolute error
- u
- u_plus
- sign crossing
- vs baseline improvement

## `proxy_scoring.csv`

22 coordinatesについて、

- method
- m
- proxy
- exact proxy
- signed point error
- abs point error

## `aggregate_metrics.csv`

- S_abs
- S_under
- E_max
- crossing count
- improved/worsened/equal rows
- ratios

## `response_vs_ritz.csv`

- metric
- A1
- A2
- winner / tie
- relevant frozen cost counters

## `m_convergence_truth_diagnostic.csv`

m=1/2/4/8 diagnostics。

---

# 26. Outcome artifact

`scientific_outcome.json`

を作り、

最低限、

- frozen Phase A commit
- prediction SHA
- truth source hashes
- S_abs A0/A1/A2
- S_under A0/A1/A2
- E_max A0/A1/A2
- crossing counts
- response_unique_tradeoff
- outcome
- outcome predicate trace
- new science action count = 0
- saved truth rows read
- limitations

を保存してください。

---

# 27. Reportで必ず議論すること

単なるOutcome表示ではなく、以下を分けて考察してください。

## A. State correction itself

A1/A2はA0より実際に改善したか。

## B. Response specificity

responseはRitzより意味のあるtradeoffを示したか。

## C. Fit bottleneck

point/proxy改善がrefit後total predictionへどれだけ残ったか。

## D. Underestimation

accuracy改善とbudget-risk方向の改善が一致したか。

## E. Next research implication

Outcomeに応じて、

- response-specific methodへ進む
- generic state improvementへ再定義
- fit model改善が次課題
- state-correction方向停止

のどれが適切か。

ただし次stageを自動開始しないでください。

---

# 28. Attempt 1 / Attempt 2履歴

Phase B reportでも、

- Attempt 1 technical failure
- Attempt 2 successful freeze

を簡潔に記録してください。

Attempt 1を削除・隠蔽しないこと。

科学結果の分母へAttempt 1を二重計上しないこと。

---

# 29. 必須成果物

新しいcreate-only artifact directoryを作ってください。

例：

`artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_<id>/`

最低限：

1. `README.md`
2. `authorization_phase_b.json`
3. `phase_a_freeze_verification.json`
4. `truth_source_identity.json`
5. `truth_access_audit.json`
6. `proxy_scoring.csv`
7. `evaluation_scoring.csv`
8. `aggregate_metrics.csv`
9. `response_vs_ritz.csv`
10. `m_convergence_truth_diagnostic.csv`
11. `A3_reference_fit.csv/json`
12. `scientific_outcome.json`
13. `report.md`
14. `action_counts.json`
15. `verification.json`
16. `source_manifest.json`
17. `publication_manifest.json`
18. `COMPLETE`

---

# 30. Tests

Phase B用に少なくとも以下をtestしてください。

1. correct Phase A SHA required
2. altered predictions rejected
3. altered phase_a blob rejected
4. missing truth row rejected
5. duplicate truth row rejected
6. wrong sign rejected
7. wrong time rejected
8. unreliable branch rejected
9. S_abs arithmetic
10. S_under arithmetic
11. sign crossing
12. zero denominator ratio handling
13. Pareto tradeoff logic
14. Outcome A
15. Outcome B
16. Outcome C
17. Outcome D
18. mixed predicate handling
19. no new science counter
20. A3 cannot modify frozen predictions

既存testsを壊さないでください。

---

# 31. Completion gate

以下がすべて満たされた場合のみ`COMPLETE`を作ってください。

- Phase A freeze verified
- truth source identity verified
- exact denominators complete
- no duplicate/missing truth
- scoring complete
- Outcome logic evaluated
- action count contract pass
- new science actions = 0
- saved direct truth distinct count = 12
- saved exact proxy distinct count = 22
- Phase A prediction unchanged
- no N2/CO/HF extension
- all tests pass

---

# 32. Commit / push

Phase B resultをcommit/pushしてください。

その後、

- remote SHA
- result artifact blobs
- prediction source identity
- truth source blobs

を独立取得して照合してください。

Phase A commitは変更しないでください。

---

# 33. 最終報告

完了後、以下を簡潔に報告してください。

1. A0/A1/A2のS_abs
2. A0/A1/A2のS_under
3. E_max
4. sign crossing count
5. point/proxy error改善
6. response vs Ritzの比較
7. response_unique_tradeoff
8. final Outcome
9. m diagnosticsの主な傾向
10. new science action count = 0
11. saved direct truth read = 12
12. saved exact proxy read = 22
13. tests
14. result commit / branch / push
15. 次stageは開始していないこと

---

# 34. 停止条件

Phase B scoring・commit・push・remote verification後に必ず停止してください。

**N2/CO/HF resource stageへ自動的に進まないでください。**

OutcomeがAでもBでもCでもDでも、次の研究判断はGPT/ユーザーが行います。

formal第1研究、Phase 0、Phase 0.5、Phase 0.6、Phase A Attempt 1/2のartifactは変更しないでください。
