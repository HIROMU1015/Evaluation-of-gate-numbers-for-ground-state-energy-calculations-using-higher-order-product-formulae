# 未解決問題の限定調査記録

2026-10-17 JST。一次文献11件の必要箇所、著者公開実装3ファイル、固定研究記録を静的に確認した。
**保持する数学的研究課題案はQ1の1件。完成した新原理又は正式採択ではない。**
全文を取得したことと全証明を読んだことは区別する。各版・取得日・bytes・SHA-256・読取り範囲は[source_registry.json](source_registry.json)。
調査はこの範囲に限り、文献未発見を世界での新規性・不能性の証明にはしない。

## 1. 何を未解決と呼ぶか

| 区分 | 具体的な対象 | 今回の意味 |
|---|---|---|
| A：数学的な条件が未閉鎖 | RGの非摂動域でのparent gapの一様な下界、係数から全charge解を得る計算量 | L04が明示する理論的留保。単に実装がない、という話ではない |
| B：既知構成があり保証・入力が限定 | eigenstate指定のBethe準備、RG parent準備、低励起のmeasurement-assisted準備 | 構成の不存在は主張しない。入力情報・保証がQ1の全入力契約まで届くかを比較 |
| C：構成原理は既知 | PF／DF、既知対角化を用いるfast-forwarding、real-spaceのCoulomb FMM、CGによる旧collision | 既知原理を候補として再採択せず、適用条件／費用や元Hとの対応を残す |
| D：既存系列の限定未解決・保留 | PF校正、PR信号移送・費用保証、J1、NA/NB、P1～P8 | 当該研究のscopeに帰属させ、今回の独立課題へ名称変更して移さない |

A/Bは「今後も全算法で不可能」という分類ではない。
Q1はAのgap命題を言い換えるものではなく、Bから**係数入力のcoherentな全基底変換**へ進む生成問題を、別の精度契約で定式化したもの。
gapの証明だけを新しい操作原理として数えない。

## 2. 一次文献から分かった到達点と障害

### 2.1 積分可能性と実行可能性の間

ABCsはBethe ansatzをunitaryな準備へ変える既知構成である。rootを与えた特定stateの準備と、
係数だけから任意入力を発展させる変換は同じではない。
L01の一般的な多magnon処理、L03の明示的deterministic準備には、既知の指数的な処理・rotation数が残る。
L02はF-basisによる構造・解析式・補助除去を進めているので、「QRしかない」とも扱わない。[L01] [L02] [L03]

より強い対照は、2026年掲載のL04である。RG eigenstateをchargeから定めたparent Hで準備する構成があり、
小g／大g等の解析結果もある。非摂動域の一様gapと、charge解をclassicalに効率よく得る保証には留保が残る。
それを無条件poly-timeの既知算法にも、単なる未実装にも分類しない。[L04]

L05のinteracting-state準備はlow-excitation等の仮定を持ち、そのままextensive fillingへは移せない。
測定・feedforwardによるstate準備を、逆変換とcontrolを含む任意入力unitaryへ無料で転用しない。[L05]

### 2.2 化学のRG表現は、元Coulomb Hの置換を許さない

RG状態をCoulomb Hamiltonianのvariational ansatzに使い、energyやtransition要素を扱う既知研究がある。
これにより模型と電子相関の接点は具体的になるが、RG Hamiltonianと元molecular Hが一致するわけではない。
既知の密度行列・overlap式から、指数個のbasis全体を安く量子変換できるとも結論しない。[L06] [L09]
2024年のL11はtransition要素の改良とSlater–Condon類似則を持つ。
旧文献の「そのような則がない」という記述を現在の到達点として引用せず、near-zero couplingを全branchでの厳密疎性とも読み替えない。[L11]

Q1はまず明示したpairing familyのsimulation primitiveを対象とし、元Hとの残余R・一体項・scalarを[問題定式化](research_problem.md)で保持する。
実分子の絶対E0や近似stateの品質が保証された、とはしない。

### 2.3 すでに生成規則がある方向

低rank分解とbasis rotationによる電子HのPF実装は既知であり、係数分解の表現を変えただけで新原理としない。[L08]
また、2026年改訂のreal-space first-quantized FMMは、Coulomb計算からphaseを生成する手順を既に持つ。
「量子FMMを使えばよい」を新しい研究課題にはしない。一般orbital基底への移送には表現変換・射影・誤差の条件が別にある。[L07]

fast-forwardingの一般的な基底変換枠、permutation-invariantなspin系、quadratic fermionの既知例も確認した。
inhomogeneous pairingへの必要な安い変換を得ずに、この枠を引用して解決とすることはできない。[L10]
同様に、genericなblack-box下界を係数明示のQ1にそのまま適用して不可能とも断定しない。

## 3. 既存repositoryの障害の帰属

| 固定研究 | 今回参照した内容 | Q1へ移さない内容 |
|---|---|---|
| 第一研究 | S4固定診断の`complete_no_benefit`、state proxyとdecisionの違い | selector、時刻、threshold、truthの再探索 |
| 第二研究 | rankによるpoint精度とsame-time budget価値の違い、承認済みclosure | rank／gamma／geometryを変更する救済 |
| PR Track A | 取得済み点優位と母平均・最終energy費用の区別 | 旧点優位を消えたと書換えない。新compile／samplingを開始しない |
| PR Track B | 後続の限定受理結果とDRAFT／NOT ADOPTED addendumを区別 | 一般DF／全RPEへの保証を新しい独立課題と呼び替えない |
| P1～P8／J1 | bus閉路、配置cell、processor、測定制御変量、lift、clock等の検討範囲 | J1 PAUSE、他STOPの解除、同じ機構の再開 |
| NA/NB | 一般rotor expの不足、TDCCとchart輸送の限界 | rotor／log輸送を別名称で再提案しない |
| 二電子collision | coefficient-independent generatorのCG/Paldus還元は独立紙上検証で確認済み | その固有値、coherence又はphaseを未解決として再審査しない |

固定根拠はSOURCE S01–S12、R01–R04。保存された科学数値の再集計・新たな詳細レビューはない。
可解代数を利用する広い問題はPRの既存scopeにもあり、テーマ全体を未探索とはしない。
今回の差分候補は、familyと入力を固定した(Q3)–(Q7)の新しい生成補題に限る。

固定資料群に対してRichardson／Gaudin／Bethe等を補助検索したが、語の不一致を未検討の証明にしない。
Richardson外挿とRichardson–Gaudinの固有state問題も区別する。
旧レビューが扱った別名の可解模型、未取得の資料、他branchの議論の可能性は残る。

## 4. 保持しなかった方向

- **RG parent gapの証明だけ**：実際に未閉鎖の数学的課題だが、それだけでは今回求める独立した生成規則との差分にならない。L04の研究を再命名せず、強い対照とする。
- **一つのBethe状態をより浅く準備するだけ**：既知ABCs／deterministic準備／測定補助の枠に対する最適化に留まる可能性が高い。Q1の全入力unitary契約とは区別する。
- **Coulombの新しいFMM利用**：具体的な既知操作があるため、異なる構成を提示せずに保持しない。
- **全Hのnoise-free測定器／copies再利用**：旧O5・X2・P6の問題と重なる。今回は追加のinstrument生成規則がなく、2件目にしない。
- **有限orbital空間へcoordinate phaseを圧縮する案**：射影後のexpを作る新規則を得ていない。前回の不足を名前だけ変えて再掲しない。
- **可解fragmentの一般発見・最適化**：既知Cartan／Lie／DF等との差分がないまま汎用solverへ置き換えない。

候補数を満たすために第2課題を作らない。
「保持1件」は新原理の発見を意味せず、必要な新数学的構成と失敗条件を定義できたという限定判断。

[L01]: https://arxiv.org/html/2202.04673v4
[L02]: https://arxiv.org/html/2411.02519v3
[L03]: https://arxiv.org/html/2403.03283v3
[L04]: https://arxiv.org/html/2503.21741v3
[L05]: https://arxiv.org/html/2403.07604v3
[L06]: https://arxiv.org/html/2007.10705v1
[L07]: https://arxiv.org/html/2510.07380v2
[L08]: https://arxiv.org/html/1808.02625v2
[L09]: https://arxiv.org/html/2012.10477v1
[L10]: https://arxiv.org/html/2105.07304v2
[L11]: https://arxiv.org/html/2405.00279v1
