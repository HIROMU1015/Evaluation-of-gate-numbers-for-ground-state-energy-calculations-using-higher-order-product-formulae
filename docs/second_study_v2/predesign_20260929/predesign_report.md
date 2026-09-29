# 第2研究v2 pre-design analysis

状態：`second_study_v2_predesign_complete_review_required`
基準identity：`599a9f2e9a45302b8d34192ef581fd3ea55a1f1e`
実行規約：`4c579886b49d1c0aef7362809ed5e41a7a77d660`

## 1. Objectiveとevidence boundary

本分析は、第1研究で分解したresource regretを、有限の追加校正による介入設計へ接続するためのread-only pre-designである。Git-trackedな保存済みCSV/JSON/reportだけを使用し、新しいHamiltonian、state、PF truth、PF/H作用、Arnoldi、gap、fit、selector、threshold、GPU計算は0である。保存truthはpost-hoc scorerとしてのみ読んだ。

第2研究v2の方法は決定しない。結論はheadroom、operational information availability、保存された情報費用を人間が比較できる形に整理するところまでである。

## 2. 第1研究との接続

第1研究は`F_total = F_model F_margin F_within F_domain F_PF`を用い、安全性と効率、point accuracyとresource decisionを分離した。保存6条件ではPF選択損失は0だった。一方、N2/COではmodelまたはwithin-domain time selectionが主なexact factorとなり、HFではdomain制約に大きなbound headroomが残った。operator-sensitive risk detectionを含む後続固定比較はresource benefitを確立しなかった。

本pre-designは、このdiagnosisに対して、(a) isolated-factor algebraic headroom、(b) operationalに取得可能な情報、(c) 既測定の古典費用、(d) decision-changing potentialを対応付ける。

## 3. Resource-loss map

第一研究6条件では、exact comparable factorだけを`log(F)`で順位付けした。

| condition | dominant exact resource factor | F_total | 主な限定 |
|---|---:|---:|---|
| N2_active_eq_sto3g | F_model | 1.100631 | exact_comparable_factors |
| N2_active_stretch150_sto3g | F_within | 1.423985 | exact_comparable_factors |
| CO_active_eq_sto3g | F_model | 1.120734 | exact_comparable_factors |
| CO_active_stretch150_sto3g | F_model | 1.193383 | exact_comparable_factors |
| HF_full_eq_sto3g | indeterminate | 2.150313 | exact_and_bounded_factors_not_ranked_together |
| HF_full_stretch150_sto3g | indeterminate | 2.102857 | exact_and_bounded_factors_not_ranked_together |

HFでは`F_within`と`F_domain`がinterval boundなので、exact factorと混ぜたdominant判定は`indeterminate`とした。R1のmodel/state/proxy成分はresource factorへ変換せず、C0 HClはsame-time budget ratioとしてのみ記録した。詳細は`resource_loss_map.csv`にある。

## 4. Intervention headroom

`H(F)=1-1/F`は、他factorを固定して当該factorだけを1へ置換する`isolated_factor_algebraic_headroom`である。実際の介入可能性や達成可能な最大削減率ではない。

- 最大のfactor別headroom候補はHF equilibriumの`F_domain`で、保存boundから約`52.711057%`–`53.304508%`。HF stretchも約`51.682967%`–`51.838825%`。
- N2 stretchのexact `F_within` headroomは`18.540233%`。
- same-time model+margin headroomはN2/COで約`7.204337%`–`13.791234%`。
- HCl C0の保存same-time perfect-calibration効果は`0.327975%`–`2.286462%`。HF domainとはsystem、task、baseline、time freedomが異なり比較不能である。
- 固定multiple-window ruleはcurrent fallback比でaggregate budgetを`10.661933%`下げたが、1/4 unsafeかつ固定benefit gate不合格で`complete_no_benefit`だった。

`intervention_headroom.csv`はfactor algebra、保存counterfactual、固定intervention結果を別fieldにする。

## 5. Information accessと費用

取得可能性とcertificate十分性は一致しない。

- local CISD proxy、fit residual、multiple-window consistency、Hamiltonian residual、prefix stability、projected Ritz値/gap、Arnoldi residualはtruth-free候補として取得可能。
- projected gapはfull-space gapではなく、prefix stabilityはheuristicである。これら単独ではground/branch/resource targetをcertifyしない。
- D1 true gap、exact-ground proxy、direct PF shift、full PF spectrum、branch-connected truthはoracle/scorer-only。
- `g_rho_others`のtruth-free full-space lower boundは未確立である。

保存された費用は次の通りだが、workloadとcache境界が異なるため単純比較しない。

| stage | saved workload | wall | peak memory |
|---|---|---:|---:|
| Phase A multiple-window acquisition | 44 proxy/PF-state actions、44 H exponential actions、4 state/group builds | 131.803 s | 784148 KiB |
| R1 mixed diagnosis | 5 new CISD proxy、10 exact proxy、4 exact ground | 91.433 s | 1239684 KiB |
| D1 oracle spectral diagnostic | 6 full PF build/eigendecomposition、2 exact ground | 3.761 s | 457204 KiB |
| D2-A truth-free predictor | 48 PF actions、48 H matvecs | 2.617 s | 454656 KiB |
| Phase B direct truth | 42 direct points | 4068.031 s summed | 3108804 KiB CPU / 3011 MiB GPU total |

## 6. Decision-changing headroom

### I: headroom大 × truth-free情報あり

現時点で**確立した例は0**である。multiple-window consistencyはoperational情報だったが、固定方式は1/4 unsafeで正式にno-benefitだったため、成功したIとは数えない。

### II: headroom大 × truth-free情報未確立

最も明確なのはHFのdomain restrictionである。factor headroomの保存区間は約51.68–53.30%にある一方、安全にdomainを拡張するoperational certificateはない。N2/COのmodel/within headroomにも5%を超える保存例があるが、どのtruth-free signalがdecision改善を保証するかは未確立で、threshold依存の候補に留めた。

### III: 高精度情報あり × headroom小

HCl D2-Aは保存development 6座標で最大absolute shift errorが`1.382529828669297e-08 Ha`、physical branch 6/6整合だった。一方、同一時刻の保存校正headroomは`0.327975%`–`2.286462%`で、主baseline未満の予算は0/6だった。これはpoint-estimation精度をさらに上げる優先度が低いことを示す限定的なIII例であり、一般分子やtime selectionへ一般化しない。

materiality thresholdは固定していない。1%、5%、10%、20%列はdescriptive sensitivityだけである。

## 7. Q1–Q5へのdescriptive回答

1. **最大headroom**：保存factorではHF `F_domain`。ただしanalytic boundかつcap外を実行可能にする証拠ではない。
2. **truth-free情報**：候補observableは複数あるが、最大headroomに対する安全なdomain certificateは未確立。
3. **高精度でもdecisionが変わりにくい領域**：HCl D2-A/C0のsame-time taskが該当する。
4. **既測定cost**：truth-free D2-AはHCl6点で48 PF+48 H actions、2.617 s。Phase Aは44 proxy点で131.803 s。direct truthは42点で4068.031 s。ただしcache/workload差を保持する。
5. **三分類**：Iは確立0、IIはHF domainが中心、IIIはHCl same-timeが明確。N2/CO model/withinはmateriality thresholdに依存するII候補。

## 8. Data-use boundary

H-chain、LiH、BeH2、H2O、NH3、CH4、N2、CO、HFは旧ledgerで使用済みである。LiF/HClは旧ledger作成後に第二研究以降で使用済みとなったため、R1–C0の監査済みsourceで補完した。今回参照した全systemは将来の第2研究v2独立holdoutには数えない。未使用分子の探索・列挙は行っていない。

## 9. Unresolved itemsと停止

- largest headroomへ作用するtruth-free domain/certificate情報が未確立。
- `g_rho_others`、ground/reference、branch/alias、PF/H action forward errorのoperational certificateが未確立。
- factorは介入で相互変化し得るため、isolated algebraic headroomは因果効果ではない。
- 古典費用はsmall cached HClやmixed workloadsの保存値で、scaling lawではない。
- materiality、成功基準、method、holdoutは未固定。

ここで停止する。C1、D2-B、method/selector/threshold実装、holdout、新PF、新分子は未承認である。次は`full_second_study_v2_research_direction_review`である。
