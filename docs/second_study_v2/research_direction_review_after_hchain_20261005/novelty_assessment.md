# 新規性の暫定評価と文献境界

2026-10-05にrepositoryの[role map](../hf_domain_protocol_20260930/related_work_role_map.md)と一次文献を照合した。下記は限定的scope comparisonであり、網羅的systematic reviewでも新規性の確定でもない。`novelty_external_verification_required=true`を維持する。外部手法の実装・計算・benchmarkは行っていない。

## 既に先行研究が扱うこと

| 一次資料・確認版 | 今回の役割 | 重複するscope | 今回の差分候補・限定 |
|---|---|---|---|
| [Mehendale et al., arXiv:2312.13282v3](https://arxiv.org/html/2312.13282v3)、2025-08-04 | core | 固有値PF error、norm boundとerror estimatorの比較、time-step/partition/resource選択との接続。Introduction / Conclusionを確認 | 「固有値errorがresourceに重要」は新規ではない。固定finite-time候補とwidth/abstention後の実際のdecision比較が候補差分 |
| [Maxwell et al., arXiv:2606.30738v1](https://arxiv.org/html/2606.30738v1)、2026-06-29 | core | Practical error estimation、取得計算の効率化、BCH、現実的resource estimate。Introduction / Applications / Conclusionを確認 | 情報取得費用を減らすという一般論も新規ではない。安価情報を基準とした追加情報の限界価値を分離する比較が必要 |
| [Hejazi et al., arXiv:2412.16811v1](https://arxiv.org/html/2412.16811v1)、2024-12-22 | core | QPE-specific energy error、高次PF、低energy条件、resource scaling。Abstract / Discussionを確認 | Task-specific PF誤差評価は既存。今回は固定current_m3・fixed budget modelの有限候補decision。新PFや理論scalingを主張しない |
| [Yi and Crosson, arXiv:2102.12655v1](https://arxiv.org/abs/2102.12655v1)、2021-02-25 | core | 固有値・固有vector・gapに依存するPF spectral解析。Abstract / scopeを確認 | Ground/branch/gap条件は未取得ならcertificateに使えない。既存theoremをempirical M1幅へ移し替えない |
| [Zhao et al., arXiv:2209.12653v3](https://arxiv.org/abs/2209.12653v3)、2023-08-14 | peripheral | Dynamics向けadaptive time-stepとresource使用。Abstract / scopeを確認 | Adaptive一般は新規ではない。Frozen QPE time/budget choiceとdynamics feedbackは別task |
| [Miller et al., phase2, arXiv:2504.17881v2](https://arxiv.org/html/2504.17881v2)、2026-07-16 | core context | Empirical PF errorと保守的boundを比較してcircuit depth/resourceを見直す。Abstract / Introductionを確認 | Bound-vs-empirical resource gapだけでは差分不足。Cheap baseline、width付きspectral、conditional取得、freezeされたdecisionを同時に比較する必要 |

上表の差分欄は本レビューの推論であり、各論文に同じ比較が絶対ないと証明したものではない。特にMaxwell/phase2がpractical resource relevanceを扱うため、「初めてestimatorを資源判断で評価した」は使わない。検索語だけで該当論文が出ないことも新規性の証明ではない。

## Novelty candidateをproblem-specificに限定

| 候補 | 暫定評価 | 成立に必要なもの |
|---|---|---|
| 1. Finite-time PF-QPEにおけるdecision-level calibration比較 | 有望だが単独の一般framework claimは弱い | 同一PF/state/time候補のcounterfactualとfrozen operational decisionを分離。第一研究のlossと接続 |
| 2. Safety・quantum budget・classical情報費用・width/abstentionの分離 | 最も守りやすい方法論的差分候補 | Fixed-cheap frontierを対照にし、false-negative/unknown costを隠さない。量子・古典総合優位は未確立 |
| 3. Cheap-sufficientとaccurate-but-decision-ineffectiveの具体的実証 | 現在の論文核の候補 | H-chainはfamily内6適格系、HF/HClは別contractのdevelopment条件として記す。Regime境界の汎用predictorは未確立 |

Selective acquisition一般、hybrid cheap+expensive一般、Arnoldi/Krylov、uncertainty-aware/adaptive decision一般をnoveltyに数えない。Procedural freezeやunwrap座標系auditは再現性上重要だが、それだけで新しい量子algorithmとなるわけではない。

## 今採用できる主張とまだ使わない主張

使える候補は「fixed fourth-order PF、finite-time calibration、continuous QPE rotation-cost proxyに限定した、情報精度・不確実性・安全なdecision・取得費用の分離評価」である。

「Spectralは一般にcheapより高精度」「cheap stabilityで安全性を保証」「quantum advantageを改善」「全分子のregime map」「新しい厳密bound」「最初のvalue-of-information framework」は使わない。Value-of-informationは本研究ではobserved decision utilityの呼称で、Bayesian optimal acquisitionの一般理論ではない。

## 投稿前の追加照合（今回は実装・実験しない）

1. 最も近いMehendale/Maxwell/phase2と、finite-time time-step selectionの引用追跡でclaim overlapを確認する。
2. Contribution statementをfixed contract・observed regimes・non-certificateへ限定する。
3. Positive spectral valueを主張する場合だけ、代表的外部estimator最大1方式との比較の必要性を再審査する。今回その実装は未許可。
4. 小さい2-condition effectを効果量の一般化にせず、全negative/non-executed evidenceを併記する。

外部確認のURLs・版・確認scopeは[source registry](source_registry.json)にも保存する。External pagesは書誌照合に限り、scientific evidence matrixの内部実験結果を置換しない。
