# リポジトリ案内

この文書は、ファイルを一括移動せずに現在の役割と読み順を示す。古い実行指示やrunnerの存在だけから研究状況を推測せず、最初に[`current_research_status.md`](current_research_status.md)を確認する。

## まず読むファイル

1. [`docs/current_research_status.md`](current_research_status.md)：現在の目的、確認済み結果、適用範囲、停止判断。
2. [`docs/pf_data_use_ledger.md`](pf_data_use_ledger.md)：探索・開発・過去のホールドアウトの区別。
3. [`review_response/finite_time_cost_strategy.md`](../review_response/finite_time_cost_strategy.md)：直接有限時間評価、二項モデル、計算方法の方針。
4. `current_research_status.md`からリンクされた`artifacts/*/report.md`：数値根拠。
5. [`README.md`](../README.md)：環境構築とパッケージ全体。

## 役割別マップ

| 役割 | 場所 | 内容 |
|---|---|---|
| 共通実装 | `src/trotterlib/` | PF係数・分解、Hamiltonian生成、時間発展、誤差・コスト解析 |
| 実験・監査 | `review_response/*.py`、`review_response/*.sh` | 数値検証、探索、再集計、CPU/GPUベンチマーク |
| 自動テスト | `review_tests/` | 共通実装と検証runnerの回帰テスト |
| 研究文書・プロトコル | `docs/`、`review_response/*.md` | 現状、データ履歴、固定規則、GPUサーバー指示 |
| 計算結果 | `artifacts/` | raw JSON/CSV、集計、図、報告書、manifest |
| 論文・発表資料 | `aqis2026/`、PDF、ノートブック、スライド草稿 | 原稿、参考資料、解析ノート |

## `review_response/`の接頭辞

- `run_`、`sweep_`、`smoke_`、`benchmark_`：数値計算・性能測定。
- `validate_`、`compare_`、`ablate_`：検証・比較・切り分け。
- `search_`、`refine_`、`rank_`、`screen_`：PF探索・選別。
- `analyze_`、`summarize_`、`audit_`：保存結果の再集計・監査。
- `gpu_*.md`：GPUサーバー側Codexへの実行指示。完了済み指示も残る。

## 成果物を読む際の注意

- `Status`、元commit、protocol hash、manifestを確認する。
- 指示書が存在しても実行済みとは限らない。
- `COMPLETE`だけでなく、監査JSONと必要ファイルの整合性を確認する。
- 未コミットのローカルpilotは、GitHubから監査可能な確定結果として扱わない。
- `e_direct`と重なり位相による代理量、局所格子最小と連続時間の大域最小を区別する。
- 巨大cacheやpickleはGitから除外される場合がある。再利用時は元サーバー成果物とhashを確認する。

## 整理方針

既存runner同士のimport、保存済み指示書、成果物のsource pathが現在の配置に依存しているため、ファイルを一括移動しない。新しい再利用可能な機能は`src/trotterlib/`、実験固有処理は`review_response/`、状態と方針は`docs/`へ置く。移動が必要な場合は、import、文書リンク、実行コマンド、テストを同じ変更で更新する。
