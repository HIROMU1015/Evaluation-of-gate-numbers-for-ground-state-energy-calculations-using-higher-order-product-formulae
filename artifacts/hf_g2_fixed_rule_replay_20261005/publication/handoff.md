# HF G2 fixed-rule replay：review handoff

Status: `second_study_v2_hf_g2_fixed_rule_replay_complete_review_required`
Classification: **`D_gate_false_negative`**（G2専用taxonomy。元S1AのDとは別）。

## 結論

HF eq/stretchともcheap candidate・eligibility・signは全gammaで安定し、q=0、gamma=1.01、1.6T0を選択した。H1はB2のまま、decision changeは0。保存truthによる採点ではeqがunsafe、stretchはsafeだった。

| 条件 | q | B2/H1 budget | Safety LHS [Ha] | 結果 |
|---|---:|---:|---:|---|
| HF equilibrium | 0 | 313366606.6694983 | 0.00017072575273433498 | unsafe |
| HF stretch150 | 0 | 220076403.84964326 | 0.00015841630475708096 | safe |

epsilon_Eは0.00015936001019904 Ha。EqではLHSがepsilonを超える。候補・eligible set・proxy signの安定は、proxyの過小評価がmargin内であることを保証しなかった。これは一件のdevelopment counterexampleであり、全cheap calibrationの否定ではない。

## 対照と解釈を混同しない

- T0 reproductionは2/2 PASS。B0は2/2 safe。元HF branch/shift controlが崩れた結果ではない。
- Fixed cheap gamma=1.01/1.02/1.05はeq unsafe、1.10はeq safe。Stretchは全4gamma safe。
- Always-M1は2/2 safe・10%target達成。Point branch/empirical width coverageは6/6。これは保存対照で、H1がM1を使った結果ではない。
- Common gamma=1.10のsafe aggregateは580977536.2089661、always-M1は572482494.3535492。元bridgeの小さいaggregate差が再現されたが、H1のselective利益ではない。
- Eqではsafe gamma=1.10 cheapの341290363.69945365がM1の351773269.593654より低予算。Stretchではsafe gamma=1.01 cheapの220076403.84964326がM1の220709224.75989527より低予算。これらtruth後のcondition-wise選択を新しいoperational gamma ruleにしない。
- B2/H1 aggregate 533443010.51914155はunsafe条件を含むので、safe comparatorに対する資源利益として解釈しない。
- q=1 conditional H1 pathは今回も観測されず、実測性能・combined acquisition costについて主張しない。

## Freeze / identity

- Base: `b92bd034dcf711ce819835ffa1dd6b59dc08977d`
- Protocol / implementation: `67a832f0083e593dd375bd3040dab75680790a09`
- Cheap / q commit: `50d0293d8f03541913a4d2a9c924336e8df9a1a1`
- H1 commit: `d4c5e78cac5fa9cc7be6de4c15c0022a49009638`
- Final prediction commit: `0b4dca38bac1aa2c1b70d60702a72e378c5e4b3b`
- Prediction SHA-256: `4b8b1a3635bf1988bd0ce3af53c05b874352262c9224b84906697dc4c6c4256c`
- Result manifest SHA-256: `f72869a1b5327ce6bd474aecfefb9822f0e76328c1a920fc835601e4110cdb8b`
- Result commit: このhandoffを含むcontent commit（自己参照hashは埋め込まない）。
- Publication provenanceはresult content commitの後に別commitで固定する。

Cheap4件、H1 4件、final prediction5件をcommit blobとbyte照合した。M1 conditional取得は0、comparator用保存M1の復号6件はH1 commit後。Truth6点はfinal prediction HEAD/blob gate後に再利用した。Combined artifactのraw bytesはhash/lexical projectionで読んだが、cheap段階でM1値は復号していない。既知developmentの手続き監査であり、prospective blind/holdoutではない。

## 資源・検証

新規PF/H action、M1、truth、gap、state/H生成、fit、GPUはすべて0。保存cheap6 PF/6 H exponential、M1 48 PF/48 H matvecを今回の実行回数に数えない。各stageのreplay workは0.0531 / 0.0333 / 0.0661 / 0.0485秒（startup・artifact serialization除外）、記録されたprocess RSS high-waterは382268 KiB。これはarm-specificやincremental memoryではなく、peakを合算しない。

Formal pre-freeze/pre-score/post-score synthetic testsは各18 passed、fail/skip 0。初期development testも18 passed。Full legacy suiteは実行しておらず、過去のnongreen状況を置き換えない。8出典のorigin/snapshot bytes、16 decision safety式、6 exact truth coordinates、runner manifest5 payloadを独立照合した。

## 次の研究方針レビューに戻す

Direction Cは維持できるが、現B2/H1 acquisition gateを未知条件でsafeとして採用する根拠はない。Cheapの安定性と必要marginは別情報である、という具体的な境界をCのRQに入れることを推奨する。Cheap-firstはfixed frontierを基準に保持し、adaptive superiorityを主張しない。Spectralは条件付きの対照・sub-regime候補であって、今回selective positiveを実証したとは言わない。

**ここで停止する。** Gate redesign、gammaのtruth適合、HCl/LiF、追加M1、C1/D2-B、新gap/combined cost計測は別review/承認。最終RQ・novelty・paper landing、current_research_status更新は今回自動実施しない。旧HF robust_signal、旧S1A D、H-chain、D2-Aのformal artifactは未変更。Pushは未承認。

[結果report](../result/report.md)、[機械可読result](../result/result.json)、[6座標diagnostics](../result/coordinate_diagnostics.csv)、[execution audit](execution_audit.json)、[G2 protocol](../../../docs/second_study_v2/hf_g2_fixed_rule_replay_20261005/protocol.json)。
