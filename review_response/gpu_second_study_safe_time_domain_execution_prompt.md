# GPUサーバー側Codexへの将来実行依頼：第二研究 safe-time-domain v1

この文書はprotocol完成後の将来実行用である。protocol branch上では新規分子生成、Phase A、
Phase B、direct truth計算を開始しない。まずPhase A/Phase B runnerを別の実装commitとして
reviewし、明示的に実行を開始するときだけ以下を使う。

## 固定版

- protocol base：`123c84d459613db109dc23aa3b0872334fa12ddd`
- protocol branch：`second-study-safe-time-domain-protocol-20260927`
- protocol：`review_response/second_study_safe_time_domain_protocol.json`
- protocol SHA-256：同梱
  `review_response/second_study_safe_time_domain_protocol.json.sha256`の先頭field
- source/leakage audit：
  `review_response/second_study_safe_time_domain_source_leakage_audit.json`
- PF：`current_m3`だけ
- 情報源：`multiple_window_consistency`だけ
- 独立評価：LiF active-space 2条件、HCl full-electron 2条件
- target error：`0.00015936001019904 Ha`
- `gamma=1.01`、`beta=1.2`
- Phase B direct truth：最大44点

## 実装前ゲート

次のrunner名を固定する。

- `review_response/run_second_study_safe_time_domain_phase_a.py`
- `review_response/run_second_study_safe_time_domain_phase_b.py`

runnerが存在しないprotocol-only commitから計算を始めない。実装commitでは、
`review_response/second_study_safe_time_domain_guard.py`を使ってselector payload、prediction、
freeze marker、Phase B座標を検査する。protocolの科学的定数をrunner側へ複製せずJSONから読む。

実装testは少なくとも次を含める。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -m pytest -q \
  review_tests/test_second_study_safe_time_domain_protocol.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

## Phase A前の独立性preflight

GPUサーバーのrepository、全worktree、untracked `artifacts/`、log、archive名を、次の4 IDと
`LiF`、`HCl`、固定geometryで検索する。

- `LiF_active_eq_sto3g`
- `LiF_active_stretch150_sto3g`
- `HCl_full_eq_sto3g`
- `HCl_full_stretch150_sto3g`

既存のPF誤差、QPE費用、proxy response、direct truthを一件でも発見したら、別分子へ
差し替えない。`no_go_independence_contaminated`を記録して停止する。文書や分子名一覧だけで
数値結果がなければ、そのpathと判定根拠をauditへ記録する。

次の第一研究source identityもhash照合する。

- `artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`
- `artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`
- `artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201/`
- `artifacts/server_pf_first_study_s4_state_convergence_v1_1_20260925_96699df/`
- `artifacts/pf_first_study_regret_decomposition_20260925_7f0b30d/`
- `artifacts/pf_first_study_completion_analysis_20260926_940ee7f/`
- `paper/evidence/paper_source_manifest.json`
- `paper/figures/paper_figure_manifest.json`

P03/H01の既存pickleとdirect truthは開発sourceのidentity確認と資源見積り専用であり、独立4条件の
Phase A inputやPhase B cacheに流用しない。

## Phase A branchとworktree

protocol final commitから独立worktreeと新branch
`second-study-safe-time-domain-phase-a-results-20260927`を作る。同名があれば連番を付ける。
既存worktreeをreset、clean、stashしない。mainへmerge、force-pushしない。

Phase A outputは新規にする。

`artifacts/server_second_study_safe_time_domain_phase_a_20260927_<implementation-short-sha>/`

Phase Aではexact ground state/energy/gap/overlap、direct PF eigenvalue/error/cost、既存label、
truth pathを作らず、開かず、selectorへ渡さない。分子生成中のsector選択もRHF determinantと
CISD supportだけで行う。exact diagonalizationをPhase Aの便利なvalidationとして実行しない。

将来runnerのCLIは次の形にする。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -u review_response/run_second_study_safe_time_domain_phase_a.py \
  --project-root "$PWD" \
  --protocol review_response/second_study_safe_time_domain_protocol.json \
  --processes 1 \
  --output artifacts/server_second_study_safe_time_domain_phase_a_20260927_<implementation-short-sha>
```

Phase A完了時に、4条件、4 strategy、取得したproxy prefix、全古典情報count、prediction hash、
protocol hash、最大44点のPhase B座標計画を照合する。pickle、`.runtime`、`.npy`をcommitしない。
軽量成果物、test log、`PHASE_A_FROZEN.json`をcommit・新規pushし、ここで一度停止する。

## Phase B前ゲート

Phase A commitとprediction SHA-256を実行依頼へ明記し、次をすべて確認する。

1. Phase A commitがHEADの祖先で、originに存在する。
2. protocol hashとsource auditが一致する。
3. `predictions.json`がcommit済みで`prediction.sha256`とbyte-identical。
4. oracle-access counterが全て0。
5. 4条件と4 strategyがexact一致。
6. coordinate planは36 candidate、最大4 current-selection、4 anchor、総数最大44。
7. Phase B outputは新規で、第一研究direct cacheを含まない。
8. GPU free memoryが8 GiB以上。
9. 集中testと全`review_tests`が合格する。

## Phase B branchと実行

Phase A commitから別worktreeと新branch
`second-study-safe-time-domain-phase-b-results-20260927`を作る。同名があれば連番を付ける。

Phase B outputは次とする。

`artifacts/server_second_study_safe_time_domain_phase_b_20260927_<implementation-short-sha>/`

単一GPU・単一processで実行する。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
python -u review_response/run_second_study_safe_time_domain_phase_b.py \
  --project-root "$PWD" \
  --protocol review_response/second_study_safe_time_domain_protocol.json \
  --phase-a-root artifacts/server_second_study_safe_time_domain_phase_a_20260927_<implementation-short-sha> \
  --backend gpu \
  --gpu-id 0 \
  --processes 1 \
  --output artifacts/server_second_study_safe_time_domain_phase_b_20260927_<implementation-short-sha>
```

同じPhase B runの`.runtime/direct_cache`だけ再開に使える。cache keyにはprotocol hash、prediction
hash、Hamiltonian hash、formula hash、absolute time hex、backend、dtype、branch-rule versionを
含める。他run、第一研究、別protocolのcacheは拒否する。同時並列化しない。

## 数値gateと採点

- 固有対残差`<=1e-10`。
- unitarity Frobenius残差`<=1e-10`。
- anchor ground overlap`>=0.9`。
- 全追跡点のprevious/ground overlap`>=0.9`。
- phase gap`>1e-8 rad`。
- branch disagreement 0。

失敗時は`failed_numerical_validation`として停止し、閾値を緩めない。

`current_fallback`、`equal_information_pooled_fit`、`multiple_window_rule`、
`uncapped_counterfactual`を分離する。counterfactualは安全な運用法として数えない。
direct interpolation、連続global oracle表現、別PF順位を使わない。

主表には精度未達、execution/extension coverage、棄却、凍結Pauli rotations、fixed-grid regret、
同情報費用baselineとの差、状態生成、Hamiltonian作用、PF action、group spectrum、proxy点、
CPU/GPU秒数・memoryを含める。古典秒数とPauli rotationsを加算しない。

全gate合格時だけ`complete_with_benefit`または`complete_no_benefit`と`COMPLETE`を許す。
benefit条件はprotocol JSONから一つも変更しない。

## 最終test、commit、push、停止

集中testと全`review_tests`を実行し、protocol/prediction/source hash、coordinate数、branch audit、
4 strategy採点、decision、manifest、COMPLETE条件を照合する。pickle、`.runtime`、`.npy`はcommit
しない。軽量成果物とtest logを結果branchへcommitし、originへ新規pushする。

最終報告にはbranch/commit/hash、4条件、proxy点・direct点、各時刻、数値残差、accuracy/coverage/
rejection、4 strategyの予算とregret、状態生成・Hamiltonian作用・group spectrum・校正点数、
実行時間、CPU/GPU memory、test件数、未解決事項を示す。その後停止し、閾値再調整、別分子、
別基底、別精度、別PF、S5へ進まない。
