# 既存研究の現在地：Phase B

2026-10-18 JST。正式状態の変更は0件。Phase AでB-01だけを `PAUSED_PENDING_NEW_EVIDENCE` とした後の、成果完成に向けた資料整理である。科学的採択・投稿GO・新規性レビュー・追加計算の判断ではない。

観測範囲は[remote観測](repository_observation.json)、[58件の固定SOURCE](source_registry.json)、[ローカル原稿の最小identity](local_publication_inventory.json)。固定公開報告の結果を引用し、数値・順位・保証を再計算していない。研究全履歴は既存横断整理[X01][X02][X03][X04]を参照する。

| 系列 | 目的・保存成果 | 確認できた状態と限界 | 次に必要な判断 |
| --- | --- | --- | --- |
| 第一研究 S0–S4 | 有限時間PF校正の状態置換・proxy差・fit誤差、許容時刻域と安全余裕を分離。安全性と資源regretの差、固定二状態診断のnegative resultを保存 [S01][S03] | `complete_mechanism_study_no_method_benefit`。S4 `complete_no_benefit`、S5へ進まない [S02]。後続の主張台帳、evidence matrix、4主図・3表は存在 [S04][S06]。本文完成は未確認 | 既存結果だけの論文化方針を維持し、対象本文を特定して証拠対応を確認する。独立分子へのselector成功や普遍的1%安全保証へ拡張しない |
| FS-R1（第一研究の後続候補） | Phase A prediction freezeとB0 preflightが保存されている | `GO_FOR_FS_R1_PHASE_B_PRODUCTION` は準備gate。`Phase_B_authorized=false`、truth実行0、資源利益未確立 [S07]。S0–S4の完成とは別 | 第一研究を完成させる前提条件にしない。production開始は別判断・別承認 |
| 第二研究 Direction C | cheap校正の過小評価とmargin、spectral point/width/abstention、decision headroomを分離 [T01]。G/Rとprospectiveを含む後続evidence mapあり [T05][T06] | Direction C承認済み。成果整理版は `complete_review_required`、3主図、outline/abstractあり [T02][T03][T07]。G/Rは完了受理、H-chain追加scienceはいったん終了 [T05]。新selector・certificate・総費用優位は未確立 | 10/5構成案・図と10/6後続証拠の配置、第一研究との境界、限定claimをGPT／ユーザーが判断する |
| Evaluation高次PF・既存原稿 | 高次PFの分子基底energy向け費用評価という既存原稿系列。履歴PDFあり [M01]。現rootには別のTeX・図・3月/5月PDFが存在 | [local inventory](local_publication_inventory.json)のTeX等は主にuntracked。本文の公開固定版との対応は未確立。古いPDFの存在は最新原稿完成・editorial対応完了の証拠ではない。第一・第二研究の本文と同一視しない | どの版・研究claimを完成対象にするかを特定するまで、投稿準備度の順位は付けない。新たな独立成果として件数を加算しない |
| PR Track A | 既知PRと強化決定論対照の有限signal資源評価。H4 geometryの全面実測、H6/H8の固定確認・強化対照・後続限定検証 [A01] | v0.4通し原稿と4主図＋S1がある [A03][A04][A11]。H8 A/B/D、H6 DBA、H4 follow-up、new2代表点、H4/H6 theory/compiled比較まで後続公開済み [A05]–[A10]。原稿はこれらを統合済みとはしない | 同一metric・DF/control・候補集合・標本・bias条件を保ってclaimと最新証拠を配置する。単価実測の完了を総費用再会計・科学的採択へ読み替えない |
| PR Track B（M1-S除く） | 有限return局所生成・finite-bit・P5、固定native比較と限界、D1–D3/S4の費用交換。技術ノートv1.0を保存 [B03] | D＋Eと個別closure維持。10/18の限定照合は `A_INSUFFICIENT_EVIDENCE`／`B_DESCRIPTIVE_RESULTS_ONLY` [B01][B02]。これは技術分類・単独論文化保留案で、Track B全体の正式終了ではない | 新しい重要科学レビューを必要とするか、既存技術ノート保全で足りるかをユーザーが判断。追加生成探索・数値救済は開始しない |
| PR M1-S | T1a/T1bの適用域付き理論、固定H4診断、同じ保存信号のStage S局所witness、統合研究記録 [C01] | 研究方向の正式終了・継続・HOLDは未採択。統合後mandatory STOP [C02]。全定理priority、whole-wrapper総費用、多round RPE、論文化は未確立。既存summaryは論文草稿ではない | 終了／ノート化／限定再開をGPT／ユーザーが別途判断。Stage CやTask Bを自動準備しない |
| 保留・終了した探索系列 | J1/Q1、R1-P、集団遷移、G、固定条件付き測定、B-01等の限定成果を保存 [X02][H01] | 各PAUSE/CLOSED/NOT RETAINEDを維持。G・集団遷移・固定条件付き測定の正式判断も固定照合 [H03][H04][H05]。A2はNOT_ADOPTED、現実用化経路は追加投資なし [Q01]。共分散縮約は既知還元 [Q02]、PR研究④の新テーマ選定も正式保留 [Q03] | 新証拠と別方針承認がある場合だけ再検討。今回の論文化候補や自動ToDoに戻さない |

**古い表から更新した事実**：10/17の「H8 Phase C実行待ち」や10/18 14:18の「A/B/D未着手」は時点記録である。後続のA/B/D完了を優先する。ただし、元のSTOP・失敗・未承認表記は書き換えない。[A02][A05][A06]  H4保留も過去snapshotだけで現在一般へ拡大せず、後続の明示指示による完了を区別する [A08]。

全体を単一scaling・成功率へ統合しない。第一・第二研究には共通HF/B0と異なるnative contractがあり、PRは主にcomplex signal・P=0のwrapper費用である。元有限基底Hamiltonianの絶対E0を保持するD2と既存D1制約は維持する。PRのsignal費用やPF-reference shiftを、そのまま絶対E0認証・end-to-end優位へ移送しない。

<!-- fixed-source-index -->

[A01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/621d7d7bed183862db8d9f01b6fdb4406f942309/docs/research/track_a_h4_h8_cross_system_evidence_inventory_20261017.md
[A02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/docs/research/track_a_research_handoff_20261018.md
[A03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/docs/manuscripts/track_a_resource_study_geometry_native_v0_4.md
[A04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/docs/manuscripts/track_a_h4_b0i_v0_4_scientific_review_handoff.md
[A05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/839c403004cf9343730c43adb346024aea41999b/docs/research/track_a_h8_ab_20261018.md
[A06]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/bc9cceac6088d798dc0c6dca92490066258860e5/docs/research/track_a_h8_dba_20261018.md
[A08]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/97d25cc431516d720ce91c7cb4f148e061d8ea34/docs/research/track_a_h4_followup_20261018.md
[A10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/7e454b91185ed7b0f92a3790f800ba5d65d5f156/docs/research/track_a_pr_theory_vs_compiled_completed_20261018.md
[A11]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/artifacts/resource_applicability/track_a_h4_b0i_manuscript_integration/2026-10-14/README.md
[B01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/aafa0f4a42fc0b5780e0716c4bd7c7710bfa4d14/docs/research/track_b_paper_claim_survey_20261018/handoff.md
[B02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/aafa0f4a42fc0b5780e0716c4bd7c7710bfa4d14/docs/research/track_b_paper_claim_survey_20261018/paper_claim_sheet.md
[B03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/aafa0f4a42fc0b5780e0716c4bd7c7710bfa4d14/docs/manuscripts/track_b_return_aggregation_native_resource_note_v1_0.md
[C01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/5f079dbe67bb35eff35613857b169fdf812af4b8/docs/research/m1s_integration_20261017/integrated_research_summary.md
[C02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/5f079dbe67bb35eff35613857b169fdf812af4b8/docs/research/m1s_integration_20261017/codex_restart_handoff.md
[H01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/research_exploration/b01_pause_decision_20261018/research_pause_decision.md
[H03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/addf2cecdc78a271b0139f0459266aa4fef5812d/docs/research_exploration/coherent_subspace_g_closure_20261018/research_closure_decision.md
[H04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b58d5750b2d9d1917d3f34d25dd49bdcaf6b5c66/docs/research_exploration/collective_transition_pause_decision_20261018/research_decision_record.md
[H05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe29fcc73290d35af8c68281330c84b9258e3296/docs/research_exploration/conditional_measurement_closure_20261018/research_closure_decision.md
[M01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/Evaluation%20of%20gate%20numbers%20for%20ground%20state%20energy%20calculations%20using%20higher-order.pdf
[Q01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/f7e103bf3a0ffcee6162bd4b8d244f9a2f4502c5/docs/research/qc_a2_current_route_handoff_20261018/handoff.md
[Q02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/88e4665590bb93c16fdd070e14980d9d3cbff699/docs/research/qc_iv_covariance_method_audit_20261018/method_comparison.md
[Q03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/7eff8a33bef4ee1f29698ab10c6da46988dc8db5/docs/research/qc_iv_selection_hold_20261018/decision_record.md
[S01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/PF_first_study_final_synthesis_20260925.md
[S02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/PF_first_study_final_decision_20260925.json
[S03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/PF_first_study_paper_claim_ledger_20260926.md
[S04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/evidence/paper_evidence_matrix.md
[S06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/figures/paper_figure_manifest.json
[S07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/GO_NO_GO_FOR_PHASE_B_PRODUCTION.json
[T01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[T02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/result_synthesis_20261005/handoff.md
[T03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/result_synthesis_20261005/manuscript_outline_and_abstract.md
[T05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[T06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/evidence_integration_20261006/evidence_map.md
[T07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/artifacts/study2_result_synthesis_20261005/COMPLETE.json
[X01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/algorithm_improvement_overlap_matrix.md
[X02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/active_and_pending_research_map.md
[X03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c6419859029824a4ee8c3dfd3c8126fe585ffbe2/docs/research_exploration/cross_repository_two_branch_delta_20261017/review_readiness_delta_handoff.md
[X04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
