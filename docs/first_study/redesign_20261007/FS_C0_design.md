# 第1研究の再設計 / FS-C0

設計日: 2026-10-07 (JST)
状態: GPTによる研究設計案を選定済み。リポジトリのsource/backend closureと実行承認は未完了。
この文書はscience実行許可ではなく、旧formal resultや既存protocolの修正でもない。

## 1. 推奨する研究の中心

有限時間PF校正の誤差を小さくすること自体ではなく、資源判断が行われる座標で、どの校正介入が安全なQPE予算削減を生むかを調べる。

主RQ: 同じHamiltonian、PF、目標精度、QPE費用モデルで、(i)校正状態の精密化、(ii)短時間fitから選択時刻でのlocal proxy評価への変更、のどちらが、校正誤差と凍結予算の過剰配分を減らすか。

研究対象はまず古典的なoffline calibration / resource planning。校正状態の変更を、QPE入力状態の変更と混同しない。QPE入力状態・準備・成功確率モデルは比較で固定し、その改善の利益を計上しない。

仮題: Decision-relevant calibration of product-formula errors for molecular phase estimation.
既存数学、Ritz、Krylov、responseを新発明とは主張しない。

## 2. 変更しないevidence

Repository:
HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae

- Formal authority: PF_first_study_paper_claim_ledger_20260926.md / final synthesis / completion analysis.
- Phase 0: 1b7b2fc959185ca1be06581682a67d28e02db21c
- Phase 0.5: 48f3d889d096f2fe3af55c200a757747df384941
- Phase 0.6: 6fae17723f888a62a998f90436516785a67651c6
- Attempt 1 failure audit: 3d7a923f2a8d11aff57a05454eca8e142496833e
- Phase A Attempt 2: 53a88c28b7587ab61efb93d6ba30974c9d3d6404
- H4 Phase B: 5b370ec22f7ffeac687ef70e1bcb87337f5fb976
- Second-study-v2 integration: 0a18168ae56852d7c754c28d05d5ce21bbce5b06

H4 Outcome C point_onlyおよびresponse_unique_tradeoff=trueを維持する。
Cはrefit失敗の実証ではない。baseline S_under=0からのstrict decreaseが不可能だった。
旧Outcomeを新しいsafety判定で置き換えない。

## 3. 今回の代数的再解釈

### 3.1 H4の精度改善と資源尺度

同時刻、同じgammaでは B_new/B_old=(epsilon-c_old)/(epsilon-c_new)。
H4 t=0.4に保存された値を代入した参考計算では、Responseの削減率0.0120393542%、Ritzの削減率0.0127726590%。これは新しいoperational budgetの達成結果ではなく、既存scalarの事後換算。

Ritz t=0.4のu=4.001935244501792e-12 Ha、gamma1.01のmargin=1.5745764377680851e-6 Ha。S_underの総和を単一座標のmarginと比較しない。

### 3.2 Responseの固定部分空間における表現

B=LZ、z_t=Z B^+ Q A_t psi、w=Q(B^+)^dagger Z^dagger r。
固定psi/Z/B/cutoffの下で、g_resp(t)=<psi|A_t|psi>-2 Re<w|A_t|psi>。
wはtime/observableに依存しない。rho_lin=|psi><psi|-|psi><w|-|w><psi|で同じ線形汎関数になる。
これは既存responseを別形式で表した代数で、Ritzとの同値性や誤差の原因を証明したものではない。
新Response variantのproduction実験はしない。synthetic恒等式テストだけC0に含める。

## 4. Decision-window framework

c=|delta_hat|、e=|delta_direct|、epsilon=0.00015936001019904 Ha、beta=1.2。
候補予算 B=gamma beta K/[t(epsilon-c)]、0<=c<epsilon。
それ以外はinfeasible。安全判定は保存truthによる s=epsilon-e-beta K/(tB)>=0。
u=e-c、M_gamma=(1-1/gamma)(epsilon-c)ならs=M_gamma-u。
これは連続費用モデル内の数値的判定。未知分子のcertificateではない。

### 4.1 Truth-free除外

同一PF、0<t<=T、e>=0なら C_required>=beta K/(T epsilon)。
B0からのsaving上界Hmax=1-beta K/(T epsilon B0)。Hmax<etaなら、そのPF/domain内だけの介入ではeta削減に届かない。
Tを広げたりPFを変えたりする方式へこの除外を適用しない。B0の安全性をこの式で保証しない。

### 4.2 採用に必要な精度

要求saving etaに対し、候補tで妥当なPF誤差上界Uが存在するなら、
U <= epsilon-beta K/[t(1-eta)B0]
が、その上界に基づく予算でeta削減する条件。
Uをfit residual、Ritz rank差、response残差から根拠なく生成しない。
最初のC1はfixed gammaによる経験的候補をtruthで採点する。保証付きUを得たというclaimはしない。

### 4.3 Fit sensitivity

固定OLSはf(t)=ell(t)^T y。入力変更Delta yに対しDelta f=ell(t)^T Delta yは厳密。
f!=0では d log B/d y_i=sgn(f) ell_i/(epsilon-|f|)。
これは校正点誤差のdecisionへの感度。model/proxyバイアスをboundする式ではない。
誤差を一律に小さくする方法と、decisionでの影響を測る方法を区別する。

## 5. FS-C1: 最初の新規science実験（実行は未承認）

### 5.1 対象

新分子は生成せず、下の二つの既使用development条件を事前固定する。

| condition | PF | K | t_ref (Ha^-1) | t0 (Ha^-1) | B0 |
|---|---|---:|---:|---:|---:|
| N2_active_eq_sto3g | current_m3 | 19176 | 0.6263494343795273 | 0.5983202971910435 | 301091225.69005436 |
| CO_active_eq_sto3g | current_m3 | 37936 | 0.6546804264781796 | 0.6127481451622522 | 578970030.3225045 |

出典は既存completion analysis decision_trace.csvとPhase0 resource_headroom.csv。
実装では原本のexact stored time/binary64値を参照し、上表の丸め転記で置換しない。
Hamiltonian、CISD、ordered groups、sector、basis、constant/energy originは元source identityを継承する。
同名分子の再生成や近傍geometryで代用しない。

### 5.2 固定時刻

Trainingは元CISD側t_refの{0.1,0.2,0.3,0.4,0.5}倍の保存座標。
C0で元predictionの実際のtraining列と一致を確認する。不一致なら推測で進まない。
各systemでtraining5点+元選択時刻t0の計6 positive times。
本新protocolでは負時刻のscienceを追加しない。旧H4の正負22点contractは変更しない。
Ritzに合わせたt_ref再計算、t0移動、domain拡張、PF再選択は行わない。

### 5.3 2×2 arms

| arm | calibration state | t0で使う推定値 |
|---|---|---|
| M00 | CISD | 元と同じ5点二項fit f0(t0) |
| M10 | Ritz8 | 同じ5点から再fitしたf8(t0) |
| M01 | CISD | t0で実際に評価したg0_trial(t0) |
| M11 | Ritz8 | t0で実際に評価したg8(t0) |

主候補はM11。M10はstate-only、M01はlocal-evaluation-only対照。
localとはdirect eigenvalue truthではなく同じimag-echo proxyの直接評価。
4 armはtruth前にすべてfreezeし、事後best armへ主方式を切り替えない。
既存B0をhistorical referenceとして保持し、M00再現を別gateで確認する。原本を上書きしない。

### 5.4 State/fit

Ritzは固定m8 residual Krylov、MGS2pass、machine-precision rank stop、最大9次元projected lowest Ritzを継承。
rank breakdownは規則どおり保持し、m16等へ救済しない。
m1/2/4の新規PF測定は今回は追加しない。
fitはno-intercept/unweighted/column-scaled OLS、a4 t^4+a6 t^6。
新たなt^8項、正則化、window移動なし。
W(t)=exp(-iHt)U_P(t)、U_P≈exp(+iHt)、proxy=Im<psi|W|psi>/t。
各armはscalar forward expectationだけを使う。response/adjointは実行しない。

### 5.5 予算・safety・資源目標

gamma=1.01を全4 armで固定。新たなgamma sweepは行わない。
主resource目標eta=0.02（2%）を本新実験の設計上の目標として採用。
これは普遍定数でも旧Outcomeの修正でもなく、既存dataを見た上で将来の未取得介入を評価する設計値。

- primary_gain_i = M11がnumerically valid、safe、かつB11<=0.98 B0。
- local_gain_i = M01がnumerically valid、safe、かつB01<=0.98 B0。
- state_increment_i = M01とM11がともにsafe、かつB11<=0.98 B01。
- safety_repair_i = M01 unsafe、M11 safe。これはgainとは別の結果。

2systemそれぞれで判定し、平均だけで片側のunsafeを相殺しない。
S_underのstrict decreaseを主成功条件にしない。
raw s=0境界や差が既存数値識別限界に重なる場合はnumerically_indeterminateを併記し、認証済みとは扱わない。

### 5.6 最低限の出力

各arm/systemで、signed estimate、c、e、u、M、s、B、B/B0、saving、fit/proxy quality。
state/fit側の差をsigned量で記録し、絶対値の差やbudget差を独立原因の加算分解としない。
state×local interactionをf/g差およびlog-budget差として記述できるが、人口全体の因果効果は推定しない。

### 5.7 Cost accounting

joint nominal rank8、2system、2states、6positive times、initial+coldの算術上の回数:
- explicit state-refinement H matvec: 36 (=9×2passes×2systems)
- PF forward vector actions: 48 (=2states×6times×2passes×2systems)
- PF adjoint: 0
- exact-H echo vector actions: 48
- small Ritz solves: 4
- operational primary fits: 4（2states×2systems、replay後に1度）
- new direct PF eigenvalue truth: 0
- new full-H ground/eigh/Schur: 0
- response solve: 0
- distinct scoring targets: 2（元S0 exact selected times）

既存B0校正を共有した上での1system/1passの追加費用は、M01がPF forward1+exact-H echo1、M11がstate-refinement H9+small Ritz1+PF forward1+exact-H echo1。M10は同じstate構築にtraining5点のPF/echoとfit1が必要。4arm比較のために全6点を両stateへ評価するjoint実験費を、M11単独運用費へ押し付けない。既存baseline構築・Hamiltonian/group前処理が共有されないcold standaloneの場合はその費用も加算する。

これは全古典計算費ではない。exact-H exponentialの内部matvec、group preprocessing、行列積、norm estimation、scalar fit、memory、wallを別ledgerにする。exact-H actionをH matvec1回と数えない。
standalone / incremental / joint costsを別記録。監査のcold replayとAttempt1損失は研究実行費に含め、将来単独運用の1pass費用とは分ける。

H4のdense36×36 backendをN2/COへ無検討で拡張しない。C0で既存N2/CO native action backend、任意Ritz vectorへの適用、exact-H echo、source identity、数値精度、資源上限を閉じる。準備できなければscienceを開始しない。

### 5.8 Classical calibrationとQPE費用

Ritz vectorは古典的校正に使い、QPE入力状態のquantum preparationには使用しない。
従って本実験に新Ritz量子状態準備費を架空に加算しない。同時に、量子状態準備改善の利益も計上しない。
表示するresource vectorは(classical wall/memory/H/PF/H-exp actions, projected QPE rotation cost)。
CPU秒と量子rotationを重みなしに足さない。hardware pricingがない限りnet economic advantageを断言しない。
必要ならlambda_min=Delta classical cost/(B0-Bnew)のbreak-even変換係数を表示する（単位を明記）。

### 5.9 Truth barrier / reproducibility

C0は既に公開されたdevelopment outcomesをレビューする段階であり、knowledge-blindではない。
C1 production入力はH/groups/CISDとfixed metadataのみ。exact-ground vector/energy、PF truth、phaseBを計算入力にしない。
C1で4 arm全出力・scorer・source/code/protocolをfreezeした後、exactly matchingな元S0 e(t0)2値を読む。
保存exact proxy追加取得やfull-H truthは初回C1では不要。
Missing/duplicate/identity mismatchは停止。nearest-time substitutionや新truth生成で救済しない。
既知の2条件をholdout/prospectiveと呼ばない。

## 6. Stop / continue

旧H4 Outcomeは一切変更しない。以下は新C1の判断。

1. M11が片側でもunsafe: primary methodのresource拡張を停止。gamma/rankを調整せず原因と対照を報告。
2. 両側safeだがeta gain未達: accuracy-onlyとして整理。より小さな残差を追う計算を増やさない。
3. primary_gainが2/2: resourceレベルの小規模development支持。C2候補へ。
4. さらにstate_incrementが2/2: state-refinement固有の増分resource valueを支持する条件がある。
5. local_gainが2/2でstate_increment不成立: cheap local evaluationを主たる競合として残し、「Ritzが不可欠」と主張しない。
6. primary_gainが1/2: heterogeneous development result。追加分子を当たるまで増やさない。原因を既存出力で整理して完了候補。
7. numerical/technical failure: science不支持とは別。durable snapshotからのscalar-only recoveryを優先。追加scienceは自動再実行しない。

cold/scienceで得た原scalarはschema検証前のprivate create-only checkpointへ保存し、hashを持つ。これは正式freezeの代替ではない。

## 7. FS-C2（条件付き次段、未承認）

目的: C1で確認した校正介入の利益がtime selectionへも残るか。
事前に指定する範囲はN2 stretch150、CO stretch150の2既使用条件まで。
候補時間は各旧t0×{1,1.25,1.5}のうち旧allowable domain内のもの。再scale/追加なし。
CISD-localとRitz8-localを両方測り、同一candidate domain/gamma/cost definitionで比較。
method内のselected candidateをpredictionからfreezeしてからtruthを採点する。
これはQPE開始前の時刻選択であり、QPEの各powerで異なるPF/timeを動的に使う方式ではない。
新truthが必要なら最大6candidate coordinates、必要anchor最大1/systemを別途明示承認。枝不確定は停止。
新Hamiltonianや新ground solveを自動許可しない。
C1/C2で追加介入の対象は合計4molecular conditionsまで。HF/H-chainを追加して成功率を上げない。

## 8. 論文と停止境界

中心claim候補:
- calibrationの支配誤差成分とresource改善の対象は同じとは限らない。
- 同じPF・timeでstate/local-fit介入を区別すると、budget gainの原因を特定できる。
- truth-free domain下限によって、固定domain内の大幅改善が不可能な場合を事前除外できる。
- 追加校正の量子費用削減と古典情報費用を分離して報告する必要がある。

C1 positiveなら、mechanism→intervention→budgetの論文へ。
C1 negativeでも、効果が出ない場所を誤差尺度・時間域で説明する数値方法論論文へ。Responseの新発明や普遍safe policyを掲げない。
現時点でpublication acceptance、noveltyの優先権、一般分子へのtransfer、完全FT runtime、quantum advantageは主張しない。

第2研究v2とは、第一研究=校正量の誤差原因と介入、第二研究=cheap baseline固定下でのspectral情報/width/adoptionを分ける。共通evidenceを二重に独立実験として数えない。

## 9. C0でCodexに依頼する範囲

production science 0のまま、immutable evidence registry、source/backend closure、machine-readable new protocol、4-arm/scorer skeleton、synthetic arithmetic/serialization tests、operation-budget mapを作る。
H4既存scalarのmargin/resource換算は新しいpost-hoc layerへ保存可能。
新N2/CO proxy/Ritz/fit/scienceはまだ実行しない。
C0完了後、source/cost gateが閉じたらC1を1回の承認でprediction→freeze→scoringまで実行する方式を推奨。データ境界は維持し、数値が好ましいかどうかでtruth開封対象を選別しない。

## 10. 主要文献（確認した一次資料）

- Abe et al., Evaluating higher-order product formulae for molecular ground-state energy estimation, arXiv:2605.30967v1 (2026).
- Mehendale et al., Estimating Trotter Approximation Errors to Optimize Hamiltonian Partitioning for Lower Eigenvalue Errors, arXiv:2312.13282v3 (2025).
- Assaraf & Caffarel, Zero-Variance Zero-Bias Principle for Observables in Quantum Monte Carlo: Application to Forces, arXiv:physics/0310035v1 (2003).
- McClean et al., Hybrid Quantum-Classical Hierarchy for Mitigation of Decoherence and Determination of Excited States, arXiv:1603.05681 / PRA 95, 042308 (2017).
- Yi & Crosson, Spectral Analysis of Product Formulas for Quantum Simulation, arXiv:2102.12655 (2021).
- Rendon, Watkins & Wiebe, Improved Accuracy for Trotter Simulations Using Chebyshev Interpolation, arXiv:2212.14144v4 / Quantum 8, 1266 (2024).
- Becker & Rannacher, An optimal control approach to a posteriori error estimation in finite element methods, Acta Numerica 10, 1–102 (2001), DOI:10.1017/S0962492901000010.
- Kronenberger, Erakovic & Reiher, Trotter Error and Orbital Transformations in Quantum Phase Estimation, arXiv:2602.18913v1 (2026).
- Kraft et al., Bounded-Error Quantum Simulation via Hamiltonian and Lindbladian Learning, PRX 16, 031037 (2026), DOI:10.1103/s96t-n8tx.

文献の一般的手法や保証を本研究に自動移植しない。本レビューは網羅的な先行研究不存在の証明ではない。
