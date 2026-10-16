# P1* 最小記号的成立性検証：実行前契約草案

2026-10-17 JST。契約識別子：**P1STAR-A-v1**。状態：**DRAFT / PHASE_A_DOCUMENTATION_ONLY / PHASE_B_NOT_AUTHORIZED**。

**今回は入力・単一ansatz・判定方法・予算の案だけを固定する。係数生成、CAR正規形計算、方程式生成・求解、symbolic checker作成・実行、証明は0件。** 以下の式・factor行列・segment順序は提案する入力仕様であり、計算結果・解いたpulse・検証済みの生成規則ではない。

## 1. 目的、正本、承認境界

P1*はB分類の未検証・高リスク構成仮説であり、新原理の存在、既知法との独立性、有限時間の正しさ、資源優位は未確立。正式採択はない。正本は固定commit **67d9e3b938b8a03120b836a1c32283b7c9e9a1f0** の[principle_ideation_map.mdのP1*節][S2]。同commitの[handoff][S1]、[既報比較][S3]、[provenance][S4]を併読した。

問いは、非可換な二つのHermitian一体電子factorを共通busへ結合し、CARの関係を**制御パラメータの選択に用いて**必要な電子二体作用とbus帰還を両立する共同閉路を作れるか、である。単独factorの閉路の連結、一般的な交換子合成、CARによる事後の式の簡約だけを成功とはしない。

元の表現

\[
H_{\rm orig}=cI+T+\sum_{\ell=1}^{r}\lambda_\ell L_\ell^2+R,\qquad
L_\ell=\sum_{pq}(\ell_\ell)_{pq}a_p^\dagger a_q=L_\ell^\dagger
\]

を変更しない。今回提案する局所テストは、そのうち二factorの生成機構だけを模す。元Hのc,T,Rを0と認定したり、分子係数を生成・置換したりするものではない。D1（block-encoding／qubitization中心へ移行しない）とD2（元電子Hの絶対E0との対応を維持）を保持する。

ユーザー指示の**Phase Aだけが今回承認済み**。本草案を公開しても実行承認にならない。実行対象の変更、原理の正式採択、詳細科学レビューはユーザー／GPTの判断事項である。

## 2. A1：最小電子演算子系の固定候補

### 2.1 入力として提案する因子

4つのfermionic modesを1,2,3,4と番号付けし、以下を一つの固定候補として提案する。

\[
\ell_1=
\begin{pmatrix}
1&0&0&0\\
0&-1&0&0\\
0&0&2&0\\
0&0&0&-2
\end{pmatrix},\qquad
\ell_2=
\begin{pmatrix}
0&1&0&0\\
1&0&1&0\\
0&1&0&1\\
0&0&1&0
\end{pmatrix},\qquad
L_j=d\Gamma(\ell_j).
\]

これは**選定のための行列計算から得たものではない**。異なる対角重みと、それらを結ぶ実対称hoppingという構造を選んだ入力案である。未知係数のfit、分子Hamiltonian、別行列の候補探索はない。実対称な一体行列を指定することでHermitian factorを定義するが、具体的な交換子、平方、正規形、sector行列は今回生成しない。

局所テストの重みは固定した正規化として **λ1=λ2=1** を提案し、目標を

\[
K=L_1^2+L_2^2
\]

と定義する。Kのnormal orderingや二体成分は未計算。単位重みはこの記号的テストの仕様であり、元の化学factorのλが単位であるという主張ではない。別の比率を結果後に試さない。

### 2.2 full Fock空間とsectorの役割

- full Fock空間は4 modesの全粒子数を含む空間とする。**主たる係数同値判定はfull Fock空間**で行う。
- 粒子数 **N=2** のsectorを、目標二体作用が一体作用へ退化しないことの識別用に指定する。追加のspin／点群sectorは課さない。
- 4 modes・N=2を最小検証案とする理由は、単電子／単正孔の縮約だけで一体・二体の差を失う設定を避け、占有と空孔の双方に複数modeを残すためである。一般的な最小性定理や、この具体例の非退化を証明したものではない。
- N=2で高体作用が消えることを、full FockでCAR恒等式が成立したことと混同しない。主判定が失敗しても、N=2だけへ判定領域を切り替えて救済しない。

このfull Fock主判定は、元のsector限定目標より強い保守的な提案である。成功すれば同sectorにも適用できるが、不成立からsector限定の全構成を否定できない。この選択の科学的採否は未承認として残す。

### 2.3 Phase B冒頭で必要になる適格性gate

別途承認後の**同じ1条件集合の入力確認**として、以下をexactに確認する仕様を提案する。今回は結果を認定しない。

1. L1,L2の交換子がfull FockとN=2の双方で非零であること。
2. Kがfull Fockでscalar＋一体演算子だけではなく、N=2に制限してもscalarと全一体演算子の線形spanへ収まらないこと。
3. 片方のfactor又は目標相互作用が消えるような退化でないこと。

非可換性・二体非自明性を入力の要請として置き、未計算を検証済みと表現しない。gateが不成立／未確定なら、この入力案でP1*を識別できないため **INCONCLUSIVEで停止**する。mode、factor、sector、重みを変更しない。

## 3. A2：許可primitiveと物理access

ℏ=1、電子とbusの演算子は異なるtensor factorに作用するとする。busは共通の1 oscillatorで、

\[
[X_b,P_b]=iI_b
\]

というCCRを用いる。fermion CARは

\[
\{a_p,a_q^\dagger\}=\delta_{pq}I,\qquad
\{a_p,a_q\}=\{a_p^\dagger,a_q^\dagger\}=0
\]

として別に扱う。これらは採用する既知の定義であり、新しい交換子計算ではない。

| 記号 | この契約で仮定する形式操作 | 物理実装についての状態 |
| --- | --- | --- |
| A | L1⊗Xbのsigned evolution | coupling生成・精度・費用は未確認 |
| B | L1⊗Pbのsigned evolution | X/P切替・位相制御を含め未確認 |
| C | L2⊗Xbのsigned evolution | 異なる電子frameのcouplingは未確認 |
| D | L2⊗Pbのsigned evolution | 同上。無料oracleとはしない |
| 符号反転 | 同じgeneratorの実振幅の符号を反転 | negative timeとはせず、coupling符号の実現が必要 |
| bus quadrature位相 | X/Pの位相frameを切り替えるaccess | primitiveの物理契約。独立した追加pulseや未知の帰還操作を挿入しない |
| 電子一体制御 | **今回の固定wordには追加しない** | 将来必要となっても自動追加しない |

今回の局所テストでは **H_known(s)=0** と置く。これは元HのT等を消すことではなく、制御側に未指定のcounterterm、電子二体oracle、resolvent、postselection、追加bus、補助qubitを入れないための限定である。

形式primitiveを使えるという条件付き検証と、それを物理的に実装できるという主張を分離する。電子basis rotation、bus準備・tail、bandwidth、phase、control、読出しの費用は今回評価しない。bus付きHamiltonianのground energyを元E0の代わりにしない。

## 4. A3：単一の有限segment ansatz

**一つの固定12 segment wordだけ**を提案する。固定順序は時間の早い順に

\[
(G_1,\ldots,G_{12})=
(A,B,C,D,A,C,B,D,A,D,B,C)
\]

とする。自由パラメータは実数 **x1,…,x12**、各xjは **−1≤xj≤1**。このboxも提案する固定制御族の一部であり、失敗後に拡張しない。各primitiveを同じ回数訪れる短いinterleavingを仕様として選んだ。解の存在や独立性を計算して選んだwordではない。

物理時間では各segmentを正の共通時間Δとし、segment jのHamiltonianを **g xj Gj** と定義する。g>0は共通のcoupling尺度。dimensionlessな形式展開変数を **η=gΔ** とする。xj<0は正時間内のcoupling符号反転、xj=0はidentity segmentである。ηに依存するxj、追加の待機時間、独立なduration、frequency、補正pulseは導入しない。

\[
U_j(\eta)=\exp(-i\eta x_jG_j),\qquad
U(\eta)=U_{12}(\eta)\cdots U_1(\eta).
\]

目標propagatorとformal logは、**達成した式ではなく照合する入力**として

\[
U_{\rm target}(\eta)=
\exp[-i\eta^2K\otimes I_b],\qquad
\log U(\eta)\equiv-i\eta^2K\otimes I_b
\pmod{\eta^5}
\]

と定義する。展開はηの**total degree 4まで**。目標の模擬時間尺度はこの正規化でη²、実際の制御時間は12Δであり、両者を同一視しない。元化学Hの物理時間への換算は対象外。

### 選定理由と閉鎖条件

有限segmentは、許すprimitive、順序、自由度、終了点を明確に固定し、既知の独立閉路への還元を追跡するために選ぶ。正本にある有限Fourierは構成例であり、今回のユーザー指示が許す有限segment方式へ契約を具体化した。Fourier族や他wordを並行提案・探索しない。

閉鎖条件は「全segmentの平均forceが0」という一条件にしない。主条件は上のformal-log一致であり、bus変位だけでなく、busに非自明に作用する全成分を4次まで除去する。これは有限次数の形式条件で、有限ηのcoherent returnの保証ではない。

**この節は入力の文法だけである。新しいMagnus係数、BCH展開、閉鎖方程式、係数表、解、pulse波形・回路図は作っていない。**

## 5. 展開・同値判定の規約案

Phase Bが承認された場合だけ、既知のMagnus／Lie-word又は同値なformal-log手続きをこの固定wordに適用する。

1. ηの次数、bus polynomialの次数、電子body数を別のgradeとして保持する。η⁴の打切りをbusのFock打切りとしない。
2. 電子operatorはCARだけでnormal orderへ直す。creation indexを昇順、annihilation indexを降順にする規約を固定し、縮約・重複index・符号を記録する。具体的normal formの生成はPhase Bに属する。
3. bus側はCCRを使うWeyl対称順序を比較basisとして提案する。電子CARとbus CCRを相互に代用せず、異なるtensor factorだけを可換とする。
4. 電子のscalar、一体、二体、三体以上と、bus identity／非identityを分けて判定する。full Fockで整理した後にN=2へ制限する。
5. full FockのCAR恒等式、選んだ数値一体factor固有の関係、N=2だけの関係を別タグにする。後二者を普遍的CAR関係と呼ばない。
6. 正規形を得る前のLie-wordの由来と、どの関係で同じ電子成分をまとめたかを保持する。genericな自由電子代数に対する別の係数条件集合を作って再求解することはしない。
7. oscillatorを有限行列へ切ってCCRを近似しない。exact state、Fock cutoff、numerical dynamics、expectation値による零判定を使わない。

logはη=0近傍の**formal series**として定義する。unbounded bus全空間でのnorm収束、tail、有限時間のbranchは証明しない。恒等式mod η⁵を数値error bound又はcoherent-control保証へ昇格させない。

## 6. A4：事前判定条件

| 識別する条件 | 将来満たすべきこと | 成功としない例 |
| --- | --- | --- |
| 電子二体作用 | 適格性gateを満たしたK全体とη²のpure-electronic作用が一致する | scalar又は一体だけを残す、Kの二体部分だけを合わせて他を無視 |
| bus変位 | η¹〜η⁴に現れるX/P一次作用を含め、不要成分が0 | 一次平均forceだけの相殺、bus期待値だけの相殺 |
| bus高次作用 | 同範囲でsqueezing・占有依存・混合polynomial等の全bus非identity成分が0 | 初期vacuum上の見かけの相殺、部分trace後channelだけの一致 |
| 電子高体作用 | full Fockで、目標Kに含まれない三体以上の残余が0 | N=2では消えるからfull Fockの高体残余を省く |
| scalar・一体 | K自身に含まれる成分と、目標からの差を明示。残差は0を要求 | 無料counterterm、未知のglobal phase、後付けの一体補正 |
| CARによる共同性 | 関係の出所を示し、**CARを使ったパラメータ選択の局所的な規則**を説明できる | solverが出した値をCARで後処理するだけ、interleavingという見た目だけ |

Kをsquareとして指定したまま、scalar・一体成分も含めて一致させる。normal ordering由来の一体作用を勝手に捨てない。今回は追加cleanup primitiveを許さないため、目標との差に一体／scalar driftが残れば、この契約の達成とはしない。補正を追加して救う場合は別契約になる。

formal-log一致が得られても、共同閉路の独立性は別gateである。全ての非零segmentが実質的に一方のfactorへ落ちる場合、二つの独立factor閉路へ分解できる場合、既知の一般交換子合成を記号だけ変えた場合は新原理の候補としない。

## 7. A5：同じprimitiveでの既知baselineと還元screen

| 比較対象 | この契約で比較する範囲 | 追加してはいけないもの |
| --- | --- | --- |
| Density-square＋独立閉路 | A/Bだけの既知rectangle閉路と、C/Dだけの既知rectangle閉路を順に行う構成。[L01] [L02] | exactなexp(K)を入力oracleにすること |
| 幾何学bus gate | 同じfactorのX/P displacementでbusを戻す既知機構。[L02] | 異なる電子factorが可換と仮定すること |
| 交換子product formula | A〜Dのelementary指数へそのまま適用できる既知の交換子合成・和との組合せ。[L12] [L13] | L12の補助qubit版等、今回のprimitive外のaccessを混ぜること |
| Decoupling／refocusing | 許す符号・quadrature切替だけで表現できる既知の平均化・refocusing。[L03] [L14] | 未許可のspin rotations、第二bus、無限強度pulse |
| 一般的制御最適化 | 固定wordの条件を一般solverへ渡すという既知の方法との違い | 数値fit・多seed最適化を新しい生成原理とすること |

これは**既知構成への静的な対応表**であり、第二の探索ansatzではない。独立閉路baselineは、非可換な二factorの合成ではそのままexp(K)に一致すると仮定しない。外側PFの誤差や交換子も別に扱う必要がある。同じ形式次数・振幅box・primitiveで、何に還元されたかを判別する用途に限定し、gate数・費用・勝率をbenchmarkしない。

将来の有界な還元screenは、固定wordについて以下を調べる仕様とする。

- 隣接同一generatorの合成、正逆相殺、**正当な可換性が確認された場合だけ**の並替え。
- 既知のsingle-factor閉路へまとめられる部分と、その単なる連結への退化。
- L12/L13の既知formulaへ同じprimitiveを代入しただけという具体的対応。
- 係数の選択に使った関係の由来。CARの利用と、factor固有・sector固有の簡約を区別する。

非可換wordの任意の順序変更、cyclic permutation、global conjugationを自動的な同一作用とはしない。形式的に見つかった1解についてscreenする範囲で、全factorizationの探索や新しい独立性定理を作らない。有限screenで還元が見つからないことも、新規性の証明ではない。

既知の非可換forceでは残留bus作用が起こり得る。[L03] [L04] また、一般的な高次交換子合成と係数条件の求解は既報である。[L12] [L13] したがって係数整合だけでは、CARから新しい共同閉路生成規則が得られたとは判定しない。

## 8. Phase Bで必要となる計算と実行上限の提案

**以下の手順・予算は未承認。ジョブ、checker、科学コード、係数表を今回作成しない。**

| 順序 | 別途承認後の単一runで行う内容 | 停止条件 |
| --- | --- | --- |
| 1 | 固定factorとKの適格性gate、入力・版・hashを確認 | gate不成立／未確定はINCONCLUSIVE |
| 2 | 固定12 wordのlogをη⁴まで生成し、CAR／CCRで整理 | 次数・正規形・予算の不足はINCONCLUSIVE |
| 3 | full Fockで目標一致・bus零化・残余零化の**一つの係数条件集合**を作る | 別sector又は別ansatzの条件を追加しない |
| 4 | その集合と固定boxをexact arithmeticで整合性検査する | 最初のexact整合例、exact不整合認定、又は予算上限で終了 |
| 5 | 整合例があれば同じ式へexact代入し、限定した既知法還元screenとCAR選択規則の説明を行う | 別解・別parameter族の自動探索を続けない |
| 6 | 許可された4分類の一つと限界を記録 | **Mandatory STOP** |

提案予算は **1条件集合・1 job・1 CPU process・16 GiB RAM・wall time 30分**。exact operator／polynomialの展開中間項は**保存されたterm総数20万**を上限候補とし、出力はtext／metadata合計20 MiB以内。これは計算量の実測値・必要資源の見積り結果ではなく、runを有限にする技術上限案である。wall timeは入力gateから還元screen・報告までの全体に課し、段階ごとにリセットしない。

有理数とiを係数domainとして開始し、解はexact rational又はexact real-algebraic representationで扱う。数値探索、random seed、近似根の許容閾値、fitは提案しない。全12実パラメータのboxを扱えないbackendでは、勝手に有理数だけの不存在へ一般化しない。

整合例はexact代入で確認された1例又は1つのコンパクトな同時返却familyまでとし、その先の探索はしない。**NO_SOLUTION**には固定box内の全実パラメータを対象としたexactな不整合根拠が必要。rootが見つからない、timeout、途中の式膨張、Groebner basisだけで実数可否を閉じられない等はINCONCLUSIVEとする。

具体的なexact algebra backend・version・決定的な実行経路は今回未設定。将来承認時に、この同じ契約の計算を実施できる環境とchecker作成範囲を明示してbindする必要がある。未設定のまま実行せず、欠落を埋めるための科学コードも今回作らない。

memory・time・term上限で終了した後に、再起動、予算増、次数削減、parameter固定、別順序・別factor・別sectorへの再試行をしない。継続には結果と変更理由を示した別承認が必要である。

## 9. Phase Bの結果分類案

| 分類 | 必要な根拠 | 含意しないこと |
| --- | --- | --- |
| NONTRIVIAL_FORMAL_CANDIDATE | 適格性gate、固定4次のexact整合例、限定screenで既知への明白な退化なし、CARを制御選択へ使う局所的説明が揃う | 有限時間の正しさ、新規性、汎用生成規則、資源優位、正式採択 |
| KNOWN_CONSTRUCTION_ONLY | 見つかった構成が独立閉路又は既知交換子合成等へ帰着する具体的対応を示せる | 固定ansatzの他の全解も既知だという主張 |
| NO_SOLUTION_IN_FIXED_ANSATZ | gateを満たす入力に対し、このword・η⁴・box・full Fock条件のexact不整合が閉じる | 全mode、全sector、全制御族での不可能性 |
| INCONCLUSIVE | 入力gate、正規形、算術、実数可否、予算、還元screen又はCAR選択規則の説明が不足 | 不成立、低価値、科学的STOP又は正式GO |

operator条件に解があっても共同性を説明できなければINCONCLUSIVEとし、単なる解発見をNONTRIVIALへ格上げしない。KNOWN_CONSTRUCTION_ONLYは**今回得た構成**の分類で、別の解の不存在は含めない。現時点では4分類のどれも実行結果として付与していない。

## 10. 未解決の科学的・技術的判断

1. 4-mode・N=2識別用／full Fock主判定という、元のsector目標より強い契約が最初の検証として適切か。
2. 指定した二factorが非可換性・二体非自明性のgateを満たすか。今回は未確認であり、結果で入力を差し替えない。
3. 12 segment・4次・振幅box・単位重みの固定族を一度検査する価値があるか。可解性も必要十分な自由度も未確立。
4. 同じ1条件集合から、事後simplifyを越えるCAR依存の制御選択規則を説明できるか。できない場合にINCONCLUSIVEとする厳しさが適切か。
5. exact backend・version・単一runの実装範囲と提案予算を、将来どのように承認へbindするか。

これらは契約草案の採否・将来承認事項であり、詳細科学レビューを開始する依頼ではない。資料作成を理由に追加計算へ進まない。

## 11. 保全・公開・停止位置

U1-AR（C1完結・STOP）、U3/H05（E4完結・STOP）、U4（C4完結・STOP）、T1-D撤回、第一研究S0〜S4完了・S4否定結果、第二研究Direction Cの既存scope、FS-R1 Phase B未承認、PR Track A/Bの独立した状態・契約、PR H1〜H4 PAUSED、その他STOP・HOLD・CLOSED・NOT_ADOPTEDを維持する。[S1] [S5] [S6]

既存SOURCE、raw results、protocol、authorization、grant、ledger、manifest、STOP markerを変更しない。P1*を既存研究の成果へ統合しない。元workspaceと他worktreeのdirty／staged／untrackedを保存し、PRへの操作はread-onlyとする。保全照合の範囲と限界は[provenance.json](provenance.json)に記録する。

Repository：**HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae**。新規branch：**qc-p1star-symbolic-preflight-20261017**。base：**67d9e3b938b8a03120b836a1c32283b7c9e9a1f0**。

新規資料は本書とprovenance.jsonの**2件だけ**。読む順序は本書→provenance→必要に応じて正本[S2]と既報比較[S3]。origin/result commitとverified snapshot commitを分け、manifestはprovenance自身を自己除外する。公開後の最終commit、remote SHA、両ファイルのbyte・Git blob・SHA-256照合は最終報告と独立したlocal receiptに記録し、公開前provenanceを書き換えない。

**今回のscience実行は0件。Phase Bは未承認・未実施。Mandatory STOP：この契約案2資料をcommit・通常push・独立照合したら停止する。別途明示承認まで係数生成・CAR計算・求解・checker作成実行・新証明・simulation・compile・最適化・benchmark・詳細レビュー・正式採択に進まない。**

[S1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/research_hypothesis_handoff.md
[S2]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/principle_ideation_map.md
[S3]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/prior_art_and_novelty_boundaries.md
[S4]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/provenance.json
[S5]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/research_decision_handoff.md
[S6]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_state_transition.md
[L01]: https://arxiv.org/abs/1808.02625v2
[L02]: https://arxiv.org/abs/quant-ph/0509202v3
[L03]: https://arxiv.org/abs/1110.1870v2
[L04]: https://arxiv.org/abs/2105.05768v1
[L12]: https://arxiv.org/abs/1211.4945v2
[L13]: https://arxiv.org/abs/2111.12177v1
[L14]: https://arxiv.org/abs/1509.00408v2
