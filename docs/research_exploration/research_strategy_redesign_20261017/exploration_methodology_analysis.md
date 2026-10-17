# 探索方法の問題点と改善策

2026-10-17 JST。作成：Claude Code（Codex側の技術調査・資料作成の役割）。
対象は、2026-10-16から10-17に行った新アルゴリズム探索の系列E0～E9である。系列の内容と根拠は[横断分析](research_exploration_retrospective.md)にまとめた。
本書は過去の正式判断を再審査・変更しない。J1の`PAUSED_PENDING_NEW_MECHANISM`、Q1の`PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE`、その他の状態を維持する。

記述の区別：固定SOURCEに書かれている事実には出典を付ける。複数の系列を比べて導いた解釈は【分析】と明記する。
【分析】はGPT／ユーザーの判断材料として出すCodex側の見解であり、科学的結論の確定ではない。

## 1. 各系列の終わり方

| 系列 | 最後に決め手となった点 | 種類 | 決め手になった確認 |
|---|---|---|---|
| E0 T1（3af746a、00311e0） | 既知のlogical accreditationと位相推定法の接続で、独立した差分と資源上の利益が未確立 | 独立性・価値 | 候補を作った資料自身の記述と、ユーザーの判断[E0-t1d] |
| E1 障害起点（60bf810） | X1は既知compilerを越える選択器を提示できない。X2は既知の測定法へ帰着 | 規則の不足、還元 | 一次文献・公開実装との照合[E1-handoff] |
| E2 P1～P8（67d9e3b） | P1*だけを分類Bで保持。C 4件は構成の核が既知、D 3件は必要な操作が未定義 | 選別 | 既知法照合と操作の定義可能性[E2-handoff] |
| E3・E4 P1*固定word（1771564～5110d34） | N=1必要条件の3次残差が全実振幅で非零。既知の単独閉路＋対称Strang積は形式4次を満たす | 固定ansatzの具体的な不成立。比較構成は既知 | exact solver（box内UNSAT）の後の紙上導出[E3-report] [E4-cubic] |
| E5 J1（dd36794～95be623） | 20-pulseは完成gate＋汎用echoへexactに書換え。G1は3次で不成立。G2は既知rectangleのStrang分割 | 還元（20-pulse、G2）、限定的な不成立（G1） | 紙上の書換えと低次展開[E5-20handoff] [E5-finalhandoff] |
| E6 NA/NB（813fd44） | NAは独立した生成段階を構成できない。NBの中核は既知TDCCで、chart移送は未知振幅なしに定義できない | 規則の不足、還元＋情報取得の欠如 | 紙上代入と一次文献[E6-handoff] |
| E7・E8 二電子補助衝突（b5c4932、c23e9bc） | total spinの関数として、CG／Paldus＋3値phaseへ明示的に還元 | 還元 | CAR／spinの恒等式と独立紙上検証[E7-handoff] [E8-handoff] |
| E9 Q1（3abef73～17cf407） | 文法G・G_F・G_Sが限定的に不成立。書換え可能部分は既知。共通unitary Bは未構成 | 限定的な不成立＋部分還元＋規則の不足 | 紙上導出[E9-inshandoff] [E9-richandoff] |

どの系列でも、最終的な決め手は短い紙上の確認だった。計算機による科学計算を行ったのはE3だけで、その結論は後の紙上導出に包含された（§2 RC4）。
PR側でも、E0より前の新アルゴリズム仮説H1～H4の静的K0が、総合技術判定`NO_GO_NO_INDEPENDENT_GENERATION_RULE`で終わっていた[PR-transition]。PR側の他の方向（第一候補、H-E1、M、SOS-PF等）も、既知法への還元か生成規則の欠如で閉じた（[横断分析](research_exploration_retrospective.md) §2.2）。

### 1.1 先に出されていた指摘との関係

新アルゴリズム探索の前に、PR側のGPTレビューは、次の候補の事前条件として、改善レバー、具体的生成写像、同じ合法情報・価格の強対照、情報モデル、スケールへの機構、native／FT費用の経路、明示的なSTOP条件を挙げていた（[PR M再評価][PR-mreview] §7.3）。
翌日のGPTレビューは「先に強い比較対照・タスク・量子資源のレバーを選ぶ」こと、「そのレバーに効く具体的な構成規則だけを候補にする」ことを推奨し、同型のK0静的監査を延々と繰り返すより、研究の問いと資源レバーが固まった節目で科学レビューへ戻すよう述べた（[PR GPTレビュー][PR-gpt1016]）。
Claudeレビューは、PFの係数・分割・表現の設計空間が先行研究で密に埋まっていると指摘した（[PR Claudeレビュー][PR-claude1016] §7.4）。

【分析】本書の改善策の多くは、これらの指摘と同じ方向にある。本書が加えるのは、E0～E9でそれらが手順として実装されなかった経緯の確認（§2）と、実装するための段階・screening・判定基準の具体化（[プロトコル](research_selection_and_validation_protocol.md)）である。

## 2. 共通する根本原因

### RC1 「関係・表現」から始め、「生成規則」が後回しになった

各系列の出発点は、利用できそうな数学的関係や表現だった。CARの反交換関係（P1*、J1）、非可換な場の運動量（NA）、nilpotentな対数振幅（NB）、pairing basisのlevel再帰（Q1）である。
失敗の決め手は毎回、その関係を**許可された入力と操作から実際の操作列として作る規則**の段階にあった。

- 規則を書けた場合、その規則は既知の生成規則と一致した。J1 20-pulseは完成gateの汎用echo[E5-20handoff]、G2は既知rectangleのStrang分割[E5-finalhandoff]、衝突はCG／Paldus[E7-handoff]、NBはTDCC[E6-handoff]。
- 規則を固定した場合、その規則は低次で不成立だった。P1*固定word[E4-cubic]、J1のG1[E5-finalhandoff]、Q1のG・G_F・G_S[E9-pause]。
- 規則を書けなかった場合、候補は残らなかった。X1[E1-handoff]、P5・P7・P8[E2-handoff]、NA[E6-handoff]、Q1の共通unitary B[E9-pause]。

E1の方法には、規則を作り出す段階がなかった。新しい証明は承認範囲の外で、将来の規則は「外部の新しい証拠」として提示されることが期待された[E1-handoff] §4。
J1とQ1の再開条件も、「既知法に還元されない具体的な規則が提示されること」という形である[E5-pause] [E9-pause]。

【分析】独立性を問う単位が「機構・表現」に置かれ、成立性を決める単位が「生成規則」にあった。両者がずれていたため、発想段階では有望に見えた候補が、規則の段階で上の三つのどれかに終わった。

### RC2 必要な情報の取得法を、候補選定の後で調べた

各系列は、全Hの発展oracle、exact ground、gap、Bethe rootsなどを無料入力にしないことを明示していた（例：[P1～P8][E2-handoff]のD2欄、[Q1定式化][E9-handoff] §1）。
この方針は正しく守られた。その結果、取得法のない情報が必要な構成は、検討の後半で成立しなくなった。
NBのchart間移送は未知振幅を要し[E6-handoff]、NAの修正案は多電子固有問題の供給を要し[E6-hyp] §2.4、Q1のY・Bはchild spectrum情報を外部入力しないと定義できなかった[E9-pause]。

【分析】隠れoracleを使わなかったことは正しい。原因は、「必要な情報をすべて列挙し、取得法を確認する」作業が候補保持の条件になっていなかったことである。

### RC3 既知法への還元を構成の後で確認した。還元の手掛かりは初期にあった

還元はどれも、構成を作った同じ作業か、その直後の作業で判明した（§3.2の表）。決め手になった確認は、完成blockへの書換え、対称性による保存量の関数への書換え、代数構造と既知の枠組みとの照合で、いずれも短い紙上の操作だった。
手掛かりは、多くの場合、構成の前に記録されていた。

- E2では、文献検索の前に固定したPhase A記録に、P3「possible complete reduction」、P4「likely Hellmann-Feynman」、P6「likely known control variates」、P5「no explicit allowed resolver」、P7「lift and recovery not specified」、P8「no distinct operational transfer rule」が既に書かれていた[E2-prov]。
- E0では、候補を作った資料自身が、近接研究は適用可能性を述べており「単純な接続だけなら差分は弱い」と書いていた[E0-matrix]。
- E5のJ1仮説は、DCGを「最も強い還元リスク」とし、既知の完成閉路＋汎用echoへ説明が尽きる場合は取り下げると事前に書いていた[E5-j1prior] [E5-j1handoff]。20-pulse cellは、完成したblockを反対向きに共役する形をしていた[E5-20math]。
- E7の衝突の生成子は、係数に依存せず、同時軌道回転で不変だった[E7-task]。

【分析】これらの確認を、構成を作る前の固定手順として行えば、構成作業の前に還元の候補を把握できた可能性がある。
特にP1*では、最も単純な既知構成（単独閉路＋対称Strang積）が目標を形式4次まで満たすことが、計算と独立検証の後で確認された[E4-cubic]。

### RC4 固定ansatzが機構から導かれず、承認の区分によって紙上の事前解析が抜けた

P1*の固定wordは「各primitiveを同じ回数訪れる短いinterleavingを仕様として選んだ。解の存在や独立性を計算して選んだwordではない」と記録されている[E3-contract]。
紙上検証は、既知の比較構成がA/Bを4回、C/Dを2回使うことを指摘し、固定wordの反例でも成功例でもないと明記した[E4-cubic] §6。
試験はN=1、すなわち一体の水準で失敗しており、P1*の核心であるCARの二体構造は関与していない[E4-cubic] §7。

承認の区分も、安い確認を高価な工程の後ろに置いた。発想段階では「new theorem, correctness proof or counterexample proof」が承認外で[E2-prov]、P1*の契約段階では「new Magnus or Lie-word coefficients」「new CAR normal forms or sector algebra calculations」「equation generation, solving or counterexample search」が承認外だった[E3-prov]。
一方、環境binding、技術基盤、資源契約比較、driver、freeze、実行承認は段階ごとに承認された。
Git履歴では、契約草案（1771564、10-17 00:43）からUNSATの記録（a63c6dc、03:34）まで10 commit、約3時間を要した。最終attemptの計算自体は約310秒、worker RSS peakは約338 MiBだった[E3-report]。
準備段階では2回`NOT_READY`と判定された。exact実数判定backend・checker・資源制限の実行経路が揃っていないこと[E3-binding]と、16 GiBのRAM制限と保存中間term 20万の上限を確認できていないこと[E3-foundation]が理由である。契約の予算は「計算量の実測値・必要資源の見積り結果ではなく、runを有限にする技術上限案」だった[E3-contract]。実行中に拘束になったのは、出力trace（19 MiB）、管理term数（20万）、不要な積の列挙で、3回の技術修正を要した[E3-report] [E3-resource]。
その後の紙上導出は、契約で固定済みの入力だけを使い、N=1の必要条件から、全実振幅について3次で不成立になることを示した[E4-cubic]。

【分析】人手による短い導出と機械による科学計算が同じ承認区分に入っていたため、「紙上の低次事前解析」という工程が手順から抜け落ちた。ansatzが機構から導かれていなかったため、計算の結論は機構について情報を持たなかった。
紙上の低次展開を先に行えば、同じ判断に、より強い形で到達できた可能性が高い。

PR側の第一候補（一体項再配分PF）では、10-14に`REDUCES_TO_KNOWN`と判定された後、GPTの判断に基づき、別のscope（有限stepの成分の有用性）の計算が行われた。結果は、登録した10%費用改善の基準を4条件とも満たさない`NO_UNIFORM_REGISTERED_COMPONENT_GAIN`だった。途中で独立checkerの数値許容の失敗とcheckerの修正・再監査を経ている（[PR研究目的・研究課題][PR-purpose]）。
【分析】この計算は承認された範囲で正しく行われたが、第一候補の現固定構成CLOSEDという判断を変えなかった。計算を提案する前に「どの結果ならどの判断が変わるか」を表にする条件（[プロトコル](research_selection_and_validation_protocol.md) §9）は、このような場合にも適用できる。

### RC5 新規性の基準が機構の同一性に偏り、価値の基準が定義されていなかった

複数の系列が、発想段階では資源優位を必須条件にしないと明記した（[P1～P8 provenance][E2-prov]の`proof_or_resource_advantage_required_at_ideation: false`、[NA/NB][E6-handoff]）。一方で独立性は、生成の仕組みが既知法と異なるかで判定した。
J1の再開条件は「CARが目標二体信号の生成と3次bus残差の相殺の**両方**に不可欠」という機構の条件である[E5-pause]。
J1が扱った局所目標（double-excitation gate）は、同じaccessの既知構成でfull Fockにおいてexactに作れる対象だった[E5-20math]。

【分析】この組合せでは、既知の部品を使っても証明可能な資源・保証の差を持つ構成（成果型O2・O3）は評価の対象外になり、新しい機構でも価値のない構成は評価の対象になる。
新規性の成否が、価値のある問題の成否と直結しない設計だった。§3.3で詳しく扱う。

PR側のGPTレビューは「改善レバー」と「強対照」を候補の事前条件に挙げていた（§1.1）。E2は、高リスクの発想を早く捨てないために、ユーザーの承認により発想段階の資源優位・証明の要求を外した[E2-prov]。
【分析】発想を広く保つことと、候補として検証作業を割り当てる前にレバーと強対照を確認することは両立する。過去の系列では、前者を採ったときに後者の確認も候補作成の後に回った。

### RC6 独立性のために課した性質が、自然な構成の障害そのものになった

- J1：完成rectangleを使えば最高bus次数は消えるが、既知gate＋echoになる。未完了legにすると一体Lieの3次障害が残る。それを汎用対称化で消すと、CAR固有の相殺という根拠がなくなる。記録はこの境界を明示している[E5-finalmath]。
- Q1：uniform準位は既知のCG／Schur経路へ退化するため、Q1は準位の非一様性を要件にした[E9-prior]。文法GとG_Fの障害は、どちらも非一様性 \([\mathsf d,J]\ne0\) から生じた[E9-insobs] [E9-ricderiv]。

【分析】既知法を避けるために課した性質（未完了leg、非一様性）が、試した自然な文法を壊した。障害を除くと既知法に戻る。
この「挟み撃ち」は、独立性の要件を決めた時点で予見できる種類の構造である。J1の記録は、bus次数の補題（一体factor×線形busの三重Lie語の最高次係数は一体の入れ子交換子）からこの構造が導かれることを示した[E5-finalmath] §2.1。
新しい規則は、その性質を直接扱う手段を持つ必要がある。最初の命題は、その手段そのものを問う形にするべきだった。

### RC7 最初の命題の「大きさ」は小さかったが、「情報量」が合っていなかった

最初の確認は小さく取られていた（N=1、4 modes、交換対1個、L=4・m=2）。大きさの問題ではない。
問題は、命題の結果が次の判断をどう変えるかである。P1*の命題は、機構から導かれていない固定wordの成否だった（RC4）。
Q1の最小例（L=4・m=2）は、成功するには最初から核心の共通unitary Bが必要で、そこでの肯定的結果も一般Lの成果とはしない設計だった[E9-minimal]。失敗しても部分的な成果が残りにくかった。

【分析】J1の最終探索は、障害を構成classの性質として書き、次の文法が満たすべき4条件を導いた[E5-finalhandoff]。この「障害の一般化→脱出条件」の形を最初から命題設計に入れると、失敗の情報量が増える。

### RC8 枠組みを毎回変え、既知法の近くで候補を作った

E0～E9は、独立テーマ、障害起点、異分野の機構、独立構成原理、ボトルネック操作、未解決問題と、枠組みを変えながら約20時間で進んだ（2026-10-16 22:22の3af746aから10-17 18:23の17cf407まで）。
各系列はSTOPとGPT／ユーザーの判断で区切られ、複数段に進んだのはP1*～J1とQ1だけだった。

候補の作り方にも共通点がある。
T1は既知論文の対象外の記述から作られた[E0-landscape]。E1の障害O1～O5は本プロジェクト自身の過去の実験・監査から抽出され、5件中3件は科学的に閉じたからではなく既存研究の担当範囲として除外され、残る2件にそれぞれ1件の仮説を置いた[E1-map] §7。
Q1の「未解決」は、文献が明示する未閉鎖の命題ではなく、「11文献の範囲でこの契約を満たす構成が見つからない」ことに依っていた[E9-problem] [E9-survey]。

PR側では、新アルゴリズム仮説H1の式(1)～(3)が、SOS-PF K0と一体再配分の事前監査に既にあった（[PR K0][PR-k0]）。内部の既存記録との重複である。
同じ記号が別の意味で使われる例も多く、PR側の資料自身が「今回の観点C1〜C5は、旧候補C1〜C4、Track B内部D1〜D3、第2研究Direction C、固定条件D1/D2とは別のラベルである」と警告している（[PR探索範囲表][PR-coverage]）。

【分析】どの枠組みでも、候補は既知法との差分として定義された。差分として定義された候補は、既知法へ還元されやすい。
また、未解決性の程度が外部の基準で校正されていなかったため、課題の難しさを事前に見積もれなかった。内部記録との照合と、repository・commitを付けたIDの付け方も、候補を作る前の工程として必要である。枠組みを変えてもRC1～RC7は変わらなかった。

### RC9 D1の範囲で、構成の空間が成熟している

D1はblock-encoding／qubitization中心への無断の移行を禁じる。その範囲で主に残る構成は、PF系、測定・推定protocol、追加accessとしての外部bus等である。
外部busを使うP1*は、新しい制御accessを研究対象に含めるかというGPTの判断事項を伴っていた[E2-handoff]。

【分析】過去の構成は、生成子が係数にどう依存するかで三つの型に分かれ、それぞれ既知の道具の領域に入った。

| 型 | 例 | 行き着いた先 |
|---|---|---|
| 局所型：係数で重み付けした局所的な生成子の積 | P1*、J1、NAの分割修正 | PF・交換子合成・echo・Strangへの還元、又は低次の障害[E4-cubic] [E5-finalhandoff] [E6-hyp] |
| 対称型：係数に依存しない、対称性で決まる生成子 | 二電子補助衝突J_N。Q1が避けたuniform準位の場合 | Schur／CG／Paldusへの還元。衝突では係数への依存が状態準備へ移った[E7-task] [E9-prior] |
| spectral型：係数に依存し、固有問題の解を要する生成子 | NAの対角化修正、NBのchart移送、Q1のY・B | 隠れ情報（固有値・固有vector・振幅）の要求[E6-hyp] [E6-handoff] [E9-pause] |

この分類は過去の有限個の構成についての観察であり、定理ではない。新しい原理は、局所型で既知の道具と異なる資源・誤差構造を持つか、spectral型の情報を構造classで効率よく得るか、これらに当たらない生成の仕方を持つ必要がある。
PR側のClaudeレビューも、PFの係数・分割・表現の設計空間が先行研究で密に埋まっていること、低energy構造による大きな既知の利得がblock-encoding側にあることを指摘していた[PR-claude1016]。
これは探索方法では回避できない構造的な要因である。D1を変える提案はしない。範囲の確認はGPT／ユーザーの判断事項とする（[handoff](research_strategy_handoff.md) §4）。

### RC10 同一性照合の記録が大きく、研究判断はそれで変わらなかった

各系列は、source registry、static audit、provenance、独立fetch照合を作成した。
E0～E9の16の資料directory（P1*の実行系列を除く）では、JSONの記録が合計約698 KB、Markdown本文が合計約486 KBだった（固定commitのGit treeのbyte数）。Q1の4 directoryでは、JSONが約166 KB、本文が約104 KBである。

【分析】byte数は作業時間を直接示さない。ただし記録の範囲では、照合作業が研究判断を変えた例は見当たらない。
同一性照合とGitHub handoffは既存規約であり、維持する。提案は、照合を道具で自動化し、研究の中核（生成規則・screening・最小命題）に使う時間を確保することである。照合の要件そのものは変えない。

## 3. comment.md B1～B4への回答

### 3.1 B1：数学的表現と計算可能な操作の隔たり

| 問い | 過去の記録から分かること |
|---|---|
| 恒等式や表現変換の存在だけで、実装可能と考えていなかったか | 研究記録は実装可能性を仮定しないよう明示していた。「零平均変位は演算子値の閉鎖を保証しない」[E2-handoff]、「式の交換が物理的なpath変換ではなく」[E5-j1handoff]、「係数軸の直交回転と、実装可能な軌道ユニタリによる\(\operatorname{Ad}_{U}\)変換を混同しない」[E6-hyp] §2.4。問題は、生成規則がなくても分類Bとして保持できたことにある（RC1）。 |
| unitary、isometry、state preparation、block diagonalizationを混同していなかったか | 区別していた。二電子の抽出→SWAP→逆抽出は反対称空間でunitaryにならない[E7-task] §4。有限角度でのtarget channelはunitary evolutionではない[E8-handoff] §2。Q1は共通unitary Bと個別の対角化を区別した[E9-inshandoff]。ただし区別が明示されたのは仕様化の段階で、発想段階の課題定義には含まれていなかった。 |
| 計算量の大きい部分を、暗黙のoracleや既知変換として与えていなかったか | 明示的に禁じていた（RC2）。禁止を守った結果、取得法のない情報が不成立の理由になった。 |
| 未知の固有値・固有vector・Bethe roots・振幅の取得法まで考えたか | Q1は、child root、全固有vector、spectral projectorを外部入力にしない条件を明示し、それが保留理由の中心になった[E9-pause]。取得法の検討は候補選定の後だった。 |

改善：生成規則Rと情報予算を候補の入場条件にする（[プロトコル](research_selection_and_validation_protocol.md) Stage 3、S1）。目標出力の種類（unitary等）をStage 0で確定する（S7）。生成子の係数依存性の型（RC9）をStage 3で記録する。

### 3.2 B2：既知法への還元の発見時期

| 構成 | 還元先 | 還元の水準 | 判明した時点 | より早い段階で判別できた可能性のある確認【分析】 |
|---|---|---|---|---|
| P1*の比較構成 | 単独factor閉路（Spillerら）＋対称Strang積 | 生成の同値（既知構成そのもの） | 計算と独立検証の後（5110d34）[E4-cubic] | 最も単純な等アクセスbaselineの確認（S5）。67d9e3bは最も近い既存研究としてSpillerらの閉路bus gateを既に挙げていた[E2-handoff] |
| J1 20-pulse cell | 完成gateを反対向きに共役する汎用echo | 生成の同値（full Fockでexactに書換え） | 構成した同じ作業（c7d3f07）[E5-20handoff] | 完成block分解（S4）。部品を表現ρで先に簡約する2行程度の確認で判別できた可能性がある |
| J1 G2（24-pulse） | 可換aggregate forceの既知rectangleのStrang分割 | 生成規則の同値（1～3次で一致。有限ηでexactに同一のpathとはしない） | 構成した同じ作業（143f50d）[E5-finalhandoff] | S4・S5 |
| 二電子補助衝突 J_N | total spinの関数としてのCG／Paldus変換＋3値phase | 生成の同値（明示的な操作対応） | 仕様化した同じ作業（b5c4932）、独立検証（c23e9bc）[E7-handoff] [E8-handoff] | 対称性の確認（S3）。係数に依存せず同時軌道回転で不変な生成子は、保存量の関数になると予想できる |
| NB | CC／TDCC | 生成の中核が同値 | 同じ作業（813fd44）[E6-handoff] | 代数構造の同定（S6）。CCの指数形の時点で照合できる |
| X2 | 既知のfermionic joint測定＋energy重み、又は2-copy Bell測定＋別の符号取得 | 生成の同値 | 同じ作業（60bf810）[E1-handoff] | S6・S1（無料の符号・共分散が要るか） |
| T1 | logical accreditation＋位相推定 | 組合せの水準 | 候補を作った資料自身（3af746a）[E0-matrix] | S5 |
| Q1の書換え可能部分 | Sylvester逆、不変部分空間、block diagonalization、Bethe/F-basis | 部分還元 | 挿入則・Riccatiの紙上検討（2a3e689、d33fc8b）[E9-richandoff] | S6 |

問いへの回答：

- **どの段階で既知法との同値性を調べればよかったか。** 構成を作る前、生成規則を書いた直後（プロトコルStage 4）。上の表のどの還元も、規則の形から短い書換えで判明している。
- **単純な代数的簡約や対称性の確認で早期判別できたか。** 衝突はS3、J1 20-pulseとG2はS4で、構成の詳細に入る前に候補を挙げられた可能性がある【分析】。当時の記録で判別可能だったと断定はしない。
- **名前や表現の違いに影響されず、入力・操作・出力で比較できていたか。** 最終的には各系列が入力・操作・出力で比較し、名前の関連だけでは還元と判定しない原則を明記した[E7-prior]。用語（CAR交換対、非可換な場の運動量、chart貼合せ、level挿入）を入力・操作・出力へ翻訳したのは、構成の段階だった。翻訳を候補保持の前に行う（Stage 0・3）。
- **出力が同じことと、生成アルゴリズムが同値であることを区別できていたか。** 区別していた。G2は1～3次の一致に留め、有限ηで同一のpathとはしないと明記した[E5-finalhandoff]。衝突では、first-orderの機能（既知HME）と生成の手順（CG／Paldus）を分けた[E7-prior]。この区別を還元の水準R0～R3として記録様式に入れる（プロトコル§2.2）。
- **独立性の判定基準自体について。** J1の「比較代数で非零・CARで零」という診断は、full Fockで等しいblockへの置換で結果が変わり、独立性の十分条件ではなかった[E5-20handoff]。【分析】独立性の基準は、形式表示ではなく、操作列やunitaryの不変量として定義する必要がある。

### 3.3 B3：新規性の要求条件

**厳しすぎた可能性がある点【分析】**

1. 成果型が「独立した新構成原理」に限られていた。既知の部品を使う新しい組合せ規則（O2）、より強い保証（O3）、構造classに限定したアルゴリズム（O4）、構成classの特徴付け（O5）は、成果の候補として扱う枠がなかった。
2. P1～P8の分類Cは「構成の核が既知」を理由とした[E2-handoff]。核が既知でも新しい保証や組合せ規則が成果になり得るかは別の問いだが、その問いを立てる区分がなかった。
3. 二電子補助衝突の組合せ（反対称fermion空間での係数copy衝突とCG／Paldus＋3値phase）は、protocolとしての新規性と資源価値を網羅調査しないまま、新操作の課題としては保持しないとされた[E7-prior]。否定ではなく、評価の枠の外に残った。
4. J1の再開条件は機構の条件である[E5-pause]。等アクセスbaselineに対する資源の差を示す構成は、この条件を満たさなくても別の成果型になり得る。J1の再開条件そのものを変える提案はしない。

**緩すぎた可能性がある点【分析】**

1. 分類B（最初の数学的問いが具体的）は、生成規則がなくても保持できた。P1*はこの基準で保持され、固定wordが機構から導かれないまま計算に進んだ（RC4）。
2. J1の「独立性の第一点検」は、既知gate＋echoでも満たされる必要条件にすぎなかった[E5-20handoff]。
3. 価値軸が未定義だったため、新しい機構が見つかっても、それが研究成果として何を意味するかを判定する基準がなかった。

**改善**：新規性を「機構の差」と「価値の差」の二軸で判定し、成果型O1～O5を事前に宣言する（プロトコル§2.1）。
単なるgate連結・再命名・parameter調整はどの型にも入らないことを明記する。O2～O5を独立成果として認めるかは、GPT／ユーザーの判断事項である。科学的新規性の正式認定は、今回行わない。

### 3.4 B4：研究課題の大きさと難しさ

| 問い | 過去の記録から分かること |
|---|---|
| 初期段階から一般Hamiltonianへの適用を求めすぎていなかったか | D2は全系列で境界条件として保持された。最初の確認は小さく取られており、一般Hの要求が最初の確認を妨げた例は見当たらない。ただしE1の障害は「絶対E0を所定精度で読む」等のend-to-endの大きさで書かれ、補題の大きさに分けられていなかった[E1-map]。 |
| 全入力unitary、有限精度保証、多項式費用、絶対E0を同時に要求しすぎていなかったか | Q1の目標命題は、全入力coherent、operator残差ζ、poly(L,b,log(1/ζ))の費用、m=Θ(L)、任意のactive subset、非摂動区間を同時に含む[E9-problem]。最初の命題（L=4・m=2）は小さいが、核心の共通unitary Bを最初から要した。 |
| 最小例だけ成立して一般化不能な課題を選んでいなかったか | Q1は6次元の対角化だけでは一般Lの成果としないと明記していた[E9-handoff]。最小例の成立を一般化と取り違えた記録は見当たらない。 |
| 補題を適切な大きさに分割できていたか | J1は交換対1個・1～3次という補題から始めた[E5-j1handoff]。P1*は1次・2次の解族、3次残差という中間の補題を経ずに、4次条件全体をsolverに渡した。中間の補題は、後のGPTレビューと紙上検証で導かれた[E4-cubic]。 |

**探索段階で確認すること、正式採択前に証明することの分離**

| 段階 | 確認・証明すること |
|---|---|
| 探索段階（Gate Aまで） | 課題定義、等アクセスbaseline、価値軸の仮説、生成規則R、情報予算、係数依存性の型、S2の最小sector・低次条件、S3～S6の還元screening、独立性要件と障害の同根性の確認 |
| 最小命題（Gate Bまで） | 事前に固定した成功・失敗基準での最小命題。失敗時は障害の一般化と脱出条件 |
| 正式採択前（Gate Cまで） | 一般の大きさでの正しさ、計算量、有限精度、誤差、D2の全項目との接続、全費用を戻した等アクセス比較、GPTによる独立性判断 |

## 4. 改善策：原因・改善・適用段階

| 原因 | 改善策 | 適用段階（プロトコル） |
|---|---|---|
| RC1 生成規則の後回し | 生成規則Rを書けない発想は「アイデア」として記録し、研究候補にしない | Stage 3 |
| RC2 情報取得法の後回し | 必要な量の全列挙と取得法・費用の確認（情報予算） | Stage 3、S1 |
| RC3 還元の後期確認 | 等アクセスbaselineの事前記録と、S3～S6の還元screening。初期記録の還元の手掛かりを、そのまま判定項目にする | Stage 1、Stage 4 |
| RC4 恣意的ansatzと承認区分 | ansatzを機構から導く。最小例の手計算（S2）を、探索作業の承認範囲に含めることをGPT／ユーザーへ提案する。計算は判断を変える場合だけ | Stage 4、Stage 5、§9 |
| RC5 新規性基準の偏り | 成果型O1～O5と価値軸の事前宣言。機構・価値の二軸判定。独立性の基準を操作の不変量で定義する | Stage 2、S4 |
| RC6 独立性要件と障害の同根性 | 独立性の要件を決めたら、その要件が自然な文法を壊さないかを先に調べる（S8）。壊す場合は、その性質を扱う手段を最初の命題にする | Stage 2、Stage 4 |
| RC7 命題の情報量 | 族に対する命題を優先し、失敗時は障害の一般化と脱出条件を書く | Stage 5、Stage 6 |
| RC8 枠組みの入替えと既知法の近くでの候補生成 | 既知構成と障害の一覧を引き継ぐ。未解決性を外部の記述で校正する。族ごとの試行上限。新しい枠組みで何が変わるかを最初に書く | Stage 1、§8 |
| RC9 D1下の空間の成熟 | 方法では回避できない。成果型の範囲と探索するaccess modelをGPT／ユーザーが判断する | Gate A以前の方針判断 |
| RC10 照合作業の比重 | 照合を道具で自動化する。要件は変えない | 全段階 |

## 5. 回避できる原因と、できない原因（comment.md Q2）

**探索方法の改善で回避できる見込みのあるもの【分析】**：RC2、RC3、RC4、RC7、RC10。
いずれも、確認の順序・承認の区分・記録の書式を変えれば、同じ情報をより早く、より安く得られる。過去の決め手が全て紙上の短い確認だったことが根拠である（§1）。

**一部だけ回避できるもの**：RC1、RC5、RC6、RC8。
生成規則を入場条件にすれば、規則のない候補に時間を使うことは避けられる。しかし規則を見つける難しさは残る。
成果型を広げれば評価の枠は合うが、何を成果と認めるかは研究目的の判断である。
挟み撃ちの構造は早く見つけられるが、それを越える手段があるかは問題の難しさに依る。

**探索方法では回避できないもの**：RC9と、個々の数学的問題の本来の難しさ。
係数だけから全入力coherentな基底変換を作るQ1のような問題は、手順を変えても難しさは変わらない。D1下の構成空間の成熟も、研究目的とaccess modelの判断に関わる。

## 6. 研究目的の設定について

comment.mdは、研究継続ありきの結論を出さず、目的の設定自体も検討するよう求めている。過去の結果から言えることは次のとおり。

1. 「D1の範囲で、元の電子Hに対する独立した新構成原理」という目的は、PR側のH1～H4とE0～E9で、一度も最終保持に至らなかった。これは目的が誤りだという証拠ではない。同じ方法での継続が成果を生む根拠も、記録からは見つからない。
2. 目的を変えずに方法を変える選択、成果型をO2～O5へ広げる選択、探索するaccess modelの範囲を確認する選択がある。どれもGPT／ユーザーの判断事項である。
3. 新アルゴリズム研究を終える判断の条件も記録しておく。推奨戦略の最初の作業（[戦略比較](future_research_strategies.md) §10）で、D1・D2の下で補題の大きさのgapを一つも特定できない場合は、継続の根拠が弱いと判断する材料になる。終了するかどうかは、その結果を見てGPT／ユーザーが判断する。

<!-- fixed-source-references -->

[E0-landscape]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_exploration/quantum_chemistry_independent_topics_20261016/research_topic_landscape.md
[E0-matrix]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_exploration/quantum_chemistry_independent_topics_20261016/candidate_evidence_matrix.md
[E0-t1d]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/research_exploration/t1_withdrawal_20261016/decision_record.md
[E1-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/research_decision_handoff.md
[E1-map]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/problem_and_failure_map.md
[E2-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/research_hypothesis_handoff.md
[E2-prov]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/provenance.json
[E3-binding]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/90d439e87a9aa83444e5f3e48020c1cc05bf007f/docs/research_exploration/p1star_environment_binding_20261017/execution_environment_binding.md
[E3-contract]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md
[E3-foundation]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/208cb9bfdbca6116b11b70bc01937aba732e9199/docs/research_exploration/p1star_technical_foundation_20261017/technical_readiness_report.md
[E3-prov]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/provenance.json
[E3-report]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/scientific_execution_report.md
[E3-resource]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/resource_recovery_addendum.md
[E4-cubic]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5110d347e1f032c9093430b3def13b3391602cdd/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md
[E5-20handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c7d3f077d634e4165b7cd326bac7caa1ae04ff66/docs/research_exploration/p1star_j1_paper_feasibility_20261017/decision_handoff.md
[E5-20math]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c7d3f077d634e4165b7cd326bac7caa1ae04ff66/docs/research_exploration/p1star_j1_paper_feasibility_20261017/mathematical_feasibility_record.md
[E5-finalhandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/143f50d3bf2636b1433d9b70a844bbdc22832a6e/docs/research_exploration/p1star_j1_final_limited_search_20261017/research_decision_handoff.md
[E5-finalmath]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/143f50d3bf2636b1433d9b70a844bbdc22832a6e/docs/research_exploration/p1star_j1_final_limited_search_20261017/limited_construction_record.md
[E5-j1handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/dd36794069f2f8063d3eba6c7e3fcc989d9b0ceb/docs/research_exploration/p1star_joint_loop_principles_20261017/research_decision_handoff.md
[E5-j1prior]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/dd36794069f2f8063d3eba6c7e3fcc989d9b0ceb/docs/research_exploration/p1star_joint_loop_principles_20261017/prior_art_and_rejected_directions.md
[E5-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/95be62395d3740db39b6830c68f4fd1e25f595ee/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[E6-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/813fd44bfd70f9bc4266e35cc8e4dd28037dedce/docs/research_exploration/independent_construction_principles_20261017/research_hypothesis_handoff.md
[E6-hyp]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/813fd44bfd70f9bc4266e35cc8e4dd28037dedce/docs/research_exploration/independent_construction_principles_20261017/construction_hypotheses.md
[E7-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5c49323957f1bfa2a24cb2786a0ebd1f3932925/docs/research_exploration/bottleneck_operation_design_20261017/decision_handoff.md
[E7-prior]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5c49323957f1bfa2a24cb2786a0ebd1f3932925/docs/research_exploration/bottleneck_operation_design_20261017/prior_art_and_limits.md
[E7-task]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5c49323957f1bfa2a24cb2786a0ebd1f3932925/docs/research_exploration/bottleneck_operation_design_20261017/operation_design_task.md
[E8-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c23e9bc6028c52761e6220b91e2d1e1bd8b3ceaf/docs/research_exploration/pair_collision_cg_verification_20261017/verification_handoff.md
[E9-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/research_handoff.md
[E9-inshandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/verification_handoff.md
[E9-insobs]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/insertion_obstruction_and_checks.md
[E9-minimal]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/minimal_paper_checks.md
[E9-pause]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17cf4073094c713257d6eabadb440d6d973a9229/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
[E9-prior]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/prior_art_comparison.md
[E9-problem]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/research_problem.md
[E9-ricderiv]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/riccati_paper_derivation.md
[E9-richandoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/decision_handoff.md
[E9-survey]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/unresolved_problem_survey.md
[PR-claude1016]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dbe51f1870cd069b952cc92593833d355da10e28/docs/reviews/quantum_chemistry_pf/qc_sos_pf_post_k05_claude_scientific_review_20261016.md
[PR-coverage]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_coverage_map.md
[PR-gpt1016]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dbe51f1870cd069b952cc92593833d355da10e28/docs/reviews/quantum_chemistry_pf/qc_sos_pf_post_k05_gpt_scientific_review_20261016.md
[PR-k0]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/0d460c54f3bf54ea46d4d8129f6702703c4bb217/docs/research/qc_new_algorithm_static_screen_k0_20261016/technical_report.md
[PR-mreview]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/docs/reviews/quantum_chemistry_pf/qc_m_k0_claude_scientific_rereview_and_direction_20261015.md
[PR-purpose]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/78b50c515d9df9556f261e74ca7c57af461b7199/docs/research/%E7%A0%94%E7%A9%B6%E7%9B%AE%E7%9A%84%E3%83%BB%E7%A0%94%E7%A9%B6%E8%AA%B2%E9%A1%8C.md
[PR-transition]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_state_transition.md
