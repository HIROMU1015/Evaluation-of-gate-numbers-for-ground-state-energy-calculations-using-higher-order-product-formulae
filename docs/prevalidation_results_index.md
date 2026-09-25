# PF研究事前検証のGitHub結果索引

最終更新：2026-09-25

この文書は、`PF_research_prevalidation_catalog_2026-09-20.md`から実際に実行し、研究判断に採用した検証の固定結果をGitHub上で追跡するための索引である。カタログの128項目すべてを完了一覧として扱わず、実行済みの最終・採用結果だけを記載する。

失敗した初回実行や、後続retryで置き換えられた中間成果物は科学的根拠に数えない。大容量pickle、再生成可能なcache、作業ログもGit管理対象外とする。各報告書の`Status`、audit、manifest、固定commitを確認してから引用する。

## 入口

- [事前検証カタログ](../PF_research_prevalidation_catalog_2026-09-20.md)
- [現在の研究方針と検証状況](current_research_status.md)
- [データ使用履歴](pf_data_use_ledger.md)
- [有限時間コスト戦略](../review_response/finite_time_cost_strategy.md)

## 基盤監査と既存結果再解析

この群の固定commitは`2ba6174b6f9617d51766579c775a77132f3c7f57`である。

| カタログ項目 | 内容 | 状態 | 固定報告書 |
|---|---|---|---|
| B01 | 時間発展符号・単位・定数項 | complete | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/artifacts/prevalidation_b01_time_units_constants_20260921_retry1/report.md) |
| B02 | PF係数丸め・形式次数 | complete | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/artifacts/prevalidation_b02_coefficient_order_conditions_20260921_retry2/report.md) |
| B03 | S2列・積順序・隣接マージ | complete | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/artifacts/prevalidation_b03_s2_order_merge_equivalence_20260921/report.md) |
| B04--B07 | セクター、枝、雑音床、独立経路 | complete | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/artifacts/prevalidation_b04_b07_numerical_integrity_20260921_retry1/report.md) |
| B08/C02/C03 | 再現性・解析時刻・QPEコスト単位 | complete_with_findings | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/artifacts/prevalidation_b08_c02_c03_repro_cost_units_20260921_retry1/report.md) |
| X01 | 既存結果・情報アクセス・閾値・代替策・凍結予算・費用対効果 | complete/complete_with_findings | [artifact tree](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/tree/2ba6174b6f9617d51766579c775a77132f3c7f57/artifacts) |
| X02 | 有限時間曲線とモデル整合性 | complete_with_findings | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3/report.md) |

## 小系の機構・校正診断

D04、F01/F02/F05、H01 pilot、H03/H04/H05の固定commitは`6d13384ef327e5b248c2ce93ae29ad4e7686b2e5`である。F03は本索引ブランチで初めてGit管理した。

| カタログ項目 | 内容 | 状態 | 固定報告書 |
|---|---|---|---|
| D04 | 同一古典時間予算比較 | complete_with_findings | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_d04_equal_classical_budget_20260922/report.md) |
| F01 | 有効Hamiltonian係数の直接抽出 | complete | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/report.md) |
| F02 | 8次係数の直接項・状態混合分解 | complete_with_findings | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md) |
| F03 | 小さい先頭係数と小さい誤差演算子の区別 | complete_with_findings | [report](../artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md) |
| F05 | 物理gapとPF位相gap | complete | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_f05_energy_phase_gap_20260922/report.md) |
| H01 pilot | exact/HF/CISD状態比較 | pilot_complete_with_findings | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_h01_approximate_state_pilot_20260922/report.md) |
| H03 | 行列を作らないD4作用評価 | complete_with_scaling_blocker | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_h03_matrix_free_d4_action_20260922/report.md) |
| H04 | compact BCH・重要成分選別 | complete_with_findings | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md) |
| H05 | a6/a8取得法 | complete_with_findings | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md) |

## 統一比較・ホールドアウト・後続判断

| 役割 | 内容 | 固定commit | 固定報告書 |
|---|---|---|---|
| 短時間規則診断 | NH3時刻尺度 | `84a37d1` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/84a37d15ceed616cf8d863efc1e09dbc7be3f2ba/artifacts/server_time_scale_fit_diagnosis_20260920_022258_e4509cb/report.md) |
| 高次項診断 | 全電子NH3 | `1615947` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1615947b5fe5c0a95619c26e9723812512318a55/artifacts/full_electron_nh3_higher_term_diagnosis_20260919_230358_605384c/report.md) |
| 枝規則監査 | NH3固有枝 | `76d091f` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/76d091f18b7f68b2612dc2c8267bbab5e23c12a1/artifacts/server_nh3_branch_protocol_audit_20260920_222119_d8c1d55/report.md) |
| D01/D02開発比較 | NH3既存PF統一比較 | `46a7ed1` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/46a7ed165650cb80506be14d997380e0bf333680/artifacts/server_existing_pf_unified_nh3_20260920_233516_e692360/aggregate/report.md) |
| 固定ホールドアウト | N2/CO主・HF補助 | `33a761d` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md) |
| 校正点数副解析 | 三点対五点 | `20d64c2` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/20d64c2fea1ed2d2188777df4f3d962ee94df486/artifacts/three_vs_five_point_holdout_reanalysis_20260922/report.md) |
| H01 | 近似状態校正 | `568f002` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/568f00249abb5b89ae3e6bb39cb4af87ed8581bd/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/aggregate/report.md) |
| H02 | 有限時間制御状態 | `16bd6c2` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe/artifacts/server_h02_finite_time_controlled_state_20260922_a228b5f/report.md) |
| F01/F02/F05 | HF成功・破綻機構bridge | `6eb1aa0` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md) |
| 実用候補 | practical calibration最小版 | `4f4374b` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/report.md) |
| D03 | 目標精度依存 | `a8b9a92` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a8b9a92c9fcdb1b4187d5aa3c239ed8b7443dcfd/artifacts/server_d03_target_accuracy_followup_20260923_748b3d4/report.md) |
| M01 | 資源指標感度 | `b5af699` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5af6996159b3dfbd6e5bb3cc2467cb23155906d/artifacts/prevalidation_m01_resource_metric_sensitivity_20260925_3b6e5f0/report.md) |

## 保存範囲

- 上表の結果は報告書に加え、各commit内のJSON、CSV、audit、manifest、軽量図、関連testで確認する。
- H01/H02やHF bridgeで使った大容量pickle/cacheはGitHubへ複製していない。manifestのhashと固定集計を再現性の根拠とする。
- `complete_with_findings`は検証が未完了という意味ではなく、固定した監査が修正点、適用限界、または反例を発見したことを表す。
- 初回失敗や置換済みretryを最終結果として引用しない。上表の固定報告書を正本とする。
