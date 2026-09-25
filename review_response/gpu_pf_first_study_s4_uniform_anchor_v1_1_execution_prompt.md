# GPUサーバー側Codexへの実行依頼：第一研究S4 Phase B v1.1

S4 Phase Aは正常に完了し、予測はcommit・hash固定されています。初回Phase Bはdirect
計算前に、保存済み下側anchorが6群で存在しないことを検出して停止しました。初回の
未完了出力を保存したまま、Phase A予測を一切変えず、uniform new-anchor v1.1で
Phase Bだけを一度再実行してください。

今回の範囲は **S4 Phase B v1.1のみ** です。Phase A再実行、selector修正、閾値調整、
S5、新分子、別基底、別精度、PF探索、追加diagnosticへ進まないでください。

## 固定版

- v1.1実装commit：`96699df`
- amendment：`review_response/pf_first_study_s4_uniform_anchor_protocol_v1_1.json`
- amendment SHA-256：`9ce996b2732e02a7bb2fa4f1d6f8a4e09fd503896a4eda7a9a4496be0f402150`
- parent S4 protocol SHA-256：`5c3c33fab6752b5ccf0ec9ee415e115bdf2134256e5a956f6b0e9b639f554c40`
- v1.1 runner：`review_response/run_pf_first_study_s4_state_convergence_v1_1.py`
- frozen Phase A commit：`95ed24c74bb29d883bbaf76d4578ff7af08ed995`
- frozen prediction SHA-256：`47cdef9b52ea73feef0c005229cb9a482ee8e95afff87f038ff8461549f1c729`
- Phase A artifact：`artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f/`

## 最初にv1履歴を保存・pushする

現在の`gpu-first-study-s4-state-convergence-results-20260925`で、Phase A commit
`95ed24c...`と初回Phase B停止状況を失わないでください。未完了Phase B directoryは
削除、変更、commit、cache流用しません。

Phase A commitを含む現在の結果ブランチを、まず同名の新規remote branchへpushして
ください。force-pushしません。未完了Phase B出力はuntrackedのまま元worktreeに保存し、
その絶対パスを記録します。

## v1.1結果ブランチ

`git fetch origin --prune`後、Phase A commit `95ed24c...`から独立worktreeと次の新規
ブランチを作ります。

`gpu-first-study-s4-state-convergence-v1-1-results-20260925`

同名があれば連番を付けます。この新規ブランチへv1.1実装commit `96699df`だけを
cherry-pickしてください。Phase A commitが祖先に残り、Phase A artifactがtrackedかつ
byte-identicalであることを確認します。既存作業ツリーをreset、clean、stashしません。

## anchor v1.1の固定規則

初回に不足した6群だけを特例扱いしません。全6条件×2 PF=`12`群へ同じ規則を使います。

各群について、frozen Phase A選択と固定係数`0.99,1.00,1.01`から得る最小挿入時刻を
`t_min`として、

`t_anchor = 0.5 * t_min`

を新規direct計算します。時刻選択にtruth値や保存grid位置を使いません。anchorでは
exact-ground overlap最大の枝を初期化し、その後は全挿入点を時刻昇順にprevious-vector
overlap最大で追跡します。

- frozen unique selection：20。
- condition/PF群：12。
- 挿入direct点：最大60。
- 新規uniform anchor：12。
- 新規direct点合計：最大72。
- 保存anchor再計算：0。
- v1 direct cache再利用：0。

新規anchorには保存shiftがないため`1e-9 Ha`再現ゲートを使いません。anchor自身に次を
要求します。

- 固有対残差`<=1e-10`。
- unitarity Frobenius残差`<=1e-10`。
- exact-ground overlap`>=0.9`。
- phase gap`>1e-8 rad`。

挿入点のprevious/ground overlap、phase gap、全strategyの採点・benefit判定はparent S4
から変更しません。

## source identity

H01は以前と同じ元成果物を読み取り専用で使います。

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`

P03もhash一致が確認済みの元成果物を読み取り専用で使います。commit収録コピーは使いません。

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-unused-molecule-holdout/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`

P03は少なくとも次を照合します。

- manifest SHA-256：`25e0f759e9b6eca995da5056fea22a12290cb237b4c400d895ca39923df819f6`
- summary SHA-256：`0f0b2590faa278e7c96f7797b81b557544d4d4469b3f13a9079b71548054ce45`
- protocol SHA-256：`b0fc69d3ef89fcae28172ae1bd89ca0b192154ff86eed34410f73cdc2a770a56`

H01/P03をコピー、修正、再manifest化しません。

## direct計算前ゲート

1. HEADにPhase A commit `95ed24c...`が祖先として含まれる。
2. v1.1 amendment hashとparent protocol hashが一致する。
3. Phase Aの4固定ファイルがcurrent HEADにcommit済みでbyte-identicalである。
4. prediction SHA-256が`47cdef9b...`である。
5. 20 unique selection、12 condition/PF群がexact一致する。
6. 保存した初回Phase B directoryに`COMPLETE`がなく、direct cacheが空である。
7. H01/P03 source identityが全件合格する。
8. 次のtestが合格する。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -m pytest -q \
  review_tests/test_pf_first_study_s4_state_convergence.py \
  review_tests/test_pf_first_study_s4_state_convergence_v1_1.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_s0_exact_time_scoring.py \
  review_tests/test_pf_first_study_s0_exact_time_scoring_v1_1.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

## 実行

単一GPU・単一processで実行します。出力先は新規で上書きしません。

`artifacts/server_pf_first_study_s4_state_convergence_v1_1_20260925_96699df/`

`--failed-phase-b-root`には元worktreeに保存した初回未完了Phase B directoryの絶対パスを
指定してください。Phase A directoryは新worktree内のcommit済み相対パスを使います。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -u review_response/run_pf_first_study_s4_state_convergence_v1_1.py \
  --project-root "$PWD" \
  --phase-a-root artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f \
  --failed-phase-b-root /absolute/path/to/preserved/incomplete_s4_v1_phase_b \
  --h01-root /home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8 \
  --p03-root /home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-unused-molecule-holdout/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797 \
  --backend gpu \
  --gpu-id 0 \
  --output artifacts/server_pf_first_study_s4_state_convergence_v1_1_20260925_96699df
```

新しいoutputの`.runtime/direct_cache`だけは同じv1.1 runの再開に使えます。cache keyには
amendment hashが含まれるためv1 cacheは受理されません。同時並列化しません。

## 結果、test、push

全source/numerical gate合格時だけ`complete_with_benefit`または
`complete_no_benefit`と`COMPLETE`を許します。失敗時は`failed_numerical_validation`
として閾値を緩めません。

計算後に集中testと全`review_tests`を実行し、prediction/amendment hash、branch CSV、
strategy scoring、decision、audit、manifest、COMPLETE条件を照合してください。

pickle、`.runtime`、`.npy`はcommitしません。軽量成果物とtest logをv1.1結果ブランチへ
commitし、originへ新規pushします。mainへmerge、force-pushしません。

最終報告では次を示します。

- v1結果ブランチpush、v1.1結果ブランチ、Phase A commit、v1.1実装・最終commit。
- parent protocol、amendment、predictionの3 hash。
- 20 unique selection、60以下の挿入点、12新規anchor、総新規direct点。
- 12 anchor時刻、最小anchor ground overlap・phase gap。
- 最大固有対/unitarity残差、最小挿入previous/ground overlap・phase gap。
- 7 strategyの安全数、平均・最大主regret、benefit/no-benefit判定内訳。
- 実行時間、CPU/GPU最大メモリ、test件数、未解決事項。

その後停止し、S5や追加実験へ進まないでください。
