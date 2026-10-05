# Main-analysis freeze / result navigation

主方向Cと解析仕様は[final_direction_and_claim_scope.md](final_direction_and_claim_scope.md)および
[quantity_dictionary_and_analysis_spec.md](quantity_dictionary_and_analysis_spec.md)で固定した。
既存研究status文書・旧formal結果は変更せず、本段階の最新版はこの索引から参照する。

結果：[主解析report](../../../artifacts/budget_safety_mechanism_20261005/report.md)。
全scalar：[analysis.json](../../../artifacts/budget_safety_mechanism_20261005/analysis.json)。
原本対応：[source_registry.json](source_registry.json)（originとverified snapshotは別field）。

再実行用ではなく再現性の記録：

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=review_response \
python review_response/budget_safety_mechanism_analysis.py \
  --design-freeze-commit d77b4644600fb8ef2af05108b766efd95e5704da
```

主解析は一回完了済みで、既存outputへは上書き禁止。数値結果を変更しない再監査は
`python review_response/verify_budget_safety_mechanism_outputs.py` で可能。
最初のdesign manifestはfreeze時の仕様・原本registry・test/codeを対象とし、このREADMEはcompletion索引として後から追加。
結果のrunner manifest、completion manifest、publication provenanceを分け、自己参照commitを埋め込まない。
新しい科学計算もpushも自動的に開始しない。停止点は論文着地点・claimのレビュー。
