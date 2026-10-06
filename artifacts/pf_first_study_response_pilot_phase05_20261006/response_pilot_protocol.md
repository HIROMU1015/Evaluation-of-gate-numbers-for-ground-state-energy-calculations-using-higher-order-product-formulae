# Response pilot protocol v1 — 説明版

**Normative authorityは[JSON](response_pilot_protocol.json)。本書／codeと競合したら計算前に停止する。**

## ScopeとRQ

保存済みH4の36次元sector Hamiltonian、CISD、current_m3だけを使う。STO-3G、1Å linear chain、constant除去、alpha4/beta4、MSB位置0、sector ascending indices、13 group順序と各hashは[Phase A identity](source_identity_phase_a.json)へ凍結した。Hamiltonian、PF係数、分子、geometry、input stateは追加しない。epsilon=0.00015936001019904 Ha、beta=1.2、gamma=1.01を変えない。資源選択は今回のpilotの対象外。

RQ1はexact targetを保ったstate bias低減、RQ2は同じfitを再適用した後のtotal改善、RQ3はordinary Ritz改善に対する独自のtradeoff、RQ4はabsolute error・magnitude underestimation・sign crossingの違い。

Training absolute times=`[.10,.15,.20,.25,.30]`、evaluation=`[.125,.175,.225,.275,.35,.40]` Ha^-1。両signを独立に計算し、合計22 signed coordinates。evalは12 rows。既知のdevelopment資料を使用するので、freezeの手続きをもって独立holdout／prospectiveへ再ラベルしない。

## Algorithmとarms

`W=exp(-iHt)U_P(t)`、`A=(W-W†)/(2it)`、`g_base=Im<psi|W|psi>/t`。

`E=<psi|H|psi>`、`Q=I-psi psi†`、`r=Q(H-E)psi`、`L=Q(H-E)Q`、`a=QApsi`。

時間共通residual Krylov basis Zを最大8方向まで構築する。各mについてfull-space residualの`min_c ||a-LZ_m c||`をSVDで解き、`z=Z_m c`、`g_resp=g_base-2Re(z†r)`。`L_m`と`a_m`の投影式へ切り替えない。

Ritzは同じ`V=[psi,Z_m]`、`H_m=V†HV`のlowest small Ritz pairを使用する。proxyはRitz state上の同じA expectation。m8は両methodのprimary、m1/2/4はconvergence diagnostics。途中のrank stopは共通prefixとして記録するだけで、別directionやmへ救済しない。

| Arm | estimator | 使用境界 |
|---|---|---|
| A0 | bare CISD | Phase A |
| A1 | response m8 | Phase A primary |
| A2 | Ritz m8 | Phase A primary |
| A3 | 保存exact proxyと同じfitの参照 | Phase B reference only |
| Diagnostics | response/Ritz m1/2/4 | Phase A、selection inactive |

Phase-averageはPhase 0の機構参照だけでoperational armを増やさない。

## 数値規則

complex128/float64、machine epsilon=2^-52。projectionは`v-psi<psi|v>`。MGSを正確に2pass行い、各passでpsi、accepted basis列の順で直交化する。basis phaseは最大絶対成分をreal positive、tieは最小index。

初期rank thresholdは`64 eps N max(||Hpsi||,|E|,tiny)`。後続は`64 eps N max(||Hz_previous||,||Lz_previous||,|E|,tiny)`。候補norm<=thresholdならprefix停止。orthogonality誤差が`64 eps N`を超えたら停止し、3pass目は追加しない。

SVDはfull residual matrix B=N×kのthin SVD。`sigma >64 eps max(N,k) sigma_max`だけを保持する。inverse、ridge search、gap truthは使わない。zero rankならz=0、Ritz=original state、baselineのPF結果を再利用する。factorは時間共通、同じ実効prefixは一度だけfactorizeする。

記録はabsolute／relative response residual、||z||、basis dimension、SVD effective rank、全singular values、cutoff、retained condition、full condition（singularならnullとstatus）、rank threshold、orthogonality誤差、projected診断。relative residualは`||d||/max(||a||,epsilon_num)`、`epsilon_num=64 eps N max(||a||,1 Ha)`。certificateと呼ばない。

Ritz projected Hermiticity誤差は`64 eps N max(||H_m||_F,tiny)`以下でのみsymmetrizeする。lowest small eigenspaceのeps-derived tieをJSONのdeterministic projection規則で処理する。nonfiniteは停止。巨大な||z||やconditionは隠さず報告し、結果後の救済thresholdは導入しない。

元normalization/H Hermiticity/group-sum/unitarity/±U adjoint gateを保持する。noiseはmethod別に同じ
`max(PF unitarity/|t|, cold replay差,50 eps max(||H||_2,1/|t|))`。
rho≥100 resolved、≥10 marginal。それ以下はunresolved。responseのresidualはnoiseやbias保証へ流用しない。one complete cold replayではbasis/state/solver/backend/proxyを独立に再構築し、全部のactionを加算する。

## Fitとmetrics

全armへ独立に同じunweighted、no-intercept、column 2-norm scalingのOLSを適用する。主モデルはpositive5点の`a4*t^4+a6*t^6`、両signへ同じeven predictionを出す。evenized 4/6 fitとodd 5/7 fitは保存だけで主判定へ切り替えない。全positive5点がmarginal/resolved、3点以上resolved、scaled cond≤1e8でfit_ok。その他はnot_identifiable。raw fitと全rowsをstatusとともに保存し、不適格rowsを除いて有利な分母にしない。

主metricは12 eval rowsの`fhat-delta_direct`。point `g_method-g_exact`はmechanism diagnostic。
`u=|delta|-|fhat|`、`u+=max(0,u)`、`sign(fhat)!=sign(delta)`を保存する。sign(0)=0。crossingをcomponentwise attributionしない。

集約はS_abs、S_under、E_max、crossing count、baselineよりimproved/worsened/equal counts、全response residual statistics、cost。continuous ratiosとabsolute valuesを必ず併記し、ratio分母ゼロならnull。主判定はstrict scalar decreaseで、5%／10%の新しいmaterial gateを足さない。

## Outcomeと停止規則

数値不適格はまずD相当のunstable statusとし、A/Bの肯定判定へ入れない。その他はA→B→C→Dの順で判定する。

| Outcome | 凍結条件 |
|---|---|
| A response_specific_support | ResponseのS_absとS_underがbaselineより低下、全22 signed rowsでm増加のresidual convergence gate合格、Ritzに対するunique tradeoff、primary fits適格 |
| B generic_state_improvement | ResponseとRitzがともにS_abs／S_under低下、responseにunique tradeoffなし |
| C point_only | Responseのpoint-error総和は低下するがtotal S_abs／S_under両方の改善は満たさない。resource段へ進まない |
| D no_benefit | 両methodともtotal／unsafe両方の改善を満たさない、または数値不安定 |

Unique tradeoffは`(S_abs,S_under,standalone H actions,standalone forward+adjoint PF actions)`でRitzにPareto-dominatedされず、1要素以上strictly better。同じmをequal costと扱わず、悪化する項も明示する。projection/solve/storageも別報告し、異なる単位を任意の重みで足さない。

Response residual convergenceは各coordinateの1→2→4→8すべてで`d_next<=d_prev+eta_prev+eta_next`。`eta_m=64 eps N(||a||+||B||_F||c||)`は丸め許容量だけ。cutoffが変わって非単調なら失敗を記録し、修正しない。A-Dに入らないasymmetric／nonconverged組合せは`inconclusive_mixed_predicates`というreporting statusに残し、無理に科学的成功／失敗へ分類しない。

## Truth barrierと将来実行

Phase Aはsaved H/13 groups/CISDだけを入力とする。exact state/energy、D operators、direct branch/error-decomposition、truth混在CSVは渡さない。全proxy・fit・prediction・diagnostic・counter・source/code/protocol hashesをfreeze/commitし、full40 SHAを取得する。行列／state／response vectorはprivate runtime、public scalar manifestには含めない。

Phase Bは実際のcommitted prediction blobとfile bytes/SHA256を確認してから、保存direct12点とexact proxy22点のみを読む。exact trainingはA3 reference fit専用。predictionは変更しない。元正負branchのexact keysを[saved lookup contract](saved_truth_join_contract.json)へ固定した。欠損・duplicate・unreliable branchで停止し、新しいbranch solveやinterpolationをしない。

今はproduction CLIが両phaseともdecode前に停止する。将来のseparate authorization後、固定Padé backendとwhitelist loader/cold noise計測adapterを実装し、synthetic acceptance checks→source checks→Phase A→commit/hash照合→Phase Bという順に進む。新H／ground／Schur／direct truthは0。全m予定はcold込みH18、forward220、adjoint44、small Ritz8、response RHS176。詳細は[cost accounting](cost_accounting.md)。

Level1–2の判断だけを目標とする。N2/CO等のresource stage、quantitative resource gate、新PF／新分子は後の別preregistrationと承認で扱う。このPhase0.5はcommit/pushとremote blob確認後に停止する。
