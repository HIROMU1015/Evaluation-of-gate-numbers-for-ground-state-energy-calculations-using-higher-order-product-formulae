# Codexへの指示｜PF研究成果レポートの証拠監査・repo統合

**2026年9月29日｜文書作業のみ**

## 1．依頼の目的

添付の研究成果整理稿をGitHub上の固定evidenceと照合し、研究相談・発表・修論等へ転用できる内部成果レポートとしてリポジトリへ保存してください。投稿論文の執筆や、新しい研究方針・実験方法の開発は今回の作業に含みません。

内容の中心は、PFの性能、有限時間校正の信頼性、追加情報の資源価値です。単なるartifactの時系列一覧へ戻さず、「問い→方法→観測→解釈→限界」が読める構成を維持してください。新しい仮説を有効性実証済みの成果へ格上げしないでください。

## 2．入力とidentity

Repository:
`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

集約snapshot:
`fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`

添付の内容整理稿:
- `PF_research_outcomes_20260929.md`
- `PF_research_claim_evidence_ledger_20260929.md`
- `PF_research_storyline_20260929.md`
- `PF_research_source_registry_20260929.json`

関連する固定結果:
- R1 evidence review：`a134ba3950a521225a14c46943d0dbe469425e00`
- D1 result：`94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a`
- D2-A result：`e1fd81dc0f3c58396b99fee40ac55987b9dc4f07`
- D2-A scoring audit：`17e4d6357c7c5ef9bb849d0f787a642f972c7995`
- C0 planning content：`1b45089f9fd6244f5240e197a090003ea7956101`
- C0 final identity：`fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`

これらのcommitは役割ごとに扱い、文字列の似た「execution」「planning」「result」を同じprovenanceとしてまとめないでください。今回作るdocument bundle commitは、既存evidence commitと別です。

現在のworktreeが別作業を含む場合は触らず、固定snapshotから専用planning/documentation worktreeを作ってください。branch案は`pf-research-outcomes-summary-20260929`です。既存branchがあれば履歴と用途を確認し、上書き・reset・force pushで再利用しないでください。mainへのmergeは今回しません。

## 3．最初に確認すること

source registryの全S IDについて、指定commit・pathが読めることを確認してください。別branchの同名ファイルを黙って代用しないでください。registryにあるGit blob SHA-1はコネクタ返却値であり、ChatGPT側が再hashしたSHA-256ではありません。必要なblob identityと今回の読み取りbytesから得たSHA-256を、新しいsource manifestへ区別して記録してください。

指定sourceに不足があれば、同じcommitの報告書が示すCSV/JSON/manifestへ読む範囲を広げて構いません。公開H-chain原稿は指定v1を対象とし、最新版や別原稿に無言で置き換えないでください。係数ID対応・版・出版状態が未確認なら、現稿の限定を残します。

sourceが読めない場合は、アクセス失敗・未追跡・path不一致などを具体的に記録してください。数値が一致する別資料を、指定sourceを読んだ証拠にはしないでください。

## 4．行う作業

### A．CL01–CL30と原sourceの照合

各CLについて、対象系・PF・時刻・比較相手・費用式・gamma・母集団・source versionを照合してください。報告書だけで確認したものと、CSV/JSONの原rowまで照合したものを分けます。

特に以下を確認してください。

1. 第一研究のH4/二準位128 caseは3倍dominance、R1は元allowanceと2倍dominanceであること。
2. 第一研究H4のm5_best選択と、S0の別6条件の結果を混同していないこと。
3. S0の1%余裕6/6、F_total、F_t、F_P、HF domain/within上下界の分母・単位。
4. S4のbeta修正では旧絶対phase errorを流用せず、1.2統一監査で42/42・成否変更0・no_benefit不変を使うこと。
5. 第二研究の独立4条件評価とR1以降のpost-hoc診断が混ざっていないこと。
6. aggregate budgetにunsafe条件が含まれること、uncapped counterfactualが非運用の診断であること。
7. R1の16行は10座標を共有し、局所11/16・15/16はcounterfactualであること。
8. D1のKは非対象cluster保持数であること。exact weightsとq_omitを運用入力扱いしないこと。
9. D2-Aの旧整数判定0/6と、audit後の表現不変6/6を併記すること。6/6は運用上のground/branch certificateではないこと。
10. D2-Aは1点棄却・予算出力5/5 safe・主baseline比低予算0/6であり、6/6安全実行とは書かないこと。
11. current widthは経験的であり、厳密certificateの本質的コストを証明したとしないこと。
12. C0のRayleigh residualとD2-Aのunit-circle候補残差、g_targetとg_rho,others、chord/phase/energyを区別すること。
13. HClの同時刻0.327975〜2.286462%という利益上限を、HF cap外、別時刻、別PF、bias補正へ広げないこと。
14. source台帳の9月25日以後に使われたHCl/LiFは、今後の方式に対するdevelopmentであること。
15. 新4次式の原稿内名称とコードIDの同一性を確認できなければ、同一視しないこと。

### B．必要な範囲での編集

数値の転記誤り、百分率と比の誤記、source pathの誤記など、一意に確認できる訂正は行い、`correction_log.md`へ旧文・新文・根拠を残してください。

原資料同士の矛盾、定義が異なる数値、根拠が不足する物理解釈は、黙って調停せず確認事項にしてください。支持されない強い表現は削除または限定し、理由を記録してください。新しい係数・threshold・誤差幅・因果仮説を作って説明を補わないでください。

文章の整形や読みやすさの改善は可能ですが、reportの結論を「新方式成功」に変えたり、全体を投稿論文形式へ作り替えたりしないでください。future directionは、実績と別の節に置いたままにします。

### C．成果物を一つのbundleとして配置

配置案:

`docs/research_outcomes/20260929/`

本体・台帳・短縮版・source registry・この指示書・READMEを同じdirectoryへ置き、relative linksを保ってください。加えて以下を作成してください。

- `evidence_audit_report.md`：確認できた内容、訂正、残るsource不足。
- `claim_evidence_audit.json`：CLごとの確認状態、根拠path/field/row/commit、未解決理由。
- `source_manifest.json`：参照sourceのcommit、Git blob、bytes、SHA-256。
- `correction_log.md`：元稿からの編集差分と理由。
- `bundle_manifest.json`：今回の文書artifactのfile set、bytes、SHA-256。
- `decision.json`：文書作業の状態と、科学計算未実施・未許可の境界。

既存status文書への変更は、このbundleへの入口リンクと「成果整理時点」の短い追記に限ります。元の研究decision、protocol、raw CSV、scoring auditを上書きしません。古い文書の当時の結論も消しません。

## 5．許可する検査と、禁止する計算

許可するのは、gitのread操作、sourceの読み取り、保存CSV/JSONのcount・表示単位・費用恒等式の算術照合、文書編集、相対リンク確認、JSON parse、source/bundleのhash確認です。保存値からの算術は`post_hoc documentation arithmetic`と明記し、新しい方法の成績にしません。

次は行わないでください。
- 分子生成、状態再計算、PF/H作用、Arnoldi再実行、full eigensolve、gap取得。
- toy numerical experiment、新しいboundの実装・検証、thresholdやmarginの調整。
- C1、D2-B、LiF追加実験、holdout、新PF探索、bias補正。
- GPU問い合わせ・割当・kernel、環境・依存パッケージの更新。
- 証拠不足を補うための新規研究計算。
- 科学計算が走る可能性のあるreview_tests全体の無条件実行。
- mainへのmerge、無関係な変更のstage、既存結果の再分類・上書き。

新しい図の数値生成は今回不要です。既存図を再利用する場合でも、正しいsource・scope・captionを照合したものだけに限定し、未確認の図を成果図として載せないでください。

## 6．完了条件

3文書が一貫した用語・数値・evidence classを使い、CLごとのsourceと限定が追跡できること。原結果・audit・C0が保存され、新しい科学計算が0であること。

未解決がないと推測して空配列にしないでください。例えば公開原稿とPF IDの対応が未確認なら、その項目は明記します。文書統合ができたことと、研究上の未解決問題が解消したことは別です。

`decision.json`には、少なくとも以下を区別してください。

```json
{
  "classification": "research_outcomes_documentation_and_evidence_audit",
  "status": "research_outcomes_documentation_complete_review_required",
  "evidence_snapshot": "fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3",
  "new_scientific_computation_count": 0,
  "original_research_artifacts_modified": false,
  "scientific_execution_authorized": false,
  "c1_authorized": false,
  "d2_b_authorized": false,
  "holdout_authorized": false,
  "new_pf_authorized": false,
  "source_audit_unresolved_items": "実際の確認結果を配列で記録する",
  "next_step": "human_review_of_outcomes_documents_only"
}
```

上のJSONはschema設計例であり、未確認の完了状態を先に記入しないでください。source不足で主要主張を検証できない場合は、`research_outcomes_documentation_partial_source_review_required`等に区別し、どこまで作成できたかを残します。

## 7．Gitと最終報告

専用branchでは今回のdocument bundleと必要最小限の入口リンクだけをstageしてください。`git add -A`で無関係な変更を含めないでください。document content commitと、必要ならそのcommitを記録するidentity commitを区別してください。自身の未来のhashをsource欄へ捏造しないでください。

commit後、branch・commit・変更ファイル・主要訂正・未解決事項・科学計算0を報告して停止してください。remote pushはユーザーが与えた明示的な許可の範囲で行い、pushした場合はremote tipを実際に確認してください。mainにはmergeしません。

**この作業の終了は、研究成果が読みやすく追跡可能な文書になった時点です。新しい研究検証を開始する合図ではありません。**

## 8．追加監査要件

1. source registryでは、結果を最初に生成した`origin_result_commit`と、今回内容を照合する
   `verified_snapshot_commit`を別fieldで記録する。同一blobでも統合しない。
2. CL30および将来研究方針はscientific evidence claimではなく`governance_scope`として分離する。
3. `bundle_manifest.json`は自己参照を避けていることを`manifest_self_excluded: true`で明示する。
4. handoff元ZIPのSHA-256を
   `b3a3d0054a17c428cfe0d8958c70892b36538c84fdf72061d6e4f1b36726cc85`
   として固定する。
5. 上記以外は本指示書の既存規則に従い、科学計算、C1、D2-B、新PF、追加分子を実行しない。
