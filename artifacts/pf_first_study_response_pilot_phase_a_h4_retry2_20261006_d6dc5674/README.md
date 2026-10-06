# H4 Phase A Attempt 2 — technical retry

**PHASE_A_NUMERICALLY_READY**。Attempt2のscience初回1回＋complete cold replay1回を完了。private recovery snapshotを先に保存し、JSON-native normalization後に凍結strict schemaを通過した。saved truth access **0**、PhaseB **未実行**。prediction freezeをGitHubへ公開した後に停止する。

## Numerical review

Krylov rank=8、prefix stop=False。orthogonality residual=5.03962e-16。response8 SVD rank=[8]、retained condition=3.4991704。66/66 residual convergence checks PASS。response8 relative residual=0.208834–0.208975、||z||=8.40242e-09–2.13619e-06。

Ritz8 projected dimension=9、numerical gates PASS、unique lowest pair。A0/A1/A2 primary fitsは全てfit_ok。cold replay最大差=0.0。H18、PF forward220、adjoint44、response SVD8、RHS176、small Ritz8、fit27、全counterは固定contractと一致。

residualはequation-solving診断でありaccuracy certificateではない。truth-dependentなaccuracy、underestimation、response/Ritz優劣、Outcome A/B/C/D、resource benefitは判定していない。

## 読む順序

1. [numerical_gates.json](numerical_gates.json)、[verification.json](verification.json)。
2. [attempt_history.json](attempt_history.json)、[serialization_fix.md](serialization_fix.md)、[serialization_preflight.json](serialization_preflight.json)、[recovery_snapshot_audit.json](recovery_snapshot_audit.json)。
3. [phase_a.json](phase_a.json)、[predictions.json](predictions.json)、[fit_results.csv](fit_results.csv)、[response_diagnostics.csv](response_diagnostics.csv)、[ritz_diagnostics.csv](ritz_diagnostics.csv)、[proxy_values.csv](proxy_values.csv)。
4. [action_counts.json](action_counts.json)、[truth_access_audit.json](truth_access_audit.json)、[source_identity.json](source_identity.json)、[source_manifest.json](source_manifest.json)、[publication_manifest.json](publication_manifest.json)。

## Freeze identity

`predictions.json`はstrict payload内predictionsのexact canonical projectionで、新fitではない。prediction SHA-256: `9ce3d4e7ec89575f1d661515cddb636fab0288c5c4149df1c85dc529adace18f`。補助CSVにsign/magnitude/qualityを保存する。

Phase0.6 truth barrierが検証するcomplete scalar blobは`phase_a.json`。SHA-256: `4c10e6e766319c88bf8375c6c1422a43dbb75df8becefb8a5dee4aa4e5b25eb4`。hashの役割を混同しない。両hashを`PHASE_A_FROZEN`に固定し、containing40-char commitはself-referenceを避けrepository外freeze receiptと最終handoffに保存する。

private recovery snapshot／L_m,a_m projected diagnosticsはrepository外に保持し、publicにはhash・record数だけを保存する。snapshotはPhaseB inputにもprediction freezeの代替にもならない。vectors/states/basis/response matrices/unitariesは公開していない。

## Attempt history and authority

Attempt1は初回＋cold replayを実行後serialization boundaryで停止し、output recovery／prediction freezeなし。truth access0。audit commit`3d7a923f2a8d11aff57a05454eca8e142496833e`を変更せず履歴に保持する。Attempt2は今回許可されたtechnical retry1回だけ。Attempt3は実行していない。

science authorityはPhase0.5 JSON、SHA-256 `38ddb97f8f3c0bcc155eb9be23fb650772db264b6da0686f905a1d7d8ba482e3`。Phase0.6 kernels/schemaは無変更。execution base `f45ea0716bbcc8cfa0aae34db47a517209aab9c8`でserialization/recovery packageをcommitしてから実行した。既存75＋追加21、計96 tests PASS、retry前science count0。

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。Branch: `pf-first-study-response-pilot-h4-phase-a-retry2-20261006`。必要scalar artifactsをnormal commit/pushし、remote tipと独立取得blobを照合する。formal result、Phase0、Phase0.5、Phase0.6、S4、Attempt1 auditは変更していない。

GPT／ユーザーに判断してほしいのは、このnumerical viabilityを確認した後にPhaseB saved-scalar scoringを別途承認するか。今回はPhaseBへ進まず停止する。
