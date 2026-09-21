# GPUサーバー側Codexへの実行依頼：H01 近似状態校正

GPUサーバーにある既存cloneを使い、現在の作業内容を壊さない独立worktreeと新しい結果ブランチでH01検証を実行してください。cloneを作り直さず、既存ツリーをreset、clean、stash、checkoutで変更しないでください。

## 固定した版

- リポジトリ：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- H01計画commit：`1ecfed25f0ce1849e80ed623e4804091cfc9a4b0`
- 監査済みホールドアウトcommit：`3fb79743aa6ef2915d3b041ac26737a42c53610b`
- 元の数値結果commit：`33a761d44a24022ad61192c41a196dd4cb3afbca`

H01仕様の正本は計画commitにある次の2ファイルです。

- `review_response/gpu_h01_approximate_state_calibration_prompt.md`
- `review_response/h01_approximate_state_calibration_protocol.json`

期待するSHA-256は次です。

- 指示書：`6de65ac35f3e525ac56feca3ce8ad1c8454cb2703ed710104374a16884db2ce0`
- JSON：`e0e2649db1f8d109779ab1db26822f45c92c2a660569caa643f5f363e3ce27a6`

この実行依頼の要約と正本が競合する場合は固定JSONを優先し、独自解釈で進めず計算前に報告してください。指示書を省略せず最後まで読み、全条件に従ってください。

## 作業開始

1. `git remote -v`でoriginが上記HIROMU1015リポジトリであることを確認する。
2. `git status --short --branch`で既存cloneの状態を記録する。
3. `git fetch origin --prune`後、上記3 commitを取得できることを確認する。
4. H01計画commit `1ecfed2`から独立worktreeと新しい結果ブランチを作る。

結果ブランチ名は原則として

`gpu-h01-approximate-state-calibration-results`

とします。同名ブランチが存在する場合は上書きせず日付または連番を付け、manifestとreportに記録してください。

## 再利用元の確認

元成果物

`artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`

の`manifest.json`、`post_run_audit.json`、`aggregate/summary.json`、raw/fine JSONを先に確認してください。数値rawは変更しません。

GPUサーバーに未追跡のHamiltonian pickleや群スペクトルcacheが残っている場合、次が一致するときだけ再利用できます。

- 条件名だけでなく、座標、基底、電子数、軌道数、凍結内殻、Hamiltonian hash。
- 群内容と順序、sector、数値精度。
- cacheの必須フィールドと生成commit。

一致を確認できなければ再構築してください。cacheパスそのものを同一性の根拠にしないでください。

## 今回の範囲

- 主条件：N2/COの凍結内殻CAS(10e,8o)、平衡・1.5倍伸長の4条件。
- 補助条件：全電子HF/STO-3G、平衡・1.5倍伸長。
- PF：`current_m3`、Yoshida 4次。
- 状態：厳密基底状態、RHF determinant、CISD。
- 主代理量：同一状態に対する`<phi|exp(-iHt) U_PF(t)|phi>`の連続unwrap位相を時刻で割った符号付きecho代理量。
- 主モデル：5点の$t^4+t^6$。
- 診断：3点fit、echo虚部。
- truth：元の直接PF固有値結果を優先再利用し、固定検証に必要な未計算絶対時刻だけ追加する。

PF係数、分子、基底、モデル次数、点、閾値、1%余裕を結果に合わせて変更しないでください。これはoracle由来の$t_ana$を使って状態置換だけを調べる開発診断であり、end-to-endの安価な実用校正とは呼びません。

## 実装時の重要事項

- CISDをCASCI/FCIで代用しない。
- PySCF CISD determinant順序から既存JW population basisへの変換をテストする。
- 近似状態の生成・fit・選択へ厳密状態を入力しない。厳密状態は評価と直接truthに限定する。
- 単なる$E_\phi$回転ではなく、正本で定義したexact-reference echoを主代理量にする。
- proxy値を`e_direct`または直接固有値シフトと呼ばない。
- 新しい直接truthでは、前時刻重なりを実際の枝選択に使い、最大厳密基底重なり規則との一致も監査する。
- 元実装の絶対パス、statusだけのskip判定、不完全なcache keyを引き継がない。
- CPUのみとGPU利用経路を代表条件で実測してから本バッチ方式を決める。

長時間処理は再開可能なtmuxで実行してください。条件・PF・状態・絶対時刻単位で原子的に途中保存し、必須フィールドとhashを検査してからskipします。

## 成果物、検証、停止

正本の指定どおり、新しい

`artifacts/server_h01_approximate_state_calibration_<YYYYMMDD>_<git-short>/`

へmanifest、状態raw、echo raw、直接truth再利用表、追加直接点、枝監査、モデル集計、予算結果、timing/memory、テストログ、軽量図、`report.md`を保存してください。

新規テストと全`review_tests`を実行し、source/protocol hash、rawと集計の一致を検査してください。完了条件を満たす前に`COMPLETE`を作らないでください。

コード、テスト、固定仕様、必要なrawと集計、reportを新しい結果ブランチへcommitし、HIROMU1015のoriginへpushしてください。mainへmergeせず、既存ブランチをforce-pushしません。

最終報告では、ブランチ名、commit、成果物パス、テスト結果、実行時間・最大CPU/GPUメモリ、厳密状態echo sanity、CISD/RHFの主4条件、HF補助条件、PF選択、未解決事項を示してください。その後停止し、H02/H05、F領域、新PF探索、新規分子へ自動的に進まないでください。
