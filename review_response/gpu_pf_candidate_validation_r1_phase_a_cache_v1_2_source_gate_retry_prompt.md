# GPUサーバー側Codexへの再実行依頼：D2R R1 v1.2のみ

v1.1は本計算前のsource-identity gateで停止しました。protocol/amendment、Phase A runtime、
4 system cache、focused/full testsは合格しており、R1 output、exact ground、proxy、direct truth、
GPU操作はすべて0です。

停止原因は、portable-test v1.1で固定したtestファイルが、R1の元source一覧にも含まれていたためです。
v1.2ではそのtestファイル1件について、元blobとportable版の両SHA-256を固定して認証します。
その他の固定sourceはすべて引き続きsource commitとのbyte identityを要求します。

親指示

- `review_response/gpu_pf_candidate_validation_r1_phase_a_cache_execution_prompt.md`
- `review_response/gpu_pf_candidate_validation_r1_phase_a_cache_v1_1_retry_prompt.md`

の全科学規則を維持し、以下のsource-gate差分だけを適用してR1を新規branch/worktreeから一度
再実行してください。

## 固定版

- original cache実装commit：`fba3383c6db8bde905c2f7b131de21f1c03d43da`
- portable-test commit：`832ca7af1de55cb738dea7007331c59d29342730`
- source-gate実装commit：`47ef65e7ca3ed75a67fd5e485a7fb8b633c21e27`
- R1 protocol SHA-256：
  `186d2240bbf78733c1389fac66e2b261a7dfe50d8712b656ce0e1c45a6c67e49`
- Phase A cache amendment SHA-256：
  `a95a9abf87f1d428c35d34ed13cbea8c2ff930e91a3e5eb3a2550fd5d1dd1051`
- test portability amendment SHA-256：
  `9cc7b101fdcca2f696e0d2a7ed43f4564bc3b42e9cd5c38397943b1426572cc3`
- source-gate amendment：
  `review_response/pf_candidate_validation_r1_source_gate_amendment_v1_4.json`
- source-gate amendment SHA-256：
  `94fd553f6d600578ae3bdb97c1167e4054369ef0a0d7b58c3f6aecbb16dbeaad`
- source commit：`05649f1a7b6e405eadc2dbbdc0897836e0fa2f02`
- Phase A runtime inventory SHA-256：
  `5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91`

## 保存するv1.1停止

- branch：`gpu-pf-candidate-validation-r1-v1-1-20260928`
- HEAD：`832ca7af1de55cb738dea7007331c59d29342730`
- status：`failed_source_identity`
- focused：35 passed
- full：319 passed、1 skipped（pennylaneのみ）
- production source／既存artifact差分：0
- R1 output directory：未作成
- exact/proxy/direct/GPU counts：全て0
- worktree：clean

初回およびv1.1 branch/worktreeを変更、削除、reset、rebase、amendしません。

## 認証する唯一のsource差分

```text
path:
review_tests/test_second_study_safe_time_domain_execution.py

source-commit blob SHA-256:
a37901af437bea8f0a4fe3cc501f148279c1037a55ae924012632547360bdba1

portable current SHA-256:
b4735f7d81eb16a616a53710a9578170a5f4390e931a2864ac2ddd1765d004e0
```

許可する意味差分は`abs(recomputed-stored) == 1 ULP`から`<= 1 ULP`へのtest-only変更と
その説明commentだけです。このfileはR1 runnerのproduction import対象ではありません。

runnerは次を要求します。

- 上記path、元hash、現hashがamendmentと完全一致。
- 固定source一覧のそれ以外の全fileが`05649f1a...`とbyte-identical。
- 許可外source差分0。
- 未使用または実際には同一のoverrideも拒否。
- `source_manifest.json`に元hash、現hash、authorized overrideを記録。

## branchとworktree

```bash
git fetch origin --prune
git cat-file -e 47ef65e7ca3ed75a67fd5e485a7fb8b633c21e27^{commit}
git merge-base --is-ancestor \
  832ca7af1de55cb738dea7007331c59d29342730 \
  47ef65e7ca3ed75a67fd5e485a7fb8b633c21e27
git merge-base --is-ancestor \
  efea5fe0718c2c2623935949460498da066bdec3 \
  47ef65e7ca3ed75a67fd5e485a7fb8b633c21e27
```

`47ef65e7...`から独立worktreeと新規branchを作ります。推奨名は

`gpu-pf-candidate-validation-r1-v1-2-20260928`

です。同名があれば上書きせず連番を付けます。

## 再実行gate

親指示と同じ固定process environmentで、以下を最初から再実行します。

1. protocolと3 amendmentのSHA-256照合。
2. Phase A runtime 56 files、113,469,289 bytesと4 system cacheの全identity照合。
3. focused tests。fail/skip 0。
4. 全`review_tests`。fail 0、pennylaneだけ最大1 skip。
5. source gate。authorized override exact 1、unlisted difference 0。
6. 全gate合格時だけR1。
7. R1完了後のfocused/full tests。

R1 commandは親指示のcommandへ次の2引数を追加します。

```bash
  --test-portability-amendment review_response/pf_candidate_validation_r1_test_portability_amendment_v1_3.json \
  --source-gate-amendment review_response/pf_candidate_validation_r1_source_gate_amendment_v1_4.json \
```

完全な実行例：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_pf_candidate_validation_r1.py \
  --project-root "$PWD" \
  --protocol review_response/pf_candidate_validation_r1_protocol.json \
  --phase-a-cache-amendment review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json \
  --test-portability-amendment review_response/pf_candidate_validation_r1_test_portability_amendment_v1_3.json \
  --source-gate-amendment review_response/pf_candidate_validation_r1_source_gate_amendment_v1_4.json \
  --phase-a-root /home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694 \
  --output-dir artifacts/server_pf_candidate_validation_r1_20260928_fba3383
```

初回/v1.1停止ではoutputが作成されていません。存在確認後、存在しなければ上記新規outputを使い、
存在する場合は上書きせず連番を付けます。

## 完了、commit、停止

親指示のR1完了gate、計算count、commit除外物、最終報告項目は変更しません。追加で次を報告します。

- source-gate amendment hash。
- authorized override countがexact 1。
- 元/current test hash。
- unlisted source difference countが0。

軽量成果物とtest logだけを新規branchへcommitし、originへnon-force pushします。その後停止し、
R2、新方式、追加diagnostic、別分子・PF、threshold変更へ進まないでください。
