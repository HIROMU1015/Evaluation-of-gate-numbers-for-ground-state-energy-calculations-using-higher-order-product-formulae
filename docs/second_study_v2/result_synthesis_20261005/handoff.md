# 第2研究成果整理版 — GPT review handoff

Status: `second_study_v2_result_synthesis_complete_review_required`。
承認済みGPT方針に従う資料整理であり、元のscientific formal resultを置換するstatusではない。

## 公開対象identity

- Repository: [HIROMU1015 / Evaluation]( https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae )
- Branch: `pf-second-study-v2-result-synthesis-20261005`
- Main-analysis base: `bfe715fc1c04325535a3c4d63ea4584e691dc322`
- Result synthesis origin commit: `1883d8a75d5dfe83052c52da24c079ddfde2aa2f`
- Verified result snapshot commit: `1883d8a75d5dfe83052c52da24c079ddfde2aa2f`（originと別field）
- [主成果31ファイルを含む固定snapshot](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/tree/1883d8a75d5dfe83052c52da24c079ddfde2aa2f/docs/second_study_v2/result_synthesis_20261005)
- Publication commit: このhandoffとpublication manifestを含むcommit。自己参照hashは埋めない。

本handoffはpush前に作成した記録である。Non-force push後のremote先端40文字SHAと
fetch/blob照合の実施結果は、Codexの最終報告を参照する。
Local commitだけでは公開済みとしない。Core snapshotはpublication commitの親で、
必要な元scalarはその履歴・同一treeに保持する。

## GPTが読む順序

1. [承認済みRQ・claim scope](approved_scope_and_rq.md)。
2. [成果統合と3主図](result_synthesis.md)。
3. [caption](../../../paper/study2/figure_captions.md)、[claim–evidence台帳](claim_evidence_ledger.md)。
4. [先行研究差分と確認範囲](related_work_delta.md)。
5. [原稿構成・概要案](manuscript_outline_and_abstract.md)、[未確立事項](outstanding_claims.md)。
6. [主解析原数値report](../../../artifacts/budget_safety_mechanism_20261005/report.md)。
7. [Source registry](source_registry.json)、[completion](../../../artifacts/study2_result_synthesis_20261005/COMPLETE.json)、
   [core manifest](../../../artifacts/study2_result_synthesis_20261005/manifest.json)、
   [publication provenance](publication_provenance.json)。

GPT側に確認してほしいのは、C1–C3の限定と根拠の対応、先行研究と重なる一般論を
新規性へ混ぜていないか、承認済み論文着地点に沿った原稿構成になっているかである。
新しいgateや追加科学計算の要否はGPT側で判断し、Codexはここで開始しない。

## 検証したこと

主図3点をPNG/SVG/PDFで作成し、CSV row pointer 200件とDecimal50単位変換を照合した。
Focused testsは31 passed、fail/skip 0。Source registry直接16項目と既存41項目について、
origin/resultとverified snapshotのGit blobs・hashを照合し、原本scalarは不変。
図のmarker・凡例・符号・欠測・axis clippingを目視確認した。
生成SVGの通常の行末空白と、byte-identicalなGPT原文のMarkdown改行空白を保持した。
それ以外の変更についてGit whitespace checkは合格した。

新PF/H action、Arnoldi、ground/direct truth/gap、再fit、再採点、主解析再実行、GPUは0。
Environment/package/driver変更、private runtimeの読取や公開も行っていない。
Rootのdirty/staged状態は作業前後で同じ。Local layout draft 2組は非公開のまま保持する。

## 残る限定

MehendaleのarXiv v3 technical本文と出版書誌は確認したが、出版版本文固有のN2追加などは
今回Codexで独立に確認できていない。GPT原文の確認報告とは区分してある。
他文献も本文範囲とabstract範囲を分け、外部法の同条件実装比較としない。

未知系safe policy、一般spectral不要性、state/rank因果、HF/HCl energy分解、
q=1 combined/cold cost、end-to-end advantage、certificateは未確立。
旧H8 legacy/full-suite問題をfocused testsで解消したとはしない。

停止点は成果版レビュー。元のprediction、truth、budget、formal decision、
historical no-push記録は変更しない。
