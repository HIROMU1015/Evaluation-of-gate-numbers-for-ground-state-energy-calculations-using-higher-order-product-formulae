# 既存冷却法と生成機構の比較

2026-10-18 JST（作業系列ID：20261017）。指定3論文を含む一次資料を確認した。下表は実際に読んだ本文範囲に限る要約で、全冷却分野のpriority調査ではない。原文bytes/hash・版・読取り範囲は[registry](source_registry.json)。論文本文は再配布しない。

## 1. 入力から操作までの既知の到達点

| 一次資料 | 入力→coupler/操作 | 非可換性・保証/費用の境界 |
| --- | --- | --- |
| Ding–Zhan–Preskill–Lin, 2508.05703v2 [L01] | 与えたcoupler集合とランダム浴周波数、時間envelope、forward system–bath発展、1補助qubitの反復reset | Algorithm I/Thms1–3。一般の費用はmixingに依存しground保証にはgap依存もある。明示効率保証の模型classを一般相互作用Hへ広げない |
| Schlömer–Chen–Yelin–Hu, 2605.01029v1 [L02] | symmetry-preserving hopping・spin-exchange等の局所toolboxから選び、周波数をランダム化してreset | 一般強相関fermionへの数値証拠とETH接続のconjectureを分離。spin-exchangeも複数fermion演算子であり「多電子coupler」は未開拓ではない。一般mixing保証は未確定 |
| Zhanほか, 2503.15827v3 [L03] | 与えたAに対する `K=∫f(s)e^{iHs}Ae^{-iHs}ds`、負周波数filter、Lindblad発展 | §IIの構成は固有basisの事前列挙を要しない一方、H simulation・quadrature・gap下界等を会計。論文のblock-encoding実装をD1下で自動採用しない。quasi-free/特定弱相互作用のrapid mixingは既知 |
| Marti–Mansuroglu–Hartmann, 2403.14506v2 [L04] | free理論由来のfermionic coupler、fridgeとの共鳴、spectroscopy、reset | §§2.2–2.3。理想全eigenbasis couplerと実用free couplerを区別。相互作用系への情報取得・低energy初期subspace・gap/走査条件を無視しない |
| Temmeほか, 0911.3635v2 [L05] | 実装可能なproposal unitary、coherent energy測定、energy差によるaccept/reject、recovery | pp.4–7,9の操作記述。固有一覧は無料入力しないが、制御時間発展/読出し/拒否回復とmixing費用を払う。有限温度経路も含む既知方式 |
| Verstraete–Wolf–Cirac, 0803.1447 [L06] | dissipationによる状態準備という既存framework | 今回はofficial abstract/metadataだけ確認。個別の局所準備定理を本文確認済みとして輸入しない |

[L01]: https://arxiv.org/html/2508.05703v2
[L02]: https://arxiv.org/html/2605.01029v1
[L03]: https://arxiv.org/html/2503.15827v3
[L04]: https://arxiv.org/html/2403.14506v2
[L05]: https://arxiv.org/pdf/0911.3635v2
[L06]: https://arxiv.org/abs/0803.1447

## 2. 今回の具体的規則との対応

| 今回検討した規則 | 入力/操作/出力の対応 | 技術分類・独立性の限界 |
| --- | --- | --- |
| 対角係数から二電子下降predicateを作る | 対角energy差を可逆評価→条件付きdouble excitationとancilla rotation→reset。占有人口は集団proposalのzero-temperature Metropolis型更新 | **B**。通常の振幅減衰のcoherent拡張と既知の下降遷移選択。gateが同じだからでなく、受理predicateと更新機構自体が既知 |
| H*の条件付き回転でpair jumpをdressing | 係数から2次元のdetuning/角度→W†→既知pair reset→W。interactionは角度に保持 | **B**。解析的な小ブロック基底変換を用いた既知rank-one冷却。一般Hの新しいjump生成を得たとはしない |
| 同じAのspectral filterを変える | [L03] §IIと同じHeisenberg evolution積分。非零の既存遷移の率/選択性を変える | **B**。元のAの零matrix elementは同じまま。collectiveな辺を新生成したことにならない |
| dressingを固定して境界hoppingだけ追加 | 実CPTP操作は定義できるが、sourceと補空間のcoherence項が残る | **C**。固定rank-one grammarの全状態単調性が破れる。cycle/複数jump/input-class法の一般否定ではない |

本作業の具体的Wが[L04]に同じ式で掲載されているとは主張しない。[L04]のfree基底couplerと今回の相互作用依存Wには差がある。ただし今回Wを生成できた根拠は、既知の条件付き2次元対角化が可能な制限classである。ユーザーが求める「小blockを解いてresetするだけを越える構成」は得られていない。この範囲のB判定を、全cooling算法が同じという還元にしない。

## 3. 文献から輸入しない条件

resetは熱力学的/情報的資源であり費用を0にしない。共鳴幅、有限時間filter、spectral connectivity、Lindblad gap、古典coupler生成を同時に無料化しない。既知法がgroundを固定点に持つことと、任意初期stateから速く到達することは別。非可換Lindblad発展の既知実装があることだけで新しいcoupler選択則の有無は決まらない。

紙上障害のpriorityは認定しない。今回未確認なのは、一般非可換係数から安く得るcoherence補正・接続性・進捗の規則、その最良既知法への完全対応と実用性。未発見を新規性の根拠にせず、これ以上の網羅探索は今回自動開始しない。
