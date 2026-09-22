# 現在の研究方針と検証状況

最終更新：2026-09-22

最新の確認済み結果：ブランチ`gpu-h02-finite-time-controlled-state-results`、コミット`16bd6c2`

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

## H01/H02の停止判断

近似状態校正の主質問には次の結論が得られた。

1. exact-ground校正は数値的に再現する。
2. HF/CISDのエネルギー品質だけでは固定した予測基準を保証しない。
3. エネルギー誤差、分散、残差、重なりを組み合わせても一般の十分条件にはならない。

したがって、近似状態のスカラー閾値を追加調整するH01/H02系列はここで終了する。H03--H05の誤差演算子・BCH・高次係数取得は将来の安価な校正法候補として残すが、現在の主結論に必須の追加計算とはしない。これらを本格展開する場合は、研究目的を「安価な誤差演算子評価」へ拡張したことを明示する。

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

## 今後の作業範囲

### 必須

1. P0-3、H01、H02を主結果表、研究状況、データ使用履歴へ統合する。
2. `current_m3`＋三点/五点二項モデルのactive-space結果を同じ表で示す。
3. 直接格子最小が計算点集合上の最小であり、連続時間の大域最小ではないことを明記する。
4. P0-3 runnerの枝選択が各時刻最大基底重なりだったという監査上の差異を残す。合格主結果には枝切替の兆候がなかったが、将来runnerでは短時間からの連続追跡を用いる。
5. 校正点数と古典計算時間を量子コスト改善と分離して報告する。

### 現在は行わない

- `two_term_center`または新しいPF係数の再探索。
- H01/H02の近似状態閾値の追加調整。
- 結果を見ながら全電子分子や多項式次数を追加すること。
- H03--H05を主線として無制限に拡張すること。

全電子一般性を論文の必須主張へ変更する場合に限り、PF、モデル、校正点、分子、構造、判定基準を事前固定した新しい分子単位ホールドアウトを1回実行し、結果にかかわらず停止する。

## GitHub上の主要結果

| 内容 | 結果commit | 報告書 |
|---|---|---|
| NH3既存PF統一比較 | `46a7ed1` | `artifacts/server_existing_pf_unified_nh3_20260920_233516_e692360/aggregate/report.md` |
| N2/CO/HF固定ホールドアウト | `33a761d`、監査`3fb7974` | [`artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md`](../artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md) |
| H01近似状態校正 | `568f002` | [`artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/aggregate/report.md`](../artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/aggregate/report.md) |
| H02有限時間制御状態診断 | `16bd6c2` | [`artifacts/server_h02_finite_time_controlled_state_20260922_a228b5f/report.md`](../artifacts/server_h02_finite_time_controlled_state_20260922_a228b5f/report.md) |
| 三点対五点二項fit再集計 | 本統合ブランチ | [`artifacts/three_vs_five_point_holdout_reanalysis_20260922/report.md`](../artifacts/three_vs_five_point_holdout_reanalysis_20260922/report.md) |

## ファイルの読み順

1. 本書：現在の結論、適用範囲、停止判断。
2. [`docs/pf_data_use_ledger.md`](pf_data_use_ledger.md)：探索・開発・過去のホールドアウトの区別。
3. [`review_response/finite_time_cost_strategy.md`](../review_response/finite_time_cost_strategy.md)：直接有限時間評価と縮約校正の位置付け。
4. 上表のGit管理済み報告書：数値根拠。
5. [`docs/repository_guide.md`](repository_guide.md)：実装・検証・資料の所在。

指示書やrunnerが存在するだけでは検証完了を意味しない。成果物の`Status`、commit、条件数、manifestを確認する。未コミットのローカルpilotは確定証拠として扱わない。
