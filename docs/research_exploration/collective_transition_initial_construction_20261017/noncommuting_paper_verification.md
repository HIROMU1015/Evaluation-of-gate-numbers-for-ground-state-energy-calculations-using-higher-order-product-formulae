# CAR・CPTP・非可換energy変化の紙上検証

2026-10-18 JST（作業系列ID：20261017）。すべて以下の式の紙上導出。数値行列、solver、科学用記号計算、回路compileによる検算は行っていない。一般的な冷却のNO-GOも、独立した数学的新規性も主張しない。

## 1. 指定pair-resetの確認

昇順ket `|ij〉=a_i†a_j†|vac〉` (i<j)、N=2とする。

\[
T=a_3^\dagger a_4^\dagger a_2a_1,
\quad T|12\rangle=|34\rangle,
\quad T^\dagger|34\rangle=|12\rangle.
\]

ほかの4 ketにはTもT†も零。`P=T†T=|12〉〈12|`、`TT†=|34〉〈34|`、T²=0。全Fock空間なら `P=n1 n2(1−n3)(1−n4)` であり、sectorを指定せずrank-oneと置かない。

`q=cosθ−1`、`s=sinθ` とし、K0=I+qP、K1=−isTとすると

\[
K_0^\dagger K_0+K_1^\dagger K_1
=I+(2q+q^2+s^2)P=I.
\tag{V1}
\]

ancilla0からの拡大unitaryは、`|12,0〉`と`|34,1〉`を結ぶ2次元回転である。残りは恒等作用なのでKraus表現を直接得る。Kraus和はCP、V1よりTP。`[N,T]=0` より粒子数sectorを保存する。bathはtrace/resetし、成功結果のpostselectionは要求しない。

H_Dのenergyは |12〉でc−U、|34〉でc−U−2μ、四つのmixed配置でc−μ。一電子移送はU−μ>0上がり、pair移送は2μ下がる。従って

\[
C_T^*(H_D)-H_D=-2\mu s^2P\preceq0.
\tag{V2}
\]

これは既知振幅減衰を使った障壁診断であり、新アルゴリズムではない。

## 2. Bare pairを非可換Hへ移したときの障害

任意Hermitian Vに対し

\[
C_T^*(V)-V=q\{P,V\}+q^2PVP+s^2T^\dagger VT.
\tag{V3}
\]

Vをone-body hopping和とすると `PVP=0`、`T†VT=〈34|V|34〉P=0`。H_D+λVでは

\[
\Delta_H=-2\mu s^2P+\lambda q\{P,V\}.
\tag{V4}
\]

χ=V|12〉≠0なら |12〉とχ/‖χ‖上の圧縮は

\[
\begin{pmatrix}-a&b\\b^*&0\end{pmatrix},
\quad a=2\mu s^2,\quad |b|=|\lambda q|\,\|\chi\|.
\]

b≠0なら固有値の一つ `(-a+√(a²+4|b|²))/2` が正。よって元Hへの**全入力一step単調性**は不成立。占有対角なinputでcoherence項が零になる場合はあるが、H-groundへ収束することにはならない。

## 3. H*を保持するdressingの検証

ここからは[構成C3–C7](collective_transition_construction.md)で新たに具体化した限定例を検証する。

### 3.1 CAR符号と係数からの角度

`G13=a3†a1−a1†a3` とすると

\[
G_{13}|12\rangle=-|23\rangle,\quad G_{13}|23\rangle=|12\rangle,
\]
\[
G_{13}|34\rangle=-|14\rangle,\quad G_{13}|14\rangle=|34\rangle.
\]

従ってH*のordered blocks (12,23)、(34,14)はそれぞれ

\[
\begin{pmatrix}c-U&-t\\-t&c-\mu\end{pmatrix},
\qquad
\begin{pmatrix}c-U-2\mu&t\\t&c-\mu\end{pmatrix}.
\tag{V5}
\]

数値対角化ではなく、回転後off-diagonalが零になる `tan(2β_A)=2t/(U−μ)`、`tan(2β_B)=2t/(U+μ)` を解く。同じsin符号を両blockに使うと誤る。C4の−β_A/+β_BがC5のa,bを与える。

13と24はhoppingがPauli-blocked/emptyで、energyはc−μ。V5の高い枝は `c−(U+μ−R_A)/2`、`c−(U+3μ−R_B)/2`。低い枝C6を含めてbがN=2の最小energyである：E_a>E_b、各高い枝は自身の低い枝より上、c−μ>E_b。**この小classではE0=E_bを解析的に知れる**。一般電子Hの未知E0を無料にしたのではなく、この例自体に量子優位を主張できない理由でもある。

### 3.2 CPTP・work・energy

Wはunitary、Nと可換、C7はC_Tのunitary conjugationなのでCP/TPとsector保存が従う。条件付き回転のworkは各W/W†内で返却し、bathだけをresetする。scalar cはTPから `C*(cI)=cI`。controlled fermionic gatesの相対位相はC4/C5/Tの定義で固定し、global phase同値で符号を捨てない。

`H*|a〉=E_a|a〉`、`H*|b〉=E_b|b〉` より

\[
\widetilde C^*(H_*)-H_*=-\omega s^2P_a\preceq0.
\tag{V6}
\]

これは全inputのH* energyに対する式で、非可換tを捨てていない。g=ground bのpopulationとsource aのpopulationは

\[
p_a(m)=\cos^{2m}\theta\,p_a(0),
\qquad
p_b(m)=p_b(0)+(1-\cos^{2m}\theta)p_a(0).
\tag{V7}
\]

他のpopulationは不変。dark成分が残るため一般初期stateからgroundへ収束しない。|12〉からなら `p_a(0)=cos²β_A`、`p_b(0)=0`、残るaの高い枝のpopulationはsin²β_A。この具体的なlow-energy人口移送は示せたが、一般準備の性能ではない。b自体はW|34〉として直接準備でき、既知強対照を無視できない。

## 4. 固定rank-one dampingの正確な境界

### 4.1 任意Hに対する必要十分条件

直交する既知state a,b、P=|a〉〈a|、Q=I−P、T=|b〉〈a|について同じチャネルを使う。`E_a=〈a|H|a〉`、`E_b=〈b|H|b〉` と定義するだけで

\[
\Delta_H=s^2(E_b-E_a)P+q(PHQ+QHP).
\tag{V8}
\]

を得る。V3で `PHP=E_aP`、`T†HT=E_bP`、`2q+q²=−s²` と整理すればよい。θ∈(0,π/2]とすると

\[
\Delta_H\preceq0
\quad\Longleftrightarrow\quad
QH|a\rangle=0\ \text{かつ}\ E_b\le E_a.
\tag{V9}
\]

右辺ならV8は負のP倍。逆はQH|a〉≠0の場合、そのnormalized方向とa上の圧縮が負のdeterminantを持つことから従う。残るP上の期待値がE_b≤E_aを要求する。

V9は**固定rank-one振幅減衰で全状態一step単調性を要求するclassだけ**の条件。target bがH固有stateである必要まではない。未知のsource固有vectorを構成する方法をV9自身は与えない。多数jumpの和、cycle、有限の加熱、限定input classにはこの必要条件を無条件に広げない。独立新定理のpriorityも認定しない。

### 4.2 境界hoppingを残す具体例

5 modes・N=2へ埋め込み、`H0=H*+ε5 n5`、旧a,bはn5=0とする。`R=τ(a5†a1+a1†a5)`、τ≠0を加える。これはnumber-preservingな境界hoppingである。

`〈a|R|a〉=〈b|R|b〉=0` だが

\[
Q R|a\rangle=-\tau\cos\beta_A|25\rangle\ne0.
\tag{V10}
\]

固定W/pair-resetではV8のP対角項は `−ωs²P_a` のまま、off-diagonalは残る。従って全状態単調性は任意の非零τで破れる。τが小さくても「厳密な全入力Loewner単調性」を救わないことと、近似/限定inputの有用性は別である。bにもRは一般に作用するため、旧targetを新しいgroundと置かない。

### 4.3 下降するinput classと誤差の明示

一般のH=H0+Rでa,bがH0固有state、`d=E_a^0−E_b^0>0` とする。`d_eff=d+R_aa−R_bb`、`r=‖QRP‖`、`p=Tr(Pρ)`。V8と正のρのCauchy–Schwarzから

\[
\operatorname{Tr}(\rho\Delta_H)
\le -s^2d_{\rm eff}p+2|q|r\sqrt{p(1-p)}.
\tag{V11}
\]

d_eff>0ならa0=s²d_eff、b0=|q|rとして

\[
p\ge\frac{4b_0^2}{a_0^2+4b_0^2}
\tag{V12}
\]

は一step非増加の十分条件。P対補空間のcoherenceが零なら交差項は消え、同じd_effで下降する。これらはinput classを明示した保証で、V10から全冷却不能とはしない。

rの合法な上界を係数normから得れば使えるが、tightなrやpの取得費を無料にしない。V12を満たすpの測定/信頼区間を実行時に使うなら、独立copiesと追加承認が必要。繰返し中にpは減るので、V12だけから全stepの収束率を作れない。

## 5. 有限精度・成立範囲

理想C7と実装チャネルのdiamond差をε_ch以下、`B_H≥‖H−cI‖` を係数からの上界とすれば、一回のenergy変化の差は `B_H ε_ch` 以下。実装した微小誤差が全状態単調性を自動保持するとはしない。近似W、predicate符号、parity、reset、gate中のdrift、sector leakageを別に予算化する。

ここで成立したのはH*の明示構成/V6/V7と、固定rank-one文法のV8–V12。非可換H一般の新しい生成則、効率的収束、分子の資源優位は示していない。
