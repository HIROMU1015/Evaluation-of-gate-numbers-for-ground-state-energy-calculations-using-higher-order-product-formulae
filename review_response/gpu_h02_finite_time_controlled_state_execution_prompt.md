# GPUサーバー側Codexへの実行依頼：H02 有限時間制御状態診断

H01の近似状態校正に続き、状態エネルギー誤差、分散、Hamiltonian残差、厳密基底状態重なりというスカラー量だけで、有限時間PFコスト校正に使える状態を判定できるか診断してください。

今回の範囲は **H02のみ** です。H05、新PF係数探索、新分子、別基底、別目標精度、追加の直接PF固有値計算へ進まないでください。

## 固定した版

- H01結果ブランチ：`gpu-h01-approximate-state-calibration-results`
- H01結果commit：`568f00249abb5b89ae3e6bb39cb4af87ed8581bd`
- H02実装・固定仕様commit：`a228b5f357c73b8e4978fc19253b2885c40df6b6`
- H02固定仕様：`review_response/h02_finite_time_controlled_state_protocol.json`
- H02固定仕様SHA-256：`46345041b0da6449ff33d87f242ba8dade6ebf330eb1994426b063674bbfe4d9`
- H02説明：`review_response/h02_finite_time_controlled_state_diagnosis.md`
- H02 runner：`review_response/run_h02_finite_time_controlled_state_diagnosis.py`

新しい結果ブランチは`a228b5f357c73b8e4978fc19253b2885c40df6b6`から作成してください。推奨ブランチ名は

`gpu-h02-finite-time-controlled-state-results`

です。同名ブランチが既にあれば上書きせず、日付または連番を付けてください。既存の作業ツリーをreset、clean、stashせず、独立worktreeを使用します。mainへは統合しません。

## 最重要条件：H01サーバーキャッシュを直接再利用する

この診断はH01と同一のHamiltonian、厳密基底状態、CISD状態、RHF determinantを必要とします。Gitに保存された座標からローカルで再構築したpilotでは、保存済みH01 exact-ground echoとの差が最大約`1.87e-7` Hartreeとなり、要求値`1e-9` Hartreeを満たしませんでした。このpilotはcommit`a228b5f`に`failed_numerical_validation`として保存されており、科学的結果として解釈してはいけません。

GPUサーバー上でH01を実行した元成果物を探してください。想定パスは次です。

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-full-electron-nh3/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`

環境上の絶対パスが異なる場合は、成果物名

`server_h01_approximate_state_calibration_20260922_011228_e0692a8`

で検索して構いません。ただし、別の計算から作ったキャッシュや再構築値へ置き換えないでください。

計算開始前に、元成果物内に少なくとも次が存在することを確認してください。

- `aggregate/summary.json`
- `cache/N2_active_eq_sto3g.pkl`
- `cache/N2_active_stretch150_sto3g.pkl`
- `cache/CO_active_eq_sto3g.pkl`
- `cache/CO_active_stretch150_sto3g.pkl`

4個のpickleをH01の`_load_system`で読み、内部hash、protocol hash、条件名の検査を通してください。ファイルがない、読み込めない、hashが不一致、またはH01結果と対応しない場合は、Hamiltonianを再生成して本計算を続けず停止し、どこまで確認したかを報告してください。

## 実行前検査

1. `git remote -v`で`origin`が`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`であることを確認する。
2. `git fetch origin --prune`後、上記2 commitを取得できることを確認する。
3. H02固定JSONのSHA-256が上記値と一致することを確認する。
4. H01元成果物の`aggregate/summary.json`のhashがH02 manifestに記録されることを確認する。
5. 既存テストとH02 unit testを先に実行する。

固定JSON、説明、runnerが競合する場合は、固定JSONを優先して勝手に条件を変更せず、長時間計算前に報告してください。

## 診断対象と固定範囲

対象HamiltonianはH01の主4条件だけです。

- `N2_active_eq_sto3g`
- `N2_active_stretch150_sto3g`
- `CO_active_eq_sto3g`
- `CO_active_stretch150_sto3g`

PFは`current_m3`と`yoshida4`、誤差モデルは5点の`t^4+t^6`だけです。PF係数、分割、群順序、Jordan--Wigner写像、符号規約、コスト式、目標精度を変更しません。

各条件でCISDおよびRHF状態の厳密基底状態に直交する成分を用い、事前固定した4エネルギー誤差と4位相から制御状態を作ります。同一位相quartetで状態エネルギー誤差、分散、残差ノルム、厳密基底状態重なりが同一であることを確認し、echo係数、予測最適時刻、モデルコスト、PF選択の位相依存を比較してください。

新しい直接PF固有値点は計算しません。H01の基底接続枝による直接格子最小コストを評価用truthとして再利用します。したがって、本診断を新しい分子ホールドアウトやend-to-endの安価な校正と表現しないでください。

## 実行方法

新しい、上書きされない出力先を作ってください。例：

`artifacts/server_h02_finite_time_controlled_state_<YYYYMMDD>_<git-short>/`

元H01成果物の絶対パスを明示して、次の形でrunnerを実行します。

```bash
python review_response/run_h02_finite_time_controlled_state_diagnosis.py \
  --project-root "$PWD" \
  --h01-server-artifact /absolute/path/to/server_h01_approximate_state_calibration_20260922_011228_e0692a8 \
  --output artifacts/server_h02_finite_time_controlled_state_<YYYYMMDD>_<git-short>
```

H01の実測ではこのstate-action規模はCPUがGPUより速かったため、runner既定のCPU complex128を優先して構いません。GPU使用自体は目的ではありません。独立条件を並列化する場合も、同じcacheを壊さずCPUメモリに余裕がある範囲にしてください。

## 必須の数値ゲート

制御状態の結論を読む前に、4条件×2 PFの保存済みH01 exact-ground echoを再計算し、全5点について最大絶対差`1e-9` Hartree以下を必須とします。

- 8/8組すべて合格した場合だけ`complete_with_findings`と`COMPLETE`を許す。
- 1組でも不合格なら`failed_numerical_validation`とし、`COMPLETE`を作らず、見かけ上の位相依存を科学的結論に使わない。
- 閾値を緩めない。
- 不合格を解消するためにPF係数、状態、軌道、fit点、モデル次数を変更しない。

さらに次を検査してください。

- protocol hash一致。
- 各位相quartetが4状態を含む。
- quartet内の4スカラー量の最大幅が絶対`1e-10`以下。
- 新規direct truth点が0である。
- source cacheを使用したこと、bytewise Hamiltonian hash、metadata差をauditへ保存する。

## 成果物と解釈

runnerが出力する少なくとも次を保存してください。

- `controlled_states.csv`
- `proxy_models.csv`
- `selection_results.csv`
- `phase_group_summary.csv`
- `correlations.csv`
- `audit.json`
- `manifest.json`
- `report.md`

元H01のpickleや巨大な作業cacheはcommitしません。manifestには元H01成果物の絶対パス、H01 commit、summary hash、H02 protocol hashを記録します。

報告書では次を分けて結論してください。

1. H01 exact-ground echoを完全に再現できたか。
2. 同じスカラー量を持つ位相quartetで、PF選択が変わった組数。
3. PF選択が変わらなくても、予測最適時刻またはモデルコストが1%以上変わった組数。
4. H01直接コストに対する最大PF選択損失。
5. スカラー量だけで有限時間校正の適格性を判定できるという仮説が反証されたか。
6. これはoracle機構診断であり、安価な運用規則はまだ得られていないという限界。

相関係数だけで十分性を主張せず、固定した構成的反例基準を主判定にしてください。反例が得られなかった場合も「十分である」とは断定せず、今回の制御方向と範囲で反証できなかったと記載します。

## テスト、commit、push、停止

1. H02 testと全`review_tests`を実行する。
2. raw/CSV/audit/manifest間の件数とhashを照合する。
3. 全数値ゲート合格時だけ`COMPLETE`の存在を確認する。
4. コード変更が必要だった場合は最小限にし、理由と差分をreportへ記録する。
5. 軽量な結果、report、テストを結果ブランチへcommitする。
6. `origin`の新規結果ブランチへpushする。force-pushしない。

最終報告では、結果ブランチ、commit、成果物パス、テスト件数、実行時間・最大メモリ、exact echo再現の8組の最大差、構成的反例の件数、PF選択変化、最大選択損失、未解決事項を示してください。その後停止し、H05、新PF探索、新分子へ自動的に進まないでください。
