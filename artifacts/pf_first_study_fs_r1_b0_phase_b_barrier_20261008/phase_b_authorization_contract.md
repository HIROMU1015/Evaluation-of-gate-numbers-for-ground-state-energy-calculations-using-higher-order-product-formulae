# Separate Phase B science authorization

B0 issues no production authorization. A future explicit approval must provide: explicit_science_authorization=true; phase=FS-R1-Phase-B; request_stage=FS-R1-Phase-B-production; nonempty approval_reference; a new fixed authorization_id; protocol_sha256; prediction_sha256; science_origin_commit; handoff_commit; handoff_proof_sha256; phase_b_execution_code_sha256; branch_ladder_sha256; source_hashes; truth_coordinate_budget=12.

Use full-precision authority from phase_b_bridge_contract.json and parsed canonical execution_code_identity.json. The consumed Phase A authorization ID is rejected. B0 GO is preflight eligibility, not approval.

Validate authorization before freeze verification or a truth lease. Then validate actual v3 freeze/independent remote/recovery/source/code. Only then atomically create the fixed authorization-keyed lease in /tmp/fs-r1-phase-b-production-private-20261008/leases. Changing run ID cannot reuse approval. Failed/partial/completed/public-failed states all prohibit another science run. No production callback/registry substitution is accepted.
