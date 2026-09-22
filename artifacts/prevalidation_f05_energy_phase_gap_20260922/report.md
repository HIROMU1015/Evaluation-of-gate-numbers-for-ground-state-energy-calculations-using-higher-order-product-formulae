# F05: physical energy gap versus finite-time PF phase gap

Status: **complete**

X02の直接枝曲線とF02のD4状態混合を結合し、物理エネルギーギャップ、有限時刻PF位相ギャップ、結合行列要素の役割を分離した。新しいPF直接点は計算していない。

## Conditions

| system | PF | physical min gap | dominant mixing gap | gap ratio | lowest-gap mixing share | min reliable normalized phase gap | first warning |
|---|---|---:|---:|---:|---:|---:|---:|
| H2 | yoshida4 | 0.355279 | 1.140198 | 3.209 | 1.717e-31 | 1.0000 | 3.9177 |
| H2 | current_m3 | 0.355279 | 1.140198 | 3.209 | 1.522e-34 | 0.1078 | 5.3901 |
| H2 | two_term_center | 0.355279 | 1.140198 | 3.209 | 2.287e-33 | 0.0683 | 5.4334 |
| H4 | yoshida4 | 0.232630 | 1.614830 | 6.942 | 2.651e-31 | 0.3115 | 2.1055 |
| H4 | current_m3 | 0.232630 | 2.079811 | 8.940 | 3.125e-33 | 0.0208 | 2.5943 |
| H4 | two_term_center | 0.232630 | 2.079811 | 8.940 | 1.029e-32 | 0.0187 | 2.5943 |

## Findings

短時間ではphase_gap/tが物理最小ギャップに一致し、6条件の最大相対差は1.362e-05だった。これは物理ギャップと位相ギャップのt→0対応を数値的に確認する。

最低励起群のD4二次混合への最大寄与率は2.651e-31で、支配群のギャップは最小物理ギャップの3.21–8.94倍だった。小ギャップだけでなく結合行列要素が必要である。

同一system内でも信頼枝中の最小normalized phase gapと最初の枝警告時刻はPF依存であり、有限tauの位相近接を固定された物理ギャップだけから推定できない。最初の警告は全6条件でground-overlap低下を含み、phase-gap絶対閾値単独ではなかった。

位相ギャップが短時間線形値の10%未満へ圧縮されたのは3/6条件。一方、最初の枝警告がX02の位相ギャップ絶対閾値で発火した条件は0/6で、警告後の孤立した小位相ギャップは信頼枝の根拠に使っていない。

## First-warning causes

| system | PF | selection disagreement | ground overlap <0.9 | previous overlap <0.9 | phase gap <1e-6 | phase gap (rad) |
|---|---|:---:|:---:|:---:|:---:|---:|
| H2 | yoshida4 | no | yes | no | no | 1.452597e+00 |
| H2 | current_m3 | no | yes | no | no | 1.679538e-01 |
| H2 | two_term_center | no | yes | no | no | 9.632628e-02 |
| H4 | yoshida4 | no | yes | no | no | 6.531348e-02 |
| H4 | current_m3 | no | yes | yes | no | 1.698258e-02 |
| H4 | two_term_center | no | yes | yes | no | 1.409347e-02 |

## Decision

F05の最小検証は完了した。最小物理ギャップだけではD4状態混合を説明できず、位相近接も固定された物理ギャップの単純な写像ではない。PFとtauに依存する位相圧縮、対象枝の重なり、結合行列要素を併記する必要がある。

この小系結果は、全電子HF伸長条件の破綻原因を直接確定するものではない。同条件へ適用する場合は同じ枝・基底を保存した追加診断が必要である。

## Files

- `audit.json`: complete machine-readable result.
- `condition_summary.csv`: six joined condition summaries.
- `phase_gap_points.csv`: all reliable and post-warning phase-gap points.
- `mixing_gap_groups.csv`: F02 degenerate energy-group contributions.
- `manifest.json`: source, input, artifact hashes and runtime.
