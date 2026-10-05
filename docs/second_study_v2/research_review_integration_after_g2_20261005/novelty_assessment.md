# 新規性の扱い — G2追加による限定

[旧新規性レビュー](../research_direction_review_after_hchain_20261005/novelty_assessment.md)の一次文献role map、版、限定的scope比較を継承する。今回は新しい文献検索・一次論文の再照合・外部baseline実装を行っていない。`novelty_external_verification_required=true` を維持する。

G2が加えるのは、同じ保存HF候補・fixed rule・freeze/scorerの境界でcheap stability gateのfalse negativeを記録したこと。これは具体的な反証可能性と再現性を補強するが、Arnoldi、cheap proxy、adaptive calibration、selective acquisition一般、value-of-information一般の新規発明ではない。

守れるcontribution候補は、固定finite-time PF-QPE contractにおける、point精度・width/abstention・safe quantum decision・fixed cheap対照・information costの分離評価である。第一研究loss -> decision window -> 追加情報の価値という接続を中心に置く。

まだ使わない表現：

- 「初めてのresource-aware calibration framework」
- 「cheap stabilityが安全性を保証」
- 「spectralが不可欠／常に不要」
- 「validated selective algorithm」「汎用regime map」
- 「combined H1 costを減らした」「end-to-end quantum advantage」
- 「HF 2条件のreplayが独立holdout validation」

Noveltyの最終判断と投稿前の最も近い先行法との照合は人間レビュー後の別作業。G2のnegative resultだけで新規性が確定したとはしない。
