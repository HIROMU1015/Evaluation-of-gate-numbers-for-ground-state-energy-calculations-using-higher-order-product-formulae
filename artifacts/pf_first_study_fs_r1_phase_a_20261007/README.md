# FS-R1 Phase A 実行前停止監査

**PHASE_A_NUMERICAL_CONTRACT_UNCLOSED**。添付§23に従い、productionを開始する前に停止した。
Phase A prediction freezeは成立しておらず、Phase BはNO-GO / 未承認。

v2はcold replayの再構築範囲を固定しているが、raw proxy・fit coefficient・arm prediction・budget・
deterministic Ritz診断の差を合格とするproduction用の比較規則/許容差がない。
H4のnoise ruleは観測した差をetaへ取り込む診断で、今回のreplay合格上限にはならない。
RitzのMGS/rank/Hermiticity閾値、synthetic testのatol、resource判定のeta=0.02も代用していない。
前回のGO判定ではこの数値契約の不足を見落としていた。旧GOを上書きせず、今回の追加監査として記録した。

読む順序：

1. [Phase B判定](GO_NO_GO_FOR_PHASE_B.json) → [数値契約監査](numerical_contract_audit.json)
2. [実行依頼の原文](authorization_request.md) §23 → [v2 snapshot参照](phase_a_protocol_snapshot.json)
3. [source byte/metadata確認](source_identity.json) → [実行/未実行値](production_results.json)
4. [260 tests再実行](tests.log) → [検証](verification.json) → [action counts](action_counts.json) / [truth audit](truth_access_audit.json)
5. [cost](cost_ledger.json) → [authority hashes](source_manifest.json) → [publication hashes](publication_manifest.json)

N2/COのsanitized archive SHA、全NPY member file SHA、metadata/array allowlist、ordered group SHAは一致。
NPYの数値decodeやH matvecを行わず、元のtruth-only pickleも開いていない。
H digestは凍結identityとarchive完全一致によりbindした。今回H CSR digestを再計算したとは主張しない。
source missing / reconstruction mismatch / branch failure / 観測済みnumerical failureではない。

|報告項目|N2|CO|
|---|---|---|
|retained Ritz rank|未計算|未計算|
|M00′ / M10′ / M01′ / M11′|すべて未計算|すべて未計算|
|B0′ / B01′ / B10′ / B11′ / prediction-only ratios|すべて未計算|すべて未計算|
|cold replay差 / 数値gate結果|未測定|未測定|

production source load/PF/echo/H/Ritz/fit/group actionsはすべて0。truth access / new direct truthも0。
production wall/RSSは未測定。metadata/hash監査のwall/RSSをcost ledgerへ別scopeで記録した。
既存260 tests PASSはproduction toleranceの証明ではない。
RUN_STARTED lease未作成、science returnなし、private scalar recovery未作成。
prediction SHAはnullで、prediction_manifest.json / prediction.sha256は意図的に作成していない。
publication_manifest.jsonは停止監査のhashであり、Phase B用のprediction hashではない。
private npz/pickle/vector/unitary/recoveryは一切公開していない。

GPTに判断してほしい事項は、観測前に固定するphysical-production replay/norm合格規則。
必要なunits・absolute/relative comparison・near-zero/near-infeasible budget・rank/status一致・fit/budgetへの誤差伝播を明示すること。
Codexは許容差を提案/選定していない。次の契約を承認・version/freezeした後に実行を再開する。
initial全2条件→cold全2条件のorchestration、Phase A lease、完全なdiagnostic/recovery wrapperも実行前review対象。
これらは実装残件であり、今回productionを試行した記録ではない。

起点はdd41c5eaad4a88339f7bbb69267bfdace9fb86e5。branchはpf-first-study-fs-r1-phase-a-20261007。
旧artifactと現在の第2研究workspaceを変更せず、追加auditだけをcommitする。
commit/push後の40桁SHA、remote tip照合、独立fetch/blob確認は外部receiptとhandoffで報告する。
この監査の公開後に停止する。
