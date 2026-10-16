# 高次PFの有限時間固有位相誤差研究：完結性監査

監査日：2026-10-16 JST。Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。
本書の分類は静的監査上の判断であり、既存のformal status、研究方針、GO/STOP、実行承認を変更しない。

## 1. 監査結果

**有限時間での先頭則の破綻、先頭係数と演算子の違い、4次PFのa8における状態混合、proxyと対象固有位相の違い、安全性と資源効率の分離には、限定された主張として完結した成果がある。** S4と第二研究v1の失敗も、事前固定した方式に対する完了したnegative resultである。[F02] [F03] [SYNTH] [CLAIM] [V1]

一方、全電子系を含めて有限時間モデルが成立する条件を事前に判別すること、安価な高次係数取得の一般性、離散最適時刻のサイズ移送は未確立である。FS-R1は新source上のpredictionが凍結されているが、資源利益の問いはtruth未採点のまま残る。これらを独立研究として正式採択できるとは、本監査では判断しない。[HF] [H05] [SCALE] [FSA] [FSB]

「理由が全く不明な現象」が広く放置されている、という結論にはならない。F02/F03/F05、HF bridge、D1、H4 pilot、2026-10-07のA1/A3/A6/B3によって説明は進んでいる。残る中心的な不足は、**局所の機構説明を、使用時刻・対象枝・残余誤差予算に結び付く適用条件へ閉じられるか**である。一般の摂動公式を再提示するだけでは、この不足を埋めたことにならない。[F05] [D1] [H4] [EXP] [STRATEGY]

## 2. 確認方法と資料の世代

GitHubの120 remote headsを取得し、既存120 remote-tracking refsとの一致を確認した。branchの存在だけを研究完了の根拠にせず、主要report、decision、protocol、保存scalar表、manifestを固定commitから読み取った。監査用の独立bare repositoryにもGitHubから取得し、参照blobのbytes・Git blob SHA・SHA-256を照合する。全branchの全科学結果を再検証した監査ではない。詳細な取得範囲は[provenance.json](provenance.json)に記録する。

読取りでは科学runnerをimport/実行せず、保存数値の再集計・再採点・再ランキングも行っていない。以下の件数・係数・費用は原report/保存表の引用である。旧資料に記録された科学計算件数を、今回の実行件数へ加えない。

| 世代 | 固定資料 | 現在の扱い |
|---|---|---|
| 旧入口 | main `20d64c2fea1ed2d2188777df4f3d962ee94df486`、status更新2026-09-22 | 9月末・10月の正本として使わない。[MAIN] |
| 事前検証 | `e820f653a5916f27233ab4674a89d288cf969e37` | F/H report・数表・protocolの確認snapshot。[F01] [F02] [F03] [H04] [H05] |
| 第一研究formal | `cd81018932b9557b7a55e2e1cd8c5e3988245409` | S0–S4の完了と9/26 claim ledger。S4 beta不一致はcompletion analysisの訂正範囲を優先。[CLAIM] [COMP] |
| R1後の再設計 | `0d13decb8793c5e6fd83075b1559e05424f93c04` | 提案・計画。D1/D2や10月結果の存在で更新して読む。[REORIENT] |
| 第二研究Direction C | `e895870f16878ee4181b0e0dfe3159826a791563` → `1d01e77247364b49dbce2e9ce2fe7c32af0fb937` | 承認済みscope、prospective・geometry・rankの後続証拠。native H-chain closed=0は集計バグで、訂正版18を使う。[DIRC] [EVMAP] [CORRECTION] |
| 10/7条件拡張 | `19362c23ccdc16b6ad0ff547cc363e138a3930d2` | A1/A3/A6/B3完了。古いH4-only・未確認点の説明をそのまま一般化しない。[EXP] |
| 第一研究follow-up最新 | `a7644d5ebe64b66044461623506093ac6b0a1206` | FS-R1-B0はpreflight GO。Phase B science未承認・truth 0。[FSB] |

監査branchの起点は最後のB0 snapshot。別系統の既存資料は元公開branchの固定commitリンクで参照し、複製・merge・science sourceの変更をしない。provenanceは監査branch祖先内の資料と、別公開branchで取得可能な資料を区別する。ローカルの整理中pathや未追跡artifactを、新しい公開根拠に置き換えていない。

## 3. Phase A：科学的問いごとの分類

分類単位を狭い問いへ固定する。例えば「a8分解が説明できた」と「一般分子で有限時間域を事前認証できた」は別の問いである。

| ID | 科学的問い | 監査分類 | 到達点／残る境界 |
|---|---|---|---|
| Q01 | 形式次数の先頭則はQPE使用時刻でも十分か | `COMPLETED_WITH_SUPPORTED_CLAIM` | 一律には十分でない反例と誤差床を確認。一般的破綻率は不明。[COST] [WINDOW] |
| Q02 | 小さいa4は小さい誤差演算子を意味するか | `COMPLETED_WITH_SUPPORTED_CLAIM` | 意味しない。H2/H4と人工分割族で構成的に示した。[F03] |
| Q03 | 4次PFのa8を直接項と状態混合へ分けられるか | `COMPLETED_WITH_SUPPORTED_CLAIM` | 非縮退局所摂動の既知構造を8条件で確認。全有限時刻への保証ではない。[F02] |
| Q04 | 小さい高次係数を安価・安定に取得できるか | `PARTIALLY_RESOLVED` | exact response等の小系検証は完了。D8構築・近似状態・未使用系の費用保証が残る。[H05] |
| Q05 | NH3のfit失敗・孤立dipは数値床／枝取り違えだけか | `COMPLETED_WITH_SUPPORTED_CLAIM` | grid効果をfloor効果から分離。特定dipは同一枝で再現。連続大域最小は未証明。[TIME] [NH3BR] |
| Q06 | 一項・二項・三項の固定モデルはどこまで移送できるか | `PARTIALLY_RESOLVED` | NH3とN2/COの限定的支持、HF伸長等の失敗。一般適用条件は未確立。[NH3MOD] [HOLDOUT] |
| Q07 | gap・相殺・相関から成功／失敗理由を一意に説明できるか | `OPEN_QUESTION_WITH_EVIDENCE` | gap単独説は不十分。HF対では複数機構が共変し、唯一原因・事前判別は未確立。[F05] [HF] |
| Q08 | exact-state overlap proxyはPF対象固有位相と同じか | `COMPLETED_WITH_SUPPORTED_CLAIM` | 同じではない。HCl圧縮診断、H4/H6のspectral分解で機構を確認。[D1] [H4] [EXP] |
| Q09 | 校正精度、安全なcap、低資源費用は同じ目的か | `COMPLETED_WITH_SUPPORTED_CLAIM` | 違いと費用因子を第一研究の範囲で確定。一般safe certificateはない。[CLAIM] [COMP] |
| Q10 | S4二状態診断／第二研究v1の固定方式は利益を示すか | `COMPLETED_WITH_NEGATIVE_RESULT` | 事前固定benefitを満たさず完了。改善方式一般の不可能性ではない。[SYNTH] [V1] |
| Q11 | D2-Aのbranch失敗は物理的に誤枝を回収したことか | `COMPLETED_WITH_SUPPORTED_CLAIM` | integer比較0/6と物理枝6/6の座標系不一致を監査。元formal STOPは不変。[D2AUD] |
| Q12 | direct最適時刻・高次PFの順位をサイズ外挿できるか | `PARTIALLY_RESOLVED` | 離散小系証拠はあるがY8則不成立、H5/Y8 gate失敗、未使用サイズ則は未確立。[SCALEOLD] [SCALE] |
| Q13 | FS-R1のstate/local介入はsafeな資源削減を与えるか | `OPEN_QUESTION_WITH_EVIDENCE` | 新source predictionは凍結済み。12点truth ladderと2終点採点が未実施。[FSA] [FSB] |
| Q14 | Direction Cの固定scopeは科学的に閉じるか | `COMPLETED_WITH_SUPPORTED_CLAIM` | 信頼性・headroom・point/width/採用制約の限定主張は既存成果で閉じる。[DIRC] [EVMAP] [CLOSURE] |
| Q15 | HF/HCl/prospectiveでPF/H-reference誤差分解を閉じたか | `INCONCLUSIVE_EVIDENCE_MISSING` | absolute target correspondenceが不足。shift/branch診断だけで補完しない。[EVMAP] |
| Q16 | historical H01復元、S5、旧方式の運用採用を続けるか | `STOPPED_OR_NOT_ADOPTED` | 正式停止・未採用を保持。停止そのものを未解決科学の証拠にはしない。[FSC06] [FSR0] [SYNTH] [DIRC] |

## 4. 問い・仮説・結果・証明の対応

### Q01：有限時間の有効次数、符号反転、順位

当初の問いは`alpha*t^p`からの解析時刻・費用がdirect PFでも妥当か、である。検討した説明は高次項、符号相殺、数値床、proxyと固有値の差。保存棄却表では0.1 kcal/molのH2/H4/H5/H6についてm5・Y8とも解析時刻が10%先頭則適合域外で、H7も有限時間比・局所次数の診断がある。Y8は高次2項を加えてもH2–H6の解析時刻を一律には覆わない。[COST]

H4/H5の8次・10次窓では、信号が数値床を越えた時点ですでに観測次数が変わる例がある。形式次数の代数検証と有限精度のfree-fitを同一視しない。数値的反例の成立は完了しているが、全PF・分子・精度での順位や破綻確率は証明していない。広時間費用JSONにはproxyとdirectが別fieldであり、legacyの`analytic_and_measured_ranking_agree`をdirect順位一致と読み替えない。[WINDOW] [WIDE]

Morales論文も短時間則の適用条件と有限時間関数による比較を扱う。本repositoryで「有限時間で先頭則が崩れ得る」という一般論を新たな独立中心成果として二重計上しない。[L3]

### Q02・Q03：a4相殺とa8状態混合

F03の仮説は、エネルギー先頭係数の小ささがD4全体の小ささではなく、対角期待値の相殺を表し得ること。H2/H4×4 PFで、m5のcentered D4 actionは`|a4|`の40–67倍だった。人工族ではa4零点へ近づいてもD4が有限で、同一枝で先頭則使用時刻の誤差が増えた。これは当該族での構成的機構と数値検証であり、分子での発生頻度の証明ではない。[F03]

F02は、局所的な対称4次有効Hamiltonianと非縮退基底状態について、既知の摂動構造

`a8 = <0|D8|0> + Σ(n≠0) |<n|D4|0>|²/(E0−En)`

を保存演算子で検証した。最適化PFでは正のD8期待値と負の混合項が相殺し、two_term_centerの正味a8は成分絶対値和の1.2–3.5%だった。縮退励起群は基底に依存しないgroup和で扱った。係数分解の問いは完了している。小さい正味a8から有限時間全域の小剰余を結論することはできない。[F02] [STRATEGY]

F01の有限log検証窓は、任意時刻の収束半径の証明ではない。これらは主として4次・H2/H4であり、6次/8次や全電子全分子の統一機構を完了したとは扱わない。固有値／固有ベクトルの分離、対角BCHへの着目自体には先行研究がある。[F01] [L1] [L4]

### Q04：係数の識別と取得費用

F02では通常倍精度の5項direct fitで相殺後a8が3窓すべて安定したのは3/8。曲線残差が小さくても小係数の機構を同定できない、という識別性の結論であり、恒等式の失敗ではない。F02の窓・50%相対係数基準はaudit内protocolに固定されている。[F02]

H05はexact BCH＋responseで8/8、D8対角項だけで6/8、HF responseで4/8、CISDで7/8の残差基準を記録した。exact a4＋保存tail2点の方式も8/8だが同じdevelopment集合で選ばれ、exact a4とdirect点を必要とする。H04はD4のsymbolic blockerを解いたが、D6/D8構築・dense入力・状態vectorの費用を解消していない。H05 online timingはD6/D8構築と元direct点取得を除外する。[H04] [H05]

従って「安価でoracle-freeな高次係数取得法を完成」は未支持。固定H05方式の未使用系評価が後続で同じ設計のまま実施された証拠は、今回の参照資料には見つからない。他の三点・五点holdoutは設計が異なり、代用しない。新しい命題や実装を作らず、残件だけを[options](research_completion_options.md)に示す。

### Q05・Q06：NH3診断から固定holdoutまで

時間窓×floorの2×2監査ではgridだけで7/24のfit statusが変わり、floorだけでは0/24だった。特定のNH3 stretch/joint_refineのdipは独立PF構築、greedy/global連続枝、maximum-ground枝が一致し、再現可能な同一枝上のgrid-local現象となった。旧TIME reportの「物理的か枝問題か未確定」を、そのまま現在の欠損とは扱わない。数学的な全時刻の滑らかさ・大域最小は証明されていない。[TIME] [NH3BR]

統一NH3比較は同じgrid選定に用いたdevelopmentで、Yoshida4の二項／三項、Yoshida6の三項が4条件に同じモデルで合格した。一方、m5_bestは0/4、最適化4次の全電子transferは不十分だった。条件ごとの最良モデルを後付けに選ぶ診断と、固定モデル基準を分ける。[NH3MOD]

後のN2/CO CAS(10e,8o)平衡・1.5倍伸長holdoutでは、Yoshida4/current_m3/two_term_centerの二項とYoshida6の三項が主4/4に合格、m5は0/4。これは当時の未使用4条件であり、以後の方式に再利用すればdevelopmentになる。五点校正はoracle-assisted。HF全電子stretchの失敗を、active-spaceの完了した肯定主張へ差し戻さない。[HOLDOUT]

一項、同じdirect点で再fitした一項、二項を分けた履歴比較と、固定モデルholdoutは存在する。二項化の効果を係数再校正だけへ還元するのは不適切だが、この事実は未知全電子系での必要十分条件ではない。[HANDOFF] [HOLDOUT]

### Q07：相殺・励起スペクトル・電子相関による説明の不足

F05は最小物理gapの励起群がD4混合を支配しない例を示し、支配群gapは最小gapの3.21–8.94倍だった。結合行列要素とPF依存の有限時間位相圧縮が必要で、最小gap一つでは不十分という限定結果は完了している。[F05]

HF bridgeではYoshida4のeq pass/stretch failを固定し、a4、結合、D8、混合、物理gapを同じsourceで調べた。stretchで相対高次寄与が増え、normalized phase compressionは両方1だった。しかし複数量が同時に変わるため、report自身が唯一原因の証明を否定している。電子相関descriptorから任意分子の失敗を事前に判別した証拠もない。[HF]

後続A1はH6の信号判定を満たす46 caseでstate31/mixed15を報告し、H4元56ラベルのうち6 caseもnot_identifiableだったと区別した。formal128 caseの79/49は原分類として保存し、信号適格性を無視した一般支配則にしない。H6の短時間分類は長時間A3の因果説明そのものでもない。[SYNTH] [EXP]

未解決なのは「機構が存在するか」ではなく、共変する量から有限時間の成立／不成立を分ける条件が得られるか、である。既存のgap摂動boundや軌道変換研究との差は必要であり、電子相関との相関表だけを新しい統一理論としない。[L1] [L2] [L6]

### Q08・Q11：proxy、spectral成分、枝定義

R1後計画に残ったHCl proxy差の圧縮仮説はD1で検証され、既存6点でweight-ranked K≤4の固定criterionを満たした。これはoracle診断でありtruth-free法の完成ではない。D2-Aの旧integer branch比較0/6は後の表現不変監査でphysical branch6/6と区別された。最大shift errorは約1.38e−8 Haだがbaseline未満budgetは0/6、元formal STOPは不変である。[D1] [D2] [D2AUD]

H4 pilotではstate改善後にもfitとexact-proxy/direct差が残った。10/7 A3ではH6の指定長時間点で非対象weight約0.513%の寄与が対象寄与の約5.18倍だった。高いtarget overlapだけでは微小な対象shiftと同じproxyを保証しない、という機構例は追加済みである。A3が調べていない元selected pointの帰属は未確認のまま。[H4] [EXP]

したがって、一般のspectral恒等式や「proxy≠eigenphase」を新たな未解決研究として再採択する根拠は弱い。運用時の枝同定、有限情報による厳密width、費用便益の保証は別の強い問いで、今回未達である。[L1] [L3] [L4] [DIRC]

### Q09・Q10：第一研究formalと第二研究v1は完了

第一研究の中心claimは校正・時刻域・marginの資源伝播である。S0の6 development条件は1%余裕付き予算でsafeでも、HF総費用因子は約2.15/2.10。保存2PF格子ではPF選択因子1で、HF cap内改善の上限とdomain損失下界を分けた。代数恒等式とcap点の条件付きboundはあるが、cap外安全性や連続大域最小の証明ではない。[CLAIM] [COMP]

S4のtargeted診断は固定benefit不成立、S5は非実施。S4の保存beta=0.105と費用式beta=1.2の不一致は9/26監査で扱われ、42/42安全とno_benefitは不変だった。原S4の絶対marginをそのまま引用しない。第二研究v1のmultiple-window ruleも4/4 safety等を満たさず`complete_no_benefit`。これらは未完了の成功法ではない。[SYNTH] [COMP] [V1]

10/7 B3の0.75 capはHF二条件の予測選択でunsafe。0.5/0.75/1.0の結果は単調ではなく、個別Yoshida4の安全な結果でselectorを救済していない。旧formalのno_benefitを覆したとは扱わない。[EXP]

### Q12：direct最適時刻とサイズ則

当初の狙いは、directで得た最適時刻と費用を大きい系へ移すこと。保存partial reportではeven H2/H4/H6のm5 power lawは小系の有望性に留まり、Y8は予測可能なpower law不成立だった。後のH5/H7 interimはH7の31点/PFを完了しており、旧partialの「H7実行0」は最新状態ではない。ただしH5/Y8はbranch gate失敗で科学的採点対象外、odd-familyのH5/H7/H9 fitも未実施である。[SCALEOLD] [SCALE]

10/7 A6ではH4局所最小の費用が約3.94%動き、元固定予算の約2倍という傾向は残った。離散最小の精密値と費用差の定性的主張を分離する必要がある。サイズ外挿、連続最適性、6/8次の一律な優位条件は依然未確立だが、停止したから未完了と判定したのではなく、保存LOO・枝gate・刻み依存がその不足を示す。[EXP] [L3]

### Q13：10月FS-C0〜FS-R1は新sourceの未採点follow-up

FS-C0はstate/localの2×2介入を設計したがbaseline定義とsourceに残件があり、C0.5はsource missing、C0.6はreconstruction mismatch。これらは方法の科学的不支持ではない。historical H01復元路線は正式に終了し、C0.6のone-shot bytesを別のnew regenerated sourceとして固定した。新sourceとの差を手法改善と呼ばない。[FSC0] [FSC05] [FSC06] [FSR0]

R0のbranch未閉鎖はR0.1で固定12点ladderへ進み、初回R1 Phase Aの数値契約不足はA0 v3で閉じた。その後Phase A productionはN2/COの4-arm、cold replay、全8有限budget区間を凍結した。science originは`89c091e885c07b7c02883b1479a143c23f51df3c`、handoffは`e00ebc2024f72272cec64ebfd20c771d03665e95`。originとsnapshotを統合しない。[FSR01] [FSASTOP] [FSA0] [FSA]

最新B0はtruth barrier、保存budget scorer、executor準備を完了しただけで、production truth、Schur、branch continuationは0、Phase B authorized=false。残る問いは「固定された介入がtrue safetyと資源利益を示すか」であり、prediction budgetの大小だけでは答えられない。既存第一研究の完了を取り消さず、既存follow-upとしてC2へ整理する。[FSB]

### Q14・Q15：第二研究Direction Cとの境界

Direction Cの承認scopeは、凍結予算の信頼性、名指しcheap対照からのheadroom、実M1のpoint/width/採用制約である。native H-chainとH6 geometryではsmall-margin sufficiencyが確認された一方、prospective一般分子のgamma1.01は選択decision6/13 safe。分母は16 attempted=13 scored+2 time-domain不適格+1 input-reference不適格で、除外を成功/unsafeへ変換しない。[DIRC] [EVMAP]

rank16/32でpoint精度が改善しても、same-time cheapへの仮想budget advantageは各0/9。geometry15点はwidth coverageがあっても15/15 abstention。point改善だけではresource valueを説明できないという限定主張は既に第二研究の中心成果である。全spectral法の不可能性、新しいcertificate、古典＋量子net advantageまでは示していない。[EVMAP]

H-chainのPF/H-reference分解は確認済みで、native18のclosed=0は訂正済み文書バグ。HF/HCl12とprospective39のabsolute target correspondenceはindeterminateのまま。37/39のbranch/gap互換診断をabsolute identityの完了へ代用しない。これを埋めることは現在の限定中心claimの必須条件ではなく、別の強い主張を要求する場合の残件である。[CORRECTION] [EVMAP]

## 5. 重複、先行研究、未確立の扱い

| 対象 | 重複関係と境界 |
|---|---|
| 第一研究formal | state/proxy/fit分解、safe≠efficient、domain/margin/PF費用分解、S4 negativeは既存中心成果。新研究として再計上しない。[CLAIM] |
| 第一研究follow-up | H4 point改善は実証済み、FS-R1 state/localの資源価値は未採点。既存計画の続きであり独立新テーマではない。[H4] [FSA] |
| 第二研究Direction C | safety/headroom、point/width/採用の違い、確認済みH-chain相殺は既存中心成果。新しい原因名を付けて別成果にしない。[DIRC] [EVMAP] |
| 別PRの第一・第二研究、Track A/B | 本repositoryの固定資料だけでは別PRの全scopeを独立監査していない。合流・変更・独立性の確定は行わない。重複確認が必要ならGPTに別PRのclaim ledgerとの照合判断を求める。 |
| 既知理論 | 固有値摂動、gap依存、compact BCH、subspace/response、有限時間費用比較そのものは新規claimにしない。[L1] [L2] [L3] [L4] [L5] |

一次文献は原文の該当節またはabstractまでの取得範囲をprovenanceに分けた。Yi–Crossonはspectral perturbationとgap仮定、Mehendale等は分子の摂動推定とCISD、Morales等は高次PF・固有値誤差・短時間則外の比較、Maxwell等は対角BCHとcompact表現を扱う。これらに有限時間分子条件の全ての残件が解決済みと書いてあるとは確認していない。[L1] [L2] [L3] [L4]

軌道変換とTrotter誤差、誤差測定を通じた資源推定、既存の高次PF分子論文も近接する。今回は後三者をabstract/書誌の範囲で確認し、全文を読んだ新規性証明には使わない。[L6] [L7] [L8]

## 6. GPT側で判断する事項と停止

1. Q07の適用条件を、既存第一研究の説明補強に留めるか、剰余・枝・情報取得を含む新しい理論的主張として要求するか。既知摂動論との差が必要。
2. Q13を既存follow-upとして完結させる必要があるか。必要なら固定FS-R1 Phase Bだけを別承認するか。今回の監査は承認を発行しない。
3. Q04/Q12を独立研究として扱うだけの具体的な未達claimがあるか。既存D8取得法・有限時間比較との重複、失敗gate、移送範囲を先に判断する。
4. 第一・第二研究の限定claimの論文化はC1として既存成果だけで進めてよいか。未確立の一般保証やnet advantageを必須化しない。
5. 別PR/Track A/Bとの重複は、必要なclaim ledgerを指定してGPT側で判断する。合流は行わない。

具体的な未解決範囲は検出したが、独立新研究の科学的採否・優先順位・論文化可能性は確定していない。
**今回の新規科学計算・科学実装・科学的再集計・再採点・再ランキングはすべて0件。監査資料の作成とGit/hash検証だけを実施し、handoff後Mandatory STOPとする。**

<!-- fixed-source-references -->

[MAIN]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/20d64c2fea1ed2d2188777df4f3d962ee94df486/docs/current_research_status.md
[HANDOFF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3254f79825cfbcc2af91b6c07d01de469d3e4eb6/review_response/pf_cost_predictability_handoff.md
[COST]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/server_cost_validity/integrated_boundary_recheck_20260902/pf_cost_rejection_tests.md
[WIDE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/server_cost_validity/wide_time_cost_analysis.json
[WINDOW]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/46a7ed165650cb80506be14d997380e0bf333680/artifacts/server_pf_window_validation/README.md
[TIME]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/84a37d15ceed616cf8d863efc1e09dbc7be3f2ba/artifacts/server_time_scale_fit_diagnosis_20260920_022258_e4509cb/report.md
[NH3BR]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/76d091f18b7f68b2612dc2c8267bbab5e23c12a1/artifacts/server_nh3_branch_protocol_audit_20260920_222119_d8c1d55/report.md
[NH3MOD]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/46a7ed165650cb80506be14d997380e0bf333680/artifacts/server_existing_pf_unified_nh3_20260920_233516_e692360/aggregate/report.md
[HOLDOUT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md
[F01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/report.md
[F02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md
[F03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md
[F05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f05_energy_phase_gap_20260922/report.md
[H04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md
[H05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md
[HF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_final_synthesis_20260925.md
[CLAIM]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[COMP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/artifacts/pf_first_study_completion_analysis_20260926_940ee7f/report.md
[STRATEGY]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_research_strategy_and_plan_20260925.md
[REORIENT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/0d13decb8793c5e6fd83075b1559e05424f93c04/PF_research_reorientation_after_R1_20260928.md
[V1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/05649f1a7b6e405eadc2dbbdc0897836e0fa2f02/review_response/second_study_safe_time_domain_completion_report.md
[D1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a/artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2/report.md
[D2]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17e4d6357c7c5ef9bb849d0f787a642f972c7995/artifacts/server_pf_spectral_recoverability_d2_a_result_20260929_e2e8e5c/report.md
[D2AUD]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17e4d6357c7c5ef9bb849d0f787a642f972c7995/artifacts/pf_spectral_recoverability_d2_a_scoring_audit_20260929/report.md
[SCALEOLD]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961/report_partial_v1_2.md
[SCALE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/server_hchain_direct_optimal_time_h5_v1_2_20260927_e82b6ae/report.md
[DIRC]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e895870f16878ee4181b0e0dfe3159826a791563/docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md
[EVMAP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1d01e77247364b49dbce2e9ce2fe7c32af0fb937/docs/second_study_v2/evidence_integration_20261006/evidence_map.md
[CORRECTION]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1d01e77247364b49dbce2e9ce2fe7c32af0fb937/docs/second_study_v2/evidence_integration_20261006/documentation_correction.md
[CLOSURE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1d01e77247364b49dbce2e9ce2fe7c32af0fb937/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[H4]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5b370ec22f7ffeac687ef70e1bcb87337f5fb976/artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/report.md
[EXP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/19362c23ccdc16b6ad0ff547cc363e138a3930d2/docs/research_outcomes/20261007/validation_expansion_results.md
[FSC0]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_c0_20261007/README.md
[FSC05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_c05_execution_closure_20261007/README.md
[FSC06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_c06_functional_equivalence_20261007/README.md
[FSR0]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r0_rebaseline_20261007/README.md
[FSR01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r01_branch_extension_20261007/README.md
[FSASTOP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_phase_a_20261007/README.md
[FSA0]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008/README.md
[FSA]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[FSB]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/README.md
[L1]: https://arxiv.org/html/2102.12655v1
[L2]: https://arxiv.org/html/2312.13282v3
[L3]: https://arxiv.org/html/2210.15817v3
[L4]: https://arxiv.org/html/2606.30738v1
[L5]: https://arxiv.org/abs/2412.16811v1
[L6]: https://arxiv.org/abs/2602.18913v1
[L7]: https://arxiv.org/abs/2512.02131v1
[L8]: https://arxiv.org/abs/2605.30967v1
