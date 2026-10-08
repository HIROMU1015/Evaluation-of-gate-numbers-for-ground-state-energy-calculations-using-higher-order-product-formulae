# FS-R1 Phase A production — frozen v3 prediction review

**PHASE_A_FROZEN_READY_FOR_GPT_REVIEW**。固定entrypointを1回実行し、N₂/COの全4 arm・cold replay・数値gateが正常完了した。
全8 armが有限budget区間。truthによる安全性・資源削減の判定は未実施。Phase Bの承認はfalseで、ここで停止する。

読む順序： [Phase B判定](GO_NO_GO_FOR_PHASE_B.json) → [保存結果](production_results.json) / [budget](predicted_budgets.json) → [Ritz](ritz_diagnostics.json) / [cold](cold_replay.json) / [数値gate](numerical_gate_audit.json) → [counts](action_counts.json) / [cost](cost_ledger.json) / [truth audit](truth_access_audit.json) → [prediction manifest](prediction_manifest.json) / [source manifest](source_manifest.json) / [remote proof](remote_verification.json)。

M00′はCISD 3点fit、M10′はRitz8の同一3点fit、M01′はCISD local、M11′は同一Ritz8 local（primary）。
以下の区間幅は数値再現性の幅であり、true PF errorのcertificateではない。Budgetはpredicted QPE PF rotations。

|condition|arm|signed prediction (Ha)|uncertainty (Ha)|nominal budget|budget interval|
|---|---|---:|---:|---:|---|
|N2_active_eq_sto3g|M00p|-2.971308155823279e-05|1.1122914179929199e-07|299615772.6844654|[299358941.00748473, 299873045.431624]|
|N2_active_eq_sto3g|M10p|-2.1174490948798008e-05|1.1122914179929199e-07|281102281.27839935|[280876196.6750522, 281328730.1377769]|
|N2_active_eq_sto3g|M01p|-2.8146607939821813e-05|1e-11|296038849.9350435|[296038827.3734132, 296038872.4966773]|
|N2_active_eq_sto3g|M11p|-2.1136831775269882e-05|1e-11|281025694.41568553|[281025674.0843867, 281025714.7469872]|
|CO_active_eq_sto3g|M00p|-2.8632627528376264e-05|9.800205391365774e-08|573991663.7360073|[573561683.2540551, 574422289.3863002]|
|CO_active_eq_sto3g|M10p|-1.9492938036226276e-05|9.800205391365774e-08|536483867.9660144|[536108227.67684627, 536860035.03152645]|
|CO_active_eq_sto3g|M01p|-2.6690906602018264e-05|1e-11|565590825.9010235|[565590783.2693355, 565590868.532718]|
|CO_active_eq_sto3g|M11p|-1.9457265017262835e-05|1e-11|536347072.94336736|[536347034.6062329, 536347111.2805072]|

両分子・両passともrequested=retained rank=8、projected dimension=9。rank-stop index=null、reason=requested_rank_reached。
phase pivot=1567、tie branch=lowest_projected_eigenspace:e0がinitial/coldで完全一致した。
最大raw proxy/fit係数/予測差はすべて0。energy/residual差も0だが、独自の差toleranceは追加していない。
各passのnorm・Cauchy・Ritz orthogonality/Hermiticity gateが合格。Ritz residual normはN₂ 0.0005757249717132314、CO 0.0017703567530129947。収束のtruth証明ではない。

Actual PF=32、echo=32、explicit H matvec=36、small Ritz solve=4、fit=8。group applications=39904、materializations=11520。
entrypoint wall=4.181532307993621 seconds、process peak RSS=168755200 bytes。
RSSは同一processの累積high-water mark。expm_multiply内部workはunknown/null。Classical costをQPE rotationsへ換算していない。

Truth accessの6項目、新direct truth座標、branch ladder、ground operational readsはすべて0。runtime open auditでもpickle/truth module sourceは0、sanitized archiveは各分子2回。
各科学return後のprivate recovery 7件はcreate-only/fsync/SHA/lease bindingを検証。initial aggregateはcoldより前。private snapshot bytesは公開していない。

Prediction SHA-256: `d1f95e5ee38e72cc5cb04cfb805c0ae441060104828c18268574acda5d2215a9`。prediction.sha256はcanonical prediction_manifest.jsonのSHAで、production_results.json単体のSHAとは役割が異なる。
Science origin/result commit: `89c091e885c07b7c02883b1479a143c23f51df3c`。このcommitをGitHubから独立bareへ取得し、26新規blobと84 authority blobを照合した。
現在のbranchはpf-first-study-fs-r1-phase-a-production-20261008。後続のhandoff commitは検証receipt・判定・資料だけを追加し、science-originの全blobを保全する。
handoff commit自身のremote tip・blob・manifest検証はpush後の別receipt/handoffで記録する。commit/hashを自身のblobへ埋め込む循環は作らない。

既存317テストは本番前に全PASS。旧FS-R0/R0.1/A0・H4・C0等のartifactと既存branchは変更していない。
preflight.py / authorized_invocation.pyは履歴・承認追跡の資料。今回のauthorizationは消費済みで、実行scriptを再起動してはいけない。
freeze_saved_scalars.pyは保存値だけの包装。verify_saved_package.pyは読み取り専用のhash/committed blob/scalar/CSV検証で、source load・Ritz・PF・echo・fit・truthを実行しない。

GPT/userに判断してほしい点は、このprediction freezeのレビューと別のPhase B承認。v3のPhase B barrierがprediction/uncertainty/code/source/recovery/remoteにbindすることも別途確認が必要。
physical branch certification・true safety・resource outcomeはまだ未確立。12点truth ladderは1点も計算していない。
