# F02: fourth-order PF tau^8 state-mixing audit

Status: **complete_with_findings**

F01で抽出・独立検証したD4/D8を使い、a8をD8期待値とD4の二次状態混合へ分解した。H2/H4×4 PFの8条件を対象とする。

## Component identity

| system | PF | <D8> | D4 mixing | a8 | net/absolute components | largest excitation-group share |
|---|---|---:|---:|---:|---:|---:|
| H2 | yoshida4 | -9.742118e-07 | -2.298518e-07 | -1.204064e-06 | 1.0000 | 1.0000 |
| H2 | current_m3 | 5.930781e-10 | -3.969068e-10 | 1.961713e-10 | 0.1982 | 1.0000 |
| H2 | two_term_center | 1.939678e-10 | -2.081642e-10 | -1.419650e-11 | 0.0353 | 1.0000 |
| H2 | m5_best | 1.406484e-10 | -8.242569e-11 | 5.822269e-11 | 0.2610 | 1.0000 |
| H4 | yoshida4 | -6.623300e-05 | -9.050783e-06 | -7.528378e-05 | 1.0000 | 0.2629 |
| H4 | current_m3 | 2.240191e-08 | -1.431016e-08 | 8.091751e-09 | 0.2204 | 0.2724 |
| H4 | two_term_center | 8.287922e-09 | -8.088158e-09 | 1.997642e-10 | 0.0122 | 0.2729 |
| H4 | m5_best | 4.927308e-09 | -2.852180e-09 | 2.075128e-09 | 0.2667 | 0.2707 |

The mixing denominator is negative for every excited state, so the D4 second-order contribution is non-positive. Degenerate-state rows are also aggregated by energy because individual eigenvectors inside a degenerate subspace are basis-dependent.

## Direct signed-shift fit

The a8 coefficient is stable across all three direct-fit windows in **3/8** conditions under the declared 50% relative coefficient criterion.

| system | PF | stable | worst rel. a8 error | rel. window spread | max disagreement contribution / epsilon at t=0.8 |
|---|---|:---:|---:|---:|---:|
| H2 | yoshida4 | yes | 4.168e-04 | 5.406e-04 | 5.284e-07 |
| H2 | current_m3 | no | 2.814e+00 | 2.567e+00 | 5.811e-07 |
| H2 | two_term_center | no | 4.354e+01 | 3.995e+01 | 6.507e-07 |
| H2 | m5_best | no | 9.692e+00 | 8.804e+00 | 5.941e-07 |
| H4 | yoshida4 | yes | 7.527e-04 | 6.422e-04 | 5.966e-05 |
| H4 | current_m3 | yes | 8.282e-02 | 9.399e-02 | 7.056e-07 |
| H4 | two_term_center | no | 4.368e+00 | 4.489e+00 | 9.187e-07 |
| H4 | m5_best | no | 7.357e-01 | 8.277e-01 | 1.607e-06 |

## Interpretation

Yoshida 4次ではD4状態混合が相殺前成分絶対値和の12.0%–19.1%を占め、D8期待値と同符号でa8を増強する。

3つの最適化PFではD8期待値が正、D4状態混合が負で、状態混合は相殺前成分絶対値和の36.7%–51.8%を占める。two_term_centerの正味a8は成分絶対値和の1.2%–3.5%しか残らない。

直接固有値シフトの5項fitでa8が窓間安定したのは3/8条件。不安定5条件でもt=0.8での係数不一致の寄与は最大1.607e-06 epsilonであり、曲線再現の良さだけでは相殺後a8の機構成分を同定できない。

## Decision

F02の機構分解は完了した。ただし、相殺後のa8を通常の倍精度直接fitから相対精度よく取り出せない条件が5/8あるため、statusは`complete_with_findings`とする。これは恒等式の不成立ではなく、大きい二成分の差として残る小係数をfitする識別性の問題である。

次は保存済みの物理ギャップ・PF位相ギャップと本監査の励起状態別寄与を結合し、F05で真の小ギャップと位相折り返しを分離する。

## Files

- `audit.json`: complete summary and checks.
- `condition_summary.csv`: component ratios and direct-fit stability.
- `excited_state_contributions.csv`: state-resolved D4 mixing.
- `degenerate_group_contributions.csv`: basis-invariant energy-group sums.
- `direct_fit_comparison.csv`: three-window signed direct fits.
- `manifest.json`: input/source/artifact hashes and runtime.
