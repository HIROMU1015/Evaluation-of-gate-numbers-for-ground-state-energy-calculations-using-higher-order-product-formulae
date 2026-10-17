## 3. 本レビューの独立紙上導出：固定wordは既に3次で不成立

### 3.1 命題と適用範囲

以下で演算子のtensor積に現れる恒等演算子を適宜省略する。元契約どおり

\[
L_j=d\Gamma(\ell_j),\qquad
\ell_1=\operatorname{diag}(1,-1,2,-2),\qquad
\ell_2=\begin{pmatrix}
0&1&0&0\\
1&0&1&0\\
0&1&0&1\\
0&0&1&0
\end{pmatrix},
\]

\[
A=L_1\otimes X_b,\quad B=L_1\otimes P_b,\quad
C=L_2\otimes X_b,\quad D=L_2\otimes P_b,
\qquad [X_b,P_b]=iI_b
\]

とする。固定された時系列wordと積は

\[
(G_1,\ldots,G_{12})=(A,B,C,D,A,C,B,D,A,D,B,C),
\]

\[
U(\eta)=U_{12}\cdots U_1,\qquad
U_j=\exp(-i\eta x_jG_j).
\]

目標は

\[
\log U(\eta)=-i\eta^2(L_1^2+L_2^2)\otimes I_b
\pmod{\eta^5}.
\tag{1}
\]

これはS02–S03の条件そのものである。

**命題。** この固定word、固定factor、full Fockの意味で、(1)を満たすη非依存の実振幅は存在しない。実際、1次と2次の必要条件を満たした時点で、消せない3次のbus依存項が残る。この結論は振幅上限を使わず、\(x\in\mathbb R^{12}\)にも成立する。

以下は形式級数・演算子代数の紙上証明であり、数値行列プログラム、438条件の再生成、solver、busの有限cutoffを使わない。

### 3.2 1次の閉鎖条件

full Fock上で(1)が成立するなら、粒子数を保存する各演算子をN=1部分空間へ制限しても成立しなければならない。N=1上で\(L_j\)は\(\ell_j\)として作用する。

\(\ell_1\)は非零対角、\(\ell_2\)は非零非対角であり線形独立である。また\(X_b,P_b\)も線形独立なので、1次項が消えるには各primitiveの振幅和が0でなければならない。

\[
\begin{aligned}
x_1+x_5+x_9&=0, &x_2+x_7+x_{11}&=0,\\
x_3+x_6+x_{12}&=0, &x_4+x_8+x_{10}&=0.
\end{aligned}
\tag{2}
\]

ここでN=1を用いることは、元の判定をN=1へ変更して救済する操作ではない。**full Fockでの恒等式を否定するため、その必要条件を部分空間で調べている。** N=2限定の成否は、この論法からは判断しない。

(2)を使い、振幅を

\[
(x_1,\ldots,x_{12})=
(a,c,e,g,b,f,d,h,-a-b,-g-h,-c-d,-e-f)
\tag{3}
\]

と書く。

### 3.3 2次項を6個の符号付き面積に集約する

primitiveの順を\(A<B<C<D\)とする。各pair\(r<s\)について

\[
M_{rs}:=
\sum_{j:G_j=s}x_j\sum_{k<j:G_k=r}x_k
\tag{4}
\]

を定義する。1次の閉鎖条件の下では、時系列の逆順積に対する2次logは

\[
[\log U]_{\eta^2}
=\sum_{r<s}M_{rs}[G_r,G_s].
\tag{5}
\]

ここで\([\log U]_{\eta^2}\)はη²の係数を表す。符号は

\[
\frac12\sum_{j>k}[-ix_jG_j,-ix_kG_k]
\]

から直接得られる。各pairの「rが先、sが後」と「sが先、rが後」の和は、(2)によって0なので、差の1/2が(4)になる。

固定wordに(3)を代入し、位置を順に追うと、

\[
\begin{array}{ll}
M_{AB}=ac+(a+b)d, & M_{AC}=ae+(a+b)f,\\
M_{AD}=ag+(a+b)h, & M_{BC}=c(e+f),\\
M_{BD}=-dg, & M_{CD}=-fg.
\end{array}
\tag{6}
\]

を得る。たとえば\(M_{CD}=eg+(e+f)h-(e+f)(g+h)=-fg\)である。これは12個の位置の手計算による整理であり、保存多項式の科学的再集計ではない。

必要な交換子は

\[
[A,B]=iL_1^2\otimes I_b,\qquad
[C,D]=iL_2^2\otimes I_b,
\tag{7}
\]

\[
[A,C]=[L_1,L_2]\otimes X_b^2,\qquad
[B,D]=[L_1,L_2]\otimes P_b^2,
\tag{8}
\]

\[
\begin{aligned}
[A,D]&=\tfrac12[L_1,L_2]\otimes\{X_b,P_b\}
       +\tfrac{i}{2}\{L_1,L_2\}\otimes I_b,\\
[B,C]&=\tfrac12[L_1,L_2]\otimes\{X_b,P_b\}
       -\tfrac{i}{2}\{L_1,L_2\}\otimes I_b.
\end{aligned}
\tag{9}
\]

(9)は\(X_bP_b=(\{X_b,P_b\}+iI_b)/2\)と\(P_bX_b=(\{X_b,P_b\}-iI_b)/2\)を用いて展開すれば得られる。

### 3.4 2次目標が振幅の構造を強制する

N=1上で\([\ell_1,\ell_2]\neq0\)である。例えばその(1,2)成分は2である。独立なWeyl成分\(X_b^2,P_b^2,\{X_b,P_b\},I_b\)を比較すると、不要bus項の消去には

\[
M_{AC}=M_{BD}=0,\qquad M_{AD}+M_{BC}=0
\tag{10}
\]

が必要である。

さらに、N=1上で\(\ell_1^2,\ell_2^2,\{\ell_1,\ell_2\}\)は線形独立である。確認に必要な成分は簡単で、

\[
\ell_1^2=\operatorname{diag}(1,1,4,4),\qquad
\ell_2^2=\begin{pmatrix}
1&0&1&0\\
0&2&0&1\\
1&0&2&0\\
0&1&0&1
\end{pmatrix},
\]

\(\{\ell_1,\ell_2\}\)の非零成分は(2,3)と(3,2)の1だけである。したがって、(2,3)成分、(1,3)成分、対角成分を順に見れば独立性が分かる。

bus恒等成分を目標\(-i(L_1^2+L_2^2)\)と一致させるため、

\[
M_{AB}=M_{CD}=-1,\qquad M_{AD}-M_{BC}=0.
\tag{11}
\]

(10)と(11)より、mixed pairの面積はすべて0である。

\[
M_{AC}=M_{AD}=M_{BC}=M_{BD}=0.
\tag{12}
\]

ここまでの条件を(6)へ順に代入する。

\[
\begin{aligned}
-fg=-1&\ \Rightarrow\ fg=1,\ f,g\neq0,\\
-dg=0&\ \Rightarrow\ d=0,\\
ac+(a+b)d=-1&\ \Rightarrow\ ac=-1,\ a,c\neq0,\\
c(e+f)=0&\ \Rightarrow\ e=-f,\\
ae+(a+b)f=0&\ \Rightarrow\ b=0,\\
ag+(a+b)h=0&\ \Rightarrow\ h=-g.
\end{aligned}
\tag{13}
\]

従って、1次と2次を満たす振幅は必ず

\[
\boxed{
x=(a,c,-f,g,0,f,0,-g,-a,0,-c,0),\qquad
ac=-1,\quad fg=1.
}
\tag{14}
\]

となる。元のbox内では\(|a|=|c|=|f|=|g|=1\)、\(c=-a\)、\(g=f\)となり、2次までの候補は4組に限られる。ただし、次の不成立証明にはこのboxによる限定を使わない。

重要なのは、12個の振幅を自由に調整できるように見えたansatzが、既に2次条件によって、4個のzero pulseを持つ特定の入れ子構造へ縮退することである。

### 3.5 入れ子閉路のexactな書換え

(14)の下で、

\[
V_\eta=e^{ic\eta B}e^{ia\eta A},
\]

\[
R_2=e^{ig\eta D}e^{-if\eta C}e^{-ig\eta D}e^{if\eta C}
\]

と置く。\([C,D]=iL_2^2\)はCとDに可換なので、central commutatorの恒等式から

\[
R_2=e^{-ifg\eta^2L_2^2}=e^{-i\eta^2L_2^2}.
\tag{15}
\]

同様に

\[
V_\eta e^{-ic\eta B}e^{-ia\eta A}
=e^{iac\eta^2L_1^2}=e^{-i\eta^2L_1^2}.
\tag{16}
\]

固定wordの非zero pulseを実際の積順に並べると、

\[
\begin{aligned}
U(\eta)
&=e^{ic\eta B}e^{ia\eta A}
 e^{ig\eta D}e^{-if\eta C}e^{-ig\eta D}e^{if\eta C}
 e^{-ic\eta B}e^{-ia\eta A}\\
&=\left(V_\eta e^{-i\eta^2L_2^2}V_\eta^{-1}\right)
  e^{-i\eta^2L_1^2}.
\end{aligned}
\tag{17}
\]

この恒等式は「二つの平方をそのまま足す」構成ではない。L2²を生成する閉路が、まだ完了していないL1による条件付き変位の中に挿入され、L2²が\(V_\eta\)で共役されている。

### 3.6 消せない3次項

共役の1次展開より

\[
\begin{aligned}
V_\eta(L_2^2\otimes I_b)V_\eta^{-1}
&=L_2^2\otimes I_b
+i\eta[L_1,L_2^2]\otimes(aX_b+cP_b)
+O(\eta^2).
\end{aligned}
\tag{18}
\]

(17)の二つの指数の先頭は双方η²なので、それらの間のBCH交換子はη⁴から始まる。従って、

\[
\boxed{
\log U(\eta)
=-i\eta^2(L_1^2+L_2^2)\otimes I_b
+\eta^3[L_1,L_2^2]\otimes(aX_b+cP_b)
+O(\eta^4).
}
\tag{19}
\]

この3次係数は零ではない。N=1上で

\[
([\ell_1,\ell_2^2])_{13}
=(1-2)(\ell_2^2)_{13}=-1.
\tag{20}
\]

また\(ac=-1\)だからaとcは非零で、\(X_b,P_b\)の線形独立性から\(aX_b+cP_b\neq0\)である。したがって(19)のbus依存項を消すことはできず、(1)は成立しない。□

### 3.7 証明から分かること／分からないこと

**分かること**：

- 固定wordの不成立は、4次の複雑な高体項に初めて現れるのではなく、3次で既に決まる。
- 438条件の再求解、別solver、全traceの再構築をしなくても、元の固定問題に対する不成立を別経路で説明できる。
- このwordで振幅boxを広げても改善しない。3次条件の失敗を含む、より高い形式次数を要求しても改善しない。
- 障害は、条件付き変位によるL2²の共役と、その残留bus作用である。
- 少なくとも今回の固定問題では、N=1に制限した必要条件の段階で障害がある。従って、N=2の非自明な二電子CAR構造を利用した共同設計の一般的可能性まで試せたわけではない。

**分からないこと**：

- 別word・別factor・sector限定条件・別の許可制御でP1*が成立するか。
- 保存された438行の各係数がすべて正しく生成されたか。
- solver実装・driver全般が任意入力で正しいか。
- 新規性・有限時間の誤差保証・物理的couplingの実現費用。

本証明はZ3と条件生成コードに依存しないが、本レビュー内で行った紙上導出である。**外部の独立査読、形式証明器、機械検証済み証明書の取得とは区別する。** 確度は高いと判断するが、研究成果として採用する際には短い導出の独立した読み合わせが適切である。

---

## 4. 別の12-pulse既知構成：segment数だけの不可能性ではない

### 4.1 単独factorの閉路

一つのHermitian電子演算子Lについて、

\[
\begin{aligned}
R_L(u,v)
&=e^{-iu\eta L\otimes X_b}
  e^{-iv\eta L\otimes P_b}
  e^{iu\eta L\otimes X_b}
  e^{iv\eta L\otimes P_b}\\
&=e^{-iuv\eta^2L^2}\otimes I_b.
\end{aligned}
\tag{21}
\]

これは、\([L\otimes X_b,L\otimes P_b]=iL^2\otimes I_b\)が両生成元に可換なためのexactな幾何学的閉路である。条件付きdisplacementとbusの自動的なdisentanglementは既知の研究であり、この式を新原理とは扱わない。[L01, L02]

### 4.2 3個の閉路を対称に組み合わせる

\[
S(\eta)=R_{L_1}(1,\tfrac12)\,
        R_{L_2}(1,1)\,
        R_{L_1}(1,\tfrac12)
\]

とすれば、

\[
S(\eta)=
 e^{-i\eta^2L_1^2/2}
 e^{-i\eta^2L_2^2}
 e^{-i\eta^2L_1^2/2}\otimes I_b.
\tag{22}
\]

\(\tau=\eta^2\)に関する通常のStrang分割であり、

\[
\log S(\eta)=-i\eta^2(L_1^2+L_2^2)\otimes I_b+O(\eta^6).
\tag{23}
\]

従って元の「η⁴まで一致」という精度条件を満たす。各閉路は4 pulse、合計12 pulseであり、振幅は\(\pm1,\pm1/2\)の範囲内である。

具体的に、元契約と同じ「時系列を右から作用させる」規約では、別の時系列wordと振幅を

```text
word:       B, A, B, A, D, C, D, C, B, A, B, A
amplitude: -1/2,-1,1/2,1,-1,-1,1,1,-1/2,-1,1/2,1
```

と書ける。これは(21)–(22)を書き下した紙上の既知構成であり、新しい科学jobの実行結果ではない。

### 4.3 この比較からの結論

この構成は**元の固定wordとは違う**。したがって、既存のUNSATの反例や、その計算の救済結果ではない。また単独factor閉路と既知PFに完全に分解されるため、P1*が求める独立した共同閉路生成原理を実証しない。

しかし、「4 modes・2 factor・1 bus・12 pulse・box・形式4次」という大枠だけでは不可能でないことは分かる。**今回の不成立を、12 segment数そのものや補助振動子方式全体の不足へ帰属させることはできない。**

この既知比較構成の役割は、将来の検証器に対するpositive controlと、P1*で新たに主張する差分の基準である。今回これをdriverへ入力したり、回路を生成・compileしたりしてはいない。今後の人工検証として使う場合も、その作業範囲を明示する。

なお「12未満なら成功」「必ず2倍改善」といった新しい成功基準は設定しない。今回の12-pulse構成は比較点であって、ユーザーが採択していない資源gateではない。

---

