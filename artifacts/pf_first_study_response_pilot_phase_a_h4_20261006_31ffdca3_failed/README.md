# H4 Phase A — failed artifact boundary

**PHASE_A_FAILED**。H4 Phase Aを1回実行したが、公開artifact作成前のstrict schema検証で停止した。prediction freezeは未完了。Phase B／saved truth accessは0。追加scienceは実行していない。

起点: [`6fae17723f888a62a998f90436516785a67651c6`](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/commit/6fae17723f888a62a998f90436516785a67651c6)。Phase0.5 protocolとPhase0.6 code/schema/source identityは変更せず使用した。今回のapprovalは[authorization.json](authorization.json)にPhase A限定で保存する。

## 原因と保存状態

凍結loaderの`ordered_group_identity=list(zip(groups, hashes))`はPython tuple pairsを返す。凍結schemaはJSON arrayを要求するため、in-memory objectへ直接行ったjsonschema検証が失敗した。canonical JSONのroundtripではidentity metadataがschemaに適合し、source hashも変わらないことを、science演算なしで再現した。

wrapperは数値payloadを検証前に保存しておらず、process終了によりKrylov rank、SVD/condition、residual convergence、fit coefficients/status、cold-replay差、rank依存counterを回収できない。`execute_phase_a`の正常returnと内部counter比較通過はobserved control flowとして記録するが、rank8の実測値とは報告しない。これはartifact integrityのhard failureであり、科学的成功／失敗の判定ではない。

## 読む順序

1. [failure.json](failure.json)、[verification.json](verification.json) — 停止点と未保存値。
2. [schema_failure_reproduction.json](schema_failure_reproduction.json)、[test_identity_serialization.py](test_identity_serialization.py) — metadata-only再現。
3. [action_counts.json](action_counts.json)、[numerical_gates.json](numerical_gates.json)、[truth_access_audit.json](truth_access_audit.json)。
4. [authorization.json](authorization.json)、[source_identity.json](source_identity.json)、[source_manifest.json](source_manifest.json)、[publication_manifest.json](publication_manifest.json)。

`PHASE_A_FROZEN`、prediction SHA、Phase A freeze commitは存在しない。このfailed-attempt auditのGitHub commitをfreeze commitに流用しない。

## 次の判断

GPT／ユーザーに、serialization-only修正と検証前のscalar recovery保存、その後の新しいPhase A試行を別途承認するか判断してほしい。今回、その修正・再計算・Phase Bは実行していない。formal result、Phase0、Phase0.5、Phase0.6、S4の原本は変更していない。

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。Branch: `pf-first-study-response-pilot-h4-phase-a-20261006`。公開するのは失敗監査とprovenanceのみで、state/vector/matrix/unitary/pickle/private runtimeは含まない。
