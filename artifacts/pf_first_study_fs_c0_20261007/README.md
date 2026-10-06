# 第1研究 FS-C0 — decision-relevant calibration intervention

2026-10-07 JST。**FS-C0の資料・実装監査を完了、FS-C1はNO-GO／science未承認。** 原S0のN2/CO selected timeに対応するtruth joinは2/2成立した。既存native PF関数は任意の互換vectorを取れる構造だが、現在の元H01/private sanitized cache、canonical array identity、Ritz入力に対する数値・内部費用契約、M00再現許容差は未完了。これをscience不支持と扱わない。

原baselineは3点であり、「元5点」への一致は不成立。時刻・baseline定義の修正は未承認のため operational training_times=null として実行を閉じる。

production H/PF/echo/Ritz/proxy/fit/new truth/full-ground/Schur/array decodeはすべて0。H4 Outcome C、formal・Phase0/0.5/0.6、Attempt1/2、PhaseBを編集していない。C0は既使用development evidenceの設計・source/backend closure監査で、独立holdoutではない。

読む順序:
1. [GO_NO_GO_FOR_FS_C1.json](GO_NO_GO_FOR_FS_C1.json) / [source_and_backend_closure.json](source_and_backend_closure.json) / [backend_review.md](backend_review.md)
2. [research_decision.md](research_decision.md) / [four_arm_design.md](four_arm_design.md)
3. [fs_c1_protocol.md](fs_c1_protocol.md) / [fs_c1_protocol.json](fs_c1_protocol.json) / [algorithm_design.md](algorithm_design.md)
4. [cost_dictionary.md](cost_dictionary.md) / [predicted_action_budget.json](predicted_action_budget.json)
5. [H4_posthoc_decision_scale.csv](H4_posthoc_decision_scale.csv) / [headroom_reference.csv](headroom_reference.csv)
6. [verification.json](verification.json) / [tests.log](tests.log) / [serialization_end_to_end_test.json](serialization_end_to_end_test.json)
7. [evidence_registry.json](evidence_registry.json) / [source_manifest.json](source_manifest.json) / [publication_manifest.json](publication_manifest.json)

Implementation: [scoring_skeleton.py](scoring_skeleton.py)、[serialization_boundary.py](serialization_boundary.py)、[synthetic_math.py](synthetic_math.py)、[test_fs_c0.py](test_fs_c0.py)。production runnerは含まない。CLIを追加して本packageをscienceに使わない。C1開始は別の明示承認とclosure後。

依頼元3資料の原文は `docs/first_study/redesign_20261007/` へbyteコピーして公開する。元PhaseB worktreeのuncommittedファイルを移動・編集していない。

検証再現: 新規temporary directoryを使い、`PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q -p no:cacheprovider artifacts/pf_first_study_fs_c0_20261007/test_fs_c0.py`。synthetic frozen-blobテストはGit取得をfixtureへ置き換え、byte/hash barrierを試す。実GitHub publicationは別途独立取得して全新規blobを照合する。

publication manifestは自己除外、sourceのorigin/result commitとverified snapshotを別fieldにする。起点 `5b370ec22f7ffeac687ef70e1bcb87337f5fb976`。branch `pf-first-study-fs-c0-20261007`。handoff commitは最終報告とexternal receiptに残し、自己参照を作らない。
