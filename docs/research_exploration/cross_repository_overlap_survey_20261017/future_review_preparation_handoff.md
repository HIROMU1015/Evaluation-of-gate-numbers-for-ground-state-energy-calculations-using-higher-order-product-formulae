# 2リポジトリ横断整理：GPT研究戦略レビュー前のhandoff

2026-10-17 JST。**今回の成果は、Evaluationの研究履歴とPR既存20方向の対応、およびPR固定整理後の差分である。新しい研究方向・ランキング・科学レビュー・採択は行っていない。**

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。
branch：`qc-cross-repository-overlap-survey-20261017`。親はR1-P正式不保持を含む `608c6553dcbb63fc45311e004bdd94d20d5840e0`。
PRはread-only。既存3資料の固定commitは `d09ba606a9fceef806a9313e3f7c43cd21d19e3f`。
今回の公開commit自身のSHAは循環参照を避け、公開・照合後の最終chatとGit履歴で示す。

## 読む順序

1. 本書：何が既存成果で、何が重複・未確認か。
2. [active_and_pending_research_map.md](active_and_pending_research_map.md)：他chatとの競合・正式状態・承認境界。
3. [algorithm_improvement_overlap_matrix.md](algorithm_improvement_overlap_matrix.md)：既存20方向への具体的な入力・操作・保証・費用の対応。
4. [evaluation_algorithm_improvement_history.md](evaluation_algorithm_improvement_history.md)：Evaluationの時系列・成果・未解決。
5. [pr_algorithm_improvement_history.md](pr_algorithm_improvement_history.md)：PR既存整理への入口と、H8／encodingの追加差分のみ。
6. [cross_repository_research_inventory.md](cross_repository_research_inventory.md) → [source_registry.json](source_registry.json) → [static_audit.json](static_audit.json)／[provenance.json](provenance.json)。

## 1. 何を改善してきたか

Evaluationは、PF次数・係数の性能比較から、有限時間の固有枝誤差、oracle-assisted校正、state/proxy/fit分解、時刻域・予算安全性・資源regretの研究へ進んだ。
その後、既存方法のfollow-up、有限時間機構の完結監査と候補配置、新しい生成原理、最後に既知作用への新保証課題T0/R1を検討した。

PRは既存資料 [P01][P02][P03] を再利用する。Track Aの既知PRの評価、Track Bの有限law/return/価格設計、M1-Sの±共有と限定理論、PRに限らない新算法探索を区別する。
今回の主な追加作業は、Evaluationがこれら既存研究のどの部位と重なるかの照合である。PR全研究の詳細年表は再生成していない。

## 2. どこまで成果として支えられているか

| 範囲 | 既存証拠が支える到達点 | 支えていない主張 |
| --- | --- | --- |
| Evaluation第一研究 | state/proxy/fitの分離、safe≠efficient、時刻域・marginの費用伝播。S4固定診断のno-benefit [E04][E05] | 全電子への一般適用条件、普遍的低regret selector、FT総費用改善 |
| Evaluation第二研究 | Direction Cの限定信頼性・headroom、point/width/abstentionの違い。G/R完了受理 [E10][E11][E12] | spectral必須、全rank/全系の不可能性、経験的widthの厳密certificate |
| Evaluation新構成系列 | fixed wordの限定障害、J1の既知生成への対応、CG/Paldus還元の紙上確認、Q1の限定文法の不足 [E21][E23][E28][E30] | 新しい独立生成法の確立、各分野一般のNO_GO、実装・資源優位 |
| PR各系列 | 元固定整理が記す限定理論・数値・実装成果をそのscopeで保持 [P01] | 全系列を一つの独立新アルゴリズム成功／失敗とまとめること |
| PR H8後続 | 強化対照・bias規約により局所比較の結論が変わる、model条件付きP=0の保存結果 [P04][P06] | 母平均優位、全格子実測最良、厳密bias、全round E0資源優位 |

この表は既存claimの記録であり、今回の独立した数学的認証・科学レビューではない。新しい数値を作らず、保存値の再解析・再ランキングもしていない。

## 3. 重複と還元の重要な区別

- **同じ中核を繰り返しやすいところ**：EV-P3とPR H1のprocessed/corrected PF、Hamiltonian再分割・counterterm、Gaussian/frame共有、測定制約、samplingの費用配分。20方向対応表で入力・生成操作まで照合する。
- **部分重複だが同一課題でないところ**：R1-Pの低energy射影normとPR C2の固有枝外挿、Schur/responseによる校正と元Hのdownfolding、pairing全基底再帰とencoding/CG。
- **共通の用語から統合しないところ**：二電子衝突と±乱択label共有、fit窓の外挿とRichardson作用、microstep最適時刻と全interrogation T、spectral rankとDF rank。
- **既知還元の射程**：J1のecho/Strang、NBのTDCC、collisionのCG/Paldus、A+のR1-P、PR現encodingのnumber shiftはいずれも固定資料に基づく限定結果。G/D系列全体のpriority等の未確立を、既知性確定へ変換しない。

研究管理上の重複は、既知法への数学的還元の証明とは別である。今回新しい同値定理や新規性の最終判定は作っていない。

## 4. 現在の競合・判断待ち

1. **FS-R1**はprediction freezeと技術準備までで、truth未採点・Phase B未承認。新しいstate/local校正研究を提案する前に既存follow-upとの関係を確認する [E07][E08]。
2. **J1／Q1／R1-P**はそれぞれ正式PAUSE／PAUSE／独立候補不保持。旧handoffの当時の条件付き保持を最新状態にしない [E24][E31][E37]。
3. **PR H8 Phase Cと非相殺cost**は、旧整理の未収録・未承認段階を越えて完了公開している。以後の科学採択レビューの有無は未確認。追加再会計・compileを自動ToDoにしない [P04]–[P07]。
4. **PR現exact-encoding試行**は既知shiftへ還元され、正式に区切り、④選定段階へ戻った。全encodingが閉じたのではない [P09][P10]。
5. **PR-B／M1-S**の既存成果・休止・未採択・mandatory STOPは別の状態。M1-Sの限定理論受理を新実行のGOにしない [P01][P02]。

さらに、PR rootの未追跡ローカル文書
`qc_track_iv_research_question_redesign_review_20261017.md` を取得した（registry **L05**）。
ヘッダ・結論・状態部分では、重要科学レビュー完了を自己申告し、**既存SOS-PF A2の有限step相対形式保証→energy出力区間→step選択を、条件付き提案・未採択・実行未承認**としている。
今回、その紙上導出や正しさ・新規性・優位を評価していない。元のレビュー開始チャットや正式採択記録を取得したわけでもない。
このローカル記録を「既に正式採択された次の研究」へ格上げせず、同時に「A2の検討は誰も行っていない」と再提案しない。
R1-Pとの関係は、保証という主題の近接性まで記録する。**同一定理への還元・包含の成否は未判定**であり、本調査で追加検算しない。
原本は本成果物へ複製・commitせず、取得時のbytes・hash・mtime・公開到達性の限界だけを記録した。

## 5. 何を繰り返さないか

既存定義のままの係数・fragment・word・law・名前の変更を、未検討領域として扱わない。
固定ansatzの否定を分野一般の不能性へ広げない。構成未発見を実装不能と呼ばない。
情報取得が未定義の変換・root・branch・振幅・全H発展を無料oracleとして加えない。
新しい厳密保証を論じる場合も、既存A2／M1-S／R1-P／第一・第二研究のどの対象量・入力・baselineと異なるかを先に区別する。

これは研究戦略・選定gateを新しく採択する指示ではない。既存資料の重複と承認境界を示したものである。

## 6. レビュー前の重要な不足

| 未確認・取得範囲 | 影響 | 今回の扱い |
| --- | --- | --- |
| PRローカルA2レビューL05の公開固定版・承認原本 | 次の保証研究との競合、statement比較 | 文書冒頭と状態だけ確認。全文科学検算・新しい公開は別指示。自己申告を正式採択にしない |
| PR [P01] §8の旧レビュー原本・H7承認文言・出版版差分等 | 過去のレビュー帰属、承認履歴、priority | 新たに回収していない。旧索引を参照し、未取得を解消済みにしない |
| Evaluation U1/U3/U4/T1の旧Claude原本等 | 正式決定の背景レビュー | 正式決定はユーザー判断として保持。原文の内容を復元しない |
| 未保存chat・遠隔job・未commit sourceの現在進行 | 同時作業との競合 | Git/共有資料の観測以上を断定しない。今後の実行前に必要ならユーザーが範囲を特定 |
| 2 repository間の共通情報access・全E0費用・資源尺度 | 優位の横断比較 | 新数値やランキングを作らず、不足をそのまま残す |

## 7. 公開・保全とMandatory STOP

新規6 Markdown、SOURCE registry、観測記録、静的監査、provenanceのみを追加する。
PR固定3資料・過去SOURCEは複製しない。origin/resultとverified snapshotを別fieldにし、provenanceはmanifestから自己除外する。
通常push後にremote SHA、独立空bare fetch、Git blob・bytes・SHA-256・commit固定rawを照合する。
開始時のEvaluation112／PR184 worktreeのGit状態を比較する。並行更新があれば戻さず記録し、未追跡/ignored内容全体の保全証明とはしない。

**Mandatory STOP：資料公開・照合後に停止する。**

次の担当は**ユーザー**：本資料とPR固定3資料・後続差分をGPTへ渡し、研究戦略レビューを開始するか、その範囲と必要な原本を判断する（今回の作業とは別）。
**GPT**：別途開始指示を受けた場合に研究戦略・claim・未解決問題の価値を判断する。
**Codex**：追加探索、科学レビュー、新規計算、既存研究再開、未追跡レビューの公開を自動開始しない。現在承認済みの後続研究作業はない。

<!-- fixed-source-index -->

[E04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/PF_first_study_final_synthesis_20260925.md
[E05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/PF_first_study_paper_claim_ledger_20260926.md
[E07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[E08]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/GO_NO_GO_FOR_PHASE_B_PRODUCTION.json
[E10]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[E11]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[E12]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/evidence_integration_20261006/README.md
[E21]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md
[E23]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_j1_final_limited_search_20261017/research_decision_handoff.md
[E24]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[E28]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/pair_collision_cg_verification_20261017/verification_handoff.md
[E30]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/q1_riccati_final_paper_check_20261017/decision_handoff.md
[E31]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
[E37]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_nonretention_decision_20261017/research_decision_record.md
[P01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/strategy_handoff.md
[P02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
[P03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/fixed_evidence_index.json
[P04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/6dc5bf0de01a0aa23cafe0ff022c0cd21fbf1086/docs/research/track_a_h8_phase_c_run01_results_20261017.md
[P06]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/23d46e489af054735d9d328aad0342ecdbddf305/docs/research/track_a_h8_noncancellation_cost_run01_results_20261017.md
[P07]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/23d46e489af054735d9d328aad0342ecdbddf305/artifacts/resource_applicability/track_a_h8_noncancellation_cost_run01/2026-10-17/terminal_v1.json
[P09]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/c55fc504c8c6f02eefdf9d7fd27d8dae56a8ed60/docs/research/qc_exact_encoding_controlled_construction_20261017/decision_handoff.md
[P10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/a791b6ac174790605a77915e012039a4334bcfb4/docs/research/qc_exact_encoding_direction_adoption_20261017/decision.json
