# H4 Phase B — saved-scalar scoring

**Outcome C: `point_only`**。A1/A2のS_absはA0より減ったが、A0 S_under=0でstrict underestimation reduction条件を満たさない。response_unique_tradeoff=trueはA1 S_under0対A2正値に基づく固定Pareto判定で、accuracy/cost優位やOutcome Aではない。

New science actions **0**。saved direct **12**、saved exact proxy **22**、A3 reference fits **3**。既存96＋追加35、**131 tests PASS**。Phase Aのprediction/coefficients/commitは変更せず、Attempt1も保持した。次stageは開始せず、commit/push/remote verification後に停止する。

読む順序: [scientific_outcome.json](scientific_outcome.json) → [report.md](report.md) → [aggregate_metrics.csv](aggregate_metrics.csv) / [response_vs_ritz.csv](response_vs_ritz.csv) → [verification.json](verification.json) / [phase_a_freeze_verification.json](phase_a_freeze_verification.json) → source/truth/access/action manifests。mとoracle比較は診断のみ、selector/outcome変更へ使わない。

Phase A freeze `53a88c28b7587ab61efb93d6ba30974c9d3d6404`。prediction SHA `9ce3d4e7ec89575f1d661515cddb636fab0288c5c4149df1c85dc529adace18f`、strict payload SHA `4c10e6e766319c88bf8375c6c1422a43dbb75df8becefb8a5dee4aa4e5b25eb4`。source/code/protocol、両prediction blob、remoteとpublication manifestをtruth読込前に検証した。

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。Branch: `pf-first-study-response-pilot-h4-phase-b-20261006`。新しい結果artifactだけをnormal commit/pushする。remoteの結果blobとprediction-source/truth-source blobsを独立取得して照合し、40-char result SHAは最終handoff／external receiptに保存する。self-referenceを避けpublication manifestは自己除外。

GPT/userへの判断事項: generic state improvementとfit/proxy residualを次の研究候補とするか、またbaseline underestimation floorを今後の独立protocolでどう扱うか。今回は研究方針・threshold・formal claimsを変更しない。
