# 第一研究 completion analysis 指標辞書

## 費用

- `C_star_reference_grid`: 元2 PF・保存truth格子上の最小直接費用。連続時間oracleではない。
- `C_selected_formula_star_reference_grid`: 選択PFに限定した保存truth格子上の最小直接費用。
- `C_required_selected_time`: 選択PF・exact selected timeの直接誤差を用いた必要費用。
- `C_hat`: truthを使わずPhase Aで凍結した予測費用。
- `B_frozen`: `gamma * C_hat`。今回の`gamma`は1.01。

## 乗法因子

- `F_model = C_hat / C_required_selected_time`: モデル予算の局所的な保守性。
- `F_margin = B_frozen / C_hat`: 固定安全余裕。エネルギー誤差へ1%を足す操作ではない。
- `F_calibration = F_model * F_margin`。
- `F_within`: 実際の許容時刻域内での時刻選択因子。
- `F_domain`: fallback等で許容域を狭めたことによる因子。
- `saved_F_time = F_within * F_domain`。
- `F_P`: 保存2 PF格子におけるPF選択因子。
- `F_total = F_model * F_margin * F_within * F_domain * F_P`。

## coverage status

- `exact_saved_grid_only`: 保存格子oracleが許容域内にあり、保存格子を母集合とした会計では`F_domain=1`。連続時間最適を意味しない。
- `analytic_bound_at_cap`: 全域truthなし。上限補題による`F_within`上界と`F_domain`下界だけを報告する。
- `coverage_insufficient`: 既存データだけでは分離不能。補間や近傍置換をしない。

## safetyとefficiency

- `energy_margin_gamma_1_01_hartree`: target errorからdirect PF誤差と予算由来QPE誤差を引いた量。非負なら、この連続費用proxy内で安全。
- `F_total`: 保存格子基準に対する凍結予算倍率。安全性とは別の効率指標。
- `direct_time_regret`: direct必要費用の時刻選択損失。
- `frozen_budget_overhead`: 1.01倍凍結予算を基準費用で割った超過。上のregretと同一ではない。

## S4費用定義監査

- `stored_s4_beta=0.105`: S4 protocolが保存phase errorの再計算に使用した値。
- `practical_cost_beta=1.2`: practical/S0予測費用とdirect費用が使用した値。
- `consistent_phase_error`: 凍結予算を生成した費用式と同じ1.2で再計算した診断値。元S4成果物は変更しない。
