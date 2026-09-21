# GPUサーバー側Codexへの依頼：H01 近似状態による有限時間PF校正

未使用分子固定ホールドアウトの結果を受け、次はPF係数を再探索せず、有限時間二項モデルの校正に厳密基底状態が本当に必要かを切り分けてください。N2/CO/HFは結果確認済みなので、今回は独立ホールドアウトではなく**近似状態置換の開発用診断**です。

GPU利用そのものは目的ではありません。RHF/CISD生成、Hamiltonian作用、PF作用、必要な直接固有値検証について、CPU・GPU・メモリを実測に応じて使い分けてください。

## 1. 固定した出発点

- リポジトリ：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- 監査済み基点commit：`3fb79743aa6ef2915d3b041ac26737a42c53610b`
- 元の数値結果commit：`33a761d44a24022ad61192c41a196dd4cb3afbca`
- 元の実装commit：`d288797a544c5e0ffac7bf1c46d7308de90fd9fb`
- 元の成果物：`artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`
- H01固定JSON：`review_response/h01_approximate_state_calibration_protocol.json`
- H01固定JSONの期待SHA-256：`e0e2649db1f8d109779ab1db26822f45c92c2a660569caa643f5f363e3ce27a6`
- データ使用履歴：`docs/pf_data_use_ledger.md`

この指示書と固定JSONが競合する場合は固定JSONを優先し、解釈で埋めず実行前に停止して報告してください。固定JSONを省略せず最後まで読み、hash一致をmanifestへ保存します。

既存cloneを使い、現在の作業ツリーをreset、clean、stash、checkoutで変更しないでください。`3fb7974`から独立worktreeと新しい結果ブランチを作ります。ブランチ名は原則として

`gpu-h01-approximate-state-calibration-results`

とし、同名が存在する場合は上書きせず日付または連番を付けてください。mainへは統合しません。

## 2. 問いと今回答えないこと

主質問は次です。

> `current_m3`またはYoshida 4次の二項有限時間モデルについて、厳密基底状態をRHFまたはCISD状態へ置き換えても、PFの実行可能性、QPEコスト、PF順位を保てるか。

今回は状態置換だけを切り分けます。元計算で得た各PF・Hamiltonianの`analytic_time`を代理校正点の尺度として再利用します。したがって、短時間係数や時刻尺度まで安価に決めるend-to-end法の検証ではありません。そこはH05以降です。

次へは進まないでください。

- PF係数探索、m=4探索、追加PF。
- 新しい分子、基底、active space、目標精度。
- F01/F02/F05、H02以降の機構診断。
- 有理関数、三項化、適応的な時刻選択。
- 結果を見た後の閾値、1%余裕、点数、代理量の変更。

## 3. 条件、PF、状態を固定する

### Hamiltonian

主開発集合は元成果物の次の4条件です。

- `N2_active_eq_sto3g`
- `N2_active_stretch150_sto3g`
- `CO_active_eq_sto3g`
- `CO_active_stretch150_sto3g`

全電子挙動の補助診断として次の2条件も同じ方法で計算しますが、主合否へ混ぜません。

- `HF_full_eq_sto3g`
- `HF_full_stretch150_sto3g`

座標、RHF軌道、凍結内殻、active space、群分け、群順序、Jordan--Wigner写像、定数除去、保存則セクター、目標誤差は元成果物から変更しません。

### PF

係数とS2列を変更せず、次の2つだけを主比較します。

- `current_m3`＋$t^4+t^6$：低コスト主候補。
- Yoshida 4次＋$t^4+t^6$：予測性基準。

`two_term_center`、`m5_best`、Yoshida 6次は今回追加しません。

### 状態

各条件で次の3状態を同じFock基底、軌道順序、セクターへ写像します。

1. 厳密基底状態：代理量自体の上限診断と評価だけに使用。
2. RHF Slater determinant：最小費用の近似状態。
3. CISD状態：同じRHF軌道を使い、N2/COでは元Hamiltonianと同じ2空間軌道を凍結して残り8軌道・10電子、HFでは凍結なし6軌道・10電子。

CISDをCASCI/FCIへ置き換えないでください。CISD振幅からpopulation-sectorベクトルへ変換するときは、PySCFのalpha/beta determinant順序、Jordan--Wignerのspin-orbital順序、既存basis整数の対応を明示し、単一・二重励起の小さい既知例でテストしてください。

各状態について次を保存します。

- 正規化。
- 同一Hamiltonianでのエネルギー期待値、厳密エネルギーとの差、分散、残差。
- 厳密基底状態との重なり確率。ただしこれは評価専用であり、RHF/CISD生成・代理fit・代理選択へ入力しない。
- population sector外および追加Z2 sector外のノルム。
- 状態生成時間と最大メモリ、CISD収束情報。

sector外ノルムが$10^{-8}$を超える場合は、勝手に射影して続行せず、determinant変換または対称性の不一致として停止してください。

## 4. 代理PF誤差の定義

近似状態$|\phi\rangle$に対し、元runnerと同じ符号規約で

$$
z_{\mathrm{echo}}(t)
=\langle\phi|e^{-iHt}U_{\mathrm{PF}}(t)|\phi\rangle
$$

を計算します。PFが厳密なら1になる相対echoです。

主代理量は、小時刻から連続unwrapした

$$
\delta_{\mathrm{phase}}^{(\phi)}(t)
=\frac{\operatorname{unwrap}\arg z_{\mathrm{echo}}(t)}{t}
$$

です。診断として

$$
\delta_{\mathrm{imag}}^{(\phi)}(t)
=\frac{\operatorname{Im}z_{\mathrm{echo}}(t)}{t}
$$

も保存します。いずれも符号を保持します。

単に$E_\phi$で回転した$\langle\phi|U_{\mathrm{PF}}|\phi\rangle$は、近似状態自身のエネルギー分散を含むため診断欄にのみ保存できます。主代理量へ置き換えないでください。また、近似状態から得たどの値も「直接PF固有値シフト」または`e_direct`と呼ばないでください。

$e^{-iHt}$は、元の制限Hamiltonianに対する同じ複素倍精度の作用として計算します。密な全対角化を代理計算の標準経路にせず、疎行列`expm_multiply`、既存スペクトル、または検証済みの同等実装を使って構いません。方法と費用を保存してください。

## 5. 校正モデル

元raw JSONから各PF・条件の`analytic_time`を読み、次の同一絶対時刻で代理量を計算します。

$$
t/t_{\mathrm{ana}}=0.1,0.2,0.3,0.4,0.5.
$$

符号付き5点を用いて、固定二項モデル

$$
\delta(t)=a_4t^4+a_6t^6
$$

を無重み最小二乗で作ります。これが`echo_phase_5point`主モデルです。

固定済み診断としてのみ、次も保存します。

- echo位相の0.1、0.2、0.3の3点二項fit。
- echo虚部の5点二項fit。
- echo虚部の3点二項fit。

各fitについて、$a_4,a_6$、設計行列条件数、学習残差、係数符号、予測$t_*$、$t_*$での各項寄与を保存します。元の直接固有値5点fitの係数との差も報告しますが、厳密係数へ近づけるために代理定義や点を調整しないでください。

## 6. 代理定義のsanity check

近似状態の結論を見る前に、厳密基底状態＋echo位相5点について確認します。

1. 人工Hamiltonianで`U_PF=e^{iHt}`としたときechoが1になる。
2. 元rawの十分小さい時刻で、echo位相の符号が直接固有値シフトの符号規約と一致する。
3. 4つの主条件で、厳密状態echoモデルが元の直接モデルの結論を再現できるか。

ここで符号・実装不一致があればRHF/CISDの成否を解釈せず、原因を報告して停止してください。有限時間の代理量差により4指標が落ちる場合は、それ自体を「厳密状態でもecho代理が不十分」というH01結果として保存し、RHF/CISDの成功とは呼ばないでください。

## 7. 直接truthの再利用と追加計算

元成果物のraw/fine JSONを最優先で再利用します。再利用点はHamiltonian metadata、PF係数、展開S2列、rotation数、絶対時刻、backend精度、protocol hashを照合し、元ファイルとcommitをmanifestに記録してください。

各代理モデルの予測$t_*$に対し、まず

$$
t/t_*=0.85,0.90,0.95,1.00,1.05,1.10,1.15
$$

の直接truthを評価します。既存絶対時刻と一致しない点だけ追加します。異なる状態やモデルが同じPF・絶対時刻を要求する場合は一度だけ計算します。

元ホールドアウトと同じ固定規則で候補になったモデルだけ、$0.90$から$1.10t_*$を1%刻みで細密化します。明確な不合格を細密化しません。

新しい直接truth点では、十分小さい時刻から厳密基底状態へつながる固有枝を隣接固有ベクトルまたは近縮退部分空間の重なりで連続追跡してください。同時に各時刻の最大厳密基底重なり規則も計算し、選択が異なれば警告します。以前のrunnerのように`previous_vector`を診断だけへ使い、枝選択を各時刻独立にしないでください。

直接truthの4指標と合格閾値、凍結予算倍率1.0/1.01は固定JSONどおり変更しません。

## 8. 主判定

主判定単位は「同一状態法＋同一PF＋echo位相5点＋active-space 4条件」です。

- 厳密状態echo sanity：元の主結論を再現できること。
- CISD置換成功：4条件すべてで4指標に合格し、1%余裕付き凍結予算も4/4達成すること。
- RHF置換：同じ基準で報告するが、CISD成功の必須条件にはしない。
- PF選択：代理法で実行可能と判定したPFの中から、元の直接結果と同じ最低直接コストPFを選べること。

条件ごとにecho位相・echo虚部・3点・5点を見て最良を後から選ぶ結果は参考値に分離し、主成功と混同しないでください。HF分子の2条件は補助診断であり、active-space 4条件の主合否を変更しません。

## 9. 実装前テストと再開安全性

長時間計算前に少なくとも次をテストしてください。

- 固定JSONのhashとrunner設定の完全一致。
- 元rawのsource hash、PF係数、S2列、rotation数、Hamiltonian metadataの照合。
- RHF determinantのbasis整数とoccupation対応。
- 小系CISD振幅のPySCF determinant順序から既存JW basisへの変換。
- 変換後CISDのノルムと、PySCF CISDエネルギー／同一Hamiltonian期待値の一致。
- 人工例でのecho恒等性、位相符号、連続unwrap。
- exact-state proxyとapproximate-state proxyの情報遮断。近似fitコードが厳密状態配列を参照しないこと。
- `infeasible_error_budget`を正の小数へclipしないこと。
- キャッシュキーにH01 protocol hash、Hamiltonian hash、state method、PF、絶対時刻、echo/direct区分、数値方式を含めること。
- statusだけでなく必須フィールド、hash、時刻集合まで検証してskipすること。
- stage計画にサーバー固有絶対パスを保存せず、成果物ルートからの相対パスで再開できること。

既存`review_tests`と新規テストを実行し、件数・結果を成果物に保存してください。

## 10. 代表条件の実測

`CO_active_eq_sto3g`＋`current_m3`＋CISD＋最初の正式校正時刻を代表条件にします。

- CISD生成。
- CPUでのexact-reference作用＋PF作用。
- 利用可能ならGPUでのPF作用と転送＋CPUまたはGPUでのexact-reference作用。
- 元の直接Schur点との費用比較。

状態生成、PF構築／作用、exact-reference作用、転送、総時間、CPU RSS、GPU増分を保存します。速く再現可能な方式を本バッチへ採用し、独立条件の並列数は共有資源を圧迫しない範囲にします。

## 11. 成果物

新しい

`artifacts/server_h01_approximate_state_calibration_<YYYYMMDD>_<git-short>/`

へ、少なくとも次を保存してください。

- `manifest.json`：最終status、全commit/hash、環境、backend、既知の未完了項目。
- 状態生成raw：RHF/CISD設定、振幅変換診断、状態指標、時間・メモリ。
- 全echo点のraw JSON：複素振幅、位相unwrap、虚部、代理量、時間・メモリ。
- 再利用・追加した直接truth点と枝監査。
- 全モデル係数、条件数、予測$t_*$、4指標、予算判定のJSON/CSV。
- exact/RHF/CISD、3点/5点、位相/虚部の比較表。
- PF選択混同行列または条件別選択表。
- 軽量な図と`report.md`。
- テストログと機械可読テスト集計。

report冒頭では次を分けて結論してください。

1. 厳密状態でもecho代理が直接固有値モデルを再現するか。
2. CISD状態で主4条件を通せるか。
3. RHF状態でどこまで通るか。
4. `current_m3`とYoshida 4次の実行可能性・順位を保てるか。
5. 直接固有値5点に対して、状態生成とecho校正を含む古典費用が実際に減るか。
6. HF伸長の既知の破綻を誤って成功と判定していないか。
7. この検証がoracle由来の時刻尺度を使う開発診断であり、end-to-end実用校正ではないこと。

## 12. commit、push、停止

コード、テスト、固定JSON、raw、集計、図、reportを新しい結果ブランチへcommitし、`HIROMU1015/*`のoriginへpushしてください。既存成果物を上書きせず、mainへmergeせず、force-pushしません。

最終報告では、ブランチ、commit、成果物パス、テスト結果、実行時間・最大メモリ、主4条件と補助2条件の結論、未解決事項を示してください。その後停止し、H02/H05、F領域、新PF探索、新しい分子ホールドアウトへ自動的に進まないでください。
