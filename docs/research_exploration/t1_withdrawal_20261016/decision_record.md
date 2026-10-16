# T1-D正式採択：独立研究候補からの撤回記録

決定日：2026-10-16 JST。決定主体：ユーザー。Codexの役割：正式採択済み判断の記録と、2資料の公開・照合。

**T1-D：T1「trap認証の取得費を含むPF位相推定の有限精度設計」を独立研究候補から撤回する。T1を独立研究として追究せず、追加文献調査・実装・科学計算を行わない。**

## 1. 正式採択事項と決定の範囲

本記録は、ユーザーの作業指示「T1-D正式採択・独立研究候補からの撤回記録」に記された2026年10月16日の正式採択を反映する。

- T1を独立研究として追究しない。
- T1の追加文献調査・実装・科学計算を行わない。
- 既存静的調査を今回の研究選定の成果として固定保存し、Claudeレビューは取得状況を明示して参照する。
- 新しい技術補論、合成保証、証明、反例は作成しない。
- 新規性の不存在、trap認証の不可能性、量子資源改善の一般的不可能性を結論にしない。
- 新しい科学的証拠が得られ、ユーザーが別途明示承認した場合だけ再検討できる。

これは直近の静的調査で残った候補1件に対する研究選定判断である。量子化学・Hamiltonian simulation全般の研究探索を永久に終了する決定ではない。

## 2. 固定証拠とClaudeレビューの取得状況

対象repositoryは `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。既存調査の固定commitは `3af746a9fc4406e7de910745bc9a749fbefbf5e8`。次の4資料を読み取り、同commitのGitHub rawから取得したbyte列とローカルGit blobを照合した。取得版、byte数、Git blob、SHA-256、origin/result commitとverified snapshot commitを[provenance.json](provenance.json)に記録する。

| 固定資料 | 今回の決定に関係する到達点 |
|---|---|
| [candidate_handoff.md][HANDOFF] §1・§4 | T1は条件付き候補。独立した新規性・資源利益は未確立で、単純な既知結果の合成なら独立候補から外す条件が記されていた。 |
| [candidate_evidence_matrix.md][MATRIX] §1・§2・§6 | 既存法との差分、認証の対象と対象外、有限標本energy推定・取得費・状態同定の未完了事項が分離されていた。 |
| [research_topic_landscape.md][LANDSCAPE] §1・§7・§8 | 正式採択に十分な新規性・資源利益は確定しておらず、既存研究のSTOP・PAUSEとscopeを維持していた。 |
| [既存provenance.json][STATIC_PROVENANCE] | 文献版・読取り範囲・公開codeの静的確認・未確認事項・科学実行0件の記録。全文取得と全文読了・証明監査は区別されていた。 |

Claudeの独立科学レビューは、ユーザーが指定した **`レビューoutter(9).md`** である。本作業では原文を取得できず、**原文未確認**とする。利用可能なローカル資料のファイル名、添付テキスト、固定commitのpathを確認したが、同レビューの原文identityを確定できなかった。検索範囲とアクセス上の限界はprovenanceに記す。

従って、レビューの本文・強い表現を引用したり、内容を独立検証済みとして帰属したりしない。決定のauthorityは今回のユーザーによる正式採択であり、技術的な証拠水準の参照先は上記固定4資料である。レビューを取得・保存済みとは記録しない。原文未取得でも本決定の記録と停止を実施するというユーザー指示に従う。

既存4資料は履歴に保存し、内容を書き換えたり重複コピーを公開したりしない。そこで述べた「将来の追加確認・最小検証」は作成当時の条件付き案として残るが、**T1について今後実施する行動は本T1-D決定が規定する**。旧handoffを追加調査や実行の承認として使わない。

## 3. 撤回の理由

**現在確認できる独立した科学的差分と資源上の利益が、追加研究を正当化するほど確立していないため、独立研究候補から撤回する。**

既存のlogical accreditationと位相推定法を接続すること自体は、独立研究としての新規性を確立しない。既存調査は、有限標本の推定保証、必要な状態情報、認証情報の取得費まで含めた総資源について未確認事項を列挙したものであり、独立した新アルゴリズムや量子資源の利益を示した成果ではなかった。[HANDOFF] [MATRIX]

この証拠水準に基づきユーザーは追加追究を終了した。未確認事項を本作業で新しい文献調査、証明、数値実験によって埋めることはしない。

## 4. 保存する科学的整理と主張の限界

既存調査が参照したlogical accreditation（`2508.05523v3`、既存registryのL17）は、指定されたノイズ・回路・実行独立性等の仮定の下で、trap結果から、実装出力と理想compiled target回路の出力分布の距離を制約する。[MATRIX] §2。本作業では同論文の新規取得・再読や証明監査を行わず、固定調査と今回のユーザー指示にある区別を保存する。

| 区別する対象 | 本記録で保持する限界 |
|---|---|
| 回路実行時のlogical noise | 認証の仮定と対象回路に関する条件付きの制約。任意のノイズに対する無条件保証へ拡張しない。 |
| 回路合成・compile近似誤差 | 理想compiled回路が意図した回路を近似する誤差は別問題。出力の認証だけで消えない。 |
| PF近似による固有エネルギーbias | compiled回路の正しい実行の認証と、対象Hamiltonianの固有エネルギーへの近似は別問題。 |
| 基底状態の同定とoverlap条件 | 出力分布の制約だけで対象が真の基底状態だと同定したことにはならない。 |
| 有限標本による位相推定誤差 | TVDや観測量の既知保証と、位相推定・後処理を通したenergy保証を同一視しない。 |
| 認証情報の取得費を含む総資源 | target/trap測定、状態準備、合成等を含む利益は本調査では実証されていない。 |

**支持される結論**は、現在の証拠ではT1の独立した差分・利益が追加研究を正当化するほど確立しておらず、ユーザーが研究選定上の撤回を決定したことである。

**本決定から導いてはいけない一般主張**は次のとおり。

- T1または関連分野に新規性がないことを一般証明した。
- 有限標本保証の接続を完全に独立証明・監査した。
- trap認証が不可能、あるいは無価値である。
- あらゆる条件で量子資源改善が不可能である。
- 絶対基底エネルギーの認証が一般に不可能である。
- 既存認証理論と位相推定法のあらゆる組合せについて、研究価値がないと確定した。

レビュー原文が未確認であること、文献で未確認の事項、科学的な一般的不可能性は、それぞれ異なる。本書は新しい定理・技術補論・不可能性証明ではない。

## 5. 追加作業の停止と再検討条件

T1の追加文献調査、アルゴリズム設計、技術補論、証明・反例、実装、benchmark、科学計算、保存値の数値再解析・再fitは実施しない。既存静的調査の未完了事項を自動的な次工程にしない。

再検討には、**新しい科学的証拠**と、**ユーザーによる別途の明示承認**の両方が必要である。本記録はその証拠を新たに探すことや、同じ問いを別名で再開することの承認ではない。条件の充足・再開の判断をCodexが自動で行わない。

今後の一般方針として「具体的な未解決技術課題を起点として、新しい解決原理を探索する」ことがユーザーにより承認された。ただし、本作業の範囲はT1の終了記録までである。次の課題の列挙、先行研究調査、設計、実装、科学計算、論文化・投稿検討には進まない。

## 6. 他研究とworkspaceの保全

| 保全対象 | 維持する状態 |
|---|---|
| U1-AR、U3/H05、U4 | C1・E4・C4完結および追加研究の正式STOP。 |
| 第一研究S0〜S4 | 完了状態、S4の否定結果、final synthesisと限定claim。 |
| 第二研究Direction C | 独立した既存研究の承認済みscope。 |
| FS-R1 Phase B | 科学実行未承認、既存のtruth barrier。 |
| PR Track A/B | 既存scope・結果・authority。今回のT1-Dによる変更なし。 |
| 既存R5 | PAUSE。旧調査で現行PAUSE原文未確認だった限界も保持し、本作業で再調査・再開しない。 |
| 2026-10-16のU1〜U7候補探索終了 | 既存の監査対象scopeの完結記録。[U1_U7_CLOSURE] |

既存SOURCE、raw results、claim ledger、authorization、grant、STOP、manifestを変更しない。元workspaceと既存worktreeのdirty/staged/untracked状態を保全する。新branchは既存静的調査commitから作成し、変更は本書とprovenanceの新規2資料だけに限定する。既存資料・privateデータの新規公開、旧branchへのcommit、mainへのmergeは行わない。

## 7. GitHub引き渡しとMandatory STOP

branch：`pf-t1-d-research-candidate-withdrawal-20261016`。保存先：`docs/research_exploration/t1_withdrawal_20261016/`。読む順序は本書、[provenance.json](provenance.json)、必要に応じて固定4資料。

新規2資料のみを明示stageしてcommitし、許可されたrepositoryへ通常のnon-force pushを行う。公開後にremote SHAと、commit固定GitHub rawから取得した両ファイルのGit blob・byte数・SHA-256を照合する。最終commit identityと照合結果は最終handoffで報告する。provenanceは自己hashと最終commitの循環参照を除外し、公開前の記録と公開後の照合を区別する。

本作業での新規科学計算・simulation・保存値の数値再解析・再fit・新証明・反例・科学実装・benchmark・追加文献調査・新テーマ採択はいずれも0件。実施するのは固定資料の読取り、決定の文書化、Git・文書・hashの照合である。

**Mandatory STOP：2資料の公開・照合後に停止する。T1の追加追究も、次の新テーマ探索も自動開始しない。**

[HANDOFF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_exploration/quantum_chemistry_independent_topics_20261016/candidate_handoff.md
[MATRIX]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_exploration/quantum_chemistry_independent_topics_20261016/candidate_evidence_matrix.md
[LANDSCAPE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_exploration/quantum_chemistry_independent_topics_20261016/research_topic_landscape.md
[STATIC_PROVENANCE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_exploration/quantum_chemistry_independent_topics_20261016/provenance.json
[U1_U7_CLOSURE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3af746a9fc4406e7de910745bc9a749fbefbf5e8/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/audited_candidate_scope_closure.md
