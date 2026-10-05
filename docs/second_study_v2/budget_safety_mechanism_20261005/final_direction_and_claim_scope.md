# 第2研究：G2後の最終方針・claim scope freeze

ユーザー承認日：2026-10-05。Direction Cを研究の主方向として固定する。
これは追加検証の承認ではなく、既存結果を説明する主解析の承認である。

## 主題とRQ

有限時刻のPF校正情報が、QPEの時刻・連続予算判断にいつ価値を持つか、その条件と限界を調べる。
Primary RQは、cheap predictorの過小評価量を固定予算の許容marginが吸収できる条件は何か。
Secondary RQは、spectral point accuracy、経験的width、abstention、資源上のdecision windowが
どのように異なり、追加情報の精度改善が判断改善に結び付かないregimeをどう説明できるか。

cheap-first/fixed-gamma frontierを基準線とする。既存B2/H1 gateは履歴上の固定対照であり、
主方式として採用・修正しない。spectralは条件付き情報取得の対照であり、gateの失敗から
spectral必須とは結論しない。新selector、Arnoldi自体の新規性、証明付きcertificateは目標にしない。

## 主解析の優先順位

1. e-c、M_gamma、safety slack、gamma_reqでHF/H-chain/HClの同一座標scalarを整理する。
2. M1のsigned point error、width coverage、rank/allowance abstention、decision windowを分離する。
3. H-chainの約33%を固定時刻比・leading-modelの算術基準と、安全だったという実証に分ける。
4. 同一Hamiltonian・sector・energy origin・physical branchが確認できる場合だけPF/H-reference
   誤差を分解する。H-reference基準にtruth shiftを足しただけの量は独立PF truth energyではない。

## 主張の境界

- safeとは保存numerical truthとcontinuous rotation cost proxy上の判定。厳密保証でも
  離散QPE query count/end-to-end実装保証でもない。
- HF pilot/bridge/G2は同じ2条件を再利用する。30座標は30独立sampleではなく、10 native condition。
  H-chainは7系を試み6系を採点、H3はreference不成立であり効果0とは数えない。
- HF、HCl、H-chainの候補contractを統合した新しいselectorを作らない。各native 3候補を維持する。
- q=1 conditional H1 cost、standalone cold cost、rigorous cost envelopeは未確立のまま。
  process peak RSSを足さず、shared/cache/reference/comparator/truthをH1 incremental costと混ぜない。
- gamma_req、最小safe gamma、candidate oracle、width windowはpost-hoc development arithmetic。
  operational policyの新性能・独立holdout・interventionの達成可能性・scalingを示さない。
- H-chain fixed-time/leading-model比との差は因果的独立成分ではない。偶奇、charge、spinは交絡する。
- PF/H誤差分解が可能でもstate quality/rankの原因実証にはならない。
- D2-A formal close、post-hoc branch audit、C0、HF robust_signal、G2 D_gate_false_negative、
  H-chainの既存formal結果を変更しない。解析での再表現は原本上書きではない。
- 新規性は既存文献に対してまだ無条件に確立していない。主解析後に論文着地点を再確認する。

## 不許可・停止点

新規PF/H作用、Arnoldi、truth/ground/gap取得、fitting、gate/threshold/gamma変更、q=1探索、
HCl/LiF追加、rank探索、追加H-chain、certificate取得を行わない。
結果は `second_study_v2_budget_safety_mechanism_analysis_complete_review_required` で停止する。
追加計算・paper landingの最終承認・pushは別承認。今回の方針freezeは主方向を固定するが、
結果を先取りした論文claimのfreezeではない。

この解析は既知結果を見た後の説明的解析である。解析前commitは分析仕様の固定であり、
新しいtruth-blind実験や新しい科学的prediction freezeと呼ばない。
