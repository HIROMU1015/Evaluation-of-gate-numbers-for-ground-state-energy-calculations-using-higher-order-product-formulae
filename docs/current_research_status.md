# 現在の研究方針と検証状況

最終更新：2026-09-25

最新の確認済み結果：ブランチ`resource-metric-sensitivity-20260925`、コミット`b5af699`

この文書は、古い実行指示や途中結果を現在の結論と誤認しないための入口である。数値を引用するときは、ここからリンクしたGit管理済み報告書も確認する。

## 研究目的

主目的は、単にPF固有値誤差やQPEコストが最小になるproduct formula（PF）を探すことではない。有限個の校正情報から最適時刻とQPE総コストを予測でき、その予測が直接PF固有値計算と一致するPF・有限時間モデルを得ることである。予測可能性を満たす範囲で量子コストを下げる。

4次PFの現在の主モデルは、符号付きPF固有値シフトを

$$
\delta E(t)=a_4t^4+a_6t^6
$$

とする二項モデルである。`e_direct`は、保存則セクター内のPFユニタリを構築・対角化し、$t\to0$で厳密基底状態へ接続する固有枝から得た符号付きエネルギーシフトを指す。重なり位相は代理量であり、`e_direct`とは呼ばない。

## 現在の主結論

### 1. active-spaceでは既存PFと二項モデルが主候補

事前固定した未使用分子N2/COの凍結内殻CAS(10e,8o)、平衡・1.5倍伸長4条件では、次が固定モデルで4/4合格した。

- Yoshida 4次＋二項モデル。
- `current_m3`＋二項モデル。
- `two_term_center`＋二項モデル。
- Yoshida 6次m=3＋三項モデル。

`m5_best`＋二項モデルは0/4だった。合格PFの中では`current_m3`の直接格子最小コストが最小で、凍結QPE予算も4/4達成した。`current_m3`に対する直接コスト比は、`two_term_center`が1.148--1.161、Yoshida 4次が1.900--1.936、Yoshida 6次が1.587--1.770だった。

したがって、現在のactive-space主候補は`current_m3`＋二項モデルである。`two_term_center`は予測可能性を優先した概念実証として残すが、現時点で再探索・微調整を優先しない。

### 2. 三点校正はactive-spaceの縮約候補

未使用N2/COで事前指定した三点二項アブレーションと五点二項主解析を比べると、比較可能な4次PFについて全16 PF・Hamiltonian組の合否、凍結予算、1%余裕付き予算が一致した。Yoshida 4次、`current_m3`、`two_term_center`は両方で4/4合格し、`m5_best`は両方で0/4だった。

このため、$0.1,0.2,0.3t_{\mathrm{ana}}$の三点二項fitをactive-space向け縮約候補とし、五点fitは参照・監査用に残す。ただし、同じ4条件による副解析であり、全電子系や別の分子クラスへ一般化済みとは扱わない。

### 3. 全電子一般性は未確立

全電子HF/STO-3Gでは、平衡構造でYoshida 4次＋二項モデルが合格した一方、1.5倍伸長では固定した主PF・モデル対がすべて不合格だった。全電子NH3でもPF・モデル依存の不合格が確認されている。

したがって、現在の肯定的な主張範囲は凍結内殻active-spaceである。全電子一般性を本研究の主張に含めるまでは、全電子専用PFまたは普遍PFが得られたとは書かない。現在は追加の全電子分子を後付けで増やさず、この境界を未解決事項として明示する。

### 4. 現在の校正はoracle-assisted

N2/COの主結果は各Hamiltonian・PFについて厳密基底状態と直接PF固有値点を使う`oracle-assisted target calibration`である。未知分子を高価な校正なしに予測できた、という結果ではない。

H01ではexact-ground echoが主4条件・2 PFで8/8合格した一方、CISDおよびRHFへの置換は固定した4基準を全条件で満たさなかった。CISDは1%余裕付き凍結予算を満たしても、予測時刻・コスト・残差の厳密基準には合格しなかった。

H02では、状態エネルギー誤差、分散、Hamiltonian残差、厳密基底状態重なりが同じ制御状態を作った。32/32位相quartetで予測時刻またはモデルコストが1%以上変化した。PF選択反転と選択損失は0だったため、これはPF選択失敗の実証ではなく、通常の状態品質スカラーだけでは有限時間校正精度を保証できないという反例である。

### 5. full-electron破綻は「先頭演算子が小さい」だけでは説明できない

F01/F02/F05のHF平衡・1.5倍伸長比較では、Yoshida 4次＋五点二項モデルの成功例と破綻例を、同一Hamiltonianキャッシュ上の有効Hamiltonian係数と固有枝診断で比較した。伸長時には`|a4|/||D4||`が`2.43e-3`から`7.02e-4`へ低下した一方、`D4`の非対角結合と状態混合は消えず、解析最適時刻は1.384倍へ伸び、`t_ana`での8次寄与比は`0.00767`から`0.0371`へ増えた。正規化PF位相gapの圧縮は観測されなかった。

F03のH2/H4×4 PFと人工二準位族でも、小さい`a4`と小さい`D4`は一致しなかった。`m5_best`では中心化した`D4`作用が`|a4|`の40--67倍であり、人工族で`a4`の零点へ近づくと`D4`ノルムを保ったまま一項解析時刻の直接誤差が100倍以上の目標誤差へ増大した。連続枝追跡に警告はなく、この破綻を枝選択だけでは説明できない。

したがって、全電子伸長条件の破綻は、小さい対角先頭係数を「誤差演算子全体が小さい」と解釈して長い時刻を選ぶことと、高次寄与・状態混合が組み合わさる境界として扱う。これは候補機構の切り分けであり、単一原因の厳密証明ではない。

### 6. oracle-free最小selectorは安全性候補を得たが、低regretではない

固定後にtruthを入力する二段階評価で、CISD状態とsigned proxyからPF・時刻・QPE配分を選ぶ最小selectorを評価した。選択時には厳密基底状態、直接PF固有値シフト、直接最適時刻、過去の合否を与えていない。

N2/CO主4条件とHF stress 2条件の全6条件で、1%余裕付き凍結予算は6/6達成し、棄却は0だった。ただし選択は全条件で`current_m3`となり、oracle格子最小に対する最大選択損失はN2/COで22.4%、HFで114%だった。これは安全な運用候補のdevelopment evaluationであり、独立ホールドアウトを通過した低regret selectorではない。

### 7. 目標精度依存は代表範囲で確認したが、coverageに限界がある

D03ではCA、CA/10、CA/100を固定し、既存truth curveを優先して代表PFの順位とモデル有効性を再評価した。N2の代表条件では、CA/10とCA/100で`current_m3`、Yoshida 4次、Yoshida 6次が評価可能かつ合格し、`current_m3`が最小コストだった。CAでは`current_m3`の保存済みcoverageがなく、Yoshida 4次と6次だけが比較可能だった。

全体coverageはNH3でCA `0/14`、CA/10 `13/14`、CA/100 `2/14`、P0-3集合でCA `4/24`、CA/10 `18/24`、CA/100 `8/24`だった。このため、代表N2では厳密化による順位逆転を確認しなかったが、「高次PFはどの精度でも有利にならない」という一般結論にはしない。

### 8. 代表N2では資源指標を変えてもPF順位は不変

M01では、N2平衡・伸長とCA/10・CA/100の4比較群について、合格PFだけを対象に総Pauli rotation数、RZ-layer depth、T-count、T-depthを比較した。4指標すべてで`current_m3`が4/4最小となり、最良PFの変化は0/4、pairwise inversionも0だった。Yoshida 4次/`current_m3`比は約1.89--2.04、Yoshida 6次/`current_m3`比は約1.31--1.72だった。

HF伸長では生の資源量が安くても予測モデルが不合格のPFがある。したがって、資源指標感度は予測適格性を先に判定した後の比較であり、回路全体のruntime評価ではない。

## 機構診断・近似状態診断の停止判断

H01/H02により、exact-ground校正の数値再現と、通常の状態品質スカラーだけでは有限時間校正精度を保証できないことを確認した。F01/F02/F03/F05により、先頭対角係数、演算子ノルム、非対角結合、状態混合、高次寄与、位相gapを分離して比較できた。したがって、状態品質スカラーの閾値調整とF領域の追加分解はここで停止する。

今後F/H領域を再開するのは、固定したoracle-free selectorの棄却規則または安全余裕を事前に改善する具体的仮説がある場合に限る。既存のF結果を見て同じHF条件へ特徴量を後付けし、その条件を検証集合と呼ぶことはしない。

## 現在固定する評価規則

- 目標誤差：$\epsilon_E=1.5936001019904\times10^{-4}$ Hartree。
- 短時間格子：`geomspace(0.02, 1.8, 34)`。
- rolling window：5点。
- 雑音床：$5\times10^{-13}$ Hartree。
- 形式次数許容差：0.2。
- 最小$R^2$：0.999。
- 条件を満たす最初の窓を採用する。
- 主参照：五点`0.1,0.2,0.3,0.4,0.5 t_ana`。
- active-space縮約候補：三点`0.1,0.2,0.3 t_ana`。
- 凍結予算の安全余裕：主結果と区別して1%を併記する。

モデル判定は次の4基準を維持する。

- モデル予測時刻でのコスト相対誤差1%以下。
- 計算した局所格子最小に対する直接コスト損失1%以下。
- 予測時刻と直接格子最小時刻の差5%以下。
- 未使用時刻での最大符号付き誤差残差$0.05\epsilon_E$以下。

## 事前検証の終了判断

当初残していた5項目の到達状況は次のとおりである。

| 項目 | 状態 | 到達点 | 残る制約 |
|---|---|---|---|
| ① F01/F02/F05：破綻機構 | 完了 | HF成功・破綻対で演算子対角項、結合、混合、高次寄与、gapを比較 | 単一原因の厳密証明ではない |
| ② practical calibration最小版 | 完了・有望 | truthを隠した選択で1%余裕付き予算6/6達成 | development評価であり、最大regretはN2/CO 22.4%、HF 114% |
| ③ D03：目標精度依存 | 完了・coverage制約あり | 代表N2のCA/10・CA/100で`current_m3`最小 | CAとCA/100の全体coverageは不完全 |
| ④ 資源指標感度 | 完了 | 代表N2の4比較群・4指標で順位不変 | controlled-U、状態準備、QFT、routing、factoryは未算入 |
| ⑤ 結果統合・研究方針台帳 | 完了 | 本書、有限時間戦略、データ使用履歴へ統合 | 新しい数値証拠は生成していない |

この段階で、事前検証は次の研究テーマを選べるだけの情報を得た。大規模分子ホールドアウトを追加し続ける必要はない。

### 採用する研究方針

- 真値参照：厳密基底状態と直接PF固有値による五点二項校正を、機構解釈・採点用のoracle基準として維持する。
- 運用候補：`current_m3`、CISD由来signed proxy、固定した1%安全余裕を用いる最小selectorを主候補とする。
- 適用範囲：肯定的主張は凍結内殻active-spaceとし、全電子伸長は棄却・境界診断の対象とする。
- PF探索：新しい係数探索は停止する。既存PFが固定した独立評価で安全性またはコスト目標を満たさない場合だけ再検討する。
- 高次数：代表N2で順位逆転は見つからなかったが、coverage外へ一般化しない。高精度域を論文の主題にする場合だけ、事前登録した不足点を限定補完する。
- 資源量：総rotationだけに依存した順位ではなかった。より完全なfault-tolerant costは、QPE回路設計を次テーマに選ぶ場合だけ評価する。

### 次に行うなら1件だけ

practical selectorのコード、候補PF、proxy、時刻候補、安全余裕、棄却規則、採点式を結果を見る前に固定し、数値的に未使用のactive-space分子群で1回だけ独立評価する。この試験ではtruthを選択段階から隔離し、主判定を1%余裕付き予算の安全率、coverage、oracle最良に対するregretとする。分子を結果に応じて交換せず、成功・失敗にかかわらず一度停止する。

### 現在は行わない

- `two_term_center`または新しいPF係数の再探索。
- H01/H02の状態品質スカラー閾値の追加調整。
- 同じN2/CO/HFをpractical selectorの独立検証として再利用すること。
- 全電子一般性を得るための分子・基底・モデル次数の後付け追加。
- D03のcoverage不足を、研究主題を決めずに全面補完すること。
- 回路全体を含まないproxyから実機runtimeを断定すること。

直接格子最小は、計算済み時刻集合上の最小であり連続時間の大域最小ではない。P0-3 runnerは各時刻の最大基底重なりを用いており、合格主結果に枝切替兆候はなかったが、将来runnerでは短時間からの連続追跡を用いる。校正点数と古典計算時間は量子コスト改善と分離して報告する。

## GitHub上の主要結果

| 証拠の役割 | 内容 | 結果commit | 固定報告書 |
|---|---|---|---|
| 開発比較 | NH3既存PF統一比較 | `46a7ed1` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/46a7ed165650cb80506be14d997380e0bf333680/artifacts/server_existing_pf_unified_nh3_20260920_233516_e692360/aggregate/report.md) |
| 総合索引 | カタログから実行した固定結果 | 本ブランチ | [index](prevalidation_results_index.md) |
| 基盤監査 | B01--B08、C02/C03、X01/X02 | `2ba6174` | [artifact tree](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/tree/2ba6174b6f9617d51766579c775a77132f3c7f57/artifacts) |
| 古典予算・小系機構 | D04、F01/F02/F05、H01 pilot、H03/H04/H05 | `6d13384` | [artifact tree](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/tree/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts) |
| 機構診断 | F03：小さいa4と小さいD4の区別 | 本ブランチ | [report](../artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md) |
| 当時の固定ホールドアウト | N2/CO主・HF補助 | `33a761d` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md) |
| oracle近似状態診断 | H01 | `568f002` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/568f00249abb5b89ae3e6bb39cb4af87ed8581bd/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/aggregate/report.md) |
| oracle機構反例 | H02 | `16bd6c2` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe/artifacts/server_h02_finite_time_controlled_state_20260922_a228b5f/report.md) |
| oracle機構診断 | F01/F02/F05 HF bridge | `6eb1aa0` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md) |
| oracle-free selector開発評価 | practical calibration最小版 | `4f4374b` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/report.md) |
| reuse/coverage感度 | D03目標精度依存 | `a8b9a92` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a8b9a92c9fcdb1b4187d5aa3c239ed8b7443dcfd/artifacts/server_d03_target_accuracy_followup_20260923_748b3d4/report.md) |
| reuse/coverage感度 | M01資源指標感度 | `b5af699` | [report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5af6996159b3dfbd6e5bb3cc2467cb23155906d/artifacts/prevalidation_m01_resource_metric_sensitivity_20260925_3b6e5f0/report.md) |

## ファイルの読み順

1. 本書：現在の結論、適用範囲、停止判断。
2. [`docs/prevalidation_results_index.md`](prevalidation_results_index.md)：実行済み最終結果の固定commitと報告書。
3. [`docs/pf_data_use_ledger.md`](pf_data_use_ledger.md)：探索・開発・過去のホールドアウトの区別。
4. [`review_response/finite_time_cost_strategy.md`](../review_response/finite_time_cost_strategy.md)：直接有限時間評価と縮約校正の位置付け。
5. 上表のGit管理済み報告書：数値根拠。
6. [repository_guide.md](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/20d64c2fea1ed2d2188777df4f3d962ee94df486/docs/repository_guide.md)：実装・検証・資料の所在。

指示書やrunnerが存在するだけでは検証完了を意味しない。成果物の`Status`、commit、条件数、manifestを確認する。未コミットのローカルpilotは確定証拠として扱わない。
