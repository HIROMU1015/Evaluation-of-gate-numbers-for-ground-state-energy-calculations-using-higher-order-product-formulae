# 今後の研究戦略の比較と推奨

2026-10-17 JST。作成：Claude Code（Codex側の技術調査・資料作成の役割）。
**本書は研究戦略の比較と推奨であり、新しいアルゴリズム候補の構成探索ではない。推奨した戦略の正式採択はGPT／ユーザーが判断する。**
根拠のない数値scoreや成功確率は作らない。評価は過去の具体的な結果に基づく定性的な記述に限る。
過去研究の正式状態（J1、Q1を含む）は変更しない。D1・D2を維持する。

## 1. 比較の前提

[横断分析](research_exploration_retrospective.md)と[方法論の分析](exploration_methodology_analysis.md)から、次の事実を前提にする。

| 前提 | 内容 | 根拠 |
|---|---|---|
| F1 | 9系列（E1～E9）で、独立した構成仮説として最終保持されたものは0件。J1とQ1は追加探索の一時保留 | [J1保留][E5-pause]、[Q1保留][E9-pause] |
| F2 | 終わり方は2種類。限定文法の低次障害（P1*固定word、J1のG1、Q1のG・G_F・G_S）と、既知の生成規則への還元（Strang、echo、CG／Paldus、TDCC、既知joint測定、Sylvester等） | 方法論の分析 §1 |
| F3 | 毎回不足したのは、係数と許可操作から作用を作る生成規則、又は隠れ情報なしの取得法 | 方法論の分析 RC1・RC2 |
| F4 | 価値軸（資源・保証）は発想段階で要求されず、新規性は機構の同一性で判定された | 方法論の分析 RC5 |
| F5 | D1の範囲で主に使える構成はPF系、測定・推定protocol、追加accessとしての外部bus等。新しい制御accessを研究対象に含めるかはGPTの判断事項 | [P1～P8][E2-handoff] |
| F6 | 決め手は全て紙上の短い確認で、計算機による科学計算を要しなかった | 方法論の分析 §1 |
| F7 | PR側の新アルゴリズム仮説H1～H4の静的K0も、総合技術判定`NO_GO_NO_INDEPENDENT_GENERATION_RULE`で終わっていた | [PR範囲整理][PR-transition] |
| F8 | 候補は毎回、既知法との差分（既知論文の対象外の記述、自分の研究の障害、「調べた文献に無い」契約）として作られた | 方法論の分析 RC8 |
| F9 | 過去の構成は、生成子の係数依存性で局所型・対称型・spectral型に分かれ、それぞれ既知のPF系の道具、Schur／CG、隠れ情報の要求に行き着いた | 方法論の分析 RC9 |

## 2. 評価軸

comment.md §5の8軸を使う。各軸で、過去の結果から何が言えるかを書く。

1. 独立した新成果につながる可能性
2. 最初に検証できる数学的命題の明確さ
3. 先行研究との差分を判別する容易さ
4. 新しい操作生成規則を構成する余地
5. 既存研究資産の活用可能性
6. 研究の拡張可能性
7. 実装・数値検証へ進む際の前提条件
8. 元の量子化学問題との関連性

## 3. 戦略A：未解決の数学的命題を起点にする

**内容**：既知アルゴリズムの到達点から、未解決の構成補題や計算量上の問題を特定し、それを研究課題にする。

**過去の実施例**：Q1。一次文献11件と著者公開sourceを調べ、inhomogeneousなRichardson–Gaudin pairing familyで、係数だけから全入力coherentな基底変換を、指数個のstate・root setを列挙せずに生成する構成を課題とした[E9-handoff]。
最小例（L=4・m=2）の挿入則は、独立2次元channel文法で不成立となり、親Fは既知法へ限定的に還元された[E9-inshandoff]。
Riccati文法では、Fと可換なYが矛盾し、固定Sylvester逆がγ=√2で特異になった[E9-richandoff]。追加探索は一時保留となった[E9-pause]。

| 項目 | 内容 |
|---|---|
| 利点 | 命題が明確で、先行研究の到達点が文献に書かれているため差分を判別しやすい。解ければ独立した数学的成果になる（成果型O1・O3） |
| 失敗しやすい点 | 未解決である理由が「本質的に難しいから」である命題を選びやすい。Q1では、最小例が既に核心（共通unitary B）を含み、部分的な成果が残りにくかった。必要な情報（child spectrum）が隠れoracleに当たるかを、選定の後に調べた。Q1の「未解決」は、文献が明示する未閉鎖の命題ではなく、11文献の範囲で契約を満たす構成が見つからないことに依っていた[E9-survey]。既知のCG／Schur経路を避けるために課した非一様性が、試した文法の障害そのものになった（方法論の分析 RC6） |
| 適した対象問題 | 文献で明示的に未解決とされ、補題の大きさで、隠れ情報を要さず、最小例の成否が族の判断を変える命題 |
| 初期判定方法 | 情報予算（S1）を先に行う。最小例が核心の全てを要するか、部分的な補題に分けられるかを確認する。文献で「なぜ未解決か」の記述を読み、既知の困難（例：固有値問題を解くことと同等）に当たらないか確認する。独立性のために課す要件が自然な文法を壊さないか（S8）を確認する |

## 4. 戦略B：既存アルゴリズムの具体的障害を起点にする

**内容**：特定のHamiltonianや操作について、現在の方法がどこで計算資源や情報を失っているかを調べ、その制約を変える構成を探す。

**過去の実施例**：E1。第一・第二研究、PR Track A/B等の固定結果から5件の障害（O1～O5）を抽出し、X1（encoded wordの代表・parityの共同選択）とX2（energy向けjoint測定とcopy間の情報再利用）を一次文献と照合した。
X1は既知compilerを越える具体的選択器を提示できず、X2は既知の測定法へ帰着した。独立研究候補は0件だった[E1-handoff]。

**過去の実施で起点にした障害の性質【分析】**：O1～O5は、主に本プロジェクト自身のPF研究の結果から得た障害だった[E1-handoff]。
文献上で最も強い既知アルゴリズムの費用式・保証のどの項が改善の余地を持つかを起点にしたものではない。

**改良案B′**：起点を「最強の既知baselineの費用式・保証の、特定の項」に置く。等アクセスで全費用を戻したbaselineを最初に固定し、そのどの項を変えるかを命題にする。

**B′が、過去の「すき間探し」とどこが違うか**：E0のT1は既知論文の対象外の記述から作られ、E1の障害は本プロジェクト自身の過去の結果から作られた（方法論の分析 RC8）。どちらも、「そこが本当に費用・保証を決める項か」「文献上も開いているか」を確かめないまま差分を定義した。
B′では次の三つを、候補を作る前に満たす。

1. 対象の項が、等アクセスの最強baselineの**総費用又は保証の形を支配する**ことを、費用式で示す。
2. その項の改善余地が、文献の明示的な記述（未解決の記述、既知の下界・上界の隔たり、適用条件の限界）で裏付けられる。
3. その項を変える操作が、局所型・対称型・spectral型の既知の道具（方法論の分析 RC9）のどれで既に変えられていないかを確認する。

| 項目 | 内容 |
|---|---|
| 利点 | baselineを最初に固定するため、既知法への還元（RC3）を最初の段階で確認できる。改善対象が費用の項として定量的に書けるため、価値軸（RC5）が自然に決まる。第一研究のPF有限時間モデル、第二研究の予算安全性、PR Track A/Bの部分ランダム化、P1*・J1・Q1の障害補題などの資産を使える |
| 失敗しやすい点 | 単なる性能改善（parameter調整、compile設定、定数の改善）に留まる危険がある。過去のE1のように、自分の研究の障害を起点にすると、文献上の強いbaselineから離れる。対象の項が第一・第二研究やPR Track A/Bの担当範囲と重なる場合、停止系列の改名による再開にならないかを確認する必要がある（E1はO1～O3をこの理由で除外した[E1-map]） |
| 性能改善と独立成果の区別 | 独立成果とするには、費用の項のscalingや保証の形を変える新しい数学的言明（新しい生成規則O1、組合せ規則O2、保証O3）が要る。同じ手続きのparameter・compileの最適化は独立成果にしない |
| 適した対象問題 | D2の課題（絶対E0推定）又はその部分課題で、最強baselineの費用式が文献に明示され、その項の改善余地が文献上も指摘されているもの |
| 初期判定方法 | 等アクセスbaselineの費用式を書き、対象の項を一つ特定する。その項を変える構成が隠れ情報を要さないか（S1）、既知の別手法で既に変えられていないか（S5・S6）を確認する |

## 5. 戦略C：特殊なHamiltonian構造から新しい構成を探す

**内容**：対称性、保存量、低rank構造、局所性、可解部分空間、特殊な電子相関などを利用する。

**過去の実施例**：Q1は可積分なpairing模型（Richardson–Gaudin）を対象にした[E9-handoff]。二電子補助衝突では、作用がtotal spinの関数であることが、既知のCG／Paldus変換への還元の決め手になった[E7-handoff]。

| 項目 | 内容 |
|---|---|
| 利点 | 構造があると証明が可能になり、小例での判定も明確になる。spin、粒子数、sector、因子分解（DF）など、一般の分子にも存在する構造は、元の量子化学問題と直接つながる |
| 失敗しやすい点 | 構造が強いほど、既知の厳密な道具（表現論、Schur／CG、Bethe ansatz、F-basis）で説明が尽きやすい。過去の2例はどちらもこの形だった。係数に依存しない生成子は対称性で決まり既知の変換に落ち、係数に依存する生成子は固有問題の解を要した（方法論の分析 RC9）。可積分模型の結果を一般分子の結果と取り違える危険がある |
| 特殊模型の扱い | 一般化が未証明という理由だけでは排除しない。成果型O4として範囲を明記し、一般分子への適用は未確認として扱う |
| 適した対象問題 | 一般の分子Hにも存在する構造（対称性、低rank、sector構造）で、それを使うと最強baselineのどの費用項が変わるかを書けるもの |
| 初期判定方法 | 構造を使う作用が、その構造の既知の厳密な道具で書けるかを先に確認する（S3・S6）。書ける場合、残る差分が資源・保証にあるかを確認する |

## 6. 戦略D：異分野の新しい構成技法を導入する

**内容**：量子制御、数学的物理、数値解析、情報理論、代数的アルゴリズム等の構成技法を導入する。

**過去の実施例**：P1～P8は異分野の機構を起点に8件を整理し、P1*だけを保持した[E2-handoff]。P1*とJ1は量子制御のbus gateの技法を使い、既知のStrang・echo・rectangleへ還元されるか、低次で不成立だった[E4-cubic] [E5-finalhandoff]。
NAは群rotorの運動量、NBはnilpotentな対数とchartの貼合せを使い、NAは生成段階を構成できず、NBはTDCCへ還元された[E6-handoff]。

| 項目 | 内容 |
|---|---|
| 利点 | 既知のアルゴリズムの枠に無い発想を持ち込める。成立すれば新しい操作生成規則（O1）になり得る |
| 失敗しやすい点 | 過去の実施例の大半で、異分野の用語を入力・操作・出力へ翻訳すると、既知の量子アルゴリズムの部品に一致した。P1～P8では、文献検索の前の記録で、8件中6件に還元先又は欠落操作が既に書かれていた[E2-prov]。外部bus等の新しいaccessを要する場合、そのaccessを研究対象に含めるかという別の判断が要る |
| 表現の変更で終わらないための検証基準 | ①翻訳test：導入する技法を、task cardの入力・許可操作・出力で書き直す。②対応test：書き直した操作が、既知の量子アルゴリズムの部品（PF、交換子合成、echo・DCG、Schur／CG、CC／TDCC、既知測定）のどれに当たるかを確認する。③性質test：既知の部品が持たない性質（資源・誤差構造・情報取得）を一つ書く。この3つを候補保持の前に行う |
| 適した対象問題 | 戦略A又はB′で特定したgapを埋める道具の探索。発想の起点としてではなく、道具の供給源として使う |
| 初期判定方法 | 上の3testをプロトコルのStage 3・4の一部として行う |

## 7. 補助戦略E：既に得た障害を一般化する

**内容**：P1*の3次障害、J1の一体入れ子交換子の障害、Q1の交換子・Riccatiの障害を、構成のclassに対する補題として一般化する（成果型O5）。

| 項目 | 内容 |
|---|---|
| 利点 | 最初の命題が明確で、既存資産を直接使う。得た補題は、将来の候補のscreening（S2等）を強くする |
| 限界 | 新アルゴリズムそのものではない。独立成果としての価値は限定的な可能性がある |
| 注意 | J1・Q1の内容に関わるため、実施はJ1・Q1の再開ではないことを明記したうえで、GPT／ユーザーの明示判断を要する |

本書では補助戦略Eを主戦略として推奨しない。障害の一覧は、[横断分析](research_exploration_retrospective.md) §6.1に、screeningの道具として整理した。

## 8. 比較表

各欄は、過去の結果に基づく定性的な記述である。

| 評価軸 | A 未解決命題 | B′ 最強baselineの具体的gap | C 特殊構造 | D 異分野技法 |
|---|---|---|---|---|
| 1 独立成果の可能性 | 解ければ大きいが、Q1は最小例で核心に当たった | O1～O3の成果型を明示すれば判定できる。単なる性能改善に留まる危険あり | O4として限定的。過去2例は既知の厳密な道具へ還元 | 成立すればO1。過去の実施例は大半が還元 |
| 2 最初の命題の明確さ | 高い（文献に到達点がある） | 高い（費用式の項を指定できる） | 高い（小例が明確） | 低い（翻訳が先に要る） |
| 3 先行研究との差分の判別 | 文献の到達点と比べやすい | baselineを最初に固定するので最も判別しやすい | 構造の既知の道具との比較が要る | 用語の違いが判別を遅らせた |
| 4 新しい生成規則の余地 | 大きいが、隠れ情報の危険 | gapの性質による | 構造の道具の外に出る必要 | 大きいが、実績は還元が多い |
| 5 既存資産の活用 | Q1の挿入・Riccatiの知見 | PF有限時間モデル、予算安全性、Track A/B、障害補題 | spin・sector・DFの扱い、衝突の還元 | P1～P8、P1*・J1の制御代数 |
| 6 拡張可能性 | 命題による | 課題レベルで定義するため拡張しやすい | 一般化は未確認として扱う | 不明 |
| 7 実装・数値検証の前提 | 遠いことが多い | baselineの費用模型が比較の基準を与える | 小例は近い | 新しいaccessの物理的前提が要ることがある |
| 8 元の量子化学問題との関連 | 命題による（RG模型は一般の分子Hではない） | D2の課題から出発するため直接 | 一般分子にもある構造なら直接 | 導入する技法による |

## 9. 推奨

### 推奨1（主戦略）：B′ 最強baselineの具体的gapを起点にする

**推奨理由**

1. 過去の主因であるRC3（還元の後期発見）とRC5（価値軸の欠如）を、最初の段階で扱える。baselineを最初に固定し、変える項を指定するためである。
2. 生成規則の対象が「baselineのどの項を変える操作か」として具体的になり、RC1（規則の後回し）を減らせる。
3. 本プロジェクトの資産（PF有限時間モデル、予算安全性、PR Track A/Bの部分ランダム化、過去の障害補題）が、そのままbaselineの理解とgapの特定に使える。
4. D2の課題（絶対E0推定）から出発するため、元の量子化学問題との関連が保たれる。
5. この方向は、新アルゴリズム探索の前にPR側のGPTレビューが推奨した「先に強い比較対照・タスク・量子資源のレバーを選ぶ」「そのレバーに効く具体的な構成規則だけを候補にする」と一致する（[PR GPTレビュー][PR-gpt1016]、[PR M再評価][PR-mreview] §7.3）。E0～E9は、この推奨を候補作成前の固定手順としては実装しなかった（[横断分析](research_exploration_retrospective.md) §2.3）。B′は、それを[プロトコル](research_selection_and_validation_protocol.md)のgateとして実装する案である。

**この戦略の限界**：独立した「新構成原理」より、新しい組合せ規則や保証（O2・O3）に至る可能性が高いと考える【分析】。それを研究成果として認めるかは、GPT／ユーザーの判断事項である。

### 推奨2（補助戦略）：A′ gapを補題の大きさの未解決命題として定式化する

B′で特定したgapを、戦略Aの規律で数学的命題にする。Q1の経験から、次の条件を課す。

1. 文献で未解決とされる理由を確認し、既知の困難（例：固有値問題を解くことと同等）に当たらない。
2. 隠れ情報を要さない（S1を先に行う）。
3. 最小例の成否が族の判断を変え、失敗しても障害の一般化が残る。
4. 成果型（O1～O5）と、成功時に変わるbaselineの項が書ける。

B′とA′は一つの流れとして使う。B′が「何を変えるか」を決め、A′が「何を証明するか」を決める。C（特殊構造）とD（異分野技法）は、gapを埋める道具の供給源として、プロトコルのscreeningを通して使う。

### 推奨しない進め方

- task・baseline・gapを定めずに、新しい枠組みで発想を広く集め直すこと（P1～P8型の再実施）。過去と同じ失敗の型を繰り返す可能性が高い【分析】。
- J1・Q1の再開条件を満たす規則を探す作業を、正式な再開判断なしに始めること。
- 研究を続けることだけを目的とした追加検証。

### 未確認事項

1. D1・D2の下で、補題の大きさで、文献上未解決とされるgapが実際に存在するか。今回は文献の新規調査をしていないため未確認である。最初の作業（§10）で確認する。
2. O2・O3を独立成果として認めるか。GPT／ユーザーの判断が要る。
3. 外部bus等の新しいaccess modelを、探索の範囲に含めるか。GPT／ユーザーの判断が要る。
4. 推奨戦略でも成果が得られない可能性は残る。成功の見込みを数値では示さない。
5. PR側のClaudeレビューは、低energy構造による大きな既知利得がblock-encoding側にあると指摘した（[PR Claudeレビュー][PR-claude1016] §7.4）。D1の下でB′が支配的な費用項を変えられる余地がどれだけあるかは、T0の結果を見るまで分からない。

### 研究目的の設定に関する選択肢（GPT／ユーザー判断）

| 選択肢 | 内容 | 過去の記録との関係 |
|---|---|---|
| 目的を維持し、方法を変える | 「D1の範囲で元の電子Hに対する独立した新構成原理」を目的のまま、B′＋A′とプロトコルで進める | 本書の推奨 |
| 成果型を広げる | O2～O5を独立成果として扱う | 方法論の分析 RC5 |
| 探索するaccess modelの範囲を確認する | D1の下で、外部bus等の新しいaccessや、block-encoding法を対照として参照する範囲を決める | PR側のGPTレビューは、対照として参照することと新算法として採用することを分けた[PR-gpt1016] |
| 既存研究資産との優先順位を比べる | Track A/B、第一・第二研究の未完了部分の情報価値を、新テーマと比べる | PR側のGPTレビューが10-16に推奨していた[PR-gpt1016] |
| 新アルゴリズム研究を一時停止する | T0で補題の大きさのgapが見つからない場合の選択肢 | 前提にしない（comment.md §1） |

## 10. 最初の具体的作業（提案・未承認）

**T0：一つの課題に対する「最強baselineとgapの台帳」の作成**。静的な文献・既存記録の調査で、新規科学計算、新アルゴリズム候補の構成探索、正式採択を含まない。

| 項目 | 内容 |
|---|---|
| 対象課題 | GPT／ユーザーが1件選ぶ。推奨は、D2の課題「有限基底電子Hの絶対E0を、指定精度でD1の範囲で推定する」を端から端まで扱い、費用を部分課題（時間発展の1 step、step数、推定protocol、state準備・overlap）に分解すること |
| 成果物1 | task card（[プロトコル](research_selection_and_validation_protocol.md) Stage 0の書式） |
| 成果物2 | baseline card 3件以上：本プロジェクトの現行PF経路（第一研究の有限時間モデルを含む）、文献上最強のPF系経路、PR Track A/Bのランダム化経路、最も単純な既知経路。費用式、仮定、必要情報、証明済み部分と経験的部分を分ける |
| 成果物3 | 費用の分解と、baselineが資源・情報を失っている点の一覧（文献の版と箇所を付ける）。既存の台帳（第一・第二研究、PR Track A/B等）で確立している内容は再計算せず参照する |
| 成果物4 | gapの一覧。各gapについて、§4のB′の三条件（総費用・保証を支配する項であること、文献上の明示的な裏付け、既知の道具で既に変えられていないこと）、成果型、S1（情報予算）とS5（等アクセスbaseline）の紙上の事前確認、補題の雛形（成功・失敗基準）、変わる判断。第一・第二研究、PR Track A/B、PR側の停止系列と重なる場合は、その旨と、停止系列の再開に当たらない理由 |
| 成果物5 | GPTが選ぶための1～2件の推薦と理由。該当gapが無い場合は「補題の大きさのgapは見つからなかった」と報告する |
| 担当 | Codex側が作成し、GPTがgapを選ぶ（Gate A相当の判断）。ユーザーが範囲を承認する |
| 停止点 | 台帳の公開・照合で停止する。gapの選定、候補の構成、計算へ自動で進まない |
| 既存の推奨との対応 | PR側のGPTレビューが推奨した手順（研究目標と比較する量子資源の固定、有力な費用レバーの先行特定、レバーに効く構成規則だけを候補にする）の前半を、台帳として具体化したもの（[PR GPTレビュー][PR-gpt1016]） |

T0で補題の大きさのgapが一つも見つからない場合、その結果は、新アルゴリズム研究の継続の可否をGPT／ユーザーが判断する材料になる。継続も終了も、ここでは前提にしない。

<!-- fixed-source-references -->

[E1-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/research_decision_handoff.md
[E1-map]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/problem_and_failure_map.md
[E2-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/research_hypothesis_handoff.md
[E2-prov]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/provenance.json
[E4-cubic]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5110d347e1f032c9093430b3def13b3391602cdd/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md
[E5-finalhandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/143f50d3bf2636b1433d9b70a844bbdc22832a6e/docs/research_exploration/p1star_j1_final_limited_search_20261017/research_decision_handoff.md
[E5-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/95be62395d3740db39b6830c68f4fd1e25f595ee/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[E6-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/813fd44bfd70f9bc4266e35cc8e4dd28037dedce/docs/research_exploration/independent_construction_principles_20261017/research_hypothesis_handoff.md
[E7-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5c49323957f1bfa2a24cb2786a0ebd1f3932925/docs/research_exploration/bottleneck_operation_design_20261017/decision_handoff.md
[E9-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/research_handoff.md
[E9-inshandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/verification_handoff.md
[E9-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17cf4073094c713257d6eabadb440d6d973a9229/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
[E9-richandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/decision_handoff.md
[E9-survey]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/unresolved_problem_survey.md
[PR-claude1016]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dbe51f1870cd069b952cc92593833d355da10e28/docs/reviews/quantum_chemistry_pf/qc_sos_pf_post_k05_claude_scientific_review_20261016.md
[PR-gpt1016]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dbe51f1870cd069b952cc92593833d355da10e28/docs/reviews/quantum_chemistry_pf/qc_sos_pf_post_k05_gpt_scientific_review_20261016.md
[PR-mreview]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/docs/reviews/quantum_chemistry_pf/qc_m_k0_claude_scientific_rereview_and_direction_20261015.md
[PR-transition]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_state_transition.md
