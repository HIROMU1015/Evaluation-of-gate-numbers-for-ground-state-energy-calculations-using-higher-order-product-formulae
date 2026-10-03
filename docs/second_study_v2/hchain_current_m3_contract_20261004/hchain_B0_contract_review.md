# H-chain B0 contract review

結論: T0が共通契約として採用できないため、B0の数値を正式baselineとして回復しない。

## 正式なcost・margin規約

第一研究metric dictionaryとHF budget accounting specが定めるbaselineは

`C_hat=beta*K/[t*(epsilon_E-abs(model_signed_shift(t)))]`

`B_frozen=gamma*C_hat`、`gamma=1.01`

である。したがってH-chainで同じ意味を継承する場合の設計式は

`B0=1.01*beta*K_current_m3/[T0*(epsilon_E-abs(frozen_model_shift(T0)))]`

であり、`epsilon_E=0.00015936001019904 Ha`、`beta=1.2`、KはH2/H4/H6で108/2556/14344。marginはcostへ掛ける。proxy errorへ1%を加えたり、gammaをdenominatorへ移したりしない。

M1の `e_use=abs(delta_hat)+width` によるcandidate budgetとは別量である。baselineにM1やdirect shiftを入れない。B1のfour-gamma cost frontierもbaseline gammaとは別armとして管理する。

## Continuous/discrete

正式metricは `continuous_rotation_cost_proxy`。整数化は `not_defined_in_inherited_study`。新しいceil規則は導入しない。safetyの将来scoringは同じbeta/Kを使う
`abs(delta_direct)+beta*K/(t*B_frozen)<=epsilon_E`。
今回はprediction/scoringを実行しない。

## 保存情報の可用性

- H4: 凍結CISD二項modelの係数 `[-1.360617053210676e-5,4.56745637114026e-8]`、powers `[4,6]` とnative selected cost `19421980.53117479` がある。T0を別途正当化できればmodel評価の算術は可能。ただし保存native selected costをhalf-scale B0へ改名しない。
- H2: CISD D4の一項costは保存されているが、H01の定義は `K/[t*(epsilon-|<D4>|t^4)]`、betaなし。保存costをそのままbeta=1.2のB0へ移さない。D4 routeへのbaseline redesignも未承認。
- H6: exact-ground modelはoperational baselineへ流用不可。CISD state/hash・同定義のcheap modelも未確定。

H2/H6で継承cheap routeを選ぶ場合は `B0_requires_new_cheap_acquisition` が条件付きで必要になる。しかし現段階の主blockerはT0/model/state契約であり、cheapを計算すれば自動的に解消するとはしない。全系の正式B0は `null`。truthを使ったB0やbaseline最適化は0件。
