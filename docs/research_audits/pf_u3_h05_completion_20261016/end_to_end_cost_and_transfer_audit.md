# U3／H05：総取得費用と移送性の静的監査

2026-10-16 JST。新規計算・benchmark・数値再解析なし。以下は保存report、scalar ledger、sourceの読取りであり、時間・係数・pass数を再集計していない。[方式と判定](h05_method_and_evidence_map.md)、[判断への引渡し](research_completion_handoff.md)、[provenance](provenance.json)を参照。

## 1. 費用に関する既存証拠

H05 online timingだけでは総費用は評価できない。一方、**D04にはa4取得費・direct点再計測・dense D4/D6/D8構築を含む小系比較が既にある**。したがって「D6/D8やdirect点は一切未計測」とは記述しない。残る不足は、計測の範囲、前処理内訳、高精度・大規模系での取得、未使用系での費用・必要精度の同時成立である。[H05] [D04]

| 保存method | 高次残差pass | median warm秒 | median cold秒 | median PF exponential数 | median estimated peak MiB |
|---|---:|---:|---:|---:|---:|
| fixed-a4 tail2 | 8/8 | 2.1762e-2 | 2.4315e-1 | 96 | 0.4039 |
| free tail5 | 8/8 | 8.5570e-3 | 2.2995e-1 | 240 | 0.2997 |
| dense BCH effective order8 | 8/8 | 5.9836e-2 | 2.8123e-1 | 0 | 0.8703 |

D04 reportから引用。fixed2がfree5より速かったのは1/8、推定peak memoryが同等以下だったのは0/8。dense BCHのmedian marginal時間はfree5の6.992605370149022倍。点数削減は実証範囲を持つが、一律の古典時間・memory削減は支持されていない。[D04] [D04SUMMARY]

`cold_seconds_no_reuse`は同じfresh processを各方式で実行して得た時間ではなく、**X02保存setup_seconds＋各方式marginal時間**の会計値である。setupはH2 0.06781270890496671秒、H4 0.3749687490053475秒。D04のwarmもH04からのa4時間、7反復medianのdirect build/Schur、101反復medianのfit等を組み合わせる。比較可能な小系会計だが、統一した単発end-to-end実行の測定値とは区別する。[D04CODE] [X02AUDIT]

表のPF exponential数はsourceの`len(expanded_steps)×point_count`という構造上のaction会計である。`s2-cache` backendの実時間、実際のexpm呼出し、量子gate数を同じ単位とは見なさない。[D04CODE]

## 2. 費用分類とcoverage

分類は各行に記した測定範囲へ適用する。`MEASURED_EXCLUDED_FROM_REPORTED_TIMING`は別artifactで測定済みでも当該reported timingへ入っていないもの、`SOURCE_AVAILABLE_NOT_MEASURED`は公開sourceの手順を確認できるが独立した時間fieldがないものを指す。`ESTIMATED_ONLY`と実測RSSを混同しない。

| 費用項目 | 分類・根拠 | 含まれる範囲／残る不足 |
|---|---|---|
| Hamiltonian取得・前処理全体 | `MEASURED_INCLUDED`：D04 coldにX02 setupを加算 | 既存小系のsetup合計。D04自身の新規SCF計測ではない |
| SCF、積分変換、group・sector構築、exact stateの内訳 | `SOURCE_AVAILABLE_NOT_MEASURED`：固定公開のprepare chain、PySCF/FCI source。X02 timerの完全な原本sourceは`NOT_AVAILABLE` | 準備工程の存在は追えるが、X02保存setupの内訳を個別に確定できない。欠けたX02 sourceをdirty rootで代用しない |
| exact ground state取得 | `MEASURED_EXCLUDED_FROM_REPORTED_TIMING`：setup合計としてD04 coldに課金、H05 onlineからは除外 | exact state単独の時間は`NOT_AVAILABLE`。H05は保存stateを読むだけ |
| HF／CISD state取得 | `MEASURED_EXCLUDED_FROM_REPORTED_TIMING`：H01 generation time、H05は再利用 | determinant生成・既存H部分空間対角化のみ。新しい分子のSCFからの費用ではない |
| D4 compact生成・作用 | `MEASURED_INCLUDED`：H04生成／作用、D04 fixed-a4費用 | H05 state timerは作用から開始し、compact項生成を含まない。D04は両方を課金 |
| D6/D8 dense構築 | `MEASURED_EXCLUDED_FROM_REPORTED_TIMING`：H05 online。`MEASURED_INCLUDED`：D04 dense order8 | H2/H4のcomplex128 dense series一式。D6/D8個別・高精度の費用内訳は未計測。H04型の安価な高次grouped backendの実証ではない |
| D6/D8作用・期待値 | `MEASURED_INCLUDED`：H05 expectation_seconds | 保存dense行列のmatvec。生成・入手・保存I/Oを含む時間ではない |
| projected response solve | `MEASURED_INCLUDED`：H05 response_solve_seconds | np.linalg.solve本体のみ。Q、dense augmented行列、RHS準備やcondition number計算はtimer外 |
| response前後の行列準備・条件検査 | `SOURCE_AVAILABLE_NOT_MEASURED`：H05 projected_response_mixing | 独立timerなし。一般系でのgap依存・近似状態安定性の費用保証なし |
| dense再帰摂動 | `MEASURED_INCLUDED`：D04 perturbation_seconds | BCH backendのH0完全対角化・係数再帰を含む。H05 projected solveと別の実装 |
| direct PF点 | `MEASURED_EXCLUDED_FROM_REPORTED_TIMING`：H05 reused points。`MEASURED_INCLUDED`：D04 direct build＋Schur | D04は既存40座標を7反復。タイマーはoverlap枝選択・unwrap・eigenpair残差評価前に停止し、その後処理は含まない |
| direct枝の参照情報 | `SOURCE_AVAILABLE_NOT_MEASURED`：D04 exact ground overlap＋E0 unwrap | exact state/E0を使用。H05行のrequires_exact_state=falseはfitインターフェースのfieldであり、全工程oracle-freeの証拠ではない |
| cancellation／数値精度 | `SOURCE_AVAILABLE_NOT_MEASURED`：F01 H2 70/100桁検査、HF bridge 128-bit Arb | F01総時間は保存されるが高精度工程の切分けなし。D04はcomplex128で、任意系の必要桁数・その増分費用は`NOT_AVAILABLE` |
| 方式別memory | `ESTIMATED_ONLY`：D04 shared_input_bytes＋incremental_working_bytes | ndarray形状等による式。BLAS/Schur workspace、Python objects、I/O等を含む各方式の実測peakではない |
| process memory | `MEASURED_INCLUDED`：H05最大RSS 281564 KiB、D04 peak_process_rss_bytes 293650432 | 複数方式を走らせたprocessのhigh-water mark。方式別表へ分配できない |
| model fit | `MEASURED_INCLUDED`：D04 fit_seconds。H05 condition／残差diagnostics | scaled least squares、既存点・固定priorを入力。係数の数値識別とfinite-time剰余保証は別 |
| reuse・amortization | `MEASURED_INCLUDED`の工程値を使った保存会計、未使用系の効果は`NOT_AVAILABLE` | D04のsetup/4＋marginalは4 PFに均等配分する契約。新しい実測totalではない |
| 実量子state準備・測定shots・FT runtime | `NOT_AVAILABLE` | この古典係数取得比較では計測していない。QPE回転数へ古典秒数を換算・加算しない |

根拠：[H05CODE] [H01] [H01CODE] [H04] [D04CODE] [D04RES] [D04DENSE] [X02AUDIT] [PREP] [PYSCF] [F01] [HFBRIDGE]。

H05のaudit elapsed 0.903127304976806秒、F01の167.9319780319929秒は保存されたworkflow全体の時間であり、各方式の同一契約の総取得時間ではない。H05のdiagonal-only行にもexact response行と同じstate_timings（solveを含む）が付くため、この時間で両方式の速度差を比較できない。[H05AUDIT] [H05CODE] [F01MAN]

静的sourceからの標準dense線形代数の見積りとして、sector次元dの行列保管はO(d²)、vectorはO(d)、dense solve／完全対角化は通常O(d³)である。これは`ESTIMATED_ONLY`の算法上の目安で、今回のbenchmarkや実用領域のscaling実証ではない。compact項数の減少はこれらを自動的に除かない。

## 3. 再利用の単位と適用限界

| 再利用単位 | 再利用可能とsourceから分かるもの | 再利用できない／未確認のもの |
|---|---|---|
| 同一H・basis・分割 | H、group、state、E0、group spectra、setup | 別分子・geometry・basisに同じ情報を無課金で移すこと |
| 同じ分割の複数PF | 準備済みstate/group、場合によりgrouped表現の構造 | a4の作用・PF重み、D6/D8、response RHS、direct Uは一般にPF依存 |
| 同じH/PFの複数時刻 | state/E0、group spectra、構築済み演算子 | 新時刻のunitary build／Schur、branch certification費用 |
| 同じH/PF/stateを多回使用 | 既取得係数や参照のamortizationの可能性 | 何回なら他方式より得かという未使用系での実証。今回break-even計算はしない |

保存scalar・code・hashは今回の静的資料作成へ再利用できる。一方、既に見たN2/CO/NH3/HFの結果を今後の方法選択へ使用した後、その同じ系を無条件に未使用testと呼べない。独立性は分子名だけでなくHamiltonian、PF、state、時刻、選択履歴、truth exposureで判断する。

## 4. 移送性の証拠台帳

| 固定資料 | 選択・開発への使用と後続評価 | H05同一方式の独立評価か |
|---|---|---|
| F01/F02 H2/H4、4 PF | F01 interlaced時刻はoperator fitに対する未使用時刻だが、H05はその保存shiftを新たなfit入力へ使用 | いいえ。F01のholdoutというfield名からH05独立性は継承されない |
| H05固定tail2点 | 6種direct設計等を同じ8条件で比較し選択 | development。選択後に未使用系へそのまま適用した記録は確認できない |
| D04 H2/H4 | H05の設計・係数・判定を保持した同じ8条件の費用監査 | 科学的な移送testではない。独立な時間計測でも新しいHamiltonian評価ではない |
| NH3統一比較 | short-time grid選択に使用した4条件。Yoshida4二項／三項等を比較 | development。H05固定a4＋tail2ではない。[NH3] |
| N2/CO frozen-core active-space、eq/stretch150 | 当時凍結した自由5点t4/t6等で主4条件を評価。Yoshida4等4/4、m5_best 0/4 | 別方式の当時のholdout。H05へ転用不可。[HOLDOUT] [HOLDPROTO] |
| HF全電子eq/stretch150 | 同じholdout研究の補助stress。Yoshida4二項のeq pass／stretch failが後のbridgeで診断された | H05の同一recipeではない。HF bridgeは機構診断で、N2/CO dense D8も作っていない。[HFBRIDGE] |
| 第一研究final synthesis／claim ledger | N2/CO/HFの6条件をdevelopmentとして、S4 no_benefit後のS5未使用分子評価は停止 | H05へ新しい独立性を付与しない。[SYNTH] [CLAIMS] |
| 10月H4 response follow-up | 既知H4/current_m3のstate改善・finite-time proxy/refit。Outcome C | H05のa8係数取得・固定2点ではない。[H4FOLLOW] |
| 10月H6等validation expansion | 短時間proxy分類、spectral分解、局所grid、HF cap感度 | 対象サイズが増えてもH05同一構成の検証ではない。[EXPANSION] |
| FS-R1 Phase A/B0 | N2/CO新source、CISD/Ritz×3点fit/local。prediction凍結、truth未採点、Phase B承認false | 別方式・別source。未採点predictionはH05の移送成功ではない。[FSA] [FSB] |

後続holdoutの主判定はeta_star≤0.01、eta_min≤0.01、eta_t≤0.05、unseen residual／epsilon≤0.05など、凍結protocolの契約である。H05の参照三項t*における高次係数残差と同じ判定ではない。1%費用margin付きbudgetの成功もH05の残差passと合算しない。[HOLDPROTO]

## 5. 独立性を今後確認する際の固定項目

以下は**新protocolの採択ではなく、GPT／ユーザーが必要性を判断した場合の不足情報一覧**である。新しい条件・threshold・時刻はここで設定しない。

1. 対象Hのsource identity、basis、geometry、分割、energy origin、PF重みとstateの完全な固定記録。
2. どの資料・truthを選択者が既に見たか、およびdevelopment／最終評価への役割分担。
3. H05固定の絶対2時刻・a4 prior・fit powers・signed branch規則を保持するのか。時刻をt_ana相対へ置換すれば別recipeになる。
4. exact a4の取得backendとその費用、E0／exact vector／spectral情報へのアクセス範囲。
5. 比較baseline（既存free3/free5、必要なら既存dense基準）と全方式に同じ費用・情報境界を課す規則。
6. 係数精度、元の高次加重残差、direct finite-time精度、budget safetyを区別した評価対象と停止点。
7. 生成・準備・精度・枝検査・fit・memory・再利用の何を測るか、既存測定との互換性。
8. source／branch／数値gate失敗、原recipe不適用、資源上限到達時の停止と、失敗後のretuning禁止。

既存保存値を使うと新科学計算を避けられる可能性はあるが、**再fit・再採点自体が今回は禁止**であり、既に露出した保存値では独立性も回復しない。必要となる科学計算・再解析は[handoff](research_completion_handoff.md)の未承認事項へ留保する。

## 6. 探索範囲と未取得事項

取得した62件の固定GitHub text/scalar/source blobと、指定3論文を資料台帳で記録した。10個の既存研究snapshotに対し`H05|direct_fixed_a4_2_tail|fixed-a4|fixed_a4`をmd/py/protocol/decision JSONで検索し、上表の後続資料を読んだ。U1-AR作業branch・成果物は検索対象にしていない。全branchの全科学データを網羅した不存在証明ではなく、**本監査の確認資料には同一固定H05方式の未使用系評価がない**という結論である。

X02の原本runnerは要求したe820 snapshotにも監査baseにも見つからず、固定auditにそのsource hashだけが残る。setup合計は取得済みだが、timer coverageの完全復元は未完。H01の別名H02 pathもe820で404だったため、実在する16bd6c2固定commitのH02報告を使用した。これらを科学的失敗やsource再生成の許可と解釈しない。private cache、npz、pickle、matrix/vector、exact stateは開いておらず、source回収・新規計算による穴埋めをしていない。

<!-- fixed-source-references -->

[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[D04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/report.md
[D04CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_d04_equal_classical_budget.py
[D04DENSE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/dense_bch_timing.csv
[D04RES]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/method_resources.csv
[D04SUMMARY]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/method_summary.csv
[EXPANSION]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/19362c23ccdc16b6ad0ff547cc363e138a3930d2/docs/research_outcomes/20261007/validation_expansion_results.md
[F01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/report.md
[F01MAN]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/manifest.json
[FSA]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[FSB]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/README.md
[H01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h01_approximate_state_pilot_20260922/report.md
[H01CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_h01_approximate_state_pilot.py
[H04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md
[H05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md
[H05AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/audit.json
[H05CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_h05_higher_order_acquisition.py
[H4FOLLOW]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5b370ec22f7ffeac687ef70e1bcb87337f5fb976/artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/report.md
[HFBRIDGE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md
[HOLDOUT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md
[HOLDPROTO]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/review_response/unused_molecule_frozen_holdout_protocol.json
[NH3]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/46a7ed165650cb80506be14d997380e0bf333680/artifacts/server_existing_pf_unified_nh3_20260920_233516_e692360/aggregate/report.md
[PREP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/validate_hchain_perturbative_estimator.py
[PYSCF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/src/trotterlib/qiskit_time_evolution_pyscf.py
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_final_synthesis_20260925.md
[X02AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3/audit.json
