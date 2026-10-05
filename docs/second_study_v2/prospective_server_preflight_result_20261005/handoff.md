# GPT review handoff — prospective preflight

Status: `prospective_budget_safety_preflight_complete_review_required`。
科学計算・GPU操作は0。共有環境変更0。実割当は `allocation_unverified`。

Publication status: `pending_user_push`。
本bundleはlocal commit済みだが未公開で、GPTがGitHubから成果を読める状態ではない。
ユーザーがpushを担当すると明示したため、Codexはこれ以上push/API書込みを試行しない。
通常HTTPS pushは認証情報不足、GitHub連携のGit tree書込みはintegration権限不足（403）で失敗した。
成果branchのremote先端は存在せず、公開snapshot SHAはnull、remote fetch/blob確認は未実施。
共有認証/環境/Git設定を変更せず、以下のコマンドをユーザーへ引き渡す。

Repository rootから実行する（科学計算runnerは起動しない）。

```bash
git -C .worktrees/gpu-pf-study2-prospective-preflight-20261005 push origin HEAD:refs/heads/gpu-pf-study2-prospective-preflight-20261005
```

push後のremote先端照合は次で行える。公開後の40文字SHAはlocal HEADと一致する必要がある。

```bash
git -C .worktrees/gpu-pf-study2-prospective-preflight-20261005 rev-parse HEAD
git ls-remote --heads origin gpu-pf-study2-prospective-preflight-20261005
```

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

Instruction branch: `pf-study2-prospective-server-preflight-20261005`

Instruction/handoff commit: `c04d95a9fa8b9653b58bea59169ce6e7352a9da0`

[指示commit固定リンク](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/commit/c04d95a9fa8b9653b58bea59169ce6e7352a9da0)

Result branch: `gpu-pf-study2-prospective-preflight-20261005`

Artifact origin/freeze commit: `dfdbc703443da4a847f8fb6c5975fc3d32c24e3a`

[成果資料commitの予定URL（未公開・現在取得不可）](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/commit/dfdbc703443da4a847f8fb6c5975fc3d32c24e3a)

そのcommitは13件のreview資料を含み、core manifest SHA-256は
`0e2cbc4dbcc9340c7189df44cb26754e03e3f9e17cdbcad63604de893953490f`。
後続handoff commitは公開状態のreport/audit/handoffとvalidation/manifestを更新する。
origin/freeze commitと、push後に検証する公開snapshot commitは役割を統合しない。

このbundleを含む40文字のlocal SHAと未公開状態を最終メッセージに示す。
pushが成功した後だけpublication SHA、commit固定リンク、remote先端/fetch/blob確認を報告する。
publication SHAを自身のmanifestへ埋める自己参照は行わない。
この文書自身がどのGitHub commitで開かれているかがresult snapshotの固定identityである。
source origin/result commitとverified snapshot commitは [source registry](source_registry.json) の別fieldを使う。

## 読む順序

1. 同commitの [AGENTS.md](../../../AGENTS.md) と [今回の指示書](../../../review_response/gpu_pf_study2_prospective_preflight_prompt_20261005.md)。
2. [report.md](report.md) — 完了範囲・計算0・制約。
3. [hardware_and_allocation.json](hardware_and_allocation.json) — timestamp、128 CPUs、実割当unknown、disk、既存Python metadata。
4. [candidate_inventory.csv](candidate_inventory.csv) と [usage_history_scope.json](usage_history_scope.json) — 20件案・別open-shell4件・既使用5件・実装除外2件、novelty未認定。
5. [parallel_resource_plan.md](parallel_resource_plan.md) と [resource_planning_arithmetic.json](resource_planning_arithmetic.json)。
6. [protocol_draft.md](protocol_draft.md) — 未確定10項目、implementation不足、全prediction barrier、missingness/immutable scoring。
7. [source_registry.json](source_registry.json)、[access_and_operation_audit.json](access_and_operation_audit.json)、
   [validation.json](validation.json)、[bundle_manifest.json](bundle_manifest.json)。

## GPT側の判断待ち

最終conditionのnovelty要件・history gapの扱い、geometry/strata、basis/active space/charge/spin/state recipe、
一般分子reference/time/T0/B0、beta/epsilon、fixed B1 arm selection/fallback、
M1全候補またはmetadata-fixed subset・rank/reference/width/adoption、
same-H ground/direct branch/gap/numerical gates、
承認されたCPU/RAM/disk/phase wall/全体wall/retryとfailure分母を判断する。
今回20件をtest setへ採用したり、CH2/HCNを未使用familyと認定したりしていない。

CPU1/BLAS1のhistorical H8 timings/RSSは計画参考であり、新server/new moleculeの資源保証ではない。
parallel worker数と各phase上限は未確定。one matrix storageだけでtruth可否を確約しない。
一般分子のtruth-free input wrapperが不足し、旧_prepare_systemにはground solveが含まれる。
source code変更・数値test・科学pilotを今回は行っていない。

次段階はGPT側・ユーザーのreviewと別承認。計算0のpreflight publicationをexecution authorizationと解釈しない。
input生成、reference、prediction、truth、scoringへ続けず、指定statusで停止する。
