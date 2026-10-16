# P1STAR-A-v1 Phase B 最終freeze — 2026-10-17

**状態：`FREEZE_COMPLETE / SCIENCE_EXECUTION_NOT_AUTHORIZED`。** 入力・source・環境・運用条件・未承認planを固定した。科学計算、因子適格性、CAR/CCR整理、固定word展開、係数条件生成・求解は0件。Science CLI、science worker branch、固定input loaderは呼び出していない。

## 正本と成果物

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。独立branch：`qc-p1star-phase-b-final-freeze-20261017`。base/技術driver固定commit：`d1d57110238d2ea283fb6f49bfcc519d2e8ef11e`。科学契約固定commit：`1771564d919837e2440a9fcb175ac054284a729c`。

読む順序は本書 → [未承認plan](execution_plan_draft.json) → [inputと意味のbinding](input_contract_binding.json) → [source identity](source_identity.json) → [静的audit](freeze_audit.json) → [provenance](provenance.json)。[科学契約](../p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md)、[資源追補](../p1star_science_driver_20261017/resource_policy_addendum.md)、[driver使用方法](../../../research_tools/p1star_driver/README.md)は既存履歴から継承し、変更・再生成していない。

今回のユーザー指示はfreezeとその引渡しの承認であり、科学実行承認ではない。AGENTS.mdのGitHub handoff規約に従い、GPTが確認できるよう必要な新規freeze資料だけをcommit・通常push・独立照合する。

## 固定した科学入力

[scientific_input.json](scientific_input.json)：**1271 bytes**、UTF-8、indent=2、末尾LF。固定契約の整数をそのまま保存した入力仕様であり、計算されたmatrix/vector artifactではない。

- 4 fermionic modes。L1/L2の一体入力行列は正本のまま。契約のmode 1..4とsourceのindex 0..3は順序を保った番号対応。
- Kは **L1²+L2²（単位重み）** と定義したまま。平方・交換子・CAR normal formは生成していない。
- 主判定はfull Fock、N=2は識別用sector。1個の共通bus、exact CCR、有限Fock cutoffなし。H_known=0、追加primitiveなし。
- 時系列word：`A,B,C,D,A,C,B,D,A,D,B,C`。積は `U12 ... U1`、各segmentは `exp(-i eta x_j G_j)`。
- x1〜x12はeta非依存の実数、閉box `[-1,1]`。η⁴まで展開し、目標logは `-i eta² K tensor I_b mod eta⁵`。

実行JSONにはdriverの厳密な文法が許す7 fieldsだけを置く。K、mode/bus数、full Fock主判定、位相・正規形などは固定sourceが実装するため、inputへ余分なkeyを追加しない。[input_contract_binding.json](input_contract_binding.json)に明示的に記録し、source hashへbindした。これは契約変更ではない。

`science_spec.py` のexpected定数をASTから限定したliteral grammarで静的に読み、JSONとの一致を確認した。module/functionをimport・実行せず、電子行列の積・交換子・rank・適格性を計算していない。

## 固定identity

| 対象 | SHA-256 |
|---|---|
| 入力bytes | `eb6581e351cabae863eab4bb40ef659a91655c25685fdd5a0fb988ab9a2521a5` |
| raw環境snapshot bytes | `f7ecc84b243071c810f0559d79e0fff29636d7b6ad92b8c9a2adcdf73a41dc66` |
| 両package combined code hash（driver互換） | `df274182322caff125a5c43f9a1d80bc407bb31feb7046a62195a115ac03a31e` |
| settings canonical JSON（driver互換） | `d564e2cc7e927fa815ed8da232f7ee4bfbe8e27ab8a38c1bbbc0c651753815ee` |
| operating_settings.json保存bytes | `458e9582a187345df402945c7b64e2b34c9399047d67ebb7b1905bedbd06081c` |
| 科学契約bytes | `96f6b22768e2a92944259a44a550cb734cb6f789ee8ea5a9a66193a1994887d6` |
| 資源追補bytes | `68908a78b3c79b53a6f0298c010852b6f907d3a9520af89871495adfa313e3de` |
| 未承認plan bytes | `d492a5daaf8eb0ccb968d25f5a30ca89960130a830ea73e696b16036fadd931a` |

hashのbyte数・Git blobは[provenance](provenance.json)と[source identity](source_identity.json)にも保存する。settings canonical hashと整形済みfileのbyte hashを区別する。combined code hashは `authorization.code_digest()` と独立したfile list計算で一致した。foundation→driverの順、各packageのsorted paths、`.py`/`.json`、tests directory除外という既存規則をそのまま使い、package別hash・Git tree・全tracked fileのbytes/blob/SHA-256も記録した。

## 実行環境

[environment_snapshot.json](environment_snapshot.json) は `collect_runtime()` のraw dictionaryを保存した、実際のpreflightと互換のsnapshot。CPython **3.11.1**、SymPy **1.13.3**、mpmath **1.3.0**、Z3 **4.13.3.0**。Python/libpython、installed package manifest、実際にmappedされたlibz3、Z3 CLIのbytes/hashとpathを含む。solver check、人工test、科学testは今回実行していない。

Interpreter：`/tmp/qc-p1star-foundation-20261017-4v_c3t_n/venv/bin/python`。既存隔離venvを再利用し、installや既存lockの改変はない。mapped libz3 SHA-256：`fa2f59a2be4292e8eefc4928f9cdc8eaad6f2ae8e44476fd67c1f03ab86e767f`。driver/foundation内のenvironment_lock.jsonは過去の技術snapshotのまま保存する。過去の「input未作成」「運用値未固定」という記録も当時の履歴であり書き換えない。

このvenvは `/tmp` にあるため、次回まで所在・bytesを保持する必要がある。消失・移動・package変更等で現在のsnapshotと一致しなければ実行せず、別環境へ勝手に差し替えない。新snapshotが必要ならfreeze変更として判断を受ける。branchを別pathへcheckoutした場合も、planのabsolute input/environment/cwd bindingを黙って変えない。

## 固定した実用運用値

[operating_settings.json](operating_settings.json) とplan内settingsは同一である。以下は今回選択・固定した次回承認対象であり、科学jobは起動していない。

| 設定 | 固定値 | 適用範囲 |
|---|---|---|
| wall_seconds | 1800秒（30分） | `supervise`起点からworker終了まで。gate・展開・solver・screen・worker trace/outputを同じ時計で監視。段階リセットなし |
| rss_bytes | 12884901888（12 GiB） | worker RSSを約20 ms周期で観測し超過時停止。job全体hard RAM capではない |
| address_space_bytes | 17179869184（16 GiB） | workerのRLIMIT_AS。仮想アドレス空間、RAM保証ではない |
| solver_timeout_ms | 900000（15分） | 1回だけのcheck。全体残り時間との小さい方を適用 |
| terms | 200000 | 自前TermLedgerのlive管理map entries。native内部・一時list等は対象外 |
| trace_events | 1000000 | provenance events。旧toy値20万から広げ、traceだけの早期停止を抑える。無制限にはしない |
| output_bytes | 19922944（19 MiB） | driverが管理するworker stdout/stderr captureと最終result envelope |
| solver_rlimit | null | 人工UNKNOWN用の極小resource countは使わず、wall/RSS/AS/termsで有限化 |
| 計算worker/CPU | 1 / 1 | 監視controllerを別に置く。許可CPUの最小値へaffinity、現在CPU0。native parallel無効、関連thread数1 |

旧toy設定をそのまま科学設定とせず、wall 30秒から30分、RSS 512 MiBから12 GiB、AS 2 GiBから16 GiBへ広げる。host read-only観測時は64 GiB弱の総RAM、約48 GiBのMemAvailableだった。値はplanにtimestamp付きで記録し、job quota・予約・将来の空き容量保証とはしない。次回、共有環境の空き容量を再確認し、不足なら開始せず、値の自動縮小・増額やretryをしない。

包括的native term計数、専用cgroup、厳密なjob全体16 GiB RAM enforcementは要求しない。cgroup再調査・変更・権限昇格による資源設定は今回行っていない。RSSはovershootし得てcontrollerを含まない。wallもsourceの実装範囲であり、controller前処理・最終JSON整形/保存、OS scheduling/kill遅延にまで厳密な30分を保証しない。この不足を「保証済み」としない。

traceを含む詳細結果は20 MiB枠に収まる保証がない。trace上限100万に達する前でも出力上限でINCONCLUSIVEになり得る。結果後にtrace削除・出力枠拡大・再実行して救済しない。変更が必要と判明した場合は別判断に残す。

## 一回限りの実行・保存計画（未承認）

run ID：**`P1STAR-A-v1-20261017-66736428e878`**。予約した識別子であり、実行回数・attempt消費数は0。

- 共通attempt directory：`/home/abe/myproject/Evaluation_numGate_highorder/.runtime/p1star_phase_b/attempts`
- 協調lock：`/home/abe/myproject/Evaluation_numGate_highorder/.runtime/p1star_phase_b/attempts/p1star-science-job.lock`
- 予約marker：`/home/abe/myproject/Evaluation_numGate_highorder/.runtime/p1star_phase_b/attempts/bd7a34d5ae7fe9564d34137d71fb3ef2f516bc0bcd2e5caab4810f2d5af95f14.attempted`
- 結果directory：`/home/abe/myproject/Evaluation_numGate_highorder/.runtime/p1star_phase_b/runs/P1STAR-A-v1-20261017-66736428e878`

これらのruntime directory/fileは今回作成していない。`.runtime` の内容をcommit/pushしない。次回、科学実行が承認された場合にだけ共通directoryと保存先を用意する。既存markerがあれば削除・移設して再利用しない。別worktreeでも同じ共通lockを使う。receiptは署名付きsecurity tokenではなく、実際の人の承認の記録である。

本planは **`explicit_user_approval=false`、`approval_reference=null`、`science_execution_authorized=false`**。科学実行承認を捏造していない。science CLIはこの状態なら承認gateを通れないが、今回確認のためにCLIを呼ぶこともしない。

次回、ユーザーがこのfreeze commit・run ID・入力/source/環境/契約/追補/設定identityを明示して1回のPhase Bを承認した後、実在する承認referenceを記録した**別のapproved derivative**を作る。凍結した草案は上書きしない。変更可能なのはauthorization metadata（`freeze_state`, `science_execution_authorized`, `approval.explicit_user_approval`, `approval.approval_reference`）だけ。input・source・環境・settings・path・run IDを維持し、derivativeのbytes/hashも実行receiptに残す。freeze値を変える場合は同じ承認の自動拡張としない。

metadata preflightが通った後、markerをO_EXCLで作成してから入力を読む。正本とのliteral照合後、最初の科学処理は**因子適格性gate**。不成立/未確定はINCONCLUSIVEで停止。gateが通った場合だけ、固定4次log→一つのfull Fock条件集合→1回のexact solver→SAT witness exact再照合→限定screenへ進む。別ansatz、別factor/sector、追加cleanup、数値fit、探索の繰返しはない。

result.jsonはbounded writerで保存し、driver上限19 MiBに対してruntimeの他のtext/metadataへ1 MiBを予約する。controller stderrは256 KiB、receipt等は残り768 KiB以内。合計20 MiB以内の保存運用とする。worker stderrはすでにdriverの管理captureへ合流する。追加のraw trace/SMTコピーを別fileへ複製しない。この外部writer/合計budgetはoperatorの実行手続きであり、固定driverが自動で全file総量をenforceするという主張ではない。書込み・容量・監視経路が用意できなければ開始しない。

run receiptはfreeze/approved plan/source/input/environment/settingsのhash、実行開始終了時刻、OS return code、driver status/停止理由、保存fileのbytes/hash、attempt消費・lock・所有workerの終了確認を含む。statusをprocessのexit0だけから認定しない。異常終了・外部controller障害・保存不足はINCONCLUSIVEとし、部分保存もhashと不足理由を残す。別jobを自動起動しない。

## 結果ごとのMandatory STOP

- 入力gate失敗、資源不足、timeout、backend不一致、UNKNOWN、異常終了、witness再照合不成立、出力不足：INCONCLUSIVEで停止。科学的な不存在としない。
- exact UNSAT：固定word・4次・全閉box・full Fock条件内のsolver依存結論として記録し停止。独立証明書の検証済みとはしない。sector限定構成一般を否定しない。
- exact SAT：witnessをexact保存・再照合し、限定screenを記録して停止。既知対応があればその対応の範囲を示す。screen不一致やCAR選択説明不足だけで新原理・GOへ格上げしない。

新証明、反例探索、新ansatz、再計算、詳細科学レビュー、原理の正式採択、他研究のSTOP解除は自動開始しない。T1-D、U1/U3/U4、第一・第二研究、FS-R1 Phase B未承認、PR Track A/B等の既存状態は本taskから変更しない。D1/D2を維持する。

## auditと保全

[freeze_audit.json](freeze_audit.json) はliteral JSON照合、bytes/hash、固定source/lockとの一致、環境metadata収集、承認false・reference null・attempt未作成を記録する。新規科学testも、既存74件の再実行もしていない。74 PASSはdriver固定commitの過去の人工技術記録として継承する。

既存source、科学結果、STOP/PAUSE、authorization、grant、manifest、他worktreeは変更対象外。保全snapshotの対象と限界、観測した並行変更はprovenanceへ記録する。新規freeze資料だけを明示stageし、通常push後にremote SHA・fresh Git・raw bytes・Git blob・SHA-256を照合する。provenanceは自己除外manifestとし、自身も公開後の独立照合に含める。公開完了状態は最終handoff/receiptで報告する。

**Mandatory STOP：このfreeze資料の公開・照合をもって停止。Phase B科学計算は未承認・未実施。残るのは、固定された1回の実行に対するユーザーの別途明示承認である。**
