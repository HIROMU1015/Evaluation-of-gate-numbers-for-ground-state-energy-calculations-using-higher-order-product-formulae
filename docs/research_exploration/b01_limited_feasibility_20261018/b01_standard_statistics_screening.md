# B-01：標準統計による費用差の照合

以下は既知の確率恒等式・concentrationを公表手順の量へ適用する紙上検討。新しい認証アルゴリズム・filter・逐次停止則は作成していない。公表上界を下界に読み替えず、検討したplug-in評価の限界をD1全般へ拡張しない。各評価は理想測定の条件付き式であり、実際の数値実行は0件。

## 1. 公表費用の構造

L01 Algorithm4の内部精度をepsilon_cとし、`tau=eta epsilon_c^2/160`。中央窓Iの半幅はPDF目視で`L=sigma sqrt(8 ln(sigma^-1 tau^-1))`と確認した（text抽出ではsqrtが欠落する）。端窓Jの質量をA_J、中央窓の質量をqとする。

既知の拒否標本化の確率は、任意窓Kについて

\[
q_{\rm acc}(K)=\frac{\sqrt{2\pi}\sigma}{|K|}
                    \int_Kg_\sigma(x)\,dx.
\]

粗い区間が正しくIがgroundを覆えばq>=c eta。したがって中央窓で一つのaccepted sampleを得る期待filter数は`Otilde(eta^-1)`。同じetaを通常のBernoulli濃度評価で無視しない。公表C.7の大きい項は、条件付き分散をO(eta epsilon_c^2)精度へ推定するaccepted samplesと、この拒否費用の積である。

## 2. 端窓のBernoulli：標準的な改善は既に入る

端窓のfilter成功indicatorをB_Jとすると`E B_J=kappa A_J`、`kappa=sqrt(2 pi) sigma/|J|=Otilde(1)`。検定境界付近ではA_J=O(tau)、したがって`Var(B_J)<=E B_J=O(kappa tau)`である。

同じ許容mass誤差tauを、全rangeだけのHoeffdingで見ると試行数は`O((kappa tau)^-2 log(delta^-1))`。Bernoulliのvariance-sensitiveな評価を境界の検定へ用いると、通常のChernoff/Bernstein型で`O((kappa tau)^-1 log(delta^-1))`となる。公表C.7の`Otilde(eta^-1 epsilon_c^-2)`はこの構造を既に使っている。高いA_Jでは受理条件を満たさないことを検定するので、全入力の小さいvarianceを仮定する必要はない。

ここでの改善を、中央窓の分散推定にも同じまま移植することはできない。二つの確率変数のvarianceが違う。

## 3. 中央窓：range・variance・mean取得を分ける

accepted sampleをY=X−e∈[−L,L]とする。既に固定したmean推定Mが窓内にあるとき、`W=(X-M)^2`は[0,4L²]。Mを得た標本とWのvalidation標本を独立にすれば、Mに条件付けて通常の集中評価を使える。

literalなAlgorithm4のmeanと二次momentの要求精度tauへ、rangeを保ったHoeffdingを適用すると、十分なaccepted sample数は

\[
m_{\rm mean}=O(L^2\tau^{-2}\log\delta^{-1}),\qquad
m_W=O(L^4\tau^{-2}\log\delta^{-1}).
\]

公表の正規化されたO(1) rangeをLのまま保持するだけでsigma依存を改善する余地がある。しかし、このままの期待filter費は

\[
\widetilde O\left[
 \eta^{-1}\epsilon_c^{-2}
 +(L^2+L^4)\eta^{-3}\epsilon_c^{-4}\right]
\]

という、各統計量を指定精度へ推定する標準的な**十分評価**で、目標のeta^-1 epsilon^-2依存を証明しない。公表認証の全証明を独立再認証した費用保証でもない。sigma・eta・epsilonの全領域でこの評価が最良だとも主張しない。Step7の強いmean精度を勝手に緩めて費用を落とし、元の決定保証だけを残すことはしていない。

## 4. Empirical Bernsteinとsample varianceを具体的に当てる

[L07：Maurer–Pontil](https://arxiv.org/pdf/0907.3740v1) Theorem4/10のbounded-variable評価を使える。Wのmeanを許容誤差tauで推定する通常のBernstein型の十分数は、定数・logを除き

\[
m=O\left[
\left(\frac{\operatorname{Var}W}{\tau^2}
       +\frac{4L^2}{\tau}\right)\log\delta^{-1}
\right].
\]

未知varianceはempirical版のconfidenceで扱い、未知の真のvarianceを設定入力にしない。単一Gaussianに近いcompleteness側でも、既知恒等式`Var((X-E X)^2)=2 sigma^4`がある。有限窓のtail誤差を別に抑えた場合も、Gaussian背景の二次momentの揺らぎを0とはできない。このplug-in評価の項は`Otilde(sigma^4 eta^-2 epsilon_c^-4)`。既知のsigma²をWの平均から差し引いても`Var(W-sigma²)=Var(W)`である。

通常のsample varianceへTheorem10を適用する場合も、range幅R=2L、v=Var(X|I)として`|sqrt(vhat)-sqrt(v)|=O(R sqrt(log(delta^-1)/m))`。ゆえにvをtau精度にする十分条件は

\[
m=O\left[\left(\frac{vR^2}{\tau^2}
                       +\frac{R^2}{\tau}\right)\log\delta^{-1}\right].
\]

v≈sigma²なら先頭項はOtilde(sigma⁴ eta^-2 epsilon_c^-4)。これは分散functional単体への適用であり、Algorithm4のmean/output条件を変更した完全認証法の保証ではない。公表thresholdへの誤差配分と受理余裕まで満たす必要がある。いずれもaccepted sample取得のfilter費は残る。

したがって「empirical Bernsteinを使えば目標へ到達」とは示せない。同時に、この二次moment評価のepsilon^-4が、あらゆる認証法に必要という下界も得ていない。

## 5. D1でmomentを評価する場合の正規化費

[access照合](b01_access_and_theorem_audit.md)のa0,a1,a2を使う。q=a0>=c etaであり、各絶対誤差をr0,r1,r2、r0<=q/2とする。通常の比率の誤差伝播は

\[
|\widehat\mu-\mu|=O((r_1+Lr_0)/q),\qquad
|\widehat v-v|=O((r_2+Lr_1+L^2r_0)/q)
\]

となる（中心はeへ移し、meanが窓内である範囲）。例えばvariance誤差tauを保証するには、`r2+L r1+L² r0=O(q tau)`という十分条件が必要で、q tauは最悪O(eta² epsilon_c²)のscaleになる。meanにも別の必要精度がある。

既知L04 Algorithm1のFourier L1係数量をK_kとすると、各線形functionalをr_kで評価するrange型の十分費用は`O(K_k² r_k^-2 log(delta_k^-1))`。Fourier打切りbiasもr_kへ含める。同じ基礎記録の相関が比率誤差を改善する可能性を否定していないが、それを上式から無料で仮定しない。この素朴な移植ではetaに関する追加の不利な依存が生じ得る。

L01 CorollaryC.4のprinted statementは未正規化積分と未正規化混合momentを比較している。これを条件付き量の誤差として使う際にqを落としてはならない。そのままC.5へ移せる精度・定数・eta依存を、本調査で独立再認証してはいない。訂正後の定理や新しい費用式を宣言せず、この接続も未確認として残す。これは原論文全体の誤りやD1の不可能性の認定ではない。

## 6. 選択・停止・validation

[L08：Howardほか](https://arxiv.org/pdf/1810.08240v9) Theorem4はbounded observationsに対する時間一様のempirical Bernstein保証を与える。適用対象は固定窓のB_JやW、あるいは同じfunctionalに対して条件付き不偏性を保つ測定推定量。時刻・軸を適応的に選ぶ場合は、その条件付き期待値とrangeを確認する。

窓を同じ標本で選び直すと、固定functionalのconfidence sequenceだけでは選択を覆わない。fresh validationか、選んだclass全体の同時保証・その費用が必要。stage kに`delta_k=delta_test/[k(k+1)]`等を割り当てればunion boundで全stageを覆えるが、log(k)の費用や準備回数が増え、η・epsilonの主要powerを消す根拠にはならない。逐次検定を新しく構成・実装したわけではない。

拒否samplingの期待数と高確率の総数も区別する。実行上限を設ける場合には、その打切りによるREJECT/失敗確率を別に加える必要がある。filter近似、simulation、coarseの誤りも別eventとし、confidenceだけでbiasは除去できない。

## 7. このscreeningの帰結

通常の統計で改善できる箇所は具体的にある。端窓のrare-event評価は公表法が既に使用し、range保持はsigma依存を鋭くし得る。独立validation・時間一様confidenceは選択/停止の誤受理を管理する。一方、これらだけでN_targetまで閉じる証拠は得られなかった。

残る障害は、固定variance判定のO(eta epsilon²)精度、Gaussian背景の四次moment、accepted sample取得、D1移植時の正規化とFourier係数費である。これらは検討した手順・評価に限定した障害であり、新しい量子機構が必要・可能であるとは結論しない。
