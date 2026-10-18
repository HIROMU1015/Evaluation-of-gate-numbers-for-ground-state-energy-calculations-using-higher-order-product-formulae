# 係数・測定記録からbasisを生成する紙上規則

2026-10-18 JST。**一つの具体的な生成・更新手順を記述できた。ただし独立性・資源優位は未認定である。** 以下のG/Rは本文内の参照記号で、正式研究ID・採択済みアルゴリズム名ではない。擬似コードは実行していない。

## 1. 規則G：係数graphの有限predicateと共通記録によるsplit

### 1.1 係数だけで候補を生成する

正規順序化・重複整理されたfermion term listを入力とする。scalarを除いた各term μのorbital支持をI_μ、係数をb_μとする。

1. 各orbitalを頂点とし、異なるp,qについてw_pq=Σ_{μ:p,q∈I_μ}|b_μ|を作る。絶対値でgraphを作るが、energy測定から係数の符号・位相を削除しない。
2. wの降順、同率ならorbital番号順でKruskalの最大重みspanning forestを作る。各union直後の頂点集合を保存する。孤立頂点を残す。
3. 集合族Cを全singleton、全I_μ、上記のunion集合の重複除去とする。
4. 各C∈Cと整数0≤k<|C|に対しq_{C,k}(x)=1[Σ_{p∈C}x_p≤k]を候補とする。重複した真理値の全列挙はせず、同じ構文のみを重複除去する。構文を辞書順で固定する。

未知g、energy branch、全配置表は使わない。|C|=O(L+n)、Q=|D|≤n|C|=O(n(L+n))。一般電子二体listの粗い上界はO(n^5)候補で、主対象のL=O(n)でもO(n²)となり得る。全候補が安価という意味ではない。係数bit精度、graph整列、集合storageは別途払う。

### 1.2 basisを定義する

初期label f_0(x)=0。各stepで現treeの一leaf aとq∈Dを選び、そのcellだけをq=0/1へ分割する。fは決定treeとして表し、leaf数K≤K_max、split数≤K_max−1。空cellを実際には知れないため、有限shotでは人口の下側証拠を満たす候補だけを受理する。

\[
|\chi_a\rangle=\Pi_a|\psi\rangle,\qquad
\Pi_a=\sum_{x:f(x)=a}|x\rangle\langle x|,
\quad V_f=\operatorname{span}\{\chi_a\}.
\tag{G1}
\]

cell内の配置の相対位相と振幅比はseedのまま保たれる。線形結合はcell間の相対位相も持てる。seedのzero supportを新しく生成することはできない。

### 1.3 membershipを回路へ入れず取得できる共通記録

J=Σ_{l=1}^M j_lP_l、j_l∈R、Λ=Σ|j_l|、P_lはHermitian Pauliとする。Λ=0ならH=cIなので、E0=cを返すだけで測定を行わない。以下はΛ>0の経路である。P_lはoccupation encodingで

\[
P_l|y\rangle=\omega_l(y)|y\oplus d_l\rangle,
\qquad |\omega_l(y)|=1
\]

と作用する。d_lとphaseは係数写像から既知である。

各shotでlを|j_l|/Λで選ぶ。ancilla |+〉とseedを準備してcontrolled-P_lを作用させ、

\[
|\Omega_l\rangle=(|0\rangle|\psi\rangle+|1\rangle P_l|\psi\rangle)/\sqrt2
\tag{G2}
\]

を作る。ancillaはX/Yを等確率で測り、符号s=±1と全systemのZ bitstring xを記録する。この回路の**仕様**を記しただけで、build/compileしていない。Aを一回使い、controlled-A/A†は使わない。

記録r=(l,β,s,x)についてy=x⊕d_lとし、任意のfへ古典的に再labelする。βは測定軸、a,a′はleaf番号である。

\[
Z_{aa'}^{f}(r)=2\Lambda\,\mathrm{sgn}(j_l)s
\bigl(1_{\beta=X}+i1_{\beta=Y}\bigr)
1_{f(x)=a}1_{f(y)=a'}.
\tag{G3}
\]

\[
\mathbb E Z^f_{aa'}=\langle\psi|\Pi_a J\Pi_{a'}|\psi\rangle=:J^f_{aa'}.
\tag{G4}
\]

位相ωを後からもう一度掛けない。controlled-Pが位相を含んでいる。複素matrixを作った後、(Jhat+Jhat†)/2でHermitianにする。populationは別のm_S回のseed Z測定からphat_aを得てShat=diag(phat)とする。scalarはHhat=c Shat+Jhatとして一回だけ戻す。

同じ記録から全候補treeを再評価できる。新しいmembership反射・controlled predicateの測定は不要。ただし有限shotの情報量、各bitstringを保存する古典費、選択biasを消したわけではない。[導出と一様誤差](mathematical_and_cost_analysis.md)を必須条件にする。

この経路は最小回路との主張ではない。VQNHEのstar-qubit測定は追加ancillaを不要にできる強い対照である。G2を既知測定より優れたものとして扱わない。

### 1.4 更新操作を記録から決める

有限class Fを「Dを用い、最大K_max leafまで分割した全tree」と**測定前に**定義する。データを見て辞書を追加しない。全Fを列挙する必要はなく、統計保証のunion対象としてだけ用いる。

各候補f′と現fについて、同じ共通記録からJhat/Shatを集計し、小さな一般化固有値問題を解く。各候補の有効性と誤差幅u_fは数学文書のM4で定義する。人口の下側証拠が弱い場合やShatが正定値でない場合は未解像として候補を除外し、cell削除・ridge補正で救済しない。

\[
g_{\mathrm L}(f,f')=\widehat E_f-\widehat E_{f'}-u_f-u_{f'}.
\tag{G5}
\]

両方u≤ε_RRを満たし、g_L>0である候補だけを比較する。順位はg_L/C_add(f,f′)。C_addは候補のbit処理、K+1 solve、storage増分を**事前に固定した古典operation規約**で数えた正の費用である。同率ならpredicateとleafの固定順を使う。測定共通費m_H(C_A+C_cP)+m_S C_Aは全候補に共通して一回だけ計上する。未取得の追加shotをゼロ価格で仮定しない。

具体的な費用proxyとして、W_f(x)=Σ_{q∈path_f(x)}(2|C(q)|+1)をoccupation読取・加算・比較の操作数とし、C_addを、全H記録のW_f′(x)+W_f′(x⊕d_l)、全人口記録のW_f′(x)、solveのa_s(K+1)³、集計のa_a(m_H+m_S+(K+1)²)、storage増分のa_m((K+1)²−K²)の和と定義する。a_s,a_a,a_mは結果前の正の算術／storage重みで、実測fitしない。このproxyは実時間や最適費用の保証ではない。全候補をscreenした費用は既に支払った費用であり、stepの実費は候補の和として会計する。g_L/C_addの順位だけからscreening全体の節約を主張しない。

このpacketのGは記録を追加取得しない。候補なし、leaf上限、または統計証拠不足でSTOPする。停止はE0精度達成の証拠ではない。理想energyの単調性を満たす候補でも、有限shotでg_L>0を証明できなければ停止する。

```text
Input: canonical H, sector, seed preparation A, K_max,
       fixed m_H/m_S, epsilon_RR, alpha_H/alpha_S, cost convention
If Lambda = 0: return E0 = c without quantum measurements; STOP
Generate D from coefficient graph, term supports and occupation-count tests
Declare F = all D-trees with <= K_max leaves; freeze D and all conventions
Plan shared records R_H by G2 and R_S by computational-basis sampling
f <- constant tree
For at most K_max-1 updates:
    Form all one-leaf / one-predicate splits of f
    Relabel the SAME R_H/R_S for each candidate; compute Jhat, Shat
    Certify population and simultaneous Ritz error widths
    If current f is uncertified: return UNRESOLVED and STOP
    Reject uncertified candidates and nonpositive certified gains
    If no candidates: return f, energy interval, reason; STOP
    Select highest g_L / C_add; break ties by fixed structural order
    f <- chosen tree; keep old cells through their sum in the new span
Return f, basis specification, matrix-estimation record and limitations
```

これは入力からbasisと測定計画を出す規則であり、「良いlabelを選ぶ」という未定義oracleは残していない。K_max等の数値設定・量子標本・solveは今回作っていない。

### 1.5 量子状態としての出力を要求する場合

今回の直接出力はbasisの仕様・Ritz energyである。得た係数zから|φ〉∝F_z|ψ〉、F_z(x)=z_{f(x)}を**実際に準備**するには、fの可逆計算、zのtable参照、複素phaseとcontrolled rotation、workのuncompute、成功branchのpostselectionが必要になる。

最大係数C=\|z\|∞で正規化すると成功率はp_succ=z†Sz/C²。z†Sz=1としても1/C²が小さければ再準備回数が大きい。cell単体の準備成功率はp_a。energy推定だけでこれらのcoherent出力stateを既に得たとは言わない。

## 2. 既知法との対応を先に固定する

G1のspanはQSEでO_a=Π_aとしたもの、状態F_zψはdiagonal非unitary後処理である。G2–G4はPauliが結ぶ配置対のinterferenceを取得して古典関数を掛ける方式で、VQNHEの測定原理と同じ情報を対象とする。複素Fに対する双線形形式はpolarizationからも復元でき、one-hot Fの選択だけを新発見にしない。

shadow QSEは測定済み情報で小さな局所subspaceを評価しbasisをfilterする具体例を持つ。従って「再利用＋energy gainで選択」も新規核心とは言えない。Gに残る調査対象は、係数graphで作る有限dictionary、一様confidenceで更新を止める条件、古典費を含む具体的な選択規則の**組**が、強い既存方式と異なる有用なtradeoffを持つかだけである。[比較文書](prior_art_and_baselines.md)では、この差が未確立であると記録した。

## 3. 別案R：support外へのcoherent操作を加える

対角basisのsupport障害に対し、非零hoppingまたは二電子励起の各fermion term TからU_T=exp[(π/4)(T−T†)]とIを有限poolにし、span{U_Tψ}を候補とする案も限定検討した。1/4回転を最適とする主張はない。係数の支持から出す固定の操作poolである。

これはseedにない配置を生成し得るが、Gramは一般に非対角となる。〈ψ|U_i†P_lU_j|ψ〉と〈ψ|U_i†U_j|ψ〉には対ごとの干渉回路が必要で、Gの対角再label記録をそのまま再利用できない。K²要素、controlled操作、準備とconditioningを払う。

pool operatorを既知QSEに与える構成であり、Hamiltonian-wordのpool拡張はIQAE等と近接する。残差に従って組み合わせればDavidson系へ戻る。本packetでは別の取得・選択・費用改善を構成できなかったため、**Rは既知operator-pool QSEの組合せへの還元として記録し、独立候補として数えない。** Rを実装・追加探索しない。

## 4. この構成で得たもの／得ていないもの

得たものは、有限の係数→predicate写像、共通の位相測定記録→行列写像、適応的選択のconfidence条件、費用と停止点である。coherenceを単なる人口samplingへ置き換えていない。

得ていないものは、連結した非自明な電子familyでの小K近似保証、p_minの係数下界、VQNHE/shadow QSE/TPSCIとの独立な利得、絶対E0精度の合法な停止保証である。規則が具体化したことと、独立した新候補が成立したことを分ける。
