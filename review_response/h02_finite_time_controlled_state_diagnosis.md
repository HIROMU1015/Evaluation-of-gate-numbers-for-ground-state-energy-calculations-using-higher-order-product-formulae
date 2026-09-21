# H02：N2/CO有限時間二項モデルに対する制御状態診断

## 目的

H01では、exact-ground echoは主4条件・2 PFで合格した一方、CISD echoは1%余裕付き凍結予算を全件満たしても、4つの予測指標には合格しなかった。本診断では、状態エネルギー誤差、分散、Hamiltonian残差、厳密基底状態との重なりだけで、近似状態を有限時間PFコスト校正へ使用できるかを判定できるか調べる。

これはH02の機構診断であり、新しい独立ホールドアウトではない。PF係数、モデル次数、分子、基底、目標精度、H01の直接truthは変更しない。

## 固定入力

- H01結果ブランチ：`gpu-h01-approximate-state-calibration-results`
- H01結果コミット：`568f00249abb5b89ae3e6bb39cb4af87ed8581bd`
- H01成果物：`artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`
- 固定仕様：`review_response/h02_finite_time_controlled_state_protocol.json`
- 固定仕様SHA-256：`46345041b0da6449ff33d87f242ba8dade6ebf330eb1994426b063674bbfe4d9`

対象はN2/COの平衡・1.5倍伸長4条件、PFは`current_m3`とYoshida 4次、モデルは5点の$t^4+t^6$ echo-phaseモデルだけとする。

## 制御状態

各HamiltonianでH01と同じexact ground、CISD、RHF determinantを再構築する。CISDとRHFからexact groundに直交する成分$|\chi\rangle$を作り、

$$
|\phi(q,\varphi)\rangle=
\sqrt{1-q}|\psi_0\rangle+e^{i\varphi}\sqrt{q}|\chi\rangle
$$

を用いる。$q$は状態エネルギー誤差が事前固定値$0.001,0.005,0.01,0.05$ Hartreeになるよう決め、$q\le0.25$を要求する。位相は$0,\pi/2,\pi,3\pi/2$とする。

同じ方向・エネルギー誤差の4状態は、エネルギー誤差、分散、残差ノルム、厳密基底状態重なりが同じになる。したがって、その4状態でecho係数、予測最適時刻、PF選択が変われば、これらのスカラー量だけでは適格性を判定できない直接の反例になる。

## 有限時間校正

H01のoracle由来$t_{\mathrm{ana}}$を固定して、

$$
t/t_{\mathrm{ana}}=0.1,0.2,0.3,0.4,0.5
$$

で

$$
\frac{1}{t}\arg\langle\phi|e^{-iHt}U_{\rm PF}(t)|\phi\rangle
$$

を計算し、$a_4t^4+a_6t^6$へ符号付き最小二乗fitする。H01のexact-ground echoを再現できることを先に確認する。

direct truthはH01の基底接続固有枝と直接格子最小コストを再利用する。制御状態ごとの新しいPF固有値計算は行わない。このため、評価対象は係数誤差、予測時刻・モデルコストの差、PF順位とH01直接コストに対する選択損失であり、H01の4基準を新たに合格したとは判定しない。

## 判定

次のいずれかを満たす位相4状態組を構成的反例とする。

1. 位相だけで選択PFが変わる。
2. 同一PFの予測最適時刻の相対幅が1%以上になる。
3. 同一PFの予測モデルコストの相対幅が1%以上になる。

スカラー量の組内広がりは絶対$10^{-10}$以下を要求する。再構築時のエネルギーメタデータは$10^{-9}$ Hartree、CISD/RHF診断量は絶対$10^{-6}$以内を要求し、さらにexact-ground echoの保存値との差を$10^{-9}$ Hartree以下とする。

## 適用範囲

- exact groundを状態構築に使うoracle診断であり、実用状態準備法ではない。
- H01の$t_{\mathrm{ana}}$と直接コストを使うため、end-to-endの安価な校正ではない。
- スカラー診断が不十分と分かっても、分散や重なりが無価値とは結論しない。
- 次段階は、必要な場合だけ誤差演算子に感度を持つ安価な適格性検査を設計する。H05、新PF探索、新分子へ自動的に進まない。
