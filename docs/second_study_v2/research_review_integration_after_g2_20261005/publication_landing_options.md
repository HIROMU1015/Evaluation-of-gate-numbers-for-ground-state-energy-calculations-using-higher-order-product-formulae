# G2後の論文着地点 — 最終承認前

旧[3案](../research_direction_review_after_hchain_20261005/publication_landing_options.md)にG2を反映した差分。投稿可否・掲載先・新規性を保証する文書ではない。

## 推奨候補：decision value / observed-regime characterization

主メッセージ候補：**より正確なPF校正が、より良い安全なQPE資源判断を意味するとは限らない。安価情報の安定性も、十分なbudget marginを保証しない。**

現在揃う論点は、第一研究のloss分解、H-chainのcheap sufficiency、HFの小さいcommon-margin spectral対照差、HClのpoint/width/utility乖離、G2のfrozen-gate反例である。これは観測caseの整理で、汎用regime predictor、scaling theorem、厳密certificate、未知条件への保証ではない。

G2前に残っていた「HFで同ruleをreplayした結果」は取得済み。残る未取得はq=1 conditional value、combined incremental cost、実用effect size/ceiling、未使用条件での再現である。未取得を埋める追加計算を今回の完了条件にしない。

## Positive selective spectral論文

現gateを主方式にしてこの着地点を採用する根拠は不足。HF/H-chainとも実現H1はq=0で、H1のspectral利益は未観測。Safeなalways-M1はconditional H1成功の代理ではない。Rare q=1を探して主張を救済しない。

## Cheap sufficiency / tested spectral limitations

H-chain contract内の限定結果として保持できるが、HF eqのgamma=1.01はunsafeであり、全分子cheap sufficiencyは主張できない。HF各条件のsafe cheap armは存在するが、truth-freeなgamma選択法は未確立。独立主論文として広げるより、推奨候補の一節にする案が自然である。

## 原稿構成候補

1. Study 1：資源損失とisolated-factor algebraic headroom。
2. Study 2：fixed contract・情報境界・continuous budget・four-gamma comparator。
3. H-chain cheap-sufficient casesとH3 applicability failure。
4. HF/HCl：point、width、margin、safe quantum decisionの分離。
5. G2：cheap stability gateのfrozen-rule反証検査。
6. 情報費用の未評価部分、novelty限定、generalization限界。

これはレビュー用outlineで、原稿・章構成の正式freezeや`current_research_status.md`更新ではない。
