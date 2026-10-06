# Serialization-only patch

Phase0.6 loader, science kernels, backend, fit, counts, truth barrier and strict schema remain byte-for-byte unchanged. The new `retry2_boundary.py` operates only after science returns and on identity metadata during preflight.

`to_json_native` is pure: tuple→list, numpy scalar→Python scalar, one-dimensional real/integer/bool/string metadata arrays→list, Path→string. It preserves insertion/order and numeric precision. Complex arrays/matrices, nonfinite values and nonstring object keys are rejected; science vectors/matrices are not publicized. `normalize_payload` checks canonical scalar bytes and the source hash before/after normalization. Frozen tuple/list canonical source identity bytes are identical.

Production preflight identity-decodes exactly H, 13 ordered groups, CISD and verifies all frozen hashes/dtypes/shapes/order/metadata. It reproduces the raw tuple schema failure, validates normalized metadata, dumps allow_nan=False, loads, revalidates, compares canonical bytes and all 15 identities. No H matvec/PF/response/Ritz/production fit or truth values are computed.

The first boundary after `execute_phase_a` returns is `write_recovery`: an outside-repository, exclusive-create, fsync, read-only scalar JSON plus SHA256. Its strict structure excludes truth/exact-state/private matrix fields, carries protocol/code/source/authorization/attempt provenance, and is reloaded/hash-validated before public schema validation/write. It is not a Phase B input or a public commit freeze. Frozen public writer remains unchanged; it receives the normalized scalar object and stores L_m/a_m only in a separate private directory.

Tests keep the old raw failure and new pass. Injected public-writer and strict-schema failures retain an identical recovery payload without a science rerun. Existing Phase0.5/0.6 truth barrier/cold replay/action-count tests are retained. No scientific method or threshold is altered.
