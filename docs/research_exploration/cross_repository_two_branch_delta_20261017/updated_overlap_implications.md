# 横断重複防止マップへの差分

2026-10-17 JST。[既存横断マップ][O02]（Evaluation `609a63231ee0786cf8da31f6b33358acfd6f2548`）と[PR既存20方向][P02]（`d09ba606a9fceef806a9313e3f7c43cd21d19e3f`）を正本として再利用する。以下のPRM番号は旧横断整理の行番号であり、別の研究分類や新候補を作らない。科学的同値・包含・独立性の新しい判定はしない。

## 1. 重点6方向に追加する内容

| 旧マップ方向 | 今回の補足・解消した不足 | 維持する未確認・重複防止の境界 | 固定根拠 |
| --- | --- | --- | --- |
| PRM04 SOS/PSD finite-step certificate | A2関連でRF0/RF1/EW/QPEの限定技術監査が公開。旧L05の原本も公開固定版あり | 「A2は未着手/原本未公開」を最新状態として繰り返さない。一方A2はNOT_ADOPTED。独立新定理/有用certificate取得とはしない。N3 occupation証拠やR1-Pへ自動転用しない | [A01][A02][A06][P02] |
| PRM16 finite-step bias・経験的allowance | 全vector相対log保証とexact-ground入力のwindowという対象が明示された | 第一/第二研究の保存truthに対するsafe、signed枝shift、width/abstention、H8非相殺診断とは別。経験的数値をrigorous保証へ格上げしない | [A02][E05][E06][O02] |
| PRM14 native価格・回路会計 | H8登録3構成cosine/sine計6軸のRZ/CX/depth、固定モデル誤差PASSが取得済み | 全候補価格・全ハミルトニアン・別compiler・T費用へ一般化しない。Evaluationのcontinuous rotation proxy/古典H作用とcompiled RZは同一量でない | [B01][B03][O02] |
| PRM10 強い決定論baseline | H8 B0/B0+Iの選択された強対照に直接compile証拠が追加 | 新最良候補や新削減率を認定しない。R1-Pには同low-energy通常4次PF、A2には同task/同情報の強いcommutator・低energy対照を与える必要が残る | [B01][A03][E03] |
| PRM05 PF外挿・Richardson | R1-P不保持と、単一S2の相対log保証を比較する仕様が明確になった | A2はRichardson二点相殺の成立証明ではない。R1-P A+還元を外挿一般の解決にもA2の既知還元にも拡張しない | [A02][E01][E02][E04] |
| PRM15 RPE/QPE全round・絶対E0 | A2の固定powers QPE、既知支持/unwrap、scalar L復元という接続条件が公開 | state/cert/controlled native/readout/全confidence込み総費用は未取得。多roundRPE・平均信号・M1-Sへそのまま移せない。H8compileも総E0保証ではない | [A02][A03][B03] |

既存BF/BM、Return aggregation、Parent allocation、M1-S、N1/N2、THRIFT、H1–H4等の整理は再作成していない。N3という名称はoccupation certificateと別系列の「決定論剰余の確率的補正」に衝突するため、ここでのN3は**④occupation certificate**に限る。[P02]

## 2. A2相対保証とEvaluation R1-P：対応仕様の比較

| 比較軸 | R1-Pの固定記録 | A2関連の今回の固定監査 | 今回判定していないこと |
| --- | --- | --- | --- |
| Hamiltonian/分割 | 正のk-local項、extensiveness J、固定数commuting layers。既知還元は正refinement(A+)と同じJの会計を満たす範囲 | 共通不変sectorの有限PSD fragmentsと認証caps、`G=ΣF_j`、`Λ=Σf_j`。各fragmentのsector保存。小localityを共通仮定にはしない | 任意fragment・sector-only PSDまでR1還元を広げない。非局所だから局所定理が無関係ともいわない |
| 作用と保証対象 | 非unitary二点Richardson `X_r=(4/3)U_2r−(1/3)U_r` のright-restricted norm `‖(X_r−exp(−itH_+))P_E‖`、有限r相殺/漏洩 | 単一正stage対称S2のeffective Kについて全vector Loewner相対形式、有限h剰余。ground支持入力でK測定windowとQPE | restricted norm・相対形式・固有枝・信号誤差の同一視。包含/同値/数学的独立性 |
| 入力/証拠取得費 | 合法なJ・cutoff・sector・局所分割。P_Eは証明用対象であり無料の射影oracleではない。state/tail/overlapは別取得 | 認証L/U、同じ分割のPSD/caps、任意ならK_SOSの有限精度証拠。EWはexact ground copiesまたは別state誤差予算 | ground、gap、tight Λ、下界、全振幅を無料入力にして総費用を閉じること |
| 既知定理 | 固定予備還元がcommutator/leakage・有限BCH・DuhamelからA+下の目標上界を記録 | 固定監査がK0/K0.5と3論文の対応を整理。PSD/log/Cauchy/Markov/QPEの道具、低energy有限step保証一般は既知 | A2の全vector/log/有限領域/EW接続まで含む全statementの最強既知定理対応は未確定。今回新しい還元証明なし |
| 絶対E0 | scalar cを各controlled回路に保持。signed sampling増幅、state/tail・phase protocol・confidence・native価格が残る。同lowenergy通常4次PF対照あり | Lを一回復元し、centeringをcontrolled phaseへ保持。既知support/unwrapと固定powers。state/cert/実装/読出しを別会計 | 両者とも保証の成立だけで総E0優位を認定しない。単step上界と出力task全体を直接比較しない |
| 正式研究状態 | ユーザー承認済み **NOT_ADOPTED**、独立候補として不保持。一般NO_GOや研究全体CLOSEDではない | **A2 NOT_ADOPTED**。技術分類 **VALID_WITH_UNRESOLVED_NOVELTY**。K1-F未承認/未実行 | R1不保持をA2棄却へ移さない。A2VALIDをR1再開条件成立としない |

根拠：[R1元の定式化][E04]、[R1既知定理対応][E02]、[R1強対照と絶対E0][E03]、[R1正式不保持][E01]、[A2監査][A02]、[A2先行研究・実用条件][A03]。

共通するのはPSD、低energyを使う誤差保証、有限剰余、同情報の強対照、scalar/成功確率/取得費の保持である。新たに詳細が分かったことで**重複照合すべき仕様が特定できた**。それ以上の還元/非還元の結論は本調査に含まない。

## 3. 第一・第二研究、N3、H8との境界

第一研究の中心は保存PFの有限時刻固有枝・proxy校正と条件付き意思決定の証拠であり、全vector有限step証明ではない。[E05] 第二研究Direction Cはcheap predictorの過小評価とbudget margin、点精度・経験的width・abstention・decision windowを分けた承認済み主解析で、厳密certificateや離散QPE/end-to-end実装保証を目標にしていない。[E06]

したがってA2は同じ「有限step」「energy」「QPE」を扱うため問題領域で接するが、第一・第二研究でPSD caps、認証L/U、state品質、相対形式の条件が満たされたと示す追加証拠ではない。保存されたsafeや約束予算をA2の定理定数へ代入した新成功例は作らない。

N3 occupation certificateのSchur/Fantope等の証拠生成、縮約・正規化・D1下の実現費は別仕様。N3現検証系列CLOSEDと、理論/限定prototypeの条件付き保持を維持する。A2全statementとの関係を名称だけで同じ証明としない。[P02]

H8直接compileは既存構成の価格検証であり、PSD相対形式の検証ではない。特にH8 S4には負stageがあり、RF0/RF1の正stage S2保証を適用しない。saved signed DFを認証PSD分割とみなさず、compileのPASSをbias保証へ移さない。[A02][B03]

## 4. 将来のレビューで判断すべき点（未実施）

GPT／ユーザーがレビューを別途開始する場合は、A2の**同一statement**への既知定理対応、最強同情報baselineとのtask比較、証拠取得・state・controlled実装込みの価値を判断する。これは本書で結論を与えた事項でも、Codexへの追加証明・数値再会計の承認でもない。R1-P、J1、Q1や既存STOPを解除しない。

[O02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/algorithm_improvement_overlap_matrix.md
[P02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
[A01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/decision_handoff.md
[A02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/mathematical_audit.md
[A03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/prior_art_and_practical_conditions.md
[A06]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/inputs/qc_track_iv_research_question_redesign_review_20261017.md
[B01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/ce6cd8ead5c0311ec72165c04869e7df4050b75b/docs/research/track_a_h8_key_compile_completed_results_20261017.md
[B03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/ce6cd8ead5c0311ec72165c04869e7df4050b75b/artifacts/resource_applicability/track_a_h8_key_compile_completed_six/2026-10-17/six_axis_results.json
[E01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/608c6553dcbb63fc45311e004bdd94d20d5840e0/docs/research_exploration/r1_nonretention_decision_20261017/research_decision_record.md
[E02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b39a54443e6b4780295bc0499ac8f8d7b10b083f/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_known_theorem_mapping.md
[E03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b39a54443e6b4780295bc0499ac8f8d7b10b083f/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_baseline_and_scope.md
[E04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/f0da24896b346e59ce225d1c264dd04420e1276c/docs/research_exploration/t0_baseline_gap_survey_20261017/t0_research_problem_candidates.md
[E05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/PF_first_study_paper_claim_ledger_20260926.md
[E06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
