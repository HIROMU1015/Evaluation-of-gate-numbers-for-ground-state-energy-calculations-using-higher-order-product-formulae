# 第一研究：論文用 evidence matrix

**status:** `complete_existing_evidence_package`

**integration snapshot:** `6a1e54d5e830a20b8817791f9f1f65729815fc12`

**new direct truth / Hamiltonian / state / fit:** `0 / 0 / 0 / 0`

この文書は論文本文ではなく、主張と保存済み証拠を結ぶ監査用台帳である。
数値の正本は `paper_numbers.csv`、file/commit/hashの正本は
`paper_source_manifest.json` とする。

## 主張と証拠

| ID | 固定主張 | 主要証拠 | 許される表現 | 必須の限定 | 数値行 |
|---|---|---|---|---|---:|
| C1 | Direct PF error is reproducible as the signed eigenvalue shift of the branch connected continuously to the exact ground state. | S0 v1.1 branch audit and six exact-time signed shifts. | Numerical implementation is reproducible for the fixed six-condition scope. | Do not generalize branch reliability beyond the tested six conditions and fixed PF implementation. | 18 |
| C2 | State substitution is a major calibration-error axis: 79/128 fixed cases are state-dominant and 49/128 are mixed. | S1/S2 frozen three-way decomposition; S3 retrospective synthesis. | State substitution is often important in this fixed development set. | Do not claim universal state dominance; H4 and controlled two-level cases have different mixtures. | 8 |
| C3 | The 1% frozen safety margin succeeds at the exact selected time in 6/6 development conditions. | S0 exact-time v1.1 scoring and the frozen decision trace. | Development-set safety for gamma=1.01. | Not an independent-molecule or universal safety guarantee. | 74 |
| C4 | Safety and efficiency differ; total frozen-budget factors reach about 2.15 and 2.10 for the two HF stress cases. | Completion-analysis cost-factor decomposition. | safe != efficient under the continuous cost proxy. | C_star is the original two-PF saved-grid minimum, not a continuous-time global oracle. | 6 |
| C5 | PF-selection loss is zero in all six conditions on the original two-PF saved grid. | Regret and completion decompositions. | PF redesign is not the observed bottleneck in this candidate set. | Do not generalize beyond current_m3, yoshida4, and the saved grid. | 7 |
| C6 | For HF, the time loss is dominated by the admissible-domain restriction rather than within-domain selection. | Completion-analysis analytic bounds at the frozen cap. | F_domain lower bounds are 2.114659 (eq) and 2.069664 (stretch). | No claim that cap-external times are safe or that the saved-grid oracle is continuous-global. | 12 |
| C7 | Among the four primary active-space conditions, calibration dominates three and time selection dominates N2 stretch. | Frozen regret decomposition on the original saved grid. | The observed resource loss has more than one improvement axis. | Primary four conditions and saved-grid accounting only. | 7 |
| C8 | Calibration precision is resource-relevant through \|b\|/(epsilon-e), not only through \|b\|/e. | Analytic cost identity reproduced in all six completion-analysis rows. | Use the remaining-budget-normalized bias as a resource-side calibration metric. | Requires the fixed cost model and a positive remaining error budget. | 36 |
| C9 | The preregistered operator-sensitive two-state diagnostic detects HF/current_m3 risk but does not improve resource regret over baseline. | S4 frozen predictions and fixed no_benefit decision. | A valid negative result for this diagnostic and decision rule. | Do not claim that operator-sensitive diagnostics in general cannot help. | 24 |
| C10 | After correcting S4 absolute cost accounting to beta=1.2, all 42 strategy-condition rows remain safe, zero labels change, and no_benefit is unchanged. | Completion-analysis S4 cost-definition audit. | The qualitative S4 conclusion is robust to the beta-definition correction. | 42 means 6 development conditions x 7 strategies; raw S4 absolute margins are superseded. | 34 |

## 図の固定順序（このtaskでは作図しない）

1. **Decision pipeline** — proxy入力、PF/時刻選択、凍結予算、truth採点の情報境界。
2. **Three-error decomposition** — state substitution、proxy–eigenvalue、model fit。
3. **Safety versus efficiency** — S0/completionの6条件のみ。S4の42行監査とは混ぜない。
4. **Within-domain versus domain loss** — N2/COのsaved-grid会計とHFの解析的boundsを描き分ける。

## 表の固定内容

- **Table 1:** 6条件 x 2 PFのdecision trace。`decision_trace.*`行を使用する。
- **Table 2:** `F_model`, `F_margin`, `F_within`, `F_domain`, `F_PF`, `F_total`。coverage statusを必ず併記する。
- **Table 3:** 7 strategyのcorrected安全数、平均・最大regret、corrected最小margin。

## 出典の優先順位とsupersession

1. completion analysisをC4–C10の正本とする。
2. S0 exact-time v1.1をC1/C3の正本とする。
3. S1/S2とS3をC2の機構証拠に使う。
4. S4原成果物はrisk matrix・相対regret・`no_benefit`に使う。
5. S4原成果物の絶対phase-error/marginは引用せず、beta=1.2のcorrected auditで置換する。

## Coverageを混同しないための規則

- `exact_saved_grid_only`: N2/COの保存済み2-PF truth grid上の厳密会計。
- `analytic_bound_at_cap`: HFでcap点と保存grid参照から得た上下界。
- `C_star`は常にoriginal two-PF saved-grid minimumと書き、continuous oracleとは呼ばない。
- `42/42 safe`は6 development conditions x 7 frozen strategiesであり、独立42条件ではない。

## Reverse fact audit（本文完成後に実施）

- [ ] 本文の全数値が `paper_numbers.csv` の `metric_id`へ逆引きできる。
- [ ] 各数値のscope、evaluation group、coverage status、limitationが本文またはcaptionに反映される。
- [ ] S4の絶対margin/phase-errorはcorrected auditだけから引用される。
- [ ] 6条件のS0安全性と6 x 7行のS4 strategy監査を同じ標本数として扱っていない。
- [ ] HF boundsをcap外安全性やcontinuous-time global optimumの証拠として使っていない。
- [ ] negative resultを診断一般の無効性へ拡張していない。

## 停止条件

このpackage作成では、新規計算、図作成、本文執筆、selector変更、S5、新分子、
新PF、別基底、別精度、追加diagnosticを行わない。
