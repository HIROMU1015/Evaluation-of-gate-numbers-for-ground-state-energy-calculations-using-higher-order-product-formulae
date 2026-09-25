# GPUサーバー側Codexへの実行依頼：第一研究S0 exact-time採点 v1.1

第一研究S0の初回runは計算自体を完了しましたが、固定数値ゲートにより
`failed_numerical_validation`となりました。失敗成果物を変更・削除せず、
source identityだけを事前固定し直したv1.1でS0を一度だけ再実行してください。

今回の範囲は **S0 exact-time採点v1.1のみ** です。selector再実行、係数探索、
追加分子、別精度、S3、calibration改善へ進まないでください。

## 固定した版と失敗run

- 作業ブランチ：`first-study-mechanism-decision-v1-20260925`
- v1.1実装・manifest helper commit：`3279201bd046d63cad18c1f4964fa026599137a2`
- v1.1 anchor protocol：`review_response/pf_first_study_s0_anchor_protocol_v1_1.json`
- v1.1 anchor protocol SHA-256：`8f776ded65e42b7657d5c014cf525421b95cbbfb40aa0744c69d2c11f00204b1`
- 親第一研究protocol SHA-256：`410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565`
- frozen predictions SHA-256：`fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e`
- v1.1 runner：`review_response/run_pf_first_study_s0_exact_time_scoring_v1_1.py`
- manifest-only helper：`review_response/refresh_pf_first_study_s0_v1_1_manifest.py`

初回失敗runは次です。

- branch：`gpu-first-study-s0-exact-time-results-20260925`
- commit：`0ee4cc4c2567d7bda25d8e2e93d2ba051d2a0678`
- artifact：`artifacts/server_pf_first_study_s0_exact_time_20260925_b3a079f/`
- status：`failed_numerical_validation`

この失敗runでは`CO_active_eq_sto3g`だけ、P03 raw由来の
`t=0.5894372011255475`をanchorに選び、H01 pickleで再計算したため、保存shiftとの
差が`1.0414120648186197e-07 Ha`となりました。枝重なり、phase gap、固有対残差、
unitarityは合格しており、枝選択の曖昧さではありません。別source domainの点と
H01 cacheを混ぜたことが原因です。

v1.1では変更を次の一点に限定します。

> H01 pickleからPF unitaryを構築するbranch anchorは、同じH01 truth内で
> `truth_provenance == new_h01_continuous_branch_calculation`の点から選ぶ。

selector、selected formula/time、predicted cost、frozen budget、3個の挿入時刻、
判定閾値、regret referenceは一切変更しません。`1e-9 Ha`のanchor許容差も
緩めません。

## 安全な作業場所

既存cloneで`git fetch origin --prune`し、上記commitを取得できることを確認して
ください。現在の作業ツリーをreset、clean、stashせず、`3279201...`から独立
worktreeと新規結果ブランチを作ります。推奨ブランチ名は

`gpu-first-study-s0-exact-time-v1-1-results-20260925`

です。同名が既にあれば上書きせず連番を付けてください。mainへmergeせず、
force-pushしないでください。

初回失敗artifactとその`.runtime`を変更・削除・再利用しないでください。v1.1は
anchor protocol hashをcache keyへ追加済みなので、初回の24 cache recordはv1.1の
cache hitとして受理されません。

## H01元成果物

前回と同じH01元成果物を直接使います。以前の絶対パスは次でした。

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`

絶対パスが異なる場合は成果物名で検索して構いません。Hamiltonianを再生成しないで
ください。6 pickle、6 metadata、`aggregate/summary.json`、`truth/`、`COMPLETE`
が揃う唯一の候補を使い、既存source identity検査をすべて通してください。

P03とpractical成果物はcommit収録の次を使います。

- `artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`
- `artifacts/server_practical_calibration_minimal_20260923_79035cc/`

## truth計算前ゲート

1. `origin`が`HIROMU1015/*`であること。
2. HEADが`3279201bd046d63cad18c1f4964fa026599137a2`であること。
3. v1.1、親protocol、frozen predictionsの3 hashが上記値と一致すること。
4. 失敗runがGitHub上に保存され、statusがfailedで`COMPLETE`がないこと。
5. v1.1 preflightで6条件すべてにH01-native anchorが一意に得られること。
6. 次の集中テストをtruthを開く前に実行すること。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -m pytest -q \
  review_tests/test_pf_first_study_s0_exact_time_scoring_v1_1.py \
  review_tests/test_pf_first_study_s0_v1_1_wrapper.py \
  review_tests/test_pf_first_study_s0_v1_1_manifest_refresh.py \
  review_tests/test_pf_first_study_s0_exact_time_scoring.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

保存truthによる事前固定anchorは次です。これと一致しなければ計算前に停止します。

| condition | H01-native anchor time |
| --- | ---: |
| `N2_active_eq_sto3g` | `0.5721861616352092` |
| `N2_active_stretch150_sto3g` | `0.806176425611238` |
| `CO_active_eq_sto3g` | `0.5886807290771116` |
| `CO_active_stretch150_sto3g` | `0.8563682148339049` |
| `HF_full_eq_sto3g` | `0.14715507960862567` |
| `HF_full_stretch150_sto3g` | `0.20109906745049325` |

## 固定計算

上書きしない新規出力先を使います。例：

`artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201/`

単一GPU・単一processで次を実行してください。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -u review_response/run_pf_first_study_s0_exact_time_scoring_v1_1.py \
  --project-root "$PWD" \
  --practical-root artifacts/server_practical_calibration_minimal_20260923_79035cc \
  --h01-root /absolute/path/to/server_h01_approximate_state_calibration_20260922_011228_e0692a8 \
  --p03-root artifacts/server_unused_molecule_frozen_holdout_20260921_d288797 \
  --backend gpu \
  --gpu-id 0 \
  --output artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201
```

計算点数は初回と同じ、18 new direct truth coordinatesと6 anchor recomputationsです。
v1.1 cacheだけは同じ新規出力先で再開できます。別条件の並列実行や旧cacheのコピーを
行わないでください。

## 数値ゲートと成果物

親protocolの全ゲートに加え、全6 anchorについて次を必須にします。

- source domainが`H01-native`。
- provenanceが`new_h01_continuous_branch_calculation`。
- 保存shiftとの絶対差が`1e-9 Ha`以下。

固有対残差・unitarity Frobenius残差は`1e-10`以下、branch/ground overlap警告閾値
は`0.9`、resolved phase gapは`1e-8 rad`より大きいことを変更しません。

6条件、18新規点、6 anchor、全source/numerical gateが合格した場合だけ
`complete_exact_time_scoring`と`COMPLETE`を許します。一つでも不合格なら
`failed_numerical_validation`とし、閾値を変更せず停止してください。不合格runの
数値を科学的結論に使用しません。

少なくとも次をcommit対象にします。

- `protocol.json`
- `s0_anchor_protocol.json`
- byte-identicalな`predictions.json`と`prediction.sha256`
- `source_manifest.json`
- `branch_audit.csv`
- `scoring.csv`
- `audit.json`
- `manifest.json`
- `report.md`
- test logs

pickle、selected-vector `.npy`、`.runtime`はcommitしません。

## post-run検証、commit、push、停止

本計算後に集中テストと全`review_tests`を実行し、ログを結果directoryへ保存します。
その後、科学結果を再計算せずtest logをmanifestへ収録するため、次を1回実行します。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python review_response/refresh_pf_first_study_s0_v1_1_manifest.py \
  --output artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201
```

manifest記載hash、CSV件数（24 branch rows、6 scoring rows）、prediction hash、audit、
`COMPLETE`を再照合してください。

reportでは、初回runがなぜ無効だったか、v1.1で変更したのがanchor source identity
だけであること、6条件のexact-time regret、gamma=1.0/1.01 success、旧nearest-grid
との差、主4条件とHF stress 2条件の分離を明記します。v1.1がcompleteの場合だけ
科学的に解釈してください。

軽量成果物とreportを新規結果ブランチへcommitし、`origin`へpushしてください。
最終報告では、結果ブランチ、commit、成果物パス、実行時間、CPU/GPU最大メモリ、
test件数、18点完了、6 anchor時刻と最大再現差、最大固有対/unitarity残差、最小branch
overlap、6条件のregretとgamma=1.01成功を示してください。その後停止し、S3や追加
実験へ進まないでください。
