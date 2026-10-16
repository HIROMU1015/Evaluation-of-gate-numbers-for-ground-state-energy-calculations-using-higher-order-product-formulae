# P1* Phase B基盤：技術的準備判定

2026-10-17 JST。対象：**P1STAR-A-v1**。**判定：NOT_READY**。技術実装と人工テストは完了したが、専用jobの16 GiB RAM制限と、保存中間terms全体の20万上限を確認できていない。科学契約は変更していない。

## 1. 権限・正本・今回行わなかった計算

今回のユーザー指示は、隔離exact solver環境、CAR／CCR adapter、resource guardの技術実装・技術テスト・公開を承認する。**P1*の科学計算、科学的成立性の認定、Phase B実行承認は含まない。**

最新binding正本はcommit **90d439e87a9aa83444e5f3e48020c1cc05bf007f** の[binding記録][binding]と[provenance][binding-prov]。科学契約はcommit **1771564d919837e2440a9fcb175ac054284a729c** の[契約草案][contract]を保持した。旧文書の「今回未実装・未承認」はその作成時点の記録として変更していない。今回の技術実装の権限は新しいユーザー指示による。

P1*のL1／L2／Kをcodeへ入力せず、その交換子・正規形・適格性を計算していない。固定12 segmentのMagnus／formal-log展開、係数条件の生成・求解、反例探索、新証明、分子simulation、pulse最適化、回路生成、benchmarkも0件。科学契約の4 modes、N=2、full Fock主判定、2因子、12 segment、4次、振幅boxを変更していない。因子適格性は将来のPhase B冒頭の最初の科学gateとして残す。

## 2. Exact solver：隔離構築・人工問題で確認したこと

新しいvenvに**CPython 3.11.1／z3-solver 4.13.3.0／SymPy 1.13.3／mpmath 1.3.0**を固定した。既存repositoryのvenvは変更していない。公式PyPIの版別metadataを取得し、そのSHA-256と照合したwheelだけをoffline導入した。[requirements.lock](../../../research_tools/p1star_foundation/requirements.lock)と[environment_lock.json](../../../research_tools/p1star_foundation/environment_lock.json)を保存した。

| 対象 | bytes | SHA-256 |
| --- | --- | --- |
| Z3 4.13.3.0 Linux x86_64 wheel | 28,124,043 | `794843e4946ade1561e40a75ffc1163b45d36b493fd6cc269ad1d6a65bddb8e5` |
| 実際にmappedされたlibz3.so | 21,715,032 | `fa2f59a2be4292e8eefc4928f9cdc8eaad6f2ae8e44476fd67c1f03ab86e767f` |
| venv内のz3 CLI binary | 21,613,408 | `1cc0766515f49af2b79d2243685f496814b0feb9ceab28744cfecdbf7c5f5d9c` |

libraryとCLIのbytesは検証済みwheel内の同じmemberと一致する。求解経路はCLI subprocessではなく**Python process内のSolverFor("QF_NRA")**である。各呼出しでZ3 version、mapped library hash、runtime package versionを照合する。公式[Programming Z3 §6.5][z3-doc]が記述する実数多項式decision procedureを、実際に以下の人工問題で確認した。性能評価や、P1*の式での完了保証ではない。

| 人工fixture | 既知の結果 | 技術確認 |
| --- | --- | --- |
| 1変数をexactな1/3へ固定、閉boxも[1/3,1/3] | SAT | 有理数分子・分母、閉境界、exact代入 |
| u²=2、box [1,2] | SAT | 正の√2をexactなreal-algebraic root-objectとして保持 |
| √2をexactな係数として√2 u=1、box [0,1] | SAT | exact real-algebraic入力とwitness |
| u²+1=0、実box [-1,1] | UNSAT | 実数不整合。rational rootがないだけの判定ではない |
| u²=2、box [-1,1] | UNSAT | boxを含めた不整合 |
| 12個のtoy変数、u0²=1/2、他11変数=u0、全box [0,1] | SAT | 12実変数の結合等式と全閉box、12個のexact代数的witness |
| 上記とは独立の既知SATな1変数問題にnative rlimit=1 | UNKNOWN | `max. resource limit exceeded`をUNSATへ変換しない |

最後の12変数fixtureは、既知の小さな平方根問題を等式chainへした人工問題であり、P1*の条件集合を生成・模擬したものではない。solverのUNKNOWN分岐には、nativeで実際にUNKNOWNとなるテストと、control-flow用の明示したinjectionテストを分けた。

SAT witnessはdecimal表示に依存せず、有理数の整数分子／分母又はexact `root-obj`式をJSONに保存した。元の等式・boxへexact代入して閉じることを確認するが、**代入確認も同じZ3への信頼に依存**する。非多項式、未宣言symbol、量化子、complex条件の未分離、逆向きbox等は拒否する。すでにcallerがfloatをexact-looking ASTへ変換した履歴までは検出できないため、int／Fractionからの入力経路を要求する。

UNSATはsolver依存のexactな結論として保存する。別の既知人工矛盾をproof-enabled contextで試すと、proof textを取得できたが**trusted theory lemmaを含む**。独立したcertificate checkerは作成・実行しておらず、`independent_certificate_verified=false`を維持した。proof textがあることを、独立検証可能な数学的証明書の検証成功としない。[公式API][z3-api]も参照した。

## 3. CAR／CCR adapter：実装と技術テスト

[実装source](../../../research_tools/p1star_foundation/)は科学データを内蔵しない汎用packageである。

- 係数はPython Fractionの実部・虚部によるQ(i)。float／Python complexを拒否し、小さい非零有理数をtoleranceで捨てない。SymPy 1.13.3のQQ_Iとのexact round-tripもテストした。係数domainの意味は旧bindingと同じで、kernelでは汎用SymPy expandを呼ばない。
- Fermionは定義CARによる隣接交換、縮約、nilpotencyを実装し、creation昇順／annihilation降順へ正規化する。2つのgeneric modeの基本反交換関係、occupationの既知恒等式、index順とnormalizationの冪等性をテストした。固定factorやsector行列を使っていない。
- Busは正確なCCRのX-before-P形式と、全distinct wordの平均で定義するWeyl対称basisの間を変換する。既知のXP／PXの符号・定数、4次の6-word対称平均、短いgeneric wordのround-tripをテストした。oscillatorの有限行列、Fock cutoff、状態simulationは使わない。
- Electron／busのtensor key、η次数、parameter指数、電子body数を分離する。CAR、CCR、factor固有、sector固有を別タグとし、sector由来をfull Fock認定へ流用する操作は拒否する。
- input IDとorigin、局所rule、変換前wordをtraceに保持する。項が相殺して消えてもinputの由来は残る。factor固有・sector固有の関係の発見・適用は実装対象外で、タグの分離をテストした。

変換logはソフトウェアの由来情報であり、CARを使ったP1*制御選択規則、新原理、full Fockでの科学的成立性を示さない。失敗時に部分的なTensorExpressionを有効結果として返さない処理もテストした。

## 4. Resource guard：保証範囲と不足

固定値は **1 job／1 CPU process／16 GiB RAM／全体1800秒／保存terms総数200,000／出力20 MiB**。定数の技術テストで元契約と一致することを確認した。以下の制御を実装したが、表の範囲を越える保証へ拡張しない。

| 制約 | 確認できた制御 | 残る不足 |
| --- | --- | --- |
| 1 job | 同じpathのfile lockを使うlauncherの重複を拒否し、終了後に解放する | ホスト全体の排他ではない。P1* science launcherは存在しない |
| 1 CPU process | stdlib人工workerのaffinityが1 CPU、1 thread。worker内のforkをchild-only RLIMIT_NPROCで拒否。solverはin-process、parallel mode無効 | native内部の全動作や将来の科学driverを認定したものではない。監督はworker外に置く |
| 16 GiB RAM | 小さい人工workerでRLIMIT_ASによる過大virtual allocationのMemoryErrorを確認 | **RLIMIT_ASはvirtual address space**。job RAMの代用ではない。現在のsession memory.max／swap.maxはmax、cgroup mountはread-only。専用job cgroupなし |
| 全体wall | 単一monotonic deadline、TERMを無視する人工workerも外部SIGKILLで停止 | 技術probe用の制御。OS scheduling・kill cleanupを含む厳密な全job完了上限や30分science driverは未確認 |
| terms総数200,000 | 同一ledgerの全管理TermMapを集約し、新規entryのinsert前に拒否。小さい境界、複数map、例外解放をテスト | **入力・再帰stack・一時object・trace・Z3内部projection／polynomial／AST・serialization等は未集計**。全中間項上限を保証できない |
| 出力20 MiB | 同じOutputBudgetを通る複数file writeを合算し、上限超過前に拒否。probe stdout／stderr captureも合計を有界化 | native／直接writeや文字列生成前の内部storage、全job file quotaを包括的に制御していない |

技術テストは小さい人工上限を使い、RAMを16 GiBまで実際に消費する負荷試験やbenchmarkは行っていない。41テストの外側にも60秒・1 CPU affinity・RLIMIT_AS 1 GiBを設定した。この外側制限もRAM hard limitではない。

cgroupへの書込み、root／user managerの権限取得、sudo、controller有効化、既存service／cgroupの変更は**0件**。不足する権限を迂回せず、read-onlyのprobe結果を保存した。Python/native内部の項数を監視できない範囲を「制限対象外」と勝手に再定義せず、科学jobへの入口を閉じた。

## 5. 技術判定と将来の残条件

[technical_test_results.json](technical_test_results.json)は **41 tests、失敗0、error0、skip0**。source hash、環境lockのhash、人工SAT／UNSAT／UNKNOWNとexact witness、proof capability、readinessを保存した。codeを変更していない状態で確認した結果であり、科学的結果ではない。

最終判定は**NOT_READY**である。`TECHNICAL_READY_WITH_CONTRACT_CHANGE_REQUIRED`にしない理由は、項数定義だけの問題に加えて、必要なRAM制御経路自体が確保できていないためである。契約変更は提案を採択せず、実施していない。

将来の判断・実装に残る条件は次のとおり。

1. 権限を持つ専用job環境で、固定RAM・CPU・process・wall・全出力制限を設定・読戻し・人工テストで確認すること。今回の権限では実施しない。
2. native内部を含むterms集計の実行可能な仕様・実装を得ること。管理対象を変更するなら、理由と影響を示してユーザー／GPTの判断を受けること。今回それを変更していない。
3. 科学実行の前に、科学driverの実装範囲、入力・環境・source hash、全budgetの適用、停止後再試行なしを固定すること。このpackageには因子適格性・Magnus・条件生成の科学driverがない。
4. そのうえで**ユーザーのPhase B科学計算の別途明示承認**が必要。技術テスト成功、環境導入、GitHub公開を承認の代用にしない。

因子適格性は未計算であり、環境整備の途中へ移していない。full Fock主判定が将来不成立でも、sector限定構成一般の不成立とはしない。D1／D2、元電子Hamiltonianの絶対基底エネルギーとの対応を維持する。

## 6. 使用方法・保全・公開

[README](../../../research_tools/p1star_foundation/README.md)に隔離再構築、backend identity照合、人工テスト、read-only readiness診断の手順を記載した。`--run-science`等のoptionは存在せず、`require_phase_b_ready()`は拒否する。

新branchは **qc-p1star-phase-b-technical-foundation-20261017**、baseは **90d439e87a9aa83444e5f3e48020c1cc05bf007f**。新規のsource・tests・lock・使用方法・本報告・技術結果・provenanceだけを明示stageして通常pushする。既存資料はbaseの履歴から参照し、再生成・上書きしない。

読む順序：**本報告→README→technical_test_results.json→environment_lock.json→provenance.json→必要に応じて固定科学契約**。sourceのorigin/result commitとverified snapshot commitを分け、manifestはprovenance自身を自己除外する。公開後のcommit・remote SHA・fresh Git blob・raw bytes・SHA-256は別local receiptで照合する。

元Evaluation workspace・既存worktreeのdirty／staged／untrackedを保全し、PR側はread-onlyで監査した。並行して変化した他worktreeはwriterを推定せず、そのまま保持する。既存SOURCE、科学結果、authorization、grant、STOP／PAUSE、T1-D、U1／U3／U4、FS-R1 Phase B未承認、PRのCLOSED／STOP／PAUSED／HOLD／NOT_ADOPTEDを変更しない。監査の範囲と限界は[provenance.json](provenance.json)へ記録する。

**Mandatory STOP：技術基盤の実装・検証・公開照合後に停止する。P1*科学計算、科学レビュー、正式採択を開始しない。**

[binding]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/90d439e87a9aa83444e5f3e48020c1cc05bf007f/docs/research_exploration/p1star_environment_binding_20261017/execution_environment_binding.md
[binding-prov]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/90d439e87a9aa83444e5f3e48020c1cc05bf007f/docs/research_exploration/p1star_environment_binding_20261017/provenance.json
[contract]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md
[z3-doc]: https://z3prover.github.io/papers/programmingz3.html#sec-nlsat
[z3-api]: https://z3prover.github.io/api/html/z3.z3.html
