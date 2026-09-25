# 第一研究S4 exact-time採点 v1.1：uniform lower anchor

S4 Phase Aはtruthなしで完了し、6条件×7 strategyの予測がcommit・hash固定された。
初回Phase Bはdirect計算前に、6 condition/PF群で最初の挿入点より下側の保存済み
H01-native anchorが存在しないため停止した。新規direct点、cache、科学結果は0である。

これは数値ゲート違反ではなく、保存anchor可用性に依存したv1規則の範囲不足である。
Phase A予測を変更・再実行せず、Phase B branch初期化だけをv1.1として固定し直す。

## 一律規則

保存anchorが見つからなかった6群だけを特例扱いしない。全12 condition/PF群で、
その群の固定済み挿入時刻の最小値を`t_min`として

\[
t_{\rm anchor}=0.5t_{\min}
\]

を新規計算する。時刻はPhase A予測と固定係数`0.99,1.00,1.01`だけから決まり、
truth値や保存gridの位置を使わない。

新anchorではexact-ground overlap最大の固有枝を選び、以後は時刻昇順にprevious-vector
overlap最大で追跡する。anchorは再計算ではなく新しいdirect座標として数える。
したがって最大会計は挿入60点＋anchor 12点=`72`点、保存anchor再計算は0点である。

anchorには保存shiftがないため`1e-9 Ha`再現ゲートは適用しない。その代わりanchor自身に
固有対残差、unitarity、ground overlap、phase gapの固定ゲートを適用する。挿入点の
previous/ground overlapとphase gapは親protocolから変更しない。

## Phase境界

親Phase A commit `95ed24c...`とprediction SHA-256 `47cdef9b...`をbyte-identicalに
再利用する。selector、strategy、formula、time、予測費用、budget、判定式は変更しない。
初回の未完了Phase B出力は削除・変更・cache再利用せず保存する。

全ゲート合格後のbenefit/no-benefit判定は親S4と同一である。どちらのcomplete結果でも
このrun内ではS5や追加diagnosticへ進まない。
