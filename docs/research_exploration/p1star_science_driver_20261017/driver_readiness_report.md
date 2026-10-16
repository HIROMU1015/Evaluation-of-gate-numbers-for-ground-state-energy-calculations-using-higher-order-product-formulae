# P1STAR-A-v1 driver 技術判定 — 2026-10-17

**判定：`DRIVER_TECH_READY`。** 必要な汎用driver機能を実装し、既存41件＋追加33件の**人工技術テスト74件がPASS**した。P1*の固定factor、固定12 segment、実係数条件は一切計算していない。科学的成立性・科学的GO・Phase B実行承認・正式採択は認定しない。

## 今回の成果と承認境界

2026-10-17のユーザー指示に基づき、[資源運用追補](resource_policy_addendum.md)、[sourceと使用方法](../../../research_tools/p1star_driver/README.md)、[test結果](technical_test_results.json)、[provenance](provenance.json)を作成した。独立branch `qc-p1star-phase-b-science-driver-20261017`、base `a242f8e7fffa8b3f51b06b89242f5cc16c6b839f` を使用する。

元科学契約 `1771564d919837e2440a9fcb175ac054284a729c` はbyte一致のまま。科学契約、旧resource比較、旧environment binding、旧foundation report/results、既存authorization・grant・STOP・PAUSE・manifestを上書きしていない。`research_tools/p1star_foundation/` も変更していない。

旧 `NOT_READY` は当時の「全native termsを含む20万上限」「専用cgroupによるjob全体16 GiB」の厳密契約に対する履歴であり、その記録を維持する。今回の判定は、新たに承認された実用監視方針でのdriverの人工技術検証である。旧比較案R-TERMS-2全体の採択とは記載しない。

## 実装した経路

1. 入力gate：exact Hermiticity、full FockとN識別sectorの非可換性、平方和Kの二体非自明性・非退化。sectorではscalar+全一体作用のspanとKとのexact rank比較を行う。失敗時はINCONCLUSIVEで停止し、factor変更・sector救済を行わない。
2. 有限wordの形式log：標準のtruncated expとlog seriesを次数1〜4で実装。時系列の左積 `U_last ... U_first`、`-iηx_jG_j` の符号、CAR電子正規形、exact CCR/Weyl、parameter powers、body数、tensor基底、transform logを保持する。
3. 係数条件：full Fockの全basis成分を比較し、targetに含まれるscalar/一体/二体成分も保持する。不要なbus非identity、高体、scalar、一体等を捨てず、real/imagのexact多項式等式にする。sector tagは拒否する。
4. exact求解：既存Z3 4.13.3.0のQF_NRA/NLSatに、等式と閉boxを渡して1回だけcheckする。SATはrationalまたはreal-algebraic root objectで保存し、元の全等式とboxへexactに再代入する。UNSATは指定ansatz/box内のsolver依存結論。独立証明書は未検証。UNKNOWN・不足・異常はINCONCLUSIVE。
5. bounded screen：adjacent exact cancellation、同一factorの四pulse quadrature閉路、literal group commutator、literal連結を具体的対応付きで記録する。任意のpulse再順序・cyclic同値・一般的還元・新規性の自動証明をしない。CAR選択の主張と事後normal orderingを別fieldで保存し、主張だけを独立検証済みとしない。
6. 科学入口：明示的CLIとworker branchを設け、別途承認、全freeze hash、実環境一致、1回限りのattempt markerを要求する。承認前に科学inputを開かない。科学固定specのvalidatorは承認後のlazy importに限定する。今回この入口・worker science branch・validatorは実行していない。

`NONTRIVIAL_FORMAL_CANDIDATE` は自動認定しない。SATでもscreenに一致しなければ `formal_consistent=true` とINCONCLUSIVEを併記し、科学的解釈を別途判断に残す。full FockのUNSATをsector限定原理一般のno-goへ拡張しない。

## 人工検証の証拠

`technical_test_results.json` が実行済みsuite、各test ID、PASS、時間、使用source hash、実環境identityを保持する。実行時間は技術監査のmetadataであり科学benchmarkではない。

| 確認対象 | 人工testの内容 |
|---|---|
| 非可換積・CAR・CCR | 二mode電子演算子、occupation冪等性・nilpotence、exact `[nX,nP]=in`、Weyl成分とtensor分離 |
| 形式log | 同一生成元、2生成元の標準BCH 4次（4次項が非zeroになるtoyを使用）、central bus rectangle |
| 適格性gate | 固定P1*と異なる2個の4-mode toy factorで通過、可換・退化toyで停止 |
| full Fock/sector | 3-body occupation積がN=2で消えてもfull Fock residualに保持される。sector tag混入を拒否 |
| 条件生成 | scalar/一体/二体/高体、real/imag、bus非identityを検出。bus残差を落とせば誤るtoy UNSATを含む |
| exact solver | rational・algebraic SAT、exact witness再構成・改ざん検出、実box UNSAT、native resource countによる実UNKNOWN、制御経路の注入UNKNOWN |
| 接続したpipeline | 4-pulse single-factorの既知toy閉路でSAT→exact再照合→既知対応、zero boxでUNSAT、失敗/UNKNOWNでINCONCLUSIVE・retryなし |
| 実行監視 | 同じworker経路で人工pipeline完了、1 CPU affinity、wall kill、RSS閾値停止、AS不足のMemoryError、出力上限、exit19の異常終了 |
| 承認境界 | science actionの承認なし/falseはinput reader呼出前に拒否。成功・hash改ざん・attempt重複はSYNTHETIC-ONLYのreceiptで検証。科学CLIは呼ばない |
| 旧互換性 | foundationの41件を変更せずPASS。旧readinessが旧契約のNOT_READYを保持することも確認 |

開発中は追加testの確認後、4次BCH testを「4次項が非zero」のtoyへ強化し、最終74件を再実行した。新しい科学問題の試行・条件調整ではない。公開するJSONは最終source snapshotに対応する。今回の人工試験に固定P1*のL1/L2/Kと固定12 wordの組合せは用いていない。

## 実行環境と資源の限界

CPython3.11.1、SymPy1.13.3、mpmath1.3.0、Z3 4.13.3.0。既存隔離venvを再利用し、install、global package変更、新規binaryの公開は行っていない。mapped `libz3.so` のSHA-256は `fa2f59a2be4292e8eefc4928f9cdc8eaad6f2ae8e44476fd67c1f03ab86e767f`。新driverのenvironment lockは今回の技術snapshotであり、実科学のfreezeではない。

TermLedgerの管理map上限とbounded outputを維持し、実用的なwall/RSS監視、AS制限、CPU affinity、協調lockを実装した。**native全termsの包括的計数、専用cgroup、job全体16 GiB RAM hard capは保証していない。** RSSはサンプリングでovershootし得る。controllerのメモリとPython/nativeの一時表現はTermLedger対象外。OS全体障害で最終ログを必ず残せる保証もない。詳細は追補を参照。

科学用時間・メモリ・traceの運用値は未固定。toyは30秒wall/512 MiB RSS/2 GiB AS等の小さい技術設定を使ったが、科学承認へ転用しない。小さい4-pulseでも多数のtraceを生成する。実固定12-pulseが実用運用枠で完了するか、何terms・何時間を要するかは未計算であり、INCONCLUSIVE停止の可能性がある。性能・資源優位の主張はしない。

科学CLIの全経路を通すtestは、今回の禁止範囲に従って未実施。共有する承認・演算・solver・監視は人工testで確認し、固定literal bindingとlazy import順序は静的に確認した。これは実科学のend-to-end成功を保証しない。

## 保全と公開の扱い

本taskの書込みは独立worktreeの新driverと新docsだけ。開始時baselineはEvaluation92 worktrees、PR207 worktrees。公開前のread-only比較ではEvaluationの既存92件はHEAD・index・dirty/staged/untracked metadataが一致した。PRでは205件が完全一致、2件に差分、さらに1件の新worktreeを観測した。PR rootのuntracked metadata変化、別worktreeのHEAD/index更新をprovenanceへ記録し、本taskから変更・復元・commit/pushしていない。全worktreeが不変だったとは主張しない。

保存snapshotはHEAD、porcelain-v2、semantic index、staged/unstaged diff、dirty tracked bytes/hash、untracked metadataを対象とする。全untracked/ignored fileの内容をhashした保証ではない。保全範囲を過大に記載しない。

既存資料はbase履歴から継承し、重複生成しない。新規ファイルのみを明示stageして通常pushし、remote先端SHAとfresh Git取得、Git blob、raw bytes、SHA-256を最終引渡し時に照合する。自己参照を避けるため、provenanceは自身をmanifestから除外し、公開後receiptで自身も照合する。公開commit/照合完了状態は最終handoffと公開後receiptを正本とし、凍結した過去provenanceを書き換えない。

## 次回の判断事項

- P1STAR-A-v1 Phase Bを1回だけ実行する別途明示承認。今回の技術承認を転用しない。
- 元契約＋本資源追補、入力bytes/hash、code/commit/hash、環境snapshot/hash、具体的な全運用値、共通lock/attempt directory、承認reference、停止点のfreeze。
- 因子適格性gateから始め、gate失敗・資源停止・UNKNOWNはINCONCLUSIVE、solver UNSATは固定full Fock ansatz/box内の結論とする運用の確認。
- 結果後の新ansatz、retry、証明、反例探索、科学レビュー・新規性解釈・正式採択は自動開始しない。

T1-D、U1/U3/U4、第一・第二研究、FS-R1 Phase B未承認、PR Track A/Bの既存PAUSE/HOLD/CLOSED等は本taskで変更しない。D1/D2、元Hamiltonian絶対基底エネルギーとの対応を維持する。

**Mandatory STOP：技術成果物の公開・照合後に停止。P1*科学計算は未承認・未実施。**
