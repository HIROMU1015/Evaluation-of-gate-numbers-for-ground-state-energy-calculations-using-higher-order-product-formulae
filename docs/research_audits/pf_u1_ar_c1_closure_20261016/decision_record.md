# U1-AR：C1完結と追加研究STOPの決定記録

**決定日：2026-10-16 JST。決定主体：ユーザー。** 本記録は今回の明示指示に基づく承認済み方針の記録であり、Codexによる新しい研究採択・仮説検証ではない。

## 1. 正式採択事項

- U1-ARを独立研究として追加追究しない。
- P1-A1〜A4を実施しない。
- U1-ARの追加研究をSTOPする。
- 既存成果を第一研究の限定的な理論補論（完結経路C1）として整理する。
- 新しい証拠と別承認がなければ再開しない。

本記録でのC1は**今回採択された限定完結の経路**を指す。既存paper claim ledgerの行ID `C1`を改訂・再定義したものではない。旧監査に残る「U1-AR/P1 GOは未判断」は作成時点の記録として保存し、現在の追加研究STOP方針をこの新規資料で記録する。旧監査の原文・statusを上書きしない。[HANDOFF] [CLAIMS]

STOPは研究方針の決定であり、「ARが存在しない」「P1実験で仮説が棄却された」という科学的結果ではない。P1-A1〜A4を未実施のまま、成功・失敗の結果を作らない。

## 2. 固定証拠と決定の根拠の区別

| 根拠 | 固定identity／確認した内容 | この決定での役割 |
|---|---|---|
| ユーザーの今回の指示 | 2026-10-16の承認済み方針と科学的制約10項目 | STOP・C1整理の直接の権限根拠 |
| U1-AR最新監査 | `7bbcdd405f49874f308a8abd433dae49cca5cd6e`の[handoff][HANDOFF]、[文献対応][LITERATURE]、[データ所在][DATA]、[定義監査][DEFINITIONS]、[provenance][PREPROV] | 既知文献との重なり、相手状態対応等の不足、枝・単位・warningの相違、未完了証明義務を記録 |
| 第一研究final synthesis | `7f0b30d215e8094c95ae895b9469a04180e2385e`の2026-09-25版 | S0〜S4完了、`complete_mechanism_study_no_method_benefit`、S4 `complete_no_benefit`を保持する基準。[SYNTH] |
| 第一研究paper claim ledger | `cd81018932b9557b7a55e2e1cd8c5e3988245409`の2026-09-26版 | development集合・資源proxy等の既存限定、中心claim、引用優先順位を保持する基準。[CLAIMS] |
| F02/F03/F05・HF等の既存結果 | 各原本reportとsourceを固定commitで参照 | 補論の局所係数・状態混合・proxy／枝の解釈に用いる。AR因果性の新しい実証にはしない |
| Claude再レビュー `レビューoutter(6).md` | **原文未取得・未確認** | 以下の修正事項はユーザーが提示した内容に基づく。Claude原文の逐語引用・節番号・証明を推定しない |

レビュー原文はworkspace・attachment・標準文書ディレクトリ等のアクセス可能なfilename検索と、監査固定commitのpath確認で見つからなかった。全保存場所に存在しないという主張ではない。旧監査の`レビューoutter(5).md`未取得記録とも区別する。原文取得を待たずにユーザー指定の修正を採用することが、今回明示的に許可されている。

## 3. 採用する科学的修正

| ユーザー指定項目 | 本資料・補論での扱い |
|---|---|
| 1：命題Rの一般形 | 「有限次の有効Hamiltonianは折り返し共鳴を一切表現できない」は誤った一般主張として採用しない。今回、撤回根拠を新しい反例・証明で作り直さない |
| 2：tau W_Sと2pi | `tau W_S >= 2pi`をTaylor発散・AR発生・PFモデル失敗の保証に使わない。W_Sの未確認定義を新たに確定しない |
| 3：実軸近接 | 実軸の位相近接を複素特異点や真のTaylor収束半径の直接証拠にしない |
| 4：F05 warning | 有限gridのOR判定をAR onsetへ改名しない |
| 5：未確立の機構 | 最近接PF相手状態、H4のRegime II、HF内殻励起仮説を確立結果として掲載しない |
| 6：枝規則 | X02のprevious最大とHF/NH3のground最大を明記し、unwrapも区別する |
| 7：摂動・混合・proxy | 非縮退・gap・局所展開・同一H/sector等の適用条件を添える。bare Hのgapと円周phase gapを置換しない |
| 8：MagnusとTaylor | 作用素logの級数の十分条件と対象固有枝のTaylor半径を別の対象として記す |
| 9：命題A/B/M/N/C | 未完了証明義務を証明済み独立新規定理として掲載しない。命題Cの原文も未取得で、内容を代作しない |
| 10：第一研究 | 既存限定claim・結果・S0〜S4の完了とS4否定結果を変更しない |

この表はユーザー提供の再レビュー修正を反映したもの。レビュー原文を独立確認した、あるいは数学的詳細レビューを完了したという意味ではない。

## 4. C1補論の範囲

[c1_theory_appendix_draft.md](c1_theory_appendix_draft.md)は、第一研究が使う対象量と解釈の限界を説明する独立草案である。扱うのは有限時間PFの符号付き固有位相shift、各sourceの枝規則、既知の局所摂動論、F02のa8混合、F03の相殺、F05/HFの限定結果、proxyと固有値の差、Magnus/BCHの十分条件の限界である。

新しいAR閾値・descriptor・判別法・普遍的収束半径・有限次数の不可能性定理を加えない。未完了証明を埋めるための新証明・反例・symbolic checkerも作らない。独立新規論文の成立証明や、第一研究の新しい成功claimとして扱わない。

草案を保存する承認は、既存本文への統合、既存claim ledgerの変更、外部投稿・出版の承認ではない。今回は原稿・図・captionを直接編集しない。

## 5. 再開条件

再開には、**新しい証拠があり、それに基づくユーザーの別の明示承認があること**を必要とする。新しい文献・原文・保存データの所在が判明しただけで自動再開しない。

別承認が将来与えられる場合には、目的、対象、既存成果との差、許可する情報・truth access、作業／計算上限、停止点をその承認範囲で確認する。これは今後の研究protocolを制定するものでも、未承認の実験案を準備しておく指示でもない。P1-A1〜A4仕様の復元・改訂・実行をToDoへ自動登録しない。

## 6. 不変な記録と保全

第一研究S0〜S4の完了、S4 `complete_no_benefit`、S5へ進まない既存決定を保持する。[SYNTH] [CLAIMS] 補論の理論的説明を使って否定結果を成功へ読み替えない。claim ledgerの行IDや数値も変更しない。

旧SOURCE、raw results/CSV、protocol/manifest、review原文、STOP、authorization、grant、ledgerは変更しない。**追加研究STOPはこの新規decision recordへ記録し、既存STOP markerを書き換えない。** U3/H05、第二研究、PR研究、R5探索、FS-R1その他の研究系列の状態・成果物を変更・再開しない。

新規branch `pf-u1-ar-c1-closure-20261016`、独立worktree、base `7bbcdd405f49874f308a8abd433dae49cca5cd6e`を使用する。新しくcommit・pushするのは本書、補論草案、[provenance.json](provenance.json)の3資料だけ。既存資料は固定commitで参照し、複製・再生成しない。

新規科学計算、保存値の再解析・再集計・再fit、新しい証明・反例構成、科学実装はすべて0件。文書の引用・リンク・byte/hash・Git差分・元workspace保全だけを検証する。公開後にremote先端SHAと固定GitHub commitの3 blobを再取得して照合し、その結果と最終commitをchatで報告する。

**Mandatory STOP：3資料の公開・照合後は停止する。研究再開、新計算、数学的詳細レビュー、本原稿への統合・投稿へ自動進行しない。**

<!-- fixed-source-references -->

[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[DATA]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/stored_data_availability.md
[DEFINITIONS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/definition_contract_audit.md
[HANDOFF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/gpt_decision_handoff.md
[LITERATURE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/literature_correspondence.md
[PREPROV]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/provenance.json
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7f0b30d215e8094c95ae895b9469a04180e2385e/PF_first_study_final_synthesis_20260925.md
