# 研究経緯とRQの再評価

これは既存Git-tracked evidenceの統合と研究方針提案であり、再実験・policy実行・再fitではない。確認snapshotは`50cdc62d69a28bc5d4f4893f3c589e0bbd6d81db`。E番号は[source registry](source_registry.json)に対応する。

## 途中段階だけで判断しない研究経緯

| 段階 | 保存事実 | 今回の位置付け |
|---|---|---|
| 第一研究 E01–E03 | `F_total=F_model*F_margin*F_within*F_domain*F_PF`。保存表の`F_P`を統一表記`F_PF`へ対応付ける。HFはdomain factor下界eq 2.114659 / stretch 2.069664、cap内saving上限約1.254948% / 0.322572% | 損失源を分けた。Domain拡張の安全性や独立介入の因果効果は未証明 |
| 旧第二研究 E04 | `complete_no_benefit`。Multiple-windowはsafe 3/4、equal-information比aggregate budget 1.2526414181 | Equal-information comparatorでbenefitを示せず正式終了。再開しない |
| D1 E05 | HCl 6座標で少数成分のoracle spectral compression | Truth-free operational predictorではない |
| D2-A E06–E08 | Original `d2_a_complete_close_spectral_route_stop`。別auditでinteger座標系不一致、physical branch 6/6、max point error 1.382529828669e-8 Ha、abstention 1/6、nonabstain unsafe 0、低予算0/6 | `accuracy_recovered_but_certification_cost_not_advantageous`はaudit後の解釈。正式statusの置換ではない。Widthはempiricalでcertificate取得費用を実測した意味でもない |
| C0 E09–E10 | Conditional residual-separation boundを設計。`g_rho_others`のtruth-free lower bound/target identity未取得。Current widthがbaseline-equivalent window内0/6、same-time perfect calibration saving 0.327975–2.286462% | 情報の鋭さ・必要情報・資源窓を接続したdevelopment arithmetic。新boundの数値成功ではない |
| HF pilot E11–E14 | 固定`T0,1.3T0,1.6T0`。M1は2/2 safe/target、1.6T0。Eqのcheapは1.10だけsafe、stretchは1.01からsafe。正式`robust_signal` | 大きいdomain intervention effectと小さいspectral-specific effectを分ける |
| HF bridge E15–E17 | M1 572.482494M vs common safe cheap 580.977536M、約1.4622%。EqはM1が3.0716%高く、stretchはcommon1.10比7.9178%低い。Oracle conditionwise cheapは561.366768M | M1はcommon marginに対して小さいaggregate利益を持つが、各条件にもっと安いsafe cheapがある。Oracle gammaをoperational policyにしない |
| Selective design / coverage E18–E21 | B2/H1 cheap policy同一、取得qと採用を分離。完全tuple 12/28、missing M1 16、HF/HCl candidate contractは別 | Coverageだけではpolicy fitting不可。Tuplesの完備とfrontier contractの可用性は別 |
| S1A E22–E24 | Formal D `contract_or_cost_not_replayable`。HCl four-gamma frontier不足でM1/truthを開く前に停止 | General-molecule B2/H1は未実行。後のH-chain成功でこの欠損を埋めたことにしない |
| H-chain E25–E34 | Attempted 7、reference適格6、H3適用不能1。6系q=0、r=.8、safe/target、B/B0約.67。Fixed1.01と同じ。Always-M1はB0 fallback | Cheap-sufficient regime。Adaptive/selective incremental valueなし。q=1 combined path未観測 |

`H(F)=1-1/F`は他因子固定の`isolated_factor_algebraic_headroom`であり、interventionで達成可能な最大削減率ではない。異なるPF/state/time/benchmark間の因子やbudgetを直接poolしない。

## Evidence matrixの読み方

[CSV](evidence_matrix.csv)は24行、33fieldで、stage/conditionと6つのD2-A座標診断を含む。行数はsample数ではない。同一HF/HClの第一研究・pilot・bridge・C0を重複して独立標本に数えず、HF aggregate/oracle行を第3条件にしない。

`direct_scored_evidence`、`development_diagnostic`、`counterfactual_or_oracle`、`blocked_not_executed`、`protocol_applicability_failure`を分離する。未実行qは`not_evaluated`であって0ではない。Numeric fieldの空欄は未取得・非適用であり、0補完しない。HFのnumeric `cheap_frozen_budget`は比較軸を揃えたcommon gamma=1.10、H-chainはfixed1.01=B2/H1。他gammaの安全性はtext fieldと原表を参照する。

Internal E01–E37は確認snapshotのtracked bytesのみ。Source registryはpathのbyte-identical publication originとverified snapshotを分け、元の科学的generating-result commitも別に保持する。External papersは書誌・scope照合であり、内部実験の代替証拠ではない。

37件のpath origin/snapshotはbyte identityを検査した。一方、第一研究の元S0結果commit `cc3626a8135b647fe283fc60c963de70c5f6b2a5`はこのreview Git storeにobjectがなく、E03に記載されたupstream参照としてのみ保存する。今回確認済みのcompletion/decomposition文書commitと混同せず、元S0 commitのblobを再検証したとは主張しない。欠損を直すための計算・cache復元・history書換えは行わない。

## 判断量を分離する

`delta_direct`はsigned shift、`e_direct=abs(delta_direct)`はuncorrected QPE予算のPF error。機構解析の`abs(delta_hat-delta_direct)`をbudget errorへそのまま代入しない。安全性は元規則`abs(delta_direct)+beta*K/(t*B_frozen)<=epsilon_E`を保持する。

`e_use_M=abs(delta_M)+w_M`のwidthはpoint errorと別である。経験的coverageは必要な診断だが、未知条件のcertificateではない。Fixed tのcheap budget `B_C`をM1が下回る必要条件は、継承したcontinuous modelでは

`w_M < epsilon_E-abs(delta_M)-beta*K/(t*B_C)`

である。これは代数的decision windowであり、幅をそこまで下げられる方法を保証しない。右辺が非正なら同時刻での追加精密化を正当化しない。C0では既存w_winを参照するだけで、新しいwidth/gapを生成しない。

Decision utilityは安全性を先に判定し、その上でtime、quantum budget、fallback、classical costを比較する。Unsafeだが安いbudgetをbenefitに数えない。単位が異なるPF/H actions、seconds、RSS、rotation costを任意の重みで足さずPareto型の比較とunknownを保つ。

効果は別々に記録する：`domain_intervention_effect`（同じ情報で候補域を広げた効果）、`adaptive_cheap_effect`（fixed-cheap vs B2）、`spectral_incremental_effect`（cheap vs同候補M1/H1）、`selective_acquisition_effect`（H1 vs always-M1）。HFの約1.46%はcommon-margin comparatorに対するpost-hoc差で、H1実測効果ではない。H-chainの約33%はbenchmark anchor比で、HFのdomain factor回復率ではない。

## Primary RQ

**有限時間PF-QPEの固定候補・resource modelにおいて、追加校正情報は、cheap-onlyに対してどの条件で安全な時刻・予算判断を改善し、その取得費用に見合うか。**

- Why important: 第一研究で同定したresource lossを減らすには、推定精度ではなく選択と予算が変わる必要がある。
- Existing evidence: H-chain cheap sufficiency、HFの小さくcondition依存のM1利益、HClのaccuracy/width/utility不一致。
- Missing evidence: General moleculeでの正式B2/q/H1実行、q=1 path、条件付きincremental cost、未使用条件への外挿。
- Success criterion: 固定比較でsafe/unsafe、B/B0、fixed cheap dominance、width/abstention、情報費用を分離し、どこで追加情報の価値が消えるかを再現可能に示す。Positive spectral caseは必須ではない。
- Failure interpretation: すべてfixed cheapで説明できれば「追加spectral価値なし」というscope-limitedな答え。Contract不足ならanswer unavailableであり、効果0ではない。

## Secondary RQ 1：cheap sufficiencyとgate failure

**Cheap stability情報は、spectral不要な条件とcheap-only安全性をどこまで識別できるか。**

- Why important: 不要な高価情報を取得せず、unsafeな未取得を見逃さないかを調べる。
- Existing evidence: Eligible H-chain 6系はq=0でsafe、fixed1.01とB2同一。HF eqには小gamma unsafeという保存例がある。
- Missing evidence: HFで同じno-fit ruleを適用したqとdecision。現在のレビューでは計算していない。
- Success criterion: 固定ruleのq=0をtruthで採点し、false-negativeがない範囲とある範囲を明記。Adaptive benefitはfixed frontierを超えた場合だけ認定。
- Failure interpretation: q=0/unsafeはcheap instability gateの失敗。結果後にthresholdを変えず別のdesign reviewへ戻る。

## Secondary RQ 2：accuracyからwidthからutility

**Point errorの改善がwidth/abstentionを経てresource actionを改善する条件は何か。**

- Why important: Spectralの高精度点推定を量子利益と取り違えない。
- Existing evidence: D2-A高精度・低予算0/6、C0の狭いwindow、H6 allowance不足、H7/H8 point errorも悪化、HF conditionwise勝敗。
- Missing evidence: Operational certificate、安価なfull-space separation情報、他PFへの一般化。
- Success criterion: 既存point/width/decisionを同一座標で分離し、point accuracyだけ、width阻害、rank阻害、decision利益を識別する。Conditional boundの仮定未取得はindeterminate。
- Failure interpretation: Widthだけが原因という仮説はH7/H8で支持されない。精度向上の積み増しを自動承認しない。

## Secondary RQ 3：情報取得費用とselectivity

**安全なquantum decisionの改善を、どの追加情報量・古典費用で得たか。**

- Why important: 小さい量子gainに巨大な古典calibrationを払うことを避ける。
- Existing evidence: HF separate arm 48 PF/48 H matvec vs cheap6 PF/6 H exponential、H-chain q=0 shared-pathの測定とcomparator別会計。
- Missing evidence: q=1 combined実測、cold always-M1、未知conditionでのoperational取得費用。
- Success criterion: `C_shared+C_cheap+q*C_spectral_given_cheap+C_decision`をresource vectorで記録。Conditional acquisition量とquantum非劣性を同時に比較する。
- Failure interpretation: Separate-armの和はscenarioであってactual combinedのhard boundではない。費用不明ならcost_not_evaluableとし、information-efficiencyを主張しない。

## 第一研究との二部構成

Study 1: diagnose model/information/domain losses。

Study 2: quantify the decision value of additional calibration information。

この接続は自然だが、研究方針の解釈である。第二研究を「より正確なestimatorの開発」や「selectiveが必ず勝つ証明」へ固定しない。文献との差分と着地点は[新規性評価](novelty_assessment.md)、[論文案](publication_landing_options.md)で限定する。
