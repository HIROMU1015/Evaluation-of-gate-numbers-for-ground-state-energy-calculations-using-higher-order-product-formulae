# B0 / cheap-first / spectral / B2・H1の位置付け

この文書は研究運営上の提案（`governance_scope`）である。既存policy・gamma・候補・scorerを変更する実装指示ではない。

| 対象 | レビュー資料内の役割 | 現在の制限 |
|---|---|---|
| B0 | Contractごとのbenchmark anchor / reproduction control | HF P0のB0とH-chain reference由来B0を混同しない。Fallbackもtruthで採点する |
| B1 fixed cheap four-gamma frontier | Cheap-firstのprimary comparator | 1.01/1.02/1.05/1.10を全て報告。Truth後の最小safe gammaはoracle診断 |
| Cheap-first | 情報取得順序とbaselineの位置付け | 「常にgamma=1.01」「cheap stabilityでsafe」と同義ではない。新運用policyはまだ作らない |
| 現B2 no-fit rule | 反証検査されたhistorical policy / diagnostic | H-chainではfixed1.01と同じ、HF eqではunsafe。未知条件でsafeな主方式として採用しない |
| 現H1 acquisition gate | Historical selective hypothesisの対照 | G2でもq=0、H1=B2。q=1の性能・費用は未測定。変更・救済しない |
| Always-M1 / saved spectral | 条件付き比較とaccuracy–width–utility診断 | 必須・汎用優位とは言わない。今回のH1が利用した情報に数えない |
| Condition-wise safe cheap選択 | Post-hoc oracle / counterfactual | Eq1.10とstretch1.01を新selectorに転用しない |

## Gate反例が確定したこと

HF eqではgamma間の選択候補・eligibility・signが安定していたが、q=0かつB2/H1はunsafeだった。**試したcheap stability criterionは、必要なbudget marginを十分に判定しなかった。** これはG2 frozen ruleについての具体的なnegative resultである。

判定対象は `abs(delta_direct)+beta*K/(t*B_frozen)<=epsilon_E` であり、signed shiftの近さだけではない。True shift、true gap、safe gammaをpredictor側で使ったことにはしない。T0 control PASSとcap-out safety failureを分ける。

## Gate失敗から導出しないこと

- cheap calibration全般が失敗する、またはcheap-firstを捨てるべき、とは言わない。
- spectral取得が安全性確保に不可欠、とは言わない。保存fixed cheap gamma=1.10もHF eqをsafeにする。
- 保存M1がsafeであったことを、H1がq=1なら成功したという実測結果にしない。
- 全gamma安定を見ていたことは、全gammaの安全性が事前に分かっていたことではない。
- unsafeな小budgetをquantum benefitに数えず、2条件を平均して相殺しない。

## 追加情報の価値を比較する順序

Procedural validity -> frozen-budget safety -> 同contract内のsafe quantum budget/time -> information actions / wall / memory / shared cost。古典費用とquantum rotationsを任意の係数で足さない。

効果を分離する：domain intervention、adaptive cheap、spectral incremental、selective acquisition。H-chainのanchor比約33%はadaptive/selective固有効果ではない。HFのcommon-margin aggregate約1.46%はH1 selective効果ではない。

現gateの変更はこの文書化に含めない。別レビューで設計変更を承認する場合も、G2 truthに合わせたthreshold fittingやrare q=1探索を自動的に始めない。
