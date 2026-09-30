# Baseline comparison specification

## Scope

比較は同一task、PF、state identity、candidate contract、budget constants、評価集合で行う。異なるcandidate gridやstateを同じarmの観測として暗黙にpoolしない。

## Arms

| Arm | 入力 | 役割 | 運用上の扱い |
|---|---|---|---|
| B0 | inherited baseline | domain介入前の基準 | frozen |
| B1 | cheap proxy + fixed gamma | 固定cheap frontier | 4 armを独立評価 |
| B2 | `I_C` only | cheap適応で十分か | 最大一方式、未実装 |
| M1 | fixed spectral module | always-on高情報基準 | module変更なし |
| H1 | B2と同じ`I_C` + selective `I_S` | 選択取得候補 | 未実装 |

## Effect decomposition

### Domain intervention effect

`domain_intervention_effect(A) = metric(A) - metric(B0)`

B0から長時間候補へ移る介入全体を測る。HFにおける約25–35%の改善をspectral固有効果と呼ばない。

### Adaptive cheap effect

`adaptive_cheap_effect = metric(B2) - metric(pre_frozen_B1_reference)`

B1 referenceはtruth後に条件別最良gammaへ置き換えない。B1四armの結果とoracle frontier diagnosticを分離する。

### Spectral incremental effect

`spectral_incremental_effect = metric(spectral_enabled) - metric(identical_cheap_layer)`

H1対B2ではcheap features、cheap policy、candidate set、fallbackを一致させる。M1対B1はhistorical fixed-arm comparisonであり、H1対B2と同じ因果差とはみなさない。

### Selective acquisition effect

`selective_acquisition_effect = H1 - M1`

同じ安全性・coverageと、事前固定quantum-budget非劣性条件の下で、総校正費用vectorが改善したかを測る。query率低下だけでは成功としない。

## Primary scoring

各condition/familyおよびaggregateで次を保存する。

- unsafe countと危険な過小評価。
- execute coverage、fallback、abstention。
- frozen continuous budget、`B/B0`、`t/T0`。
- spectral request、adoption、invalidation、failure、wasted-query rate。
- wall time、peak memory、PF actions、H matvec、H exponential、materialization、sparse multiply。

異なるcoverageで成功例だけを平均しない。unsafe armは低budgetでも勝ちに数えない。fallbackも誤差・budget・費用を採点する。

## Two admissible success modes

1. **Classical-cost improvement**: H1がM1に対して安全性・coverageとquantum noninferiorityを維持し、総校正費用を減らす。
2. **Quantum-budget improvement**: H1がB2に対して安全性・coverageを維持し、事前固定classical budget ceiling内で量子予算を減らす。

両方を満たすことは強い結果だが必須としない。Pareto非劣解の場合は比較範囲を限定して報告する。

## Diagnostic-only references

- condition-wise oracle gamma。
- oracle choice between cheap and spectral。
- post-hoc best candidate。
- true required gamma。

これらは上限・機構診断であり、B2/H1入力や運用baselineへ昇格させない。

## Pending numerical decisions

- quantum-budget noninferiority margin。
- classical-information budget ceiling。
- minimum practical effect size。
- query budget。
- aggregate weightingとfailure priority。

HFの保存1–3%差を使って事後的に決めない。これらがfreezeされるまで科学実行を承認しない。

## Valid negative outcomes

`no_query_needed`、`cheap_only_sufficient`、`always_on_M1_preferred`、`cheap_features_not_discriminative`、`M1_transfer_failed`、`no_material_methodological_gain`を正式な停止先とする。
