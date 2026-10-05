# 第2研究の承認済み方針と主張範囲

2026-10-05のユーザー承認に基づき、[GPTレビュー原文](approved_gpt_review.md)を成果整理へ反映する。
これは研究判断の実装であり、新しい科学的結果や実行許可ではない。
原文の「提案」「未commit」という記録は作成時点のまま保存する。

## 研究の中心

Direction Cを維持し、有限時間PF校正から凍結したQPE予算の信頼性と、
追加校正により資源を削減できる残余余地を扱う数値方法論研究としてまとめる。

Primary RQは次の通りである。

> 固定した有限時間PF-QPEの問題設定において、近似校正から凍結した予算の安全性と資源効率は、
> どの誤差要因・安全余裕・候補時刻に左右され、追加spectral校正は何を改善し、
> 何を改善できなかったか。

Secondary RQは、signed精度と絶対誤差過小評価の違い、cost-free oracleと実M1の違い、
同じHamiltonianとphysical branch上のPF/H-reference誤差分解を扱う。
Information costは保存されたstage会計に限定し、net advantageは達成済み部分に含めない。

## 三つの中心成果

1. 内部選択安定性やsigned点精度だけでは、指定uncorrected taskの凍結予算安全性を代用できない。
2. 安全な名指しcheap対照が残すoracle headroomと、M1のpoint・width・rank・採用制約を分ける。
3. H-chainの確認済みidentityの範囲で、shift精度とabsolute PF固有値回収精度を分ける。

slackの同値変形、Arnoldi、精度と資源の乖離一般、誤差相殺原理は新規性ではない。
差分候補は固定finite-time contractにおける上記の具体的数値評価の組合せである。
世界初・網羅的先行研究不存在・掲載可能性の保証は行わない。

## 方式の位置付け

| 対象 | 承認された位置付け |
|---|---|
| Fixed B1 gamma frontier | 主要対照。各固定armを残し、truth後の最小safe gammaをoperational方式にしない |
| cheap-first | 情報取得順序。未知条件でcheap safetyを保証する規則ではない |
| 現B2/H1 | G2反例を持つhistorical diagnostic。主運用方式として非採用 |
| M1 | 固定rank/reference/empirical width/adoptionの組。spectral法一般ではない |
| Truth oracle | 同時刻または元3候補内のcost-free改善余地。実現可能な校正介入ではない |
| C0 | 幅と必要情報の設計。厳密certificateの成果ではない |

H-chain約33%は主に固定時刻比とleadingモデルで説明されるbenchmark比較で、
adaptive/selective独自の改善とは呼ばない。
情報一般の害ではなく、実装した推定器・幅・採用規則の組を評価する。

## 現在は進めないもの

新gate、gamma/threshold/width/rank変更、q=1探索、新分子・PF・時刻・gap、
HF/HCl分解の穴埋め、科学計算再実行は許可しない。
第一研究のformal結果、D2-Aの元停止判断、G2とH-chainのprediction/採点は変更しない。
追加検証の必要性と範囲はGPT側へ戻す。

次の停止点は成果整理版のレビューである。投稿完成・未知条件へのpolicy認証とは区別する。
