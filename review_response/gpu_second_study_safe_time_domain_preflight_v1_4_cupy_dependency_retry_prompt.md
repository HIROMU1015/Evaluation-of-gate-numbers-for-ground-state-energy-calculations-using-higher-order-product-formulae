# GPUサーバー側Codexへの再実行依頼：第二研究preflight v1.4のみ

v1.3 preflightは環境identity gateで正しく停止しました。許可済み
`cupy-cuda12x==13.6.0`がMETADATAで必須依存`fastrlock>=0.5`を宣言し、import時に同じ固定overlayの
`fastrlock==0.8.3`を読み込む一方、v1.3はCuPy以外のoverlay distributionを禁止していたためです。

v1.4ではCuPyと、その固定必須依存fastrlockの2 distributionを事前固定します。この規則で
**preflight全体だけを新規branch/outputへ一度再実行**してください。過去のbranch、commit、outputを
変更せず保存し、Phase A/Bや科学計算へは進まないでください。

## 固定版

- protocol commit：`804331ecc976b83ae880940719706c11999247bc`
- protocol SHA-256：
  `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- v1.3 review済みbundle commit：`25a4a415609189ce3333c380e7c55a76d76e401f`
- v1.3停止commit：`17422078d27bf3fc9e395719d335cd9ffa0e08a8`
- v1.4 amendment commit：`9e0afa0dda26bc44d94a998739ef0ba103889ac1`
- v1.1 amendment SHA-256：
  `218d325d2b13eea24196302a52e4a1a3e34ae92973518b61835bf2ad3974759d`
- v1.2 amendment SHA-256：
  `ab87da7c42aba20658e5f5d4a204cdf761c50f0814d24719a36e72be674da77e`
- v1.3 amendment SHA-256：
  `c8ec1925f2ad8f2dbb0b3e466514cd8fb0d70d39c58ee538e3ea5ff4e8e7d6ac`
- v1.4 amendment：
  `review_response/second_study_safe_time_domain_preflight_cupy_dependency_amendment_v1_4.json`
- v1.4 amendment SHA-256：
  `849542cb18c03356d0224e28905fddd1fbb8b912b92a01621d03843c810b57e3`
- source runner：`review_response/run_second_study_safe_time_domain_preflight.py`

protocol、v1.1/v1.2/v1.3 amendment、source runner、科学規則は変更しません。

## 保存する過去の記録

少なくとも次の5 result commitと対応branch/outputを変更、削除、再利用しません。

- `e1891dfd24ec5f0064b0598e51eb260073fd2b1e`：初回`failed_source_identity`
- `b520f9bd8f575456531e7c0b0f2692973b436e21`：v1.1 `failed_environment`
- `fd827f50dcbe64f8e2ea9d931cfdf2dd8eea4480`：strict v1.2
  `failed_environment_identity`
- `ef2dc7443092e93d09ead2fbf717645362fe4189`：adapted evidence
  `preflight_pass_phase_a_not_authorized`
- `17422078d27bf3fc9e395719d335cd9ffa0e08a8`：v1.3
  `failed_environment_identity`

v1.3停止ではsource runner以降は未実行で、Phase A/B、科学計算、GPU allocation/kernel、環境変更は0です。

## v1.4で変える唯一の規則

v1.3のprocess限定overlayをそのまま使い、許可するoverlay distributionを次の2件として固定します。

1. `cupy-cuda12x==13.6.0`
   - RECORD SHA-256：
     `374e873c946b8fb847925051ccd22b534660b480ae4d1c01aea1f540dadec401`
   - 所有top-level module：`cupy`、`cupyx`、`cupy_backends`
2. `fastrlock==0.8.3`
   - RECORD SHA-256：
     `0368d7063abcf0dfe42c68e6509edaaa6337a9aaa0c0750289884b82474d3aac`
   - 所有top-level module：`fastrlock`
   - 許可根拠：CuPy METADATAの必須依存`fastrlock>=0.5`

`cupyx`と`cupy_backends`は別distributionではなく、CuPy RECORDが所有する構成moduleとして扱います。
これ以外のoverlay distributionを一件でも検出したら`failed_environment_identity`として停止します。

## 固定process environment

Python：

`/home/AbeHiromu/venvs/trotter-common/bin/python`

`PYTHONPATH`：

```text
src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages
```

`LD_LIBRARY_PATH`：

```text
/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib
```

全commandで継承値をappendせず上記値へ置換し、`PYTHONNOUSERSITE=1`、
`PYTHONDONTWRITEBYTECODE=1`を設定します。environmentをactivateせず、package/libraryのinstall、
update、downgrade、修復、コピー、shell設定変更をしません。

## branchとworktree

```bash
git fetch origin --prune
git cat-file -e 17422078d27bf3fc9e395719d335cd9ffa0e08a8^{commit}
git cat-file -e 9e0afa0dda26bc44d94a998739ef0ba103889ac1^{commit}
git merge-base --is-ancestor \
  804331ecc976b83ae880940719706c11999247bc \
  9e0afa0dda26bc44d94a998739ef0ba103889ac1
git merge-base --is-ancestor \
  25a4a415609189ce3333c380e7c55a76d76e401f \
  9e0afa0dda26bc44d94a998739ef0ba103889ac1
```

v1.4 review済みbundle commit（固定版へ後から追加されるcommit）から独立worktreeと新規branchを
作ります。推奨名は

`gpu-second-study-safe-time-domain-preflight-v1-4-20260927`

です。同名があれば連番を付けます。既存worktreeをreset、clean、stashせず、mainへmerge・
force-pushしません。

推奨output：

`artifacts/server_second_study_safe_time_domain_preflight_v1_4_20260927_9e0afa0/`

既存directoryへ書かず、過去output/cacheをコピー、入力、再開に使いません。

## environment identity gate

最初に固定process environmentで読み取り専用identity/import smoke testを実行します。

- protocolと4 amendmentのSHA-256を照合する。
- v1.3で固定したPython、primary package、NVIDIA distribution、CUDA library identityを再照合する。
- CuPyとfastrlockのdistribution version、dist-info path、METADATA/RECORD pathとSHA-256を記録する。
- 両RECORD SHA-256を上記固定値と一致させる。
- 各METADATAと実際に読み込むpackage/module fileをRECORD記載digestに対して検証する。
- CuPy METADATAに`fastrlock>=0.5`が必須依存として存在することを確認する。
- `importlib.metadata.packages_distributions()`とRECORD ownershipを使い、
  `cupy`、`cupyx`、`cupy_backends`をCuPy、`fastrlock`をfastrlockへ分類する。
- fresh child processでCuPy import前にfastrlockが未load、CuPy import後に固定overlayからloadされたことを
  記録する。
- loaded overlay moduleの所有distributionを全件列挙し、許可2件以外が0であることを確認する。
- Qiskit Aer extensionの`ldd`結果、NVIDIA distribution/RECORD hash、実際のshared-library解決pathを
  記録する。

import smokeだけに留め、CuPy array作成、device query、device allocation、GPU kernelを実行しません。
Hamiltonian/state/proxy/PF action/group spectrum/direct truthも生成しません。

## source identityと残りpreflight

environment gate合格後だけ、固定process environment下で次を新規に実行します。

1. source runnerと67 checks。
2. H01/P03元成果物identity。
3. 全worktree、全Git ref、untracked artifact、binary、log、archiveを対象にしたLiF/HCl独立性検索。
4. `nvidia-smi`によるGPU identity、process、各GPU free memory 8 GiB以上の確認。
5. focused tests。
6. 全`review_tests`。
7. decision、manifest、全成果物SHA-256の照合。

source runner：

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python \
  review_response/run_second_study_safe_time_domain_preflight.py \
  --project-root "$PWD" \
  --output artifacts/server_second_study_safe_time_domain_preflight_v1_4_20260927_9e0afa0/local_source_preflight.json
```

67/67、raw/canonical origin一致、全hash一致、Phase A/B authorization=false、新規科学計算count=0を
要求します。

focused tests：

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests/test_second_study_safe_time_domain_protocol.py \
  review_tests/test_second_study_safe_time_domain_preflight.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

全review tests：

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests -p no:cacheprovider
```

focused testsはfail/skip 0。全review testsはfail 0とし、
`review_tests/test_pennylane_bch.py`の`pytest.importorskip("pennylane")`だけを最大1 skip許可します。

独立性検索は過去結果をコピーせず再実行します。未知の独立4条件に対する数値PF error、QPE cost、
proxy response、direct truthが一件でもあれば`no_go_independence_contaminated`として停止します。

## 成果物、commit、push、停止

新規outputに少なくとも次を保存します。

- `python_environment_identity.json`
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

全gate合格時だけstatusを`preflight_pass_phase_a_not_authorized`とし、marker/decisionへ
`phase_a_authorized=false`、`phase_b_authorized=false`を記録します。

pickle、npy、`.runtime`、archive展開物をcommitしません。軽量audit/test logだけを新規branchへ
commitします。push権限がなければlocal result commitで停止し、次をユーザーへ報告します。

```bash
git push -u origin gpu-second-study-safe-time-domain-preflight-v1-4-20260927
```

最終報告にはbranch/result commit、5 hash、67 checks、H01/P03、独立性検索、
Python/CuPy/fastrlock/NVIDIA/shared-library identity、GPU memory、test件数、go/no-go、未解決事項を
示してください。

報告後に停止し、Phase A/B、科学計算、threshold調整、別PF・別分子へ進まないでください。
