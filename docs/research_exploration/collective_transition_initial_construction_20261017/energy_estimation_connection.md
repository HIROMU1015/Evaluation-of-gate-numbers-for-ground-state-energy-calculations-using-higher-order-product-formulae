# 元Hamiltonianの絶対E0への接続と未取得条件

2026-10-18 JST（作業系列ID：20261017）。状態準備の一step進捗、低energy人口、ground overlap、絶対E0読出しを区別する。以下は紙上の接続条件であり、完成したE0算法・資源削減率ではない。

## 1. 今回成立した接続と限界

H*のC7はsource aからground bへ人口を移し、V7のground weight増加を与える。しかしa,b以外のdark成分は消えない。初期状態を任意とした収束保証はない。さらにH*は係数からE_bとW|34〉を直接計算/準備できる小classなので、この例で量子E0優位を唱えない。

一般H0+Rで旧groundを準備できたとして、係数から `‖R‖≤r_coe` を証明すればvariational principleから、その状態の元Hに対するexcessは高々 `2 r_coe` と抑えられる。この評価は未知E0を実行入力しないが、r_coeが小さくない限り所定精度へ接続しない。今回Rを捨てて成功としたわけではなく、この残差や必要な改良は未解決である。

## 2. 一般の準備チャネルに必要となる保証

H0=H−E0I≽0を証明の記号として用いる。実行時にE0を要求しない。例えば別途

\[
C^*(H_0)\preceq(1-\kappa)H_0+\nu I
\]

を合法な係数/構造から得られれば、`x_m=Tr(H0 C^m(ρ))` は

\[
x_m\le(1-\kappa)^m x_0+\nu\frac{1-(1-\kappa)^m}{\kappa}
\]

となる。ただし**今回の一般Hチャネルについてκ>0、ν小を示したわけではない**。固定rank-oneチャネルのdark stateがあるため、一律ν=0、κ>0は通常成立しない。別のcycle保証・入力class・hitting評価でもよく、この形を必須にしない。

energy期待値の下降はground overlap増加を一般には意味しない。excessがδ以下なら、任意ε>0に対して高energy weight `Tr[1_(E0+ε,∞)(H)ρ]≤δ/ε` というMarkovの帰結はあるが、exact ground overlapをgapなしに得ることはできない。

## 3. 読出しとの十分条件

準備状態σで `Tr[(H−E0I)σ]≤α ε/4` とする。HのenergyがE0+ε/2を越えるweightはα/2以下。Hと可換な理想energy-readout POVMが各固有energyを誤差ε/2、失敗α/2以下で読むなら、合計失敗α以下でE0±ε以内を出す。これは既知のMarkov/union boundの整理であり新規性ではない。

近似PFや一般POVMに「固有vectorごとの成功」を確認しただけで、全coherenceの保証を作らない。理想instrumentからの全入力作用誤差、unwrap/known support、scalar phase、synthesis、state/readoutの失敗予算を別に保持する。[A2差分handoff][E04]の固定powers条件を、今回のcoolerの成立証拠や多roundRPE保証として流用しない。

scalar cは状態のenergy flowにはTPにより影響しないが、絶対energy出力で復元する。元の一体項・相互作用・残余、DF等の近似差、sector選択が真のgroundを含む条件を台帳に残す。任意のspin/seniority部分問題の最小値を元電子Hの絶対E0としない。

## 4. 比較と費用

同じ初期accessに対して、通常の高confidence QPE/CDF等のenergy推定、既知system–bath、filtered jump、解析可能ならtargetの直接準備を比較する。冷却前overlap、mixing、制御H発展、spectral下界を一方だけ無料にしない。

量子gate、reset、depth、coherent time、古典前処理、memoryは別座標。量子gate座標gなら記号的に

\[
C_{\rm total}^{(g)}=C_{\rm coeff/setup}^{(g)}+
\sum_\ell N_\ell\left(C_{\rm prep,\ell}^{(g)}+
 m_\ell C_{\rm channel,\ell}^{(g)}+C_{\rm read,\ell}^{(g)}\right)
\]

を置き、古典coupler生成/証拠取得/償却を別に併記する。今回新しいgate数・改善率・分子benchmarkは算出していない。

## 5. 後続検証の提案（未承認・未実施）

第一の判断対象は、一般Hへ拡張する具体的な係数生成/複数jump/cycleが既知の小block法を越えるかであり、単に同じ4-modeを数値対角化することではない。もしGPT／ユーザーが数値検証を求めるなら、対象係数family、N/spin sector、初期state、θ、境界項、参照H/誤差norm、保存物、call数とSTOPを先に科学契約へ固定する。

目的候補はV10の境界残差と、提案された新しいcycleの元Hに対する進捗を区別すること。solver/行列/compileの実行は新しい明示承認後に限る。CPU/RAM/workerの人工上限やphase/総wall上限を新契約へ勝手に追加しない。今回はその契約を発行せず、実行も開始しない。

[E04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c6419859029824a4ee8c3dfd3c8126fe585ffbe2/docs/research_exploration/cross_repository_two_branch_delta_20261017/review_readiness_delta_handoff.md
