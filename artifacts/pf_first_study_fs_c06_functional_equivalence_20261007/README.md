# FS-C0.6：functional-equivalence source reconstruction audit

最終判定は **NO_GO_RECONSTRUCTION_MISMATCH**。既存H02候補と、各条件1回の固定再構成の両方で、必須のhistorical Hamiltonian SHA完全一致を満たさなかった。whole-pickle SHAだけを理由に棄却した結果ではない。FS-C1は開始していない。

起点はFS-C0.5 `75fe0d65a2940f160ea42f6414fc2246d67bd0cf`、契約をdecode前に固定したcommitは `a5fb9835657c3e5ac1658d1323b5746bf318fc8c`。コード・環境・許容差を結果後に変えていない。再構成はN₂・COとも正常にreturnし、technical failureは0。historical H01 pickleは現在もmissingであり、historical source recoveredとは呼ばない。

| 条件 | source | 計算したHamiltonian SHA | CISD fingerprint最大絶対差 |
|---|---|---|---:|
| N2 | 既存H02 | `eafba466ff0d7503ab178d5bd90207f5bc33715a1282cce299236ca5077d3e7c` | 1.43679851e-08 |
| CO | 既存H02 | `d54736a5c167508c68cf56baa2b49f61cb35d89c0caa477f406ca5a69e7b45cd` | 2.95493607e-08 |
| N2 | 1回再構成 | `f4a08b755a4e903f4e9611fee394d6101a5d27279a1bd8af567b97920da5402e` | 1.71706149e-08 |
| CO | 1回再構成 | `27ed246b354c754a506541dac81650aafdfa413b375fadf0b736822c171fb4c5` | 1.23575689e-09 |

historical H SHAはN₂ `62ed51d7bd47f6596a1a6a40cc0330e4727dc51f42114bd05226dcef1f884be7`、CO `1fed49b19bd97eef281089589112128fe46914ef8ed843e739e8588714290224`。算出規則はhistorical CSR shape/indptr/indices/dataのbytesをそのままSHA256に入力する。丸め・sort・reorderによる救済は行っていない。

geometry/sector/basis順序は一致し、removed constant差はN₂約1.42e−14 Ha、CO約2.27e−13 Ha。CISD差は1e−6以内。ただし、この数値的一致でH完全一致の必須条件を置き換えない。group countとterm count列は一致し、ordered group SHA列は4sourceとも不一致。numerical group contentの独立検証はH棄却後には実施していない。

[M00 reproduction](M00_reproduction.json)は保存された3 training proxy・係数・prediction・B0をtargetsとして維持し、新しいproxy/fit差は **null／NOT_RUN**。PF/echo、production arbitrary-vector、production cold PF/echo/fitも未実施であり、差0やPASSとは報告しない。sourceをfresh loadした4組のidentity replayは一致した。これはhistorical sourceとの一致やbackend再現のPASSではない。

[費用記録](cost_ledger.json)はsource validation 14 actions（prepare_condition 2回＋identity/fingerprint audit 8回＋予備source load/inspection 4回）、ground solve 2回、FS-C1 science 0、新direct PF truth 0。preliminary decode 4回も含めsource loadは12回。PF/echo 0、Ritz matvec/solve 0。expm内部作業はunknown/null。再構成のwallはN₂8.570秒、CO11.183秒、process peak RSSは約592 MB／609 MB。環境はPython3.12.3、NumPy1.26.4、SciPy1.14.1、PySCF2.7.0、OpenFermion1.6.1、Qiskit1.3.0／Aer0.15.1、BLAS/OMP/MKL各1thread。

operational sourceは採用できず、sanitized exportは0。private matrix/vector/pickle/exact stateは公開しない。exact groundはprivate validation fingerprintに限って使った。新v3の3-point M00、M10同一座標、M11 primary、M01 challengerを維持し、v1/v2と旧研究artifactは変更していない。

過去H02 server auditのH一致・差0は、当時のserver cacheについてのattestationである。今回見つかったローカル候補の同一性を保証しない。H SHAが違う原因（solver丸め、mapping、他の差など）は本監査では特定せず、物理的差の大きさも確定しない。

読む順序：このREADME → [判定](GO_NO_GO_FOR_FS_C1.json) → [source契約](source_contract.md) → [候補監査](candidate_source_audit.json) → [再構成監査](reconstruction_audit.json) → [fingerprint registry](historical_fingerprint_registry.json) → [cold](cold_replay_audit.json)／[費用](cost_ledger.json) → [verification](verification.json)。テストは既存114＋新規22＝136件すべてPASS（[tests.log](tests.log)）。再構成用Python3.12環境にはjsonschemaがないため、テストは既存114件と同じPython3.11環境で実行した。再構成環境は変更していない。新規テストのPF/echoはsynthetic 2×2、係数再現はsaved-scalarのみで、N₂/CO source/backend reproductionの代替ではない。

GPT/userに判断を依頼する点は、当時監査済みserver sourceを回収する方針、または別途source acceptance契約を再検討するか。ここでは契約を緩めず、追加再構成もFS-C1も開始せず停止する。slideは変更していない。
