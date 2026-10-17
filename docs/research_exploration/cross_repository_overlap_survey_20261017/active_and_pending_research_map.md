# 進行中・判断待ち・保留の対応表

観測は2026-10-17の今回取得したlocal Git/共有文書/remote refsに限定する。[repository_observation.json](repository_observation.json) に取得時刻、開始時のbranch・worktree、digestを保存する。
オンラインchatや遠隔jobの全件照会はしていない。「最新公開記録に実行中の証拠なし」を「現在どこでも停止中」と読み替えない。

## 最優先で取り違えを避ける状態

| 対象 | 研究結果・正式状態 | 技術STOP・実行承認 | 次の担当／未承認部分 |
| --- | --- | --- | --- |
| EV-FSR1 | Phase A prediction freeze済み。資源利益は未採点 [E07] | B0 preflight GO、**Phase_B_authorized=false、truth0** [E08] | GPT／ユーザーが固定predictionを判断。Phase Bの別承認は未確認。Codexは実行しない |
| EV-S1 | S0–S4完了、S4 no-benefit、S5へ進まない [E04][E06] | 過去のrun承認を再実行権限にしない | 論文配置・本文統合は別判断。未採点FS-R1と一括完了にしない |
| EV-S2C | Direction C承認、G/R完了受理、H-chain追加scienceはいったん終了 [E10][E11] | rank64、H9/H10、追加geometry等へ進まない | GPTの論文claim配置判断。absolute identity残件は自動ToDoでない |
| EV-U1/U3/U4・T1D | 各正式STOP／完結／撤回 [E13][E14][E15][E17] | 元の未実施案を次の既承認jobとしない | 新証拠＋別承認を要する。旧Claude原本の欠落を解消済みにしない |
| EV-J1 | **PAUSED_PENDING_NEW_MECHANISM** [E24] | 旧pulse案・solverの追加実行承認なし | 再開条件に合う具体規則が提示されてもGPT／ユーザー判断が必要 |
| EV-Q1 | **PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE** [E31] | Riccatiの一般解やBは未構成。新ansatz探索承認なし | 係数からの独立label混合規則が再検討条件。自動探索しない |
| EV-R1-P | **NOT_ADOPTED：独立研究候補として不保持** [E37] | 4軌道2電子の追加検証は不実施 | 実質的に異なる新証拠・問題の提案がある場合だけ別判断。一般外挿NO_GOではない |
| PR-A H8通常Phase C | [P04]で一回完了、保存1900行・全回収・gate PASS | 実行grant消費済み・次stage false [P05]。旧「結果未収録」を最新実行待ちにしない | GPT／ユーザーの結果解釈・claim判断。新compileや再会計承認ではない |
| PR-A H8非相殺cost | [P06]で一回完了。通常signedとは別会計 | grant消費済み・次stage false [P07] | GPT／ユーザー判断待ち。厳密biasや全候補実測の不足を自動補完しない |
| PR-A V1/V2・開殻等 | 旧固定整理の状態を維持 [P01][P02] | V2現設計はユーザーCLOSED、V1追加実測・H5/H7次段階等は旧記録で未承認 | 後続の承認・新結果を今回確認しなかった。ユーザー以外の推奨を認可にしない |
| PR-B | D+E正式、個別closureを保持、次期4群未採択 [P01][P02] | 休止の明示解除記録は今回も未取得 | 新RQ再開／note化／休止の選択はユーザー/GPT。現行進行中の科学jobは未確認 |
| PR-M1S | 限定理論契約・過去各runは採択済み、**研究方向の正式採択なし** | 統合後mandatory STOP。R0–R7は提案で一括承認でない [P01]§2.3 | 終了／note／限定再開等をGPT／ユーザーが選ぶ。新しい実行承認は未確認 |
| PR-IV exact encoding現attempt | ユーザー正式に現attemptを区切り、**RESEARCH_QUESTION_SELECTION**へ [P10] | 実装・数値・別構成の自動承認なし。既存停止解除false | 次の具体課題は未採択。選定作業の新指示が必要 |
| PR-IV既存系列 | N1 STOP、N2 HOLD、N3現系列CLOSED、THRIFT現template CLOSED、H1–H4 PAUSED、A2 NOT_ADOPTED等 [P02][P10] | 当該K0.5/K1等未認可・未実施を維持 | 選定段階への復帰はこれらの停止解除ではない |
| 旧R5 | Evaluation固定handoffに「PAUSE維持・現在のPAUSE原本は未回収」と記録 [E42] | 原本を新たに取得していない | **二次記録の限界付きで維持**。他のR1/R5やM1-S再開番号と同定しない |

## ローカル観測と公開証拠

PR root未追跡のA2再設計レビュー（registry **L05**）では、有限step相対形式保証からenergy区間・step選択へ接続する提案がある。
文書の自己申告は「レビュー完了・提案・未採択・実行未承認」。このレビューの数式・新規性・開始承認を本作業が独立確認したのではない。
公開固定版は未確認で、これを次の既承認研究としない。一方、既存A2を全く未検討とする旧時点記述だけで他chatの検討を見落とさない。
R1-Pとの定理包含や差分を評価する作業は今回行わない。

Evaluation共有`comment.md`は20:20完了報告に対応する旧戦略指示で、後続T0/R1の最新正式判断は反映していない。
共有`review.md`にも過去の「Q1 push未実施」が残るが、公開branchの後続記録を優先し、履歴を上書きしない。
PR共有報告は19:15の4系列整理完了で、以後のH8・encoding差分は固定公開commitから確認した。これら共有文書を現在の全chatの活動台帳とは扱わない。

開始時のEvaluation112 worktreeのうち109にporcelain出力があり、その多くは共有指示symlink等の未追跡表示である。
tracked diffを持つのはroot、`pf-study2-evidence-integration-20261006`、detached `/tmp/pf-valid-review-3f47b59` の3箇所。
PR184 worktree中9にporcelain出力とtracked変更を観測した。root、PR-2、representation review intake、過去Track A準備・H4実行worktreeが含まれる。
**このdirty状態は現在実行中・未完了scienceの証拠ではない。** 内容・活動者・未反映chatを推測せず、全状態を保全する。

最新の公開tipだけを読む方法と異なり、branch群と古いcheckoutを分けて確認した。ただし、別chatで未保存・未commitの承認がある可能性までは排除できない。
その確認が将来の実行に必要なら、実行前にユーザーが該当承認を特定する。今回その確認不足を理由に既存研究を停止・再開したり、追加契約を作ったりしない。

## 次の担当と停止

今回承認されているのは横断整理と公開・照合だけである。次の研究戦略レビュー開始は別判断。
**ユーザー**が本handoffをGPTへ渡し、レビュー開始・範囲・必要な未取得原本を判断する。
**Codex**は本資料公開・照合後に停止し、追加研究、原本回収、科学レビュー、科学計算を自動実施しない。

<!-- fixed-source-index -->

[E04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/PF_first_study_final_synthesis_20260925.md
[E06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/PF_first_study_final_decision_20260925.json
[E07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[E08]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/GO_NO_GO_FOR_PHASE_B_PRODUCTION.json
[E10]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[E11]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[E13]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[E14]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u3_h05_e4_closure_20261016/decision_record.md
[E15]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/decision_record.md
[E17]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/t1_withdrawal_20261016/decision_record.md
[E24]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[E31]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
[E37]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_nonretention_decision_20261017/research_decision_record.md
[E42]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/quantum_chemistry_independent_topics_20261016/candidate_handoff.md
[P01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/strategy_handoff.md
[P02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
[P04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/6dc5bf0de01a0aa23cafe0ff022c0cd21fbf1086/docs/research/track_a_h8_phase_c_run01_results_20261017.md
[P05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/6dc5bf0de01a0aa23cafe0ff022c0cd21fbf1086/artifacts/resource_applicability/track_a_h8_phase_c_run01/2026-10-17/terminal_v1.json
[P06]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/23d46e489af054735d9d328aad0342ecdbddf305/docs/research/track_a_h8_noncancellation_cost_run01_results_20261017.md
[P07]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/23d46e489af054735d9d328aad0342ecdbddf305/artifacts/resource_applicability/track_a_h8_noncancellation_cost_run01/2026-10-17/terminal_v1.json
[P10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/a791b6ac174790605a77915e012039a4334bcfb4/docs/research/qc_exact_encoding_direction_adoption_20261017/decision.json
