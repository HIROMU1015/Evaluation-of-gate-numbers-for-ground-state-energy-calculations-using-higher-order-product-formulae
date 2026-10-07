# FS-R1-A0 production numerical-contract freeze

**GO_FOR_FS_R1_PHASE_A_PRODUCTION**（契約・実装のpreflight判定）。production science / truth accessは0。
このGOはPhase A/Phase B実行承認ではない。GPT reviewと別のPhase A production承認まで停止する。

起点4e5c3ba2e3497915cd1668d9ac5cd77640ab2938の停止理由を、結果を見ずに閉じた。
v3はFS-R1-20261007-v3、freeze日は2026-10-08。旧v1/v2・science artifactを上書きしていない。

読む順序：

1. [GO判定](GO_NO_GO_FOR_PHASE_A_PRODUCTION.json) → [承認済みamendment](numerical_contract_amendment.md)
2. [v3](fs_r1_protocol_v3.json) → [数値契約](fs_r1_numerical_contract_v1.json)
3. [fixed-design propagation](fit_uncertainty_propagation.json) → [budget intervals](budget_uncertainty_contract.md)
4. [norm](norm_contract.md) / [replay](replay_contract.md) / [Ritz](ritz_replay_contract.md)
5. [順序](phase_a_orchestration.md) / [lease](run_lease_contract.md) / [recovery](recovery_contract_v2.md)
6. [317 tests](tests.log) → [verification](verification.json) → [production zero audit](production_action_audit.json)
7. [source identities](source_identity_audit.json) / [unchanged science audit](unchanged_science_contract_audit.json)
8. [code identities](execution_code_identity.json) / [authority manifest](source_manifest.json) / [publication manifest](publication_manifest.json)

|item|frozen rule/value|
|---|---|
|raw proxy replay|absolute difference≤1e-11 Ha; no primary rtol|
|input norm|abs(l2 norm−1)≤1e-12|
|PF/reference norm|abs(l2 norm−1)≤1e-10|
|N2 tau_fit(t0)|1.1122914179929199e-7 Ha|
|CO tau_fit(t0)|9.800205391365774e-8 Ha|

PはH01のt/t_ref scaled designからlstsq(...,I3,rcond=None)をunscaleした固定linear map。
係数のtauはtau_g×P各rowのL1 norm、predictionのtauはtau_g×qPのL1 norm。
P/w/係数bound/t0 boundは固定coordinateのみから計算した。手入力の近似値をauthorityにしていない。
fitの外挿でraw replay boundが増幅することも、この固定mapの結果として保存した。
これらはreproducibility uncertaintyであり、model bias/truth certificate/resource etaではない。

Magnitude interval=[max(0,|p|−tau),|p|+tau]。c_max≥epsilonならNUMERICALLY_INDETERMINATE_BUDGETで全budget null。
それ以外はB_min/B_maxをdenominator intervalから計算しnominalも保存。clippingやnominal-only feasible救済なし。
Budget replayはprediction gateと解析的伝播により判断し、独立のbudget atol/rtolは導入しない。
両pass indeterminateならundefinedのまま保存しfinite-budget coverageはfalse。status/denominator sign changeはfail。
ratioもpositive intervalから算出しprediction_only_not_truth_scoredとする。

Ritzはrank/stop index/reason/projected dimension/pivot/tie branch/zero-nonzeroが完全一致。
各passで64 eps Nのorthogonality/既存projected Hermiticity gateを独立に満たす。
Energy/residual差は保存するが新しい手決めdifference toleranceはない。downstream proxy replayも必須。
ASTによる追加はreturn診断だけで、固定済みMGS/lowest Ritz pair/phase/tieの算術は同一。
cached Hpsi/HZからRitz residualを記録し、H actionを追加しない。

順序はN2 initial→CO initial→initial aggregate recovery→N2 cold→CO cold。
各scientific return直後にも個別recoveryを保存し、public/numerical schema processingに先行する。
同一authorization_idのleaseはrun IDを変えても再利用不可。failed/partial/completed/public-failedの全状態を保護する。
public failure後はprivate scalar bytes/hash/lease bindingsを確認してserializationだけを復旧し、scienceは再実行しない。
未来の本番入口は別の明示Phase A authorizationとactual v3/code hashを要求し、A0からのdispatchを拒否する。
code hashはexecution_code_identity.jsonのparsed JSONをcompact/sorted+newlineへcanonical化したSHA。値はverificationに保存。

**検証：既存260＋追加57＝317 PASS**。
input/output normとraw replayのinclusive boundaries、固定P/wの独立検算・全perturbation vertices、budget境界/ratio、
Ritz categorical/independent gates、initial-before-cold、indeterminate N2でもCO継続、lease重複/再利用、
recovery-before-public/public故障時no-rerun/hash/binding改変、authorization拒否、Ritz算術AST同一性を検証した。
norm境界の試験は表現されたnorm errorの≤を検査する。1+tolがbinary64で境界を超えて丸まる場合もULP slackは加えない。

N2/CO archiveはwhole SHAで再確認のみ。numeric source decode/H matvec/Ritz/PF/echo/fit/arm prediction/budget productionは0。
元pickle・ground・historical truthを開かず、branch/Schur/direct truthは0。
本番RUN_STARTED/recovery/prediction SHAは未作成。pytestの模擬lease/recoveryだけで故障経路を検証した。
physical production数値成立・性能は未測定。v3 prediction用のPhase B barrierは後段の別review/承認対象。
private source/vector/unitary/recoveryはGitへ公開していない。公開される小さなP/A/wはユーザー§41が指定した固定design定数。

GPTに確認してほしい点：このv3数値契約とlease/recovery/orchestration実装を、別承認のPhase A productionへ進めてよいか。
公開branchはpf-first-study-fs-r1-a0-numerical-contract-20261008。
commit/push後の40桁SHA・remote先端・独立取得blob照合は外部receipt/handoffで報告する。A0公開後に停止する。
