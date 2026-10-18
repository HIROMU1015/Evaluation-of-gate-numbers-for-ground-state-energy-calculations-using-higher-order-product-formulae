# GPT／ユーザー向け：B-01保留後の既存成果完成

**B-01を正式保留し、既存結果で進める文書作業の第一候補を第一研究とする暫定推薦をまとめた。** Phase Bは研究管理資料だけであり、科学的価値の順位・投稿GO・研究方向の正式採択ではない。

読む順序：[暫定優先度](provisional_priority_and_dependencies.md) → [研究状態](research_portfolio_status.md) → [原稿・図表inventory](publication_readiness_inventory.md) → [残作業と次のカード](remaining_work_and_approval_matrix.md) → [SOURCE](source_registry.json)・[観測](repository_observation.json)・[provenance](provenance.json)・[静的監査](static_audit.json)。

Phase A最終公開commit：`d26aa812226819c406d6ce645dbb3c1056b0e8ee`、branch `qc-b01-pause-decision-20261018`。[正式保留handoff](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/research_exploration/b01_pause_decision_20261018/research_decision_handoff.md)。B-01状態は `PAUSED_PENDING_NEW_EVIDENCE`、根拠E。数学的不可能性ではない。正規化moment/confidence/費用、有用な合法eta、同一D1での具体的生成/費用命題などの新証拠と、GPT／ユーザーの別判断が再開条件。自動探索・再開しない。

Phase Aのremote SHA・空bare独立fetch・11blob/bytes/SHA-256・固定rawを確認し、保全を確認してからPhase Bを開始した。開始時の308 checkoutは、同時に別作業で追加されたPR worktree1件を追加entryとして区別すると元status/未追跡metadataに完全一致した。厳密な全snapshot等値ではない点と確認方法はPhase A receiptに保存している [H02]。新規登録を消したり他作業を止めたりしていない。

主な確認結果は次の通り。

- **第一研究**：S0–S4、主張台帳、evidence matrix、4主図・3表まで固定。S4 negativeとS5非実施を保持し、既存結果での論文化方針を確認した [S02][S03][S04][S06]。新しい通し本文完成・reverse fact audit完了は未確認。FS-R1 productionは未承認の別系列 [S07]。
- **第二研究**：Direction C、outline/abstract、3主図、後続G/R/prospectiveのevidence mapあり [T01][T03][T06][T07]。限定claimの配置と第一研究との境界が判断点。絶対identity・総費用・一般保証の未確立を追加実験の自動ToDoにしない。
- **Track A**：v0.4原稿/図は存在するが、10/18の後続A/B/D等は原稿の時点より新しい [A03][A05]–[A10]。旧「未着手」を最新完了状態と混同しない。単価取得と総費用再会計を区別する。
- **旧高次PF**：local TeX/図/PDFの存在と最小identityを確認した。対象の正式原稿版・公開対応・editorial処理は未確定のためpriority保留。非公開原稿・指示・レビュー・editorial本文は公開していない。
- **Track B/M1-S**：技術ノート/理論・限定結果を保全。Track B最新技術分類はA証拠不足/B記述のみ [B01][B02]、M1-S研究方向は未採択 [C02]。独立論文化や再開を認可していない。

GPT／ユーザーには、まず次の文書作業をA-1（第一研究）から始めるか、A-2（第二研究）、A-3（Track A）を優先するかを判断してほしい。A-1には対象本文版の指定が必要。旧高次PFを優先するならA-4の版・SOURCE同定が先になる。科学的な中心claim、独立論文としての着地点、追加重要レビュー・計算の要否は別の判断であり、今回Codexは代行していない。

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。
Branch：`qc-research-portfolio-priority-20261018`。
Directory：`docs/research_exploration/research_portfolio_priority_20261018/`。
本資料はPhase A最終commitをbaseとし、Phase B追加directory以外を変更しない。PRはread-only参照。SOURCEのorigin/resultとverified snapshotは別fieldで保存する。

公開後はremote SHA・新規空bareへの独立fetch・全blob/bytes/SHA-256・commit固定rawを照合し、receiptを別子commitに記録する。receipt自身の最終commitも別に照合する。未実施の公開確認を先にPASSとはしない。既存310 checkoutのmetadata、両dirty rootのstaged/unstaged diffとuntracked metadataを確認する。別作業のG6 application survey worktreeには進行に伴うmetadata変化を観測したため、当該1 checkoutの不変性は主張しない。その他309 checkoutと両rootの保全を別に照合し、例外を監査へ明記する。他作業への書込み・停止は行わない。untracked全内容・ignored runtime・共有job全体の監査ではない。

**Mandatory STOP：Phase Bの公開・同一性・保全確認後に停止。** 文書カードも未開始のままユーザーへ返す。新規科学計算、保存値再解析、回路build/compile、重要科学レビュー、新算法探索、原稿執筆・claim変更、投稿、契約/grant発行、他系列状態変更は全て0件。次の担当はGPT／ユーザーで、具体的な次作業の採否と範囲を選ぶ。

<!-- fixed-source-index -->

[A03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/docs/manuscripts/track_a_resource_study_geometry_native_v0_4.md
[A05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/839c403004cf9343730c43adb346024aea41999b/docs/research/track_a_h8_ab_20261018.md
[A10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/7e454b91185ed7b0f92a3790f800ba5d65d5f156/docs/research/track_a_pr_theory_vs_compiled_completed_20261018.md
[B01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/aafa0f4a42fc0b5780e0716c4bd7c7710bfa4d14/docs/research/track_b_paper_claim_survey_20261018/handoff.md
[B02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/aafa0f4a42fc0b5780e0716c4bd7c7710bfa4d14/docs/research/track_b_paper_claim_survey_20261018/paper_claim_sheet.md
[C02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/5f079dbe67bb35eff35613857b169fdf812af4b8/docs/research/m1s_integration_20261017/codex_restart_handoff.md
[H02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/research_exploration/b01_pause_decision_20261018/publication_receipt.json
[S02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/PF_first_study_final_decision_20260925.json
[S03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/PF_first_study_paper_claim_ledger_20260926.md
[S04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/evidence/paper_evidence_matrix.md
[S06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/figures/paper_figure_manifest.json
[S07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/GO_NO_GO_FOR_PHASE_B_PRODUCTION.json
[T01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[T03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/result_synthesis_20261005/manuscript_outline_and_abstract.md
[T06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/evidence_integration_20261006/evidence_map.md
[T07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/artifacts/study2_result_synthesis_20261005/COMPLETE.json
