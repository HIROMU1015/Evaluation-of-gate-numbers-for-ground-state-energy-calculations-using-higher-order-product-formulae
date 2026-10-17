# M=5・N=3：weight、coherence、有限角度、制御位相

2026-10-17 JST。**判定：確認。** 全て形式的なket・exactな分数による紙上導出。
数値行列生成、対角化、simulation、回路compileは行っていない。
規約は[CAR再導出](independent_car_derivation.md) (C1)–(C4)。以下\(|x;\alpha\rangle=|x\rangle\otimes|\alpha\rangle\)。

## 1. weight blockとspin multiplicity

target数3、補助数2なので総数5、固定\(m=S_z=1/2\)。
weight \(w_i=n_i+m_i\)はJ及びKで保存される。
double数rならsingle数は\(s=5-2r\)、そのうち補助に入るsingle数は\(k=2-r\)。
一つのweightに対する次元は\(\binom{s}{k}\)。

| r | weightの例 | s,k | 固定weightの次元 | 存在するSと固定mでのmultiplicity |
|---|---|---|---|---|
| 0 | (1,1,1,1,1) | 5,2 | 10 | S=1/2:5、S=3/2:4、S=5/2:1 |
| 1 | (2,1,1,1,0) | 3,1 | 3 | S=1/2:2、S=3/2:1 |
| 2 | (2,2,1,0,0) | 1,0 | 1 | S=1/2:1 |

single spinのfixed-m空間では、各spin-S irrepからm=1/2の状態が1個ずつ現れる。
spin-Sのコピー数は、magnetization SとS+1の状態数の差

\[
\mu_s(S)=\binom{s}{s/2-S}-\binom{s}{s/2-S-1}
\tag{E1}
\]

である。binomialの範囲外は0とし、この手での数え上げが表のmultiplicityを与える。
\(2S+1\)をここに再び掛けてはいけない。mを固定しているからである。
異なるweightの個数はr=0で1、r=1で20、r=2で30。
全体は\(1\cdot10+20\cdot3+30\cdot1=100=\binom53\binom52\)で、tensor積の次元とも整合する。

\(K=11I/4-S^2\)、\(J=(K^2+3K-6I)/12\)より

| S | Kの値 | Jの値 | 使用するphase |
|---|---|---|---|
| 1/2 | 2 | 1/3 | \(f_{1/2}=e^{-i\theta/3}\) |
| 3/2 | −1 | −2/3 | \(f_{3/2}=e^{+2i\theta/3}\) |
| 5/2 | −6 | 1 | \(f_{5/2}=e^{-i\theta}\) |

全3sectorが存在するのはr=0。r=1とr=2へ架空のsectorを足さない。

## 2. 指定状態へのJの直接作用

\[
u=|123;12\rangle,\quad v=|123;45\rangle,\quad
x=|345;12\rangle,\quad y=|245;13\rangle,\quad z=|145;23\rangle.
\]

targetでのannihilationは

\[
A_{12}|123\rangle=|3\rangle,\quad
A_{13}|123\rangle=-|2\rangle,\quad
A_{23}|123\rangle=|1\rangle.
\tag{E2}
\]

creation \(A_{45}^\dagger\)で残る一電子をascending orderへ直す交換はそれぞれ2回で、追加符号は+。
従って、spinや固有値を用いずJの定義から

\[
Ju=u/3,\qquad Jv=(x-y+z)/3.
\tag{E3}
\]

Juでは\(\beta=12\)だけが非零。他のpairを除いて12を戻そうとすると、残る1又は2でPauli零となる。
Jvでは初期補助が\(\alpha=45\)、最終補助がそれぞれ\(\beta=12,13,23\)。
この添字順序が、目的の二対交換の向きを固定する。

ユーザー指定の入力は

\[
|\chi\rangle=(|12\rangle+i|45\rangle)/\sqrt2,\quad
|\Psi\rangle=(u+iv)/\sqrt2.
\]

\[
U(\theta)|\Psi\rangle
=\frac1{\sqrt2}\left[(1-i\theta/3)u+iv+
\frac{\theta}{3}(x-y+z)\right]+O(\theta^2).
\tag{E4}
\]

従ってx,y,zへの最初の遷移振幅は順に
\(+\theta/(3\sqrt2),-\theta/(3\sqrt2),+\theta/(3\sqrt2)\)。
入力のiと発展の−iを両方保持した結果である。

## 3. pair coherenceと添字転置を区別する

補助密度演算子の非対角成分は

\[
\rho_{2;12,45}=-i/2,\qquad \rho_{2;45,12}=+i/2.
\]

\(\operatorname{Tr}_B(|\beta\rangle\langle\alpha|\rho_2)=\rho_{2;\alpha\beta}\)なので

\[
H_{\rm eff}=\Gamma_3(\rho_2)/3,
\qquad H_{\rm eff}|123\rangle=|123\rangle/6+i|345\rangle/6.
\tag{E5}
\]

Jの直接作用(E4)をpartial traceしても、\(P=|123\rangle\langle123|\)について

\[
\rho_T(\theta)=P+\frac{\theta}{6}
(|345\rangle\langle123|+|123\rangle\langle345|)+O(\theta^2)
=P-i\theta[H_{\rm eff},P]+O(\theta^2).
\tag{E6}
\]

E4のxとuは同じ補助12を持つため干渉し、y,zの補助は元入力にないためfirst orderでは寄与しない。
補助をclassical mixtureへdephaseすると(E6)のcross項は消える。
また\(\rho_2\)を転置してしまうと(E5)のiの符号が逆となり、(E6)も逆向きになる。
指定の複素coherenceは、この二つの誤りを実際に区別する。

## 4. CGから得る有限角度の独立照合

全up→全downのwordを軌道別up/downへ直す符号は

\[
\eta(x,\alpha)=(-1)^{\sum_{i<j}m_i n_j}.
\tag{E7}
\]

u,v,x,y,zでそれぞれ−,+,+,−,+。
uはlocal \(-|\mathrm d\,\mathrm d\,\uparrow\,0\,0\rangle\)、vは\(|\uparrow\uparrow\uparrow\downarrow\downarrow\rangle\)、
xは\(|\downarrow\downarrow\uparrow\uparrow\uparrow\rangle\)へ写る。\(\mathrm d\)はdouble。
CGの位相規約と4本のpathを[操作対応](cg_operation_mapping.md) §3で明示する。
その係数の積から、spin projector \(P_S\)について

| S | \(\langle v\vert P_S\vert v\rangle\) | \(\langle x\vert P_S\vert v\rangle\) |
|---|---|---|
| 1/2 | 1/2 | 1/6 |
| 3/2 | 2/5 | −4/15 |
| 5/2 | 1/10 | 1/10 |

を得る。これは数値対角化から取得した値ではなく、明示したCG path係数の手での積和。
従って

\[
\langle v|U|v\rangle=\tfrac12 f_{1/2}+\tfrac25 f_{3/2}+\tfrac1{10}f_{5/2},
\]
\[
F(\theta):=\langle x|U|v\rangle
=\tfrac16 f_{1/2}-\tfrac4{15}f_{3/2}+\tfrac1{10}f_{5/2}.
\tag{E8}
\]

\(F(0)=0\)、\(F'(0)=-i/3\)となり、Jを直接作用させた(E3)と一致する。
vの最初の3つのupを置換する対称性と(E7)から、y,zへの振幅は−F,+F。
指定入力からのx振幅は有限角度でも\(iF(\theta)/\sqrt2\)となり、(E4)の正のfirst-order符号を再現する。
CGで得た\(\langle v|J|v\rangle=0\)、\(\langle v|J^2|v\rangle=1/3\)も、(E3)の直交3項と整合する。

## 5. controlとscalar phase

Qを符号化・fermionic permutation・CGの合成、Dを上記3phaseとする。
\(U=Q^\dagger DQ\)をcontrolへ接続する正しい演算は

\[
W=(I_C\otimes Q^\dagger)
(|0\rangle\langle0|\otimes I+|1\rangle\langle1|\otimes D)
(I_C\otimes Q).
\tag{E9}
\]

0枝ではQをその逆で戻してI、1枝ではUとなる。
workとmultiplicityを全て戻すので、

\[
W(|+\rangle|\Psi\rangle)
=(|0\rangle|\Psi\rangle+|1\rangle U|\Psi\rangle)/\sqrt2.
\tag{E10}
\]

weightの異なるuとvを測定・dephaseしない。
coherent controlのoff-diagonalを確認するため

\[
\mathcal A(\theta)=\langle\Psi|U|\Psi\rangle
=\tfrac34 f_{1/2}+\tfrac15 f_{3/2}+\tfrac1{20}f_{5/2}
=1-i\theta/6+O(\theta^2).
\tag{E11}
\]

controlのreduced density operatorでは
\((\rho_C)_{10}=\mathcal A/2\)、\((\rho_C)_{01}=\mathcal A^*/2\)。
ここはuncontrolled target channelの一致だけでは判定できない。

特に\(J=K^2/12+K/4-I/2\)からscalar \(-I/2\)を落とすと

\[
J'=J+I/2,\quad U'=e^{-i\theta/2}U,
\quad\mathcal A'=e^{-i\theta/2}\mathcal A.
\tag{E12}
\]

したがってcontrol間の位相が変わる。落とした場合は1枝に\(e^{+i\theta/2}\)を掛け直す必要がある。
報告された3phaseをそのまま用いる構成は、このscalarを含むため修正を要しない。
CG basisの各ketに任意の固定位相を付けても、Qと同じQの逆を用いれば相殺する。

## 6. 元SOURCE §4のSWAP圧縮の再確認

\(S_3|123\rangle=(|12\rangle|3\rangle-|13\rangle|2\rangle+|23\rangle|1\rangle)/\sqrt3\)。
補助45とのSWAP後は、補助12,13,23の3つの直交枝に、それぞれ単一のpair／spectator ketが現れる。
各枝の\(\operatorname{im}S_3\)内への射影は対応する\(S_3|345\rangle,S_3|245\rangle,S_3|145\rangle\)だけであり、
正規化前枝の振幅\(1/\sqrt3\)と、その像との重なりの絶対値\(1/\sqrt3\)を掛ける。
従ってimage内norm squaredは\(3\cdot(1/3)^2=1/3\)、image外は2/3。
これは(CARとは別の)定義からの紙上確認で、SWAPをimage上のunitaryと扱えないという元SOURCEの説明を支持する。
CG構成の完成時に物理空間へ戻れることとは矛盾しない。

## 7. この小例での判定

block次元、存在spin／multiplicity、Jの3値、pair coherenceの符号、有限角度のCG作用、control及びscalarは**確認**。
小例だけで一般M,Nを保証するという主張はしない。一般恒等式の根拠は[CAR導出](independent_car_derivation.md) (C5)–(C13)。
有限精度gate列、実機noise、費用・絶対E0の取得はこの紙上検証の対象外であり、検証済みとしない。
