# 新原理探索：次の研究判断へのhandoff

**未検証の発想8件から、Bの構成仮説P1*を1件保持した。Aは0件、Cは4件、Dは3件。正式採択・科学的GO・新規性認定は0件。**

P1*は、非可換な電子密度と共通の補助振動子の結合に対し、フェルミオンの反交換関係（CAR）を使って不要なbus作用を消し、元の電子相互作用を残す共同閉路を構成できるか、という高リスクの問いである。単独の幾何学ゲート、DF、非可換force、交換子合成、decouplingそのものは既知。新しい生成規則が本当に残るかも未確立である。

2026-10-16のユーザー承認に従い、発想、既知法照合、技術的成立性、正式採択を分離した。研究資源不足を理由とする探索終了や既存研究への資源回収は提案しない。論文化は評価していない。本書の分類は今回の概念整理であり、研究方針の追加変更をCodexが決定した記録ではない。

## Phase C：分類と理由

| 仮説 | 分類 | 分類の直接の理由 | 科学的実行 |
| --- | --- | --- | --- |
| P1*：CARを使う非可換密度の共同bus閉路 | **B** | force族・目標作用・不要成分を説明できる。CARから共同cycleを生成できるかが未解決。成立・独立性・費用はunknownだが、最初の数学的問いが具体的 | 未承認・未実施 |
| P2：配置依存の励起閉路cell | C | CI row oracle、graph分解、multi-edge可解成分の骨格が既知。追加の化学固有label生成規則を今回提示できない | 未実施 |
| P3：等スペクトルdefect | C | 既存H1監査、既報の固有状態条件・processed／corrected PFへ還元が強い | 停止系列を維持 |
| P4：基準からenergy微分を積分 | C | 既知の微分関係と積分。新しい経路・状態取得規則なし | 未実施 |
| P5：有理propagatorを補助散乱で生成 | D | resolventを許可されたprimitiveで得る操作が未定義 | 未実施 |
| P6：定常性control variate | C | 零期待値制約を追加する測定枠組みが既知。独立したA選択・測定生成規則なし | 未実施 |
| P7：誤差だけをsyndromeへ送るlift | D | lift・recoveryの具体的写像が未定義 | 未実施 |
| P8：自律energy clock | D | 原点と符号を保つ情報転送操作が未定義 | 未実施 |

**Aは0件**：実質的な独立差分を説明できる段階まで到達したと認定できるものはない。Bは「Aになる見込みが高い」という順位ではない。保証未証明・高リスクだけを理由にC/Dへ落としていない。Cは構成の核が既知、Dは必要な操作が未定義という理由で区別した。

P1から残すのはP1*だけである。単独density-square閉路を逐次実施する構成はC相当で、保持する仮説の実績には含めない。最大3件という枠を埋めるために、既知法の改名や曖昧な発想をBへ追加しない。

## Phase D：P1*で判断すべき科学的内容

| 項目 | 判断材料 |
| --- | --- |
| 科学的中心課題 | 非可換な一体電子密度を同じbusへ結合し、CARで同じ電子作用となる項を共同利用することで、必要二体相互作用とbus帰還を同時に設計できるか |
| 最も近い既存研究 | Mottaほかのdensity-square、Spillerほかの閉路bus gate、Bermudezほかの非可換forceと残留結合、Sutherland–Srinivasの非線形spin–motion、Childs–Wiebe／Chenほかの交換子積、Bookatzほかのdecoupling。固定版・箇所は[照合表](prior_art_and_novelty_boundaries.md) |
| 構成原理の核心となり得る部分 | 各factorの閉路を独立に作る代わりに、factor labelとCARの商関係を使い、複数密度にまたがる符号・quadrature cycleを生成すること。CARを単に式のsimplifyへ使うだけでは足りない |
| 最大の理論的障害 | 零平均変位は演算子値の閉鎖を保証しない。busのsqueezing／占有依存項、電子高体項、有限時間残余を同時に抑えつつ、目標二体項を消さない条件が両立するか |
| 最大の技術的障害 | 異なる軌道frameのL⊗X、L⊗Pを同時／交互に供給する物理access。basis rotation、可逆算術、bandwidth、bus占有・準備、coherent controlとreadoutの価格 |
| 必要仮定 | Hermitian factorと一体・scalar・residualの明示。許されたforceの符号・quadrature制御。特定の初期bus stateと占有tail管理。対象電子sector。全Hやexact ground情報を無料入力にしない |
| 肯定的結果の価値 | たとえ直ちに資源優位がなくても、電子相互作用を生成する新しい代数的制御規則又は適用classが得られる可能性。既知逐次閉路との違いを具体的に検証できる |
| 否定的結果の価値 | CARの同値関係がbus帰還に使えない、特定制御族で条件が競合する、又は全て既知交換子合成へ還元される、という障害を切り分けられる。一般no-goとはしない |
| 最小の技術確認で分かること | 非可換な二つの記号的Hermitian一体factorと一busを対象に、固定した小さな制御族で、必要二体項と不要bus項の係数条件が両立し得るか。独立閉路へ退化するだけか。新しい係数・解・証明は今回作っていない |
| 追加の証明が必要な箇所 | CARからcycleを生成する規則の存在／正しさ、finite-time remainder、bus tail、coherent control後のphase、全Hへの組込み誤差。有限次数条件を満たすだけで有限時間保証としない |
| 追加実装・科学計算が必要な箇所 | 将来採用する場合の代数展開／求解、pulse生成、電子＋bus dynamics、回路化／compile、native cost、energy推定との接続。いずれも別承認が必要 |
| 独立研究として成立しない条件 | 完全な構成対応を示した結果、DF＋単独閉路＋既知PF、汎用交換子合成、一般optimizerの適用だけに帰着する場合。化学固有の追加生成規則がなく、原理ではなく既知法比較に留まる場合 |

高い費用や保証未証明は、それだけでは独立研究としての価値を否定する条件ではない。費用・保証は未確立のまま残す。特定ansatzが失敗しても、他の全制御族・量子化学の新原理一般の不可能性とはしない。

## 次の判断の順序と承認境界

**現在の停止位置は、概念資料の公開・照合まで。** 下記は将来の判断点であり、実行protocolや次jobの認可ではない。

1. GPT／ユーザーが、P1*の狭い問いに独立研究として検討する価値があり得るか、既知制御合成の問題に完全に含まれるかを判断する。新規性の最終判断はCodexが代行しない。
2. 検討を続ける場合に限り、まず数学的な最小確認だけを別承認で限定する。対象は記号的factor、制御primitive、有限ansatz、何を出力して止めるか。分子simulation・fitting・pulse最適化を一括承認とはしない。
3. その結果に新しい構成規則が残る場合も、実装・科学計算・証明・詳細科学レビュー・正式採択はそれぞれ別に判断する。

最小確認で提案するのは、既知のMagnus表示と明示したCAR関係を使った係数整合の検討である。**今回はその新しい代数展開、方程式生成・求解、定理・反例証明を行っていない。** 低次数の条件が存在したとしても、finite-time／全H／絶対energyの成立を認めるものではない。

外部busの入力モデルを既存gate modelへ無償追加しない。GPTが新しい制御accessの検討自体を研究目的として認めるかも判断事項である。実用優位は発想時の必須条件にしていないが、将来優位を主張する際は同じaccessと全費用の比較が必要になる。

## D1・D2と既存研究の保全

| 固定境界／系列 | 今回維持する内容 |
| --- | --- |
| D1 | block-encoding、qubitization、それらを中核とする方式へ移行しない。P1*のdeterministic bus帰還を、射影／postselectionでHを実装する方式へ置換しない |
| D2 | 元の電子Hの絶対E0。核反発・normal-order等のscalar、sector、simulation誤差、state overlap／準備、control位相を保持。bus付きHのenergyを代用しない |
| T1-D | 候補撤回と既存の閉鎖を維持。認証とPF推定の組合せを再開しない |
| U1/U3/U4・U1〜U7 | 既存CLOSED／STOPと監査対象scopeの完結を維持 |
| 第一・第二研究 | 完了・限定claim・否定結果・Direction Cの承認scopeを維持。新しい発想のために結果を再解析しない |
| FS-R1 Phase B | 科学実行未承認、truth barrier不変 |
| PR | H1〜H4 PAUSED、N1 STOP、N2 HOLD、N3 CLOSED、THRIFT現template CLOSED、旧D HOLD、PF小改変PAUSED、SOS-PF現探索CLOSED／A2 NOT_ADOPTED等を維持 |
| Track A/B | 独立の既存成果・受理範囲・認可を維持。後続M1-Sの限定理論を古い資料から一括PAUSEDとしない |
| 前回探索 | 60bf810の候補0件、X1/X2の結論・限定性・当時の公開前記録を凍結して保持 |

既存SOURCE、結果、STOP、authorization、manifest、prediction、budget、width、threshold、gateを変更しない。元workspace、PR、他worktreeのdirty／staged／untrackedを戻す操作も行わない。保全確認の方法・限界・並行更新の有無はprovenanceに明記する。

## 公開identityと読む順序

Repository：**HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae**。

専用branch：**qc-cross-domain-mechanism-ideation-20261016**。base／前回探索：**60bf810df6559cc41686f3fcff90fd5108435b1a**。別PR repositoryの参照scope：**56f1cc55c59ab7bc42c6b24e0953675de9b29b1d**。

読む順序：

1. 本書：分類、P1*の価値・障害・将来判断、保全と停止位置。
2. [principle_ideation_map.md](principle_ideation_map.md)：8発想の6項目、P1*の入力・操作族・目標。
3. [prior_art_and_novelty_boundaries.md](prior_art_and_novelty_boundaries.md)：既知への対応、部分還元、未解決差分、公式source。
4. [provenance.json](provenance.json)：版・固定commit・origin/resultとverified snapshot・hash・権限・保全・文書検査。

新規4ファイルだけをcommit・通常non-force pushする。最終40文字commitと固定リンク、remote先端、全4ファイルのGitHub取得byte・Git blob・SHA-256照合は、公開後の最終報告とlocal receiptで記録する。本書／provenanceへ自身のcommitを自己参照で埋めるための追記commitは作らない。過去の「未push」は作成時点の履歴として変更しない。

検証済みなのは、固定資料のidentity、限定した既知法との対応、資料整合・公開identityである。**P1*の存在・正しさ・独立性・資源優位・元E0推定の達成は未確立。**

GPTに判断してほしい事項は、P1*が既知法への完全還元を免れる構成問題を持つか、新しい電子―bus制御accessを検討対象に含める価値があるか、必要なら最小の記号的確認をどこまで別承認するか、の3点。詳細科学レビューの開始を依頼・実行したものではない。

**Mandatory STOP：資料公開・照合後に停止する。新規科学計算・simulation・保存値再解析／fit・回路生成／compile・pulse最適化・科学実装・benchmark・新証明・既存STOP解除・詳細科学レビュー・正式採択は全て未実施。自動進行しない。**
