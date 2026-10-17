# 既知法との入力・操作・出力の対応

2026-10-17 JST。今回の新規性判断を「関連する既知法がある」という理由だけで行わず、
具体的なgeneratorと生成規則まで対応させる。
**操作仕様Aは既知HMEの機能とCG/Paldus＋phaseへ還元され、最終の新操作設計課題は0件。**

## 1. 実際に比較した一次文献

固定版、取得bytes・SHA-256、成功／失敗、読取り範囲は[source_registry.json](source_registry.json)。
取得した全文と、必要箇所だけを読んだことを区別する。全証明・全出版版差分の独立科学レビューは行っていない。

| ID | 一次資料・固定版 | 今回の読取り範囲と比較に使う事実 |
|---|---|---|
| L01 | Mottaら, [Low Rank Representations for Quantum Simulation of Electronic Structure, 1808.02625v2](https://arxiv.org/html/1808.02625v2) | 本文Eqs. (1), (3), (6)–(8)周辺。二体積分の低rank表示、一体補正、basis rotationと既知PF。二電子係数補助状態の衝突とは異なる強い実装baseline |
| L02 | Kimmelら, [Hamiltonian Simulation with Optimal Sample Complexity, 1608.00281v1](https://arxiv.org/html/1608.00281v1) | DME／partial SWAP、Theorem 1、Appendix C Theorem 20のcontrolled版。copiesとして供給される密度行列の空間と係数・正規化を区別する |
| L03 | Weiら, [Realizing Non-Physical Actions through Hermitian-Preserving Map Exponentiation, 2308.07956v1](https://arxiv.org/html/2308.07956v1) | HMEのTheorem 1、joint generatorのChoi partial transpose、sample／controlに関するstatementの必要箇所。Aのfirst-order機能はこの枠組みの特殊化 |
| L03-P | [npj Quantum Information掲載版、10.1038/s41534-024-00949-z](https://www.nature.com/articles/s41534-024-00949-z) | web toolでTheorems 1–2、Corollary 1、Code availabilityを確認。独立HTTP取得はcookie/browserのinterstitialとなり、掲載本文のraw bytesを取得済みとはしない。式のbyte provenanceはL03の版固定arXivを使う |
| L04 | Bacon–Chuang–Harrow, [The Quantum Schur Transform: I. Efficient Qudit Circuits, quant-ph/0601001v1](https://arxiv.org/html/quant-ph/0601001v1) | §IV.1のCG入出力、§IV.2／§Vの再帰の説明。total-spin／representation labelへcoherentに写して戻す基礎操作は既知 |
| L05 | Burkat–Fitzpatrick, [The Quantum Paldus Transform: Efficient Circuits with Applications, 2506.09151v2](https://arxiv.org/pdf/2506.09151v2) | abstract、導入、§IIIのoccupation→N,S,M／GT labelとCG構成の説明（PDF内の該当節）。仮想up/down speciesのFock空間へ既知の変換を適用できるという比較。全resource table・appendixの監査ではない |
| L06 | Baker–Saxena–Kyaw, [Efficient Quantum Circuits for Coherent Conversion Between General First- and Second-Quantized Many-Body Representations, 2606.25029v1](https://arxiv.org/html/2606.25029v1) | abstract、§II.2のladder／occupation規約、conversion algorithmの入出力に関する説明。符号化変換そのものを新しい操作原理と数えない。full conversion theoremの独立証明監査はしていない |
| L07 | Childs–Wiebe, [Product Formulas for Exponentials of Commutators, 1211.4945v2](https://arxiv.org/html/1211.4945v2) | §VII.Bの補助系によるanticommutator／powers合成の説明。pair交換の式を既知commutator合成へ渡すだけでは独立生成則としない |

L03-Pの掲載版著者・題名とarXiv v1の違いはそのまま区別する。全数学的差分を同一と認定していない。
L06については現行abstractのsubmission historyも読み、今回使用したv1のidentityを確認した。
同論文の一般統計sectorに対するconversionはcanonical GT／Young–Yamanouchi labelの入力promiseを伴う。
これを任意のmultiplicity情報を消せる変換として引用せず、今回の衝突還元には直接CG/Paldusを使い、必要なmultiplicityを保持する。
HTML表示の生成日を論文versionの提出日とはしない。

## 2. 機能の還元と、実際の衝突の還元

| 比較軸 | 同じものとして示せる対応 | この比較からは示さないこと |
|---|---|---|
| DMEの作用対象 | N=2では\(J_2=\mathrm{SWAP}\)で普通のDMEへ還元 | 普通の一回SWAPを抽出imageへ圧縮しただけでN>2もunitaryになること |
| HMEの入力と出力 | \(\mathcal N(X)=\Gamma_N(X)/\binom N2\)、入力は二電子係数状態\(\rho_2\)、出力のtarget generatorは\(\mathcal N(\rho_2)\)。Aのjoint generatorはそのChoi partial transpose | HMEを新原理として再提案すること、copies準備やjoint evolutionが無料であること |
| 衝突の生成 | 二speciesのexchange \(K_1\)で\(J_N=(K_1^2+NK_1-2NI)/(4\binom N2)\)。\(K_1=N-S^2+m(m-1)\)なのでtotal-spin labelに応じた既知phaseで生成 | 一般の二体化学HがCGだけで対角化できること。ここで対角化したのは**係数非依存の補助衝突**だけ |
| phaseと逆写像 | pair labelの符号化→fermion ordering→CG/Paldus→3種類のphase→逆変換という入出力規則 | uncontrolled channelが同じならcontrolled版のscalarを捨ててよいという結論 |
| 誤差と費用 | 元interaction時間\(\tau\)に対しcollisionの総角度\(t=\binom N2\operatorname{Tr}(V)\tau\)。copy消費・準備・finite-step誤差は残る | 既知DF/PFより安いこと、一般sample下界が構造既知Vのgate下界であること |

二speciesによる多項式の対応は、今回の紙上整理である。
L04/L05に本書の\(J_N\)式がそのまま載っているという帰属はしない。
既知CG/Paldusがtotal-spin labelを生成することと、本書の(9)–(11)を合わせて、**今回の操作仕様全体の生成を既知構成へ対応付けた**。
新たな化学係数の固有値を入力した還元ではない。

一般の化学Vは補助状態\(\rho_2\)へ入り、衝突後に消費される。
このため、NAの任意のinertia tensorに対するrotor expと異なる。
NAの不足oracleを「全spin」と名称変更して再開したのではなく、今回はVに依存しないjoint generatorを対象にし、具体的な既知還元を確認した。

## 3. 公開実装で確認できたものと取得限界

OpenFermion snapshot **90074a3093f8e79f8432fb47103527d22e1cb609** の2ファイルをread-onlyで取得し、
GitHub treeのblob、raw bytes、SHA-256を確認した。origin/result commitはfileごとの最終変更commitを別fieldに保存し、snapshotと統合しない。
import、関数実行、test、Hamiltonian生成、state準備、回路build／compileは0件。

| ID | 固定公開source | 確認箇所・比較対象 |
|---|---|---|
| C01 | [low_rank.py](https://github.com/quantumlib/OpenFermion/blob/90074a3093f8e79f8432fb47103527d22e1cb609/src/openfermion/circuits/low_rank.py) | `low_rank_two_body_decomposition`と`prepare_one_body_squared_evolution`。一体補正、reality／symmetry条件、平方のbasis／density-density表示。Aのcollisionとは違う既知生成経路 |
| C02 | [slater_determinants.py](https://github.com/quantumlib/OpenFermion/blob/90074a3093f8e79f8432fb47103527d22e1cb609/src/openfermion/circuits/slater_determinants.py) | Slater determinantの準備がorthonormal rowsとGivens decompositionを入力にすること。一般に相関した二電子係数状態の準備を同じ入力価格にしない |

HME掲載版はコードをreasonable requestで利用可能とする。今回は著者への連絡を行わず、その実装を取得・実行していない。[L03-P]
Paldus論文の本文回路・label仕様は読んだが、著者の公開実装repositoryを本調査では固定取得していない。
実装未取得を、新しい原理の必要性や世界での不存在の証拠にはしない。

本repositoryの`component_sector_pf.py`も静的に確認し、既存の小成分参照・対角化と、量子回路生成を区別した。[S10]
`chemistry_hamiltonian.py`のexact eigensolverを運用入力に流用していない。[S11]
CC/TDCCの公開sourceについては前回固定資料の還元記録だけを参照し、今回は追加調査・実行していない。[S01, S02]

## 4. 既存系列との境界

- **P1* J1**：oscillator X/P、共同閉路、pulse word、CAR相殺の追加探索は行っていない。正式PAUSEを維持する。[S03]
- **P2**：配置graphの小cell／label選択は既知。Aは係数非依存のjoint generatorのweight blockだったが、結局CG/Paldusの既知構成へ戻る。P2のsolverやcatalogを再開しない。[S04]
- **P3、H-E1、M、SOS-PF**：PF errorの補正式・次数・PSD分割を設計していない。HMEを使うために元Hを勝手にPSD化・shiftする作業もしていない。
- **P4、P6、P8、H2/H4、X2**：Hamiltonian経路、零期待値制約、clock、ground copiesを使う読出しへ移していない。
- **P7、X1、N1/H3**：PF誤差をsyndromeへ移すliftやencoded representativeの探索はしていない。標準符号化・Paldusを新原理とも数えない。
- **NA/NB**：全H rotorの生成や、未知振幅のlog／chart輸送の追加検討はしていない。今回の入力は係数が既知の二電子補助状態である。
- **第一／第二研究、PR Track A/B**：既存scope、受理／未採用、source、grant、STOP・PAUSEを維持する。保存値の再集計や新しいlaw・selector・resource比較はない。[S07–S09, R01–R05]

## 5. 不保持の理由と、残る未解決事項

不保持の理由は、未証明・高リスク・資源不足ではない。
具体化した衝突の生成が、既知CG/Paldus＋phaseで説明できたためである。
新しいprimitiveを要求せず、input、mode ordering、total-spin label、phase、inverseまで対応を記述できた。

一方、以下は今回解決していない。

- 完全に同一のchemistry end-to-end protocolが過去文献にあるかという網羅的な新規性調査。
- 二電子係数状態の効率的準備、変換gate列、control／routing／synthesisを含む資源価値。
- 元Hへの接続、state準備・overlap・位相窓・成功確率を含む絶対E0取得の全費用。
- 今回の短いCAR対応の独立した他者確認。科学実装やnumerical testによる再現はしていない。

これらの未完了事項を、それだけで新操作の設計課題として保持しない。
数学的対応の確認が必要なら、[操作仕様 §8](operation_design_task.md)の小例で符号とphaseを先に確認する案はあるが、
公開後に詳細レビュー・実装・追加探索を自動開始しない。

[L03-P]: https://www.nature.com/articles/s41534-024-00949-z
[S01]: ../independent_construction_principles_20261017/research_hypothesis_handoff.md
[S02]: ../independent_construction_principles_20261017/prior_art_and_not_retained.md
[S01, S02]: source_registry.json
[S03]: ../p1star_j1_pause_decision_20261017/research_decision_record.md
[S04]: ../cross_domain_mechanism_ideation_20261016/principle_ideation_map.md
[S07–S09, R01–R05]: source_registry.json
[S10]: ../../../src/trotterlib/component_sector_pf.py
[S11]: ../../../src/trotterlib/chemistry_hamiltonian.py
