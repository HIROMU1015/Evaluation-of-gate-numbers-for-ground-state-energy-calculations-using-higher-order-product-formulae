# 候補T1の証拠・入力・保証・実現可能性の比較

2026-10-16 JST。候補は**T1の1件のみ・条件付き**。既知結果、新しい問い、未検証の改善可能性を分ける。数式は引用元のstatementの再掲に限定し、新しい合成保証を証明していない。[HANDOFF]

## 1. 最も近い既存研究との差分

T1の問いは、**deterministic PFのHadamard-test型energy推定において、trap回路から取得するlogical outputの誤差情報を、有限標本の推定失敗確率と取得費へ接続したとき、実行する時刻・PF・shot・認証精度の選択を改善できるか**である。PF係数探索、AR機構、少数点からの高次係数取得、direct optimumのサイズ移送は対象にしない。

| 近い既存法 | 既に解いた問題・アルゴリズム | T1で同じものとして主張できない部分 |
|---|---|---|
| QCELS / low-depth RPE [L01] [L24] | 複素time signalから単一周波数を推定し、multi-levelでambiguityを制御。overlap条件下のdepth/total evolution保証 | 推定器の再実装、短深度一般、既存robustness定理の再証明 |
| depolarization-aware QCELS [L03] | 指数減衰率を別測定し、gapを使うサンプリングと補正lossでenergy推定 | 既知global depolarizing lawの下で同じrate補正を行うこと |
| EFT評価 [L04] | H2のTrotterized H-test、RPE/QCELS、rotation synthesis、surface-code費用を比較 | 既存rotation数にノイズ率を掛けた費用比較 |
| EUMLE / circuit division [L06] | 既知noise channelのquasiprobability分解からunbiasedな推定・分割費用を扱う | 既知noise characterizationを無料入力にした一般noise mitigation |
| logical accreditation [L17] | trap circuitの失敗からideal compiled target outputとのTVD/observable誤差を制約 | TVD認証そのもの、TVDから観測量誤差への既知不等式。原論文はQCELS後処理を対象外とするが、適用が容易とも述べる |
| verified phase estimation [L23] | 状態準備の逆回路とpostselectionでsignalのerrorをmitigate | 入力へ戻る検査をtrap認証や無条件のenergy certificateと改名すること |

**残余の候補は情報・推定・資源を結ぶ具体的な設計問題**である。既存論文の未評価部分を見つけたことは確認できるが、独立した新アルゴリズムや厳密な新規性を確認したわけではない。特にL17自身がapplicationへの適応可能性に言及しており、単純な接続だけなら差分は弱い。

## 2. 数学的仮定と保証の対象

| 資料 | 入力・仮定 | 保証／適用範囲 | 実証と費用の意味 |
|---|---|---|---|
| QCELS、`2211.11973v2` [L01] | 同じHのcontrolled evolution、共通のprepared state、bounded spectrumとalias管理。主結果はlarge overlap、低overlap版はfilter窓・relative-overlap情報が必要 | overlapに応じた最大時間短縮とHeisenberg型total evolution。ideal momentと有限shotに関する条件付き解析。任意PF/任意device noiseの保証ではない | TFIM/Hubbardの数値比較。古典least-squaresを用いる。著者codeのsignal generatorは既知spectrum/populationを入力する |
| adapted RPE、`2302.02454v4` [L24] | 同じunitaryのpowers、初期target overlapの下界。Theorem 2は`p0 > 4-2 sqrt(3)`という条件を持つ | 所定shot数でmodulo phase誤差を高確率制御。ground-state同定やPF biasを自動保証する定理ではない | TFIM例。phase ambiguity、state admixtureとshotを区別。旧Kimmel等v3のerratumを無視した元証明は用いない。[L19] |
| noisy QCELS、`2307.11257v2` [L03] | normalized H、非零gap、`p0>0.5`、controlled circuit全体のglobal depolarization `exp(-alpha abs(t))`。alphaの別取得 | alpha推定とGaussian系のtime sampling/補正loss。precisionに関するpolynomial costはnoise/gap比にも依存。局所noiseの数値支持を一般定理にしない | 4-qubit TFIM、global noiseとQiskit local noise診断。calibration circuitと主データ両方が必要。化学実機の検証ではない |
| H2 EFT評価、`2403.00077v1` [L04] | minimal-basis H2の小qubit Hamiltonian、指定state overlap、depolarizing logical model、surface-code/factory/synthesisモデル | protocol比較とモデル内資源推定。Trotter誤差は小さいことを別チェックし、主な最適化対象から実質分離 | H2回路のsimulation。state準備にexact eigensystemを使う公開sourceがある。最終physical費用はarchitecture仮定付き |
| EUMLE、`2410.05369v2` [L06] | noisy sampleからideal distributionを得るquasiprobability情報。MSQPE解析はeigenstate preparation等を仮定 | EUMLEの一致性・漸近正規性、global noise下のcircuit division等。有限標本のuniform coverageそのものではない | Hubbard・分子の資源推定。化学の主要例はTHC/qubitization、code distance/factoryも最適化。標準偏差とfixed failure probabilityの規約差を原文も区別 |
| logical accreditation、`2508.05523v3` [L17] | 下記A1〜A4、指定logical gate/layer構造、target/trapのランダム実行順序、trap shots | compiled target distributionへのTVD、bounded observable誤差。stateの物理的ground-state性やPF近似誤差を認証しない | IQPとTrotterized circuitのsurface-codeモデル。QCELS後処理・energy推定全体は未評価。trap数は精度依存で、無料ではない |
| VPE、`2010.02538v1` [L23] | state preparationとunpreparation、戻り測定、noise/実装条件に応じたsignal再正規化 | error mitigation。数値例の高次error抑制を任意noiseのcertificateに拡張しない | free-fermion/Ising/electronic-structureの小規模simulation。state準備の逆回路、棄却shotとsampling costが必要 |

### logical accreditationの条件を省略しない

L17 §IIIのA1はphysical single-qubit gate noise、A2はlogical single-qubit Clifford noiseのgate-independenceに関する仮定で、位置依存は許す。A3は各runのCPTP evolutionと**異なるrunの独立性**を要求する。独立だが非同分布のdriftは許されても、run間の任意相関まで保証するものではない。fully FTのmagic-state構成にはA4のnon-noise-decreasing条件もある。within-runの非Markov性に対して使うsoundness boundも選ぶ必要がある。

同論文の既知statementは、ideal compiled targetとexperimental outputのTVD上界を`gamma`とすると、bounded observableの誤差を`2 gamma ||O||_infty`で制約するというもの。trap failure平均を加法精度`eta`、失敗確率`alpha`で評価するshot数は`O(eta^-2 log(1/alpha))`であり、qubit数に独立なshot数でも**各trap回路の実行費は消えない**。[L17] §III.C/H

このgammaはPF/Trotter近似やrotation synthesisの設計誤差を測定するものではない。L17 §IIIもそのblind spotを明記する。**TVD→energy intervalの新しい式や一般ground-state保証は、本調査で導いていない。** controlled phase convention、alias窓、target overlap、有限shot、compiled approximationの別契約が必要である。

QCELS/RPEは共通Hまたは同じunitaryのpowersに関するtime signalを使う。初期案では一つのfitの中でPF wordを固定し、そのinteger powersを使う設計を出発点とする。時刻ごとにPF/stepを変えて異なるeffective spectrumを黙って一つの指数へfitしない。そうした変更を許すには、各点のideal-H signalへの近似と推定器への伝播を別に正当化する必要があり、今回その保証は作っていない。

## 3. 入力情報・費用の比較

| 情報／費用 | 既存法での役割 | T1で確認が必要なこと |
|---|---|---|
| Hamiltonian、定数項、時間の単位 | circuitとenergy originを定義 | identity/global phaseをcontrolled回路で失わないbinding。古い異なるH/sourceを混ぜない |
| prepared stateとtarget overlap/window | QCELS/RPEの識別可能性を支える | 高overlapを無償oracleにしない。下界・窓をどう得るか不明なら条件付き結果に留める |
| exact ground/spectrum | 著者codeや小系benchmarkのdata generationに使用 | **採点oracleだけ**と運用入力を分ける。真値でschedule・state・認証精度を選ばない |
| noise model/alpha | noisy QCELS/EUMLE/既存physical costingの入力 | trap情報が何を代替し、何はなお必要か。model-known対照にも同等の情報費を課金する |
| PF・synthesis error上界 | ideal Hとcompiled targetの差を制約 | 既知の保守的boundが大きすぎれば認証後も有用なenergy推定にならない。高次係数取得研究で救済しない |
| target shots | real/imaginary H-testのsampling | 短時間と長時間の情報価値・failures・state準備を含める |
| trap shots | gamma推定のconfidence | targetごとのprecision、再利用可能性、independent holdout、同時confidenceの費用。異なる回路の認証を無条件に共有しない |
| classical fit/compilation | nonlinear least-squares、trap生成、回路合成 | multi-start/alias探索や新compilerを無料にしない。古典処理と量子資源を単位なしに合算しない |
| physical resources | logical gate数からcode/factory/runtimeへ変換 | T count、depth、logical cycles、physical qubitsを分ける。architecture未固定ならvectorで報告し、net advantageを断言しない |

## 4. 公開実装と既存コードの静的確認

| 固定source | 確認した構成 | 再利用できる部分／必要な変更 |
|---|---|---|
| `zhiyanding/QCELS`、`0242c200d9c60f565443067d56e611c51e4fead8` [C01] [C02] [C03] | SciPy loss、multi-level window、Fourier filter。`generate_Z_est`はspectrum/populationからsampling | classical fit/referenceとして有用。実H-test/trapの測定recordsを受けるdata interfaceは別途必要。既知spectrum generatorを実装可能な測定器と呼ばない |
| `adbacze/qpe4earlyftqc`、`563b763586fa55d67e79496c198167da177f8c74` [C04] [C05] [C06] [C07] [C08] | Qiskit H2、W/Usp callback、noisy RPE/QCELS、Clifford+T compiler | callback/回路の出発点。documented Qiskit 0.43.1系と外部gridsynthへの依存があり、現環境で動作することは未検証。encoded trap認証は実装されていると確認していない |
| `StefanoPolla/EarlyFT_QPE`、`01e339b0171067a915f0cfc0b17a063da1e06a0d` [C09] [C10] [C11] | MSQPEとlogical/physical costing | 強いmodel-known対照の設計参考。PFにそのまま接続する版やlogical accreditation実装を確認したわけではない |
| logical accreditation [L17] | 本文/appendixにlogical layers・trap構成とsimulation仕様 | 本調査では著者による公開実装の所在を特定できなかった。実装不存在の証明ではない。trap compiler・twirling・測定record・confidence処理が大きな新規開発部分 |
| 本repositoryの`chemistry_hamiltonian.py` [HAM] | PySCF/OpenFermion、JW、H-chain geometry、commuting grouping、exact sparse eigensolver | H生成とPauli listを将来再利用可能。`ham_ground_energy`はexact oracleであり運用入力へ混ぜない。今回何も呼び出していない |
| `product_formula.py` / `sector_pf.py` / `component_sector_pf.py` [PF] [SECTOR] [COMPONENT] | S2 composition列、dense sector unitary、component eigensystemとsparse block exponential | deterministic PFのspec/referenceに有用。dense unitary builderはcontrolled gate circuitやnoisy logical hardwareの代替ではない。sector外leakageを許すnoiseはsector内simulationだけでは検査できない |

QuantumMAMBOのBLISS sourceも静的確認したが、T1の初期実装要件には含めない。[C12] [C13] 公開コードをダウンロードしたことは、実行・再現成功・論文と同一版の保証ではない。固定SHA、path、byte/hash、read scopeをprovenanceへ記録した。

## 5. 手元の資源と最小検証の実現性

read-onlyのhost metadataではCPU affinity 32、`MemTotal: 65522480 kB`を確認した。`nvidia-smi`はdriverと通信できず、使用可能なGPUは確認できなかった。これは割当済み計算予算や性能benchmarkではなく、他server/GPU/QPUへの使用承認も意味しない。[PROVENANCE]

少qubitのH-test signalと古典fit、Clifford trapの論理レベル機能比較はCPU上で検討可能と推定する。ただし未実装・未実測である。statevector、dense unitary、density matrixの費用はそれぞれ異なり、後二者は指数的memoryを要する。encoded FT回路を全noise密度行列で直接解く方針を前提にしない。full fault-toleranceの検証と、logical noise channelの小系機能試験を区別する。

将来の最小試験案は、2〜4 system qubits程度のfresh/public小分子Hamiltonianと1 ancilla、少数の固定time levels、既存deterministic S2/S4、明示したstate準備を対象にすること。比較するのはnoiseless、model-known noise対照、trap上界のglobal配分、time別配分。global depolarizationをpositive controlとし、A1〜A3を満たす別noise、仮定違反のstressを分ける。**具体座標・件数・thresholdを固定した実行protocolではなく、必要な検証の目的と規模の案である。科学実行は未承認。**

小系でも、(i)仮定内のcoverageが壊れる、(ii)認証費が全利益を消す、(iii)配分が強い対照と同じ、という失敗は判別できる。小系の成功だけでは大系での資源利益や実機noiseへの妥当性は示せない。

## 6. 未完了義務と候補を取り下げる条件

| 未完了事項 | 今回の到達点・必要判断 |
|---|---|
| 同じend-to-end設計の先行研究不存在 | 確定していない。L17の後続・VPE・noise-aware PEとの追加比較が必要 |
| finite-sample energy inference | TVD/observableの既知保証とenergy estimatorの間の条件を列挙しただけ。新証明は0件 |
| 認証情報が選択を変えるか | 未検証。単純union/triangle bound＋既知scheduleで全て説明され、追加利益がなければ独立性は弱い |
| calibration/trap費用 | 未測定。対象回路と同じ費用モデルで全shots・state準備・confidenceを含める必要 |
| ground-state/branch同定 | overlapやisolating windowのpriorが必要。出力bitの正しさだけではground stateを認定できない |
| 既存研究との差 | [LANDSCAPE]§7の境界を維持。U7やPRのscopeへ戻るなら別名の新テーマにしない |

これらを解いたものとして正式採択・実装・検証へ進めない。今回の作業は静的整理と4資料の公開照合までで、完了後Mandatory STOPとする。

<!-- fixed-source-references -->

[C01]: https://github.com/zhiyanding/QCELS/blob/0242c200d9c60f565443067d56e611c51e4fead8/README.md
[C02]: https://github.com/zhiyanding/QCELS/blob/0242c200d9c60f565443067d56e611c51e4fead8/qcels.py
[C03]: https://github.com/zhiyanding/QCELS/blob/0242c200d9c60f565443067d56e611c51e4fead8/fourier_filter.py
[C04]: https://github.com/adbacze/qpe4earlyftqc/blob/563b763586fa55d67e79496c198167da177f8c74/README.md
[C05]: https://github.com/adbacze/qpe4earlyftqc/blob/563b763586fa55d67e79496c198167da177f8c74/H2_simulations/H2aRPE.py
[C06]: https://github.com/adbacze/qpe4earlyftqc/blob/563b763586fa55d67e79496c198167da177f8c74/packages/qpe_protocols/aRPE.py
[C07]: https://github.com/adbacze/qpe4earlyftqc/blob/563b763586fa55d67e79496c198167da177f8c74/packages/qpe_protocols/qcels.py
[C08]: https://github.com/adbacze/qpe4earlyftqc/blob/563b763586fa55d67e79496c198167da177f8c74/packages/CliffordTCompiler/CTcompiler.py
[C09]: https://github.com/StefanoPolla/EarlyFT_QPE/blob/01e339b0171067a915f0cfc0b17a063da1e06a0d/README.md
[C10]: https://github.com/StefanoPolla/EarlyFT_QPE/blob/01e339b0171067a915f0cfc0b17a063da1e06a0d/eftqpe/MSQPE.py
[C11]: https://github.com/StefanoPolla/EarlyFT_QPE/blob/01e339b0171067a915f0cfc0b17a063da1e06a0d/eftqpe/physical_costing/ftqc_SinQPE.py
[C12]: https://github.com/iloaiza/QuantumMAMBO.jl/blob/f8fbc4dccb89e3f8bed97b544fc87a06600fd81a/README.md
[C13]: https://github.com/iloaiza/QuantumMAMBO.jl/blob/f8fbc4dccb89e3f8bed97b544fc87a06600fd81a/src/UTILS/bliss.jl
[COMPONENT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/src/trotterlib/component_sector_pf.py
[HAM]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/src/trotterlib/chemistry_hamiltonian.py
[HANDOFF]: candidate_handoff.md
[L01]: https://arxiv.org/abs/2211.11973v2
[L03]: https://arxiv.org/abs/2307.11257v2
[L04]: https://arxiv.org/abs/2403.00077v1
[L06]: https://arxiv.org/abs/2410.05369v2
[L17]: https://arxiv.org/abs/2508.05523v3
[L19]: https://arxiv.org/abs/1502.02677v3
[L23]: https://arxiv.org/abs/2010.02538v1
[L24]: https://arxiv.org/abs/2302.02454v4
[LANDSCAPE]: research_topic_landscape.md
[PF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/src/trotterlib/product_formula.py
[PROVENANCE]: provenance.json
[SECTOR]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/src/trotterlib/sector_pf.py
