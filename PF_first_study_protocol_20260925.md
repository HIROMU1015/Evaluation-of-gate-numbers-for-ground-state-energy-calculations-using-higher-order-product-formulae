# 第一研究protocol v1.0：校正誤差の三分解と凍結資源への伝播

**固定日：2026年9月25日**  
**状態：正式実行前に事前固定済み**  
**対応する全体計画：`PF_research_strategy_and_plan_20260925.md` のS0〜S2**

## 0. 正本と変更規則

機械可読な正本は次である。

- `PF_first_study_protocol_20260925.json`
- SHA-256：`410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565`
- hashファイル：`PF_first_study_protocol_20260925.json.sha256`

本書は固定JSONの説明版である。本書、runner、既存コードの既定値が固定JSONと
競合する場合、固定JSONを優先し、科学的計算の前に停止する。条件変更が必要なら
結果を見る前でもversionを上げ、新しいJSON、hash、Phase A commitを作る。

以前の探索案は `PF_first_study_protocol_20260925_draft.md` として保存した。正式
結果へ探索案の「候補」「初期提案」を混入させない。

## 1. 目的、主張範囲、停止点

同一Hamiltonian・PFについて、有限時間の予測差を

$$
\widehat f_\psi-\delta_P
=
(\widehat f_\psi-g_\psi)
+(g_\psi-g_0)
+(g_0-\delta_P)
$$

へ分ける。各項をそれぞれ

1. model--approximate-state proxy差、
2. approximate--exact state proxy差、
3. exact-state proxy--PF eigenvalue shift差、

とし、時刻選択、PF選択、凍結QPE予算へどう伝播するかを調べる。

今回の第一研究は

$$
\boxed{\text{Mechanism}+\text{Decision sensitivity}}
$$

までである。新しい実用selectorの完成、未使用分子への転用、新PF係数探索は
含まない。H2/H4は既に使用済みの開発系なので、独立holdoutとは呼ばない。

## 2. 固定source identity

commit `6d13384ef327e5b248c2ce93ae29ad4e7686b2e5`に収録された次の2成果物を
byte-for-byteで使用する。

- `artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/effective_operators.npz`
- `artifacts/prevalidation_h01_approximate_state_pilot_20260922/states.npz`

固定JSONには次を保存した。

- 2ファイルのSHA-256。
- 保存済みH2/H4 Hamiltonianのcanonical array SHA-256。
- H4の13 groupの順序と各groupのhash。
- basis、geometry、電子数、sector、orbital/qubit ordering。
- 36個のsector full-basis indices。
- exact/RHF/CISD stateのhash。
- HF determinant indexとCISD subspace positions。

今回使うH4 Hamiltonianは、保存済み36次元sector Hamiltonianそのものである。
別のfull-Fock-space Hamiltonianを再生成して同等とみなさない。source fileまたは
内部配列が一つでも不一致なら`failed_source_identity`として停止する。

生成時manifestはdirty worktreeのhead `2ba6174`を記録しており、成果物は後に
`6d13384e`へ収録された。この履歴を隠さずsource manifestへ記録する。

## 3. 固定PFと費用

対象は次の対称4次PFに固定する。

- `yoshida4`
- `current_m3`
- `two_term_center`
- `m5_best`

係数列、S2列、H4での展開step数、Pauli rotation数、出典は固定JSONを正本とし、
ラベルから再構成しない。目標誤差とQPE定数は

$$
\epsilon_E=1.5936001019904\times10^{-4}\ \mathrm{Ha},
\qquad \beta=1.2
$$

である。

## 4. S0：既存practical選択のexact-time採点

正本はcommit `4f4374b`のpractical最小版である。

- protocol SHA-256：`7bbe9958837a881f0247b6e72f5e80e2331e0cfe50dea18addd13a2748467d55`
- predictions SHA-256：`fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e`
- Phase A commit：`79035cc7c414c04cafe8b9f8bdc779a17ec57302`

6条件の`selected_formula`、`selected_time`、`predicted_cost`、frozen budgetを変更
しない。各選択時刻の`0.99,1.00,1.01`倍を挿入し、保存済み連続枝の最寄りの信頼
可能な下側点から接続する。追加のbracketing点が必要なら計算し、すべて新規診断
点として数える。

元protocolの`new_direct_truth_point_count=0`を後続採点へ流用しない。実際に追加
した正の点数を保存する。主regretの基準は元の2 PF・元の保存格子のままとし、
拡張格子の基準は別列で報告する。

## 5. Experiment A：数式・数値実装validation

これは一般性を主張する実験ではなく、測っている量が定義どおり動くかの検査で
ある。

### 5.1 二準位系

可換対照：

$$
H=X+Z,\quad A=0.4(X+Z),\quad B=0.6(X+Z).
$$

非可換対照：

$$
H=X+Z,\quad A=X,\quad B=Z.
$$

状態はexact ground、$q=0.01,\phi=0$のreal状態、$q=0.01,\phi=\pi/2$のcomplex
状態に固定する。時刻の絶対値は

$$
0.05,0.08,0.12,0.18,0.27,0.40\ \mathrm{Ha}^{-1}
$$

で、正負を独立に計算する。80桁参照とcomplex128実装を照合する。

### 5.2 保存済みH2

保存済みH2行列・2 group・exact stateを使い、4 PFを同じ正負時刻で検査する。
再生成しない。

三分解closure、even/odd次数、可換系の真のゼロ、係数丸めによる偽の低次項を
すべて検査する。ここで失敗したらExperiment B/Cへ進まない。

## 6. Experiment B：H4 controlled study

### 6.1 状態

exact、RHF、CISDに加え、

$$
|\psi(q,\phi)\rangle
=\sqrt{1-q}|0\rangle+e^{i\phi}\sqrt q|\chi_{\rm CISD}\rangle
$$

を使う。

$$
q\in\{10^{-3},10^{-2},5\times10^{-2}\},\qquad
\phi\in\{0,\pi/2,\pi,3\pi/2\}.
$$

CISDをexactへphase-alignし、

$$
\chi_{\rm raw}=|\mathrm{CISD}\rangle
-|0\rangle\langle0|\mathrm{CISD}\rangle,
\qquad
\chi_{\rm CISD}=\chi_{\rm raw}/\|\chi_{\rm raw}\|
$$

とする。この方向を全PFで共通にし、PF別の$QD_4|0\rangle$方向を主比較へ追加
しない。

### 6.2 共通絶対時刻による機構解析

trainingは

$$
T_{\rm train}=\{0.10,0.15,0.20,0.25,0.30\}\ \mathrm{Ha}^{-1},
$$

未使用evaluationは

$$
T_{\rm eval}=\{0.125,0.175,0.225,0.275,0.35,0.40\}\ \mathrm{Ha}^{-1}
$$

へ固定し、両方の正負時刻を計算する。PF・状態ごとに窓を動かさない。

fitは切片なし・無重み最小二乗で、列2-norm scaling後の条件数も保存する。

- 正時刻proxyへの偶数二項：powers `[4,6]`。
- evenized proxyへの偶数二項：powers `[4,6]`。
- odd診断：powers `[5,7]`。選択には使わない。

scaled design condition numberが$10^8$を超えるfitは不安定とする。

### 6.3 近似状態だけを使うdecision track

主運用状態はCISD、RHFとcontrolled statesは診断である。exact stateはoracle比較に
だけ使う。

先頭係数は`geomspace(0.02,1.8,34)`、5点rolling window、雑音床
$5\times10^{-13}$ Ha、次数許容差0.2、$R^2\ge0.999$、最初の合格窓という既存
規則で近似状態proxyから得る。合格窓がなければabstainし、個別のPFだけ窓を
変えない。

近似状態proxyの$a_4$から

$$
t_{\rm ana}^{\rm proxy}
=\left(\frac{\epsilon_E}{5|a_4^{\rm proxy}|}\right)^{1/4}
$$

を作る。主fit点は

$$
T_{\rm fit}=\{0.1,0.2,0.3,0.4,0.5\}t_{\rm ana}^{\rm proxy},
$$

3点法`{0.1,0.2,0.3}`はselection-inertなablationに限定する。時刻選択は

$$
T_{\rm select}
=\operatorname{geomspace}(0.25,2.0,401)t_{\rm ana}^{\rm proxy}
$$

からだけ行う。signed $t^4+t^6$モデルを使い、費用では絶対誤差を使う。4 PFで
予測可能かつfeasibleな候補の最小費用を選び、候補がなければabstainする。

Phase Bでは、Phase Aで固定した4 PF固有の格子の和集合だけを直接評価し、その
最小を`C_ref_grid`とする。truthを見た後に格子を拡張しない。これは連続時間の
厳密最適値とは呼ばない。

## 7. Experiment C：固定H二準位相殺系

$$
H=X+Z,\quad A(\lambda)=X+\lambda Z,
\quad B(\lambda)=(1-\lambda)Z
$$

とYoshida4を使う。固定点は

$$
\lambda\in\{1,\lambda_0-0.1,\lambda_0-0.03,
\lambda_0,\lambda_0+0.03,\lambda_0+0.1\},
\quad \lambda_0=-2+\sqrt{15}.
$$

$\lambda=1$は$B=0$の可換対照である。exact groundと同じ$q,\phi$状態族を使い、
三分解と資源感度を評価する。step費用は2 groupで展開した7 group exponentialと
し、分子のPauli rotation数とは呼ばない。人工系を分子での頻度やtransferの
証拠にしない。

## 8. 正負時刻の位相・枝規則

正時刻と負時刻を別系列として

$$
0\rightarrow+t_1\rightarrow+t_2\rightarrow\cdots,
\qquad
0\rightarrow-t_1\rightarrow-t_2\rightarrow\cdots
$$

と追跡する。符号付き時刻を一つの配列へ連結してunwrapしない。

各点でprincipal phase、unwrapped phase、unwrap整数、echo overlap、branch ID、
ground/previous/projector overlap、固有対残差、unitarity residual、
$\|U(-t)-U(t)^\dagger\|$を保存する。その後だけ

$$
g_{\rm even}(t)=\frac{g(+t)+g(-t)}2,
\qquad
g_{\rm odd}(t)=\frac{g(+t)-g(-t)}2
$$

を作る。

## 9. 数値識別性

各時刻でsignal $S=|g(t)|$と、すべてHartree単位へ換算した数値noise $N$を保存し、

$$
\rho=S/N
$$

を計算する。

- `resolved`：$\rho\ge100$。
- `marginal`：$10\le\rho<100$。
- `unresolved`：$\rho<10$。

主fitは5点すべてが少なくともmarginalで、3点以上がresolvedの場合だけ成立する。
満たさない場合は`not_identifiable`とし、PF固有の時刻変更を行わない。行自体は
削除せず保存する。noiseの定義と全数値許容差は固定JSONを正本とする。

## 10. Phase A / Phase B

### Phase A：selector freeze

入力可能：Hamiltonian、指定された入力状態、近似状態training proxy、PF係数、
展開費用、目標誤差、事前固定した数値品質指標。

入力禁止：exact-ground proxy、直接PF固有値shift、direct optimum/minimum cost、
truth-grid値、過去のH4合否、Phase B出力。

Phase A終了時に少なくとも

- `protocol.json`
- `source_manifest.json`
- `predictions.json`
- `prediction.sha256`
- focused test log
- git commit

を保存し、commit境界を作る。controlled stateはexact情報から構成したoracle機構
診断なので、practical selectorの証拠には使わない。

### Phase B：truth scoring

Phase Aのpredictionとscorerを変更せず、直接固有枝、直接費用、oracle比較、regret、
frozen-budget marginを加える。truthを見た後のbug修正は元runを`invalidated`として
保存し、protocol versionを上げてPhase Aからやり直す。

## 11. 資源採点

$$
B_\gamma=\gamma\widehat C,
\qquad
\epsilon_{\rm PE}=\frac{\beta K_P}{tB_\gamma},
\qquad
S_E=\epsilon_E-|\delta_P(t)|-\epsilon_{\rm PE},
$$

を$\gamma=1,1.01$で計算する。$S_E\ge0$を成功とする。$\gamma$を二重に掛けない。

報告する損失は、同一PF内の時刻選択regret、PFと時刻を合わせたjoint regret、
`B_gamma/C_ref_grid-1`である。モデルfitに失敗したPFも、枝が信頼可能で直接費用が
feasibleならdirect referenceから除かない。

## 12. 終了条件

次のどれか、またはいずれも成立しなかったnull結果を得た時点で停止する。

1. 一つの誤差成分が他の各成分の3倍以上となる状態が、同一caseのresolved評価点の過半数で続く。
2. 固定したPF・状態・介入条件により支配成分が切り替わる。
3. 誤差成分の少なくとも一つが$0.05\epsilon_E$以上でも、joint regretが10%以下かつ$\gamma=1.01$で$S_E\ge0$となる。

終了後は、追加分子、新PF探索、改善calibrationの選択、S3へ自動的に進まない。

## 13. 必須成果物

- `protocol.json`、`source_manifest.json`
- `observables.csv`、`error_decomposition.csv`
- `state_diagnostics.csv`、`operator_diagnostics.csv`
- `signal_quality.csv`
- `predictions.json`、`prediction.sha256`
- `allocation_scoring.csv`、`branch_audit.csv`
- `resources.csv`、`audit.json`、`manifest.json`
- `report.md`

source identity、Experiment A、Phase A/B境界、件数・hash照合のすべてが合格した場合
だけ`COMPLETE`を作る。科学的な仮説不支持は正当な結果だが、数値validation失敗を
科学的結果として解釈しない。
