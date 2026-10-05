# GPUサーバー側Codex：prospective cheap + all-candidate M1 prediction freeze

GPUサーバーのCPUを使います。GPU操作は禁止です。AGENTS.mdと本書を全文確認し、
今回のhandoff commitから専用branch/worktreeを作ってください。handoff commitは
`ec87adf35a5f8c2812557812ece34f3d41be3da1`の子孫であり、本書と新implementation manifestを含みます。
同名branch/worktreeがあれば上書きせず、衝突を報告してください。

推奨branch：`gpu-pf-study2-prospective-prediction-20261006`。
新worktreeは元P3と同じサーバーで作り、元のfrozen `.runtime`をread-onlyで参照します。
cloneだけではruntimeは得られません。移送・再生成・等価cacheへの置換は禁止です。
旧worktreeのreset/clean/stash、環境変更、他ユーザーのprocess操作は禁止です。

## 対象と停止点

承認書：`docs/second_study_v2/prospective_prediction_20261006/approved_prediction_authorization.md`。
machine contract：同directoryの`authorization.json`。
P1/P3 source/protocolは変更しません。Direction C、16条件・4familyの分母を保持します。

- P3 ready13条件×3の39 exact coordinatesのみ。candidate planはbyte-identical。
- LiH_R1.40/R2.60はdomain-ineligible、LiF_R2.60はinput-ineligibleとしてterminal seal。
- Cheap全39、B1 gamma4arm保存。B0=.8*t_ref、gamma1.10、benchmarkでありfallback/safe扱い禁止。
- Cheap hash/commit freeze後、cheap結果と無関係にM1全39。
- Primary rank8、prefix1/2/4/8、MGS2、既存gates/phase/widthをそのまま使用。
- Breakdown/lack of allowanceは記録してabstain。lower-prefix救済・rank変更・再試行禁止。
- Accepted positive finite allowanceのmin-budget、exact tieはearliest time。accepted0はcondition abstention。
- B2/H1/selective acquisitionは実装・実行しない。
- exact ground/fullPF/direct truth/gap/scoring/gamma_req/oracle/PF-H decompositionは全0。
- CH2は固定triplet population sector、global molecular ground claimなし。

成功statusは`prospective_candidate_M1_prediction_freeze_complete_review_required`。
Predictionをcommit/pushしremote/blob gateを確認した時点で停止、truthを1件も開かずGPTレビューへ戻します。

## 有効なallocationとruntimeを先に確認

P3 allocationは`2026-10-06T04:05:36.631599+00:00`で期限切れです。
期限を自己更新せず、schedulerまたはユーザーから有効なallocationと新出力先の承認を確認してください。
science承認はallocation期限の更新ではありません。未確認なら計算前で停止して不足項目だけ尋ねます。

上限は既存枠：CPU16、RAM128GiB、job12h、worker12GiB/2h、累積disk2GiB、reserve128MiB。
本実装は1 worker/BLAS1。旧P3 artifact/runtimeと新predictionを合算してdisk会計します。
旧private allocation/evidenceは旧P3 artifact、新allocation/evidenceは新出力`.private`内に保持しGitに入れません。
Renewalは枠内でも実際のauthority/evidence/start/expiryが必要です。

新出力は固定：`$PWD/artifacts/prospective_candidate_M1_prediction_20261006`。
新allocation JSONはその`.private/allocation.json`に保存し、P3と同じrequired quota/evidence fieldに加えて
`starts_UTC`と`cumulative_disk_roots=[元P3 artifact絶対path,新出力絶対path]`を記録してください。
`approved_output_root`は新出力そのもの。`workers=1`、`reserved_disk_bytes=134217728`。
quota値・expiry・evidenceは実際の承認から記録し、将来時刻やauthorityを捏造しないでください。

`RUNTIME_ROOT`は次の元P3 artifactの`.runtime`を想定します。実在pathを明示し固定してください。

```text
/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/gpu-pf-study2-prospective-preparation-20261005/artifacts/prospective_input_reference_preparation_20261005/.runtime
```

元INPUT_FROZEN、各runtime SHA/H/CISD/sector/group identityを照合します。terminal3条件のruntimeは開きません。
CH2 historyはP3のoriginal cutoff certificateを再利用し、計算後の履歴検索でunseenを再定義しません。

## 実行環境とsource gate

新worktreeで以下を設定します。Python/package/CUDA/driver/共有環境を変更しません。

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:.
PREDICTION_PYTHON=/home/AbeHiromu/venvs/trotter-common/bin/python
ALLOCATION_FILE="$PWD/artifacts/prospective_candidate_M1_prediction_20261006/.private/allocation.json"
RUNTIME_ROOT=/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/gpu-pf-study2-prospective-preparation-20261005/artifacts/prospective_input_reference_preparation_20261005/.runtime
"$PREDICTION_PYTHON" review_response/run_prospective_candidate_prediction.py verify-source
"$PREDICTION_PYTHON" review_response/run_prospective_candidate_prediction.py tests --label pre
```

source gateは inherited42 sourceとP3 review54資料をbaseのblob/SHAで照合し、新6sourceをsealed content commitで照合します。
fail/skip/identity mismatchなら停止。full legacy suiteはtruth-bearingなので実行禁止です。

## Cheapを一回だけ取得しcommit freeze

各CLIは自身のsignal wall/RSS監視を持ちます。native kernel中にも期限を守るため、scheduler/cgroupまたは
自身が起動したprocessの外側にwall watchdogを併用し、allocation残時間より長い実行を許さないでください。
以下の7200sは上限であり、有効な残時間が短ければ短縮して自身のprocessだけを管理します。

```bash
timeout --signal=TERM --kill-after=10s 7200s "$PREDICTION_PYTHON" -u \
  review_response/run_prospective_candidate_prediction.py cheap \
  --runtime-root "$RUNTIME_ROOT" --allocation "$ALLOCATION_FILE"
```

exit0、cheap PF/H-exp39/39、truth/GPU/B2/H1全0、39rows、13 decisions、terminal3を確認。
`STARTED.json`があるphaseは再実行しません。失敗時checkpoint/STOPPEDを保持し、科学・数値failureの救済retryは禁止です。
今回のwrapperはtechnical failureも自動retryせず停止します。

以下6ファイルだけをstage/commitします。progress/checkpoint/STARTED/private/runtimeはstageしません。

```bash
git add artifacts/prospective_candidate_M1_prediction_20261006/cheap/prediction.json \
  artifacts/prospective_candidate_M1_prediction_20261006/cheap/CHEAP_FROZEN.json \
  artifacts/prospective_candidate_M1_prediction_20261006/cheap/resource_audit.json \
  artifacts/prospective_candidate_M1_prediction_20261006/cheap/access_audit.json \
  artifacts/prospective_candidate_M1_prediction_20261006/cheap/source_audit.json \
  artifacts/prospective_candidate_M1_prediction_20261006/cheap/manifest.json
git commit -m "Freeze prospective cheap candidate predictions before unconditional M1"
CHEAP_COMMIT=$(git rev-parse HEAD)
"$PREDICTION_PYTHON" review_response/run_prospective_candidate_prediction.py tests --label mid
```

## Unconditional M1、post tests、global seal

```bash
timeout --signal=TERM --kill-after=10s 7200s "$PREDICTION_PYTHON" -u \
  review_response/run_prospective_candidate_prediction.py m1 \
  --runtime-root "$RUNTIME_ROOT" --allocation "$ALLOCATION_FILE" --cheap-commit "$CHEAP_COMMIT"
"$PREDICTION_PYTHON" review_response/run_prospective_candidate_prediction.py tests --label post
"$PREDICTION_PYTHON" review_response/run_prospective_candidate_prediction.py seal --cheap-commit "$CHEAP_COMMIT"
```

M1 rows39、PF/H-matvec各312以下かつ同数、primary unavailableはabstention。
Global条件16/family4、13予測+terminal3、missing0、truth/GPU全0。
raw M1 prefix diagnosticsはabstentionでも保存。inf widthはnull+nonfinite理由で保存し0扱いしません。
classical費用はcheap/M1別、group/component/projected eigensolveを隠さず記録。RSS peakは合計しません。
H exp内部matvecはunknownのまま、1と捏造しません。安全性/branch正解/width coverageは未評価。

最終commit対象はM1軽量6件、global軽量10件、pre/mid/postのtest JSON/log6件だけです。
下記scriptはその固定allowlistだけをstageします。`git add .`は使用禁止です。

```bash
"$PREDICTION_PYTHON" -c 'import subprocess; import prospective_candidate_prediction as p; import run_prospective_candidate_prediction as r; names=[p.OUTPUT+"/m1/"+n for n in (*r.M1_FILES,"manifest.json")]+[p.OUTPUT+"/global/"+n for n in (*r.FINAL_FILES,"manifest.json")]+[p.OUTPUT+"/"+label+"_tests."+ext for label in ("pre","mid","post") for ext in ("json","log")]; subprocess.run(["git","add","--",*names],check=True)'
git diff --cached --stat
git commit -m "Freeze all-condition prospective candidate and M1 predictions; truth unopened"
PREDICTION_COMMIT=$(git rev-parse HEAD)
"$PREDICTION_PYTHON" review_response/run_prospective_candidate_prediction.py verify-freeze --prediction-commit "$PREDICTION_COMMIT"
git push -u origin gpu-pf-study2-prospective-prediction-20261006
git ls-remote --heads origin refs/heads/gpu-pf-study2-prospective-prediction-20261006
```

push前にfetch/push双方がHIROMU1015の指定repositoryであること、stagedが上記22件だけであることを確認。
remote先端はPREDICTION_COMMITと一致必須。認証失敗時は未公開として報告し、force/API別repoへ迂回しません。
同名branch衝突でbranch名を変える場合は本commandのpush/ls-remoteもその実名へ揃えます。

## 最終報告

branch、bundle/content/P3/input/cheap/predictionの40文字commit、manifest/prediction SHA、読む順序と
GitHub commit固定リンク、16/13/3 inventory、action totals、M1 candidate/condition abstention数、missing数、
rank/gate/failure reasons、pre/mid/post tests、wall/RSS/disk、retry/denied-read/truth/GPU counters、remote一致を報告。
frozen runtimeやprivate allocation/evidence、pickle、matrix/vector、unitary、exact stateは公開しません。
status確認後に必ず停止し、truth/scoringの新承認を待ちます。
