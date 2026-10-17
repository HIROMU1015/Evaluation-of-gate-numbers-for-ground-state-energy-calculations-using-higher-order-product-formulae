# Q1：挿入文法の限定的障害と確認範囲

2026-10-17 JST。記号(1)–(14)は[親子・Fの導出](parent_form_factor_derivation.md)に従う。
**具体的な子Bは未構成。以下の負の結果は、明示する一段の独立channel文法だけを対象とする。**

## 1. 検討する最小文法

親子の3＋3空間で、まずoccupation分枝を混ぜない局所基底変更を行い、
三つの互いに独立な「上段の一状態＋下段の一状態」にする。
各2次元channelに一つの回転／phaseを適用して新しい六つのenergy labelにする文法をGとする。
局所基底変更は係数依存でもよく、各channelでのangleも同じである必要はない。

Gが可能なら、ある三次元unitary V2,V1により、
\(V_2^\dagger h_2V_2\)、\(V_1^\dagger(h_1+sI)V_1\)、\(V_2^\dagger TV_1\) が全て対角になる。
従って必要条件は

\[
[h_2,TT^\dagger]=0,
\qquad [h_1,T^\dagger T]=0.
\tag{15}
\]

これは単にSVDができるかという問いより強い。
SVDのsingular basisを選んだ際に、対角energy作用がchannel間の結合を再生成しない必要がある。
非縮退の親固有labelをphase／permutationで変えるだけの挿入則もGの部分族である。

## 2. 全指定gでの反例

J²=3J、T=J−Iだから

\[
TT^\dagger=T^\dagger T=I+J.
\tag{16}
\]

u方向の固有値は4、直交する二次元では1。T、従ってFのsingular valuesは(2,1,1)でrankは3。
「couplingは一つのbright channelだけ」というrank-oneの短絡も成立しない。
Hamiltonianの一対相互作用がrank-oneであることと、異なるpair数間のTのrankは別である。

(4)より

\[
[h_1,I+J]=[\mathsf d,J],\qquad
[h_2,I+J]=-[\mathsf d,J],\qquad
[\mathsf d,J]_{12}=d_1-d_2=-1/2\ne0.
\tag{17}
\]

gに依存する項はこの交換子では消えるので、g∈[1/8,1/2]の全域で(15)が破れる。
**Gによる厳密な三つの独立2次元挿入は不成立**。
singular value 1の二重縮退内の基底自由度でも、非零の交換子は消せない。

parent固有基底でも

\[
[D_2,FF^\dagger]=U_2^\dagger[h_2,TT^\dagger]U_2\ne0,
\quad
[D_1,F^\dagger F]=U_1^\dagger[h_1,T^\dagger T]U_1\ne0.
\tag{18}
\]

特にFがparent energy label上で単に対角又はmonomialになることはない。
この結果はFの全要素が非零であるという主張ではない。
また複数段でchannelを混ぜるunitary、別のcompactな生成規則、近似的operator残差の可能性を排除しない。
近似誤差の正の下界、gate下界、一般Q1の不可能性は示していない。

## 3. 各確認条件の判定

| 対象 | 今回の判定 | 根拠／不足 |
|---|---|---|
| occupationからQ5への移送 | 確認 | (2)–(7)。新self−g、off-diagonal−gF、親g不変 |
| 親のUの直交性・phase convention | 確認（形式的な親変換） | (9)–(12)。子Bの確認へ流用しない |
| 係数とparent labelからのF | 既知法への限定還元 | (10)–(13)。secular rootの取得・arithmeticを無料化しない |
| 文法Gの子B | 限定的な障害 | (17)で必要条件が破れる |
| 一般の子B†B=I | 未解決／未確認 | 具体的なBなし。存在定理による代用をしない |
| K B=B Dchildと新energy評価 | 未解決／未確認 | child spectrumを生成する規則なし |
| 全入力labelのsuperpositionへの共通作用 | 未解決／未確認 | 一つのBが提示されていない |
| eigenlabel・補助work返却 | 未解決／未確認 | 可逆なlabel移送とuncomputeの規則なし |
| Bを含むcontrolled evolution | 未解決／未確認 | scalarの必要条件は次節で確認するがB未構成 |

例えば入力label x=1100、y=1010に対して必要なのは、同じ固定されたBが
\(\alpha|x\rangle+\beta|y\rangle\) の係数と相対phaseを保ち、同じwork初期値・終値で作用すること。
個別state準備 \(|z\rangle|0\rangle\mapsto|z\rangle|E_z\rangle\) だけでは、そのまま満たさない。
zを捨てれば、出力 \(\alpha|x\rangle|E_x\rangle+\beta|y\rangle|E_y\rangle\) のoff-diagonal項が失われる。
これを直す具体的な可逆操作を得たとはしない。
個々のeigenvectorのcolumn phaseは一貫したBと逆Bで相殺可能だが、その一貫性も必要である。

## 4. scalarとself-pair phaseの紙上点検

このsectorでは \(\sum_pq_p=2I\) なので

\[
h_{[4]}^{(2)}=-2gI+\bar h,
\qquad
\bar h=\sum_pd_pq_p-g\sum_{p\ne q}P_p^\dagger P_q.
\tag{19}
\]

上段も下段も合計self−2gで一致する。下段だけ新self−gを落とすと、
Hamiltonian誤差は \(+gQ_{4=1}\) となり、全sector共通scalarの変更でも補えない。

controlを \(|+\rangle\)、対象を任意の \(|\psi\rangle\) とした正しい作用は

\[
\frac1{\sqrt2}\left(
|0\rangle|\psi\rangle+
|1\rangle e^{-it(c-2g)}e^{-it\bar h}|\psi\rangle
\right).
\tag{20}
\]

eigenlabel k上のcontrolled phaseであれば、値は \(c+E_k(h)=c-2g+E_k(\bar h)\)。
c又は−2gを「globalだから」と捨てるとcontrolの0/1間の相対phaseを変える。
ここでc−2gと分けたのはphaseの監査用の恒等式であり、新しいEchild評価を構成したことではない。
親h2の−2gを含むEchildへ、さらに−2gを二重加算してもいけない。
**(20)の必要条件の確認と、未構成Bによる実操作の確認は区別する。**

## 5. 不足する具体的な構成と次の紙上命題

不足はparent Fの未知な符号表だけではない。
(14)で非可換なΛとFを同時に扱い、親label間の混合を生成し、新energy評価と結び付ける一つの規則がない。
Fの点ごとの評価や既知SVDだけでは、残るparent energyの非対角作用を解消しない。

次に実施するかをGPT／ユーザーが判断する**有限例だけの検証提案**として、
Gを越える非対角label混合を、既知のgraph-subspace／Riccati表現で明示できるかを挙げる。
A=Λ+δI、D=Λ+sIとすると、上段ξ、下段Yξという三次元graphがKの不変部分空間になる必要十分な恒等式は

\[
-gF+DY-YA+gYFY=0,
\quad\text{すなわち}\quad
[\Lambda,Y]+Y-gF+gYFY=0.
\tag{21}
\]

これはKの作用を上下段で比較して得た必要なテストであり、新しい解法ではない。
**最初に検証すべき命題**：係数と(10)のparent labelだけを使う明示的な非対角Y(g)の規則を提示でき、
指定g域で(21)が恒等的に成立するか。新たなchild固有vector／root setや汎用6次元対角化を入力する規則は不合格。
Yが構成できても、graphの正規化、補空間、残る二つの三次元作用の対角化、label返却を同じ規則で閉じる必要があり、B完成ではない。
graph座標にpoleが出ても、そのchartの失敗と全Bの不可能性を同一視しない。
Y=Y†等の追加制約を証拠なく置かず、(21)を満たすYの存在だけで安い生成を認めない。

この提案を新研究候補として採択したり、実際にYを探索したりしていない。
GPT／ユーザーは、このような具体的な非対角規則を紙上で検討する価値があるか、Q1を未解決のまま止めるかを判断する。

## 6. 一般Lについての停止境界

具体的なBを得ていないため、依頼Dの前提が満たされない。
**一般Lの挿入再帰の構成・費用・conditioning・誤差伝播の新たな検討は実施しない。**
6次元での(17)を一般不能性へ、親の三次表現を全m共有のpoly費用又はfast-forwardingへ外挿しない。
SOURCEの(Q3),(Q7)は未証明のまま保全する。
