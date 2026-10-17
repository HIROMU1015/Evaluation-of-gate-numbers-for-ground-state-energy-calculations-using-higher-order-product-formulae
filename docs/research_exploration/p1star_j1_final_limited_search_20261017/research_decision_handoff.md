# J1最終限定探索：判断用handoff

2026-10-17 JST。**非還元な共同生成文法は得られなかった。第一推奨はJ1追加探索の一時保留。正式な研究状態は変更していない。**

読む順序：本書 → [限定構成と数学的導出](limited_construction_record.md) → [provenance](provenance.json)。本branchは最新紙上検証c7d3f077d634e4165b7cd326bac7caa1ae04ff66を起点に、新規資料だけを追加する。

## 一度だけ検討したもの

完成した二体gateにechoを掛ける前回の構成から離れ、許可されたHermitian一体factor×共通busの、**まだ閉じていない二つの2-pulse leg**を直接交換する文法を定めた。S/A経路の差でCAR交換対を使い、2次信号を$-4iH_\diamond$にする。

| 文法 | 結果 | 判定 |
| --- | --- | --- |
| G1：16-pulseの未完了legのgroup commutator | 1次は零、2次は不要busなしの非零二体信号。3次のWeyl対称$X^2P$に非零の一体係数が残る。 | **限定的な不成立**。このcellだけの否定。 |
| G2：同じlegを対称PFに置き換えた24-pulse修正版 | 1～3次条件を満たすが、3次は比較代数ですでに零。可換aggregate forceの既知rectangleをStrang分割した生成規則そのもの。 | **成立するが既知法への還元**。J1固有の候補として保持しない。 |
| 非還元なJ1共同生成一般 | 具体例も一般的不可能性証明も得ていない。 | **未解決**。新たに保持する非還元候補は0件。 |

二つを調べたところで終了し、第三の文法、振幅調整、solver、網羅探索へ進めていない。新規科学計算、科学的な記号計算コードの作成・実行、数値simulation、実装は0件。

## 今回明らかにした障害

一体factor×線形busからの三重Lie語では、bus三次の最高次数係数は電子の一体入れ子交換子となる。N=1上で非零なら、二体のCAR零関係ではfull Fockの零へ送れない。G1では、この係数の(r,q)成分が$(-1+i)/2\ne0$となる。

G2の対称化はその障害を除けるが、相殺は一体Lie関係と一般的なPFの対称性で説明が尽くされ、CARは二体信号を選ぶところにしか必要ない。CARが目標生成と3次相殺の**両方**に不可欠、という今回の要件は満たせない。

同じ2次信号は、q,sの直交した和差modeを使った既知の幾何学的位相閉路へ具体的に対応する。その座標変換を無料の物理rotationにしていない。G2と完成baselineの一致は1～3次についてで、有限ηでexactに同一のpathとはしない。

## GPT／ユーザーへ戻す推奨と不足事項

**第一推奨：J1の追加探索を一時保留する。** 今回の固定範囲では、科学計算へ渡す非還元の文法を作れず、計算で判別すべき独立機構が未定義のままである。これはJ1一般やP1*一般の不可能性、又は高リスク研究全体に価値がないという結論ではない。

継続を判断するために不足するのは、次の条件を同時に満たす一つの具体的文法である。

1. 最高bus三次を一体Lieの段階で消す。
2. 残るbus一次成分を、CARで消える電子積の関係へ送る。
3. 同じ未完了cellで二体信号も生成し、完成gate＋汎用PF／echo／DCGの説明へ還元されない具体的根拠を示す。
4. 実制御、全低次条件、shuffle、Hermiticityを同時に満たす。

これは将来の再開を判断する条件の記録であり、次の探索作業の開始指示ではない。今回、追加候補、計算計画、driverを作らない。研究候補の正式採択・取り下げ・PAUSED/HOLDへの状態変更も行わない。

4次以降、G2全体の有限時間帰還、unbounded busの誤差保証、物理的access、新規性・資源優位は未確立。D1・D2、元Hの絶対E0対応、full Fockとsectorの区別、既存のSOURCE・結果・grant・authorization・STOPは維持した。

## 固定参照と引き渡し

- [J1仮説：dd36794069f2f8063d3eba6c7e3fcc989d9b0ceb](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/dd36794069f2f8063d3eba6c7e3fcc989d9b0ceb/docs/research_exploration/p1star_joint_loop_principles_20261017/joint_loop_principle_hypotheses.md)
- [前回の紙上検証：c7d3f077d634e4165b7cd326bac7caa1ae04ff66](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c7d3f077d634e4165b7cd326bac7caa1ae04ff66/docs/research_exploration/p1star_j1_paper_feasibility_20261017/mathematical_feasibility_record.md)
- [固定wordの3次障害：5110d347e1f032c9093430b3def13b3391602cdd](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5110d347e1f032c9093430b3def13b3391602cdd/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md)

前記録Eq. (12)の表示ミスは数学記録末尾に注記した。原本は修正していない。sourceのorigin/result commitと今回照合するsnapshotはprovenanceで別fieldに保持する。

**次の担当：GPT／ユーザーが、一時保留を採るか、追加情報を条件として継続するかを判断する。Codexは資料のcommit・通常pushとremote SHA／Git blob／bytes／SHA-256照合を完了してMandatory STOPする。** 科学計算、実装、追加探索、科学レビュー、正式な状態変更を自動開始しない。
