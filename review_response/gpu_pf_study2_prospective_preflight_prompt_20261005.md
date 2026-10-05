# GPUサーバー側Codexへの指示 第2研究prospective validationのCPU実行準備

## 今回の目的と停止点

強いCPUと条件単位の並列枠を利用し、新規条件によるprospective budget-safety validationを準備する。
今回はread-only preflightとprotocol案の作成だけを行う。本計算や数値pilotを開始する指示ではない。

Direction C、承認済みRQ・claim scope、既存formal resultは維持する。
研究全体の方針、対象条件、追加検証の範囲、未確定の科学規則はGPT側が判断し、
Codexは可用性・provenance・資源見積り・実装上の不足を整理する。

正常終了statusは `prospective_budget_safety_preflight_complete_review_required`。
これは計算準備の調査完了であり、`execution_ready`や未知条件へのsafe policy認証ではない。
確認不能な項目は `unresolved_requires_review` と記録する。
preflightが完了しない場合はpartial reportを残し、完了statusを付けない。

## 固定された起点と読む順序

Repositoryは次だけを使用する。

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

- 成果整理の公開snapshot: `e895870f16878ee4181b0e0dfe3159826a791563`
- 成果整理origin commit: `1883d8a75d5dfe83052c52da24c079ddfde2aa2f`
- 本指示を含むhandoff commit: ユーザーのhandoff messageに示す40文字SHA。
  上記snapshotの子孫であることを確認する。branch先端を無条件に代入しない。

最初に次を読む。

1. `AGENTS.md`
2. `docs/second_study_v2/prospective_server_preflight_20261005/README.md`
3. 同directoryの `authorization_scope.json`、`source_registry.json`、`bundle_manifest.json`
4. `docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md`
5. `docs/second_study_v2/result_synthesis_20261005/outstanding_claims.md`
6. `docs/second_study_v2/budget_safety_mechanism_20261005/quantity_dictionary_and_analysis_spec.md`
7. 本指示書全文。

handoff commitから新規独立worktreeとbranchを作る。
推奨branchは `gpu-pf-study2-prospective-preflight-20261005`。
既存branch/pathと衝突したら連番を付け、上書きしない。
サーバーのrepository実在pathを確認し、ローカルPCの絶対pathを流用しない。
既存worktreeをreset、clean、stashせず、mainへmerge・force-pushしない。

## 今回許可する作業

- CPU・RAM・ディスク・process affinity・cgroup・schedulerによる利用枠のread-only確認。
- 既存Pythonの実在path、version、必要packageのmetadata、BLAS設定方法の確認。
- Git管理下の既使用条件のmetadata inventoryと、アクセス可能な旧資料の使用履歴確認。
- 候補分子・geometry・basis・sectorについて、文献や既存metadataに基づく可用性調査。
- 既知の軌道数・電子数・spin populationからの組合せ算術によるsector次元見積り。
- 保存済みstage timingsとmatrix storageの算術による資源見積り。
- 科学計算を実行しないprotocol draft、parallel plan、未解決一覧、handoffの作成。
- 必要な軽量資料だけのcommitと、許可repositoryへのnon-force push。

外部文献を利用する場合は一次資料を確認し、URL・確認範囲を残す。
過去の数値結果を候補選択の根拠にしない。旧資料の読取は使用履歴metadataの抽出に限定する。
private runtimeを開いたり、旧truthの数値を分析したりして候補を選ばない。

## 今回実行しないこと

SCF、Hamiltonian/CISD生成、PF/H action、reference-grid取得、cheap candidate取得、
Arnoldi/M1、exact ground、full PF matrix、direct truth、target gap、performance scoringは全て0。

GPU query/allocation/kernel、CuPy import、`nvidia-smi`も0。
CPU/BLAS速度を測る数値benchmarkや「小さい1点だけ」の科学計算も実行しない。
package、Python、CUDA、driver、共有環境を変更しない。
他ユーザーのprocessへ介入せず、schedulerや利用申請を迂回しない。
B2/H1 gateの修正、gamma/width/rank調整、q=1探索、新PF、H-chain追加、
geometry sweepの別実験、離散QPE resource modelへの変更は行わない。
既存prediction、truth、budget、formal result、主解析・主図を変更または再実行しない。

## サーバーのCPUとRAM確認

物理CPU数・logical CPU数・affinity上限と、実際に使用を認められたCPU枠を分ける。
RAM総量・現在のavailable・cgroup/job memory limit・他ジョブの予約を分け、
「機械全体の空き」を「自分の割当」と解釈しない。
`/proc`、`lscpu`、`free`、`df`、自分のcgroup/scheduler metadata等をread-onlyで確認できる。
credential、token、全environment、他ユーザーの詳細process一覧はログへ出さない。

利用枠が不明なら `allocation_unverified` とし、並列数は未確定のままにする。
Pythonはサーバー既存環境を明示的に一つ提案する。古いサーバーpathを無条件に採用しない。
実際の数値library importがGPUや自動初期計算を起動しないことを確認できなければ、
package versionはmetadataだけで調査する。インストールや修復はしない。

## 未使用条件と候補inventory

規模の構想は20〜40 conditions、各3候補時刻である。
4〜6 molecular families × 4〜6 geometriesは例であり、確定したCartesian productではない。
LiH、LiF、BeH2、CH2、HCNも例示で、採用済み・未使用確定ではない。

各候補について以下を記録する。

- molecule/family、geometryと単位、charge、spin、basis、active/frozen-core案。
- 既使用conditionのidentity、source path、origin/result commit、verified snapshot commit。
- `condition_unseen`、`family_unseen`、`previously_used`、`unverified`の区別。
- 過去に使ったstate、basis、geometry、PF、time contractとの一致・相違。
- 使用履歴を調べたrefs・archives・accessible metadataの範囲と、未取得範囲。
- 軌道数/electron population/sector次元の根拠、見積りか保存実測値かの区別。
- 入力生成法、RHF/CISD・open-shell等の対応可否、現在の実装との差分。
- feasible / infeasible / unknownと、その理由。安全性やspectral有利性を理由にしない。

Git snapshotにない過去branchやローカル旧資料が未調査なら「新規」と断定しない。
同じfamilyの未使用geometryはnew conditionであって、new-family holdoutではない。
公開Git履歴・artifact manifest・source registryを先に調べ、全巨大JSONやruntimeを無差別に開かない。
必要に応じて `rg --files` と限定した `rg` を使用する。
使用履歴が不明な候補をprospective test setへ自動採用しない。

strataの提案は分子構造、geometry、polarity、電子数、sector size等の事前metadataから行う。
cheapの大小・sign flip・q=1・M1が勝つ条件を探索してstrataを作らない。
weak/strong correlationはこの段階ではgeometry由来の設計意図であり、実測済み性質としない。
closed-shell以外は別stratum案とし、対応state recipeの承認前に追加しない。

## 条件単位の並列CPU計画

将来の主計算は、独立conditionごとにworker processを分ける構成を第一案とする。
各worker内はまずBLAS thread 1を提案し、nested parallelismを避ける。
多thread案を併記する場合も、thread数を最適化する数値benchmarkは今回行わない。
SciPyのBLAS/LAPACKは別途threadを持ち得るため、process数だけではCPU利用枠を管理できない。
参考: [SciPy公式の並列実行説明](https://docs.scipy.org/doc/scipy/tutorial/parallel_execution.html)。

将来の実行環境案には以下を含めるが、まだnumerical runnerを起動しない。

```text
PYTHONNOUSERSITE=1
PYTHONDONTWRITEBYTECODE=1
OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

coordinatorだけがGit index/commit/pushを扱い、workerは固有output directoryへ書く。
shared cacheはsealed/read-onlyとし、worker間でmatrix/vectorを無制限に複製しない。

phase別にworker上限を提案する。input、prediction、dense truthの並列数は同じでなくてよい。
CPUについて `P * threads_per_worker <= allocated_CPU_budget` を満たし、
RAMについて同時workerの予約合計とcoordinator/cache/OSの余裕が割当内に収まるよう設計する。
heterogeneous sectorでは一律process数だけでなくmemory-aware queueを提案する。
割当、各worker予約、余裕の値は承認前のproposalと明記する。

complex128 dense matrix 1枚は `16*d*d bytes`。
full PF、Schur、eigenvectors、solver workspace、H、temporary copies、input/cacheを別に積算する。
one matrixの容量やGPU VRAMだけでtruth feasibilityを決めない。
truthはcondition内の3座標を原則逐次処理し、各座標のmatrix lifetimeを分離する。

保存H8のsector 4900ではdirectのnamed stageが約479 s/座標、
peak RSSが約2.39 GiBだったが、同条件・CPU単一process/BLAS thread 1の歴史的実測である。
server/new moleculeの速度保証・RSS上限ではない。過去preflightの約226.5 s予測は実測を過小評価した。
この参考値から大規模batchの速度や並列数を確約しない。
H8の旧1800 s/4 GiB上限も新batchへ自動継承しない。

aggregate makespan、worker wall合計、CPU time、stage wall、RSS peakを別fieldで保持する設計にする。
個別peak RSSの合計を実測concurrent peakと呼ばない。
PF action、H exponential action、H matvec、input/preprocessing/cache cost、decision costもphase別にする。
未計測の内部matvecはunknownとし、H exponential 1回をH matvec 1回に置換しない。
quantum budgetとCPU秒を直接加算せず、end-to-end/net advantageは未確立として扱う。

## Protocol案で未確定事項を明示する

最低限、次を `unresolved_requires_review` または根拠付きproposalとして整理する。

1. 最終condition一覧と事前strata、basis/active space、charge/spin、state recipe。
2. `current_m3`のgroup order/coefficient/energy origin/sector identityとKの計数法。
3. 一般分子のtruth-free reference、t_ref算出rule、grid上限、fit failure handling。
4. 各conditionの3候補、baseline T0/B0、beta/epsilonの単位・値、fallback。
5. Fixed B1 gamma `1.01,1.02,1.05,1.10`のbudget/selection規則と適用可能領域。
6. M1は全候補か事前metadataだけから定めるsubsetか、rank/reference/width/adoption規則。
7. same-H ground、physical branch/alias、direct scorer、gap定義、continuationとnumerical gates。
8. phase別CPU/thread/RAM/wall/I/O上限、全体上限、own-process watchdog。
9. technical retryの上限、checkpoint hash、numerical failureとtechnical failureの区別。
10. reference不成立・abstention・branch indeterminate・resource stop・欠測の記録と分母。

HFとH-chainのnative contractは異なる。
H-chainの34点grid、leading_fit、時刻比やB0を一般分子へ無断で流用しない。
M1のm=8も全条件へ暗黙適用しない。rank-aware規則は結果前に承認する。
時間やallocationを満たさない候補をbasis変更で救済せず、変更案は別レビューへ戻す。

## 将来承認後の実行順序

次は設計案であり、この指示だけでは実行しない。

```text
対象条件と全科学規則の承認およびprotocol commit
  -> implementation seal と truth-free tests
  -> input identity と referenceおよびexact candidate coordinatesのfreeze
  -> cheap取得 と 固定B1 decision
  -> 事前固定した全候補またはsubsetのM1取得 と decision
  -> 全conditionのprediction commit と hashおよびbyte gate
  -> その後だけ same-H ground と direct truth
  -> truth freeze
  -> immutable scoring
  -> GitHub資料公開 と GPT review stop
```

candidate時刻はruleをprotocolで先に固定し、truth-free reference後にabsolute timeと
binary64 float.hexをfreezeする。reference不成立は適用不能として記録し、別ruleで救済しない。
全対象conditionのpredictionをfreezeするまで、どのworkerも新truthを開かない。
M1はtruth前であり、truth後に「有望な条件だけ」計算してはならない。
最終freezeにはM1のabstention/fallbackも含め、scorerはprediction/selector/budget/widthを変更しない。

今回は現B2/H1を主運用方式として復活させない。
selective q経路を含める必要性は別承認であり、含めるならq freeze前にM1を読むことはできない。
既存full/legacy testにはtruth読取があるため、prediction前に無差別実行しない。
新規truth-free focused testsとtruth後のtestsをprotocolで分け、既知legacy failureを隠さない。

## 解析とclaim scope

signed shiftとabsolute PF errorを分け、continuous_rotation_cost_proxyをprimary候補とする。
整数化したQPE queryや新resource modelへ自動移行しない。

以下は既存specに沿う将来のscoring定義案であり、今回数値を取得しない。
`e=abs(delta_direct)`、`c=abs(delta_cheap)`、`u=e-c`。
同時刻の `B_gamma=gamma*beta*K/[t*(epsilon-c)]` が成立する領域で
`M_gamma=(1-1/gamma)*(epsilon-c)`、`slack=M_gamma-u` を使う。
gamma=1でもslackを使い、marginで割った比率は作らない。
`gamma_req=(epsilon-c)/(epsilon-e)` は両allowanceが正の領域だけのtruth diagnostic。
e>=epsilon等はinfeasible/indeterminateの理由を残し、小さいbudgetへ置換しない。
最終safetyは `e + beta*K/(t*B_frozen) <= epsilon` とし、branchが認定できない場合は
safeにせずindeterminateとする。truthを使ってbudgetを増減させない。

slackによるsafe判定は同じbudget式の同値変形であり、未知系へのpredictive certificateではない。
prospective studyは結果前に固定した予算の安全性・適用性・残余headroomを評価する。
native候補内のcost-free oracle、実M1のpoint/width/abstention、同時刻比較と時刻選択を分ける。
PF/H-reference分解は同一H、energy origin、sector、physical branchを確認できる場合だけ行う。
gapを取得するかとその範囲も別承認であり、certificate用の追加gap取得は行わない。

3時刻を3独立sampleと数えず、family内の複数geometryの依存も明記する。
frozen / attempted / reference-eligible / predicted / truth-valid / scoredを別分母にする。
failureを条件一覧から事後除外・置換して成功率を改善しない。
未知条件の結果を見てgamma、threshold、width、rank、selectorや主claimを変更しない。

## 必須成果物とGitHub公開

新しい `docs/second_study_v2/prospective_server_preflight_result_YYYYMMDD/` に以下を作る。

- `report.md`: 実施範囲、確認できたこと、未解決事項、計算0、次の承認要求。
- `hardware_and_allocation.json`: 実測時刻、CPU/RAM/利用枠、environment metadata、unknown。
- `candidate_inventory.csv`: identity、使用履歴、novelty区分、dimension、可用性と除外理由。
- `parallel_resource_plan.md`: phase別queue/thread/RAM/wall案、見積り根拠と非保証。
- `protocol_draft.md`: frozen継承項目、proposal、未確定項目、barrierと停止点。
- `source_registry.json`: origin/result commitとverified snapshot commitを別fieldで記録。
- `access_and_operation_audit.json`: action/eigensolve/ground/truth/gap/GPU/scoring全て0。
- `bundle_manifest.json`: 軽量全件hash、`manifest_self_excluded: true`。
- `handoff.md`: repository、branch、commit固定リンク、読む順序、GPTに必要な判断。

metadata調査自体ができなかった項目も成果物に明示し、実測値を捏造しない。
最終チェックはリンク、CSV/JSON、hash、source/blob、禁止操作0、dirty状態の保持に限定する。
実施していない数値testsをpassedと記載しない。

coordinatorが必要な軽量ファイルだけを明示的にstageし、local commitを作る。
originのfetch/push URLが `HIROMU1015/*` であることを再確認してnon-force pushする。
remote branch先端40文字SHAを照合し、fetch可能性と必要blobを確認する。
push不能ならhandoff未公開と報告する。新commitは科学計算実行許可を意味しない。
secret、private runtime、pickle、matrix/vector、unitary、exact stateは公開しない。

最後にpreflight status、branch/commit/hash、実際の利用枠、候補coverage、
parallel proposal、未確定contract、GPT側の承認待ちを報告して停止する。
続けてinput生成、reference取得、prediction、truthへ進まない。
