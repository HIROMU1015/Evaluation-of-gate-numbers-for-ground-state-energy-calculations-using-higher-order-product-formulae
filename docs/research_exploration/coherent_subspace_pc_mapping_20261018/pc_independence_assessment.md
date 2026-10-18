# P-c独立性の技術判定

2026-10-18 JST。**主分類：B（既知法の具体的な特殊化・既知手順の組合せへの還元）。** 同じ有利な入力条件を許した対照に対し、Gだけに残る生成・選択・取得・保証・費用mechanismは確認されなかった。研究の正式採択／CLOSED／PAUSEDや、独立した科学的新規性の最終審査は行っていない。

## 1. Bの根拠

単に「QSEに属する」と判断したのではない。次の三つを具体的に閉じた。

1. **生成の再現。** 係数支持の加算→最大重みKruskalの全union列→single linkage hierarchy→occupation countの全threshold、という有限古典処理へDを分解した。両者で実際に生成する場合の費用も等しく計上した。
2. **選択結果の再現。** coherent cellをpiecewise diagonal関数／projector QSEのoperatorとして表し、同じ全候補matrix、同じ有限class confidence、同じinterval gap、同じoperation-count proxyを計算した。ratio greedyと固定tieを適用すると全更新列・終了理由が一致する。
3. **取得費・分布の再現。** Gのraw記録と既知VQNHE配置対測定のrecordを、ψを使わないbit変換と公平coinで相互対応させた。Hermitian後の一標本matrixとC_addの統計はorientation非依存なので、実際の意思決定にはcoinも不要。同じm_H/m_Sでjoint distribution、cross-covariance、confidence、選択結果を再現できる。

導出は[操作対応](pc_known_method_mapping.md)K1–K5と[情報・費用](pc_information_and_cost_comparison.md)I1–I5。どれも手計算の仕様照合で、計算機による科学検証・独立形式認証は行っていない。

## 2. B1–B4への回答

| 問い | 結果 | 残すべき境界 |
| --- | --- | --- |
| B1：Dに独立の生成機構があるか | 同じ係数処理とordered forest／thresholdで同じDが得られる。Dを入力として許せば独自取得はさらに残らない | この特定dictionaryを電子問題へ使う全手順の過去の初出までは特定していない。用途の初出未確認を生成機構の差としない |
| B2：選択を再現できるか | 同じspace・matrix・幅・costから同じg_L/C_addと更新列・STOPを再現できる | 無変更のVQNHEのneural訓練、SSEのtop-K filterやregularizationがliteralにGと同じとは言わない |
| B3：測定情報は本当に同費用か | 理想の既知配置対測定とGの対応は同shot・同seed準備回数。Gの意思決定matrix族の分布・分散まで対応する | native gate価格・noiseは未測定。標準local shadowsは同じrecord lawでなく、そのまま同shotと扱えない |
| B4：費用と保証に差が残るか | D構成、全候補評価、記録storage、confidence、人口conditioning、state出力費を同じ範囲で数えるとG固有差を特定できない | 既知対照のよりよい測定law、grouping、cache等を禁止してGを勝たせない。一方、それらの最適費用を今回求めたわけでもない |

## 3. なぜliteralな差をA判定にしないか

SSE原法はPauli poolの2次元filter、Gは現tree全体のleaf splitであり、選択結果は一般に違う。Gはconfidence下界を使い、原SSEのGram eigentruncationを使わない。adaptive measurement QSEの測定配分更新とも異なる。

しかし、この差は、同じpredicate classへ既知QSE solveを行い、既知の有限class confidenceとinterval比較、cost-ratio greedyを使う手順で再現できる。Gだけに新しい測定や未知の生成operatorが必要になるわけではない。結果の違いを作る特定のheuristic設定があることと、同じ有利な情報を許した既知手順では再現できないmechanismがあることを区別する。

既知部品の組合せが常に新規成果にならない、という一般論は採っていない。今回のGには、その組合せから得られる新たな効率保証、候補探索数の削減保証、強い対照とのstatistical separation等が定義・証明されておらず、操作の明示的再現にも残差がなかった。この範囲でBとする。

## 4. 限定的障害と未確認事項

以下をBの判定から切り分ける。

- 標準local-shadow recordへGのcount predicateを移すと、人口observableだけでも通常estimatorの分散が大きくなり得る。情報・費用文書§5はこの限定的な測定差を示す。全SSE変種の障害でも、VQNHE対照に残るGの優位でもない。
- g_L/C_addは、全候補をscreenした費用を回収する最適化定理ではない。C_addはproxyであり、原Gは全screening費を別途足している。ratioを採用するだけでは総測定費・古典費の改善は証明されない。
- Gの目的とtree classについてsubmodularity等を認定していない。既知cost-aware greedyの近似率・lazy評価保証を適用しない。この欠落を埋める別構成はP-cの範囲外として行わない。
- forestのzero edge、有限bitの係数比較、solver・tieの規約は固定Gの未指定部分が残る。両者で同じ規約を使う各場合について還元する。Gだけにexact arithmeticを無料で与えない。
- hardware noise・native/routing費、全先行論文での同一組合せの掲載、最適cost等は未確認。これらから別の独立機構を推測しない。

従って局所的なC/D事項はあるが、**主たるP-cの操作上の再現性がDのまま残った、という結果ではない**。上の分布対応と手順対応でBを判断する。世界的なpriorityや有用性の査読判定までは主張しない。

## 5. P-dへ進む根拠

**今回のP-cから、独立候補GのP-dを開始する根拠は得られなかった。** 関数classの有用性や特定dictionaryの実験的価値が一般にない、という結論ではない。ユーザーがそれを別の評価研究として選ぶかどうかは研究判断であり、今回は提案された連結familyの構成・近似保証・数値実験を開始していない。

ユーザー／GPTへ戻すのは、このB判定を受けて現Gを構成ノートとして区切るか、正式な研究状態をどう扱うかの判断である。今回の作業だけでCLOSED/PAUSEDや新しい候補採択を記録しない。未確認native費やpriorityを理由にCodexが無制限の探索・追加検証を続けることもしない。
