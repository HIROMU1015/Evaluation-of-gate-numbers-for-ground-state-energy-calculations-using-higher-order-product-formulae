# Attempt 2 serialization/recovery preflight

Science action count **0**; saved truth access **0**. Existing75 + new21 = **96 tests passed**. Production15 identity metadata roundtrip passes the unchanged strict schema with identical source hash. Attempt1 audit `3d7a923f2a8d11aff57a05454eca8e142496833e` is preserved.

Read [serialization_fix.md](serialization_fix.md), [serialization_preflight.json](serialization_preflight.json), [preflight_tests.log](preflight_tests.log), [test_retry2.py](test_retry2.py), then [retry2_runner.py](retry2_runner.py).

Only normalization, private scalar recovery, their tests/preflight and associated orchestration are added. This package is committed before science. The runner requires a clean exact commit/branch, separately supplied Attempt2 Phase-A-only authorization, 1 execution plus 1 complete cold replay, and create-only runtime/output. It has no Attempt3, PhaseB or automatic retry path. Phase0.5 normative protocol, Phase0.6 code/schema and Attempt1 original files are unchanged and hash-registered.

Branch: `pf-first-study-response-pilot-h4-phase-a-retry2-20261006`. The later scalar science artifact is separate and create-only. This preflight is not a prediction freeze or a science result.
