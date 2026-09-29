# 第2研究v2 pre-design correction log

基準commit：`599a9f2e9a45302b8d34192ef581fd3ea55a1f1e`
実行規約commit：`4c579886b49d1c0aef7362809ed5e41a7a77d660`

## 結論

科学数値の訂正は0件である。既存artifactと既存statusは変更していない。

## 表記・provenance上の処置

| 項目 | 処置 | 科学数値への影響 |
|---|---|---|
| PF選択因子 | 既存台帳に合わせ`F_PF`へ統一 | なし |
| headroom | `isolated_factor_algebraic_headroom`と保存counterfactual効果を分離 | なし |
| access | snapshot上の可用性と未知条件でのoperational availabilityを分離 | なし |
| truth | `new_truth_count=0`と保存truthのread countを分離 | なし |
| data-use ledger | 2026-09-25台帳に未収録のLiF/HClを監査済み後続sourceで補完 | 旧台帳は不変更 |
| D2-A branch | 元integer比較でなく既存read-only auditの表現不変判定を使用 | 元D2-A statusは不変更 |

## 限定

`H(F)=1-1/F`は他factor固定の代数値であり、因果的に達成可能な最大削減率ではない。
materiality thresholdは固定していない。
