# H6 Track G — truth-only continuation review

Status: `hchain_h6_geometry_sweep_truth_continuation_complete_review_required`.

許可されたcontinuationを1回だけ実施し、新4 geometryのtruth **12/12点**を取得しました。
R=1.00 Åの既存truth **3点**をreuseし、固定predictionのまま5 geometryを採点しました。
H/CISD、reference、cheap、M1、groundの新規取得はすべて0です。Track Rは完了扱いのまま変更していません。

## 読む順序

1. [REPORT.md](REPORT.md) — 結果、計算履歴、限界、GPTへの確認事項。
2. [geometry_summary.csv](tables_figures/geometry_summary.csv)、[coordinate_diagnostics.csv](tables_figures/coordinate_diagnostics.csv)
   — 5 geometryのdecisionと15 coordinateの診断。全gammaを含む75行は[primary_scalars.csv](tables_figures/primary_scalars.csv)。
3. [geometry_safety.png](tables_figures/geometry_safety.png)、[M1_point_width.png](tables_figures/M1_point_width.png)、
   [PF_H_reference_decomposition.png](tables_figures/PF_H_reference_decomposition.png)
   — captionはREPORT内。線は表示上の接続であり補間truthではありません。
4. [truth/prediction.json](truth/prediction.json)、[analysis/prediction.json](analysis/prediction.json)
   — 凍結済みtruth原本とimmutable scorer出力。generic bundle schemaのためファイル名は`prediction.json`です。
5. [review_audit.json](review_audit.json)、[source_registry.json](source_registry.json)、
   [readiness/prediction.json](readiness/prediction.json)、[source_freeze.json](../../docs/second_study_v2/hchain_truth_continuation_20261006/source_freeze.json)
   — byte/hash、same-H/sector、sealed `.py` import、作用回数、前後test。
6. [authorization.json](../../docs/second_study_v2/hchain_truth_continuation_20261006/authorization.json)、
   [approved_scope.md](../../docs/second_study_v2/hchain_truth_continuation_20261006/approved_scope.md)
   — 今回の承認範囲。公開hashは[publication_manifest.json](publication_manifest.json)。

## 結果の要点

- B0とB1の4 gammaは、選択されたdecisionで全5 geometryが安全。
- gamma=1.01は全15 coordinateで安全。gamma=1の**post-hoc診断**だけはR=1.60の3点でunsafe。
- B1(gamma=1.01)は全geometryで`0.8*t_ref`を選択し、B0比のbudget削減は32.24–33.10%。
  固定時刻比の構造的寄与と安全性の実証を区別し、新方式の効果と解釈しません。
- M1 point errorはR≤1.20の9点でcheapより小さく、R≥1.40の6点では大きい。
  empirical width coverageは15/15ですが、rank8 M1は全15点で元のabstentionを維持。
- physical branchは15/15で一致。PF/H-reference誤差分解はsame-H・energy origin・physical branchを
  確認した15点に限定して閉じています。

## Commit identity / publication

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

Branch: `pf-study2-hchain-h6-truth-continuation-20261006`

| Role | Origin / result commit |
|---|---|
| Public recovery base | `1aad415bfaed5503508872c1fa5a8a8c12da4193` |
| Original failed Track G record | `e74fdec5e5085fd7c4f7a39fb4d59cec052f68f4` |
| Input freeze | `afbf22d063199ccc573c6664d7198acea1990a3f` |
| Reference / coordinate freeze | `cd5488902e46bc1320d6fc983f2d6e76d5aa4010` |
| Prediction freeze (unchanged) | `61ae95edce8c4a25167521c0e6e95a83c3cbc4bb` |
| Ground freeze (unchanged) | `1e5d66a4914bc50a8afa55baa578cca55a227979` |
| Continuation infrastructure | `d72105d50894319d93132d869ab3d36425b8f745` |
| Continuation source freeze | `916be0cc184368acebb4b1fe3ec1aefb5a1a6691` |
| Readiness freeze | `8c40bba6ab3fec5249c79e6c58473e7132984f07` |
| Truth freeze | `6acee8a5b61ae691460d3d8ec7ac2c6f137f7e9a` |
| Analysis freeze / verified scalar snapshot | `8d774a5a242d802ff6ae8f72ce3cd7152442c326` |
| Saved R1.00 truth origin | `5a9226a94fad0b578df1a53edd1a29e3571ad8c3` |
| Accepted Track R result (separate published branch) | `0c40a3d7987e0961262bfd38bbb214a9e2946824` |

Final publication commitは自己参照を避けてhandoff messageに40文字hashで示します。
そこではnon-force push、remote SHA一致、remoteからのfetch、必要blobを検証した結果も報告します。
過去の「失敗」「push未実施」は原本のまま保存し、今回の公開で書き換えません。

`.runtime`・matrix/vector・unitary・exact stateは公開対象外です。現在のbranchはscalarsと監査資料を
読むためのものです。別環境でのruntime再構築・科学計算再実行を承認するものではありません。

## 停止点

追加science、rank/gamma/gate修正、研究方針変更は行いません。
GPTには、このgeometry依存性をDirection Cの証拠へどう統合するかと、claimの限定が適切かを確認してください。
