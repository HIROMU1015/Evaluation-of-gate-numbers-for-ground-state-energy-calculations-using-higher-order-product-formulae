# Q1：L=4、m=2の親子作用とform factorの独立紙上導出

2026-10-17 JST。固定SOURCEは `3abef73cdd8a578d56f1d96d070862c71749e403`。
以下は手で行った演算子・有限和の導出であり、行列生成、数値対角化、solver、記号計算プログラムを実行した結果ではない。
**Q5のブロック式は確認できる。親のFは既知の一対secular問題へ表せるが、子のunitary挿入則Bは得られていない。**

## 1. 規約とoccupation作用

fermion modeの順序を \(1\uparrow,1\downarrow,2\uparrow,2\downarrow,\ldots,4\downarrow\) とし、
\(P_p^\dagger=a_{p\uparrow}^\dagger a_{p\downarrow}^\dagger\)、\(P_p=a_{p\downarrow}a_{p\uparrow}\) を用いる。
seniority-zeroでは \(q_p=P_p^\dagger P_p\) はpair occupationで、\(n_{p\uparrow}+n_{p\downarrow}=2q_p\)。

\[
h_J=\sum_{p\in J}d_pq_p-g\sum_{p,q\in J}P_p^\dagger P_q,
\quad d_p=2\epsilon_p,
\quad d=(-3,-1,1,3)/4,
\quad g=\gamma/4\in[1/8,1/2].
\tag{1}
\]

元の模型は \(cI+h_{[4]}\)。今回だけは指定どおりR=0の厳密pairing模型を扱う。
cは親hに重複配分せず、子に一度だけ足す。

\(|S\rangle=\prod_{p\in S}^{p\text{昇順}}P_p^\dagger|0\rangle\) とする。
異なるpのpair同士は四回のfermion交換で符号が \((-1)^4=+1\)。
同じpでは \(a_{p\downarrow}a_{p\uparrow}a_{p\uparrow}^\dagger a_{p\downarrow}^\dagger|0\rangle=|0\rangle\)。
したがって、qが占有、pが空ならpair移動の係数は+1で、Hamiltonianの移動振幅は**−g**である。
二つとも占有した別p,qへの移動はPauliにより零。p=qは各occupied pairにつき−gを与える。

\[
h_J|S\rangle=
\left(\sum_{p\in S}d_p-g|S|\right)|S\rangle
-g\sum_{q\in S}\sum_{p\in J\setminus S}|(S\setminus\{q\})\cup\{p\}\rangle.
\tag{2}
\]

これはpair符号・対角self項を同時に固定する。文献による \(-g/2\) の規約は移入しない。

## 2. 最後のlevelによる3＋3分解

I={1,2,3}、新levelは4とする。上段は4が空のm=2 sector、下段は4がoccupiedのm=1 parent sector。
両方とも \(\binom32=\binom31=3\) 次元で、合計 \(\binom42=6\)。
parentのhole labelを \(|\bar i\rangle=|I\setminus\{i\}\rangle\) として、基底順を

\[
(|23\rangle,|13\rangle,|12\rangle)\ \oplus\ (|14\rangle,|24\rangle,|34\rangle)
\tag{3}
\]

に取る。これはSOURCEの6個のoccupation文字列の並べ替えにすぎない。
下段のparent labelはそれぞれ \(|1\rangle,|2\rangle,|3\rangle\)。

u=(1,1,1)の記号、\(J=uu^T\)、\(\mathsf d=\operatorname{diag}(d_1,d_2,d_3)\)、\(S=d_1+d_2+d_3=-3/4\) を使うと、(2)より

\[
h_1:=h_I^{(1)}=\mathsf d-gJ,
\qquad
h_2:=h_I^{(2)}=(S-g)I-\mathsf d-gJ.
\tag{4}
\]

h1の対角は \(d_i-g\)、h2は \(S-d_i-2g\)、両者の非対角は−g。
親の結合は引き続き **g=γ/4** であり、γ/3へ変更しない。

\(T=\sum_{p\in I}P_p^\dagger\) の一対→二対作用は、\(|j\rangle\) から \(|\bar i\rangle\) へi≠jの場合だけ+1なので、

\[
T_{ij}=1-\delta_{ij},\qquad T=J-I.
\tag{5}
\]

4からIへpairを移す項が上右、逆が下左。ゆえにoccupation基底の作用は

\[
h_{[4]}^{(2)}=
\begin{pmatrix}
h_2&-gT\\
-gT^\dagger&h_1+sI
\end{pmatrix},
\qquad s=d_4-g=3/4-g.
\tag{6}
\]

上段の対角は \((0,-1/2,-1)-2g\)、下段は \((0,1/2,1)-2g\)。
下段はparentの−gと新しいself−gが合計−2gになっている。
たとえば \(|14\rangle\to|24\rangle\) も \(|14\rangle\to|13\rangle\) も振幅−g、
\(|14\rangle\to|23\rangle\) は一回のpair移動では零。off-diagonalの向きと添字をこの作用で確認できる。

親の基底変換を \(U_1^\dagger h_1U_1=D_1\)、\(U_2^\dagger h_2U_2=D_2\) と書けば、(6)は

\[
\mathcal K=
\begin{pmatrix}D_2&-gF\\-gF^\dagger&D_1+sI\end{pmatrix},
\qquad F=U_2^\dagger TU_1,
\tag{7}
\]

となる。これはSOURCEの(Q5),(Q6)と一致する。ここではまだUやBの安い量子実装を仮定していない。

## 3. このparentに固有の反転関係

r(1)=3、r(2)=2、r(3)=1とし、そのpermutationをΠと書く。
\(\Pi\mathsf d\Pi=-\tfrac12 I-\mathsf d\)、\(\Pi J\Pi=J\) より

\[
h_2=\Pi h_1\Pi+\delta I,
\qquad \delta=-1/4-g.
\tag{8}
\]

したがって同一の位相規約で \(U_1=U\)、\(U_2=\Pi U\) と選べる。
\(D_1=\Lambda\) なら \(D_2=\Lambda+\delta I\) で、parentの二対固有状態を別々に列挙する必要はない。
これはこの三準位の等間隔性を使った既知のparticle/hole・準位反転の有限次元対応である。
子の対角化や、一般のactive subsetに対する同じ関係は意味しない。

## 4. 親Fのlabel付きsecular表現と情報取得

任意label a∈{1,2,3}について、\(h_1v=\lambda v\) の各成分から

\[
(d_i-\lambda)v_i=g\sum_jv_j,
\qquad
1=g\sum_{i=1}^{3}\frac1{d_i-\lambda}.
\tag{9}
\]

g>0でdが相異なるため、\(\lambda=d_i\) は固有値ではない。
実際、対応する成分式から \(\sum_jv_j=0\)、残る成分が零、最後の成分も零となり矛盾する。
同様に非零固有vectorでは \(\sum_jv_j\ne0\)。

f(λ)=1−gΣ(d_i−λ)⁻¹は各pole間で狭義減少し、片側極限の符号が反転する。
従って未知のmany-body gapやcontinuation branchを入力せず、次の順序でparent labelを定義できる。

\[
\lambda_1<d_1<\lambda_2<d_2<\lambda_3<d_3,
\quad
\lambda_1\in(d_1-3g,d_1),\quad
\lambda_2\in(d_1,d_2),\quad
\lambda_3\in(d_2,d_3).
\tag{10}
\]

最初の区間の左端でf>0となるのは各 \(d_i-d_1+3g\ge3g\) かつ二つは真に大きいため。
\(x=\lambda+1/4\) と置き(9)の分母を払うと

\[
p_g(x)=x(x^2-1/4)+g(3x^2-1/4)=0.
\tag{11}
\]

この三次式は手による展開であり、記号solverの出力ではない。
正規化とphase規約を

\[
N_a=\left(\sum_i(d_i-\lambda_a)^{-2}\right)^{-1/2}>0,
\qquad U_{ia}=N_a/(d_i-\lambda_a)
\tag{12}
\]

とする。異なるλa,λbでは(9)の差をλa−λbで割れば内積が零になり、同じlabelではNで長さ1。
よってこの**parentの形式的変換U**は実直交である。これは子Bのunitarityの確認ではない。

\(\Pi T=J-\Pi\) だから、親Fは全a,bに共通して

\[
F_{ab}=N_aN_b\left[
\frac1{g^2}-\sum_{i=1}^{3}
\frac1{(d_{r(i)}-\lambda_a)(d_i-\lambda_b)}
\right],
\quad F=U^T(J-\Pi)U=F^T.
\tag{13}
\]

**得られた範囲**：(10)のlabelと係数から一意に定義される三次secular座標を使う、既知の点ごとの表現。
これは一対のrank-one／Bethe問題と(8)による還元であり、新しいform-factor原理ではない。
未知のchild Bethe roots、六つのchild固有状態、gap、正しいbranchは入力していない。

**取得費を残す**：λを外部から無料に受け取る規則にはしない。
値を得るなら、指定区間内の三次式の符号によるroot isolation／有限精度評価、N・分母のarithmetic、
要求するF誤差への伝播を処理する必要がある。その既知の一変数処理を行う手順は説明できるが、今回実行していない。
特にλをsymbolに残した(13)だけを、可逆arithmeticの実装・gate費用・clean workの証明に数えない。
全a,bの表を先に作って与えることもしていない。
点ごとの式があってもFはunitaryではなく、それだけで子の一つのBは生成されない。

## 5. 子に残る作用の正確な形

(7),(8),(13)を合わせると

\[
\mathcal K=
I_2\otimes\bigl(\Lambda+(1/4-g)I_3\bigr)
-\tfrac12 Z\otimes I_3-gX\otimes F,
\tag{14}
\]

ここでZ=diag(1,−1)、Xは二つのoccupation分枝を交換する。
新levelのbranch detuningは下段−上段=1。
FがΛと両立するlabel別scalarでないことが、単純な挿入回転を妨げる。
具体的な不成立範囲、controlled phase、Bの未確認事項は[検証記録](insertion_obstruction_and_checks.md)。

一次文献との対応と規約差は[比較・範囲](prior_art_and_scope.md)、SOURCE同一性は[source registry](source_registry.json)。
