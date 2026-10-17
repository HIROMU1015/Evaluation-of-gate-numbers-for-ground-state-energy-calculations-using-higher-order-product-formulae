# 先行研究との対応と独立性の限界

2026-10-17 JST。Q1は既知の「積分可能系の量子準備」という研究テーマの新規発見ではない。
今回新たに要求するのは、明示familyでの(Q3)の契約と、(Q5)–(Q7)を満たす係数からの生成補題。
**この補題を構成・証明するまで、新しいアルゴリズム構成原理を得たとは扱わない。**

## 1. 確認した一次文献

以下は必要箇所の要約。全文を取得しても、全証明・出版差分・全resource tableを監査したわけではない。
固定版のidentityと読取り範囲は[source_registry.json](source_registry.json)。

| ID | 固定一次資料 | 今回の比較に使う到達点 |
|---|---|---|
| L01 | [Sopenaら, Algebraic Bethe Circuits, 2202.04673v4](https://arxiv.org/html/2202.04673v4) | rootを受けたstateのdeterministic準備。一般の多magnonでの大きいP block／QR・gate合成の費用を、free primitiveにしない |
| L02 | [Ruizら, F-basis, 2411.02519v3](https://arxiv.org/html/2411.02519v3) | 解析的なABCs・補助空間の基底・inhomogeneous XXZへの構成を含む強い対照。Q1と同じ係数入力の全RG基底compilerまで示すとは読まない |
| L03 | [Raveh–Nepomechie, 2403.03283v3](https://arxiv.org/html/2403.03283v3) | arbitrary U(1) stateの明示準備。\(\binom{L}{m}-1\)のmulti-controlled rotationという到達点があり、extensive fillingでは指数個になる |
| L04 | [Lutzら, 2503.21741v3](https://arxiv.org/html/2503.21741v3) | charge eigenvalueからのparent準備。RGでは非摂動域gapとuniformなclassical解法の保証が未閉鎖。単一stateの条件付き構成を過小評価しない |
| L05 | [Piroliら, 2403.07604v3](https://arxiv.org/html/2403.07604v3) | LOCC付き近似準備。interacting-state例はlow-excitation・近似commutator等の仮定を持ち、全入力unitaryではない |
| L06 | [Johnsonら, 2007.10705v1](https://arxiv.org/html/2007.10705v1) | RG stateを元Coulomb Hのvariational ansatzへ使う。模型Hと物理Hの同一性や、coherent基底変換の安さは主張されない |
| L07 | [Berryら, 2510.07380v2](https://arxiv.org/html/2510.07380v2) | real-space FMM＋phase生成＋PFという既知のCoulomb生成規則。今回新案として保持しない |
| L08 | [Mottaら, 1808.02625v2](https://arxiv.org/html/1808.02625v2) | low-rank factorization、basis rotation、平方fragmentの既知PF。新primitiveの価格を無視しないbaseline |
| L09 | [Johnsonら, Transition density matrices, 2012.10477v1](https://arxiv.org/html/2012.10477v1) | RGの状態間overlap／TDMの既知式。指定要素を求めることと、全要素を安く量子作用させることは別 |
| L10 | [Gu–Somma–Şahinoğlu, 2105.07304v2](https://arxiv.org/html/2105.07304v2) | 効率的な基底変換・block発展等を仮定したfast-forwarding。permutation-invariant／quadraticの既知十分条件も比較 |
| L11 | [Johnson, 2405.00279v1](https://arxiv.org/html/2405.00279v1) | 改良TDMと近零特異値によるSlater–Condon類似則。near-zeroに基づく参照stateの構造を、全branchの厳密疎性やcoherent compilerと同一視しない |

「最良構成」は、上の確認範囲での強い対照群を意味する。全手法での最適性・下界は認定していない。
L01–L03のXXZ結果をそのままRGのgate上界とはしない。同じBethe準備という名前だけで還元又は非還元を認定しない。
L09/L11の同粒子数TDMと、(Q6)のpair数を変えるform factorも区別する。
後者をoverlapの特殊極限で扱う可能性はあるが、今回その移送の導出や全基底factorizationまで確認していない。

## 2. 入力→操作→出力で比較する

| 比較 | 既知法が与えるもの | Q1に必要な追加事項 |
|---|---|---|
| root指定の準備 | 与えられたroot setに対応する一つのketを既知referenceから作る | 係数から全labelへ一貫したWとDの生成。前処理・root取得の費用も含む |
| charge-parent準備 | charge情報とparent条件の下で指定stateを準備 | 未知gap／chargeを入力にしない(Q3)のoperator保証。既知法の条件を証明するだけでは今回の新生成補題にしない |
| MPS／QR／F-basis | 一つのBethe stateの構造・準備の強い既知手掛かり | 指数個のcolumn／branchを列挙しないshared recurrenceとclean work。一般rational/Gaudin limitの移送可能性は未確認 |
| 既知fast-forwarding | 使える基底変換とblock回路があれば発展を生成 | まさにその安いWとD評価を構成する。一般の\(W e^{-itD}W^\dagger\)は新規性ではない |
| uniform準位のcollective spin | 対称性を用いる既知CG／Schurの経路 | 異なる\(\epsilon_p\)によりcollective total spinだけでは残らない作用を扱う。uniform準位への退化だけでは失敗 |
| 一般PF | 既知gateから元Hの発展を所定精度で近似 | Q1のpolylog時間・精度依存を目指す別の生成補題。PF次数や係数を変えるだけでは成功にしない |

pair演算子は\([P_p,P_p^\dagger]=1-n_{p\uparrow}-n_{p\downarrow}\)を満たし、異なる軌道では偶演算子として交換する。
従ってPの二次式を元fermionのquadratic／Gaussian Hamiltonianとして扱うことはできない。
また異なる\(\epsilon_p\)の一体項は一般にtotal pair-pseudospinの\(S^2\)を保存しないため、
旧collisionで成立した「total spinだけにphaseを付ける」操作では足りない。

L10のLie-algebra経路は、実装できる生成元・既知Cartan構造等の条件を伴う。
RG chargeが可換であるというだけで、未知の基底を既知のcomputational diagonal basisとして与えてはいけない。
一方、同じ入力条件で既知法へ具体的に還元できれば、新構成としての独立性は撤回する。

## 3. 公開実装の静的確認

著者repository `AlejandroSopena/Algebraic-Bethe-Circuits` のrelease `1.0`、
snapshot **7f33e688e4ac15cb3a7a1c57a5de4a3a66d0cdee** を固定し、次の3ファイルを取得した。
origin/result commitは各pathの最終変更commitとしてsnapshotと別fieldへ保存した。

- [README.md](https://github.com/AlejandroSopena/Algebraic-Bethe-Circuits/blob/7f33e688e4ac15cb3a7a1c57a5de4a3a66d0cdee/README.md)：root指定と、Pのunitary／isometryの区別を確認。
- [bethe_circuit.py](https://github.com/AlejandroSopena/Algebraic-Bethe-Circuits/blob/7f33e688e4ac15cb3a7a1c57a5de4a3a66d0cdee/bethe_circuit.py)：`aba(roots)`、`_unitary_gates(roots)`が明示rootを受けることを確認。
- [Pk_gates.py](https://github.com/AlejandroSopena/Algebraic-Bethe-Circuits/blob/7f33e688e4ac15cb3a7a1c57a5de4a3a66d0cdee/Pk_gates.py)：`full_pink`と`RT`のKronecker／QR配列がmagnon数に依存することを確認。配列のcode上isometryを任意入力上の完成unitaryとして無料にしない。

これはXXZ準備実装であり、RGの全固有基底compilerを実装しているとは扱わない。
上記sourceをimport、実行、test、変更、compileしていない。記載されたbackend設定も適用していない。
L04のdata repositoryは文献中に参照があるが、今回コードを取得・実行していない。
公開実装を発見できないことは不存在の証拠ではなく、Q1の独立性の根拠にもしていない。

## 4. 過去の提案との重複の限界

P2の「小cellを選び対角化する」という一般骨格や、NAの二次Lie表示と、広い代数的な重なりはある。
Q1はその広い分類を新規と呼ばず、明示したinhomogeneous family・extensive filling・係数前処理・全入力norm保証に絞る。
二電子collisionのcoefficient-independentなCG generatorとも、異なる対象である。
今回はその既知還元を変更・再審査せず、Q1のlevel追加の係数依存作用を扱う。

PRの既存scopeも、可解代数の利用一般を既検討としている。
Q1で差分となり得るのはcompactな挿入補題だけであり、
単に「Bethe」「Gaudin」「intertwiner」と呼ぶこと、既知のmatrix elementを再導出することは十分でない。
既知準備＋既知gap仮定＋QPEという組合せに尽きる場合は、新原理の課題としては保持しない。

## 5. 未確認範囲

本調査は、2026-10-17時点で取得・固定した文献とsourceの必要箇所に限る。
全Bethe／integrable quantum algorithmsの網羅的優先権調査、L02の全Gaudin limit、L04の全証明の独立査読はしていない。
そのため「新しい構成が世界にない」とは断定しない。
一方、今回の対照の入力・出力・費用が(Q3)–(Q7)を満たすと読み替える根拠も得ていない。
Q1の正式採否は、限定familyの科学的価値と、この追加構成が研究目的に合うかを含め、GPT／ユーザーへ戻す。
