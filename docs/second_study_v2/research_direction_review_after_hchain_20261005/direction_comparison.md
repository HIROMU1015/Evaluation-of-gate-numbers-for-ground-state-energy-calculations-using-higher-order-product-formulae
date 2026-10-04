# 4つの研究方向の比較

このrankingは既存証拠に基づく研究運営上の判断（`governance_scope`）であり、測定値・採択確率ではない。5段階はすべて「5ほど今回の主線として有利」とする。リスク・計算負担・rare-case依存は低いほど高得点。重み付き合計によるpseudo-objective rankingは作らない。Noveltyは[外部照合の限定](novelty_assessment.md)を伴う。

| 評価軸 | A selective spectral主線 | B cheap-only adaptive主線 | C decision value / regime主線 | D spectralをnegativeとして閉鎖 |
|---|---:|---:|---:|---:|
| Scientific importance | 4 | 4 | 5 | 3 |
| Novelty potential（未確定） | 3 | 2 | 3 | 2 |
| 第一研究との接続 | 4 | 4 | 5 | 3 |
| 既存証拠の支持 | 1 | 3 | 5 | 3 |
| Falsifiability | 4 | 4 | 4 | 3 |
| Additional computation負担の低さ | 2 | 4 | 5 | 5 |
| Post-hoc tuning riskの低さ | 1 | 3 | 4 | 4 |
| Negative-result robustness | 2 | 3 | 5 | 3 |
| Publication story clarity | 2 | 3 | 4 | 3 |
| Rare q=1 case非依存性 | 1 | 5 | 5 | 5 |
| Fixed cheapだけで説明されるリスクの低さ | 1 | 2 | 5 | 4 |
| Reproducibility / preregistration compatibility | 3 | 4 | 5 | 4 |

## Ranking：C > B > D > A

1. **C**はcheap sufficiencyもspectral不利益も小さいpositiveも同じ問いの答えとして受け止める。固定cheap比較、width、取得費用、formal Dを含むことが必要で、曖昧な「regime-dependent」で終わらない。
2. **B**は実証基盤が強い代替。ただし支持されるのはcheap-firstであり、adaptive B2の追加利益ではない。研究をadaptive新方式として売るなら、fixed gammaに対する新しい証拠が必要。
3. **D**はtested H-chainでspectral主線を停止する判断として堅牢。しかし全spectral routeの一般的否定ではHFの小さいaggregate利益とgeneral-molecule q未実行を無視する。単独論文のnegative claimはscopeを強く限定する。
4. **A**は重要で反証可能だが、主要6条件を満たすexecution証拠がまだない。q=1を探すこと自体が目的になると新規計算とpost-hoc自由度が増える。

## Aの必要条件の監査

| 必要証拠 | 現状 |
|---|---|
| General moleculeで非自明なq=1 | 未取得。S1A Dはqの評価結果ではない |
| q=1がtruth上合理的 | 未採点 |
| H1がB2を改善 | 未取得。H-chainはH1=B2 |
| Fixed cheap frontierでは同じ結果を得られない | 未確立。HF各条件にはM1より安いsafe cheap、H-chain fixed1.01と同じ |
| Always-M1より取得量を減らす | H-chainではq=0でM1取得を省いたが、quantum actionはfixed cheapでも説明可能。q=1を含むnontrivial selective性能は未測定 |
| Classical overheadが許容可能 | q=1 combinedと許容ceiling未取得。Secondsとquantum rotationsの相殺モデルなし |

## Bを過大評価しない

H-chainの約33%は固定candidateでbenchmark anchorより改善した効果である。Gamma frontier内の適応を不要にした事実も含む。HFではcondition-wise oracle gammaがM1より安いが、そのtruth-free選択法は未確立。したがって「cheapが十分→adaptive cheapが新規で有効」には進まない。

## Cに必要な反証可能性

同じPF/state/candidate contract内でsafe decisionを比較する。Additional spectral取得がcheapのunsafeを避け、fixed cheapより少ないsafe budgetを示せば、spectralの条件付き価値を認める。逆に全差がfixed margin/domainで説明できれば追加情報不要と記録する。Cost不明・tuple不足は効果0ではなく未評価。Condition間を混ぜた一つの改善率ではなく、勝敗と分母を残す。

## Dの閉鎖範囲

現在終了すべきなのは、tested H-chainでの追加spectral拡張と、精度・certificateを無条件に主線にする探索である。一般分子のspectral不要を断定することではない。HF-only replayがno-valueまたはgate failureでも、元HF `robust_signal`やD2-A formal statusを後から書き換えない。
