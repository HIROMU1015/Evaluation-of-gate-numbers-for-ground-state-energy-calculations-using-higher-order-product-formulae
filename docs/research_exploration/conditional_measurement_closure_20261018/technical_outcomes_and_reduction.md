# 保存する数学的成果と還元

2026-10-18 JST。下記は固定構成commit `beecb0c9fbaa8c8aab3a76b88b5e8f2e0faba63b` の成果を保存する記録であり、新たな理論・証明・数値検算を追加していない。詳細本文は[固定packet](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/tree/beecb0c9fbaa8c8aab3a76b88b5e8f2e0faba63b/docs/research_exploration/algorithm_difference_construction_20261018)を参照する。

| 保存する成果 | 固定資料・適用範囲 |
| --- | --- |
| 非可換hoppingとdensityを含む有限電子family | research_problem_and_gap.md P1–P2。四mode、N=2、H=cI+F+R。残余Rを捨てない |
| spectator占有→active Givensの有限生成 | generation_rule_construction.md G1–G6。係数から三つの角度を作り、占有読出し・feedforward・一回転・読出しを行う |
| 固定基底の同時対角化障害 | discriminating_examples.md D1。tu≠0で二contextのactive演算子が非可換。一つの固定active軸に限る |
| 固定分割に対する標本分散差 | 同D2–D4。明示された診断stateで条件付きF測定の分散0、別poolの標本平均には分散が残る。全推定量の下界・量子優位ではない |
| 残余項のrecord-only再構成障害 | 同D5–D6。同じF record lawだがR平均が異なる二state。元Rには別のfresh copiesを計上する |

還元の中心は、L01の公表済みsymmetry-conditioned one-body手順にactive集合{1,2}、spectator集合{3,4}、外側変換Iと具体的h(z)を代入する操作である。公表法の回転規約をU_v=U_s†に合わせるとPOVMが一致し、record変換はidentityとなる。角度生成・precision・準備・readout・古典費を同じに計上する。[固定操作対応](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/beecb0c9fbaa8c8aab3a76b88b5e8f2e0faba63b/docs/research_exploration/algorithm_difference_construction_20261018/generation_rule_construction.md)

従ってB_sepとの差が実際にあることと、強いB_pub／B_fairに対する独立差の有無を分ける。B_plus_core一致だけから核心の先行存在を推論せず、公表生成式への具体的代入を根拠にした。全条件付き測定・全実装の同一性や世界的priorityを認証したわけではない。

旧数学本文、SOURCE、文献provenance、監査・publication receiptは凍結のまま履歴内で参照し、今回再生成・修正しない。
