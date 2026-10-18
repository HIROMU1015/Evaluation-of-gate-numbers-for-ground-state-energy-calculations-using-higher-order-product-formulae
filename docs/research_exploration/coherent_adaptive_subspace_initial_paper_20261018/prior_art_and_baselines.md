# 一次文献と同じaccessの強対照

検索・取得日：2026-10-18 JST。方法の比較を目的とする限定調査であり、網羅priority・独立新規性・最新最良性能の認証ではない。[文献registry](literature_registry.json)に取得URL、実際に取得されたversion、HTML bytes/SHA-256、読取り範囲を記録した。HTML全文を取得できても、数値表・全supplementを科学監査したとはしない。

## 1. 入力、生成、更新、行列要素

| 方法／一次資料 | ①H・seed情報 | ②basis候補の生成 | ③選択・更新規則 | ④行列要素 |
| --- | --- | --- | --- | --- |
| QSE [L01] | 電子H、準備seed | a†a等の励起演算子をseedへ作用 | 励起階層・指定operator pool | RDM／Pauli期待値からH_ijとS_ij、一般化固有値問題 |
| QSCI [L02] | 電子係数、近似seedのZ samples | sampled determinant／計算可能な配置basis | 出現頻度等でR配置を選ぶ | 係数から古典的に全行列要素を計算 |
| SKQD [L03] | H、reference、実時間発展access | 複数Krylov stateからsampled bitstrings | sampled supportを集めて古典対角化 | 配置Hを古典計算。coherent Krylov matrixの測定とは異なる |
| QDavidson [L04] | H、reference、補正stateの準備 | Ritz残差／imaginary-time型補正 | 線形独立性を確認して拡張 | Hadamard型H/S、残差関連測定、QITE mapping |
| QJD／SBQJD [L05] | H、reference、preconditioner | 直交制約付きJD correction | projected correction equationで拡張 | H/S測定、LCU等。sample版は本文で初期reference改善に利用 |
| Quantum Krylov／PQSE [L06,L07] | H、reference、momentsまたはRTE | H^kψ等のKrylov列 | PQSEは小spaceを最低Ritz state経由で順次接続、varianceを用いる | momentsの再利用、または干渉測定。重なりと統計誤差を扱う |
| nu-VQE [L08] | H、parameterized seed、Jastrow型operator | diagonal非unitary Oψ | Oとseedの変分parameter最適化 | O†HO、O†Oの期待値。論文のlinearized形も区別する |
| VQNHE [L09] | Pauli H、seed、bitstring関数F | diagonal Fψ。複素Fも扱う | 古典関数／量子parameterを最適化 | 配置対を結ぶPauli測定回路とF(x)*F(y)の後処理、Zでnorm |
| HCI／selected CI [L10] | 古典係数、明示CI係数 | 一・二電子励起の接続配置 | \|H_ai c_i\|が閾値を超える候補等 | Slater–Condon等で古典計算 |
| TPSCI [L11] | orbital cluster、cluster states、古典係数 | 相関cluster stateのtensor products | tensor-product basisでselected CI、cluster basis改善 | cluster行列を再利用して古典計算 |
| Adaptive measurement QSE [L12] | H、固定励起pool、古典trialとseed | 指定QSE pool | Ritz係数からdressed observableを更新し測定basis分布を再設計 | biased shadows／grouping等でH/Sを推定 |
| Shadow subspace expansion（SSE）[L13] | H、seedのclassical shadows | local Pauli pool等 | {I,G_i}のenergy改善でfilter、選択poolでregularized solve | 同じshadow記録のPauli積期待値を再利用 |

## 2. 再利用、古典費、保証の境界

以下の一般的なK³ solve等は今回の会計であり、各論文の最適費用定理を輸入したものではない。

| 方法 | ⑤状態準備・測定再利用 | ⑥古典費用 | ⑦精度・Hamiltonian class・限界 |
| --- | --- | --- | --- |
| QSE | 同じseedの期待値を複数entryで共有可能 | operator展開・RDM格納・K² entries・dense solve K³ | 理想の変分性。有限shotとconditioning、元groundへの近似誤差は別 |
| QSCI | Z samplesを再選択に使用、projected observablesは古典側で評価可能 | 配置選択、接続生成、R配置のsolve・storage | noiseが選ぶsupportを変えても、正しい古典projected Hなら変分性を保つ。小Rの近似精度はseedに依存 |
| SKQD | 複数timeごとのsamplesをunion・recoveryに使う | support生成とsolve、simulation費も必要 | Theorem 1はground sparsity、初期overlap、gap／幅と成功sampling条件に依存。一般分子無条件の多項式保証ではない |
| QDavidson | 旧H/S entryを保持、新補正stateとのcross測定を追加 | QITE mappingの線形系、pool・domain、subspace solve | 残差収束の指標とground判定を分ける。補正state生成は無料でない |
| QJD | 旧basisを保持。新stateとpreconditioner／LCUの費用を払う | correction equation、分解・係数normとsolve | 局所Newton型議論を任意seedのground保証へ拡張しない。inverse・LCU成功率の取得費を別途扱う |
| Krylov／PQSE | moment table・basis生成を共有できる | moment処理、小solveの列と最終再構成 | 小spaceの分割で数値安定性を改善する設計。occupation cell分割と同一の意味ではない |
| nu-VQE | seed回路を深くせず追加observableを測る方式 | transformed operator展開、parameter探索 | 変分ansatz。追加Pauli数・sampling費はOの形に依存し、一般の小測定数保証ではない |
| VQNHE | 固定seed・固定Pauli回路のbitstringsは複数Fに後処理できる | 各sampleでF評価、関数最適化 | normと関数のoutput rangeを含む費用。任意Fを小さい総費用で最適化する保証ではない |
| HCI | 古典のintegral整列・接続list・CI係数を再利用 | 生成候補数、選択、疎solve、必要ならPT | variational CIとPT補正を区別。明示CI入力が容易な場合の必須対照 |
| TPSCI | cluster matrixと相関basisを再利用 | cluster解法・tensor contraction・選択・solve | 局所相関をbasis内に保持する強対照。tensor構造の容易な例で量子優位を認定しない |
| Adaptive QSE | 測定結果から次のbasis配分を更新 | observableのdressing、grouping、solve | 測定配分の適応は既知。新しいbasis生成則との同一性は別途対応が必要 |
| SSE | quantum記録を増やさずpool選択・matrix形成 | filter、shadow observable処理、regularization・solve | shadow norm／Pauli weightのsampling費を払う。推定energyの改善と厳密E0証明を分ける |

補助資料として[Dual-GSE](https://arxiv.org/abs/2309.14171)のabstractも確認した。expectation値再利用はそこにも現れるため、一般的な「再利用」を発明としない。HTML全文は404だった。[QSCI-CMP](https://arxiv.org/abs/2608.05766)もabstract確認に留め、chemical preselectionの既知性だけを境界に用いる。本文未取得から回路・費用定理を輸入していない。

## 3. 今回Gの具体的な還元と残る比較

| Gの部位 | 対応・判別 | 今回の分類 |
| --- | --- | --- |
| Π_aψ、一般化固有値問題 | QSEのoperatorをΠ_aへ特殊化 | 既知frameworkに包含。これだけでは候補全体を棄却しない |
| F_z(x)=z_{f(x)}によるstate表現 | nu-VQE/VQNHEのdiagonal関数classに入る | 表現上の独立差なし |
| Pauli配置対の位相を測り任意fへ再label | VQNHEの配置対測定に同じ関数classを与え、複素quadratic formをpolarizationしてJ^fを復元できる | 再利用それ自体に独立差なし。Gのancilla経路の方が高価な可能性もある |
| 小subspaceのenergy gainで候補を選ぶ | SSEの{I,G_i} filter、selected CIのenergy／perturbative選択と近接 | greedy gain一般は新規核心にしない |
| 係数graph→count predicate、g_L/C_add | 具体的な有限写像は構成した。確認した本文から同じ全手順の掲載までは特定していない | **追加証拠が必要**。未発見を独立新規性の証拠にしない。既知部品のheuristicな組合せに尽きる可能性 |
| support外へのR | operator-pool QSE、Hamiltonian-word expansion、Davidson補正に接続 | 固有の取得・費用差は構成せず、独立候補として数えない |

特にSSEは、既存データで候補を選ぶだけでなく、小spaceで改善を評価する具体手順まで持つ。前回レビューのC4をGで使うだけではここを越えない。Gは実用的改善をまだ証明していないため、この表を「独立候補が残る」という判定には用いない。

## 4. 同じtaskでの比較仕様

主対照は、**同じψ、同じH、同じdictionary D、同じε_RRと成功率**を許すVQNHE型の配置対記録＋piecewise関数／QSE solveと、適切なshadowまたはbiased測定を使ったQSEである。baselineにもGのcoefficient dictionary、記録の再利用、confidence管理を使う選択肢を与える。これで同じ手順になるなら、名称や更新順だけを差にしない。

QSCIには同じψのZ accessを与え、configuration精度が同じになるために必要なRと全古典費を数える。QSCIにGの重い干渉測定を強制しない。SKQD／QDavidson／QJDには追加のevolution・correction accessを与える場合だけその費用を加え、accessを揃えないquery数の比較を避ける。

ψがD_exp個の明示CI係数なら、Hψの接続候補を粗くO(D_exp n⁴)で生成できる場合がある。HCI等のより強いscreeningも許す。fragment構造にはTPSCI、quadratic／one-dimensionalに容易な構造には相応の古典解法を入れる。回路seedがあるだけで古典困難とも量子優位とも仮定しない。

改善があり得る費用項はcandidateごとの新測定やmembership回路であるが、主対照も再利用するため、比較差は未成立である。basis圧縮率、理想energy低下、Gram対角化だけの比較で成功としない。

## 5. 一次資料・確認箇所

- L01 McClean et al., *Hybrid Quantum-Classical Hierarchy for Mitigation of Decoherence and Determination of Excited States*: [arXiv:1603.05681v1](https://arxiv.org/html/1603.05681v1)、本文式(6)–(8)と電子QSE階層。
- L02 Kanno et al., *Quantum-Selected Configuration Interaction*: [arXiv:2302.11320v1](https://arxiv.org/html/2302.11320v1)、方法・配置選択・変分性の節。後の出版版の全差分は未監査。
- L03 Yu et al., *Quantum-Centric Algorithm for Sample-Based Krylov Diagonalization*: [arXiv:2501.09702v3](https://arxiv.org/html/2501.09702v3)、§II.1、Algorithm 1、Theorem 1とその条件。実験の新再解析なし。
- L04 Tkachenko et al., *Quantum Davidson Algorithm for Excited States*: [arXiv:2204.10741v2](https://arxiv.org/html/2204.10741v2)、§II、式(3)–(9)、QITE費の記述。
- L05 Zhang et al., *Quantum Jacobi-Davidson Method*: [arXiv:2602.01670v1](https://arxiv.org/html/2602.01670v1)、§II.1–3、correction equation、LCU、sample版の使用範囲。前回レビュー時の本文未取得は今回解消。ただし全式・費用定理の独立認証ではない。
- L06 O’Leary et al., *Partitioned Quantum Subspace Expansion*: [arXiv:2403.08868v3](https://arxiv.org/html/2403.08868v3)、§2.2とAlgorithm、既存IQAEとの比較。IQAE原論文は今回未取得で、Rの独立性を認定する根拠に使わない。
- L07 Zhang et al., *Measurement-efficient quantum Krylov subspace diagonalisation*: [arXiv:2301.13353v3](https://arxiv.org/html/2301.13353v3)、方法のmeasurement／statistical errorの節。全sample complexity定理を移植しない。
- L08 Benfenati et al., *Improved accuracy on noisy devices by non-unitary Variational Quantum Eigensolver for chemistry applications*: [arXiv:2101.09316v1](https://arxiv.org/html/2101.09316v1)、§II–III、式(3)–(9)。
- L09 Zhang et al., *Variational Quantum-Neural Hybrid Eigensolver*: [arXiv:2106.05105v1](https://arxiv.org/html/2106.05105v1)、本文式(1)–(9)、supplementのmeasurement efficiencyとcomplex function。Gとのpaired-measurement対応は今回の代数的推論。
- L10 Holmes et al., *Heat-bath Configuration Interaction*: [arXiv:1606.07453v1](https://arxiv.org/html/1606.07453v1)、deterministic heat-bathの候補生成とSCI選択規則。
- L11 Abraham and Mayhall, *Selected Configuration Interaction in a Basis of Cluster State Tensor Products*: [arXiv:2002.03107v2](https://arxiv.org/html/2002.03107v2)、cluster basis／TPSCI方法。全性能claimの検証なし。
- L12 Nakamura et al., *Adaptive measurement strategy for quantum subspace methods*: [arXiv:2311.07893v2](https://arxiv.org/html/2311.07893v2)、§IIとStep 1/2のmeasurement更新。
- L13 Boyd et al., *High-Dimensional Subspace Expansion Using Classical Shadows*: [arXiv:2406.11533v1](https://arxiv.org/html/2406.11533v1)、§III.1の2次元filter、§III.2–3のnoise／regularization。本文の保証を有限shotの厳密ground上界と読み替えない。

arXivのunversioned HTML取得が返したversionを上で固定した。2026年の出版版まで全て確認した「最新網羅review」ではない。特に新しいsubspace pruning、decision-tree後処理、統計的選択に関する全一次文献を網羅したとはしない。

## 6. Gを具体化した後の限定追加検索

検索語は `quantum subspace expansion decision tree Hamiltonian`、`variational quantum eigensolver graph partition nonunitary postprocessing`、`adaptive quantum subspace operator selection measurement cost confidence`、`quantum eigensolver diagonal decision trees`。直接一次abstractで確認した近接資料を以下へ追加した。本文／supplementまでは取得・比較していないため、以下からGへの厳密包含や費用定理を認定しない。

| 一次abstract | Gへの境界として使えること／使えないこと |
| --- | --- |
| A01 [CASH-QSE, 2609.08170](https://arxiv.org/abs/2609.08170) | occupation構造で直交した量子成分を作りclassical referenceと組み合わせる先行例。Gram測定省略やoccupation利用の語だけを差にしない。FCI-guidedな選択がabstractに明記され、Gの合法accessに無費用移植しない |
| A02 [Resource-efficient energy-based operator selection, 2606.04786](https://arxiv.org/abs/2606.04786) | energy landscapeによるoperator選択と費用削減も既知の具体課題。Gと同じpredicate更新であるとは確認していない |
| A03 [Shot-Efficient ADAPT-VQE, 2507.16879](https://arxiv.org/abs/2507.16879) | Pauli結果再利用とvarianceに応じた配分の組も先行する。再利用＋費用配分という語の組だけに新規性を与えない |
| A04 [Graph Neural Networks for Fast Operator Selection, 2606.08794](https://arxiv.org/abs/2606.08794) | interaction graphとstate-dependent情報による候補選択が先行。訓練dataはexact simulationsと記載され、Gの係数だけの辞書と同一accessではない。学習・教師data取得を対照から無料にしない |
| A05 [AIM-ADAPT-VQE, 2212.09719](https://arxiv.org/abs/2212.09719) | informationally complete測定をoperator poolの選択に再利用する具体先行例。Gのrecordが特別であるとはしない |
| A06 [Towards Interpretability of Neural Quantum States, 2508.14152](https://arxiv.org/abs/2508.14152) | Boolean/Fourier構造による量子state表現の分析。tree／相関次数の語だけで新表現としない。Gの係数生成・測定・更新まで同じという判断は本文未比較のためしない |

この限定検索でもGの全graph/count/confidence/cost手順の一致を特定したわけではない。しかし、それは「独立候補が残る」ことの証拠ではない。全近接文献の詳細科学レビューへ無制限に広げず、今回の技術分類を追加証拠必要に固定する。
