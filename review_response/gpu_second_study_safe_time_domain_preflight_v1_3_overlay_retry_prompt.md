# GPUサーバー側Codexへの再実行依頼：第二研究preflight v1.3のみ

strict v1.2 preflightは環境identity gateで正しく停止しました。固定Python environmentにはCuPyがなく、
Qiskit Aer importはdefault library searchでCUDA 12.9 nvJitLink symbolを解決できませんでした。
その後のadapted preflightで、既存packageだけを使うprocess限定overlayにより、科学計算を一切せずに
全preflight gateが合格することを確認しました。

v1.3では、そのoverlayを事前固定した正式規則として **preflight全体だけを新規branch/outputへ一度
再実行**してください。過去4回のbranch、commit、outputは変更せず保存します。

Phase A、Phase B、新規Hamiltonian、RHF/CISD、group spectrum、proxy、PF action、direct truthは
許可しません。GPU device allocationとkernelも実行せず、preflight完了後に停止してください。

## 固定版

- protocol commit：`804331ecc976b83ae880940719706c11999247bc`
- protocol SHA-256：
  `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- parent preflight実装commit：`0f3381863ed0eb0a31b59b8018e816bebe3840f7`
- v1.2 review済みbundle commit：`a23b5beb8c62380b8f873385e37fd0031e265da2`
- v1.3 overlay amendment commit：
  `699774cd23ac0010bde6ee015489ea62aaacf7a1`
- v1.3 review済みbundle commit：
  `25a4a415609189ce3333c380e7c55a76d76e401f`
- v1.1 amendment SHA-256：
  `218d325d2b13eea24196302a52e4a1a3e34ae92973518b61835bf2ad3974759d`
- v1.2 amendment SHA-256：
  `ab87da7c42aba20658e5f5d4a204cdf761c50f0814d24719a36e72be674da77e`
- v1.3 amendment：
  `review_response/second_study_safe_time_domain_preflight_environment_overlay_amendment_v1_3.json`
- v1.3 amendment SHA-256：
  `c8ec1925f2ad8f2dbb0b3e466514cd8fb0d70d39c58ee538e3ea5ff4e8e7d6ac`
- source runner：`review_response/run_second_study_safe_time_domain_preflight.py`

protocol、v1.1/v1.2 amendment、source runnerは変更しません。

## 保存する過去4回の記録

1. `gpu-second-study-safe-time-domain-preflight-20260927`
   - commit：`e1891dfd24ec5f0064b0598e51eb260073fd2b1e`
   - status：`failed_source_identity`
2. `gpu-second-study-safe-time-domain-preflight-v1-1-20260927`
   - commit：`b520f9bd8f575456531e7c0b0f2692973b436e21`
   - status：`failed_environment`
3. `gpu-second-study-safe-time-domain-preflight-v1-2-20260927`
   - commit：`fd827f50dcbe64f8e2ea9d931cfdf2dd8eea4480`
   - status：`failed_environment_identity`
4. `gpu-second-study-safe-time-domain-preflight-v1-2-adapted-20260927`
   - commit：`ef2dc7443092e93d09ead2fbf717645362fe4189`
   - status：`preflight_pass_phase_a_not_authorized`
   - classification：environment adaptation evidenceであり、formal v1.2 completionではない。

4 branch/outputをreset、rebase、amend、削除、変更、再利用しません。adapted outputからauditや検索結果を
コピーせず、今回のfilesystem stateで全gateを再実行します。

## v1.3で許可する唯一のoverlay

Python本体と科学packageの主environment：

`/home/AbeHiromu/venvs/trotter-common/bin/python`

CuPyだけを読む既存site-packages：

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages`

許可する外部distributionは`cupy-cuda12x==13.6.0`だけです。NumPy、SciPy、Matplotlib、PySCF、
OpenFermion、OpenFermion-PySCF、Qiskit、Qiskit Aer、pytest、pandasはすべて
`trotter-common`から解決しなければなりません。`trotterlib`は今回のcurrent worktreeの
`src/trotterlib`から解決します。

各commandでは、継承された`PYTHONPATH`と`LD_LIBRARY_PATH`をappendせず、次の値で置換します。

```text
PYTHONPATH=src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages

LD_LIBRARY_PATH=/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib
```

`PYTHONNOUSERSITE=1`と`PYTHONDONTWRITEBYTECODE=1`も設定します。virtualenvをactivateせず、
absolute Python pathを使います。shell startup file、共有環境、package、CUDA、driverを変更しません。

package/libraryをinstall、update、downgrade、修復、コピーしません。別site-packagesや別library
directoryを追加しません。固定overlayで失敗した場合は`failed_environment_identity`として停止します。

## branchとworktree

```bash
git fetch origin --prune
git cat-file -e e1891dfd24ec5f0064b0598e51eb260073fd2b1e^{commit}
git cat-file -e b520f9bd8f575456531e7c0b0f2692973b436e21^{commit}
git cat-file -e fd827f50dcbe64f8e2ea9d931cfdf2dd8eea4480^{commit}
git cat-file -e ef2dc7443092e93d09ead2fbf717645362fe4189^{commit}
git cat-file -e 699774cd23ac0010bde6ee015489ea62aaacf7a1^{commit}
git cat-file -e 25a4a415609189ce3333c380e7c55a76d76e401f^{commit}
git merge-base --is-ancestor \
  804331ecc976b83ae880940719706c11999247bc \
  699774cd23ac0010bde6ee015489ea62aaacf7a1
git merge-base --is-ancestor \
  a23b5beb8c62380b8f873385e37fd0031e265da2 \
  699774cd23ac0010bde6ee015489ea62aaacf7a1
git merge-base --is-ancestor \
  699774cd23ac0010bde6ee015489ea62aaacf7a1 \
  25a4a415609189ce3333c380e7c55a76d76e401f
```

v1.3 review済みbundle commit `25a4a41...`から独立worktreeと新規branchを作ります。
推奨名は

`gpu-second-study-safe-time-domain-preflight-v1-3-20260927`

です。同名があれば上書きせず連番を付けます。既存worktreeをreset、clean、stashせず、mainへ
merge・force-pushしません。

## 新規output

推奨output：

`artifacts/server_second_study_safe_time_domain_preflight_v1_3_20260927_699774c/`

同名があれば連番を付けます。既存outputへ書かず、過去output/cacheを入力や再開に使いません。

## environment identity gate

最初に固定overlayを使う読み取り専用identity/import smoke testを実行し、
`python_environment_identity.json`へ次を記録します。

- Python requested path、realpath、executable SHA-256、version、prefix/base-prefix。
- `pyvenv.cfg` path/SHA-256。
- `requirements-gpu.txt` SHA-256。
- 実際の`PYTHONPATH`、`LD_LIBRARY_PATH`、`sys.path`、`site.getsitepackages()`。
- 全対象moduleの`__file__`、distribution名/version、解決元分類。
- `cupy-cuda12x==13.6.0`が固定CuPy overlayから解決されること。
- 固定10 packageが`trotter-common`から解決されること。
- `trotterlib`がcurrent worktreeの`src/trotterlib`から解決されること。
- 5個のCUDA library directoryが実在すること。
- 関連NVIDIA distribution名/versionと各`RECORD` fileのSHA-256。
- Qiskit Aer extensionに対する`ldd`等の読み取り専用確認で、実際に解決されたshared-library path。
- `qiskit_aer`と`cupy`のimport成功。

unlisted foreign module、別site-packages、別CUDA library directoryへの解決を一件でも検出したら停止します。

import smokeだけに留め、CuPy array、device allocation、GPU kernel、Hamiltonian/state、proxy、PF action、
group spectrum、direct truthを生成しません。NVIDIA package versionと`RECORD` hash、および全environment
identityを今回のpreflight結果で固定し、後のPhase Aはそのidentityとbyte-identicalでなければ開始不可と
記録します。

## source identity gate

environment gate合格後、3 amendmentのhashを照合し、固定overlay下でsource runnerを再実行します。

```bash
sha256sum review_response/second_study_safe_time_domain_protocol.json
sha256sum review_response/second_study_safe_time_domain_preflight_amendment_v1_1.json
sha256sum review_response/second_study_safe_time_domain_preflight_environment_amendment_v1_2.json
sha256sum review_response/second_study_safe_time_domain_preflight_environment_overlay_amendment_v1_3.json

PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python \
  review_response/run_second_study_safe_time_domain_preflight.py \
  --project-root "$PWD" \
  --output artifacts/server_second_study_safe_time_domain_preflight_v1_3_20260927_699774c/local_source_preflight.json
```

source runnerのschemaは`second_study_safe_time_domain_local_preflight_v1_1`のままです。

- source checks 67/67。
- raw/canonical origin一致。
- protocol/v1.1/v1.2/v1.3 hash一致。
- Phase A/B authorization=false。
- 新規Hamiltonian/state/proxy/direct truth count=0。

一つでも失敗すれば`failed_source_identity`として停止します。

## 残りのpreflight

source gate合格後だけ次をすべて新規に実行します。

1. H01/P03元成果物のidentity照合。
2. 全worktree、全Git ref、untracked artifact、binary、log、archiveを対象にしたLiF/HCl独立性検索。
3. `nvidia-smi`によるGPU identity、process、各GPU free memory 8 GiB以上の確認。
4. focused tests。
5. 全`review_tests`。
6. decision、manifest、全成果物SHA-256の照合。

過去の検索件数をコピーせず、今回のscope/count/context/classificationを記録します。過去4回のoutput、
v1.3 amendment/prompt/testはplanning/validationとして個別分類できますが、未知の数値PF error、
QPE cost、proxy response、direct truthを自動的に安全扱いしません。一件でも独立4条件の数値結果を
発見したら`no_go_independence_contaminated`として停止します。

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

focused testsはfail/skipとも0を要求します。全review testsはfail 0を要求し、skipは
`review_tests/test_pennylane_bch.py`の`pytest.importorskip("pennylane")`だけを最大1件許可します。
それ以外のskipは`failed_tests`です。

## 成果物、commit、push、停止

新規outputには少なくとも次を保存します。

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

全gate合格時だけstatusを`preflight_pass_phase_a_not_authorized`とします。markerとdecisionに
`phase_a_authorized=false`、`phase_b_authorized=false`を明記します。

pickle、npy、`.runtime`、archive展開物をcommitしません。軽量audit/test logだけを新規branchへ
commitします。Codexにpush権限がなければlocal result commitで停止し、次のnon-force commandを
ユーザーへ報告してください。

```bash
git push -u origin gpu-second-study-safe-time-domain-preflight-v1-3-20260927
```

最終報告にはbranch/result commit、4 hash、67 checks、H01/P03、独立性検索、Python/module/library
identity、GPU memory、focused/full tests、go/no-go、未解決事項を示してください。

報告後に停止し、Phase A、Phase B、科学計算、threshold調整、別PF・別分子へ進まないでください。
