# 第2研究の成果整理版 — 2026-10-05

承認済みDirection Cに沿い、凍結済みscalarだけから3主図・caption・claim–evidence台帳・
先行研究差分表を作成した。新規科学計算、主解析再実行、再fit、再採点、policy変更は0。
原本数値は既存主解析CSVのままで、図用JSONは表示traceである。

## GPTが読む順序

1. [承認反映した方針・RQ・claim scope](approved_scope_and_rq.md)。
2. [結果統合：Table 1と3主図](result_synthesis.md)。
3. [詳しいcaption](../../../paper/study2/figure_captions.md)と[claim–evidence台帳](claim_evidence_ledger.md)。
4. [先行研究role map / 差分 / access scope](related_work_delta.md)。
5. [原稿構成と概要案](manuscript_outline_and_abstract.md)、[未確立事項](outstanding_claims.md)。
6. [原数値report](../../../artifacts/budget_safety_mechanism_20261005/report.md)と[source registry](source_registry.json)。

ユーザー/GPTが承認した原文は[approved_gpt_review.md](approved_gpt_review.md)。
公開identityは後から追加するpublication handoffで示す。
[COMPLETE](../../../artifacts/study2_result_synthesis_20261005/COMPLETE.json)と
[focused検証log](../../../artifacts/study2_result_synthesis_20261005/focused_test_log.txt)は本成果版の検証記録。
原文内の「未commit」は作成時点の記録を保つ。

## 数値・図・証拠の位置

- [既存主解析artifact](../../../artifacts/budget_safety_mechanism_20261005)がauthoritativeな数値source。
- [最終figure bundle](../../../paper/study2/figures)はPNG/SVG/PDF、元CSV行に対応したdisplay data、自己除外manifest。
- [図表仕様](rendering_spec.md)は単位・並び・欠測・丸め・軸設定を明記。
- [描画コード](../../../review_response/render_pf_study2_result_synthesis.py)と[focused tests](../../../review_tests/test_pf_study2_result_synthesis.py)は科学runnerをimportしない。

Origin/result commitとverified snapshot commitを別fieldで照合する。
元41 source registryと原本manifestは変更しない。
MehendaleはarXiv v3の該当本文と出版書誌を確認したが、出版本文固有の追加記述は今回Codexで未確認。
他文献も本文確認とabstract確認を分ける。新方式を実装した外部baseline比較ではない。

## 検証コマンド

このworktree内で、既存venvを使ったread-only検証：

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/abe/myproject/Evaluation_numGate_highorder/venv/bin/python -m unittest discover \
  -s review_tests -p test_pf_study2_result_synthesis.py -v
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/abe/myproject/Evaluation_numGate_highorder/venv/bin/python \
  review_response/render_pf_study2_result_synthesis.py --verify-only
```

描画そのものは3形式を作る表示処理で、science acquisitionではない。
既存figuresへの上書きは拒否する。検証だけなら--verify-onlyを使う。
別環境でのvenv再構築やpackage変更はこの手順の一部ではない。

Focused testsと表示照合が通ったことをrepository全体greenとは記録しない。
元H8 legacy/full-suiteの未解決事項は原本のまま。
今回の停止点は成果版のGPTレビューであり、新科学計算の開始ではない。
