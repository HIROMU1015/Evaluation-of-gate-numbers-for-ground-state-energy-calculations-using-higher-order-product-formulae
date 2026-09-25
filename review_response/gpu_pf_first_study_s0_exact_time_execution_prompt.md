# GPUサーバー側Codexへの実行依頼：第一研究S0 exact-time採点

第一研究のExperiment A/B/Cは完了しています。残るS0だけを、既に固定したpractical selectorを一切変更せず、GPUサーバーに残るH01元pickleから実行してください。

今回の範囲は **S0 exact-time採点のみ** です。selector再実行、係数探索、追加分子、別精度、S3、calibration改善へ進まないでください。

## 固定した版

- 作業ブランチ：`first-study-mechanism-decision-v1-20260925`
- S0 scorer実装commit：`b3a079f`
- 第一研究protocol SHA-256：`410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565`
- practical protocol SHA-256：`7bbe9958837a881f0247b6e72f5e80e2331e0cfe50dea18addd13a2748467d55`
- frozen predictions SHA-256：`fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e`
- practical Phase-A commit：`79035cc7c414c04cafe8b9f8bdc779a17ec57302`
- runner：`review_response/run_pf_first_study_s0_exact_time_scoring.py`

新しい結果ブランチは`b3a079f`から作成し、推奨名を

`gpu-first-study-s0-exact-time-results-20260925`

とします。同名が存在すれば上書きせず連番を付けてください。既存作業ツリーをreset、clean、stashせず、独立worktreeを使用します。mainへは統合しません。

## 最重要条件：H01元pickleを直接使う

H01元成果物は、以前の実行環境では次でした。

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`

絶対パスが異なる場合は成果物名で検索して構いません。次がすべてある唯一の候補を使ってください。

- `COMPLETE`
- `manifest.json`
- `aggregate/summary.json`
- `cache/{N2_active_eq,N2_active_stretch150,CO_active_eq,CO_active_stretch150,HF_full_eq,HF_full_stretch150}_sto3g.pkl`
- 対応する6個の`.metadata.json`
- `truth/`内の2 PFの保存truth JSON

Hamiltonianを再生成しないでください。runnerはpractical固定protocolに保存された各pickle SHA-256、Hamiltonian SHA-256、H01 protocol hash、metadataを照合します。不一致・欠損・候補の曖昧さがあれば長時間計算せず停止してください。

P03元成果物は、このcommitに収録された

`artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`

を使います。practical元成果物は

`artifacts/server_practical_calibration_minimal_20260923_79035cc/`

です。両方について`COMPLETE`、manifest、summary、protocol/prediction hashをrunnerが検査します。

## 計算前ゲート

1. `git remote -v`で`origin`が`HIROMU1015/*`であることを確認する。
2. `git fetch origin --prune`後、`b3a079f`を取得できることを確認する。
3. 独立worktreeを`b3a079f`から作る。
4. 第一研究protocolとfrozen predictionsのSHA-256を上記値と照合する。
5. H01元成果物6 pickleのsource identityを確認する。
6. 次をtruth計算前に実行する。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -m pytest -q \
  review_tests/test_pf_first_study_s0_exact_time_scoring.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

固定scorerまたは判定閾値に問題を見つけた場合は、truthを開く前なら停止して報告してください。truthを一度開いた後にscorerを修正しないでください。バグ修正が必要なら現runを`INVALIDATED_RUN`として保存し、新protocol/新Phase-A境界が必要です。

## 固定計算

対象は6条件すべてで、frozen selectorが選択済みの`current_m3`です。各選択時刻$t_s$について

`0.99 t_s, 1.00 t_s, 1.01 t_s`

を直接計算します。各条件で、保存済み連続枝の直下にある信頼可能な点を1点再計算して枝vectorを復元し、そこから3点へ連続追跡します。

- 新規direct truth点は3点×6条件=`18`と数える。
- 下側anchorの再計算6点は新しい時刻座標ではないため別会計にする。
- anchor shiftと保存値の絶対差は`1e-9 Ha`以下。
- 固有対残差とunitarity Frobenius残差は`1e-10`以下。
- ground/previous branch overlap警告閾値は`0.9`。
- 位相gap`1e-8 rad`以内はresolved扱いにしない。
- 元のselected formula/time/predicted cost/frozen budgetを変更しない。
- 主regret基準は元の2 PF・元の保存格子。挿入点を含む拡張格子は別列で報告する。

既存H01実測では、3136次元条件はGPUでPFユニタリを構築しCPU Schurを行う方式が有利でした。まず単一GPU・単一processで実行してください。GPU使用自体は目的ではありませんが、同時並列でメモリを圧迫しないでください。

出力先は上書きしない新規directoryにします。例：

`artifacts/server_pf_first_study_s0_exact_time_20260925_b3a079f/`

実行例：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -u review_response/run_pf_first_study_s0_exact_time_scoring.py \
  --project-root "$PWD" \
  --practical-root artifacts/server_practical_calibration_minimal_20260923_79035cc \
  --h01-root /absolute/path/to/server_h01_approximate_state_calibration_20260922_011228_e0692a8 \
  --p03-root artifacts/server_unused_molecule_frozen_holdout_20260921_d288797 \
  --backend gpu \
  --gpu-id 0 \
  --output artifacts/server_pf_first_study_s0_exact_time_20260925_b3a079f
```

runnerの`.runtime/direct_cache`で再開できます。同じ出力先を再開する場合、cache keyとvector hashが一致する完了点だけを再利用してください。公開成果物へ`.runtime`やpickleをcommitしません。

## 成果物と判定

少なくとも次を保存します。

- `protocol.json`
- byte-identicalな`predictions.json`と`prediction.sha256`
- `source_manifest.json`
- `branch_audit.csv`
- `scoring.csv`
- `audit.json`
- `manifest.json`
- `report.md`

6条件、18新規点、6 anchor、全source/numerical gateが合格した場合だけstatusを`complete_exact_time_scoring`とし、`COMPLETE`を許します。不合格なら`failed_numerical_validation`とし、`COMPLETE`を作らず、閾値を緩めないでください。

reportでは次を明示してください。

1. frozen prediction hashが不変か。
2. exact selected timeでのsigned shiftと直接費用。
3. 同一PF時刻regret、元2-PF格子に対するjoint regret、拡張格子regret。
4. γ=1.0/1.01のenergy marginと成功数。
5. 旧nearest-grid採点との差。
6. 新規truth 18点とanchor再計算6点の別会計。
7. N2/CO主4条件とHF stress 2条件を分離した解釈。

## テスト、commit、push、停止

本計算後に集中テストと全`review_tests`を実行し、ログを結果directoryへ保存してください。manifest記載hash、CSV件数、prediction hash、audit集計を再照合します。

軽量成果物、report、必要な結果再現テストを新しい結果ブランチへcommitし、`origin`へpushしてください。force-pushしないでください。mainへmergeしないでください。pickle、selected-vector `.npy`、`.runtime`はcommitしません。

最終報告では、結果ブランチ、commit、成果物パス、実行時間、CPU/GPU最大メモリ、テスト件数、18点の完了、anchor最大差、最大固有対/ユニタリ残差、最小枝overlap、6条件のexact-time regretとγ=1.01成功を示してください。その後停止し、追加実験やS3へ進まないでください。
