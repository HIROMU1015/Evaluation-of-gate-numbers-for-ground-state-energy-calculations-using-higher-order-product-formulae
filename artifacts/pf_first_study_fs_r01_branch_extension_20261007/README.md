# FS-R0.1 branch-extension protocol / preflight

**GO_FOR_FS_R1_PHASE_A**（preflight/code-ready判定）。今回のproduction truthとFS-R1 scienceはともに0。
GOはscience実行承認ではない。GPT/user review後の別承認まで停止する。

FS-R0 commit `3469b29f53a2c559bb8f6785bcba68a2896d41a5`からの追加artifact。
旧v1、new source identities/operational exports、旧science成果物を変更しない。
v2は `FS-R1-20261007-v2`、revision reasonはnew-source physical branch continuation requires preregistered lower-time certification ladder。

読む順序：

1. [GO判定](GO_NO_GO_FOR_FS_R1_PHASE_A.json)、[承認済みamendment](branch_extension_amendment.md)
2. [v2 protocol](fs_r1_protocol_v2.json)、[ladder](branch_ladder.json)、[truth budget](truth_budget.json)
3. [branch contract](branch_contract.md)、[executor](truth_executor_contract.md)、[oracle isolation](truth_only_source_contract.md)
4. [barrier](phase_barrier_v2.md)、[Phase A freeze schema](phase_a_freeze_schema_v2.json)、[checkpoint](branch_checkpoint_schema.json)
5. [cost](cost_contract_truth.json)、[planned action budget](predicted_action_budget_v2.json)
6. [260 tests](tests.log)、[verification](verification.json)、[production zero audit](production_action_audit.json)
7. [source manifest](source_manifest.json)、[publication manifest](publication_manifest.json)

|condition|six ascending fixed coordinates|
|---|---|
|N2|0.06263494343795273 → 0.12526988687590546 → 0.18790483031385818 → 0.31317471718976365 → 0.5923370942191331 → 0.5983202971910435|
|CO|0.06546804264781796 → 0.1309360852956359 → 0.19640412794345388 → 0.3273402132390898 → 0.6066206637106297 → 0.6127481451622522|

truth total12=branch certification10+primary t0 scoring2。全点positive-time、condition内は必ず昇順。
最初の0.1t_refだけmaximum exact-ground-overlap seed、以後はmaximum previous-selected-vector overlap。
phase gap<1e-8のclusterはbasis-invariant projector continuityを使い、projected vectorにもeigenpair residual<=1e-10を要求する。
previous overlap>=0.9、unitarity Frobenius residual<=1e-10。exact tieのordering/phase規則は事前固定。
曖昧なcluster/低overlap/residual/identity/missing/duplicateでBRANCH_CONTINUATION_FAILEDとして残りを停止する。
midpoint/0.4/0.75/smaller anchor/denser gridのadaptive insertionや救済は行わない。

**座標audit**：COの0.99*t0のbinary64計算値は0.6066206637106296で、添付の明示値0.6066206637106297と1 ULP異なる。
添付§4の固定座標をauthorityとして保持し、11/12のformula一致と12/12の表示値一致を区別して記録した。
照会への別回答を受け取ったという記録は作っていない。[authority record](coordinate_resolution.json)を確認する。
この差をnearest-time代替や結果後のtime optimizationとして扱わない。runtimeはliteralのhex/hashを検証する。

source identityはFS-R0のN2 `6b93735a56638c40a2bcd35e504f1ee823cfdbe396441fce15fd5e02502b044d`、
CO `ed9ec93d6945a11bd144d2531ffedaf67da829383334b47206b78c11aee34f17`。
new namespaceはFS-R1:<source identity>:positive:k<ladder index>、旧ID6/9や旧truthを流用しない。
truth-only loaderはverified Phase A freeze/remote/code/config/source/recoveryと別science authorizationを要求し、
private original C0.6 whole SHAとfrozen new identityを照合後にstored exact ground/energyを読む。
PFは同じsanitized archiveのcurrent_m3・group order・sector/originから作る。exact groundはseed/comparator専用。
今回は元pickleをdecodeせず、既知private binary4ファイルのSHA/availability確認のみ。

production executorはCPU complex128でnative left-productをidentity blockへ適用し、complex Schur、
deterministic matching、projector、residual/ unitarity、private checkpointを通る経路を実装済み。
実1568次元はstatic/API readinessのみ。数値branch PASS、性能、resource outcomeはまだ未確立。
tiny-matrix testsはactual native PF→Schur→checkpoint→continuationの全12点pipelineとfailureの停止を検証した。

Phase Aの4-arm/training/t0/Ritz8/constants/fit/B0′/budget/safety/outcome/cold countsはv1を維持する。
estimatorへground overlapを渡さず、branchの中間10値はB0′、t0、arm選択へ入れない。
両ladderが完全PASSした後、final t0のsigned shiftだけを既存scalar scorerへ渡す。
branch certification PASSはscience successではない。

Phase A予定PF/echo各32、rank8ならexplicit H36/small Ritz4/fit8。
Phase B予定unitary/Schur/matching/vector checkpoint/residual/ unitarity各12、source loads2、new ground solves0。
truth_validation_costをclassical calibrationとQPE rotationsから分離。measured production costはnull。
scalar recoveryはpublic validationより先にcreate-only/fsync/SHA保存。
RUN_STARTED leaseはscience retryを拒否し、public failureの回復はprivate scalar serializationのみ。
private source/vector/unitaryはGitに含めず、checkpoint path/SHA/identity/time/branch metadataだけ公開可能。

**検証**：既存195＋新規65＝260 tests PASS。production truth=0、FS-R1 science=0、Ritz/proxy/fit/scoring=0。
旧artifactのdiffは空。publication manifestは自己除外し、source origin/resultとverified snapshotを別fieldで保持する。
公開branchは `pf-first-study-fs-r01-branch-extension-20261007`。post-push状態は独立remote照合receiptとhandoffで報告する。

GPTに確認してほしい点：pre-registered cluster解決/停止規則と明示座標authorityを含むv2が、FS-R1 Phase Aの実行承認に足るか。
順序はR0.1→GPT review→別承認のPhase A→prediction freeze→Phase B。ここで停止する。
