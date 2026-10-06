# FS-C1-20261007-v1 — 実行前の設計snapshot

machine-readable [fs_c1_protocol.json](fs_c1_protocol.json)が本snapshotの対応仕様。science_authorized=false、execution_ready=false。曖昧さが残る状態を、実行可能な完成protocolと呼ばない。

N2_active_eq_sto3g、CO_active_eq_sto3g、current_m3、Ritz m8、epsilon_E=0.00015936001019904 Ha、beta=1.2、gamma=1.01、eta=0.02。development-informed設計であり、既存結果から独立に選ばれた閾値ではない。t0/K/B0はJSONと原sourceのexact stored値を使用。

原baselineは3点であり、「元5点」への一致は不成立。時刻・baseline定義の修正は未承認のため operational training_times=null として実行を閉じる。

B=gamma beta K/[t(epsilon-c)]、c=abs(estimate)、0<=c<epsilon。c>=epsilonはinfeasibleでB=null。zero/negative t/K/B0、不正gamma、nonfiniteは停止する。

scoring: e=abs(saved_direct)、u=e-c、M=(1-1/gamma)(epsilon-c)、s=epsilon-e-beta K/(tB)=M-u。raw s>=0の判定を保存し、数値不確定境界を併記する。未知分子のcertificateではない。

各分子別に判定:
- primary_gain: valid/safe M11、B11<=0.98 B0
- local_gain: valid/safe M01、B01<=0.98 B0
- state_increment: safe M01/M11、B11<=0.98 B01
- safety_repair: numerically identified unsafe M01、safe M11。savingとは別。

indeterminate/invalid armは支持として数えない。raw thresholdをroundingや別toleranceで救済しない。今はnative numeric uncertainty契約が未確立で、scorerではnull uncertaintyをindeterminateとしてfail closedにする。平均で片側unsafeを相殺しない。

truth joinsは元S0 v1.1 exact t0（正）の2値。condition/PF/whole-source-cache/H/order/sector/origin、元saved branch IDを使う。N2 branch ID6 / CO ID9であり、H4のbranch0固定を移植しない。隣接.99/1.01座標を採点対象にしない。

C0ではsource join監査のため元S0のこの2値の一致のみを確認し、H4保存scalarを事後換算した。C1のoperational入力へtruthを混入させない。既知development dataであり、将来commit/hash境界を作ってもknowledge-blind/holdoutにはならない。

2/2 primary gainは小規模development支持。1/2は条件依存として残す。unsafeならprimary資源拡張を停止、safeでもeta未達なら追加微小残差探索をしない。technical failureはscience不支持と分離し、saved scalarからのrecoveryを優先。いずれも後段は別承認。
