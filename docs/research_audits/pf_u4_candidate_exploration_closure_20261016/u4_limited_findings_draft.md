# U4限定成果草案：direct grid最適時刻と小系・系族・格子への依存

**2026-10-16 JST。独立した草案。** ユーザー採択済みU4-C4に従い、U4-C1相当の既存補助成果を保存する。第一研究本文・図・caption・claim ledgerへは統合していない。以下の数値は固定reportからの引用であり、新しい再fit・再集計・最適化・ランキングではない。[decision_record.md](decision_record.md)

## 1. 対象量と既存計算の範囲

旧U4はH-chain、`4th(m5_best)`（以下m5）と`8th(Morales-Y8m10b)`（以下Y8）について、direct PF固有位相誤差を使う費用proxyの離散最小時刻を比較した登録済みretrospective小系検証である。even neutral singlet H2/H4/H6とodd cation triplet H5/H7は別の物理系族であり、一つのサイズ回帰へ混ぜない。grid決定前に既存H-chain結果を見ており、独立holdoutではない。[PROTO] [PROTOJSON]

原protocolの費用定義は

\[
C_{\mathrm{direct}}(t)=\frac{\beta N_{\exp}}
 {t\,[\epsilon_E-|\delta E_{\mathrm{direct}}(t)|]},\qquad
\epsilon_E=0.00015936001019904\ \mathrm{Ha},\quad\beta=1.2.
\]

`N_exp`は原実装のPF一stepに対応する費用因子である。`|delta E_direct| >= epsilon_E`はinfeasibleとして有限費用を付けない。これはrepositoryのcontinuous QPE precision-allocation proxyであり、状態準備や係数・truthの情報取得費、完全なfault-tolerant runtimeを含む費用ではない。[PROTO] [PROTOJSON] [FITCODE]

探索点は`0.20 t_ana`から`1.70 t_ana`まで`0.05 t_ana`刻みの31点。`t_grid*`はこの範囲の有限費用を持つgrid点から選ばれた最小であり、全正時刻における連続大域最適値ではない。`t_ana`は正規化と有限探索域の定義に使われ、grid内部のdirect最小を解析的に選ぶものではない。[PROTO] [GRIDCODE]

branchは最初の点でexact ground overlap最大をseedとし、時刻の昇順にprevious vectorとのoverlap最大で追跡する。原gateは全点でcontinuous枝とmaximum-ground枝のshift差`<=1e-10 Ha`、unitarity/Schur残差`<=1e-10`、選択最小点ground overlap`>=0.9`、探索域端点の最小は不適格。previous overlap`<0.5`はwarningで、単独の不合格条件ではない。このU4規則を、別sourceのbranch規則やAR発生判定と同一視しない。[PROTO]

## 2. 先頭誤差モデルの解析時刻：静的に確認できた定義

既存関数`analytic_optimal_time(alpha, order, epsilon_e)`は、正の`alpha`と形式次数`p=order`に対して

\[
t_{\mathrm{ana}}=\left[\frac{\epsilon_E}{(p+1)\alpha}\right]^{1/p}
\]

を返す。これは原sourceの式を再掲したもので、新たな最適時刻定理の証明ではない。m5は`p=4`、Y8は`p=8`である。[TIMECODE] [PROTOJSON]

`sweep_direct_scaling_h6_h7.run`は`_fit_short_time`の`fixed_order_alpha`をこの関数へ渡す。fit helperはprepared stateとenergyを用い、

\[
g_0(t)=\frac{\operatorname{Im}\!left[
e^{-iE_0t}\langle\psi_0|U_{\mathrm{PF}}(t)|\psi_0\rangle\right]}t
\]

の絶対値を短時間の入力とする。`5e-12 Ha`を越える点を用い、形式次数を固定した係数を`loglog_average_coeff`で取得する。既定fit時刻はm5が`0.15–0.8 Ha^-1`、Y8が`0.8–1.6 Ha^-1`の各9幾何間隔点である。free-order fitは別fieldに保存される。[SWEEPCODE] [FITCODE] [RUNV11]

したがって、ここでの`alpha`は既存の**exact-state overlap proxyに対する短時間固定次数fit係数**である。厳密なTaylor係数を独立取得したことや、全有限時刻でdirect対象固有位相誤差とproxyが等しいことを意味しない。U4の`direct`は選択・費用採点側のPF固有位相評価を指し、正規化入力までoracle-freeであることを表さない。

| 確認できた範囲 | 保留する範囲 |
|---|---|
| 親protocol→v1.1 runner→direct sweep→短時間fit→`analytic_optimal_time`というsource上の呼出し経路 | 元計算の全入力・数値を今回再実行して再現したという主張 |
| ordering-aware sector helperがprepared state/energyを用い、残差条件に応じてsector groundを再対角化するsource | state/Hamiltonianの全取得費、fit・direct探索・backend準備を含むend-to-end会計 |
| GPU interimも同じdirect sweep・既定fit時刻を呼ぶsource、source manifest内の関連hash一致 | GPU/CPUの異なるrunのfit係数を同一の保存値とみなすこと |
| `t_ana`の式、fitのproxyとfloor、有限探索域への使い方 | 未知系で同等情報を安価に得られる保証、低費用の前向き時刻予測則 |

根拠：[RUNV11] [SWEEPCODE] [FITCODE] [SECTORCODE] [GPUCODE] [GPUSOURCE]。コードはtextとして静的確認しただけで、import・実行、private state/matrix読取り、係数や取得費の新計算は行っていない。**`t_ana`入力経路の静的確認と、取得費を含む総費用の未確認は両立する。** 未確認費用を0と仮定しない。

## 3. 系族別に保存するm5の結果

### 3.1 even neutral singlet：旧partial report

| 系 | `t_ana`［Ha⁻¹］ | `t_grid*`［Ha⁻¹］ | `t_grid*/t_ana` | 保存された1%区間［相対時刻］ | 元row status |
|---|---:|---:|---:|---|---|
| H2 | 3.39638459 | 4.75493843 | 1.40 | [1.400, 1.400] | `scorable` |
| H4 | 2.31036235 | 3.46554352 | 1.50 | [1.500, 1.500] | `scorable` |
| H6 | 2.08465064 | 2.81427836 | 1.35 | [1.350, 1.350] | `scorable` |

原報告の引用：[OLD]。m5のpower-law LOO最大誤差`4.034%`、constant LOO最大誤差`44.242%`と、`small_system_predictable_requires_H8_holdout`という当時の分類を保存する。これはH2/H4/H6内の事後的な小系支持であり、未知H8への前向き予測の検証ではない。今回C4を採択したため、分類名にあるH8 holdoutを実施ToDoへ変換しない。

### 3.2 odd cation triplet：後続H5/H7 interim

| 系 | `t_ana`［Ha⁻¹］ | `t_grid*`［Ha⁻¹］ | `t_grid*/t_ana` | 保存費用比 `cost(t_grid*)/cost(t_ana)` | 元row status |
|---|---:|---:|---:|---:|---|
| H5 | 2.59399493279 | 3.50189315927 | 1.35 | 0.624886839724 | `scorable` |
| H7 | 2.17422823128 | 3.15263093535 | 1.45 | 0.638511699204 | `scorable` |

原報告の引用：[INTERIM]。各PF・系31点の後続interimにH7結果がある。旧partialの`not_executed_user_stop`は当時の記録として残し、最新の実行状況には使わない。odd-familyのH5/H7/H9 fitは未実施である。

H5の旧partialと後続interimでは物理時刻の表示値が少し異なる。表3.2はinterimの値だけを引用し、旧H5の`2.59399773 / 3.50189693`と混ぜない。parity amendmentは同一物理時刻でのCPU/GPU比較を規定しており、別runの正規化時刻差をなかったことにはしない。[OLD] [INTERIM] [GPUPARITY]

費用比約`0.625 / 0.639`は、このdirect gridで得られた事後的な費用proxyの比較である。情報取得費や状態準備を含む総費用削減、新しい実装可能な資源削減法、未知サイズでも使えるselectorを確立したとは記述しない。

## 4. Y8の不成立とgate不適格を別に保存する

even H2/H4/H6のY8では`t_grid*/t_ana = 1.15 / 1.35 / 1.25`が保存されているが、power-law LOO最大誤差`41.515%`、constant LOO最大誤差`38.752%`で、原分類は`no_predictable_power_law_on_current_sizes`である。m5の小系傾向からY8を含む一般的なサイズ則や高次数PFの一律優位へ拡張しない。[OLD]

H5/Y8は後続interimでも`not_scorable_gate_failure`で、最大branch差は保存値`0.0134158260484 Ha`。失敗artifactは保持するが、成功最適時刻・成功費用比・成功サイズ回帰へ含めない。backend parityが通ることと科学的branch gateが通ることを区別する。[INTERIM] [GPUPARITY]

H7/Y8は後続interimで`scorable`、31点、`t_grid*/t_ana=1.1`である。これをH5/Y8の失敗を救済する根拠や、Y8サイズ則の独立検証にはしない。[INTERIM]

親partialのstatus `failed_numerical_or_boundary_validation`とdecision `not_scorable_due_to_numerical_or_boundary_gate`、後続interimの`complete_H5_H7_interim_scope`はそれぞれのscopeの原記録として保持する。scorableな個別rowがあっても親statusを書き換えない。[OLD] [INTERIM]

## 5. 零交差依存・有限grid・連続最小の区別

原protocolの1%区間は、保存grid上で`cost <= 1.01 × minimum_cost`を満たし、選択最小点を含む連結成分である。零交差との関連も、符号付きdirect誤差の隣接点間の符号変化区間との交差を記録する規則である。even系m5の3 rowには`zero-crossing assisted=True`が保存されている。[PROTO] [OLD]

この離散診断から、正確な連続零点、連続最小点の存在・一意性・大域性、1%許容幅を証明したとは言えない。単一grid点の1%区間を幅0の連続区間と読み替えない。相殺近傍を利用した事後最小という限定を付ける。

後続A6はH4・m5_bestについて、**別の401点grid/run**の元最小点と左右保存点の間を細分化した固定局所検証である。以下は2026-10-07報告§4の引用で、今回の再集計ではない。[EXP]

| A6での比較 | 時刻［Ha⁻¹］ | 必要費用［百万回転］ | 元の固定予算／必要費用 |
|---|---:|---:|---:|
| 元401点最小 | 3.5175172132783867 | 8.946045 | 1.983521 |
| 追加後の局所9点最小 | 3.5083978485276024 | 8.593978 | 2.064779 |

A6原報告は必要費用が`3.935%`低下したと記す。零交差近傍の刻みが離散最小の具体値に影響する一方、元固定予算が候補内必要費用の約2倍という傾向は残った。A6自体も連続最適化・根探索・探索域外確認をしていない。[EXP]

この結果は格子依存を示す別runの証拠として参照する。旧U4の31点gridへA6の点や数値を追加して一つの実験にしたり、U4のH4値をA6値で上書きしたりしない。A6を用いて旧U4のサイズ則を再fitすることもしていない。

## 6. 既存研究・先行研究との重複

2026-10-16の既存完結性監査§5とmap§4は、Morales等 `arXiv:2210.15817v3`の有限時間関数による比較・短時間則の適用限界、Mehendale等 `arXiv:2312.13282v3`の分子摂動推定・時刻選択との重複を整理している。ここでは**その固定監査に記録された対応範囲**を引き継ぎ、今回新しい全文レビューや網羅的新規性調査を行ったとは記述しない。[AUDIT] [MAP]

有限時間で先頭則からの解析時刻がdirect grid最小と異なることや、費用proxyが時刻に依存すること自体を新しい独立中心成果として数えない。U4の保存価値は、本repositoryの指定PF・系族・grid・gateにおける限定比較である。有限時間校正の安全性と効率、保存gridと連続oracleの違いは第一研究の既存中心claimにも含まれる。[CLAIMS]

U1の理論補論、U3/H05の取得法補論と本草案は既存補助資料として保持する。重複を理由に原文を移動・削除・統合していない。本草案を独立したサイズ予測則、新しい資源削減法、一般的な最適時刻定理、独立新規論文の成立証明として扱わない。[U1] [U3]

## 7. 未実施・未確認事項と終了境界

| 項目 | 現在の扱い |
|---|---|
| U4のH8/H9 direct最適時刻検証 | 未実行を保持。第二研究のH8/current_m3等の別実験で代用しない |
| odd-family H5/H7/H9のfit、未使用系での前向き検証 | 未実施。H5/H7の2点を新しい回帰へ変換しない |
| `t_ana`の情報取得費、状態準備・校正込みの総費用 | source上の定義と入力経路は§2の限りで確認。総会計は未確認。0費用と仮定しない |
| 連続最適時刻・一般サイズ則・新しい剰余やbranch保証 | 未証明。新しい証明・反例・実装で埋めない |
| Claude `レビューoutter(8).md` | 原文未取得・未確認。ユーザー採択事項と固定資料を根拠にする |
| 本原稿への配置・統合、第一研究の論文化 | 将来の別編集案件。今回実施・承認していない |

第一研究S0〜S4完了とS4否定結果、U1/U3のSTOP、FS-R1 Phase B未承認、第二研究その他のscopeを維持する。[SYNTH] [CLAIMS] [U1] [U3] [B0GO] U4-C2/C3と新テーマ探索を開始せず、4資料の公開・照合後Mandatory STOPとする。

<!-- fixed-source-references -->

[AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_audit.md
[B0GO]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/GO_NO_GO_FOR_PHASE_B_PRODUCTION.json
[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[EXP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/19362c23ccdc16b6ad0ff547cc363e138a3930d2/docs/research_outcomes/20261007/validation_expansion_results.md
[FITCODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/run_large_hchain_moment_phase.py
[GPUCODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/run_gpu_hchain_direct_h5_h7.py
[GPUPARITY]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/run_gpu_hchain_direct_h5_h7_v1_2.py
[GPUSOURCE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/server_hchain_direct_optimal_time_h5_v1_2_20260927_e82b6ae/source_manifest.json
[GRIDCODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/run_hchain_direct_optimal_time_scaling.py
[INTERIM]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/server_hchain_direct_optimal_time_h5_v1_2_20260927_e82b6ae/report.md
[MAP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/open_question_and_evidence_map.md
[OLD]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961/report_partial_v1_2.md
[PROTO]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/hchain_direct_optimal_time_scaling_protocol.md
[PROTOJSON]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/hchain_direct_optimal_time_scaling_protocol.json
[RUNV11]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/run_hchain_direct_optimal_time_scaling_v1_1.py
[SECTORCODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/hchain_direct_sector_v1_1.py
[SWEEPCODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/review_response/sweep_direct_scaling_h6_h7.py
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7f0b30d215e8094c95ae895b9469a04180e2385e/PF_first_study_final_synthesis_20260925.md
[TIMECODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/src/trotterlib/cost_validation.py
[U1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[U3]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/56531350d2b931e5cce753c2474e2401094b0eea/docs/research_audits/pf_u3_h05_e4_closure_20261016/decision_record.md
