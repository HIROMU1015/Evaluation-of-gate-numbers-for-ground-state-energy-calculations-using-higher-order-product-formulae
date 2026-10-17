# T0：絶対E0までの総費用・誤差分解

[共通task](t0_task_definition.md) の下での会計式。新しい資源値の計算ではない。
SOURCE IDは [registry](source_registry.json)、方法別の根拠は [baseline cards](t0_baseline_comparison.md)。

## 1. 呼出しを展開した会計

測定round・時刻・乱択方法をまとめて \(j\)、その繰返しを \(N_j\) と書くと、同一gate種について

\[
 G_{\rm total}=G_{\rm setup}+\sum_jN_j\{P_j+C_{\rm ctrl\!\mathchar`-sim}(t_j,\delta_j)
 +C_{{\rm aux},j}+C_{{\rm meas},j}\}.
\]

setupと古典前後処理は別費用軸でも残す。stateを維持する逐次QPEでは、再準備は実際に破棄・再試行する単位で数える。
独立Hadamard testでは通常shotごとに準備する。適応的手順・rejection samplingは期待値とtail／最大費用を区別する。
最大depthは各回路内の準備・controlled evolution・補助操作を足した最大値であり、総evolution timeではない。

| 部分 | 必要な入力／価格 | 既存資料から欠ける場合 |
| --- | --- | --- |
| Hamiltonian前処理 | integral精度、factorization、残余、fragment・sampling table生成 | setup cost unknownとする |
| simulation | 分割、PF word、step数、負時間、rotation精度、control、processor | 一回あたりの指数個数だけで総gateとしない |
| protocol | 全時刻、各精度・shots、branch復元、confidence allocation | 単時刻bias／visibilityをE0誤差に読み替えない |
| preparation | circuit、sector漏れ、overlap下限の根拠、再準備・uncompute | 保存exact vectorの価格を運用側へ流用しない |
| synthesis／FT | gate set、誤差、routing、magic state等 | RZ/CXとT/Toffoliを数値変換しない |

PRの保存式 \(F_m+N_m(C_m+P)\) はこの会計の単一task版である（PRM）。
共通のper-shot準備費 \(P\) も、\(N_m\) が違えば差し引きでは消えない。
shot数だけの優位と総費用の優位は異なる。

## 2. PFの費用と精度の接点

単純なp次PFに全入力で使える局所norm上界
\(\|S_p(s)-e^{-isH}\|\le K_p|s|^{p+1}\)
があれば、unitary性とtelescopingから、r stepの十分条件は
\(K_p|t|^{p+1}/r^p\le\delta_U\) となる。
\(K_p\) は同じ分割・sector・係数に対して合法に得た上界である必要がある。nested-commutator評価は既知（L01）。
これは十分上界であって最小step数・実測値ではない。

1 stepのrotation数や指数個数 \(n_{\exp}\) に、synthesis・control・orbital変換の実価格を掛ける。
processed PFでは \(P K^rP^{-1}\) の両端を払い、各stepにprocessorを掛け直さない（E13）。
有限角丸め・負時間・分解誤差をこの式から除外しない。

本repoのE12が評価する

\[
 C(t)=\frac{\beta n_{\exp}}{t\{\epsilon_E-e(t)\}},\qquad 0\le e(t)<\epsilon_E,
\]

は既存の連続rotation型QPE費用モデルである。power law \(e(t)=a t^p\) での最適時刻も実装済みだが、
今回は実行していない。\(\beta\)、誤差曲線、grid、state・branchの正当性が必要であり、
準備・confidence・有限bit synthesisを自動で含む公式ではない。
第二研究の「安全性」はこの既存proxy内の固定結果であり、新しい回路認証ではない（E11）。

## 3. 絶対energyと失敗確率

同じsector上での保証を用い、十分な加算会計の例を

\[
 \epsilon_{\rm coeff}+\epsilon_{\rm model}+\epsilon_{\rm energy\!\mathchar`-protocol}
 \le\epsilon_E,
 \qquad
 \alpha_{\rm information}+\alpha_{\rm prep}+\alpha_{\rm sim}
 +\alpha_{\rm statistical}+\alpha_{\rm branch}\le\alpha
\]

と書ける。これらは新しい固定budgetではなく会計欄。区分の重複や独立性を仮定しない。
\(\|H_{\rm impl}-H_{\rm orig}\|_{\mathcal S}\le\epsilon_{\rm model}\) なら最小固有値差をその値で抑える既知の十分条件が使える。
DF残余のenergy評価だけでnorm保証を代替しない。

PF誤差をenergyへの系統biasとして直接証明した場合と、全回路の分布摂動として成功率へ計上する場合は分ける。
後者なら、各回路のoperator／channel誤差を適切なtrace-distanceまたはdiamond-distanceへ変換した上で、
全使用回数のhybrid bound等で合計する。根拠なく \(\delta_U/t=\epsilon_E\) と置かない。
係数誤差・synthesisを含む同じ効果を両経路で二重計上しない。

\(H=cI+H'\) のcontrolled evolutionではcontrol=1枝の \(e^{-ict}\) を保持する。
既知のshift／rescaleはenergyと許容誤差を元の単位へ戻す。全系のglobal phaseだから無視できる、とはしない。
windowは係数norm等の安全な上界から作れるが、その幅と前処理費は残る。

## 4. 信号・統計・phaseの区別

Hadamard信号の加法誤差 \(\delta_z\) はenergy誤差ではない。位相へ移すには非零の信号半径が必要で、
有限時刻からfrequencyを識別するにはoverlap、window、複数時刻の推定保証を要する。
RMS \(\epsilon\) の定理（L04）と成功率 \(1-\alpha\) の定理（L02／L08）は直接等置しない。
必要なら既知の確率不等式・反復集約でconfidenceを変換し、その追加費を残す。

符号付きsamplingの一般形は、既知weights \(w_j\) に対して \(S=\sum_j|w_j|\) とし、
確率 \(|w_j|/S\) で選んだ回路の±1測定値に \(S\operatorname{sgn}(w_j)\) を掛けるもの。
信号精度 \(\delta_z\) の十分shotsは \(O(S^2\delta_z^{-2}\log(1/\alpha_z))\)。
これは既知のquasiprobability会計で、新しいsampling則の提案ではない。
PRのnormalizerと外挿のweight和は別の起源だが、どちらも振幅低下を無料で取り除けない。

## 5. 何が支配するか

固定instanceの \(\eta,P_j,N_j,C_j\)、許容誤差、native gate契約がないため、単一の実測支配項は特定できない。
条件付きには、(i) PF精度・時刻に伴うstep増加、(ii) 小overlap／小visibilityや符号weightによるshots、
(iii) 各shotの再準備、(iv) empiricalな誤差係数をrigorousな値へ置換する費用が制約となる。

強い既知法もこの分離を行っている。特にL08 Theorem 48はsimulationをCDFへ接続する定理まで含む。
「その接続が存在しない」を新gapにはしない。一方、同定理に未価格の準備・overlap取得を加えて
本repoの全taskを解いたという証拠もない。未取得の費用値を埋めず、instanceを越えた再順位付けをしない。
