# U3／H05：E4正式採択・補助成果としての完結・追加研究STOP

**決定日：2026-10-16 JST。決定主体：ユーザー。** 今回の添付指示に記載された承認済み方針を記録する。CodexがE1〜E4の採否・新規性・研究価値を改めて判断したものではない。

## 1. 採択事項と完結の意味

**E4：U3／H05を独立研究として継続せず、既存第一研究の補助成果として完結する。**

1. U3／H05を独立した新研究として追加追究しない。
2. H05の成果は、E1で記述可能な限定範囲の技術比較・機構解析として保存する。
3. E2の固定2点方式の未使用系検証は実施しない。
4. E3の新しい高次係数取得理論・一般D6/D8構築法の研究は今回開始しない。
5. U3／H05の追加研究をSTOPする。
6. 将来、新しい科学的証拠が得られ、ユーザーが別途明示承認した場合に限り、再開を検討できる。
7. 第一研究の論文へ統合するかは、後の原稿編集段階で別途判断する。

**E4は独立研究としての扱い、E1は保存・記述できる成果の範囲**である。E1を追加の独立研究として採択したわけではない。STOPは研究上の終了判断であり、未使用系の実験でH05が否定されたことや、新しい係数取得法の数学的不可能性を証明したことを意味しない。

## 2. 固定根拠と、独立研究として継続しない理由

| 根拠 | 固定identityと役割 |
|---|---|
| 今回のユーザー指示 | 2026-10-16のE4採択・E2/E3不実施・STOP・限定草案作成・3資料公開の直接の権限根拠 |
| U3/H05静的監査 | `e2c8527eb10d383c41f161078565e04d29a5df9b`の[handoff][AUDITHANDOFF]、[方式・証拠][AUDITMAP]、[費用・移送性][AUDITCOST]、[provenance][AUDITPROV] |
| 元の成果 | `e820f653a5916f27233ab4674a89d288cf969e37`のH05、D04、H04、F02/F03のreport、H05/D04 audit・source。[H05] [D04] [H04] [F02] [F03] |
| 第一研究の完成scope | final synthesis `7f0b30d215e8094c95ae895b9469a04180e2385e`、paper claim ledger `cd81018932b9557b7a55e2e1cd8c5e3988245409`。[SYNTH] [CLAIMS] |
| U1-ARの既存完結記録 | `b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5`の[decision][U1DECISION]・[C1補論草案][U1DRAFT]。STOP・原文・草案を維持する |
| Claude `レビューoutter(7).md` | アクセス可能なfilename検索では**未取得・原文未確認**。ユーザーのE4採択と固定GitHub資料を正式根拠にする。原文の引用・節・評価を推定しない |

ユーザーが今回の判断で踏まえた固定証拠は、既知の摂動／response・compact BCHとの関係、小系development内の検証範囲、同一2点方式の独立holdout未確認、D04の非一律な費用優位である。高次係数取得・状態依存・費用会計の限定比較を第一研究の補助成果として保存し、未使用系検証や新理論で独立研究へ拡張しない、という承認済みの配置判断を記録する。[AUDITHANDOFF] [AUDITMAP] [AUDITCOST]

前回監査の「E1〜E4未採択」「E4をformal STOPへ自動変換しない」は作成時点の記録として保存する。**今回の明示承認による現在の方針を本書へ追加**し、旧資料を遡及編集しない。H05/D04原報告の将来holdout候補という記載も履歴として保持し、その追加実行には進まない。

## 3. 補助成果として認める限定範囲

| 成果 | 保存する既存到達点 | 主張しないこと |
|---|---|---|
| Exact BCH＋response | H2/H4 STO-3G×4種類の4次PF、8条件で標準摂動のa8混合を確認し、元の高次残差基準を達成 | 新しい摂動論、6次・8次PFの性能検証、安価な一般D6/D8構築 |
| HF／CISD | HF response 4/8、CISD 7/8。H2 CISDはexactと一致 | 高いenergy精度・overlapによる一般的係数精度保証、全8条件が独立した近似状態検証 |
| Exact a4＋固定2点 | 同じ開発集合で、参照三項モデルのt*における高次加重残差8/8 | a8の高い相対精度、t*のdirect truth、全有限時間保証、QPE budget safety、未使用系移送 |
| D04 | a4取得費を課金した小系会計。fixed2がfree5より速い1/8、推定peak memoryが同等以下0/8 | direct点数削減を一律の古典総費用・memory・量子資源削減へ言い換えること |
| H04 | compact D4の式生成短縮と作用の整合性 | dense入力・状態取得・高精度・一般D6/D8の費用解消 |

根拠：[H05] [H05AUDIT] [D04] [H04] [H01]。条件数・判定は元資料を引用し、保存CSVの再集計・再fitは行っていない。

## 4. 第一研究・U1-AR補論との関係

[first_study_technical_supplement_draft.md](first_study_technical_supplement_draft.md)を独立草案として保存する。中心は係数取得法、exact/HF/CISD、few-point設計とa4 prior、取得時間・memoryの比較である。既存第一研究本文、図、caption、claim ledgerへは統合しない。

有限時間の対象枝、proxy、Taylor/Magnusの一般的な説明はU1-ARの[既存C1補論][U1DRAFT]への参照に留める。F02のa8式など必要な接続部分のみ再掲し、掲載時にどちらを定義の正本にするかという編集候補を技術草案に記す。既存C1草案の編集・移動・削除を行わない。

第一研究S0〜S4は完了済み、S4は`complete_no_benefit`を保持する。補助成果の配置を、その否定結果や既存限定claimを変更する理由にしない。U1-ARのSTOP、第二研究、PR、R5探索、FS-R1その他の研究状態へ干渉しない。[SYNTH] [CLAIMS] [U1DECISION]

## 5. STOPと再開条件

E2の追加holdout、E3の新理論・一般D6/D8構築研究を実施しない。新しい方法・分子・PF・state・benchmark・閾値・rankの検討を、完結作業の残件へ自動追加しない。

再開を検討できるのは、**新しい科学的証拠とユーザーの別の明示承認が両方ある場合だけ**である。原文や未取得資料の所在判明だけで自動再開しない。必要となる対象・範囲・truth access・上限・停止点は、将来の別承認の範囲で確認する。本書は再開protocolや追加実験の予約ではない。

今回の草案の保存・GitHub公開は、本原稿への統合・論文投稿の承認ではない。U4その他の候補の科学レビューや次の独立研究テーマの選定にも進まない。

## 6. 保全・公開範囲と終了

独立worktree／branch `pf-u3-h05-e4-closure-20261016`、base `b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5`を用いる。U3監査commitは別の固定参照として取得し、merge・cherry-pickしない。

新規作成・commit・pushは本書、技術補論草案、[provenance.json](provenance.json)の3資料のみ。既存SOURCE、results/CSV、protocol、manifest、decision、review原文、claim ledger、STOP、authorization、grantは上書きしない。H05、D04、H04等の`complete_with_findings`も元のまま保持する。元workspaceのdirty/staged/untracked、active `src/trotterlib/cost_validation.py`、他worktree・cache・研究jobを変更しない。

新規科学計算、保存値再解析・再集計・再fit・再ランキング、新証明・反例、科学実装・benchmarkはすべて0件。検証は文書・引用・byte/hash・Git差分・保全の確認に限定する。新規3 blobを公開後のGitHub固定commitから再取得し、remote SHA・byte・Git blob SHA・SHA-256を照合して完了を報告する。

**Mandatory STOP：3資料の公開と照合が完了したら停止する。研究再開・次テーマ選定・U4評価・追加計算・本原稿統合・投稿へ自動進行しない。**

<!-- fixed-source-references -->

[AUDITCOST]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e2c8527eb10d383c41f161078565e04d29a5df9b/docs/research_audits/pf_u3_h05_completion_20261016/end_to_end_cost_and_transfer_audit.md
[AUDITHANDOFF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e2c8527eb10d383c41f161078565e04d29a5df9b/docs/research_audits/pf_u3_h05_completion_20261016/research_completion_handoff.md
[AUDITMAP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e2c8527eb10d383c41f161078565e04d29a5df9b/docs/research_audits/pf_u3_h05_completion_20261016/h05_method_and_evidence_map.md
[AUDITPROV]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e2c8527eb10d383c41f161078565e04d29a5df9b/docs/research_audits/pf_u3_h05_completion_20261016/provenance.json
[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[D04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/report.md
[F02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md
[F03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md
[H01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h01_approximate_state_pilot_20260922/report.md
[H04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md
[H05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md
[H05AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/audit.json
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7f0b30d215e8094c95ae895b9469a04180e2385e/PF_first_study_final_synthesis_20260925.md
[U1DECISION]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[U1DRAFT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5/docs/research_audits/pf_u1_ar_c1_closure_20261016/c1_theory_appendix_draft.md
