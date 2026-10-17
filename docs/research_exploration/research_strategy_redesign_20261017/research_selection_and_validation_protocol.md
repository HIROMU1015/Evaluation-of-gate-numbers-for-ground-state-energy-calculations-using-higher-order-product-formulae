# 研究候補の選定・検証プロトコル（提案）

2026-10-17 JST。作成：Claude Code（Codex側の技術調査・資料作成の役割）。
**本書は、今後の新アルゴリズム研究で使う候補選定・検証手順の提案である。GPT／ユーザーが採否を判断するまで、正式な運用規則ではない。**
既存の`AGENTS.md`、D1・D2、freeze・truth barrier、GitHub handoff規約、計算性能方針を置き換えない。
過去研究（J1、Q1を含む）の正式状態・保留理由・再開条件に遡って適用しない。

読む順序：[横断分析](research_exploration_retrospective.md) → [方法論の分析](exploration_methodology_analysis.md) → [戦略比較](future_research_strategies.md) → 本書 → [判断用handoff](research_strategy_handoff.md)。

## 1. 目的と設計条件

このプロトコルは、過去の探索で繰り返し起きた次の事象を、手順の側で防ぐために設計した（根拠は[方法論の分析](exploration_methodology_analysis.md) §2）。

1. 発想は具体的でも、許可された入力と操作から目的の作用を作る**生成規則**がないまま検討が進んだ。
2. 既知法への還元が、構成を作った後に判明した。
3. 固定ansatzへの重い計算が、紙上で分かる低次の障害より先に行われた（P1*）。
4. 失敗が一つのansatzに限られ、次の試行をどこへ向けるべきかという知見が残りにくかった。

設計条件はcomment.mdの指定に従う。簡単な数学的障害を重い計算より先に調べる。既知法への還元を早期に確認する。
有望な高リスク仮説を、未証明という理由だけで排除しない。一方、具体的な生成規則がないまま探索を繰り返さない。
個別ansatzの失敗を研究分野全体の不可能性へ拡張しない。研究を続けるためだけの追加検証を作らない。
科学計算を提案するときは、それで変わり得る判断を明示する。形式的なレビュー段階を増やすことは目的にしない。

## 2. 用語

| 用語 | 定義 |
|---|---|
| アイデア | 生成規則をまだ書けない発想。記録はするが、研究候補として検証作業を割り当てない。 |
| 研究候補 | §4の課題定義・baseline・生成規則の記録を持ち、Gate Aの判断対象となるもの。 |
| 生成規則 R | 入力（Hamiltonian係数、許可primitive、許可された古典前処理）から、量子操作の列又は族を決める明示的な手続き。「ある恒等式が成り立つ」「ある表現が存在する」だけではRではない。 |
| 隠れ情報 | Rの実行に必要だが入力にない量。固有値、固有vector、Bethe roots、状態振幅、spectral projector、overlap、符号、gapなど。 |
| 等アクセスbaseline | 同じ入力・同じ許可操作で同じ目標出力を与える既知構成。最も強いものと、最も単純なもの（例：単独閉路＋対称PF）の両方を指す。 |
| 価値軸 | baselineとの差を評価する軸。資源（gate数、depth、ancilla、試行回数）、誤差構造、保証の形、適用範囲、必要情報。 |

### 2.1 成果型

候補は、最初に目指す成果型を宣言する。成果型は新規性の正式認定ではなく、何を示せば成果になり得るかの事前宣言である。

| 型 | 内容 | 独立した成果にならない例 |
|---|---|---|
| O1 | 新しい操作生成規則（新primitive、新しいcell文法、新しい情報取得規則） | 既知の規則の言い換え、名前の付け替え |
| O2 | 既知部品の新しい組合せ規則で、等アクセスbaselineに対し証明可能な資源・誤差構造の差を持つもの | 単なるgate連結、parameter調整、compile設定の変更 |
| O3 | 既存手法に対するより強い数学的保証（誤差界、成功確率、精度依存性、適用条件） | 経験的fitを保証と呼ぶこと |
| O4 | 構造を持つHamiltonian classに限定したアルゴリズム・保証 | 特殊模型の結果を一般分子の結果と書くこと |
| O5 | 構成classの特徴付け、又は一般化した障害（no-go）定理 | 一つのansatzの失敗をclass全体の否定と書くこと |

O5は独立した数学的成果になり得るが、新アルゴリズムではない。O2・O3を独立成果として扱うかはGPT／ユーザーの判断事項である（[handoff](research_strategy_handoff.md) §4）。

### 2.2 既知法への還元の水準

| 水準 | 意味 | 扱い |
|---|---|---|
| R0 表現の言い換え | 同じ操作を別の記号・別分野の用語で書いただけ | 独立性なし |
| R1 生成の同値 | 構成の操作列が、恒等変形で既知の操作列（echo、Strang、CG、TDCC等）に一致する | 独立性なし |
| R2 出力の同値 | 同じ演算子・状態を作るが、生成の手続きは異なる | 価値軸で差がある場合に限りO1／O2の候補 |
| R3 部分還元 | 一部の部品だけが既知 | 既知部分を除いた残りを明示し、その残りで再判定 |

J1の20-pulse cellはR1（完成gateの汎用echoへのexactな書換え）、J1のG2はR1（既知rectangleの対称PF分割）、二電子補助衝突はR1（total spinの関数としてCG／Paldus＋3値phase）、NBはR1（生成の中核がTDCC）にあたる。
いずれも原記録に根拠がある（[J1 20-pulse][E5-20handoff]、[J1最終探索][E5-finalhandoff]、[衝突][E7-handoff]、[NA/NB][E6-handoff]）。

## 3. 全体の流れ

```text
Stage 0 課題定義 ─ Stage 1 baseline ─ Stage 2 差分と成果型 ─ Stage 3 生成規則と情報予算 ─ Stage 4 早期screening
                                                                                          │
                                                                              Gate A（GPT）：候補として保持するか
                                                                                          │
                                   Stage 5 最小命題の紙上判定 ─ Stage 6 障害の一般化と脱出条件（失敗時）
                                                                                          │
                                                                              Gate B（GPT）：継続・一時保留・終了
                                                                                          │
                                   Stage 7 一般化補題・計算量・誤差・D2接続 ─ Stage 8 計算契約案（必要時のみ）
                                                                                          │
                                                                    Gate C（GPT／ユーザー）：正式採択・計算承認
```

Codex側は、Stage 0～4、Stage 5～6、Stage 7～8をそれぞれ一つの作業単位として、途中でSTOPせずに実施できる形を提案する。
GPTの判断点はGate A・B・Cの三つに集約する。過去の系列では、紙上の小さな一段ごとにhandoffとSTOPが入った（例：J1はdd36794→c7d3f07→143f50d→95be623の4段）。
一つの作業単位をどこまで事前承認するかは、GPT／ユーザーが決める。

## 4. 各段階の内容

### Stage 0：課題定義（task card）

| 項目 | 記載すること |
|---|---|
| 科学的問題 | 何を可能にするか。時間発展か、絶対E0推定か、その部分課題か。 |
| 入力 | Hamiltonian表現（係数、因子分解、sector）、精度ε、許可された古典前処理。 |
| 許可操作 | gate model primitive、測定、ancilla、外部bus等。D1との関係を明記する。 |
| 目標出力 | unitary、isometry、状態準備、block diagonalization、推定値のどれか。全入力に対するcoherentな作用か、特定状態への作用か。 |
| D2との接続 | scalar、一体項、残余相互作用、sector、位相、state overlap・準備のうち、どれを扱い、どれを後段に残すか。 |
| 費用の指標 | 何を数えるか（gate数、depth、試行回数、総時間、古典費用）。 |

### Stage 1：baseline（baseline card）

- 同じtask cardでの最強の既知構成と、最も単純な既知構成を記録する。費用式、仮定、必要情報も書く。
- 最も単純な構成の例：単独factorの閉路と対称PF（[P1*の比較構成][E4-cubic] §6）、完成gateの共役によるecho（[J1][E5-20handoff]）、Schur／CG変換（[衝突][E7-handoff]）、TDCC（[NB][E6-handoff]）、既知のjoint測定（[X2][E1-handoff]）。
- 過去の系列の既知法対応表と一次文献を、[横断分析](research_exploration_retrospective.md) §6.3の「既知構成の一覧」として再利用する。障害の補題（同§6.1）も、screeningの道具として引き継ぐ。
- 内部の既存記録（両repositoryの過去のK0、監査、停止系列）とも照合する。PR側の仮説H1の式(1)～(3)は、SOS-PF K0と一体再配分の事前監査に既にあった（[PR K0][PR-k0]）。閉じた系列の閉鎖単位（「現固定構成」「現定義」等）も確認し、停止系列の改名による再開にならないようにする（[横断分析](research_exploration_retrospective.md) §2.2）。
- 「未解決」の根拠は、文献が未解決・未閉鎖と明示している記述、又は既知の下界・上界の隔たりに置く。「調べた文献の範囲で同じ構成が見つからない」ことだけを未解決性の根拠にしない。Q1の未解決性は、11文献の範囲でその契約を満たす構成が見つからないことに依っており、難しさが外部の基準で校正されていなかった（[研究問題][E9-problem]、[未解決問題調査][E9-survey]）。

### Stage 2：差分と成果型（gap card）

- baselineが失っている資源・情報・保証を、費用式の項や保証の形として特定する。
- 成果型（O1～O5）と価値軸を宣言する。機構が新しいことだけでは足りず、価値軸の差を少なくとも仮説として書く。
- 一般化に失敗した場合に残り得る限定成果（O4、O5等）を書く。
- 次の判定で変わる判断を表にする（合格なら何をし、不合格なら何をしないか）。

### Stage 3：生成規則と情報予算（rule card）

- 生成規則Rを、入力・操作・出力・共通label更新・返却するworkまで書く。証明は不要だが、手で一例へ代入できる具体性を要する。
- ansatz（word、cell、文法）は、仮説の機構から導いた理由を書く。機構と無関係に固定したansatzは、成否が機構について情報を持たない（P1*の固定wordの例。[3次障害][E4-cubic] §7）。
- Rの実行に必要な量を全部列挙し、それぞれの取得方法と費用を書く。隠れ情報が残る場合は、その取得問題を含めて課題を再定義するか、条件付き（例：O4）として明示する。
- 生成子の係数依存性の型を記録する。局所型（係数で重み付けした局所的な生成子の積）、対称型（係数に依存しない、対称性で決まる生成子）、spectral型（係数に依存し、固有問題の解を要する生成子）のどれに当たるか、又はどれにも当たらないか。過去の構成は、局所型は既知のPF・交換子合成・echo、対称型はSchur／CG、spectral型は隠れ情報の要求に行き着いた（[方法論の分析](exploration_methodology_analysis.md) RC9）。どれかに当たる場合、その型の既知の道具と何が違うかをStage 4で確認する。
- 書けない場合は、アイデアとして記録して止める。Rを書くための作業を別途行う場合は、その作業自体に範囲と回数の上限を付ける（§8）。

### Stage 4：早期screening（紙上、最小例）

§5のS1～S8を、計算・詳細導出より先に、この順序で行う。各testは判定の種類（成立性か独立性か）を区別して記録する。
Stage 0～3の記録に、既に還元の手掛かり（「likely known」等）や欠落操作が書かれている場合は、その項目を最初に判定する。過去のP1～P8では、文献検索の前の記録に8件中6件の結論の芽が書かれていた（[P1～P8 provenance][E2-prov]）。

### Gate A：候補として保持するか

Codex側は、Stage 0～4の記録と、S1～S8の結果（合格・不合格・判定不能）を渡す。GPTは研究価値と独立性の見込みを判断する。
保持は正式採択ではない。保持の条件は§6の「仮説保持」の列による。

### Stage 5：最小命題の紙上判定

- 命題は、成功と失敗のどちらの結果でも次の判断が変わるものにする。固定ansatz一つの成否より、族（family）に対する命題を優先する。
- 成功・失敗の判定基準を、導出の前に固定する。結果を見てから次数、box、sector、targetを変えない。
- 最小の非自明例は手で追える大きさにする。full Fockの恒等式を判定するときも、N=1などの低次sectorを必要条件として先に確認する（S2）。

### Stage 6：障害の一般化と脱出条件（失敗時）

- 障害が出たら、その障害が成り立つ構成のclass（どの仮定を使ったか）を書く。例：「一体factor×線形busの三重Lie語では、bus三次の最高次係数は一体の入れ子交換子になり、N=1で非零ならCARの二体零関係では消せない」（[J1最終探索][E5-finalhandoff]）。
- そのclassから外れるために次の文法が満たすべき条件（脱出条件）を書く。J1とQ1の再開条件は、この形の条件として既に記録されている（[J1保留][E5-pause]、[Q1保留][E9-pause]）。
- 次の文法は、記録済みの全障害の脱出条件を満たす場合に限って試す。満たす文法を書けない場合は、Gate Bで一時保留を提案する。

### Gate B：継続・一時保留・終了

§7の条件で判断する。一時保留では、再開条件を「何が提示されれば再開を判断するか」という形で書く。

### Stage 7：一般化補題

一般の大きさへの拡張、計算量、有限精度、誤差、D2の全項目（scalar、一体項、残余相互作用、sector、位相、state準備・overlap）との接続を補題として列挙し、証明計画を作る。
ここで初めて、全入力unitary、有限精度保証、多項式費用、絶対E0までの道筋を要求する。

### Stage 8：計算契約案（必要な場合のみ）

§9の条件を満たす場合だけ、実行契約の案を作る。実行はGate Cの承認後に別作業として行う。

### Gate C：正式採択・計算承認

正式採択の条件は§6の「正式採択」の列による。新規性の判断、計算の承認、研究方針への組込みはGPT／ユーザーが行う。

## 5. 早期screening battery（S1～S8）

| test | 内容 | 判定の種類 | 不合格時 | 動機となった過去の事例 |
|---|---|---|---|---|
| S1 情報予算 | Stage 3で列挙した量が、入力・効率的な古典前処理・明示したsubroutineで得られるか | 成立性（隠れoracleの有無） | 課題を再定義するか、条件付き候補として明示 | NBのchart移送は未知振幅を要した[E6-handoff]。Q1のY・Bはchild spectrum情報なしでは定義できなかった[E9-pause]。P8は原点と符号を保つ転送操作が未定義[E2-handoff] |
| S2 最小sector・低次 | 最小の非自明sector（N=1、4 modes、L=4・m=2等）で、1～3次又はそれに相当する最小条件を手で展開する | 成立性 | 族の命題として障害を一般化（Stage 6） | P1*固定wordはN=1の3次で全実振幅について不成立[E4-cubic]。J1のG1は一体入れ子交換子がN=1で非零[E5-finalhandoff] |
| S3 対称性 | 目的の作用が大きな群（同時軌道回転、粒子置換等）と可換なら、保存量（total spin等）の関数としてSchur／CG等の既知変換へ書けないか | 独立性 | R1還元として記録。残りがあれば再判定 | 二電子補助衝突はtotal spinの関数で、CG／Paldus＋3値phaseへ還元[E7-handoff] [E8-handoff] |
| S4 完成block分解 | 構成を、単独で目標を完成させるblock（既知gate）とその共役・積に書き換えられるか | 独立性 | 汎用echo・PF・Strangへの還元（R1） | J1 20-pulseは(VBV⁻¹)(V⁻¹BV)へexactに書換え[E5-20handoff]。J1のG2は既知rectangleの対称PF分割[E5-finalhandoff] |
| S5 等アクセスbaseline | 最も単純な既知構成が同じ目標を何次まで、どの費用で達成するか。新構成が価値軸で何を改善するかを書けるか | 独立性と価値 | 価値軸の差を書けなければGate Aで不保持を提案 | P1*では単独閉路＋対称Strang積が形式4次を満たした[E4-cubic] |
| S6 構造の同定 | 代数構造（nilpotent、可換、Lie代数の型、可積分性、Riccati・Sylvester型）を既知の枠組みと照合する | 独立性 | 還元の水準（R0～R3）を記録 | NBはCC／TDCC[E6-handoff]。Q1の書換え可能部分はSylvester逆・不変部分空間・block diagonalization・Bethe/F-basis[E9-richandoff] |
| S7 作用の種類 | 必要なのが全入力に対するcoherentなunitaryか、isometryか、状態ごとの準備か、block diagonalizationかを確定する。非unitaryな写像を混入させない | 成立性 | Stage 0の目標出力を修正 | 二電子の抽出→SWAP→逆抽出は反対称空間でunitaryにならない[E7-handoff]。Q1は共通unitary Bと個別の対角化を区別した[E9-inshandoff] |
| S8 要件と障害の同根性 | 既知法を避けるために課した要件（例：非一様性、未完了のleg）が、試そうとする自然な文法を壊さないか。壊すなら、その要件の性質を直接扱う手段を最初の命題にする | 成立性と独立性 | 最小命題（Stage 5）を作り直す | J1は完成rectangleなら既知echo、未完了legなら一体Lieの3次障害、対称化ならCAR不要という境界に当たった[E5-finalmath]。Q1の文法G・G_Fの障害は、Q1が要件にした準位の非一様性から生じた[E9-insobs] [E9-prior] |

S1～S8はどれも、過去の事例では手で追える紙上の確認で決着した。計算機による科学計算を必要としない。
S3～S6の「独立性」の判定は還元の候補を示すまでであり、還元が実質的に完全か（R1かR3か）の最終判断はGPTが行う（§10）。
独立性の判定は、形式表示ではなく、操作列又はunitaryの不変量で行う。J1の「比較代数で非零・CARで零」という診断は、full Fockで等しいblockへの置換で結果が変わり、十分条件にならなかった[E5-20handoff]。

## 6. 判定基準：段階と水準

comment.md §7の10項目を、どの段階で、どの水準まで確認するかとして定義する。「仮説保持」はGate Aで候補として残す最低条件、「正式採択」はGate Cで研究成果の候補として採る条件である。
候補の選定時に証明が完了している必要はない。

| # | 基準 | 適用段階 | 仮説保持（Gate A） | 正式採択（Gate C） |
|---|---|---|---|---|
| 1 | 科学的問題が明確か | Stage 0 | task cardの全項目が埋まっている | GPT／ユーザーが課題として承認している |
| 2 | 入力・許可操作・目標出力が定義されているか | Stage 0、S7 | 定義があり、作用の種類（unitary等）が確定している | D1・D2との整合を含めて確定している |
| 3 | 新しく必要になる数学的構成が具体的か | Stage 3 | 生成規則Rが一例へ代入できる形で書かれている（未証明でよい） | Rの正しさが最小例で示され、一般化補題の証明計画がある |
| 4 | 強い既知baselineを確認しているか | Stage 1、S5 | 最強の既知構成と最も単純な既知構成が記録されている | 等アクセスで、全費用を戻した比較が完了している |
| 5 | 新規性を判断する具体的な差分があるか | Stage 2、S3～S6 | 価値軸の差が仮説として書かれ、S3～S6でR0・R1還元が見つかっていない | 差分が導出又は証明で確認され、GPTが独立性を判断している |
| 6 | 最小の数学的検証が可能か | Stage 5 | 成功・失敗基準を固定した最小命題がある | 最小命題が肯定的に解決している |
| 7 | 必要なoracleや情報取得費を隠していないか | Stage 3、S1 | 必要な量が全部列挙され、隠れ情報は明示されている | 全取得費が計上されている（条件付き成果ならその条件が成果の範囲として明記されている） |
| 8 | 一般化できなくても独立した限定成果があり得るか | Stage 2 | 限定成果の型（O4、O5等）が書かれている | 限定成果としての価値をGPTが判断している |
| 9 | 次の検証でどの判断が変わるか | 全段階 | 次段階の判定表がある | 計算を伴う場合、§9の条件を満たす |
| 10 | 継続・保留・終了の判断条件が明確か | Stage 2、Stage 6 | 族の試行上限と停止規則がある | 一時保留・終了時の再開条件の書式がある |

「仮説保持」の条件を満たさない場合でも、それだけで発想の価値を否定しない。不足項目を明記してアイデアとして記録する。

### 6.1 PR側で示された事前条件との対応

PR側のGPTレビューは、次の新候補を判定する事前条件として7項目を挙げていた（[PR M再評価][PR-mreview] §7.3）。本書の基準はそれを置き換えるものではなく、段階と水準を付けて運用するためのものである。

| PR側の事前条件 | 本書での対応 |
|---|---|
| 1 改善レバー | Stage 2（gap card、価値軸）、基準5 |
| 2 具体的生成写像 | Stage 3（rule card）、基準3 |
| 3 同じ合法情報・価格の強対照 | Stage 1（baseline card）、S5、基準4 |
| 4 情報モデルの明示 | Stage 3の情報予算、S1、基準7 |
| 5 スケールへの機構 | Stage 3（Rの一般の大きさへの延長を仮説として書く）、Stage 7（証明計画）、基準8 |
| 6 native／FT費用の経路 | Stage 0の費用の指標、Stage 2の価値軸、Stage 7 |
| 7 明示的なSTOP条件 | Stage 2の判定表、§7、基準10 |

本書で加えたのは、S2～S4・S6～S8の紙上screening、係数依存性の型、成果型O1～O5、還元の水準R0～R3、障害の一般化と脱出条件、試行上限、Gate A～Cである。

## 7. 次段階へ進む条件、一時保留・終了の条件

### 7.1 進む条件

| gate | 進む条件 |
|---|---|
| Gate A → Stage 5 | §6の仮説保持の全条件。S1～S8に「判定不能」が残る場合は、その項目を最小命題に含める。 |
| Gate B → Stage 7 | 最小命題が肯定的に解決し、その結果がS3～S6の還元に当たらない。 |
| Gate C → 正式採択・計算 | §6の正式採択の全条件。計算を伴う場合は§9の条件。 |

### 7.2 一時保留の条件

- Stage 6で、記録済みの全障害の脱出条件を満たす文法を一つも書けない。
- 族の試行上限に達した。上限はGPTが設定する。過去のJ1（20-pulse、G1、G2）とQ1（G、G_F、G_S）では、各3文法で保留の判断材料が揃った。
- 一時保留では、再開を判断する条件を、提示されるべき規則の性質として書く（J1・Q1の記録と同じ書式）。

### 7.3 終了の条件

- 候補全体がR0又はR1の還元に当たると確認された。
- 必要な隠れ情報の取得が、元の問題（例えば絶対E0そのもの）を解くことと同等であると示された。
- task cardがD2に照らして不適切だと判明し、修正しても元の量子化学問題との関係が残らない。

### 7.4 してはいけない判断

- 未証明、高リスク、資源優位が未確立という理由だけで候補を落とすこと。
- 一つのansatz・文法の失敗を、族全体・分野全体の不可能性として記録すること。
- 研究を続けることだけを目的に、次の判断を変えない追加検証を作ること。
- 結果を見てから次数、box、sector、target、閾値を変えて救済すること。

## 8. 試行回数の管理

- 生成規則を書くための作業（Stage 3）と、文法の試行（Stage 5～6）には、作業単位ごとの上限を付ける。上限はGPTが設定する。
- 新しい文法は、記録済みの障害の脱出条件をすべて満たすことを事前に示した場合に限って試す。満たさない文法を「念のため」試さない。
- 同じ族を別の名前・別の枠組み（例：cross-domain、obstacle、open problem）で始め直すときは、既存の障害記録と既知構成の一覧を引き継ぎ、新しい枠組みで何が変わるかを最初に書く。

## 9. 科学計算を提案する条件

次の全てを満たす場合に限り、Codex側は計算契約の案を作る。実行は別の明示承認による。

1. 紙上の判定（S1～S8、最小命題、障害の一般化）で決着しない具体的な問いがある。
2. 計算結果のどの値が、Gate B又はCのどの判断をどう変えるかを、事前に表で示せる。
3. 等アクセスbaselineと比較条件が固定されている。
4. 否定的な結果が出た場合に、族の否定か特定ansatzの否定かを事前に区別できる。
5. 計算対象、入力、精度、truth access、出力、停止点を持ち、`AGENTS.md`の計算性能方針に従う資源設定を持つ。

P1*では、固定box内の4次条件438本に対するexact solverのUNSATが得られた後、紙上導出で、全実振幅について3次で既に不成立であることが示された（[実行報告][E3-report]、[3次障害][E4-cubic]）。
紙上導出の方が強く、障害の機構も説明した。この事例を、条件1と2を課す理由とする。

### 9.1 紙上の最小例の手計算の扱い（提案）

P1*の発想段階と契約段階では、新しい係数・正規形・方程式・証明・反例の紙上作成が承認範囲の外にあった（[P1～P8 provenance][E2-prov]、[P1*契約 provenance][E3-prov]）。そのため、紙上の低次事前解析という工程が抜けた。
次の区別を、今後の作業指示の承認範囲に入れることをGPT／ユーザーへ提案する。

| 区分 | 内容 | 扱いの提案 |
|---|---|---|
| 紙上のscreening | 承認済みの候補について、最小の非自明例でS1～S8を手で確認する。数行から数頁の導出で、計算機による科学計算・記号計算プログラムを使わない | 候補を検討する作業の承認に含める |
| 最小命題の紙上判定 | Stage 5の命題の導出 | Gate Aの後、範囲を指定して承認 |
| 計算機による科学計算 | solver、数値対角化、記号計算プログラム、simulation | §9の条件で、別の明示承認 |

この表は提案であり、採用されるまで既存の承認の扱いを変えない。

## 10. CodexとGPTの役割分担

| 作業 | 担当 | 境界 |
|---|---|---|
| task card・baseline card・gap card・rule cardの起草、文献・既存記録からの情報整理 | Codex側 | 研究価値の判断はしない |
| S1～S8の機械的な確認（小例の手計算、対称性の確認、block分解の書換え、既知構成との照合） | Codex側 | 還元の候補と根拠を示す。還元が実質的に完全かの最終判断はしない |
| 最小命題の紙上導出、障害記録と否定範囲の明記、脱出条件の起草 | Codex側 | 承認された命題の範囲に限る |
| provenance、identity照合、GitHub handoff | Codex側 | 既存規約に従う |
| 課題の研究価値、成果型の受入れ、独立性・新規性の判断、還元の完全性の判断 | GPT | Codexが代行しない |
| Gate A・B・Cの判断、試行上限の設定、一時保留・終了・再開の判断 | GPT／ユーザー | 正式状態の記録はユーザーの明示承認後 |
| D1・D2の解釈や変更、新しいaccess modelを研究対象に含めるか | GPT／ユーザー | Codexは選択肢と根拠を示すだけ |
| 科学計算の承認 | ユーザー（GPTの判断を受けて） | §9の条件を満たす契約案に対して |

Codex側だけで実行できる技術検証は、定義済みの命題に対する紙上の導出・照合と、既存資料の整理である。
どの命題を検証する価値があるか、結果が研究成果になるかは、GPTの科学的判断である。

## 11. 記録の書式

各候補の記録には、次を含める。

1. task card、baseline card、gap card、rule card（§4）。
2. S1～S8の結果。各testについて、成立性・独立性のどちらの判定か、根拠、判定不能の理由。
3. 最小命題、事前に固定した成功・失敗基準、結果。
4. 障害の記録。否定した範囲と否定していない範囲を必ず分けて書く。
5. 脱出条件と、次の試行がそれを満たすことの説明。
6. 次の判断表と、Gate A・B・Cでの判断の記録（判断者と日時）。
7. 候補・文法・障害のIDには、repositoryと系列名を前置する（例：`EVAL-Q1-G_F`）。過去の資料では、C1、D1/D2、H1等が別の意味で重複して使われ、資料自身が警告している（[PR探索範囲表][PR-coverage]）。

## 12. 過去の事例への当てはめ（参考）

過去の正式判断を再審査するものではない。各testを先に行っていた場合に、どの時点で何が分かった可能性があるかを示す。

| 事例 | 実際に判明した時点 | 先に分かった可能性がある段階 |
|---|---|---|
| P1*固定wordの3次障害 | solverのUNSATの後、GPTレビューと紙上検証（5110d34） | Stage 4のS2（N=1、3次までの手計算） |
| P1*の比較構成（単独閉路＋Strang） | 同上 | Stage 1・S5（最も単純な既知構成の確認） |
| J1 20-pulseのecho還元 | 構成した同じ作業内（c7d3f07） | Stage 4のS4（完成block分解） |
| J1 G2の既知rectangle還元 | 構成した同じ作業内（143f50d） | Stage 4のS4・S5 |
| 二電子補助衝突のCG／Paldus還元 | 操作仕様を作った同じ作業内（b5c4932） | Stage 4のS3（同時軌道回転に対する不変性） |
| NBのTDCC還元 | 同じ作業内（813fd44） | Stage 4のS6 |
| Q1のchild spectrum依存 | 挿入則とRiccatiの紙上検討（2a3e689、d33fc8b） | Stage 3・S1（情報予算） |
| Q1の非一様性と文法G・G_Fの衝突 | 同上 | Stage 4のS8（要件と障害の同根性） |
| J1の挟み撃ち（echo還元と一体Lieの3次障害） | 最終限定探索（143f50d） | Stage 4のS8と、bus次数の補題（S2） |
| P1～P8の還元先と欠落操作 | 文献照合（67d9e3b） | 文献検索の前の記録の段階（Stage 4の冒頭） |

この表の「可能性」はCodex側の分析であり、各事例を当時の手順で発見できたかどうかの断定ではない。

<!-- fixed-source-references -->

[E1-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/research_decision_handoff.md
[E2-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/research_hypothesis_handoff.md
[E2-prov]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/provenance.json
[E3-prov]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/provenance.json
[E3-report]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/scientific_execution_report.md
[E4-cubic]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5110d347e1f032c9093430b3def13b3391602cdd/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md
[E5-20handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c7d3f077d634e4165b7cd326bac7caa1ae04ff66/docs/research_exploration/p1star_j1_paper_feasibility_20261017/decision_handoff.md
[E5-finalhandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/143f50d3bf2636b1433d9b70a844bbdc22832a6e/docs/research_exploration/p1star_j1_final_limited_search_20261017/research_decision_handoff.md
[E5-finalmath]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/143f50d3bf2636b1433d9b70a844bbdc22832a6e/docs/research_exploration/p1star_j1_final_limited_search_20261017/limited_construction_record.md
[E5-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/95be62395d3740db39b6830c68f4fd1e25f595ee/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[E6-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/813fd44bfd70f9bc4266e35cc8e4dd28037dedce/docs/research_exploration/independent_construction_principles_20261017/research_hypothesis_handoff.md
[E7-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5c49323957f1bfa2a24cb2786a0ebd1f3932925/docs/research_exploration/bottleneck_operation_design_20261017/decision_handoff.md
[E8-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c23e9bc6028c52761e6220b91e2d1e1bd8b3ceaf/docs/research_exploration/pair_collision_cg_verification_20261017/verification_handoff.md
[E9-inshandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/verification_handoff.md
[E9-insobs]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/insertion_obstruction_and_checks.md
[E9-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17cf4073094c713257d6eabadb440d6d973a9229/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
[E9-prior]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/prior_art_comparison.md
[E9-problem]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/research_problem.md
[E9-richandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/decision_handoff.md
[E9-survey]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/unresolved_problem_survey.md
[PR-coverage]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_coverage_map.md
[PR-k0]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/0d460c54f3bf54ea46d4d8129f6702703c4bb217/docs/research/qc_new_algorithm_static_screen_k0_20261016/technical_report.md
[PR-mreview]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/docs/reviews/quantum_chemistry_pf/qc_m_k0_claude_scientific_rereview_and_direction_20261015.md
