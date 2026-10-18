# 暫定の作業優先度と依存関係

**第一研究の既存証拠と本文の対応確認を、次の文書作業の第一候補として推薦する。** 科学的価値・採択可能性の順位ではなく、既存証拠で完成に近づける作業の推薦である。新しい研究方向の正式採択は0件。カードは[残作業表](remaining_work_and_approval_matrix.md)を参照。

| 暫定順 | 推薦する作業 | 根拠と限界 | 先行する入力・判断 |
| --- | --- | --- | --- |
| 1 | A-1：第一研究の本文/証拠対応 | 既存結果だけで論文化する方針が明確 [S03]。固定判定・主張台帳・数値/source索引・4主図3表があり、新scienceを必要とせず文書上の欠落を特定できる [S02][S04][S06]。本文完成を示す証拠は不足 | ユーザーが対象本文版を指定。本文が未作成なら、その事実を返す。本文執筆やclaim変更は別指示 |
| 2 | A-2：第二研究の後続証拠配置 | Direction C、3図、outline/abstract、後続G/R/prospectiveの固定mapが揃う [T01][T03][T06][T07]。追加取得より、既存構成と新しい証拠の配置確認が具体的 | GPT／ユーザーが第一研究との境界・中心claimを判断する材料を作る。10/5の `review_required` を後続science完了だけで解除しない |
| 3 | A-3：Track Aの原稿/最新結果delta | 通し原稿と図bundleは存在するが、v0.4はH8 core未統合の時点 [A03][A11]。10/18のA/B/D・H4追加・new2・theory/compiledが公開され、原稿との時点差が大きい [A05]–[A10] | 最新証拠の対応表まで。保存単価統合・順位更新はDで別承認。科学的着地点と必要な保証をGPT／ユーザーが決める |
| 順位保留 | A-4：旧高次PF原稿の版同定 | ローカルTeX/図/PDFはあるが、公開固定版・最新正式claim・editorial対応の関係を確認できていない。第一/第二研究との重複も未確定 | 対象版・公開可能資料の指定が先。原稿ファイルの存在数や古いPDFだけで高順位にしない |
| 現在の追加投資対象にしない | Track B/M1-S・保留探索の新規研究 | Track B最新分類はA証拠不足/B記述結果のみ [B01][B02]。M1-Sは統合記録があり、正式研究方向は未採択 [C02]。B-01、A2、研究④選定等のSTOPを維持 [H01][Q01][Q03] | 既存ノート・理論・限定結果を保存。終了の新採択や数学的no-goへ変換しない。追加レビュー・再開は別判断 |

1–3は互いの完了を必須にする科学的依存関係ではない。順序は、証拠の固定度・文書の不足の特定しやすさ・追加承認を要する部分の少なさから推薦した。数値scoreは用いていない。投稿先、著者作業量、外部原稿の最新状況、別chatの未保存判断は確認しておらず、それらで順序を変える余地がある。

第一・第二研究は共通HF/B0を共有するが、第一の校正機構/許容域/regretと、第二の追加情報/width/decision headroomのscopeを区別する [S03][T01][T06]。同じ結果を独立成果数へ加算しない。旧高次PF原稿を三本目の独立完成論文と認定せず、版同定後に境界を判断する。

PR Track Aのcompiled信号費用、Track Bのfinite Taylor synthetic、M1-Sの単一信号/方向制御理論には異なるtask・情報・価格・保証がある。それぞれの局所利益を他系列のpriorityやend-to-end優位の根拠へ流用しない。D1・D2の既存制約を維持する。

**今回の次段階はユーザー／GPTによる作業選択。Codexは公開照合後STOPする。** 新たな文書作業を選ばない場合も、既存成果の保全だけでよい。順位保留の解消や新規研究を必須課題にしない。

<!-- fixed-source-index -->

[A03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/docs/manuscripts/track_a_resource_study_geometry_native_v0_4.md
[A05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/839c403004cf9343730c43adb346024aea41999b/docs/research/track_a_h8_ab_20261018.md
[A10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/7e454b91185ed7b0f92a3790f800ba5d65d5f156/docs/research/track_a_pr_theory_vs_compiled_completed_20261018.md
[A11]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/artifacts/resource_applicability/track_a_h4_b0i_manuscript_integration/2026-10-14/README.md
[B01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/aafa0f4a42fc0b5780e0716c4bd7c7710bfa4d14/docs/research/track_b_paper_claim_survey_20261018/handoff.md
[B02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/aafa0f4a42fc0b5780e0716c4bd7c7710bfa4d14/docs/research/track_b_paper_claim_survey_20261018/paper_claim_sheet.md
[C02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/5f079dbe67bb35eff35613857b169fdf812af4b8/docs/research/m1s_integration_20261017/codex_restart_handoff.md
[H01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/research_exploration/b01_pause_decision_20261018/research_pause_decision.md
[Q01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/f7e103bf3a0ffcee6162bd4b8d244f9a2f4502c5/docs/research/qc_a2_current_route_handoff_20261018/handoff.md
[Q03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/7eff8a33bef4ee1f29698ab10c6da46988dc8db5/docs/research/qc_iv_selection_hold_20261018/decision_record.md
[S02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/PF_first_study_final_decision_20260925.json
[S03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/PF_first_study_paper_claim_ledger_20260926.md
[S04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/evidence/paper_evidence_matrix.md
[S06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/figures/paper_figure_manifest.json
[T01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[T03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/result_synthesis_20261005/manuscript_outline_and_abstract.md
[T06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/evidence_integration_20261006/evidence_map.md
[T07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/artifacts/study2_result_synthesis_20261005/COMPLETE.json
