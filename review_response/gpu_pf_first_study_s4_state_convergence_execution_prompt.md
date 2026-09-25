# GPUサーバー側Codexへの実行依頼：第一研究S4 状態収束診断

第一研究S3までの統合結果を受け、S4で事前固定したoperator-sensitive二状態診断を
一度だけdevelopment比較してください。Phase Aで全strategyの予測をcommitしてから、
Phase Bで初めてdirect truthを開きます。

今回の範囲は **S4のみ** です。S5、新分子、別基底、別精度、PF係数探索、閾値調整、
追加diagnosticへ進まないでください。

## 固定した版

- 実装commit：`f66e86f`
- protocol：`review_response/pf_first_study_s4_state_convergence_protocol.json`
- protocol SHA-256：`5c3c33fab6752b5ccf0ec9ee415e115bdf2134256e5a956f6b0e9b639f554c40`
- 説明：`review_response/pf_first_study_s4_state_convergence_protocol.md`
- runner：`review_response/run_pf_first_study_s4_state_convergence.py`
- practical Phase-A commit：`79035cc7c414c04cafe8b9f8bdc779a17ec57302`
- practical prediction SHA-256：`fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e`

新しい結果ブランチは`f66e86f`から作成してください。推奨名は

`gpu-first-study-s4-state-convergence-results-20260925`

です。同名があれば上書きせず連番を付けます。既存作業ツリーをreset、clean、stash
せず独立worktreeを使い、mainへmergeまたはforce-pushしないでください。

## 元成果物

H01は、GPUサーバーに残る次の元成果物を直接使います。

`server_h01_approximate_state_calibration_20260922_011228_e0692a8`

以前の絶対パスは次でした。

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`

絶対パスが違う場合は成果物名で検索して構いません。6 pickle、6 metadata、
`aggregate/summary.json`、`truth/`、`manifest.json`、`COMPLETE`が揃う唯一の候補を
使ってください。Hamiltonianを再生成しません。

practical成果物はcommit収録の次を使います。

- practical：`artifacts/server_practical_calibration_minimal_20260923_79035cc/`

P03については、commit収録コピーの`manifest.json`が`843a3d69...`であり、practical
固定protocolが要求する`25e0f759...`と一致しません。したがってcommit収録コピーを
Phase A/Bのsourceとして使わず、S0 v1.1成功runでも使用したGPUサーバー上の元成果物を
読み取り専用で使ってください。

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-unused-molecule-holdout/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`

P03元成果物について、計算前に次を照合します。

- `COMPLETE`が存在する。
- `manifest.json` SHA-256：`25e0f759e9b6eca995da5056fea22a12290cb237b4c400d895ca39923df819f6`
- `aggregate/summary.json` SHA-256：`0f0b2590faa278e7c96f7797b81b557544d4d4469b3f13a9079b71548054ce45`
- P03 protocol SHA-256：`b0fc69d3ef89fcae28172ae1bd89ca0b192154ff86eed34410f73cdc2a770a56`

この元成果物をコピー、修正、再manifest化しないでください。実際に使った絶対パスと
3 hashをPhase A/Bのsource manifestと最終報告へ記録します。上記P03またはH01の
source hash、Hamiltonian hash、protocol hashのいずれかが合わない場合は、計算を
始めず停止してください。

## 計算前ゲート

1. `origin`が`HIROMU1015/*`であること。
2. HEADが`f66e86f`であること。
3. S4 protocol hashが上記値と一致すること。
4. practical protocol/prediction/freeze identityがrunnerの固定値と一致すること。
5. H01元成果物の6 pickleがすべてsource identity検査を通ること。
6. truthを開く前に次の集中testを実行すること。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -m pytest -q \
  review_tests/test_pf_first_study_s4_state_convergence.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_s0_exact_time_scoring.py \
  review_tests/test_pf_first_study_s0_exact_time_scoring_v1_1.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

## Phase A：truthなしの選択固定

上書きしない新規出力先を作ります。例：

`artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f/`

CPU単一processで実行します。GPUは不要です。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -u review_response/run_pf_first_study_s4_state_convergence.py phase-a \
  --project-root "$PWD" \
  --practical-root artifacts/server_practical_calibration_minimal_20260923_79035cc \
  --h01-root /absolute/path/to/server_h01_approximate_state_calibration_20260922_011228_e0692a8 \
  --p03-root /home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-unused-molecule-holdout/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797 \
  --output artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f
```

ここで使うH01パスはsanitizerだけへ渡り、`run_phase_a_selector`へは渡りません。
selectorが受け取れるのは、Hamiltonian、component spectra、term counts、full CISD、
決定論的truncated CISD、PF情報、target error、proxy作用だけです。

次を検査してください。

- full CISDを係数絶対値降順・index tie-breakで累積二乗ノルム0.99へtruncateしたこと。
- 診断時刻がfull-CISD `t_ana`の`0.1,0.2,0.3,0.5`倍であること。
- state-risk閾値が`0.05 epsilon_E`で固定され、signed sign規則も固定どおりであること。
- 現行法、PF固定2種、record-only、universal fallback、targeted fallback、
  equal-cost 7点fitの7 strategyが6条件すべてで選択済みであること。
- `oracle_information_used=false`、`new_direct_truth_point_count=0`であること。
- `PHASE_A_FROZEN`、`prediction.sha256`、`phase_a_audit.json`が整合すること。

Phase A成果物、protocol、runner、testを結果ブランチへcommitしてください。**このcommitが
完了するまでH01/P03のdirect truth JSONを開かず、Phase Bを実行しないでください。**
Phase A commitとprediction SHA-256をログへ明記します。

## Phase B：固定予測のexact-time採点

Phase A commit後にだけ実行します。上書きしない別出力先を使います。例：

`artifacts/server_pf_first_study_s4_state_convergence_20260925_<phaseA-short>/`

3136次元条件は、S0と同様に単一GPUでPF unitaryを構築しCPU Schurを行います。
単一processとし、同時並列化しません。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -u review_response/run_pf_first_study_s4_state_convergence.py phase-b \
  --project-root "$PWD" \
  --phase-a-root artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f \
  --h01-root /absolute/path/to/server_h01_approximate_state_calibration_20260922_011228_e0692a8 \
  --p03-root /home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-unused-molecule-holdout/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797 \
  --backend gpu \
  --gpu-id 0 \
  --output artifacts/server_pf_first_study_s4_state_convergence_20260925_<phaseA-short>
```

runnerはPhase Aの4固定ファイルが現在のHEADにcommit済みでbyte-identicalであることを
先に検査します。不一致ならtruth計算へ進みません。

各unique selected coordinateの`0.99,1.00,1.01`倍を計算し、条件・PFごとに同じ
H01 domainの`truth_provenance == new_h01_continuous_branch_calculation`の下側anchorを
再計算してから連続追跡します。

- unique selected coordinateは最大36。
- 新規direct coordinateは最大108。
- anchor再計算は最大12で、新規座標とは別会計。
- anchor再現差は`1e-9 Ha`以下。
- 固有対残差とunitarity Frobenius残差は`1e-10`以下。
- previous/ground overlapは`0.9`以上。
- phase gapは`1e-8 rad`より大きいこと。
- γは`1.01`だけを主採点に使う。
- 主regretは元2-PF保存grid、挿入点を含む拡張regretは副指標とする。

閾値、truncation率、診断時刻、strategy、予測、formula/time、budgetをtruth結果に応じて
変更しないでください。失敗時に閾値を緩めません。

## 成果物と判定

Phase Bでは少なくとも次を保存します。

- `protocol.json`
- byte-identicalな`predictions.json`と`prediction.sha256`
- `PHASE_A_FROZEN`
- `source_manifest.json`
- `branch_audit.csv`
- `strategy_scoring.csv`
- `reference_costs.csv`
- `decision.json`
- `audit.json`
- `manifest.json`
- `report.md`

全source/numerical gateが合格した場合だけ`complete_with_benefit`または
`complete_no_benefit`と`COMPLETE`を許します。gate失敗なら
`failed_numerical_validation`として`COMPLETE`を作りません。

benefitはprotocolの3条件をすべて満たす場合だけです。

1. targeted fallbackがγ=1.01でunsafe 0、主4条件coverage 4/4。
2. 6条件平均regretがbaselineより相対10%以上低く、条件別悪化は絶対0.10以下。
3. universal fallbackまたはequal-cost追加点より、平均regretで相対5%以上、または
   最大regretで相対10%以上よい。

`complete_no_benefit`も有効な科学結果です。その場合、diagnosticを調整せずS5へ
進みません。`complete_with_benefit`の場合も、このrun内ではS5へ進みません。

## post-run、commit、push、停止

Phase B後に集中testと全`review_tests`を実行し、ログを結果directoryへ保存します。
prediction hash、CSV件数、manifest hash、audit集計、`COMPLETE`条件を再照合します。

pickle、`.runtime`、selected-vector `.npy`はcommitしません。軽量成果物とreport、test
logを同じ新規結果ブランチへcommitし、`origin`へpushします。

最終報告では次を示してください。

- 結果ブランチ、Phase A commit、最終commit、2成果物パス。
- protocol/prediction hash。
- Phase A/B実行時間、最大CPU RSS、最大GPU memory。
- state-risk trigger matrixとtruncation係数数。
- unique selection数、新規direct点数、anchor数と最大再現差。
- 最大固有対/unitarity残差、最小overlap、最小phase gap。
- 7 strategyのγ=1.01安全数、平均・最大主regret。
- benefit/no-benefitの固定判定と各判定項目。
- test件数と未解決事項。

その後停止し、S5や追加diagnosticへ自動的に進まないでください。
