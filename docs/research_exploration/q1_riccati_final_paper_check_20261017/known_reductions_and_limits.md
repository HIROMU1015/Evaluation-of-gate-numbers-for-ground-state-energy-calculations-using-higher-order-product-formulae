# Q1非対角Riccati：既知法との差分とunitary接続の限界

2026-10-17 JST。具体的なRiccati解Yも子の挿入unitary Bも得ていない。
以下は一次文献・固定SOURCEとの対応と不足の記録であり、Yが得られたと仮定した確認結果ではない。

## 1. 入力・操作・出力で比較する

| 方法 | 必要な情報と生成対象 | 今回の判定 |
|---|---|---|
| scalar二次式をFへ適用 | g、F、既知の三つのF固有値から関数を生成 | 紙上導出(5),(6)の明示候補は非対角だがRiccati残差が非零。独立解なし |
| Sylvester逆／Riccati反復 | 親energy差を含む逆作用素、初期値、収束・精度制御 | 既知法への書き換え。全域逆の文法は(14)で閉じない。反復は未実行 |
| invariant-subspace／spectral projector | childの適切な不変部分空間と、graphに移す可逆な上段射影 | それを入力すれば既知の座標移送。必要な部分空間の係数生成が未解決 |
| block diagonalization／direct rotation | 実際のRiccati解とgraph正規化 | 既知の接続であり、今回のY又はBの構成ではない [R01] [R02] |
| Bethe state／form factor | on-shell等のrapidities、正規化、state又はmatrix element | 親の既知表現は利用できる。child全基底の共通生成を自動では与えない [P01] |
| F-basis／ABCs | Betheパラメータを含むMPSと補助空間変換、state準備 | 既知の解析的unitary準備を尊重する。RGの本Riccati生成への移送は未構成 [P02] [P03] |

[R01]: https://arxiv.org/html/1307.6439v1
[R02]: https://arxiv.org/html/math/0105142v3
[P01]: https://arxiv.org/html/2012.10477v1
[P02]: https://arxiv.org/html/2202.04673v4
[P03]: https://arxiv.org/html/2411.02519v3

Riccati式、行列関数、部分空間座標という名前に新規性はない。
今回のG_Fの不成立は固定模型への手による適用であり、一般Riccati理論への新定理や優先権を主張しない。
成功に必要だった差分は、同じ係数入力からFとも非可換なYと新energy評価を生成する実際の規則であり、それは残らなかった。

## 2. 既知graph変換との具体的な対応

[Makarov–Schmitz–Seelmann](https://arxiv.org/html/1307.6439v1)のIntroduction、§2、Remark 2.11は、
Riccati条件、graph、相似block化、polar decompositionによるunitary block化の関係を扱う。
同論文のgraph変数Xが今回のYに対応し、文献中のskew block変数Yは今回の3×3のYとは異なる。
今回の有限次元ではunbounded operatorのdomain条件を新しい障害として持ち込まない。

対応する既知の正規化はI+Y†YとI+YY†、直交補graphは−Y†を用いる。
しかしこれらを記号として書くことは、入力係数からYを得たことにならない。
形式的な上段の有効作用A−gFYも、実際のenergy一覧ではなく、残る三次元作用である。
Riccati解が仮にあっても、それを対角化・energy評価へつなぐ費用とcoherentなlabel返却が残る。
今回それらの正規化・補空間・対角化を具体Yに適用した確認は行っていない。

[Albeverio–Makarov–Motovilov](https://arxiv.org/html/math/0105142v3)の§2、Lemma 2.5等では、
Sylvester式の解表示にspectraの分離条件が現れる。
今回の成分式(11)はその有限次元での既知の対応であり、分離を無料に仮定できないことを(13),(14)で確認した。
文献の十分条件が全ての別解法に必要だとは読み替えない。

例えば既知のrank-three直交spectral projector Pが得られ、P11が可逆なら、graph座標はY=P21 P11⁻¹と書ける。
このPの選択・生成やchild energy／固有vectorを外部から渡せば、既知の不変部分空間法を隠しただけになる。
P11の特異性はその座標の問題であり、全ての別chartや物理的なunitaryの不可能性ではない。
今回Pの計算・spectral list取得・matrix sign等の実行はしていない。

## 3. Bethe／F-basisと親labelの情報費

[RG transition-density文献](https://arxiv.org/html/2012.10477v1)の§II、§III.1–III.2では、
stateとform factorがrapiditiesとnormに依存する。
前回のparent一対secular式は、この小例では係数と順序labelから定義できる既知の表現である。
今回の紙上証明はそのlabel順序を利用したが、新しいroot取得、全child stateの列挙、全child spectrumのoracleは使っていない。
形式λを使ったことを、可逆評価の実装費が零であるとの主張にしない。

[ABCs](https://arxiv.org/html/2202.04673v4)の§3.1はABAをQR経由で準備用unitaryへ移し、
[F-basis構成](https://arxiv.org/html/2411.02519v3)の§3はパラメータを持つMPSから解析的unitary準備を導く。
指定stateの準備と、係数だけから全parent/child labelを一貫して変換する本課題の契約は区別する。
これらを一般に非効率と断定しない。一方、各stateへ既知準備を適用し列挙しただけではQ1の生成補題ではない。

著者公開実装snapshot `7f33e688e4ac15cb3a7a1c57a5de4a3a66d0cdee` については、
前回SOURCEの固定registryにあるroots入力・QRの静的記録を参照する。
今回コードを再取得・再実行・変更しておらず、前回の実装監査を新規実施と数えない。
新規Riccati solverの取得や実行もしていない。

## 4. B条件の到達状況

| 依頼Bの条件 | 今回の到達状況 |
|---|---|
| 実際のYでRiccati恒等式 | 未達。G_F候補は失敗し、別の解は未構成 |
| graphの正規化・直交補 | 具体Yがないため未実施。既知の条件付き関係を比較したのみ |
| 残る三次元作用とenergy評価 | 未実施・未構成 |
| 共通unitary B、B†B=I、K B=B Dchild | 未確認。存在又は既知block化で代用しない |
| superposition coherence、work返却 | 未確認。個別state準備を共通Bと認定しない |
| controlled scalar phase | 前回の必要条件を保全。具体Bによる新しい確認はなし |
| 一般Lの費用・conditioning・誤差伝播 | 具体Yがないため拡張検討は未実施 |

固定模型のself項は全m=2空間で−2gI。controlled evolutionのcontrol=1にはc−2gのphaseを残す。
Riccati式でcが消えることを、絶対energyやcontrol相対phaseの削除へ移してはいけない。
D2としてscalar、一体項、self、元Hへの対応を保持し、seniority-zeroの最低値を全電子sectorの絶対E0と同一視しない。
R=0は指定された厳密pairing模型の条件で、一般電子Hの残余を黙って捨てる条件ではない。
D1に従いblock-encoding／qubitization中心へ移行しない。

## 5. 独立性・未確認範囲と判断材料

既知の処理として書ける部分は既知法へ還元され、独立した係数生成則の実例は得られなかった。
新たな結果は、明示した二文法についての有限例の限定的障害だけである。
全Riccati解の不存在、一般Q1の不能性、gate下界、資源優位、全世界での新規性は未検証。
文献確認は指定箇所に限り、文献未発見を不存在の証拠にしない。

数学的に別解があり得ることは残るが、いま追加探索を自動継続するための具体的機構・成功を識別する生成則は得ていない。
本依頼の最終限定という条件に従い、**Q1の追加探索を一時保留することを第一推奨**とする。
これは正式状態の変更ではなく、GPT／ユーザーへの判断材料である。
