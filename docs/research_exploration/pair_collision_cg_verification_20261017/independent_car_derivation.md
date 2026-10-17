# 二電子補助衝突：定義からのCAR再導出

2026-10-17 JST。対象SOURCEは`b5c49323957f1bfa2a24cb2786a0ebd1f3932925`。
**判定：確認。** 以下の規約と固定粒子数sectorでは、報告された恒等式は整合する。
過去の結論や固有値を仮定せず、CARで正規順序化してからspinへ移す。
「独立」は定義から再導出する方法を指し、別モデルによる検証又は第三者査読を意味しない。
計算機代数、数値行列、solver、simulation、科学実装は使っていない。

## 1. tensor積と二species CARの規約

軌道labelは1,...,M。target基底と補助基底を

\[
|x\rangle=a_{x_1}^\dagger\cdots a_{x_N}^\dagger|0\rangle_a,
\quad x_1<\cdots<x_N,\qquad
|\alpha\rangle=|p q\rangle,\quad p<q
\]

と固定する。二species全体で

\[
\{a_p,a_q^\dagger\}=\{b_p,b_q^\dagger\}=\delta_{pq},
\quad \{a_p,b_q\}=\{a_p,b_q^\dagger\}=0
\tag{C1}
\]

を満たし、他の同種反交換子は0とする。
元のtensor積からのisometry \(\Phi\)は

\[
\Phi(|x\rangle\otimes|p q\rangle)
=a_{x_1}^\dagger\cdots a_{x_N}^\dagger b_p^\dagger b_q^\dagger|0\rangle.
\tag{C2}
\]

すなわち**全a creation、次に全b creation**である。
tensor積のoddな演算子を単純に互いに反可換とはしない。
例えば\(b_p=(-1)^{\hat n_a}\otimes\widetilde b_p\)というparity付き表現で(C1)を実現できる。
ここで用いる\(a_p^\dagger a_q\)、\(b_q^\dagger b_p\)、二対の偶演算子は異species間で可換。
bの二個のannihilation／creationではparityが二回現れるので、(C2)上で追加の\((-1)^N\)は残らない。

\(A_{pq}=a_q a_p\)、\(B_{pq}=b_q b_p\)（p<q）と置く。
\(\hat n_b=2\)に限ると

\[
B_\beta^\dagger B_\alpha|\gamma\rangle_b
=\delta_{\alpha\gamma}|\beta\rangle_b.
\tag{C3}
\]

従って検証対象は、二species上では

\[
C_N\Phi J_N\Phi^\dagger
=\sum_{\alpha\beta} A_\alpha^\dagger A_\beta B_\beta^\dagger B_\alpha,
\qquad C_N=\binom N2.
\tag{C4}
\]

補助matrix unitは\(|\beta\rangle\langle\alpha|\)であり、転置して\(|\alpha\rangle\langle\beta|\)に変更しない。
以下では\(\Phi\)で同定した\(J_N\)を単にJと書く。

## 2. Kの二乗を4種類の縮約へ分ける

\[
K=\sum_{pq}a_p^\dagger a_q b_q^\dagger b_p.
\]

異speciesの偶演算子を交換し、各speciesにCARを一度使うと

\[
K^2=\sum_{pqrs}
(\delta_{qr}a_p^\dagger a_s-a_p^\dagger a_r^\dagger a_q a_s)
(\delta_{ps}b_q^\dagger b_r-b_q^\dagger b_s^\dagger b_p b_r).
\tag{C5}
\]

この段階では固定粒子数の値を代入しない。

**両方を縮約する項**は

\[
\sum_{pq}a_p^\dagger a_p b_q^\dagger b_q=\hat n_a\hat n_b.
\tag{C6}
\]

**aだけを縮約する項**は

\[
-\sum_{pqs}a_p^\dagger a_s b_q^\dagger b_s^\dagger b_p b_q
=-(\hat n_b-1)K.
\tag{C7}
\]

ここで符号と「−1」は

\[
\sum_q b_q^\dagger b_s^\dagger b_p b_q
=b_s^\dagger\hat n_b b_p=(\hat n_b-1)b_s^\dagger b_p
\]

から得る。\(\hat n_b b_p=b_p(\hat n_b-1)\)を使っており、annihilationの途中で粒子数を元の値のまま固定してはいけない。

**bだけを縮約する項**も同様に

\[
-\sum_{pqr}a_p^\dagger a_r^\dagger a_q a_p b_q^\dagger b_r
=-(\hat n_a-1)K,
\tag{C8}
\]

なぜなら\(\sum_p a_p^\dagger a_r^\dagger a_q a_p=a_r^\dagger\hat n_a a_q\)だからである。

**縮約しない項**は

\[
D=\sum_{pqrs}a_p^\dagger a_r^\dagger a_q a_s
b_q^\dagger b_s^\dagger b_p b_r.
\]

\(p<r,q<s\)のordered pairに直すと

\[
a_p^\dagger a_r^\dagger a_q a_s=-A_{pr}^\dagger A_{qs},
\qquad b_q^\dagger b_s^\dagger b_p b_r=-B_{qs}^\dagger B_{pr}.
\]

二つのminusが相殺する。
\(p\leftrightarrow r\)又は\(q\leftrightarrow s\)の交換ではa側とb側が同時に反転するので、各ordered pairに4個の同じ項が対応する。
一致する添字の項は反交換性により0。従って

\[
D=4\sum_{\alpha\beta}A_\alpha^\dagger A_\beta B_\beta^\dagger B_\alpha
=4C_NJ\quad(\hat n_b=2).
\tag{C9}
\]

この係数4は、積分の1/4規約から借りたものではなく、ordered pair化の二つのfactor 2である。

## 3. 固定sectorでの恒等式

(C6)–(C9)を足すと、\(\hat n_a=N,\hat n_b=2\)において

\[
K^2=2NI-[(N-1)+(2-1)]K+4C_NJ
=2NI-NK+4C_NJ.
\]

従って

\[
\boxed{\displaystyle
J=\frac{K^2+NK-2NI}{4\binom N2}}
\tag{C10}
\]

を得る。ここまでの導出はM=5、N=3だけでなく、有限Mと\(2\le N\le M\)の全ての非空な指定sectorに対する代数恒等式。
補助粒子数が2でない場合、(C3)のmatrix-unit対応をそのまま使えない。

## 4. spin演算子へ移す符号

\[
S_+=\sum_p a_p^\dagger b_p,\quad S_-=S_+^\dagger,
\quad S_z=(\hat n_a-\hat n_b)/2.
\]

\[
S_+S_-=\sum_{pq}a_p^\dagger b_p b_q^\dagger a_q
=\hat n_a-\sum_{pq}a_p^\dagger b_q^\dagger b_p a_q
=\hat n_a-K.
\tag{C11}
\]

最後の項ではa_qを二つのb演算子の向こうへ動かすのでminusは追加されない。
CARから\([S_+,S_-]=2S_z\)であり、
\(S_+S_-=S^2-S_z(S_z-1)\)。従って固定\(m=(N-2)/2\)で

\[
K=N I-S^2+m(m-1)I.
\tag{C12}
\]

同一軌道のa／bは仮想spinのup／downであり、元電子の物理spinに関する追加仮定ではない。
元のM個のspin-orbitalを、M個の仮想site・2M個のmodeへ符号化しただけである。

weight \(w_i=n_i+m_i\)を固定し、double数r、single数sとすると
\(s=N+2-2r\)。singleはspin 1/2、emptyとdoubleはspin 0。
\(S\ge m\)、\(S\le s/2\le m+2\)なので、存在するsectorのspinは\(m,m+1,m+2\)の一部。
軌道数又はweightが許さないsectorを追加しない。
(C12)の固有値は順に\(2,2-N,-2N\)、(C10)へ代入すると

\[
\boxed{\lambda_m=1/C_N,\quad \lambda_{m+1}=-2/N,\quad \lambda_{m+2}=1.}
\tag{C13}
\]

N=2では最初と最後が同じ+1であり、「常に3種類の異なる値」という意味ではない。
M=5・N=3での存在sector、multiplicity、作用の別経路確認は[小例](small_example_and_control.md)へ。
ここでの一般的なCAR保証を、小例で数個の状態を調べただけの外挿とはしない。

## 5. 判定の範囲

| 対象 | 判定 | 根拠 |
|---|---|---|
| tensor積→二species | 確認 | (C2)とparity付きCAR。偶演算子対応に追加の\((-1)^N\)なし |
| pairの添字と符号 | 確認 | (C3),(C4),(C9)。補助は\(\vert\beta\rangle\langle\alpha\vert\) |
| 係数4、\(C_N\)、scalar | 確認 | 4縮約の明示展開。定数\(-2NI\)を保持 |
| spinと3値の対応 | 確認 | (C11)–(C13)、存在しないsectorを除く |
| 実装の有限精度／費用 | 今回未解決 | 紙上の演算子同値から、compile結果・資源優位・絶対E0の全算法を結論しない |

過去SOURCE本文は訂正せず保全する。今回、対象式に符号・係数・scalarの訂正が必要となる誤りは発見しなかった。
新アルゴリズム候補の採択、J1の再開、追加探索は行わない。
