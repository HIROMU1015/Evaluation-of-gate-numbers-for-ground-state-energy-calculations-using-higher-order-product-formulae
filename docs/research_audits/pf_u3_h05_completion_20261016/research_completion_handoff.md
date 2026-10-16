# U3／H05：科学判断のための静的監査handoff

2026-10-16 JST。対象repositoryは`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。専用branchは`pf-u3-h05-completion-static-audit-20261016`、baseは`b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1`。本資料は選択肢と不足証拠を提示し、研究方針、中心claim、科学的新規性、追加研究のGOを採択しない。[AUDIT] [OPTIONS]

読む順序は本資料 → [方式・証拠](h05_method_and_evidence_map.md) → [総費用・移送性](end_to_end_cost_and_transfer_audit.md) → [provenance](provenance.json)。新しく公開するのはこの4資料だけ。最終commit固定URLと公開後照合結果はchatの最終handoffに示す。provenanceは自身のhash／handoff commitを自己参照しない。

## 1. 現時点で確立した範囲と未完了の問題

| 方式 | 既存到達点 | 未確立事項 |
|---|---|---|
| A1 exact BCH＋response | H2/H4×4種類の4次PFでa8混合identityと高次残差8/8。dense D4全体を作らず混合を取得 | exact state・dense H・D6/D8の取得費、一般系の安定性・総費用・有限時間保証 |
| A2 approximate-state BCH＋response | HF4/8、CISD7/8。状態品質と高次係数精度の条件依存を記録 | state scalarからの事前認証、実用状態取得費、未使用系の固定精度保証 |
| A3 exact a4＋固定tail2点 | 同一development集合の高次残差8/8、最悪0.02829 epsilon | 同一recipeの未使用系評価、参照・枝・a4も課金した費用利益、direct finite-timeでの妥当性 |
| A4 direct operator取得 | H04はcompact D4 symbolic生成blockerを解消。D04は小系dense order8生成費を計測 | 安価な一般D6/D8構築、dense入力・statevector・高精度・memory制約 |

根拠：[H05] [H05AUDIT] [H04] [D04]。上表の8/8は参照三項モデルt*での高次係数差の判定である。4次PFのsubleading a6/a8を扱った結果を、6次・8次PFの一般取得へ拡張しない。

費用不足を一括して「未測定」とするのも不正確である。D04はa4取得費を課金し、fixed2がfree5より速いのは1/8、推定memoryが同等以下なのは0/8と報告している。小系dense構築の計測は存在する。一方cold時間は保存setupとmarginal値の合成であり、精度変更・大規模系の全工程や方式別実測peak memoryは未取得である。[D04] [D04CODE]

## 2. 既存成果だけで記述できる限定claim候補

以下は原結果のscope内で記述可能な候補であり、論文中心claimとして採択したものではない。

- 固定小系・4次PFでは、a8はD8対角項とD4状態混合を含み、混合を一律に落とせない。既知摂動構成を保存8条件で検査した。[F02] [H05]
- exact a4をpriorにすると、同一development集合で2個のdirect入力点でも宣言した高次残差基準を満たす。ただし点数、相対係数精度、古典費用、有限時間truth精度は別である。[H05AUDIT]
- 状態近似や相殺により、曲線残差、係数の相対精度、operatorの大きさ、選択・予算の指標は一致しない。[F02] [F03] [H01]
- compact D4による式生成短縮と、総取得費の削減は異なる。保存D04の小系比較は一律の時間／memory優位を支持しない。[H04] [D04]

これらの数学的枠組みには明確な先行研究がある。指定3論文の版・式・情報要件・実証範囲の照合は[方式資料の節6](h05_method_and_evidence_map.md#6-先行研究との限定照合)に集約した。先行法との差を確認しても、それだけで独立した研究価値が成立するとは判定しない。

## 3. E1〜E4の成立条件と停止条件

既存完結性監査のC2/C3/C4という整理は監査上の候補であり、研究採択ではない。以下のE1〜E4もGPTが選ぶための比較表で、Codexの推奨順位・採択結果ではない。[OPTIONS]

| 経路 | 成立に必要な証拠・残作業 | 成功時／不成立時の結論候補 | 新科学計算・停止条件 |
|---|---|---|---|
| E1 既存成果で限定完結 | 上記限定claimのscopeと、既知理論・第一研究補助成果との関係をGPTが選ぶ。必要なら既存図表・引用の編集のみ | 小系機構・取得法比較として記述可能。安価な一般取得法・未使用系保証は主張しない | 既存scopeなら新計算を要件にしない。独立性が必要な中心claimへ変われば、その判断で停止しE2/E3/E4を再検討 |
| E2 限定追加検証 | **H05の同一固定recipe**の移送精度と総取得費の成立を検査する必要が中心claimにあるとGPTが判断。未露出条件、truth access、budget、評価対象を事前固定 | 成功しても固定した評価範囲だけを追加。精度passでも費用利益なしなら、その両方を結論に残す。失敗なら限定scope／不成立を報告 | 科学計算または保存値の科学再解析の別承認が必要。source/branch/数値gate失敗、情報予算不適合、上限到達で停止。時刻・threshold・stateの結果後変更で救済しない |
| E3 新理論を要する主張 | 一般D6/D8取得費、近似状態係数の認証、有限時間剰余・branch条件を含む保証等、何を新しく保証したいか確定。既知定理の仮定との差を整理 | 必要な保証が既知理論の適用で足りるか、新結果が必要かを科学側が判断 | 今回は証明・symbolic checker・新backendを設計しない。新しい理論命題や科学実装が必要になった時点で停止 |
| E4 独立研究として扱わない | 文献と既存研究のclaim対応を確認し、H05固有の問い・費用／情報契約が独立した中心を作るか科学側が判断 | 重複が強い場合、第一研究の補助・技術比較・限界として配置する選択肢 | E4を新しいformal STOPへ自動変換しない。第一・第二研究のledgerやGO/STOPを書き換えない |

## 4. 追加研究が必要と判断された場合の最小の対象と目的

ここでは実験座標やthresholdを指定しない。未使用分子・PF・rank・gap・truthを追加する承認も与えない。

| 未承認の作業対象 | 検証目的 | 入力・既存baseline | 判定に必要な不足情報 |
|---|---|---|---|
| 同一A3固定recipeの未露出条件評価 | exact a4＋保存の絶対2時刻・t6/t8 fitが移送するか | exact a4の定義、E0、branch付signed shift、固定PF。既存free3/free5を同じ情報・費用境界で比較 | 条件の独立性、元基準を何に適用するか、finite-time direct評価と係数残差の区別、全工程費用 |
| 既存backendの取得費coverage補完 | H05 online／D04会計から除外された工程が実用費を変えるか | SCF/状態/BCH/response/枝検査/precision/memory/reuseの同定 | 欠けた原sourceの回収で足りるか、限定benchmarkが必要か。後者は新科学計測として別承認 |
| A2近似状態の未解決部分 | 要求係数精度の事前認証が必要かを判断 | 既存HF/CISD、同一H・PF、既知摂動baseline | norm/gap等の追加情報の費用と保証範囲。新しいstate診断の設計へ自動拡大しない |

「2点法なので安い」を検証目的にせず、**どの取得情報をどの費用で得て、どの評価対象を満たすか**を先に判断する必要がある。特にexact a4を近似a4へ置換したり絶対時刻を系依存座標へ変更したりすれば別方式となり、H05固定方式の評価とは分けなければならない。[H05CODE] [D04]

E2で必要なbaselineにはH05内の自由3/5点t4/t6/t8を含められるが、既存N2/CO研究のt4/t6二項fitとは同一ではない。A1の係数参照やdense backendを使う場合も、参照取得費と運用取得費を別fieldに記録する必要がある。これらは将来仕様の確認項目で、今回の正式protocolではない。

## 5. GPTが判断すべき科学的論点

1. 完成対象を、相殺下の小系取得法比較までに限るか、未使用系の性能・総取得費まで含むか、一般保証まで要求するか。
2. 独立した中心課題となり得る差分は、subleading a8混合の実証、固定prior＋few-pointの情報／費用契約、未使用系での同時成立のどこにあるか。既知理論・既存第一研究との重複を許容する位置付けか。
3. D04の非一律速度優位を踏まえ、点数削減以外に何を成功条件とする科学的理由があるか。古典秒数、memory、量子回転数のどれを主claimへつなぐか。
4. exact-state／direct oracleを許す技術研究で十分か、oracle-free／近似状態認証を必須にするか。後者は単なるholdout追加だけで解消しない可能性がある。
5. E1〜E4のどれを採るか、その判断に本当に不可欠な追加証拠は何か。新しい理論・計算の範囲と停止点はどこか。

本監査はこれらの答えを選ばない。既存結果だけで一般解が完成したとも、限定追加研究で必ず論文化できるとも、独立研究として不適切と確定したとも書かない。

## 6. 他系列・既存停止記録との関係

U1-ARは別担当の静的調査であり、そのworktree、branch、scratch、成果物を変更・取り込んでいない。F02/F03/H04/H05という固定公開資料の共有はあるが、折り返し共鳴仮説との統合、相互結果待ち、P1科学計算はしていない。

本repository第一研究はS0〜S4の機構・信頼性・安全性／効率性の分離を中心に完成scopeを持つ。S4 `complete_no_benefit`後のS5は未実行停止を保持する。H05の小系結果が補助成果へ入る可能性と、第一研究のformal statusを変更することは区別する。[SYNTH] [CLAIMS]

10月H4 response follow-up、FS-R1 state/local介入は第一研究follow-upで、H05 projected D4 responseや固定tail2と異なる。FS-R1-B0のGOはpreflightでありscience authorization=false。Phase Bを開始していない。[H4FOLLOW] [FSA] [FSB]

第二研究Direction Cにはpoint改善とdecision/resource価値の分離という接点があるが、H05は係数取得の問いであり、spectral width/certificate／branch recoveryの既存主claimとは別に扱う。独立性や統合は採択していない。[SECOND]

他PRの第一・第二研究（Track B）、Track A、条件付きPAUSEDの新アルゴリズム探索は対象外。完全なclaim-ledger比較はしておらず、「重複なし」とは認定しない。いずれの研究目的、formal status、STOP、authorization、claim ledgerも変更しない。

## 7. 実施範囲・保全・Mandatory STOP

今回の新規Hamiltonian／SCF／FCI／state計算、D4/D6/D8生成、response solve、PF固有位相、保存値再集計・再fit・再採点・再ランキング、benchmark、科学実装、新証明、GO/STOP採択は**すべて0件**。既存科学testsも実行していない。実施した検証は文書構造・リンク・byte/hash・Git差分／公開blob・元workspace保全の監査に限定する。

専用worktreeで4資料だけを作成する。既存SOURCE、results/CSV、protocol/manifest、review原文、STOP、authorization/grant/ledger、第一・第二研究のformal statusは変更しない。元workspaceのHEAD・status・worktree diff・index diff・変更tracked file hashesを前後比較し、provenanceに記録する。全private/untracked binaryをhashしたという主張はしない。

GitHub固定commitから4資料を再取得し、remote branch先端・byte数・Git blob SHA-1・SHA-256が一致した後にhandoff完了とする。公開証明とself-hashの循環を避け、最終commit／4資料の公開後照合は最終chatで報告する。既存資料は固定commitへリンクし、複製・重複commit・mergeしない。

**Mandatory STOP：4資料の通常non-force pushと公開後照合を終えたら停止する。** 以後のH05計算、追加holdout、研究採択、詳細科学レビュー、U1-AR計算、FS-R1 Phase Bを自動開始しない。

<!-- fixed-source-references -->

[AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_audit.md
[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[D04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/report.md
[D04CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_d04_equal_classical_budget.py
[F02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md
[F03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md
[FSA]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[FSB]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/README.md
[H01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h01_approximate_state_pilot_20260922/report.md
[H04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md
[H05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md
[H05AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/audit.json
[H05CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_h05_higher_order_acquisition.py
[H4FOLLOW]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5b370ec22f7ffeac687ef70e1bcb87337f5fb976/artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/report.md
[OPTIONS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_options.md
[SECOND]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e895870f16878ee4181b0e0dfe3159826a791563/docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_final_synthesis_20260925.md
