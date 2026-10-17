# 研究戦略の再設計：判断用handoff

2026-10-17 JST。作成：Claude Code（Codex側の技術調査・資料作成の役割）。読み手：GPT／ユーザー。
**本書は判断材料であり、研究戦略の正式採択ではない。** 推奨した戦略・プロトコル・最初の作業は、いずれも未承認の提案である。
J1の`PAUSED_PENDING_NEW_MECHANISM`、Q1の`PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE`、その他の既存研究のSOURCE・結果・grant・承認・科学契約・STOP・PAUSEは変更していない。
新規科学計算、solver、数値対角化、記号計算プログラム、回路build、新アルゴリズム候補の構成探索は0件。

## 1. 五つの問いへの回答

### Q1. なぜ独立した新アルゴリズムの成立に至らなかったのか

PR側の新アルゴリズム仮説H1～H4（2026-10-16）と、E0～E9の系列（10-16～17）は、どれも「独立した生成規則が残らない」形で終わった。PR側でそれ以前に閉じた方向（10-13～16）も、多くは既知法への還元か生成規則の欠如で閉じた（[横断分析](research_exploration_retrospective.md) §2.2）。
**決め手は毎回、許可された入力と操作から作用を作る生成規則の段階にあった。** 規則を書けた構成は既知の生成規則と一致し（J1 20-pulseは汎用echo、J1 G2はStrang分割、二電子補助衝突はCG／Paldus、NBはTDCC）、規則を固定した構成は低次で不成立だった（P1*固定word、J1 G1、Q1のG・G_F・G_S）。規則を書けない発想は残らなかった（X1、P5・P7・P8、NA、Q1の共通unitary B）。
背景には次の要因がある（詳細は[方法論の分析](exploration_methodology_analysis.md) §2）。

1. 発想の単位が「使えそうな数学的関係・表現」で、生成規則と必要情報の取得法が候補選定の後に回った（RC1・RC2）。
2. 既知法への還元の手掛かりは初期の記録にあったが、確認は構成の後だった（RC3）。
3. P1*では、機構から導かれていない固定wordへ重い計算が先行し、紙上の低次事前解析は承認区分の外にあった（RC4）。
4. 新規性は機構の同一性で判定され、資源・保証という価値の基準が定義されていなかった（RC5）。
5. 独立性のために課した性質（J1の未完了leg、Q1の非一様性）が、試した自然な文法を壊した（RC6）。
6. 構造的な要因として、D1の範囲の構成は、生成子の係数依存性で局所型（PF・交換子合成・echo）、対称型（Schur／CG）、spectral型（固有問題・隠れ情報）に分かれ、どれも成熟した道具の領域に入った（RC9）。

### Q2. その原因のうち、探索方法の改善で回避できるものは何か

**回避できる見込みがあるもの**：還元の後期確認、情報取得法の後回し、計算の先行と紙上事前解析の欠落、命題の情報量の不足、照合作業の比重（RC2・RC3・RC4・RC7・RC10）。過去の決め手が全て紙上の短い確認だったことが根拠である。
**一部だけ回避できるもの**：生成規則の欠如、新規性基準の偏り、要件と障害の同根性、既知法の近くでの候補生成（RC1・RC5・RC6・RC8）。早く見つけられるが、越える手段があるかは問題の難しさに依る。
**方法では回避できないもの**：D1下の構成空間の成熟（RC9）と、個々の数学的問題の本来の難しさ。研究目的とaccess modelの判断に関わる。

### Q3. どのような種類の研究課題を、どのような方法で探索するのが適切か

**推奨1（主戦略）：B′ 最強baselineの具体的gapを起点にする。** D2の課題（絶対E0推定）について、等アクセスで全費用を戻した最強の既知baselineを最初に固定し、総費用又は保証の形を支配する特定の項で、文献上も改善余地が明示されているものを対象にする。
**推奨2（補助戦略）：A′ そのgapを、補題の大きさの未解決命題として定式化する。** 隠れ情報を要さず、最小例の成否が族の判断を変え、独立性の要件が自然な文法を壊さない命題に限る。
C（特殊構造）とD（異分野技法）は、gapを埋める道具の供給源として、プロトコルのscreeningを通して使う。比較と理由は[戦略比較](future_research_strategies.md) §§8–9。
推奨1は新しい発想ではない。新アルゴリズム探索の前に、PR側のGPTレビュー（2026-10-15、10-16）が、「先に強い比較対照・タスク・量子資源のレバーを選ぶ」こと、「そのレバーに効く具体的な構成規則だけを候補にする」こと、7項目の事前条件を推奨していた[PR-gpt1016] [PR-mreview]。E0～E9はこれを候補作成前の固定手順としては実装しなかった。本書の提案は、それを段階・screening・gateとして実装することである（[横断分析](research_exploration_retrospective.md) §2.3）。
成果型は、新しい生成規則（O1）だけでなく、証明可能な資源差を持つ組合せ規則（O2）、より強い保証（O3）、構造classのアルゴリズム（O4）、構成classの特徴付け（O5）を事前に宣言して扱う。

### Q4. 次の研究候補について、いつ・何を・どの水準まで確認すれば先へ進めるか

[選定・検証プロトコル](research_selection_and_validation_protocol.md)のStage 0～8とGate A・B・Cによる。要点は次のとおり。

| 時点 | 確認すること | 水準 |
|---|---|---|
| Gate A（候補として保持） | 課題定義、等アクセスbaseline、価値軸、生成規則R、情報予算、係数依存性の型、紙上screening S1～S8 | Rが一例へ代入できる具体性。S3～S6で既知法へのR0・R1還元が見つからない。証明は不要 |
| Gate B（継続・保留・終了） | 事前に成功・失敗基準を固定した最小命題。失敗時は障害の一般化と脱出条件 | 最小命題の肯定的解決。脱出条件を満たす文法を書けなければ一時保留 |
| Gate C（正式採択・計算） | 一般化補題、計算量、有限精度、誤差、D2の全項目、全費用の等アクセス比較、GPTの独立性判断 | 正式採択の全条件。計算は判断を変える場合だけ |

### Q5. 推奨する戦略で最初に実施すべき具体的な作業は何か

**T0：一つの課題に対する「最強baselineとgapの台帳」の作成**（静的な文献・既存記録の調査）。
推奨する対象課題は、D2の「有限基底電子Hの絶対E0を、指定精度でD1の範囲で推定する」を端から端まで扱い、費用を部分課題（時間発展の1 step、step数、推定protocol、state準備・overlap）へ分解すること。
成果物は、task card、baseline card 3件以上、費用の分解、B′の三条件を満たすgapの一覧（補題の雛形と変わる判断付き）、GPTが選ぶための1～2件の推薦である。詳細は[戦略比較](future_research_strategies.md) §10。
補題の大きさのgapが一つも見つからない場合は、その結果自体が、新アルゴリズム研究の継続の可否を判断する材料になる。

## 2. 最も重要な教訓

**新規性を問う単位を「機構・表現」から「等アクセスbaselineに対する、生成規則と価値（資源・保証）の差」へ移し、それを構成の前に紙上で確認する。**
過去の決め手になった確認（完成blockへの書換え、対称性による保存量の関数への書換え、N=1の低次展開、代数構造と既知の枠組みとの照合、情報予算）は、どれも短い紙上の操作で、多くは初期の記録に手掛かりがあった。

## 3. 探索方法で変えるべき点

1. 起点を「発想・機構」から「task、最強baseline、gap」へ移す（Stage 0～2）。
2. 生成規則Rと情報予算を、研究候補の入場条件にする（Stage 3、S1）。
3. 紙上のscreening S1～S8を、計算・詳細検討より先に一括で行う（Stage 4）。紙上の最小例の手計算を、候補を検討する作業の承認範囲に含める（プロトコル§9.1、提案）。
4. 最初の命題を、失敗しても族に対する知見が残る形にし、「障害の一般化→脱出条件→次の文法」の順で進める。族ごとの試行上限を置く（Stage 5～6、プロトコル§8）。
5. 成果型O1～O5と価値軸を事前に宣言し、独立性は操作の不変量で判定する（プロトコル§2.1、§5）。
6. GPTの判断点をGate A・B・Cの三つに集約する。過去の系列では紙上の小さな一段ごとにSTOPが入った。

## 4. GPT／ユーザーによる正式判断が必要な事項

1. 推奨戦略（B′＋A′）を採るか。別の戦略を採るか。
2. 成果型をO1以外（O2～O5）へ広げ、独立成果として扱うか。
3. [選定・検証プロトコル](research_selection_and_validation_protocol.md)（Stage・Gate・S1～S8・試行上限）を今後の運用として採るか。試行上限の値。
4. 紙上の最小例の手計算を、候補を検討する作業の承認範囲に含めるか（プロトコル§9.1）。
5. T0の実施の可否、対象課題、範囲、停止点。
6. D1の範囲で、外部bus等の新しいaccess modelを探索の対象に含めるか。D1・D2の変更は提案していない。
7. J1・Q1の再開条件を、新しい候補を作るときの設計上の参照に使ってよいか。これはJ1・Q1の再開ではない。
8. 既存研究資産（Track A/B、第一・第二研究の未完了部分）の情報価値を、新テーマと比べる作業を行うか。PR側のGPTレビューが10-16に推奨していた。
9. T0の結果を受けて、新アルゴリズム研究を継続するか、一時停止するか。

## 5. 研究状態の保全

| 対象 | 状態 |
|---|---|
| J1の追加探索 | `PAUSED_PENDING_NEW_MECHANISM`（変更なし）[E5-pause] |
| Q1の追加探索 | `PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE`（変更なし。Q1は未採択の研究課題案）[E9-pause] |
| T1 | T1-Dの撤回（変更なし） |
| 第一・第二研究、U1/U3/U4、FS-R1 Phase B、PR Track A/B、PR側の停止系列、P1～P8、NA/NB、二電子補助衝突 | 既存の記録どおり（変更なし） |

過去の保留・終了の理由と再開条件を書き換えていない。本作業の分析は、既存の正式判断の再審査ではない。

## 6. 読む順序とSOURCE

1. 本書。
2. [横断分析](research_exploration_retrospective.md)：研究ごとの目的・成果・障害・状態、成立性と独立性の区別、数学的知見、一般化の範囲。
3. [方法論の分析](exploration_methodology_analysis.md)：共通の根本原因RC1～RC10、comment.md B1～B4への回答、改善策。
4. [戦略比較](future_research_strategies.md)：戦略A～D（と補助E）の比較、推奨、未確認事項、最初の作業T0。
5. [選定・検証プロトコル](research_selection_and_validation_protocol.md)：候補の必要条件、段階ごとの確認、役割分担、進む条件、保留・中止条件、計算を提案する条件。
6. [source_registry.json](source_registry.json)、[static_audit.json](static_audit.json)、[provenance.json](provenance.json)。

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。
branch：`qc-research-strategy-redesign-20261017`。起点：`17cf4073094c713257d6eabadb440d6d973a9229`（Q1正式一時保留、研究系列の先端）。
固定参照13 commitは、GitHubから独立に取得した空のrepositoryで照合した。各fileのorigin/result commitとverified snapshot commit、Git blob、bytes、SHA-256、commit固定rawの照合結果はsource_registryに別fieldで記録した。
本書を含む公開commitの40文字SHAは、自己参照を避けて本書に埋め込まない。公開後の照合結果は、作業報告に別途記録する。

**Mandatory STOP：成果物の公開・照合後に停止する。** 新しいアルゴリズム候補の探索、科学計算、実装、正式な研究方針の変更、詳細科学レビューへ自動進行しない。

<!-- fixed-source-references -->

[E5-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/95be62395d3740db39b6830c68f4fd1e25f595ee/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[E9-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17cf4073094c713257d6eabadb440d6d973a9229/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
[PR-gpt1016]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dbe51f1870cd069b952cc92593833d355da10e28/docs/reviews/quantum_chemistry_pf/qc_sos_pf_post_k05_gpt_scientific_review_20261016.md
[PR-mreview]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/docs/reviews/quantum_chemistry_pf/qc_m_k0_claude_scientific_rereview_and_direction_20261015.md
