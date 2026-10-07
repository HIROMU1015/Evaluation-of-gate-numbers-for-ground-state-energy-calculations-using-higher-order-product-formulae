# 全面再構成版の改訂記録と出典確認

改訂日：2026-10-07。文書の差し替えに関する記録。

ユーザーが採用した添付構成案を、[構成案本文](lab_progress_slide_outline.md)へ反映した。本編29枚・補足3項目から、本編46枚・補足8項目へ置き換え、投影用の「スライド本文」と発表者用の問い・口頭補足・つなぎ・出典を分けた。採用した文章、表、数式、数値、研究の位置付けは添付から変更していない。改行コードだけをCRLFからLFへ揃え、改訂日行のMarkdown改行用の末尾2空白は保持した。

## 1. 入力と今回の作業範囲

| 項目 | 記録 |
|---|---|
| 差し替え前の公開構成案 | `be747ad19003ef17d8f40f0a3e2e1ba9b6ebb039` |
| 差し替え前の構成案SHA-256 | `c26f8c8cb0a232c73bfe1fb245a95e40de5e0675454ba69817b57c0634909e01` |
| 添付原本SHA-256 | `6810bf320074ee49a0931bc6790e2910a3e09190d434952172615930d3017f8d` |
| LFに揃えた添付・採用本文SHA-256 | `e3aee437a8dd55d696ecef4237d7ffba91fd6d82e223d7c9c36ac867eebf5dae` |
| 公開資料 | 本文、改訂記録、文書監査コード・JSON・manifest |
| 新規科学計算・fit・正式分類の変更 | なし |

IDEで編集されていた差し替え前の本文は、上記公開commitの本文と同一だった。過去22件のコメント対応や保存値監査を作り直さず、その公開履歴を起点にした。別作業の未追跡ファイルには変更を加えない。

今回Codexが確認したのは、添付との一致、番号・タイトル一覧・各欄・表・数式区切り、文書内アンカー、相対リンク、指定commitでのGitHub参照先blob、sourceのhashとmanifestである。添付冒頭やE22・E24の「確認した」という記述は、添付の作成者が記した確認内容として保持した。今回の文書編集で過去の科学監査を再実行したという意味ではない。元論文のWebページも今回再取得していない。

FS-C0.6以降のsource再構成に関する別チャット向け指示は、この資料改訂の対象から除いた。follow-upの説明は、採用本文が参照するE22の固定snapshotにおける設計・開始前判定の説明として保持し、別作業の進捗を混ぜて更新していない。

## 2. 旧29枚との対応

本文冒頭の「本編タイトル一覧」に新番号から旧番号への対応がある。下表は逆方向の参照であり、旧ページにあった説明を新しいページへ分けた位置を示す。

| 旧Slide | 新Slide |
|---|---|
| 1 | 01 |
| 2 | 02 |
| 3 | 03, 08 |
| 4 | 04 |
| 5 | 05 |
| 6 | 06, 07 |
| 7 | 08, 09, 10 |
| 8 | 13 |
| 9 | 14, 16 |
| 10 | 14, 15 |
| 11 | 17, 18 |
| 12 | 19 |
| 13 | 10, 20 |
| 14 | 11, 12, 19 |
| 15 | 21, 23 |
| 16 | 22, 23 |
| 17 | 23, 24 |
| 18 | 25 |
| 19 | 26, 27, 28 |
| 20 | 29 |
| 21 | 30, 31 |
| 22 | 32, 33, 34 |
| 23 | 35, 36 |
| 24 | 37 |
| 25 | 38, 39, 42 |
| 26 | 40, 41, 42 |
| 27 | 43, 44 |
| 28 | 45 |
| 29 | 42, 46 |

補足は、手順の違い、信号判定と旧ラベル、安全余裕、状態品質、固有枝、元格子と局所格子、別protocol、予備比較と計画の8項目へ整理された。実験ごとに異なる分母・候補集合・参照情報を混同しない説明を補足へ置いている。

## 3. 既存結果の統合と出典

採用本文は、保存済みA1/A3/A6/B3をそれぞれ短時間比較（Slide 17）、H6固有成分（Slide 28）、H4局所時刻（Slide 23）、HF上限0.75（Slide 33–34）へ反映した。今回、新しい条件拡張や再採点は行っていない。

各sourceのorigin/resultの記録と今回指定されたverified snapshotは、[source registry](../../../artifacts/lab_progress_full_restructure_20261007/source_registry.json)で分けて保持する。以前のE01–E25のoriginと確認版の記述も、[旧source記録](../../../artifacts/lab_progress_full_restructure_20261007/previous_source_records.json)に原文のまま残した。E17–E19の共通science result originは`8436a2f3644e0403ff5ebf19bee6caae364ae66e`で、本文が参照する`19362c23ccdc16b6ad0ff547cc363e138a3930d2`は確認snapshotである。同じblobでもこの二つの役割を統合しない。

本文のE25は、採用した添付に固定commitが記載されていなかったため、その説明を保持している。今回の版管理確認では、以前の22件コメント対応が以下のcommitに含まれることを確認できた。この別紙で固定参照を補い、採用本文の文章は書き換えていない。

- [差し替え前の29枚構成案](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/be747ad19003ef17d8f40f0a3e2e1ba9b6ebb039/docs/research_outcomes/20261006/lab_progress_slide_outline.md)
- [22件コメントの対応](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/be747ad19003ef17d8f40f0a3e2e1ba9b6ebb039/artifacts/lab_progress_inline_comment_audit_20261007/comments.json)
- [その時点の保存値・文書確認](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/be747ad19003ef17d8f40f0a3e2e1ba9b6ebb039/artifacts/lab_progress_inline_comment_audit_20261007/checks.json)

これらは履歴に保持し、46枚の文書に旧29枚用の監査を再適用しない。

## 4. 採用本文に残した限定

- H4・H6の信号判定成立ケースと、元の全56ケースの分類ラベルを分ける。信号判定不成立は計算漏れやゼロ誤差を意味しない。
- H4の局所時刻細分化は保存格子の近傍だけを評価したもの。連続時間全体の最小費用を確定した結果にはしない。
- H6の固有成分分解は枝を確認できた別の固定点に関する結果。元の選択時刻の正式な未確認判定を変更しない。
- HF上限0.75と1.0/1.8の不足を同一の原因へまとめない。既存閾値・上限の最適化にはしない。
- 開発6条件の精度達成を、未知分子への独立保証へ広げない。
- 同じPF・時刻での状態改善、時刻の再選択、予算の安全性、追加情報の費用を別々に扱う。
- 第1研究follow-upの2×2比較は、参照したE22時点では開始条件が未確定の計画。第3研究も条件付きである。

## 5. 読む順序と文書確認

[構成案本文](lab_progress_slide_outline.md) → 本記録 → [確認結果](../../../artifacts/lab_progress_full_restructure_20261007/checks.json) → [source registry](../../../artifacts/lab_progress_full_restructure_20261007/source_registry.json)の順で確認できる。GPTへの引き渡しは、今回の公開branchと40文字commitを最終回答で示す。manifestは自身をhash対象から除外し、その理由を明記する。

ユーザーが採用した構成・文章を反映する作業であり、新しい研究判断は加えていない。次のレビューでは、46枚の順序、投影用本文の長さ、説明の重複を確認できる。未確認の科学事項を解決したという追加claimはない。
