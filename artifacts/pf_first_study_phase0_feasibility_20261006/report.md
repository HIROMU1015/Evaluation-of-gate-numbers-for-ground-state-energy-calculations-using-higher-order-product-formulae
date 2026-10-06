# 第1研究 Phase 0：state-induced biasに介入する価値の監査

2026-10-06 / post-hoc feasibility audit / new science calculation = 0。

推奨は **GO_response_pilot**。H4でstate誤差のmechanism headroomとunsafe方向への寄与があり、N2/COには別途resource headroomが残る。ただし両者を結ぶ実分子の因果証拠、oracle-freeな補正器、追加校正費用を含むnet gainは未確立である。これは次段の最小pilotを検討する価値の判断案であり、研究方針変更・algorithm成功・pilot実行を承認するものではない。最終採否はGPT/ユーザーに残す。

## 目的・authority・保持したformal結果

最終synthesis、claim ledger、completion analysisをauthorityとし、第2研究v2のpoint accuracy / budget safety / resource valueの区別を解釈へ用いた。旧途中方針を採用していない。指定16資料と補助15資料の31 sourceを固定snapshot `c515562f1c00b5402d5ca266852986ba12ca4002` と照合した。

formal結果は79/128 state dominant、49/128 mixed、S4 no-benefit、S0 gamma=1.01で6/6 safeのまま。128はcase単位、今回の1,536行はcase × sign × evaluation timeであり、独立標本数ではない。BはH4 56 case・672行、Cは二準位72 case・864行。Cの各lambdaを別caseに保ち、分子での頻度へ一般化しない。positive/negative timeも独立反復ではない。

全行をCSVに保持した。predictionの主診断は保存model_status=fit_okかつquality_class=resolved（B 588行、C 720行）。216行のnot_identifiable、144行のunresolved等を消さず、全行・状態別・PF別・時刻別の再集計を併記した。Phase平均はfitを使わないので、4 proxyすべてresolvedのquartet（B 134/144、C 180/216）を別の主集計とした。これらは解析分母であり、formal判定規則の変更ではない。

## RQ0-3 / Analysis A：phase quartetで何が消えるか

列定義をsource codeから確認した。保存gは `proxy_imag_hartree = Im(<psi|echo|psi>)/t`、予測は `fhat_approx_hartree`。保存されている別量 `proxy_arg_hartree` は使っていない。この区別によって、phase平均の線形性を主張できる。

`G(t)=(echo(t)-echo(t)^dagger)/(2 i t)` と書くとgはHermitian Gの期待値であり、同じground/chi方向について

`E_state(q,phi) = q*(G_chichi-G_00) + 2*sqrt(q*(1-q))*Re(exp(i*phi)*G_0chi)`。

quartet平均はcross成分を消し、`E_state_avg=q*(G_chichi-G_00)`を残す。保存値の`E_int=E_state-E_state_avg`をcoherent interference、平均残差をこのcontrolled族におけるdiagonal population成分として分けられる。この解釈を非線形arg proxyへそのまま適用しない。一般のRHF/CISDで実装可能な位相操作やresponse estimatorが得られたという意味でもない。

H4のresolved quartetで、pooled絶対state誤差は **26.9828%**減った。二準位Cでは **96.5910%**。全complete quartetでもB 26.9842%、C 96.5910%である。Cの大きな改善をH4や実分子へtransferしない。

| H4 PF | resolved quartets | pooled絶対state誤差の減少 | interferenceの二乗誤差share |
|---|---:|---:|---:|
| current_m3 | 34 | 40.3166% | 66.1033% |
| m5_best | 28 | 51.1029% | 76.9938% |
| two_term_center | 36 | 23.5713% | 48.1153% |
| yoshida4 | 36 | 26.6054% | 51.8377% |

二乗誤差shareはB全体51.8426%、C 99.7325%。`mean(E_state^2)=E_avg^2+mean(E_int^2)`の直交会計であり、絶対誤差の加算shareではない。個別phaseでは干渉がpopulation誤差を相殺している場合があり、phase平均がそのphaseの誤差を増やす負のreductionも削除・clipしていない。

| H4 absolute time | resolved quartets | pooled絶対state誤差の減少 | interference二乗share |
|---|---:|---:|---:|
| 0.125 | 16 | 25.2587% | 49.1394% |
| 0.175 | 22 | 25.5497% | 49.4603% |
| 0.225 | 24 | 25.9368% | 49.8822% |
| 0.275 | 24 | 26.3076% | 50.4019% |
| 0.350 | 24 | 26.9166% | 51.3570% |
| 0.400 | 24 | 27.3452% | 52.1030% |

時刻別の連続値を残した。単純な全体平均は大きいsignalの時刻・PFに重みを置くので、PF/time別表を併読する。保存3 qをすべてresolved quartetとして比較できるBの42/48座標では、`E_avg/q`の最大相対rangeは9.71328e-06、`RMS(E_int)/sqrt(q*(1-q))`は2.37298e-10。Cでは60/72座標、各7.59577e-06、1.21526e-10だった。丸め・小signalを含む保存値は線形populationとsqrt型interferenceの構造に整合する。新しいexponent fitは0であり、3 qの外へ厳密なpower lawを一般化しない。

## RQ0-2 / Analysis B：oracle removalのheadroomと残る誤差

原fitを固定し、`E_no_state=E_fit+E_proxy`、`hat_delta_no_state=hat_delta-E_state`とした。実際にstateを改善してモデルを再fitした結果ではなく、state項だけを除く代数的oracle診断である。

| 主診断 | rows | 元のabs総和 / Ha | no-state abs総和 / Ha | 総和の減少 | 改善 / 悪化行 | residualでfit / proxyが大きい行 |
|---|---:|---:|---:|---:|---:|---:|
| H4 B | 588 | 0.000326694795 | 3.50192056e-05 | 89.2808% | 566 / 22 | 527 / 61 |
| two-level C | 720 | 0.078729631 | 0.0291153276 | 63.0186% | 540 / 180 | 571 / 149 |

Bのmedian row retentionは0.0014022185、Cは0.047439726。mean of ratiosに置き換えず、pooled効果は総和比で示した。全行の総和減少はB 89.2886%、C 63.0186%で、主集計と整合する。ただしH4 22/588行、C 180/720行は悪化し、signed成分間の相殺を失う。state correctionが全caseを改善するとは言わない。

| H4 PF | eligible rows | abs総和の減少 | residual fit / proxyが大きい行 |
|---|---:|---:|---:|
| current_m3 | 166 | 99.3199% | 159 / 7 |
| m5_best | 86 | 99.7574% | 86 / 0 |
| two_term_center | 168 | 98.8357% | 160 / 8 |
| yoshida4 | 168 | 88.8098% | 122 / 46 |

| H4 state family | eligible rows | abs総和の減少 | 同符号underestimated rows | stateが最大unsafe寄与のrows |
|---|---:|---:|---:|---:|
| cisd | 46 | 98.9020% | 12 | 12 |
| controlled | 494 | 83.2300% | 332 | 316 |
| rhf | 48 | 99.9398% | 12 | 12 |

stateを除くと、H4ではfitが527/588、proxyが61/588で最大residualとなる。Cではfitが571/720、proxyが149/720。これは新しいformal dominanceではなく、2 residual成分の単純な大きさ比較。fitが次のbottleneckになりやすい一方、oracle removal後の総量は元より小さい。PF/state_id/time/q別の全連続値は[summary CSV](mechanism_and_budget_summary.csv)にあり、original case dominanceの79/49を併記して保持した。

## RQ0-1 / Analysis C：absolute dominanceとunsafe方向は同じか

`u=abs(delta_direct)-abs(fhat_approx)`を直接計算した。signed total errorの符号をunsafeと同一視していない。同符号rowだけ `u_k=-sgn(delta_direct)*E_k` を使い、sign-crossingでは3成分ともnullにした。stateのunsafe最大寄与は正のu_kのargmaxであり、3倍・過半数という元のformal dominance ruleを再定義していない。

H4主診断は588行中576行が同符号、12行がsign-crossing。同符号の過小評価356行中、stateが最大unsafe寄与なのは **340/356 (95.5056%)**、fitは16/356、proxyは0/356だった。よってこのH4範囲では「大きいだけ」に留まらず、state errorはunderestimation方向にも主要である。一方stateは同符号576行中220行 (38.1944%)でconservative方向へ働いている。大きいstate errorを一律riskと呼ばない。

H4のpositive underestimation総和は0.000290508041 Haから1.78470802e-05 Haへ **93.8566%**減った。ただしunderestimated行数は356→343で、全行が安全になるわけではない。u>0はmarginを要する方向であり、gamma込みfrozen budgetのunsafe判定そのものではない。機構表の固定時刻はH4のselected t=2.1466でも、実分子6条件のselected timeでもない。

C主診断は720行中230行sign-crossing、490行同符号。同符号過小評価130行でstate最大は71、fit最大は59、proxy最大0。state conservativeは318/490。oracle removalでpositive underestimation総和は **77.9324%**減るが、全符号を含むunderestimated行数は202→250に増える。人工相殺系ではstateとfitの相殺がriskに影響し、補正が普遍的に安全性を改善するという主張は支持されない。全保存行のCにはproxy最大unsafe寄与48行があるが、それらはnot_identifiable/unresolved側の診断なので確立したproxy bottleneckの頻度として主張しない。

## Analysis D：6条件margin-capacity

completion analysisのbeta=1.2、epsilon=0.00015936001019904 Ha、gamma=1.01を保持した。`M=(1-1/gamma)*(epsilon-c)`、`slack=M-(e-c)`を再計算し、元の`energy_margin_gamma_1_01_hartree`と全6条件で一致した。最大差は2.37169e-20 Ha。

| condition | c / Ha | e / Ha | e-c / Ha | M_1.01 / Ha | safety slack / Ha | gamma_req | original safety |
|---|---:|---:|---:|---:|---:|---:|---|
| N2_active_eq_sto3g | 3.0348397e-05 | 2.1708889e-05 | -8.6395085e-06 | 1.2773427e-06 | 9.9168512e-06 | 0.93723619 | True |
| N2_active_stretch150_sto3g | 2.8064634e-05 | 8.5685917e-06 | -1.9496043e-05 | 1.2999542e-06 | 2.0795997e-05 | 0.87070854 | True |
| CO_active_eq_sto3g | 2.9756708e-05 | 1.9985414e-05 | -9.7712941e-06 | 1.283201e-06 | 1.1054495e-05 | 0.92989186 | True |
| CO_active_stretch150_sto3g | 2.8587321e-05 | 1.5196991e-05 | -1.339033e-05 | 1.2947791e-06 | 1.4685109e-05 | 0.90711675 | True |
| HF_full_eq_sto3g | 1.0751002e-06 | 1.9998854e-06 | 9.2478527e-07 | 1.5671773e-06 | 6.4239205e-07 | 1.00587687 | True |
| HF_full_stretch150_sto3g | 9.4702743e-07 | 5.14051e-07 | -4.3297643e-07 | 1.5684454e-06 | 2.0014218e-06 | 0.99727424 | True |

gamma_reqは `(epsilon-c)/(epsilon-e)` のpost-hoc診断だけで、operational gammaにしていない。conservative条件の値が1未満になるのも式の値として残した。HF eqのunderestimationは固定margin内に収まる。第2研究v2のHF cheap gamma1.01 unsafeは別のprediction/armであり、第1研究S0の6/6 safeと矛盾しない。両armの分母・budget contractを混ぜない。

## RQ0-4 / Analysis E・F：resourceに残る価値

`H_cal=1-1/(F_model*F_margin)`は、truthを無料で得て固定marginも除いたsame-time continuous-cost診断。state-specific gain、実測のresource削減、net gainではない。gammaを1.01に保ったperfect-prediction saving `1-1/F_model`も併記し、gammaを取り除く価値をstate correctionの利益へ混ぜない。

| condition | H_cal | perfect prediction・固定gamma saving | F_time | F_total | 同一PF/cap truth-free最大saving上界 |
|---|---:|---:|---:|---:|---:|
| N2_active_eq_sto3g | 7.2043% | 6.2764% | 1.021338 | 1.100631 | 57.4624% |
| N2_active_stretch150_sto3g | 13.7912% | 12.9291% | 1.227600 | 1.423985 | 60.4256% |
| CO_active_eq_sto3g | 7.9315% | 7.0108% | 1.031843 | 1.120734 | 58.1307% |
| CO_active_stretch150_sto3g | 10.1865% | 9.2883% | 1.071820 | 1.193383 | 59.6194% |
| HF_full_eq_sto3g | 0.4082% | -0.5877% | 2.141534 | 2.150313 | 1.6581% |
| HF_full_stretch150_sto3g | 1.2600% | 0.2726% | 2.076361 | 2.102857 | 1.5785% |

| condition | F_model | F_margin | F_calibration | F_within | F_domain | F_PF | coverage |
|---|---:|---:|---:|---:|---:|---:|---|
| N2_active_eq_sto3g | 1.066967 | 1.010000 | 1.077637 | 1.021338 | 1.0 | 1.000000 | exact_saved_grid_only |
| N2_active_stretch150_sto3g | 1.148490 | 1.010000 | 1.159975 | 1.2276 | 1.0 | 1.000000 | exact_saved_grid_only |
| CO_active_eq_sto3g | 1.075394 | 1.010000 | 1.086148 | 1.031843 | 1.0 | 1.000000 | exact_saved_grid_only |
| CO_active_stretch150_sto3g | 1.102394 | 1.010000 | 1.113418 | 1.07182 | 1.0 | 1.000000 | exact_saved_grid_only |
| HF_full_eq_sto3g | 0.994157 | 1.010000 | 1.004099 | <=1.012709 | >=2.114659 | 1.000000 | analytic_bound_at_cap |
| HF_full_stretch150_sto3g | 1.002733 | 1.010000 | 1.012761 | <=1.003236 | >=2.069664 | 1.000000 | analytic_bound_at_cap |

N2/COの7.20%-13.79%は、state-related calibrationを試す際にresource評価を残す理由になる。しかし保存6条件にはselected timeの三分解がないため、この余地をstate correctionの回収可能量とは同定できない。N2 eq、CO eq/stretchは既存会計でcalibration側が大きく、N2 stretchはtime factor=1.227600がcalibration factor=1.159975を上回るmixedな課題である。新しい分類thresholdは作っていない。

HFはcalibration-limitedというよりtime/domain-limitedな境界。完全same-time校正後にもF_time=2.141534/2.076361が残り、F_domain下界は2.114659/2.069664。gamma固定ではHF eqのperfect prediction savingは負 (-0.5877%)で、state correctionがunderestimationを直すこととbudgetを縮めることは逆向きになり得る。

truth-free上界は `C(P,t)>=beta*K_P/(T*epsilon)` から `H_max_domain=1-beta*K_P/(T*epsilon*B0)` を計算した。関数入力にeやtruthはなく、K、T、epsilon、beta、B0は凍結prediction/decision trace由来。HF上界は1.658056% / 1.578484%。従来の`e(T)/epsilon`によるwithin-time saving上界（1.254948% / 0.322572%）とはbaselineが異なる。今回の式はB0からのsavingで、calibration余地も含むため両者を同じ数値とみなさない。

active-spaceで約57%-60%というdomain上界は、e=0、t=Tの理想費用下限を置くため緩い。実現可能なsaving、continuous global optimum、cap外の安全性、PF変更まで含む上界とは主張しない。HFのF_within/F_domainはboundsのまま、active-spaceのexactは保存grid会計だけに限る。個別CSVにはactual total regret=F_total-1、両headroom、factorの区間を同じrowに残した。

## 研究として新しく見える点・到達点

Phase 0自体は新アルゴリズムではない。新しい可視化は「state errorの大きさ → 位相干渉とpopulation → unsafe方向 → 同時刻resource余地 → domain境界」を分けて見ること。H4ではunsafe寄与も確認できたため、第1研究を、介入可能なstate-induced biasとresource上の価値を識別するfollow-upへ発展させる根拠がある。既存formal paperの中心claimを今回のpost-hoc結果で改稿していない。

1. **State-robust PF calibration mechanism**：最小pilotの妥当な第一目標。phase quartetはmechanism対照として使えるが、exact groundを含むcontrolled状態を準備できる実用法が得られたとは言えない。
2. **Resource-improving calibration method**：N2/COの一部条件で検証する価値は残る。oracle-free response rule、prediction freeze、誤差予算の安全性、追加measurement/state-preparation/classical costを含むnet valueのすべてが必要。現時点の到達結果ではない。
3. **Calibration improvementが無価値になるresource boundary**：HFの同一PF/capでは上界が小さく、大きなregretをstate correctionだけで取り戻すことはできない。普遍的な無価値性ではなく、指定domain内の境界として述べられる。

exact-ground targetを変えずstate sensitivityを減らすresponse-corrected calibrationは、次段のalgorithmic contribution候補。既存scalarから線形response係数を取り出せても、exact情報に依存しない測定法、population補正、fit残差の扱い、コスト優位は別問題である。今回の監査は先行研究との新規性調査を行っておらず、新規アルゴリズムとしての優先権・noveltyは未確認。

## Go / No-Goと最小pilot案（未承認）

総合推奨は **GO_response_pilot**。A mechanism headroomとB safety relevanceはH4の保存値で支持され、C resource headroomは少なくともN2/COの一部に残る。D residualではfitが次のbottleneckとなり、HFではdomainが残る。この組合せは小規模pilotの価値を支持するが、成功予測ではない。結果後の数値Go閾値は新設していない。

GO_mechanism_onlyはHF cap内の到達目標として適切であり、oracle-free補正器や実分子でのcost advantageが得られなければ全体の次段もその範囲へ限定する。NO_GO_state_correctionを全体へ選ぶほどheadroomが消えている結果ではないが、実用方式は将来の独立事前固定評価で棄却され得る。判断の採用はGPT/ユーザーに残す。

新規scienceより先に、response estimatorがexact targetを維持しoracle情報を使わない仕様と、追加費用の数え方をGPT/ユーザーが確定する必要がある。Phase averagingはground/chiに依存する機構oracleで、実用response ruleの代用品ではない。

未承認の最小mechanism pilot案は、保存H4 1系・current_m3 1 PF・既存CISD 1入力を基本とし、元5 training +6 evaluation絶対時刻を両signで使うこと。評価truthをprediction freeze後に開き、既知development値の再利用をprospective/holdoutと呼ばない。任意の新q/geometry/PF、gamma/selector調整を加えない。この座標ではdirect truthは保存済みなので新規ground/Hamiltonian/direct truthは0で済む。

具体的response方式が未定のためaction数は条件付きの見積りである。1〜2 extra probe/channelをrとし、全11絶対時刻を±で測るなら追加PF actionは **22*r=22〜44回**、trainingだけなら10*r=10〜20回。時刻に依存しない補助stateが必要なら0〜2 state準備。補正モデルのfitは1組をfreezeする案であり、今回は実行していない。既存phase平均だけなら追加actionは0だが、新しいresponse方式の実証にもならない。4 phaseを新たに測る方式ならbaselineの4倍の校正actionとなり、同じcost estimateでは扱わない。

mechanism支持後にresourceを調べる最小拡張候補は、calibration側の余地が残る既使用N2/CO 1条件・current_m3だけ。別protocolでselected time/budgetをfreezeする。未保存selected timeならdirect truthは概ね1〜3 selected/local座標/条件に加え、必要なbranch anchor。Schur/eigensolveはそのdirect truth取得に伴うもので、具体的countとstate/response actionは別承認時に確定する。targeted改善に見える値だけを選んで評価集合と呼ばない。

## 検証・停止

11 focused testsが合格。両符号のrisk恒等式、sign-crossing attribution禁止、相殺除去による悪化、ゼロ分母、quartet completeness、population/interference分離、truth-free bound、gamma恒等式、stdlib-onlyのimport境界、全数値artifactのbyte再現、原本source identity、既存output上書き拒否を確認した。

三分解closure最大2.1684e-19 Ha、same-sign risk closure最大1.0842e-19 Ha。原本hashは開始・終了時に31/31一致。sourceのorigin/result commitとsnapshotは別fieldに保ち、manifestは自己除外。CSV内のnegative reduction、sign-crossing、not_identifiable、unresolvedも残した。

Phase 0はここで停止する。新規science、pilot、S4 redesign、formal claim変更、gamma/selector tuningを開始しない。GPTへのレビュー項目は、GO推奨の採否、oracle-free responseの具体仕様、mechanism→resource bridgeを確認する最小範囲、論文に追加するならfollow-upとしての配置。
