# 人間レビューで決めること・停止点

本bundleは資料統合完了であり、最終研究方針の承認ではない。`evidence_class=governance_scope` の提案と凍結済み科学結果を分けて判断する。

## 最終承認が必要な4点

1. **主線Cを正式採用するか。** 第二研究を「追加calibration informationのsafe resource decision value / observed regimes」と定義する。Positive selective spectralは必須にしない。
2. **現B2/H1 gateを主方式に採用しない方針でよいか。** Cheap-firstはfixed frontier baseline、spectralはconditional comparator。再設計・route停止のどちらも今回自動実施しない。
3. **RQと論文着地点をどこまで限定するか。** Known development / fixed current_m3 / continuous rotation-cost proxy / observed-case taxonomyへ限定し、cost未評価とcertificate不在を含める。
4. **レビュー後の文書更新と後続検証が必要か。** 最終RQ・戦略文書・`docs/current_research_status.md`を承認後に更新する。HCl/LiF、gate fitting、q=1探索、cost計測を行うなら、それぞれ問い・上限・success/no-goを別承認する。

## まだ決めない数値条件

Minimum practical effect size、classical-cost ceiling、quantum-budget noninferiority marginは `unresolved_requires_review`。HF eqのtruthに合わせてgamma/thresholdを新規固定しない。既存gamma frontierを増やさない。

## レビュアーに渡す範囲

本[入口](README.md)、[統合matrix](evidence_matrix.csv)、[方式の位置付け](method_positioning.md)、[RQ](research_question_review.md)、[着地点](publication_landing_options.md)、[decision](decision.json)を中心に読む。必要なraw result・protocol・旧bundleは[source registry](source_registry.json)のtracked pathを辿る。

外部共有する場合、G2を祖先として含む本integration branchを、別途明示されたpush指示で `HIROMU1015/*` originへnon-force pushすればよい。Runtimeは不要で含めない。Local commitはGitHub公開を意味せず、今回remote refは照会しない。`push_performed=false` はこの作成時点の記録で、後の公開状態は別確認する。

## Stop

`second_study_v2_g2_review_integration_complete_review_required`

新しい科学計算、real replay/scorer再実行、gate変更、最終方針の確定、current status更新、push、PR、main mergeは行わない。レビューの応答を受けるまでここで停止する。
