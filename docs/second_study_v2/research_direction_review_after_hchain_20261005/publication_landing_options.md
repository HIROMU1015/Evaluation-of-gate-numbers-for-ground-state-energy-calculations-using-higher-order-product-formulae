# 論文の着地点：3案

投稿可否や掲載先を保証する評価ではない。どの着地点でも[第一研究との接続と数量定義](research_question_review.md)、[新規性の未確定性](novelty_assessment.md)を共有する。

## Landing 1：selective spectral positive

主メッセージ候補：Cheap calibration identifies easy regimes; selective spectral information helps difficult resource decisions.

- Necessary evidence: General moleculeでnontrivial q、H1がB2よりsafeまたは低予算、fixed cheapで同じ価値が得られない、always-M1に量子非劣性、conditional取得量・費用減、独立なfreeze/scorer。
- Current evidence: H-chainのq=0 cheap-sufficient側とHFのaccurate M1はある。q=1 conditional H1の実測はない。
- Missing evidence: General-molecule policy実行、q=1 benefit、combined incremental cost、未使用conditionでの再現。
- Weakness: HFでは各条件のsafe cheapがM1より安い。現状でpositive selectiveのタイトルは結論先取り。
- Publication risk: Rare q=1探しによるgeometry/threshold post-hoc selection、classical overhead未評価。現状は保留。

## Landing 2：decision value / observed-regime map（推奨）

主メッセージ候補：More accurate finite-time PF calibration need not improve the frozen resource decision; information value depends on the decision window, uncertainty and acquisition cost.

- Necessary evidence: 同一候補のfair fixed-cheap比較、point/width/branch/abstention/decisionを分けた表、positive・negative・applicability failure・未実行の区別。安全性とbudgetを同じresource modelで採点。
- Current evidence: H-chain6適格系のcheap sufficiency、HCl accuracy/width/utility不一致、HF小さいcommon-margin aggregate利益とconditionwise逆転、H3 reference適用不能、S1A D。
- Missing evidence: General moleculeでの同じB2/H1 ruleの正式実行とgateの反証検査。Combined cost不明部分とexternal noveltyの限定も必要。
- Weakness: Regimeの原因・境界をまだ予測できない。「Regime map」はobserved-case taxonomyであって学習済み汎用mapではない。
- Publication risk: 単なる過去結果の編集・estimator benchmarkに見える可能性。第一研究loss→decision window→追加情報費用という問いと反証可能なgate診断を明確にする。

この案ではspectral positiveを見つけなくても論理は閉じる。すべてfixed cheapで説明できた場合も、追加精度を払う価値がなかった条件と理由が答えになる。ただしcase数だけで一般的不可欠性・不要性を主張しない。

## Landing 3：cheap sufficiency / tested spectral limitations

主メッセージ候補：In the tested H-chain contracts, inexpensive finite-time calibration sufficed for safe resource decisions; fixed-width spectral calibration did not improve allocation.

- Necessary evidence: Fixed-cheap comparator、全attempted systemsとH3未採点、scope固定、negativeの原因をpoint accuracy/width/rankへ分離。General moleculeへ拡げるには別証拠が必要。
- Current evidence: H-chainの全eligible systemでfixed1.01=B2=H1、always-M1 B0 fallback。HCl同時刻低予算0/6。
- Missing evidence: General-molecule一様な非優位は未確立。HFにはcommon-margin比較で約1.46%のM1利益がある。
- Weakness: Cheap手法そのものは既存で、adaptive B2追加利益もない。Fixed empirical widthの不利益をspectral全方式のno-goへ拡張できない。
- Publication risk: 「Spectralは不要」という過大negative claim、基準B0を恣意的なweak baselineと誤読されること。Scope-limited結果なら守れるが、独立主論文よりLanding 2の一節として強い。

## 原稿の最小構造

1. 第一研究で同定したresource lossと、finite-time calibrationの判断問題。
2. Fixed model/候補、cheap・M1・B2・H1の情報境界、four-gamma対照、freeze順序。
3. H-chain cheap sufficiencyとgeneral-molecule accuracy/utilityの相違。Contract別に提示してpoolしない。
4. Width/abstention、signed vs absolute error、classical information-cost、失敗・未評価の整理。
5. Limited gate diagnostic（承認された場合だけG2）、観測regimeと未確立の境界。

推奨はLanding 2。Landing 1は条件付き将来候補、Landing 3は現証拠で守れる限定結論。これは新計算・投稿・章更新の承認ではない。
