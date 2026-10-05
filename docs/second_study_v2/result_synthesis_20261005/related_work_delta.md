# 第2研究の先行研究role mapと差分

本表は[承認済みレビュー](approved_gpt_review.md)のL1–L10を、今回の確認範囲付きで整理する。
RW01–RW10は本表専用IDで、旧protocolの文献IDを上書きしない。
差分欄は**本研究側の限定された比較・解釈**であり、外部方式を実装した性能比較ではない。
新規性の判断はGPT側に残す。網羅的な検索や世界初の証明ではない。

## 役割と確認範囲

| ID / review ID | 一次資料と役割 | 確認できたscope | 本研究の差分候補・主張しないもの |
|---|---|---|---|
| RW01 / L1 | Mehendale et al., Estimating Trotter Approximation Errors to Optimize Hamiltonian Partitioning for Lower Eigenvalue Errors. **core** | [arXiv v3本文](https://arxiv.org/html/2312.13282v3)のII、III、IV：近似CISDを用いる摂動推定、partitioningとT-gate資源順位。高い相関でも順位差がある。出版書誌は[出版社の記録](https://blogs.rsc.org/dd/2026/07/)で確認：Digital Discovery 4, 3540–3551 (2025), DOI 10.1039/D5DD00185D | 近似状態からのPF推定、精度と資源順位の乖離を新規としない。今回の差分候補は、固定有限時間の凍結予算、片側不足量、safe cheap対照からのoracle余地、実width/adoption/referenceの併記。出版版固有のN2記述は下記access区分 |
| RW02 / L2 | Simon–Love, Quantum Advantage in Resource Estimation. **core** | [arXiv v1本文](https://arxiv.org/html/2512.02131v1)のmain、Appendix B/D：量子phase-error測定をQPE資源最適化へ利用。Phase proxyの非上界性と非固有状態の扱いも議論 | 校正情報を将来QPEの資源判断へ使う発想は既存。本研究は量子測定法を提案せず、保守的boundだけでなくsafe fixed-cheapからの残余余地と実凍結判断を評価。同法の失敗・優劣を示したとは言わない |
| RW03 / L3 | Maxwell et al., Practical Estimation of Trotter Error for Hamiltonian Simulation. **core** | [arXiv v1 abstract/書誌](https://arxiv.org/abs/2606.30738v1)：asymptotic BCHによる実用誤差推定、compact表現、sampling | 高精度・低費用の推定器自体が新規とはしない。本研究は推定器の精度・規模・古典計算量で優るとは主張せず、有限時間budget投入後の信頼性を扱う。全文定理の比較は未実施 |
| RW04 / L4 | Yi–Crosson, Spectral Analysis of Product Formulas for Quantum Simulation. **core** | [arXiv v1 abstract/書誌](https://arxiv.org/abs/2102.12655v1)：spectral perturbation、初期状態overlapを伴うQPE固有値誤差 | Norm誤差と固有値誤差の違いは既存。本研究は一般spectral boundやgap certificateを導出していない |
| RW05 / L5 | Hejazi et al., Better product formulas for quantum phase estimation. **core** | [arXiv v1 abstract/書誌](https://arxiv.org/abs/2412.16811v1)：QPE energy誤差に特化したproduct formula解析、spectral/gapを伴うscope | 本研究はcurrent_m3を固定した校正・budget評価で、全次数の新PF定理やPF設計を主張しない |
| RW06 / L6 | Miller et al., phase2: Full-State Vector Simulation of Quantum Time Evolution at Scale. **core** | [arXiv v2 abstract/書誌](https://arxiv.org/abs/2504.17881v2)：2026改訂、boundと実測誤差の資源差を扱う | Boundと経験誤差の差一般を新規としない。本研究の比較はsafe cheap対照からのcost-free余地を含む。大規模simulator性能比較ではない |
| RW07 / L7 | Kronenberger–Erakovic–Reiher, Trotter error and orbital transformations in quantum phase estimation. **peripheral** | [arXiv v1 abstract/書誌](https://arxiv.org/abs/2602.18913v1)：orbital変換とTrotter誤差、単純descriptor/recipeの限界 | Descriptor限界一般を新規としない。本研究は軌道変換を介入させず、固定contractの具体的cheap stability反例を示す。出版版全文を今回確認したとはしない |
| RW08 / L8 | Pelofske–Eidenbenz, Effects of Trotter Error, Digitization Error, and Initial State Overlap on Tapered Quantum Phase Estimation for Minimum Eigenvalue Computation. **peripheral** | [arXiv v1 abstract/書誌](https://arxiv.org/abs/2609.06249v1)：Trotter、位相離散化、初期overlapの回路QPE評価 | 本研究のcontinuous rotation proxyを、離散query数や回路成功確率の評価と同一視しない。全文詳細は未確認 |
| RW09 / L9 | Epperly–Lin–Nakatsukasa, A theory of quantum subspace diagonalization. **method source（背景）** | [arXiv v2 abstract/書誌](https://arxiv.org/abs/2110.07492v2)：量子部分空間の一般化固有値問題のconditioningとtruncationに関する理論 | Krylov/部分空間法の背景。今回のunitary Arnoldi M1を同じ一般化問題と扱わず、同論文の定理をempirical width certificateへ無条件適用しない |
| RW10 / L10 | Rendon–Watkins–Wiebe, Improved Accuracy for Trotter Simulations Using Chebyshev Interpolation. **peripheral** | [arXiv v4 abstract/書誌](https://arxiv.org/abs/2212.14144v4)：interpolationを用いたzero-step誤差低減 | 外挿・補正は現在のuncorrected finite-time budgetと別task。実装しない。今回の小さいheadroomから補正付きtaskの可能性を否定しない |

## 出版版とarXivのaccessを混ぜない

Mehendaleの[出版版DOI](https://doi.org/10.1039/D5DD00185D)はrole mapへ追加した。
書誌は出版社由来の記録で確認できたが、この環境から出版本文へ直接アクセスする試行は403等で失敗した。
したがって、今回Codexが確認したtechnical evidenceはarXiv v3の明記した範囲である。

承認済みGPT原文は出版版本文とN2伸長の追加を確認したと報告している。
この報告は原文として保持するが、今回のCodex確認と統合しない。
出版版固有のN2分析やstate-quality detailを本稿の独立検証済み比較の根拠には使わない。
必要なら原稿最終確認時にGPT側で照合する。図表完成のための新規分子計算は不要である。

RW03–RW10はabstract/書誌のscope確認である。定理・numerical table・結論を全文検証したとは記録しない。
版・URL・確認区分は[文献registry](related_work_registry.json)に保存する。

## Contribution文の境界

採用する表現は、固定current_m3・native有限時刻・continuous budgetにおける
凍結実判断の失敗/安全事例、safe cheapからのoracle近接、固定M1の幅/採用とreference誤差を
接続した**限定された数値的信頼性評価**である。

slackの代数、Arnoldi、accuracyとutilityの乖離一般、freeze手順、誤差相殺一般は単独の新規性ではない。
外部方式への性能優位、厳密certificate、未知系のpolicy保証、世界初を追加しない。
旧baseline gateを再開せず、外部方式の実装も本作業では行わない。
