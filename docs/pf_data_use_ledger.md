# PF研究データ使用履歴

最終更新：2026-09-25

この文書は、分子やHamiltonian条件が係数探索、解析規則の開発、または結果確認に使われたかを記録する。過去に「ホールドアウト」として導入した条件でも、その結果を見た後は、将来の研究全体に対する完全未使用条件とは扱わない。

## 判定区分

- **探索・訓練**：PF係数または候補の選択に使用した。
- **開発・診断**：係数は固定されていたが、モデル次数、時刻格子、閾値、枝選択、次の候補選定に結果を使用した。
- **過去のホールドアウト**：当時の問いには未使用だったが、現在は結果を確認済みである。
- **数値的に未使用**：計画書で名前が挙がっただけで、PF誤差やQPEコストの結果を見ていない。

## 使用済み条件

| 分子・系列 | 主な条件 | これまでの役割 | 今後の扱い |
|---|---|---|---|
| H-chain | H2、H4、H5、およびH6以降の複数サイズ | 初期のPF比較、係数探索、サイズホールドアウト、代理診断 | 使用済み。新しい分子ホールドアウトには数えない |
| LiH | STO-3G、6-31G、cc-pVDZ、active-space変更 | `two_term_center`の選択集合および後続診断 | 探索・開発に使用済み |
| BeH2 | 3基底、平衡・伸長、active-space変更、全電子条件 | `two_term_center`の選択集合、構造ホールドアウト、共同探索、凍結予算監査 | 探索・開発に使用済み |
| H2O | 3基底、平衡・伸長、active-space変更、全電子STO-3G | `two_term_center`の選択集合、高次項・全電子診断、共同探索 | 探索・開発に使用済み |
| NH3 | 3基底のactive space、平衡・伸長、全電子STO-3G | 当初の分子ホールドアウト。その後、短時間格子、モデル次数、固有枝、既存PF統一比較の開発集合 | 完全未使用ではない。今後は開発集合 |
| CH4 | 6-31G、cc-pVDZ、平衡・1.25倍伸長、凍結内殻CAS | ローカルで二項モデルと中間時刻を評価済み。成果物は2026-09-21時点で未コミットのものを含む | 数値結果を確認済みなので完全未使用ではない |
| N2 | STO-3G、凍結内殻CAS(10e,8o)、平衡・1.5倍伸長 | 固定PF・モデルの主未使用分子ホールドアウト、その後H01/H02、practical selector、D03、M01 | コミット`33a761d`以後の方法選択にも使用済み。今後は開発集合 |
| CO | STO-3G、凍結内殻CAS(10e,8o)、平衡・1.5倍伸長 | 固定PF・モデルの主未使用分子ホールドアウト、その後H01/H02、practical selector、D03 | コミット`33a761d`以後の方法選択にも使用済み。今後は開発集合 |
| HF | STO-3G、全電子、平衡・1.5倍伸長 | 補助ホールドアウト、その後H01、F01/F02/F05、practical stress、D03/M01診断 | 全電子破綻機構とselector境界の開発に使用済み。独立検証には使わない |

主な根拠は、`docs/current_research_status.md`、`review_response/pf_cost_predictability_handoff.md`、Git管理済みの各報告書、およびローカルの既存`artifacts/`である。NH3の統一比較はブランチ`gpu-existing-pf-unified-nh3`、コミット`46a7ed1`、N2/CO/HFの固定ホールドアウトはブランチ`gpu-unused-molecule-frozen-holdout-results`、コミット`33a761d`にある。

## 2026-09-21固定ホールドアウトの結果

N2/COの主4条件では、Yoshida 4次＋二項、`current_m3`＋二項、`two_term_center`＋二項、Yoshida 6次m=3＋三項が4/4合格し、`m5_best`＋二項は0/4だった。`current_m3`は合格PFの中で直接コストが最小で、凍結予算も4/4達成した。全電子HFでは、平衡構造でYoshida 4次＋二項が合格したが、1.5倍伸長では固定した主モデルがすべて不合格だった。

この結果は各Hamiltonianで直接固有値5点を使う`oracle-assisted target calibration`の分子間転用性を検証したものであり、高価な校正なしの未知分子予測を意味しない。

同じ固定プロトコルに事前指定されていた三点二項アブレーションを五点二項主解析と[再集計](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/20d64c2fea1ed2d2188777df4f3d962ee94df486/artifacts/three_vs_five_point_holdout_reanalysis_20260922/report.md)したところ、比較可能な4次PFの全16 PF・条件組で、4基準の合否、凍結予算、1%余裕付き予算が一致した。このため三点fitをactive-space縮約候補、五点fitを参照・監査用とする。この再集計はN2/COを新しいホールドアウトとして再利用したものではなく、同じ実行内の固定副解析である。

## H01/H02後の扱い

H01ではN2/COを主開発集合、HFを補助診断集合としてRHF・CISD校正を評価した。H02ではN2/COについて、同じエネルギー誤差・分散・残差・厳密重なりを持つ制御状態の有限時間応答を評価した。通常の状態品質スカラーだけでは有限時間校正の適格性を保証できないという結論を得たため、この閾値調整系列は停止した。

## 2026-09-23以降の追加使用

| 検証 | 使用した数値条件 | データの役割 | 独立性への影響 |
|---|---|---|---|
| F01/F02/F05 HF mechanism bridge | HF平衡・伸長、Yoshida 4次を主比較、`current_m3`を診断対照 | H01 cacheと保存済みdirect truthを用いたoracle機構診断 | HFは演算子特徴量、状態混合、高次寄与、棄却境界の開発にも使用済み |
| practical calibration最小版 | N2/CO主4条件、HF stress 2条件 | truthを選択器から遮断したdevelopment評価。採点時だけ既存truthを使用 | N2/CO/HFはselector、1%安全余裕、sentinel、regret判断のホールドアウトではない |
| D03目標精度依存 | NH3、N2/CO/HFの保存済み曲線と限定follow-up | CA、CA/10、CA/100のcoverage・順位診断 | 使用条件は精度域選択の開発集合。coverage外へ一般化しない |
| M01資源指標感度 | N2平衡・伸長のCA/10・CA/100、HF伸長診断 | 合格PFについてrotation、RZ depth、T-count、T-depthを再集計 | N2/HFは資源指標選択の開発集合。新規PF固有値点は0 |

これらの検証後、N2、CO、HFにはpractical selectorの独立ホールドアウトとしての余地は残っていない。NH3も短時間規則、モデル次数、PF比較、D03に使用済みである。既存結果を再利用したD03/M01は新しい分子ホールドアウトではなく、reuse/coverage sensitivityとして扱う。

## 次の独立検証で固定すべきもの

次の研究テーマをoracle-free selectorとする場合、数値的に未使用のactive-space分子群を開く前に、少なくとも次をcommitとhashで固定する。

- selector実装と入力schema。
- 候補PF、proxy式、proxy時刻、選択可能な絶対時刻。
- 1%安全余裕と、棄却・fallback規則。
- truthを選択段階から隔離する手順。
- coverage、安全予算達成率、unsafe件数、oracle最良に対するregretの採点式。
- 分子、構造、基底、active space、および一度で停止する規則。

分子名は実行前に固定し、PF誤差やQPEコストを確認してから交換しない。ローカルとGPUサーバーの既存成果物を実行前に再検索する。結果が成功でも失敗でも、その1回を報告して停止し、同じ集合でselectorや安全余裕を再調整しない。

現在の肯定的主張範囲は凍結内殻active-spaceである。追加の全電子分子、別基底、別目標精度は自動的に加えない。

## 独立性の境界

2026-09-21の検証で独立だったのは、固定済みPF・モデル形式・時刻規則をHF、N2、COへ移したときの成否である。今後、これらの結果を用いて近似状態、モデル、時刻、閾値、安全係数、PF候補を選択した場合、HF・N2・COはその選択に対するホールドアウトではない。
