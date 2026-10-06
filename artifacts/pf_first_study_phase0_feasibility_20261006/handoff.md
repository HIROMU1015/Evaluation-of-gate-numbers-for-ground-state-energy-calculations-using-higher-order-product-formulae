# GPT research handoff: first-study Phase 0

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
Branch: `pf-first-study-phase0-feasibility-20261006`
Source snapshot: `c515562f1c00b5402d5ca266852986ba12ca4002`
Final handoff commit: reported in the chat after non-force push and independent fetch verification. This file does not contain its own commit SHA.

## Read order

1. [README](README.md), then [report](report.md).
2. [Feasibility recommendation](feasibility_decision.json).
3. [Margin capacity](margin_capacity_first_study.csv), [resource headroom](resource_headroom.csv).
4. [Mechanism and budget summaries](mechanism_and_budget_summary.csv), [phase summaries](phase_group_summary.csv), [q scaling](phase_q_scaling.csv).
5. [Source registry](source_registry.json), [analysis protocol](analysis_protocol.json), [verification](verification.json), [tests](tests.log), [publication manifest](publication_manifest.json).

必要なrow-level CSV（phase_average_analysis、oracle_state_removal、budget_direction_attribution）、summary scalar、metric dictionary、元の依頼全文、純scalar builder、focused testsも同じhandoff commitへ含める。31個の既存sourceは起点commitのblobと同一で、origin/result commitとverified snapshotを別fieldで保持している。既存資料を再生成・重複commitしていない。

## Verified and unresolved

H4のstate-removal機構headroom、同符号underestimationへのstate寄与、linear imaginary-echoのphase分解、6条件margin恒等式、PF/time/domain別resource headroomを検証した。新規science actionは0、formal resultsとS4 no-benefitは不変。

実分子のresource headroomをstate correctionが回収できる割合、oracle-free response estimator、追加校正費用を含むnet gain、prospective safety/transferは未確立。GO_response_pilotはpost-hoc feasibility推奨であり、pilot実行やformal claim改稿の許可ではない。

## GPT/user decisions requested

- GO_response_pilot推奨を採用するか。
- exact-ground targetを維持するoracle-free response estimatorの具体仕様。
- H4 mechanism pilotと、その後のN2/CO 1条件resource評価の最小範囲・費用会計。
- 新規結果を論文へ入れる場合のfollow-up配置とclaim scope。

Phase 0は完了時に停止し、これらの研究判断を待つ。新規scienceを開始しない。
