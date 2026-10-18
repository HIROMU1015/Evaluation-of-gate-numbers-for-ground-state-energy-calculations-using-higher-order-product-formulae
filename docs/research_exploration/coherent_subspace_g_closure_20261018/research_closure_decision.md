# 現G探索の正式CLOSED判断

2026-10-18 JST。**正式状態：現G探索 CLOSED。独立新アルゴリズム候補：NOT RETAINED。技術的根拠：P-c＝B（既知手順への還元）。P-d：未実施・未判定。**

## 承認の出所と記録の役割

本決定の出所は、この作業を直接依頼したユーザーの「Codex作業指示：適応的部分空間生成規則Gの正式CLOSED記録」（2026-10-18 JST）である。同指示は、ユーザーが研究判断を承認済みであることを明示し、次を指示した。

> 現Gを独立した新アルゴリズム候補として保持しない。
>
> 固定されたG構成の新規アルゴリズム探索をCLOSEDとする。

併せて、構成結果・既知法への還元を研究記録として保全し、P-dの追加構成・数値検証へ進まないことが承認された。**Codexはこの承認済み判断を記録する担当であり、新しい終了判断や重要科学レビューを代行していない。** 別のGPTレビューの実施日時・結論・承認原本を推定して補わない。

## 対象の固定

| 項目 | 決定 |
| --- | --- |
| 対象 | 初期構成commit `7bbcc6c35a3d53bcdbbf720526c5cae0d885c7cd` に記述され、P-c commit `793cd63089dea8ca3e66b8c7faba173a198530eb` で照合された具体的な規則G |
| 終了する作業 | その固定Gを独立新アルゴリズムとして保持・継続する探索 |
| 保持するもの | 係数dictionary、coherent cell、共通測定、confidence、費用付き選択・STOPの構成記録と還元記録 |
| 追加検証 | 現G継続の根拠が得られなかったため進まない。P-d、改良heuristic探索、計算・実装を開始しない |
| 対象外 | QSE、QSCI、VQNHE、coherence保持部分空間法全般、他の構成・研究系列 |

固定Gの記述上の未指定規約を今回補完・最適化しない。特定dictionaryの有用性や研究分野全体の可能性を否定した決定でもない。

## 判断根拠

初期構成はP-aの紙上成立、P-bの独立性不成立、P-cの未確定、P-dの未証明を残した。その後の[P-c独立性判定][pc-assessment]はBを記録した。同じHamiltonian、seed/access、dictionary、候補class、測定情報、confidence、費用・tie規約を与えると、既知の係数graph処理、VQNHEのpiecewise complex F、projector QSE、confidence・interval比較・cost-ratio選択の組合せでGの全更新列とSTOPを再現できる。

[測定・費用比較][pc-information]は理想モデルでの配置対測定とGの意思決定統計の対応も記録する。一方、SSE原法の標準shadow分布・filter・regularizationがGと異なる点は維持する。具体的な独立生成機構、独立保証、資源優位は確認されていない。このB判定を根拠に、ユーザーは現Gを独立候補として継続しないと判断した。

これは全先行研究のpriority認証、全実装の同等性証明、P-dや絶対E0保証の不可能性証明ではない。[未解決事項と適用範囲](remaining_questions_and_scope.md)を変更しない。

## 過去記録と他系列の保全

旧packetの「正式状態変更なし」「ユーザー／GPTの判断待ち」は、その作成時点の記録として保持する。今回の承認により新たに現Gの正式状態を定めるのであり、旧SOURCE・provenance・receiptを遡及して変更しない。機械可読な現在の決定は[decision.json](decision.json)に限定して記録する。

J1・Q1のPAUSE、R1-Pの独立候補不保持、集団遷移生成のPAUSED、SOS-PF A2のNOT_ADOPTED、第一・第二研究、PR Track A/Bおよび他系列の正式状態は変更しない。D1の既存制約とD2の元の有限基底電子Hamiltonianの絶対E0を保持する条件も維持する。

**公開・照合後にMandatory STOP。** 次の研究方向の選択はユーザー／GPTが別途判断する。今回から派生する科学作業・レビューの実行承認はない。

[pc-assessment]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/793cd63089dea8ca3e66b8c7faba173a198530eb/docs/research_exploration/coherent_subspace_pc_mapping_20261018/pc_independence_assessment.md
[pc-information]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/793cd63089dea8ca3e66b8c7faba173a198530eb/docs/research_exploration/coherent_subspace_pc_mapping_20261018/pc_information_and_cost_comparison.md
