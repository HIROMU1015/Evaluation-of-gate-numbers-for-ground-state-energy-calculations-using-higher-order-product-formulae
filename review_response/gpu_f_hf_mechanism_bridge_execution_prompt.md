# GPUサーバー側Codexへの実行依頼：F01/F02/F05 HF成功・破綻bridge

既存のH01 server cacheを直接再利用し、Yoshida 4次の二項モデルが通る
`HF_full_eq_sto3g`と、同じ全電子HF/STO-3Gで破綻する
`HF_full_stretch150_sto3g`を、F01/F02/F05の同一機構指標で比較してください。

今回の範囲はこのbridgeだけです。新PF係数探索、practical calibration、D03、M01、
追加分子、追加基底、別目標精度、新しい直接PF truth点へ進まないでください。

## 固定した版

- 統合・計画ブランチ：`prevalidation-f-mechanism-bridge-20260922`
- 固定計画commit：`aa912b4`
- H01結果commit：`568f00249abb5b89ae3e6bb39cb4af87ed8581bd`
- 未使用分子holdout結果commit：`33a761d44a24022ad61192c41a196dd4cb3afbca`
- 小系F/H/D機構結果commit：`6d13384`
- 固定JSON：`review_response/f_hf_mechanism_bridge_protocol.json`
- 固定JSON SHA-256：`2b239b180c5fffe3c79e492220b344bfdec15e9a9f4d37259b9b815b52de26f4`
- preflight：`docs/f_hf_mechanism_bridge_preflight_20260922.md`

新しい結果ブランチは`aa912b4`から作成してください。推奨名は
`gpu-f-hf-mechanism-bridge-results`です。同名が存在すれば上書きせず日付または連番を
付けます。既存cloneをreset、clean、stashせず、独立worktreeを使います。mainへは
統合しません。

固定JSONと本文が競合する場合はJSONを優先し、条件を変更せず長時間計算前に報告して
ください。

## 最重要条件：H01の元pickleを使う

想定するH01元成果物は次です。

`/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-full-electron-nh3/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`

絶対パスが違う場合は成果物名で検索できます。少なくとも次を確認してください。

- `cache/HF_full_eq_sto3g.pkl`
- `cache/HF_full_stretch150_sto3g.pkl`
- 対応する2個の`.metadata.json`
- `aggregate/summary.json`
- H01の`COMPLETE`

`run_h01_approximate_state_calibration.py:_load_system`でpickleを読み、内部protocol hashと
sparse Hamiltonian hashを検査します。さらにcommit済みmetadataと照合し、次のhashを
必須とします。

- equilibrium：`cd074e4870223646ff51e98a72a679b33019cd96bb013de7536c0ceb3e7456c8`
- stretch150：`c68722b3f9f98488e765afb49fa2d1153e41b2a8e84b6df21841400650cec499`

ローカルで再生成したpilotは群数49・制限次元20まで一致しましたが、Hamiltonian hashが
一致しませんでした。pickleがない、読めない、hashが違う場合は再生成値で本計算を続けず、
`failed_source_identity`として停止してください。

## 主比較と既存truth

主比較はYoshida 4次の`two_term_5point`について次の2条件だけです。

1. HF full-electron equilibrium：既存判定は合格。
2. HF full-electron stretch150：既存判定は不合格。

`current_m3`は診断対照です。N2/COのactive-space 4条件は、既存の成功曲線・H01状態診断
との文脈比較だけに使います。3136次元のN2/COに密D8演算子を構築しません。

直接シフト、fit、局所格子最小、枝情報は次のcommit済み成果物から読みます。

- `artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`
- `artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`

新しい直接PF固有値点は0件でなければなりません。

## runner実装

新しいrunnerとunit testを追加してください。固定JSONを直接読み、少なくとも次を行います。

### 1. H01 component spectrumから群Hamiltonianを復元

各`ComponentSpectrum`の各batchについて、1次元blockは固有値を対角要素へ戻し、それ以外は
`V diag(lambda) V^dagger`を元indexへ配置します。全群和がcache内Hamiltonianと固定閾値内で
一致することを検査します。群順序を変更しません。

### 2. F01：D4/D6/D8

保存済みPF係数と`iter_s2_sequence_steps`から実際の順序を作り、ordered productの形式級数を
有効Hamiltonian次数8まで計算します。同じアルゴリズムを`complex128`と`clongdouble`で実行し、
固定JSONの精度ゲートを適用してください。

`H_eff = H + t^4 D4 + t^6 D6 + t^8 D8 + ...`について、少なくとも次を保存します。

- 各DのFrobenius norm、spectral norm、Hermiticity残差。
- H固有基底での対角・非対角norm。
- `<0|Dk|0>`、`||Q Dk|0>||`、物理gap。
- equilibriumからstretchへの比と、Yoshida4からcurrent_m3への比。
- H0一致、禁止次数、倍精度差。

有限時刻matrix logによる独立回収も、JSONの3固定窓と`t^4,t^6,t^8,t^10,t^12`で行います。
これは形式級数の独立確認であり、都合のよい窓だけを主結果に選ばないでください。D8が窓依存なら
不安定と報告し、形式級数結果を書き換えません。

### 3. F02：a8の分解

各条件・PFで

`a8_diag=<0|D8|0>`

と

`a8_mix=sum_n!=0 |<n|D4|0>|^2/(E0-En)`

を別々に計算し、和を形式摂動再帰のa8と照合します。励起状態別寄与、mixing fraction、
cancellation ratio、符号を保存します。既存直接5点の三項fitも診断として再計算しますが、係数が
窓に敏感なら演算子分解の反証には使いません。

### 4. F05：物理gapとPF phase gap

JSONの固定相対時刻で、物理gap、円周上の対象PF枝と最近接枝のphase gap、phase gap/time、
ground overlap、前時刻overlap、unwrap整数、固有対残差を保存します。commit済み直接点と重なる
時刻では、符号付きシフトを`1e-9` Hartree以内で再現することを必須とします。

位相近接だけ、物理gapだけ、または多項式次数不足だけで原因を断定せず、JSONの事前固定flagを
並列に評価してください。

## 数値ゲートと解釈

固定JSONの全`numerical_gates`をそのまま使います。緩めません。

- source identityまたは必須数値ゲート不合格：`failed_numerical_validation`、`COMPLETE`なし。
- 合格：`complete_with_findings`を許可。
- mechanism flagは因果の証明ではなく、同一HFペアで観測された整合的な説明候補として記載。
- N2/COの機構をHF結果から直接断定しない。

## 成果物

上書きされない

`artifacts/server_f_hf_mechanism_bridge_<YYYYMMDD>_<git-short>/`

へ少なくとも次を保存してください。

- `operator_decomposition.csv`
- `a8_state_mixing.csv`
- `direct_fit_diagnostics.csv`
- `phase_gap_points.csv`
- `condition_comparison.csv`
- `external_success_context.csv`
- `audit.json`
- `manifest.json`
- 軽量な比較図
- `report.md`
- 全ゲート合格時だけ`COMPLETE`

manifestには元H01成果物の絶対パス、2 pickleのSHA-256、内部Hamiltonian hash、H01 summary hash、
固定protocol hash、新規direct truth点数0を記録します。pickle自体はcommitしません。

報告書の主結論は次の順にしてください。

1. 同一HFでequilibrium成功からstretch破綻へ変わる際、D4対角、D4結合、D8直接項、D4混合項の
   どれが最も変わったか。
2. a8の相殺または状態混合が二項モデル破綻と整合するか。
3. 物理gap低下とPF phase gap圧縮のどちらが説明力を持つか。
4. current_m3対照は同じ傾向か。
5. N2/CO成功例へ一般化できる範囲と、できない範囲。

## テスト、commit、push、停止

人工小行列で群復元、dtype一致、a8分解、phase gap、source identity失敗をunit test化します。関連testと
全`review_tests`を実行し、基点由来の既知収集問題があれば新規test結果と分けて報告してください。
raw/CSV/audit/manifestの件数とhashを照合します。

コード、test、軽量結果、reportを結果ブランチへcommitし、`HIROMU1015/*`のoriginへ新規branchとして
pushしてください。force-push、mainへのmerge、既存成果物の削除は行いません。

最終報告には結果branch、commit、成果物パス、test件数、実行時間・peak memory、全数値ゲート、
主機構結論、未解決事項を示してください。その後停止し、practical calibration、D03、M01へ自動的に
進まないでください。
