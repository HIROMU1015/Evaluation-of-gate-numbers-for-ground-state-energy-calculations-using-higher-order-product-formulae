# 第一研究 S4 protocol v1：operator-sensitive状態収束診断

## 目的

S3で選んだ一方式だけを開発比較する。full CISDの係数をexact情報なしで99%累積
ノルムへ決定論的にtruncateし、full/truncated CISDのsigned echo proxy差を
PF別・有限時刻別に測る。差が大きいPFだけ既存の`0.5 t_ana`上限へ送る方式が、
全条件を保守化する方法または同じ4追加作用を時刻fitへ使う方法より効率的か判定する。

これは状態誤差の上界ではなく、CISD tailに対する局所的なoperator-sensitive安定性
診断である。「二状態が一致したのでexact stateにも近い」とは解釈しない。

## 固定範囲

- development主条件：N2/CO active-spaceの平衡・stretch150。
- stress条件：HF分子full-electronの平衡・stretch150。
- PF：`current_m3`, Yoshida4。
- 目標精度、PF係数、分割、rotation数、二項モデル、元fallbackは既存practical
  v1.1から変更しない。
- S4 protocol JSONを正本とし、本文と競合するときはJSONを優先する。

## 診断と閾値

full CISD係数を絶対値降順、同値ならrestricted-basis index順に並べ、二乗ノルムの
累積が0.99へ最初に達するprefixだけを残して正規化する。Hamiltonian、exact state、
overlap、energy、gap、truthは構築に使わない。

full-CISD `t_ana`の`0.1, 0.2, 0.3, 0.5`倍で

\[
d_P=\max_t\frac{|g_{\rm full,P}(t)-g_{\rm trunc,P}(t)|}{\epsilon_E}
\]

を計算する。`d_P>0.05`、またはnoise floorを越えたsigned proxyの符号不一致を
state-riskとする。結果を見て0.99、0.05、時刻集合を変えない。

## 固定比較

1. 現行二PF practical selector。
2. `current_m3`固定。
3. Yoshida4固定。
4. 診断を記録するだけで選択を変えないもの。
5. 全PFを`0.5 t_ana`へ制限するuniversal fallback。
6. 元fallbackまたはstate-riskが立ったPFだけを制限するtargeted fallback。
7. 同じ4追加作用をfull-CISDの追加時刻`0.15,0.25,0.4,0.7`へ使う7点fit。

診断だけ、fallbackだけ、組合せを分ける。診断が不発または全発火なら、その診断の
選択性による改善とは主張しない。

## Phase A/B境界

Phase Aではsanitized入力だけを使い、全strategyのformula、時刻、予測誤差、予測費用、
診断、fallbackを凍結する。scorerと判定式も同じcommitへ含める。

Phase Bではprediction hashを確認してからtruthを開く。各unique selected coordinateの
`0.99,1.00,1.01`倍を直接計算し、同一H01 domainのanchorから連続追跡する。主regret
基準は元の二PF保存gridとし、挿入点を含む拡張基準は別列にする。

最大は36 unique selected coordinates、108新規direct coordinates、12 anchor再計算
である。実際には同一coordinateを重複計算しない。

## 判定

targeted fallbackの有益性は、次をすべて満たしたときだけ認める。

- 1.01予算でunsafe executionが0、主条件coverage 4/4。
- 6条件平均regretが現行法より相対10%以上低く、どの条件もregret悪化が絶対0.10以下。
- universal fallbackまたはequal-cost extra pointsより、平均regretで相対5%以上、
  または最大regretで相対10%以上よい。

全gate合格でもこの条件を満たさなければ`complete_no_benefit`で停止する。診断を
追加調整しない。有益な場合だけ、新protocolでS5の未使用active-space分子評価を一度
行う。
