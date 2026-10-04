# Prediction / freeze / scoring contract

今回のstatusは `hchain_independent_validation_protocol_blocked`。設計文書のみであり、下記の実行やテストを許可しない。

## Two distinct preparation boundaries

指示には「新CISD・cheap calibrationはまだ実行しない」と「generated state hash / candidate absolute timesを事前固定」の両方がある。H2/H6のt_refは未取得なので、今回9点の絶対座標を埋めて実行可能とすることはできない。

別reviewが必要な順序案：

1. 本設計・acquisition wrapper・state/H input sourceを固定し、truth-free input/reference preparationだけを別承認する。
2. 同一sectorのCISD hashと34点short-time gridの値・hexを、取得前にそれぞれ固定する。H6 Hamiltonianの新規再構築はこの承認に自動的には含まれない。
3. 継承fitでt_refを取得し、candidate_planの9点のabsolute time / hexを固定する。H4 scalar reuseは同一H/state/PF/gridのidentity確認が必要。
4. 新しいcandidate freeze commitをreviewした後、候補上のcheap/M1 predictorとtruth scorerの一回実行を別承認する。

これを今回の暗黙の実行権限や「計算済みprotocol」とはしない。H4の3行だけは保存fitのscalarからabsolute time / hexを記載するが、input runtime identityの確認は未実施。H2/H6の空欄6行は未取得であり、0・旧oracle t_ana・近傍点に置換しない。

座標算術は float64(r)*float64(t_ref) の一回の積に固定する。factor_of_T0=1.0,1.3,1.6は意味上のlabelであり、1.3*T0等へ式を組み替えて別hexを生成しない。fit gridのgeomspaceも実行environmentで値/hexをfreezeしてから取得する。

## Predictor information allowlist

許可候補はsanitized Hamiltonian（action用）、CISD state、RHF/sector/orbital identity、ordered PF component、canonical coefficient hex、source/protocol hash、固定9候補のみ。F01/H01のarchiveにはexact state・ground energy・effective-H oracleが含まれるので、丸ごとのarchiveや歴史的load_h4_systemを渡さない。

CISD generatorのsubspace eigensolveはinput preparationに隔離する。候補predictorではfull-H / full-PF truth eigensolver、full PF matrix、exact state、direct shift、truth phase gap、truth label、追加時刻を禁止する。H2のm=4 projected solveはsector全体と同じ次元になる有限サイズ例であることを明記し、exact-state入力の流用と区別する。

## Cheap → acquisition freeze → conditional spectral

- cheapの9候補を取得し、B0・全four-gamma B1 frontier・B2 action・cheap instability・H1 qを固定する。qにM1やtruthを使わない。
- q=1のsystemだけで、昇順3候補のM1を取得する。H1とalways-M1で同じstart state、prefix、phase rule、同一sourceを使用する。
- H1のfinal action / selection / fallback / budgetを固定する。q=0ではB2と一致。q=1ではS1A consistencyとadoption規則をそのまま使う。
- always-M1 comparator用の不足systemのM1は、H1 decision固定後に補完する。共有のM1作用数は全体最大60。H1へq=0のM1出力を逆流させない。
- B1/B2/H1/M1全最終predictionとauditをcommit / SHA-256固定し、ここまでtruthを開かない。

このshared scheduleはreview案であり、実装済みではない。実測H1 combined pathとstandalone comparator costの可用性は分離する。

## Freeze artifacts and immutable scorer

候補案：prediction.json、prediction.sha256、PREDICTION_FROZEN.json、source_audit.json、access_audit.json、resource_audit.json、manifest.json。これら軽量7件だけを明示stageする。acquisition q freezeとfinal decision freezeの別hash、時刻、source/input/candidate-plan commitをprediction内に保存する。runtime、state、matrix、unitary、eigenvector、pickle、npyはGitへ含めない。

scorer開始時HEAD=prediction commit、7件がcommit blobとbyte-identical、実装・protocol・input・candidate hash一致を要求する。不一致時はtruthを開かない。scorerはprediction / gamma / eta / primary / width / selectorを変更しない。

freeze前はtruthを読むexisting testsを実行しない。truth-free test allowlistは実装reviewで固定する。focused/full execution testsはfreeze後に限る。scorer後も同じtestsとmanifest検証を行う。

中断再開は別実行承認で同一run identity / outputだけを許す設計とする。別run、threshold救済、追加anchor、H2/H4への自動subset化は禁止。
