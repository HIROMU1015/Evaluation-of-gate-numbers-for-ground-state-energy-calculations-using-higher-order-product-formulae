# 差分claimと三種の比較対照

2026-10-18 JST。仮説はFの占有条件付き測定である。結論を先に言えば、固定基底ablationとの差はあるが、**核心を既に含む公表法が存在し、その具体的代入で同じ操作・記録分布・費用を再現できる**。B_plus_core一致だけからの循環的な新規性否定を使わない。

## 対照の由来

| 区分 | 今回の具体的な手順と根拠 | 許可するもの・比較の意味 |
| --- | --- | --- |
| B_pub（軌道basis測定） | Hugginsほか[L03 §II.1、式(2)–(5)](https://arxiv.org/html/1907.13117v4)の、軌道回転後のoccupation測定 | 公表済みの既知部品。原論文の分割器が必ず今回の二poolを選ぶ、とはしない |
| B_sep（ablation） | tXとuSZを別poolで測る明示的な固定分割。必要ならνS+dZを同じdiagonal poolへ加える | 核心を外した識別用。これを世界最強のB_pub／B_fairとは呼ばない |
| B_pub（条件付き測定） | Patel–Yen–Izmaylov [L01 §III.2–3、式(25)–(35)、Fig.1(b)](https://arxiv.org/html/2305.18251v2) | 対称性occupationを読み、係数を代入したone-body問題から軌道回転を決める。今回の核心を公表時点で具体化している直接対照 |
| B_fair | L01へP2係数を渡し、active二modeの閉形式角度、三値sのtable共有、同じ精度・seed・feedforwardを許す | [G5への代入](generation_rule_construction.md)で候補と同じG4。候補専用oracleを呼ばず、同じ算術・量子操作で生成できる |
| B_plus_core | 任意のenergy評価frameworkに今回のP2 pattern検査とG1–G4をそのまま差し込む | どこが差になるかを示すadapter／ablation用。これの一致だけを核心の先行存在の証拠にしない |

L02（Patel–Izmaylov、[2402.09376v1 §II.2–4](https://arxiv.org/html/2402.09376v1)）は、より広いsymmetry付きfragmentと測定生成を扱う補助対照として該当節のみ確認した。今回の還元はL01とG5で閉じており、L02の全graph分割・数値優位を再認証する必要はない。

## 同じ条件を与える範囲

H=cI+F+R、mode順、N=2、有限bit係数、同じstate準備AとC_A、未知ρ、装置が許す測定／feedforward、precision・失敗率、Rの評価と全古典費を揃える。候補側だけにD2の都合のよいstate、真のvariance、対称性、角度・routingを無料で渡さない。state-independent range boundを使う場合も両者で同じにする。

**生成済み角度を無料で渡した下流比較だけではない。** B_fairもP1→P2の係数検査、a_s、sqrt、atan2、Givens角の生成、table保存、結果に応じたbranchを自ら計算する。三つのh(z)という定数サイズ入力なので、候補にだけ独立の難しい生成器が残るわけではない。一般の多数modeに対する最適pattern抽出費を0としていないし、その新規アルゴリズムを今回構成したともしていない。

## claimの判定

| claim | 根拠と判定 |
| --- | --- |
| 条件付き軸は一つの固定active軸と異なる | D1の非可換性で成立。ただし限定classの差 |
| coreを入れると物理的な測定分散が変わり得る | D2–D4で成立。古典縮約順序だけの変更ではない |
| coherent controlの保持が破壊的F測定に必須 | 不成立。G4は測定→古典feedforwardでも実現し、公表L01が明記する |
| 条件付き測定coreが新しく、既知対照では同費用に生成できない | L01の具体的係数代入とG4 identityにより支持されない |
| 同じF recordから元Rまで追加準備なしに得られる | D5–D6で否定される（record-only universal reconstructionに限る） |
| 有用な絶対E0推定・独立資源改善が完成した | 未証明。state誤差と全H測定・noise・native費が残る |

今回のpattern・例・式の組合せの世界的初出は認定していない。重要なのは、量子操作と情報取得の核心に対し、論文に既にある生成手順を具体的に代入でき、別の独立価値差が残らないことである。既知部品を用いる全組合せの無価値や、「B_plus_coreに含まれたら常に既知」という一般規則は導かない。
