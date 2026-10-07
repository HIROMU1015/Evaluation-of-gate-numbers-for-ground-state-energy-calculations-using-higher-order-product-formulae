# FS-C0.5 execution closure — NO_GO_SOURCE_MISSING

2026-10-07 JST。historical baselineをsource-backed echo_imag_3pointへ修正し、M00/M10の保存絶対3時刻と元numerical conventionを固定した。M00 primary prediction/B0は保存値のまま。

指定whole-pickle SHAに一致するN2/CO原本は探索範囲内で回収できなかった。旧H02 worktreeの同名2候補はSHA不一致でdecode前に棄却。canonical array identity、production backend再現、M00再現許容差、echo数値boundは未完了。保存scalar算術とsynthetic試験のPASSはproduction再現の証拠ではない。source missingはscience failureではない。

production science action=0。FS-C1 runnerは未完成・science未開始。Hamiltonian/CISD/group再生成は禁止を維持する。旧formal/Phase0/H4/FS-C0 artifactsは変更していない。

読む順序:

1. [GO_NO_GO_FOR_FS_C1.json](GO_NO_GO_FOR_FS_C1.json)、[source_recovery_audit.json](source_recovery_audit.json)、[canonical_source_identity.json](canonical_source_identity.json)
2. [research_amendment.md](research_amendment.md)、[fs_c1_protocol_v2.md](fs_c1_protocol_v2.md)、[baseline_contract.json](baseline_contract.json)
3. [backend_reproduction_preflight.json](backend_reproduction_preflight.json)、[echo_numerical_contract.json](echo_numerical_contract.json)、[backend_contract.md](backend_contract.md)
4. [cost_contract.json](cost_contract.json)、[cold_replay_contract.md](cold_replay_contract.md)、[recovery_contract.md](recovery_contract.md)
5. [verification.json](verification.json)、[tests.log](tests.log)、[source_manifest.json](source_manifest.json)、[publication_manifest.json](publication_manifest.json)

GPT/userへ返す判断: 原本探索の追加手段があるか、または将来別source/identity契約への再設計を承認するか。後者の設計・計算は今回実施しない。追加science authorizationは別途必要。

再検証は新temporary pathで PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q -p no:cacheprovider artifacts/pf_first_study_fs_c0_20261007/test_fs_c0.py artifacts/pf_first_study_fs_c05_execution_closure_20261007/test_fs_c05.py。hash-pinned native definitionsをsyntheticだけに使う。

Repositoryは https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae、branch pf-first-study-fs-c05-execution-closure-20261007。固定handoff commitとremote取得receiptは最終報告で示す。publication_manifestは自己除外。凍結文書の公開前状態を後から書き換えない。
