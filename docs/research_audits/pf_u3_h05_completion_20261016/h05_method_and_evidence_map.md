# U3／H05：方式と証拠の静的対応表

2026-10-16 JST。研究採択・新規性・論文化可能性の判定は行っていない。新しい科学計算、保存数値の再集計・再fit、科学実装、証明は0件。数値は固定GitHub資料からの引用である。

読む順序は[研究判断への引渡し](research_completion_handoff.md) → 本資料 → [費用・移送性](end_to_end_cost_and_transfer_audit.md) → [provenance](provenance.json)。出発点は既存完結性監査のU3/Q04であり、その分類・formal statusは変更しない。[AUDIT] [QUESTIONS] [OPTIONS]

## 1. 元結果の対象と判定の意味

H05はH2/H4の固定Hamiltonian分割、`yoshida4`、`current_m3`、`two_term_center`、`m5_best`という**4種類の4次PF**、計8条件である。a6/a8という高い時間次数の係数を扱うことを、6次・8次PFでの実証と混同しない。H01のexact/HF/CISD状態、F01の同一basisのH・group・D6/D8、F02の混合参照、H04のcompact D4作用を再利用した。H2/H4のsector次元は4/36、group数は2/13である。[H05] [H05AUDIT] [F01REG] [D04DENSE]

固定prepare経路はSTO-3G、H原子の直線鎖、隣接距離1.0 Å、両系とも電荷0・singletを指定する。scalar identityだけでなく元演算子のmanifest hashもsource identityの根拠となるが、今回そのnpzを開いて座標・matrixを再検証してはいない。[CHEM] [CONFIG] [F01MAN]

保存された展開は

$$
H_{\rm eff}(t)=H+t^4D_4+t^6D_6+t^8D_8+\cdots,\qquad
E_{\rm PF}(t)-E_0=a_4t^4+a_6t^6+a_8t^8+\cdots.
$$

H05の`residual pass`は、参照a4/a6/a8の**三項多項式モデル**から選んだ、t=0に接続する許容区間内の連続最適時刻t*で

$$
\frac{|(\widehat a_6-a_6)t_*^6+(\widehat a_8-a_8)t_*^8|}{\epsilon}\leq0.05,
\qquad \epsilon=0.00015936001019904\ {\rm Ha}
$$

を満たすことを指す。近似状態でも、この主判定はa4誤差を含まない。`full_residual_over_epsilon`は別fieldである。**t*でのdirect PF truth、全使用時刻での剰余bound、凍結QPE予算の安全性、連続direct最適性を採点した結果ではない。** 参照t*の選択自体にexact係数を使う。[H05CODE] [H05AUDIT] [TSTAR]

| H05保存method ID | direct点数 | a6符号一致 | a8符号一致 | 高次残差pass | 最悪高次残差／epsilon |
|---|---:|---:|---:|---:|---:|
| bch_exact_response | 0 | 8/8 | 8/8 | 8/8 | 2.459e-12 |
| bch_exact_d8_diagonal | 0 | 8/8 | 7/8 | 6/8 | 8.117e-1 |
| bch_hf_response | 0 | 2/8 | 3/8 | 4/8 | 7.845e1 |
| bch_cisd_response | 0 | 8/8 | 8/8 | 7/8 | 5.181 |
| direct_fixed_a4_2_tail | 2 | 8/8 | 8/8 | 8/8 | 2.829e-2 |
| direct_fixed_a4_3_tail | 3 | 8/8 | 8/8 | 8/8 | 3.358e-2 |
| direct_fixed_a4_5_tail | 5 | 8/8 | 8/8 | 8/8 | 3.529e-2 |
| direct_free_3_tail | 3 | 8/8 | 8/8 | 7/8 | 5.143e-2 |
| direct_free_5_tail | 5 | 8/8 | 8/8 | 8/8 | 4.742e-2 |
| direct_order12_16 | 16 | 8/8 | 7/8 | 7/8 | 1.456 |

元report／method summaryの数値・分母を保持した。16点法はt4/t6/t8/t10/t12の5係数fitであり、点数増加・次数追加が一律に救済しなかった例である。[H05] [H05SUMMARY]

## 2. A1：exact BCH＋response

非縮退のexact ground stateを用いた既存の構成は

$$
a_4=\langle0|D_4|0\rangle,\quad a_6=\langle0|D_6|0\rangle,\quad
a_8=\langle0|D_8|0\rangle+
\sum_{n\ne0}\frac{|\langle n|D_4|0\rangle|^2}{E_0-E_n}.
$$

H05はD4の行列全体を作らずH04のgrouped作用v=D4|0>を取得し、Q=I−|0><0|として`[Q(H−E0)Q+|0><0|]x=−Qv`をdense solveし、`Re<v|x>`を混合項へ足す。これは既存source/F02の式の転記であり、新しい証明ではない。[H05CODE] [F02] [BCHSOURCE]

| 要素 | 入力・出力と既存到達点 | 限界 |
|---|---|---|
| D4 | group行列・固定PF重み・exact vectorから作用とa4 | vectorとdense group入力を保持。compact項生成も必要 |
| D6/D8 | F01の保存dense演算子から期待値 | responseはこれらを供給しない。一般分子の安価な生成法は未確立 |
| response | H、E0、exact vector、D4作用からa8混合 | H05のsolveは全励起固有対の列挙を要求しないが、完全なdense Hを要求する |
| 参照 | F01/F02はH固有基底・励起情報を用いて独立な式との一致を検査 | 参照側の完全対角化を、運用側の入力要件へ無条件に足さない。一方exact state取得費は残る |
| 正確性 | exact response残差最大2.429e-18、F02混合との差最大1.799e-18 Ha | 保存8条件での数値identity。高次剰余や任意分子での安定性の定理ではない |

H05の「inexpensive mixing correction」はD6/D8を既に持つ条件での補正部分を指す。D8対角だけの6/8という結果は混合を一律に省略できないことを示す。演算子構築は未解消の取得工程だが、H05 online時間から支配率を数値断定することはできない。D04には小系でのdense構築の別計測がある。[H05] [D04]

## 3. A2：近似状態BCH＋response

H05は同じdense D6/D8を保持したまま、|0>をH01のHF／determinant-space CISDへ置換する。エネルギーは`<psi|H|psi>`、射影もpsiから作る。非固有状態の周りでこの式を解いて得る量はapproximationであり、exact ground eigenenergy係数のidentityではない。[H05CODE]

HFは保存basisの最低軌道占有determinant、CISDはそこからsingle/double励起の部分行列の最低固有vectorである。H2のCISDは4/4次元を使うためexactと一致し、独立な近似状態成功例を増やさない。H4は27/36次元、保存overlapは0.99946684だが、H05のCISD法は全体で7/8に留まる。HF/CISDの生成時間は既存H・basisからのdeterminant生成／部分空間対角化の時間で、SCF・積分・元H取得からの費用ではない。[H01] [H01CODE]

状態energy error、variance、residual、overlapを保存していることと、係数精度を事前保証できることは異なる。H02のN2/CO制御状態ではこれらのscalarを等しくしても校正量が異なる反例がある。ただしそれはfinite-time proxy校正の反例であり、あらゆるnorm/gap補助情報を含む保証の不可能性や、H05各高次係数の一般不可能性の証明ではない。[H02] [REVIEW]

10月H4のresponse8/Ritz8は状態改善をfinite-time校正へつなぐ別研究で、Outcome C `point_only`。Responseのtotal absolute error改善は残ったが、baselineのS_under=0に対するstrict減少は不成立だった。これをH05のD4応答式の高次係数保証や未使用系成功に読み替えない。FS-R1もRitz/local・3点proxyの別構成で、Phase Bのscience承認はfalseである。[H4FOLLOW] [FSA] [FSB]

## 4. A3：exact a4＋固定few-point

`direct_fixed_a4_2_tail`は、F01 `middle`窓の**interlaced holdout_rows**を時刻順に並べた16点の0始まりindex `[11,15]`である。元の窓端0.09/0.70 Ha⁻¹や、後続研究のt_ana相対座標とは区別する。保存入力は全8条件で

`[0.3931379077393266, 0.65653639279173] Ha^-1`

であり、signed direct PF shiftからexact a4*t4を引き、t6/t8の2未知係数をscaled least squaresで求める。a4はF01参照の`energy_coefficients.a4`を直接渡す。H05が独立にa4を取得する処理をfitに内包しているわけではない。D04はH04 compact D4生成＋exact-state作用をa4取得費として別途課金した。[H05CODE] [FITDIAG] [D04CODE]

H05保存条件数は67.7000299710837。最悪a8相対誤差は1.95463172257444であり、8/8の加重残差passを相対精度のよいa8取得という保証にしない。保存t*／最大入力時刻比の最大は9.06162186369475。これは三項モデル内での遠方評価を含み、その時刻のdirect truth検証を意味しない。[H05AUDIT]

H05のfree3/free5も同じdevelopment集合の比較armだが、前者はindex `[13,14,15]`、後者は`[11,12,13,14,15]`でt4/t6/t8をすべてfitする。fixed3は`[11,13,15]`なので、D04の「same-point」3点比較は**同点数**比較であって同一時刻座標のpaired比較ではない。5点比較は両方式のindexが同じである。[H05AUDIT] [D04CODE]

後続の一項fit、t4/t6二項の自由fit、t4/t6/t8三項の自由fitは、未知数、点、時刻規則、事前情報、採点対象が異なる。N2/CO等でそれらが成功しても、H05固定2点方式の未使用系評価にはならない。[HOLDPROTO] [HOLDOUT]

## 5. A4：高次演算子の直接取得

H04はH4/YoshidaのD4に関するraw commutator 168,560個をgrouped 456項へ縮約し、全保存D4作用の最大相対差1.406e-11を報告した。H03のsymbolic生成blockerはこの範囲で解消済み。一方、signed importance上位項を増やした24曲線中13で非単調悪化があり、PF順位の安定を剰余保証にしない。[H04]

D4のgroupingをD6/D8生成法の完成と見なさない。F01はformal ordered-product log／有限時間matrix-logの検査、H2の70/100桁比較、H4のcomplex128 backendを持つ。D04はcomplex128のeffective order8 dense seriesを新たに構築した既存計測を保存する。その再帰摂動backendはH0の完全対角化を行うため、H05 projected solveの費用とは分ける。[F01] [D04CODE] [BCHSOURCE]

dense Hamiltonianとgroup、statevector、dense中間series、operator作用、高精度の必要性、exact参照・状態取得は残る。F02は相殺後a8の窓間相対安定が3/8でも短時間曲線誤差は小さくなり得ると示し、F03は小a4と小D4を区別した。いずれも高次係数の安価な一般取得や有限時間保証を完成させた証拠ではない。[F02] [F03]

## 6. 先行研究との限定照合

指定3論文の固定版HTMLを取得し、以下を読んだ。byte/hashはprovenanceに保存した。査読最終版・他version・各software全体の監査、証明の再証明、網羅的先行研究探索は行っていない。

| 論文・取得版／読んだ箇所 | 数学的対象と情報要件 | H05と比較できる差分・費用の限界 |
|---|---|---|
| Mehendale et al., 2312.13282v3。II Eq.(6)–(9)、III.1–2／Tables 1–2、Appendix A.3–5／Eq.(26) | 2次PFの先頭t2固有値係数、BCH期待値。exact／CISD、Hと分割を使用。STO-3GのH2/LiH/BeH2/H2O/NH3で評価 | H05の4次PFのa6/a8 responseや固定2点fitそのものではない。状態依存摂動推定と資源評価は先行。T-gate見積りと対角化実装を記すが、H05と同契約の古典総取得時間は本文に確認できない。[LMEH] |
| Maxwell et al., 2606.30738v1。III.1 Theorems 1/3、III.2 Eqs.(9)–(20)、III.3 Eq.(21)、IV.1 Eqs.(22)–(25)、IV.2／Appendices A–B | 一般PFの先頭誤差のasymptotic対角構造。2/4次PFのcompact BCH、importance。電子系はCDF＋approximate DMRG/MPSで最大56 qubit | H04の直接の先行法。O(L3)→O(L)、O(L5)→O(L2)はcommutator数であり全状態取得費ではない。H05のsubleading a6/a8混合や固定2点移送の実証とは別。本文に同契約のend-to-end CPU timingは確認できない。[LMAX] |
| Hejazi et al., 2412.16811v1。I Eqs.(3)–(9)、II Eqs.(10)–(13)、III、IV、Supplement VI/VII Eqs.(23)–(29) | 任意次数PFのgapped eigenstateに対するMagnus／摂動解析。Eq.(9)の剰余はO(s^(2p))。p=4ではs8がその境界。全経路の非零gapを仮定 | H05のa8混合を無視できる根拠にはならない。数値例は3×4 XY・9 qubit random系で、H05分子移送ではない。QPE向けPF構成・低energy boundを扱うが、同契約の古典係数取得費・近似状態認証は確認できない。[LHEJ] |

BCH、固有値摂動、responseによる混合の構成は既知の枠組みに属する。H05で比較対象になり得る具体点は、保存された特定4次PF・分割でのsubleading成分、相殺下の取得誤差、固定prior＋direct点の情報／費用契約である。これらが独立した新規性を成立させるかは未判定。単に「高次」「response」「compact」という名称の共通性から、同一手法とも独立新規とも結論しない。

H04のarbitrary palindromic S2 composition係数検査と、Maxwellの再帰的PFの文脈も分ける。高次一般保証を求めるなら、既知結果の適用仮定と足りない保証を先に確定する必要がある。採択は[handoff](research_completion_handoff.md)のGPT判断事項に留保する。[H04]

<!-- fixed-source-references -->

[AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_audit.md
[BCHSOURCE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/bch_matrix_series.py
[CHEM]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/src/trotterlib/chemistry_hamiltonian.py
[CONFIG]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/src/trotterlib/config.py
[D04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/report.md
[D04CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_d04_equal_classical_budget.py
[D04DENSE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/dense_bch_timing.csv
[F01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/report.md
[F01MAN]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/manifest.json
[F01REG]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/formula_registry.csv
[F02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md
[F03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md
[FITDIAG]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/direct_fit_diagnostics.csv
[FSA]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_phase_a_production_20261008/README.md
[FSB]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a7644d5ebe64b66044461623506093ac6b0a1206/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/README.md
[H01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h01_approximate_state_pilot_20260922/report.md
[H01CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_h01_approximate_state_pilot.py
[H02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe/artifacts/server_h02_finite_time_controlled_state_20260922_a228b5f/report.md
[H04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md
[H05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md
[H05AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/audit.json
[H05CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_h05_higher_order_acquisition.py
[H05SUMMARY]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/method_summary.csv
[H4FOLLOW]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5b370ec22f7ffeac687ef70e1bcb87337f5fb976/artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/report.md
[HOLDOUT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md
[HOLDPROTO]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/review_response/unused_molecule_frozen_holdout_protocol.json
[LHEJ]: https://arxiv.org/html/2412.16811v1
[LMAX]: https://arxiv.org/html/2606.30738v1
[LMEH]: https://arxiv.org/html/2312.13282v3
[OPTIONS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_options.md
[QUESTIONS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/open_question_and_evidence_map.md
[REVIEW]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_research_direction_review_e820f65_20260925.md
[TSTAR]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/reference_tstar.csv
