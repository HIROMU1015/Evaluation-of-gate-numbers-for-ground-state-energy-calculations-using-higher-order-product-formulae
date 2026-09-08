# m=3未使用サイズ検証に引き継ぐ短時間フィット規則

これはH2/H4/H5での候補探索とH6のCPU検証で実際に使用した規則である。H8/H9でも同じ規則を使う。以前の引き継ぎには閾値と窓選択コードの共有が不足していたため、ここに明記する。

## 計算点と誤差量

- 時刻：`np.geomspace(0.06, 0.80, 15)`。両端を含む対数等間隔15点。
- 使用する誤差：短時間の摂動推定値。既存実装は $U(t)\simeq e^{+iHt}$ の符号なので、$z(t)=e^{-iE_0t}\langle\psi_0|U(t)|\psi_0\rangle$、$e(t)=|\operatorname{Im}z(t)|/t$ とする。定数項を除いたHamiltonianと同じエネルギーを使う。
- 形式次数：4。
- 数値雑音の下限：`5e-13` Hartree。今回はGPU差から下限を再推定する規則ではない。

## 窓の合否と選択

元の15点の並びから連続5点ずつ、開始位置を1点ずつずらす。全部で11窓が候補になる。

1. 5点すべての誤差が有限かつ **厳密に `5e-13` より大きい**窓だけを評価する。雑音以下の点を取り除いて離れた点をつなぐことはしない。
2. 対数上で切片と次数を自由に最小二乗フィットし、`abs(free_order - 4) <= 0.2` かつ `r2 >= 0.999` を要求する。
3. 合格窓のうち **開始位置が最も早い窓**を採用する。次数が4に最も近い窓や、最長の窓を選ぶ規則ではない。
4. 採用窓について、次数4に固定した係数を

   $$
   \alpha=\exp\left[\frac{1}{5}\sum_{i\in\mathrm{window}}\log\frac{e(t_i)}{t_i^4}\right]
   $$

   で求める。自由フィットの切片から得る係数は最終的な $\alpha$ に使わない。
5. 合格窓がなければ `qualified=false`、`selected_window=null` とし、このモデルによる解析適格性を不合格とする。閾値や時刻範囲を変更して合格させない。

端点除外による係数安定性は、この実行時の合否条件には含まれていない。全15点の自由フィットも参考値であり、採用判定には使わない。

## 同じ規則を実行するコード

窓計算は既存の `src/trotterlib/fit_window.py` の `rolling_loglog_fits` をそのまま使える。選択処理は次のとおりで、元の `select_declared_fit_window` と同じである。

```python
import numpy as np
from trotterlib.fit_window import rolling_loglog_fits

times = np.geomspace(0.06, 0.80, 15)
windows = rolling_loglog_fits(
    times, np.asarray(errors), formal_order=4,
    noise_floor=5e-13, window_size=5,
)
eligible = [w for w in windows
            if w["order_deviation"] <= 0.2 and w["r2"] >= 0.999]
selected = min(eligible, key=lambda w: (
    w["start_index"], w["stop_index_exclusive"]
), default=None)
qualified = selected is not None
alpha = None if selected is None else selected["fixed_order_alpha"]
```

`select_best_rolling_fit` は別規則なので使用しない。最終合否にも `short_time_fit_qualified` を含める。

計算量を減らすため、最初の5点から始めて合格したら停止してよい。失敗時は次の点を1点だけ追加して次の連続5点を調べ、最大15点で停止する。この順序なら全11窓を評価した場合と採用窓は同一である。未計算の窓は未計算として保存する。

GPU側H7実装は最初の5点だけを計算している。今回の3候補はその窓が上記条件を満たすため採用窓は整合するが、H8/H9で最初の窓が不合格の場合は後続窓の確認が必要になる。

保存項目は、規則の数値、計算した時刻と誤差、評価窓、採用窓、`qualified`、最終 $\alpha$ とする。数値精度不足が疑われる場合は同条件で精度を調べ、規則の変更が必要なら別検証として報告する。
