# GPUサーバー側Codexへの実行依頼：第2研究v2 HF domain pilotのみ

第1研究でHF 2条件のtime-domain lossが支配的であることを確認し、HF domain-intervention pilotの
P0設計、execution authorization、predictor/scorer実装を固定しました。今回は固定6座標に対し、
**Phase A truth-free predictionを一度実行してcommit/hash freezeし、その後だけPhase B scoringを一度実行**してください。

C1、D2-B、LiF、新分子、新PF、候補時刻追加、threshold・eta・gamma・width変更、外部baseline実装には進みません。
結果を見た後の救済は行わず、result commitを作成して報告した時点で停止してください。

## 固定identity

- protocolization commit: `6047f66ae9aad38eadfdbe8cf3d63277829ce8b1`
- execution protocol freeze commit: `afd561ed4b152c106018fc5b9ac8cc7a0375c043`
- implementation commit: `0aef1c0da7aecb48e8cde0e5c969885d0f970ef0`
- P0 protocol SHA-256: `a2f1b286eb0a94f63bd23702c7c1b26a46480d1c3731932e74dd22c074b60a1c`
- execution authorization SHA-256: `78d1ccea726c814679915dfdd85afe5bbbee997a2065014b5ed0536199d9adbd`
- implementation manifest SHA-256: `b74c285c833046274e0d917e11bc28ea41e58cdc472289ae21dbef9275a6faf7`
- core SHA-256: `3dcd57b6e3821d4ff64e1c4e67876a8b9916fad708955a98aa7cc097197fb230`
- cache adapter SHA-256: `4407aed4f3a17d413511d8a55cb6f27111289928bf47b972400223ad9b6301ca`
- predictor SHA-256: `1ce389a91a3c19bc89f44ec4f55b39754af298000d3aa6bea575fe2bc2fff702`
- scorer SHA-256: `f35cf0d4dfc7d2b248b38faf1022af816996dabc1373e18600e392db30b075bf`
- test SHA-256: `25b04938508357b0294c230feb34cb159c4a48a48e6e9fbb32c0fc449895b74b`
- inherited D2 core SHA-256: `04eafd4051430be55c1494a6fbadf1800b2dc7c54ab1c3071a7a3e0a7616d033`
- first-study protocol SHA-256: `410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565`

このpromptを含むexecution bundle commitはhandoff messageで40文字hashを示します。そのcommitは
implementation commitの子孫でなければなりません。

## 固定科学規則

- condition: `HF_full_eq_sto3g`, `HF_full_stretch150_sto3g`
- PF: `current_m3`のみ、`K=9108`
- candidate: 各条件 `T0`, `1.3*T0`, `1.6*T0` のexact 3点、合計6点
- `eta=0.10`、結果後変更禁止
- primary resource metric: `continuous_rotation_cost_proxy`
- discrete budget: `not_defined_in_inherited_study`
- M1: D2-Aのm=8 explicit-vector unitary Arnoldi、prefix `1,2,4,8`
- B1: 同一候補のlocal CISD proxy、gamma `1.01,1.02,1.05,1.10`を独立armとしてfreeze
- T0はintervention候補ではなくreproduction control/fallback
- T0 reproduction failなら、そのconditionのcap-out interventionはprocedurally invalid
- scorer safety: `abs(delta_direct)+beta*K/[t*B_frozen] <= epsilon_E`
- target: `t>T0`かつ`B_frozen<=0.90*B0`

## 禁止事項

- prediction commit前にdirect truth、branch audit、H01 truth JSONをpredictor processへ渡さない。
- predictorでexact ground、full H/PF eigensolver、full PF matrixを使わない。
- prediction、selector、eta、gamma、candidate、width、branch ruleをscorerで変更しない。
- 近傍truth、interpolation、追加anchor、追加座標を使わない。
- GPU query/allocation/kernel、CuPy import、`nvidia-smi`を実行しない。
- package、Python、CUDA、driverを変更しない。
- C1、D2-B、LiF、holdout、新PF、外部baselineへ進まない。
- 既存worktreeをreset、clean、stashせず、mainへmerge・force-pushしない。

## branch / worktree

handoff commitから新規独立worktreeとbranchを作ります。推奨branch:

`gpu-second-study-v2-hf-domain-pilot-20260930`

同名があれば上書きせず連番を付けます。次のsourceはimplementation commitとbyte-identicalを要求します。

```bash
git diff --exit-code 0aef1c0da7aecb48e8cde0e5c969885d0f970ef0 -- \
  review_response/hf_domain_intervention_pilot.py \
  review_response/run_hf_domain_intervention_prepare.py \
  review_response/run_hf_domain_intervention_predictor.py \
  review_response/run_hf_domain_intervention_scorer.py \
  review_tests/test_hf_domain_intervention_pilot.py
```

## 固定process environment

```text
Python=/home/AbeHiromu/venvs/trotter-common/bin/python
PYTHONPATH=src:review_response:.
PYTHONNOUSERSITE=1
PYTHONDONTWRITEBYTECODE=1
OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

CPU単一processです。spectral armとlocal-proxy armは各1800秒以内、peak CPU RSSは4 GiB以内です。

## HF source cache preflight

H01 cache rootはサーバー上の実在pathを明示的に一つ選び、以後変更しません。候補は過去provenance上の
次のartifactです（実際の配置が異なる場合、pathだけ変更できるがhash規則は変更不可）。

```text
/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8
```

必須pickle hash:

- HF eq: `1da32d7e96eddaebfd3039f4576e1b4f86098c1acffb207d59779cf6f3c3b07a`
- HF stretch: `89e7cff9a70d481fcc15b11908686a47d55b23a2b7206062d8b9a1ea9fe1d173`

Hamiltonian hash:

- HF eq: `cd074e4870223646ff51e98a72a679b33019cd96bb013de7536c0ceb3e7456c8`
- HF stretch: `c68722b3f9f98488e765afb49fa2d1153e41b2a8e84b6df21841400650cec499`

一致しなければ科学計算前に停止し、再構築・代替cache・threshold変更を行いません。

## Freeze前truth-free test

prediction freeze前は次だけを実行します。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests/test_hf_domain_intervention_pilot.py \
  -p no:cacheprovider
```

fail/skip 0を要求します。

## Input adapter

`CACHE_ROOT`を上記preflightで固定し、新規input outputを用います。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_hf_domain_intervention_prepare.py \
  --cache-root "$CACHE_ROOT" \
  --authorization review_response/hf_domain_intervention_pilot_execution_authorization.json \
  --output-root artifacts/server_hf_domain_intervention_input_20260930_0aef1c0
```

これはcache identityを検証し、predictor用allowlistへHamiltonian/CISD/PF componentだけを隔離します。
PF/H action、eigensolver、direct truth、GPU countは0でなければなりません。`.runtime`はcommitしません。

## Phase A：truth-free predictor

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_hf_domain_intervention_predictor.py \
  --project-root "$PWD" \
  --p0-protocol docs/second_study_v2/hf_domain_protocol_20260930/second_study_v2_hf_domain_protocol.json \
  --authorization review_response/hf_domain_intervention_pilot_execution_authorization.json \
  --source-contract docs/second_study_v2/hf_domain_protocol_20260930/source_and_coordinate_contract.json \
  --candidate-plan docs/second_study_v2/hf_domain_protocol_20260930/hf_domain_candidate_plan.csv \
  --sanitized-root artifacts/server_hf_domain_intervention_input_20260930_0aef1c0 \
  --processes 1 \
  --output-dir artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0
```

必須gate:

- status `hf_domain_prediction_frozen_truth_not_opened`
- condition 2、candidate 6
- truth/direct/full eigensolver/full PF/GPU count 0
- M1 PF actions/H actions 各48以下
- B1 PF action 6、H exponential action 6
- arm別wallを分離
- prediction manifest全件一致

次の軽量7件だけを明示的にstageしてcommitします。

```bash
git add \
  artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0/prediction.json \
  artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0/prediction.sha256 \
  artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0/PREDICTION_FROZEN.json \
  artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0/source_audit.json \
  artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0/access_audit.json \
  artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0/resource_audit.json \
  artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0/manifest.json
git commit -m "Freeze HF domain pilot predictions"
PREDICTION_COMMIT=$(git rev-parse HEAD)
```

## Prediction freeze後test

ここから既存truth artifactのtest読取を許可します。focused 48 passed相当と全`review_tests`を実行し、
fail 0を要求します。prediction 7件とsource 5件がcommit blobとbyte-identicalで、tracked worktreeがcleanで
あることを再確認します。

## Phase B：truth scorer

T0 truthは次のtracked branch auditからexact coordinateを2件reuseします。cap外候補はtracked artifactに
exact coordinateがないため、cache identity合格後に最大4点だけCPUで計算します。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_hf_domain_intervention_scorer.py \
  --project-root "$PWD" \
  --p0-protocol docs/second_study_v2/hf_domain_protocol_20260930/second_study_v2_hf_domain_protocol.json \
  --authorization review_response/hf_domain_intervention_pilot_execution_authorization.json \
  --source-contract docs/second_study_v2/hf_domain_protocol_20260930/source_and_coordinate_contract.json \
  --prediction-root artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0 \
  --prediction-commit "$PREDICTION_COMMIT" \
  --prediction-artifact-relative artifacts/server_hf_domain_intervention_prediction_20260930_0aef1c0 \
  --cache-root "$CACHE_ROOT" \
  --truth-source artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201/branch_audit.csv \
  --output-dir artifacts/server_hf_domain_intervention_result_20260930_0aef1c0
```

必須gate:

- scorer開始時HEADがprediction commitそのもの
- prediction 7/7がcommit blobとbyte-identical
- truth exact 6、reuse 2、新規最大4、nearest/interpolation 0
- T0 reproduction control 2件
- physical branch判定はshift/gapで行い、unwrap integer同士を直接比較しない
- continuous frozen budgetだけを正式採点
- `COMPLETE.json`とstatus `second_study_v2_hf_domain_pilot_complete_review_required`
- classificationは固定taxonomyのexact 1件

計算後に同じfocused/full testsを再実行します。resultの軽量6件だけを明示的にstageし、local result commitを
作成します。`.runtime`、pickle、matrix/vector、unitary、exact stateをcommitしません。

execution authorizationでは`push_authorized=false`なので、今回はpushせずlocal result commitで停止します。
最終報告にはbranch、bundle/protocol/implementation/prediction/result commit、全hash、6座標の両arm prediction、
T0 control、truth computed/reused、branch/safety/target、gamma frontier、classification、resource/test件数、
未解決事項を示してください。
