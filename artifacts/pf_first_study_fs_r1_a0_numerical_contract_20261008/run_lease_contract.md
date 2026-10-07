# Authorization-keyed exclusive lease

Private registry is frozen in v3. Atomic mkdir keyed by SHA256(authorization_id) and create-only/fsync RUN_STARTED hold run ID, authorization/protocol/source/code hashes, UTC time, pid and host.
Changing run ID cannot reuse authorization. Every existing lease directory blocks another run, including failed/partial/serialization-failed/completed states. A0 consumes no production authorization/lease.
RUN_STARTED is immutable; create-only durable stage events distinguish calculation started, scientific return, recovery saved, science completed, public serialization failed/completed and publication complete.
Incomplete directory creation/fsync remains conservatively consumed. No lease deletion, retry or rollback is part of the API.
Publication completion requires independent remote proof. Public/schema failure after science completion leaves science state completed; only serialization recovery is allowed.
These are workflow guards, not authentication against arbitrary Python or manual private-file deletion.
