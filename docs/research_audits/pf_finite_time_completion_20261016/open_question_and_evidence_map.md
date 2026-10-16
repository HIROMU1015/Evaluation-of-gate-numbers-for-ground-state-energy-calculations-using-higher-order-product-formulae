# 未解決問題と既存証拠の対応

2026-10-16 JST。監査上の候補整理であり、科学的採択・優先順位・追加実行許可ではない。分類の全体は[完結性監査](research_completion_audit.md)、作業条件は[完成オプション](research_completion_options.md)、byte identityは[provenance](provenance.json)を参照する。

## 1. 解決済み部分を取り除いた残余

| ID | 残る具体的な問い | 既存の肯定／反対証拠 | 解決された部分 | 不足する証拠 | 重複と位置付け |
|---|---|---|---|---|---|
| U1（Q07） | 相殺、D4結合、D8、物理gapが共変するとき、有限時間で低次モデルが成立する条件を区別できるか | F03の小a4・有限D4、F02のa8内部相殺、F05の最小gap非支配、HF eq/pass–stretch/fail。[F03] [F02] [F05] [HF] | 各成分の存在と役割は小系で説明済み。HF位相圧縮単独説は支持されない。A1はH6でもstate/mixedを確認。[EXP] | 使用時刻までの剰余と対象枝の連続性を含む条件、または同一H/PF等を保ち何を変えるか明確な識別比較。分子・相関・basis間の移送根拠 | 第一研究S3の補助機構に含まれるが、一般的な事前判別は未解決。独立性は未確定。C1で記述を閉じるかC3を要求するかGPT判断 |
| U2（Q13） | FS-R1でstate改善とselected-time local評価はtrue safetyを保って予算を減らすか | H4はaccuracy改善を実証。N2/CO新source4-arm predictionは凍結済み。[H4] [FSA] | source分離、数値再現契約、cold replay、B0 barrier準備は完了 | 既存protocolの12点branch ladder成立と、最終2点truthでの保存nominal budget採点。未成立なら科学判定不可 | 既存第一研究follow-upそのもの。新独立テーマに数えない。C2。Phase Bは未承認のまま。[FSB] |
| U3（Q04） | exact a4＋少数direct点／responseが未使用系でも必要精度と取得費を満たすか | H05 exact response8/8、fixed-a4 tail2点8/8。HF4/8、CISD7/8。D8対角項のみ6/8。[H05] | responseによる混合補正の小系identityと、単純fit増量が解決しないことは確認済み | 固定H05設計の未使用系評価、a4取得とD6/D8構築を含む総費用。direct点をtruth-freeと呼ばない | H05の未達境界。既存摂動推定・compact BCHとの重複が強い。C2/C3、独立論文の中心候補とするならC4との比較判断が必要。[L2] [L4] |
| U4（Q12） | direct grid最適時刻と費用を、相殺・branch warningを越えてサイズ移送できるか | even小系m5のLOO支持、Y8 power law不成立、H5/Y8枝gate失敗、H7 interim完了、A6で局所最小3.94%変化。[SCALEOLD] [SCALE] [EXP] | H7未実行という古い記録は後続で解消。H5の値はゲート不合格のまま保持 | 事前固定した未使用サイズ検証と最小近傍の頑健性。連続最適性を求めるなら別の数学的根拠 | 既存direct-scaling路線の残余。第二研究のH8/current_m3は別PF・候補契約で代用不可。C2、一般則ならC3。再開は未採択 |
| U5（Q06） | frozen/active-spaceで成立しfull-electronで破綻するモデルの条件は何か | NH3固定比較、N2/CO holdout成功、HF stretch失敗。NH3 time-grid効果は分離済み。[NH3MOD] [HOLDOUT] [NH3BR] | 「全てfit窓のせい」「項数追加で必ず救済」は支持されない | U1の条件を分子間に移す根拠。単なる分子名ラベル・post-hoc fittingでは不十分 | U1と大きく重なる。別研究候補として重複計上しない。現主claimはactive-space限定でC1完結可能 |
| U6（Q15） | HF/HCl/prospectiveでもPF側・H-reference側の絶対誤差を同じH/origin/physical branchで分離できたか | H-chain native18、G15、R36診断行ではclosure。一方HF/HCl12とprospective39はindeterminate。[EVMAP] [CORRECTION] | native H-chain closed=0は文書バグとして訂正済み。37/39互換枝診断は絶対対応の確認ではない | 欠けたabsolute identity tuple。原資料の回収で足りるか、新しいground/target情報が必要かは未確定 | 現Direction CはH-chain限定なので未完了の中心claimではない。現状はC1のscope整理／C4。穴埋めは自動ToDoにしない |
| U7（Q08/Q14） | strictなtruth-free width・branch適格性が、安い対照より有用な資源判断を与えるか | D1低次元圧縮、D2-A物理枝6/6でもbudget利益0/6、rank16/32のpoint改善後もadvantage0/9、prospective39/39 M1 abstention。[D1] [D2AUD] [EVMAP] | 既知scalar spectral分解、固定M1 packageの限界、widthとpointの違いは解決済み | 許可情報量・対象枝仮定・費用を固定した新しい十分条件／保証。一般spectral法の否定・肯定には代表法比較も必要 | 第二研究中心成果を言い換えるだけならC4。強い保証はC3。現B2/H1は非採用を維持し、新gateを設計しない。[DIRC] |

U1/U2は、GPTが残件として特に内容を確認しやすい二つである。U1は複数の既存機構証拠に対する適用条件の不足、U2は既存follow-upの明確な未採点終点を持つ。これは研究価値や採択順位の正式判断ではない。U3/U4の科学的意義は、既存手法との差と目的scopeを明確にすることに依存する。

## 2. 「未解決」として再提案しない項目

| 誤って残件にしやすい記録 | 最新の証拠／正しい扱い |
|---|---|
| NH3 dipは枝／数値問題か不明 | 後続NH3 branch auditが独立構築・3追跡規則で同一枝再現を確認。全連続時刻の大域最適性だけは未証明。[NH3BR] |
| a8混合公式が未検証 | F02で成分identityを確認済み。小係数fitの不安定性は別の識別問題。[F02] |
| exact stateならproxy差が消える | HCl D1、H4、H6 A3で非対象spectral寄与を確認済み。追加の一般論説明だけでは新研究にならない。[D1] [H4] [EXP] |
| H03 symbolic生成が依然blocker | H04 full compact D4が解消。ただしD8等とstatevectorの費用は未解消。[H04] [H05] |
| norm上位項を増やせば精度は単調改善 | H04では24曲線中13に非単調悪化。PF順位安定は剰余boundではない。[H04] |
| H7 direct optimumは未実行 | 後のH5/H7 interimに31点/PFがある。H5/Y8の失敗を成功に混ぜず、H9を含むodd fitは未実施。[SCALE] |
| D2-Aは物理的wrong branch0/6だから方法の位相回収が全失敗 | integer IDと物理枝座標の不一致監査がある。物理枝6/6、元STOP不変、資源利益0/6を別々に記載。[D2AUD] |
| H-chain reference分解が0/18 | 旧builderのstatus名判定bug。原CSVは18確認済み。訂正版を使用する。[CORRECTION] |
| H4 Outcome Cだからstate改善はrefitで消失 | total absolute error改善は残った。baseline S_under=0でstrict減少が成立しない固定Outcome C。[H4] |
| FS-C0.5のsource欠損を回収すれば同じhistorical研究を継続できる | C0.6もhistorical SHA不一致。R0でhistorical復元路線を終了し、別new sourceへ移った。新旧truthを混ぜない。[FSC06] [FSR0] |
| FS-R1 Phase Aは数値契約不足のまま | A0 v3後にproduction freezeが成立済み。現在の不足はPhase B truth採点。[FSA0] [FSA] |
| B0のGOがscience実行許可 | preflight GOでありauthorized=false。監査依頼も実行許可を与えない。[FSB] |
| S4/v1のno_benefitが研究未完了を意味する | 固定比較は完了したnegative result。閾値救済やS5再開を完成条件にしない。[SYNTH] [V1] |

## 3. F02・F03・H05で統一して説明できる範囲

既存資料だけで、次の筋道は説明できる。先頭係数の抑制と演算子・結合の抑制は異なり（F03）、a8にはD8直接項とD4混合があり内部相殺も起こる（F02）。小係数の相対fitは不安定になり得るが、有限時間曲線の絶対残差はなお小さくなり得る（F02）。混合補正をresponseで取得してもD6/D8入力とstate品質の問題は残り、少数direct点の成功はoracle費用とdevelopment適合を伴う（H05）。[F03] [F02] [H05]

これは既存機構の整合的な統合である。以下までは説明しない。

- HFのpass/failを一つの因果量に還元すること。bridgeではgapと各係数が共変する。[HF]
- 小さいa8、良いfit、良いoverlapから、全使用域の小剰余・正しい枝・safe予算を証明すること。[F02] [F05] [EXP]
- 任意分子・6/8次PF・別basisへ移送すること。[F01] [COST]
- 精度改善から量子費用・古典費用込みのnet gainを導くこと。[H05] [EVMAP]

## 4. 重複確認の範囲

| 一次資料 | 確認範囲 | 既知の重複 | 今回は解決済みと見なせない残余 |
|---|---|---|---|
| Yi–Crosson, arXiv:2102.12655v1 | 本文spectral/gap仮定・perturbation | 固有値と固有ベクトルの分離、gap依存解析 | repositoryの相殺した4次PFがどの有限時刻まで低次モデルで足りるか。[L1] |
| Mehendale et al., arXiv:2312.13282v3 | 本文の摂動推定・CISD・resource結論 | 状態依存固有値誤差、近似状態、時刻・分割選択 | H05固定tail設計の移送やnew-source FS-R1の未採点結果。[L2] |
| Morales et al., arXiv:2210.15817v3 | 本文IVの比較・固有値誤差 | 異次数・長さ・processing、有限時間関数による閾値 | 本repositoryの分子別truthと固定予算評価。単なる有限時間比較は重複。[L3] |
| Maxwell et al., arXiv:2606.30738v1 | 本文asymptotic結果・compact BCH節 | 対角誤差構造・compact表現・importance selection | H-chain groupingでのsigned pruning bound、安価なD8取得と有限時間適用条件。[L4] |
| Hejazi et al., arXiv:2412.16811v1 | abstract/scope | QPE向けtask-specific PFと低energy解析 | 本監査では全文の定理適用を照合していない。[L5] |
| Kronenberger et al., arXiv:2602.18913v1 | abstract/書誌 | 軌道basisとTrotter誤差・低誤差recipeの難しさ | U1の特定descriptor・全電子移送の未解決性を全文で確定してはいない。[L6] |
| Simon–Love, arXiv:2512.02131v1 | abstract/書誌 | 誤差を測って資源を推定する課題 | 現研究の古典校正と同じ費用契約とは確認していない。[L7] |
| Abe et al., arXiv:2605.30967v1 | abstract/書誌、repo旧README | 高次PFの分子資源評価という既存成果 | 旧順位や係数版を現在のfinite-time truthで無条件に書き換えない。[L8] [OLDREADME] |

この表は静的な限定対応確認であり、網羅的新規性調査ではない。別PR/Track A/Bの原資料は今回の監査対象repository外で、完全なclaim照合は行っていない。別研究の目的や成果を変更する承認もない。

## 5. 証拠の強さと採否の境界

数学的に既知の局所恒等式、保存finite-time数値の再現、同一条件内の機構診断、未使用条件での固定予測は区別する。原reportの`complete`はそのprotocolの完了であり、一般的科学問題の解決ではない。反対に未実行計画や技術STOPがあるだけでは、新しい科学問題が残った証拠にはならない。

U1–U7の証拠を新たに合算・再ランキングしていない。rank違い、複数時刻、同一family、再利用truthを独立標本に増やしていない。追加仮説の採否、必要な数学的成果、計算上限と停止点はGPT／ユーザー判断に留保し、監査後は停止する。

<!-- fixed-source-references -->

[OLDREADME]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3254f79825cfbcc2af91b6c07d01de469d3e4eb6/review_response/README.md
[COST]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/server_cost_validity/integrated_boundary_recheck_20260902/pf_cost_rejection_tests.md
[NH3BR]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/76d091f18b7f68b2612dc2c8267bbab5e23c12a1/artifacts/server_nh3_branch_protocol_audit_20260920_222119_d8c1d55/report.md
[NH3MOD]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/46a7ed165650cb80506be14d997380e0bf333680/artifacts/server_existing_pf_unified_nh3_20260920_233516_e692360/aggregate/report.md
[HOLDOUT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md
[F01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/report.md
[F02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md
[F03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md
[F05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f05_energy_phase_gap_20260922/report.md
[H04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md
[H05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md
[HF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_final_synthesis_20260925.md
[V1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/05649f1a7b6e405eadc2dbbdc0897836e0fa2f02/review_response/second_study_safe_time_domain_completion_report.md
[D1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a/artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2/report.md
[D2AUD]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17e4d6357c7c5ef9bb849d0f787a642f972c7995/artifacts/pf_spectral_recoverability_d2_a_scoring_audit_20260929/report.md
[SCALEOLD]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961/report_partial_v1_2.md
[SCALE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4672f3f5c57e34a553518b10655396a195521294/artifacts/server_hchain_direct_optimal_time_h5_v1_2_20260927_e82b6ae/report.md
[DIRC]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e895870f16878ee4181b0e0dfe3159826a791563/docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md
[EVMAP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1d01e77247364b49dbce2e9ce2fe7c32af0fb937/docs/second_study_v2/evidence_integration_20261006/evidence_map.md
[CORRECTION]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1d01e77247364b49dbce2e9ce2fe7c32af0fb937/docs/second_study_v2/evidence_integration_20261006/documentation_correction.md
[H4]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5b370ec22f7ffeac687ef70e1bcb87337f5fb976/artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/report.md
[EXP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/19362c23ccdc16b6ad0ff547cc363e138a3930d2/docs/research_outcomes/20261007/validation_expansion_results.md
[FSC06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_c06_functional_equivalence_20261007/README.md
[FSR0]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r0_rebaseline_20261007/README.md
[FSA0]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008/README.md
[FSA]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[FSB]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/README.md
[L1]: https://arxiv.org/html/2102.12655v1
[L2]: https://arxiv.org/html/2312.13282v3
[L3]: https://arxiv.org/html/2210.15817v3
[L4]: https://arxiv.org/html/2606.30738v1
[L5]: https://arxiv.org/abs/2412.16811v1
[L6]: https://arxiv.org/abs/2602.18913v1
[L7]: https://arxiv.org/abs/2512.02131v1
[L8]: https://arxiv.org/abs/2605.30967v1
