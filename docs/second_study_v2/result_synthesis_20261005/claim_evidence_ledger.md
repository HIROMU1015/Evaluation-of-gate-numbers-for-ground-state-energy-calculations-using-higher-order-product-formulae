# 第2研究の主張と証拠の対応

本台帳は保存結果、固定モデル内の代数、post-hoc oracle、governanceを分離する。
30座標は10 native条件に属し、行数を独立標本数とみなさない。
Data snapshotはbfe715fc1c04325535a3c4d63ea4584e691dc322。
以下のCSVリンクは公開handoff commit内で同じbytesを保持する。

| ID | 主張 | Evidence class | 根拠と抽出key | 図と比較対象 | 限定と未確立事項 |
|---|---|---|---|---|---|
| C1a | e-c<=M_gammaは指定cheap budgetのsafe条件と同値 | fixed_model_algebra | [仕様](../budget_safety_mechanism_20261005/quantity_dictionary_and_analysis_spec.md)、[capacity](../../../artifacts/budget_safety_mechanism_20261005/budget_safety_capacity.csv)、全gamma。gamma1はslack | Fig1の説明軸 | 新PF theoremではない。c>=epsは式不適格、e>=epsは有限safe予算なし |
| C1b | 現gateのq=0/内部安定性は安全性の代用にならない | frozen_decision_empirical + post_hoc_replay | [selected](../../../artifacts/budget_safety_mechanism_20261005/selected_frozen_budget_safety.csv)、HF eq/stretch arm=B2,H1、candidate=1p6T0。safe=False/True | Fig1、同じfixed1.01と保存decision | 2 development条件。新holdoutではなく、全cheap情報の不可能性やspectral不可欠性ではない |
| C1c | Signed精度とabsolute-error underestimationは違う | saved_scalar_empirical | [capacity](../../../artifacts/budget_safety_mechanism_20261005/budget_safety_capacity.csv)、stretch_1p6T0,gamma1.01。cheap negative/truth positive、uはmargin内 | Fig1b、HF eqとの対比 | Uncorrected taskに限定。Signed精度がbias correctionでも不要とは言わない |
| C2a | 名指しsafe同時刻対照のperfect-truth headroomは10%未満 | fixed_model_cost_free_oracle_arithmetic | [same-time](../../../artifacts/budget_safety_mechanism_20261005/same_time_oracle_headroom.csv)、HF1.01 5/6、Hchain1.01 18/18、HCl1.02 6/6 | Fig2a、29 valid comparisons | Unsafe HF eq1.6T0は未定義。別時刻/PF/correction/gamma/metricを含めない。取得費用と達成可能性は未確立 |
| C2b | Fixed M1 pointのwidth-only win windowとoracle floorは違う | post_hoc_fixed_point_arithmetic | [windows](../../../artifacts/budget_safety_mechanism_20261005/width_decision_windows.csv)、same_time_fixed_cheapのnative gamma、eta0/.1 | Fig2c、当該coordinateのsafe対照 | Negative windowをゼロにしない。Rank/branch gateは独立、非負窓でも運用successとは限らない |
| C2c | M1 point改善は採用利益へ直結しない | fixed_package_empirical | [M1](../../../artifacts/budget_safety_mechanism_20261005/m1_point_width_abstention.csv)、HF6改善/0abstain、Hchain11改善/12abstain、HCl6改善/1abstain。[selected](../../../artifacts/budget_safety_mechanism_20261005/selected_frozen_budget_safety.csv)、always_M1 | Fig2b,d、fixed cheapと保存M1 | Empirical widthはcertificateではない。全M1 pointが良いともspectral全般が劣るとも言わない |
| C2d | H-chain fixed cheapのselected r=.8は元3候補のoracle最良と同じ | post_hoc_fixed_native_candidate_oracle | [native oracle](../../../artifacts/budget_safety_mechanism_20261005/oracle_headroom_by_contract.csv)、H2/H4/H5/H6/H7/H8 oracle_candidate_id | Fig2a,d、選択済みcheapから残り0.9766–2.7290% | 元表のoracle_relative_savingはB0基準で別量。連続最適化や候補外の最適性ではない |
| C2e | 共通fixed gamma1.10に対しHF aggregate M1 advantage約1.46%が残る | saved_fixed_arm_arithmetic | [selected](../../../artifacts/budget_safety_mechanism_20261005/selected_frozen_budget_safety.csv)、HF2条件 B1_gamma_1.1/always_M1。572482494.3535492 vs 580977536.2089661 | 本文の補助比較、same-time1.01の図とは別 | 事後条件別最小safe gammaと混同しない。2条件等重みのbudget合計で、未知系・net benefitではない |
| C3 | PF回収精度とH-reference誤差がshift点精度へ別々に寄与 | identity_verified_saved_decomposition | [decomp](../../../artifacts/budget_safety_mechanism_20261005/m1_reference_error_decomposition.csv)、same_H_origin_physical_lift_verified_saved_diagnosticの18点 | Fig3、A,R,保存shift error | H2丸め域。HF/HCl12未確定。誤差相殺原理・state/rankの因果性・certificateを新規claimにしない |
| S1 | H-chain約33%は固定domain/modelに近い安全なbenchmark比較 | model_arithmetic + empirical_safety | [model](../../../artifacts/budget_safety_mechanism_20261005/hchain_model_vs_observation.csv)、全6系 | 付録、leading modelと保存B2/B0 | 差0.0563–0.3199ppは独立adaptive因果効果ではない |
| S2 | 情報取得costはstage別の観測範囲に限定される | saved_resource_inventory | [resource](../../../artifacts/budget_safety_mechanism_20261005/resource_accounting_scope.csv)、元source/JSON pointer/cost_scope | 付録、quantum Bとは別unit | 2220 leavesは足し合わせない。q=1/cold/end-to-end未計測 |
| G1 | Direction Cと論文中心claimを採用し現B2/H1を主運用非採用 | governance_scope | [ユーザー承認GPT原文](approved_gpt_review.md)、[承認反映](approved_scope_and_rq.md) | RQとmethod roles | 実験から自動導出されたscience claimではなく、追加scienceの許可でもない |

証拠traceは[figure data](../../../paper/study2/figures/figure_data.json)に元rowと行番号で保存する。
同じCSVの全行を独立なevidenceとして増やさない。
旧D2-A integer branch formal判定と後のphysical branch auditは原本を維持し、
表示統合によってformal decisionを上書きしない。
