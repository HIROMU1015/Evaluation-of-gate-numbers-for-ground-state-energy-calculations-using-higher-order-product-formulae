# 2リポジトリ研究一覧：ID・目的・証拠・状態の索引

本一覧は [Evaluation履歴](evaluation_algorithm_improvement_history.md) と、再利用する [PR固定整理][P01]／[20方向マップ][P02] の接続用索引である。
研究の対等性を保ち、PRは完成済み詳細資料を再利用するという補足指示に従う。別のPR年表や同じBF/BM等の説明を再作成しない。
PRの原ID（A01/B01/C01/D01等）と本調査のSOURCE ID（E01/P01等）は別。原IDは [元索引][P03] で解決する。

## 評価量と成立しているclaimを先に分ける

| task／資源 | Evaluation | PR | 横断比較の限界 |
| --- | --- | --- | --- |
| 時間発展誤差 | 対象固有枝shift、echo proxy、形式BCH、R1の射影operator norm | 平均複素signal、finite RTE、signed bias、C-sec | 同じ「PF誤差」という名称から保証を移送しない |
| 資源 | continuous QPE PF rotations、保存grid regret、H作用・古典取得費、限定gate/depth proxy | Track A：P=0・shot×full-wrapper compiled RZ。Track B：synthetic加法native T/CX/1Q。M1-S：十分shot整数witness | 一つの倍率・順位へ統合しない。十分shotは必要shotの下界でない |
| state/access | oracle-assisted校正とtruth-free predictionを個別に区別 | 保存ground oracle、finite signal、一般coherent preparation等を個別に区別 | exact state、gap、branch、ρ2、full-H expを無料にしない |
| 絶対E0 | モデル／sector／scalarを持つ元問題との対応が必要 | Track A/M1-S Task Aは全round energy taskではない | 全準備・成功確率・alias等を含む統一end-to-end優位は未確立 |

## Evaluation索引

| ID | 中心機構／改善対象 | 確認された成果の種類 | 状態・既承認の次作業との境界 | 主要SOURCE／対応PRM |
| --- | --- | --- | --- | --- |
| EV-PF | 高次composition・係数catalog／step数・rotation/depth | preprintの限定比較、既存実装 | 性能比較資産。係数catalogの存在を新規性認定・実行承認にしない | [E02][E39][E43]／01,10,13,14 |
| EV-MECH・EV-CAL | BCH/摂動・二項モデル／有限時間予測 | 限定数値・機構説明 | 全電子一般則・oracle-free移送は未確立 | [E01][E03]／03,16,18 |
| EV-S1 | 校正三分解・時刻域・margin／safeとregret | formal完了・S4 fixed negative | S0–S4完了、S5へ不進行 | [E04][E05][E06]／10,14,15 |
| EV-S2V1 | multiple-window／校正使用時刻域 | fixed negative、事後原因診断 | complete_no_benefit。外挿演算子ではない | [E02][E03]／05,18 |
| EV-SPEC | spectral compression、有限作用／proxy補正 | 限定点精度・幅仕様・branch監査 | formal D2-A STOP不変、一般certificateなし | [E02][E03]／06,12,16 |
| EV-S2C | cheap-first margin・spectral対照／budget信頼性 | 承認済みDirection Cと限定数値統合 | G/R完了受理、H-chain追加science停止。中心claim配置待ち | [E10][E11][E12]／04,10,12,15,16 |
| EV-H4R | response/Ritz state介入／校正accuracy | H4固定Outcome C point_only | 資源改善・新method採択ではない | [E09]／06,09,14 |
| EV-FSR1 | new-source state/local 2×2／true safety・resource benefit | Phase A freeze、B0技術preflight | Phase B未承認・truth0、資源成否未採点 | [E07][E08]／06,14,15 |
| EV-U1 | AR/branch理論の配置 | 限定補論草案＋正式STOP | 追加研究STOP、P1-A群未実施 | [E13]／16,18 |
| EV-U3 | few-point/response／高次係数取得費 | 補助比較＋正式E4/STOP | E2/E3へ不進行 | [E14]／03,06 |
| EV-U4 | grid最適時刻／サイズ移送 | 有限小系補助結果＋正式C4/STOP | C2/C3へ不進行 | [E15]／18 |
| EV-U2/5/6/7 | 既存follow-up／既存scopeの所属 | 監査済みの重複・境界整理 | 新独立候補ではない。一括STOP/GOを新設しない | [E16]／06,15,16 |
| EV-T1D | trap認証＋推定／有限標本・取得費 | 静的候補から正式撤回 | 独立候補撤回、原レビュー未取得を保持 | [E17]／20行への同一案件対応は未判定 |
| EV-X1/X2 | encoding word共有／joint energy測定 | 規則不足・既知測定への対応 | 限定探索0件、全般no-goでない | [E18]／08,11,19 |
| EV-P1/P2/P3/P4/P5/P6/P7/P8 | bus／cell／processor／微分積分／resolvent／制約測定／code／clock | 暫定分類B/C/D。P1*以外の保持なし | 分類と正式採択を区別。各仕様は履歴の8行へ | [E19][E20]／01–03,07,11,13,19,20 |
| EV-P1STAR | CAR×線形bus固定word／共同二体生成 | saved solver UNSAT＋限定紙上障害 | 固定ansatzのみ不成立。全P1*を正式CLOSEDにしない | [E21][E22]／01,13、外部bus案件は未判定 |
| EV-J1 | CAR交換対の実制御lift | 既知echo/Strang還元、G1限定障害 | PAUSED_PENDING_NEW_MECHANISM | [E23][E24]／02,13,17 |
| EV-NA/NB | rotor／対数振幅輸送 | NA規則不足、NB核TDCC | 保持0件・mandatory STOP。一般不能性なし | [E25][E26]／02,08 |
| EV-COLL | ρ2係数補助衝突／多電子作用 | CG/Paldus＋phase還元の紙上確認 | 実装・ρ2準備・費用未確立、候補0件の限定結果 | [E27][E28]／08,09,11,17 |
| EV-Q1 | pairing全基底のcoherent再帰生成 | G/G_F/G_S限定障害、B未構成 | PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE | [E29][E30][E31]／06,08,20 |
| EV-STRAT | 過去探索の方法論・B′＋A′ | 提案資料 | 一括正式採択でない。今回も新戦略を選ばない | [E32][E33]／全体管理 |
| EV-T0/R1 | known Richardsonの低energy保証 | 条件付き課題→A+で既知補題還元→正式不保持 | R1-P NOT_ADOPTED（独立候補として）。一般外挿NO_GOでない | [E34]–[E38][E44][E45]／04,05,10,16 |

## PR索引――既存整理への参照と後続差分だけ

| ID／既存群 | 目的・機構と証拠の所在 | 原資料の状態・留保 | Evaluationとの接点 |
| --- | --- | --- | --- |
| PR-A | 既知partial-S2＋DF prefix＋finite RTEの資源地図。[P01] §2.1 | 条件付きbenchmark、各runと科学採択は別 | EV-PF/S1/S2C/T0：対照・価格・taskの境界 |
| PR-B-BF/BM | PF schedule/multirate。[P01] §2.2 BF/BM行 | 限定negative／compact BCH同値、closure採択文言の留保 | EV-PF/P3：係数・wordの部分重複 |
| PR-B-SP/BS・R/RA・G1–G5 | 合成配置、finite-law再配分。[P01] §2.2各行 | 既知手法との差／限定class／CTS対照、個別STOP | EV-P6/T0：sampling価格とobservable再表現を区別 |
| PR-B-RETURN・D1–D3 | return集約、局所非列挙、保証×native価格。[P01] §2.2・§4 | 限定synthetic成果・priority未確立、数値系列の区切りと正式状態を分ける | EV-P2/Q1とは非列挙対象が異なる |
| PR-B-PARENT | parent-child配分。[P01] §2.2 | D+E正式採択、同fixture数値探索の区切り | EVの係数PF最適化へ利益を移さない |
| PR-B-DFCORR/GAUSS/CORR | DF三次補正、Gaussian積、step相関。[P01] §2.2 | generic whole／独立新手法の限定closure等を原文どおり保持 | EV-P3/NA/X1との機構接点 |
| PR-B-FR/M1・次期方向 | 位相/半径保証、部分乱択qDRIFT等。[P01] §2.2 | FR限定理論候補、M1未採択、次期4群未採択、明示休止解除未確認 | EV校正誤差・T0との入力/保証差 |
| PR-M1S | T1a/T1b、保存H4、Stage S。[P01] §2.3 | 方向正式採択なし・mandatory STOP、whole-wrapper/Task B未評価 | EV-H4R/SPEC/COLLと同じcoherence研究に統合しない |
| PR-IV | N1/N2/N3、THRIFT、C1–C4、H-E1/M/SOS/H1–H4。[P02] §2・§4 | 正式状態・技術判定・レビュー推奨を保持 | 20方向対応表の比較先 |
| PR-DA1 | H8通常Phase C [P04][P05] | 完了・STOP、model条件付き、P=0 | 強いbaselineで結論が変わる既存結果 |
| PR-DA2 | H8非相殺cost [P06][P07] | 完了・STOP、経験的診断、P=0 | signed bias会計と混ぜない |
| PR-DI1/2/3 | exact encoding preflight→known shift→現attempt区切り [P08][P09][P10][P11] | ④選定へ復帰、全encodingの否定でない | EV-X1/NA/COLL/Q1との周辺重複と差 |

細かいPR研究ごとの最初の仮説・実施範囲・数値・次の承認は元資料に既に揃っている。上のリンクでそれを継承し、元資料の未取得項目も継承する。

## 再利用できる既存資産

- **定義・保証の切分け**：固有枝とecho、state/fit/proxy、norm/signal/phase/energy、十分shotと総費用。既存statementの条件を外して流用しない。
- **構造化実装**：Evaluation PF catalog・固有枝診断と、PR DF/Gaussian/control/full-wrapper価格。異なる`trotterlib`であり、相互import・互換性試験は未実施。
- **監査**：原点とscalar、fermionic ordering、mode/sector、multiplicity、truth barrier、origin/resultとsnapshotの分離、preflightと実行認可の分離。
- **限定negative**：S4、第二研究v1、固定bus word、G/G_F/G_S、PRの固定fixture/対照の失敗。新しい一般NO_GOとして再掲しない。

再利用可能性を記すことは新しい研究・実装・計算の採択ではない。次の研究戦略判断は別のGPT／ユーザー判断に残す。

<!-- fixed-source-index -->

[E01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/current_research_status.md
[E02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_outcomes/20260929/PF_research_outcomes_20260929.md
[E03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_finite_time_completion_20261016/research_completion_audit.md
[E04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/PF_first_study_final_synthesis_20260925.md
[E05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/PF_first_study_paper_claim_ledger_20260926.md
[E06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/PF_first_study_final_decision_20260925.json
[E07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[E08]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/GO_NO_GO_FOR_PHASE_B_PRODUCTION.json
[E09]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/report.md
[E10]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[E11]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[E12]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/evidence_integration_20261006/README.md
[E13]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[E14]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u3_h05_e4_closure_20261016/decision_record.md
[E15]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/decision_record.md
[E16]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/audited_candidate_scope_closure.md
[E17]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/t1_withdrawal_20261016/decision_record.md
[E18]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/research_decision_handoff.md
[E19]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/principle_ideation_map.md
[E20]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/research_hypothesis_handoff.md
[E21]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md
[E22]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_phase_b_execution_20261017/scientific_execution_report.md
[E23]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_j1_final_limited_search_20261017/research_decision_handoff.md
[E24]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[E25]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/independent_construction_principles_20261017/research_hypothesis_handoff.md
[E26]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/independent_construction_principles_20261017/construction_hypotheses.md
[E27]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/bottleneck_operation_design_20261017/operation_design_task.md
[E28]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/pair_collision_cg_verification_20261017/verification_handoff.md
[E29]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/open_problem_research_design_20261017/research_problem.md
[E30]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/q1_riccati_final_paper_check_20261017/decision_handoff.md
[E31]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
[E32]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/research_strategy_redesign_20261017/research_exploration_retrospective.md
[E33]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/research_strategy_redesign_20261017/research_strategy_handoff.md
[E34]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/t0_baseline_gap_survey_20261017/t0_decision_handoff.md
[E38]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_nonretention_decision_20261017/provenance.json
[E39]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/src/trotterlib/product_formula.py
[E43]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_outcomes/20260929/PF_research_claim_evidence_ledger_20260929.md
[E44]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_baseline_and_scope.md
[E45]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_known_theorem_mapping.md
[P01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/strategy_handoff.md
[P02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
[P03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/fixed_evidence_index.json
[P04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/6dc5bf0de01a0aa23cafe0ff022c0cd21fbf1086/docs/research/track_a_h8_phase_c_run01_results_20261017.md
[P05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/6dc5bf0de01a0aa23cafe0ff022c0cd21fbf1086/artifacts/resource_applicability/track_a_h8_phase_c_run01/2026-10-17/terminal_v1.json
[P06]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/23d46e489af054735d9d328aad0342ecdbddf305/docs/research/track_a_h8_noncancellation_cost_run01_results_20261017.md
[P07]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/23d46e489af054735d9d328aad0342ecdbddf305/artifacts/resource_applicability/track_a_h8_noncancellation_cost_run01/2026-10-17/terminal_v1.json
[P08]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/9ba02e46a808aa2dd7857f413cd18a014db0db38/docs/research/qc_exact_encoding_controlled_preflight_20261017/technical_preflight_report.md
[P09]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/c55fc504c8c6f02eefdf9d7fd27d8dae56a8ed60/docs/research/qc_exact_encoding_controlled_construction_20261017/decision_handoff.md
[P10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/a791b6ac174790605a77915e012039a4334bcfb4/docs/research/qc_exact_encoding_direction_adoption_20261017/decision.json
[P11]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/67576526c4e96ae7235fa645fdf744278d049f8d/docs/research/qc_exact_encoding_direction_adoption_20261017/publication_receipt.json
