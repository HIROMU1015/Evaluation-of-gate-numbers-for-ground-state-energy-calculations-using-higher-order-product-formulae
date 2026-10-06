# 第1研究 response-corrected calibration — Phase 0.5

**設計freeze完了。science未実行。H4 / current_m3 / CISDのみ。**

Phase 0の`GO_response_pilot`を、algorithm・equal-information Ritz comparator・fit・metric・truth境界・action会計へ具体化した。元formalの79/128・49/128、S4 `no_benefit`、Phase 0のoracle結果は変更していない。Phase 0のoracle state-removalは実際の補正法の成果ではない。

ユーザー承認で2点を解消した。full residual `min||a-LZc||`を採用し、投影`L_m`は診断用とする。「一般にAとHが可換なら補正ゼロ」は成立しないため、ゼロ補正テストを恒等演算子／exact eigenstateに限定し、可換反例を保存する。[承認記録](user_amendments.json)。

`science_ready=true`は**仕様が閉じ、別途承認するH4 pilotを設計できる**という意味。実行許可はfalse。production実行adapterは未接続で、`--phase-a/--phase-b`はarchiveを開く前に停止する。要求されたimplementation skeletonとsynthetic-only kernelを提供した。将来adapterをこの仕様に沿って実装・synthetic acceptance確認後、承認済み範囲だけを実行する。

読む順序：

1. [Normative protocol JSON](response_pilot_protocol.json)と[説明版](response_pilot_protocol.md)。
2. [Algorithm design](algorithm_design.md)：数式、target invariance、可換反例、限界。
3. [Cost accounting](cost_accounting.md)と[予定回数](expected_action_counts.json)。
4. [Novelty review](novelty_review.md)：一次文献との重なりと限定された候補。
5. [GO/no-go](GO_NO_GO_FOR_SCIENCE.json)、[verification](verification.json)、[tests](tests.log)。
6. [Source manifest](source_manifest.json)、[Phase A input identity](source_identity_phase_a.json)、[publication manifest](publication_manifest.json)、[handoff](handoff.md)。

`phase05_math.py`はdim≤16のsynthetic reference kernels、`phase05_phase_a.py`はtruth fieldのない型付きbuilder、`phase05_phase_b.py`はcommit/blob/hash照合後のimmutable採点、`phase05_runner.py`はproduction停止境界。synthetic builderは試験用qualityをresolvedに設定するのでproductionへそのまま転用しない。実用noise/cold replay adapterの契約はprotocolに固定した。

再現（repository root、numpy 1.26.4 / scipy 1.14.1 / pytest 8.3.3）：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider artifacts/pf_first_study_response_pilot_phase05_20261006/test_phase05.py
```

22件のsynthetic testsに合格した。source/code/protocol監査は次で再現できる（read-only、H4 decodeなし）：

```bash
PYTHONDONTWRITEBYTECODE=1 python artifacts/pf_first_study_response_pilot_phase05_20261006/verify_phase05_design.py
```

production行列・ベクトルは今回decodeしていない。既存公開bundleのbyte hashとGit blobを照合し、内部配列hashは凍結Phase Bから引き継いだ。新規binary/production state/vectorは追加公開しない。既存development truthの値を設計・parameter選択には使用していない。11 absolute /22 signed timesは既知のdevelopment座標で、独立holdout／prospectiveとは呼ばない。
