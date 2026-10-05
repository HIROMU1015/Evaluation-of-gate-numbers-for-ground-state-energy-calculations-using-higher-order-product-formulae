# GPUサーバーCodex：16-condition prospective P3 input/reference preparationのみ

GPTのレビューをP1 protocol化し、一般分子reference-only wrapperとfocused testsをP2で固定しました。
今回は**実allocation・履歴・環境gateがすべて通った場合だけP3を実行**してください。
GPUは使いません。candidate cheap、M1、exact ground、direct truth、gap、scoringには進みません。

## 1. identity / authorization

- Published preflight base: `f5e737699e66731fcdd26c434652c4e62ca6b3c3`
- P1 protocol commit: `dc10db0e2b9be860239cb18b0c9275bdd24617d2`
- P2 implementation commit: `e9b0981ec4e809c0dbcc77bfcf5a6efa653f7bdc`
- 実行起点handoff commit：ユーザーのhandoff messageに示す40文字SHA。
  この指示書を含み、P2の子孫でなければならない。
- Protocol: `docs/second_study_v2/prospective_core_protocol_20261005/protocol.json`
- 条件・絶対geometry: 同directoryの `conditions.json`（16件）
- Grid binary64: `reference_grid.json`（34件）
- 実装SHA一覧: `implementation_manifest.json`（自己除外、42件）
- 承認原本: `approved_review.md`（LF化）。元添付SHA:
  `f2e20c32d8ecbdd3961da782264d82e45a469c284e95bb1ccf7b7f7b367e316c`

科学規則の正式な根拠は承認原本とP1。旧preflightの20条件案やH-chain候補比を使わない。
技術的実装選択は委任済みだが、科学条件・threshold・fit・gamma・rank・claimは変更不可。

## 2. worktree / environment

起点commitをoriginから取得し、祖先関係を確認して新規独立worktreeを作る。
推奨branch: `gpu-pf-study2-prospective-preparation-20261005`。衝突時は上書きせず連番。
既存worktreeのreset/clean/stash、main merge、force pushは禁止。
fetch/push URL双方が `HIROMU1015/*` でなければcommit/pushせず停止。

```bash
export PROSPECTIVE_PYTHON=/home/AbeHiromu/venvs/trotter-common/bin/python
export PYTHONPATH=src:review_response:.
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

Python/package/driver/共有環境を変更しない。旧truth-bearing `_prepare_system` を呼ばない。
CuPy import、GPU query/allocation/kernel、`nvidia-smi`、他人のprocess操作は禁止。

まずP2とsourceが同一であることを確認する。

```bash
git diff --exit-code e9b0981ec4e809c0dbcc77bfcf5a6efa653f7bdc -- \
  review_response/prospective_input_reference.py \
  review_response/run_prospective_input_reference.py \
  review_response/audit_prospective_ch2_history.py \
  review_tests/test_prospective_input_reference.py \
  docs/second_study_v2/prospective_core_protocol_20261005/implementation_manifest.json
"$PROSPECTIVE_PYTHON" -m pytest -q -rs \
  review_tests/test_prospective_input_reference.py -p no:cacheprovider
"$PROSPECTIVE_PYTHON" -c 'from pathlib import Path; from run_prospective_input_reference import source_gate; source_gate(Path.cwd()); print("source gates PASS")'
```

focused 41 passed、fail/skip 0を要求。NumPy/SciPy/PySCF/OpenFermionの実import/run、
loaded OpenBLASの実thread count=1もtests内で確認する。メタデータだけの確認では不可。
backend readiness失敗なら科学計算前に停止。全legacy testsは将来のglobal prediction freeze後。

## 3. CH2 history gate — サーバーで再実施

こちらでは二つのGit storeについて全到達可能commitのtracked text内容を確認した。
CH2 alias検索に加え、Python/JSONのliteral C/H/H geometryも検索し、過去実行の証拠0だった。
元のlocal-only refsとサーバーlocal-only refsは異なり得るので、この結果だけで実行しない。

サーバーのorigin refsをfetchし、shallowでないことを確認してauditを実行する。
stdout JSONを通常のログcaptureで新規private control directoryに保存する。
このauditはscientific actions/numerical imports 0。現在の候補結果を探索・選別するために使わない。

```bash
"$PROSPECTIVE_PYTHON" review_response/audit_prospective_ch2_history.py --project-root "$PWD"
```

全matching blobの内容・geometry ID・registry・executed artifact参照を確認して分類する。
今回の承認・設計・preflight・audit・synthetic test mentionを過去の分子実行と混同しない。
逆に過去のCH2科学実行が一つでもあれば、**P1で停止しGPT reviewへ戻る**。
HCN自動置換、別new family探索、12件だけでのscience開始は禁止。
unreadable textがあればreview未完了として停止。
scopeは `repository_tracked_family_unseen`。private/untracked/archive payload、binary、
unreachable、opaque unnamed dynamically-generated geometryまで不存在証明したと主張しない。

manual review後にserver history certificate JSONを作る（科学実行前、結果を見ずに）。

```json
{
  "classification": "repository_tracked_family_unseen",
  "positive_prior_science_evidence": 0,
  "manual_content_review_complete": true,
  "audited_tip_commit": "CURRENT_40_CHARACTER_HEAD_AFTER_FETCH_AND_SOURCE_FREEZE",
  "inventory_path": "server_history_inventory.json",
  "inventory_sha256": "ACTUAL_SHA256_OF_INVENTORY",
  "reviewed_blob_sha256": ["EVERY_MATCHING_BLOB_SHA256_FROM_INVENTORY"],
  "content_review_ledger": "retain per-match classification and reason"
}
```

`inventory_path` はcertificateと同directoryからの相対path。
全refsがinventoryと同じで、current HEADがaudit時tipそのものの間にinputsを実行する。
audit後にsource/refsを変更した場合は科学実行前に再audit。
後のinput/reference publicationを「過去CH2既使用」としてこのcutoff認定へ逆流させない。

## 4. 実allocation — host全体のCPU/RAMは許可ではない

usable CPU quota/affinity、RAM quota、job wall limit、writable disk quota/output locationを、
scheduler allocationまたはユーザーの明示quotaで確認する。証拠をhash固定する。
不明なら科学計算を始めず、不足quotaだけユーザーに確認する。128 CPU/1 TBを仮定しない。
scheduler予約・実使用RAM・output空き領域・job残時間は科学入力でなく技術gate。

private control directoryへ次のschemaの実数値JSONを作る。サンプル値では実行しない。

```json
{
  "verified": true,
  "authority": "scheduler_allocation",
  "usable_cpu_quota": "ACTUAL_NUMBER",
  "usable_ram_bytes": "ACTUAL_NUMBER",
  "job_wall_seconds": "ACTUAL_NUMBER",
  "writable_disk_quota_bytes": "ACTUAL_NUMBER",
  "approved_output_root": "ABSOLUTE_NEW_ARTIFACT_OUTPUT_ROOT_IN_THIS_WORKTREE",
  "workers": "ACTUAL_INTEGER",
  "worker_rss_limit_bytes": "ACTUAL_NUMBER",
  "worker_wall_seconds": "ACTUAL_NUMBER",
  "coordinator_reserved_ram_bytes": "ACTUAL_NUMBER",
  "reserved_disk_bytes": "ACTUAL_NUMBER",
  "expires_UTC": "ACTUAL_TIMEZONE_AWARE_JOB_EXPIRATION",
  "evidence": [{"path": "allocation_evidence.txt", "sha256": "ACTUAL_SHA256"}]
}
```

ユーザー指定quotaならauthority=`user_explicit_quota`。
workers ≤ CPU quota/affinity、workers×worker RSS reservation＋coordinator RAM ≤ usable RAM。
BLAS threadは各processで1。ディスクを16入力・reference・logsの累積保存用に予約する。
LiFの4900-dimensional sectorはfull dense group ensembleを保持しない。
runtimeはone-group CSR storage/component spectraとvector actionであり、full PFではない。

初回は逐次1workerでもよい。並列化するなら独立condition単位だけ、上限workersを超えない
bounded queueとRAM/disk予約をoperator側で管理する。runner自体は1 condition/1 process。
同conditionの二重起動は禁止。global input sealをreferenceが先行して越えてはいけない。
外部watchdogも自分のworker PIDだけに限定し、timeout/native-memory監視を行う。
runner内の定期RSS/wall checkはPythonでのcheckでありnative kernelのhard-cgroup保証ではない。
job wall期限を越えて継続しない。CLI全wall/RSSとnamed-stage wallを別々に記録する。

## 5. P3 inputs — 16件、状態方式を変更しない

環境・source・history・allocationが通ったらだけ、以下を行う。

- LiH: full (4e,6o), RHF、populations(2,2)、R=1.40/1.80/2.20/2.60 Å
- LiF: frozen lowest two canonical spatial core orbitals, (8e,8o), RHF、(4,4)、同R
- BeH2: linear symmetric、full(6e,7o), RHF、(3,3)、R=1.20/1.40/1.80/2.20 Å
- CH2: nominal triplet spin parameter2、ROHF、full(8e,7o)、(5,3)、
  R=1.00/1.15/1.40/1.70 Å、102°のdesign geometry。global molecular groundを意味しない。

absolute coordinatesはconditions.jsonそのものを使用する。fixed populationsはpure-S²証明でない。
CISDは同population-sectorのRHF/ROHF reference＋singles/doubles subspace。
PySCF RCISD/UCISDやUHFへ置換しない。CASCIはget_h1effのみ、kernel禁止。
SCF convergence/MO-occupation order mismatchはineligible、再ordering/状態切替による救済禁止。
Kは各conditionで独立計数し、current_m3のcanonical binary64 sequenceを使う。

以下のtask-specific変数を、確認した絶対pathで固定する。

```bash
export PROSPECTIVE_OUT="$PWD/artifacts/prospective_input_reference_preparation_20261005"
export PROSPECTIVE_ALLOCATION="ABSOLUTE_PRIVATE_CONTROL_PATH/allocation.json"
export PROSPECTIVE_HISTORY_CERT="ABSOLUTE_PRIVATE_CONTROL_PATH/server_history_certificate.json"
```

`PROSPECTIVE_OUT` はallocation approved_output_rootと完全一致しなければならない。
各condition ID（conditions.jsonに固定された16件）について**inputを一回だけ**実行する。
下記LiHは構文例。他conditionもこの同一commandへ固定IDを渡すだけ。

```bash
"$PROSPECTIVE_PYTHON" -u review_response/run_prospective_input_reference.py input \
  --project-root "$PWD" --output-root "$PROSPECTIVE_OUT" \
  --allocation "$PROSPECTIVE_ALLOCATION" --history-certificate "$PROSPECTIVE_HISTORY_CERT" \
  --condition-id LiH_R1.40
```

runtime bytesは `$PROSPECTIVE_OUT/.runtime/<condition_id>` のみ。
16件のterminal input identityが揃ってから、global input sealを作る。

```bash
"$PROSPECTIVE_PYTHON" review_response/run_prospective_input_reference.py seal-inputs \
  --project-root "$PWD" --output-root "$PROSPECTIVE_OUT" \
  --allocation "$PROSPECTIVE_ALLOCATION" --history-certificate "$PROSPECTIVE_HISTORY_CERT"
```

16個の `conditions/<id>/input_identity.json` と `INPUT_FROZEN.json` **だけを明示stage**しcommit。
失敗conditionを取り除かない。runtime、SCF/group logs、STARTED/checkpointをstageしない。
sourceはbyte-identicalのまま。global input commitを40文字で記録する。

```bash
git commit -m "Freeze prospective 16-condition input identities before reference"
export PROSPECTIVE_INPUT_COMMIT=$(git rev-parse HEAD)
```

## 6. P3 references — input commit/byte gate後にだけ

HEADがinput commitそのものでtracked worktree cleanを要求する。
INPUT_FROZENと16 input filesをcommit blobと照合し、runtime全allowlist/hashを確認してから
各conditionについてreference commandを一回だけ実行する。

```bash
"$PROSPECTIVE_PYTHON" -u review_response/run_prospective_input_reference.py references \
  --project-root "$PWD" --output-root "$PROSPECTIVE_OUT" \
  --allocation "$PROSPECTIVE_ALLOCATION" --history-certificate "$PROSPECTIVE_HISTORY_CERT" \
  --input-commit "$PROSPECTIVE_INPUT_COMMIT" --condition-id LiH_R1.40
```

34 points/eligible input、全34点後にfit。earliest window5、p4±0.2、R²≥0.999、floor5e-12 Ha。
`Im(vdot(exp(+itH)ψ_CISD,U_P(t)ψ_CISD))/t` を使用し、arg(echo)/tに変えない。
fit失敗は `reference_scale_unavailable_under_frozen_protocol`、
3候補 `{0.8,1.0,1.2}t_ref` の一つでも[0.02,1.8]外なら `candidate_time_domain_ineligible`。
後者の算術値は残せるが、execution-ready candidateとして採用・clippingしない。
入力ineligibleにもterminal reference recordを残す（actions 0）。

上限は**累積34 PF/34 H exponential per condition、全544/544**。
action checkpointはdispatch前に増える。途中失敗も消さない。
このimplementationはSTARTED markerによりscience retry 0。上限1のtechnical retry権限を
新しいoutput/marker削除/作用再実行へ使わない。失敗時は保全しreviewへ戻る。
internal expm_multiply H matvecはunknownと記録し1へ置換しない。
CISD subspace/group-component eigensolvesは別会計、exact-ground 0へ紛れ込ませない。

16件がterminalならread-only aggregation/sealを一度だけ実行。

```bash
"$PROSPECTIVE_PYTHON" review_response/run_prospective_input_reference.py seal-references \
  --project-root "$PWD" --output-root "$PROSPECTIVE_OUT" \
  --allocation "$PROSPECTIVE_ALLOCATION" --history-certificate "$PROSPECTIVE_HISTORY_CERT" \
  --input-commit "$PROSPECTIVE_INPUT_COMMIT"
```

focused testsを同条件で事後再実行。candidate absolute time/hex、16件の失敗理由・分母、
family4単位、sector/K/CISD dimensions、arm/stage別wall、RSS、共有/cache/CLI overheadを整理する。
max RSSを条件間で足して測定peakと呼ばない。並列reservationと実測process peakは別field。

## 7. publish and STOP

正式status:
`prospective_input_reference_preparation_complete_review_required`。
これはcandidate validation成功の意味ではなく、入力・reference準備の完了を意味する。
eligible fitが0でも規則を調整せず失敗理由を報告する。

commitするもの：16 reference_result.json、candidate_plan.json、report.json、manifest.json、
COMPLETE.json、sanitized history certificate/review ledger/allocation summary/test logs、handoff。
private allocation証拠に認証情報や私的情報があればraw公開せずhash+sanitized summaryのみ。
`.runtime`、pickle、matrix/vector、unitary、exact stateをcommit/pushしない。
必要軽量ファイルのみを明示stageし、result publication commitを作る。
許可 `HIROMU1015/*` research branchへ通常non-force pushしてremote SHAと取得可能blobを照合する。
GitHub handoffは必要資料の公開までが作業範囲。push失敗なら未完了として報告する。

最終報告：branch、handoff/P1/P2/input/result40文字commit、manifest/hash、16-condition status、
CH2 history scope、allocation根拠、reference counts≤544/544、candidate/M1/ground/direct/gap/scoring/GPU0、
focused test件数、私有runtime所在/byte identity、未確立事項、GPTレビュー用commit固定リンク。

**P3後は停止。候補cheap48点、全候補M1、global prediction freezeへの別承認を待つ。**
そのさらに後にtruth/scoring承認が必要。B2/H1修正、gamma/rank/grid調整、q=1例探索、
追加分子/geometry、certificate gap取得、研究RQ/claim変更は今回の範囲外。
