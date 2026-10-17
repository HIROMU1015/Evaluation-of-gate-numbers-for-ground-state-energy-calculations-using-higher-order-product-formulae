# 新アルゴリズム探索の横断分析

2026-10-17 JST。作成：Claude Code（Codex側の技術調査・資料作成の役割）。
対象は、2026-10-16から10-17に行った「既存法と異なる新しいアルゴリズム構成原理」の探索である。
過去の研究成果・失敗・未解決事項を、固定commitのSOURCEから研究ごとに整理し、横断的に比べる。

**本書は過去の正式判断の再審査・変更ではない。** J1の`PAUSED_PENDING_NEW_MECHANISM`、Q1の`PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE`、
第一研究・第二研究・PR Track A/B・P1～P8その他のSOURCE、結果、grant、承認、科学契約、STOP・PAUSEを変更しない。
新規科学計算、solver、数値対角化、記号計算プログラム、回路build、新アルゴリズム候補の構成探索は行っていない。

読む順序：本書 → [方法論の分析](exploration_methodology_analysis.md) → [戦略比較](future_research_strategies.md) → [選定・検証プロトコル](research_selection_and_validation_protocol.md) → [判断用handoff](research_strategy_handoff.md)。
SOURCEのidentityは[source_registry.json](source_registry.json)に記録した。

## 1. 範囲と記述の約束

### 1.1 対象とした系列

| ID | 系列 | 固定commit | 区分 |
|---|---|---|---|
| E0 | 独立テーマの静的調査（T1）とT1-D撤回 | `3af746a`、`00311e0` | 前史（補助SOURCE） |
| E1 | 障害を起点とした研究原理の検討 | `60bf810df6559cc41686f3fcff90fd5108435b1a` | 固定参照 |
| E2 | 初期の新構成原理探索 P1～P8 | `67d9e3b938b8a03120b836a1c32283b7c9e9a1f0` | 固定参照 |
| E3 | P1*固定wordの記号検証とexact solver | `1771564`～`9555517`、限定静的監査`37e5002` | 補助SOURCE |
| E4 | P1*固定wordの3次障害の独立検証 | `5110d347e1f032c9093430b3def13b3391602cdd` | 固定参照 |
| E5 | J1：仮説（`dd36794`）、20-pulse紙上検証、16/24-pulse最終限定探索、正式一時保留 | `c7d3f077d634e4165b7cd326bac7caa1ae04ff66`、`143f50d3bf2636b1433d9b70a844bbdc22832a6e`、`95be62395d3740db39b6830c68f4fd1e25f595ee` | 固定参照（`dd36794`は補助） |
| E6 | 独立構成原理探索 NA/NB | `813fd44bfd70f9bc4266e35cc8e4dd28037dedce` | 固定参照 |
| E7 | 二電子補助衝突の構成検討 | `b5c49323957f1bfa2a24cb2786a0ebd1f3932925` | 固定参照 |
| E8 | CG／Paldus還元の独立検証 | `c23e9bc6028c52761e6220b91e2d1e1bd8b3ceaf` | 固定参照 |
| E9 | Q1：定式化、level挿入則、Riccati最終限定検証、正式一時保留 | `3abef73cdd8a578d56f1d96d070862c71749e403`、`2a3e6898087fc248656123e7c67fb62c49b2d0f8`、`d33fc8b690df13c6aaa0835b7d10f1a96fb789d1`、`17cf4073094c713257d6eabadb440d6d973a9229` | 固定参照 |

すべてのcommitは一本の親子関係でつながり、`17cf407`がその先端である。本書のbranchは`17cf407`を起点とする。
第一研究・第二研究・PR Track A/Bは、重複の回避と研究課題の理解に必要な範囲だけ参照した（§2）。

### 1.2 記述の約束

- 事実には固定commitの資料へのリンクを付ける。複数の資料を比べた解釈は【分析】と明記する。
- comment.md §3の区別に従い、障害を次の6種に分ける。複数に当てはまる場合は、それぞれの対象と範囲を書く。

| 記号 | 種類 | 問題の性質 |
|---|---|---|
| (a) | 具体的なno-go又は反例がある | 成立性 |
| (b) | 限定ansatzで不成立 | 成立性（そのansatzに限る） |
| (c) | 構成は成立するが既知法への還元 | 独立性 |
| (d) | 具体的な構成規則が不足 | 構成の欠如（不可能性ではない） |
| (e) | 証明・実装・資源評価が未完了 | 未完了 |
| (f) | 先行研究との関係が未確定 | 未確定 |

- 「成立しなかった」と「新規性がなかった」を混同しない。必要なunitaryを具体化できなかったことを、数学的不可能性とは書かない。

## 2. 前史：PF研究から新アルゴリズム探索へ

### 2.1 既存研究の到達点（重複回避のための要約）

- 第一研究・第二研究は、PF有限時間校正の予測可能性と予算信頼性を扱った。第一研究はS0～S4が完了し、S4の二状態収束診断の固定判定は`complete_no_benefit`である。第二研究は当初の設計が`complete_no_benefit`で閉じた後、v2のDirection C（固定finite-time PF校正の予算信頼性・残余headroom）として完了が受理された（[現在の研究状態][E0-status]）。
- 2026-10-16に、PF有限時間研究の完了監査（`b4a7a82`）と、U1-AR・U3-H05・U4の候補閉鎖が記録された（[U4閉鎖][E0-u4]）。
- PR側では、2026-10-13から16にかけて、量子化学の基底エネルギー推定を対象とする複数の方向が閉じられ、新アルゴリズム研究は研究課題選定段階へ移った（§2.2、[PR範囲整理][PR-transition]）。**「独立した生成規則が特定できない」という終わり方は、E0～E9より前のPR側の探索で既に現れていた。**
- PR Track A/Bと第一・第二研究は独立した既存成果・受理範囲・認可を持ち、新アルゴリズム探索の各系列はそれを変更しないとした（[PR範囲整理][PR-transition]、[E1][E1-handoff] §5）。PR Track Aの課題は有限のcomplex-signal taskの資源比較で、D2の絶対E0の全費用ではないと記録されている（[PR探索範囲表][PR-coverage]）。

### 2.2 PR側で既に閉じた方向（2026-10-13～16）

新アルゴリズム探索と重複しないよう、PR側で閉じた主な方向を記録する。いずれも閉じた単位は「現固定構成」「現定義」「現template」等で、方向一般の不可能性ではない。

| 方向 | 状態 | 記録された理由の要旨 |
|---|---|---|
| 第一候補（一体項再配分PF、厳密ground応答） | 現固定構成CLOSED | 10-14に、固定したequal-access first-pair classで同情報のcompact BCHへ`REDUCES_TO_KNOWN`。その後、GPTの判断に基づく別scope（有限stepの成分の有用性）の計算を行い、登録した10%費用改善の基準を4条件とも満たさず`NO_UNIFORM_REGISTERED_COMPONENT_GAIN`（[PR研究目的・研究課題][PR-purpose]） |
| H-E1（現定義）、M-a／M-b、PF小改変探索系列、旧D | 現定義CLOSED、STOP（K1なし）、PAUSED、HOLD | 「現在の固定PFに小さな自由度を追加し、誤差係数の代理量を下げ、数値結果を見て研究を救済する」反復は、独立した新規性を確認する効率が低い（[PR M再評価][PR-mreview] §7.1、[PR状態採用][PR-pfpause]） |
| SOS-PF | 現分割生成探索CLOSED、K0技術判定`UNDETERMINED_DATA_REQUIRED`、A2（有限step保証理論）NOT_ADOPTED（CLOSEDではない）、K1-F未認可 | （[PR SOS-PF状態採用][PR-sosdecision]、[PR範囲整理][PR-transition]） |
| H1～H4（新アルゴリズムの静的K0） | PAUSED（総合技術判定`NO_GO_NO_INDEPENDENT_GENERATION_RULE`、H2は`UNDETERMINED_DATA_REQUIRED`） | 既知の恒等式・測定・frame・位相参照の条件に帰着（[PR範囲整理][PR-transition]）。H1の式(1)～(3)は、SOS-PF K0と一体再配分の事前監査に既にあった（[PR K0][PR-k0]） |
| 旧候補C1～C4（macrocycle、branch付きPF外挿、self-energy／active space、cost-aware sampling） | 各記録の状態（新catalog生成へ進まない等） | 既知のcomposition、Richardson型bias相殺、Schur/Feshbach、importance sampling等との対応を監査済み（[PR探索範囲表][PR-coverage]） |
| N1（表現selector）、N2（signed charge）、N3（occupation保証）、THRIFT現template | STOP、HOLD、CLOSED、CLOSED | N1は固定比較での不成立、N2はfit改善と回路費用改善が別であること、N3は一般二体・全energy・solver費用が未解決であることが記録されている（[PR探索範囲表][PR-coverage]、[PR範囲整理][PR-transition]） |

### 2.3 新アルゴリズム探索の前に出されていた方法論上の指摘

- **GPT（10-15、M案K0停止後の再評価）**：次の新候補を判定する事前条件として、改善レバー、具体的生成写像、同じ合法情報・価格の強対照、情報モデル、スケールへの機構、native／FT費用の経路、明示的なSTOP条件の7項目を挙げた（[PR M再評価][PR-mreview] §7.3）。
- **Claude（10-16、SOS-PF後のレビュー）**：これまでの系列に共通するのは「PFの係数・分割・表現の設計空間が先行研究で密に埋まっており、独立した新規性が残りにくいこと」であり、低energy構造による大きな利得（SOSSA）はblock-encoding側で実現していると指摘し、次の候補を作る前にユーザーがD1・D2を判断するよう推奨した（[PR Claudeレビュー][PR-claude1016] §7.4）。
- **GPT（10-16、同）**：「研究全体では、先に強い比較対照・タスク・量子資源のレバーを選ぶ」、「そのレバーに効く具体的な構成規則だけを候補にする」、最強baselineとSTOPを事前に書けないならK0／K1を開始しない、と推奨した。block-encoding法を対照として参照することと、新算法として採用することを分け、範囲はユーザーが判断するとした（[PR GPTレビュー][PR-gpt1016]）。

【分析】E0～E9の各系列は、これらの指摘のうち情報モデル（無料入力にしない）とSTOPの規律を一貫して守った。一方、「先にレバーと強対照を選び、それに効く規則だけを候補にする」ことは、候補を作る前の固定手順としては実装されなかった。
E2はユーザーの承認により、発想段階では資源優位も証明も要求しない方針を採った（[E2 provenance][E2-prov]）。この選択は、高リスクの発想を早く捨てないためのものである。結果として、レバーと強対照の確認は候補を作った後に回った。

### 2.4 D1・D2の由来

| 時点 | 記録 | 内容 |
|---|---|---|
| 10-14 | PR 厳密ground前提PF方向の再レビュー | 「block-encoding、qubitization、およびそれらを中心とするQSVT/量子walkの設計を今回の候補・必須対照から除外する」（[PR再レビュー][PR-exactground]）。この時点では特定の研究方向の範囲設定 |
| 10-16 | PR Claudeレビュー | D1（block-encoding／qubitization除外の扱い）とD2（taskの範囲）を、ユーザーの判断事項として初めてラベル付きで提示（[PR Claudeレビュー][PR-claude1016] §7.4） |
| 10-16 | PR GPTレビュー | 既存の除外を無断で変更しないと推奨（[PR GPTレビュー][PR-gpt1016]） |
| 10-16 13:07 | PR 既存技術基盤対応表 | D1・D2を「固定する」（[PR基盤表][PR-foundation]） |
| 10-16 14:19 | PR 範囲整理 | D1をQSVT・量子walkまで含めて明記し、D2に定数項・energy origin・対象粒子数sectorを明記（[PR範囲整理][PR-transition]） |
| 10-16 23:38 | EVAL E1 | ラベルなしの「比較前に固定した条件」として、定数項・核反発・normal-order補正を含む絶対E0を記載（[E1候補][E1-cand] §1） |
| 10-17 00:17 | EVAL E2 | provenanceでD1・D2のラベルが付き、D2に「all residuals retained」が加わった（[E2 provenance][E2-prov]） |

D1・D2の固定を決めたユーザー指示・GPT方向レビューの本文は、今回読んだrepositoryの範囲では確認できなかった。

### 2.5 E0：独立テーマの静的調査とT1-Dの撤回

| 項目 | 内容 |
|---|---|
| 問題 | PF系列の完結後に、量子化学の独立研究テーマを静的に探す。残した候補T1は、deterministic PFのHadamard-test型energy推定で、trap回路のlogical accreditationの誤差情報を、有限標本の推定失敗確率と取得費へ接続し、時刻・PF・shot・認証精度の選択を改善できるか、という設計問題だった（[E0 handoff][E0-topics]、[E0 matrix][E0-matrix]）。 |
| 結果 | T1は「条件付き候補1件」。新しい数学的機構は提案していない。近接研究自身が適用可能性を述べており、「単純な接続だけなら差分は弱い」と自ら記録した（[E0 matrix][E0-matrix]）。 |
| 正式判断 | ユーザーがT1-Dとして独立研究候補から撤回した。理由は「現在確認できる独立した科学的差分と資源上の利益が、追加研究を正当化するほど確立していない」こと（[T1-D][E0-t1d] §3）。 |
| 分類 | (c) 既知のlogical accreditationと位相推定法の接続。(e) 有限標本の推定保証・取得費は未確立。実現可能性の否定ではない。 |

【分析】T1は、既知論文の対象外の記述（後処理を対象外とする）から作られた候補だった。資料自身が「既存論文の未評価部分を見つけたこと」は新規性ではないと書いている（[E0 matrix][E0-matrix]）。
この「既知法のすき間から候補を作る」形は、E1でも繰り返された（§4.1）。

E0の直前に、Evaluation側ではPF有限時間研究の完結性監査とU1／U3／U4の閉鎖が行われ、監査済みのU1～U7の範囲では「直ちに追加研究として採択する独立テーマを残さない」と記録された（[U4閉鎖][E0-u4] §2）。
PR側（§2.2）とEvaluation側の両方で、同じ10-16にPF改良系の候補が独立テーマにならないという判断に達し、その後にE0～E9の新アルゴリズム探索が続いた。

## 3. 時系列

| commit（JST） | 系列 | 枠組み | 結果 | 正式状態 |
|---|---|---|---|---|
| 10-16 22:22 `3af746a` | E0 | 独立テーマの静的調査 | T1を条件付き候補1件 | 採択なし |
| 10-16 23:14 `00311e0` | E0 | T1-D | T1を撤回 | ユーザーの正式判断 |
| 10-16 23:38 `60bf810` | E1 | 障害起点 | 障害5件、仮説2件、独立研究候補0件 | Codexの限定探索結果（正式STOPではない） |
| 10-17 00:17 `67d9e3b` | E2 | 異分野の機構 | 8件からP1*を分類Bで保持。A 0件、C 4件、D 3件 | 暫定分類 |
| 10-17 00:43～03:37 `1771564`～`9555517` | E3 | P1*の科学契約と実行 | 固定12-segment wordでexact `UNSAT`（`NO_SOLUTION_IN_FIXED_ANSATZ`） | 固定ansatzの結果 |
| 10-17 14:00 `37e5002` | E3 | 限定静的監査 | Z3依存UNSATを支持、独立certificateなし | 監査記録 |
| 10-17 14:49 `5110d34` | E4 | 紙上の独立検証 | 固定wordは全実振幅で3次不成立。既知比較構成は形式4次を満たす | 検証記録 |
| 10-17 15:10 `dd36794` | E5 | J1仮説 | 高リスク仮説1件を保持 | 正式採択ではない |
| 10-17 15:24 `c7d3f07` | E5 | J1 20-pulse | 1～3次条件は成立、既知gate＋echoへ還元 | 状態変更なし |
| 10-17 15:42 `143f50d` | E5 | J1 16/24-pulse | G1は3次で不成立、G2は既知rectangleのStrang分割。一時保留を推奨 | 状態変更なし |
| 10-17 15:53 `95be623` | E5 | J1正式判断 | 追加探索を一時保留 | **PAUSED_PENDING_NEW_MECHANISM** |
| 10-17 16:15 `813fd44` | E6 | 独立構成原理 | NA/NBとも保持0件 | Codexの限定探索結果 |
| 10-17 16:42 `b5c4932` | E7 | ボトルネック操作 | 衝突J_NはCG／Paldus＋3値phaseへ還元、新操作課題0件 | Codexの限定結果 |
| 10-17 17:00 `c23e9bc` | E8 | 還元の独立検証 | 還元を確認、訂正0件 | 検証記録 |
| 10-17 17:27 `3abef73` | E9 | 未解決問題起点 | 研究課題案Q1を1件保持 | 未採択の研究課題案 |
| 10-17 17:46 `2a3e689` | E9 | level挿入則 | 文法Gは限定的に不成立、親Fは既知法へ限定還元、共通unitary Bは未構成 | 状態変更なし |
| 10-17 18:02 `d33fc8b` | E9 | Riccati最終限定 | G_FとG_Sは限定的に不成立、一時保留を推奨 | 状態変更なし |
| 10-17 18:23 `17cf407` | E9 | Q1正式判断 | 追加探索を一時保留 | **PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE** |

E1、E6、E7、E8は新しい正式状態の文字列を作っていない。いずれもCodex側の限定結果としてGPT／ユーザーへ返され、Mandatory STOPで終わった。
E8は「保持0件という正式判断」と書いている（[E8][E8-handoff] §1）が、GPT／ユーザーがいつ正式に受理したかは、今回読んだSOURCEでは確認できない。

## 4. 研究ごとの整理

各表のA1～A7はcomment.md §3の1～7に対応する（1 問題、2 機構、3 構成・検証できた内容、4 成立しなかった理由、5 既知法へ還元された部分、6 未解決の部分、7 正式状態と再開条件）。

### 4.1 E1：障害を起点とした研究原理の検討（60bf810）

| 項目 | 内容 |
|---|---|
| A1 問題 | 固定証拠から具体的な障害を抽出し、それを解く回路生成・情報取得規則を探す。最終対象は定数項・核反発・normal-order補正を含む元Hの絶対E0（[E1候補][E1-cand] §1）。 |
| A2 機構 | 障害O1～O5を抽出（[E1障害表][E1-map]）。O4からX1（code上の同値な代表の選択とword内のparity計算の再利用を共同で決める回路生成）、O5からX2（全RDMを再構成せず、energy推定に必要な情報へjoint測定を集中し、copy間の相関を使う）。 |
| A3 構成・検証 | X1・X2を入力・処理・出力の水準で記述し、6件の一次資料と2件の公開codeに限って照合。新しい総資源値・保証・証明は作っていない（[E1 handoff][E1-handoff] §3）。 |
| A4 不成立の理由 | X1は既知の経路探索・Clifford合成・block schedulingを越える具体的な選択規則・入力class・保証を提示できなかった。X2は既知のfermionic joint測定と重み最適化、又は2-copy Bell測定と別の符号取得に帰着した（[E1 handoff][E1-handoff] §2）。 |
| A5 還元 | X1：要素ごとに既知（flow-set／stabilizer回路、TOPP-HATT、分子GSEの経路利用、Paulihedral）。X2：記述した手順の水準で既知（[E1候補][E1-cand]）。 |
| A6 未解決 | O1～O5の障害そのもの。X1の独立した選択規則、X2の異なるPOVM生成規則。 |
| A7 状態 | 独立研究候補0件。Codexの限定探索結果で、正式STOPではない。既知構成と異なる明示的な規則が外部の新しい証拠として提示された場合に、ユーザー／GPTが別件として判断する（[E1 handoff][E1-handoff] §4）。 |
| 分類 | X1：(d)、要素は(c)。X2：(c)。O1～O3は、科学的に閉じたからではなく既存研究（第一・第二研究、Track B、Track A V2）の担当範囲として除外した（[E1障害表][E1-map] §7）。 |
| 否定していない範囲 | 分野全体の一般no-go、新規性不存在の一般証明、正式な新しいSTOP（[E1障害表][E1-map] §7）。X2について既報の限定的な利益。 |

### 4.2 E2：初期の新構成原理探索 P1～P8（67d9e3b）

| 項目 | 内容 |
|---|---|
| A1 問題 | 異分野の機構から、元の電子Hの時間発展又は絶対E0推定に使える新しい構成規則を仮説として作る。探索方針は「既存法の組合せから選ぶ探索」から「新しい構成規則を仮説として作る探索」へ正式に移行した（[E2 map][E2-map]）。 |
| A2 機構 | P1 非可換な電子密度と共通振動子の閉路、P2 配置依存の励起閉路cell、P3 誤差を等スペクトル方向へ送る積分、P4 基準からのenergy微分の積分、P5 補助散乱による有理propagator、P6 定常性からの制御変量、P7 有限step誤差だけをsyndromeへ送るlift、P8 自律的なenergy clock（[E2 map][E2-map]）。 |
| A3 構成・検証 | 発想を文献検索の前に固定し、その後に既知法と照合した。新しい代数展開・方程式・証明は作っていない（[E2 handoff][E2-handoff]）。 |
| A4 結果 | P1*（CARを使う非可換密度の共同bus閉路）だけを分類B（操作族・目標・最初の係数整合問題が書ける）で保持。C 4件（P2、P3、P4、P6：構成の核が既知）、D 3件（P5、P7、P8：必要な操作が未定義）（[E2 handoff][E2-handoff] Phase C）。 |
| A5 還元 | P2はCI row oracle・graph分解・multi-edge可解成分、P3は既存H1監査と固有状態条件・processed／corrected PF、P4は既知の微分関係（Hellmann–Feynman）、P6は零期待値制約を加える既知の測定枠組み。 |
| A6 未解決 | P1*がCAR固有の共同閉路規則を持つか。P5の許可primitiveによるresolvent、P7のliftとrecovery、P8の情報転送操作は未定義。 |
| A7 状態 | 分類は暫定（provenanceで`provisional_only`）。正式採択・科学的GO・新規性認定は0件。 |
| 分類 | C 4件：(c)。D 3件：(d)。P1*：(d)と(f)。 |
| 否定していない範囲 | 特定ansatzの失敗を、他の全制御族・量子化学の新原理一般の不可能性とはしない（[E2 handoff][E2-handoff] Phase D）。 |

文献検索の前に固定したPhase Aの記録には、P3「possible complete reduction」、P4「likely Hellmann-Feynman」、P6「likely known control variates」、P5「no explicit allowed resolver」、P7「lift and recovery not specified」、P8「no distinct operational transfer rule」が既に書かれていた（[E2 provenance][E2-prov]）。
P1の未解決核としては「non-Abelian bus closure, operator-valued residual displacement」が書かれており、これが後にE4の3次障害として具体化した。

### 4.3 E3・E4：P1*固定wordの検証（1771564～9555517、37e5002、5110d34）

| 項目 | 内容 |
|---|---|
| A1 問題 | 非可換な二つのHermitian一体factor \(L_1,L_2\)（4 modes）を共通busへ結合し、CARの関係を制御parameterの選択に使って、必要な電子二体作用とbus帰還を両立する共同閉路を作れるか（[契約][E3-contract]）。 |
| A2 機構と固定ansatz | primitive \(A=L_1\otimes X\)、\(B=L_1\otimes P\)、\(C=L_2\otimes X\)、\(D=L_2\otimes P\)。固定12-segment word \((A,B,C,D,A,C,B,D,A,D,B,C)\)、振幅\(x_j\in[-1,1]\)。目標 \(\log U=-i\eta^2K\otimes I+O(\eta^5)\)、\(K=L_1^2+L_2^2\)、full Fockで判定。wordは「各primitiveを同じ回数訪れる短いinterleavingを仕様として選んだ。解の存在や独立性を計算して選んだwordではない」（[契約][E3-contract]）。 |
| A3 構成・検証 | 4次formal-logから438本の多項式等式を生成し、Z3でexact `UNSAT`。4回のattemptと3回の技術修正を経た。最終runは約310秒、worker RSS peak約338 MiB（[実行報告][E3-report]）。限定静的監査はZ3依存のUNSATを支持したが、独立certificateや係数生成の独立再検証はない（[監査][E3-audit]）。紙上検証では、N=1の必要条件から、1次・2次条件が振幅を \(x=(a,c,-f,g,0,f,0,-g,-a,0,-c,0)\)、\(ac=-1\)、\(fg=1\) へ強制し、3次残差 \(\eta^3[L_1,L_2^2]\otimes(aX+cP)\) が全実振幅で非零であることを示した（[3次障害][E4-cubic] §§2–5）。 |
| A4 不成立の理由 | 固定wordは3次で不成立。原因は「低次の面積条件が自由度を失わせ、未完了の条件付き変位の中で別factorの平方を作ると、その平方の共役がbus依存残差を生む」機構（[3次障害][E4-cubic] §7）。 |
| A5 還元 | 2次で強制される構造は、単独factor閉路の入れ子である（式(10)–(12)）。比較構成（単独factor閉路3個の対称Strang積）は同じprimitive・box・12 pulseで形式4次を満たすが、primitiveの訪問回数はA/Bが各4、C/Dが各2で固定wordと異なり、既知構成に分解される（[3次障害][E4-cubic] §6）。 |
| A6 未解決 | 別word・別factor・η依存振幅・sector限定・別の許可制御でP1*が成立するか。438条件の各係数とsolverの一般的な正しさ。新規性、有限時間誤差、coupling費用。 |
| A7 状態 | 科学分類`NO_SOLUTION_IN_FIXED_ANSATZ`。P1*の分類B自体を改めた記録はない。次の判断はGPT／ユーザー（[3次障害][E4-cubic] §7）。 |
| 分類 | 固定wordについて(a)（全 \(\mathbb R^{12}\)、形式3次以上、紙上証明）と(b)。比較構成は(c)。P1*の核心（CARから制御cycleを生成する規則）は(d)・(f)。 |
| 否定していない範囲 | η依存振幅、別factor、別word、追加pulse、sector限定構成、P1*一般、補助振動子方式全体。\([L_1,L_2]\ne0\)だけからの一般障害も主張しない（[3次障害][E4-cubic] §§5, 7）。 |

【分析】この試験はN=1、すなわち一体の水準で失敗しており、CARの二体構造は関与していない。資料自身が、N=2固有のCAR関係を使う構成一般の可能性は決まらないと書いている（[3次障害][E4-cubic] §7）。
したがってE3は、P1*の核心である「CARによる共同閉路」を検査していない。

### 4.4 E5：J1（dd36794、c7d3f07、143f50d、95be623）

| 項目 | 内容 |
|---|---|
| A1 問題 | E4の障害（未完了の変位による相互作用の共役）を、別経路との共同相殺へ変える。4軌道のCAR交換対 \(Q_1=E_{pq}E_{rs}\)、\(Q_2=E_{ps}E_{rq}\)、\(Q_1+Q_2=0\) を構成前の入力とし、2次信号に差、3次の不要bus作用に和を割り当てる制御cellがあるか（[J1仮説][E5-j1handoff]）。 |
| A2 機構 | Hermitian一体factor（hopping S/A）×共通bus X/Pの実制御だけでcellを作る。独立性の第一点検として、比較代数（普遍包絡代数）で非零の3次bus項がCARで零になることを要求した（[J1仮説][E5-j1handoff] §2）。 |
| A3 構成・検証 | 20-pulse cellで1～3次の形式条件 \(\rho(\ell_1)=0\)、\(\rho(\ell_2)=-4iH_\diamond\otimes I\)、\(\rho(\ell_3)=0\) を満たした（[20-pulse][E5-20handoff]）。16-pulseのG1（未完了2-pulse legのgroup commutator）と24-pulseのG2（legの対称PF化）を一度だけ調べた（[最終探索][E5-finalhandoff]）。 |
| A4 不成立の理由 | 20-pulse cellはfull Fockで \(\rho(U_J)=(VBV^{-1})(V^{-1}BV)\) へexactに書き直せ、既知gateの汎用echoだった。G1は3次のbus三次に非零の一体係数が残った。G2は1～3次を満たすが、可換aggregate forceの既知rectangleのStrang分割だった。CARが目標生成と3次相殺の両方に不可欠という要件を満たす文法は得られなかった（[最終探索][E5-finalhandoff]）。 |
| A5 還元 | 20-pulse：完成gate＋汎用echo（exactな書換え、生成の同値）。G2：既知rectangleのStrang分割（生成規則の同値。出力の一致は1～3次で、有限ηでexactに同一のpathとはしない）。20-pulseの部品は条件付き変位の4変位rectangle（Spillerら）。 |
| A6 未解決 | 非還元なJ1共同文法の存在。CARの交換記号σを実制御pathへ持ち上げる規則。4次以降、有限時間のbus帰還、物理access、一般の化学Hへの拡張、新規性、資源優位。 |
| A7 状態 | **PAUSED_PENDING_NEW_MECHANISM**（判断記録ID `P1STAR-J1-DECISION-20261017-PAUSE-01`、ユーザーの明示承認）。再開を判断する条件：「CARが目標二体信号の生成と3次bus残差の相殺の両方に不可欠で、既知法に還元されない、具体的な実制御文法が提示されること」。提示があっても自動再開しない（[J1保留][E5-pause]）。 |
| 分類 | 20-pulse・G2：(c)。G1と共通prefix族：(b)。J1一般：(d)。4次以降・費用：(e)。DCG・fermionic unitary synthesisとの全構成での関係：(f)。 |
| 否定していない範囲 | J1／P1*一般の不可能性、sector限定構成の一般的不成立、科学的NO-GO定理。高リスク・未証明だけを理由にした価値の否定（[J1保留][E5-pause]）。 |

J1の最終探索は、障害を構成classの性質として書いた。「一体factor×線形busからの三重Lie語では、bus三次の最高次数係数は電子の一体入れ子交換子となる」。一体作用のN=1制限は自分自身なので、この係数が非零なら二体のCAR零関係では消せない（[最終探索][E5-finalhandoff]、[限定構成記録][E5-finalmath] §2.1）。
同じ記録は、完成rectangleを使えば既知gate＋echoになり、未完了legにすると一体Lieの3次障害が残り、汎用対称化で消すとCAR固有の相殺の根拠がなくなる、という境界を明示した（[限定構成記録][E5-finalmath]）。

### 4.5 E6：独立構成原理 NA/NB（813fd44）

| 項目 | NA：非可換な場の運動量による二体生成 | NB：nilpotentな対数振幅の輸送とchartの貼合せ |
|---|---|---|
| A1 問題 | factorごとの平方から、群rotorの二次運動量作用へ生成単位を変える | 小指数の積から、全励起振幅・scalarの輸送へ生成単位を変える |
| A3 構成・検証 | 電子Hの二次Lie表示との対応、単一phase-kick案の非可換性を紙上で整理 | 指数parameter表示とsimilarity変換方程式が既知のCC／TDCC（Kvaal 1201.5548v2、Piggら 1205.4002v1）に対応すること、入力障害の所在を紙上で整理。圧縮、回路、E0の有限精度保証は示していない（[NA/NB仮説][E6-hyp] §3.5） |
| A4 不成立の理由 | 単一kick規則は一般の二次式Kを処理せず、その後の独立した作用生成規則を提示できなかった。二次式を分割すると既知DF／PFに戻り、irrep内の全Qを対角化すると多電子固有問題の供給を要する（[NA/NB仮説][E6-hyp] §2.4–2.5） | 有限log・similarity変換・scalar方程式は既知のCC／TDCCに対応。未知振幅を取得せずにchart間を移す量子操作が未定義（[NA/NB handoff][E6-handoff]） |
| A5 還元 | 電子Hの二次Lie表示は既知 | 生成の中核がTDCC |
| A7 状態 | 保持0件。Codexの限定探索結果（[NA/NB handoff][E6-handoff] §1） | 同左 |
| 分類 | (d)（独立した生成規則の不足）、(b)（単一kick案） | (c)（中核）と(d)（chart移送） |
| 否定していない範囲 | 非Abelian場一般による新構成の不可能性 | NBの全可能性に対する不能性 |

### 4.6 E7・E8：二電子補助衝突とCG／Paldus還元（b5c4932、c23e9bc）

| 項目 | 内容 |
|---|---|
| A1 問題 | 既知係数行列Vから準備する二電子補助状態を使い、任意のN電子targetへ相互作用を渡す、係数非依存な衝突 \(J_N=\binom N2^{-1}\sum_{\alpha\beta}A_\alpha^\dagger A_\beta\otimes|\beta\rangle\langle\alpha|\)、\(U(\theta)=e^{-i\theta J_N}\) を生成できるか（[衝突 handoff][E7-handoff]）。 |
| A3 構成・検証 | 素朴な「二電子を抽出→SWAP→逆抽出」は、反対称空間の抽出imageをSWAPが保存しないためunitaryにならないことを、M=5・N=3の手で追える例で示した（[操作仕様][E7-task] §4）。 |
| A4・A5 還元 | target／補助を仮想的な二種類のfermionとすると \(J_N=(K_1^2+NK_1-2NI)/(4\binom N2)\)、\(K_1=NI-S^2+m(m-1)I\)。total spinの許されるsectorごとに3値のphaseを付ければよく、生成は既知CG／Paldus変換と3種類のphaseへ明示的に還元された（[衝突 handoff][E7-handoff] §1）。E8は、CARとCGの二経路で独立に導出し直し、訂正0件で還元を確認した（[CG検証][E8-handoff]）。 |
| A6 未解決 | 二電子係数状態 \(\rho_2\) の効率的準備、全準備・copies・合成誤差を含む資源評価。係数への依存は、unitaryの生成から \(\rho_2\) の準備へ移っただけで、その費用は未確立（[操作仕様][E7-task] §3）。 |
| A7 状態 | 最終保持する新操作の設計課題0件。新しい正式状態文字列はない。 |
| 分類 | (c)（生成まで既知）。(e)（実装精度・総費用は対象外）。 |
| 否定していない範囲 | 他の新操作の不存在。任意の化学HをCGだけで対角化できるとは言わない（[CG検証][E8-handoff] §2）。 |

【分析】HME＋反対称fermion空間での係数copy衝突＋CG／Paldus＋3値phaseという組合せについて、protocolとしての新規性と資源価値は網羅調査されず、否定ではなく評価の枠外に残った（[比較と限界][E7-prior]）。

### 4.7 E9：Q1（3abef73、2a3e689、d33fc8b、17cf407）

| 項目 | 内容 |
|---|---|
| A1 問題 | inhomogeneousなRichardson–Gaudin pairing family（picket-fence、\(1/2\le\gamma\le2\)、pair数 \(m=\Theta(L)\)、任意のactive subset）で、係数だけから全入力に使えるcoherentな基底変換 \(W_I\) とenergy評価 \(D_I\) を、指数個のstate・root setを列挙せずに生成する。目標は \(\|h_I-W_ID_IW_I^\dagger\|\le\zeta\)、全生成費用 \(\le\operatorname{poly}(L,b,\log(1/\zeta))\)（[Q1定式化][E9-handoff]、[研究問題][E9-problem]）。 |
| 選定経緯 | 一次文献11件と著者公開sourceを調べ、「未解決」を4区分（数学的条件が未閉鎖、既知構成があり保証・入力が限定、構成原理は既知、既存系列の限定未解決）に分けてQ1を1件だけ保持した（[未解決問題調査][E9-survey]）。 |
| A2 機構 | levelを一つ加えるunitary \(B_{I,\ell}\) を、係数とcompactな再帰labelから生成する新しい再帰則（未構成）。挿入blockは \(\begin{pmatrix}D_I^{(m)}&-gF_I^{(m)}\\-gF_I^{(m)\dagger}&D_I^{(m-1)}+(2\epsilon_\ell-g)I\end{pmatrix}\)（[研究問題][E9-problem]）。 |
| A3 構成・検証 | L=4・m=2の3＋3分解、親F（三準位parentの反転関係と一対rank-one secular座標による点ごとの式）を紙上で導出した（[親F導出][E9-insparent]）。graph部分空間の条件として、Riccati式 \([\Lambda,Y]+Y-gF+gYFY=0\) を得た（[挿入障害][E9-insobs]）。 |
| A4 不成立の理由 | 独立2次元channel文法Gは \([\mathsf d,J]_{12}=-1/2\ne0\) によりg∈[1/8,1/2]の全域で不成立。Fと可換なYの文法G_Fは \([\Lambda,F^2]=0\) を導き矛盾。固定Sylvester逆の文法G_Sは \(\gamma_*=\sqrt2\) で特異。Fとも非可換なlabel混合を係数から生成し、child spectrum情報を外部入力せずに残差を閉じる規則が得られなかった（[Q1保留][E9-pause]）。 |
| A5 還元 | 親Fの式は既知法への限定還元（新しい量子生成規則ではない）。Sylvester逆・不変部分空間・block diagonalization・Bethe/F-basisへ書ける部分は既知（[既知還元][E9-ricknown]）。 |
| A6 未解決 | 一般の非可換Yと共通unitary B。(Q3)～(Q7)の成立。定式化が候補経路として挙げたCauchy／Gaudin関係によるfactorizationは、得られていないと記録された（[研究問題][E9-problem]）。 |
| A7 状態 | **PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE**（判断記録ID `Q1-DECISION-20261017-PAUSE-01`、ユーザーの明示承認）。Q1は「未採択の研究課題案」のまま。再開を判断する条件：「Hamiltonian係数から、非対角なlabel混合と共通unitary挿入則を生成する、既知法へ還元されない具体的規則が提示されること」。child root・全固有vector・spectral projectorを外部から与える規則や、既知処理への書換えだけでは充足しない（[Q1保留][E9-pause]）。 |
| 分類 | G・G_F・G_S：(b)（各文法の中では具体的な障害）。書換え可能部分：(c)。Y・B：(d)。費用・誤差：(e)。 |
| 否定していない範囲 | Q1全体やRichardson–Gaudin模型一般の不可能性。有限bit有理入力での一般的な不能性。限定的障害をgate数・bit数・conditioningの下界やNO-GO定理として扱わない（[Q1保留][E9-pause]）。 |

【分析】GとG_Fの障害は、どちらも準位の非一様性（\([\mathsf d,J]\ne0\)）から生じた。一方、非一様性は、uniform準位の既知CG／Schur経路への退化を避けるためにQ1自身が課した要件だった（[既知法比較][E9-prior]）。
新規性のための要件と、試した対称性適合型の文法が、最初から構造的に衝突していた。

## 5. 横断表：成立しなかったものと、新規性がなかったもの

| 構成・命題 | 結果 | 分類 | 問題の性質 | 否定された範囲 | 否定されていない範囲 |
|---|---|---|---|---|---|
| T1（認証＋位相推定の接続） | 撤回 | (c)(e) | 独立性・価値 | 接続だけの独立研究化 | 認証法・位相推定の研究価値 |
| X1（代表・parityの共同選択） | 保持せず | (d)、要素は(c) | 規則の不足 | 記述した水準の独立候補 | 共同選択の目標そのもの |
| X2（energy向けjoint測定） | 保持せず | (c) | 独立性 | 記述した手順の独立性 | 既報の限定的な利益 |
| P2・P3・P4・P6 | 分類C | (c) | 独立性 | 今回の記述の独立性 | 各分野の研究価値 |
| P5・P7・P8 | 分類D | (d) | 規則の不足 | なし（操作が未定義） | 将来の操作定義 |
| P1*固定12-segment word | 不成立 | (a)(b) | 成立性 | このword・factor・target・η非依存の全実振幅、形式3次以上 | 別word・別factor・η依存振幅・sector限定・P1*一般 |
| P1*比較構成（単独閉路＋Strang） | 成立、既知 | (c) | 独立性 | P1*の証拠としての価値 | — |
| J1 20-pulse cell | 成立、既知 | (c) | 独立性 | J1の独立成功例と数えること | 全J1 path |
| J1 共通prefix族 | 不成立 | (b) | 成立性 | 同じ完成blockを同じprefixで運ぶ族 | 独立輸送・別path・同時制御 |
| J1 G1（16-pulse） | 不成立 | (b) | 成立性 | 指定係数・順序の1 cell | 全振幅・別word・同時制御 |
| J1 G2（24-pulse） | 成立、既知 | (c) | 独立性 | J1固有候補としての保持 | — |
| NA 単一phase-kick | 不成立 | (b)(d) | 成立性・規則の不足 | 一般Kへの単一kick | 非Abelian場一般 |
| NB 生成の中核 | 既知 | (c)(d) | 独立性・規則の不足 | 中核の独立性 | NBの全可能性 |
| 二電子補助衝突 J_N | 成立、既知 | (c) | 独立性 | 新操作としての保持 | 他の新操作、組合せprotocolの価値 |
| Q1 文法G | 不成立 | (b) | 成立性 | 一段の独立channel文法、g∈[1/8,1/2] | 複数段の混合、別のcompact規則、近似 |
| Q1 文法G_F | 不成立 | (b) | 成立性 | Fと可換なYの全branch | 一般のY、Fと非可換なY |
| Q1 文法G_S | 特異点あり | (b) | 成立性 | 連続区間での固定Sylvester逆 | 有限bit有理入力、poly(bit長)算法 |
| Q1 親F・Riccati書換え | 既知 | (c) | 独立性 | 新しい生成則としての保持 | — |
| Q1 共通unitary B | 未構成 | (d)(e) | 規則の不足 | なし | Q1全体、RG一般 |

【分析】成立性の否定（(a)・(b)）は、どれも特定の文法・ansatzに限られている。独立性の否定（(c)）は、構成が成立した場合にだけ起きた。
**今回の記録の範囲では、成立した構成はいずれも既知の生成規則と一致し、既知の生成規則に当たらない構成はいずれも成立しなかったか、規則として書けなかった。** この対応が、E0～E9の結果の要約である。
これは記録された有限個の構成についての観察であり、一般的な法則として主張するものではない。

## 6. 得られた有用な数学的知見

### 6.1 障害の補題（将来のscreeningに使えるもの）

| # | 内容 | 出典 | 適用範囲 |
|---|---|---|---|
| K1 | 粒子数保存primitiveのfull Fock恒等式は、N=1の一体行列でも必要条件として成り立つ。CARの二体関係はN=1では見えない | [3次障害][E4-cubic] §2 | 制限後の積の関係をfull Fockへ戻して代用しない |
| K2 | 1次閉鎖の下で \(\Omega_2=\sum_{r<s}M_{rs}[G_r,G_s]\)（時系列の累積面積）。任意のwordを手で評価できる | [3次障害][E4-cubic] §3 | 形式次数 |
| K3 | 未完了の条件付き変位Vの中で別factorの平方を作ると、\(V(L_2^2\otimes I)V^{-1}\) の1次項がη³でbus依存残差 \([L_1,L_2^2]\otimes(aX+cP)\) を生む | [3次障害][E4-cubic] §4 | 低次条件を満たした振幅の下 |
| K4 | 一体factor×線形bus（η非依存）の三重Lie語では、bus三次の最高次係数は一体の入れ子交換子で、N=1で非零ならCARの二体零関係では消せない。CARはbus一次の電子積にしか効かない | [限定構成記録][E5-finalmath] §2.1 | 低次の必要条件。全実pathの不可能性ではない |
| K5 | 「比較代数で非零・CARで零」は、full Fockで等しいblockへの置換で判定が変わる。独立性の十分条件ではない | [20-pulse][E5-20handoff] | 形式語の上の診断 |
| K6 | 反対称空間では、二電子の抽出→SWAP→逆抽出はunitaryにならない | [操作仕様][E7-task] §4 | M=5・N=3の具体例と一般の理由 |
| K7 | inhomogeneous準位では \([h_1,T^\dagger T]=[\mathsf d,J]\ne0\) が独立channel文法を壊し、Fと可換なYは \([\Lambda,F^2]\ne0\) と矛盾する | [挿入障害][E9-insobs]、[Riccati導出][E9-ricderiv] | L=4・m=2、指定区間 |
| K8 | 一つのSylvester逆を連続parameter区間で使うと、内部の共鳴点（Q1では \(\gamma_*=\sqrt2\)）で特異になる | [Riccati導出][E9-ricderiv] | 有限bit有理入力での分母零は主張しない |

### 6.2 正の構成・恒等式

- 単独factor閉路の厳密恒等式 \(R_L(u,v)=e^{-iuv\eta^2L^2}\otimes I\)、及び3閉路の対称Strang積で形式残差 \(O(\eta^6)\)（[3次障害][E4-cubic] §6）。bus付き構成の**positive control**として使える。
- 互いに素な軌道対の可換なhopping factorで、double-excitation gateをfull Fockでexactに作る8-pulse構成（[20-pulse数学記録][E5-20math]）。
- 未完了legでのCARによる二体信号の抽出 \(\rho(F_SG_S-F_AG_A)=4H_\diamond\)（[限定構成記録][E5-finalmath]）。
- 衝突の閉形式 \(J_N=(K_1^2+NK_1-2NI)/(4\binom N2)\) と、total spinごとの3値phase。N=2では \(J_2=\mathrm{SWAP}\)（[衝突 handoff][E7-handoff]、[CAR再導出][E8-car]）。
- controlled evolutionでは、scalar cとself項がcontrol=1 branchに \(e^{-it(c-2g)}\) を残す。一部だけを落とすとbranch依存の誤差になる（[挿入 handoff][E9-inshandoff] §2）。衝突の検証でも、scalarの脱落が相対位相を変えることを確認した（[小例と制御][E8-small]）。

### 6.3 既知構成の一覧（還元先）

将来の候補のbaselineとして、過去の系列で還元先になった既知構成を一覧にする。一次文献の版と読取り範囲は各系列のregistryに記録されている。今回は一次文献を新たに取得・再読していない。

| 既知構成 | 還元された構成 | 記録した系列 |
|---|---|---|
| 条件付き変位の4変位rectangle（Spillerら、quant-ph/0509202v3 §IV） | P1*の2次構造、J1の部品 | E4、E5 |
| 対称Strang積（Strang 1968、DOI 10.1137/0705041） | P1*比較構成、J1 G2 | E4、E5 |
| 完成gateの共役による汎用echo、DCGの考え方（Khodjasteh–Viola 0906.0525v2） | J1 20-pulse | E5 |
| 交換子積・group commutator（Childs–Wiebe 1211.4945v2） | J1 G1・G2の外形 | E5 |
| 密度平方・DF（Mottaら 1808.02625v2） | P1、NAの分割修正 | E2、E6 |
| CC／TDCC（Kvaal 1201.5548v2、Piggら 1205.4002v1、公開実装HyQD） | NB | E6 |
| Schur変換・CG（Bacon–Chuang–Harrow quant-ph/0601001v1）、Paldus（Burkat–Fitzpatrick 2506.09151v2） | 二電子補助衝突 | E7、E8 |
| fermionic joint測定と重み最適化（2402.19230v3）、2-copy Bell測定（2412.14466v1） | X2 | E1 |
| flow-set／stabilizer回路（2512.11418v2）、TOPP-HATT（2512.13580v2）、分子GSEの経路利用（2511.09322v1）、Paulihedral（2109.03371v1） | X1の要素 | E1 |
| Sylvester逆、不変部分空間、block diagonalization、Bethe/F-basis（Q1のregistryの文献） | Q1の書換え可能部分 | E9 |
| logical accreditation（2508.05523v3）、QCELS／RPE | T1 | E0 |

J1の記録では、Strang分割の一次文献IDがJ1の4 commitに記載されていない。上流のE4で書誌確認に使ったDOIを、ここでは対応として示した。

## 7. 共通する失敗原因と、一般化の範囲

### 7.0 共通する失敗原因（要約）

詳細と根拠は[方法論の分析](exploration_methodology_analysis.md) §2にある。

| 原因 | 要旨 |
|---|---|
| RC1 | 「関係・表現」から始め、許可された入力と操作から作用を作る生成規則が後回しになった |
| RC2 | 必要な情報（固有値、振幅、child spectrum等）の取得法を、候補選定の後で調べた |
| RC3 | 既知法への還元を構成の後で確認した。還元の手掛かりは初期の記録にあった |
| RC4 | 固定ansatzが機構から導かれず、承認の区分によって紙上の低次事前解析が抜けた |
| RC5 | 新規性の基準が機構の同一性に偏り、資源・保証という価値の基準がなかった |
| RC6 | 独立性のために課した性質（未完了leg、非一様性）が、自然な文法の障害そのものになった |
| RC7 | 最初の命題は小さかったが、失敗しても次の判断を導く情報が残りにくかった |
| RC8 | 枠組みを毎回変え、既知法との差分として候補を作った。内部記録との照合とIDの付け方にも問題があった |
| RC9 | D1の範囲の構成空間が成熟しており、局所型・対称型・spectral型のどれも既知の道具の領域に入った |
| RC10 | 同一性照合の記録が大きく、研究判断はそれで変わらなかった |

### 7.1 一般化できること

1. **決め手は毎回、生成規則の段階にあった。** 規則を書けた構成は既知の生成規則と一致し（20-pulse、G2、衝突、NBの中核）、規則を固定した構成は低次で不成立だった（P1*固定word、G1、G・G_F・G_S）。規則を書けない発想は残らなかった（X1、P5・P7・P8、NA、Q1のB）。§5の表がその根拠である。
2. **決め手は短い紙上の確認で得られた。** E4、E5、E6、E7、E8、E9の判断は全て紙上導出による。計算機による科学計算を行ったE3の結論（box内UNSAT）は、E4の紙上導出（全実振幅、3次、機構の説明）に包含された。
3. **還元先と欠落操作の多くは、検討の初期に見えていた。** E2のPhase A記録、E0のmatrix、E1のX2の処理記述、E7の係数非依存性がその例である（§4.2、§2.5、§4.1、§4.6）。
4. **独立性のために課した性質が、自然な構成の障害そのものになることがあった。** J1の未完了leg、Q1の非一様性がその例である（§4.4、§4.7）。
5. **否定範囲の記録は全系列で厳密で、過度な一般化は防がれていた。** この慣行は維持すべきである。

### 7.2 一般化できないこと

1. 個々の障害（K1～K8）は、それぞれの文法・ansatz・範囲に限られる。CARを使う構成一般、bus付き構成一般、Richardson–Gaudin模型一般、NA/NBの全可能性について、不可能性は示されていない。
2. 「保持0件」の繰返しは、新しい構成原理が存在しないことの証拠ではない。D1・D2の範囲に新原理があるかどうかは、この記録からは決まらない。
3. J1・Q1の一時保留は追加探索の保留であり、研究価値の否定ではない。再開条件は記録のとおりで、本書はそれを変更しない。
4. 新規性の有無は正式に認定されていない。既知法への還元の判定は、各記録が式とpathで示した範囲に限られる。
5. 第一研究・第二研究・PR Track A/Bの結果を、新アルゴリズム探索の失敗の原因として再評価しない。

## 8. 正式状態の一覧（今回変更していない）

| 対象 | 状態 | 根拠 |
|---|---|---|
| J1の追加探索 | `PAUSED_PENDING_NEW_MECHANISM` | [J1保留][E5-pause] |
| Q1の追加探索 | `PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE`（Q1は未採択の研究課題案） | [Q1保留][E9-pause] |
| T1 | 独立研究候補から撤回（T1-D） | [T1-D][E0-t1d] |
| E1、E6、E7・E8 | 新しい正式状態の文字列なし。限定結果をGPT／ユーザーへ返却 | 各handoff |
| P1*固定word | `NO_SOLUTION_IN_FIXED_ANSATZ`（固定ansatzの科学分類） | [実行報告][E3-report] |
| 第一研究・第二研究、U1/U3/U4、FS-R1 Phase B、PR Track A/B、PR側の停止系列 | 既存の記録どおり | [E1][E1-handoff] §5 |

<!-- fixed-source-references -->

[E0-matrix]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_exploration/quantum_chemistry_independent_topics_20261016/candidate_evidence_matrix.md
[E0-status]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17cf4073094c713257d6eabadb440d6d973a9229/docs/current_research_status.md
[E0-t1d]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/research_exploration/t1_withdrawal_20261016/decision_record.md
[E0-topics]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_exploration/quantum_chemistry_independent_topics_20261016/candidate_handoff.md
[E0-u4]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/decision_record.md
[E1-cand]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/constructive_principle_candidates.md
[E1-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/research_decision_handoff.md
[E1-map]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/problem_and_failure_map.md
[E2-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/research_hypothesis_handoff.md
[E2-map]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/principle_ideation_map.md
[E2-prov]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/provenance.json
[E3-audit]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/37e5002a7e32a7f0c3f70cdd098f2ee145b828e7/docs/research_exploration/p1star_unsat_limited_static_audit_20261017/limited_static_audit.md
[E3-contract]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md
[E3-report]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/scientific_execution_report.md
[E4-cubic]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5110d347e1f032c9093430b3def13b3391602cdd/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md
[E5-20handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c7d3f077d634e4165b7cd326bac7caa1ae04ff66/docs/research_exploration/p1star_j1_paper_feasibility_20261017/decision_handoff.md
[E5-20math]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c7d3f077d634e4165b7cd326bac7caa1ae04ff66/docs/research_exploration/p1star_j1_paper_feasibility_20261017/mathematical_feasibility_record.md
[E5-finalhandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/143f50d3bf2636b1433d9b70a844bbdc22832a6e/docs/research_exploration/p1star_j1_final_limited_search_20261017/research_decision_handoff.md
[E5-finalmath]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/143f50d3bf2636b1433d9b70a844bbdc22832a6e/docs/research_exploration/p1star_j1_final_limited_search_20261017/limited_construction_record.md
[E5-j1handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/dd36794069f2f8063d3eba6c7e3fcc989d9b0ceb/docs/research_exploration/p1star_joint_loop_principles_20261017/research_decision_handoff.md
[E5-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/95be62395d3740db39b6830c68f4fd1e25f595ee/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[E6-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/813fd44bfd70f9bc4266e35cc8e4dd28037dedce/docs/research_exploration/independent_construction_principles_20261017/research_hypothesis_handoff.md
[E6-hyp]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/813fd44bfd70f9bc4266e35cc8e4dd28037dedce/docs/research_exploration/independent_construction_principles_20261017/construction_hypotheses.md
[E7-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5c49323957f1bfa2a24cb2786a0ebd1f3932925/docs/research_exploration/bottleneck_operation_design_20261017/decision_handoff.md
[E7-prior]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5c49323957f1bfa2a24cb2786a0ebd1f3932925/docs/research_exploration/bottleneck_operation_design_20261017/prior_art_and_limits.md
[E7-task]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5c49323957f1bfa2a24cb2786a0ebd1f3932925/docs/research_exploration/bottleneck_operation_design_20261017/operation_design_task.md
[E8-car]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c23e9bc6028c52761e6220b91e2d1e1bd8b3ceaf/docs/research_exploration/pair_collision_cg_verification_20261017/independent_car_derivation.md
[E8-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c23e9bc6028c52761e6220b91e2d1e1bd8b3ceaf/docs/research_exploration/pair_collision_cg_verification_20261017/verification_handoff.md
[E8-small]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c23e9bc6028c52761e6220b91e2d1e1bd8b3ceaf/docs/research_exploration/pair_collision_cg_verification_20261017/small_example_and_control.md
[E9-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/research_handoff.md
[E9-inshandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/verification_handoff.md
[E9-insobs]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/insertion_obstruction_and_checks.md
[E9-insparent]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/parent_form_factor_derivation.md
[E9-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17cf4073094c713257d6eabadb440d6d973a9229/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
[E9-prior]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/prior_art_comparison.md
[E9-problem]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/research_problem.md
[E9-ricderiv]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/riccati_paper_derivation.md
[E9-ricknown]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/known_reductions_and_limits.md
[E9-survey]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/unresolved_problem_survey.md
[PR-claude1016]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dbe51f1870cd069b952cc92593833d355da10e28/docs/reviews/quantum_chemistry_pf/qc_sos_pf_post_k05_claude_scientific_review_20261016.md
[PR-coverage]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_coverage_map.md
[PR-exactground]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/docs/reviews/quantum_chemistry_pf/qc_exact_ground_state_pf_direction_rereview_2026-10-14.md
[PR-foundation]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/acfa8674d51ede1d5cd50f1b49873e67de5b71b9/docs/research/qc_existing_technical_foundation_map_20261016.md
[PR-gpt1016]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dbe51f1870cd069b952cc92593833d355da10e28/docs/reviews/quantum_chemistry_pf/qc_sos_pf_post_k05_gpt_scientific_review_20261016.md
[PR-k0]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/0d460c54f3bf54ea46d4d8129f6702703c4bb217/docs/research/qc_new_algorithm_static_screen_k0_20261016/technical_report.md
[PR-mreview]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/docs/reviews/quantum_chemistry_pf/qc_m_k0_claude_scientific_rereview_and_direction_20261015.md
[PR-pfpause]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/artifacts/qc_pf_exploration_state_adoption/2026-10-15/decision.json
[PR-purpose]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/docs/research/%E7%A0%94%E7%A9%B6%E7%9B%AE%E7%9A%84%E3%83%BB%E7%A0%94%E7%A9%B6%E8%AA%B2%E9%A1%8C.md
[PR-sosdecision]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dbe51f1870cd069b952cc92593833d355da10e28/artifacts/qc_sos_pf_a3_state_adoption/2026-10-16/decision.json
[PR-transition]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_state_transition.md
