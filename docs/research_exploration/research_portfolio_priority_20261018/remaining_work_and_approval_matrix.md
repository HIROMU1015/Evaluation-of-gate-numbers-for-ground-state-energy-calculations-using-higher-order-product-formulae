# 残作業の分類と次の作業カード

A＝既存資料の文書対応、B＝追加技術検証、C＝重要科学判断、D＝科学計算・数値再解析の可能性。**今回は整理のみ。以下の作業カードを開始しない。** 既存の承認・one-shot完了を、新しい実行許可に流用しない。

| 系列 | A：既存資料だけ | B：追加技術確認の候補 | C：GPT／ユーザー | D：必要となり得る追加scienceと判断への影響 |
| --- | --- | --- | --- | --- |
| 第一研究 | 本文→C1–C10→metric/source対応、caption/表番号、限定の欠落一覧 | 矛盾が残る場合だけsource pointer・保存形式の限定検査。science checkerは別範囲 | 既存結果だけの中心claim・着地点・本文版の採用 | cap外安全・連続oracleなど現在除外するclaimを新たに要求する場合だけtruthが必要となり得る。そのclaimを採るかを先に判断。S5/FS-R1は自動開始しない |
| 第二研究 | 10/5outline/図と10/6 G/R/prospective mapの配置delta、第一研究との重複表 | 新しく引用するsourceのidentity欠落を限定確認。legacy full-suite greenは主張しない | 独立論文としてのclaim・第一研究との境界・既存レビュー後の採用範囲 | 絶対energy identityやq=1総費用を新claimにするなら新取得・会計が必要となり得る。限定論文のために自動補完しない |
| 旧高次PF | 対象版・公開版とlocal TeX/図/sourceのidentity表 | private原本の合法な公開対応、係数/実装の同一性が必要な場合の静的確認 | 現原稿の中心claim・editorial方針・修正範囲の選択 | 厳密次数・実資源など拡張claimのために必要かは未決。新係数調整・回路検証を本調査から発注しない |
| PR Track A | v0.4と後続固定結果の対応、測定/model/有限標本/経験的allowanceのラベル整合 | 欠けた原来歴join・compiler identityの確認は個別scope。raw不足を新samplingで代用しない | 最新証拠で採るclaim、case studyのscope、追加検証の必要性 | B/D実測の総費用統合は保存値再解析Dで別承認。母平均・選択保証や未取得A_COSTも新scope。結果は比較claimの強さを変え得るが、今回契約・grantを作らない |
| PR Track B | 完成ノートと10/18技術分類の索引・限定の保持 | 原本未提供検算などの有無確認は必要性決定後 | 狭い構成ノートの価値を追加重要レビューへ戻すか、現在の記録保全で足りるか | 独立生成・normalizer・native取得込み利益の新証拠は新研究に当たる。今回探索・計算しない |
| M1-S | 既存統合記録の利用 | 不足source/引用の確認を行うかも別指示 | ノート化・正式状態・継続scope。既存推奨を採択へ昇格しない | whole-wrapper・Task Bは新理論/実装/実行の採択が必要。Stage Sだけから発注しない |

次のCodex作業の候補は次の通り。全て**提案・未開始**であり、本ユーザー指示B4の停止境界を守る。

## A-1：第一研究の本文・固定証拠対応

- 対象：Evaluation第一研究。固定入力：[S03][S04][S05][S06][S08]（snapshot `d26aa812226819c406d6ce645dbb3c1056b0e8ee`、originはregistry別field）。
- 作業：ユーザーが特定する本文版の数値・図表・限定を既存台帳に対応付け、未対応箇所を記録する。保存値を再計算せず、本文の科学的結論も変更しない。
- 追加入力：対象本文のpath/commit。未取得なら「本文未特定」で止め、旧高次PF TeXで代用しない。
- 成果物：claim/source/caption対応表、欠落と矛盾の一覧、手続き監査handoff。
- 承認：既存方針は既存結果だけの論文化。ただしこの実作業を開始するユーザーの次指示が必要。重要claim判断はGPT／ユーザー、新scienceは含まない。
- 依存・STOP：S4 corrected beta、saved-grid/HF boundsを保持。新truth・再採点・claim拡張が必要になれば該当部分を止めて判断を返す。対応表公開後STOP。

## A-2：第二研究の後続証拠配置delta

- 対象：Evaluation第二研究。固定入力：[T01]–[T09]、特に10/5成果版と10/6 G/R完了受理・map。
- 作業：既存outline/claim台帳/図captionのどこが後続証拠を扱い、どこが未対応かを文書上で対応付ける。数値・比率を再集計しない。
- 成果物：節/図/claimと後続evidenceのdelta表、第一研究との共有HF/B0・独立scopeの境界表。
- 承認：既存のevidence整理許可は確認済み [T05]。本カード開始は次のユーザー指示で指定する。本文・claim採用はGPT／ユーザー。
- 依存・STOP：prospectiveの分母16/13や時刻・rankの相関を維持する。新absolute identity・rank・gamma等の取得要求で止める。配置表公開後STOP。

## A-3：Track A原稿と最新完了証拠の差分

- 対象：PR資料をread-only参照し、Evaluationでhandoff可能。入力：[A03][A04][A11]、後続[A01][A02][A05]–[A10]。
- 作業：v0.4の過去「未取得」を後続証拠へ対応付ける変更候補一覧。DF/control/metric/標本/selection条件を保持し、本文に採る科学表現は決めない。
- 成果物：原稿箇所・旧証拠・新固定証拠・残る限定・要判断事項の表。最新結果の統合原稿や新図は作成しない。
- 承認：過去の原稿整備・計算完了は新解析の承認ではない。本カード開始には次のユーザー指示。B/D単価の費用統合・選抜・再会計は別の明示承認を要する。
- 依存・STOP：外部scopeの混合、母平均保証への飛躍、new2の別原稿への無照合同定、PR最新branchの書換えをしない。追加science/重要レビューが必要なら判断を返す。差分表公開後STOP。

## A-4：旧高次PF原稿の版と公開証拠の同定

- 対象：Evaluation。入力：[M01]、[local inventory](local_publication_inventory.json)とユーザー指定の正式原稿版・公開可能なsource。
- 作業：既存PDF/TeX/図のidentityと既知公開版との関係を確認し、第一/第二研究との対応・未対応を記録する。editorial判断は代行しない。
- 成果物：版/source/図の対応表、公開可能範囲と未確認点。非公開レビュー・指示・editorial原本は公開しない。
- 承認：最小identityを超える私有原本の公開は今回未承認。対象版と開始範囲をユーザーが別途指定する。
- 依存・STOP：認可未確認の原本公開、LaTeX build、係数修正、数値再解析・compileには進まない。対象版不明なら不足入力を具体的に返してSTOP。

重要科学レビューの開始、科学契約・grant発行、原稿執筆、投稿、研究の正式状態変更は、どのカードにも含めない。既存結果に基づく文書作業も、本作業の完了後に自動開始しない。

<!-- fixed-source-index -->

[A01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/621d7d7bed183862db8d9f01b6fdb4406f942309/docs/research/track_a_h4_h8_cross_system_evidence_inventory_20261017.md
[A02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/docs/research/track_a_research_handoff_20261018.md
[A03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/docs/manuscripts/track_a_resource_study_geometry_native_v0_4.md
[A04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/docs/manuscripts/track_a_h4_b0i_v0_4_scientific_review_handoff.md
[A05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/839c403004cf9343730c43adb346024aea41999b/docs/research/track_a_h8_ab_20261018.md
[A10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/7e454b91185ed7b0f92a3790f800ba5d65d5f156/docs/research/track_a_pr_theory_vs_compiled_completed_20261018.md
[A11]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/2c22c8edad6a497240f57f8654da3778c0df1fdd/artifacts/resource_applicability/track_a_h4_b0i_manuscript_integration/2026-10-14/README.md
[M01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/Evaluation%20of%20gate%20numbers%20for%20ground%20state%20energy%20calculations%20using%20higher-order.pdf
[S03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/PF_first_study_paper_claim_ledger_20260926.md
[S04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/evidence/paper_evidence_matrix.md
[S05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/figure_captions.md
[S06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/figures/paper_figure_manifest.json
[S08]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/evidence/paper_source_manifest.json
[T01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[T05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[T09]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d26aa812226819c406d6ce645dbb3c1056b0e8ee/paper/study2/figures/figure_manifest.json
