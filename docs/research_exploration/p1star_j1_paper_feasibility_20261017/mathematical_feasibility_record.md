# J1：四軌道交換対の限定的な紙上成立性検証

2026-10-17 JST。正本はJ1 commit `dd36794069f2f8063d3eba6c7e3fcc989d9b0ceb`。**実制御による1～3次条件は、下記の20-pulse cellで満たせる。ただし、そのcellは完成した幾何学的位相gateと汎用echoへ還元される。J1に要求した独立した共同生成規則の成立は未解決である。** この二つを同じ「成立」と呼ばない。

新たに行ったのは本書の紙上導出と一次文献の限定照合である。科学用プログラム、CAR係数表の生成、solver、数値行列計算、最適化、simulation、網羅的word探索は実行していない。過去の結果・契約・grant・STOPを変更しない。読む順序は[判断用handoff](decision_handoff.md) → 本書 → [provenance](provenance.json)。

## 1. 問題、比較代数、適用範囲

異なる四軌道 $p,q,r,s$ に対し

\[
E_{ij}=a_i^\dagger a_j,\quad Q_1=E_{pq}E_{rs},\quad Q_2=E_{ps}E_{rq},\quad
H_j=Q_j+Q_j^\dagger,\quad D_j=Q_j-Q_j^\dagger.
\]

CARから直接

\[
Q_1=-a_p^\dagger a_r^\dagger a_q a_s,
\qquad Q_2=+a_p^\dagger a_r^\dagger a_q a_s,
\qquad Q_2=-Q_1. \tag{1}
\]

従ってfull Fockで $H_2=-H_1,D_2=-D_1$。目標は $H_\diamond=H_1$。q,sを占有しp,rを空にした配置にQ1は非零の遷移を作り、逆向きはQ1†が担う。H1は非零のHermitian二体作用で、N=1では零となる。この非零性をN=1の検査で置き換えない。

比較代数は、一体Lie関係だけを課した $U(\mathfrak{gl}_4)\otimes\mathcal W_b$、

\[
[E_{ij},E_{kl}]=\delta_{jk}E_{il}-\delta_{li}E_{kj},\qquad [X,P]=iI
\]

とする。電子生成元には $E_{ij}^\dagger=E_{ji}$ を入れる。ρはそのfull fermionic Fock表現への写像で、busには恒等写像を作用させる。比較代数ではQ1とQ2は別のPBW二次単項であり、Q1+Q2を零にしない。以下、ρを書く前の式はこの比較代数でも成立することを明示して使う。

許す実操作は固定J1の

\[
S_{ij}=E_{ij}+E_{ji},\quad A_{ij}=-i(E_{ij}-E_{ji}),\quad M=n_p,
\]

\[
\mathcal F=\{M,S_{pq},A_{pq},S_{rs},A_{rs},S_{ps},A_{ps},S_{rq},A_{rq}\}
\]

への共通bus X/P結合だけ。各指数は $e^{-i\eta cF\otimes B}$、$c\in\mathbb R,B=X,P$ とする。ηは実の形式スケール、制御係数はη非依存。右端の指数が時間的に最初に作用する。電子とbusのtensor記号は必要な箇所以外省略する。

目的は $\rho(\ell_1)=0,\rho(\ell_2)=-i\kappa H_1\otimes I,\kappa\ne0,\rho(\ell_3)=0$。O記号は形式次数であり、unbounded busのノルム誤差・収束を意味しない。旧L1/L2、12 segment、box、4次目標の実行契約とは別の概念的検証で、旧契約を変更した実行ではない。

## 2. Hermitian制御で実装できる既知の基本閉路

Hermitian F,Gが電子側で可換なら、

\[
\begin{split}
R(F,G;\eta)&=e^{-i\eta FX}e^{-i\eta GP}e^{+i\eta FX}e^{+i\eta GP},\\
[-iFX,-iGP]&=-iFG\otimes I.
\end{split} \tag{2}
\]

最後の交換子はFX,GPの双方に可換なので

\[
R(F,G;\eta)=e^{-i\eta^2FG}\otimes I. \tag{3}
\]

これはbusを戻して電子積を残す通常のconditional-displacement rectangleであり、独立したJ1機構ではない。[Spiller et al., v3, §IV, Eqs. (7)–(10)](https://arxiv.org/html/quant-ph/0509202v3#S4)の機構に対応する。規格化と符号は本書のCCRと(2)から導いた。qubitの実装費や一般の化学factorへの物理accessまで同論文で保証されたとはしない。

四添字が異なるため、$S_{pq},S_{rs}$ は可換、$A_{pq},A_{rs}$ も可換であり、交換側 $ps,rq$ も同じである。この可換性は一体Lie関係だけで成立する。そこで**primitiveではなく、4指数ずつへ展開できる略記**として

\[
\begin{split}
B_1&=R(S_{pq},S_{rs};\eta)R(A_{pq},A_{rs};\eta)^{-1},\\
B_2&=R(S_{ps},S_{rq};\eta)R(A_{ps},A_{rq};\eta)^{-1},\\
T_1&=S_{pq}S_{rs}-A_{pq}A_{rs}=2H_1,\\
T_2&=S_{ps}S_{rq}-A_{ps}A_{rq}=2H_2,\qquad K_j=-iT_j\otimes I
\end{split} \tag{4}
\]

と置く。最後の二つの積の差はS/Aを展開すれば分かり、ここでもCARの二体零関係はまだ使わない。各Rはη²だけの関数なので、比較代数でも

\[
\log B_j=\eta^2K_j+O(\eta^4),\qquad \ell_1(B_j)=\ell_3(B_j)=0. \tag{5}
\]

二つのrectangleの電子gate同士が比較代数で可換とは仮定していない。BCHの最初の積間交換子はη⁴である。

## 3. 紙上で定義できる一つの有限実制御cell

\[
h=-iM\otimes X,\quad V=e^{\eta h},\qquad
U_J=(VB_1V^{-1})(V^{-1}B_2^{-1}V)
     =VB_1V^{-2}B_2^{-1}V. \tag{6}
\]

これは20個の許されたHermitian force指数で構成する。逆gateはその定義にある指数を逆順・逆符号で実行することであり、新しい操作ではない。時系列を具体的に書くと次のとおり。各行の「係数」は $e^{-i\eta cF\otimes B}$ のcで、全て実数±1である。

| 時間順 | 電子factor | bus | 係数 |
| --- | --- | --- | --- |
| 1 | M | X | +1 |
| 2,3,4,5 | $S_{ps},S_{rq},S_{ps},S_{rq}$ | X,P,X,P | −1,−1,+1,+1 |
| 6,7,8,9 | $A_{rq},A_{ps},A_{rq},A_{ps}$ | P,X,P,X | −1,−1,+1,+1 |
| 10,11 | M,M | X,X | −1,−1 |
| 12,13,14,15 | $A_{pq},A_{rs},A_{pq},A_{rs}$ | X,P,X,P | −1,−1,+1,+1 |
| 16,17,18,19 | $S_{rs},S_{pq},S_{rs},S_{pq}$ | P,X,P,X | −1,−1,+1,+1 |
| 20 | M | X | +1 |

行2–9は $B_2^{-1}$、行12–19はB1である。隣接する10,11をまとめなくても有限cellになる。各segmentを正の同一時間としてsigned couplingを与えればよく、非HermitianなEの直接指数化、電子だけのrotation、二体oracle、補助bus、補正gateは用いない。これは指定accessの下での数学的なreal-control実現であって、ハードウェアの独立addressability・校正を確認したものではない。

## 4. 1次・2次・3次の全成分と符号

(5)を共役すると

\[
\begin{split}
\log(VB_1V^{-1})&=\eta^2K_1+\eta^3[h,K_1]+O(\eta^4),\\
\log(V^{-1}B_2^{-1}V)&=-\eta^2K_2+\eta^3[h,K_2]+O(\eta^4).
\end{split} \tag{7}
\]

双方の先頭がη²なので、その間のBCH交換子はη⁴以上。従って比較代数で

\[
\ell_1=0,\qquad \ell_2=K_1-K_2=-i(T_1-T_2)\otimes I,
\qquad \ell_3=[h,K_1+K_2]=-[M,T_1+T_2]\otimes X. \tag{8}
\]

この負号は $(-i)(-i)=-1$ による。$M=n_p$ に対して、一体Lie関係だけから

\[
[M,Q_j]=Q_j,\quad [M,Q_j^\dagger]=-Q_j^\dagger,
\quad [M,T_j]=2D_j.
\]

よって

\[
\boxed{\ell_3=-2(Q_1+Q_2-Q_1^\dagger-Q_2^\dagger)\otimes X.} \tag{9}
\]

(1)とその随伴を適用すればfull Fockで

\[
\boxed{\rho(\ell_1)=0,\quad
\rho(\ell_2)=-4iH_\diamond\otimes I,\quad
\rho(\ell_3)=0.} \tag{10}
\]

κ=4は実非零であり、2次信号も非零。2次電子項は二体Hだけで、scalar・一体・bus二次項は残らない。

**3次の一成分だけを都合よく抽出したのではない。** 各Rは比較代数ですでにexactなbus I gate、各Bjのlogはηの偶数次数だけを持つ。3次の候補は(7)のprefixとの交換子だけで、そこにbus Xが1個だけ現れる。従ってP一次、Weyl次数3、他の電子body数にある3次成分は全て零であり、残るX一次成分を(9)が尽くす。この理由はcell (6)に特有で、一般のJ1 pathの3次残差を(9)だけと置く許可にはならない。

比較代数では $Q_1+Q_2-Q_1^\dagger-Q_2^\dagger\neq0$。Q1,Q2の異なるPBW単項と、それらの随伴は打ち消し合わない。従って $\mathcal B\ell_3\neq0$ であり、full Fock CARで初めて零になるというJ1の**必要な診断条件**は通る。ただし独立性までは示さない。

Hermiticityも整合する。Tj,HjはHermitian、Kj,hはanti-Hermitian、Djと(9)はanti-Hermitianで、全てunitary積のformal logとして正しい性質を持つ。

## 5. shuffle・Lie・実pathの整合性

ここでは2次面積と3次モーメントを独立の未知数として指定していない。表に示した区分一定の実pathから、(2)、(5)、(7)を順に導いた。各力のsigned一次積分はcell全体で零となり、(8)の1次零と一致する。

演算子関係を入れる前の自由な制御letterのtensor代数で、各segmentの指数はgroup-likeであり、その積もgroup-like。従ってそのiterated-integral係数はshuffle恒等式を満たし、logは自由Lie級数となる。その後に比較代数、CAR表現へ写している。さらに(8)は、元のforceの交換子とそのhとの入れ子交換子で得た式であり、Lie条件を破る任意の連想積をlogへ挿入していない。

この存在経路による確認は、任意の望ましい係数配置が実現できるという主張より狭い。特にσを物理swap又はLie automorphismとして実装したことにはしていない。

## 6. 同じ向きの輸送では信号を失う：限定族の負の結果

比較のため、**同じ二つの完成blockを同じprefixで輸送する族だけ**を調べる。各rectangleのsigned面積を共通にt倍して作る $B_j(t)$ を用いれば、(5)の先頭は $tK_j$。これはRの一方のcouplingをt倍する実制御であり、非整数gate powerをoracleとして許しているのではない。

\[
U_{\rm same}=(VB_1(t_1)V^{-1})(VB_2(t_2)V^{-1}).
\]

full Fockの低次係数は

\[
\rho(\ell_2)=(t_1-t_2)K_1,
\qquad \rho(\ell_3)=(t_1-t_2)[h,K_1]. \tag{11}
\]

$[h,K_1]=-2D_1\otimes X\neq0$ なので、3次零化は $t_1=t_2$ を強制し、2次信号も零になる。よって非零M輸送を共通に持つこの族ではκ≠0と両立しない。これは**限定的な不成立**である。独立した輸送、別の実path、同時制御、全J1を否定しない。M輸送を全く入れない族はそもそもこの障害を持たず、既知の閉路合成である。

(6)は第二経路の面積と輸送の両方を反転するので、2次は差、3次は和となる。従って望む符号割当て自体がHermiticity又はshuffleと普遍的に矛盾する、という否定はできない。

## 7. 得たcellがJ1固有の共同原理ではない理由

必要な診断条件(9)だけで成立を認定すると、次の還元を見落とす。

まずfull FockでB1自体が完成した目標gateになる。$E=E_{pq},F=E_{rs}$ と置き、互いの随伴も含めてEとFの組は可換とする。

\[
H=EF+E^\dagger F^\dagger=H_1,\qquad
J=EF^\dagger+E^\dagger F,
\]

\[
S_{pq}S_{rs}=H+J,\qquad A_{pq}A_{rs}=-H+J.
\]

CARにより $E^2=(E^\dagger)^2=F^2=(F^\dagger)^2=0$。HJの各積項、JHの各積項はE又はF（又は随伴）の平方を含み、双方とも零。従って二つのHermitian積は可換であり、(3)–(4)から

\[
\rho(B_j)=\exp(-2i\eta^2H_j)\otimes I,
\qquad \rho$B_2^{-1}$=\rho(B_1)=:B. \tag{12}
\]

これはN=2だけの縮約ではなくfull Fockの関係である。表現を取る前の比較代数で(12)を仮定して、(9)を消したわけではない。

その結果cell全体はfull Fockで**exactに**

\[
\rho(U_J)=(VBV^{-1})(V^{-1}BV)=VBV^{-2}BV. \tag{13}
\]

ここで既知の同一gateBを逆向きに共役して二度用いる処理は、CAR交換対を入力としない汎用のechoである。一般の $B=e^{\eta^2K}$ に対して二つの3次誤差 $\pm[h,K]$ が相殺する。第二blockを最初からB1に置き換えた同じtemplateなら、比較代数でも3次は零になる。**物理的出力は同じなのに「比較代数で非零」の診断だけが変わる。**

従って本例ではCARは二つの既知gateの同一性を確かめるために使われており、その交換対が同じ未完了cellで目標生成とbus帰還の双方に不可欠な、新しいpath生成規則にはなっていない。途中でMの変位が開いているという見た目はこの還元を妨げない。実際、B1だけでも二体信号があり、B1を二度使う既知構成はbusを戻して同じ先頭信号を作る。

本例は完成gateへCAR-null identityを末尾に追加した形ではない。**それを避け、(9)を通ってもなお既知echoへ還元される**ことが、判別基準の限界を具体化している。本cellをJ1の独立した成功例として数えない。ただし、一例の還元から全てのJ1 pathの還元を結論しない。

## 8. 既知法との対応と非認定事項

| 比較対象 | 今回の具体的対応・限界 |
| --- | --- |
| 幾何学的位相／独立閉路 | 全てのRは可換電子forceの4変位閉路そのもの。Bjはその完成gateの積。[Spiller et al., v3, §IV](https://arxiv.org/html/quant-ph/0509202v3#S4)。 |
| 交換子product formula | (2)はcentralな交換子合成、(7)–(8)は通常の共役とBCH。一般的な交換子・反交換子合成は既知。[Childs–Wiebe, v2, 導入・§VII.2](https://arxiv.org/html/1211.4945v2)。同論文の補助qubitをここへ無料で移してはいない。 |
| echo／DCG | 還元(13)は本文中で直接確認した汎用の反対共役。DCGの「gateと誤差の関係を設計する」考え方とも重なる。[Khodjasteh–Viola, v2, §IV.2, Eqs. (28)–(29)](https://arxiv.org/html/0906.0525v2)。本cellをその論文のbalance-pair sequenceそのものとは認定せず、有限次元bathの保証をunbounded oscillatorへ転用しない。 |
| fermionic unitary synthesis | (4)、(12)はHermitian hopping積によるdouble-excitation gateの分解で、電子代数を先に使うというだけでは独立性を示さない。[Magoulas–Evangelista, v1, abstract](https://arxiv.org/html/2511.13485v1)はLie構造を使ったexact分解を扱う。今回、その全spin-adapted分解との一対一の包含は調べていない。 |

文献はJ1の既存registryを再利用し、上記の必要部分だけ一次本文／abstractで照合した。網羅的新規性調査、著者実装の実行、全定理の詳細科学レビューではない。今回の還元判定の直接根拠は(12)–(13)であり、「文献に関連語があるから」と判断したのではない。

## 9. 判定と、次の判断に不足しているもの

| 対象 | 今回の判定 |
| --- | --- |
| 20-pulse cell (6)の実制御への持上げ | **1～3次条件は成立**。κ=4、比較代数の全3次残余(9)がCARで零。指定Hermitian力だけを使用。 |
| このcellの独立性 | **既知法への還元**。完成した位相gateの合成と反対共役echo (13)。J1独自の共同生成原理の成立とは数えない。 |
| 共通prefixを持つ族(11) | **限定的な不成立**。3次零化が二体信号も零にする。 |
| 非還元なJ1共同cell一般 | **未解決**。今回構成できず、不可能性も示していない。正式な取り下げ・採択はしない。 |

科学計算へ進む価値をGPT／ユーザーが判断するために不足するのは、**(13)の既知templateで尽くされない、同一の未完了な目標生成cellの文法と、そこでCAR交換対が不可欠になる具体的な係数機構**である。単にQ1+Q2を含む3次式を指定したり、比較代数で非零な式を作ったりするだけでは足りない。

最小の次検証案は、まずそのような文法を一つだけ紙上で指定し、許可alphabetから実pathへ展開して、(a)全2次bus項と非零信号、(b)線形及び三次の全bus残余、(c)完成gate＋echoへの具体的還元、を同時に点検すること。これは**将来の提案で、今回実行する追加探索ではない**。その文法がないまま大規模な係数生成・solver・全H計算へ進める根拠は、本記録からは得られない。高リスク・未証明だけを理由に価値を否定した結論でもない。

本書は機械検証・別人の査読・独立UNSAT証明書ではない。共同cell全体の4次以降の残余、有限ηでのcoherent bus帰還、unbounded busの解析、一般の化学項・複素位相への被覆、物理access、費用優位、新規性は未確立。(3)、(12)の基本gateの帰還と、(6)全体の帰還を混同しない。元の固定ansatzのUNSATを変更せず、sector限定・P1*一般の不可能性にも拡張しない。

D1・D2、元電子Hamiltonianのscalar・一体作用・残りの相互作用と絶対基底エネルギー対応、full Fock主判定、既存研究のSTOP／CLOSED／PAUSED／HOLDを維持する。

**次の担当はGPT／ユーザー**：既知法への還元という今回の結果を踏まえ、非還元な文法を追加検討するか、その最小範囲を判断する。**Codexは資料公開・照合を完了してMandatory STOP**。追加科学計算、別cell探索、実装、詳細レビュー、正式採択を自動開始しない。
