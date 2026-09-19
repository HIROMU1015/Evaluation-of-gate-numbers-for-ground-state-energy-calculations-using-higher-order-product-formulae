# リポジトリ案内と整理方針

この文書は、既存ファイルを移動せずに「どこに何があるか」を示す案内である。`review_response/` のスクリプトは相互に import し、実行中の検証や保存済み指示書も現在のパスを参照しているため、整理の第一段階ではパスを維持する。

## 現在の役割別マップ

| 役割 | 現在の場所 | 主な内容 |
|---|---|---|
| 共通実装 | `src/trotterlib/` | PF係数・分解、Hamiltonian生成、時間発展、保存則セクター計算、誤差・コスト解析。新しい再利用可能な機能はここに置く。 |
| 検証・探索コード | `review_response/*.py`、`review_response/*.sh`、ルートの `search_nonprocessed_4th_*.py` | 査読対応、PF係数探索、分子ホールドアウト、CPU/GPUベンチマークなどの実験用入口。 |
| 自動テスト | `review_tests/` | 共通実装と査読対応コードの回帰テスト。`tests/` は別用途の古い作業資料も含み、現在 `.gitignore` の対象である。 |
| 研究文書・実行指示 | `review_response/*.md` | 検証規則、研究方針、結果の説明、GPU側Codexへの指示。 |
| 計算結果 | `artifacts/` | JSON/CSV、図、レポート、ログ、キャッシュ。一次データと再生成可能な一時データが混在する。 |
| 論文・資料作成 | `aqis2026/`、`review_response/slide_outline.md`、`review_response/response_to_reviewers_draft.md`、ルートのPDF・ノートブック | AQIS原稿、スライド構成案、査読回答草稿、参照論文、解析ノートブック。 |
| 古い草案 | `code_draft/`、`tests/overleaf/` | 履歴確認用。新しい共通実装の置き場にはしない。 |

## 完了済み結果のアーカイブ

未追跡ファイル数を減らすため、2026-09-18に完了済みの次の6実験の条件別JSONを、各実験ディレクトリの `raw_results.zip` にまとめた。ZIP内には元のリポジトリ相対パスとSHA-256付きマニフェストを保存している。`report.md`、集計・解析JSON、入力構造、実行スクリプト、完了マーカーは展開したまま残した。

- `nonhchain_active_space_local_20260908`
- `nonhchain_active_space_geometry_local_20260908`
- `nonhchain_active_space_size_local_20260908`
- `nonhchain_basis_local_20260908`
- `h2o_m3_remainder_diagnosis_20260909`
- `m3_remainder_cross_molecule_20260909`

過去の未追跡ログ61件は `artifacts/_untracked_logs_before_20260918.zip` にまとめた。実行中の `existing_pf_nh3_holdout_comparison_20260918` と関連smoke出力は対象外である。集計JSONの `source` 欄には元の個別ファイルパスが残るため、その個別JSONを読む再解析の前には復元すること。

リポジトリのルートで、アーカイブの照合と元パスへの復元を行える。

```bash
python review_response/archive_completed_local_artifacts.py --verify artifacts/nonhchain_basis_local_20260908/raw_results.zip
python review_response/archive_completed_local_artifacts.py --restore artifacts/nonhchain_basis_local_20260908/raw_results.zip
```

復元は、既存ファイルの内容が異なる場合は上書きせずに停止する。その他の結果ディレクトリ、とくに後続スクリプトが個別JSONを直接参照するものは、現時点では展開したまま保持する。

## まず読むファイル

- 現在の研究目的・確定結果・進行中作業：[`docs/current_research_status.md`](current_research_status.md)
- 実装全体とセットアップ：[`README.md`](../README.md)
- 共通PF実装：[`src/trotterlib/product_formula.py`](../src/trotterlib/product_formula.py)、[`src/trotterlib/pf_decomposition.py`](../src/trotterlib/pf_decomposition.py)
- 有限時間コスト・予測可能性の研究経緯（履歴資料）：[`review_response/pf_cost_predictability_handoff.md`](../review_response/pf_cost_predictability_handoff.md)
- 短時間フィットの規則：[`review_response/m3_short_time_fit_protocol.md`](../review_response/m3_short_time_fit_protocol.md)
- 査読対応の従来の入口：[`review_response/README.md`](../review_response/README.md)
- スライドの内容構成：[`review_response/slide_outline.md`](../review_response/slide_outline.md)
- AQIS原稿：`aqis2026/`（ローカル資料。GitHubから読む場合は追跡・push済みかを別途確認する）

## `review_response/` 内の探し方

ファイル名の接頭辞はおおむね次の役割を表す。ただし完全な規約ではなく、既存ファイルの移動や改名を伴わない分類である。

- `run_`、`sweep_`、`smoke_`、`benchmark_`：数値計算・性能測定の入口。
- `validate_`、`compare_`、`ablate_`：検証、比較、切り分け実験。
- `search_`、`refine_`、`rank_`、`screen_`、`explore_`：PF係数の探索・選別。
- `analyze_`、`summarize_`：保存結果の再集計・解釈。
- `gpu_*.md`：GPUサーバー側Codexへの依頼文・実行指示。完了済みの指示書もあるため、ファイルの存在だけで未実施と判断しない。
- その他の `*.md`：プロトコル、方針、結果、論文・発表用の文章。

現在の二項モデルに関するコードの入口は `compare_existing_pf_low_order_models_local.py`（H-chain内の既存PF比較）と `compare_existing_pf_nh3_holdout_local.py`（NH3の分子比較）である。研究上の現状はコードや指示書の存在から推測せず、`docs/current_research_status.md` と、そこからリンクされた完了済み報告書を確認する。

## 将来の配置案（まだ移動していない）

```text
src/trotterlib/       再利用する計算実装
experiments/          検証・探索・ベンチマークの実行入口
review_tests/         自動回帰テスト（名称統一は別途判断）
docs/                 プロトコル、研究方針、結果の案内、GPU指示
presentations/        スライド構成・学会原稿・発表用素材
artifacts/            実験ごとの一次結果・要約・図
references/           参照論文などの外部資料
```

これは分類の目標であって、現在のファイルパスを表すものではない。特に `review_response/` は一括移動せず、依存関係と実行コマンドを検証しながら小単位で移す。

## 整理を進める際の順序

1. **案内を整備する（この段階）**：既存パスを維持し、READMEと本書から目的のコード・資料へ辿れるようにする。
2. **結果の保存規則を決める**：一次JSON、要約、図、巨大キャッシュ・ログを区別し、各実験ディレクトリに実行条件と元コミットを記録する。既存結果を一括改名しない。
3. **検証コードを段階的に移す**：実行中ジョブがなくなってから、依存関係を調べ、テーマ単位で `experiments/` などへ移す。移動と同じ変更で import、文書内パス、実行コマンド、テストを更新する。
4. **文書と発表資料を分ける**：研究メモ・プロトコルを `docs/`、GPU指示を `docs/prompts/`、スライドや原稿を `presentations/` などへ移すか判断する。外部のCodexに渡した既存パスは必要に応じて互換リンクまたは案内を残す。
5. **テストと除外規則を整理する**：`review_tests/`、`tests/`、`pyproject.toml` の `testpaths` と `.gitignore` の整合性を確認する。現在は `testpaths = ["tests"]` だが、Git管理のテストは主に `review_tests/` にある。

移動・削除・Git追跡対象の変更は、実行中ジョブと未コミット変更を確認したうえで、各段階を独立した変更として行う。特に `artifacts/` 内の計算結果とルートのPDFを、サイズや名前だけで不要と判定しない。
