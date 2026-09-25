# M01 resource-metric sensitivity

Status: **complete_with_findings**

D03で固定された二項モデル選択時刻と直接誤差を再利用し、新しいPF固有値点を計算せず、回路資源の単位だけを比較した。

## 指標別最良PF

| condition | target | rotations | RZ layers | T-count | T-depth | best change | pairwise inversions |
|---|---|---|---|---|---|---:|---:|
| HF_full_stretch150_sto3g | CA_div_100 | current_m3 | current_m3 | current_m3 | current_m3 | False | 0 |
| N2_active_eq_sto3g | CA_div_10 | current_m3 | current_m3 | current_m3 | current_m3 | False | 0 |
| N2_active_eq_sto3g | CA_div_100 | current_m3 | current_m3 | current_m3 | current_m3 | False | 0 |
| N2_active_stretch150_sto3g | CA_div_10 | current_m3 | current_m3 | current_m3 | current_m3 | False | 0 |
| N2_active_stretch150_sto3g | CA_div_100 | current_m3 | current_m3 | current_m3 | current_m3 | False | 0 |

## D03固定モデル合格PFに限定した最良PF

この表は資源量だけでなく、D03の固定モデル判定に合格したPFだけを採用候補として比較する。

| condition | target | eligible PFs | rotations | RZ layers | T-count | T-depth |
|---|---|---|---|---|---|---|
| HF_full_stretch150_sto3g | CA_div_100 | yoshida6_m3 | yoshida6_m3 | yoshida6_m3 | yoshida6_m3 | yoshida6_m3 |
| N2_active_eq_sto3g | CA_div_10 | current_m3;yoshida4;yoshida6_m3 | current_m3 | current_m3 | current_m3 | current_m3 |
| N2_active_eq_sto3g | CA_div_100 | current_m3;yoshida4;yoshida6_m3 | current_m3 | current_m3 | current_m3 | current_m3 |
| N2_active_stretch150_sto3g | CA_div_10 | current_m3;yoshida4;yoshida6_m3 | current_m3 | current_m3 | current_m3 | current_m3 |
| N2_active_stretch150_sto3g | CA_div_100 | current_m3;yoshida4;yoshida6_m3 | current_m3 | current_m3 | current_m3 | current_m3 |

## 選択時刻での回路資源内訳

| condition | target | PF | direct pass | rotations/PF | compiled RZ/PF | RZ layers/PF | T/RZ |
|---|---|---|---:|---:|---:|---:|---:|
| N2_active_eq_sto3g | CA_div_10 | current_m3 | True | 19176 | 18896 | 4522 | 144 |
| N2_active_eq_sto3g | CA_div_10 | yoshida4 | True | 8296 | 8176 | 1950 | 153 |
| N2_active_eq_sto3g | CA_div_10 | yoshida6_m3 | True | 19176 | 18896 | 4522 | 148 |
| N2_active_eq_sto3g | CA_div_100 | current_m3 | True | 19176 | 18896 | 4522 | 169 |
| N2_active_eq_sto3g | CA_div_100 | yoshida4 | True | 8296 | 8176 | 1950 | 178 |
| N2_active_eq_sto3g | CA_div_100 | yoshida6_m3 | True | 19176 | 18896 | 4522 | 172 |
| N2_active_stretch150_sto3g | CA_div_10 | current_m3 | True | 18952 | 18672 | 4438 | 139 |
| N2_active_stretch150_sto3g | CA_div_10 | yoshida4 | True | 8200 | 8080 | 1914 | 148 |
| N2_active_stretch150_sto3g | CA_div_10 | yoshida6_m3 | True | 18952 | 18672 | 4438 | 144 |
| N2_active_stretch150_sto3g | CA_div_100 | current_m3 | True | 18952 | 18672 | 4438 | 164 |
| N2_active_stretch150_sto3g | CA_div_100 | yoshida4 | True | 8200 | 8080 | 1914 | 173 |
| N2_active_stretch150_sto3g | CA_div_100 | yoshida6_m3 | True | 18952 | 18672 | 4438 | 167 |
| HF_full_stretch150_sto3g | CA_div_100 | current_m3 | False | 9108 | 9108 | 2661 | 171 |
| HF_full_stretch150_sto3g | CA_div_100 | yoshida4 | False | 3948 | 3948 | 1149 | 179 |
| HF_full_stretch150_sto3g | CA_div_100 | yoshida6_m3 | True | 9108 | 9108 | 2661 | 179 |

## 主結論

- N2主判定4組のうち、最良PFが資源指標で変わった組は `0`。
- N2主判定におけるpairwise順位反転は合計 `0`。
- N2主判定では `current_m3` が4資源指標すべてで最良だった。
- Pauli rotations、compiled RZ、RZ layerは別の単位として保存した。
- T-count/T-depthは1%の合成エネルギー予算と `ceil(3 log2(1/epsilon_rot))` を使う固定proxyである。
- controlled-U、状態準備、QFT、routing、magic-state factoryは含まないため、実行時間とは呼ばない。
- HF stretchは破綻例の診断であり、N2の主判定と混ぜない。
- HF stretchではraw資源最小の `current_m3` はD03固定モデルに不合格であり、採用可能PF限定では `yoshida6_m3` のみが残る。
