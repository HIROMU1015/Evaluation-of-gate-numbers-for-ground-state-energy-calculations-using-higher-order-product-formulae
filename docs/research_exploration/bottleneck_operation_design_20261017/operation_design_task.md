# 検討課題A：反対称空間を保つ二電子係数補助状態との衝突

2026-10-17 JST。**1件の操作仕様を具体化したが、既知Paldus／CG＋phaseへの明示還元が得られたため、最終保持は0件。**
既知HMEの機能と、そのjoint generatorの構成を分けて調べた記録である。
紙上の短い代数確認を含むが、新しい科学実行契約・候補の正式採択・実装承認ではない。
§§1–5で不足操作の候補を定義し、§6で既知の操作から目的作用を生成する規則を示す。

## 1. 解決対象となる障害

普通のdensity matrix exponentiation（DME）は、対象と同じ空間の密度行列を補助入力とし、partial SWAPを使う。[L02]
一方、電子の二体積分は二電子空間の係数であり、N電子空間の密度行列ではない。
「二電子係数を符号化した状態のcopiesから、N電子の相互作用を生成する」には、二電子作用を多電子へ持ち上げる操作が必要となる。
対象N電子のground-state copiesやRDMを係数状態の代わりに使うことはしない。

有限の直交spin-orbital基底の大きさをM、対象粒子数をNとし、\(2\leq N\leq M\)を考える。
\(\mathcal F_N=\wedge^N\mathbb C^M\)、\(\mathcal P_2=\wedge^2\mathbb C^M\)と置く。
pair label \(\alpha=(p,q),p<q\)、\(A_\alpha=a_q a_p\)で

\[
H_{\rm orig}=cI+d\Gamma(h)+\Gamma_N(V)+R,\qquad
\Gamma_N(X)=\sum_{\alpha\beta}X_{\alpha\beta}A_\alpha^\dagger A_\beta .
\tag{1}
\]

ここではantisymmetric pair basis内の行列Vを使い、反対称化積分に対する1/4規約と混ぜない。
\(c\)は核反発等を含む元の絶対energy origin、一体項も保持する。
この設計課題の初期クラスは\(V\succeq0\)のnumber-conservingな二体kernel。
通常の有限基底Coulomb反発はこのクラスに含まれるが、任意の有効Hamiltonianの二体部分までPSDとは仮定しない。
full Coulomb kernelを使う場合R=0にできる。truncation、signed分解、downfolding等を導入するならRと元Hへの誤差・費用を別に戻す。
今回は分子積分の作成・分解・切捨て・PSD判定を実行していない。

\(Z=\operatorname{Tr}_{\mathcal P_2}V>0\)、\(\rho_2=V/Z\)、\(C_N=\binom N2\)とする。
\(\rho_2\)は**既知係数から準備する二電子の補助状態**であり、未知の電子groundやその2-RDMではない。
V=0の場合は相互作用がない別の自明な境界例である。

## 2. 新操作の候補として調べた機能仕様

求めるのは、係数Vに依存しないunitary family

\[
U_{N,M}(\theta)=e^{-i\theta J_N}\quad\text{on }\mathcal F_N\otimes\mathcal P_2
\tag{2}
\]

を、全Hの発展oracleなしで生成する規則。
そのgeneratorを明示して

\[
J_N=\frac1{C_N}\sum_{\alpha\beta}
A_\alpha^\dagger A_\beta\otimes|\beta\rangle\langle\alpha|
\tag{3}
\]

と固定する。係数に依存しないのはJとその回路生成であり、\(\rho_2\)の準備はVに依存する。
\(e^{-i\theta J_N}\)を呼べることを新たな無料primitiveとはしない。検討開始時には、**まさにその生成を不足操作の候補**とした。
式(3)をHamiltonian simulatorへ渡すだけでは具体化にならない。§6の還元は、その呼出しを仮定せずに記述する。

\(\sigma\in D(\mathcal F_N)\)について、一回の衝突と補助状態のdiscardは

\[
\mathcal E_{\theta,\rho_2}(\sigma)=
\operatorname{Tr}_{B}\{U_{N,M}(\theta)(\sigma\otimes\rho_2)U_{N,M}(\theta)^\dagger\},
\]
\[
\left.\partial_\theta\mathcal E_{\theta,\rho_2}(\sigma)\right|_{\theta=0}
=-i[\Gamma_N(\rho_2)/C_N,\sigma]
\tag{4}
\]

を満たす。これは(3)からの短いpartial-trace確認であり、HMEの一般的なfirst-order構成の特殊化である。[L03]
HMEそのもの、first-order平均場の恒等式、copiesを用いることを新原理と数えない。
有限角度の\(\mathcal E\)は一般にunitary channelではなく、\(e^{-i\theta\Gamma_N(\rho_2)/C_N}\)に厳密一致するとは要求しない。

**coherent controlも仕様に含む。** 制御bitと任意の外部referenceを保ち、
\(|0\rangle\langle0|\otimes I+|1\rangle\langle1|\otimes U_{N,M}(\theta)\)を構成する。
補助work registerは返し、coherentなweight/block labelを測定して消さない。
\(J_N\mapsto J_N+\lambda I\)のようなscalar変更は、uncontrolled channelで見えなくてもcontrol位相を変えるため台帳に残す。

## 3. 入力・出力・primitive・追加access

| 項目 | 仕様 |
|---|---|
| 古典入力 | M、N、pair／fermion符号の規約、角度\(\theta\)、合成精度。補助状態準備用の全V係数とZは別入力 |
| 量子入力 | 任意の\(\mathcal F_N\)状態、係数を符号化した\(\rho_2\)一copy、必要なcontrol/reference、初期化work |
| 出力 | 同じtarget粒子数Nと二電子補助空間上の(2)。targetと補助のentanglementは許す。補助は後で消費される |
| 使う基礎操作 | 占有bitとpair labelの可逆演算、符号付きmode permutation、制御回転・phase、uncompute。基礎gateの使用だけを新規性としない |
| 構成対象として調べた部分 | 全占有weightから決まる小blockを、電子係数なしで混合するrecoupling規則。§6では既知CG／Paldusを用いた生成へ還元 |
| 追加access | \(\rho_2\)の反復準備。混合状態のpurification／classical ensembleを使うなら、それらの準備・reset・誤差・coherent controlの費用を明示 |
| 無料にしないもの | Vのスペクトル、一般の\(\rho_2\)準備、全H/Jのexp、未知ground・gap・位相、全N電子振幅、postselection成功確率 |

二電子空間の次元は\(\binom M2\)なので、その係数からの一般的な状態準備は有限の古典処理で記述できる。
しかし安価さは未確立であり、classicalな固有分解・purification合成を行う場合も取得費へ戻す。
Slater determinantを準備する既知Gaussian/Givens回路が、一般の相関した\(\rho_2\)を無料で準備するわけではない。[C02]
今回、その準備solver・回路を実行していない。

## 4. なぜ抽出してSWAPするだけでは足りないか

二電子をcoherentに抽出する数学的isometryを

\[
S_N|\psi\rangle=\frac1{\sqrt{C_N}}\sum_\alpha|\alpha\rangle_P\otimes A_\alpha|\psi\rangle_T
\tag{5}
\]

と置く。\(S_N^\dagger S_N=I\)であり、\(\Gamma_N(X)/C_N=S_N^\dagger(X\otimes I)S_N\)。
さらに

\[
J_N=(S_N^\dagger\otimes I_B)
(\mathrm{SWAP}_{P,B}\otimes I_T)(S_N\otimes I_B)
\tag{6}
\]

だからHermitianで\(\|J_N\|\le1\)である。
ただし(6)の圧縮を、**そのままunitaryなSWAPとして実行できる**とは結論できない。
\(\Pi=S_NS_N^\dagger\otimes I_B\)のimageは一般のSWAPで不変ではない。
\(S_N^\dagger\)をimage外で自由に逆操作として使ってはいけない。

最小の分かりやすい比較として、M=5、N=3の形式的占有状態を考える。
\(|123\rangle=a_1^\dagger a_2^\dagger a_3^\dagger|\mathrm{vac}\rangle\)とし、補助pairを\(|45\rangle\)とすると

\[
S_3|123\rangle=(|12\rangle|3\rangle-|13\rangle|2\rangle+|23\rangle|1\rangle)/\sqrt3.
\]

抽出pairと補助のSWAP後には、例えば補助\(|12\rangle_B\)成分に\(|45\rangle_P|3\rangle_T\)だけが現れる。
しかしimage内の対応する成分は\(S_3|345\rangle\)であり、他のpair選択成分も必要になる。
各補助labelでのimageへの重なりをこの三項から手で読むと、全体のimage内確率は1/3、image外は2/3となる。
これは**普通の一回SWAPを圧縮のまま閉じる案の失敗**であって、科学simulationや一般no-goではない。

(6)からblock-encodingを作り、QSVT／qubitizationでexpを生成する経路は今回D1の中心方向に採用しない。
射影・Zeno・generic Hamiltonian simulationへ戻る場合は、その既知経路と必要accessを明記し、新操作の解決とは数えない。
N=2では\(C_N=1\)、\(S_N\)にspectatorがなく\(J_2=\mathrm{SWAP}\)。これは重要な既知positive controlであり、新規性の根拠ではない。

## 5. 占有数から小blockを特定する

式(3)は、targetの占有数と補助pairの占有数の和

\[
w_i=n_i+m_i\in\{0,1,2\}
\tag{7}
\]

を保存する。したがって、係数Vに依存せず、全weight wをcoherentに計算してblockをlabelできる。
\(r=\#\{i:w_i=2\}\in\{0,1,2\}\)とすると、double-occupiedな軌道はtarget／補助の両方に入る。
single-occupied軌道数は\(s=N+2-2r\)、そこから補助へ入る数は\(k=2-r\)。
固定w内の状態数は

\[
d_{N,r}=\binom{N+2-2r}{2-r}\le\binom{N+2}{2}.
\tag{8}
\]

これは(7)の組合せの数え上げであり、科学的な固有値計算ではない。
元の係数Hamiltonianの配置graphをclusteringするP2と異なり、ここでのblockは**係数非依存の補助衝突**に対する運動学的なもの。
ただし小blockを扱うという骨格自体は既知なので、その一般論を新原理と数えない。

検討時には、生成規則の不足を以下の段階へ分けた。

1. \(|x;\alpha\rangle\)からw、r、昇順single軌道list、補助subsetのcanonical rankを可逆に計算する。
2. 実軌道labelをcanonical labelへ移す際のfermion符号を追跡する。wは記録したままcoherentに保持する。
3. canonical blockの作用\(B_{N,r}\)について、係数に依存しない混合規則\(R_{N,r}\)とphaseを生成し、
   \(R_{N,r}B_{N,r}R_{N,r}^\dagger\)を扱う明示した再帰・回転列を作る。
4. phaseを適用し、混合、符号frame、rank／label計算を全て戻す。workを返し、controlの相対位相を保つ。

「small blockだから対角化可能」「\(R\)が存在する」と書くだけでは完成にしない。
この段階3を既知Schur／Clebsch–Gordan（CG）／Paldusと具体的に比べると、次の還元が得られる。[L04–L06]

## 6. 紙上の明示還元：二種類のフェルミオンと全spin

targetを仮想的なup species、補助pairをdown speciesとして、同じM軌道の二種類のフェルミオンへ符号化する。
元のtensor-product basisの順序を「全up creation、次に全down creation」と固定する。
\(a_p,b_p\)はこの二種類のCAR演算子とし、up数N、down数2の部分空間を使う。
これは電子の物理spinを新たに仮定することではなく、target／補助のtensor積に対する既知の符号化である。

\[
K_1=\sum_{pq}a_p^\dagger a_q b_q^\dagger b_p,\qquad
S_+=\sum_p a_p^\dagger b_p,\qquad S_-=S_+^\dagger,
\quad m=S_z=(N-2)/2.
\]

CARで一回縮約する関係と、二回縮約する関係は、このfixed-population空間で

\[
S_+S_-=N I-K_1,\qquad
K_1^2=2NI-NK_1+4C_NJ_N.
\tag{9}
\]

二つ目の式では、両speciesで縮約する項が\(2NI\)、片方だけの縮約が\(-NK_1\)、
両方で縮約しない項が二対交換の\(4C_NJ_N\)になる。
補助は二電子なので、そこでの\(b_i^\dagger b_j^\dagger b_l b_k\)はpairのmatrix unitに一致する。
従って

\[
J_N=\frac{K_1^2+NK_1-2NI}{4C_N},\qquad
K_1=N I-\{S^2-m(m-1)I\}.
\tag{10}
\]

**不足操作の候補(3)が、全spinの既知演算子の多項式になった。**
この二speciesのup/down数では、可能なtotal spinは\(S=m,m+1,m+2\)のうち、軌道数・占有で許されるもの。
それぞれの\(K_1\)は\(2,2-N,-2N\)であり、(10)の\(J_N\)の固有値は

\[
\lambda_{m}=1/C_N,\qquad
\lambda_{m+1}=-2/N,\qquad
\lambda_{m+2}=1.
\tag{11}
\]

存在しないspin sectorへphaseを要求しない。N=2では固有値は\(+1,-1,+1\)となり、pair-register SWAPの対称／反対称sectorと整合する。
(9)–(11)は今回、既知CAR／spin代数を手で整理した対応式であり、文献に同じ式が明記されていると帰属しない。
計算機でのCAR展開、matrix生成、対角化、solverは行っていない。独立査読済みの新定理とも認定しない。

**既知操作による入力→出力の生成規則**は以下まで書ける。

1. 補助pair labelを二つのoccupied down-modeへ可逆に符号化する。targetはN個のup-mode。
2. 使用するPaldus回路のmode順序へ、符号を追跡して並べ替える。例えばup全部→down全部から軌道別up/downへ移す場合、
   その符号は\((-1)^{\sum_{i<j}m_i n_j}\)。これは可逆parity演算又は既知fermionic permutationで扱い、省略しない。
3. 既知Paldus変換、又はsingle-occupied軌道のspin-1/2を結合する既知CG列でtotal spin Sをcoherentにlabelする。
   empty／double-occupied軌道はspin 0である。multiplicity・占有情報も保持する。[L04, L05]
4. Sに従って\(e^{-i\theta\lambda_S}\)を掛ける。Nが既知なので(11)のphaseに未知の固有値・gap・groundを必要としない。
5. 変換、mode順序、pair labelの符号化を全て戻す。制御版ではstep 4をcontrolledにし、scalar phaseを含めて扱う。

変換全体をQと書けば、出力は\(Q^\dagger\operatorname{diag}(e^{-i\theta\lambda_S})Q\)であり、(10)から(2)に対応する。
有限精度gate合成、初期化work、符号化変換、\(\rho_2\)準備の費用は残るが、それらを未知の新操作として追加する必要はない。
本作業で回路をbuild／compileしたとは扱わない。

この還元は、既知法の名前が関連するというだけの判断ではない。
target／補助の符号化、generator、total-spin label、phase、逆写像を対応させたものである。
**Aは新しい操作原理の設計課題として保持しない。**
「既知gateをまだ実装していない」「特殊化した回路をもっと安くしたい」という理由で新原理の課題へ戻さない。

## 7. 既知法との対応と独立性の限界

| 既知部分 | この課題との正確な関係 |
|---|---|
| DME／controlled partial SWAP | N=2の(2)–(4)に対応。N>2の反対称なpair抽出imageを普通のSWAPで保つ条件までは与えない |
| HME | \(\mathcal N(X)=\Gamma_N(X)/C_N\)に対するChoi partial transposeのjoint generatorが(3)。**機能・first-order規則は既知HMEへ還元**される |
| DFと密度平方gate | 係数から平方fragmentを作り各fragmentを生成する既知構成。\(J_N\)を一括生成する同じ操作とは限らないが、元Hの強い実装baselineである |
| 一般の交換子合成 | (3)を項ごと又はcommutatorの積で近似する存在は、新しい係数非依存recoupling規則の発見と区別する |
| Schur／CG／Paldus、1Q–2Q変換 | 上の(9)–(11)により、CG/Paldus＋既知phaseの構成へ具体的に還元。1Q–2Q変換一般も既知であり、符号化変換自体を新原理としない |
| CC/TDCC | 未知波動関数の対数や振幅を輸送する操作ではない。NBのchart移送を再開せず、\(\rho_2\)は既知係数から準備する |

「既存アルゴリズムでは元Hをsimulateできない」とは主張しない。
既知DF/PF、一般sparse合成、Schur等は実装経路を与え得る。
普通のpartial SWAP／isometryだけでは満たせない仕様でも、既知CG/Paldusを使えば具体的な生成経路が書ける。
このため、その不足だけを根拠に新しい操作が必要とはしない。
既報に完全同一のchemistry protocolがあるか、総費用が有用かの網羅的調査はしていない。
しかし、今回求めた衝突の生成を新原理と扱う理由は残らなかった。

## 8. 最小の紙上確認案（追加実施は未承認）

この対応式を後で確認する場合の最小例は、M=5、N=3の形式的な占有空間とする。
固定wのr=0,1,2では、block状態数はそれぞれ10、3、1。
今回はその行列を計算機で生成・対角化せず、gateの回転角列も生成していない。
紙上で得たphaseの値は(11)の\(1/3,-2/3,1\)であり、これと実装角度列の生成は区別する。

確認順序は以下である。

1. 全up→全downのmode順序で(9)の縮約と符号を紙上で読み合わせる。
2. (10)–(11)が\(A_\alpha^\dagger A_\beta\otimes|\beta\rangle\langle\alpha|/3\)の作用と一致するか。
3. 補助状態\((|12\rangle+i|45\rangle)/\sqrt2\)、target\(|123\rangle\)という形式例で、pairの非対角coherenceが\(|345\rangle\)への作用へ伝わるか。
   既知のgroundや位相を入力する例ではない。\(\rho_2\)の非対角成分をclassical mixtureへ置き換えていないかを判別する。
4. control\(|+\rangle\)を含む場合の0/1間のoff-diagonal blockまで、同じ符号・scalarで一致するか。
5. 既知CG／Paldusのlabelと(11)の対応を確認し、実質的な新操作が残っていないかを判別する。

これは既知還元の短い確認案であり、新候補の正式採択や科学実装に進む提案ではない。
資源優位、分子benchmark、多段階の詳細レビューへ自動で広げない。

## 9. 失敗条件・不足情報・元Hへの接続

| 判定対象 | 成立しない／独立設計として残らない条件 |
|---|---|
| 作用の正しさ | target粒子数又は反対称性がcollision完了時に失われる。generatorが(3)と異なる。符号、Z、\(C_N\)を落とす |
| coherent実装 | w／rの測定で必要なcoherenceを消す。workに情報が残る。controlのrelative scalar phaseがずれる |
| oracle会計 | \(e^{-i\theta J_N}\)、一般\(\rho_2\)の準備、N電子ground／振幅表を無料で入力する |
| 独立性 | HMEの定理を引用するだけ、既知CG/Paldusや小block対角化の書換えだけ、又はPF/commutator係数の探索だけで生成を説明し尽くす |
| D1 | block-encoding／qubitizationを中核にする実装へ自動で切り替える |
| D2 | \(c\)、\(d\Gamma(h)\)、R、元Hのsector・energy originを落とす。collision成功をE0取得と同一視する |

構成が得られた場合でも、r回の衝突でinteractionの物理時間\(\tau\)を模擬する辞書は
\(t=C_N Z\tau\)、\(\theta=t/r\)。copied-state型の既知HMEの誤差・消費copyは依然残る。
制御版を含む誤差、\(\rho_2\)準備誤差、recoupling合成誤差、resetと古典前処理を全て会計する必要がある。[L02, L03]
sample accessだけを仮定する既知下界を、係数と準備回路が既知のこの問題の一般gate下界へ転用しない。
逆に、係数が既知だからcopy数・gate数が改善したとも主張しない。

一体項・scalar・Rとの接続には既知の正しい合成が必要で、その外側PFは新規性と数えない。
絶対E0推定にはさらに実際に準備するstate、ground overlap／識別条件、位相窓、読出しと成功確率が必要である。
今回それらを供給したとも、無料で仮定したとも扱わない。

未実装の変換・準備・費用評価は残るが、今回の操作機能と生成の核は既知構成へ還元できる。
追加の独立した規則を必要とする仕様を、ここからさらに変更して救済する作業は行わない。
**最終保持0件。対応式を確認する必要がある場合の条件付き案は§8だけとし、採否はGPT／ユーザーへ戻す。公開・照合後Mandatory STOP。**

[L02]: https://arxiv.org/html/1608.00281v1
[L03]: https://arxiv.org/html/2308.07956v1
[L02, L03]: prior_art_and_limits.md
[L04–L06]: prior_art_and_limits.md
[L04, L05]: prior_art_and_limits.md
[C02]: https://github.com/quantumlib/OpenFermion/blob/90074a3093f8e79f8432fb47103527d22e1cb609/src/openfermion/circuits/slater_determinants.py
