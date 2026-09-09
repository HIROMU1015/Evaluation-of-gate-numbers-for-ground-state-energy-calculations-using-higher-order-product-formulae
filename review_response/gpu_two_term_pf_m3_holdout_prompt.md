# GPUサーバー側Codexへの依頼：m=3二項モデルPFの未使用検証

ローカルで、4次PFの符号付き直接誤差を

$$
\delta E(t)=a_4t^4+a_6t^6
$$

で表し、有限時間コストを予測しやすくする係数探索を行った。局所再探索では、次の $m=3$ 候補がLiH、BeH2、H2Oと3基底の9条件で最良だった。

$$
(w_0,w_1,w_2,w_3)
=(-0.5479746372736223,\ 0.4130665734843169,\
0.1864679228988850,\ 0.1744528222536092).
$$

この係数はここで固定し、NH3とH6/H7を未使用データとして検証してほしい。ホールドアウト結果を見て係数を再調整しないこと。

関連ファイルは次のとおり。

- `artifacts/two_term_pf_m3_refinement_local_20260909/report.md`
- `review_response/refine_two_term_pf_m3_local.py`
- `review_response/analyze_two_term_pf_probe.py`
- `review_response/validate_two_term_pf_optima_local.py`
- 既存のGPU密行列・保存則セクター直接計算コード

## 検証対象

- H6、H7。
- 凍結内殻active-space NH3のSTO-3G、6-31G、cc-pVDZ。
- 比較基準として現行m=3も同じ条件で計算する。計算済みでHamiltonian、grouping、係数、時刻が完全に一致する点は再利用してよい。

## 計算内容

1. 各系で既存の共通短時間フィット規則を使い、一項係数 $\alpha$ と $t_{\mathrm{ana}}$ を求める。
2. $0.1,0.2,0.3t_{\mathrm{ana}}$ の符号付き $e_{\mathrm{direct}}$ から $a_4t^4+a_6t^6$ を決める。
3. 二項モデルが予測する最適時刻 $t_*$ を求める。
4. 少なくとも $0.9t_*,t_*,1.1t_*$ を直接計算する。既存点の再利用または少数の追加点で可能なら、直接コスト最小の位置も局所的に細分化する。
5. 基底状態につながるPF固有枝、固有対残差、基底状態重なりを保存する。重なり位相だけを $e_{\mathrm{direct}}$ の代用にしない。

直接対角化できる条件では通常の直接対角化を基準にする。実行方式はGPUに限定せず、サーバーのCPU密行列、GPU密行列、独立条件のCPU並列のうち実測で速いものを使ってよい。CPU並列ではOpenBLASのスレッド数が小さいため、1ジョブのスレッド数を増やすより、独立した系・PFをプロセス並列し、必要ならNUMAを意識して配置する。

## 報告してほしい量

各条件について、少なくとも次を同じ分母で示す。

$$
\eta_*=\frac{|C_{\mathrm{2term}}(t_*)-C_{\mathrm{direct}}(t_*)|}
{C_{\mathrm{direct}}(t_*)},
$$

$$
\eta_{\min}=\frac{C_{\mathrm{direct}}(t_*)}
{C_{\mathrm{direct}}(t_{\mathrm{direct},*})}-1,
\qquad
\eta_t=\left|\frac{t_*}{t_{\mathrm{direct},*}}-1\right|.
$$

ここで $t_{\mathrm{direct},*}$ は計算した局所格子内の直接コスト最小時刻とし、連続最適値と断定しない。二項モデルの未使用時刻における最大残差 $|\delta E_{\mathrm{direct}}-\delta E_{\mathrm{2term}}|/\epsilon_E$ も示す。

候補の主目的は最低コストだけではなく、異なるHamiltonianに対するコスト解析の再現性である。現行m=3とのコスト比と予測誤差の両方を分けて報告する。

最初に短い代表条件でCPU/GPUの所要時間を比較し、長い全条件を開始する前に実行方式を決めてよい。結果、コード、JSON、簡潔な報告書を別ブランチへ保存し、mainへはまだ統合しないこと。
