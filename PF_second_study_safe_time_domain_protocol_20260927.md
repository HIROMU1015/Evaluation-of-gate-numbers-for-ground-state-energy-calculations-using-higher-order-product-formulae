# 第二研究protocol：multiple-window consistencyによる安全な時間域拡張

作成日：2026年9月27日

状態：`protocol_only_no_phase_a_or_phase_b_executed`

base branch：`first-study-paper-figures-20260926`
base commit：`123c84d459613db109dc23aa3b0872334fa12ddd`

機械可読な正本は
`review_response/second_study_safe_time_domain_protocol.json`、そのSHA-256は
`review_response/second_study_safe_time_domain_protocol.json.sha256`に置く。

## 1. 問いと範囲

第二研究の問いは次である。

> 近似状態と有限個の校正情報だけを使い、現行fallbackの`0.5 t_ana`より広い
> 時刻域を利用してよい経験的根拠を作り、精度達成と古典情報費用を保ちながら、
> 凍結Pauli rotation予算を減らせるか。

固定PFは`current_m3`だけとする。PF選択、新PF探索、係数変更、別精度、別基底の
追加は行わない。S4の`complete_no_benefit`、第一研究のprediction、閾値、
truncation率を変更しない。

採用する情報源は **multiple-window consistency** 一方式だけである。CISD状態の
echo proxyを隣接する二つの三点窓でfitし、次の候補点での予測残差、窓間差、符号、
feasibilityを検査する。二状態一致、別のproxy consistency、operator診断、学習済み
error envelopeは重ねない。

この規則は経験的方法であり、上限外の厳密安全保証ではない。二窓の一致、小さいfit
残差、小さい固有対残差のいずれも、それだけで物理的安全性を証明しない。

## 2. 第一研究から固定する事実

source identityの機械可読監査は
`review_response/second_study_safe_time_domain_source_leakage_audit.json`に置く。
正本artifactを再照合した結果は次のとおりである。

- `gamma=1.01`の凍結予算は、exact selected-time採点で6/6安全。
- original two-PF saved gridでは6/6で`F_P=1`。
- active-space 4条件の`F_total`は
  `1.100631, 1.423985, 1.120734, 1.193383`。
- HF 2条件の`F_total`は`2.150313, 2.102857`。
- HF/current_m3は両方とも相殺fallbackが発火し、`0.5 t_ana`上限を選択。
- 上限内の最大直接費用削減率はHF平衡`1.254948%`、HF伸長`0.322572%`。
- HFのdomain-loss下界は`2.114659, 2.069664`。
- S4の固定結果は`no_benefit`。beta=1.2 corrected auditでも42/42行が安全で、
  label変更は0。42行は6条件×7 strategyであり、42独立条件ではない。

S0 commitはbaseのGit祖先ではないが、baseに収録されたS0の`manifest.json`、
`audit.json`、`scoring.csv`はcommit
`cc3626a8135b647fe283fc60c963de70c5f6b2a5`のblobとbyte-identicalである。この
branch topologyとfile identityを区別する。

## 3. 開発集合と独立評価集合

`docs/pf_data_use_ledger.md`に従い、H-chain、LiH、BeH2、H2O、NH3、CH4、N2、CO、HFは
すべて探索・開発・診断または過去のholdout結果確認に使用済みとする。特にN2/CO/HFの
6条件は第二研究のrule developmentと資源見積りには使えるが、独立評価には使わない。

独立評価は結果を見る前に次の4条件へ固定する。

| 条件 | 群 | bond length | basis | frozen core | active space |
|---|---|---:|---|---:|---:|
| `LiF_active_eq_sto3g` | independent active-space | 1.5639 Å | STO-3G | 2 spatial orbitals | 8e, 8o |
| `LiF_active_stretch150_sto3g` | independent active-space | 2.34585 Å | STO-3G | 2 spatial orbitals | 8e, 8o |
| `HCl_full_eq_sto3g` | independent full-electron stress | 1.2746 Å | STO-3G | 0 | 18e, 10o |
| `HCl_full_stretch150_sto3g` | independent full-electron stress | 1.9119 Å | STO-3G | 0 | 18e, 10o |

protocol作成時点のlocal worktree横断検索と全local Git refsで、これらの正確なcondition ID、
PF誤差、QPE費用の既存数値使用は見つからなかった。ただしGPUサーバーの未追跡成果物は
このworktreeから完全には監査できない。Phase A前にサーバー全体を同じ4 ID、`LiF`、
`HCl`、geometry hashで検索する。既存数値が一件でも見つかったら分子を差し替えず、
`no_go_independence_contaminated`として停止する。

## 4. 共通定義

目標誤差は

`epsilon_E = 0.00015936001019904 Ha`

とする。直接PF誤差を`e_direct(t)`、`current_m3`一ステップのPauli rotation数を`K`とし、
corrected auditと同じ`beta=1.2`を使う。

```text
C_required(t) = beta K / [t (epsilon_E - e_direct(t))]
B_frozen(t)   = gamma beta K / [t (epsilon_E - e_hat(t))]
gamma         = 1.01
```

古典秒数、CPU/GPU memory、状態生成数、Hamiltonian作用数、group spectrum数、proxy点数を
別々に保存する。これらをPauli rotation数と換算条件なしに加算しない。

## 5. Phase A：truthを開かない選択

### 5.1 入力境界

Phase Aに許すのはcondition specification、Hamiltonian、term grouping、component spectra、
term counts、同一active spaceのdeterminant-space CISD state、`current_m3`係数、目標誤差、
protocol定数、CISD echo proxyとその費用だけである。

次はPhase Aとselectorから禁止する。

- exact ground state、energy、overlap、gap。
- direct PF eigenvalue、signed shift、absolute error、required cost。
- direct optimum、candidate-grid minimum、過去のpass/fail label。
- Phase B出力、truth path、既存direct座標から導いた情報。

独立分子の生成でもexact diagonalizationをしない。粒子数sectorを固定し、追加Z2 sectorを
使う場合はRHF determinantとCISD supportだけからmask/targetを決める。Phase Bで別sectorが
真の基底だったと分かっても、Phase Aを適応・再実行しない。

### 5.2 現行rule

time scaleは既存practical ruleを維持する。絶対時刻`0.02`から`1.8 Ha^-1`の34点
geomspaceを小さい順に評価し、最初に合格した5点rolling windowから`alpha_proxy`と
`t_ana=(epsilon_E/(5|alpha_proxy|))^(1/4)`を作る。formal-order toleranceは`0.2`、
minimum R²は`0.999`、noise floorは`5e-13 Ha`である。

現行current_m3 baselineは`0.1,0.2,0.3 t_ana`の`[t^4,t^6]`fit、`0.05` robustness、
`0.5` sentinelを使う。相殺index `<0.02`、sentinel residual `>0.05 epsilon_E`、符号不一致、
符号判定不能のいずれかでfallbackし、最大時刻を`0.5 t_ana`へ制限する。これらを再調整しない。

### 5.3 新しいmultiple-window rule

現行fallbackが発火した条件だけに適用する。最初の観測列は

`0.1, 0.2, 0.3, 0.5 t_ana`

とし、上限外候補を次の順に一度だけ評価する。

`0.65, 0.80, 0.95, 1.10, 1.25, 1.40, 1.55, 1.70 t_ana`

候補`r_j`ごとに、直前3点のmodel `f_prev`と、`r_j`を含む最新3点のmodel `f_curr`を、
固定power`[4,6]`でsigned least squares fitする。次をすべて満たすとconsistency passとする。

1. `|g(r_j)-f_prev(r_j)| / epsilon_E <= 0.05`。
2. 最新3点上の`max |f_prev-f_curr| / epsilon_E <= 0.05`。
3. 測定proxyと両modelの候補点予測がsign noise floorを超え、同一符号。
4. `e_guard=max(|g|,|f_prev|,|f_curr|) < epsilon_E`。
5. 数値計算が有限で、repeatability gateを通る。

初めて不合格になった点で即時停止し、後続候補を取得しない。consistencyに合格しても、
現行fallbackに対する予測凍結予算削減が5%未満なら、その点は通過できるが選択候補には
しない。合格かつ5%以上の候補中で`e_guard`による予測費用が最小の点を選ぶ。
判断不能またはeligible点0なら現行設定へ戻る。

この`0.05 epsilon_E`は第一研究のsentinel residual thresholdを継承したもので、独立評価を
見て決めない。窓幅、候補列、5%改善条件もこのprotocolで固定する。

### 5.4 四つの比較

| strategy | 入力費用 | 選択 |
|---|---|---|
| `current_fallback` | 現行情報だけ | 現行current_m3 ruleと`0.5 t_ana` fallback |
| `equal_information_pooled_fit` | 新ruleが実際に取得した同一proxy点 | 全点を一つの`[t^4,t^6]`fitに入れ、窓gateなしで観測済み候補から選ぶ |
| `multiple_window_rule` | 上と完全に同じ | 隣接窓gate、`e_guard`、停止規則で選ぶ |
| `uncapped_counterfactual` | 元三点model | capだけ外して固定候補列から選ぶ。運用安全法とは扱わない |

`equal_information_pooled_fit`と新ruleは、状態生成、group spectra、Hamiltonian exponential、
PF state action、proxy点、cacheを一つずつ共有する。この比較で古典情報費用を一致させる。

### 5.5 Phase Aの計数とfreeze

一条件あたり、CISD状態生成1、group-spectrum build 1、短時間proxy最大34、固定relative
proxy 5、拡張proxy最大8、合計proxy最大47とする。4条件合計の最大は状態生成4、
group-spectrum build 4、proxy/Hamiltonian exponential/PF state action各188である。

Phase Aは`predictions.json`、`prediction.sha256`、`PHASE_A_FROZEN.json`を作る。protocol hash、
source audit、sanitized-input hash、4 strategyの選択、proxy取得prefix、Phase B座標計画を含め、
commit・originへpushするまでPhase Bを開始しない。freeze後の科学的変更はrunをinvalidatedとして
保存し、新protocol versionを必要とする。

## 6. Phase B：凍結後だけdirect truthを採点

全4条件で、`current_m3`の次の9点を直接計算する。

`0.50, 0.65, 0.80, 0.95, 1.10, 1.25, 1.40, 1.55, 1.70 t_ana`

これに現行baselineの選択時刻を一条件最大1点加える。各条件で全採点時刻の最小値を
`t_min`とし、新規anchorを`0.5 t_min`に置く。絶対時刻を`rtol=2e-12, atol=1e-14`で
deduplicateする。

- candidate grid：4×9 = 36点。
- 現行selected time：最大4点。
- 新規anchor：4点。
- 新規direct truth：最大44点。
- 第一研究direct cache再利用：0。

anchorだけexact-ground overlap最大の枝を初期化し、以後の全点は時刻昇順にprevious-vector
overlap最大で追跡する。各点でexact-ground overlap最大枝との一致も監査する。

数値gateは固有対残差`<=1e-10`、unitarity Frobenius残差`<=1e-10`、anchor ground overlap
`>=0.9`、全追跡点のprevious/ground overlap`>=0.9`、phase gap`>1e-8 rad`、branch disagreement
0である。不合格時は`failed_numerical_validation`として停止し、閾値を緩めない。

## 7. 採点

主判定を次に置く。

1. `accuracy_target_miss_count`と`unsafe_execution_count`。
2. execution coverage、extension coverage、consistency rejection数。
3. 条件別・合計の凍結Pauli rotation予算。
4. 固定current_m3 9点grid最小に対するdirect selection regretとfrozen-budget regret。
5. `equal_information_pooled_fit`に対するregret差。
6. 状態生成、明示的Hamiltonian-vector作用、Hamiltonian exponential、PF state action、
   group spectrum、proxy点の数と秒数。
7. Phase B direct点数、GPU秒数、CPU/GPU peak memory。

candidate-grid oracleは9個の直接点の有限集合最小であり、continuous-time global oracleとは
呼ばない。補間しない。反実仮想は別表にし、成功判定へ使わない。

## 8. go/no-goと終了判定

Phase Aへ進むには全source hash、全unit test、local/GPU-server-wide independence search、
新規output確認が必要である。server側でLiF/HClの既存数値を発見した場合は条件を交換せず停止する。

Phase Bへ進むには、Phase Aのtruth access countが全て0、predictionとcoordinate planがcommit・
push・hash固定済み、direct計画が44点以下、runtime cacheが同一protocol/prediction由来であることを
要求する。

`complete_with_benefit`には次をすべて要求する。

- source/numerical gate全合格。
- 新ruleのunsafe execution 0、execution coverage 4/4。
- 少なくとも1条件で`0.5 t_ana`を超える選択。
- 合計凍結予算が現行fallbackの90%以下。
- 新ruleの平均regretが同情報費用baselineより小さい。
- 新ruleの最大regretが同情報費用baseline以下。
- 条件別regret悪化が最大0.10以下。
- 新ruleと同情報費用baselineの古典情報countが完全一致。

数値gateは通るがbenefit条件を一つでも満たさなければ`complete_no_benefit`とする。これは有効な
negative resultであり、LiF/HClを見た後に閾値、候補時刻、state truncation、geometry、basis、
gammaを変えない。

## 9. 必要なcache・pickle・成果物

既存の開発用sourceは次を読み取り専用で使う。

- H01：`artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/`。
  server-side `cache/*.pkl`はsource identityと見積り用であり、独立LiF/HCl入力へ流用しない。
- P03：`artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/`。
  `raw/`と`fine/raw/`は開発truth専用で、Phase Aから隔離する。
- S0 v1.1、S4 v1.1、regret decomposition、completion analysis、paper evidence/figure manifests。

独立評価4条件の既存pickleは0を要求する。Phase Aで新しく作るsystem/proxy/component cache、
Phase Bで作るdirect cacheは`.runtime/`だけに置き、protocol hashとprediction hashをcache keyへ
含める。pickle、`.npy`、`.runtime`はcommitしない。第一研究direct cacheは再利用しない。

## 10. 事前資源見積り

既存の8-active-orbital条件では、restricted dimension 1568、81–99 groups、system preparation
7.45–11.37秒、proxy point約0.18秒、CPU peak約0.75 GiBだった。current_m3 direct pointは
median 4.19–4.84秒、最大11.75秒、GPU maximum 701 MiBだった。

LiFはより大きいsectorになり得るため、次の幅を予約する。

| 区間 | 時間 | peak memory |
|---|---:|---:|
| Phase A（4条件、CPU、単一process） | 2–10分 | CPU 1–4 GiB |
| Phase B（最大44 direct点、単一GPU） | 8–30分 | GPU 1–4 GiB、CPU 1–4 GiB |
| tests・監査・manifest | 2–10分 | CPU 1–2 GiB |

これは停止用上限ではなく事前見積りである。GPUは空き8 GiB以上をpreflight条件とする。
実測では状態生成、group spectra、proxy、direct、testを分けて記録する。

## 11. このtaskの停止点

このprotocol-preparation taskでは、新規LiF/HCl生成、Phase A、Phase B、direct truth、追加分子、
別PF、S5を実行しない。protocol、hash、source/leakage audit、boundary test、GPU実行指示を
commit・pushした時点で停止する。
