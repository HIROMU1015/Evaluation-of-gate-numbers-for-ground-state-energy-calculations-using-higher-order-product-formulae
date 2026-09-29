# D2-A audit後のPF研究戦略：C0固定版

作成日：2026-09-29
状態：`post_d2a_width_design_complete_review_required`

## 1. 結論

主題を「Arnoldi点推定をさらに高精度化すること」から、次へ移す。

> 有限時間product-formula（PF）固有値誤差について、資源判断に必要十分な事後幅を、
> どの情報と古典費用で構成できるかを明らかにする。追加校正が有益な条件と、単純な
> 予算余裕を選ぶべき条件を分ける。

D2-Aの凍結点推定は、scoring auditの表現不変判定でHCl development 6座標すべての
物理枝と整合し、最大shift誤差は`1.3825298286692967e-8 Ha`だった。一方、保存幅では
1件棄却、主baselineより低予算は0/6だった。したがって現在の問題は点推定の不足ではなく、
幅、枝・参照条件、必要情報の取得可能性である。

元のD2-A正式判定`d2_a_complete_close_spectral_route_stop`は履歴として変更しない。
ただし旧integer比較の0/6を物理枝回収失敗として引用せず、auditを必ず併記する。

## 2. C0で固定した分離

- `delta_hat`と`delta_direct`はsigned shiftで、機構とbias補正候補に使う。
- `e_direct=abs(delta_direct)`だけを未補正QPEのbudgetへ使う。
- 点推定誤差、幅、許容誤差、量子予算を別量として扱う。
- `g_target=min_{j!=0}|lambda_j-lambda_0|`と
  `g_rho_others=min_{j!=0}|lambda_j-rho|`を別fieldにする。
- chord distance、principal phase separation、unwrapped energy separationを暗黙変換しない。
- conditional certificate、empirically validated width、heuristic widthを混同しない。

## 3. 第一候補bound

有限次元normal作用素`A`、正規化ベクトル`y`、

`rho=y^* A y`, `r=||(A-rho)y||`

を考える。対象固有値`lambda_0`が別途同定され、全ての非対象固有値について

`|lambda_j-rho| >= g_rho_others > r`

という正しい下界がある場合、

`|lambda_0-rho| <= r^2 / [g_rho_others (1-r^2/g_rho_others^2)]`

を条件付き候補とする。この式は`g_target`をそのまま代入する規則ではない。
projected Ritz gapもfull-space下界ではない。対象がgroundであること、対象枝、作用誤差、
roundoffは別条件である。

unitary固有値`lambda=exp(i theta)`と`rho=a exp(i phi)`に対するchord上界`d`からは、
`a>0`かつ`|1-a| <= d < 1+a`のとき、

`alpha_max=acos((1+a^2-d^2)/(2a))`

をprincipal angle上界候補とする。arccos引数のclampは丸め許容内だけ認める。
alias-freeなphysical liftが認定されたときだけ`alpha_max/t`をenergy幅へ変換する。
条件不足、`rho=0`、不整合、非自明なphase情報がない場合は`indeterminate`とし、
小さい経験幅へfallbackしない。

`g_chord=2 sin(g_phase/2)`は、両点がunit circle上で、
`g_phase in [0,pi]`がprincipal circular separationの場合だけ許可する。

## 4. 保存scalarから分かった資源価値

HCl 6座標では現行widthを決めた成分は全て`local_residual_width`だった。保存実装は
`local_residual_width=r_H+PF_phase_radius`であり、明示的なnumerical action boundは0だった。
これはforward-error certificateが0であることを意味せず、未取得条件として残す。

同じ時刻、未補正タスク、local-CISD `gamma=1.02` baselineに対する完全校正時の最大削減率は
`0.327975%`から`2.286462%`だった。現行widthとbaseline同等に必要な幅
`w_win(t;0)`の比は`1.1062`から`167.4915`で、6/6すべて現行幅が大きかった。

これは「幅を小さくすれば大きな利益が出る」ことを示さない。同時刻の利益は小さいため、
将来のC2で大きな価値を求める場合は、同じ情報予算での時刻選択またはbias補正のどちらか一方を
別taskとして選ぶ必要がある。

## 5. 情報取得に関するC0判断

条件付きbound自体は数理的候補になる。しかし最重要入力`g_rho_others`のtruth-freeな
full-space下界を、現在の許可情報から得る経路は未確立である。局所Ritz gap、prefix安定性、
D1 true gapはoperational certificateに使えない。

候補経路は、独立に認証されたスペクトル区間、作用素摂動上界を伴う既知参照、
または検証可能な補空間排除である。これらが元のground-energy問題を実質的に解く費用を要するなら、
local calibrationと固定marginが合理的な対立法になる。

## 6. 次段階のgate

C1は未承認である。進行判断には少なくとも次を要求する。

1. `g_rho_others`または同等の分離情報をtruth-freeに取得する具体的経路。
2. ground、branch、alias、action errorを含むclaim classの固定。
3. 必要幅`w_win`へ到達し得ることと、その情報費用の見積り。
4. 同じ保証区分・coverageを持つbaselineとの比較。
5. predictor freeze後だけoracle/scorerがtruthを開く境界。

true gapを入れたoracle腕だけが鋭い場合は、実用法成功へ進まない。方法として成立しなくても、
必要情報量と資源価値の定量的限界が得られる場合はlimit studyとして残せる。

## 7. 停止

C0では新しいArnoldi、Hamiltonian/PF作用、gap計算、toy numerical experiment、LiF、D2-B、
holdout、新PFを実行していない。C1、time-selection、bias correctionの実装は別承認とする。

第一研究の完成は本経路から独立して優先する。次はC0成果の研究方針レビューであり、
自動的にC1へ進まない。
