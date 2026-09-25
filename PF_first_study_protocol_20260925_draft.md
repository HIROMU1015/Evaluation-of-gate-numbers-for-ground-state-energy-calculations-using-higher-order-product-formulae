# 最初の本実験：校正誤差の三分解と凍結資源への伝播

**日付：2026年9月25日**  
**用途：研究実行環境のCodexへ渡す作業仕様案**  
**対応する全体計画：`PF_research_strategy_and_plan_20260925.md` のS0〜S2**

## 1. 今回の目的と停止点

目的は、同一Hamiltonian・PFについて、有限時間の予測のずれを

1. モデルと近似状態proxyの差、
2. 近似状態proxyとexact状態proxyの差、
3. exact状態proxyと直接固有値シフトの差、

へ分け、それぞれが最終的な時刻選択と固定予算にどのように影響するかを調べることである。

「相殺が必ず校正失敗を引き起こす」と仮定しない。改善が起きる場合、係数は変わっても資源はほぼ変わらない場合、proxyのモデル構造が合っていない場合も残す。

今回の停止点は、**既存結果の確定、解析可能な例での定義検証、H4の4種類の対称4次PFでの最初の原因分離レポート**である。ここで一度報告し、全分子への拡張、新PF探索、最終holdout、巨大な高次BCH展開へ自動的に進まない。

本仕様は計画であり、既存の検証結果を無効にするものではない。

## 2. 最初に読む固定資料

リポジトリ：

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

基準索引：`e820f653a5916f27233ab4674a89d288cf969e37`

- `docs/prevalidation_results_index.md`
- `docs/current_research_status.md`
- `docs/pf_data_use_ledger.md`

主な固定結果：

| 内容 | commit |
|---|---|
| 初期監査、X01/X02 | `2ba6174b6f9617d51766579c775a77132f3c7f57` |
| F01/F02/F05、H01pilot、H03/H04/H05、D04 | `6d13384ef327e5b248c2ce93ae29ad4e7686b2e5` |
| F03 | `e820f653a5916f27233ab4674a89d288cf969e37` |
| H02制御状態 | `16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe` |
| practical最小版 | `4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a` |

H02のproxy定義の正本は、最後から二つ目のcommit内の

- `review_response/h02_finite_time_controlled_state_protocol.json`
- `review_response/run_h02_finite_time_controlled_state_diagnosis.py` の `_echo_models`

である。これは `arg(<psi|exp(-iHt) U_PF(t)|psi>)/t` を用いている。一方、practical最小版は `Im` 版である。定義を混ぜない。

ローカルで後続修正や6選択点の確定作業が既に完了していないか確認し、完了済み部分は再計算しない。必要なファイルが別ブランチにある場合は、そのcommitを明示して読み、依存を確認してから再利用する。結果ブランチを無条件に一括mergeしない。

## 3. S0：既存の6選択点を確定する

practical最小版の `predictions.json`、`protocol.json`、`audit.json`、元Hamiltonian/cacheのhashを照合する。

各条件の `selected_formula`、`selected_time`、`predicted_cost` は変えない。保存済みtruthの近傍時刻ではなく、選択時刻そのものに点を挿入する。

### 必須の枝監査

孤立点で最大基底重なりを選ぶだけにしない。既存の基底接続枝の前後へ新点を挿入し、次を保存する。

- exact groundとの重なり。
- 前後の枝ベクトルまたは対応する射影空間との重なり。
- unwrap整数と固有位相。
- 固有対残差とユニタリ残差。
- 直接の符号付きシフトと絶対誤差。

前後のベクトルが保存されていない場合、必要最小限の前後点を再計算する。その計算を隠さず、新しい診断点として数える。必要な呼び出し回数を「厳密に6回」と決め付けない。

### 予算は1.00と1.01の両方

$$
B_\gamma=\gamma\widehat C,
\quad
\epsilon_{\rm PE}=\frac{\beta K_P}{\tau B_\gamma},
\quad
S_E=\epsilon_E-|\delta_P(\tau)|-\epsilon_{\rm PE}.
$$

$\gamma=1,1.01$で計算する。$\gamma$を二重に掛けない。PFコストK、beta、targetは元protocolを継承する。

保存する費用指標：同一PFの時刻選択損失、PF選択を含む直接費用損失、$B_\gamma/C_{\rm ref,grid}-1$。基準格子の範囲を変える場合は、旧基準に対する列も残す。

**終了条件**：6条件のexact-time評価、枝の整合、予算定義が確定すること。達成・未達のどちらでも報告する。未達を直すために過去の選択や予算を変更しない。

## 4. S1：数学・推定量・符号の単体検証

$U_P(\tau)\approx e^{+iH\tau}$、$W=e^{-iH\tau}U_P$を使う。

$$
g^{\rm Im}_\psi=\operatorname{Im}\langle\psi|W|\psi\rangle/\tau,
\qquad
g^{\rm arg}_\psi=\operatorname{unwrap}\arg\langle\psi|W|\psi\rangle/\tau.
$$

同じproxy定義ごとに

$$
\widehat f_\psi-\delta=
(\widehat f_\psi-g_\psi)+(g_\psi-g_0)+(g_0-\delta)
$$

を実装し、直接差と再構成差が数値精度内で一致することを確認する。

### 4.1 必須の正負対照

- 可換分割：PFがexactになる例。真のゼロをfit失敗から区別する。
- 非可換2×2例：独立な行列指数との照合。
- exact状態：H01相当のproxyに接続する。
- 実ベクトル近似状態と、複素位相を持つ近似状態。
- $+\tau,-\tau$：符号、負時刻、even/oddの取り違えを検出する。
- 係数丸め：形式4次条件の残差を監査し、見かけの低次項と区別する。

### 4.2 この計画から得た検証予測

局所的に$H_{\rm eff}=H+\tau^4D_4+\tau^6D_6+\cdots$なら、Im proxyの演算子は

$$
A(\tau)=\tau^4D_4+
\frac{\tau^5}{2i}[H,D_4]+\tau^6\left(D_6-\frac16[H,[H,D_4]]\right)+O(\tau^7).
$$

これを独立に導出・高精度検算する。H02の複素状態で$\tau^5$が実際に重要かは未確定であり、結果から判断する。

exact groundでは、非縮退・局所解析性の下で

$$
g_0-\delta=-\tau^8\sum_{n\ne0}
\frac{|\langle n|D_4|0\rangle|^2}{E_0-E_n}+O(\tau^{10})
$$

が予測される。F02の状態混合量と、三分解の第三項を同一H/Pで照合する。表示した漸近式を有限時間全域の保証にしない。

導出とコードの符号が一致しなければS2へ進まず、原因を解消する。単純な倍精度差分だけで小係数を同定しない。

## 5. S2：H4の同一条件実験

### 5.1 対象

既存F01/F03/H01pilotと同じH4のHamiltonian・軌道・群順序を再利用する。異なる再生成結果を同一Hとみなさない。基底の変換が必要なら、演算子と状態の両方へ同じ変換を適用して照合する。

PFは、Yoshida4、`current_m3`、`two_term_center`、`m5_best`の4つ。最初にYoshida4とm5を通して実装を確認し、問題がなければ他の2つも同じ規則で完了する。結論に都合のよいPFだけを残さない。

### 5.2 状態

exact、RHF、CISDを使う。これに、CISD由来の直交方向を固定した

$$
\sqrt{1-q}|0\rangle+e^{i\phi}\sqrt q|\chi\rangle
$$

を加える。

最小の提案点は$q\in\{10^{-3},10^{-2},5\times10^{-2}\}$、$\phi\in\{0,\pi/2,\pi,3\pi/2\}$。これは提案グリッドであり、物理的な普遍閾値ではない。数値条件の調整は正式結果を見る前の単体検証で終え、採用グリッドをprotocolへ固定する。

まず同じ$\chi$を全PFへ渡し、入力状態を公平にする。$QD_4|0\rangle$に合わせた最悪方向を追加する場合はPF内の別診断とし、PFごとに違う入力状態を与えた結果からPF順位を結論しない。

### 5.3 固定時刻版

まず学習・評価時刻を状態やPFのtruth最適時刻から独立に固定する。H4については、正時刻の五点

$$
\tau=0.10,0.15,0.20,0.25,0.30\quad\mathrm{Hartree}^{-1}
$$

を初期提案とし、対応する負時刻も計算する。既存の時刻セットを使う方が合理的なら正式実行前に変更を記録する。一つのPFだけ、結果を見て別の有利な窓へ移さない。

この共通時刻版は原因分離用であり、歴史的な$0.1,\ldots,0.5\,\tau_{ana}$プロトコルの置換や再評価ではない。

モデルは次を区別する。

- 元の偶数二項fit。
- even部分の二項fit。
- 奇数寄与の診断を加えたfitまたは既知の演算子係数との比較。

項数が異なる比較では同じ点数だけでなくfitの自由度も示す。追加の負時刻を使う方式だけ無料で情報が増えた比較にしない。

未使用評価点は保存された信頼可能なX02曲線の範囲から事前に固定する。共通格子での数学的な比較と、各PFの精度達成が可能な時刻領域の比較を分ける。

### 5.4 選択時刻版

次に、各近似状態の校正だけから時刻・予算を選ぶ。truthに由来する$\tau_{ana}$は選択側へ渡さない。現行practical方式は変更せず基準法として残し、新方式は別名・別protocolにする。

選択点で直接枝を採点し、三分解のどの成分を除くと配分結果が変わるかをoffline置換で調べる。置換は原因診断であり、実用的な成績ではない。

## 6. 固定Hの人工族

既存F03の人工族ではHも変化するため、それを「相殺だけの操作」と説明しない。

今回の候補は

$$
H=X+Z,\quad A=X+\lambda Z,\quad B=(1-\lambda)Z,
$$

に対するYoshida4である。S2の因子順序まで固定する。

非自明な$a_4$零点候補$\lambda_0=-2+\sqrt{15}$を独立な形式級数・高精度行列で確認する。$\lambda=1$はB=0の別の可換対照であり、非自明な零点と混同しない。

最初は$\lambda_0\pm0.03,\lambda_0\pm0.1$など、少数の事前固定点で十分。Hと物理ギャップは固定できるが、群ノルム・D4/D6/D8は変わるため全て記録する。$a_4\to0$で一項解析時刻を無制限に伸ばす方式は、適用外を含むnegative controlとして扱う。

人工系での成功を分子一般性の証拠にしない。H4と同じ三分解・予算採点を用い、何を制御できたかを明確にする。

## 7. 主な保存物

- `protocol.json`：本実験で固定した入力、時刻、モデル、指標、停止条件。
- `observables.csv`：exact delta、exact/approx proxy、Im/arg、even/odd。
- `error_decomposition.csv`：各寄与、合計、再構成残差。
- `state_diagnostics.csv`：状態法、q、phase、エネルギー、分散、oracle量。
- `operator_diagnostics.csv`：a4、D4ノルム、centered action、必要な高次成分。
- `predictions.json`：採点前のPF、time、PE配分、費用、hash。
- `allocation_scoring.csv`：gamma1/1.01、exact-time、予算余裕、費用比較。
- `branch_audit.csv`：連続枝、overlap、unwrap、residual。
- `resources.csv`：状態生成・群準備・proxy・fit・追加作用のcold/warm費用。
- `report.md`：以下の結論表と、次に進める一工程。

## 8. 報告してほしい結論

| 問い | 答え方 |
|---|---|
| exact状態でもproxy差は残るか | 大きさ、次数、F02混合量との一致・不一致 |
| realとcomplexで何が違うか | 奇数成分、偶数fitへの影響、偶対称化後に残る差 |
| 相殺の強いPFは状態に敏感か | 相対係数だけでなく、epsilonで正規化した絶対誤差で比較 |
| その差は時刻・凍結予算へ伝わるか | PF内・PF間・保守予算の三つの損失を分離 |
| どの改善が意味を持つか | 追加点、状態改善、proxy変更のうち、支配項を改善するものを一つ選ぶ |
| 仮説を支持しない例はあるか | 小さい係数でも安定、敏感でも配分が頑健、等を明示 |

終了時に「もっと多くの分子を計算すべき」とだけ結論しない。まず得られた原因分離から、次に進めるべき一工程を提案する。

## 9. 実行上の制限

既存成果物を上書きしない。未コミット作業を確認して新しい研究用ブランチ・結果ディレクトリへ分離する。mainの更新や他ブランチの破壊的整理はしない。

CPU/GPUは実測で選ぶ。共有計算機を占有する無制限の並列化はしない。denseな全N2/CO D8を、この最初の実験のために新規構築しない。

単体検証で不整合が見つかった場合は、本番の大量計算を止め、原因と修正案を報告する。科学的な不合格を数値実装の失敗と混同しない。

本仕様の完了後は、一度停止して進捗を共有する。ここから先は全体計画のS3以降であり、別の研究判断で進める。
