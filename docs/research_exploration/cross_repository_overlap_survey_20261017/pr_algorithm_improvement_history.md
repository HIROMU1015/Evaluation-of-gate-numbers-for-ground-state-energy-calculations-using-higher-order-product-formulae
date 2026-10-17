# Partially：既存整理資料の再利用と19:09 JST以後の公開差分

本書はPR全研究の年表を作り直さない。ユーザー補足に従い、`d09ba606a9fceef806a9313e3f7c43cd21d19e3f` の次の3資料を既存正本として再利用する。

1. [strategy_handoff.md][P01]：4系列の時系列・目的・成果・未確立事項。
2. [overlap_and_progress_map.md][P02]：正式状態と20方向の重複防止マップ。
3. [fixed_evidence_index.json][P03]：原典SOURCE索引。主要128件（PR126・Evaluation2）と補助287件、正式状態記録33件。今回それら415本文を再調査・複製していない。

BF/BM、SP/BS、R/RA、G、Return aggregation、D1–D3、Parent allocation、M1-S、N1–N3、THRIFT、SOS-PF、H1–H4の詳細は上記固定資料の該当行を参照する。再利用した主張と、今回直接確認した後続差分を混同しない。

## 既存4系列への入口

| 本整理ID | 内容と参照先 | 19:09時点で区別されていた状態 | 今回の扱い |
| --- | --- | --- | --- |
| `PR-A` | Track Aの有限時間signal・測定込みcompiled資源評価。[P01] §2.1・§3 | 各run完了・技術STOP、H8 Phase Cは承認済みで確認時点の資料には結果未収録。結果採択レビューとは別 | 下記差分DA1/DA2で更新 |
| `PR-B` | Track B、M1-Sを除く。[P01] §2.2・§4 | Parent allocationのD+Eは正式。BF/BM closure、G区切り、DF補正、Gaussian、休止の記録は原文の強さを維持 | 当日19:09以後の公開状態変更を今回取得したrefsでは確認しなかった。休止解除の欠落は解消済みにしない |
| `PR-M1S` | 正負branchのlabel共有。[P01] §2.3、旧索引C01–C11 | 限定理論受理、H4保存oracleの診断。総回路費用・Task B・方法priority未確立。方向の正式採択なし、統合後mandatory STOP | 新しい結果・契約・方向採択の差分は確認しなかった。未承認Stage C等を開始しない |
| `PR-IV` | PRに限らない新算法。[P01] §2.4、[P02] §2 | N1 STOP、N2 HOLD、N3現系列CLOSED、THRIFT現template CLOSED、H1–H4現探索PAUSED、SOS-PF現分割生成CLOSED、A2 NOT_ADOPTED等 | exact-encodingの狭い既存残件に下記DI1–DI3の公開差分あり。その他停止は維持 |

PR rootの `PROJECT_MAP.md` と研究概要は古いPR-2段階も大量に保持する。checkout HEADやbranch名だけで最新研究を判定せず、固定整理と後続の個別result/decisionを使った。
開始時339公開branch先端はローカルtracking refsと一致した。184登録worktreeを観測した。dirtyは実行中を意味せず、外部chat/jobの現在状態は断定しない。

## DA1：H8 Phase C結果が公開された

結果commit **`6dc5bf0de01a0aa23cafe0ff022c0cd21fbf1086`**、branch `track-a-h8-phase-c-integration-20261017`。
[結果本文][P04]と[terminal][P05]は完了・native exit0・回収・最終gate PASS・次stage未認可を記録する。

- 対象：linear H8、隣接1.00 Å、STO-3G、tol-only DF28、16 spin modes／sector4900、T=.8、q=1/2/4/8。
- task：ε=.05/.01/.005/.001/.0005の**複素signal精度**、allowance倍率1/10、通常signed bias、P=0。state preparationを除くshot-weighted full-wrapper RZ。
- 保存資料の結果：決定論184候補の最良は全条件で固定model推定を含み、PRは確認union6・各n32の有限標本点推定。
- 倍率1の削減率は、本文から順に **−7.136909%、33.092838%、31.306608%、22.961345%、−51.140301%** と転記する。新たな再会計・丸め値からの比率計算は行っていない。
- .05/.0005ではPR点費用優位が消失。中間3精度の正値も、母平均・全格子実測最良・厳密bias・絶対E0総費用の保証ではない。

既存資料の「Phase C未実施／承認待ち結果」はその確認時点の履歴として保存する。後続本文のdispatch/wait時刻は19:08:17–18、公開commitは19:15:20である。
したがって、**19:09以後に新しく実行されたと断定せず、19:09の整理で未収録だった結果の後続公開差分**として扱う。既存整理自体を書き換えない。

## DA2：非相殺COST_COMPARISONも完了公開

結果commit **`23d46e489af054735d9d328aad0342ecdbddf305`**、branch `track-a-h8-noncancellation-cost-readiness-20261017`。
SOURCE `ac932974a0f250be0df5720e1b6dad06f9ff9535`、readiness `4d923ebac693a221fc5ecb3f73cdc55b29318a42` は結果commitと別である。

[本文][P06]と[terminal][P07]は承認されたcost stageの一回完了とSTOPを記録する。同じH8条件・P=0・5精度で、経験的非相殺biasを使う。
倍率1・184基準の保存削減率は **16.624251%、34.684864%、35.125323%、39.283346%、−29.091008%**。
通常signedと異なる適格性・shot会計であり、方式改善・新compile・厳密誤差保証を意味しない。
両会計を一つのwinner表へ混合しない。旧資料の「COST_COMPARISON未承認」は当時の記録で、現在の差分は個別実行完了である。ユーザーによる結果の科学採択・新しいGPT採否レビューの完了までは確認していない。

## DI1–DI3：exact encodingの既存残件を限定検討し区切った

| 差分 | 固定公開記録 | 内容・証拠区分 |
| --- | --- | --- |
| DI1：静的preflight | `9ba02e46a808aa2dd7857f413cd18a014db0db38`、receipt付きtip `68a87f99e16cff3e20d256e0432b11e6f3fb9d8b`。[P08] | encoder、sector、mode順、control scalar、既存APIの接続条件を整理。新生成規則は未提示。Paldus本文の必要範囲がこの作業で取得されたという記録がある。旧未取得レビュー原本を一括取得済みにしない |
| DI2：一つの固定N・spin-free DF平方block | `c55fc504c8c6f02eefdf9d7fd27d8dae56a8ed60`、receipt付きtip `830be75335bb9b599488cb365213d555b0dc18bb`。[P09] | `D_s=D−s(N̂−N0)` の構成を既知のnumber/symmetry shiftへ具体対応。**REDUCES_TO_KNOWN_METHOD**。qubit削減、native利益、全energy優位は未測定 |
| DI3：ユーザーの正式方向判断 | decision `a791b6ac174790605a77915e012039a4334bcfb4`、公開照合tip `67576526c4e96ae7235fa645fdf744278d049f8d`。[P10][P11] | 現限定attemptを **CONCLUDED_NO_FURTHER_EXPLORATION_IMPLEMENTATION_OR_NUMERICAL_VALIDATION** とし、④の **RESEARCH_QUESTION_SELECTION** へ戻る。全encodingのNO_GOでも④全体の終了でもない。次の具体課題は未採択 |

既存20方向の行8（encoding/sector）の狭い記録不足を、現在も全く未検討と呼ばない。一方、この一試行の既知法還元から、同一absolute-energy条件での全費用比較が完成したとも扱わない。

## 未確認事項の持越し

別途、root未追跡の `qc_track_iv_research_question_redesign_review_20261017.md`（registry L05）を取得した。
ヘッダ・結論・状態だけを確認すると、既存A2の有限step相対形式保証／energy出力区間／step選択を扱うローカル提案であり、未採択・実行未承認と明記する。
レビュー完了・開始承認は文書の自己申告として記録し、元chatを独立取得したことにはしない。
本文の数学的検算・候補比較は行わず、公開固定版は未確認。この後続検討の存在は記録するが、PR既存正式状態を変更しない。

[P01] §8の欠落は、上記で個別に取得・更新が確認できたものだけを更新対象とする。
GPT V1強化baselineレビュー原本、H7承認文言、Track Bの一部review原稿、M1-S旧Claude原本・Davies全文、出版版差分等は、今回新たに取得していない。
exact-encoding preflightに保存されたGPT原本はその特定レビューの取得であり、これら旧原本の代替ではない。

次の科学判断はGPT／ユーザーの担当。今回の差分確認から新レビュー、追加compile、保存値再解析、M1-S再開、別encoding設計を始めない。

<!-- fixed-source-index -->

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
