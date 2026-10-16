# 第一研究向け技術補論草案：4次PFの高次誤差係数取得・状態近似・取得費用

2026-10-16 JST。**独立草案・既存本文へ未統合。** ユーザーが採択したE4に従い、H05を第一研究の補助成果として限定整理する。[決定記録](decision_record.md)を参照。数値・判定は固定原本からの引用であり、今回の新計算・保存値再解析・新証明・科学実装ではない。

## 1. 目的と第一研究内での位置付け

本補論は、有限時間PF校正に用いる高次係数の取得に、どの情報と費用が必要だったかを説明する。対象はH2/H4のSTO-3G、`yoshida4`、`current_m3`、`two_term_center`、`m5_best`という**4種類の4次PF、8条件のdevelopment集合**である。時間次数6/8の係数を取得したことを、6次・8次PFの検証と混同しない。[H05AUDIT] [AUDITMAP]

第一研究の中心claim、development集合、資源proxyの限定、S0〜S4完了とS4 `complete_no_benefit`は既存final synthesis／paper claim ledgerを保持する。[SYNTH] [CLAIMS] 本補論は独立新規論文の成立、新規推定理論、方法論上の資源利益を主張しない。

対象枝、energy origin、proxyと固有値、Taylor/Magnusの一般的な説明は[U1-ARのC1補論][U1DRAFT]を参照し、ここでは係数・入力・取得費の比較に集中する。U1-ARの研究STOPを解除するものではない。[U1DECISION]

## 2. 対称4次PFのa4・a6・a8

固定された同じH・sector・basisにおいて、原点近傍の有効Hamiltonianと基底energy枝が局所展開でき、基底状態が非縮退・孤立しているという条件で、保存F02が用いた展開は

$$
H_{\rm eff}(\tau)=H+\tau^4D_4+\tau^6D_6+\tau^8D_8+\cdots,
\qquad
\delta_P(\tau)=a_4\tau^4+a_6\tau^6+a_8\tau^8+\cdots.
$$

exact基底状態に対する標準Rayleigh–Schrödinger固有値摂動の構成は

$$
a_4=\langle0|D_4|0\rangle,\quad
a_6=\langle0|D_6|0\rangle,\quad
a_8=\langle0|D_8|0\rangle+
\sum_{n\ne0}\frac{|\langle n|D_4|0\rangle|^2}{E_0-E_n}.
$$

H05/F02はこの既知の二次状態混合を小系で確認した。新しい摂動論の発見ではない。F02は縮退励起空間のbasis依存を避けるためenergy群への和も保持し、最適化PFではD8対角とD4混合の相殺を報告する。F03は小a4をD4全体や励起結合の小ささと区別する。[F02] [F03] [HEJ]

各係数とtauのべきを掛けたenergy寄与を区別する。局所係数のidentityを有限使用域全体の剰余boundに拡張せず、bare Hのenergy分母を円周位相gapで置換しない。一般的な枝・解析性の条件はC1草案側を参照する。[U1DRAFT]

## 3. D4混合の応答計算と情報要件

H05の既存実装ではv=D4|0>、Q=I−|0><0|とし、射影応答を

$$
[Q(H-E_0)Q+|0\rangle\langle0|]x=-Qv,
\qquad
\mu=\operatorname{Re}\langle v|x\rangle,
\qquad a_8=\langle D_8\rangle+\mu
$$

という形で取得する。これはsourceの再掲であり、新しい導出・数値解法の実装ではない。[H05CODE] exact状態の保存8条件で高次残差基準を達成し、応答残差の最大値は2.429e-18だった。D8対角だけの方式は6/8に留まる。[H05]

この射影線形応答は、励起状態和を明示列挙する代わりに線形方程式を解くSternheimer型の既知構成に対応する。標準一次摂動の状態方程式、スペクトル和、射影による非特異化はBaroni et al.の固定preprint Eqs.(25)、(28)、(30)にも示される。同資料はKS/DFPTの文脈であり、その費用・占有空間・self-consistency条件をH05の多体dense系へ同一視しない。[BARONI] Sternheimer原論文は歴史的出典として挙げるが、今回は出版社の書誌・abstractのみを確認し、購読を要する本文の式を読了したとは主張しない。[STERN]

| 工程 | H05の入力・取得内容 | 残る費用・制約 |
|---|---|---|
| D4作用 | H04のcompact grouped作用からvとa4 | dense group入力・statevector・項生成・作用の費用 |
| D6/D8期待値 | F01の保存dense演算子を利用 | responseは演算子を生成しない。D6/D8の取得費は別工程 |
| 混合 | dense H、exact state/E0、vからprojected solve | 全励起固有対の列挙は不要だが、dense Hとexact state取得は必要 |
| 独立な参照 | F02の励起状態和との一致 | 参照側の完全対角化と、H05の運用側solveの情報・費用を分ける |

`direct_point_count=0`は上記入力が不要という意味ではない。H05のonline timerだけから安価・oracle-freeな総取得法が完成したとは言えない。[H05CODE] [AUDITCOST]

## 4. Exact／HF／CISD状態の比較

H05は同じ保存D6/D8を使い、状態をexact／HF／determinant-space CISDで比較した。近似状態ではenergyと射影も当該状態から作るため、exact固有値摂動identityそのものではなく推定である。[H05CODE]

| 方式 | a6符号一致 | a8符号一致 | 元の高次残差pass | 最悪高次残差／epsilon |
|---|---:|---:|---:|---:|
| exact BCH＋response | 8/8 | 8/8 | 8/8 | 2.459e-12 |
| exact D8対角のみ | 8/8 | 7/8 | 6/8 | 8.117e-1 |
| HF response | 2/8 | 3/8 | 4/8 | 7.845e1 |
| CISD response | 8/8 | 8/8 | 7/8 | 5.181 |

元report／method summaryを引用した。[H05] [H05SUMMARY] 主判定は次節の高次残差であり、近似状態のa4誤差を含むfull residualとは別fieldである。

H2のCISDは4/4次元のためexactと一致する。H4は27/36次元のCISDで、保存overlapは0.99946684だが、H05全体のCISDは7/8に留まる。全8条件を独立した近似状態の成功例に数えない。状態energy精度・overlapの良さだけから係数精度を一般保証しない。[H01] [H05]

H01の状態生成時間は、既存Hからのdeterminant生成・部分空間対角化の時間であり、新しい分子のSCF・積分・Hamiltonian取得からの費用ではない。近似状態の品質問題を、追加状態計算や診断の設計で今回救済しない。

## 5. Exact a4＋固定2点と自由fit

`direct_fixed_a4_2_tail`はexact a4をF01参照から入力し、保存されたsigned direct PF shiftからa4*tau^4を引いて、a6/a8をscaled least squaresで取得する。F01 middle窓のinterlaced `holdout_rows`を時刻順に並べた16点の0始まりindex `[11,15]`、保存時刻は

`[0.3931379077393266, 0.65653639279173] Ha^-1`

である。ここでF01に対するholdout時刻はH05のfit入力に再利用されており、H05独立評価という意味ではない。設計選択と評価は同じH2/H4 development集合で行われた。[H05CODE] [FITDIAG] [AUDITMAP]

H05の8/8判定は、exact参照a4/a6/a8の三項モデルが定める、t=0から接続する許容域内のモデル最適時刻t*で

$$
R_{6,8}=\frac{|(\widehat a_6-a_6)t_*^6+(\widehat a_8-a_8)t_*^8|}{\epsilon}\leq0.05,
\qquad \epsilon=0.00015936001019904\ {\rm Ha}
$$

を満たすという判定である。a4誤差、t10以降の打切り残差、direct truthをこの主指標に含めない。t*自体もexact参照係数を使って定める。[H05AUDIT] [H05CODE]

| 保存method ID | 既知prior・fit powers | direct点数 | 高次残差pass | 最悪高次残差／epsilon |
|---|---|---:|---:|---:|
| direct_fixed_a4_2_tail | exact a4、t6/t8 | 2 | 8/8 | 2.829e-2 |
| direct_free_3_tail | なし、t4/t6/t8 | 3 | 7/8 | 5.143e-2 |
| direct_free_5_tail | なし、t4/t6/t8 | 5 | 8/8 | 4.742e-2 |
| direct_order12_16 | なし、t4/t6/t8/t10/t12 | 16 | 7/8 | 1.456 |

元H05 reportの比較であり、新しいfitではない。[H05] 固定2点法の最大a8相対誤差は保存auditで1.95463172257444。高次加重残差passを、a8自体の高い相対精度と同一視しない。[H05AUDIT]

D04の3点fixed/free比較は同点数比較で、fixed3のindex `[11,13,15]`とfree3の`[13,14,15]`は同一座標ではない。fixed5/free5はともに`[11,12,13,14,15]`。点数、時刻配置、a4 priorの情報を分けて読む。[H05CODE] [D04CODE]

## 6. D04の取得費用・memory会計

D04はH05設計を保持した既存小系の費用監査であり、exact a4取得費も課金する。固定2点法が自由5点fitより速かったのは**1/8条件**、推定peak memoryが同等以下なのは**0/8条件**。支持されるのは限定されたdirect入力点数削減であり、一律の古典総費用削減ではない。[D04]

| 保存方式 | median warm秒 | median cold秒 | median PF exponential action数 | median estimated peak MiB |
|---|---:|---:|---:|---:|
| exact a4＋tail2 | 2.1762e-2 | 2.4315e-1 | 96 | 0.4039 |
| free tail5 | 8.5570e-3 | 2.2995e-1 | 240 | 0.2997 |
| dense BCH effective order8 | 5.9836e-2 | 2.8123e-1 | 0 | 0.8703 |

元D04 reportの値を引用した。[D04] [D04SUMMARY] `dense_bch_order8`は小系でD4/D6/D8を含むdense seriesを構築する既存実測であり、D6/D8構築が一切未計測という扱いにしない。そのbackendはH0の完全対角化と再帰摂動を使い、H05 projected solveとは別である。[D04CODE] [BCHSOURCE]

| 指標・範囲 | 保存会計の意味と不足 |
|---|---|
| H05 online | D4作用・保存D6/D8の期待値・solve本体。D6/D8構築、元direct点取得、項生成、応答行列準備等の全工程ではない |
| D04 warm | H04のa4生成・作用時間、反復direct build/Schur時間、fit時間等を組み合わせたmarginal会計 |
| D04 cold | 保存X02 setup時間＋marginal。全方式を同じfresh processで単発実行した総時間ではない |
| direct点のtimer | 既存40座標・7反復のbuild/Schur。overlap選択・unwrap・残差診断の前にtimerが止まる |
| PF exponential action数 | `len(expanded_steps)×point_count`の構造的会計。実expm呼出し数・実時間・量子gate数と同一ではない |
| 方式別memory | 配列shape等からのestimated peak。Python/BLAS workspace等を含む方式別実測RSSではない |
| 再利用 | 同一Hの準備・state・group等を共有できる会計を持つ。新系・別PFの係数取得を無課金にする根拠ではない |
| 未取得の実用費用 | 高精度の増分、一般系のD6/D8、状態取得の詳細、方式別実測peak、全工程の同契約でのscaling等 |

根拠：[H05CODE] [D04CODE] [D04RES] [D04DENSE] [AUDITCOST]。元の会計を再集計せず、古典秒・memory・PF action・量子回路資源を別の指標として保持する。量子state準備・shotsやFT runtimeを含む総資源削減をこの表から主張しない。

## 7. H04 compact D4と残るD6/D8の障害

H04はH4/Yoshidaの168,560 raw commutatorを456 grouped termへ短縮し、保存D4作用に対する最大相対差1.406e-11を報告した。H03のsymbolic生成上の問題はこの範囲で解消済みである。[H04]

同時に、norm-product importance上位項を増やした24曲線中13に非単調悪化があり、signed cancellationを無視したpruningを一般保証にしない。compact項数の減少は、dense Hamiltonian/group入力、状態vector、演算子作用、高精度、状態・参照の取得費を除かない。[H04]

D04の小系dense構築実測と、安価で一般的な高次grouped D6/D8 backendの成立は別である。本草案は新しいD6/D8構築法、source実装、収束検証を追加せず、これらの不足を新しい研究課題として自動再開しない。[D04] [decision record](decision_record.md)

## 8. 移送性・有限時間保証の限界とC1補論との整理

同一の固定H05方式を未使用系へ変更なしで適用した独立評価は、既存静的監査の確認範囲では未確認である。N2/CO、NH3、HF等の三点・五点自由fitや、その予算・安全性評価は別の設計・入力・評価対象を持つ。別方式の成功をH05の移送成功へ転用しない。[AUDITCOST]

参照三項モデルt*での高次残差8/8は、t*のdirect PF真値、全有限時間域、QPE予算の安全性、連続direct最適性を保証しない。これを確認するE2を今回は実施せず、E3の一般理論にも進まない。

| 共通する内容 | 掲載時の整理候補（今回未統合） |
|---|---|
| 対象量・枝・energy origin、proxyと固有値差 | U1-AR C1草案の節1・4を共通定義の候補とし、本補論では参照に留める |
| F02のa8標準混合式 | C1節3と本補論節2が重複する。統合時は一方に定義を置き、もう一方を係数取得・response比較への参照とする候補 |
| Taylor/Magnus・未証明のAR関係 | C1節2・5・7へ参照し、本補論では新しい一般説明・AR原因説を加えない |
| H05の状態・few-point・D04費用／H04限界 | 本技術補論の固有部分として保存する候補 |

この表は掲載時の編集候補であり、既存草案の編集・移動・削除、統合の採択ではない。[U1DRAFT] U1-ARのSTOP、命題R一般形の不採用、未完了証明義務を維持する。[U1DECISION]

## 9. 先行研究との関係と引用範囲

| 固定一次資料・読んだ箇所 | この技術比較との関係 |
|---|---|
| Mehendale et al., `2312.13282v3`、II Eqs.(6)–(9)、III、Appendix A.3–5 | 2次PFの先頭energy係数をBCH期待値から取得し、exact/CISD・分子系を比較。状態依存誤差推定は既知。H05の4次PF subleading a6/a8・固定2点設計の同一検証ではない。[MEH] |
| Maxwell et al., `2606.30738v1`、III.2–3 Eqs.(19)–(21)、Fig.1、IV.1 Eq.(23) | compact BCH・importanceはH04の直接の先行法。Fig.1にはBCH生成時間の比較があるが、項数やその時間をH05のstate・D6/D8・全取得費と同一視しない。[MAX] |
| Hejazi et al., `2412.16811v1`、I Eqs.(3)–(9)、補足Eqs.(23)–(29) | gapped eigenstateに対する既知摂動の文脈。経路gap等の条件と高次状態変形を保持し、a8混合の新発見・普遍的有限時間保証にしない。[HEJ] |
| Baroni et al., `cond-mat/0012092v1`、§II.C導入部、Eqs.(25)/(28)/(30) | 標準一次状態摂動、スペクトル和と射影線形応答の関係を参照。DFPT/KSの費用をH05へ移植せず、Sternheimer型構成の既知性を示す。[BARONI] |
| Sternheimer, Phys. Rev. 96, 951 (1954)、DOI `10.1103/PhysRev.96.951` | 歴史的出典。出版社書誌・abstractのみ確認し、本文は未取得。[STERN] |

各版・byte/hash・実際の確認範囲を[provenance](provenance.json)に記録する。4本の固定本文の関連箇所を確認し、Sternheimer原論文の読了範囲は明確に区別した。無制限の新規性探索や、新しい証明は行っていない。

## 10. 掲載しない主張と草案の終了

- H05が新しいRayleigh–Schrödinger摂動論やSternheimer型responseを発見した。
- 4次PFのa6/a8取得が、6次・8次PFそのものの性能を検証した。
- 8/8という加重残差passが、高い相対係数精度、direct truth精度、全時刻保証、予算安全性、独立移送を同時に意味する。
- 2点という入力数から、a4 prior・state・枝参照・精度・memoryを含む一律の総費用削減が成立した。
- compact D4が一般的なD6/D8構築やend-to-end資源問題を解決した。
- E4のSTOPがH05の実験的否定や、新取得法の一般不可能性を証明した。
- 本補論が第一研究S4の否定結果、既存claim、U1-ARのSTOPを変更する。

H05を第一研究の限定的な技術比較・機構解析として保存する範囲で草案を終える。本原稿への統合・投稿、追加研究・新テーマの選定は別途判断とし、今回自動進行しない。

<!-- fixed-source-references -->

[AUDITCOST]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e2c8527eb10d383c41f161078565e04d29a5df9b/docs/research_audits/pf_u3_h05_completion_20261016/end_to_end_cost_and_transfer_audit.md
[AUDITMAP]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e2c8527eb10d383c41f161078565e04d29a5df9b/docs/research_audits/pf_u3_h05_completion_20261016/h05_method_and_evidence_map.md
[BARONI]: https://arxiv.org/pdf/cond-mat/0012092v1
[BCHSOURCE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/bch_matrix_series.py
[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[D04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/report.md
[D04CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_d04_equal_classical_budget.py
[D04DENSE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/dense_bch_timing.csv
[D04RES]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/method_resources.csv
[D04SUMMARY]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_d04_equal_classical_budget_20260922/method_summary.csv
[F02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md
[F03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md
[FITDIAG]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/direct_fit_diagnostics.csv
[H01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h01_approximate_state_pilot_20260922/report.md
[H04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md
[H05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md
[H05AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/audit.json
[H05CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_h05_higher_order_acquisition.py
[H05SUMMARY]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/method_summary.csv
[HEJ]: https://arxiv.org/html/2412.16811v1
[MAX]: https://arxiv.org/html/2606.30738v1
[MEH]: https://arxiv.org/html/2312.13282v3
[STERN]: https://journals.aps.org/pr/abstract/10.1103/PhysRev.96.951
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7f0b30d215e8094c95ae895b9469a04180e2385e/PF_first_study_final_synthesis_20260925.md
[U1DECISION]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[U1DRAFT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b56a3c79c7c6e421d412e8e0e31b50f087ddf6e5/docs/research_audits/pf_u1_ar_c1_closure_20261016/c1_theory_appendix_draft.md
