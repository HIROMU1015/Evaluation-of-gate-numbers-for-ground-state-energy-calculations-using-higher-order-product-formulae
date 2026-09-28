# GPUサーバー側Codexへの実行依頼：D2R R1原因分離のみ

第二研究safe-time-domainは`complete_no_benefit`で正式完了済みです。研究方針を
練り直すため、R0 failure ledgerは固定済みで、R1の10個の既存選択座標だけを
事後的に原因分離します。

ローカル環境でのHamiltonian再構築は、固定11点bridgeの4点で`1e-10 Ha`を超えたため
正しく停止しました。閾値を緩めず、GPUサーバーに保存されている元Phase A runtimeの
4 system cacheを56ファイルすべてbyte-identicalに検証して読み込んでください。

今回許可するのはR1だけです。R2、新方式、新時刻、新分子、新PF、Phase A/B再実行、
新規direct truthは許可しません。R1結果をcommit・pushして報告した時点で停止してください。

## 固定identity

- source/R0 base commit：`05649f1a7b6e405eadc2dbbdc0897836e0fa2f02`
- R1 cache実装commit：`fba3383c6db8bde905c2f7b131de21f1c03d43da`
- branch：`research-revision-candidate-validation-r0-r1-20260928`
- second-study protocol SHA-256：
  `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- R1 protocol：`review_response/pf_candidate_validation_r1_protocol.json`
- R1 protocol SHA-256：
  `186d2240bbf78733c1389fac66e2b261a7dfe50d8712b656ce0e1c45a6c67e49`
- local bridge amendment SHA-256：
  `bd0f9c1d32db6fda391b912a769688e6f53d4b39ecdb2e8ce8ab196f1baf03fd`
- Phase A cache amendment：
  `review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json`
- Phase A cache amendment SHA-256：
  `a95a9abf87f1d428c35d34ed13cbea8c2ff930e91a3e5eb3a2550fd5d1dd1051`
- R0 coordinate plan canonical SHA-256：
  `84faad4338438d405e75d56dedd80233c5e86ea2b2a16412d48ad6c744759626`
- R0 ledger canonical SHA-256：
  `fe08eea8f9f8e101fa49661c6ea5a73b2863b7a4bc6eaa42df13e3dc96b200a0`
- frozen Phase A result commit：`efea5fe0718c2c2623935949460498da066bdec3`
- frozen prediction SHA-256：
  `3406d2f69237d95b14be298059f777df3fbd5043446add2c31559bf902a34b83`
- Phase A runtime inventory SHA-256：
  `5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91`
- runner：`review_response/run_pf_candidate_validation_r1.py`

protocol、10座標、分解式、materiality、2倍dominance規則、budget規則を変更しません。
closed second-study判定も変更しません。

## 保存する停止記録

次のローカル停止監査はGit収録済みです。

`artifacts/pf_candidate_validation_r1_local_environment_gate_20260928_5c36399/`

- status：`failed_environment_reconstruction_bridge`
- bridge：11点中7 pass、4 fail
- 最大差：`2.591319440669042e-09 Ha`
- exact ground state：0
- R1 selected-coordinate result：0
- new direct truth：0

GPU側でこの停止記録や過去のincomplete outputを変更、削除、再利用しません。

## 元Phase A runtime

次の絶対pathだけを読み取り専用で使います。

```text
/home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694
```

`.runtime`は56 files、113,469,289 bytesです。移動、コピー、再生成、修正、削除、
再manifest化しません。runnerはproxy/exact計算前に、全file set、relative/absolute path、
byte count、total bytes、SHA-256をcommitted inventoryと照合します。

固定system cache SHA-256：

- LiF eq：`115e0283566fe7c140ec8191b6885f75985e8f5ef97007154832720ce3ec688a`
- LiF stretch：`87a1bed28bb264842343b18c3854ee395e0ec2c2d92af0916b997a5f505bf8c9`
- HCl eq：`8733b890a2d1f449f30ac43290b00fc94d5b08129403bee735fb78fa308aeab7`
- HCl stretch：`8bac20c917e2242c1ecc84c9735bf0a93758e8b0211fe297551ae2026b1239f7`

一件でも不一致なら`failed_phase_a_runtime_identity`として、再構築や代替cacheを行わず停止します。

## 禁止事項

- Phase A/B runnerを再実行しない。
- Hamiltonian、RHF、CISDを再生成しない。
- direct PF eigenpair、direct shift、direct QPE costを新規計算しない。
- 10座標以外のproxyを取得しない。
- full PF unitaryを構築しない。
- GPU query、device allocation、kernelを実行しない。
- threshold、分解式、dominance規則を結果後に変更しない。
- R2、追加diagnostic、別分子・geometry・basis・PFへ進まない。
- 既存worktreeをreset、clean、stashせず、mainへmerge・force-pushしない。

## branchとworktree

```bash
git fetch origin --prune
git cat-file -e fba3383c6db8bde905c2f7b131de21f1c03d43da^{commit}
git cat-file -e efea5fe0718c2c2623935949460498da066bdec3^{commit}
git merge-base --is-ancestor \
  efea5fe0718c2c2623935949460498da066bdec3 \
  fba3383c6db8bde905c2f7b131de21f1c03d43da
```

`fba3383c6db8bde905c2f7b131de21f1c03d43da`から独立worktreeと新規branchを作ります。推奨名は

`gpu-pf-candidate-validation-r1-20260928`

です。同名があれば上書きせず連番を付けます。

## 固定process environment

Phase A/Phase Bと同じ既存Pythonを使います。

```text
/home/AbeHiromu/venvs/trotter-common/bin/python
```

各commandで次を置換設定します。

```text
PYTHONPATH=src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages

LD_LIBRARY_PATH=/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib
```

`PYTHONNOUSERSITE=1`、`PYTHONDONTWRITEBYTECODE=1`、
`OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`、`MKL_NUM_THREADS=1`も設定します。
environmentやpackageを変更しません。

## 計算前test

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests/test_pf_candidate_validation.py \
  review_tests/test_second_study_safe_time_domain_execution.py \
  -p no:cacheprovider
```

続いて同じenvironmentで全`review_tests`を実行します。focusedはfail/skip 0、fullはfail 0、
skipは既知の`pennylane`任意依存だけを最大1件許可します。

## R1実行

新規output：

`artifacts/server_pf_candidate_validation_r1_20260928_fba3383/`

同名が存在すれば連番を付け、既存directoryへ書きません。CPU単一processで実行します。

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
  --phase-a-root /home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694 \
  --output-dir artifacts/server_pf_candidate_validation_r1_20260928_fba3383
```

同一runの中断再開だけ、同じoutputの`.runtime`を使用できます。別run、ローカルretry、
Phase B direct cacheをコピー・流用しません。

## 完了gate

次を全件要求します。

- status：`r1_complete_stop_for_research_direction_review`
- Phase A runtime：56 files、113,469,289 bytes、全hash一致
- original system cache reuse：4
- Hamiltonian/CISD regeneration：0
- exact ground state：4、residual各`<=1e-10`
- coordinate rows：10
- strategy decomposition rows：16
- saved CISD proxy reuse：5
- new missing-coordinate CISD proxy：5
- new exact-state proxy：10
- new direct truth：0
- full PF unitary：0
- GPU operation：0
- 分解closure：各`<=1e-14 Ha`
- `R1_COMPLETE.json`が存在
- `r2_authorized=false`

計算後に同じfocused/full testsを再実行し、結果logをoutputへ保存します。科学結果や閾値を
変更しません。

## commit、push、停止

軽量成果物、resource/test logだけを新規branchへcommitします。`.runtime`、pickle、npy、
exact state、proxy cacheはcommitしません。originへ新規non-force pushします。

最終報告には次を示してください。

- branch、implementation/result commit、protocol/amendment/manifest hash。
- Phase A runtime identityと4 system cache hash。
- 10座標のCISD/exact/direct値と3成分、closure。
- 16 strategy行のdominant/mixed分類と、allowanceに対する各成分比。
- LiF平衡の大失敗、HClの小さな不足、HCl平衡の拡張成功、HCl伸長の停止判断について、
  R1結果から直接言える原因。
- local CISD/exact budget counterfactualのsafe数。
- 次に情報を1種類だけ取得する場合の候補。ただしR2を実行・実装しない。
- wall/CPU memory、計算count、pre/post test件数、未解決事項。

そこで停止してください。研究方針の選択はR1結果をGitHubから確認した後に行います。
