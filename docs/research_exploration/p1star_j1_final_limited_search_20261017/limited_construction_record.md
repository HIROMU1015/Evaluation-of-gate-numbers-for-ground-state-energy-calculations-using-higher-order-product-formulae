# J1：未完了経路を組む最終限定探索

2026-10-17 JST。**今回、非還元な共同生成文法は得られなかった。新原理の候補として残す構成は0件。第一推奨はJ1追加探索の一時保留であり、研究状態の正式変更は行わない。** 以下は、固定した二つの関連文法だけを調べた紙上記録で、全J1又はP1*の不可能性証明ではない。

読む順序：[判断用handoff](research_decision_handoff.md) → 本書 → [provenance](provenance.json)。最新の紙上検証はcommit c7d3f077d634e4165b7cd326bac7caa1ae04ff66、J1正本はdd36794069f2f8063d3eba6c7e3fcc989d9b0ceb、固定wordの障害の独立検証は5110d347e1f032c9093430b3def13b3391602cdd。過去の資料・source・結果・契約を上書きしない。

## 1. 一度限りの範囲と判定基準

前の20-pulse cellは、full Fockで完成した二体gate Bを作ってから、$(VBV^{-1})(V^{-1}BV)$という汎用echoへ還元できた。そのため今回は、二体gateを入力とせず、**電子factorごとに分割した、まだ閉じていないX/P経路を先に相互作用させる**。

検討は次の二つで終了する。修正版の失敗を受けて第三の文法、振幅族、別factor、最適化を追加しない。

| ID | 紙上で検討する有限文法 | 検討目的 |
| --- | --- | --- |
| G1 | 二つの未完了な2-pulse legのgroup commutatorをS/A経路で組む16-pulse cell | CARによる二体信号の抽出と、未完了経路間の3次相殺が同時に起きるか。 |
| G2 | 同じlegを3-pulseの対称分割にした24-pulse修正版 | G1の3次障害を除いたとき、CAR固有の生成規則が残るか。 |

全て紙上の実制御定義である。新規科学計算、solver、科学的な記号計算プログラムの作成・実行、数値行列計算、simulation、数値・網羅的word探索、実装・benchmarkを行っていない。Git・byte hash・文書検査用の技術処理は演算子計算に使用しない。

「同じ出力が一般的な合成でも作れる」だけでは、全ての生成規則を同一としない。本記録の還元判定は、**実際のpathが既知のgroup commutatorと対称product formulaで生成されていること、3次相殺が比較代数でも起きること、同じ2次信号が既知の閉路へ具体的に写ること**に基づく。比較代数の非零残余がCARで零になる診断だけを十分条件としない。

## 2. 記号、実操作、CARが作用できる次数

四軌道p,q,r,sは相異なる。電子CAR、$[X,P]=iI$、電子とbusのtensor分離を使い、

\[
E_{ij}=a_i^\dagger a_j,\quad
S_{ij}=E_{ij}+E_{ji},\quad A_{ij}=-i(E_{ij}-E_{ji}),
\]

\[
Q_1=E_{pq}E_{rs},\quad Q_2=E_{ps}E_{rq},\quad
H_\diamond=Q_1+Q_1^\dagger,\quad Q_2=-Q_1
\tag{1}
\]

とする。(1)最後の式はfull FockのCAR恒等式である。許す操作は固定J1の

\[
\mathcal F=\{n_p,S_{pq},A_{pq},S_{rs},A_{rs},
S_{ps},A_{ps},S_{rq},A_{rq}\}
\]

に対する$e^{-i\eta cF\otimes X/P}$、実のη非依存係数cだけ。G1/G2はn_pを使わず、許可alphabetの部分集合である。右端の指数が最初に作用する。逆pathはsegmentを逆順・逆符号にする操作で、新しいgate oracleではない。ηのO記号は形式次数であり、有限時間のbus norm保証ではない。

比較代数は一体Lie関係のみを課した$U(\mathfrak{gl}_4)\otimes\mathcal W_b$。ρをfull Fock CAR表現とする。$[E_{ij},E_{kl}]=\delta_{jk}E_{il}-\delta_{li}E_{kj}$は比較代数でも課すが、Q1+Q2や同じannihilation添字の積を零にする関係は課さない。

### 2.1 bus三次の最高次数に関する必要条件

電子A,Bとbus線形u,vに対して

\[
[A\otimes u,B\otimes v]
=\tfrac12[A,B]\otimes\{u,v\}
 +\tfrac12\{A,B\}\otimes[u,v].
\tag{2}
\]

一体factorの交換子は一体で、$[u,v]$はscalar。この式をもう一度使うと、三重Lie語のbus Weyl次数3の係数は、電子側の入れ子の**一体**交換子になる。低いbus次数には電子積が現れ、そこで初めてCARの二体零関係が作用し得る。

また$(X,P)\mapsto(-X,-P)$のparityから、奇数η次数のlogはbusの奇parityを持つ。3次で可能なのはWeyl次数3と1で、bus恒等成分はない。この条件はη非依存の線形forceに限定する。

一体作用$d\Gamma(t)$のN=1制限はt自身である。そのため、bus三次係数の一体行列が非零なら、二体CAR関係でfull Fockの零へ送ることはできない。逆にこの行列が零なら、一体Lie関係の段階ですでに零である。**J1では最高bus次数を先に消した上で、残るbus一次の電子積へCARを使う必要がある。** これは低次の必要条件であり、全ての実pathについてその実現が不可能という結論ではない。N=1を二体信号の主判定に切り替えてもいない。

## 3. CAR交換対から二つの未完了legを指定する

$\nu=S,A$に対して

\[
\begin{array}{llll}
f_{1S}=S_{pq},& f_{2S}=S_{ps},&
g_{1S}=S_{rs},&g_{2S}=-S_{rq},\\
f_{1A}=A_{pq},& f_{2A}=A_{ps},&
g_{1A}=A_{rs},&g_{2A}=-A_{rq},
\end{array}
\]

\[
F_\nu=f_{1\nu}+f_{2\nu},\quad
G_\nu=g_{1\nu}+g_{2\nu},\quad
J=E_{qs}-E_{sq}.
\tag{3}
\]

共有軌道を持つleg内factorは非可換である。一体Lie関係から

\[
[f_{1\nu},f_{2\nu}]
=[g_{1\nu},g_{2\nu}]=J,\qquad
[F_\nu,G_\nu]=0.
\tag{4}
\]

最後の可換性は、q,sの重なりの二寄与が逆符号になるためで、CAR商の関係ではない。

ここで非Hermitianな式を**実操作ではなく代数上の略記**として

\[
\mathsf E=E_{pq}+E_{ps},\qquad
\mathsf G=E_{rs}-E_{rq}
\]

と書けば、

\[
F_SG_S-F_AG_A
=2(\mathsf E\mathsf G+\mathsf E^\dagger\mathsf G^\dagger).
\tag{5}
\]

full Fockでは、同じannihilation添字を持つ
$E_{pq}E_{rq}=E_{ps}E_{rs}=0$と(1)によって

\[
\mathsf E\mathsf G
=Q_1-E_{pq}E_{rq}+E_{ps}E_{rs}-Q_2
=2Q_1,\qquad
\rho(F_SG_S-F_AG_A)=4H_\diamond.
\tag{6}
\]

従ってCARを構成前の係数選択に使って、S/A経路の差に非零のHermitian二体信号を割り当てられる。q,sが占有、p,rが空の配置でQ1は非零なので、これはscalar又は一体だけに退化していない。比較代数では(6)の余分な積をCARで消せず、(5)までを使う。

この段階でσを物理swapとしたり、$\mathsf E,\mathsf G$のunitaryを直接使ったりしていない。また(6)だけでは3次の閉鎖条件は何も解けていない。

## 4. G1：16-pulseの開いた経路同士の交換

次を有限実pulseの積として定義する。

\[
L_\nu=e^{-i\eta f_{1\nu}X}e^{-i\eta f_{2\nu}X},\quad
R_\nu=e^{-i\eta g_{1\nu}P}e^{-i\eta g_{2\nu}P},
\]

\[
W_\nu=L_\nu R_\nu L_\nu^{-1}R_\nu^{-1},\qquad
U_{\rm G1}=W_S W_A^{-1}.
\tag{7}
\]

各Wは8 pulse、全体16 pulse。$g_{2\nu}$の負号も単なるsigned control。L/R単独はbusを戻す二体gateではなく、非可換な電子factorを含む未完了legである。従って前の「完成gateを作ってからecho」には設計段階で戻していない。一方、group commutatorという外側の文法自体は既知である。

### 4.1 1次と2次：信号抽出までは成立

\[
a_\nu=-iF_\nu X,\qquad b_\nu=-iG_\nu P.
\]

(4)と2-pulse BCHから

\[
\log L_\nu=\eta a_\nu-\tfrac{\eta^2}{2}JX^2+O(\eta^3),
\quad
\log R_\nu=\eta b_\nu-\tfrac{\eta^2}{2}JP^2+O(\eta^3).
\tag{8}
\]

group commutatorは1次を持たず、

\[
\ell_2(W_\nu)=[a_\nu,b_\nu]
=-iF_\nu G_\nu\otimes I.
\tag{9}
\]

従って比較代数でも2次bus非identityは零で、full Fockでは

\[
\rho(\ell_1(U_{\rm G1}))=0,\qquad
\rho(\ell_2(U_{\rm G1}))=-4iH_\diamond\otimes I.
\tag{10}
\]

κ=4は実非零。電子scalar、一体drift、余分な二体作用は(6)で消え、目標だけが残る。

### 4.2 3次：bus三次がCARを使う前に障害となる

$A=\eta a+\eta^2a_2+\cdots,B=\eta b+\eta^2b_2+\cdots$について

\[
\log(e^Ae^Be^{-A}e^{-B})
=\eta^2[a,b]
 \eta^3\{[a_2,b]+[a,b_2]
 \tfrac12[a+b,[a,b]]\}+O(\eta^4).
\tag{11}
\]

本設定では$[a_\nu,b_\nu]=-iF_\nu G_\nu\otimes I$がa,bと可換なので、最後の項は零。Weyl対称単項を

\[
\mathcal W_{21}=\tfrac13(X^2P+XPX+PX^2),\quad
\mathcal W_{12}=\tfrac13(XP^2+PXP+P^2X)
\]

とすると、

\[
\boxed{\begin{split}
\ell_3(W_\nu)={}&
\tfrac i2[J,G_\nu]\otimes\mathcal W_{21}
+\tfrac i2[F_\nu,J]\otimes\mathcal W_{12}\\
&-\tfrac12\{J,G_\nu\}\otimes X
-\tfrac12\{F_\nu,J\}\otimes P.
\end{split}}
\tag{12}
\]

例えば$[JX^2,G_\nu P]=[J,G_\nu]\mathcal W_{21}+i\{J,G_\nu\}X$。これに(8)の$-1/2$とbの$-i$を掛けると、(12)の$i/2$と$-1/2$が得られる。順序・i・符号をこの式で固定した。

全体では$\ell_3(U_{\rm G1})=\ell_3(W_S)-\ell_3(W_A)$。両Wの先頭がη²なので、W間のBCH交換子は3次へ寄与しない。具体的に

\[
[J,G_S]=S_{rq}+S_{rs},\qquad
[J,G_A]=A_{rq}+A_{rs}.
\tag{13}
\]

したがって$\mathcal W_{21}$の電子係数は

\[
\tfrac i2(S_{rq}+S_{rs}-A_{rq}-A_{rs}).
\tag{14}
\]

N=1上の(r,q)成分は$i(1+i)/2=(-1+i)/2\neq0$。X/P線形単項又は別の三次単項と混同できず、この非零の一体作用をCARの二体零関係で消すこともできない。**G1は3次で限定的に不成立**。下位のX/P一次成分が一部CARで消えても、この結論は変わらない。

(12)はこの文法の全3次で、都合のよいX一次項だけを選んだものではない。純電子3次はparityで存在しない。今回否定したのは(3)、(7)の係数・順序を明示した一つのcellであり、全振幅・別word・同時制御・全J1のno-goではない。

## 5. G2：対称化すれば通るが、CARによる3次相殺ではなくなる

一度だけの修正版として、同じf/gを対称分割する。

\[
\begin{split}
\widetilde L_\nu
 &=e^{-i\eta f_{1\nu}X/2}e^{-i\eta f_{2\nu}X}e^{-i\eta f_{1\nu}X/2},\\
\widetilde R_\nu
 &=e^{-i\eta g_{1\nu}P/2}e^{-i\eta g_{2\nu}P}e^{-i\eta g_{1\nu}P/2},\\
\widetilde W_\nu
 &=\widetilde L_\nu\widetilde R_\nu
   \widetilde L_\nu^{-1}\widetilde R_\nu^{-1},\qquad
U_{\rm G2}=\widetilde W_S\widetilde W_A^{-1}.
\end{split}
\tag{15}
\]

各Wは12 pulse、全体24 pulse。全係数は実数±1、±1/2で、pulse数以外の新しいprimitiveはない。

対称legは$\widetilde L_\nu(-\eta)=\widetilde L_\nu(\eta)^{-1}$であり、logの2次が零。同じことがRにも成り立つ。従って

\[
\log\widetilde L_\nu=\eta a_\nu+O(\eta^3),\qquad
\log\widetilde R_\nu=\eta b_\nu+O(\eta^3).
\]

(11)の$a_2,b_2$がともに零となり、残る入れ子交換子も(4)で零なので

\[
\ell_1(\widetilde W_\nu)=0,\quad
\ell_2(\widetilde W_\nu)=-iF_\nu G_\nu\otimes I,\quad
\ell_3(\widetilde W_\nu)=0
\quad\text{（比較代数ですでに成立）}.
\tag{16}
\]

よってfull FockでG2は

\[
\rho(\ell_1)=0,\qquad
\rho(\ell_2)=-4iH_\diamond\otimes I,\qquad
\rho(\ell_3)=0.
\tag{17}
\]

G1の全3次項が消える理由は、二体CAR関係ではなく、**両legの一般的な対称product formulaと、aggregate factorの一体Lie可換性**である。3次のbus一次・三次、不要な純電子作用の全てについて(16)が適用される。「比較代数で非零、CARで零」という必要な診断すら満たさず、J1固有の成功例には数えない。

### 5.1 既知の生成規則への具体的対応

同時制御も許すJ1 accessでは、合計一体forceから

\[
\mathcal R_\nu
=e^{\eta a_\nu}e^{\eta b_\nu}e^{-\eta a_\nu}e^{-\eta b_\nu}
=e^{-i\eta^2F_\nu G_\nu}\otimes I
\tag{18}
\]

を作れる。G2は、この既知の可換force rectangleの各legを通常のStrang分割へ置き換えた**そのもののpath**である。これは電子二体gateを無料入力にした対応ではなく、一体forceの実指数を段階ごとに対応させたもの。

(16)から$\log\widetilde W_\nu$と$\log\mathcal R_\nu$は3次まで一致する。ただし、**有限ηで両者がexactに等しいとはしない**。Strangのleg誤差は一般にその先へ入る。ここでの還元は既知の生成規則の具体的な特殊化であり、4次以降を無視してexact等式と偽るものではない。

さらに、比較のためのorbital labelとして

\[
u=(q+s)/\sqrt2,\quad v=(s-q)/\sqrt2
\]

を用いると、$\{p,u,r,v\}$は直交する四modeで、

\[
F_S=\sqrt2 S_{pu},\quad G_S=\sqrt2 S_{rv},\quad
F_A=\sqrt2 A_{pu},\quad G_A=\sqrt2 A_{rv}.
\tag{19}
\]

これは(3)を解釈する座標変換であり、新しい物理rotationを無料操作として追加していない。これらのforceは元の許可factorの同時和である。

CARのnilpotencyにより、互いにdisjointなpairのS積とA積は可換である。前の紙上検証と同じく、$e=E_{pu},g=E_{rv}$なら、$(eg+e^\dagger g^\dagger)(eg^\dagger+e^\dagger g)=0$かつ逆順も零で示せる。従って既知のrectangle二つはfull Fockで

\[
\rho(\mathcal R_S\mathcal R_A^{-1})
=e^{-i\eta^2(F_SG_S-F_AG_A)}
=e^{-4i\eta^2H_\diamond}\otimes I.
\tag{20}
\]

このexact式は**比較baseline**についてであり、G2全体のfinite-time bus帰還を認定するものではない。G2の信号選択にCARを使っていても、(18)–(20)の既知の幾何学的位相gate／fermionic代数分解から独立した共同生成原理は残らない。

## 6. 実pathの整合性と還元判定

G1/G2は双方とも具体的な有限実指数の積なので、演算子関係を課す前の自由な制御letterのsignatureはgroup-likeで、shuffle関係を満たし、logはLie級数である。2次面積と3次モーメントを別々の任意数として設定していない。(11)–(12)はその積から導く入れ子交換子である。

f,g,F,GはHermitian、Jはanti-Hermitian。(12)の$[J,G]$、$[F,J]$はHermitianで$i/2$を持ち、$\{J,G\}$、$\{F,J\}$はanti-Hermitian。したがって全logがanti-Hermitianであること、係数が実signed controlから生じることは整合する。非Hermitian Eの指数、二体force、補助qubit、sectorだけの恒等式、未指定のcleanupは用いない。

| 比較対象 | 具体的な判定 |
| --- | --- |
| 完成した単独閉路の連結 | G1は未完了の分割legを交換するが3次で失敗。G2は(18)の閉路のlegを既知PFで分割した生成規則。(20)が同じ信号の完成閉路baseline。 |
| 既知gate＋echo | 以前の20-pulseは正確にこの還元。今回はそのgateを部品にせず(7)を試したが、通ったG2の改善はCARによらない一般対称化。新しいechoの名称変更として保持しない。 |
| DCG | 今回のG2をDCGの特定のbalance-pair sequenceとexactに同一視する根拠はない。DCGで誤差関係を設計する一般的発想を新規とはせず、未承認の補償pulseを追加しない。DCGへ非還元なことの網羅的証明もない。既知PFへの明示的還元だけで本例の独立性は否定できる。 |
| 一般的な交換子合成 | (7)、(15)はgroup commutator。G2はそのlegを対称PFで実装する既知の階層構成であり、新しい生成規則ではない。 |
| fermionic unitary synthesis | (6)、(19)–(20)がdouble excitationの既知代数的分解に対応する。特定論文の全spin-adapted分解との包含を今回証明したわけではない。CARを先に使うという看板だけでは独立性を認定しない。 |

一次文献の必要箇所を既存registryから再利用し、今回も限定照合した。

- [Spiller et al., quant-ph/0509202v3, §IV Eqs. (7)–(10)](https://arxiv.org/html/quant-ph/0509202v3#S4)：4 conditional displacementの幾何学的位相とbus帰還。(18)の規格化・符号は本書で直接確認した。
- [Childs–Wiebe, 1211.4945v2, 導入・§II](https://arxiv.org/html/1211.4945v2)：elementary指数からの汎用commutator product formula。G1/G2の外側の文法を新規としない。同論文の補助qubit accessを追加しない。
- [Khodjasteh–Viola, 0906.0525v2, §IV.2 Eqs. (28)–(29)](https://arxiv.org/html/0906.0525v2)：gateとidentityの誤差を合わせるDCGのbalance-pair構成。bath norm保証を本busへ無条件転用しない。
- [Magoulas–Evangelista, 2511.13485v1, abstract](https://arxiv.org/html/2511.13485v1)：Lie構造によるfermionic unitaryのexact分解。全構成の詳細照合は未実施で、検索不一致を独立性の証拠にはしない。

本書の還元は式とpathで示した範囲の結論であり、関連文献が存在するだけで別の生成可能性を排除したものではない。新しい網羅的新規性調査・詳細科学レビューは開始しない。

## 7. 結果と終了判断に渡す材料

| 対象 | 判定 |
| --- | --- |
| G1の1次・2次 | **成立**。不要busは零、非零二体信号κ=4。CARが信号抽出に作用する。 |
| G1の1～3次全条件 | **限定的な不成立**。(14)のbus三次・一体係数が非零。 |
| G2の1～3次 | **成立するが既知法への還元**。3次は比較代数ですでに零、CAR固有の相殺ではない。 |
| J1固有の非還元な共同生成文法 | **得られず／一般の存在問題は未解決**。非還元の成功例0件、全pathの不可能性証明0件。 |
| 今回新たに保持する研究候補 | **0件**。形式上の高リスク候補を無理に追加しない。 |

今回の有用な境界は、CARによる二体信号の抽出までは未完了legの構成へ具体化できるが、同じ構成で残るbus三次は一体Lieの障害になること、それを汎用対称化で消すとCAR固有の相殺という根拠がなくなること。この二つは、無制限のword探索へ進む代わりに、今回の限定探索を終える判断材料となる。

J1固有の研究可能性は、**抽象的には未否定だが、今進める具体的な非還元文法がない**という状態である。bus三次を比較代数で消し、bus一次の電子二次成分へCARの零関係を送り、同じ未完了cellで目標生成にも不可欠にするpathが不足する。実制御・shuffle条件を満たすその文法と、既知gate＋PF／echo／DCGへの具体的非還元の根拠がない限り、科学計算で何を識別するかを固定できない。

従って**第一推奨はJ1の追加探索を一時保留し、今回の知見を記録して終えること**。これはユーザーが指定した「具体的な非還元文法が得られなかった場合」の報告であり、Codexによる研究状態のPAUSED/HOLDへの正式変更ではない。高リスク・未証明そのものを理由にした一般的な価値否定でもない。

4次以降、G2全体の有限ηでのcoherent bus帰還、物理access、一般の化学Hamiltonianへの拡張、新規性、資源優位は未確立。full Fockをsector限定と混同せず、固定wordのUNSATとその独立検証の射程を拡張しない。D1・D2、元電子Hamiltonianのscalar・一体・残余相互作用と絶対E0対応、既存のSOURCE・結果・grant・authorization・STOPを維持する。

### 前記録の表示上の注記

c7d3f07の数学記録Eq. (12)の第2式には、ρとB2逆の間にinline数式delimiterが混ざる表示ミスがある。意図する式は

\[
\rho(B_2^{-1})=\rho(B_1)=B
\]

で、同commitのhandoffにはこの形で記されている。今回新資料内に注記し、凍結資料を修正しない。前記録の数学的結論を覆す問題ではない。

**Mandatory STOP：新規資料の公開・照合後に終了。GPT／ユーザーは継続又は一時保留を判断する担当であり、Codexは正式状態変更、科学計算、実装、追加探索、詳細科学レビューを開始しない。**
