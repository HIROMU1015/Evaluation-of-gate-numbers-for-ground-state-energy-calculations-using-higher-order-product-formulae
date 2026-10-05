# G2後の研究方針レビュー資料 — 統合版

Status: `second_study_v2_g2_review_integration_complete_review_required`

**Direction Cを暫定主線として保持し、現B2/H1 gateは主方式に採用しない。** これは最終方針の承認ではなく、G2を反映したレビュー用提案である。科学結果は既存の凍結済み成果物、研究上の位置付けは `governance_scope` として区別する。

## 今回追加された判断材料

| Contract / 条件 | 固定ruleの結果 | 言えること | 言えないこと |
|---|---|---|---|
| H-chain適格6系 | q=0、B2=H1=fixed cheap 1.01、safe/target。H3はreference適用不能で未採点 | 試したcontractにはcheap-sufficient regimeがある | 適応・selectiveの追加利益、全分子の安全性 |
| HF equilibrium G2 | q=0、gamma=1.01、1.6T0、B2/H1 unsafe | cheap stability gateのdevelopment false negative | cheap全方式の否定、spectralの不可欠性 |
| HF stretch150 G2 | q=0、gamma=1.01、1.6T0、B2/H1 safe | 同じruleでも条件で安全性が異なる | 未使用条件への一般化 |
| HCl D2-A/C0 | 別auditではphysical branch 6/6、同時刻baselineより低予算0/6 | 点精度とwidth・decision utilityは別 | 元formal statusの置換、幅の厳密certificate |

G2正式分類は **`D_gate_false_negative`**。元S1Aの `D_contract_or_cost_not_replayable` とは別taxonomyであり、旧S1Aを解除した結果ではない。

## HFの安全な対照

`epsilon_E=0.00015936001019904 Ha`。Scorerは凍結済み連続budgetに対して `abs(delta_direct)+beta*K/(t*B_frozen)<=epsilon_E` を適用した。

| 条件 | B2/H1 budget | safety LHS [Ha] | B2/H1 | safe fixed cheap対照 | always-M1 budget |
|---|---:|---:|---|---|---:|
| equilibrium | 313366606.6694983 | 0.00017072575273433498 | unsafe | gamma=1.10: 341290363.69945365 | 351773269.593654 |
| stretch150 | 220076403.84964326 | 0.00015841630475708096 | safe | gamma=1.01: 220076403.84964326 | 220709224.75989527 |

T0 controlは2/2 PASS、B0は2/2 safe。Always-M1も2/2 safe/10%target、物理branch・経験的width coverageは6/6。ただしH1はM1を取得せず、H1=B2、decision changeは0。q=1 combined pathは未観測である。

各条件のsafe cheap対照はtruth後の診断であり、そのgammaを未知条件で選べるpolicyは未確立。Common gamma=1.10のsafe aggregate 580977536.2089661とalways-M1 572482494.3535492の差（約1.4622%）は元bridgeと同じ保存データに基づく対照差で、selective benefitではない。Unsafeを含むB2/H1 aggregate 533443010.51914155を資源利益に数えない。

## レビューの順序

1. [統合evidence matrix](evidence_matrix.csv)：旧24行をそのまま保持し、G2の2条件とaggregateの3行を追記。27行は27 independent samplesではない。
2. [方式の位置付け](method_positioning.md)：cheap-first baseline、spectral条件付き対照、現gate非採用の範囲。
3. [RQ提案](research_question_review.md)、[方向比較](direction_comparison.md)、[論文着地点](publication_landing_options.md)。
4. [新規性の限定](novelty_assessment.md)、[人間レビュー事項](review_questions.md)。
5. [機械可読decision](decision.json)、[出典](source_registry.json)、[照合audit](validation_audit.json)、[manifest](manifest.json)。

## 保存する境界

旧レビューは[元bundle](../research_direction_review_after_hchain_20261005/recommended_direction.md)として保存。G2 [handoff](../../../artifacts/hf_g2_fixed_rule_replay_20261005/publication/handoff.md)・[result](../../../artifacts/hf_g2_fixed_rule_replay_20261005/result/result.json)・prediction、旧正式判定、runner manifestは変更しない。G2は既知developmentデータのpost-hoc replayであり、prospective blind/holdoutではない。

今回行うのは文書統合とbyte/hash/scalar対応の検査のみ。新PF/H action、Arnoldi、truth/gap/state生成、fit、gate調整、combined acquisition計測は0。Full legacy suiteは実行しない。最終RQ・方針文書・`docs/current_research_status.md`の更新、HCl/LiF/C1/D2-B、外部baseline実装は未許可。Local commitまで、pushは別指示。ここで研究方針レビューへ戻る。
