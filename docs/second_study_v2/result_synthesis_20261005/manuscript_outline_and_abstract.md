# 第2研究の原稿構成と概要案

[承認済みGPTレビュー](approved_gpt_review.md)の着地点を、既存図表へ対応付けた編集draftである。
新しい研究方針・中心claim・追加検証範囲を決める文書ではない。
投稿先・採択見通し・世界初はここで確定しない。

仮題：
**有限時間積公式校正の信頼性と資源削減余地：QPE予算の数値的評価**

英題候補：
**Reliability and Resource Headroom of Finite-Time Trotter-Error Calibration for Quantum Phase Estimation**

## 概要案

近似状態を用いた有限時間PF誤差校正について、固定した四次積公式current_m3とQPEの連続rotation費用モデルの下で、凍結予算の安全性と資源削減余地を評価する。10 native条件30座標の保存結果から、誤差絶対値の過小評価と予算余裕、無償の完全情報が与える費用下限、固定spectral推定の点誤差・幅・採用制約を分離した。HFでは内部選択が安定した同じcheap gateが安全・危険な判断を返す一方、reference適格H-chain6系ではfixed cheapとadaptive/selective判断が同一で安全だった。名指しした29の安全な同時刻cheap比較は、完全truthを無償で取得しても10%の予算削減に届かなかった。また、同一Hamiltonian・energy origin・physical branchを確認したH-chain18座標の誤差分解により、shift精度を絶対PF固有値の回収精度と同一視できない事例を確認した。これらは固定有限時間のuncorrected taskにおける数値的信頼性と残余余地の結果であり、未知条件への安全policy、spectral法一般の不要性、量子・古典のend-to-end優位を示すものではない。

29比較や30座標を独立標本数としない。H3 reference失敗を未採点として残す。
この概要は[claim台帳](claim_evidence_ledger.md)のC1–C3と同じscopeである。

## 本文と図表の対応

| 節 | 読者へ伝えること | 図表・根拠 |
|---|---|---|
| 1. 問題設定と近接研究 | 有限時間の点推定を凍結budgetへ変換する課題。第一研究との境界 | [先行研究差分](related_work_delta.md)、[scope](approved_scope_and_rq.md) |
| 2. 固定taskと評価方法 | current_m3、native candidates、continuous metric、truth barrier、条件単位。H3/H2の限定 | [result synthesis Table 1](result_synthesis.md#評価対象と比較単位)、元protocolへのリンク |
| 3. 安全性・oracle・widthの量 | signed/absolute、片側不足量、gamma1 slack、same-time oracleとfixed-point windowを区別 | 台帳C1a/C2a/C2b、元quantity dictionary |
| 4. Cheap判断の反例と安全事例 | HF eq unsafeとstretch safeの符号反転、H-chain fixed cheap同一性 | Figure 1、C1b/C1c |
| 5. 改善余地と実M1 | 名指しsafe対照の小さい残余余地、point/width/abstain/fallback、HF共通1.10の小さい差を残す | Figure 2、C2a–C2e |
| 6. PF側とreference側 | H-chainでの成分別観測。相殺一般や因果state/rankを新規としない | Figure 3、C3 |
| 7. 含意と限界 | cheap-firstは取得順序、現B2/H1はhistorical diagnostic。外部手法/未知系/証明/総費用は未達 | [未確立事項](outstanding_claims.md)、元resource会計 |
| 付録 | 全gamma/座標、H-chain約33%のモデル説明、historical stop/provenance/software caveat | 元CSV、source registry、各原本report |

D1/D2/C0/G2という作業順を本文の論理構成にはしない。
約33%を新しいadaptive方式の因果効果として見出しにせず、安全だった実証とモデル比率を分ける。
外部代表法の比較や新たなrank/gap取得を原稿完成の自動条件にしない。

## GPT側へ戻す確認点

C1–C3が対象・対照・evidence classとともに伝わるか、先行研究と重なる一般論を新規性へ
混ぜていないか、限定された独立論文としての原稿着地点が適切かを確認してもらう。
この編集draftを理由に科学計算を開始しない。
