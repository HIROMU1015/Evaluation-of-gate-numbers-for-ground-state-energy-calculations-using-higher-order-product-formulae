# 費用会計の契約

単位を分離する: classical wall seconds、peak RSS bytes、H per-vector matvec、H matmat/block calls、PF per-vector forward、group sparse gate materialization、sparse vector/block multiply、H-exponential action/internal products/norm work、small Ritz solve、scalar fit、predicted continuous QPE rotations。CPU秒と量子rotationを足してnet advantageを主張しない。

現入力案のnominal rank8、2systems、2states、6positive times、initial+cold: explicit refinement H36、PF forward48、adjoint0、exact-H echo48、small Ritz4、主fit4。新truth/full-H ground/eigh/Schur/response0。これらは予定論理数で、C0で実行した数ではない。元5点案の48回と、原3点に修正した場合の32回を混同しない。

explicit Hは各pass1+k（Hpsiとaccepted k列のHZ）、nominal k8なら9。rank stopは実際のkを数え、36を架空に維持しない。fitはcold replay後に1回、validation fitsを別に追加しない。

inherited native iteratorをmetadataだけで数えると、N2はmerged group steps1121、distinct(group,weight) sparse gates324、K19176。COは1373、396、K37936。単独vector呼出しscheduleの場合、1PF actionあたりこれらのgroup multiply/materialization数となる。2statesをcolumn blockへまとめるならper-vector action数は同じだがblock-call/cache/materializationは別数になる。現在はbackend scheduling/resource契約が未完了なので、どちらも実測totalにはしない。

前処理: 元component eigensystemsとCSR Hの取得・hash・検証、group sparse gateのbuild、exact-H norm/trace estimation、internal matvec/matmat/rmatvecを記録する。既存のsmall connected-component spectraを使う場合はinherited preparationとして報告する。fresh prepare_conditionで分子/H/ground/CISDを再生成しない。

exact-H expm_multiply action1をH matvec1と数えない。old CSR APIで内部回数を取得できなければunknown/null、理由とwallを保存し、ゼロとしない。cold independent passで共有cacheは使わない。persistent preprocessingが使えないcold standaloneにはその取得・build費を含める。

joint: 4arm比較と全training/local両state・両pass。standalone operational: one condition/one passでそのarmに必要な取得のみ。incremental: 元baseline校正済みを共有した追加費。
- M01 incremental: local PF1+echo1。
- M11 incremental: H9+small Ritz1+local PF1+echo1。
- M10 incremental: 同じstate refinementにtraining各PF/echoとfit1。

M10の対照fit計算をM11単独運用の必須費へ押し付けない。validation cold replay、FS-C0 synthetic tests、旧H4 Attempt1 technical lossは研究実行費に区分して残し、将来単独1pass運用費と分ける。失敗試行を成功runから隠さない。

Ritzは古典校正stateで、量子入力state準備に使わない。新quantum state preparation費と重なり改善利益はともに作らない。resource vector=(classical費用、projected QPE rotations)。Bnew<B0ならlambda_min=Delta classical cost/(B0-Bnew)を単位付きbreak-evenとして表示できるが、任意のCPU→gate換算係数を導入しない。

Truth-free screen: C_req>=beta K/(T epsilon)、Hmax=1-beta K/(T epsilon B0)。Hmax<etaなら同一PF/domainで目標に届かない。raw negative headroomをclipしない。B0がsafeだという証明でも、PF変更/domain拡張の不可能性でもない。

headroom_reference.csvのN2/CO same-time margin-removed oracleとfixed-gamma perfect-prediction savingを分ける。HF domain上界約1.58–1.66%は2%設計目標を除外するが、HF新scienceは行わない。H4事後換算も実際のoperational budget生成やC1成功ではない。
