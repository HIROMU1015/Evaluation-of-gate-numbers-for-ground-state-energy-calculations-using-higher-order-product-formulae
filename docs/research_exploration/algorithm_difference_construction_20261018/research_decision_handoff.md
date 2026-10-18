# 差分仮説・識別例・生成規則：限定構成研究handoff

2026-10-18 JST。**一つの差分仮説を具体化し、識別例と有限操作の生成規則を得た。強い公表対照への代入で核心が再現されるため、技術分類は「既知手順への還元」。独立した具体差分候補は今回残らなかった。** 正式採択・新規性の最終認定・新しいCLOSED判断・GPT重要科学レビューは行っていない。

## 1. 何を構成したか

非可換hoppingとdensityの期待値を、別poolではなく、同copyのspectator占有結果に応じたactive回転で一緒に測る仮説を検討した。これは旧Gのpredicate dictionary／変分部分空間更新や、旧PR共分散縮約の後処理改善ではない。

四mode・N=2の元電子family H=cI+F+Rを明示し、F=νS+dZ+tX12+uSZ、R=η(X23+X34)とした。tuη≠0ではhopping graphが連結でRも残る。係数からa_s=d+us、r_s=√(a_s²+t²)、θ_s=atan2(t,a_s)を作り、spectator占有測定→一Givens回転→active占有測定→νs+r_s(x1−x2)という有限手順を記述した。擬似コードを科学用プログラムや回路objectとして実装・実行していない。

## 2. 識別できた差と還元

- 条件付き回転を外した一つのactive基底では、[h_+,h_-]=4ituY≠0により二contextを同時対角化できない。
- 準備費を双方へ戻した明示stateで、Fの条件付きscoreは分散0、一方tXとuSZを別poolで測る標本平均には分散が残る。これは実際の測定変更であり、単なる古典縮約差ではない。
- ただし**[公表L01](https://arxiv.org/html/2305.18251v2)は既に占有symmetry測定からの条件付き軌道回転を生成する**。S1={1,2}、S2={3,4}、具体的h(z)を代入すると同じ角度・操作・POVMになる。record変換はidentityで、未知ρを含む全標本law・分散・相関、同じ算術なら費用まで再現できる。
- Fのrecordだけから全Hを無料評価する案には、spectator測定で失うRのcoherenceという障害がある。同じF record lawでR平均が逆になるN=2の二stateを示した。Rのfresh copiesを費用へ戻した。

B_pub、B_fair、B_plus_coreを分離している。B_plus_core一致から核心の既知性を推論せず、L01の既存生成式への具体的代入を根拠に還元した。固定一基底との差やtoy分散差を、強対照への資源改善・量子優位・絶対E0保証に格上げしない。

## 3. 未証明事項と次の判断

一般分子への適用、全Hでの費用優位、native/noise/routing、state品質と元Hの絶対E0への有用な保証、組合せの網羅的priorityは未確立。G1–G6、D1–D6、M1–M3は紙上導出であり、機械検算・独立形式認証をしていない。

**同じ操作・lawが既知対照で再現できることは今回紙上で閉じたため、この一件を独立候補として判別する追加数値runは提案しない。** toyでの同値確認は独立核心の判断を変えない。別heuristic・非可換context・別候補を追加探索して救済しない。

次の担当はユーザー／GPT。この限定還元と障害を研究記録として確認し、以後の研究方針を別途判断する。今回の完了報告だけを理由に新たな重要レビューを自動要求しない。新しい具体核心・科学実行を検討する場合は別の対象・範囲・承認が必要で、既に承認された後続科学作業はない。

## 4. 読む順序・SOURCE・保全

本書 → [課題とgap](research_problem_and_gap.md) → [三種の対照](claim_and_baseline_comparison.md) → [識別例](discriminating_examples.md) → [生成規則](generation_rule_construction.md) → [数学・資源](mathematical_and_resource_assessment.md) → [SOURCE](source_registry.json)・[一次文献provenance](literature_provenance.json)・[静的監査](static_audit.json)・[provenance](provenance.json)。承認済み作業範囲とGPT提案の原本はローカルの専用evidenceへbyteを保持して保存し、公開copyは含めない。SOURCE registryのlocal_input_observationsへbytes・SHA-256と読取範囲を記録する。

必須固定10commitに対応する12文書をGitと固定rawで照合した。意味の読取りはSOURCEの範囲欄に限定し、A2の保存値を再解析・ランキングせず、全transitive資料を再監査していない。一次HTML3件は方法の該当節を限定して読んだ。本文未取得の2402.09376v2等のエラーも文献provenanceへ区別し、公開版差分の網羅照合はしていない。文献全文はGitへ転載しない。

現G CLOSED／NOT RETAINED、集団遷移生成PAUSED、J1/Q1 PAUSE、R1-P不保持、A2 NOT_ADOPTEDと現実用化経路追加投資見送り、共分散縮約REDUCES_TO_KNOWN_METHOD、他系列の状態・SOURCE・raw・承認・grant・STOPを変更しない。D1/D2を維持する。最新共通運用指示2026-10-17と新worktree AGENTSを確認し、最新の直接ユーザー規約を適用した。

## 5. 公開とMandatory STOP

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。branch：`qc-algorithm-difference-construction-20261018`。base：`addf2cecdc78a271b0139f0459266aa4fef5812d`。専用新規directoryだけを通常commit/non-force pushし、remote SHA・独立空bare fetch・Git blob・bytes・SHA-256・commit固定rawを照合する。parent payloadの照合receiptを子commitへ記録し、receipt込み最終照合をチャットで報告する。manifestは自己除外する。

開始時の既存304 checkoutのHEAD・branch・status digestと両dirty rootのstaged／unstaged diff digestを保全比較する。これはuntracked内容・ignored runtime・全共有jobの包括監査ではない。資源は実空き状況を確認し、文書/Git管理の必要分だけ使用し、人工cap・共有環境／他job設定変更を加えない。

**新規科学数値計算、保存科学値再解析、simulation／solver、科学用symbolic checker、回路build／compile／benchmark、新科学契約・authorization／grant、重要科学レビュー代行、正式状態変更は0件。紙上構成だけを実施した。公開・照合後にMandatory STOP。**

原本公開の自動承認審査は、非公開入力の具体的な外部公開承認を確認できないとして拒否した。今回の公開資料は原本内容を除外し、ローカル保全とidentity metadataの記録へ変更した。
