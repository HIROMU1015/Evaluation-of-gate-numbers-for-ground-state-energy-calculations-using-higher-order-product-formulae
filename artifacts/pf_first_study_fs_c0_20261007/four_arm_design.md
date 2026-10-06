# 事前固定2×2比較

| Arm | 校正状態 | 元selected t0で使う量 | 比較上の役割 |
|---|---|---|---|
| M00 | 元CISD | 固定trainingから二項fit f0(t0) | historical B0再現のbaseline |
| M10 | residual Krylov Ritz8 | 同じtrainingで二項fit f8(t0) | state-only介入 |
| M01 | 元CISD | local imag echo g0(t0) | local-only対照・安い競合 |
| M11 | 同じRitz8 | local imag echo g8(t0) | 組合せprimary |

両分子を最初から固定。M11 primary、M01 challenger。成功するまで分子を増やしたり、事後best armへ主方式を変更したりしない。QPE入力状態は元のまま。

原baselineは3点であり、「元5点」への一致は不成立。時刻・baseline定義の修正は未承認のため operational training_times=null として実行を閉じる。

原S0 baselineは `echo_imag_3point`。H01側の5点は元P03 analytic timeを参照する別実験で、元CISD proxy t_refの5点ではない。sentinel0.5やrobustness0.05をfit trainingへ混ぜたり、近傍H01時刻で0.4を補ったりしない。

signed bookkeeping:
- state in fit = f8-f0
- local in CISD = g0-f0
- state in local = g8-g0
- interaction = (g8-f8)-(g0-f0)

これは同じH/PF/timeの介入差。absolute error・saving・costの独立加算寄与や、分子母集団の因果効果に変換しない。budgetのlog interactionを示す場合も非線形変換の比較であると記す。

historical B0をimmutable referenceとして保持し、M00再現は別gate。科学計算を開始する前に、sourceに基づく許容差を閉じる。元fitの残差・sentinelのsign thresholdをbackend誤差boundへ勝手に読み替えない。
