# 第2研究の図表作成仕様

基準snapshotは bfe715fc1c04325535a3c4d63ea4584e691dc322。
Authoritative numerical resultsは artifacts/budget_safety_mechanism_20261005 の既存CSVである。
[Source registry](source_registry.json)はorigin/result commitとverified snapshot commitを分離し、
元41件registryもそのまま参照する。GPT原文はユーザー提供のgovernance sourceで、
実験結果commitを捏造しない。

## 表示と入力

[描画コード](../../../review_response/render_pf_study2_result_synthesis.py)はstdlibのCSV読取とMatplotlibだけを使う。
Trotter実装、分子入力、runtime、pickle、matrix、vector、unitary、exact stateは開かない。
PF/H action、Arnoldi、ground/direct/gap、GPU、新fit、再採点、主解析再実行は0。
表示の単位変換と保存値の算術照合は実行する。

Figure 1はHF2条件とH-chain6条件の保存B2 actionを抽出する。
同じcoordinateとbudgetでH1およびfixed1.01と一致することを確認する。
U=e-cを負のまま保存し、M-Uをslackとして使う。gamma1のratioは作らない。

Figure 2の座標順はHF eq、HF stretch、H2/H4/H5/H6/H7/H8、HCl eq、HCl stretch。
各条件の元候補3点をabsolute time昇順で並べる。各groupの中央にcondition名を表示する。
HF/H-chainの同時刻参照はgamma1.01、HClはmain gamma1.02である。
Unsafe HF eqの1.6T0はheadroom/windowをnullとして、数値点を打たない。
Shadeと「undefined」は欠測の注記であり0%の点ではない。
Panel dだけは保存された最終actionのB/B0で、同時刻headroom比較に混ぜない。
HClに新しいselectorを適用しない。

Figure 3はidentity確認済みH-chain18座標のみを示す。
H2の丸め域はlinear、他はpanelごとのsymmetric-logで符号を保持する。
軸transform/linear-region幅は表示設定であり科学thresholdではない。
HF/HCl12点は未確定のまま。Closure roundingとphysical errorを混同しない。

## 出力と検証

PNG/SVG/PDFの3形式で3主図を出力する。English図中文字は移植可能なDejaVu Sansを用い、
日本語captionを別Markdownにする。Figure dataはCSV行番号、元row、表示値を対応付ける
plot provenanceであり、新しいauthoritative result tableではない。

Rendererは原本を上書きしない。凡例重なり・軸余白・zero付近のtick重なりを直した表示draftは
paper/study2/figure_draft_1 と figure_draft_2 にrecoverableに保持し、commitしない。
図用scalar dataは同じで、tick間引きは表示だけの変更。主解析は再実行していない。
最終版のみ公開する。Figure manifestは自分自身を除外する。

[Tests](../../../review_tests/test_pf_study2_result_synthesis.py)はsynthetic gateとread-only scalar検証だけ。
CSV row pointer 200件、Decimal50での単位変換、unsafe/missingの扱い、rank/abstention維持、
sourceのorigin/snapshot byte一致を確認する。PNGを目視し、ラベル・凡例・clipを確認する。
Legacy molecular/full testsは実行せず、過去のfull-suite不合格を修復したとは主張しない。
