# 既知法との対応、独立性の留保、保持しない方向

2026-10-17 JST。対象は[仮説J1](joint_loop_principle_hypotheses.md)。**CARの恒等式、二体作用の生成、不要作用の相殺はいずれも、それだけで新規ではない。** 本調査は一次文献の必要箇所の照合であり、網羅的な新規性証明、全定理・全実装の詳細レビューではない。文献を読んでいないことを独立性の証拠にはしない。

以前の[比較記録][previous]を再利用し、今回の機構に直接関係する原文を確認した。新たに、fermionic Hamiltonian engineering、dynamically corrected gates（DCG）、fermionic unitaryの代数的分解を追加の比較対象にした。発想と照合は文書で分離したが、発想が既知文献から完全に独立だったとは主張しない。

## 1. 一次文献との具体的比較

| ID・版固定資料／読取り範囲 | 入力・操作・出力の既知部分 | J1で残す問いと限界 |
| --- | --- | --- |
| L1 Motta et al., [1808.02625v2](https://arxiv.org/html/1808.02625v2)、Eqs. (1), (3), (5)–(6)、一体補正の説明 | 化学積分を一体補正と回転密度の積へ分解し、basis rotationと既知の時間発展を組み合わせる。 | CARのnormal-order補正や平方分解は新規としない。四添字の相互作用を選んだだけでも差分にならない。共同busの開いた経路の生成は別問題。 |
| L2 Spiller et al., [quant-ph/0509202v3](https://arxiv.org/html/quant-ph/0509202v3#S4)、§IV Eqs. (7)–(10) | 条件付きdisplacementを4回組んでbusを戻し、電子／qubit側に幾何学的位相を残す。 | commuting forceのrectangleや、その順次実装へJ1が戻れば既知構成。非可換なcross経路をCAR関係で処理する規則は、単なるbus位相とは区別する。 |
| L3 Sutherland–Srinivas, [2105.05768v1](https://arxiv.org/html/2105.05768v1)、§II.1 Eqs. (1)–(3)、Table 1の説明 | 二つの非可換spin–motion forceを同時に用い、非線形なbus作用を有効生成する。 | 非可換forceや高次bus項の生成は既知。J1ではそのbus成分を除く必要がある。論文の有効作用・残余条件を化学のcoherent帰還保証へ移さない。 |
| L4 Childs–Wiebe, [1211.4945v2](https://arxiv.org/html/1211.4945v2)、導入、§VII.2の反交換子合成（既存読取り記録も再利用） | elementary指数から高次の交換子を作り、補助qubitを使った反交換子・多体合成も扱う。 | 交換子／反交換子で目的二体作用を作るだけでは差分なし。補助qubitや多体oracleを隠してJ1のprimitiveと同一視しない。 |
| L5 Chen et al., [2111.12177v1](https://arxiv.org/html/2111.12177v1)、§I Eq. (6)、§II、再帰概要 | 係数条件から高次commutator formulaを作り、fermion hoppingの一体Lie関係にも応用する。 | 方程式をCARで小さくするだけ、又は汎用formulaのfactor代入だけなら既知。J1は一体Lie関係だけで消えない交換経路の零関係を先にcontrol生成へ使えるかを問う。 |
| L6 Bookatz–Roetteler–Wocjan, [1509.00408v2](https://arxiv.org/html/1509.00408v2)、既存§II読取り記録、今回のorthogonal array／balanced-cycle定義 | group cycle／orthogonal array等で、指定した不要作用を平均化するbounded-strength制御。 | echo／decouplingという処理自体を新規としない。有限次元local systemの条件をunbounded oscillatorへ無条件には適用しない。 |
| L7 Kum et al., [2606.17158v2](https://arxiv.org/html/2606.17158v2)、abstract、§IV.1 Eqs. (36)–(42)、§IV.2冒頭 | native fermionic Hの自由発展とlocal occupation-phase pulseを交互に用いる。局所phaseとの共役ではnumber monomialを個別に変えられないことを示し、扱える作用を整理する。 | CARに基づくcontrol生成という広い看板は既知。J1の一体factor×busだけから相互作用と帰還を共同生成する問題とは入力accessが異なる。局所phaseについてのno-goを、bus付きの全方式へ一般化しない。 |
| L8 Khodjasteh–Viola, [0906.0525v2](https://arxiv.org/html/0906.0525v2)、導入、§IV.2、特にEqs. (28)–(29) | 目標gateとidentity等の誤差を合わせるbalance pairを作り、制御cycleに組み込んでgateを補償する。 | **最も強い還元リスク。** 「信号を残し誤差を相殺」という原理は既知。J1が、既知の相互作用gateを入力にDCGを適用するだけなら保持しない。未解決なのは、CAR交換対が線形forceから同一の開いたcellを生成する規則を与えるか。 |
| L9 Magoulas–Evangelista, [2511.13485v1](https://arxiv.org/html/2511.13485v1)、abstract、本文内の限定的な語句検索 | fermionic unitaryにLie代数的構造を使い、対称性を保つexact product decompositionを構成する。 | 「電子代数を先に使う」こと自体も新規ではない。今回は全decompositionとの包含関係を監査していない。boson等の語の検索不一致を、共同bus機構の不存在の証拠にしない。 |
| L10 Zanardi–Rasetti, [quant-ph/9904011v3](https://arxiv.org/abs/quant-ph/9904011v3)、abstract | 制御Hamiltonianの縮退固有空間をadiabaticに移動させるholonomic quantum computation。 | geometric／dark-state holonomyという名称だけでは新機構にならない。CARからどの共通bus pathを作るかが未定なら、追加候補に数えない。 |

L1–L6は以前の調査を再利用した対象で、今回は記した必要箇所を読み直した。L7の版は2026-10-01のv2、L8は2009-08-13のv2、L9は2025-11-17のv1。HTMLの自動変換日を投稿・改訂日と混同しない。本文の数値実験や著者コードを実行していない。全PDF／全版差分のbyte照合は行わず、取得方法と未確認範囲をprovenanceに残す。

## 2. 独立性を判断する際の必要な区別

### 出力の新しさと生成規則の新しさ

\(H_\diamond=E_{pq}E_{rs}+\mathrm{h.c.}\) のdouble excitation、CARの反対称性、nilpotency、反交換子合成は全て既知である。J1がそれらの相互作用を初めて実装可能にする、という主張は置かない。[L1, L4, L5, L9]

比較対象は、同じHermitian一体forceとbus accessを入力に、**どの規則がpulseを生成し、どの関係で帰還を示すか**である。新しいcellが得られても、独立閉路、DCG又は既知のrepresentation-specific synthesisの具体的な特殊化と対応すれば、残る差分を再評価する。既知法でも原理的に同じunitaryを近似できるという事実だけで、全ての構成規則が同一になるわけでもない。

### 代数の商と物理的な交換操作

J1のσはannihilation側の組合せを交換する式の操作で、一般のunitary conjugationではない。従って「σでpulseを鏡映すればよい」とは言えない。CARの零関係をcontrol pathへ持ち上げる問題を省略してしまう場合、J1は構成案ではなくラベルだけになる。

### 残る独立した問い

具体的に残すのは、**同じ一体force alphabetの実pathで、2次の交換反対称な信号を保ち、3次の非零な比較代数の残余をCARの交換対の和へ送る、局所的な生成文法があるか**である。これは[仮説本文](joint_loop_principle_hypotheses.md)の条件(3)–(4)で定義した。

この問いの新規性、実現可能性、圧縮・資源効果は未確立。特にL8とL9の全構成への非還元は示していない。既報の一部が関連することだけで排除しない一方、差分が残ったという積極的な新規性認定もしない。

また、既知の目標gateへCARでidentityとなるcellを付け足すだけなら、比較代数で非零の残余を人工的に作れても共同生成原理にはならない。目標を作る開いたcellの内部でCAR関係が閉鎖に不可欠であることまで区別する。

## 3. 検討したが独立仮説として保持しない方向

以下は本探索における方向の整理であり、全制御族に対する不可能性証明ではない。「保持しない」は旧研究のCLOSED／STOPを新設・解除する操作ではない。

| 方向 | 紙上で確認できること | 保持しない理由 |
| --- | --- | --- |
| 完了した単独閉路＋Strang | 独立検証済みの12-pulse比較構成が形式4次を満たす。 | 既知の平方gateとPFの連結。P1*独立原理には数えない。 |
| 全制御の符号を反転したcopy | \(\log W(\eta)=\eta^2A+\eta^3B+O(\eta^4)\)なら \(W(-\eta)W(\eta)\) は3次が消えて先頭は\(2\eta^2A\)。 | 汎用の符号反転・compositionでCAR不要。4次残差は一般に残るので、これだけで元の形式4次整合とも言えない。 |
| microscopicな時間対称pulse | \(U(-\eta)=U(\eta)^{-1}\)となる対称性ならformal logはηの奇数次数だけで、必要なη²も消える。 | 単なるpalindromeを「3次だけを消す方法」として採用できない。閉路完成後のτ=η²でのStrang対称性とは異なる。 |
| 共通平方／Casimirを使う二factor | \(L_x=E_{pq}+E_{qp},L_y=-i(E_{pq}-E_{qp})\)ならCARより \(L_x^2=L_y^2=n_p+n_q-2n_pn_q\)。 | 非可換でも元の3次共役障害は消せるが、目標\(L_x^2+L_y^2=2L_x^2\)が単独factorの平方へ還元。二体成分があることだけでは共同性を示さない。 |
| 中間軌道の占有数でpathを選ぶ | 異なるp,q,rで \(\{S_{pq},S_{qr}\}=(1-2n_q)S_{pr}\)というCAR関係がある。 | それを汎用anticommutator synthesisで実装するだけなら既知。\(\{F,G\}=(F+G)^2-F^2-G^2\)への還元もある。占有数を制御に使うという名称だけで追加候補にしない。 |
| scalarなarea／一体Lie関係だけのpath調整 | 行列交換子やJacobi関係で条件を減らせる。 | それは既知のLie-based control／PF設計と重なる。J1には比較代数で非零だがCARで零になる関係を、生成段階に使う条件を課す。 |
| 任意のdark-state／Berry holonomy | 非可換holonomyによる制御は既知。[L10] | 多体作用とbus帰還を作る具体的なCAR由来pathが未定。純電子一体Hamiltonianの閉じたGaussian操作だけなら二体生成にはならない。busを含む新しい機構一般を否定したのではない。 |
| 占有数依存の二体bus forceを直接許す | 仮に供給すれば設計は容易になり得る。 | 元の生成したい相互作用をoracleへ移す循環。今回の一体force accessからの構成にならない。 |
| ランダム化して3次を平均零化 | 反対符号の残余が平均で消える場合がある。 | 平均channelの一致から、位相を保つcoherent bus帰還は導けない。randomized PF／noise accountingが必要で、CAR固有の制御生成規則を今回は提示していない。 |

共通平方の例は、別factorなら元の障害が無い場合があるという確認であり、元factorのUNSATを変更しない。palindromeの注意点も、全ての対称化が使えないという主張ではない。

## 4. 費用と科学的保証の未確立事項

J1の追加一体factorへのbus結合、S/Aのphase制御、shared pathの実現、初期bus準備・tail、coherent return、scalar位相、外側PFと一体作用の接続は、実装と費用の契約が未設定。原Hamiltonianの絶対E0を得るまでの資源改善は主張しない。

今回の負の方向整理も、保持1件も、科学的GOや正式採択ではない。**公開・照合後にMandatory STOP。**

[previous]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/prior_art_and_novelty_boundaries.md
