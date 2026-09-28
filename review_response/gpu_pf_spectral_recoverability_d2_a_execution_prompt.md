# GPUサーバー側Codexへの実行依頼：spectral recoverability D2-Aのみ

P-SPEC-6/D1は既存HCl 6座標で少数スペクトル成分への圧縮可能性を確認し、
`d1_complete_prototype_candidate_stop`で停止しました。今回はその結果を受けたdevelopment pilotとして、
元の近似状態からのexplicit-vector unitary Arnoldiを、同じHCl 6座標で一度だけ検証します。

実行順序は必ず次の二段階です。

1. truth-free predictorを実行し、予測artifactだけをcommitしてSHA-256固定する。
2. そのprediction freeze commitとbyte-identicalであることをscorerが検証した後だけ、既存truthを開いて採点する。

D2-B、LiF、新分子、holdout、新PF、新時刻、threshold調整、追加diagnosticには進みません。
D2-A completion reportをcommit・pushして報告した時点で停止してください。

## 固定identity

- D1 result commit：`94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a`
- D2-Prep planning commit：`d99715ef2c575a547394f2a5916abad27213d6fb`
- D2-A implementation commit：`e2e8e5c7a913140d2f2d61b2743f6fbf652498e3`
- D2 protocol SHA-256：
  `fb1d112e13830924ee5bed058cea8a8a6196d01b303b96fff664676db98d83f5`
- D2 planning manifest SHA-256：
  `efcd862712109f1bafc8c9e02f2f9a00ffcbd30b6f40826898758753b7e2f053`
- D2-A authorization SHA-256：
  `7c0e7bfd3197d0c7d7d0fd37a09bcc92d00c861d6bbaf0400f405450858a1654`
- D2 core SHA-256：
  `04eafd4051430be55c1494a6fbadf1800b2dc7c54ab1c3071a7a3e0a7616d033`
- predictor SHA-256：
  `ad7462bf2b10e0190c8eed3b9a693d1ef603af41fd10b721989d9b68d0f55364`
- scorer SHA-256：
  `473d199021fe241144cc8a81f5b7be3fb07be2afc6e2085fb8d6289a07008ad2`
- D2-A test SHA-256：
  `9ccc93247200308135263f2f6614eda4e4566ebfe4e61f6d61055080a1d9614d`
- Phase A cache amendment SHA-256：
  `a95a9abf87f1d428c35d34ed13cbea8c2ff930e91a3e5eb3a2550fd5d1dd1051`
- Phase A runtime inventory SHA-256：
  `5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91`

execution bundleの正確な40文字commitは、このpromptを渡すhandoff messageで固定します。prompt自身へ
自己参照commitを埋め込まず、handoffに示されたcommitをbranch/worktreeの起点として使用してください。
そのcommitは上記implementation commitの子孫でなければなりません。上記source 5件はimplementation
commitとbyte-identicalであることを実行前とprediction commit後に確認してください。

## 今回の科学的範囲

対象は`current_m3`の次の既存6座標だけです。

- HCl equilibrium：`0.5, 0.65, 0.8 * t_ana`
- HCl stretch150：`0.5, 0.65, 0.8 * t_ana`

predictorで許可する情報は、元Phase A cache内のHamiltonian、元CISD近似状態、PF component、
固定protocol/source identityだけです。各座標について単一のArnoldi chainを作り、prefix
`m=1,2,4,8`を共有して評価します。

- PF vector action：各座標最大8、全体最大48。
- Hamiltonian vector action：各座標最大8、全体最大48。
- CPU単一process、BLAS thread各1。
- full PF unitary、full-space eigendecomposition、exact ground state、direct truthはpredictorで0。
- GPU query、allocation、kernel、CuPy importは0。

H参照はKrylov subspace内の最低Ritz候補であり、certified ground stateとは呼びません。branch、alias、
conditioning、truncation、PF/H action数、component gate materialization、古典時間を分離して記録します。
predictorでbranch ambiguityまたは数値gate不合格になった座標は、結果後に救済せずabstainとします。

## 禁止事項

- Phase A/B、R1、D1を再実行しない。
- Phase A runtimeを変更、コピー、再生成、削除、再manifest化しない。
- 新時刻、新分子、LiF、別basis、別PF、別精度を追加しない。
- predictor実行前またはprediction commit前にtruth artifactを開かない。
- predictor processへdirect truth、D1 oracle結果、exact state、Phase B cacheを渡さない。
- scorerでprediction、threshold、Krylov dimension、branch規則、budget規則を変更しない。
- 同一座標でchainをprefixごとに再生成してaction上限を水増ししない。
- GPUをquery、allocate、使用しない。`nvidia-smi`も実行しない。
- 既存worktreeをreset、clean、stashせず、mainへmerge・force-pushしない。

## 元Phase A runtime

次の絶対pathだけを読み取り専用で使用します。

```text
/home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694
```

`.runtime`は56 files、113,469,289 bytesです。全file set、relative/absolute path、bytes、SHA-256を
inventoryと照合した後、HCl system cache 2件だけを読み込みます。

- HCl equilibrium：`8733b890a2d1f449f30ac43290b00fc94d5b08129403bee735fb78fa308aeab7`
- HCl stretch150：`8bac20c917e2242c1ecc84c9735bf0a93758e8b0211fe297551ae2026b1239f7`

一件でも不一致なら科学計算前に停止し、代替cacheや再構築は行いません。

## branchとworktree

```bash
git fetch origin --prune
git cat-file -e e2e8e5c7a913140d2f2d61b2743f6fbf652498e3^{commit}
git cat-file -e 94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a^{commit}
git merge-base --is-ancestor \
  94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a \
  e2e8e5c7a913140d2f2d61b2743f6fbf652498e3
```

handoffで示すexecution bundle commitから独立worktreeと新規branchを作ります。推奨名は

`gpu-pf-spectral-recoverability-d2-a-20260929`

です。同名があれば上書きせず連番を付けます。

次の5件に対し、implementation commitとの差が0であることを確認します。

```bash
git diff --exit-code e2e8e5c7a913140d2f2d61b2743f6fbf652498e3 -- \
  review_response/pf_spectral_recoverability_d2.py \
  review_response/pf_spectral_recoverability_d2_a_authorization.json \
  review_response/run_pf_spectral_recoverability_d2_a_predictor.py \
  review_response/run_pf_spectral_recoverability_d2_a_scorer.py \
  review_tests/test_pf_spectral_recoverability_d2.py
```

## 固定process environment

Pythonは次をabsolute pathで使います。

```text
/home/AbeHiromu/venvs/trotter-common/bin/python
```

全commandで次を置換設定します。

```text
PYTHONPATH=src:review_response:.
PYTHONNOUSERSITE=1
PYTHONDONTWRITEBYTECODE=1
OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

virtualenvをactivateせず、package、Python、CUDA、driver、shell設定を変更しません。

## Freeze前のtruth-free gate

prediction freeze前には、既存truth artifactを読むtestを実行しません。次のD2-A synthetic/source/access
testだけを実行し、fail/skip 0を要求します。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:." \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests/test_pf_spectral_recoverability_d2.py \
  -p no:cacheprovider
```

この段階では全`review_tests`、D1/R1/second-study execution testsを実行しません。test logは一時pathへ
保存します。このgateはsynthetic matrix、一時Git repository、source text、protocol/authorizationだけを使い、
Phase B `direct_points.*`、D1 oracle artifact、R1 truth artifactを開きません。

## Step 1：truth-free prediction

新規outputは次を推奨します。

`artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/`

既存directoryがあれば連番を付けます。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:." \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_pf_spectral_recoverability_d2_a_predictor.py \
  --project-root "$PWD" \
  --protocol review_response/pf_spectral_recoverability_d2_protocol_draft.json \
  --authorization review_response/pf_spectral_recoverability_d2_a_authorization.json \
  --phase-a-cache-amendment review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json \
  --phase-a-root /home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694 \
  --processes 1 \
  --output-dir artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c
```

predictor完了後、次を照合します。

- status：`d2_a_prediction_frozen_truth_not_opened`。
- coordinate exact 6、truth open 0、exact/direct/full-unitary/full-eigensolver 0。
- `PREDICTION_FROZEN.json`が存在し、prediction SHA-256とmanifestが一致。
- PF/H vector actionは各座標8以下、全体各48以下。
- GPU query/allocation/kernel 0。
- source、runtime、environment、access gateが全件合格。

`.runtime`、pickle、npy、matrix/vectorを含めず、prediction outputの軽量7ファイルだけをcommitします。
directory一括の`git add`は禁止し、次の7件だけを明示的にstageします。

```bash
git add \
  artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/prediction.json \
  artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/prediction.sha256 \
  artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/PREDICTION_FROZEN.json \
  artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/manifest.json \
  artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/source_audit.json \
  artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/access_audit.json \
  artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/resource_audit.json
git commit -m "Freeze D2-A truth-free predictions"
PREDICTION_COMMIT=$(git rev-parse HEAD)
```

commit後に上記5 sourceがimplementation commitとbyte-identicalで、worktreeにprediction変更がないことを
再確認します。staged/committed file setが上記7件だけであることも照合します。

## Prediction freeze後のtest gate

ここから既存truth artifactの読み取りを許可します。ただしpredictionの変更は禁止します。次のfocused testsを
実行し、fail/skip 0を要求します。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:." \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests/test_pf_spectral_recoverability_d2.py \
  review_tests/test_pf_spectral_information_pilot_d1.py \
  review_tests/test_pf_r1_reorientation_d0.py \
  review_tests/test_pf_candidate_validation.py \
  review_tests/test_second_study_safe_time_domain_execution.py \
  -p no:cacheprovider
```

続いて全`review_tests`を実行し、fail 0、skipは`review_tests/test_pennylane_bch.py`の任意依存
`pennylane`だけ最大1件を許可します。両logは一時pathへ保存します。test後に次を再確認します。

- HEADが`PREDICTION_COMMIT`のまま。
- prediction artifact 7件がprediction commit blobとbyte-identical。
- source 5件がimplementation commitとbyte-identical。
- tracked worktreeがclean。

一件でも不一致ならscorerを実行せず停止します。

## Step 2：既存truthによるscoring

新規outputは次を推奨します。

`artifacts/server_pf_spectral_recoverability_d2_a_result_20260929_e2e8e5c/`

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:." \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_pf_spectral_recoverability_d2_a_scorer.py \
  --project-root "$PWD" \
  --prediction-root artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c \
  --prediction-commit "$PREDICTION_COMMIT" \
  --prediction-artifact-relative artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c \
  --output-dir artifacts/server_pf_spectral_recoverability_d2_a_result_20260929_e2e8e5c
```

scorerは開始時HEADが`PREDICTION_COMMIT`そのものであること、prediction artifact 7件がそのcommit blobと
byte-identicalであることを検査します。違えばtruth採点を開始せず停止します。

正式完了statusは次のいずれかだけです。

- `d2_a_complete_prototype_candidate_stop`
- `d2_a_complete_information_cost_limit_stop`
- `d2_a_complete_close_spectral_route_stop`

いずれもD2-Aの正式な停止結果です。結果を見てthreshold、m、branch、budgetを調整しません。
`D2_A_COMPLETE.json`はcomplete statusだけで作成し、`d2_b_authorized=false`を維持します。

## 計算後test、commit、push、停止

Prediction freeze後のgateと同じfocused/full testsを再実行します。freeze前truth-free、freeze後pre-scorer、
post-scorerの各log、command、Python identity、時刻、件数、resource summaryをresult outputへ追加します。
runner生成manifestは書き換えず、その記載5ファイルを再hash照合します。

prediction commit後の最終commitには、scorerの軽量CSV/JSON/report/manifestとtest/resource logだけを
含めます。`.runtime`、pickle、npy、matrix、state、unitary、eigenvectorをcommitしません。originへ
新規non-force pushします。

最終報告には次を示してください。

- branch、execution bundle、implementation、prediction、result commit。
- protocol/authorization/core/predictor/scorer/test/prediction/result manifest hash。
- Phase A runtime 56 files identityとHCl cache 2件のhash。
- 6座標ごとのm、予測shift、e_use、abstention、branch/alias/conditioning/truncation判定、frozen budget。
- PF/H actions、component gates、wall/CPU memory、GPU counts 0。
- prediction commit 7件のbyte identity。
- 既存truth採点後のbranch correct、安全数、危険な過小評価、baseline gamma frontier、budget差。
- freeze前truth-free、freeze後pre-scorer、post-scorerのtest件数。
- 三分岐status、D2-B unauthorized、未解決事項。

報告後に停止してください。D2-B、LiF、holdout、方法のfreeze、新分子・PF、追加diagnostic、
threshold調整へ進まないでください。
