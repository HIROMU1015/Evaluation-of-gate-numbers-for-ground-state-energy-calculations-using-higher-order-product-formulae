# 第一研究 completion analysis：decision、費用定義、domain制約

**Status:** `complete_first_study_completion_analysis`
**新規direct truth:** `0`
**新規Hamiltonian・状態生成・fit:** `0`
**Protocol SHA-256:** `8ea4629434c2c52396e863b37395a969e4e9a8916ccb6c54351e3dfd1b7c11ba`

## 結論

第一研究の凍結predictionと保存truthだけを用い、費用を
`F_model * F_margin * F_within * F_domain * F_P`へ整理した。
主4条件のうちN2 stretchだけは保存格子会計でtime selection支配、
残る3条件はcalibration/budget支配である。HF stress 2条件はfallback上限に張り付き、
上限内の改善可能性よりdomain制限の下界が支配的である。

またS4の保存protocolがphase error再計算に`qpe_beta=0.105`を使う一方、
その予算を作ったpractical/S0費用は`BETA=1.2`を使っていたことを確認した。
費用定義を1.2へ揃えた読み取り専用再集計でも7 strategyすべて6/6安全で、
targeted fallbackとbaselineのregretは同じままなので`no_benefit`は変わらない。
ただし元S4のphase-error値とenergy-margin値は絶対値として流用しない。

## 条件別の費用会計

`C*`は元2 PF・保存truth格子上の基準であり、連続時間大域oracleではない。

| condition | F_model | F_margin | saved F_t | F_within | F_domain | F_P | F_total | coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| N2_active_eq_sto3g | 1.066967 | 1.010000 | 1.021338 | 1.021338 | 1.000000 | 1.000000 | 1.100631 | exact_saved_grid_only |
| N2_active_stretch150_sto3g | 1.148490 | 1.010000 | 1.227600 | 1.227600 | 1.000000 | 1.000000 | 1.423985 | exact_saved_grid_only |
| CO_active_eq_sto3g | 1.075394 | 1.010000 | 1.031843 | 1.031843 | 1.000000 | 1.000000 | 1.120734 | exact_saved_grid_only |
| CO_active_stretch150_sto3g | 1.102394 | 1.010000 | 1.071820 | 1.071820 | 1.000000 | 1.000000 | 1.193383 | exact_saved_grid_only |
| HF_full_eq_sto3g | 0.994157 | 1.010000 | 2.141534 | <=1.012709 | >=2.114659 | 1.000000 | 2.150313 | analytic_bound_at_cap |
| HF_full_stretch150_sto3g | 1.002733 | 1.010000 | 2.076361 | <=1.003236 | >=2.069664 | 1.000000 | 2.102857 | analytic_bound_at_cap |

## HF cap境界

上限点`T`がdirect errorでもfeasibleなら、`r=e(T)/epsilon`について
`F_within <= 1/(1-r)`、`F_domain >= saved_F_t*(1-r)`である。

| condition | r | F_within upper | F_domain lower | maximum saving within cap |
|---|---:|---:|---:|---:|
| HF_full_eq_sto3g | 1.254948% | 1.012709 | 2.114659 | 1.254948% |
| HF_full_stretch150_sto3g | 0.322572% | 1.003236 | 2.069664 | 0.322572% |

この結果は、cap外が安全であることを示さない。HFの約2.1倍を大きく改善するには、
上限内のoptimum推定を精密化するだけでなく、許容域を広げられる別の根拠が必要である。

## S4費用定義監査

- practical/S0 beta: `1.2`
- S4保存scoring beta: `0.105`
- beta比: `11.428571428571429`
- 保存safe rows: `42/42`
- 整合再計算safe rows: `42/42`
- 判定が変化したrows: `0`
- 整合再計算の最小energy margin: `6.42392054635e-07 Ha`
- 固定判定: `no_benefit`

元S4 artifact、prediction、truth、regret、thresholdは変更していない。これは保存費用を
同一定数で再評価したdefinition auditであり、新しいselector評価ではない。

## Safetyとefficiency

S0の1.01倍凍結予算は6/6で安全だったが、HFの`F_total`は約2.15と2.10である。
従って、このdevelopment集合と連続費用proxyでは`safe != efficient`である。
これは分子一般に対する1%余裕の保証ではない。

## 停止判断

- S4の`no_benefit`とS5非実施を維持する。
- 新PF、追加分子、新diagnostic、係数探索を開始しない。
- 次は主張台帳、図表、条件式の単体テストを論文化パッケージとして整える。
- 追加truthは、既存boundsとcoverage表示で中心主張を閉じられない場合だけ別protocolで事前固定する。
