# Resource accounting specification

## 1. Accounting identity

条件iについて、H1の総校正費用を

`C_total_cal,i = C_shared,i + C_cheap,i + q_i*C_spectral_given_cheap,i + C_decision,i`

と定義する。`q_i=0`でもcheapとdecision費用を計上し、`q_i=1`でspectral結果が失敗・不採用でもspectral費用を計上する。

M1 always-onは、実装上cheap前処理が不要なら`C_cheap`を自動加算しない。H1とM1のshared setup差は実測identity/reuseが確認できる場合だけ差し引く。

## 2. 保存する独立counter

- wall-clock seconds: shared、cheap、spectral、decision、scorerを分離。
- CPU process countとBLAS thread count。
- peak CPU RSSと、測定可能ならstage別peak memory。
- PF per-vector actions。
- Hamiltonian matvecs。
- Hamiltonian exponential actions。
- component-gate materializations。
- sparse-state multiplies。
- orthogonalization/projected-solve time。
- cache build、cache hit、reuse identity。
- spectral request、success、failure、used、unused counts。

PF action、H matvec、H exponential actionは同じ単位に変換しない。CPU秒、rotation count、action countも外生換算係数なしに合算しない。

## 3. Quantum resource metric

Primaryは継承されたcontinuous rotation cost proxyである。

`B = beta*K/[t*(epsilon_E-e_use)]`

最終安全性はtruth開封後、

`abs(delta_direct)+beta*K/(t*B_frozen)<=epsilon_E`

で採点する。離散QPE回路、実機runtime、state-preparation costは本scopeに含めない。

## 4. Cheapとspectralの費用scope

Cheap費用は、cheap proxyを全条件で生成するために実際に必要なstate/PF/H exponential/diagnosticを含む。H1でspectralを選ばなかった条件でもcheap費用を落とさない。

Spectral費用は、固定M1のPF/H actions、basis、orthogonalization、projected solve、branch/reference処理を含む。M1結果を最終採用しなくても費用を落とさない。

Decision費用にはfeature assembly、policy evaluation、validation、serializationを含める。小さいと仮定して0にしない。

## 5. Shared/reuse規則

共有費用を主張できるのは、次が一致して実装logでreuseが確認された場合だけである。

- Hamiltonian hash。
- approximate-state hash。
- PF coefficients/order。
- absolute time coordinate。
- precision/backend/process/thread identity。
- cache keyとobject identity。

別runの保存wall timeを単純に足した値は`post_hoc_no_reuse_timing_scenario`とする。実測H1費用やscaling lawとは呼ばない。

## 6. Unknownの扱い

- 保存counterが0でも、instrumentation対象外なら`unknown_or_unmeasured`。
- H exponential内部matvecは計測されていなければunknown。
- missing memory subcounterをactual zeroとしない。
- 異なるrun・environmentのwall timeは参考値で、厳密差とはしない。

## 7. Comparison output

各armについて次のvectorを出力する。

`(quantum_budget, unsafe, coverage, wall_seconds, peak_memory, PF_actions, H_matvecs, H_exponentials, materializations, sparse_multiplies, query_count)`

PrimaryはPareto比較である。単一scalarへ縮約する場合は、換算係数、感度範囲、誰がいつ固定したかを別protocolで記録する。

## 8. 現時点の既存coverage

- HF: cheap/M1のarm別費用あり。combined H1 shared/reuse費用なし。
- HCl: cheap/M1の座標別費用あり。異なるrunを跨ぎ、combined H1 shared/reuse費用なし。
- LiF: cheap費用あり、M1費用なし。
- N2/CO: cheap feature費用の一部はあるが、このcontractの完全費用tupleは未監査。

この不足は本designで新規取得しない。
