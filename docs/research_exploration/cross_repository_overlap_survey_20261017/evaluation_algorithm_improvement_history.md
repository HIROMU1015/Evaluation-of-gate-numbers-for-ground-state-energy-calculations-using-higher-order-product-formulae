# Evaluation：アルゴリズム改善研究の履歴と到達点

2026-10-17 JST。固定snapshotは `608c6553dcbb63fc45311e004bdd94d20d5840e0`。研究IDの `EV-` は本整理用であり、既存のstage名・正式状態を改名しない。
本文の `[E01]` 等は末尾の固定SOURCEリンクに対応する。全件のorigin/result commit、verified snapshot commit、blob、bytes、SHA-256、読取り範囲は [source_registry.json](source_registry.json)。数値・式・判断は保存資料からの転記であり、再解析・追加証明ではない。

## 調査の範囲

開始時の154公開branch先端とローカルtracking refが一致することを確認した。112登録worktreeのHEAD・branch・status・diff digest、全refs・Git履歴、共有指示・報告を確認した。root checkoutは古い `prevalidation-catalog-validation-20260921` であり、最新研究の正本ではない。
研究の入口は9月成果整理、10月完結性監査、後続の個別正式判断へ順に更新して読む。全branchの全数値・コード・証明の再監査ではない。未公開チャットと実行中jobの全貌は確認できない。

## 性能比較から有限時間の信頼性へ

| 時期・ID | 目的・最初の仮説／中心機構 | 実施済み検証・成果 | 限界・方針が変わった理由 | 現在状態・次の作業 |
| --- | --- | --- | --- | --- |
| 初期〜9月 `EV-PF` | PFの次数、係数、処理付き構成、一step価格と固有値誤差を合わせて低費用化 | 公開preprintではH2–H15の摂動的比較、Morales系8次・10次・新4次等。コードにもYoshida/Morales、固有値目的m6、実回路目的m5の係数catalogがある [E02][E39][E43] | preprintと`current_m3`の係数同一性は既存整理でも未照合。係数関数の存在は研究採択・性能保証ではない。新しい係数探索は本調査では行わない | 保存された性能比較／実装資産。catalog全体に一括CLOSED・新規性認定を付けない |
| 9月 `EV-MECH` | 小さい先頭誤差なら長時間でも安いという仮説を、BCH・摂動・枝診断で点検 | F02/F03/F05：小さいa4と誤差演算子の小ささは異なる。a8の直接項と状態混合、同一枝での高次寄与を限定例で分離 [E03] | 最小gap一つや対角係数だけでは有限時間域を事前判定できない。数値窓はTaylor収束半径の証明でない | 限定機構成果を保持。新しい普遍則へ格上げしない |
| 9月 `EV-CAL` | `a4 t^4+a6 t^6`等の固定校正モデルでPF・時刻を予測 | N2/CO凍結内殻CAS(10e,8o)、平衡・1.5倍伸長4条件で複数固定PF/modelが合格。合格PF中では`current_m3`が低費用。HF全電子伸長等は失敗 [E01][E02] | exact-state/direct点を使うoracle-assisted校正。未知分子への安価な移送法ではない。対象はoperator normではなく固有枝shift | active-spaceの限定的な数値到達点。全電子一般性は未確立 |
| 9/25–26 `EV-S1` | state、proxy、fit、時刻域、marginを分ければ安全で低regretな選択になるか | S0–S4完了。三つの校正誤差軸と費用因子分解を保存。S4二状態診断は安全でも平均regretがbaselineと同じ、改善0% [E04][E05][E06] | `safe != efficient`。S4 beta不一致は9/26監査の引用優先順位を守る。development6条件、continuous rotation proxyでありFT総runtimeではない | **complete_mechanism_study_no_method_benefit**。S4 **complete_no_benefit**、S5へ進まない。論文配置は別判断 |
| 9/27–28 `EV-S2V1` | multiple-windowで許容時刻域を広げる | 固定方式は**complete_no_benefit**。R0/R1事後診断で選択点の原因を分離 [E02][E03] | 同じ保存集合での診断を新holdoutや成功selectorとしない。原因ごとに別の情報が必要と分かった | v1完了。R2等の旧案は実行承認でない |
| 9/28–29 `EV-SPEC` | exact echoと固有位相の差を少数spectral情報で回収 | D1のHCl圧縮診断、D2-Aの有限作用点推定、branchの座標不一致監査、C0の必要width/headroom仕様 [E02][E03] | 点精度が高くても同時刻cheapよりbudgetが改善しない。physical branch一致と旧integer scoringを区別し、原formal STOPは不変 | 既存診断・第二研究への接続資産。一般truth-free branch/width certificateは未完成 |
| 9/30–10/6 `EV-S2C` | cheap予測の過小評価をmarginが吸収する条件、point/width/abstentionの資源価値 | **Direction C**を10/5ユーザー承認。H-chain、HF/HCl、prospective、rank・geometryの既存証拠を統合。G/Rの完了受理 [E10][E11][E12] | H-chain約33%の基準比をspectralの独立利益に帰属しない。rank16/32のpoint改善後もsame-time cheapに対するbudget advantage 0/9。一般分子gamma1.01は選択decision6/13 safe（16 attemptedとの分母差を保持） | 限定的な信頼性・headroom研究として整理済み。H-chain新scienceはいったん終了。論文claim配置はGPT判断 |

保存された関係の例：第一研究では
`f_P−δ_P=(f_P−g_ψ,P)+(g_ψ,P−g_0,P)+(g_0,P−δ_P)`、
`F_total=F_calibration F_time F_PF` を分解する [E02][E05]。
これらはPRの平均signal、shot数、native価格を直接予測する式ではない。

## 既存follow-upと完結判断

| 時期・ID | 問い・入力・機構 | 実施済み検証／結果 | 現在状態と限界 | 次の作業・承認 |
| --- | --- | --- | --- | --- |
| 10/6–7 `EV-H4R` | H4/current_m3固定座標でCISD proxyをresponse8／Ritz8へ置換 | Phase A技術失敗→同scienceのretryでfreeze→Phase B保存scalar採点。accuracy改善は残るがbaseline underestimationが0で、固定Outcomeは**C point_only** [E09] | response-specific資源改善の成功でない。Ritzとのtradeoffも残り、独立holdout・Level3達成ではない | 再定義・追加系・新予算採点は別判断 |
| 10/7–8 `EV-FSR1` | new regenerated sourceのN2/COでstate/local 2×2介入を比較 | historical H01再構築失敗を保存し、新sourceへ明示的に移行。Phase A productionのprediction8区間をfreeze。B0はtruth-only barrier等の技術準備を通過 [E03][E07][E08] | **Phase_B_authorized=false、truth coordinates executed=0**。GO_FOR_FS_R1_PHASE_B_PRODUCTIONは技術readinessでありscience GOではない。資源利益は未採点 | GPT／ユーザー判断待ち。12点ladder・終点採点を今回実行しない |
| 10/16 `EV-U1` | AR／有限時間・branch問題を独立追究するか | 既知摂動・Magnus等との関係、証拠不足・過大一般化を整理 | ユーザー正式：**追加研究STOP、C1限定補論へ保存**。P1-A1〜A4は未実施。AR一般の不能性でない [E13] | 新証拠＋別承認なしに再開しない |
| 10/16 `EV-U3` | H05のexact/HF/CISD response、few-point高次係数取得 | 小系developmentと古典取得費の限定比較を保存 | ユーザー正式：**E4完結・追加研究STOP**。E2未使用系検証・E3一般D6/D8理論は不実施 [E14] | 補助草案の本文統合も別判断 |
| 10/16 `EV-U4` | direct grid最適時刻のサイズ移送 | 小系m5の有限grid傾向、Y8則不成立、H5/Y8枝gate不適格等を保存 | ユーザー正式：**C4・追加研究STOP**、C1相当の補助成果保存。一般サイズ則の反証でない [E15] | H8/H9・連続最適則へ進まない |
| 10/16 `EV-U2/5/6/7` | 監査した残件の所属確認 | U2=FS-R1、U5=U1と重複、U6=第二研究のabsolute identity、U7=第二研究width/branchと資源価値 [E16] | 監査範囲U1–U7から直ちに独立採択する候補を残さない。既存U2/U6/U7を一括STOP・GOに変更しない | 欠損や未実行計画を新研究と数えない |
| 10/16 `EV-T1D` | trap認証とPF位相推定の有限標本・取得費接続 | 静的候補T1から選定判断へ | ユーザー正式：**独立候補撤回**。新保証の不可能性やtrap一般の否定でない [E17] | 追加文献調査・実装・計算は開始しない |

## 新しい生成原理の探索系列

| 時期・ID | 当初の生成機構 | 実施済み確認・到達点 | 限界と現在状態 |
| --- | --- | --- | --- |
| 10/16 `EV-X1/X2` | encoded word代表とparity/frame共有／joint energy測定 | 静的照合。X1は既知compiler等を越える具体規則不足、X2の具体部は既知joint測定等へ対応。候補0件 [E18] | 全encoding・測定のno-goでない。限定調査完了・mandatory STOP |
| 10/17 `EV-P1` | CARを使う複数densityの共同bus閉路 | 狭い仮説P1*を暫定Bとして保持 [E19][E20] | 未採択。単独DF-square幾何gateを新規と数えない |
| 同 `EV-P2` | 配置依存の励起閉路cell | one-sparse／graph分解の既知骨格。追加CAR label規則なし | 分類C。すべてのcycle構成の同値定理でない [E19] |
| 同 `EV-P3` | 等スペクトル方向へdefectを送るprocessor/kernel | 既存H1、processed/corrected PFへの対応が強い | 分類C。停止済みPR系列を再開しない [E19][E41] |
| 同 `EV-P4` | 基準energyから導関数を積分 | Hellmann–Feynman等の既知核。新しい経路・状態取得則なし | 分類C。未知branch/stateを無料にしない [E19] |
| 同 `EV-P5` | Cayley/resolvent型の補助散乱 | resolventを合法primitiveから作る操作が未定義 | 分類D。D1外へ無断移行しない [E19] |
| 同 `EV-P6` | 固有状態の零期待値commutatorを測定control variateに | 既知の制約付きobservable再表現。独立A選択・測定規則なし | 分類C。既報の全制約との同値性は未証明 [E19] |
| 同 `EV-P7/P8` | syndromeへ近似誤差を送るlift／自律energy clock | lift/recovery又は原点・符号を保つ情報転送操作が未定義 | 分類D。不能性証明でない [E19] |
| 10/17 `EV-P1STAR` | 固定12-segmentでbus帰還と二体信号を同時生成 | 保存solver結果は438条件のexact UNSAT。その後の紙上確認は同wordの3次障害を全実振幅へ示す [E21][E22] | **NO_SOLUTION_IN_FIXED_ANSATZ**。別word・全P1*・物理bus一般のno-goにしない。solver証拠と後続紙上結果を区別 |
| 10/17 `EV-J1` | CAR交換対を実制御pathへlift | 20-pulseは既知gate＋echo、G1は3次不成立、G2は既知rectangleのStrang分割 [E23] | ユーザー正式：**PAUSED_PENDING_NEW_MECHANISM** [E24]。一般J1の不能性でない |
| 10/17 `EV-NA/NB` | 群rotor二次作用／対数振幅輸送 | NAの単一kickは一般非可換二次式を処理せず、NBの核はCC/TDCC。chart移送未定義。保持0件 [E25][E26] | 新しい全体正式STOPでない。新規性一般の否定でない |
| 10/17 `EV-COLL` | 二電子補助状態からN電子へpair作用を渡す衝突 | 抽出SWAP案の障害と、joint collisionのCG/Paldus＋phase還元。M=5,N=3の独立紙上確認で還元維持 [E27][E28] | ρ2準備、有限精度、総費用は未確立。targetの有限角channelがそのままunitary発展とは限らない |
| 10/17 `EV-Q1` | 係数とcompact labelからpairing固有基底をlevel再帰で生成 | L4,m2の3＋3、親Fを整理。独立2D回転G、Fと可換なYのG_F、固定Sylvester逆G_Sに限定障害。共通Bは未構成 [E29][E30] | ユーザー正式：**PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE** [E31]。graph特異性と物理算法不能性を区別 |
| 10/17 `EV-STRAT` | 探索履歴・選定方法の再設計 | B′＋A′、成果型・screening・T0を提案 [E32][E33] | 戦略一括採択でない。後続T0の実施を、全戦略の承認へ拡張しない |
| 10/17 `EV-T0/R1` | 既知二点Richardsonの低energy有限step保証 | T0で条件付きR1、次にA+・同じJで既知補題＋有限BCH＋Duhamelへの還元を記録 [E34][E35][E36] | 最新のユーザー正式判断は **R1-P独立候補不保持（NOT_ADOPTED）** [E37][E38]。4軌道2電子検証は不実施 |

## 現時点で再利用できることと残件

PF catalog、固有枝とproxyの区別、state/fit/proxy分解、budget margin/headroom、source/truth barrier、scalar/controlの監査規約は既存資産である。ソースの存在は他repositoryへの互換性・性能・新規性の証明ではない。
固定generation規則を欠いた発想、既知法へ還元された構成、限定ansatzの障害、正式な不保持・保留は別の結果として残す。
FS-R1未採点、第二研究の条件外absolute identity、一般保証・全E0費用の不足は、既存の問いの残件であり本調査の新候補ではない。

SOURCEリンクは自動生成する末尾索引を参照。対応するPRとの関係は [20方向対応表](algorithm_improvement_overlap_matrix.md)、現在の承認境界は [active map](active_and_pending_research_map.md) に分ける。

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
[E35]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/t0_baseline_gap_survey_20261017/t0_research_problem_candidates.md
[E36]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_decision_handoff.md
[E37]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_nonretention_decision_20261017/research_decision_record.md
[E38]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_nonretention_decision_20261017/provenance.json
[E39]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/src/trotterlib/product_formula.py
[E41]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/prior_art_and_novelty_boundaries.md
[E43]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_outcomes/20260929/PF_research_claim_evidence_ledger_20260929.md
