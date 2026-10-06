# Native H-chain decomposition 集計の訂正

2026-10-06。ユーザー指摘のdocumentation bugを、固定commitの原CSVから確認し、scalar-only builderの判定と集計を訂正した。研究方針・RQ・中心claimの改訂ではない。

## Authorityと訂正内容

- 原本は [m1_reference_error_decomposition.csv](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/bfe715fc1c04325535a3c4d63ea4584e691dc322/artifacts/budget_safety_mechanism_20261005/m1_reference_error_decomposition.csv)。origin/result commitは `a4c98df39f6e7ecdb1d588b54b35f3e4fffa1dc9`、verified snapshotは `bfe715fc1c04325535a3c4d63ea4584e691dc322`。既存[source registry](../../../artifacts/study2_evidence_integration_20261006/source_registry.json)のblob・SHA-256を維持する。
- Native H-chainの18点はすべて `same_H_origin_physical_lift_verified_saved_diagnostic`。元[evidence map](evidence_map.md)の18点verifiedという記述と一致する。
- Builderは `startswith("closed")` だけを数えていたため、このstatusを漏らした。新判定は確認済みstatusを明示的に認め、indeterminate以外の未知statusでは停止する。status名を変更して原CSVを書き換える方法は使っていない。
- [訂正版JSON](../../../artifacts/study2_evidence_integration_20261006_correction/evidence_scalars.json)の変更は `/native_main_analysis/2/decomposition_closed` の **0 → 18** だけ。HF/HClのclosedは0、indeterminateは各6のまま。Prospective39点のindeterminate、G15点とR36診断行のclosed、すべてのbudget/safe/width/abstention/分母は不変。

旧[集計JSON](../../../artifacts/study2_evidence_integration_20261006/evidence_scalars.json)と旧packageは履歴として保持する。旧0は科学的な未確認判定ではなく、集計バグである。以降の資料では訂正版を使う。旧publication manifestは起点commit `0a18168ae56852d7c754c28d05d5ce21bbce5b06` の当時のblobを検証するもので、訂正後builder/READMEのhashへ書き換えない。

## 検証とprovenance

追加したregression testは修正前に `[0,0,0] != [0,0,18]` で失敗した。修正後のfocused testsは **18 passed、fail/skip 0**。元11 source blobのorigin/snapshot byte equalityを再照合し、registryは既存JSONと完全一致した。訂正前JSONとの全体比較により、上記1 field以外が変わっていないことも確認した。

記録は [verification.json](../../../artifacts/study2_evidence_integration_20261006_correction/verification.json)、今回の変更を含むmanifestは [publication_manifest.json](../../../artifacts/study2_evidence_integration_20261006_correction/publication_manifest.json)。新manifestは自分自身をhash対象から除外し、commitの自己参照を埋め込まない。原本source registryを複製・再freezeしない。

併せて入口のH2–H8総括リンクを修正した。旧リンクの `971dc7a9...` は総括が検証したscience snapshotだが、そのcommitに総括Markdown自体は存在しない。現在のリンクは総括のblobが存在する `a852c413...` に固定した。総括Markdownのoriginは `50cdc62d69a28bc5d4f4893f3c589e0bbd6d81db` で、science結果のoriginや検証snapshotとは別である。

[GPU server completeness audit](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6509d012380a9e02dc1043cc9d84e201bb158baf/artifacts/prospective_gpu_server_information_completeness_audit_20261006/README.md)への導線も追加した。この既存監査は13 worker / 39座標の情報完備性を確認した別evidenceであり、新科学結果・合算分母・net-cost計測とはしない。

本訂正で新規PF/H作用、ground/truth/gap、rank/geometry/time取得、fit、再scoring、gamma/width/gate調整はすべて0。科学runner・scorer・private runtime・matrix/vector・exact stateは読んでいない。Track G/Rの完了受理と停止境界は[approved_closure.md](approved_closure.md)のまま。
