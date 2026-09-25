# 第一研究：論文主張台帳と完成方針

**固定日：2026-09-26**
**状態：`paper_claims_frozen_from_existing_evidence`**
**completion analysis：`artifacts/pf_first_study_completion_analysis_20260926_940ee7f/`**
**新規direct truth / Hamiltonian / state / fit：`0 / 0 / 0 / 0`**

## 1. 論文の中心命題

本研究の中心は「新しいproduct formula係数を発見したこと」ではなく、有限時間QPEで
PF、時刻、QPE誤差配分を選ぶとき、校正誤差・許容時刻域・安全余裕が資源判断へどう
伝播するかを分離して示すことである。

主メッセージは次の一文へ固定する。

> 有限時間PF校正では、局所的な誤差推定の精度だけでなく、許容時刻域と安全余裕を
> 独立に設計する必要があり、安全な選択が低い資源regretを意味するとは限らない。

肯定的な主張はN2/COの凍結内殻active-spaceを主集合、HF全電子2条件をstress testと
して述べる。6条件はdevelopment集合であり、独立分子transfer testとは呼ばない。

## 2. 数値を引用するときの優先順位

1. completion analysisの`report.md`、`metric_dictionary.md`、
   `cost_factor_decomposition.csv`、`s4_cost_definition_audit.csv`。
2. S0 exact-time v1.1（commit `cc3626a`）。
3. S1/S2（commit `d13f49d`）、S3（`e768aaf`）。
4. S4 Phase B v1.1（commit `4d831b5`）はstrategyの相対比較と
   `no_benefit`判定へ使う。

S4 protocolの保存`qpe_beta=0.105`は、予測費用とdirect費用で用いた`beta=1.2`と
一致しない。このため、S4原報告の絶対phase-errorとenergy-margin値は引用せず、
completion analysisで`beta=1.2`へ統一した再監査値を引用する。保存S4 artifactは
履歴として変更しない。

## 3. 主張台帳

| ID | 論文で主張する内容 | 主要証拠 | 許される強さ | 必須の限定 |
|---|---|---|---|---|
| C1 | direct PF誤差は短時間から厳密基底状態へ接続する固有枝の符号付きshiftとして再現可能 | H01、S0/S4 branch audit | 数値実装の再現性 | 6条件・2 PFの範囲 |
| C2 | 固定128 caseでは状態置換が79 caseで支配し、49 caseはmixedだった | S1/S2 | 状態置換が主要な校正誤差軸 | 普遍的支配とは言わない |
| C3 | 1%余裕付き凍結予算はexact selected timeで6/6安全だった | S0 v1.1 | development集合での安全性 | 一般的安全保証ではない |
| C4 | 安全性と効率は異なり、総費用因子はHFで約2.15、2.10だった | S0、completion analysis | `safe != efficient` | continuous cost proxyと保存grid基準 |
| C5 | 元2 PF保存gridではPF選択損失は6/6で0だった | regret/completion analysis | 今回はPF再設計が主な不足ではない | 候補PF集合外へ一般化しない |
| C6 | HFの時刻損失はcap内選択より許容域制約が支配する下界を持つ | completion analysis | eqで`F_domain >= 2.11466`、stretchで`F_domain >= 2.06966` | cap外の安全性や連続oracleは未証明 |
| C7 | active-space主4条件では3条件が校正・予算支配、N2 stretchが時刻選択支配だった | completion analysis | 問題を単一改善軸へ還元できない | 保存grid会計に限定 |
| C8 | 誤差推定に必要な精度は`abs(b)/e`より`abs(b)/(epsilon-e)`で資源へ結び付く | 解析恒等式と6条件の再現 | resource-side calibration指標を導入 | 費用式が正の残余予算を持つ範囲 |
| C9 | operator-sensitive二状態診断はriskを検出したがbaselineより資源効率を改善しなかった | S4とbeta再監査 | 事前固定negative result | 診断一般の無効性とは言わない |
| C10 | `beta=1.2`へ費用定義を統一しても42/42安全、成否変更0、`no_benefit`不変だった | completion analysis | S4の定性的結論はrobust | 原S4の絶対margin値は置換する |

## 4. 主張しないこと

- 未使用分子へtransferする低regret selectorを確立した。
- 1% safety marginが分子、基底、PF、目標精度によらず十分である。
- HFのcap外時刻が安全、または実際に低コストである。
- 保存truth格子上の最小が連続時間の大域最小である。
- 状態置換誤差がすべての条件で支配する。
- S4診断が実用selectorを改善した。
- PF係数探索、高次数PF、別の回路資源指標について一般結論を得た。
- continuous cost proxyが完全なfault-tolerant runtimeである。

## 5. 費用分解と用語

保存2 PF truth grid上の基準費用を`C_star`、選択PF内の基準費用を
`C_selected_formula_star`、選択時刻のdirect誤差が要求する費用を
`C_required`、凍結予測費用を`C_hat`、安全余裕込み予算を
`B_frozen = 1.01 * C_hat`とする。

報告する因子は次である。

- `F_model = C_hat / C_required`
- `F_margin = B_frozen / C_hat = 1.01`
- `F_calibration = F_model * F_margin`
- `F_time = C_required / C_selected_formula_star`
- `F_PF = C_selected_formula_star / C_star`
- `F_total = F_calibration * F_time * F_PF`

時刻因子は`F_time = F_within * F_domain`とする。N2/COは保存格子を母集合とした
`exact_saved_grid_only`、HFはcap点での補題による`analytic_bound_at_cap`である。
異なるcoverage statusを同じ精度の推定値として平均しない。

同一時刻でdirect誤差を`e`、予測絶対誤差を`e_hat=e+b`とすると、

`F_model = (epsilon-e)/(epsilon-e-b) = 1/(1-b/(epsilon-e))`

である。この恒等式を校正精度と資源penaltyの接続として使う。分母
`epsilon-e`が小さい時刻ほど、同じ絶対biasでも費用へ強く増幅される。

## 6. 主図と主表

### Figure 1：decision pipeline

状態proxy、PF候補、時刻域、予測費用、安全余裕、direct採点の順を示す。truthが
Phase A selectorへ入っていないことと、truthは採点にだけ使うことを明示する。

### Figure 2：safetyとefficiency

completion analysisの`safety_efficiency.pdf`を基礎に、横軸を残余energy margin、
縦軸を`F_total`とする。active-space主4条件とHF stress 2条件を色または記号で分ける。

### Figure 3：時刻損失のdomain/within分離

`time_domain_bounds.pdf`を基礎にする。N2/COは保存grid上のexact会計、HFは上限・下限
として描き、同じ種類の棒に見せない。

### Figure 4：三つの校正誤差軸

S1/S2の状態置換、exact-state proxy--eigenvalue、model fitの三分解を示す。
79/49の分類は固定case集合の集計として注記する。

### Table 1：6条件decision trace

PFごとの解析時刻、元探索域、fallback、cap、予測最適時刻、選択理由を載せる。
completion analysisの`decision_trace.csv`を正本とする。

### Table 2：費用因子

`F_model`、`F_margin`、`F_within`、`F_domain`、`F_PF`、`F_total`と
coverage statusを載せる。連続oracleと誤読されない表題にする。

### Table 3：S4 negative result

7 strategyの安全数と平均・最大主regretを示す。脚注でbeta不一致と統一監査の
42/42安全、成否変更0、`no_benefit`不変を示す。

## 7. 論文構成

1. **Problem setting**：PF誤差そのものではなく`(P,t,epsilon_QPE)`の資源判断を問題にする。
2. **Finite-time calibration**：一項・二項モデル、signed proxy、branch-connected direct truth。
3. **Mechanism decomposition**：状態置換、proxy--eigenvalue、model fitの三分解。
4. **Resource regret decomposition**：`F_model F_margin F_within F_domain F_PF`を導入する。
5. **Molecular cases**：N2/CO主4条件とHF stress 2条件を分離して示す。
6. **Fixed negative result**：S4の事前固定比較と`complete_no_benefit`を報告する。
7. **Design principles and limits**：PF ranking、local calibration、admissible time domain、
   safety marginを別々に設計する必要をまとめる。

## 8. 追加計算の要否

現時点の中心主張は既存データと明示したboundsで閉じるため、第一研究の完成に追加計算は
必須ではない。特にS5、新分子、新PF、別基底、別精度、新diagnosticへは進まない。

追加truthを検討できるのは、論文査読または内部レビューで次のいずれかが中心主張に
不可欠と判断された場合だけである。

1. HFのcap外が安全であるという、現在は行わない主張を新たに採用する。
2. 保存gridでなく連続時間oracleに対する定量値が不可欠になる。
3. active-spaceの`F_domain=1`を保存grid限定でなく連続域でも主張する。

その場合も、必要な条件・PF・時刻だけを別protocolで事前固定し、現在の6条件を見て
閾値やselectorを変更しない。今回のcompletion analysisへ後付けで混ぜない。

## 9. 最終停止判断

第一研究は「有限時間PF校正の信頼性と、保守的な時刻制限が生む資源費用」を主題として
完成させる。次の実作業は本文草稿、caption、再現手順、引用可能な表の整形である。
研究アルゴリズム、selector、PF、分子集合を追加する段階ではない。
