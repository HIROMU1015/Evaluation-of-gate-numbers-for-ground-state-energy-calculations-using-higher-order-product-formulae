# T0：共通task cardと調査境界

2026-10-17 JST。技術調査・既存記録の静的確認・未採択の問題定式化。
起点は `a80596c29e0eaaf7483f8981ed0e61c918335054`、branchは `qc-t0-baseline-gap-survey-20261017`。
今回の指示は添付「T0 — 最強baselineと未解決gapの調査・研究課題の抽出」。原本identityは [SOURCE registry](source_registry.json) に記録する。

## 1. 同じ問題として比較するための契約

\[
 H_{\rm orig}=cI+\sum_{pq}h_{pq}a_p^\dagger a_q
 +\tfrac12\sum_{pqrs}v_{pqrs}a_p^\dagger a_q^\dagger a_s a_r,
 \qquad E_0^{\mathcal S}=\lambda_{\min}(H_{\rm orig}|_{\mathcal S}).
\]

係数の規約、有限軌道基底、単位、電子数、spin等の保存sector \(\mathcal S\) をtask identityに含める。
全Fock空間の最小値は別task。有限基底の外の完全基底極限・実験値との一致は今回の出力ではない。
核反発等のscalar \(c\)、一体項、二体項、分解後の残余を保持する。

入力は係数の有限bit表現と取得費、sectorの符号化、精度 \(\epsilon_E>0\)、失敗確率 \(0<\alpha<1\)。
出力は \(\Pr[|\widehat E-E_0^{\mathcal S}|\le\epsilon_E]\ge1-\alpha\) を、その仮定と費用付きで満たす推定値。
一般の係数入力だけから効率的に解けるとは仮定しない。

| 情報・操作 | 今回の扱い |
| --- | --- |
| 初期状態 | 明示回路 \(A\lvert0\rangle\) または混合状態準備手順、sector漏れ、準備費 \(P\) を記録する |
| ground-space overlap | \(p_0=\operatorname{Tr}(\rho\Pi_0)\ge\eta>0\) を使う定理では、\(\eta\) の根拠・取得費が必要。未知の実測値を無料入力にしない |
| gap | certified lower boundを必要とする定理と、gap-freeな定理を別比較する。経験的励起energyは保証ではない |
| energy window・branch | 係数から得る安全な幅、既知scalar、時刻規約を明示する。正しい固有位相branchは入力しない |
| controlled evolution | primitiveから生成・合成して費用を払う。全Hの時間発展oracleを無料としない |
| DF・active-space等 | 元のtaskを変える場合は、残余またはsector作用素norm誤差の保証を別途要する |
| exact state・全固有情報 | 過去の検証truthとして存在しても、運用側accessには移さない |
| 古典処理 | integral取得、分解、係数・誤差上界、state準備設計、sampling table、推定postprocessingを含む |

状態準備と \(\eta\) の正当化を与えられないインスタンスでは、後段の条件付き定理だけを報告する。
その費用をゼロとした「絶対E0の完全なbaseline」は認定しない。

## 2. 許可された方法と費用

研究の中心はPFによるprimitiveの合成と測定型energy推定。既知のfermion mapping、number-conserving rotation、
Pauli rotation、Hadamard test、古典的乱択・postprocessingは比較対象にできる。
block-encoding／qubitizationは外部対照として記載するが、中心へ移行しない（D1）。
QET-Uが時間発展から関数のblock-encodingを作る場合も、その実質を記録する。

費用は単一のgate数に潰さず、
\( (C_{\rm classical},N_{\rm prep},N_{\rm shots},G_{2q},G_{RZ},G_T,G_{\rm Toffoli},D_{\max},Q_{\max})\)
のうち取得済み成分を示す。実数角rotation proxyからT/Toffoli・物理runtimeへの換算は、synthesis・architecture契約なしに行わない。
総費用式と成功確率は [費用分解](t0_total_cost_decomposition.md) に記す。

今回は分子、係数データ、数値精度、\(\eta\)、hardwareを新しく選定していない。
したがって数値上の普遍的winner・支配項・新しい費用順位は出さない。

## 3. 比較の層

| 層 | 検証する対象 | 許されない推論 |
| --- | --- | --- |
| 数学的上界 | 明示条件下のnorm／energy／統計保証 | 漸近評価を有限step証明とする |
| 保存された数値結果 | 固定task・固定providerの性能 | 分子・sector・精度をまたいだ再順位付け |
| 条件付き資源推定 | 誤差係数・回路単価等を仮定した予測 | その係数やtruth accessを無料にする |
| end-to-end | preparationから絶対E0・成功率まで | 信号精度だけでE0保証を宣言する |

等アクセス比較S5では、単純なStrang／標準高次PF、sector上界、gap-free CDF、利用可能なら強い既知の外挿法を外さない。
情報予算S1では、必要情報を「与えられたもの」「合法に取得するもの」「未取得」に分ける。

## 4. 保全と停止

J1は `PAUSED_PENDING_NEW_MECHANISM`、Q1は `PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE` のまま。
第一・第二研究、PR Track A/B、P1～P8、T1-D、SOS-PF等の正式判断を変更しない。
今回のR1という符号は新しい未採択の保証問題の整理用IDであり、Q1の再開ではない。

科学計算、保存科学値の再解析・再ランキング、Hamiltonian生成、solver、科学用記号計算、回路build／compile、
benchmark、新アルゴリズムの構成探索は実施しない。最小例は次回の紙上検証案だけを残す。
静的処理はGit、HTTP取得、PDFテキスト抽出、JSON・リンク・hash監査に限る。
公開・照合完了後はMandatory STOP。候補採択・追加調査・詳細レビュー・実装を自動開始しない。
