# B03: S2列・積順序・隣接マージの等価性

- 状態: **complete**
- 評価時刻: `0.37` Hartree^-1
- 密行列ケース: 15（合格 15）
- Qiskit registryケース: 9（合格 9）
- 最大密行列ユニタリ差: `1.800e-14`
- 最大Qiskitユニタリ差: `2.911e-15`
- 最大δE経路差: `2.175e-15` Hartree

## 結論

明示展開したS2列、隣接同群をマージした列、逐次密行列builder、S2-cache builder、Qiskit grouped circuitは、検査した1〜3群と全係数列で同じユニタリおよび固有値シフトを与えた。したがって隣接マージとS2ブロックcacheは、この範囲では近似ではなく安全な高速化として採用できる。

積順序は、iteratorが `F1, F2, ...` を返すとき状態にはその順で作用し、行列表現は `... F2 F1` となる。通常の対称PFは列を逆転しても同じため、非回文の診断列を別に使って誤った右乗算を検出した。

`U(-τ)=U(τ)†` は回文のproduction列で成立した。一般の非回文列では、逆演算子は同じ列への負時刻ではなく `inverse_s2_sequence`（逆順かつ符号反転）で得られることも確認した。

## 回転数

| PF | 群数 | マージ前 | マージ後 | 非ゼロのみ |
|---|---:|---:|---:|---:|
| second_order | 1 | 2 | 2 | 2 |
| second_order | 2 | 6 | 6 | 6 |
| second_order | 3 | 9 | 9 | 9 |
| yoshida4 | 1 | 6 | 2 | 2 |
| yoshida4 | 2 | 18 | 14 | 14 |
| yoshida4 | 3 | 27 | 23 | 23 |
| current_m3 | 1 | 14 | 2 | 2 |
| current_m3 | 2 | 42 | 30 | 30 |
| current_m3 | 3 | 63 | 51 | 51 |
| morales_y8m10b | 1 | 42 | 2 | 2 |
| morales_y8m10b | 2 | 126 | 86 | 86 |
| morales_y8m10b | 3 | 189 | 149 | 149 |
| zero_middle_control | 1 | 10 | 2 | 2 |
| zero_middle_control | 2 | 30 | 22 | 18 |
| zero_middle_control | 3 | 45 | 37 | 27 |

ゼロ係数controlでは、現在のiteratorは重み0のステップを保持する。ユニタリは正しいが、runnerが返すrotation数はコンパイラ前のidentity rotationも数える。これは物理的不一致ではなく、コスト計数上の保守的な余分である。

## ゼロ係数controlの要約

- 1群: merged rotation 2、非ゼロのみ 2、ユニタリ差 2.789e-17
- 2群: merged rotation 22、非ゼロのみ 18、ユニタリ差 0.000e+00
- 3群: merged rotation 37、非ゼロのみ 27、ユニタリ差 0.000e+00

## 範囲

これは決定論的小行列監査であり、分子Hamiltonianの新規計算、係数探索、GPU計算は行っていない。詳細なstep列は `step_sequences.json`、全数値はCSVに保存した。
