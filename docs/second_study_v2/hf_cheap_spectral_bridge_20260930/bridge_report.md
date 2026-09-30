# HF cheap-vs-spectral mechanism/value bridge analysis

Status: `second_study_v2_hf_bridge_complete_review_required`

## 1. Objective

HF domain-intervention pilotの`robust_signal`を、cheap local CISD proxyで十分だった部分と、M1 spectral informationがdecisionを変えた部分へ分解した。目的はadaptive marginや新方式を作ることではなく、次の第2研究v2方針を人間が選べるように、保存済みprediction、post-freeze scorer truth、過去diagnosticを分離して整理することである。

新しいHamiltonian、state、PF/H作用、Arnoldi、direct truth、gap、fit、threshold、selector、GPU計算は0である。

## 2. Evidence boundary

- `frozen_truth_free_prediction`: prediction commit `b0d3ad687807f64155175f3e7a81bdec869543b9`に固定されたHF 6座標のB1/M1 feature、selection、budget、resource count。
- `post_freeze_truth_scoring`: result commit `0166c0de2308163777689fe4b641289ac26e33ae`で初めて利用されたdirect shift、phase gap、安全性、branch correctness。
- `post_hoc_bridge_arithmetic`: 保存値だけから行った差、比率、共通safe gamma、condition-wise oracle gammaの算術。
- `post_hoc_development_diagnostic`: R1、D2-A audit、C0など、過去に原因解釈のため取得済みの診断。

`hf_truth_free_feature_table.csv`にはtruth fieldを入れていない。`hf_truth_scoring_table.csv`は全行で`truth_used_for_post_hoc_scorer_only=true`とした。

## 3. HF pilot recap

M1と全B1 gamma armは両条件で同じ`1.6T0`を選択した。M1は両条件でbranch valid、safe、T0 reproduction pass、10% resource-reduction target達成となり、固定classificationは`robust_signal`である。

M1 point estimateのabsolute errorは、HF equilibriumで`1.1266264553e-11 Ha`、stretch150で`4.83737731e-13 Ha`だった。empirical widthはそれぞれ`4.6211073185e-6 Ha`と`1.3757152795e-6 Ha`で、両方ともpoint errorを覆った。これは保存development 2条件での結果であり、certificateや独立一般化ではない。

## 4. Cheap proxy recap

固定B1 armのselected-coordinate安全性は次の通りである。

| Condition | γ=1.01 | γ=1.02 | γ=1.05 | γ=1.10 | Post-hoc minimum safe γ |
|---|---:|---:|---:|---:|---:|
| HF equilibrium | unsafe | unsafe | unsafe | safe | 1.10 |
| HF stretch150 | safe | safe | safe | safe | 1.01 |

B1のγはPF誤差値へ直接掛ける係数ではなく、同じproxyから作ったunmargined continuous budgetへの倍率である。従って保存protocolから曖昧なく定義できる連続要求量は、

`continuous_gamma_required_from_truth = direct_required_budget / proxy_unmargined_budget`

である。保存truthを用いたpost-hoc値はequilibriumで`1.0949943864`、stretch150で`1.0037134494`だった。これはoperational selectorではない。

selected pointでcheap proxyの絶対値がdirect absolute PF errorを下回った量は、equilibriumで`1.2830006801e-5 Ha`、stretch150で`5.6301883897e-7 Ha`だった。一方、stretchではcheap signed shiftが負、direct shiftが正であり、signed point errorは大きい。これはmechanism用signed accuracyと、budgetへ入るabsolute PF errorを同一視できないことを示す。

## 5. Common fixed-safe gamma comparison

2条件を同時に覆う最小の保存済み固定armはγ=1.10だった。

| Quantity | HF equilibrium | HF stretch150 | Aggregate |
|---|---:|---:|---:|
| M1 frozen continuous budget | 351,773,269.594 | 220,709,224.760 | 572,482,494.354 |
| B1 γ=1.10 budget | 341,290,363.699 | 239,687,172.510 | 580,977,536.209 |
| M1 saving relative to B1 γ=1.10 | -10,482,905.894 | 18,977,947.750 | 8,495,041.855 |
| Relative saving vs B1 γ=1.10 | -3.0716% | 7.9178% | 1.4622% |

従ってM1はaggregateではγ=1.10より1.46%低予算だが、condition-wiseにはequilibriumでB1 γ=1.10の方が低予算である。`robust_signal`はM1が両条件でsafeかつstrong targetを満たし、固定B1 armがaggregateでM1をmatch/dominanceしなかったというpilot規則に基づく。1.46%を一般的効果量とは扱わない。

全6候補を取得するための保存情報費用は、M1が`0.493343 s`、48 PF actions、48 H matvecs、B1が`0.273952 s`、6 PF actions、6 H exponential actionsだった。H matvecとH exponential actionは同じ単位ではないので、単純なaction差を単一costへ変換しない。peak CPU RSSは`446460 KiB`、GPU operationは0だった。

## 6. Oracle conditionwise gamma diagnostic

truthを見てconditionごとに保存frontier上の最小safe gammaを選ぶと、equilibriumは1.10、stretch150は1.01となり、aggregate budgetは`561,366,767.549`である。これはM1より`11,115,726.804`、M1比`1.9417%`低い。

この`oracle_conditionwise_gamma_reference`は、condition-adaptive cheap marginに価値余地があることを測るpost-hoc diagnosticに限る。どちらのgammaを選ぶかはprediction freeze時点で知られておらず、operational baselineでもvalidated policyでもない。

## 7. Truth-free feature differences

Q1に対するdescriptive回答は、単一の状態品質値ではなく、長時間側でのlocal echo trajectoryとspectral residual/widthの違いがmargin差と同時に変化した、である。

- cancellation indexの`1.3T0 -> 1.6T0`増加率はequilibrium `1.8423`、stretch `1.0211`。
- cheap `abs(proxy)`の同区間増加率はequilibrium `2.2723`、stretch `1.6543`。
- diagonal signalの同区間増加率はequilibrium `2.7967`、stretch `2.0361`。
- selected M1 widthはequilibriumがstretchの約3.36倍、selected U Ritz residualは約2.62倍。
- 逆にselected state errorとfinal H-reference residualはstretchの方が大きい。従ってstate qualityだけで必要marginを順序付ける説明には反証的である。

これらは2条件の同時変化であり、相関、有意性、因果性、thresholdを示さない。

## 8. Candidate mechanisms

Q2、Q3への整理は次の通りである。

1. **Local finite-time proxy curvature**: cancellation、echo shift、diagonal signalの長時間成長差は、model/extrapolationまたはproxy--eigenvalue誤差の候補である。cheapに取得できるが、HF 2条件からmargin ruleは作れない。
2. **Spectral residual and width**: equilibriumの広いM1 widthはfinite-time spectral contamination/uncertainty候補である。M1の追加価値は高精度point estimateだけでなく、prefix、H-reference、U Ritz residual、branch candidateを同時に記録したことにある。ただしwidthはempiricalでcertificateではない。
3. **State substitution alone is insufficient**: stretchのstate errorとH residualが大きいのにcheap required gammaは小さいため、state quality単独のadaptive marginはこの2条件を説明しない。
4. **Signed accuracy and budget accuracy differ**: stretchではcheap signed shiftが符号を外したが、absolute magnitudeはdirect PF errorに近くγ=1.01でsafeだった。M1は符号・branch mechanismを回収したが、QPE budgetの安全性はabsolute errorで採点される。

M1の価値を分離すると、point-estimate accuracyは両条件で明確、branch/reference stabilityとprefix convergenceも全候補で合格した。一方、explicit widthはequilibriumではsafe B1より予算を増やす側に働き、stretchでは共通γ=1.10の過剰marginを避けるのに寄与した。従って「widthが常に資源を減らす」とは結論しない。

## 9. Can existing development data test them?

新規計算なしのavailability監査では、local echo/cancellation trajectory、state/H residual、fitまたはmultiple-window stabilityはN2、CO、HF、LiF、HClの既存development artifactに存在する。定義、候補時刻、取得stageは同一ではないため、現在の値を直接poolしてthresholdを作ることはできない。

M1 prefix/residual/branch fieldはHFとHCl D2-Aにのみ保存され、N2、CO、LiFには保存実行がない。新規PF/H actionsなしには補完できないため、本analysisでは`not_available`とした。

これは次のdevelopment prevalidationに入力候補があるかのinventoryであって、安全性ruleのvalidationではない。

## 10. Implications for second-study-v2

Q4のresource差は次のように分解できる。

- **HF equilibrium**: cheap proxy magnitudeの過小評価が大きく、γ≈1.095を要した。B1 γ=1.10はsafeでM1より約10.48M低予算だった。M1 point estimateは正確だが、4.62e-6 Haのempirical widthを加えたため、同条件ではspectral情報がresource advantageを持たなかった。
- **HF stretch150**: cheap signed estimateは符号を外したがabsolute magnitude biasは小さく、γ≈1.0037で足りた。共通固定γ=1.10は過剰で、M1は1.38e-6 Haのwidth込みでも約18.98M低予算だった。
- **Aggregate**: 条件ごとの勝敗が相殺され、M1 advantageは1.46%に留まる。一方、oracle adaptive cheap frontierはM1より1.94%低く、cheap adaptive marginを調べる価値余地はあるが、選択signalは未確立である。

Q5への答えは、**candidate mechanismは存在するがvalidated ruleは存在しない**、である。次のレビュー材料は以下である。

- cheap adaptive margin方向: local trajectory/cancellationの既存dataを同一定義へ揃える価値があるか。
- selective spectral calibration方向: cheap featureが不安定な条件だけM1を払う設計に価値があるか。
- hybrid direction: cheap screeningとspectral escalationを分離できるか。
- no additional value direction: 1.46% aggregate gainと追加情報費用が小さすぎると判断するか。

本analysisは最終方針を選ばない。B2、threshold、selector、external baseline、holdoutは未承認である。

## 11. Limitations

- HF 2 conditions only、same molecule。
- CISD stateは非常に高品質で、他systemのstate-substitution regimeを代表しない。
- resource metricはcontinuous rotation-cost proxyで、離散QPE query modelではない。
- candidate gridは`T0,1.3T0,1.6T0`に固定。
- M1 widthはempiricalで、full-space gap、ground/reference、forward-error certificateを持たない。
- common safe γとcontinuous required γはtruthを用いたpost-hoc scorer arithmetic。
- condition-wise oracle gammaはoperational methodではない。
- existing development featureは定義・time grid・evidence stageが異なる。
- independent generalization、new molecule、new PF、external baseline comparisonは行っていない。

ここで`second_study_v2_hf_bridge_complete_review_required`として停止し、次は`full_second_study_v2_research_direction_review`とする。
