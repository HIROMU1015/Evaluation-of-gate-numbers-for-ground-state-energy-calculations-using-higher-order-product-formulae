# HF domain pilot budget accounting specification

## Baseline quantity

第一研究の正式定義は次である。

- `C_hat`: truth-free predictionから得たcontinuous cost proxy。
- `B_frozen = gamma*C_hat`, `gamma=1.01`。
- 本pilotの`B0`はこの`B_frozen`を指す。
- `K_current_m3=9108`は1 PF step当たりのPauli rotations。

`B0`は保存artifact上の浮動小数resource proxyであり、整数gate列そのものではない。

## Target and allowance

人間が`eta=0.10`を承認した場合、

`B_target=(1-eta)B0`

`A_eta(t)=epsilon_E-beta*K_current_m3/[t*B_target]`

とする。`A_eta<=0`は、PF errorが0でもtargetを満たせないことを意味する。この判定はerror estimatorを実行する前に行う。

`e_use=abs(delta_hat)+w_A`とし、`e_use<=A_eta`をadmissionに使う。admissionはtruth safetyではない。

## Candidate budget and safety

`e_use<epsilon_E`のときだけ、

`B_continuous=beta*K_current_m3/[t*(epsilon_E-e_use)]`

を定義する。`e_use>=epsilon_E`はabstainである。

truth scorerは凍結予算について

`abs(delta_direct)+beta*K_current_m3/(t*B_frozen)<=epsilon_E`

を評価する。`<=`を安全、`>`をunsafeとする。unsafe候補をresource winへ数えない。

## Discretization blocker

凍結sourceにはcontinuous proxyから整数physical budgetへ変換するauthoritative ceiling/integerization ruleがない。従ってP0では次を固定する。

- `continuous_budget_proxy`: binary64 decimalと`float.hex`を保存。
- `discrete_budget`: `null`。
- `budget_discretization_status`: `unresolved_requires_approval`。
- ceiling、round-to-nearest、floorを新たに発明しない。
- P1前に「continuous proxyだけを研究metricとする」か「出典付き離散規則を採用する」かを人間が承認する。

離散規則が承認された場合、selectionとsafetyは離散化後の`B_frozen`でも再定義し、protocol versionを更新する。結果を見た後の変更は禁止する。

## Resource accounting separation

別々に記録する。

- quantum proxy: Pauli rotations / PF step, frozen budget
- PF per-vector actions and block calls
- component-gate materializations and sparse multiplies
- H matvecs
- H exponential actions and their internal matvecs
- inner products, reorthogonalization, projected solves
- cached/shared preparation versus newly incurred work
- predictor-only versus scorer-only cost
- wall time, peak RSS, cache/basis memory

classical secondsとPauli rotationsを加算しない。nested timingを単純加算しない。cached small-system timingをcold-start scaling lawとして外挿しない。
