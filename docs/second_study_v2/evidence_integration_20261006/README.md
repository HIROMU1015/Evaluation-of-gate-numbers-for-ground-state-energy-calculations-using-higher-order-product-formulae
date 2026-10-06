# 第2研究v2：H-chain完了後のevidence map

Track R・Track Gはユーザー/GPTのレビューを受けて完了扱いとし、H-chainの新規科学計算はいったん終了する。Direction Cと承認済みRQは変更しない。この資料は、公開済みscalar結果を統合して論文上の位置付けをレビューする入口であり、追加計算の実行許可ではない。

## 読む順序

1. [承認済み停止境界](approved_closure.md)：完了判定、公開snapshot、再開に必要な別承認。
2. [Evidence map](evidence_map.md)：native contract別の結果、重複、claimの範囲と不足。
3. [集計scalar](../../../artifacts/study2_evidence_integration_20261006/evidence_scalars.json) と [source registry](../../../artifacts/study2_evidence_integration_20261006/source_registry.json)：原本の40文字commit、blob、SHA-256、固定GitHubリンク。
4. [既存の承認済みRQ・claim scope](../result_synthesis_20261005/approved_scope_and_rq.md)：本資料によって改稿・再freezeしていない。

原本の読む順序は、[主解析][main] → [H-chain H2–H8総括][series] → [Track G][g] → [Track R][r] → [prospective final][p]。各リンクはcommit固定で、最後のprospective branchだけを読むことでTrack G/Rも同じ履歴に入っているとは仮定しない。

## 今回行った作業

既存11個のJSON/CSV blobを読み、保存済みsafe/abstain等の件数と分母を照合した。原本のprediction、budget、width、truth、scorer、sourceは変更せず、再scoring・科学runnerのimportも行っていない。新規PF/H action、ground、truth、gap、rank/geometry/time取得はすべて0。既存試験のtruth scalarを読む事後整理であり、新たなtruth-free検証ではない。

新しい資料整理のstatusは `second_study_v2_evidence_map_integration_complete_review_required`。Track G/Rの元statusは作成時点のまま保存し、後日の完了受理を別文書に記録した。

## GPTへの確認事項

このevidence mapを、承認済みDirection Cの論文構成へどう配置するか確認してほしい。特に、H-chainのsmall-margin regime、general-moleculeでのfixed small-marginの失敗、M1のpoint/width/decision-valueの分離を、異なるcandidate contractと分母を保って提示できているかを確認する。中心claimの変更や追加科学計算の判断はGPT側に残す。

## 再現・監査

リポジトリ内の純scalar builderは `review_response/study2_evidence_map.py`。source registryに記録した4 source branchの履歴が必要で、現在のbranchだけをcloneして旧branchのobjectsがない場合は先にそれらをfetchする。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/home/abe/myproject/Evaluation_numGate_highorder/venv/bin/python -m pytest -q -rs \
  review_tests/test_study2_evidence_map.py -p no:cacheprovider
```

Builderは新規output directoryだけに出力する。公開済みpackageへ上書きせず、再監査も原本を変更しない。[検証記録](../../../artifacts/study2_evidence_integration_20261006/verification.json)、[公開source確認](../../../artifacts/study2_evidence_integration_20261006/source_publication_audit.json)、[自己除外manifest](../../../artifacts/study2_evidence_integration_20261006/publication_manifest.json)を併読する。manifestは自分自身をhash対象から除外し、handoff commitはmanifestへ自己参照で埋め込まない。

[main]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/bfe715fc1c04325535a3c4d63ea4584e691dc322/artifacts/budget_safety_mechanism_20261005/report.md
[series]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/971dc7a9b1b138fbbbb95fc684aa52af657e81b1/docs/second_study_v2/hchain_independent_validation_summary_20261005.md
[g]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1e03a659f3111623fa2b7afc3d8a87eeda1f4730/artifacts/hchain_h6_truth_continuation_20261006/REPORT.md
[r]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/0c40a3d7987e0961262bfd38bbb214a9e2946824/artifacts/hchain_m1_rank_convergence_20261006/README.md
[p]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a852c41331f2c8e0f7415c34e78c0110e4afd284/artifacts/prospective_truth_scoring_20261006/final/summary.md
