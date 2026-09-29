# PF研究成果bundle 証拠監査報告

監査日：2026-09-29
分類：`research_outcomes_documentation_and_evidence_audit`
固定snapshot：`fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
handoff ZIP SHA-256：`b3a3d0054a17c428cfe0d8958c70892b36538c84fdf72061d6e4f1b36726cc85`

## 結論

CL01–CL30を固定sourceへ照合した。科学的な数値訂正は0件で、研究ストーリーの再構成も不要だった。
修正は二層provenance、CL30の`governance_scope`分離、manifest自己除外の明示に限定した。

この監査は文書・保存値・hashの照合であり、新しい分子計算、PF/H作用、Arnoldi、gap計算、truth生成、
GPU操作を行っていない。第二研究、D2-A、scoring audit、C0の既存statusとartifactは変更していない。

## Source identity

- Git source：18件。全pathが固定snapshotで読め、bytes・SHA-256を`source_manifest.json`へ記録した。
- 外部source：S01は`arXiv:2605.30967v1`の版付きtitle/authors/abstract範囲。Git blobとは扱わない。
- 補助raw source：10件。主要なCSV/JSONの行数・分類数・保存scalarを直接照合した。
- origin/result commitとverified snapshot commitは別fieldで保持した。
- C0 decisionは、content commit後にplanning content identityを記録したためoriginとsnapshotのblobが異なる。
- R0 coordinate CSVはorigin後に改行正規化されたためblobが異なる。この履歴をregistryへ記録した。

## 原rowで再現した主要値

| 対象 | 再現結果 |
|---|---|
| 第一研究S0再解析 | 6 rows、`gamma=1.01` 6/6、`factor_pf=1` 6/6 |
| HF境界 | `F_domain >= 2.114659 / 2.069664`、`F_within <= 1.012709 / 1.003236` |
| S4 beta監査 | 42 rows、42/42 safe、outcome change 0、`no_benefit`不変 |
| R0/R1 | 10 coordinates、16 strategy rows、model/state/proxy/mixed=`6/4/2/4` |
| R1 counterfactual | local CISD 11/16、local exact 15/16 |
| D1 | 6 coordinates、60 top-K rows、weight-ranked最小合格K最大4 |
| D2-A audit | physical 6/6、旧integer 0/6、abstain 1、non-abstain safe 5、baseline未満0 |
| D2-A resource | PF actions 48、H matvecs 48、wall 2.617139 s、peak RSS 454656 KiB、GPU 0 |
| C0 | local-residual width 6/6、`S_max` 0.00327975–0.02286462、width比 1.1062–167.4915 |

## Claim audit

30件の状態、照合level、source、残る限定は`claim_evidence_audit.json`へ記録した。
科学主張の棄却0、科学数値訂正0、governance claim 1件である。
報告書・台帳levelまでの確認に留めたCLと、CSV/JSON原rowまで確認したCLを分離した。

## 残る確認事項

1. 公開プレプリントの新4次式とrepository内PF code ID・係数の同一性。
2. 第一研究128 caseの1536 raw decomposition rowの独立再count。本監査では固定統合報告の集計を確認した。
3. CL02の元oracle-assisted比較のraw rows。本監査では歴史的data-use ledgerまでを確認した。
4. HClのspin/sector/solver条件を越えた無条件の`CISD=FCI`主張は未支持。
5. truth-free full-space gap、ground/reference、branch/alias、rigorous action-error certificateは未確立。
6. 将来の有限校正費用方式は未実証・未承認。

これらは成果整理bundleの作成を妨げないが、解消済みと推測してはならない。

## 判定

文書bundleはGitHub evidenceへ追跡可能な内部成果整理版として統合できる。
statusは`research_outcomes_documentation_complete_review_required`とし、次は人間による成果文書レビューだけである。
新しい科学計算のauthorizationではない。
