# GPUサーバー側Codexへの再実行依頼：D2R R1 v1.1のみ

初回R1は本計算前のfocused-test gateで停止しました。Phase A runtime、protocol、amendment、
prediction、manifest、4 system cacheのidentityは全件合格しており、R1 output directory、
exact ground state、proxy、direct truth、GPU操作はすべて0です。

唯一の失敗は、閉鎖済みPhase B結果の再計算値が保存値と完全一致したにもかかわらず、testが
「必ず1 ULP異なる」ことを要求していたためです。v1.1ではtest-onlyのportable条件として
「完全一致または最大1 ULP差」を許可します。production source、保存済み科学結果、protocol、
threshold、R1規則は変更しません。

親指示
`review_response/gpu_pf_candidate_validation_r1_phase_a_cache_execution_prompt.md`の全規則を維持し、
以下の差分だけを適用してR1全体を新規branch/worktreeから一度実行してください。

## 固定版

- original R1 cache実装commit：`fba3383c6db8bde905c2f7b131de21f1c03d43da`
- portable-test実装commit：`832ca7af1de55cb738dea7007331c59d29342730`
- R1 protocol SHA-256：
  `186d2240bbf78733c1389fac66e2b261a7dfe50d8712b656ce0e1c45a6c67e49`
- Phase A cache amendment SHA-256：
  `a95a9abf87f1d428c35d34ed13cbea8c2ff930e91a3e5eb3a2550fd5d1dd1051`
- test portability amendment：
  `review_response/pf_candidate_validation_r1_test_portability_amendment_v1_3.json`
- test portability amendment SHA-256：
  `9cc7b101fdcca2f696e0d2a7ed43f4564bc3b42e9cd5c38397943b1426572cc3`
- frozen Phase A result commit：`efea5fe0718c2c2623935949460498da066bdec3`
- Phase A runtime inventory SHA-256：
  `5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91`

## 保存する初回停止

- branch：`gpu-pf-candidate-validation-r1-20260928`
- HEAD：`fba3383c6db8bde905c2f7b131de21f1c03d43da`
- status：`failed_pre_execution_tests`
- focused：33 passed、1 failed
- full tests：未実行
- R1 output directory：未作成
- exact/proxy/direct/GPU counts：全て0
- worktree：clean

初回branch/worktreeをreset、rebase、amend、削除、変更しません。

## v1.1の唯一の変更

対象field：

`strategy_summary.uncapped_counterfactual.aggregate_frozen_pauli_rotation_budget`

- 保存値：`8689143504.848944`
- GPU Python 3.12再計算値：`8689143504.848944`
- GPU差：`0.0`
- 閉鎖監査時の再計算値：`8689143504.848946`
- 閉鎖監査時の差：`1.9073486328125e-06`（1 ULP）

test assertionだけを次に変更済みです。

```text
abs(recomputed - stored) <= ulp(stored)
```

閉鎖監査JSONに記録された`ulp_difference == 1.0`の歴史的事実を確認する別assertionは維持します。
許容幅を1 ULPより広げず、科学値の不一致を隠しません。

## branchとworktree

```bash
git fetch origin --prune
git cat-file -e 832ca7af1de55cb738dea7007331c59d29342730^{commit}
git merge-base --is-ancestor \
  fba3383c6db8bde905c2f7b131de21f1c03d43da \
  832ca7af1de55cb738dea7007331c59d29342730
git merge-base --is-ancestor \
  efea5fe0718c2c2623935949460498da066bdec3 \
  832ca7af1de55cb738dea7007331c59d29342730
```

`832ca7af...`から独立worktreeと新規branchを作ります。推奨名は

`gpu-pf-candidate-validation-r1-v1-1-20260928`

です。同名があれば上書きせず連番を付けます。

`git diff fba3383c... 832ca7af...`を確認し、production runner/sourceや既存artifactに変更がなく、
test assertionとamendment/testだけの差分であることをauditへ記録してください。

## 再実行順序

親指示と同じ固定process environmentで、次を順に実行します。

1. protocol、cache amendment、test portability amendmentのhash照合。
2. Phase A runtime 56 files、113,469,289 bytesと4 system cacheのbyte-identity再照合。
3. focused tests全件。fail/skip 0を要求。
4. 全`review_tests`。fail 0、既知の`pennylane`だけ最大1 skip。
5. 両test gate合格時だけ、親指示の同じR1 commandを新規outputへ実行。
6. R1完了gate照合。
7. focused/full testsを再実行してlog保存。

推奨outputは親指示と同じ

`artifacts/server_pf_candidate_validation_r1_20260928_fba3383/`

です。初回停止時には作成されていないことを確認し、存在する場合は上書きせず連番を付けます。

R1 command、Phase A absolute path、計算count、完了条件、commit除外物、最終報告項目は親指示から
変更しません。

## commit、push、停止

全gate合格時だけ`r1_complete_stop_for_research_direction_review`と`R1_COMPLETE.json`を許可します。
軽量成果物とtest logだけを新規branchへcommitし、originへ新規non-force pushしてください。

報告後に停止します。R2、新方式実装、追加座標、direct truth、別分子・PF、threshold変更へ
進まないでください。
