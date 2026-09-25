# 第一研究 S3：HF成功・破綻対への限定接続

**確定日：2026年9月25日**  
**状態：`complete_retrospective_synthesis`**  
**性格：既存結果だけを用いた回顧的証拠統合（独立検証ではない）**

## 1. 結論

S3の終了条件は満たされた。中核主張は次の一文である。

> 固定H4・二準位系では近似状態の置換が校正誤差の主成分になりやすい一方、HF分子の平衡・伸長対におけるexact-state低次モデルの成否は、先頭係数の対角相殺、相対的な高次項、物理gapが同時に変わる条件付き現象であり、状態の通常のスカラー量またはPF位相gapだけから有限時間PF資源効率を一意に予測することはできない。

適用範囲は、固定済みのH4/二準位development cases、STO-3GのHF分子
equilibrium/stretch150対、および既存6条件のdevelopment scoringに限る。未使用分子、
別基底、別PF、一般の近似状態生成法への独立transferは検証していない。

この統合で新しいHamiltonian、PF固有値、direct truth、fit、閾値調整は一切追加して
いない。したがってHF bridgeはS2の独立な追試ではなく、異なる既存診断を接続して
説明の適用範囲を限定するための外部文脈である。

## 2. 固定した入力

| 入力 | commit | 用途 |
| --- | --- | --- |
| 第一研究統合結果 | `9de82d37ca0cf61577df311b386d57232d360e0b` | 三分解、凍結資源、S0 exact-time採点 |
| H01近似状態校正 | `568f00249abb5b89ae3e6bb39cb4af87ed8581bd` | approximate-state transferと安全性の分離 |
| HF mechanism bridge retry-1 | `6eb1aa02f1d28904741b2cee4f70347e1203198f` | Yoshida4のHF平衡成功・伸長破綻対 |

GitHub上の正本は、[第一研究統合結果](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9de82d37ca0cf61577df311b386d57232d360e0b/PF_first_study_results_20260925.md)、
[H01 report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/568f00249abb5b89ae3e6bb39cb4af87ed8581bd/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/aggregate/report.md)、
[HF mechanism bridge report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md)から直接確認できる。

各source pathとSHA-256は
[`source_manifest.json`](artifacts/pf_first_study_s3_hf_connection_20260925/source_manifest.json)
に固定した。数値を抽出した判断表は
[`evidence_matrix.csv`](artifacts/pf_first_study_s3_hf_connection_20260925/evidence_matrix.csv)
に保存した。

## 3. 何が接続できるか

### 3.1 状態置換は有限時間校正の主要な誤差軸である

第一研究の固定128 caseでは、79 caseが`E_state_hartree`支配、49 caseがmixedで、
`E_fit`または`E_proxy`が単独支配したcaseはなかった。H4だけでは49/56 caseが状態
置換誤差支配であり、CISD/RHFは4 PFすべてで状態置換誤差支配だった。

H01でも、N2/CO主4条件に対するCISDは凍結した全条件transfer規則には不合格だった
一方、両PFで1.01予算を4/4満たした。従って、近似状態によるproxy/modelの不一致と
最終的な精度予算の安全性は同じ量ではない。S0もこの分離を補強し、1.01予算は6/6
条件で安全だった一方、exact-time joint regretは2.13%から114.15%まで広がった。

### 3.2 HF伸長の破綻は「状態混合が単純に増えた」ためではない

HF bridgeは、既存のYoshida4＋二項モデル判定を変更せず、equilibriumをpass、
stretch150をfailとして比較した。stretch/equilibriumで観測された主要な変化は次で
ある。

| 指標 | equilibrium | stretch150 | 読み方 |
| --- | ---: | ---: | --- |
| `|a4| / ||D4||` | `2.4274e-3` | `7.0242e-4` | 伸長側で対角期待値の相対相殺が強い |
| `||Q D4|0>|| / ||D4||` | `1.3655e-1` | `6.9153e-2` | 正規化couplingは増えていない |
| a8 mixing fraction | `0.32969` | `0.26088` | 伸長側で低下 |
| `|t8/(t4+t6)|` at `t_ana` | `0.007672` | `0.037141` | 相対高次寄与は約4.84倍 |
| physical gap [Ha] | `0.562324` | `0.175191` | 約0.312倍 |
| minimum phase compression | `1.0` | `1.0` | PF位相gap圧縮の証拠なし |

小さい`a4`によりstretch150の`t_ana`は1.384倍になり、その時刻では高次項の相対
寄与が増えた。ただし、physical gap、対角相殺、coupling、高次項は同時に変化して
いるため、一つを一意原因とは呼ばない。特にD4 mixing fractionは伸長側で増えて
おらず、PF位相gap圧縮も観測されていない。

### 3.3 二つの軸は結合し得るが、同一の診断ではない

第一研究の`E_state`は、近似状態proxyとexact-state proxyの差である。HF bridgeの
主比較はexact-state側の有効Hamiltonian係数と枝診断であり、HF分子対について
`E_state`支配を直接再測定したものではない。従って次の整理が必要である。

- 状態置換軸：どの近似状態をproxyへ入れたかによるバイアス。
- 有限時間演算子軸：同じ状態でも、対角相殺、高次項、gap、利用時刻により低次モデル
  の妥当性が変わる効果。
- 資源軸：精度を満たしても、選択時刻と予算がoracle gridより大きくなり得る効果。

これらは相互作用し得るが、今回の既存データだけから積や因果順序は同定していない。

## 4. 移る機構／移らない機構

| 判定 | 内容 | 根拠 |
| --- | --- | --- |
| 移る | 近似状態に対するproxy感度は、fit精度とは別の主要誤差軸である | H4 49/56、全体79/128、H01 transfer不合格 |
| 移る | 精度上の安全性と資源効率は分けて採点すべき | H4 regret 64.51%、S0 HF regret 100%超でも1.01は安全 |
| 条件付き | 先頭係数の相殺で利用時刻が長くなると、相対高次項が重要になり得る | HF Yoshida4対で`|t8/(t4+t6)|`が約4.84倍 |
| 移らない | 伸長破綻を「D4状態混合の増大」だけで説明する | mixing fractionと正規化couplingはいずれも低下 |
| 移らない | 伸長破綻をPF位相gap圧縮だけで説明する | minimum phase compressionは両条件で1.0 |
| 未確立 | Yoshida4のpass/fail機構からcurrent_m3のregret順位を予測する | PF・モデル・評価目的が異なり、S0ではHF両条件とも100%超regret |

## 5. 反証条件

次のいずれかが事前固定した独立評価で再現されれば、中核主張またはS4選択を見直す。

1. 状態階層を改善してもoperator-sensitive proxyが収束しない、または収束しても
   direct誤差・regretが改善しない。
2. 同じ状態を固定した比較で`E_fit`または`E_proxy`が一貫して支配し、`E_state`が
   少数となる。
3. 対角相殺と相対高次項を制御しても低次モデル成否が変わらず、代わりにbranch/位相
   gapが成否を説明する。
4. 未使用分子で1%安全余裕が破れ、状態感度診断がその危険を事前に識別できない。

## 6. S4へ進める一方式

S4の第一候補は、**同じ状態生成法の二つの収束度で、PF固有のsigned echo proxyの差を
測るoperator-sensitive state-convergence diagnosticと、危険時の事前固定fallbackを
一体化した方式**とする。

この方式を選ぶ理由は、通常のエネルギー誤差・分散・重なりだけでは誤差演算子に
対する方向感度を捉え切れず、同じ近似状態の同じproxyへ時刻点を追加しても
`E_state`は原理的に除去できないためである。S4では、診断閾値、fallback、追加古典
費用、比較baseline、ablationをtruthを見る前に新protocolで固定する。

S4の最低比較は次とする。

- 現在の二PF selector。
- `current_m3`固定とYoshida4固定（同じ校正・余裕）。
- 同じ追加古典費用を与えた単純な追加時刻点。
- diagnosticのみ、fallbackのみ、両者の組合せ。

S3ではこの方式を実装・採点していない。S4でdevelopment上の実益が得られた場合だけ
S5の未使用active-space分子群へ一度進み、得られなければ機構研究を中核成果として
閉じる。

## 7. S3停止判断

- 既存結果だけで条件付き関係を記述した。
- 中核主張、適用範囲、反証条件を明記した。
- 新direct truth点、新Hamiltonian、新fit、post-hoc閾値変更は0である。
- 次段候補を一方式へ限定したが、実装・性能主張は行っていない。

従ってS3は完了とする。次に計算を行う場合は、S4専用の新しい事前固定protocolを
作成してから開始する。

