# P1*固定wordの3次障害：独立した紙上検証

2026-10-17 JST。対象はP1STAR-A-v1の固定factor・固定word・full Fock formal-log目標。ユーザーが今回指定した数学的導出の検証を行った。**新たな紙上導出はあるが、計算機による科学計算・記号展開・solver・数値行列検算・新ansatz探索は0件。** 既存のSOURCE、結果、科学契約、承認、STOP／PAUSEを変更しない。

読む順序：本書 → [検証対象レビュー§3–§4の固定抜粋](review_sections_3_4_snapshot.md) → [provenance](provenance.json)。元レビュー全体の過去研究評価や研究方針を再審査・採択する作業ではない。

**結論：GPTレビューの1次・2次拘束、3次残差の正符号と係数1、固定wordの全実振幅に対する不成立、別12-pulse比較構成の形式4次整合を、元契約からの紙上導出で確認した。中心命題を訂正する誤りや未処理の振幅分岐は見つからなかった。** この文書はsolver証明書でも機械検証でもない。保存438条件の各係数が正しいことを新たに検証したものでもない。

## 1. 固定問題と独立性

正本は科学契約commit `1771564d919837e2440a9fcb175ac054284a729c` の[契約草案][contract]。実行入力は結果commit `9555517933596615064713e1988849835453eeb8` の[scientific_input.json][input]。限定監査はcommit `37e5002a7e32a7f0c3f70cdd098f2ee145b828e7` の[監査記録][audit]。本branchは最後のcommitを起点とする。

4 modesの一体行列は、\(\ell_1=\operatorname{diag}(1,-1,2,-2)\)、\(\ell_2\)は隣接成分\((1,2),(2,3),(3,4)\)とその転置だけが1の4点鎖。\(L_j=d\Gamma(\ell_j)=\sum_{pq}(\ell_j)_{pq}a_p^\dagger a_q\) とし、

\[
A=L_1\otimes X,\quad B=L_1\otimes P,\quad
C=L_2\otimes X,\quad D=L_2\otimes P,\qquad [X,P]=iI.
\]

時系列は \((A,B,C,D,A,C,B,D,A,D,B,C)\)、\(U=U_{12}\cdots U_1\)、\(U_j=\exp(-i\eta x_jG_j)\)。\(x_j\)はη非依存の実数。目標は

\[
\log U=-i\eta^2K\otimes I+O(\eta^5),\qquad K=L_1^2+L_2^2. \tag{T}
\]

以下のO記号は全て**形式次数**を意味する。有限ηでのノルム誤差やunbounded busの解析的収束は主張しない。1次・2次条件はwordの位置とCAR／CCRから導き、3次は低次条件で強制される積をexactな単独factor閉路へ書き換えて導く。保存された438条件、Z3、driverの係数生成関数は導出に使わない。

## 2. CARから得るN=1必要条件と1次閉鎖

CARと真空の定義から、\(a_p^\dagger a_q a_r^\dagger|0\rangle=\delta_{qr}a_p^\dagger|0\rangle\)。従ってN=1上で\(L_j\)の作用は\(\ell_j\)。全primitiveは粒子数を保存するので、full Fock恒等式(T)があればN=1上でも(T)が成立する。

ここで使うのは必要条件であり、元の主判定をN=1へ変更していない。特に \((L_2^2)|_{N=1}=\ell_2^2\) は制限後の積の関係であって、full Fockで \(L_2^2=d\Gamma(\ell_2^2)\) と置き換えてはいない。N=2限定の成立性は、このN=1必要条件からは判断できない。

\(\log U=\eta\Omega_1+\eta^2\Omega_2+\eta^3\Omega_3+\cdots\) と置く。1次は \(\Omega_1=-i\sum_jx_jG_j\)。N=1の(1,1)成分を取ればA/Bの和、(1,2)成分を取ればC/Dの和が得られる。XとPは線形独立なので、必要条件は

\[
\begin{split}
x_1+x_5+x_9=0,&\quad x_2+x_7+x_{11}=0,\\
x_3+x_6+x_{12}=0,&\quad x_4+x_8+x_{10}=0.
\end{split} \tag{1}
\]

この4式で全振幅を

\[
x=(a,c,e,g,b,f,d,h,-a-b,-g-h,-c-d,-e-f) \tag{2}
\]

と書く。これは全ての1次解の単なる座標表示で、追加制約ではない。

## 3. 2次の符号・全6面積・分岐を失わない拘束

\(Z_j=-ix_jG_j\) とする。積の2次係数は \(\frac12\sum_jZ_j^2+\sum_{j>k}Z_jZ_k\)、logではそこから \(\frac12(\sum_jZ_j)^2\) を引くので、

\[
\Omega_2=\frac12\sum_{j>k}[Z_j,Z_k]
=-\frac12\sum_{j>k}x_jx_k[G_j,G_k]. \tag{3}
\]

\(A<B<C<D\) とし、\(M_{rs}=\sum_{j:G_j=s}x_j\sum_{k<j:G_k=r}x_k\) と定義する。rが先・sが後の対は(3)に \(+\frac12x_jx_k[G_r,G_s]\) を与える。逆順の対の振幅積和との合計は(1)から0。従って

\[
\Omega_2=\sum_{r<s}M_{rs}[G_r,G_s]. \tag{4}
\]

次の表は固定wordの各s出現位置で、その前にあるrの累積振幅を取った**手計算**である。式の生成コードや保存条件の再集計は使っていない。

| pair | 時系列からの3寄与 | 整理した面積 |
| --- | --- | --- |
| AB | \(ac+(a+b)d+0(-c-d)\) | \(ac+(a+b)d\) |
| AC | \(ae+(a+b)f+0(-e-f)\) | \(ae+(a+b)f\) |
| AD | \(ag+(a+b)h+0(-g-h)\) | \(ag+(a+b)h\) |
| BC | \(ce+cf+0(-e-f)\) | \(c(e+f)\) |
| BD | \(cg+(c+d)h-(c+d)(g+h)\) | \(-dg\) |
| CD | \(eg+(e+f)h-(e+f)(g+h)\) | \(-fg\) |

電子／busを別tensor factorとして二つの積を引けば、必要な交換子は

\[
\begin{aligned}
[A,B]&=iL_1^2\otimes I,&[C,D]&=iL_2^2\otimes I,\\
[A,C]&=[L_1,L_2]\otimes X^2,&[B,D]&=[L_1,L_2]\otimes P^2,\\
[A,D]&=\tfrac12[L_1,L_2]\otimes\{X,P\}+\tfrac i2\{L_1,L_2\}\otimes I,\\
[B,C]&=\tfrac12[L_1,L_2]\otimes\{X,P\}-\tfrac i2\{L_1,L_2\}\otimes I.
\end{aligned} \tag{5}
\]

最後の二式のscalar項の符号は、\(XP=(\{X,P\}+iI)/2\)、\(PX=(\{X,P\}-iI)/2\) から別々に確認した。電子演算子の順序は変更していない。

N=1で \([\ell_1,\ell_2]_{12}=2\neq0\)。formal Weyl成分 \(X^2,P^2,\{X,P\},I\) を比較し、不要bus成分の零化は

\[
M_{AC}=M_{BD}=0,\qquad M_{AD}+M_{BC}=0. \tag{6}
\]

bus恒等成分の比較には、\(\ell_1^2,\ell_2^2,\{\ell_1,\ell_2\}\) の線形独立性を確認する。必要なのは3成分だけである。

- (2,3)：最初の二つは0、反交換子は \((-1+2)(\ell_2)_{23}=1\)。
- (1,3)：\(\ell_1^2\)と反交換子は0、\((\ell_2^2)_{13}=(\ell_2)_{12}(\ell_2)_{23}=1\)。
- (1,1)：上の二つの係数が0になった後、\((\ell_1^2)_{11}=1\) が残る。

従って目標の電子係数から

\[
M_{AB}=M_{CD}=-1,\qquad M_{AD}-M_{BC}=0. \tag{7}
\]

(6)–(7)により4個のmixed面積は全て0。表へ順に戻すと

\[
fg=1\Rightarrow f,g\ne0\Rightarrow d=0,
\quad ac=-1\Rightarrow a,c\ne0,
\quad e=-f,\quad bf=0\Rightarrow b=0,\quad a(g+h)=0\Rightarrow h=-g.
\]

全ての除算には、その直前に示した非零性がある。振幅分岐を落としていない。結果は

\[
\boxed{x=(a,c,-f,g,0,f,0,-g,-a,0,-c,0),\qquad ac=-1,\quad fg=1.} \tag{8}
\]

(8)は必要なだけでなく、(1)、面積表、(5)へ代入すればfull Fockで \(\Omega_1=0\)、\(\Omega_2=-iK\otimes I\) を満たす。元box内にも \(|a|=|c|=|f|=|g|=1\)、\(c=-a,g=f\) の4組がある。従って「既に3次で不成立」は、実は2次まで全く解がないという意味ではない。

## 4. 積を直接書き、3次残差を求める

(8)の4個のzero pulseを除くと、**右が時刻の早い側**となる積は

\[
U=e^{ic\eta B}e^{ia\eta A}
e^{ig\eta D}e^{-if\eta C}e^{-ig\eta D}e^{if\eta C}
e^{-ic\eta B}e^{-ia\eta A}. \tag{9}
\]

\(V=e^{ic\eta B}e^{ia\eta A}\)、\(T_1=e^{-ic\eta B}e^{-ia\eta A}\) と置く。**\(T_1\neq V^{-1}\) 一般に**。この順序を取り違えるとL1²の寄与を失う。

\([C,D]=iL_2^2\)はC,Dに可換なので、中央の4指数はcentral commutatorの恒等式より

\[
R_2=e^{ig\eta D}e^{-if\eta C}e^{-ig\eta D}e^{if\eta C}
=e^{-ifg\eta^2L_2^2}=e^{-i\eta^2L_2^2}. \tag{10}
\]

同様に \([B,A]=-iL_1^2\) を用いると、

\[
VT_1=e^{[ic\eta B,ia\eta A]}=e^{iac\eta^2L_1^2}=e^{-i\eta^2L_1^2}. \tag{11}
\]

この恒等式では交換子がそれぞれの生成元に可換であることを使っている。別factor同士の可換性は仮定しない。(9)に正しい順序で \(V^{-1}V\) を挿入して

\[
U=(VR_2V^{-1})(VT_1)
=\exp[-i\eta^2V(L_2^2\otimes I)V^{-1}]
 \exp[-i\eta^2L_1^2\otimes I]. \tag{12}
\]

ここで \(V=I+i\eta(cB+aA)+O(\eta^2)\) なので、

\[
V(L_2^2\otimes I)V^{-1}
=L_2^2\otimes I+i\eta[L_1,L_2^2]\otimes(aX+cP)+O(\eta^2). \tag{13}
\]

(12)の両指数の先頭次数はη²。BCHの指数間交換子はη⁴以上であり、η³には寄与しない。さらに(13)の \(i\eta\) と指数の \(-i\eta^2\) の積は **\(+\eta^3\)**。従って

\[
\boxed{\log U=-i\eta^2(L_1^2+L_2^2)\otimes I
+\eta^3[L_1,L_2^2]\otimes(aX+cP)+O(\eta^4).} \tag{14}
\]

係数は1であり、余分なi、1/2、負号は付かない。HermitianなL1,L2の交換子がanti-Hermitianなので、この3次項もformal logの性質と整合する。**(14)は1次・2次条件を満たした振幅(8)の下での式であり、一般の12振幅に対する3次公式ではない。**

## 5. 非零性とbox拡大では消えない理由

N=1上で

\[
([\ell_1,\ell_2^2])_{13}=(1-2)(\ell_2^2)_{13}=-1.
\]

従って(14)のη³係数の電子(1,3)成分は \(-(aX+cP)\)。もし \(aX+cP=0\) なら、そのPとの交換子は \(iaI=0\)、Xとの交換子は \(-icI=0\) となる。これは \(ac=-1\) と矛盾する。よってΩ3は非零で、(T)は成立しない。

ここまで振幅上限を一度も使っていない。従って同じη非依存の実振幅・同じword・factor・target・full Fock条件なら、\([-1,1]^{12}\)だけでなく**全ての有限実振幅 \(\mathbb R^{12}\)** に解がない。これによりbox拡大だけの救済は否定される。3次一致を含むより高次数の同じ目標も満たせない。

これは数学的な適用範囲の確認であって、boxの変更・高次数job・sector切替の実行承認ではない。η依存振幅、別factor、別word、追加pulse等を許す別問題への結論ではない。

## 6. レビューに既出の別12-pulse構成の確認

ここではレビュー§4に既に記載された構成だけを検証する。新しいwordを探索・提案したものではない。一つの電子Hermitian演算子Lに対し、

\[
R_L(u,v)=e^{-iu\eta L\otimes X}e^{-iv\eta L\otimes P}
e^{iu\eta L\otimes X}e^{iv\eta L\otimes P}
=e^{-iuv\eta^2L^2}\otimes I. \tag{15}
\]

理由は \([-iu\eta L X,-iv\eta L P]=-iuv\eta^2L^2\otimes I\) が両指数生成元に可換だからである。4つのconditional displacementでbusを戻す機構は既知である。[Spiller et al., v3, §IV, Eqs. (7)–(9)](https://arxiv.org/html/quant-ph/0509202v3#S4)を確認した。ただし同論文のqubit gateを、そのまま化学factorの実装費用保証と同一視しない。(15)の本設定への対応は、ここで交換子から直接示した。

レビューに指定された3閉路の積は

\[
S=R_{L_1}(1,1/2)R_{L_2}(1,1)R_{L_1}(1,1/2)
=e^{-i\eta^2L_1^2/2}e^{-i\eta^2L_2^2}e^{-i\eta^2L_1^2/2}\otimes I. \tag{16}
\]

\(\tau=\eta^2\)、\(F=-iL_1^2,G=-iL_2^2\) と置くと、\(S(\tau)=e^{\tau F/2}e^{\tau G}e^{\tau F/2}\)。\(S(-\tau)=S(\tau)^{-1}\) なので、η=0で0となるformal logはτの奇数次数だけを含む。τの1次係数はF+Gであるため、

\[
\log S=-i\eta^2(L_1^2+L_2^2)\otimes I+O(\eta^6). \tag{17}
\]

これは通常の対称Strang積であり、形式4次の目標を満たす。Strangの原論文の[出版社情報](https://doi.org/10.1137/0705041)は書誌確認に用いた。本文全式の再査読は行わず、(17)の次数は上の対称性から本書内で確認した。busは各(15)で戻るが、電子側の \(\exp[-i\eta^2K]\) への一致は一般に有限ηでexactではない。

時系列は次のとおりで、右から作用する積に戻すと最初と最後の4 pulseが \(R_{L_1}(1,1/2)\)、中央が \(R_{L_2}(1,1)\) になる。

```text
word:       B, A, B, A, D, C, D, C, B, A, B, A
amplitude: -1/2,-1,1/2,1,-1,-1,1,1,-1/2,-1,1/2,1
```

全振幅は元box内で、非零pulseは12個。**ただしprimitiveの登場回数はA/Bが各4、C/Dが各2であり、固定wordの各3回とは異なる。** 従って「同じprimitive・factor・1 bus・box・12 pulse・形式次数」という大枠の比較例であり、固定wordの反例でも、各primitive3回という追加制限の下での成功例でもない。単独factor閉路と既知対称PFに分解でき、P1*固有の共同生成原理を示さない。今回これをdriverへ入力・実装・compileしていない。

## 7. 検証結果・明確化事項・限界・引き渡す知見

| 対象 | 判定と適用範囲 |
| --- | --- |
| レビュー§3の1次・2次拘束と振幅族 | **確認**。(1)–(8)をCAR／CCR、wordの累積振幅、必要な3成分から独立に導出。非零性を確認してから消去するため、例外分岐なし。 |
| 3次残差 | **確認**。正符号、係数1、電子順序 \([L_1,L_2^2]\)、bus \(aX+cP\)。低次条件成立後という前提が必要。 |
| 固定wordの全実振幅での不成立 | **確認**。boxによらないN=1必要条件での非零3次残差。元のfull Fock目標を否定する。 |
| 既知12-pulse比較 | **確認・明確化**。O(η⁶)のformal-log残差、振幅box内。wordとprimitive訪問回数は異なる。固定ansatzの救済やP1*の独立新規性の証拠ではない。 |
| 中心結論の修正 | **不要**。レビュー§3–§4の中心数式の誤りは検出しなかった。上の前提・訪問回数・exact bus帰還と電子近似の区別を添えると射程が明確になる。元レビューは上書きしない。 |
| 保存438条件とsolver | **今回未検証**。この紙上の否定証明は、その全生成過程やZ3実装を認証しない。独立UNSAT certificate・形式証明器の成果物でもない。 |

次の構成原理探索に渡せる知見は、**低次の面積条件が自由度を失わせ、未完了の条件付き変位の中で別factorの平方を作ると、その平方の共役がbus依存残差を生む**という機構である。二つの単独閉路を作ったというだけで、入れ子になった積をその無共役の連結と扱ってはいけない。

この否定で本質的に使った非零性は \([L_1,L_2^2]\neq0\) と低次条件の強制である。単に \([L_1,L_2]\neq0\) という事実だけを、任意factor・任意wordに対する同じ障害の証明へ拡張しない。N=1で既に失敗するため、N=2固有のCAR関係を使う構成一般の可能性は決まらない。

数学的検証は人が追える有限な紙上導出であり、独立した別人の査読、機械証明、解析的domain評価ではない。有限時間の物理制御、原HamiltonianのE0への実装費用、資源優位、新規性、研究テーマ採択も未判定。これらを今回の検証成功から導かない。

**次の段階：GPT／ユーザーが、この不成立機構を次の構成原理検討の判断材料としてどう用いるかを判断する。Codexは本記録の公開・照合を完了してMandatory STOPする。** 次のword探索、科学計算、solver、追加レビュー、STOP解除や正式採択は自動開始しない。

[contract]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md
[input]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_final_freeze_20261017/scientific_input.json
[audit]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/37e5002a7e32a7f0c3f70cdd098f2ee145b828e7/docs/research_exploration/p1star_unsat_limited_static_audit_20261017/limited_static_audit.md
