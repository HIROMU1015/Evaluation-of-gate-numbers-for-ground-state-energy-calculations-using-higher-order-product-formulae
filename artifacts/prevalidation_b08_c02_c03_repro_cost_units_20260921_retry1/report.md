# B08・C02・C03 再現性とQPEコスト単位の一括監査

- 総合状態: **complete_with_findings**
- 個別状態: B08=complete_with_findings, C02=complete, C03=complete
- 既存成果物は読み取り専用。係数探索・新規分子計算は未実施。

## B08 失敗・欠損・cache・seed

joint refinementの387候補×7 training条件=2709枠を明示的に台帳化した。

| status | 件数 | 意味 |
|---|---:|---|
| completed | 572 | 実計算完了 |
| failed | 1 | 直接誤差が予算を使い切り有限costなし |
| censored | 2136 | 事前定義hard-condition screenで終了 |
| plannedで未記録 | 0 | 期待レコード欠損 |
| reserved not_run | 4 scopes | 未使用holdout |

唯一のfailedは数値例外やOOMではなく、`current_m3 / BeH2_full_eq` の `infeasible_error_budget` 相当である。censored条件を失敗にも成功にも数えず、shortlistの勝率を全387候補へ一般化しない。

plain JSONとgzip JSON、同一seedの候補再生成2回、保存済み候補との係数hash、既存cacheの数値同値検査はすべて合格した。seed再生成一致: `True`。

再現性metadataには不足がある。joint refinementはseed・Hamiltonian/grouping hash・係数を持つが、git commitとpackage環境を保存していない。

`pyproject.toml` の `testpaths` は `review_tests/` へ修正済みで、引数なしのpytest探索対象に 29 個の `test_*.py` モジュールが入る。B08-F01は解消した。

## C02 解析最適時刻とQPE反復係数

ランダム正値 24 ケースで、`t*=[epsilon/((p+1)alpha)]^(1/p)`、独立1次元最適化、`_qpe_iteration_factor`が一致した。最大時刻相対差 `8.263e-09`、保存済みjoint時刻の最大差 `0.000e+00`。

`2π`はQPEのradian phase grid（間隔 `2π/T`）でβへ校正済みであり、エネルギーcost式へ別の `2π` を追加しない規約と整合した。free-order fitは窓の適格性判定に使い、解析時刻はformal orderとfixed-order alphaを使っている。

### T-depth式の修正確認

`t_depth_extrapolation` と `t_depth_extrapolation_diff` の2箇所を、共通の `analytic_optimal_time` へ接続した。旧式の残存数は `0`、修正済みhelper呼び出しは `2` 箇所である。

以下は修正前の式が生じさせていた差であり、回帰テストの比較対象として保存した。

| p | 旧時刻 / 正しい時刻 | 旧1回転あたりT-depth過小量 |
|---:|---:|---:|
| 2 | 3.000000 | 4.754888 |
| 4 | 2.236068 | 3.482892 |
| 6 | 1.912931 | 2.807355 |
| 8 | 1.732051 | 2.377444 |
| 10 | 1.615394 | 2.075659 |

修正対象はrotation synthesis精度とT-depthだけであり、共通の解析時刻、直接cost、`_qpe_iteration_factor`、総RZ layer数はもともと影響を受けない。

既存figureツリーにはT-depth図が 0 件、RZ指標図が 6 件あった。notebook内の該当 3 呼び出しはすべて `rz_layer=True` である。よって再生成対象は0件で、RZ図は上書きしていない。

## C03 コスト単位

8 PF×H2/H4の 16 行について、compact m、S2 block数、merge前後の群指数数、Pauli rotation数、RZ layer depthを分離した。registryを持つ 8 行では固定表との差は rotation `0`、RZ layer `0` で全一致した。

QPE総rotationは `M_QPE × rotations/PF-unitary`、総RZ layer depthは `M_QPE × RZ-layers/PF-unitary` として別々に計算した。今回のH2集合では両指標の順位は偶然一致するが、値と物理的意味は異なり、いずれも制御化・合成・routingを含む実行時間ではない。

## 判断

pytest探索設定とT-depth時刻式は修正され、C02とC03は `complete`。B08は過去のjoint refinement成果物にcommit/package環境が無いというB08-F02だけが残るため `complete_with_findings` である。
