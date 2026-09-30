# 第2研究v2：選択的校正によるdomain損失への介入

Status: `second_study_v2_selective_calibration_design_complete_review_required`

## 1. 研究目的

第1研究で確認した有限時間domain由来の資源損失に対し、cheap情報だけで判断する方式と、必要時だけ追加spectral情報を取得する方式を公平に比較する。中心問題は推定器の精度競争ではなく、追加情報の取得が最終的な時刻・予算判断を変える価値を持つ条件と、その情報費用である。

第1研究、旧second-study、D1/D2/C0、HF pilot、HF bridgeの正式statusは変更しない。今回の成果はdesign protocolであり、科学計算、policy fit、threshold fit、holdout開封の承認ではない。

## 2. 検証済みprovenance

- HF pilot result: `0166c0de2308163777689fe4b641289ac26e33ae`
- HF bridge content: `d74d9020c2e1e97cdf120e8a0974d45cb296da4a`
- HF bridge provenance: `36989cd0a2fe8b843ec2375ec344bebcc2c9ef0c`
- HF bridge manifest SHA-256: `03be5b9ca8aadc2eef444b3bade9a4b9d512228e48517a601f1418eee9fcaf9f`

bridge原本は今回ローカルGitから直接照合した。したがって`user_report_only`ではなく、origin content commit、provenance commit、今回のverified snapshotを分けて記録する。

## 3. 研究上の固定事項

### 3.1 B2 cheap-only

`B2`はcheap情報集合 `I_C` だけから、最終的な `(t, B, execute/fallback/abstain)` を返す最大一方式のdevelopment candidateである。B2の数値ruleは未確立であり、今回fitしない。

### 3.2 H1 selective spectral

`H1`はB2と同じcheap情報、同じcheap policy、同じ候補集合から開始する。取得rule

`I_C -> q in {0,1}`

と、最終rule

`(I_C, q I_S) -> (t, B, execute/fallback/abstain)`

を分離する。H1だけcheap特徴、threshold、fallbackを有利に変更しない。B2が未確立の段階では、H1のcheap layerを固定B1 armに置く場合があるが、その比較にはcheap policy差の交絡を明記する。

### 3.3 固定M1 module

最初のdevelopmentではM1の候補grid、`m<=8`、prefix、経験的width、branch/reference手順を変更しない。候補単位の適応取得、m増加、width再調整を同時探索しない。経験的widthを数学的certificateとは呼ばない。

### 3.4 効果の分離

次の量を混同しない。

1. `domain_intervention_effect`: B0に対する、より長い時刻を使う介入全体の効果。
2. `adaptive_cheap_effect`: 事前固定B1に対するB2の増分効果。
3. `spectral_incremental_effect`: 同一cheap layerにspectral情報を加えたことによる増分効果。
4. `selective_acquisition_effect`: always-on M1に対し、必要条件だけ問い合わせることによる情報費用の変化。

HF pilotの`robust_signal`は保存するが、M1が各条件で全cheap armより優れたという意味へ拡張しない。

## 4. 情報境界

### 4.1 取得前に許可する情報

- 固定source identityとtask constants。
- cheap proxy値と、同じcheap取得から得られるtrajectory、local consistency、echo/cancellation。
- `A_eta`、cheap budget、candidate間のbudget差、目標までの余裕。
- 取得費用を測定できる場合の近似state Hamiltonian residual。
- remaining classical-information budget。

分子名、equilibrium/stretchラベルを正解routeとして使用しない。

### 4.2 取得前に禁止する情報

- direct truth、true gamma、true gap、scorer safety。
- M1 prefix、M1 width、M1 Ritz residual、M1 branch結果。
- 他armの未取得出力。
- exact-state overlapなどoracle diagnostic。
- held-out familyの情報。

### 4.3 取得後の最終判断

`q=1`でもM1出力を必ず採用する必要はない。ただしM1観測がcheap候補を不適格とした場合、安さだけを理由にcheap budgetを維持してはならない。同一時刻でcheap budgetを保持する内部整合条件は、

`e_use_S(t_C) + beta*K/(t_C*B_C) <= epsilon_E`

である。別時刻のspectral結果で未評価cheap時刻を救済しない。branch/referenceがindeterminateなら事前固定fallbackまたはabstentionへ進む。

## 5. Freezeとscorerの順序

1. source、environment、tuple identityを検証する。
2. cheap情報を取得する。
3. B2 cheap decisionとH1 acquisition decisionをfreezeする。
4. `q=1`の条件だけ固定M1を取得する。
5. H1 final actionをfreezeする。
6. freeze artifactをcommit/hash固定する。
7. その後だけtruthを開いてB0/B1/B2/M1/H1を採点する。

`spectral_requested`、`spectral_result_used`、`spectral_observation_invalidated_cheap`、query failure、fallbackを別fieldにする。取得後に不採用でもquery費用は全額計上する。

## 6. 比較arm

- `B0`: 第1研究のhistorical baseline。
- `B1`: gamma `1.01, 1.02, 1.05, 1.10`の独立frozen arms。
- `B2`: cheap-only adaptive candidate、最大一方式。
- `M1`: always-on fixed spectral module。
- `H1`: B2と同じcheap policyにacquisition gateを加えた方式。

truthから条件別に最良gammaやC/Sを選ぶoracleはdiagnosticのみである。selectivityを主張する場合は、同じquery budgetの非選択scheduleを一つ事前固定する。

## 7. Matched-data coverage

`paired_data_coverage.csv`はcondition、Hamiltonian、state、PF、absolute time、candidate rule、budget constants、evidence stage、費用scopeを区別する。

- HF 2条件×3座標: cheap、M1、truth、各arm costが同じfrozen tupleで揃う。combined H1のshared/reuse込み実測費用はない。
- HCl 2条件×3座標: same-H/state/timeのcheap、M1、truth、個別costが存在する。ただしHFとはcandidate contractと研究stageが異なり、そのままpoolしてpolicyをfitしない。combined H1費用も未測定。
- LiF 2条件: cheap/truth diagnosticはあるが、保存M1 runがなく完全tupleではない。
- N2/CO: cheap featureは存在するが、このdesign contractに対するcheap/M1/truth/cost完全tupleは未監査である。

不足値を近傍座標、補間、別state、別stageで埋めない。

## 8. Resource accounting

条件iの総校正費用を

`C_total_cal = C_shared + C_cheap + q*C_spectral_given_cheap + C_decision`

とする。wall time、peak memory、PF actions、H matvec、H exponential action、component-gate materialization、sparse multiply、cache/reuseを別々に保持する。CPU秒とrotation countを合算しない。

HF保存時間の`cheap all + queried spectral`単純和はno-reuseのpost-hoc scenarioであり、実測H1費用ではない。zero counterは意味が確認できない限り`unknown_or_unmeasured`とする。

## 9. Successと停止先

Primaryはfinal decisionでのunsafe件数、coverage、fallback/abstention、frozen budget、`B/B0`、`t/T0`、query/adoption/wasted-query rate、古典費用vectorである。

二つの勝ち方を分ける。

- M1に対して量子予算非劣性とcoverageを保ちながら総古典費用を減らす。
- B2に対して所定古典budget内で量子予算を減らす。

no-query、cheap-only sufficient、always-on M1 preferred、cheap特徴で識別不能、M1 transfer failure、実質的新知見なし、はいずれも正式な終了結果である。

## 10. 今回未確定の数値条件

以下は`unresolved_requires_review`のまま保持する。

- B2 featureとnumerical threshold。
- H1 escalation featureとthreshold。
- quantum-budget noninferiority margin。
- classical-information budget ceiling。
- minimum practical effect size。
- development family/fold boundaryと最大paired acquisition scope。
- independent holdout design。

HF 2条件の事後差へ合わせて決めない。

## 11. Related-work role map

- Mehendale et al., *Estimating Trotter Approximation Errors to Optimize Hamiltonian Partitioning for Lower Eigenvalue Errors*, arXiv:2312.13282v3: PF固有値誤差推定とtime-step/resource判断に近いcore related work。今回その推定器を追加armとして実装しない。<https://arxiv.org/abs/2312.13282>
- Mozannar and Sontag, *Consistent Estimators for Learning to Defer to an Expert*, ICML 2020, PMLR 119:7076–7087: 予測するか別情報源へ委譲する設計のconceptual background。分類lossや整合性定理をPF安全性へ転用しない。<https://proceedings.mlr.press/v119/mozannar20b.html>
- Kandasamy et al., *Multi-fidelity Bayesian Optimisation with Continuous Approximations*, ICML 2017, PMLR 70:1799–1808: cheap/high-fidelity取得を選ぶ発想のconceptual background。BOCAやGPを実装しない。<https://proceedings.mlr.press/v70/kandasamy17a.html>
- Maxwell et al., *Practical Estimation of Trotter Error for Hamiltonian Simulation*, arXiv:2606.30738v1: compact BCH等の関連する高精度誤差推定。最初の比較armへ自動追加しない。<https://arxiv.org/abs/2606.30738>

selective acquisition、learning-to-defer、multi-fidelityという一般概念自体を新規性としない。新規性候補はPF/QPE固有のbudget、安全性、branch/state failure、取得前情報境界、古典費用を同じprotocolで分離する点である。文献調査は網羅的な新規性証明ではない。

## 12. 次の停止点

本設計完成後はmatched-data coverage reviewで停止する。既存development dataだけで一つの限定prevalidationが可能か、不足tupleだけを別承認で取得する必要があるかを判断する。今回、B2/H1 implementation、科学計算、fit、holdout、C1、D2-B、新PF、外部baselineは許可しない。
