# P-c限定照合：GPT／ユーザー向けhandoff

2026-10-18 JST。**技術分類はB：Gの残る生成・confidence／費用付き選択は、既知手順の組合せとして再現できる。具体的な独立差分は残らなかった。** 正式な研究状態変更、独立新規性の科学的最終認定、GPT詳細科学レビューは行っていない。

## 1. 今回閉じたP-c

係数dictionaryは、支持の重み集計、ordered Kruskal／single linkage hierarchy、occupation-count thresholdの生成に分解できる。coherent cellはpiecewise diagonal関数／projector QSEとして表せる。同じD・記録・精度・confidence・古典費を対照へ認めると、同じmatrix、interval差g_L、C_add、g_L/C_add、固定tieから**全更新列とSTOPまで一致**する。

さらに、期待値の同一性だけではなく測定の分布を照合した。理想モデルでは[VQNHEの2種の配置対測定](https://arxiv.org/html/2106.05105v1)とGのancilla記録を、既知bit変換と公平coinで相互対応できる。Hermitian matrix標本とC_addの統計ではorientationが消えるため、意思決定にはcoinも不要。同じm_H/m_S、同じseed準備回数でmatrix族のjoint distribution、分散・相関、confidenceと選択結果を再現できる。これは今回の紙上導出であり、原論文がGそのものを掲載しているという意味ではない。

## 2. 原法との違いも残した

| 比較 | 確認したこと／しなかったこと |
| --- | --- |
| VQNHE | piecewise complex F＋QSEの線形係数solve＋既知のgraph/confidence/cost-greedy wrapperでGを再現。原論文のneural optimizerを無変更で走らせた結果が同じとはしていない |
| SSE | 原法のPauli top-K filter、Gram regularization、標準local-shadow recordはGと異なる。とくに任意count predicateの同shot・同処理費を仮定できない。同じD・取得情報を許すQSE wrapperとしてはGを再現可能 |
| adaptive measurement QSE | 原法の測定配分更新とGの固定record tree更新は別操作。固定した共通記録での再現を妨げる差ではない |
| classical手順 | Kruskal、有限class concentration、interval端点差、operation-count和、ratio greedyを明示して接続した。未知ground情報や新しい量子oracleを使わない |

Gの残る組合せは、今回の仕様では探索heuristicと既知の統計・線形代数の接続である。強い対照で再現できない生成・取得・保証のmechanism、資源削減の新しい定理は確認できなかった。全く同じ組合せの過去の初出を網羅確認したわけではない。

## 3. 限界とP-d

native gate／noise／routingの最適費用は未測定で、SSE全変種の同予算比較や全prior-art priorityも未確認である。これらはGの独立した改善を示す証拠ではない。Gのp_min・support・E0精度の課題も解決していない。

**独立候補GのP-dへ進む根拠は得られなかった。P-dの構成・数値実験は実施せず、開始しない。** 研究領域全体のNO-GO、Gの正式CLOSED／PAUSED、他系列の再開は判断していない。

## 4. 読む順序と検証

本書 → [P-c判定](pc_independence_assessment.md) → [全操作の対応](pc_known_method_mapping.md) → [測定分布・分散・費用](pc_information_and_cost_comparison.md) → [scope](scope_and_protocol.md) → [SOURCE registry](source_registry.json)・[文献provenance](literature_provenance.json)・[静的監査](static_audit.json)・[provenance](provenance.json)。前回packetはbase commitの履歴内で参照し、複製・書換えしていない。

必須14資料と横断／PR参照5件、計19資料のGit blob・bytes・SHA-256・固定rawを照合した。5件の一次HTMLは前回取得のhashを固定registryと再照合して必要節を再読し、追加のcost-greedy一次本文1件を限定取得した。forest/single linkageはpublisher summaryも確認した。Kruskal原PDF、Hoeffding原publisher本文と一部publisher取得は403で、本文取得済みとはしない。今回の具体的対応は紙上導出も併記し、未取得の定理を保証へ移していない。

静的監査は文書・Git・hash・参照・旧tracked状態の保全だけ。数学をプログラムで検査するテストではない。新規科学計算、保存数値再解析、symbolic checker、solver、回路build/compile/benchmark、新科学契約・grant、正式状態変更は各0件。

## 5. 公開と次の担当

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。branch：`qc-coherent-subspace-pc-mapping-20261018`。base：`7bbcc6c35a3d53bcdbbf720526c5cae0d885c7cd`。今回専用directoryだけを通常commit/non-force pushし、remote SHA・独立空bareへのfetch・全新規blob／bytes／SHA-256・commit固定rawを照合する。親payloadの公開receiptを子commitへ記録し、receipt自身を含む最終照合をチャットで報告する。manifestは自己除外し、循環参照を作らない。

**次の担当はユーザー／GPT。** この技術判定Bを受けて、現Gを構成ノートとして区切るか、研究系列の正式状態をどう扱うかを判断する。新しい比較研究・別候補が必要という方針変更もユーザー／GPTの判断であり、今回の承認には含めない。

**Codexは公開・照合後にMandatory STOP。** 既に承認された後続科学作業はなく、P-d、追加文献探索、実装、計算、正式採択・保留記録へ自動進行しない。
