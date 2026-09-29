# 第2研究v2 pre-design analysis 実行指示

## 0. 目的

第1研究の自然な発展として第2研究v2を設計するため、**既存の保存済み結果だけ**を用いて、

> 第1研究で同定した resource regret のうち、どの損失にどの程度の改善余地があり、その改善に必要な情報が truth-free に取得可能か

を整理してください。

今回の目的は新しい手法を実装・評価することではありません。

次の関係を明確にするための **pre-design analysis** です。

\[
\text{第1研究：resource loss の diagnosis}
\rightarrow
\text{第2研究v2：有限の追加校正による intervention}
\]

最終的には、今回の結果を人間がレビューし、

- selective calibration / adaptive intervention を進める
- information-requirement / limit study にする
- 当該介入軸を閉じる

のどれを第2研究v2の中心にするか判断します。

Codex自身は、第2研究v2の科学的方法を最終決定しないでください。

---

# 1. 基準Git identity

現在の研究成果整理版を基準にしてください。

- Repository:
  `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- Base branch:
  `pf-research-outcomes-summary-20260929`
- Audited documentation content commit:
  `68af49bee6087e4b535a50ebddf2b36dab929e62`
- Final identity commit:
  `599a9f2e9a45302b8d34192ef581fd3ea55a1f1e`
- Documentation status:
  `research_outcomes_documentation_complete_review_required`
- Final manifest SHA-256:
  `a815419d3133d4f75fad12e5e94a2c570a8eb35f6e1d950db034bb2eb2960171`
- Original handoff bundle SHA-256:
  `b3a3d0054a17c428cfe0d8958c70892b36538c84fdf72061d6e4f1b36726cc85`

まず次を読んでください。

1. `docs/research_outcomes/20260929/README.md`
2. `docs/research_outcomes/20260929/PF_research_storyline_20260929.md`
3. `docs/research_outcomes/20260929/PF_research_outcomes_20260929.md`
4. `docs/research_outcomes/20260929/PF_research_claim_evidence_ledger_20260929.md`
5. `docs/research_outcomes/20260929/evidence_audit_report.md`
6. `docs/research_outcomes/20260929/decision.json`
7. `docs/pf_post_d2a_research_strategy_20260929.md`
8. `PF_first_study_paper_claim_ledger_20260926.md`
9. `docs/pf_data_use_ledger.md`

必要に応じて、これらから参照されている原CSV / JSON / reportへ辿ってください。

---

# 2. 作業環境

現在のdirty worktreeを変更しないでください。

`599a9f2e9a45302b8d34192ef581fd3ea55a1f1e`
から専用branch / worktreeを作成してください。

branch名の候補：

`pf-second-study-v2-predesign-20260929`

既存artifact、decision、protocol、過去の結果を上書きしないでください。

今回生成するものは、新しい専用directoryへ保存してください。

推奨：

`docs/second_study_v2/predesign_20260929/`

または、それと同等に既存構造と整合する場所。

---

# 3. 科学的な前提

第2研究v2は、第1研究とは独立した新テーマとしてではなく、

> **第1研究で同定した finite-time PF calibration の resource regret を、有限の追加校正によってどこまで低減できるか**

を調べる発展研究として設計します。

第1研究の基本分解

\[
F_{\rm total}
=
F_{\rm model}
F_{\rm margin}
F_{\rm within}
F_{\rm domain}
F_P
\]

を中心にしてください。

今回のpre-designでは、新しい指標を発明して既存の分解を置換しないでください。

特に区別するもの：

- `F_model`
- `F_margin`
- `F_within`
- `F_domain`
- `F_P`
- `F_total`

また、

- signed PF shift
- absolute PF error
- point-estimation error
- uncertainty / width
- frozen quantum budget
- truth-required budget

を混同しないでください。

---

# 4. 今回の4つの主要成果物

## A. Resource-loss map

第1研究および必要な後続development条件について、保存済みscalarを用いてresource lossを整理してください。

最低限、各条件について可能な範囲で次を記録してください。

- condition
- evidence stage
- evidence class
- development / historical holdout / post-hoc 等の役割
- selected PF
- selected time
- `F_model`
- `F_margin`
- `F_within`
- `F_domain`
- `F_P`
- `F_total`
- dominant / material resource-loss factor
- exact / bound / unavailable の区別
- source artifact
- origin/result commit
- verified snapshot commit

第1研究のN2 / CO / HF 6条件を中心にしてください。

後続のLiF / HClは、同一のfactor decompositionが定義可能な保存結果だけを補助的に使用してください。

**異なるstageのmetricを無理に同じ列へ変換しないでください。**

値が比較不能なら `not_comparable` または `not_available` としてください。

---

## B. Intervention-headroom table

各resource-loss factorについて、

> そのfactorだけを理想的に解消できた場合、保存済み情報から言える最大改善余地はどこまでか

を整理してください。

これは **oracle-perfect intervention の post-hoc upper/headroom arithmetic** であり、新方式の性能ではありません。

例：

- calibration / model lossを完全に除いた場合
- margin overheadを除いた場合
- within-domain time selectionを完全化した場合
- 保存済みboundの範囲でdomain restrictionを除けた場合
- 保存PF集合内でPF selectionを完全化した場合
- 同一時刻でPF error calibrationを完全化した場合

ただし、保存結果から計算できないcounterfactualは新規計算してはいけません。

特にHFについて、

- `F_within`
- `F_domain`

の既存upper/lower boundを尊重し、cap外のoracle optimumを勝手に推定しないでください。

HCl C0については、

- same-time perfect calibration saving

を再利用してよいですが、

**HCl同一時刻・未補正task・指定baseline限定**

であることを明示してください。

各行に次を付けてください。

- intervention target
- arithmetic type
- baseline
- maximum saved improvement / bound
- whether exact / upper bound / lower bound
- whether decision-changing potential is material
- evidence class
- limitation

`material` のthresholdは今回データから最適化しないでください。

必要なら複数候補thresholdについて値を表示するだけにし、科学的成功基準として固定しないでください。

---

## C. Information-access / cost matrix

これまで登場したcandidate informationについて、運用時に取得可能かを整理してください。

最低限候補：

- local CISD proxy
- exact-ground proxy
- RHF proxy
- short-time fit coefficients
- fit residual / fit stability
- multiple-window consistency
- state energy
- Hamiltonian residual
- variance
- approximate-state diagnostics
- prefix stability
- projected Ritz values
- projected Ritz gap
- Arnoldi / Krylov residual
- D1 true spectral gap
- `g_target`
- `g_rho_others`
- direct PF eigenvalue shift
- full PF spectrum
- branch-connected direct truth
- action counts
- CPU time
- memory
- existing numerical integrity diagnostics

各情報について：

- information name
- scientific quantity
- available at prediction time?
- truth-free?
- oracle/scorer-only?
- already stored?
- requires new computation?
- current access class
- approximate classical cost if already measured
- PF/H action count if applicable
- memory if applicable
- intended loss mechanism:
  - model
  - state
  - proxy–eigenvalue
  - within-time
  - domain
  - branch/certificate
- can it directly certify the target quantity?
- evidence class
- known failure / limitation
- source

を整理してください。

重要：

**「取得可能」と「certificateとして十分」を分けてください。**

例：

- projected Ritz gapは取得可能でもfull-space gap certificateではない
- D1 true gapはoracle diagnosticでありoperational inputではない
- prefix stabilityはheuristicでありrigorous widthではない

---

## D. Decision-changing headroom analysis

これが今回最重要です。

既存truthを **post-hoc scorerとしてのみ** 使用し、

> 各誤差要因または追加情報が完全に分かったと仮定したとき、最終的なresource decisionがmaterialに変化する余地があったか

を整理してください。

最終decisionは少なくとも、

- selected time \(t\)
- frozen budget \(B\)
- execute / reject
- 必要なら selected PF

で考えてください。

ただし今回、

- 新selectorをfitしない
- thresholdを学習しない
- adaptive ruleを実装しない
- 新しいcandidate timeを生成しない

こと。

既存の保存decision / truth / boundsだけから、

- point estimateが改善してもdecisionがほぼ変わらないcase
- budgetだけmaterialに変わり得るcase
- time-domain restrictionが支配し、同一時刻精度改善では変わらないcase
- PF selection改善余地が既存集合ではないcase
- truth-free signalが既存データ上存在する可能性のあるcase
- truth-free signalが現状見当たらないcase

を分類してください。

可能なら、次のような **descriptive quantity** を保存値から計算してください。

\[
H_B =
\frac{B_{\rm baseline}-B_{\rm oracle\ corrected}}
{B_{\rm baseline}}
\]

ただし、`oracle_corrected` が既存値から定義できる場合だけです。

また、

\[
H_t
\]

のようなtime-selection headroomも、既存のsaved-grid / analytic boundから定義可能な場合だけ使用してください。

これらは **post-hoc decision headroom** であり、新method performanceではありません。

---

# 5. 第一研究との接続を明示する

最終reportでは必ず、

## 第1研究で分かったこと

- resource lossは単一要因ではない
- safetyとefficiencyは異なる
- PF selectionよりcalibration / time-domainが支配する条件がある
- operator-sensitive risk detectionだけではresource benefitが得られなかった

## 今回のpre-designで確認すること

- どのlossに改善余地があるか
- そのlossに対応するtruth-free情報があるか
- その情報によって最終decisionが変わる余地があるか
- 追加情報の取得費用がどの程度か

とつなげてください。

第2研究v2を

> Arnoldi研究
> spectral certificate研究
> gap推定研究

として再定義しないでください。

それらは必要ならintervention candidateです。

---

# 6. 旧第二研究〜C0の扱い

旧第二研究、R1、D1、D2-A、C0は削除せず、

> 第1研究で見つけたresource lossへの介入候補を絞り込むprevalidation系列

として整理してください。

ただしevidence classを厳守してください。

### 旧第二研究

- 当時の独立4条件評価
- `complete_no_benefit`
- multiple-windowという固定方式のnegative result
- time-domain expansion一般の否定ではない

### R1

- post-hoc development diagnosis
- model / state / proxy–eigenvalueの原因分離
- strategy row数を独立sample数と見なさない

### D1

- post-hoc spectral diagnostic
- compressionとrecoverabilityを混同しない
- `K_D1`をArnoldi dimensionやPF action countと混同しない

### D2-A + audit

- development prototype
- audit後はHCl 6/6でphysical branch / shift整合
- 最大absolute shift error ≈ `1.3825298286692967e-8 Ha`
- ただしoperational branch certificateではない
- abstention 1
- lower budget than main baseline 0/6

### C0

- design + post-hoc development arithmetic
- conditional bound candidate
- truth-free full-space `g_rho_others` acquisition未確立
- rigorous ground/branch/action-error certificate未確立
- same-time perfect-calibration saving ≈ 0.33–2.29%
- rigorous certification一般が高価と証明したわけではない

---

# 7. 禁止事項

今回は以下を一切実行しないでください。

- 新しい分子計算
- 新しいHamiltonian生成
- 新しいstate計算
- 新しいdirect PF truth
- PF unitary build
- PF vector action
- Hamiltonian matvec
- Arnoldi / Lanczos / Krylov execution
- full-spectrum eigendecomposition
- new gap calculation
- C1
- D2-B
- LiF追加検証
- HCl追加検証
- independent holdout
- new PF
- PF coefficient optimization
- threshold fitting
- selector fitting
- adaptive policy fitting
- bias-correction method implementation
- synthetic scientific experiment
- GPU query / allocation / kernel
- 新しい科学的methodの成功判定

既存CSV / JSON / reportからの

- read-only extraction
- arithmetic reaggregation
- consistency check
- descriptive post-hoc headroom calculation

だけを許可します。

保存済みscientific artifactは変更しないでください。

---

# 8. 新規算術のevidence class

今回新たに既存scalarから算出した量は、必ず

`post_hoc_predesign_arithmetic`

などの明示的なclassを付けてください。

これを

- independent validation
- new method result
- predictor result
- operational guarantee

と呼ばないでください。

oracle truthを使用する計算は、

`truth_used_for_post_hoc_scorer_only = true`

のように明記してください。

---

# 9. 独立性・data-use境界

`docs/pf_data_use_ledger.md`を必ず参照してください。

少なくとも、

- H-chain
- LiH
- BeH2
- H2O
- NH3
- CH4
- N2
- CO
- HF
- LiF
- HCl

について、既存使用状況を確認してください。

今回のpre-designで結果を参照した系は、将来の第2研究v2の独立holdoutには数えないでください。

ただし、今回新たに未使用分子を開いてはいけません。

未使用候補の名前を探索・列挙する必要もありません。

holdout selectionは第2研究v2 method freeze後の別作業です。

---

# 10. 出力成果物

最低限以下を作成してください。

### 1.
`resource_loss_map.csv`

### 2.
`intervention_headroom.csv`

### 3.
`information_access_matrix.csv`

### 4.
`decision_changing_headroom.csv`

### 5.
`predesign_report.md`

内容：

- objective
- evidence boundary
- 第1研究との接続
- resource-loss map summary
- intervention headroom summary
- information availability summary
- decision-changing headroom summary
- どの領域に「headroom × operational information」の両方が存在するか
- どの領域はheadroomだけあるか
- どの領域はinformationだけあるがheadroomが小さいか
- unresolved items
- limitations
- next research-direction review items

### 6.
`source_registry.json`

全sourceについて：

- path
- origin/result commit
- verified snapshot commit
- blob SHA
- role
- evidence class

### 7.
`decision.json`

ただしこれは**研究方法の最終決定ではありません。**

status候補：

`second_study_v2_predesign_complete_review_required`

最低限：

```json
{
  "status": "second_study_v2_predesign_complete_review_required",
  "new_scientific_computation_count": 0,
  "new_truth_count": 0,
  "pf_action_count": 0,
  "hamiltonian_action_count": 0,
  "arnoldi_action_count": 0,
  "new_gap_calculation_count": 0,
  "gpu_operation_count": 0,
  "selector_fit_count": 0,
  "threshold_fit_count": 0,
  "c1_authorized": false,
  "d2_b_authorized": false,
  "holdout_authorized": false,
  "new_pf_authorized": false,
  "next_step": "full_second_study_v2_research_direction_review"
}
```

必要ならfieldを追加して構いません。

---

# 11. Codexが最終的に答えてよいこと

今回のデータから、以下は**descriptive conclusion**としてまとめて構いません。

### Q1
第1研究で観測したresource lossのうち、既存情報上もっとも大きなheadroomを持つのは何か。

### Q2
headroomが大きいlossについて、truth-freeなobservable / diagnostic候補が既に存在するか。

### Q3
既存情報で高精度化できても、resource decisionがほぼ変わらない領域はあるか。

### Q4
追加情報の取得に既に観測された古典costはどの程度か。

### Q5
現時点で、

- headroom大 × operational informationあり
- headroom大 × operational information未確立
- headroom小 × high-accuracy informationあり

のどれが観測されているか。

ただし、

> 「したがって第2研究v2は方法Xで進めるべき」

という最終研究判断は行わず、候補とevidenceを提示して停止してください。

---

# 12. 特に注意する比較

以下は混同しないでください。

- 第一研究のHF `F_domain ~ 2.1`
- HCl C0のsame-time perfect-calibration saving `0.33–2.29%`

これは系、task、baseline、time-selection freedomが異なります。

前者から「HClでも大きな改善余地がある」と推論しないこと。

後者から「全研究で改善余地は最大2.29%」と一般化しないこと。

また、

- `safe`
- `low regret`
- `accurate point estimate`
- `valid width`
- `certificate`
- `resource advantage`

をそれぞれ別判定として保持してください。

---

# 13. 数値の再確認

既存成果整理bundleの科学数値はevidence auditで訂正0件でした。

今回も原sourceから主要scalarを再取得し、

- display rounding
- percentage vs ratio
- exact vs bound
- development vs independent
- stageごとのbeta / gamma
- signed vs absolute error

を再確認してください。

不一致があれば既存artifactを修正せず、

`predesign_correction_log.md`

へ記録してください。

---

# 14. Git / integrity

- dedicated clean worktreeで実施
- 既存dirty worktreeへ触れない
- `git add -A`禁止
- 今回生成したfileだけ明示的にstage
- source artifactを書き換えない
- original result statusを書き換えない
- mainへmergeしない
- remote pushは明示的許可がない限り行わない

全成果物についてSHA-256 manifestを作成してください。

manifest自身はself-excludedとし、

`"manifest_self_excluded": true`

を明記してください。

可能なら内容commitとidentity記録commitを分離してください。

---

# 15. 停止条件

以下まで完了したら停止してください。

1. resource-loss map完成
2. intervention-headroom table完成
3. information-access matrix完成
4. decision-changing headroom完成
5. source / provenance監査完成
6. predesign report完成
7. decision statusを
   `second_study_v2_predesign_complete_review_required`
   として固定
8. scientific computationが全て0であることを確認

その後、

- C1
- D2-B
- method implementation
- selector implementation
- threshold optimization
- holdout
- new PF

へ自動的に進まないでください。

---

## 最終的な位置付け

今回の作業は、

> **第1研究で得られたdiagnosisを、第2研究v2のintervention設計へ変換するためのread-only pre-design analysis**

です。

狙いは、新しい手法を成功させることではありません。

最終的に人間が、

\[
\boxed{
\text{resource headroom}
\times
\text{information availability}
\times
\text{information cost}
}
\]

を見て、第2研究v2の中心仮説・介入法・成功条件を決められる状態を作ってください。