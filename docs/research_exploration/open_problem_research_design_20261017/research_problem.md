# Q1：inhomogeneous pairing Hamiltonianの係数からcoherentな基底変換を生成できるか

2026-10-17 JST。**数学的研究課題の提案1件。正式採択・新アルゴリズム成立・資源優位の認定ではない。**
未解決とするのは以下の限定した入力・精度・費用契約であり、全世界での不存在を証明したという意味ではない。
既知Bethe状態準備と条件付きadiabatic構成があることを前提に、そのままでは満たされない契約を定義する。

## 1. 対象HamiltonianとD2

L個の対軌道、2L個のfermion modeを使い、
\(P_p^\dagger=a_{p\uparrow}^\dagger a_{p\downarrow}^\dagger\)、\(P_p=a_{p\downarrow}a_{p\uparrow}\)とする。

\[
H_{\rm orig}=cI+\sum_{p=1}^{L}\epsilon_p(n_{p\uparrow}+n_{p\downarrow})
-g\sum_{p,q=1}^{L}P_p^\dagger P_q+R
=:H_{\rm RG}+R.
\tag{Q1}
\]

p=qも含み、対一個につき現れる\(-g\)を落とさない。文献による1/2の規約をこの定義へ混入しない。
cは元の絶対energy origin、一体項はそのまま入力する。Rを黙って捨てない。

最初に狙う明示的なfamilyは、既知単位で

\[
\epsilon_p=(p-(L+1)/2)/L,\qquad g=\gamma/L,
\qquad 1/2\le\gamma\le2
\tag{Q2}
\]

というpicket-fence型。\(\gamma\)はb-bit rational、Lは偶数、pair数mは\(\Theta(L)\)、特にL/2を含む。
以下のbには、c、t、要求精度等の古典数値入力のbit長も含め、読み込み・arithmeticの費用を隠さない。
定数mだけを扱う算法では成功としない。
再帰とblocked orbitalへの対応のため、(Q2)の任意のactive subset I上でも同じuniformな仕様を要求する。
levelを一つ除いても元L、\(\epsilon_p\)、gは変えない。gを\(\gamma/(L-1)\)へ更新して別問題にしない。
このintervalは計算資源の制限でなく、証明対象とする非摂動的familyの定義である。

**化学との限界**：reduced BCS／RGは有限基底の電子pairing模型であり、一般のab initio Coulomb Hamiltonianと同一ではない。
RG状態をmolecular Hのvariational ansatzに用いる既知研究も、その同一性を与えない。[L06]
厳密な模型クラスならR=0。それ以外では新構成の対象はpairing fragmentであり、元Hの全計算が解けたとはしない。
Rが小さいと主張する場合も、そのoperator normと取得費の証拠が必要。
既知の\(\|R\|\le\delta_R\)があればenergy差は\(\delta_R\)以内、同じsectorでの発展差は\(|t|\delta_R\)以内だが、
この証拠や\(\delta_R\)を無料の入力にしない。許容誤差を超えるRは明示的にsimulateし、全費用へ戻す。
ここでのnormとE0の比較は同じ全\(\eta\)電子sector上であり、seniority-zero射影だけの残余normでは代用しない。

## 2. 入力・許可操作・出力

| 項目 | 契約 |
|---|---|
| 古典入力 | L、b-bitの\(\gamma,c\)、active subset／sector、時間t、要求誤差\(\varepsilon\)。係数(Q2)は既知式から生成 |
| 量子入力 | 任意の対象sectorの状態、外部reference、control、初期化work。eigenstateとは限らない |
| 許可操作 | 通常の有限qubit gate、可逆整数・有限精度arithmetic、既知pair／occupation符号化、明示的なphaseとuncompute |
| 出力 | 対象code上でcontrolled \(e^{-itH_{\rm RG}}\)をnorm誤差\(\varepsilon\)以内で生成し、workを戻す回路仕様 |
| 課金する処理 | 古典前処理、全angle／energy評価、必要精度、routing／符号化、coherent active-set処理、phase合成、uncompute |
| 無料入力にしないもの | rapidities、charge eigenvalues、全固有vector、gap、正しいbranch、ground label、全H又は新しい変換Wのoracle |

内部でrootを使うこと自体は禁止しない。ただし係数からuniformに生成する過程と費用を証明する。
任意angle又は大きいunitaryを単位費用oracleにせず、固定universal gateへの合成・要求精度も費用へ入れる。
指数個のroot setをあらかじめ列挙してQROMへ入れる経路は目標契約を満たさない。
block-encoding／qubitizationを中核にした構成へ移行しない。

## 3. 既知の到達点と不足

元の時間発展の**存在・一般実装可能性は未解決ではない**。項別PF等が既に使える。
Bethe ansatzはスペクトル・stateの表現を与え、ABCs／既知deterministic準備もある。[L01, L02, L03]
2026年のadiabatic構成はRGにも適用されるが、準備するstateに対応するcharge情報とparent gap等の条件が必要である。[L04]
これらの既知法を「全て指数時間しかない」とは扱わない。

今回の比較で閉じなかったのは、**係数だけから、全inputのcoherenceを保つ一つの変換とenergy評価を、
指数個のstate／branchを展開せず生成する**という点。
1 stateを準備する手順、各stateのchargeを与えた条件付き手順、任意入力の固有基底変換は異なる。
対照の到達点と量子・古典費用を[比較資料](prior_art_comparison.md)で区別する。
文献未発見だけで新規性を主張せず、次の生成補題の成立が新成果になる条件を置く。

## 4. 目標とする数学的命題

\(h_I\)を(Q1)のactive subset I上、scalarとblocked一体energyを除いたpair-space Hamiltonianとする。
各pair countを保つ**一つのunitary回路** \(W_I\)と、label zから値を可逆計算する対角operator \(D_I\)を、係数から生成する。

\[
\|h_I-W_ID_IW_I^\dagger\|\le\zeta,
\quad
G_W+C_{\rm pre}+G_{D\text{-eval}}+Q_{\rm work}
\le\operatorname{poly}(L,b,\log(1/\zeta)).
\tag{Q3}
\]

全ての量は数値実績でなく**成立を目指す命題**。多項式の次数・定数・bit精度も証明の一部であり、未提示。
最終的には\(\zeta\le\varepsilon/(2\max(1,|t|))\)を使い、phase合成誤差を残りへ入れる。
既知のDuhamel評価から

\[
\|e^{-ith_I}-W_Ie^{-itD_I}W_I^\dagger\|\le |t|\zeta.
\tag{Q4}
\]

従って成功すれば、費用を\(\operatorname{poly}(L,b,\log(\max(1,|t|)/\varepsilon))\)にする、
この限定familyのfast-forwarding構成に接続し得る。
変換→対角phase→逆変換という一般枠は既知であり、その再提示は成果ではない。[L10]
新しい仕事は、(Q3)を満たすWとDの**係数からの生成**そのもの。

近接／縮退したenergyでは、個々の固有vectorのラベルを高精度で追うことを必須にしない。
(Q3)のoperator残差を目的にするので、未知のmany-body gap又は正しい解析branchを入力にしない。
label順序は生成側が一貫して決めればよく、既知ground labelを要求しない。
pointwise state fidelityだけでは(Q3)を認定せず、全入力・referenceに対する作用を保証する。

## 5. 狙う構成補題：level追加を一つのcoherentな再帰へする

Iに最後のlevel \(\ell\)を加える。pair数mの空間は、
「既存Iにm pairs＋新level空」と「既存Iにm−1 pairs＋新levelに1 pair」の直和。
既存各sectorの固有基底で形式的に表すと、追加後Hamiltonianは

\[
\mathcal K_{I+\ell}^{(m)}=
\begin{pmatrix}
D_I^{(m)} & -g F_I^{(m)}\\
-g F_I^{(m)\dagger} & D_I^{(m-1)}+(2\epsilon_\ell-g)I
\end{pmatrix},
\tag{Q5}
\]
\[
(F_I^{(m)})_{ab}
=\langle E_{I,a}^{(m)}|\sum_{p\in I}P_p^\dagger|E_{I,b}^{(m-1)}\rangle.
\tag{Q6}
\]

これは新しいoracleの定義で解決したものではなく、**何を圧縮して生成すべきかを示す形式的な構成対象**。
既存のoverlap／form-factor行列式は要素を得る手掛かりだが、行列全体の安い量子作用を与えるとは限らない。[L09]
Fが単に低い通常rankを持つ、という仮定は置かない。

求める補題は、(Q5)を扱うlevel挿入unitary \(B_{I,\ell}\)と新energy評価を、
係数・compactな再帰labelの演算と\(\operatorname{poly}(L,b,\log(1/\zeta))\)個の基礎gateで生成するもの。
全列・全root setのQRを行わず、共通のorthogonality、coherent labelの返却、有限精度のoperator残差まで閉じる。
例えばCauchy／Gaudin関係を使うfactorizationが得られるかを調べるが、そのfactorizationは今回まだない。

重要なのは、全mを一つのuniform routineで扱い、

\[
W_{I+\ell}=(W_I\otimes I_\ell)B_{I,\ell},
\quad G_W(|I|+1)\le G_W(|I|)+\operatorname{poly}(L,b,\log(1/\zeta))
\tag{Q7}
\]

のような**共有された再帰の費用**を証明すること。
\(G_{n,m}=G_{n-1,m}+G_{n-1,m-1}+\cdots\)と独立branchを展開して二項係数個の処理へ戻ってはいけない。
parentのスペクトルやFを呼ぶ度に未知の\(W_I\)を無料にすることも不可。
誤差伝播が指数的にならないこと、angle／energy評価のbit長が多項式で済むことも補題の一部。

## 6. full電子sector、scalar、残余への接続

unpaired orbitalの集合Bとそのspinはpair相互作用で保存される。
active subsetはI=[L]\\B、pair数は\((\eta-|B|)/2\)、blocked一体energyは\(\sum_{p\in B}\epsilon_p\)。
全\(\eta\)電子sectorで用いるには、このBをcoherentに扱うuniformな(Q3)–(Q7)と符号化を証明する必要がある。
seniority-zeroのgroundが全sectorのgroundだと無料で仮定しない。
scalar \(c+\sum_{p\in B}\epsilon_p\)はcontrolled phaseに含める。

R=0であっても、simulation primitiveの成立からground-state準備・最低branchの選択が無料になるわけではない。
絶対E0推定へ接続する際は、state準備、実際のoverlap／成功条件、位相窓、測定費用を別に保持する。
一般分子でRが残る場合、外側の既知PF等との合成は新規性ではなく、全費用優位も別問題。
この課題を一般Coulomb問題の解決へ昇格させない。

## 7. 成功・失敗・未証明条件

| 判別 | 条件 |
|---|---|
| 新成果となる成功 | inhomogeneousでm=Θ(L)の(Q2)に対し、(Q3)の係数前処理とcoherentな生成補題、(Q7)の費用・誤差証明を得る |
| 数学的な負の成果 | 明示した再帰族の不可能性、又は必要なconditioning／gate数の下界を同じ入力モデルで示す。一般RG不可能性へ拡張しない |
| 目標未達 | fixed mだけ、uniform準位だけ、特定の1 stateだけ、指数個のangles／roots／大行列を必要とする |
| 独立構成として不保持 | 既存ABCsを各root setへ別々に適用するだけ、既知parent法のgap保証を仮定するだけ、既知CG＋新phaseと完全に同じ生成になる |
| oracle違反 | gap、charge表、正しいbranch、全振幅、W、exp(H)を無料入力にする |
| D2違反 | scalar・一体自己項−gm・blocked sector・R・元Hへの誤差を落とす |

主な未証明条件は、compactな挿入factorizationの存在、全branch同時の直交性、
gapに依存しないoperator誤差制御、再帰のconditionとbit長、coherent B対応の費用。
**今回はこれらの成立を示していない。** 高リスクだが、既知準備との正確な差と、証明・構成すべき対象を定義できたため研究課題案として1件残す。
最初に調べるL=4・2 pairsの手順と、棄却すべき救済は[最小検証案](minimal_paper_checks.md)。

[L01, L02, L03]: prior_art_comparison.md
[L04]: https://arxiv.org/html/2503.21741v3
[L06]: https://arxiv.org/html/2007.10705v1
[L09]: https://arxiv.org/html/2012.10477v1
[L10]: https://arxiv.org/html/2105.07304v2
