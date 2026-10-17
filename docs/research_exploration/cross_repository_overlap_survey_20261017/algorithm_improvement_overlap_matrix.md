# Evaluation × Partially：既存20方向との対応表

基準はPR固定資料 [P02] §4の20行。`PRM01–20` はその**元の行順を指す本整理用ID**であり、新しいPR分類や研究採択ではない。
PRの整理済み詳細を複製せず、Evaluationのどの入力・機構・操作・誤差・費用が対応するかを追加する。
原典の正式状態は [PR差分資料](pr_algorithm_improvement_history.md) と [active map](active_and_pending_research_map.md)。

分類は研究管理上の対応であり、新規性の最終認定ではない。
**実質的重複**＝指定した中核課題・生成操作が同じ、**部分重複**＝一部のみ共通、**相補的**＝異なる課題へ技術を再利用可能、**明確に異なる**＝その比較対で機構等が異なる、**未判定**＝原典不足。
一行に複数の比較対がある場合は分類を分ける。表の近接性から保証・採択・再開承認を移送しない。

| PR既存方向 | Evaluationの対応 | 判定・共通する数式／生成操作 | 差・費用指標・未解決部分／重複回避境界 | 根拠 |
| --- | --- | --- | --- | --- |
| PRM01 Hamiltonian分割変更 | EV-PF、EV-P3、EV-P1STAR | PF係数・word調整とBF/BMは**部分重複**。EV-P3のprocessor/kernel中核とPR H1は**実質的重複（当該中核）** | EV-PFは固有枝shiftとQPE rotation proxy、BF/BMは決定論headの有限PR task。bus couplingを使うP1*は同じ分割の名称だけで統合しない。旧D/H1等の停止を解除しない | [E19][E39][E41]、[P02]行1・13 |
| PRM02 Gaussian frame／interaction picture | EV-NA、EV-P1、EV-P3 | densityのframe、群作用、共役利用は**部分重複**。NAの一般二次rotor生成と通常Gaussian共役は**明確に異なる**問い | `H_rot W=W H`という表現対応だけではexp生成にならない。PR Gaussian積closureをNAの不能性へ移さない。THRIFT現templateと一般interaction pictureを区別 | [E25][E26]、[P02]行2 |
| PRM03 低体数化／counterterm／補正 | EV-P3、EV-MECH、EV-U3 | EV-P3の既知corrector核はPR H1/補正系と**実質的重複（核）**。BCH係数・response診断は**部分重複** | `D4`の対角・非対角やa8を診断することと、実装可能な補正を挿入することは別。EV小系取得費とPR synthetic加法Tを同じ利益にしない | [E03][E14][E19][E41]、[P02]行3 |
| PRM04 SOS/PSD有限step保証 | EV-T0/R1、EV-S2C | 低energy射影、PSD、有限剰余という保証課題は**部分重複**。経験的budget safetyとrigorous norm保証は**明確に異なる** | R1-PはA+で既知補題へ還元・正式不保持。SOS-PF A2は別の未採択課題であり同時に否定・採択しない。`safe`をcertificateへ格上げしない | [E10][E35][E37][E45]、[P02]行4 |
| PRM05 PF Richardson外挿 | EV-T0/R1、EV-S2V1 | `X_r=(4/3)U_2r−(1/3)U_r` の二点相殺は旧C2/EXT2と**部分重複**。EV-S2V1の複数fit窓はRichardson作用と**明確に異なる** | R1-Pは低energy入力へのoperator norm、C2は固有枝・gap・多幅controlの会計。R1不保持は外挿一般の否定でない。fit外挿とunitaryの線形結合を混同しない | [E02][E35][E36][E37]、[P02]行5 |
| PRM06 self-energy／downfolding | EV-SPEC、EV-U3、EV-Q1 | Schur／response／部分空間の数学は**部分重複** | EVは既存PFのspectral情報校正。PR C3/N3は元Hの縮約・実現費。Q1のgraph/Riccatiは固有基底生成で、単なる安価なground oracleを与えない。N3 closureを全部分空間法へ広げない | [E03][E14][E29][E30]、[P02]行6 |
| PRM07 cost-aware randomization | EV-P6、EV-T0、EV-PF | 費用を重みに戻す問題は**部分重複**。EVの決定論係数選択とParent allocationのlaw生成は**明確に異なる** | PR `q ∝ abs(a)/sqrt(g)`、係数配分・second momentと、EVのPF固有枝誤差は異なる入力/出力。EV-P6はobservable制約でありRTE samplerでない | [E19][E34][E39]、[P02]行7 |
| PRM08 exact encoding／sector | EV-X1、EV-NA、EV-COLL、EV-Q1 | encoding・群表現・ラベル生成・制御位相は**部分重複** | PRの後続DF number shift現attemptは既知法還元・区切り [P09][P10]。EV-COLLの仮想species total spin、Q1のpair占有labelとは同一操作でない。全encoder費用や一般interacting Hの安いexpは双方未確立 | [E18][E25][E28][E29]、[P02]行8、[P08][P09][P10] |
| PRM09 coherent ±label共有 | EV-COLL、EV-H4R、EV-SPEC | coherence/phaseの保存という接点は**相補的**。二電子CG衝突とM1-S joint lawは**明確に異なる** | M1-Sは±branchの同位置Pauli label共有、EV-COLLはCAR交換演算子のjoint unitary。どちらも「coherent」だけで同法としない。visibility改善を対象固有位相の保証に移さない | [E09][E28]、[P01]§2.3、[P02]行9 |
| PRM10 強い決定論baseline | EV-PF、EV-S1、EV-S2C、EV-T0/R1 | 同情報・強い対照の必要性は**部分重複**、異なるtaskの評価基盤として**相補的** | EVは保存PF集合・cheap対照・continuous budget、PRはB0+I／強化184候補・shot×compiled RZ。H8 Phase C後の勝敗をEVに移さない。R1には同lowenergy通常4次PFを与える | [E05][E10][E34][E44]、[P02]行10、[P04][P06] |
| PRM11 copies/RDM/測定による絶対energy | EV-X2、EV-P4/P6/P8、EV-COLL | joint測定・零期待値制約の検討は**部分重複**。EV-X2は既存PR H2/H4の近接領域を既知測定と照合済み | copies、coherent準備＋逆、ρ2準備を区別。衝突first-order情報やclockの名だけで絶対offsetが読めるとしない。元H期待値とground保証も異なる | [E18][E19][E27][E28]、[P02]行11 |
| PRM12 representation／低rank selector | EV-PF、EV-S2C、EV-SPEC | rank・代理量・情報精度と費用価値の検討は**部分重複** | PR N1の表現選択、EV M1のspectral rank、PF種類の選択は別パラメータ。rank8/16/32の値をDF rankと混同しない。N1のsynthetic0%とEV budget0/9は別結果 | [E10][E11][E39]、[P02]行12 |
| PRM13 macrocycle／異符号PF合成 | EV-PF、EV-P1STAR、EV-J1 | word合成と低次相殺は**部分重複**。既知compositionを新名で出す点の回避に同じ監査が使える | PR旧C1はPauli macrocycleの固定catalog、EVは電子×bus force。P1*3次障害とC1限定5%未達を同じno-goにしない | [E21][E22][E23]、[P02]行13 |
| PRM14 native価格・回路会計 | EV-PF、EV-S1、EV-H4R、EV-FSR1 | 同じ資源語の辞書・固定費/反復費分離は**相補的** | EV continuous PF rotations、実回路探索catalog、古典H作用と、PR compiled RZ／synthetic加法T／理論命令数は別量。未知なコード互換性を前提に両`trotterlib`を混用しない | [E05][E07][E39][E40]、[P02]行14 |
| PRM15 全round絶対E0総費用 | EV-S1、EV-S2C、EV-T0 | 有限情報から絶対E0資源へ接続する問題は**部分重複** | EVのQPE費用proxyにも全準備・離散query・成功保証はない。PR Task AのεはHaでない。どちらもend-to-end実現を達成済みとしない | [E05][E10][E34]、[P02]行15 |
| PRM16 finite-step bias／allowance | EV-CAL、EV-S2C、EV-T0/R1、EV-U1 | 誤差の種類と残余予算管理は**部分重複** | EVは符号付き固有枝shift/経験的width、R1は射影norm、PRは複素signalのsigned/非相殺診断やC-sec。H8経験的非相殺をrigorous boundにしない。R1還元を一般PF certificateへ広げない | [E03][E10][E35][E45]、[P02]行16、[P06] |
| PRM17 scalar／energy原点 | EV-COLL、EV-J1、EV-Q1、EV-T0/R1 | controlled scalar台帳は**相補的**。保持自体は既知要件 | PR B0+Iの既知identity処理、EV-COLLのphase、Q1のself-pairは値・作用が異なる。scalar保持を独立新原理に数えない。符号化shiftが元の絶対E0を捨てない条件を保つ | [E28][E29][E44]、[P02]行17、[P09] |
| PRM18 長時間／多step | EV-MECH、EV-U1、EV-U4、EV-S1 | 短時間則の運用域と高次残余は**部分重複** | EVのPF microstep最適時刻とPRの全interrogation Tは同じ変数でない。PR T panel、M1-S極限、EV grid移送の結論を同一scalingにしない | [E03][E05][E13][E15]、[P02]行18 |
| PRM19 basis共有・境界相殺 | EV-X1、EV-P2、EV-PF | parity/frame共有、既知compilerと生成規則の区別は**部分重複** | EV-X1はencoded word代表、PR M2/Gaussian/D2はbasis/sampler/実装境界。RZ内訳は削減可能量ではない。具体的共通実装の包含は**未判定**で、名称だけで同値としない | [E18][E19]、[P02]行19 |
| PRM20 return集約・非列挙normalizer | EV-P2、EV-T0、EV-Q1 | 「非列挙」の情報取得会計は**相補的**。生成対象は**明確に異なる** | PRは有限Taylorのreturn class/law、EV-P2は配置cell、Q1は固有基底の再帰label。compact labelという語だけで同構成としない。分子access・古典online費用の欠落は既存課題 | [E19][E29][E34]、[P02]行20 |

## 20方向に一対一には押し込めないEvaluation課題

| Evaluation課題 | PRとの関係 | 判断の限界 |
| --- | --- | --- |
| EV-J1／P1STARの電子×外部bus文法 | PRのGaussian/交換子合成との部分重複はあるが、同じprimitive・CAR共同閉路を研究したPR案件は固定20行からは特定できない | **未判定（同一研究案件の有無）**。未発見は新規性の根拠でない。J1 PAUSEは維持 |
| EV-Q1の非一様pairing・係数からのlevel挿入 | PR encoding/CG等との周辺重複はあるが、係数依存のinhomogeneous全固有基底生成は同じ問題でない | **明確に異なる（仕様比較）**。世界的未解決性・新規性の認定ではない。Q1 PAUSE維持 |
| EV-T1Dのtrap認証費用 | PR native/FT価格との接点はあるが、有限標本energy保証へ認証を結ぶ具体課題は既存20行では確認不足 | **未判定**。正式撤回を維持し、欠落から新候補を作らない |

## 重複判定と数学的還元は別

PRの未追跡ローカルA2再設計レビュー（registry **L05**）は、PRM04/16に関係する後続提案である。
有限step相対形式保証・energy出力区間・step選択という対象をヘッダと結論から確認したが、式の正しさ、R1-Pや既知定理への包含・還元は**未判定**。
この記録の存在を重複防止に用い、新候補や承認済み科学計算として保持し直さない。取得状態はhandoff §4・§6。

この表は原資料の入出力・改善部位・費用に基づく研究管理用の照合である。数学的還元を新たに証明していない。
既存資料が還元を記録する例は、EV-J1のecho/Strang、EV-NBのTDCC、EV-COLLのCG/Paldus、A+のR1-P、PRのBM/Gaussian/現encoding shift等である。
共通のknown componentがあっても結合全体の独立priorityまで認定されていないG/D系列等には、その留保を残す [P01]。
今後のGPTレビューでは、「この20方向に同じ言葉がない」ことを新規性認定に使わず、また、周辺機構が共通するだけで別の構成規則を一般的に排除しない。

<!-- fixed-source-index -->

[E02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_outcomes/20260929/PF_research_outcomes_20260929.md
[E03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_finite_time_completion_20261016/research_completion_audit.md
[E05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/PF_first_study_paper_claim_ledger_20260926.md
[E07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[E09]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/report.md
[E10]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[E11]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[E13]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[E14]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u3_h05_e4_closure_20261016/decision_record.md
[E15]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/decision_record.md
[E18]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/research_decision_handoff.md
[E19]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/principle_ideation_map.md
[E21]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md
[E22]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_phase_b_execution_20261017/scientific_execution_report.md
[E23]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/p1star_j1_final_limited_search_20261017/research_decision_handoff.md
[E25]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/independent_construction_principles_20261017/research_hypothesis_handoff.md
[E26]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/independent_construction_principles_20261017/construction_hypotheses.md
[E27]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/bottleneck_operation_design_20261017/operation_design_task.md
[E28]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/pair_collision_cg_verification_20261017/verification_handoff.md
[E29]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/open_problem_research_design_20261017/research_problem.md
[E30]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/q1_riccati_final_paper_check_20261017/decision_handoff.md
[E34]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/t0_baseline_gap_survey_20261017/t0_decision_handoff.md
[E35]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/t0_baseline_gap_survey_20261017/t0_research_problem_candidates.md
[E36]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_decision_handoff.md
[E37]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_nonretention_decision_20261017/research_decision_record.md
[E39]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/src/trotterlib/product_formula.py
[E40]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/src/trotterlib/cost_validation.py
[E41]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/prior_art_and_novelty_boundaries.md
[E44]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_baseline_and_scope.md
[E45]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_known_theorem_mapping.md
[P01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/strategy_handoff.md
[P02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
[P04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/6dc5bf0de01a0aa23cafe0ff022c0cd21fbf1086/docs/research/track_a_h8_phase_c_run01_results_20261017.md
[P06]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/23d46e489af054735d9d328aad0342ecdbddf305/docs/research/track_a_h8_noncancellation_cost_run01_results_20261017.md
[P08]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/9ba02e46a808aa2dd7857f413cd18a014db0db38/docs/research/qc_exact_encoding_controlled_preflight_20261017/technical_preflight_report.md
[P09]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/c55fc504c8c6f02eefdf9d7fd27d8dae56a8ed60/docs/research/qc_exact_encoding_controlled_construction_20261017/decision_handoff.md
[P10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/a791b6ac174790605a77915e012039a4334bcfb4/docs/research/qc_exact_encoding_direction_adoption_20261017/decision.json
