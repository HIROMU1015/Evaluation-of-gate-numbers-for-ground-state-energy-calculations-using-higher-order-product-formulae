# Codexへの初回指示：R1後の研究再設計とP-SPEC-6仕様化

## 今回の作業範囲

**今回実行するのは、読み取り・既存値の算術再集計・文書作成だけ。新しい科学計算、PF対角化、proxy評価、状態生成、候補選択、R2実行は行わない。**

上位方針は同梱の`PF_research_reorientation_after_R1_20260928.md`を参照する。汎用validatorを自動的に開発せず、有限時間echoと目的PF固有位相の差に必要なスペクトル情報と費用を主題とする案を仕様化する。

## 1. 基準identity

- repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- source branch: `research-direction-review-after-d2r-r1-20260928`
- evidence source commit: `a134ba3950a521225a14c46943d0dbe469425e00`
- planning bundle commit: D0のprotocol・runner・testを含む別commitとして固定し、D0実行時に記録する
- R1 result: `2cb78527ab8fd1fe99bffbdae46a5dfac1e325a3`
- R2: `r2_authorized=false`

`main`や最新tipへ勝手に読み替えない。branchが進んでいても、このcommitのsourceを読み取り、差分の存在だけ報告する。元worktreeへuncommitted変更があるなら、それを消さない。新作業branchはユーザーが作業を許可した場合に独立して作る。main merge、history rewrite、既存artifactの上書きはしない。

## 2. 読むsource

- `review_response/pf_research_direction_review_materials_20260928.json`
- `docs/pf_research_status_after_d2r_r1_20260928.md`
- `review_response/pf_candidate_validation_r1_protocol.json`
- R1 artifact `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/` のreport、coordinate CSV、decomposition CSV、decision、resource/source/manifest。
- 第二研究Phase Aのpredictions、第二研究Phase Bのdirect_points.csvとstrategy_scoring.csv。
- `review_response/second_study_safe_time_domain_protocol.json`
- R0のfailure_ledger.csv、selected_coordinate_plan.csv。
- `docs/pf_data_use_ledger.md`

既存のhash・数値監査を無目的に全面再実行しない。必要なsource hash照合、行数・joinキー・採点恒等式の再確認はread-onlyで行う。

## 3. まず既存値だけから確定すること

### 3.1 R1の証拠境界

第二研究v1の`complete_no_benefit`を保持する。R0/R1はpost-hoc development。16strategy行は4条件・10座標からなる非独立な集計である。

主要分類model 6/state 4/proxy 2/mixed 4は固定規則の結果として保持し、新方式のrisk判定へ自動転用しない。元のallowance、signed discrepancy、絶対誤差の過小評価、guard premiumを別列にする。

### 3.2 新しく作るread-only派生表

全10座標について、保存値から次を計算する。

- `local_cisd_gamma_required = (epsilon - abs(g_cisd))/(epsilon - abs(delta))`
- `local_exact_gamma_required = (epsilon - abs(g_exact))/(epsilon - abs(delta))`
- 分母が非正ならfinite budget不能として扱う。
- `arg_exact_echo/t - imag_exact_echo/t`
- signed gap `g_exact-delta`
- absolute-error gap `abs(delta)-abs(g_exact)`
- 元のstrategy budgetとの差。ただし新しい性能結果とは呼ばない。

期待される整合性の目安：最大local-CISD倍率は約1.098139、HCl伸長0.65では約1.016655、arg/Im差は10点で最大約1.63e-11 Ha。これらへ数値を合わせ込まない。不一致ならsource・式・値を報告する。

`gamma=1.10`はpost-hocな比較材料であり、採用パラメータや独立に検証された安全係数へ変えない。

### 3.3 HClの対照としての役割

保存metadata/protocolから18電子・10空間軌道、Nalpha=Nbeta=9、100次元を確認する。各スピンにvirtualが一つで、同じsymmetryの励起空間ではCISD切断が実質ないことを説明する。

RCISDのspin制約、solver収束、全スピンのground保証を同一視しない。新しいFCI/CISD計算はしない。HClのnear-exact性を、一般近似状態の低コスト性の実証に使わない。

## 4. P-SPEC-6を「未実行protocol」として設計

### 科学目的

HClの既存6選択点で、ground-state spectral measure `{phase_j,p_j}`を使い、echoのnon-target寄与と目的固有phaseの差を定量化する。高いground overlapでも残る微小biasが、資源予算に対しどれだけ重要かを示す。

### 固定する座標

R1 protocolのtime_hexをそのままコピーし、HCl equilibriumの0.5/0.65/0.8とHCl stretch150の0.5/0.65/0.8の6点だけにする。LiFの新規計算、追加時刻、追加PF、追加状態法は入れない。

### 将来許可された場合の計算上限

- new direct coordinate: 0
- rebuild existing-coordinate full U: at most 6
- eigendecomposition at existing coordinates: at most 6
- regenerate same-H exact ground state: at most 2
- new Hamiltonian: 0
- new state approximation method: 0
- new proxy-only sampling campaign: 0
- optimization / threshold tuning: 0

既存full-spectrum cacheがあればhash確認後に使う。無ければ上記再計算を明示的に許可された後だけ行う。同じ座標での再対角化を「新規direct/eigenpair計算0」と報告しない。

### 分解式

`p_j=|<u_j|0>|^2`、`delta=tilde E_0-E_0`として、

`g_exact-delta = sin(t*delta)/t-delta + sum_{j!=0} p_j*(sin(theta_j-E0*t)-sin(t*delta))/t`

を用いる。非対象phaseは円周上の位相でよい。全固有値をprincipal logでenergy順に並べて対象枝を選ばない。

対象枝のidentityは保存phase/shiftとoverlapで照合する。縮退／準縮退ではprojector weightを使い、cluster規則をpre-freezeする。

### 保存・評価

- normalization, unitary, eigenpair, phase match, complex echo reconstruction。
- 単一phase非線形項、non-target signed寄与、absolute-underestimate。
- total leakage q、`2q/t`の上界とtightness。
- K=1/2/4/8/allのoracle compression diagnosticと未保持重み上界。
- 元予算allowanceと、予算倍率を変えた場合の必要精度を別に記録。
- classic wall-time, peak memory, full-PF build/eigenpair count, cache reuse。

top-Kは次の二定義を固定し、混同しない。

- `weight_ranked`: 非対象clusterを `p_j` 降順。
- `oracle_contribution_ranked`: 実際の `|p_j[sin(phi_rel,j)-sin(t*delta_0)]/t|` 降順。oracle診断専用。

同値時は重み降順、wrapped phase昇順、cluster index昇順。Kは`1/2/4/8/all`。actual omitted signed residualと`2*q_omit/t`の保守的上界を別々に保存する。座標allowanceは同じcondition/time_hexを選んだ元strategyのallowance最小値とする。top-Kをtruthから選ぶ評価は「必要情報の圧縮可能性の診断」であり、実装されたcheap estimatorではない。

### Gate

数値gateは実行前に固定する。phase clusterは円周距離`<=1e-8 rad`、数値残差は原則`1e-10`（weight normalization、eigenpair、unitarity、exact-ground、complex echo、energy reconstruction、保存direct shift、保存target overlap）、phase gapは`>1e-8 rad`、branch disagreementは0。gate失敗をthreshold緩和で救済しない。

低次元圧縮は、6点すべてでK<=4のactual omitted residualがallowanceの25%以下、かつ保守的`2*q_omit/t`がallowance以下の場合だけ成立とする。prototype候補にはさらにweight-rankedでの成立と、truth-free route（subspace dimension<=8、PF/H作用各<=8/座標、peak memory<=4 GiB、full dense solve/direct truth入力なし）が必要である。D1はCPU単一process、BLAS thread各1、総wall time<=1800秒、GPU操作0。

科学gateは「再構成が一致した」だけで合格にしない。pilot後の分岐は以下。

1. 情報が圧縮可能かつtruthなし取得の経路と計算上限がある → 一方式のprototype設計。
2. 情報が高価／広帯域で明確な限界がある → 定量限界・構成例の研究。
3. 標準恒等式以上の知見がなく方法の見込みもない → この方向を閉じる。

## 5. 今回の成果物（提案path）

- `docs/pf_research_direction_after_r1_revised_20260928.md`
- `review_response/pf_spectral_information_pilot_protocol_draft.json`
- `review_response/pf_spectral_information_pilot_protocol_draft.md`
- `review_response/pf_spectral_information_pilot_authorization.json`
- `artifacts/pf_r1_readonly_design_summary_20260928/` の派生表、source manifest、短いreport。

authorizationには以下を明記する。

```json
{
  "status": "protocol_draft_no_scientific_execution",
  "r2_authorized": false,
  "spectral_pilot_authorized": false,
  "new_scientific_calculation_count": 0,
  "closed_second_study_reclassification_authorized": false,
  "holdout_execution_authorized": false,
  "new_pf_search_authorized": false
}
```

将来pilotが別途承認されても、旧protocolを上書きせず、独立したpilot authorizationを作る。

## 6. まだ作らないもの

- 全条件対応のadaptive selector。
- 新しいCISD thresholdやmarginの最適化。
- 大規模BCH / effective-Hamiltonian展開。
- matrix-free projected spectral solverの本実装。
- PF coefficient optimization。
- 新しいholdout分子の結果。

相似変換`U_lambda=V_lambda U V_lambda†`によってphaseを保ちechoだけを変える案は、理論対照として文書に記すだけ。gate cost同等・新PF成功・oracle-free改善を主張しない。

## 7. 最終報告

次を短く報告して停止する。

- 固定sourceを確認できたか。違うcommitやcacheへの置換がないか。
- 保存数値と算術派生の整合性。
- P-SPEC-6が取得する情報、上限、gate、3分岐。
- 第一論文・旧第二研究・R1のstatusを変更していないこと。
- R2／pilotの実行が未許可であること。

既存の陰性結果を削除せず、新しい分子や時刻を追加して救済しない。今回の提出をもって科学計算へ自動移行しない。
