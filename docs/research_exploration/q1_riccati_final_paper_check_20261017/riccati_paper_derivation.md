# Q1非対角Riccati生成則：最終限定紙上検証

2026-10-17 JST。固定SOURCE：`2a3e6898087fc248656123e7c67fb62c49b2d0f8`、元の定式化：`3abef73cdd8a578d56f1d96d070862c71749e403`。
**独立した生成規則は得られなかった。二つの明示文法の限定的障害を示し、一般のYの構成・不可能性は未解決のまま止める。**
全て手による有限次元の導出。数値・記号計算プログラム、solver、行列生成・対角化、simulationを実行していない。
今回の文法検討は下記G_FとG_Sの二つだけであり、別ansatzの大量探索や一般Lへの拡張探索は行わない。

## 1. 固定作用とRiccati条件の向き

L=4、m=2、seniority-zero、\(\epsilon=(-3,-1,1,3)/8\)、\(g=\gamma/4\in[1/8,1/2]\)。
前回の同一phase規約を使い、親一対の作用とform factorを

\[
h=\mathsf d-gJ=U\Lambda U^\dagger,
\quad\mathsf d=\operatorname{diag}(-3/4,-1/4,1/4),
\quad J=uu^T,\ u=(1,1,1)^T,
\quad F=U^\dagger C U,\ C=J-\Pi
\tag{1}
\]

とする。Πは親のlevel 1と3を交換する。Uは前回のlabel付き一対secular表現であり、未知のchild情報を入力しない。
親二対のshiftはδ=−1/4−g、新levelのshiftはs=3/4−gなのでs−δ=1。

\[
K=\begin{pmatrix}A&-gF\\-gF&D\end{pmatrix},
\qquad A=\Lambda+\delta I,\quad D=\Lambda+sI.
\tag{2}
\]

上段ξ、下段Yξというgraphの作用を比較すると

\[
K\binom{I}{Y}=\binom{I}{Y}(A-gFY)
\quad\Longleftrightarrow\quad
\mathcal R_g(Y):=[\Lambda,Y]+Y-gF+gYFY=0.
\tag{3}
\]

Yの作用方向は上段→下段。F=F†という前回の特定の親phase規約を使っている。
別phaseを選べばFとgraph座標を一貫して移す必要がある。
cは両対角blockに同じく加わるため(3)では消えるが、controlled phaseからは消えない。
parentのgをγ/3へ変えず、self-pair項も保持している。

Πu=u、JΠ=ΠJ=JよりC²=J+I。
u、Π-evenでuに直交する方向、Π-odd方向におけるCの固有値はそれぞれ2、−1、1。
従ってFのスペクトルは相異なる \(\{2,-1,1\}\) で、

\[
[\Lambda,F^2]=U^\dagger[h,J+I]U
=U^\dagger[\mathsf d,J]U\ne0,
\qquad[\mathsf d,J]_{12}=-1/2.
\tag{4}
\]

(4)は前回の障害の別表現である。今回以下では非対角Yを許しても、どの追加文法が閉じないかを確認する。

## 2. G_F：Fの関数から生成する非対角な候補

最小のcoefficient ruleとして、parent labelのenergyを混ぜるがFとは可換なYを作る文法をG_Fとする。
gや既知parent energyから求めたscalar係数を用いる多項式・有理関数・spectral functionも含む。
Fはparent energy基底では非対角なので、これは前回のlabel別2次元回転と同じ制約ではない。
**Y=Y†は仮定しない。G_Fの唯一の追加構造は[Y,F]=0。**

まず交換子項を除いたscalar二次式をFの各固有値fに対して解くと、絶対値が小さいbranchの既知関数は

\[
q_g(f)=\frac{2gf}{1+\sqrt{1+4g^2f^2}},
\qquad
Y_0=q_g(F).
\tag{5}
\]

これは未知のmatrix square-root oracleを置く必要がない有限例である。
q=q_g(1)、r=(q_g(2)−2q)/3とすれば、既知の三つのfに対する補間から

\[
Y_0=qF+r(F^2-I).
\tag{6}
\]

必要なのはg、Fとscalarの平方根 \(\sqrt{1+4g^2}\)、\(\sqrt{1+16g^2}\) だけ。
これらのarithmeticを無料の量子操作にはしない。(6)をプログラムで評価したわけでもない。
この候補は

\[
Y_0-gF+gY_0FY_0=0,
\qquad \mathcal R_g(Y_0)=[\Lambda,Y_0]
\tag{7}
\]

を満たす。しかし次の議論により、残差は非零である。

### G_F全体への限定的不成立証明

仮に[Y,F]=0かつ(3)を満たすYがあるとする。
Fは単純スペクトルなので、その直交固有基底ではYも対角で、対角値y_fは複素数でもよい。
この基底で \([\Lambda,Y]\) の対角成分は零。従って

\[
gf\,y_f^2+y_f-gf=0,
\qquad f\in\{2,-1,1\}.
\tag{8}
\]

g>0、f≠0で、判別式は \(1+4g^2f^2>0\)。全ての選択branchでy_fは実数となる。
よって**この文法のもとでの帰結として**Y=Y†を得る。一般のYへ課した仮定ではない。
(3)とその随伴の差から \([\Lambda,Y]=0\)、和から \(Y-gF+gYFY=0\)。
(8)へy_f=±1を入れると左辺は±1で零にならないため、I−Y²は可逆である。
YとFは可換なので

\[
F=g^{-1}Y(I-Y^2)^{-1}.
\tag{9}
\]

すると \([\Lambda,Y]=0\) から \([\Lambda,F]=0\)、従って \([\Lambda,F^2]=0\) となり(4)に矛盾。
**G_Fのどのbranchも指定g全域で厳密解を与えない。**
特に(6)は実際にparent energy labelを混ぜる非対角候補だが、元のRiccati式には非零残差を残す。
Y0がΛと可換なら(9)でFも可換となるので、この非対角性と残差の非零性を確認できる。

ここで否定したのは[Y,F]=0という生成文法だけである。
全てのHermitian Yの不成立、非可換なYの不成立、近似解の誤差下界は証明していない。
成功する解があるなら、少なくともFとも非可換なlabel混合が必要になる。

## 3. G_S：Sylvester逆を一律に用いる生成文法

交換子を保持する既知の書き換えは

\[
\mathcal L_g(X)=[\Lambda,X]+X,
\qquad
\mathcal L_g(Y)=g(F-YFY).
\tag{10}
\]

G_Sを、指定interval全域で同じ \(\mathcal L_g^{-1}\) を使い、右辺の更新又は級数を生成する文法とする。
その反復を実行していない。初期値・収束・打切り誤差の保証も仮定しない。
逆が存在する場合に限り、parent eigenlabel上で

\[
(\mathcal L_g^{-1}Z)_{ab}
=\frac{Z_{ab}}{1+\lambda_a(g)-\lambda_b(g)}.
\tag{11}
\]

これは既知のSylvester/Riccati処理であり、それ自体は新規則ではない。
ここでは、この固定逆を全域で使えるという前提を紙上で点検する。

親のsecular式は前回どおり、x=λ+1/4について

\[
p_g(x)=x^3+3gx^2-x/4-g/4.
\tag{12}
\]

\(g_*=\sqrt2/4\) では \(g_*^2=1/8\) なので、手による乗算で

\[
p_{g_*}(x)=(x-g_*)\bigl((x+2g_*)^2-1/4\bigr).
\tag{13}
\]

二つの負の根は \(-2g_*-1/2\) と \(-2g_*+1/2\)、残りの根g*は正。
これは親三次式の一地点での因数分解であり、childの全energy／Bethe root一覧を取得したものではない。
従って順序付き親labelで

\[
\lambda_2(g_*)-\lambda_1(g_*)=1,
\qquad \mathcal L_{g_*}(|1\rangle\langle2|)=0.
\tag{14}
\]

\(\gamma_*=4g_*=\sqrt2\) は指定された連続interval \([1/2,2]\) の内部。
よって**連続family全域に一つの可逆Sylvester作用素を仮定するG_Sは閉じない**。

元SOURCEのγが有限bit有理数という入力条件も維持する。
γ*=√2は有理数ではないため、「その有限bit入力で厳密に分母零が起こる」とは主張しない。
ただし許されるbit長を増やした有理入力列はγ*へ近づけられ、親固有値の連続性により(11)の分母を任意に小さくできる。
従ってinterval全体から一定の逆norm／conditioningを無料で与える根拠はない。
これはpoly(bit長)算法の不能性や、必要bit数・gate数の指数下界ではない。
G_Sに対する上記の否定は、連続拡張全域で固定逆が可逆という追加要件に限る。
元の有限bit有理入力における全てのSylvester逆利用法の不可能性は示していない。

分母が零なら(10)は、対応成分に \((F-YFY)_{12}=0\) という非線形の整合条件を残す。
この条件が満たせないことまでは示しておらず、別のchart、resonant blockの共同処理、別の既知解法を否定しない。
条件を解かずにpseudoinverseだけで一意のYを得たとはしない。

## 4. 何が特異で、何が未解決か

(14)は、対角block Dのlabel 1とAのlabel 2のenergyが一致するSylvester作用素の特異性。
full Kの固有gap消失、Yの発散、graph chartの破綻は、この事実だけから従わない。
またgraphを別chartへ移す必要が生じても、それは物理的unitaryの不可能性ではない。

今回得たのは、Fだけの関数では不足することと、固定Sylvester逆を全域で使う短絡の問題点である。
**Fとも非可換なYを、係数から生成し、その残差を閉じる具体的な規則は得られなかった。**
解の不存在、一般Q1の不能性、既知法で世界的に未解決であることは認定しない。
G_Sを分母が安全な部分intervalに制限しても、その処理は既知法で、収束・新規性・Bの完成は別に未証明。
不足を別ansatzの自動探索で埋めず、ここで紙上検討を終了する。
