# Phase B saved-scalar scoring implementation

Existing96 + new35 = 131 tests PASS before production truth access. Phase0.5 protocol, Phase0.6 scorer/selector/fit rules and all Phase A bytes remain unchanged.

`phase_b_scoring.py` verifies both frozen prediction blobs, their fixed hashes, full40 commit, remote branch, source/code/protocol identity and Phase A publication manifest before invoking a saved-scalar reader. It calls the inherited fixed scorer, adds 22-coordinate proxy diagnostics, and exposes the exact Outcome/Pareto predicate trace.

`phase_b_runner.py` requires a new Phase-B-only authorization and clean committed code, allows one intake of 12 direct / 22 exact proxy scalars, forbids production array/other CSV reads after identity verification, and blocks response/Ritz/eigen/Schur/PF entry points. Only A3's three fixed reference fits are observed/authorized. A0/A1/A2 and m-diagnostic coefficients/predictions are never refitted.

No metric/threshold/m/outcome/cost axis changes; no new H/PF/state/ground/direct-truth calculation; no post-hoc selector. Raw file byte integrity and nonselected row-text scanning are separated from selected scalar decoding. A3 fits and scoring views are saved privately before publication assembly.

Read implementation_preflight.json, preflight_tests.log, test_phase_b_scoring.py, then phase_b_scoring.py and phase_b_runner.py. This package is committed before production saved truth is opened.
