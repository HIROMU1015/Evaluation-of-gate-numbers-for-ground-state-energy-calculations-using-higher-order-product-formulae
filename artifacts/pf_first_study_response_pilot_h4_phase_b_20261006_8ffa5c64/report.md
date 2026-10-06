# H4 response-corrected calibration — Phase B saved-scalar scoring

最終Outcomeは **C `point_only`**。ResponseとRitzはA0よりtotal absolute errorを減らした。しかしbaseline S_under=0で、固定A/Bが要求するstrict decreaseを両methodとも満たせない。Responseのpoint改善がrefitで消えた、という意味ではない。Outcomeの名称と実測値を分けて読む。

Completed 2026-10-07 JST。artifactの20261006 labelは依頼／開始時のものを保持。Phase A freeze `53a88c28b7587ab61efb93d6ba30974c9d3d6404`、predictions SHA`9ce3d4e7ec89575f1d661515cddb636fab0288c5c4149df1c85dc529adace18f`を変更せず使用した。新science actions0、saved direct12、exact proxy22、A3 reference fits3。既存96＋新規35＝131 tests PASS。

## A. State correction itself

| Primary arm | point abs sum / eval12 Ha | total S_abs / Ha | S_under / Ha | E_max / Ha | crossings | total improved/worsened/equal vs A0 |
|---|---:|---:|---:|---:|---:|---|
| A0 CISD | 7.78116508748e-08 | 7.79176229268e-08 | 0 | 2.03086412721e-08 | 0 | 0/0/12 |
| A1 response8 | 4.61403923324e-09 | 4.59838762441e-09 | 0 | 1.16232934158e-09 | 0 | 12/0/0 |
| A2 Ritz8 | 2.42952729829e-12 | 1.27455952822e-11 | 1.25813324449e-11 | 4.0019352445e-12 | 0 | 12/0/0 |

Response total S_abs/A0=0.0590160152695（減少94.098398%）。Ritz比=0.000163577824931（減少99.983642%）。百分率は連続値の報告であり、新しいsuccess thresholdではない。22-coordinate point sumsはA0 9.91035963642e-08、A1 5.94979940158e-09、A2 3.15006561452e-12 Ha。全rowは保持する。

## B. Response specificity and costs

Ritz8はA1よりS_abs/E_maxが低く、12/12 evaluation rowsでabsolute errorが低い。同じcached Krylov情報でstandalone H9、forward22は共通だが、responseにはadjoint22、SVD1、RHS22が加わる。Ritzはadjoint0、small eigh1。異種costをscalarへ足さない。

ただしS_underはresponse0、Ritz 1.25813324449e-11 Ha。凍結Pareto tupleはresponse=(4.59838762441e-09,0,9,44)、Ritz=(1.27455952822e-11,1.25813324449e-11,9,22)。responseはS_underでstrictly better、Ritzにdominatedされず、**response_unique_tradeoff=true**。このformal tradeoffはresponseのaccuracy/cost優位やOutcome Aを意味しない。Ritz underestimationを新しいzero/material toleranceで消さない。

## C. Fit / proxy bottleneck and mechanism-to-total bridge

Responseのeval point sum 4.61403923324e-09からtotal 4.59838762441e-09へ利益は残る。A1のabs fit-component sumは8.92222641996e-12 Ha、saved exact-proxy-to-direct component sumは2.44950296027e-11 Haで、responseの残るstate/proxy差より小さい。

Ritzのpoint sum 2.42952729829e-12はtotal 1.27455952822e-11より小さく、total/point=5.24612145381。A3はpoint error0でもtotal S_abs=1.50462960022e-11 Ha。A2/A3のabs fit componentは約9.74e-12 Ha、exact-proxy-to-directは約2.45e-11 Ha。したがってstate差をほぼ除いた後には、**fit残差とfinite-time exact-proxy/direct差の両方**が残る。Phase0の「fitが次のbottleneck」という予想をfit単独の結論にはしない。

これらのabs component sumsは加算分解ではない。signed closureだけを保存し、相殺を保持する。RitzのtotalがA3より少し低いことは、fit/proxy/state残差の相殺を含むtotal metricの結果で、exact targetより良いstateを得たことではない。sign-crossing componentwise risk attributionは行わない。

## D. Underestimation and fixed Outcome

A0/A1のS_under=0、A2は正。S_under ratioはA0分母0なのでnull。Accuracy改善とunderestimation方向の改善は一致しない。A/Bのresponse_S_under<A0がfalse、Cのpoint改善かつboth-improvement不成立がtrue。Dの候補predicateもtrueだが、固定precedence C→Dで**C**を採用する。mixedへもAへも再分類しない。全predicate traceをscientific_outcome.jsonに保存した。

## m diagnostics, primary remains8

responseのS_absはm1 1.21383546051e-07、m2 8.93027971379e-09、m4 2.49733882385e-09、m8 4.59838762441e-09 Haで非単調。m1は全12行で悪化、m4はm8より小さい値だが、**m4へselectorを切り替えない**。response S_underはm1/m4/m8=0、m2=8.93027971379e-09。

Ritz S_absはm1 7.3060586594e-08→m2 5.49176325471e-09→m4 4.57279156013e-10→m8 1.27455952822e-11。raw trendだけをmechanism diagnosticとして保存する。primaryは事前固定m8。

## Phase0 oracle comparison

Phase0のpooled H4/current_m3166 rows、CISD46 rows across PFsは今回の12-row分母と異なるため、歴史的pooled headroomへのrealized fractionは計算しない。Phase0 recipe（fitを固定しstate項だけ除く）を今回の同じA0/eval12へ適用したscalar counterfactualを別artifactに保存した。

matched oracle S_abs=1.0997672393e-10 Ha、baselineとの差=7.78076462029e-08 Ha。realized fraction=(S_abs_A0−S_abs_method)/(S_abs_A0−S_abs_matched_oracle)で、response=0.942314012574、Ritz=1.00124963462。Ritzが1を超える値は、refitted interventionとheld-fit oracleが異なるためで、clipせず「100%超のstate correction」や普遍上界とは解釈しない。oracleは実現可能なoperational armではない。

## E. Next research implication — GPT/user review required

観測上、state improvementはこのH4固定座標のaccuracyへ利益を残し、ordinary RitzがresponseよりaccuracyとPF回数で優位だった。response-specific支持の固定Outcome Aは未達。generic state improvementの再定義とfit/finite-time proxy残差の整理は、次の判断材料として提示する。ただしOutcome CとS_under baseline floorを尊重し、response-specific method／generic methodへの方針変更、fit変更、state-correction停止の採否はGPT/ユーザーに残す。

N2/CO/HF、new QPE budget、selected time/PF変更、resource savingの次stageは開始しない。Level3達成とは書かない。

## History, denominator, limitations

Attempt1はserialization failure後にprediction freezeなし、truth0。Attempt2は同じscience protocolのtechnical retry1回で成功freeze。Attempt1を科学結果の分母に二重計上せず、両auditを変更せず保持する。今回のPhaseBだけがsaved direct12 / exact22を使用した。

このdataは既知development再利用でありprospective/independent holdoutではない。12 evaluationと22 proxy rowsは座標数で、正負時刻やstate/PFを独立標本として扱わない。固定H41系1PF1入力の証拠を分子全体やresource価値へ一般化しない。全値・quality・sign-crossings・null ratiosを残す。
