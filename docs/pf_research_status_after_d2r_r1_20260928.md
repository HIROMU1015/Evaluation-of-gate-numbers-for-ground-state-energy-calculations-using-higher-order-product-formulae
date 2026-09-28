# D2R R1完了時点のPF研究状況

最終更新：2026-09-28

この文書は、研究方針を練り直すための現在地を示す入口である。第一・第二研究の閉鎖判定と、閉鎖後に行ったD2R R0/R1事後原因分離を区別する。R1は方法設計用の事後診断であり、独立ホールドアウト評価ではない。

## 現在の停止位置

- 第一研究：固定protocolに従い`complete_no_benefit`で完了。既存集合で再調整しない。
- 第二研究safe-time-domain：固定4条件・42 direct coordinatesの一回評価を`complete_no_benefit`で完了。予測、threshold、候補時刻、PFを結果後に変更していない。
- D2R R0：第二研究の16 strategy-condition行からfailure ledgerと10 selected coordinatesを固定。
- D2R R1：その10座標だけで誤差原因を事後分解し、`r1_complete_stop_for_research_direction_review`で完了。
- R2：`r2_authorized=false`。新方式、新座標、新分子、新PF、追加direct truthは開始していない。

したがって次の作業は計算ではなく、R0/R1の証拠を使った研究目的・方法・独立評価設計の再決定である。

## 証拠の階層

| 層 | 証拠 | 扱い |
|---|---|---|
| 閉鎖済み評価 | 第二研究Phase A/B | 事前固定した独立4条件に対する正式結果。判定は`complete_no_benefit` |
| 読み取り専用整理 | R0 failure ledger | 閉鎖済み結果からの派生。新規科学計算なし |
| 事後開発診断 | R1 cause decomposition | 同じ4条件・既存10座標で原因を分解。次方式の設計根拠には使えるが、独立な有効性証拠には使わない |
| 未実施 | R2以降 | protocolも実行許可も未固定 |

## 第二研究の正式結果

第二研究では`current_m3`と`multiple_window_consistency`だけを固定し、4条件を評価した。全source・数値gateは合格したが、multiple-window ruleは4条件中3条件で安全、equal-information baselineは2条件で安全だった一方、平均・最大selection regret、unsafe execution 0、条件別regret増加上限を満たさなかった。

- 正式判定：`complete_no_benefit`
- multiple-window aggregate frozen budget：`10,471,889,449.41`
- current fallback比：`0.8933806671`
- equal-information比：`1.2526414181`
- multiple-window mean/max selection regret：`0.714556 / 1.486727`
- equal-information mean/max selection regret：`0.487379 / 1.036689`
- 数値gate：全件合格、branch disagreement 0
- 結果後の再調整：0

このnegative resultは変更しない。R1は判定の再採点ではなく、次の研究方式を選ぶための原因分離である。

## R0で固定した問題

R0は16 strategy-condition行を再計算なしで整理し、unsafe 6行、重複除去後10 selected coordinatesを固定した。

| 条件・strategy群 | R0の観測 |
|---|---|
| LiF平衡・4 strategy | required/frozen比`1.5686--1.8044`、allowance比`37.25--45.58`の大きな不足 |
| HCl平衡・current fallback | required/frozen比`1.00591`、allowance比`1.58777`の小さな不足 |
| HCl伸長・equal-information | required/frozen比`1.00662`、allowance比`1.65776`の小さな不足 |

## R1の固定分解

各selected coordinateで次を固定した。

\[
f_{\mathrm{model}}(t)-\delta_{\mathrm{direct}}(t)
=
\underbrace{f_{\mathrm{model}}(t)-g_{\mathrm{CISD}}(t)}_{\text{model / extrapolation}}
+
\underbrace{g_{\mathrm{CISD}}(t)-g_{\mathrm{exact}}(t)}_{\text{state substitution}}
+
\underbrace{g_{\mathrm{exact}}(t)-\delta_{\mathrm{direct}}(t)}_{\text{proxy--eigenvalue}}.
\]

16 strategy行の主要分類はmodel 6、state 4、proxy--eigenvalue 2、mixed/none 4だった。全行のclosure residualは0だった。

### 条件別に直接言えること

- LiF平衡の大失敗はmodel/extrapolationが主因である。model成分は元allowanceの`33.33--40.14`倍、state成分も`3.97--5.52`倍で二次的にmaterial、proxy--eigenvalue成分は`0.047--0.086`倍だった。exact-local counterfactualは4/4安全で、主修正対象は選択時刻でのmodel推定である。
- LiF伸長ではstate substitutionが全4 strategyで支配した。state成分はallowanceの`4.98--5.38`倍、proxy--eigenvalue成分は`0.013--0.015`倍だった。ただし元の4行はいずれもsafeであり、「失敗原因」ではなく安全例に残る潜在誤差構造である。
- HCl平衡current fallbackの小さな不足は単一成分の2倍dominanceを満たさず、model `0.945`倍とproxy--eigenvalue `0.643`倍の混合だった。state substitutionは無視できる大きさだった。
- HCl平衡でmultiple-windowが選んだ`t/t_ana=0.65`は、model成分0、state成分ほぼ0、proxy--eigenvalue成分`0.310`倍で安全だった。少なくともこの成功はCISD誤差の偶然相殺ではない。
- HCl伸長でequal-informationが選んだ`t/t_ana=0.65`の失敗はproxy--eigenvalue成分が`4.774`倍で支配し、model/stateはほぼ0だった。multiple-windowが最初の失敗後に拡張を止め、`t/t_ana=0.5`へ戻った判断はこの観測に整合する。

local counterfactualの安全数はCISD proxy利用で11/16、exact-state proxy利用で15/16だった。exact stateへ置き換えてもHCl伸長equal-informationの1行は安全にならず、state精度だけでは全失敗を解決しない。

## R1の計算・identity gate

- Phase A runtime：56 files、113,469,289 bytes、全件byte-identical
- original system cache reuse：4
- Hamiltonian/CISD regeneration：0
- exact ground states：4、最大residual `1.0883585523354841e-13`
- coordinate rows：10、strategy decomposition rows：16
- saved CISD proxy reuse：5、新規不足座標CISD proxy：5、新規exact-state proxy：10
- 新規direct truth：0、full PF unitary：0、GPU operation：0
- source override：portable test 1件だけを両hash固定で認証、未列挙差分0
- pre/post focused：各36 passed
- pre/post full：各320 passed、既知の任意依存`pennylane`だけ1 skipped

ローカルHamiltonian再構築は固定11点bridgeの4点で`1e-10 Ha`を超えたため停止し、その失敗を隠さず監査として保存した。R1本計算では元Phase A runtimeを全ファイル照合して使い、代替再構築はしていない。

## 現時点の有力な次情報

R1だけから一種類を選ぶなら、既存HCl selected pointsにおけるPF固有ベクトル重なり・固有位相branch identityが第一候補である。これは、exact-state echo proxyと追跡PF固有値の差がどの物理・数値機構から生じるかを直接切り分けるためである。

ただしこれはR2実行指示ではない。次の検討では少なくとも次を比較する。

1. 選択候補時刻でのlocal model recalibration。
2. LiF向けstate-sensitive calibration。
3. HCl向けeigenvalue寄りsurrogateまたはbranch-aware spectral diagnostic。
4. 不確かさを明示したbudget allocationまたはrobust decision rule。
5. 条件別に取得情報を変えるadaptive information acquisition。

採用方式、情報量、成功基準、development/holdout分離を事前固定するまでは新しい数値評価へ進まない。

## 解釈上の制約

- R1は同じ4条件と結果を見た後の10座標を使う事後診断である。
- 16行は独立標本16件ではなく、4条件内で座標を共有するstrategy行である。
- component attributionは固定分解式、materiality、2倍dominance規則に依存する。
- local CISD/exact counterfactualは「そのproxyを使えば全方法が有効」という外部妥当性を示さない。
- HClで観測したproxy--eigenvalue gapの機構はまだ確定していない。
- R1を用いて第二研究の`complete_no_benefit`を覆したり、同じ条件を新方式の独立検証に再利用したりしない。

## Git identityと読み順

- repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- review branch：`research-direction-review-after-d2r-r1-20260928`
- 第二研究Phase B result：`4691ac1ea7423d3c3f5a0496c41c98b9dcba360f`
- R0 ledger commit：`d9550641ce5e03ff2b4f465cfe7fb446a5d0ff41`
- R1 implementation：`47ef65e7ca3ed75a67fd5e485a7fb8b633c21e27`
- R1 result：`2cb78527ab8fd1fe99bffbdae46a5dfac1e325a3`
- R1 integration merge：`0339a0d8c4ea3c2d433eef26e642d92f81ab923b`

推奨する読み順は次のとおり。

1. 本書。
2. [第二研究完了報告](../review_response/second_study_safe_time_domain_completion_report.md)。
3. [R0 report](../artifacts/pf_candidate_validation_r0_20260928_05649f1/report.md)、[failure ledger](../artifacts/pf_candidate_validation_r0_20260928_05649f1/failure_ledger.csv)、[coordinate plan](../artifacts/pf_candidate_validation_r0_20260928_05649f1/selected_coordinate_plan.csv)。
4. [R1 report](../artifacts/server_pf_candidate_validation_r1_20260928_fba3383/report.md)、[10座標](../artifacts/server_pf_candidate_validation_r1_20260928_fba3383/coordinate_proxy_results.csv)、[16分解行](../artifacts/server_pf_candidate_validation_r1_20260928_fba3383/strategy_cause_decomposition.csv)。
5. [R1 decision](../artifacts/server_pf_candidate_validation_r1_20260928_fba3383/decision.json)、[resource audit](../artifacts/server_pf_candidate_validation_r1_20260928_fba3383/resource_audit.json)、[source manifest](../artifacts/server_pf_candidate_validation_r1_20260928_fba3383/source_manifest.json)。
6. [R1 protocol](../review_response/pf_candidate_validation_r1_protocol.json)と3 amendment。
7. [資料索引](../review_response/pf_research_direction_review_materials_20260928.json)。

研究方針を検討するGPTには、[専用指示文](../review_response/gpt_pf_research_direction_review_after_d2r_r1_20260928.md)をそのまま渡せる。
