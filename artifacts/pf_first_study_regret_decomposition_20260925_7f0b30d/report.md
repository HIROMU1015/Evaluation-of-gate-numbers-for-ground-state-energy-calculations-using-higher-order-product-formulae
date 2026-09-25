# 第一研究 practical selector regret因子分解

**Status:** `complete_regret_decomposition`  
**新規direct truth点:** `0`  
**Protocol SHA-256:** `b33f1b5088e5bd07ec7bff9499b4a91c3082124e291ccd0b3bfa2ddacc58832a`  
**Source scoring SHA-256:** `7d4ed0244076eb13259b926730b056a0f9460e63154dd7377b58dad34a95ae78`

## 結論

保存済みS0 exact-time採点だけを用いて、1%余裕付き凍結予算のoracle最小費用に対する比を

$$
F_{\rm total}=\frac{B_{\rm frozen}}{C^*}
=\frac{B_{\rm frozen}}{C_{\rm req}(\hat P,\hat t)}
\frac{C_{\rm req}(\hat P,\hat t)}{C^*_{\hat P}}
\frac{C^*_{\hat P}}{C^*}
=F_{\rm cal}F_tF_P
$$

と厳密に分解した。全6条件で積の閉包を満たし、coverage不足はなかった。
PF選択因子は全条件で`1.0`であり、観測した総regretにPF選択損失は寄与しなかった。
HFの2条件は時刻選択が支配した。主4 active-space条件では3条件がcalibration/budget支配、
N2 stretchだけが時刻選択支配だった。従って次の方法論課題を一つに還元せず、
HFではfinite-time optimum予測、active-spaceの平衡・CO条件では誤差量の校正と予算保守性を
それぞれ主要因として扱う。今回の6条件はdevelopment集合であり、一般化の証拠ではない。

## 条件別分解

ここで各`regret`は加算成分ではなく`factor - 1`である。寄与の比較には積を加法化する
`log(factor)`を使った。

| condition | $C^*$ | $C^*_{\hat P}$ | $C_{req}(\hat P,\hat t)$ | $\widehat C$ | $B_{frozen}$ |
|---|---:|---:|---:|---:|---:|
| N2_active_eq_sto3g | 273562446.926076 | 273562446.926076 | 279399598.008280 | 298110124.445598 | 301091225.690054 |
| N2_active_stretch150_sto3g | 147957576.277907 | 147957576.277907 | 181632703.256912 | 208603332.596799 | 210689365.922767 |
| CO_active_eq_sto3g | 516598986.284844 | 516598986.284844 | 533049026.424085 | 573237653.784658 | 578970030.322505 |
| CO_active_stretch150_sto3g | 338482010.433922 | 338482010.433922 | 362791668.833456 | 399939334.260336 | 403938727.602940 |
| HF_full_eq_sto3g | 217857453.169602 | 217857453.169602 | 466549222.409752 | 463823391.819337 | 468461625.737531 |
| HF_full_stretch150_sto3g | 160860033.986218 | 160860033.986218 | 334003547.093050 | 334916449.940699 | 338265614.440106 |

| condition | group | $F_{model}$ | $F_{cal}$ | $F_t$ | $F_P$ | $F_{total}$ | dominant |
|---|---|---:|---:|---:|---:|---:|---|
| N2_active_eq_sto3g | primary | 1.066967 | 1.077637 | 1.021338 | 1.000000 | 1.100631 | calibration |
| N2_active_stretch150_sto3g | primary | 1.148490 | 1.159975 | 1.227600 | 1.000000 | 1.423985 | time_selection |
| CO_active_eq_sto3g | primary | 1.075394 | 1.086148 | 1.031843 | 1.000000 | 1.120734 | calibration |
| CO_active_stretch150_sto3g | primary | 1.102394 | 1.113418 | 1.071820 | 1.000000 | 1.193383 | calibration |
| HF_full_eq_sto3g | stress_test | 0.994157 | 1.004099 | 2.141534 | 1.000000 | 2.150313 | time_selection |
| HF_full_stretch150_sto3g | stress_test | 1.002733 | 1.012761 | 2.076361 | 1.000000 | 2.102857 | time_selection |

## 1%余裕とmodel予算の分離

`F_model = C_hat/C_req`、`F_margin = B_frozen/C_hat = 1.01`、
`F_cal = F_model F_margin`である。HF equilibriumではmodel単体が必要費用を
わずかに下回ったが、固定1%余裕を含むと安全側になった。安全余裕は全条件で同じ
乗数なので、条件間の大きなregret差、特にHFの約2.1倍は説明しない。

## 集計

- 6条件平均総regret: `51.5317%`
- 主4条件平均総regret: `20.9683%`
- HF stress 2条件平均総regret: `112.6585%`
- 最大総regret: `115.0313%` (`HF_full_eq_sto3g`)
- 支配因子件数: `{"calibration": 3, "time_selection": 3}`
- 最大積閉包誤差: `2.220e-16`
- 追加Hamiltonian、fit、direct truth計算: `0`

## 解釈上の制限

- $C^*$と$C^*_{\hat P}$は元の2 PF・保存truth grid上のoracle最小であり、連続時間の大域最小ではない。
- $C_{\rm req}(\hat P,\hat t)$だけはS0で計算済みのexact selected-time truthを使う。
- 因子は相乗的であるため、`r_cal + r_t + r_P`を総regretと解釈しない。
- 今回の再解析だけから新PF探索、S5、追加diagnosticを開始しない。

## Source identity

- S0 result commit: `cc3626a8135b647fe283fc60c963de70c5f6b2a5`
- Source artifact: `artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201`
- Source manifest SHA-256: `7cc54d0b795dd08a96bf55cbc900d8f3fa4731f6eb843c915e6617f39160a32c`
- Source scoring SHA-256: `7d4ed0244076eb13259b926730b056a0f9460e63154dd7377b58dad34a95ae78`
