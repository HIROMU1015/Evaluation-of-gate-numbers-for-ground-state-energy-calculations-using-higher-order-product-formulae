# 紙上の性質・測定費・最小判別

2026-10-18 JST。[規則G](adaptive_subspace_construction.md)についての手計算による導出である。科学用プログラム・symbolic checker・数値例を実行していない。独立証明認証・新規性の科学レビューを完了したとはしない。

## M1. 表現能力とcoherence

理想matrixでS^f=diag(p_a)、H^f=cS^f+J^f。非零cellを使えばE_f=c+λ_min(J^f,S^f)≥E0。split後は親χ_aが子の和なのでV_f⊂V_f′、従ってE_f′≤E_f。これは既知のRayleigh–Ritzであり、新規寄与ではない。

cell内では(χ_a)_x=ψ_xなので、同じcellの相対振幅・位相を保つ。一方、任意のzに対するφ_x=z_{f(x)}ψ_xから、ψ_x=0ならφ_x=0である。**対角predicateだけではsupportを拡張できない。** 実際の出力stateをlabel測定でdephaseしてから同じχだと扱ってはならない。測定は各copyを消費し、次shotにはseedを再準備する。

解析記号としてground vector gを置き、ψ_x≠0のところでr_x=g_x/ψ_x、m_a=(Σ_{x∈a}|ψ_x|²r_x)/p_aとする。

\[
\eta_f^2:=1-\|P_{V_f}g\|^2
=\sum_{\psi_x=0}|g_x|^2+
\sum_{a:p_a>0}\sum_{x\in a}|\psi_x|^2|r_x-m_a|^2.
\tag{M1}
\]

η²<1ならu=P_Vg/\|P_Vg\|はgとのoverlap²が1−η²。gに直交する成分とのHのcross項は0なので、スペクトル幅Wについて

\[
0\le E_f-E_0\le\langle u|H|u\rangle-E_0
\le W\eta_f^2\le2\Lambda\eta_f^2.
\tag{M2}
\]

これは条件付きの近似診断であり、g/r/ηを入力にしてpredicateを選ぶ規則ではない。連結したH_ddでηを係数から小さく抑える命題は未証明。「rがcellごとに一定」というclass定義だけで研究課題を解いたことにしない。

## M2. 共通記録の不偏性と分散

固定l,xにおいてa_x=ψ_x、b_x=(P_lψ)_xとする。G2の状態のancilla X/Yとsystem xの同時測定から

\[
\sum_{s=\pm1}s\Pr(s,x\mid l,X)=\operatorname{Re}(a_x^*b_x),
\quad
\sum_s s\Pr(s,x\mid l,Y)=\operatorname{Im}(a_x^*b_x).
\tag{M3}
\]

Yの符号は通常のPauli Yを+1/−1として記録する規約。b_x=ω_l(x⊕d_l)ψ_{x⊕d_l}であり、xとy=x⊕d_lをfで分類すればΠ_aP_lΠ_a′のmatrix entryになる。lの|j_l|/Λと軸の1/2をG3のweightが打ち消す。これでG4を得る。

|Z^f_aa′|≤2Λ、Var(Z)を複素平均二乗偏差で定義すれば

\[
\operatorname{Var}(Z^f_{aa'})\le\mathbb E|Z^f_{aa'}|^2
=4\Lambda^2 r^f_{aa'},
\quad r^f_{aa'}=\Pr[f(x)=a,f(x\oplus d_l)=a']\le1.
\]

rはlを混合した実際の測定分布。希少cellの正規化後分散が小さいという結論ではない。配置人口だけではM3の位相を得られない。例としてN=1のψ±=(|10〉±|01〉)/√2、H=t(a1†a2+a2†a1)、実t>0では人口分布が同じでもseed energyは±tである。

## M3. 適応的再利用の同時confidence

T=K_max−1、Q個の固定predicateからのtree class Fの要素数をF_countとする。分割系列の数で上から評価すると

\[
F_{\rm count}\le\sum_{t=0}^{T}Q^t t!,
\qquad \log F_{\rm count}=O(K_{\max}\log(QK_{\max}))
\]

（Q≥1）。空cellも含めた全構文をunion対象にできる。これはclassicalに全treeを列挙する指示ではない。

全f∈Fと全entryの実部・虚部にHoeffdingとunion boundを適用する。m_H個のIID記録について、各成分の誤差≤τとする十分条件は

\[
m_H\ge\frac{8\Lambda^2}{\tau^2}
\log\frac{4F_{\rm count}K_{\max}^2}{\alpha_H}.
\]

成分のrange長は4Λである。Hermitian化はoperator norm誤差を増やさず、τ=e_H/(√2K_max)とすれば、確率≥1−α_Hで全fについて\|Jhat^f−J^f\|≤e_H。従って一つの保守的な十分条件は

\[
m_H\ge\frac{16\Lambda^2K_{\max}^2}{e_H^2}
\log\frac{4F_{\rm count}K_{\max}^2}{\alpha_H}.
\tag{M4}
\]

独立した人口記録には

\[
m_S\ge\frac1{2e_S^2}
\log\frac{2F_{\rm count}K_{\max}}{\alpha_S}
\tag{M5}
\]

で全cellの|phat_a−p_a|≤e_S、従って対角Gramのnorm誤差≤e_Sを得る。二つの記録の独立性はこのunion boundに必須ではないが、仕様を単純にするため別poolとした。

全class同時eventなので、そのデータで選んだtreeにも同じeventが成り立つ。選択後の一treeだけの固定観測量confidenceを流用しない。データを見て辞書を増やす、seedを変える、Λやsampling lawを変える場合にはこの同じ保証は使えない。mを結果後に任意停止する場合も別のanytime保証が必要であり、Gは固定mから追加取得しない。

## M4. Conditioning、Ritz誤差、受理条件

B=Λ≥\|J\|とする。実際の非零人口の最小値p_min、e_S<p_minのとき、任意の係数uのRayleigh quotientを比較すると

\[
\left|\frac{u^\dagger\widehat Ju}{u^\dagger\widehat Su}
-\frac{u^\dagger Ju}{u^\dagger Su}\right|
\le\frac{e_H+B e_S}{p_{\min}-e_S}.
\tag{M6}
\]

分子に|u†Ju|≤B u†Su、分母にu†Su≥p_min\|u\|²を使い、同じuで評価した後minを取る。cはquotientから分けて一回だけ足す。これは前回GPTのD2と同じ十分評価で、最適sample complexityや下界ではない。

観測可能な受理規則としてphat_min>2e_Sを要求する。p_min≥phat_min−e_S>e_Sだから

\[
u_f=\frac{e_H+B e_S}{\widehat p_{\min}-2e_S}
\quad\Rightarrow\quad |\widehat E_f-E_f|\le u_f
\tag{M7}
\]

を使える。Gramのcondition numberはp_max/p_min。K個の非空cellならp_min≤1/Kであり、直交性だけで大きなKを無料にはできない。粗いe_H/e_Sに対するM7が棄却を増やしても、ridge、cellの事後削除、threshold調整で当初のspace保証を救済しない。

上の式は小matrixのsolveを数学的に正確とした評価である。有限精度実装では、証拠付きの固有値演算誤差e_solveをu_fへ加え、ε_RR内に配分する必要がある。表のK³は固定word精度の算術操作数であり、係数比較・累積・solveのbit費用をゼロにした多項式bit保証ではない。今回算術実装や誤差認証は行っていない。

M4–M7の同時eventではG5>0の受理により真のE_f−E_f′≥g_L>0。有限shotの単なる最低固有値には自動的な変分性がない。Ehat+u_fは確率付きのE0上界であるが、E0に近いことを示す下界ではない。既知の係数下界c−Λは使えるものの、通常は幅が粗く、所定の絶対精度を閉じるとは限らない。残差=0の励起固有stateもあり、残差だけをground証明にしない。

## M5. 総費用と改善し得る項

| 費用 | Gで必要なもの |
| --- | --- |
| 係数前処理 | term支持からwの集計、整列O(n² log n)程度のgraph処理、O(n(L+n))個のpredicate記述。入力bit費も含む |
| 量子準備・測定 | m_H回のA、controlled-P、ancilla軸測定と全Z読出し、m_S回のAと全Z読出し。Σ_l abs(j_l) C_cP_l/Λを平均control費として払う。1 Pauliの通常all-to-all粗いgate数はO(n)で、topology/native精度の費用は未評価 |
| 全記録storage | O((m_H+m_S)(n+log M)) bits＋metadata。全配置振幅表ではないが、mが大きい場合は重い |
| 候補評価 | step tの候補数≤K_t Q。単純実装なら各候補O((m_H+m_S)c_f+K_t²)の再label／集計とO(K_t³)のdense solve。全stepで和を取る。c_fはtree評価費で粗くO(nK_t) |
| membership | energy測定中の量子membershipは0。古典評価は上のc_fに含む。cell/stateを量子準備するなら可逆count・tree・table参照・uncomputeが別途必要 |
| 更新 | 固定記録で全候補が統計条件を満たす限り追加量子shotは0。集計・solveは繰返す。新seed・新辞書・精度不足への追加取得はこの手順の外 |
| 実state出力 | cellの1/p_a、最適Fの\|z\|∞²/(z†Sz)という再準備費と回路費。energy後処理と同じ費用にしない |

一例としてp_min≥ρを合法に保証できる場合、M6の誤差をε_RRにする十分shot規模は、定数とlogを除けばm_H=O(Λ²K_max²/(ε_RR²ρ²))、m_S=O(B²/(ε_RR²ρ²))（e_S<ρ条件も必要）。ρが指数的に小さければ指数費が残る。これは粗い上界であり、実分散・covarianceを用いる強い対照がもっと安い可能性を排除しない。

改善し得るのは、candidateごとのmembership反射と独立測定、および候補を替えるたびの再取得である。しかしVQNHEやshadow QSEも再利用を許す。**これらの項がGだけで改善するとは示せていない。** 省いた量子predicateの負担を記録storage・古典predicate処理・同時confidenceが相殺し得る。

## M6. 小空間のfamily例と限定的な障害

1. **古典的に容易な成立例。** r=O(1) orbitalのinteracting fragmentとdecoupled quadratic bathで、各N_F allocationのfragment seedを全配置に非零、bathを当該N_BのSlater groundとする。single-orbital predicateを十分に分割すればK≤binom(r,N_F)でfragment全spaceを含む。全NのE0は全ての許容N_Fの最小を取り、allocationの費用を払えば得られる。しかしfragment CI＋bath一体対角化で古典的に容易であり、量子利得も新生成則の必要性も示さない。TPSCIも除外しない。Gの有限shotのgreedy順がそのfull partitionへ到達する保証でもない。
2. **support障害。** determinant seedなら全ての非零χは同じdeterminant。N=1、H=cI+t(a1†a2+a2†a1)、seed=|10〉では全fでE_f=c、E0=c−|t|。nを大きくしても同じ局所障害を埋込める。対角basis文法を否定する範囲に限り、全coherent subspace法のNO-GOではない。
3. **希少cell。** seedの人口pのcellを正規化したbasisを使うとM6のp_minが現れる。具体的に小Kでもpを任意に小さくできる。人口を全て均等と仮定した費用比較は不可。ただしM6を情報理論的な1/p²下界と主張しない。
4. **連結family。** hoppingがfragment境界を横切るH_ddでは上のdecoupled証明は使えない。係数graphのclusterがground振幅比の近似を保証する補題は得ていない。絶対係数graphが位相構造を十分に捉えること、greedyな一splitでglobalに必要な更新を見つけることも未証明。

## M7. 最小判別命題と結果の固定

| 命題 | 成功／失敗条件を先に明示した内容 | 今回の紙上結果 |
| --- | --- | --- |
| P-a：一つの記録で有限classのsplitを評価できる | G2/G3が全fのJ^fを不偏推定し、adaptive choiceにも同時eventを使えること。単なる人口記録では失敗 | M3–M7で成立。既知paired measurement／統計論の帰結で、独立新規性ではない |
| P-b：再取得を避けること自体に強対照との差がある | 同じseed、同じD、同じ候補の双線形形式をVQNHEの記録からは再評価できないこと | **この差は成立しない。** F_zのquadratic formをpolarizationして同じJ^fを得られる。Gの名称・record形式だけでは差にならない |
| P-c：生成・選択の固有差 | 同じaccess・同じ固定dictionaryを許したVQNHE/shadow QSE型対照と比べ、Gの係数生成・選択が別の有用な操作または取得費を生むこと | 未確立。Dを同じ関数classとして対照へ渡せば同じspan、同じcriterionなら同じ選択となる。対照のdictionaryを弱くして人工差を作らない |
| P-d：非自明な連結H_ddへの価値 | gを入力せず、Gが安価な一splitを正しく識別する係数条件と、同shotの最強の再利用対照との差が少なくとも一つあること | 条件も差も未証明。小例のenergy低下だけを代替成功にしない |

次の最小の**提案**はP-cの操作単位の文献・還元照合である。まずVQNHEの関数classとSSEのfilter手順にGのD／g_L／C_addを代入したとき、残る差が単なる探索heuristicかを判別する。ここで差が閉じなければ、数値化で新規性の穴を埋めない。差が具体化した場合だけ、P-dの係数条件を限定する作業の要否をGPT／ユーザーへ戻す。

P-bの対応を明示すると、Q(z)=〈ψ|F_z†JF_z|ψ〉=z†J^f zに対して、J_aa=Q(e_a)、

\[
\operatorname{Re}J_{aa'}=\tfrac14[Q(e_a+e_{a'})-Q(e_a-e_{a'})],
\quad
\operatorname{Im}J_{aa'}=\tfrac14[Q(e_a-i e_{a'})-Q(e_a+i e_{a'})].
\]

VQNHE本文とcomplex-function supplementの、Fに依存しないPauli配置対測定の記録から、これらの**非正規化numerator**を再評価できる。one-hot関数には零があるので、同論文の正のoutput-rangeを仮定した効率定理をそのまま適用していない。統計的精度・population・conditioningは別途払い、GとVQNHEの全noise分布や定数費用が同一と証明したわけでもない。

このpacketを「P-dが難しいから別の大分野をreviewする」「thresholdやseedを変えて成功させる」ための継続承認にはしない。
