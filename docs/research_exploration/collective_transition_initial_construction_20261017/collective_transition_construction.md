# 係数から集団遷移チャネルへの構成

2026-10-18 JST（作業系列ID：20261017）。以下は限定的な紙上構成。実行した科学実装・symbolic checkerはない。**具体的な有限チャネルは得たが、独立した新生成原理Aは残していない。** 対角下降則と解析的dressingはB、固定dressingの境界障害はC、一般Hの係数生成はDとする。分類は正式採否ではない。

## 1. 規則D：対角係数で共同下降を選ぶ

`D(n)=c+Σ ε_p n_p+Σ_{p<q}v_pq n_p n_q` とする。disjointなsource pair `{i,j}` とdestination pair `{r,s}`、残りの占有bit zを用いる。vは対称に拡張し `v_pq=v_qp` (p≠q)、`v_pp=0` と約束する。source2個がoccupied、destination2個がemptyのとき、移送後−移送前のenergy差は

\[
\delta(z)=\epsilon_r+\epsilon_s-\epsilon_i-\epsilon_j+v_{rs}-v_{ij}
+\sum_{k\notin\{i,j,r,s\}}(v_{rk}+v_{sk}-v_{ik}-v_{jk})z_k.
\tag{C1}
\]

係数からこのaffine式を作り、`δ(z)<0` のpredicate Πを可逆評価する。`T=a_r†a_s†a_j a_i`、`J=TΠ`、`P_J=J†J` とすれば、ΠはTと可換、J²=0、P_Jはprojector。θ∈(0,π/2]として

\[
K_0=I+(\cos\theta-1)P_J,\quad K_1=-i\sin\theta J
\tag{C2}
\]

を生成する。出力は `C(ρ)=ΣK_bρK_b†`。ancilla |0〉、`exp[-iθ(J⊗|1〉〈0|+J†⊗|0〉〈1|)]`、trace/resetで実装する。predicateのworkは占有移送の前に制御unitaryへ適切に組み込み、残したままtraceしない。spectator zはこの移送で不変なので、predicateを後でuncomputeできる。

`C*(D)−D=sin²θ δ(z)P_J≼0`。単電子で上がるがpairで下がる辺も、係数だけから選べる。全pair候補の列挙はO(M⁴)規模、1 predicateはO(M)個の係数/bit寄与を扱う。これらは組合せ規模の記述であって、総gate費・収束率の数値評価ではない。有限bitの符号判定が不確かな場合はそのpredicateを採用せず誤差を管理する。

**既知還元**：多粒子proposalのenergy差受理と通常の振幅減衰である。全状態の対角人口に関して既知のzero-temperature下降更新で、coherenceの扱いは標準CPTP拡張。pairを加えただけを新原理としない。さらに高い電子数障壁やdark成分への収束は別問題。

## 2. 規則W：非可換項を係数依存で取り込む限定構成

[入力仕様](research_problem_and_access.md)のH*を使う。これはH_Dとhoppingが可換でない相互作用模型である。次の略記は入力一覧ではなく係数から計算する式である。

\[
d_A=U-\mu,\quad d_B=U+\mu,\quad
R_A=\sqrt{d_A^2+4t^2},\quad R_B=\sqrt{d_B^2+4t^2},
\]
\[
\beta_A=\tfrac12\operatorname{atan2}(2t,d_A),\quad
\beta_B=\tfrac12\operatorname{atan2}(2t,d_B).
\tag{C3}
\]

U>μ>0,t>0より角度branchは0<β_A,β_B<π/4に固定できる。未知の固有branchを入力していない。

`G13=a3†a1−a1†a3`、`Q10=n2(1−n4)`、`Q01=(1−n2)n4` と定義し、

\[
W=\exp[(-\beta_A Q_{10}+\beta_B Q_{01})G_{13}].
\tag{C4}
\]

G13はanti-Hermitian、Q10/Q01と可換でありWはunitary。occupationをcontrolとするfermionic rotationとして指定できる。これは制御angleを持つ回転で、全体を単純なGaussian変換と呼ばない。

CAR符号を含む作用は

\[
|a\rangle:=W|12\rangle=\cos\beta_A|12\rangle+\sin\beta_A|23\rangle,
\]
\[
|b\rangle:=W|34\rangle=\cos\beta_B|34\rangle-\sin\beta_B|14\rangle.
\tag{C5}
\]

H*のこの二つのinvariant blockを解析的に解くと

\[
E_a=c-\frac{U+\mu+R_A}{2},\quad
E_b=c-\frac{U+3\mu+R_B}{2},
\]
\[
\omega:=E_a-E_b=\mu+\frac{R_B-R_A}{2}>0.
\tag{C6}
\]

|a〉,|b〉は係数から生成できる固有stateである。**未知のstateを入力してよいという意味ではない**。生成費はWとして払う。導出は[紙上検証](noncommuting_paper_verification.md)に示す。

### 2.1 入力から操作列まで

```text
Input: explicit H* coefficients c,U,mu,t and angle theta; target N=2 sector
Check: U>mu>0, t>0, Hamiltonian has exactly the declared terms
Compute: dA,dB,RA,RB,betaA,betaB with certified finite-precision errors
Describe W by occupation-controlled rotation (C4)
Apply W†; finish/uncompute any work used for its controls
Initialize bath qubit |0>
Apply Vtheta for the ordinary double-excitation T=a3†a4†a2a1
Trace/reset bath
Apply W using the CURRENT occupations; uncompute its work
Output system state
```

これは擬似コードの数学的仕様であり、プログラム・回路を実行していない。W†の制御workに旧n2/n4を残したままTを適用するとuncomputeを誤るため、各W操作内で返却する。

同じ有限operation列が任意のinput superpositionに線形に作用する。bathへの情報流出はチャネルの一部であり、全系をunitaryに戻すQ1の要請ではない。

出力チャネルは

\[
\widetilde C=\mathcal W\circ C_T\circ\mathcal W^\dagger,
\quad L=WTW^\dagger=|b\rangle\langle a|,
\quad P_a=|a\rangle\langle a|,
\]
\[
\widetilde K_0=I+(\cos\theta-1)P_a,
\quad\widetilde K_1=-i\sin\theta L.
\tag{C7}
\]

### 2.2 何が構成でき、なぜ新原理としないか

- 非可換なtと相互作用Uを落とさず、係数→角度→制御回転→pair-resetの規則を作れた。
- full Hの時間発展・Bethe roots・全eigenbasis一覧を要求しない。ただし**条件付き2次元blockが既知の解析式で解ける構造**を使った。
- couplerを展開して未知の高body oracleとせず、W†と既存double excitationとWの積として実装する。通常gate・parity・角度合成・bath/reset費用は残る。
- 既知の小ブロック対角化からrank-one振幅減衰を作る構成そのものに還元される。一般Hへの新しい係数生成文法や計算量差はない。
- この模型ではground |b〉自体が `W|34〉` として既知の操作で直接準備できる。これを無視してcoolingの資源優位を主張しない。

したがって分類B。文献の同じgateを使うという理由でなく、係数前処理まで解析的block変換へ尽き、独立な生成/保証/費用差を得ていないためである。独立新候補として正式保持する判断は行わない。

### 2.3 通常gateへ落とす有限の生成手順（紙上仕様）

未知unitaryのcallとしてW/Vを残さない。4-modeのoccupation encodingではWは既知bit-patternの二つの対 (1100,0110)、(0011,1001) 上の実2次元回転であり、角度/符号はC4/C5で固定される。他のbasis ketは不変。通常のtwo-level rotationの可逆分解で作れる。

pair＋bathではbit順を (n1,n2,n3,n4,bath) とし、Vθが結ぶのは s=11000 と d=00111だけである。Gray path

```text
11000 → 01000 → 00000 → 00100 → 00110
```

の隣接bit-pattern交換を順に行うpermutation Pを作る。各交換は、他bitを指定patternに制御したXである。Pはsを00110へ移し、bath=1のdを変えない。次にsystem=0011をcontrolとしてbathへ Rx(2θ) を適用し、Pを逆順で戻す。すなわち `Vθ=P† controlled-Rx(2θ) P`。元の二つのket以外には恒等作用で、必要な−i sinθの符号を含めてC2のStinespring unitaryを得る。Wの二つのreal rotationも同じ既知pattern分解で記述できる。

これはgate列の生成規約の紙上記述であり、回路objectのbuild/compile/実行ではない。多重制御gateの通常gate分解・work返却・rotation合成に費用を払う。encodingのbit-parity/signはC5/V5に従う。全logical W/VとチャネルはNを保存するが、上の汎用qubit分解の各中間gateまでN保存とは主張しない。各hardware primitiveにも厳密な粒子数保存を要求する装置では、そのnative controlled excitation実現を別に指定する必要がある。

## 3. 境界相互作用を入れた拡張

core N=2と保存されたspectator占有を持つ拡張sectorで、density spectator zが保存される単一hopping edgeなら、対角係数からoccupation依存detuningを評価して条件付き角度を作れる。例えばspectator5の `κ n1 n5` は、n5=zのblockでC3のd_Aを `U−μ−κz`、d_Bを `U+μ+κz` に変える。符号/branchを係数から扱い、旧角度を無条件で再利用しない。これは条件付き小block解法の範囲である。

一般のspectator patternを個別列挙する実装には指数個のblockがあり得る。detuningがaffineな場合は可逆算術で評価する余地があるが、別のhoppingでspectatorが変わると同じblock分解は失われる。複数edgeの角度が相互依存する一般Hについて効率的Wを得たとはしない。

5番目のmodeへのhopping `τ(a5†a1+a1†a5)` を追加すると、旧Wでsourceの補空間couplingが残る。[紙上検証](noncommuting_paper_verification.md) §4で、固定チャネルの全状態単調性が破れることと、なお下降するinput-classの十分条件を示す。境界項を削除した計算を一般化としない。

## 4. 他の文法を保持しなかった理由

同じAのfilter変更は既知filtered-jumpに一致し、零の遷移を新生成しない。単にTをHamiltonianの時間発展で共役する操作も、その実装とsupportを明示しなければ未知のdressing oracleを移しただけになる。一般Rを打ち消すWを「Riccati/SW等で求める」と置く案は、係数から有限操作列を得た規則ではなく、追加の解法・conditioning・誤差証拠が必要である。今回はその大量ansatz探索を開始しない。

**得た規則はB、得た限定障害はC、一般のcoherence対応生成はD。A判定の新構成候補は0件。** 未証明/高リスクだからではなく、今回実際に作れた係数生成部分が既知の小block変換の範囲だったためである。
