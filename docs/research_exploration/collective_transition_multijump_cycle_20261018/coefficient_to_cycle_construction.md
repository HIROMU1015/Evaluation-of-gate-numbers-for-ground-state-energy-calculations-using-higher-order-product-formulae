# 係数から複数jump／有限cycleを生成する限定構成

2026-10-18 JST。前回 `b7ec04fb84cd01eb846b9e3cc6d545bdf833e657` の[rank-one境界障害][E02]からの次段階。新規数値計算・科学用記号プログラム・回路実装は行っていない。本書は紙上で作った有限チャネルとaccessの仕様である。

**結果：3-jump cycleは具体化できた。元Hのenergy下降と既知cutoff以下の人口増加も条件付きで示せた。ただし写像は部分空間の弱測定＋条件付きresetへ厳密に還元される。独立新構成候補としては保持しない。** 一般Hへの生成則は未構成。正式研究状態は変更しない。

## 1. 何を変えるか

固定source ket aからbへのrank-one dampingでは、全状態一step単調性にaの固有state性が必要だった。今回はaを固有stateへ補正せず、Hamiltonianのhoppingで結ばれた**source部分空間P全体**を同じ率で移送する。個々のoccupation sourceはH固有stateでなくてよい。

同じjumpを小さいangleで繰り返す案も調べたが、同じrank-one dampingへ再結合されるため障害は残る。[導出 §1](cycle_paper_derivations.md)。複数jumpを単に増やすのではなく、sourceの被覆と共通減衰率が最終チャネルを決める。

## 2. 元の非可換Hと合法な係数条件

5 fermion modes、固定N=2の10次元空間を正本とする。CAR、ketはcreation演算子の昇順積。入力Hamiltonianを

\[
\begin{aligned}
H_5={}&cI-U(n_1n_2+n_3n_4)-\mu(n_3+n_4)+\epsilon_5 n_5\\
&+t(a_3^\dagger a_1+a_1^\dagger a_3)
+\tau(a_5^\dagger a_1+a_1^\dagger a_5)
\end{aligned}
\tag{C1}
\]

とする。`U>μ>0`、`ε5≥0`、`t>0`、実τ≠0、

\[
r=t+|\tau|,\qquad\delta=2\mu-r>0.
\tag{C2}
\]

δは係数から得る比較marginであり、未知のexcitation gapではない。条件外を不可能と判定せず「この十分証拠では未認証」とする。一般Coulomb Hamiltonianではなく、密度相互作用と二つの非可換hoppingを持つ制限電子模型である。τは前回加熱を生んだ境界hoppingそのもので、捨てない。

sourceを

\[
P=|12\rangle\langle12|+|23\rangle\langle23|+|25\rangle\langle25|
=n_2(1-n_4)|_{N=2},\quad Q=I-P
\tag{C3}
\]

とする。c,U,μ,ε5,t,τとsectorからPを指定できる。全固有state・energy一覧を使わない。H5はn2,n4を保存するので `[H5,P]=0`。sourceのhopping closureは12→23,25で止まる。

targetは既知occupation `|b〉=|34〉`、その期待energyは

\[
E_b=\langle b|H_5|b\rangle=c-U-2\mu.
\tag{C4}
\]

bは一般にH5固有stateではない。既知試行stateとその対角係数を未知groundに読み替えない。[導出 §3](cycle_paper_derivations.md)で

\[
PH_5P-E_bP\succeq\delta P
\tag{C5}
\]

を対角係数とhopping normから示す。source blockの対角化は不要。

## 3. 係数からの生成手順

```text
Read the normal-ordered coefficient list and declared N=2 sector
Check the C1 term pattern and Hermiticity; keep c, epsilon5, t, tau
Check U>mu>0, epsilon5>=0, t>0, tau!=0 and delta=2mu-t-|tau|>0
Verify termwise that n2 and n4 are conserved
Set source flag P=n2*(1-n4), target b=|34>
Generate occupation sources |12>, |23>, |25> from the allowed hopping support
Emit L1,L2,L3 below with CAR phases fixed
Choose a common 0<theta<=pi/2; no angle optimization or spectral input
For j=1,2,3: initialize bath |0>, apply Vj(theta), trace/reset bath
Return system; return each gate-control work before the next subcycle
```

この擬似コードを実行していない。有限bit入力では符号/strict marginを認証できない場合に採用せず、数値truthで条件を救済しない。係数/支持patternの読取りは入力長に応じて払う。ここでsource ketを列挙したのは3個のoccupation labelであり、全固有basis列挙ではない。一般Mでclosureが指数に拡大する場合に多項式費用とは呼ばない。

## 4. 3つのjumpと有限操作列

N=2 sectorで

\[
\begin{aligned}
L_1&=a_3^\dagger a_4^\dagger a_2a_1=|34\rangle\langle12|,\\
L_2&=-a_4^\dagger a_2 n_3=|34\rangle\langle23|,\\
L_3&=a_3^\dagger a_4^\dagger a_5a_2=|34\rangle\langle25|.
\end{aligned}
\tag{C6}
\]

L2のminusは `a4†a2|23〉=−|34〉` のCAR符号を補う。`P_j=L_j†L_j` は相互直交、`ΣP_j=P`、`L_jL_i=0`。全Fock空間でrank-one等式を主張しない。

共通angleで `z=cosθ`、`s=sinθ` とし、各subcycleを

\[
V_j=\exp[-i\theta(L_j\otimes|1\rangle\langle0|+
L_j^\dagger\otimes|0\rangle\langle1|)],
\]
\[
M_{j0}=I+(z-1)P_j,\quad M_{j1}=-isL_j,
\quad\mathcal C_j(\rho)=\sum_{v=0,1}M_{jv}\rho M_{jv}^\dagger
\tag{C7}
\]

で指定する。bathは各subcycleの前に0、後にtrace/reset。no postselection。cycleは

\[
\Phi=\mathcal C_3\circ\mathcal C_2\circ\mathcal C_1.
\tag{C8}
\]

個々のsubcycleは元H5を加熱し得る。証明するのはこの有限cycleの進捗である。

### 4.1 実装へ接続する生成規約

各Vjは既知occupation `x_j⊗0` と `b⊗1` の二つのbit-patternだけを結ぶrotation。他basis ketは不変。前回[通常gate生成の規約][E03]と同じく、二つの既知patternを隣接patternへ写すGray-path permutation、指定bitのcontrolled Rx(2θ)、逆permutationで記述できる。source/destinationと−iの位相をC6/C7で固定する。未知unitaryのcallを残していない。

single bath qubitを再利用できるが、制御work・parity処理・rotation合成・reset費用は消えない。source labelをcopyしたworkは各unitary内で返却し、誤ってtraceしてcoherenceを余計に失わせない。全logical subcycle/cycleはNを保存する。1,3,5を↑、2,4を↓とすればN↑/N↓も保存し、S²保存までは主張しない。

汎用qubit分解の各中間gateまで粒子数保存とはしない。厳密保存を各native primitiveに要求するhardwareでは別のnative実現を指定する必要がある。今回は回路objectのbuild/compileをせず、費用の数値評価もしない。

### 4.2 全Hを保持する意味

C1をenergy評価と係数条件から削除していない。一方、実施モデルは通常の制御gate列であり、自然なsystem–bath Hamiltonian `H5+Hbath+Hcoupler` が常時作用して自動的にC7を実現するという主張ではない。gate中のdriftと補償を無費用にしない。logical channelからの実装誤差を別予算にする。全H時間発展oracleは生成規則の入力ではない。

## 5. 出力チャネルと進捗

exactに

\[
K_0=Q+zP,\qquad K_j=-isL_j\ (j=1,2,3),
\]
\[
\Phi(\rho)=Q\rho Q+z(P\rho Q+Q\rho P)+z^2P\rho P
+(1-z^2)\operatorname{Tr}(P\rho)|b\rangle\langle b|.
\tag{C9}
\]

となる。[紙上導出](cycle_paper_derivations.md)でCP/TP、合成順序、coherenceを確認する。全状態で

\[
\Phi^*(H_5)-H_5=-(1-z^2)(PH_5P-E_bP)
\preceq-(1-z^2)\delta P.
\tag{C10}
\]

source人口はm cycle後 `z^(2m) Tr(Pρ0)`。低energy spectral weightについても、係数から決めるcutoffと正の増加下界が得られる。groundを入力した結果ではない。ただしQ内を冷却しないため一般のground準備・任意精度E0推定は完成していない。

## 6. 既知構成への厳密な対応

C9は次の既知instrumentそのものである。

1. Pのweak two-outcome measurementを `Q+zP` と `sP` で行う。
2. second outcomeのときだけsourceの情報を消し、既知bへresetする。
3. outcomeを忘れる。

second outcomeのdiscard/reprepareをKraus `|b〉〈x_j|` で表せばC9がそのまま出る。θ=π/2ならPのprojective flag measurement＋conditional replacementになる。通常の部分空間振幅減衰、測定後resetの有限実装であり、単に別gateへ分解できるという弱い意味の還元ではない。input/作用/coherence/出力まで一致する。

source closureと係数norm証拠は今回の具体化だが、この模型ではPはn2 flag、bは既知product、証拠はtriangle boundで足りる。独立な新しい遷移選択・証拠取得・計算量改善は示していない。このため**構成はB：既知法への還元**。同じ式の全prior publicationを網羅した、あるいは別のP選択則が新しくなり得ない、とは主張しない。

## 7. 拡張の停止点

Pを保存しないdown-hoppingを加えると全状態cycle単調性は再び破れ、source closureはtargetも含む。[導出 §5](cycle_paper_derivations.md)。block-diagonalな初期stateとlogical operation列に限ったenergy下降は残るが、Hamiltonianが作るP/Q coherenceまで制御する新規則ではない。

既知spectral filter/system–bathを追加すると言うだけで解決したことにしない。一般係数から有用なP・target・cycleを生成する方法、flag-breaking項に対するcoherence対応、取得費・混合・総E0優位は未解決。追加探索を自動開始しない。

[E02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b7ec04fb84cd01eb846b9e3cc6d545bdf833e657/docs/research_exploration/collective_transition_initial_construction_20261017/noncommuting_paper_verification.md
[E03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b7ec04fb84cd01eb846b9e3cc6d545bdf833e657/docs/research_exploration/collective_transition_initial_construction_20261017/collective_transition_construction.md
