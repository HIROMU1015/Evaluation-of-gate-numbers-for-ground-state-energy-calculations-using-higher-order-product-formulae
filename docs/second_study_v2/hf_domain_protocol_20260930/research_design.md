# 第2研究v2：HF domain-intervention pilot研究設計

状態：`second_study_v2_hf_domain_protocol_complete_review_required`

## Research question

第1研究でHF 2条件に残った大きなtime-domain損失に対し、固定された少量のtruth-free追加校正が、QPEの時刻と予算の判断を安全に変えるだけの資源価値を持つかを調べる。

中心はPF誤差推定器の精度競争ではなく、

> resource loss → 必要情報 → 情報取得費用 → safe resource decision

の接続である。Arnoldi/Krylovは既存の情報取得部品であり、新規手法として主張しない。

## Evidence connection

- 第1研究の保存factor分解では、HF equilibriumの`F_domain` headroom boundは52.711–53.305%、HF stretchは51.683–51.839%だった。
- これは`isolated_factor_algebraic_headroom`であり、介入で実現できる因果的削減率ではない。
- cap内改善余地はそれぞれ約1.255%、0.323%であり、大きな改善にはcap外の判断が必要である。
- pre-designでは「headroom大 × 成功済みtruth-free operational information」の分類Iは0だった。
- D2-A scoring auditはHCl development 6点でphysical branch 6/6と高精度point estimateを確認したが、main baselineより低い予算は0/6だった。従ってpoint accuracyだけを研究目的にしない。

## Pilot scope

- conditions: `HF_full_eq_sto3g`, `HF_full_stretch150_sto3g`
- PF: `current_m3`
- state: 第一研究と同一のoriginal CISD
- candidate grid: `{T0, 1.3T0, 1.6T0}`
- `T0`はcontrol/fallbackであり、domain intervention成功は`t>T0`のみ。
- primary proposal: `eta=0.10`。実行前の人間承認が必要。

## Arms

1. `B0`: 第一研究の`(T0,B0)`。
2. `B1`: 同じcandidate gridのlocal CISD proxy。gamma 1.01/1.02/1.05/1.10は独立armとしてfreezeする。
3. `M1`: D2-Aのexplicit-vector unitary Arnoldi (`m<=8`) と同じ経験的width。

外部手法はHF pilotへ追加実装しない。resource-aware signalがあり、cheap proxyがdecisionを再現せず、比較がArnoldi固有効果と一般的高精度校正を識別できる場合だけ、別承認で最大1方式を検討する。

## Decision rule

提案`eta`が承認された場合、`B_target=(1-eta)B0`とし、

`A_eta(t)=epsilon_E-beta*K/[t*B_target]`

を計算する。`A_eta<=0`は構造的棄却、gate不合格はabstain、`e_use<=A_eta`だけをeligibleとする。eligible候補から最小の凍結予算を選び、同値なら短い時刻を選ぶ。eligibleなcap外候補がなければB0へfallbackする。

予測とtruth採点は別processにし、predictionをcommit/hash固定するまでtruthを開かない。

## Scoring

1. source/truth evaluability
2. representation-independentなbranch/reference validity
3. frozen-budget safety
4. `t>T0`
5. eta target
6. safe local-proxy frontierに対する追加価値
7. quantum resourceとclassical information costの分離

absolute-energy unwrap integerとground-removed shift integerの直接一致は採点に使わない。

## P0 stop

今回のP0は設計と既存sourceの静的照合だけで停止する。eta、budget discretization、wall limit、runtime cache、cap外4 truth、実装/testは未承認である。P1、C1、D2-B、holdout、新PF、外部baselineへ自動進行しない。
