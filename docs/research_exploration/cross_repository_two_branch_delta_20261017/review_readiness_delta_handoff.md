# GPT／ユーザー向け：最新2ブランチ差分handoff

2026-10-17 JST。**今回の差分資料の目的は、レビュー前の情報欠落と重複を解消すること。科学レビュー・採択・追加探索は行っていない。** 保存先はEvaluation、branch `qc-cross-repository-two-branch-delta-20261017`、親は既存横断整理 `609a63231ee0786cf8da31f6b33358acfd6f2548`。新規7資料だけを追加する。

読む順序：本書 → [2ブランチの結果・条件](pr_latest_two_branch_delta.md) → [重複の仕様比較](updated_overlap_implications.md) → [状態と承認の差分](updated_active_and_pending_map.md) → [SOURCE registry](source_registry.json)・[静的監査](static_audit.json)・[provenance](provenance.json)。旧[横断handoff][O01]・[マップ][O02]・[PR20方向][P02]は変更せず、必要に応じて併読する。

## 1. 前回から新しく判明した事実

- **PR④ A2関連**：`051df4661eeffb6c6c4c978f70f43eeeaadfddd6`（payload `f70acc51644f43fc35ad73edfdc3f180a9ce1f4f`）でRF0、RF1/K0、energy window、固定powers QPE/stepの限定技術監査が公開された。分類は **VALID_WITH_UNRESOLVED_NOVELTY**。明示条件内の紙上成立性という保存判定であり、新規性・採択・費用優位の認定ではない。[A01][A02][A03]
- **旧L05の取得不足は解消**：[GPT再設計レビュー原本][A06]は公開済みで、旧観測と同じ38,606 bytes・SHA-256 `954bd40d1da7dce70a4b97336c71d1cd55031314df9c339a2de95b82fabf8527`。現在も「未公開ローカル原本」とは記述しない。採択は別問題である。
- **PR① H8**：`ce6cd8ead5c0311ec72165c04869e7df4050b75b`で強対照3構成cosine/sine計6軸の直接compile完了を取得。固定RZモデルとの保存相対誤差は約0.216–0.827%、全6軸PASS。旧SOURCEの1軸再利用、新SOURCEの5軸という来歴を分離した。**PR削減率は未更新**。[B01][B03]

## 2. 新たに具体化した重複可能性

A2とEvaluation R1-PはPSD、有限step、低energy情報、強対照と情報取得費の問題で接する。ただしR1-PはA+下のRichardson信号のrestricted norm保証、A2監査は共通不変sectorの全vector Loewner相対log保証とground支持入力のwindowである。**同値・包含・数学的独立性は今回判定していない**。[E01][E02][E03][A02][A03]

第一・第二研究の経験的safe、枝shift、width、budget marginとは問題領域で接するが、A2の厳密条件充足を示す証拠ではない。H8の6軸は価格モデルを補強し、Evaluationのcontinuous proxyやPRの総E0評価とは異なる。H8 S4の負stageにA2の正stage S2保証を適用しない。

## 3. 既存マップの補足点

PRM04/16は「保証一般が未解決」ではなく、公開監査の正確なstatementと最強既知保証との対応・実用性が未確定と書き分ける。PRM14/10はH8登録6軸の実測証拠を追加する。PRM05はRichardsonと単一S2の相対logを分ける。PRM15は固定powers QPEの接続条件を記録し、多roundRPE・準備/証拠/native/readout込み総費用が未確立であることを保持する。既存20方向は再作成していない。

## 4. 戦略レビューで注意すべき未確定事項

A2の全statementの既知還元/非還元、網羅priority、実用定数、有用h、認証W/Λ/K_SOS、古典certificate bit費用、state準備・controlled native実装・readout込み優位は未確定。exact groundや下界を無料入力にしない。単stepのoperator boundとE0出力task全体を直接比較しない。[A03]

H8のPASSは登録6軸に限り、full-grid実測最適、PR母平均優位、厳密bias、総E0優位ではない。新削減率・再ranking・新shot会計を作っていない。Phase Cと非相殺比較の旧結果・契約を保持する。[B01][B03]

A1現分割生成探索CLOSED、A2 NOT_ADOPTED、K1-F NOT_AUTHORIZED / NOT_EXECUTEDを維持する。R1-Pはユーザー承認済みの独立候補不保持NOT_ADOPTED。J1/Q1のPAUSE、他系列の状態も維持する。技術VALID/PASS、レビュー推奨、正式採否、科学計算実行承認を区別する。

## 5. 不可欠な未取得資料は何か

**今回の指定2ブランチを既存横断整理へ反映するための必須資料に未取得はない。** 固定SOURCE30資料をGit blob・bytes・SHA-256とcommit固定rawで照合し、旧L05と公開原本の同一性、H8公開projection hashも確認した。保存されている数学の独立認証やruntime全体の監査を行った意味ではない。

旧整理に残る別系列の未取得Claude原本等や、A2監査が記す補助abstract/全引用文献・出版版全体の未確認は、今回新たに取得済みとはしていない。詳しい読取り範囲はregistryにある。特定の過去判断を原文から再認証するレビューを別途求めるなら、その原本回収要否を先に指定する。今の固定scopeの戦略レビュー開始を妨げる欠落と、科学的に未判断の問題・費用未測定を混同しない。

## 6. レビュー前にCodexの追加回収が必要か

**今回の固定scopeを理解して次の戦略レビューの可否を判断するために、必須の追加技術回収はない。** 新しい詳細科学レビューの対象に応じた追加原典・runtime証拠の要求はあり得るが、それを今回自動開始しない。文書をさらに集めるだけではA2の新規性や総費用優位の判断は閉じない。

次の担当は**GPT／ユーザー**：既存正本と本差分を読み、詳細科学レビューを開始するか、開始する場合は対象claim・比較task・範囲を判断する。Codexの新計算・還元証明・追加探索・H8再会計は承認されていない。

## 7. 公開・保全・停止

新規branchを通常commit・non-force pushし、remote SHA、独立空bareへのfetch、7資料のGit blob・bytes・SHA-256・commit固定raw、旧10資料の同一性を照合する。自分のcommit SHAを自己参照するmanifestは作らず、最終40文字SHAと公開後照合は完了報告に示す。provenance manifestは自身を除外し、provenance自身も公開後の外部照合対象に含める。

開始前のEvaluation113件・PR184件の既存worktreeについてHEAD・branch・porcelain statusとstaged/unstaged diff digestを比較する。これは未追跡ファイル内容、ignored runtime、全共有環境の包括的監査ではない。PRには書き込まず、既存10資料と全既存tracked pathを変更しない。観測中の並行更新があれば今回の固定範囲へ取り込まず別途報告する。

D1を維持しblock-encoding/qubitization中心へ移行しない。D2では元の有限基底電子Hamiltonianの絶対E0を保持し、scalar・一体項・残余相互作用・モデル/実装誤差を省略しない。

新規科学計算、保存数値再解析、数値順位付け、証明/反例/symbolic checker、compile、詳細科学レビュー、研究採択、研究再開は各0件。

**Mandatory STOP：差分資料の公開・照合後にCodexは停止する。次の科学作業は自動開始しない。**

[O01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/future_review_preparation_handoff.md
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
