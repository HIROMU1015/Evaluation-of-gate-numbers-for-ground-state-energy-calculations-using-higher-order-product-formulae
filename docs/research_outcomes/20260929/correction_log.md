# Correction log

元bundle：`PF_research_outcomes_bundle_20260929.zip`
SHA-256：`b3a3d0054a17c428cfe0d8958c70892b36538c84fdf72061d6e4f1b36726cc85`

| 種別 | 対象 | 旧 | 新 | 根拠 |
|---|---|---|---|---|
| provenance metadata | source registry | 参照commitを単一fieldで記録 | `origin_result_commit`と`verified_snapshot_commit`、両blobを分離 | ユーザー承認済み追加監査要件 |
| governance classification | CL30・本体・短縮版 | `user-agreed scope / 将来判断`がscience claim表と同列 | `governance_scope`として分離 | CL30は実験結果ではなく権限境界 |
| manifest metadata | bundle manifest | 自己除外が暗黙 | `manifest_self_excluded: true` | 自己参照hashを避ける設計の明示 |
| handoff identity | instruction/registry/manifest | ZIP identityが文書外 | handoff ZIP SHA-256を固定 | 監査入力の同一性 |
| direct Git audit | S04ほか | connector由来blobまたはnull | Gitからorigin/snapshot blob、bytes、SHA-256を記録 | `source_manifest.json` |

科学数値、結果status、既存artifact、prediction、protocolは変更していない。
文章上の研究ストーリーも作り直していない。
