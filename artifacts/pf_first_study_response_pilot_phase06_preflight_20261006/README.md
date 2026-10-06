# Phase 0.6 — production adapter and science preflight

`production_execution_ready=true`、`science_authorized=false`。実装とpreflightは完了。H4 science action countおよびsaved truth accessは**0**。この時点で停止する。

起点はPhase 0.5 commit [`48f3d889d096f2fe3af55c200a757747df384941`](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/commit/48f3d889d096f2fe3af55c200a757747df384941)。normative JSONのSHA-256は`38ddb97f8f3c0bcc155eb9be23fb650772db264b6da0686f905a1d7d8ba482e3`。science仕様は変更していない。今回の§20の明示許可に従い、H4のH・13 groups・CISD計15配列をidentity確認だけにdecodeした。

## 読む順序

1. [verification.json](verification.json) — 75 tests（追加53、既存22）と判断の範囲。
2. [GO_NO_GO_FOR_H4_SCIENCE.json](GO_NO_GO_FOR_H4_SCIENCE.json) — readiness、未承認のscience、将来の固定回数。
3. [production_adapter_design.md](production_adapter_design.md)、[phase_b_truth_barrier.md](phase_b_truth_barrier.md)、[cold_replay_design.md](cold_replay_design.md)。
4. [production_source_identity.json](production_source_identity.json)、[expected_vs_implemented_action_counts.json](expected_vs_implemented_action_counts.json)、[truth_access_audit.json](truth_access_audit.json)。
5. [phase_a_schema.json](phase_a_schema.json)、[source_manifest.json](source_manifest.json)、[publication_manifest.json](publication_manifest.json)、[test_phase06.py](test_phase06.py)。

## 実装と検証

専用allowlist loader、Padé S2 backend、response/Ritzの共通9-arm interface、固定fit、完全cold replay、create-only scalar artifact、commit/hash/remote検証後のPhase B readerを実装した。productionでは別途承認されたphase-specific execution recordがない限り演算／truth readerが停止する。preflightから承認recordは作成しない。

syntheticのrank8、rank1停止、rank0でcounterが一致。rank8の2-pass nominalはH 18、PF forward 220、adjoint 44、response SVD 8、RHS 176、small Ritz 8。H4のactual rank、conditioning、proxy、fit、成否は未取得。

## 再現

Python環境はnumpy 1.26.4 / scipy 1.14.1 / pytest 8.3.3 / jsonschema 4.26.0。repository rootで以下を実行できる。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider artifacts/pf_first_study_response_pilot_phase06_preflight_20261006/test_phase06.py artifacts/pf_first_study_response_pilot_phase05_20261006/test_phase05.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python artifacts/pf_first_study_response_pilot_phase06_preflight_20261006/verify_preflight.py
python artifacts/pf_first_study_response_pilot_phase06_preflight_20261006/phase06_runner.py --preflight
```

これらはidentity-only H4 checksとsynthetic arithmeticだけを行う。`--phase-a` / `--phase-b`は承認recordなしでは停止する。scienceの実行は別途GPT/ユーザー判断後の作業。

## Handoff

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。Branch: `pf-first-study-response-pilot-phase06-preflight-20261006`。このdirectoryの公開commitはGitHubのbranch履歴／最終handoffに示す。manifestは自己除外し、含有commitを自己参照しない。既存Phase0.5の25 filesと元sourceは履歴から参照し、再生成・再commitしない。

GPTに確認してほしい事項は、固定仕様の実装適合性と、次のH4 Phase Aを承認するかの判断。readinessは科学的有効性・新規性・resource improvementの証拠ではない。formal result、Phase0、Phase0.5、S4は変更していない。
