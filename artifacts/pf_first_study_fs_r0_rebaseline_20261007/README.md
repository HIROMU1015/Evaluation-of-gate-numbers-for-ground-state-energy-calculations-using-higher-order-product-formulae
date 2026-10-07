# FS-R0 regenerated-source re-baselining preflight

最終判定：**NO_GO_BRANCH_CONTINUATION_UNCLOSED**。FS-R1は開始していない。
原指示§44の分類はNO_GO_PROTOCOL_OR_BACKEND。具体statusはユーザー/GPTの明示回答による。

FS-C0.6 commit `14972353238cb001ccb1f754288daaae1ec3f65e`を起点とした追加artifact。
historical H01 source復元路線は終了。旧成果物に変更なし。
N2/COのexact one-shot reconstruction bytesが存在し、whole SHAをC0.6 cost ledgerと照合した。
これらを**new regenerated follow-up source**として固定し、private operational exportを2件作成した。
historical recovered / functional equivalenceの主張はしない。

読む順序：

1. [最終判定](GO_NO_GO_FOR_FS_R1.json) と [承認済みbranch契約回答](branch_continuation_amendment.md)
2. [研究pivot](research_pivot.md)、[新旧scope](historical_vs_new_source_scope.md)
3. [source registry](new_source_registry.json)、[new identities](new_source_identity.json)、[sanitization](sanitization_audit.json)
4. [protocol](fs_r1_protocol.json)、[4-arm contract](four_arm_contract.md)
5. [truth contract](truth_generation_contract.md)、[barrier](truth_barrier.md)、[freeze schema](phase_a_freeze_schema.json)
6. [scoring](scoring_contract.json)、[cost](cost_contract.json)、[planned actions](predicted_action_budget.json)
7. [cold replay](cold_replay_contract.md)、[recovery](recovery_contract.md)、[195 tests](tests.log)、[verification](verification.json)
8. [authority manifest](source_manifest.json)、[publication manifest](publication_manifest.json)

| condition | new H SHA256 | fixed absolute training (M00′=M10′) | fixed t0 | K |
|---|---|---|---|---|
| N2 | `f4a08b755a4e903f4e9611fee394d6101a5d27279a1bd8af567b97920da5402e` | 0.06263494343795273, 0.12526988687590546, 0.18790483031385818 | 0.5983202971910435 | 19176 |
| CO | `27ed246b354c754a506541dac81650aafdfa413b375fadf0b736822c171fb4c5` | 0.06546804264781796, 0.1309360852956359, 0.19640412794345388 | 0.6127481451622522 | 37936 |

H/CISD/basis/group order/component stored bytes、sector/origin、generation code/environmentをhashで固定。
oracle ground/overlap/gap/direct/historical truth/branch labels/acceptanceはexportしていない。
1568次元CSR interfaceはmetadata/静的検査まで。PF/Ritz/echo/sign/fitの数値試験は2～3次元synthetic。
production数値成立や性能はまだ検証していない。hash-only public manifestsにはmatrix/vector値を含めない。

M00′は新CISD 3点fit、M10′は同時刻で新Ritz8 fit、M01′/M11′はt0のlocal proxyでfitしない。
M11′ primary、M01′ cheaper challenger。新B0′ = gamma beta K / [t0(epsilon_E−|new M00′(t0)|)]。
c≥epsilonはinfeasible。historical B0/direct値を分母・truthに混ぜない。
epsilon_E=0.00015936001019904、beta=1.2、gamma=1.01、eta=0.02。
各conditionのprimary/local/state_increment/safety_repairは独立判定し、unsafeを平均で相殺しない。

将来Phase Aのplanned actions：PF/echo各32（initial16+cold16）、rank8ならexplicit H36、small Ritz4、fit8。
rank stopに応じて実際のH/small solveを数え、expm内部workはunknown/nullとして保存する。
classical costとpredicted QPE rotationsを別単位で保存し、incremental viewsも定義した。
scalar checkpoint/fsyncをpublic validationの前に作り、serialization失敗後にscienceを自動再実行しない。
prediction/protocol/source identity/all execution codeのactual committed blobsとindependent remote receiptを照合してからtruthへ進む。

**未確立事項**：new source上にlower-time branch anchorがない。
old S0と同じphysical branch continuationを、N2 t0/CO t0のnewtruth計2点だけでは閉じられない。
単点maximum ground-overlapへの置換、旧branch ID流用、追加anchor計算は行わない。
truth_only.pyのSchur stepはguarded toy/interface prototypeであり、production truth executorが完成したとの主張ではない。

**実行結果**：195 tests PASS（既存136+新規59）。FS-R1 science=0、新direct truth=0、branch solve=0、source再生成=0。
公開対象はcode/docs/scalar schemas/hashes/testsのみ。npz/pickle/matrix/vectorはprivateのまま。
build_r0.pyは今回のcreate-only source freeze記録であり、FS-R1 driverや再構成retryとして実行しない。

GPTに判断してほしい点：別契約でbranch-anchor extensionのtruth budget/time/continuation rulesを正式承認するか、direct PF truth路線を止めるか。
CodexはFS-R0 handoff後に停止する。新scienceの別承認はまだない。
branchは `pf-first-study-fs-r0-rebaseline-20261007`。public statusはcommit作成後のremote独立照合receiptと最終handoffで報告する。
