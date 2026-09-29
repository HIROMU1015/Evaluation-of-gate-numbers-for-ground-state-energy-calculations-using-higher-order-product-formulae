# Post-D2A width design：quantity・bound・access台帳

状態：C0 design-only。新しい科学計算またはC1実行のauthorizationではない。

## 1. Quantity dictionary

| Field | 定義・単位 | 用途・制約 |
|---|---|---|
| `delta_hat_signed_hartree` | 凍結推定器のsigned PF shift [Ha] | 機構解析。未補正budgetへ直接入れない |
| `delta_direct_signed_hartree` | 保存direct truthのsigned PF shift [Ha] | post-hoc scorer専用 |
| `e_direct_hartree` | `abs(delta_direct_signed_hartree)` [Ha] | 未補正QPEのtruth-required budget |
| `point_error_hartree` | `abs(delta_hat-delta_direct)` [Ha] | scorer専用。width設計のfit targetにしない |
| `rho` | `y^* A y` [dimensionless for unitary] | 元のnormal作用素とlifted vectorに対するRayleigh quotient |
| `r_rayleigh` | `||(A-rho)y||` [Aと同じ単位] | unit-circle projection後の残差と区別 |
| `r_H` | `||(H-rho_H)y_H||` [Ha] | H reference候補の残差。ground certificateではない |
| `r_U` | `||(U-rho_U)y_U||` [dimensionless] | 元unitaryへのfull-action residual |
| `g_target_chord` | `min_{j!=0}|lambda_j-lambda_0|` | target-to-others。bound入力`g_rho_others`ではない |
| `g_rho_others_chord` | `min_{j!=0}|lambda_j-rho|` | 二次残差boundが要求するfull-space下界 |
| `g_phase_principal_rad` | unit-circle上のprincipal circular separation [rad], `[0,pi]` | chord変換の条件を満たす場合だけ使用 |
| `g_energy_unwrapped_hartree` | 認定された同一liftでの`g_phase/t` [Ha] | alias認定なしにphysical gapと呼ばない |
| `d_chord` | `|lambda_0-rho|`の上界 | residualそのものではない |
| `b_phase_rad` | target phaseのprincipal-angle幅 [rad] | lift認定後だけenergyへ変換 |
| `w_hartree` | `abs(delta_hat-delta_0)`の幅 [Ha] | claim classと未検証仮定を必ず付与 |
| `allowance_hartree` | `epsilon_E-e_use` [Ha] | 正の場合だけbudget定義可能 |
| `B` | `beta*K/[t*(epsilon_E-e_use)]` | continuous Pauli-rotation proxy |
| `w_win(t;eta)` | 希望budget改善に必要な最大width [Ha] | `eta`を結果後に選ばない |

`K_current_m3`（一PF stepのPauli rotation数）、Arnoldi次元`m`、D1 cluster数`K_D1`は
別symbolとし、交換しない。

## 2. Bound derivation ledger

### B1：normal作用素に対する条件付き二次残差bound

仮定：

1. `A`は有限次元normal、`||y||=1`。
2. `rho=y^*Ay`、`r=||(A-rho)y||`を元作用素へのfull actionで評価する。
3. 対象固有値`lambda_0`とその対象性が別途同定されている。
4. `g=g_rho_others_chord=min_{j!=0}|lambda_j-rho|`の正しいfull-space下界があり、`g>r`。
5. roundoffおよびinexact actionは別budgetで覆う。

normal固有基底で`p_j=|<u_j,y>|^2`、`q=sum_{j!=0}p_j`とすると、

`r^2=sum_j p_j |lambda_j-rho|^2`

なので`q<=r^2/g^2<1`。Rayleigh identity

`(1-q)(lambda_0-rho)=-sum_{j!=0}p_j(lambda_j-rho)`

と、非対象成分に対する`x<=x^2/g`（`x>=g`）から、

`|lambda_0-rho| <= r^2/[g(1-r^2/g^2)] = d`

を得る。

分類：`conditional_certificate_candidate`。`g`、target、action errorが未認定なら
`indeterminate`であり、empirical widthへ暗黙fallbackしない。

この導出はnormal作用素に対するC0の自足的導出である。Zhu–Argentati–Knyazevの
self-adjoint Rayleigh quotient boundと研究領域は重なるが、同論文の特定定理と同一だとは主張しない。

### B2：chord上界からprincipal phase幅

`lambda=exp(i theta)`、`rho=a exp(i phi)`、`a>0`、`|lambda-rho|<=d`とする。
実距離`x`は

`x^2=1+a^2-2a cos(theta-phi)`

なので、principal angle`alpha in [0,pi]`について、次を固定する。

- `d < |1-a|`：入力boundまたは数値identityが不整合。
- `d >= 1+a`：`alpha<=pi`しか得られず、非自明なphase certificateなし。
- `|1-a| <= d < 1+a`：
  `alpha_max=acos((1+a^2-d^2)/(2a))`。
- arccos引数が`[-1,1]`を丸め許容より外れる場合は`indeterminate`。
- clampは浮動小数丸め許容内だけ行い、科学的条件違反の救済に使わない。

`b_PF=alpha_max/t`は、`t>0`かつphysical phase lift/aliasが別途認定された場合だけ許可する。
principal angleが小さいことだけではabsolute energy branchを認定しない。

### B3：gap表現の変換

両端がunit circle上で、`g_phase_principal_rad in [0,pi]`の場合だけ、

`g_chord=2 sin(g_phase_principal_rad/2)`

を使う。`g_energy=g_phase/t`は、同一physical liftが認定された場合のunwrapped energy gapである。
projected Ritz値がunit circle内にある場合、同じ変換をそのまま使わない。

### B4：H referenceとPF shiftへの伝播

PF側幅`b_PF`とH側幅`b_H`が同じ対象枝へ対して成立し、作用・丸め上界が
`b_action`、`b_round`なら、保守的候補は

`w=b_PF+b_H+b_action+b_round`

である。H側の低いRitz値はground候補でしかなく、残差ゼロでもwrong eigenstateはあり得る。
ground認定とtarget correspondenceがない場合、claimはconditionalまたはindeterminateに下げる。

## 3. Information-access table

| Quantity | 現在の取得状態 | Access class | C1での扱い |
|---|---|---|---|
| frozen `delta_hat`, `rho`, `r_U`, `r_H`, prefix差 | D2-A predictionに保存 | existing predictor | byte-identicalで再利用 |
| point error、`delta_direct` | 保存truth | truth-only scorer | freeze後の採点だけ |
| D1 true phase gap | 保存oracle診断 | oracle diagnostic only | operational armへ禁止 |
| projected Ritz gap | 保存可能 | local projected information | full-space gap下界として禁止 |
| `g_target_chord` full-space lower bound | 未取得 | certified external information required | 取得経路がなければindeterminate |
| `g_rho_others_chord` full-space lower bound | 未取得 | certified external information required | B1の必須入力 |
| ground identity | 未認定 | external ground/reference certificate | lowest Ritzだけでは不可 |
| physical branch/alias lift | D2-Aでは経験的、auditはtruth scorer | operational certificate unresolved | integer label直接比較を禁止 |
| PF action forward-error norm | 未取得 | numerical-analysis input | 0と仮定しない |
| roundoff/nonorthogonality budget | integrity値のみ | numerical-analysis input | scientific widthと分離 |
| certified spectral interval | 未取得 | candidate truth-free route | 費用と元問題同等性を評価 |
| verified complementary-space exclusion | 未取得 | candidate truth-free route | matvec数・memoryを明示 |

## 4. Claim classes

- `conditional_certificate`：target、branch、full-space separation、action/roundoffの全条件を列挙し、
  条件の下で数学的上界が成立する。
- `empirically_validated_width`：事前固定規則が評価集合で採点されたが、一般数学保証ではない。
- `heuristic_width`：prefix変化等の診断。単独でcertificateと呼ばない。
- `indeterminate`：必要条件または情報が不足。不明を小幅で置換しない。

## 5. Resource-value definitions

未補正taskでは`e_direct=abs(delta_direct)`とし、

`C_req=beta*K_current_m3/[t*(epsilon_E-e_direct)]`

を保存truth上の同時刻必要費用とする。main baseline`B0`に対する完全校正上限は

`S_max_same_time=1-C_req/B0`。

推定値`delta_hat`に幅`w`を付ける新方式が`eta`の削減を得る必要条件は、

`w <= epsilon_E-abs(delta_hat)-beta*K_current_m3/[t*(1-eta)B0] = w_win(t;eta)`。

`eta=0`はbaseline同等以下の境界であり、strict improvementにはstrict inequalityが必要。
`w_win<=0`なら、その時刻・推定値・非負幅では目標削減に届かない。

CPU秒とPauli rotationは直接加算しない。追加古典費用、量子budget、coverage、claim classを
Pareto表示し、外生的換算係数が与えられた場合だけbreak-evenを示す。

## 6. Literature scope verified in C0

- arXiv:1207.3240v2：self-adjoint Rayleigh quotientのresidual/angle型bound。
- arXiv:2102.12655v1：PFのeigenvalue/eigenvector perturbationとgap条件。
- arXiv:2312.13282v3：近似状態・摂動的なPF eigenvalue-error推定。
- arXiv:2110.07492v2：量子部分空間対角化のconditioning/truncation解析。
- arXiv:2412.16811v1：QPE固有のPF energy-error解析。
- arXiv:2606.30738v1：compact BCHによる実用Trotter error推定。
- arXiv:2210.15817v3：PF選択・設計・費用比較。
- arXiv:2212.14144v4：Trotter誤差の補間・外挿による軽減。

公式arXiv metadataとabstractで版・scopeを照合した。C0候補boundをこれらの新規定理として
主張せず、C1前に使う特定定理の本文・仮定をさらに照合する。

## 7. C0 unresolved items

1. truth-freeな`g_rho_others_chord`下界の取得経路。
2. ground/referenceおよびphysical branchのcertificate。
3. PF/H actionのrigorous forward-error bound。
4. full-space clusterを扱うset/projector版bound。
5. baselineと新方式を同じclaim classで比較する方法。
6. 実用的効果量と許容classical budget。
