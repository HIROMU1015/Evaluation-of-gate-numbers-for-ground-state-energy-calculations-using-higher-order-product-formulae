# 係数から測定操作を生成する紙上規則

2026-10-18 JST。[P2](research_problem_and_gap.md)のFに対する具体的構成。**擬似コード・恒等式の紙上検討であり、科学用generator、symbolic checker、回路objectを作成・実行していない。**

## 1. 係数処理と生成式

P1規約の係数を読み、P2の各要素を符号付きで確認する。四つのdensity係数が(u,−u,−u,u)でない場合に近似してpatternへ合わせない。このfamily外の項があれば、そのまま別residualに残す。本packetが具体化するのは明示された四mode familyであり、一般Hの最適fragment探索器ではない。

spectator結果z=(z3,z4)∈{0,1}²に対しs=z3−z4∈{−1,0,1}。activeの

\[
Y=-i(a_1^\dagger a_2-a_2^\dagger a_1),\quad
a_s=d+us,\quad r_s=\sqrt{a_s^2+t^2}
\tag{G1}
\]

を使う。r_s>0ならcosθ_s=a_s/r_s、sinθ_s=t/r_s（θ_s=atan2(t,a_s)）とし、U_s=exp(−iθ_sY/2)。r_s=0ではθ_s=0と定義する。N12=1の基底|10〉,|01〉ではX12,Y,Zが通常のPauli X,Y,Zであり、N12=0,2では全て0。従ってFock空間全体で

\[
U_s r_s ZU_s^\dagger=a_sZ+tX_{12}.
\tag{G2}
\]

P_z=|z〉〈z|をspectator占有projectorとして

\[
F=\sum_zP_z(\nu s+U_s r_s ZU_s^\dagger),\qquad
U=\sum_zP_zU_s.
\tag{G3}
\]

というcoherent diagonalizerも定義できる。しかし目的がFの破壊的測定なら、Uの全制御branchを量子回路に保持する必要はない。

## 2. 有限の測定手順

```text
Input: P2 coefficients with fixed ordering/convention, state preparation A,
       number of independent shots and measurement/angle error specifications.
Precompute a_s, r_s and theta_s for s = -1, 0, +1 at requested precision.
For each F-shot:
    Prepare one fresh rho using A; charge its full preparation cost.
    Read occupations z3,z4 without measuring the active pair.
    Set s = z3-z4 and select the corresponding angle.
    Apply U_s dagger = exp(+i theta_s Y/2) on modes 1,2.
    Read active occupations x1,x2.
    Return (z3,z4,x1,x2) and score nu*s + r_s*(x1-x2).
Acquire R-shots from separate fresh copies using known hopping measurements.
Return c + mean(F-scores) + estimate(R), with separate uncertainties.
Do not claim an E0 certificate from this measurement alone.
```

occupation readoutはJordan–Wignerの直接bit読出しでよい。evenなactive回転はspectatorに作用せずCARのparityを壊さない。隣接pair1,2のGivens回転一つは、occupation0/2を保ちone-particle部分の二準位だけを回す有限gate列へ通常分解できる。これは回路build/compile済みという意味ではなく、native gate数・routing費を確定していない。量子ancilla、A†、controlled-A、追加copyのpostselectionは要求しない。feedforward待機・測定crosstalk・noiseの費用は無視せず、後の会計へ分離する。

## 3. record lawと公表手順への実際の代入

Q_x=|x1x2〉〈x1x2|として、この手順の一copy POVMは

\[
E_{z,x}=P_zU_sQ_xU_s^\dagger,
\quad p(z,x)=\operatorname{Tr}(\rho E_{z,x}).
\tag{G4}
\]

score y(z,x)=νs+r_s(x1−x2)の一・二次momentはTrρF、TrρF²。よってこれはFのspectral測定（縮退を細かく読んだもの）である。任意ρのspectator間coherenceがあってもG4は成立する。固定粒子数内のpopulationを結果後に切り捨てる操作ではない。

公表済み[L01 §III.2–3、式(25)–(35)](https://arxiv.org/html/2305.18251v2)へ、active集合S1={1,2}、symmetry集合S2={3,4}、外側軌道変換U_T=Iを代入する。条件付きone-body tensorは

\[
h(z)=\begin{pmatrix}d+u(z_3-z_4)&t\\t&-d-u(z_3-z_4)\end{pmatrix},
\quad h_0(z)=\nu(z_3-z_4).
\tag{G5}
\]

係数の定数部分は同論文の一般式(14)–(15)の定数多項式として残す。式(28)の線形だけの表示を理由にt,dを消さない。n_kと反射2n_k−1の多項式は同じclassである。

このh(z)の二準位回転がG1–G2である。論文のdiagonalizing unitaryの規約ではU_v=U_s†と対応させる。同論文Fig.1(b)のsymmetry readout→classically conditioned orbital rotation→occupation readoutが、上の擬似コードとG4を与える。従って**候補の核心を新たに移植する前から、公表Rと同じ係数→角度→測定lawが得られる**。record変換は(z,x)のidentity、角度・精度・順序も揃えれば全標本族・score・variance・任意の固定後処理分布が一致する。

## 4. 有限精度と構成の限界

連続角をexact gateとして無料にしない。|θtilde_s−θ_s|≤δθ、scoreのr誤差≤δr、|νtilde−ν|≤δνとすると、G2で測る有効演算子の差は

\[
\|\widetilde F-F\|\le r_{\max}\delta_\theta+
\delta_r+\delta_\nu
\tag{G6}
\]

で押さえられる（角度による二準位差は2r_s|sin(Δθ_s/2)|≤r_s|Δθ_s|）。|S|≤1、|Z|≤1を使った。ν入力をexactにscoreへ保持すればδν=0でよい。sqrt/atan2は有限bitの要求精度で計算し、三つのtableだけ保存する。tを含むrが小さいときの角度conditioningもprecision要求へ入れ、r=0の定義で除算を避ける。

これは装置noiseを含むcertificateではない。合成gate誤差・readout bias・feedforward中のdecoherenceは別途加える。同じ処理を公表手順側にも許すので、このprecision会計は候補固有の保証差ではない。

一般の多数spectatorに対し2^k branchをcoherentに安く実装できる、一般分子Hを一回で測れる、という拡張は得ていない。本構成の結果は、有限familyに対する操作成立と、その核心の公表既知法への具体的還元までである。
