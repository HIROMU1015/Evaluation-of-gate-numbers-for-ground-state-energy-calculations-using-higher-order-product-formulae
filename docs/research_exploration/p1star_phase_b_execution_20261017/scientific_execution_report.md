# P1STAR-A-v1 Phase B 科学実行結果 — 2026-10-17

**計算完了。結果は `NO_SOLUTION_IN_FIXED_ANSATZ`、Z3のexact判定は `UNSAT`。** 固定された12 segment・全12実変数の閉box・4次formal-log・full Fock一致条件の範囲で不整合と判定した。P1*全般、別word/次数/box、sector限定構成一般の不可能性は認定しない。科学的GO・正式採択・既存研究のSTOP解除は行わない。

## 読む順序と実行承認

1. 本書
2. [科学結果summary](scientific_result_summary.json) と [全attempt来歴](campaign_attempts.json)
3. [係数条件原本](coefficient_conditions.json) と [exact solver入力](exact_solver_input.smt2)
4. [実行・回復protocol](execution_protocol.md)、[資源回復追補](resource_recovery_addendum.md)、[80件の人工テスト](recovery_04_technical_tests.json)
5. [result file audit](result_file_audit.json)、[source registry](source_registry.json)、[provenance](provenance.json)

ユーザーの最新指示「計算を行って　中断された場合は修正も行ってよいので計算完了まで進めて」を、固定問題の実行と技術的中断の修正・再実行の承認として記録した。[受領文](user_execution_authority.txt)、[実行承認記録](execution_authority.json)、各approved planが実際のreferenceを保持する。以前の未承認freezeやno-retryの記録は上書きせず、最新指示に基づくcampaignを別記録にした。

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。branch：`qc-p1star-phase-b-execution-20261017`。base freeze commit：`77f6b450ac6a4899b537e22420dfa8a7833bccf2`。元科学契約：`1771564d919837e2440a9fcb175ac054284a729c`。最終計算source commit：**`227d1541b98aa48147cf92cc91856da5cb87f1e6`**。

## 何を判定したか

4 fermionic modes、正本のL1/L2、K=L1²+L2²（単位重み）、N=2識別用、共通oscillator、固定word `A,B,C,D,A,C,B,D,A,D,B,C`、x1〜x12∈[-1,1]を維持した。主判定はfull Fock、目標は `log(U12...U1) = -i η² K tensor I_b mod η⁵`。次数・target・位相・primitive・boxを結果に合わせて変えていない。factorの置換、sectorへの救済、spin/点群制限、追加cleanup、数値fit、有限bus cutoffはない。

因子適格性gateは**通過**した。full FockとN=2で非可換性・二体非自明性・非退化をexactに確認した。N=2のdimensionは6、scalar+全一体作用のspan rankは16、Kを加えたrankは17。これらは今回の入力に対する計算結果であり、普遍的な定理ではない。sectorの関係をfull Fock同値判定へ流用していない。

4次formal-log生成後、full Fock CAR基底×exact Weyl bus基底の残差を実部/虚部に分けて**438本の多項式等式**を生成した。保存monomial entriesは**28,503**。係数はQ(i)からexact real rationalへ分解し、float・近似根・許容閾値を用いていない。

| 条件の種類 | 等式数 |
|---|---:|
| bus非identity residual | 356 |
| bus identityの一体residual | 20 |
| bus identityの二体residual | 50 |
| bus identityの高体residual | 12 |
| 合計 | 438 |

zero coefficientは式に列挙しないため、この入力ではscalarの非zero条件は生成されなかった。generatorはscalarも比較対象とし、targetに含まれる一体成分を捨てていない。高体残差をN=2で消えることにより省略していない。

## exact solverの結論と証拠の範囲

最終attemptはZ3 **4.13.3.0** のQF_NRA/NLSatへ、この438等式と12個の閉区間を渡し、1回のcheckで**UNSAT**を得た。これは有理数のroot探索失敗やtimeoutではなく、記録した閉box内の全実parameterを対象とするtrusted exact real solverの結論である。SAT witnessは存在せず、witness再代入は対象外。独立検証済みUNSAT certificateはない。数学的な根拠の信頼は生成source・exact normal form・Z3実装に依存する。

| identity | SHA-256 |
|---|---|
| 科学入力（全attempt同一） | `eb6581e351cabae863eab4bb40ef659a91655c25685fdd5a0fb988ab9a2521a5` |
| 係数条件canonical JSON | `5fb523ef2c39bb447783e779e6f04564a33a5bf585196c3b15caf0a2f4a2df9a` |
| solver入力SMT2 | `1ad8745ce781e9b471028e7e6102b79f535a1dcdab2fa670439d12524ed4e8bf` |
| 最終計算combined code | `81e798e87630c645557a64b2dc8bae2b04cf60465a5159d8b15f81164d17b17b` |
| 環境snapshot | `f7ecc84b243071c810f0559d79e0fff29636d7b6ad92b8c9a2adcdf73a41dc66` |

係数条件は1,660,955 bytesのcanonical JSONをworker生成時のhashと一致する形で保存した。SMT2は2,532,283 bytesで、solverが記録した入力text/hashそのまま。再求解・新しい証明・条件の変更はせず、file/hash・分類・sourceの静的auditだけを行った。

CPython3.11.1、SymPy1.13.3、mpmath1.3.0、Z3 4.13.3.0の既存隔離環境を再利用し、各attempt前に同じruntime snapshotを照合した。旧環境lockの改変・install・global package変更はない。

## 中断と技術修正

| attempt | source commit | 結果 |
|---|---|---|
| 01 | d1d57110238d2ea283fb6f49bfcc519d2e8ef11e | OUTPUT_LIMIT。詳細traceの保存上限超過、科学的結論なし |
| 02 | 0aebf2df13de19286b07030626348842e19798ee | pure CAR/Weyl結果をcacheして重複traceを除去。20万管理termsで停止、科学的結論なし |
| 03 | 82a55a4fbec165e681e8ea19def5f785dca67301 | 管理上限を200万へ変更。sourceで無効な次数のcross-product列挙を確認し、所有workerだけをSIGTERMで技術停止。UNSATとして扱わない |
| 04 | 227d1541b98aa48147cf92cc91856da5cb87f1e6 | η次数分類で不要な積の列挙を省き、同じ固定4次条件を生成。exact UNSATで計算完了 |

修正は正規形のmemoization、重複trace保存の変更、有限な管理term予算の拡大、もともと打切る次数の積の列挙省略、metadata進捗記録。電子因子・物理入力・同値判定領域・展開次数を変えていない。cacheは普遍的なCAR/CCRから得たpure operator wordだけを扱い、sector/factor固有の関係を入れない。first derivations、cache内容hash、reuse countersを保存する。初期の全重複traceと同一bytesだとは主張しない。

元74 testsを維持し、4次の非可換reference比較・known convolution・ledger cleanup・明示的な回復予算を追加した**80件の人工テストがPASS**した。最終テストのsource hashと実計算source filesが一致する。旧attemptとmarkerを消してやり直したのではなく、distinct run IDとplan/source/settings/hashを保存した。元driverの出力制限で失われた初回の内部判定について、推測でsolver結果を補っていない。

## 実測と保存

最終run ID：`P1STAR-A-v1-20261017-66736428e878-recovery-04`。launcher wallは**310.161秒（約5分10秒）**。形式log・条件生成は約270秒、solver段階（AST生成・入力検査等を含む）は残りの約39秒。科学benchmarkや資源優位の主張ではなくexecution metadataである。

管理terms peakは**465,502**（設定上限2,000,000）、観測worker RSS peakは**354,553,856 bytes（約338.1 MiB）**。12 GiB RSS監視、16 GiB RLIMIT_AS、1,800秒worker wall、900秒solver timeout、100万trace events、19 MiB管理出力、1 MiB外部metadata、1 math worker/1 CPUを用いた。native全termsの計数やjob全体RAM hard capを保証しない。

最終raw resultは6,059,379 bytes。全attemptの保存runtime text/metadataは約7,402,387 bytesで、公開用の係数条件・SMT2と合わせても20 MiBを下回る。原本は指定`.runtime`に保持し、`.runtime`自体、computed matrices/vectors、unitary、exact statesはcommitしない。公開summaryはtrace全eventを省き、係数条件とSMT2を独立artifactへ移したprojectionで、raw原本のbytes/hashを保持する。

全attemptのowned worker終了、stderr、OS return code、marker保持をreceiptで確認した。return code 0だけで成功を判定せず、worker/solverのstatusを照合した。final UNSAT後の追加科学jobは起動していない。

## 保全・次の判断

既存Evaluation94 worktreesのうち93は完全一致。rootは承認された`.runtime/p1star_phase_b/`の新規files追加だけで、これらを除いたporcelain状態、既存untracked metadata、staged/unstaged diff、index、dirty tracked bytes/hashは一致した。新しい実行用worktreeだけでsourceと公開資料を変更した。PRのroot untracked状態と新しい準備worktreeの並行変更を記録し、本taskから変更・復元・commit/pushしていない。全worktreeが不変だったとは記載しない。

T1-D、U1/U3/U4、第一・第二研究、FS-R1 Phase B未承認、PR Track A/B等の既存状態、D1/D2を本taskで変更していない。旧SOURCE、科学契約、過去結果、grant、authorization、STOP/PAUSE、manifestは保存した。新source版と現在の結果を別artifactとして引き渡す。

この結果を受けた別ansatz・sector限定条件・新原理探索の方針はユーザー/GPTの別判断である。今回の固定ansatzのexact不整合からP1*一般を排除せず、科学レビュー・正式採択・追加証明へ自動進行しない。

**固定問題の計算と技術回復は完了。結果・source・全来歴を公開・照合したら停止する。**
