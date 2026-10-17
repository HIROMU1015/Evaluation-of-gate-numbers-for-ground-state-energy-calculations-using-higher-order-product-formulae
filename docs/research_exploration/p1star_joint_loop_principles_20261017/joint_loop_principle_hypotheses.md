# P1*：CARの交換経路から共同閉路を生成する仮説

2026-10-17 JST。**保持する未検証の構成仮説は1件（J1、高リスク）。成立した新しい構成原理・アルゴリズムは0件。** 発想と数学的な必要事項を本書、既報との対応と保持しない方向を[比較記録](prior_art_and_rejected_directions.md)、最初の検証と判断事項を[handoff](research_decision_handoff.md)に分ける。これは正式採択・科学的GOではない。

紙上の数学的検討、既存資料・一次文献の読解だけを行った。新たな科学計算、solver、数値最適化、simulation、科学用記号計算プログラム、実装・回路生成は実行していない。以下の局所恒等式は既知CARからの手計算であり、それ自体を新規成果としない。実現可能なpulse列を得たという記録でもない。

## 1. 前の失敗から変える設計単位

[独立検証commit 5110d347e1f032c9093430b3def13b3391602cdd][obstruction]は、固定wordの低次条件が振幅を拘束し、未完了のL1変位がL2²を共役するため

\[
+\eta^3[L_1,L_2^2]\otimes(aX_b+cP_b)
\]

が残ることを示した。これは固定factor・wordについてのfull Fock否定結果であり、別の共同閉路を否定しない。

次はwordを先に選んで全係数を解くのではなく、**電子経路の交換で「消える和」と「残る差」をCARから先に作り、それらへ制御経路の2次・3次の寄与を割り当てる**という生成規則を考える。相殺に使う関係を構成の入力にし、計算後の式の簡約に留めない。

元の[仮説P1*][origin]の目的、すなわち電子の非可換factorと共通busから位相を保つ相互作用を生成する問いを維持する。古い12 segment、4 primitive、box、target Kに対する実行契約は変更しない。J1は、それらと別の将来の概念仕様である。

## 2. CARで得る交換経路の和と差

4つの異なる軌道p,q,r,sについて \(E_{ij}=a_i^\dagger a_j\) と置く。CARを一度ずつ使うと

\[
Q_1=E_{pq}E_{rs}=-a_p^\dagger a_r^\dagger a_q a_s,
\qquad
Q_2=E_{ps}E_{rq}=+a_p^\dagger a_r^\dagger a_q a_s.
\]

従って

\[
Q_1+Q_2=0,\qquad Q_1-Q_2=2Q_1. \tag{1}
\]

Hermitianな \(H_\diamond=Q_1+Q_1^\dagger\) は、q,sからp,rへの二電子遷移とその逆を含む非零の二体作用である。p,rが空、q,sが占有された配置では遷移が許されるため、full Fockで零ではない。一方、N=1では両Qが零になる。**N=1だけの確認は、この候補の二体信号を消してしまう。** (1)はN=2だけの縮約ではなくfull FockのCAR恒等式である。

ここで交換記号σを \(\sigma Q_1=Q_2\) と定義する。これは二つのannihilation側の割当ての交換を表す**式の操作**であり、全軌道を交換する物理unitaryや、制御pathの自動的な対称変換ではない。この区別がJ1の最大の障害となる。

### 汎用の一体Lie代数だけでは消えない関係

抽象的一体生成元が \([E_{ij},E_{kl}]=\delta_{jk}E_{il}-\delta_{li}E_{kj}\) だけを満たす普遍包絡代数を比較対象とする。そこでは、異なる四添字の二つの積 \(E_{pq}E_{rs}\) と \(E_{ps}E_{rq}\) は別のPBW単項で、(1)の和を零には置かない。full FockのCAR表現ρへ写して初めて和が消える。

例えば \(M=E_{pp}=n_p\) なら、一体Lie交換関係だけで

\[
[M,Q_1]=Q_1,\quad [M,Q_2]=Q_2,
\quad \rho\big([M,Q_1+Q_2]\big)=0. \tag{2}
\]

比較代数では \([M,Q_1+Q_2]=Q_1+Q_2\neq0\)。したがってCAR固有の零関係を3次のbus付き輸送項へ持ち上げるための**代数的な受け皿**はある。ただし、この受け皿が実際のcontrol pathのlog係数として現れることは示していない。

## 3. J1の中心機構：2次は交換に対して反対、3次は同符号に組む

仮説は、一つの開いた共通bus経路の中で、二つの電子経路へ次の異なる割当てを作れる、というものである。

| 寄与 | 構成前に指定したい電子経路の組 | CAR表現での役割 |
| --- | --- | --- |
| 2次のbus恒等成分 | \((Q_1-Q_2)+\mathrm{h.c.}\) | \(2H_\diamond\)として相互作用を残す |
| 3次の不要bus成分 | \([M,Q_1+Q_2]\)や、(1)を左右から掛けて得る零関係の組 | 共役・輸送によるbus残余を消す |

係数は制御の符号付き面積と、その経路内での輸送・挿入の順序から決まる。**任意の2次係数と3次係数を独立に設定できるとは仮定しない。** また、3次全体が表の一項だけであるとも仮定しない。X/P一次だけでなく、Weyl次数3の全bus成分、電子の全body数を調べる必要がある。

元の障害は、一つの相互作用が一方向に共役されることで生じた。J1では同じ相互作用を作る別の電子経路をCARで特定し、相互作用の符号と輸送誤差の符号を別々に割り当てることを狙う。**「(1)がある」から「3次が消える」への飛躍はまだ埋まっていない。**

### 現在の構成仮説を数学的に定義する

許すHermitian一体factorの集合\(\mathcal F\)と、共通busのX/Pから作る実制御pathγを考える。そのformal logの次数jの係数を\(\ell_j(\gamma)\)、bus非identity成分を\(\mathcal B\)と書く。比較代数でも同じ記号を使い、ρだけをfull Fock CARへの写像とする。

J1が最初に満たすべき条件は

\[
\rho(\ell_1)=0,\qquad
\rho(\ell_2)=-i\kappa H_\diamond\otimes I_b,\quad \kappa\in\mathbb R\setminus\{0\},
\qquad \rho(\ell_3)=0, \tag{3}
\]

であり、その3次bus零化が(1)で生成されるCARの零関係を用いることを要求する。独立性の判別として、少なくとも

\[
\mathcal B\ell_3\neq0\ \text{（比較代数）},\qquad
\rho(\mathcal B\ell_3)=0\ \text{（full Fock CAR）} \tag{4}
\]

を確認したい。比較代数でも単に\(\ell_3=0\)なら、汎用の高次PF／echoで説明できる可能性が強く、J1の根拠には数えない。**(4)だけでは不十分**である。既知の完成閉路へ、CARでidentityになる余分なcellを付け足すだけでも形式上は通せるからである。CAR交換対が同じ開いたcellの目標生成とbus帰還に不可欠であること、既知の表現依存controlや誤差補償との対応も確認する必要がある。

## 4. 必要なprimitive・入力・概念的処理

### 4.1 追加する仮定

入力は元の電子Hamiltonianの係数と軌道label。最初の局所対象は、4つの異なる添字を持つ二体遷移である。元のL1/L2だけで全て実行できるとは仮定せず、次の一体factorへのbus結合を追加の**未確認access**として明示する。

\[
S_{ij}=E_{ij}+E_{ji},\qquad A_{ij}=-i(E_{ij}-E_{ji}),
\]

\[
\mathcal F=\{n_p,S_{pq},A_{pq},S_{rs},A_{rs},
S_{ps},A_{ps},S_{rq},A_{rq}\},
\]

\[
H_{\rm ctl}(t)=\sum_{F\in\mathcal F}F\otimes
\{u_F(t)X_b+v_F(t)P_b\},\qquad u_F,v_F\in\mathbb R. \tag{5}
\]

factor間には共有軌道による非可換な組がある。逐次又は同時のsigned controlを概念的に許すが、物理的な独立addressability、bandwidth、frame変更費は未確立。**非HermitianなE単独のunitary、二体force、\(e^{-itH_\diamond}\)を無料primitiveにしない。** Eは代数的な経路labelで、実操作はS/AのHermitianな組へ分解しなければならない。

busは1 oscillatorのまま。segment数・word・振幅上限は未指定で、元の12 segmentやboxを変更した実行は行わない。元契約のgrantやauthorizationをこの概念仕様へ流用しない。

### 4.2 入力から制御仕様へ至る仮説上の処理

1. 元二体係数のantisymmetryを保持し、四軌道ごとに\(Q_1,Q_2\)の交換対を作る。係数を捨てたりfitしたりしない。
2. (1)の「和が消える・差が残る」を、制御を決める前の局所規則として登録する。
3. 相互作用の面積寄与には交換対の差を、3次の輸送寄与には交換対の和を割り当てる、一つの接続した制御cellの文法を作る。
4. (3)を満たす実pathへ持ち上がるか調べる。pathのiterated integralが満たすshuffle関係とlogのLie条件、Hermiticityを同時に守る。ここが未解決であり、現時点でpulse列は出力できていない。
5. 実現した場合だけ、対応する局所制御cell、係数の符号／位相の対応、残余、費用を返す。不可能／未確定なら、失敗した持上げ条件を返す。

この規則が、各factorのbus閉路を完成させた後の連結、汎用交換子formula、又は一般optimizerへの問題投入に終わる場合は、独立した共同原理として保持しない。代数上の入力規則は具体化できたが、**段階3–4の構成の存在は仮説**である。

## 5. 7項目の判定票

| 項目 | J1の記録 |
| --- | --- |
| 1. 数学的・物理的機構 | CARの交換対の反対称部分を二体信号に、対称部分を輸送誤差の零関係に割り当て、共通busの開いた経路を共同で閉じる。 |
| 2. primitiveと入力 | (5)のHermitian一体factor×共通X/P、実signed control、元二体係数と軌道label。多体oracle、exact state、energy truthは不要。accessの実装費は未知。 |
| 3. 3次障害を避ける理由 | 零でない相互作用とCARで消える輸送項を分ける代数的関係(1)–(2)がある。ただし全3次係数をその関係へ割り当てる実pathの存在は未証明。 |
| 4. 既知との差分 | 目標二体作用や交換子生成そのものは既知。残る問いは、CAR交換対から開いたbus経路の生成規則を作り、汎用公式では零にならない3次項を相殺できるか。最適化後の簡約だけでは差分にならない。 |
| 5. 未証明条件 | 実pathへの持上げ、非Hermitian経路の物理的実現、全3次成分の零化と二体信号の保持、閉路への既知還元の回避、4次以降の残余、有限時間の位相を保つ帰還、化学Hへの被覆・費用。 |
| 6. 最小の次検証 | 四軌道の交換対1個について、紙上で(3)–(4)を満たす有限cellの文法を構成できるか、又はこの文法の整合条件が\(\kappa=0\)等を強制するかを判別する。まずsolverや全Hの展開に進まない。 |
| 7. 保持を取り下げる条件 | 必要accessが提供不能／多体oracleを隠す、σを実装可能な単純swapと誤認している、既報に同じ生成規則が完全対応、signalも零、又は実現方法が既知の独立閉路・汎用echoだけに還元される場合。高リスク・未証明だけでは取り下げない。 |

## 6. 最初の検証でも省略できない境界

**代数の零関係は制御pathではない。** σは一般に一体Lie代数のautomorphismでもない。面積と3次モーメントの交換符号を指定しただけでは、real controlのsignatureの実現可能性を示せない。この点を飛ばした「CARだから相殺する」という説明は不十分である。

正の紙上結果の最小形は、具体的な一つのcell文法、(3)の全成分確認、(4)のCAR固有性、非Hermitian accessがないこと、既知閉路への還元の点検を同時に示すこと。3次を通っても、**4次整合や有限時間の閉路を認定しない**。その先は新しい検証範囲を定める必要がある。

負の結果なら、どの文法／access／次数条件で不可能だったかを残す。固定長の一wordが失敗しただけで全pathの不可能性としない。今回のJ1を取り下げても、P1*一般の不可能性にはならない。

## 7. 元HamiltonianとE0への接続

J1は四つの異なる添字のHermitian相互作用 \(Q_1+Q_1^\dagger\) を最初の対象とし、一般の複素係数の位相や全化学Hamiltonianを既に被覆したとはしない。概念的には

\[
H_{\rm orig}=cI+T+V_{\rm exchange}+V_{\rm rest}
\]

の一部を担当する。対角・添字重複の相互作用、元の一体作用、scalar、残余は保持して別途処理・誤差会計へ戻す。cを落としたり、bus付きHの基底energyを元E0へ置き換えたりしない。外側PFや密度平方による既知部分は新規と数えず、費用も消さない。

D1・D2を維持する。full FockのCAR関係を用いた構成仮説であり、N=2だけで高体項が消えることを全空間の零化としない。初期bus状態へ戻る位相を保つ作用が最終目標で、部分traceしたchannelの平均一致だけでは成功としない。

**Mandatory STOP：本資料の公開・照合後に停止。J1の正式採択、pulse生成・科学実装・求解・詳細科学レビューへ進まない。**

[obstruction]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5110d347e1f032c9093430b3def13b3391602cdd/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md
[origin]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/principle_ideation_map.md
