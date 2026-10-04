# 次検証の比較とNEXT_MINIMAL_VALIDATION

全案は提案だけで、今回は実行しない。推奨中心はDirection Cであり、q=1 positiveを得ることを選定基準にしない。

## G1–G4の比較

| 案 | 減らせる研究不確実性 | 必要データ/計算 | 限界・順位 |
|---|---|---|---|
| G1 HCl S1A blocker removal | General moleculeのB2/q/H1を実行可能にする | HCl2条件のexact4-gamma eligibility/selection/fallback/budgetを別protocolでmaterialize。保存cheapを再利用できれば新matvec0、不可なら最大6cheap PF+6H exponentialの別承認。M16座標/truthは既存 | Original S1Aはmissing frontier生成を禁止していたため単なるrerunでは不可。Same-time headroom小、まずG2の後に必要性を判断 |
| G2 HF cheap-policy replay | 既知のmargin差がある2条件で固定cheap instability gateが妥当か。H1の追加decision価値があるか | Existing6 cheap/M1/truthとfour-gamma frontier。新科学作用0の計画 | 最小費用・最も直接の反証。**第一候補**。HF developmentのsubset replayで一般化ではない |
| G3 LiF/HCl matched completion | State/reference regimeを拡げ、spectralが必要な条件があるか | LiF既存4座標を全部使う案ならM1最大32 PF+32 H matvec、state/cache確認、truth exact identity確認。HCl部分はG1依存 | 情報利得の優先conditionと共通contractが未固定。16 missing M1一括補完はしない。G2結果後の別design対象 |
| G4 spectral central route stop | 「さらにpositiveを探索すべきか」を限定negativeとして閉じる | 新計算0 | Main estimator探索は今止められる。ただし全regime spectral不要の断言ではない。Cの論文核内でnegativeを整理 |

G1のfrontier materialization、G3のaction countsは将来の上限案であり、今回の取得数ではない。既存snapshotに入力があることとruntimeを運用できることは区別する。Untracked cacheの探索・再生成・移送を承認したことにしない。

## NEXT_MINIMAL_VALIDATION：HF-onlyのfixed-rule replay

名称案: `HF_two_condition_frozen_rule_replay_design`。科学計算ではなく既存development scalarによるpolicy診断。元4-condition S1A Dの救済ではなく、別scope・別protocol・別statusで一回だけ行う案。

| 項目 | 提案する固定範囲 |
|---|---|
| Systems / conditions | `HF_full_eq_sto3g`, `HF_full_stretch150_sto3g`の両方、current_m3、K=9108 |
| Cheap coordinates | Eq/stretch各`T0,1.3T0,1.6T0`、6点。保存binary64 hexのまま。選択済み1.6T0だけに絞らない |
| Existing data | E11 prediction、E12 separate-arm cost、E13 result、E14 exact scoring。Bridgeのoracle gammaをpredictorへ入れない |
| New data | Derived B2/q/H1 decisionsとreplay logsだけ。Cheap/M1/truth/gap/state/Hの取得は0 |
| M1 coordinates | q=1条件について保存M1全3点だけをq freeze後に開く。q=0のM1はH1 freeze後にalways-M1対照用に開く。最大6既存点 |
| Truth | 保存HF direct6点・T0 control・branch/gapをfinal prediction commit後にreuse。新truth0、近傍・補間0 |
| Rule | S1A Rules1–3、gamma1.01/1.02/1.05/1.10、sign noise floor、tie/eligibility/targetはbyte-frozen sourceに従う。HF-native候補を維持 |
| Formal scoring | Continuous frozen budgetのsafety、target、fallback、fixed-cheap対照、conditionwise結果とaggregateを分離。規則変更0 |
| Additional scientific actions | PF/H exponential/H matvec、Arnoldi、full H/PF solve、GPU：すべて0 |
| Saved cost attribution | Cheap6 PF+6H exponential、always-M1既存48 PF+48H matvec。Conditional側はq=1条件ごと既存24/24、最大48/48。Replayでこれらを再実行したと数えない |
| Actual replay runtime | File/read/decision/hash/commit時間を別記録。Saved acquisition runtimeの代替・combined測定にはしない |

## 実行前のcontract gate

1. 2条件の全4-gamma candidate rows、eligible sets、selection、fallback、budgetが保存されているかをidentity付きで確認する。元S1A gateがHF frontier存在を確認した記録はあるが、新replayの全adapter整合性を本レビューは認証しない。
2. HF reproduction-control T0をH-chain benchmark T0へ再解釈しない。B0/epsilon/beta/etaをHF authorizationから継承し、新数値を設計しない。
3. Trusted field projectorはcombined prediction全体をcheap predictorに渡さない。Cheap namespaceだけを抽出し、M1/truthアクセス禁止をsynthetic/source testsで確認する。H1だけcheap ruleを有利に変更しない。
4. HF-only subsetと新derived-decision schemaを、truthによる新q判定の前に別protocol commitで固定する。HF結果が既知であることは明記し、freezeをprospective blind evidenceと呼ばない。
5. Contractまたはcostが一意に評価できなければ停止。欠けたfrontierやpolicyを結果後に生成せず、旧S1A Dを書き換えない。

## Freeze順序案

Protocol/input identity freeze → cheap-only field access → B1/B2/q commit/hash → q=1の保存M1のみopen → H1 commit/hash → q=0保存M1のalways-M1 comparator completion → final prediction commit/byte gate → saved truth-only scorer → review stop。

Replayはacquisitionを測った実験ではない。q=1 combined H1 actual costは未測定のまま残る。元S1Aのcost-envelope式を併記する場合もsaved-arm replay scenarioとし、`max(C_C,C_S)`や和をactual combinedの数学的下界/上界と認定しない。Rigorous boundが必要なら`combined_cost_not_evaluable`で止める。

## 停止規則案

先にunsafeを判定し、unsafeな低budgetをbenefitに数えない。Practical spectral incremental effect threshold、classical ceiling、noninferiority marginは`unresolved_requires_review`。継承した10%targetはB0比のdomain intervention基準であり、新規性・practical spectral gainの閾値ではない。

| 結果 | その一回の解釈と停止後の方向 |
|---|---|
| A: q=0、fixed1.01 safe、B2/H1同一 | Cheap sufficiencyの追加development evidence。Selective positive主線を止めC/Bへ。HCl補完やrare q=1探索を自動追加しない |
| B: q=1だがH1がB2を改善しない | Triggerは作動したがdecision valueなし。Cのnegative regimeとして保持し停止 |
| C: q=1でH1改善、fixed cheapで再現不能 | Conditional spectral value候補。さらにnontrivial `0<sum(q)<2`、always-M1に量子非劣性、取得量削減を確認。Cost不明ならdecision signalだけで停止し、practical superiorityを宣言しない |
| D: q=0だがB2 unsafe | Cheap instability gate false-negative。閾値救済なし。Gate redesignの別reviewかroute停止。安いq=0を「正しく不要と識別」と言わない |
| Incomplete | Input/coordinate/four-gamma/M1/cost contract不足は未評価。効果0・policy失敗・cheap sufficiencyに分類しない |

さらに、q=1が両条件に出た場合はalways-acquireであってselective acquisition削減の証拠ではない。Fixed gammaが同等以上なら、q=1/H1にsafe利益があってもspectral-specific benefitとは数えない。既存HFのaggregate差はknown-development比較なので、新しいpolicyの独立成功に数えない。

## この先を自動実行しない

G2の結果が何であってもそこで研究方針reviewへ戻る。欠けたHCl frontier、LiF M1、追加geometry/time、q-rule tuning、C1/D2-B、combined costの新計測、holdout、外部baselineは別承認とする。今回はG2の規則適用も実行していない。
