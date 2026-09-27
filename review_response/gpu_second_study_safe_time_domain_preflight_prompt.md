# GPUサーバー側Codexへの実行依頼：第二研究 safe-time-domain preflightのみ

第一研究に続く第二研究について、protocolとローカルsource identity検証は固定済みです。
GPUサーバーでは、Phase Aを開始する前の **読み取り専用preflightだけ** を実行してください。

今回許可するのは、branch/worktree作成、hash・source identity照合、全worktree・全Git ref・
untracked成果物を対象にした独立性検索、dependency/GPU memory確認、unit test、軽量auditの
commit/pushです。新規Hamiltonian・RHF/CISD状態・group spectrum・proxy値・direct truthを
一つも生成しないでください。Phase A/Phase B runnerを作成・実行せず、preflight結果を報告した
時点で停止してください。

## 固定版

- repository：
  `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- protocol commit：`804331ecc976b83ae880940719706c11999247bc`
- preflight実装commit：`3a0dd5684abd7039935c02c14b44e3cb24bb149a`
- protocol branch：`second-study-safe-time-domain-protocol-20260927`
- implementation branch：`second-study-safe-time-domain-implementation-20260927`
- protocol：`review_response/second_study_safe_time_domain_protocol.json`
- protocol SHA-256：
  `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- source/leakage audit：
  `review_response/second_study_safe_time_domain_source_leakage_audit.json`
- preflight runner：
  `review_response/run_second_study_safe_time_domain_preflight.py`
- focused test：
  `review_tests/test_second_study_safe_time_domain_preflight.py`
- 情報源：`multiple_window_consistency`だけ
- PF：`current_m3`だけ

implementation commitはprotocol commitを祖先に持つ必要があります。protocol JSONとSHA sidecarを
変更しません。

## 絶対に行わないこと

- LiF/HClのHamiltonian、RHF、CISD、exact stateを生成しない。
- proxy echo、PF action、group spectrum、direct PF eigenpairを一回も計算しない。
- Phase A、Phase B、新規direct truthを開始しない。
- 独立性に問題が見つかった場合に別分子、別geometry、別basisへ差し替えない。
- threshold、候補時刻、停止規則、`gamma=1.01`、`beta=1.2`を変更しない。
- 第一研究cache/pickleを独立4条件の入力としてコピー・流用しない。
- 既存worktreeをreset、clean、stashせず、mainへmerge・force-pushしない。

## branchとworktree

まず既存worktreeとuntracked成果物を変更せず、次を実行してください。

```bash
git fetch origin --prune
git cat-file -e 804331ecc976b83ae880940719706c11999247bc^{commit}
git cat-file -e 3a0dd5684abd7039935c02c14b44e3cb24bb149a^{commit}
git merge-base --is-ancestor \
  804331ecc976b83ae880940719706c11999247bc \
  3a0dd5684abd7039935c02c14b44e3cb24bb149a
```

preflight実装commitから独立worktreeと新規branchを作ります。推奨名は

`gpu-second-study-safe-time-domain-preflight-20260927`

です。同名branch/worktreeがあれば上書きせず連番を付けます。作成先は既存worktree外の新規path
とし、元worktreeのuntracked artifactを移動・削除しません。

## source identity検証

新worktreeでprotocol hashを明示的に照合してから、次を新規outputへ実行します。

推奨output：

`artifacts/server_second_study_safe_time_domain_preflight_20260927_3a0dd56/`

同名が存在すれば上書きせず連番を付けます。

```bash
sha256sum review_response/second_study_safe_time_domain_protocol.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python review_response/run_second_study_safe_time_domain_preflight.py \
  --project-root "$PWD" \
  --output artifacts/server_second_study_safe_time_domain_preflight_20260927_3a0dd56/local_source_preflight.json
```

preflight runnerは次をcurrent worktreeとsource commit blobの両方で照合します。

- protocol commit/hashとsource/leakage audit。
- base、evidence、S0、S4、regret、completion commitの正しい系譜。
- `paper/evidence`、`paper/figures`、data-use ledgerの固定hash。
- 第一研究S0/S4、regret decomposition、completion analysisの固定hash。
- protocol準備中の新規Hamiltonian/state/proxy/direct truthが全て0であること。

ローカルでは67 checks合格済みです。GPUサーバーでもfailed checkが0でなければ
`failed_source_identity`として停止してください。

H01/P03の元成果物も読み取り専用で存在確認・hash照合します。commit収録コピーだけを元成果物と
みなしません。少なくともP03は以下が一致する必要があります。

- manifest SHA-256：`25e0f759e9b6eca995da5056fea22a12290cb237b4c400d895ca39923df819f6`
- summary SHA-256：`0f0b2590faa278e7c96f7797b81b557544d4d4469b3f13a9079b71548054ce45`
- protocol SHA-256：`b0fc69d3ef89fcae28172ae1bd89ca0b192154ff86eed34410f73cdc2a770a56`

H01/P03は今回の計算入力ではなく、開発source identityと資源見積りの確認対象だけです。内容を
コピー、修正、再manifest化しません。実在path、照合対象、actual/expected hashをauditへ記録して
ください。

## GPUサーバー全域の独立性検索

Phase A前の最重要gateです。repository本体だけでなく、次をすべて検索してください。

- `git worktree list --porcelain`が示すすべてのworktree。
- 各worktreeのtracked/untracked `artifacts/`、`.runtime/`、log、CSV、JSON、pickle、npy。
- repository周辺のworktree保管directoryと、関連する一時・archive directory。
- 全local branch、remote-tracking branch、tagを含む全Git ref。
- tar/zip等のarchiveは、元archiveを変更せず一覧を取り、関連archiveは一時directoryへ読み取り展開
  して内容も検索する。

検索語は最低限、次のすべてです。

```text
LiF_active_eq_sto3g
LiF_active_stretch150_sto3g
HCl_full_eq_sto3g
HCl_full_stretch150_sto3g
LiF
HCl
1.5639
2.34585
1.2746
1.9119
```

各worktree/untracked treeでは`rg --hidden --no-ignore -a --files-with-matches`等を使い、`.git`
object directoryはfilesystem検索から除外します。Git履歴は別に`git grep`を全refへ実行します。
file path自体、archive member名、binary内文字列も対象にします。実行した検索command、root、開始・
終了時刻、hit path、file SHA-256、該当context、分類を保存してください。

次の既知のplanning-only fileには分子IDやgeometryが記載されているため、名前のhitだけでは
contaminationとしません。ただし実測PF誤差、QPE費用、proxy response、direct truth、独立条件の
生成済みHamiltonian/stateが含まれていないことを個別に確認します。

- `PF_second_study_safe_time_domain_protocol_20260927.md`
- `review_response/second_study_safe_time_domain_protocol.json`
- `review_response/second_study_safe_time_domain_source_leakage_audit.json`
- `review_response/gpu_second_study_safe_time_domain_execution_prompt.md`
- `review_response/second_study_safe_time_domain_guard.py`
- `review_tests/test_second_study_safe_time_domain_protocol.py`

今回のpreflight prompt自身と、preflight runner/testの固定文字列hitもplanning/validation codeとして
分離してください。既知file以外のhitを自動的に安全扱いせず、内容を確認します。

一件でも過去の独立4条件に対するPF error、QPE cost、proxy response、direct truth、数値結果を
発見した場合は、`no_go_independence_contaminated`を記録して停止します。候補条件を交換せず、
Phase Aを開始しません。分子名一覧、protocol、未実行のgeometry定義だけなら、planning/reference
である根拠をpathごとにauditへ残します。

## dependencyとGPUの読み取り専用確認

使用予定Pythonのversion、主要package version、CUDA/CuPy backendのimport可否を記録します。
import smoke testだけに留め、Hamiltonian/stateを作りません。

`nvidia-smi`でGPU index、model、driver、total/free memory、既存processを記録します。free memoryが
8 GiB未満なら`no_go_insufficient_gpu_memory`として停止します。今回GPU kernelは起動しません。

## test

まず集中testを実行します。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -m pytest -q \
  review_tests/test_second_study_safe_time_domain_protocol.py \
  review_tests/test_second_study_safe_time_domain_preflight.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

続いて全`review_tests`を実行します。test logにはcommand、Python executable、開始・終了時刻、
pass/fail/skip件数を残します。失敗時に科学的閾値やtestを緩めません。

## 成果物、commit、push、停止

preflight outputには少なくとも次を保存します。

- `local_source_preflight.json`
- `gpu_environment.json`
- `independence_search_inventory.json`
- `independence_search.log`
- `source_identity_audit.json`
- `focused_tests.log`
- `all_review_tests.log`
- `decision.json`
- `manifest.json`
- 全gate合格時だけ`PREFLIGHT_ONLY_COMPLETE`

`decision.json`のstatusは、全gate合格時に
`preflight_pass_phase_a_not_authorized`とします。Phase Aの`COMPLETE`を作りません。失敗時は
`failed_source_identity`、`no_go_independence_contaminated`、`no_go_insufficient_gpu_memory`、
`failed_tests`のいずれかを使い、`PREFLIGHT_ONLY_COMPLETE`を作りません。

pickle、npy、`.runtime`、archive展開物はcommitしません。軽量auditとtest logだけをpreflight branchへ
commitし、originへ新規pushして構いません。force-pushしません。

最終報告には以下を示してください。

- preflight branch、protocol commit、implementation commit、preflight結果commit。
- protocol hashと67 source checkの合否。
- 検索したworktree/ref/archive数、総hit数、planning-only hit数、疑わしいhit数と判定根拠。
- H01/P03および第一研究S0/S4/regret/completion source identity。
- Python/package/CUDA/GPU情報とfree memory。
- focused/full test件数。
- go/no-go statusと未解決事項。

報告後に停止してください。Phase A、Phase B、新規分子生成、proxy、direct truth、threshold調整、
別PF・別分子へ進まないでください。
