# GPUサーバー側Codexへの実行依頼：第二研究 safe-time-domain Phase Aのみ

第二研究のprotocol、runner実装、formal preflight v1.4が固定されました。今回は
**Phase Aだけを一度実行**し、truthを含まない予測をcommit・hash固定してください。

Phase B、exact ground state、direct PF eigenpair、direct truth、結果採点は許可しません。
Phase Aの成果物をcommit・pushして報告した時点で停止してください。

## 固定版

- protocol commit：`804331ecc976b83ae880940719706c11999247bc`
- protocol SHA-256：
  `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- runner実装commit：`e86e694805e8fcbc63659f7073eea95f67b8f435`
- Phase A実行bundle commit：`bbc063a05074260930860ef862d7e24bd81e3878`
- formal preflight v1.4 result commit：
  `2b37191594d7f79565314a5dad0d889f78aec504`
- formal preflight branch：
  `gpu-second-study-safe-time-domain-preflight-v1-4-20260927`
- formal preflight artifact：
  `artifacts/server_second_study_safe_time_domain_preflight_v1_4_20260927_9e0afa0/`
- preflight `decision.json` SHA-256：
  `11dc5630d6bf21ec14f024e07ee272fc8c43c68ce1ce0fbcd2b0ab0cea393032`
- preflight `manifest.json` SHA-256：
  `107f362e63eb7fa2e7b03e37cfa357026eb07c18b032a3eafc4d1a0faf4b4363`
- preflight `python_environment_identity.json` SHA-256：
  `2e5cc1e8f476393c1e6dff4ed481bf723a83545d4a50f432cfb229215e71bf2d`
- Phase A runner：
  `review_response/run_second_study_safe_time_domain_phase_a.py`
- shared implementation：
  `review_response/second_study_safe_time_domain_execution.py`
- 情報源：`multiple_window_consistency`だけ
- PF：`current_m3`だけ

protocol、amendment、threshold、候補時刻、停止規則、`gamma=1.01`、`beta=1.2`を
変更しません。

## 今回許可する計算と禁止する計算

Phase Aでは、独立評価4条件についてHamiltonian、RHF、CISD近似状態、group spectrum、
multiple-window proxyをCPU単一processで生成できます。候補時刻の選択はproxy情報だけで行い、
4 strategyの選択・予算をfreezeします。

次は一切実行しません。

- exact diagonalization、exact ground state、exact selected-time scoring。
- direct PF eigenpair、direct PF error、direct QPE cost。
- Phase B runner、Phase B cache、`COMPLETE`の作成。
- CuPy array、GPU device query/allocation、GPU kernel。
- PF追加、分子・geometry・basis変更、threshold再調整。
- H01/P03または第一研究のpickle/cacheを独立4条件の数値入力にすること。
- 複数process、複数GPU、同一outputへの並列書き込み。

## branchと独立worktree

既存worktree、過去preflight branch/output、untracked成果物を変更しないでください。

```bash
git fetch origin --prune
git cat-file -e 804331ecc976b83ae880940719706c11999247bc^{commit}
git cat-file -e e86e694805e8fcbc63659f7073eea95f67b8f435^{commit}
git cat-file -e bbc063a05074260930860ef862d7e24bd81e3878^{commit}
git cat-file -e 2b37191594d7f79565314a5dad0d889f78aec504^{commit}
git merge-base --is-ancestor \
  804331ecc976b83ae880940719706c11999247bc \
  bbc063a05074260930860ef862d7e24bd81e3878
git merge-base --is-ancestor \
  e86e694805e8fcbc63659f7073eea95f67b8f435 \
  bbc063a05074260930860ef862d7e24bd81e3878
git merge-base --is-ancestor \
  2b37191594d7f79565314a5dad0d889f78aec504 \
  bbc063a05074260930860ef862d7e24bd81e3878
```

bundle commit `bbc063a...`から独立worktreeと新規branchを作ります。推奨名は

`gpu-second-study-safe-time-domain-phase-a-20260927`

です。同名branch/worktreeが存在すれば上書きせず連番を付けます。既存worktreeをreset、clean、
stashせず、mainへmerge・force-pushしません。

## 固定process environment

formal preflight v1.4とbyte-identicalなenvironment identityを要求します。

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
`PYTHONDONTWRITEBYTECODE=1`を設定します。virtualenvをactivateせず、package/library、CUDA、
driver、shell設定を変更しません。

Phase A runnerは、formal preflight artifactのcommit、status、marker、manifest、3固定hash、
environment identity、Phase A/B authorization=falseを実行前に再検証します。一件でも不一致なら
`failed_preflight_identity`として科学計算前に停止してください。

## 計算前test

固定environmentで次のfocused testsを実行し、fail/skip 0を要求します。

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests/test_second_study_safe_time_domain_protocol.py \
  review_tests/test_second_study_safe_time_domain_preflight.py \
  review_tests/test_second_study_safe_time_domain_execution.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

続いて同じ固定environmentで全`review_tests`を実行します。fail 0を要求し、skipは
`review_tests/test_pennylane_bch.py`の任意依存`pennylane`だけを最大1件許可します。
失敗時はpackage installやtest・科学閾値の緩和をせず停止します。

## Phase A実行

新規outputは次を推奨します。

`artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694/`

同名が存在すれば連番を付け、既存directoryへ書きません。単一CPU processで次を実行します。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_second_study_safe_time_domain_phase_a.py \
  --project-root "$PWD" \
  --protocol review_response/second_study_safe_time_domain_protocol.json \
  --preflight-root artifacts/server_second_study_safe_time_domain_preflight_v1_4_20260927_9e0afa0 \
  --processes 1 \
  --output artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694
```

Phase A runtime cacheはこのrunの再開と将来のPhase Bにだけ使用できます。別run、第一研究、過去の
preflight outputからcacheをコピーしません。

## Phase A完了条件

次を全件照合します。

- statusが`phase_a_frozen_phase_b_not_authorized`。
- independent conditionがexact 4件、各条件のstrategyがexact 4件。
- PFが全件`current_m3`。
- truth access、exact diagonalization、direct evaluationが全て0。
- proxy acquisitionが全体最大188、各条件最大47。
- coordinate evaluationが全体最大44、各条件最大11。
- frozen predictionに正のselected time、正の予算、正のrotation countがある。
- source/protocol/preflight/environment gateが全件合格。
- `phase_a_predictions.json`、`phase_a_predictions.sha256`、source audit、resource audit、
  manifestが相互一致する。
- `PHASE_A_FROZEN`が存在し、`COMPLETE`は存在しない。
- Phase A/B authorizationは引き続きfalseとして記録される。

完了後に同じfocused testsと全`review_tests`を再実行し、command、Python identity、開始・終了時刻、
pass/fail/skip件数を新規output内のlogへ保存します。predictionやselectorはtest後も変更しません。

## commit、push、停止

軽量Phase A成果物とtest logだけを新規branchへcommitします。`.runtime`、pickle、npy、PySCF scratch、
巨大matrix/state cacheはcommitしません。ただし、将来のPhase Bに必要なPhase A `.runtime`は元worktreeの
同じ絶対pathに変更せず保存し、最終報告へ記録してください。

commit後、originへ新規non-force pushして構いません。push権限がなければlocal result commitで停止し、
ユーザーが実行する正確な`git push -u origin <actual-branch>`を報告します。

最終報告には次を示してください。

- branch、bundle/runner/preflight/result commit、protocolとprediction hash。
- 4条件の`n_qubits`、`t_ana`、選択strategy/time、frozen quantum budget。
- 条件別・総proxy acquisition数、coordinate evaluation数、fallback/coverage/棄却内訳。
- Phase A runtime cacheの絶対pathとhash inventory。
- wall/CPU時間、CPU/GPU最大memory、GPU allocation/kernelが0であること。
- focused/full test件数、source/environment gate、未解決事項。

報告後に停止してください。Phase B、direct truth、結果採点、threshold調整、別PF・別分子へ進まないで
ください。
