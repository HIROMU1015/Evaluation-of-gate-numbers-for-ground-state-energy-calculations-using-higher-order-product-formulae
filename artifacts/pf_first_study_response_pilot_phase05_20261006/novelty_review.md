# Novelty positioning — 2026-10-06一次文献レビュー

**generic response equation／Krylov／Ritz／eigenstate commutator-zeroを新規性として主張しない。**

検索対象はZV/ZB improved estimators、response/coupled perturbation、QSE、eigenstate observable correction、PF eigenvalue estimation、Trotter mitigation/extrapolation、approximate eigenstate perturbative correction。著者の一次論文・arXiv・出版社を参照した。レビューは候補の限定であり、類似手法の不在を証明するsystematic reviewではない。2026年の関連QPE論文も確認した。

## 方法ごとの重なり

| 先行研究 | 確認した内容／重なり | 今回区別しようとする点 |
|---|---|---|
| [Assaraf & Caffarel, Zero-variance principle (1999)](https://arxiv.org/abs/cond-mat/9911396) | improved observableで平均を保ちvarianceを改善する一般原理。targetを保つobservable変更そのものは既存 | stochastic variance削減を今回の達成claimにしない |
| [Assaraf & Caffarel, Zero-Variance Zero-Bias (2003), §II.1, Eqs.18–34](https://arxiv.org/html/physics/0310035v1) | trial stateとobservable-dependent auxiliary derivativeで近似状態biasも抑える。**最も近い一般原理** | fixed finite-time PF echoとrefit calibration、Ritz対照、signed magnitude riskへの特化 |
| [Baroni et al., DFPT review (2001)](https://arxiv.org/abs/cond-mat/0012092) | density-functional perturbationのresponse-property体系。response求解は既存の枠組み | 電子密度／force response一般ではなく、PF calibration observableを右辺に置く開発pilot |
| [Cancès et al., response stability (2023)](https://arxiv.org/abs/2210.04512) | Sternheimer linear systemsのconditioning/gauge、Hamiltonian applicationsの効率を扱う | 今回のcutoffはnumerical stabilizationだけで、gap-free accuracy certificateは出さない |
| [McClean et al., Hybrid Quantum-Classical Hierarchy (2017)](https://arxiv.org/abs/1603.05681) | subspaceによるeigenstates改善とclassical postprocessingのhierarchy | ordinary state improvementを既存対照として正面から比較する |
| [McClean et al., Decoding quantum errors with subspace expansions (2020)](https://www.nature.com/articles/s41467-020-14341-w) | subspace expansionを使うerror mitigationとobservable評価 | QSE自体を新規手法と呼ばず、同じKrylov informationのRitz比較を置く |
| [Yi & Crosson, Spectral Analysis of Product Formulas (2021/2022)](https://arxiv.org/abs/2102.12655) | eigenstate近傍のPF eigenvalue/eigenvector perturbation、QPEとoperator normの差を分析 | exact-state spectral error分析と、CISD finite-time proxy bias／refit errorを区別 |
| [Endo et al., Mitigating algorithmic errors (2019)](https://arxiv.org/abs/1808.03623) | 異なるTrotter step countsを使ったalgorithmic-error mitigation | PFを変える／step extrapolationするarmを追加せず、固定current_m3 observableのstate biasを補正 |
| [Carrera Vazquez et al., hardware-friendly MPFs (2023)](https://arxiv.org/abs/2207.11268) | PF expectationのclassical linear combinationsでTrotter error低減 | linear observable postprocessing一般は既存。今回はPF変更なしのstate-dependent responseとbudget-risk評価 |
| [Robertson et al., Tensor Network enhanced Dynamic MPFs (2025)](https://arxiv.org/abs/2407.17405) | tensor networkで係数を求め、quantum expectationを組み合わせる | classical assistanceの存在自体を新規とせず、response/Ritzの同一情報比較を主軸に限定 |
| [Kronenberger, Erakovic & Reiher, Trotter Error and Orbital Transformations in QPE (2026)](https://arxiv.org/abs/2602.18913)／[出版社本文](https://www.tandfonline.com/doi/full/10.1080/00268976.2026.2681062) | orbital basisがTrotter errorとcircuit depthへ与える効果、perturbative energy-error estimatesを議論 | orbital/PF再探索ではなく、保存Hと固定PFでstate-substitution calibration biasを扱う |

coupled-perturbed/Sternheimer類の線形response、摂動論によるeigenstate・property補正は上記一次研究と重なる。Handy–Schaeferの古典的energy derivatives論文も検索したが出版社本文を十分確認できず、この表のtechnical根拠はaccessibleな上記一次sourcesに限定した。

## ZVZBとの代数的対応：今回の推論

これは文献からの引用ではなく、本pilotの式からの導出である。`H(lambda)=H+lambda A`、normalized trial pathのderivativeを`psi'=-z`（z⊥psi）とすると、variational energy derivativeは

\[
\left.\frac{d\langle\psi(\lambda)|H+\lambda A|\psi(\lambda)\rangle}{d\lambda}\right|_0
=\langle A\rangle-2\operatorname{Re}\langle z|(H-E)\psi\rangle
=g_{resp}.
\]

従って今回のestimatorの一般形はvariational-response improved estimatorと直接対応する。ZVZB論文の§II.1はobservableをenergy derivativeへ結び付け、trial wavefunction derivativeを補助関数として用いるため、**新しいgeneric estimatorの発明というclaimは弱い**。full residual LSをsmall Krylov spaceで解く数値実装も、既知linear algebraの組合せである。

## 最も強い候補と必要evidence

候補は「固定finite-time PF校正でapproximate-state biasをobservable-specific responseで抑え、同じsubspace情報のRitz改善とstandalone/incremental actionを比較し、同じfitの再適用後のtotal error・PF magnitude underestimationまで評価する統合方法」。この組合せが既存研究から十分区別できるかは未確定で、pilot前にpositive claimを採用しない。

Level1にはstate sensitivityと補正後proxy/refitのmechanism evidenceが必要。Level2にはOutcome Aのresponse-specific accuracy／unsafe／cost tradeoffが必要。Bならordinary state improvementとしての価値に留まり、response固有新規性は弱い。Cならfit bottleneck、Dならbenefit未成立。どの結果でもexact-H echoのclassical access費を除外しない。

Level3はN2/CO等でselected time／frozen QPE budget／resource costの改善を別preregistrationで示す段階。Phase 0のheadroomはpotential上界・開発資料であり、pilotで回収できたgainでもnet resource improvementでもない。現在はscience結果がないためLevel1、Level2、Level3の達成claimはすべて未確立。

不確実性は、ZVZBとの近い代数対応、finite-time PF-specific先行研究の探索漏れ、Ritzが同等以上になり得る点、responseのadjoint追加費、small-space bias改善がfitへ伝わらない点、既知development座標のためtransfer/prospectiveを示せない点。GPT/userは統合対象の差分と必要evidenceを評価し、論文中心claimを判断する。
