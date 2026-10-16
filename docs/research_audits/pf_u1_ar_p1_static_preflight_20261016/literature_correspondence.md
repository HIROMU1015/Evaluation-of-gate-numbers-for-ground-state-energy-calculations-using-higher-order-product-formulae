# U1-AR P1-S1：一次文献対応（2026-10-16）

今回の範囲は一次資料の読解と既存主張の対応整理。ARの実証、命題の新しい証明・反例、P1のGO、新研究の採択は行わない。Claude `レビューoutter(5).md` はアクセス可能な検索範囲で取得できなかった。以下のA/B/M/R/Nおよび§5.6への言及はユーザー指示に記された内容に限り、Claude原文との逐語照合・詳細レビューではない。

9本すべてPDF本文を取得した。以下は実際に読んだ対象箇所であり、全文読了の表示ではない。版はPDF先頭のarXiv表示を確認し、PDFのbyte/SHA-256と抽出テキストのSHA-256を `provenance.json` に記録した。本文・図の必要箇所を確認し、要旨だけの文献はない。PDFや抽出全文は公開しない。

## 取得・読了範囲と入力

| ID・一次資料（実取得版） | 本文で確認した範囲 | モデル／PF・分子基底エネルギーとの関係 |
|---|---|---|
| [R1 Rendon–Watkins–Wiebe, 2212.14144v4](https://arxiv.org/pdf/2212.14144v4) | §2.1、Lemma 1・Eq. (2.11)、§3.2.1のLemma 10–12、Appendix DのD.1–D.6の該当仮定・証明・query cost | 有限和Hamiltonian、Suzuki再帰の偶数次PF、補間・外挿によるエネルギー推定。一般的な固有値/QPEとの直接の接点がある。今回の最適化4次PFへの定数の移植は未確認。 |
| [R2 Moan–Niesen, math/0609198v2](https://arxiv.org/pdf/math/0609198v2) | §§1,3,4、Theorem 2・3、§5 Examples 1–3、§6 | 実可積分行列A(t)による線形ODEのMagnus級数。分子・対象固有枝を扱う定理ではない。 |
| [R3 Sieberer et al., 1812.05876v2](https://arxiv.org/pdf/1812.05876v2) | 本文kicked-topのFloquet定義、Fig. 2(b)周辺の固有位相・回避交差・混合、Floquet–Magnus展開の解釈 | 集団spin/kicked top、主に一次Lie分割、対称分割との比較。分子QPEへの直接の検証ではない。版指定なしの依頼に対し取得PDFはv2。 |
| [R4 Heyl–Hauke–Zoller, 1806.11123v4](https://arxiv.org/pdf/1806.11123v4) | Results「Trotter sequences as Floquet systems」Eqs. (3),(4)、Ising benchmark、IPR/OTOC・局所誤差、Methods Eq. (13) | Ising chain等の一次分割、局所観測量とchaos/localization。化学基底エネルギー/QPEの閾値の定理ではない。 |
| [R5 Kargi et al., 2110.11113v6](https://arxiv.org/pdf/2110.11113v6) | §3モデル・分割、§4.1、特に§4.1.3「Stable Regions」 | A2A Ising、Heisenberg、Rabi–Dickeの実装可能な分割。非分子モデルの有限step数値調査と特別な共鳴の解析。 |
| [R6 Bay-Smidt et al., 2605.00745v2](https://arxiv.org/pdf/2605.00745v2) | §V.1（PDFではV A）、Eqs. (14)–(16)、関連する§VI QPE資源の記述 | π電子PPP nanographene化学モデル、2次SO/tile PF、低励起gap・QPE資源。化学とphase wrappingに直接重なる。 |
| [L5 Hejazi et al., 2412.16811v1](https://arxiv.org/pdf/2412.16811v1) | 本文Eqs. (3),(4)、補足「Details of perturbation theory analysis」Eqs. (23)–(27) | 任意次数PFによる固有値誤差、gapped targetの摂動論。エネルギー推定への直接の理論的接点あり。 |
| [L7 Simon–Love, 2512.02131v1](https://arxiv.org/pdf/2512.02131v1) | 本文§§2–3、Eqs. (4)–(7)の位相誤差推定、Appendix F「Trotter Error Scaling」 | 化学・random Pauli Hamiltonian、Suzuki PF、QPE資源。状態特化した誤差推定とstep選択に直接重なる。 |
| [L8 Abe et al., 2605.30967v1](https://arxiv.org/pdf/2605.30967v1) | 要旨・導入、§IIのQPE/PF/cost、Appendix B、Appendix C/Table I、Appendix Dの誤差評価（D1–D6・Fig. 10）、Appendix Aの位相推定誤差定義 | repositoryのH-chain基底エネルギー資源評価、高次PF・最適化4次PF、摂動誤差モデル。本研究の直接の既存成果。 |

## 既知結果・重複と移植時の不足

**R1（条件付きの証明）**：Lemma 1は小刻み条件の下で有効Hamiltonianの微分を抑え、Lemma 12/D.1は複素摂動ノルムと単純固有値のgapから解析的に孤立した領域を保証する。本文の `r_max` という表現を、実際の最大Taylor収束半径の決定や実軸AR時刻の上界と読み替えない。補間の誤差保証には複素領域、log枝、PF誤差上界の仮定が必要。D.2–D.6のsmallness・state preparation/query条件も省略できない。`s=1/r`、一stepは`s t`であり、repositoryの一step時間τへの記号対応が必要。[一次資料](https://arxiv.org/pdf/2212.14144v4)

**R2（証明された十分条件）**：Theorem 3は `∫||A||₂ < π` ならMagnus級数が収束し、その和Ωが `exp Ω=Y` を満たすという定理。πは一般保証のsharpな定数だが、各系での必要条件ではないことも本文で説明される。対象は作用素logの級数であり、特定固有値のTaylor級数と同一ではない。複素skew-Hermitian PF生成子への適用根拠、負stageを含む積の順序・絶対係数・ノルム・energy gaugeの対応は未確認。新しい移植証明はしない。[一次資料](https://arxiv.org/pdf/math/0609198v2)

**R3（モデル内の数値観測・機構説明）**：位相の円周への折り返し、狭い回避交差、その後のlevel repulsionと固有状態混合は既に議論されている。Floquet–Magnus収束半径とthresholdの一致は示唆であり、本文はtruncationの完全な厳密化を主張していない。機構説明を新規発見とする余地はない。高次の分子PFにおける特定誤差モデルの破綻・対象枝との因果関係までは検証されていない。[一次資料](https://arxiv.org/pdf/1812.05876v2)

**R4（数値threshold＋小step摂動評価）**：局所観測量の安定域からchaosへの変化とTrotter誤差の増大を結び付ける。局所観測量・長時間力学と、単一の基底固有位相誤差の有限時間適用域は異なる対象。普遍的な分子QPEのAR閾値や実Taylor半径は与えない。[一次資料](https://arxiv.org/pdf/1806.11123v4)

**R5（広い数値観測と特別な共鳴解析）**：複数モデルでthresholdと共通傾向を調べ、threshold以後にもgateの同期による規則的なstable/revival領域を示す。規則性の回復は目標力学の精度回復を意味せず、sampling aliasingも区別される。共鳴を一律に「誤差増大」とする推論は支持しない。分子高次PFの対象枝・誤差モデルへの一般定理ではない。[一次資料](https://arxiv.org/pdf/2110.11113v6)

**R6（化学QPEで既知のwrapping制約）**：低状態gapでの誤差相殺、最適stepの不確かさ、QPEのphase wrappingを明示する。スペクトル幅とstepの積を2π以内にするdynamic-range条件、対象状態のweightに応じた緩和を議論している。energy shiftの選択も関与する。これは測定位相の曖昧性の議論であり、PF回避交差が誤差モデル破綻を引き起こす証明ではない。単位はeV/eV⁻¹で、repositoryのHa/Ha⁻¹と数値をそのまま比較できない。[一次資料](https://arxiv.org/pdf/2605.00745v2)

**L5（gap仮定下の摂動評価）**：固有値特化の高次項・状態変形を評価するが、経路の全 `s'∈[0,s]` で非消失gapを仮定する。Hの原点gapだけから有限step全域のgapは保証していない。U1-ARではこの仮定を確かめる必要があり、既存の局所係数だけで成立扱いにできない。[一次資料](https://arxiv.org/pdf/2412.16811v1)

**L7（QPEへの直接の重複）**：参照unitaryとの相対位相に基づく対象状態のsimulation error推定で資源を評価する。参照近似のbiasと対象固有位相との対応が必要。Appendix Fでは先頭べき則を仮定し、2次PFについて限定されたnorm由来の時間域で数値検証する。外側への保証、4次PFのAR機構、oracle-freeな有効域証明を与えるものではない。[一次資料](https://arxiv.org/pdf/2512.02131v1)

**L8（既存研究との境界）**：基底エネルギー用のPF誤差モデル・step最適化・gate/depth比較は既存成果そのもの。Appendix Dは摂動評価と2次PFの小時間比較を行うが、ARに基づく高次PF有限時間破綻の系統検証ではない。主文の `exp(+iHt)` とAppendix Dの `exp(-iHeff t)` は符号の対応を明示して読む必要がある。Appendix AのQPE標本位相誤差とPFスペクトルの折り返しは別の定義。既存資源claimを今回更新しない。[一次資料](https://arxiv.org/pdf/2605.30967v1)

## 命題A/B/M/R/Nとの静的対応

| ユーザー指示にある命題 | 参照可能な結果 | 採用前に必要な独立確認（今回は未実施） |
|---|---|---|
| A：実軸全体で対象固有枝を解析的・一意に接続 | R1はgapで隔離された複素領域、L5は経路gapを仮定。R3は回避交差・混合を観測 | 対象が固有位相、unwrapped energy、projectorのどれか。交差・縮退・対称性下の選択規則、局所から全実軸へ延長する根拠。離散overlap追跡を解析性の証明にしない。 |
| B：ARがTaylor半径を制限 | R1の解析領域保証、R2の複素パラメータとlog特異点、R3の収束/thresholdの示唆 | どの関数・log枝・展開変数の半径か。実軸の近接/回避交差と、複素平面の特異点の関係。近接は特異点・等号・上界の証明にならない。 |
| M：Magnus/BCHノルム十分条件 | R2 Theorem 3、R1 Lemma 1/D.3 | 行列の範囲、ノルム、PF生成子の時間順序・負係数・identity gauge・stage幅。十分条件外を発散域とみなさない。W_S等の定義を先に固定。 |
| R：有限次HeffではARを表現不能 | R3–R5はFloquet機構、L5/L8は局所摂動 | 「表現」の意味（近似、厳密再現、誤差保証）と次数・領域・PFを指定する必要がある。読了範囲にこの一般的な不可能性の定理は確認できない。真偽判定・反例作成はしない。 |
| N：有限局所係数から有限時間適用性を判定不能 | R1/L5はgap・ノルムなど追加仮定を使用、L7は限定域の数値確認 | 入力情報、Hamiltonian/PFのクラス、事前上界、許容誤差と「判定」の意味。読了範囲に無条件な一般不可能性の証明は確認できない。 |

文献から既知と確認できるのはFloquet折り返し・共鳴・混合の機構と、化学QPEのwrapping制約まで。現在の分子・PF・誤差モデルについてのAR因果性、新しい有効域判定、独立した新規性は未確立。C1で完結するか、狭いU1-ARを検討するかはGPT側の判断に留保する。文献探索はこの必須9本で打ち切った。
