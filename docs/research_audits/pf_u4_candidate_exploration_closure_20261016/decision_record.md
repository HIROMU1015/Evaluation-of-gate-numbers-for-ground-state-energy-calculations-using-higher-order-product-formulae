# U4-C4正式採択・限定成果保存・追加研究STOP

**決定日：2026-10-16 JST。決定主体：ユーザー。** 本書は今回の添付指示に示された正式採択事項を記録する。Codexが研究価値・新規性・科学的GO/STOPを再判断したものではない。

## 1. 決定A：U4-C4

1. U4（direct最適時刻の系サイズ移送）を独立研究として追加追究しない。
2. U4-C2（H8/H9等の新規検証）を実施しない。
3. U4-C3（連続最適時刻や一般サイズ則の新理論）を開始しない。
4. 既存U4結果を、U4-C1に相当する限定的な補助成果として保存する。
5. U4の追加研究をSTOPする。

**C4は独立研究としての追究を終える決定、C1は保存・記述する既存成果の範囲**である。新しい独立研究としてC1を別途採択したわけではない。これは研究方針の完結であり、未使用サイズでの反証、一般サイズ則の数学的不可能性、全PFに対する否定結果を意味しない。

## 2. 決定B：監査済み候補範囲の探索終了

2026-10-16の完結性監査が整理した**U1〜U7の範囲**について、新しい独立研究テーマを探す作業を一区切りにする。採択済みのU1-C1、U3-E4、今回のU4-C4と、既存研究に属するU2/U6/U7、U1と重複するU5を区別する。[MAP] [U1] [U3]

この範囲では「直ちに追加研究として採択する独立テーマを残さない」と記録する。全研究テーマの網羅的探索や、新研究の不存在・不可能性を証明したという意味ではない。U2・U6・U7の既存状態や未実施事項を、この決定によってSTOPまたはGOへ変更しない。詳細は[audited_candidate_scope_closure.md](audited_candidate_scope_closure.md)に記録する。

## 3. 固定根拠と資料の世代

| 根拠 | 固定identity・役割 |
|---|---|
| 今回のユーザー添付指示 | 決定A/B、文章作成、新規4資料のみの公開とMandatory STOPの直接の承認根拠。原byte数・SHA-256はprovenanceに記録 |
| U4 partial report | `4672f3f5c57e34a553518b10655396a195521294`の`report_partial_v1_2.md`。even H2/H4/H6と旧H5、親status・小系LOO・有限grid限定を保持。[OLD] |
| U4 H5/H7 interim | 同snapshotの`server_hchain_direct_optimal_time_h5_v1_2_20260927_e82b6ae/report.md`。H7の後続完了、H5/Y8不適格、H8/H9未実行を確認。[INTERIM] |
| 完結性監査 | `b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1`のaudit、map、options、provenance。監査時点の候補分類を履歴として保持。[AUDIT] [MAP] [OPTIONS] [AUDITPROV] |
| 後続A6 | `19362c23ccdc16b6ad0ff547cc363e138a3930d2`の条件拡張report §4。局所格子依存の別run。[EXP] |
| 既存正式決定 | U1-AR `b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5`、U3/H05 `56531350d2b931e5cce753c2474e2401094b0eea`の各decision record。[U1] [U3] |
| 第一研究・他系列の境界 | final synthesis、paper claim ledger、Direction C承認scope、G/R完了受理、FS-R1 B0の未承認条件。[SYNTH] [CLAIMS] [DIRC] [DIRCSTOP] [B0] [B0GO] |
| Claude `レビューoutter(8).md` | **原文未取得・未確認**。repository、attachments等のアクセス可能なfilename検索では見つからなかった。全保存場所での不存在とは主張しない |

Claude原文を取得できない場合に、今回のユーザー採択事項と固定GitHub資料を正式根拠として進めることは、添付指示で明示されている。原文の内容・評価・節・引用を推測しない。新しいGPT/Claude詳細科学レビューも開始していない。

旧監査にある「U4再開は未採択」「C2/C3は条件付き選択肢」という記録は作成時点のまま残す。**現在の採択方針をこの新規recordへ追加し、旧decision・protocol・STOP markerは編集しない。**

## 4. U4-C1相当として保存する限定成果

| 保存する結果 | 必須の限定 |
|---|---|
| even neutral singlet H2/H4/H6のm5で`t_grid*/t_ana = 1.40 / 1.50 / 1.35` | 指定有限grid上の事後的な最小値。未知サイズに対する前向き予測則ではない。[OLD] |
| odd cation triplet H5/H7のm5で`1.35 / 1.45` | even系と別系族。H5/H7/H9のodd fitは未実施。H7は後続interimで実行済み。[INTERIM] |
| H5/H7 m5の保存費用比`0.624886839724 / 0.638511699204` | direct grid内の事後比較。情報取得費・状態準備・fault-tolerant runtime込みの総費用削減ではない。[INTERIM] |
| Y8小系power-law不成立、H5/Y8枝gate不合格 | H5/Y8を成功データへ含めない。H5のm5まで不適格としない。[OLD] [INTERIM] |
| 零交差近傍と格子依存 | 1%区間の単一grid点は連続最小の幅の証明ではない。A6を旧U4と一つの実験へ結合しない。[PROTO] [EXP] |

[u4_limited_findings_draft.md](u4_limited_findings_draft.md)に定義・source・未確認事項を添えて保存する。`t_ana`の式と入力経路は既存sourceを静的に照合したが、取得費を含む総会計は未確認のまま。新しい係数・費用計算で埋めない。

## 5. 再開条件と、今回変更しない状態

将来のU4再開や独立研究課題の検討には、**新しい科学的証拠とユーザーの別の明示承認が両方必要**である。未取得原文の所在判明、旧計画の存在、未実行サイズがあることだけで自動再開しない。本書は追加実験や理論研究のprotocolを設定するものではない。

親U4の`failed_numerical_or_boundary_validation`、`not_scorable_due_to_numerical_or_boundary_gate`、後続の`complete_H5_H7_interim_scope`、H5/Y8の`not_scorable_gate_failure`は原本のまま保持する。今回のC4を親実験の新しい採点statusへ書き戻さない。[OLD] [INTERIM]

第一研究S0〜S4の完了、S4 `complete_no_benefit`、S5非実施、既存claim ledgerを維持する。[SYNTH] [CLAIMS] U1のC1草案とSTOP、U3のE4草案とSTOPを変更しない。FS-R1 Phase BはB0 preflight GOでも`Phase_B_authorized=false`、truth未実行のままである。[U1] [U3] [B0GO] 第二研究Direction C、PR、R5探索、他系列のscope・成果・未実施条件に干渉しない。

## 6. 公開範囲とMandatory STOP

base `56531350d2b931e5cce753c2474e2401094b0eea`から独立worktree・新規branch `pf-u4-c4-research-candidate-closure-20261016`を使用する。新規作成・commit・通常pushは、本書、限定成果草案、監査済み候補探索終了記録、[provenance.json](provenance.json)の4資料のみ。別branchの固定資料はmerge・cherry-pick・複製せず参照する。

既存SOURCE、raw results、protocol、manifest、decision、grant、authorization、STOP marker、本原稿・図・captionを変更しない。元worktreeのdirty/staged/untracked、IDEで開かれた`src/trotterlib/cost_validation.py`を保全する。

新規科学計算・保存数値の再fit/再集計/再ランキング・新証明/反例・科学実装は0件。検証は文書・引用・Git差分・byte/hash・保全に限定する。固定sourceを独立GitHub取得と照合し、公開後は新規4 blobのremote SHA・Git blob・byte・SHA-256を照合して最終handoffで報告する。provenance自身のhashは自己除外し、公開後の照合で確認する。

**Mandatory STOP：4資料の公開・照合後に停止する。第一研究の論文化・本文統合、FS-R1 Phase B、新しい独立テーマ探索、EH-1/EH-2調査・実装、U4-C2/C3、旧研究再開へ自動進行しない。**

<!-- fixed-source-references -->

[AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_audit.md
[AUDITPROV]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/provenance.json
[B0]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/README.md
[B0GO]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/GO_NO_GO_FOR_PHASE_B_PRODUCTION.json
[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[DIRC]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e895870f16878ee4181b0e0dfe3159826a791563/docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md
[DIRCSTOP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1d01e77247364b49dbce2e9ce2fe7c32af0fb937/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[EXP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/19362c23ccdc16b6ad0ff547cc363e138a3930d2/docs/research_outcomes/20261007/validation_expansion_results.md
[INTERIM]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/server_hchain_direct_optimal_time_h5_v1_2_20260927_e82b6ae/report.md
[MAP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/open_question_and_evidence_map.md
[OLD]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961/report_partial_v1_2.md
[OPTIONS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_options.md
[PROTO]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/hchain_direct_optimal_time_scaling_protocol.md
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7f0b30d215e8094c95ae895b9469a04180e2385e/PF_first_study_final_synthesis_20260925.md
[U1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[U3]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/56531350d2b931e5cce753c2474e2401094b0eea/docs/research_audits/pf_u3_h05_e4_closure_20261016/decision_record.md
