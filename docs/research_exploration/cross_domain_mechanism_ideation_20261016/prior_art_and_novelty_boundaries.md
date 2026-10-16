# 既知研究との具体的対応と新規性の境界

本書はPhase Bの限定照合である。発想8件は[Phase A](principle_ideation_map.md)に分離した。**P1*のB分類は、独立した発明・新規性・正しさの認定ではない。** 取得した一次文献の必要箇所と公式公開sourceを比較し、証明の再審査、回路生成、著者実験の再現は行っていない。

## 調査資料と読取り範囲

既存の25論文調査と前回探索のregistryを再利用し、広い調査をやり直していない。L01は以前の版固定PDF／textを再利用して必要箇所を読み直した。追加取得はP1の直接対照、P2/P6の還元確認に限定。版、取得成功／失敗、byte・SHA-256、読取り範囲は[provenance](provenance.json)で区別する。PDF全文の取得と全文精読は同じではない。

| ID・一次資料 | 今回読む範囲／既知の内容 | 今回は確認しないこと |
| --- | --- | --- |
| L01 Mottaほか、[1808.02625v2](https://arxiv.org/abs/1808.02625v2) | 本文Eqs.1、3、6–8の密度平方分解、一体補正、basis rotationと既知PF | 元benchmarkの再集計、rank／truncation選択、新しい費用評価 |
| L02 Spillerほか、[quant-ph/0509202v3](https://arxiv.org/abs/quant-ph/0509202v3) | §IV Eqs.7–10の条件付きdisplacementとbusを自動的に戻す幾何学ゲート | 測定型のgateをdeterministic coherent回路へ無条件に転用すること |
| L03 Bermudezほか、[1110.1870v2](https://arxiv.org/abs/1110.1870v2) | Fig.1、Eqs.1–3、driving／refocusingの説明。非可換forceによる未閉路・残留spin–phonon作用 | 実験適合性、全supplementの独立証明監査 |
| L04 Sutherland–Srinivas、[2105.05768v1](https://arxiv.org/abs/2105.05768v1) | §II.A Eqs.1–6、Table I。非可換forceで非線形なspin–motion作用を生成し、有限時間の残余を持つ | 任意化学Hへの新しい転用保証。HTML生成日をv1の投稿日とはしない |
| L05 Lamataほか、[1312.2849v3](https://arxiv.org/abs/1312.2849v3) | §§2.1.1–2.1.2のJW、Trotter、MS＋local gate、spin–boson結合 | busを使うだけで新しいchemistry simulatorとすること |
| L06 Toloui–Love、[1312.2579v2](https://arxiv.org/abs/1312.2579v2) | Slater規則、CI graph、one-sparse分解、oracleと回路への接続の説明 | 全複雑度定理／全appendixの再証明、compact encodingの実装 |
| L07 Childs–Kothari、[1003.3683v2](https://arxiv.org/abs/1003.3683v2) | §§2–4のrow oracle、forest／galaxy分解、multi-edge可解成分の構成 | star分解を任意のcycleの同一実装とすること、下界の一般化 |
| L08 Rubin–Babbush–McClean、[1801.03524v2](https://arxiv.org/abs/1801.03524v2) | §IV.A–B、Eqs.43–53。零期待値制約をobservableへ追加する測定削減 | 固有状態commutator全体と同論文の制約集合の完全一致 |
| L09 Hejaziほか、[2412.16811v1](https://arxiv.org/abs/2412.16811v1) | 今回はabstract／書誌。構成の詳細は既存R4 §§2–3の照合記録を再利用 | 今回の全文再監査、最新版・出版版の全差分 |
| L10 Bagherimehrabほか、[2409.08265v4](https://arxiv.org/abs/2409.08265v4) | 今回はabstract／書誌。processor／kernel区別はR4 §3を再利用 | 元監査の式表示留保を解消したという主張 |
| L11 Feynman、[Forces in Molecules, Phys. Rev.56,340](https://journals.aps.org/pr/abstract/10.1103/PhysRev.56.340) | publisher abstractのenergy微分・forceの関係の出典 | 原論文全文のbyte取得、経路積分energy算法の保証 |
| L12 Childs–Wiebe、[1211.4945v2: Product Formulas for Exponentials of Commutators](https://arxiv.org/abs/1211.4945v2) | 導入・§VII.B Eqs.98–103の補助qubitによるanticommutator／many-body合成 | その一般的合成を新しい閉路原理と呼ぶこと |
| L13 Chenほか、[2111.12177v1: Efficient Product Formulas for Commutators and Applications to Quantum Simulation](https://arxiv.org/abs/2111.12177v1) | §II Eqs.11–18のpolynomial条件、再帰の概要、§V.B Eqs.79–82のfermion応用 | 方程式を立てるだけで独立な原理とすること |
| L14 Bookatz–Roetteler–Wocjan、[1509.00408v2: Improved bounded-strength decoupling schemes for local Hamiltonians](https://arxiv.org/abs/1509.00408v2) | 導入・§IIのbounded controlとleading-order平均化、BOA／protocol定義の必要箇所 | 有限次元local spinの条件をunbounded busへ無条件に移すこと |

全資料の取得versionと読取り箇所はprovenanceのversioned_id／read_scopeにも記録する。出版版との差分監査は行っていない。

## P1で完全に既知へ還元される部分

以下は残余仮説から除外する。異分野の名称が異なっても、新しい操作とは数えない。

| 記述した操作 | 既知構成への対応 | 結論 |
| --- | --- | --- |
| Hを密度平方の和と一体補正へ書く | L01のfactorizationとnormal-order補正 | 入力表現。新規ではない |
| 一つのLに条件付きdisplacementを結合し閉路を作る | L02のbus閉路を、既知の対角化された密度へ適用する構成 | 単独density-squareの幾何学的実装というだけでは新原理でない |
| 各Lの閉路を順番に実施してPFで結ぶ | L01の分割と既知geometric primitiveの組合せ | C相当。この部分をP1*の成果にはしない |
| 非可換forceで高次作用を作る | L03/L04の残留作用・非線形生成、L12/L13の交換子合成 | 非可換性の利用そのものは既知 |
| 符号反転・time cycleで不要結合を平均化する | L03/L14等のdecoupling・Hamiltonian engineering | echoやphase cycleという名称では独立しない |
| sourceを一般optimizerへ渡しpulseを探す | 既知の制御最適化／係数条件の求解 | 新しい目的関数又は未実装というだけでは独立原理でない |
| oscillatorを加え、電子Hではなく結合系のgroundを測る | 対象Hamiltonianを変える別タスク | D2を満たす解決とはしない |

特にL04は「非可換な力では線形平均変位だけで閉路にならない」という主要な障害の直接対照である。同論文が作るbusの非線形作用は、P1*では除去又は明示的会計が必要な成分にもなる。既知の高次合成が存在するので、「非可換作用の生成が初めて可能になる」というclaimも置かない。L12 §VII.Bは補助qubitによるanticommutatorやoperator powersの合成まで扱う。補助系で二体作用を作ること、又はoscillatorを別の補助系へ交換すること自体も差分にはならない。

## P1*の比較契約

| 比較軸 | 最も近い既知法／既知部分 | P1*でなお検討する具体的な問い |
| --- | --- | --- |
| 数学的構成原理 | density-square分解、閉路位相、commutator合成、decouplingは既知 | CARで同値な電子operator wordをまとめることが、複数密度をまたぐbus帰還cycleの新しい生成規則を与えるか |
| 入力情報とoracle | H係数、factor、既知の単項指数／forceのaccess | L⊗X、L⊗Pを元係数から実現する仕様と費用が必要。全H、resolvent、exact ground情報をoracleに追加しない |
| 出力と物理量 | 単独平方gate、spin–motion有効作用、又は一般の高次積 | 電子相互作用のcoherent発展と同一bus状態への帰還。最終的にはscalarを含む元Hの絶対E0へ接続 |
| 操作・生成規則 | factorごとの閉路、再帰的commutator formula、汎用pulse探索 | factor labelとCARの商関係から、必要電子項／不要bus項を共同処理するcycleを構成できるか。現時点で係数や成功族はない |
| 仮定と誤差 | commuting displacement、有限次元spin、small-coupling／長時間極限等、各資料固有の条件 | 非可換factor、finite-time、占有tail、higher-body残余、control後の相対phaseを同時に扱う条件。全部未確立 |
| 計算・情報取得費用 | factorization、basis rotation、force、bus制御、sampling、古典最適化は別費用 | 新しい密度―bus結合を無料としない。物理time、bandwidth、占有、ancilla、coherent control、準備・読出しを別座標で会計する必要 |
| 実質的差分 | 既知法の普遍的合成能力は既にある | その存在定理の再発見を狙わず、化学代数から共同閉路を作る独立規則の可能性を問う。未発見ならCへ移る |

**差分の状態は「未解決の構成上の問い」である。** 今回、既報に同じ解がないと証明していない。既知研究の関連要素が多数あることだけで棄却しない一方、表の右欄を既にできた手順とも扱わない。P1*をAとする根拠は不足する。Bとして保持する理由は、操作族・目標・最初の係数整合問題が書け、否定的結果でも障害の所在が具体化するためである。

独立性を残すには、CARを単に計算結果のsimplifyに使うだけでなく、その関係からcycleの選択／組合せが変わる必要がある。汎用交換子合成の中間計算短縮だけなら独立した構成原理とは判断しない。この判定自体の正式受理はGPT／ユーザー側に残す。

## 他の発想の還元と未定義箇所

### P2：配置graphと可解cell

入力bit列xからSlater規則で隣接配置とmatrix elementを得る部分はL06のrow情報に対応する。配置に応じたedge labelを求め、labelごとの小成分を指数化して全Hへ再結合する骨格も既知である。L07はone-sparse edge以外のmulti-edge可解成分を実際に構成している。

したがって「軌道ではなく配置graph」「coherentにlabelを決める」「複数edgeを一度に扱う」だけを差分にできない。P2の短cycle選択はそれらの上でのclustering／scheduling目標に留まる。cycleの全仕様がstar法と完全同値だと証明したわけではないが、独立した化学固有の生成規則が残っていないためCとする。oracle算術・可逆label・fermion符号・residual被覆費用の未確立を、そのまま新原理と数えない。

### P3：等スペクトルdefect

既存の[R4 §§2–3](https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/0d460c54f3bf54ea46d4d8129f6702703c4bb217/docs/research/qc_new_algorithm_static_screen_k0_20261016/technical_report.md)は、固有状態で外側H交換子の期待値が消えることをPF生成条件へ使う既報L09と、processor／kernelを区別するL10を照合済み。P3の入力・目的・補正生成の核が重なる。元kernelの厳密共役はその固有値を変えないという区別も同監査から再利用する。

今回は新しいkernel・許可された別primitiveを提示しておらずC。H1、H-E1、SOS-PF、C1/C2の未閉鎖条件を別名の研究へ移さない。古い監査にある保証未確立や表示上の留保はそのまま残す。

### P4：energy微分の積分

H(λ)の対応固有状態の微分期待値を、既知の基準energyへ積分して足す構成は、Hellmann–Feynman関係を使う既知の状態量復元である。[L11] 本案には異なる経路生成・状態access・積分規則がないためC。groundの交差、状態準備、係数依存basis、核反発・offset、数値積分の費用を解決したとはしない。L11のabstract確認だけを現代の全量子算法の検証としない。

### P5：有理近似

rational関数を選ぶ入力→近似関数までは定義できても、Hの逆作用をどう得るかが未定義。既存scope [R2](https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/open_problem_landscape.md)が区別するblock embedding／walk／入力oracleの境界を適用する。D1外の行列関数法で実装できることを、この案のD1内生成規則とはしない。D。

### P6：零期待値control variate

本案のHに零期待値Cを加える操作は、L08 Eq.51のobservable再表現に対応する。stationary commutatorをCとして選ぶ点は、適用stateを固有状態へ限定する。近似stateでは零期待値を保証しない。L08のmarginal制約と全commutator集合が一致するとの対応は未確認だが、今回のA選択・配分生成は既知の制約最適化を越えずC。独立した情報取得手順は出していない。

### P7／P8：未定義の操作

P7はliftとrecoveryの具体的写像、P8はclockへのenergy情報転送が未定義。どちらもD。これらは「証明が難しいからD」ではない。P1*には少なくとも明示したforce族、許す操作、除去する作用、目標isometryがあるが、P7/P8には対応する中核操作の仕様がない。既知QECやspectroscopyの一般的不可能性は結論しない。

## 公開実装の静的照合

3 repositoryの関連3ファイルを必要箇所だけ読んだ。qutip-qipではpath変更により最初の取得が404となり、tree確認後にlegacy実装へ到達した。別のtwo-qubitファイルでの対象名検索も記録し、そこにないことをrepository全体の不存在とはしない。

| 固定source | 実際に確認した処理 | このsourceが供給しないもの |
| --- | --- | --- |
| [OpenFermion low_rank.py](https://github.com/quantumlib/OpenFermion/blob/90074a3093f8e79f8432fb47103527d22e1cb609/src/openfermion/circuits/low_rank.py) | low_rank_two_body_decompositionとprepare_one_body_squared_evolution。reality／symmetry条件、一体補正、平方のbasis／density-density表示 | P1*の共同bus閉路。現defaultのtruncationを今回使ったという主張 |
| [QuTiP operators.py](https://github.com/qutip/qutip/blob/f9088ccab16378157e74c67695bdb41d9cf82d1a/qutip/core/operators.py) | displaceは有限のnumber-state空間でladder operatorの指数を作る | unbounded oscillatorのtail保証、物理pulse生成、非可換な電子条件付き閉路 |
| [qutip-qip old_gates.py](https://github.com/qutip/qutip-qip/blob/781a9ebb7b43c6ff467a5efb653ca3ad8f506453/src/qutip_qip/operations/old_gates.py) | molmer_sorensenは理想的two-qubit gateの行列表現を返す | busを含む実際の帰還やHamiltonian engineeringの保証。理想gate行列からそれらを推論しない |

外部sourceは読んだだけで、import・関数呼出し・gate生成・数値テストをしていない。snapshotは取得時点のsourceであり、各論文の実験版との一致や現在の環境との互換性は未確認。P1*全体の著者実装を取得したとはしない。コード・PDFは新規commitへ転載しない。

## 結論と限界

新規性の確立は0件。**具体的な問いを持つ高リスク仮説P1*だけをBとして残す。** 既知commutator合成・decouplingとの完全還元、関連文献の網羅性、化学factorに使える制御族、有限時間の位相保証、全資源は未確立である。これらを未知のまま残すことと、既知部分を新成果と称することは区別する。

詳細科学レビュー、新しい証明・代数展開・求解、科学実装へ進まず、[判断handoff](research_hypothesis_handoff.md)へ引き渡す。

**Mandatory STOP：新規4資料の公開・照合後に停止する。**

[L11]: https://journals.aps.org/pr/abstract/10.1103/PhysRev.56.340
