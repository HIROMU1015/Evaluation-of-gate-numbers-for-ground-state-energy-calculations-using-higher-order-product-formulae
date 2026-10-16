# 第一研究・限定理論補論草案：有限時間PF誤差の対象量と局所展開の限界

2026-10-16 JST。**独立した草案。既存原稿には未統合。** ユーザーが承認したU1-AR追加研究STOP・C1整理に従う。[決定記録](decision_record.md)を参照する。本書のC1は完結経路であり、既存paper claim ledgerの行ID C1の改訂ではない。[SYNTH] [CLAIMS]

本補論の役割は、第一研究の既存結果を解釈する際に、固有位相、状態に依存するproxy、局所係数、有限時間の適用範囲を区別することである。新しいAR因果説、独立新規定理、資源削減法を主張しない。Claude再レビュー`レビューoutter(6).md`原文は未確認であり、ユーザーが列挙した修正事項を採用した。

## 1. 対象量、符号、sectorと枝

同一の固定sectorで表した有限次元Hermitian Hamiltonian Hと、そのsectorの基底対(E0, |0>)を考える。以下の局所非縮退摂動の記述では、E0が当該sectorで単純・孤立している場合を扱う。別sectorにある状態や、縮退を持つ場合への拡張は自動的には含めない。

repositoryのX02等の正符号規約に合わせ、PF一stepをU_P(tau)とし、その固有値をexp(i theta_j)と書く。tauは外側一stepの時間、単位はHa⁻¹である。内部stageはPF係数×tauであり、QPE全体の総進化時間ではない。選択された位相のliftをtheta_sel＋2pi ellとすると、非零tauでの対象の符号付きshiftは

$$
\delta_P(\tau)=\frac{\theta_{\rm sel}(\tau)+2\pi\ell(\tau)}{\tau}-E_0.
$$

ellは記録されたunwrap規則による整数で、Hの励起状態IDではない。短時間からE0へ接続する対象枝を意図することと、実軸全域でその枝が一意・解析的に追跡されたことの証明は区別する。負符号の時間発展を使う文献を引用する場合は、その符号規約を保って対応を読む。[X02CODE] [DEFINITIONS] [REN] [HEJ]

HとE0は同じenergy originでなければならない。H-chain準備ではgroupからidentity項を除いたHと非定数部分のE0を使う。HFのmidpoint処理・scalar復元やNH3のremoved constantも各sourceの定義を保持する。global scalar shiftと異なるoriginの混在を同一視しない。phase cutまでの距離、位相対の円周距離、unwrap整数は別の量である。[DEFINITIONS] [DATA]

| source | 選択枝とliftの既存規則 | 本補論での限定 |
|---|---|---|
| X02／それを継承するF05 | 初点はexact-ground overlap最大。以後はprevious selected vectorとのoverlap最大。unwrap参照は初点E0、以後previous effective energy | maximum-ground候補との一致は別診断。Schur列indexを永続的物理state IDにしない |
| HF mechanism bridge | 各点でexact-ground overlap最大。unwrapも各点のE0に近いlift。previous overlapは診断 | X02と同じ継続枝契約ではない |
| NH3 direct point | 各点でexact-ground overlap最大。E0で回転した固有値のprincipal angle/tauをshiftとする | X02型の逐次unwrapとは異なる。後のNH3比較で追跡規則の一致が確認された範囲を一般化しない |

根拠：[X02CODE] [HFCODE] [NH3CODE] [NH3AUDIT]。第一研究の既存branch auditが確認した再現性・条件範囲を保持し、この表を根拠に全runが同じ規則だったと改訂しない。[CLAIMS]

## 2. 既知の局所摂動論と円周上の隔離

原点近傍のlogの枝と規格化を選び、H_eff(0)=Hへ接続する局所展開を扱う。U_P(0)=Iではunitary固有値が全て1に重なるため、「原点でunitary固有値が単純」という仮定は使わない。局所の対象選択はHの孤立固有値と、H_effの展開を用いて定める。[REN] [F01]

Rendon–Watkins–Wiebeの§3.2.1 Lemma 11はnormal行列AのスペクトルとBの固有値の距離をspectral normで抑える既知結果である。Lemma 12／Appendix D.1は複素近傍でのH_eff−Hのノルム上界と原点gapを使った解析領域の保証である。ここではその仮定をrepositoryの全PFへ検証したとは主張しない。本文のr_maxという名称を、実際の最大Taylor収束半径の決定・実軸の共鳴閾値へ読み替えない。[REN]

円周摂動の比較対象として、固定した非零tauにおける選択unitary固有値と他の固有値との隔離を考える。保存された角距離は

$$
d_\theta(\tau)=\min_{j\ne{\rm sel}}
\left|\operatorname{Arg}\exp\{i(\theta_j-\theta_{\rm sel})\}\right|.
$$

円周上の角距離と、複素平面上のunitary固有値間の距離、bare Hのenergy gapは異なる指標である。normal行列の摂動に関するスペクトル近接結果だけで、相手状態の物理的対応、固有vectorの混合量、一意な継続、誤差モデルの成否までは確定しない。孤立性・摂動の大きさ・結合・対象枝を指定せず、d_theta/tauを摂動公式のenergy分母へ代入しない。[REN] [X02CODE] [DEFINITIONS]

この円周上の整理は既知摂動論を読むための定義であり、新しい「円周摂動定理」を提示したものではない。実軸上の位相近接は、複素パラメータ平面における特異点の位置やTaylor収束半径の直接証拠ではない。今回、その関係を証明・反証・計算していない。

## 3. 4次PFの高次係数と状態混合

F01/F02で用いた局所展開を

$$
H_{\rm eff}(\tau)=H+\tau^4D_4+\tau^6D_6+\tau^8D_8+\cdots,
\qquad
\delta_P(\tau)=a_4\tau^4+a_6\tau^6+a_8\tau^8+\cdots
$$

とする。exactな非縮退基底状態、同じH/sector/basis、適切なlogの局所展開というF02の条件で、既知の固有値摂動により保存された係数の構成は

$$
a_4=\langle0|D_4|0\rangle,\qquad
a_6=\langle0|D_6|0\rangle,
$$

$$
a_8=\langle0|D_8|0\rangle+
\sum_{n\ne0}\frac{|\langle n|D_4|0\rangle|^2}{E_0-E_n}.
$$

後半はD4による二次状態混合であり、基底状態の正の励起gapの下では非正の寄与となる。縮退励起空間の個別vectorへの配分はbasis依存なので、F02は縮退energy群への和も保存する。近似状態へ置換した期待値を、このexact固有値係数のidentityと呼ばない。[F02] [F02CODE]

これは4次PFに対する時間次数6/8の係数であり、6次・8次PF全体への実証ではない。各係数値とtauのべきを掛けた有限時間energy寄与を区別する。保存fieldの`_hartree` suffixを理由に、混合係数自体を有限時間energy shiftと読み替えない。[F01] [DATA]

Hejazi et al.のEq.(4)・Eq.(9)と補足Eqs.(23)–(29)も、状態変形と高次摂動の扱いに関係する既知結果である。同論文は経路全体の非消失gapを仮定する。Eq.(9)のO(s^(2p))という剰余の境界を、p=4でa8の状態混合が無いという主張に使わない。原点の物理gapだけで有限step全域の仮定を満たすとはしない。[HEJ]

F02のH2/H4×4 PFではa8の成分identityを確認済みで、最適化PFでは正のD8期待値と負の混合が相殺する。F03では小a4と小D4全体を区別した。これらは高次項の重要性・状態感度を説明する既存成果であり、折り返し共鳴が原因だとする新しい結論ではない。[F02] [F03]

## 4. 状態proxyと対象固有位相の差

第一研究のecho proxyは、既存sourceの正符号規約で

$$
g_\psi(\tau)=\frac{\operatorname{Im}
\langle\psi|e^{-iH\tau}U_P(\tau)|\psi\rangle}{\tau}
$$

と定義される。amplitudeのargument/tauを使うproxyは別の量であり、そのunwrapにも別の記録がある。[PROXYCODE]

exact |0>ではe^{-iE0 tau}による回転となり、同じU_Pの固有vector |v_j>を用いた既存のspectral表現は

$$
g_0(\tau)=\sum_j w_j(\tau)
\frac{\sin(\theta_j(\tau)-E_0\tau)}{\tau},\qquad
w_j=|\langle v_j|0\rangle|^2.
$$

この式は既存資料の再掲で、新しいspectral解析や寄与の再集計を行っていない。[X02CODE] [EXPANSION] exact stateを使ってもproxyは複数のPF固有成分の重み付き量であり、選択された単一枝のdelta_Pとの一致を定義に含まない。

小時間に関しては、局所摂動が適用でき、同じ枝・H・sector・originを使い、対象信号が数値精度に対して識別できる範囲で比較する。単一成分のsineを位相そのものへ近似する条件と、他成分の重みを無視できる条件は別である。高いselected-ground overlapだけから、他成分の寄与や有限時間のproxy差を一律に抑えたとはしない。

また、`<0|(H_eff−H)|0>`という有効Hamiltonianの期待値proxyと、上記sine/echo proxyを同一視しない。F02でa8に混合項が入ることは前者と対象固有値の違いを説明するが、そのまま後者の任意有限時間の剰余boundや一律の収束次数を与えるものではない。本草案は小時間のproxy差について新しい漸近式・上界・定理を作っていない。

第一研究の既存分解

$$
\widehat f_\psi-\delta_P=
(\widehat f_\psi-g_\psi)+(g_\psi-g_0)+(g_0-\delta_P)
$$

は、model fit差、状態置換差、exact-state proxyとPF固有値の差を分けるために保持する。三成分の符号付き相殺、development集合、保存grid、資源proxyの限定も変更しない。局所係数やproxy精度がよいことだけから、使用域全体の安全性、低regret、資源削減を結論しない。[SYNTH] [CLAIMS] [PHASEB] [PROXYCODE]

## 5. Magnus/BCHの十分条件と固有枝のTaylor収束

Moan–NiesenのTheorem 3は、原論文の実可積分行列A(s)によるY'=A(s)Y、Y(0)=Iに対し、integral ||A(s)||_2 ds < piならMagnus級数が収束し、その和Omegaがexp(Omega)=Yを満たすという十分条件である。§5 Example 1はこの条件が必要条件ではないことを明記する。条件外を発散域と扱わない。[MAG]

この定理の対象と、指定した固有energy枝のTaylor級数の収束半径は異なる。作用素logの選択、展開パラメータ、複素領域の固有値の隔離を分けて確認する必要がある。PFの複素生成子、負係数stage、積の順序、ノルム、identity gaugeを原論文の仮定へ対応させる新しい証明はここで行わない。十分条件の式を未検証のままrepository全PFへ適用したとは書かない。[MAG] [REN] [DEFINITIONS]

`tau W_S >= 2pi`は、Taylor発散、AR発生、PF誤差モデルの失敗の保証として採用しない。W_Sの原定義は再レビュー原文から未確認であり、本補論で新しく定義・算出しない。仮に特定sectorのenergy幅を意味する文脈でも、円周への位相写像の曖昧性と、作用素logや対象固有枝の解析性を同じ条件にしてはならない。[LITERATURE] [DEFINITIONS]

有限次の有効Hamiltonianが折り返し共鳴を一切表現できないという命題Rの一般形は、ユーザー指定の修正として撤回し、本補論には採用しない。局所打切りの精度、作用素級数の収束、固有位相の折り返しは区別すべき対象である。撤回を埋め合わせる新しい不可能性定理・反例・修正版命題は作らない。

## 6. 既存数値結果に対して許される読み方

| 固定資料 | 本補論で用いる既存結果 | 導かない主張 |
|---|---|---|
| F02 | H2/H4×4 PFのa8はD8対角とD4二次混合を含み、相殺がある | 有限tauの最近接PF相手状態・ARの同定、任意系の有限時間保証 |
| F03 | 小さいa4は小さいD4や小さい励起結合を意味しない。元の人工族は既存結果として保持 | 今回の新しい反例構成、H4/HFのAR原因の証明 |
| F05 | H2/H4×3 PFで物理gap・D4結合・円周gapを区別。最初のwarning全6条件にground overlap低下を含み、絶対phase-gap gate単独の発火は0/6と元reportが記録 | warning時刻＝AR onset、最小円周gapの相手＝支配的D4混合励起群 |
| HF bridge | Yoshida4二項のeq pass／stretch150 failを保持した診断。複数の機構量が共変し、元報告は唯一原因の証明を主張しない | 内殻励起が原因という確立結果、F05やH4との同一枝契約 |
| 第一研究S0〜S4 | 機構・信頼性研究は完了。S4診断の固定結論はcomplete_no_benefit | 補論による方法論上の成功への再分類、独立分子transfer保証 |

根拠：[F02] [F03] [F05] [HF] [SYNTH] [CLAIMS]。数値・件数は元報告の引用であり、保存CSVを再集計していない。F02/F03の同じF01 input hashは原manifestで確認できるが、F01とX02のH/basisの共通byte identityまでは旧監査で未完結だった。名目system/PFの結合を、厳密な共通basisの証明に格上げしない。[F02MAN] [F03MAN] [DATA]

最近接PF位相の相手ID・H励起状態への対応、H4のRegime II、HFの内殻励起仮説は未確立として扱う。H4 Regime IIという名称に、本草案から新しい数値境界や確立した機構を与えない。F05のwarningは有限保存grid上のOR判定であり、連続時刻での根・特異点・共鳴時刻の測定ではない。[F05] [DEFINITIONS] [DATA]

## 7. 未証明事項と掲載対象外の主張

次の表は執筆時の制約であり、証明を進める作業計画ではない。旧命題のラベルを新しい定理番号として流用しない。

| 旧ラベル／論点 | 本草案に残す限界 |
|---|---|
| A：実軸全域の解析的・一意な接続 | 局所gap付き結果や離散overlap追跡から全実軸への延長は証明していない |
| B：ARとTaylor半径 | 実軸の位相近接から複素特異点・真の収束半径は決定していない |
| M：Magnus/BCH条件のPFへの移植 | 引用定理の十分条件と、対象PFのstage・複素生成子・gaugeへの適用確認を区別する |
| N：局所係数による有限時間判定の一般不可能性 | 対象クラス・入力情報・領域・許容精度を固定した証明はない。一般不可能性を掲載しない |
| C | 原命題の正確な文面・証明義務を取得できていない。推定した命題を代作・証明済み扱いにしない |
| R：有限次HeffでAR表現不能という一般形 | 撤回・不採用。新しい反例や修正版の理論研究は行わない |

文献から引用する既知結果、保存結果、仮定、未証明事項を区別する。一般的な新規性・独立論文の成立や、U1-AR追究の再開をこの補論から導かない。再開・本原稿統合・投稿には別承認を必要とする。[HANDOFF] [LITERATURE] [decision record](decision_record.md)

## 8. 引用版と草案の停止点

今回本文の関連箇所を直接確認した一次文献は、Rendon–Watkins–Wiebe `2212.14144v4`のLemma 11/12・Appendix D.1と局所Heffの定義、Moan–Niesen `math/0609198v2`のTheorem 2/3・§5 Example 1、Hejazi et al. `2412.16811v1`のEqs.(3)/(4)/(9)・補足Eqs.(23)–(29)である。いずれも固定PDF版を取得し、byte/hashを[provenance](provenance.json)へ記録する。新しい証明や定理全体の独立再検証はしていない。他の先行研究との対応は固定U1-AR文献監査を参照し、今回9論文全体を再レビューしたとは主張しない。[REN] [MAG] [HEJ] [LITERATURE]

第一研究の中心claimと数値結果はfinal synthesis／paper claim ledgerの限定を保持する。草案はここで終了し、P1-A1〜A4、新しい科学計算・保存値解析、未完了証明の補完、既存原稿への統合へ自動進行しない。

<!-- fixed-source-references -->

[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/PF_first_study_paper_claim_ledger_20260926.md
[DATA]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/stored_data_availability.md
[DEFINITIONS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/definition_contract_audit.md
[EXPANSION]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/19362c23ccdc16b6ad0ff547cc363e138a3930d2/docs/research_outcomes/20261007/validation_expansion_results.md
[F01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/report.md
[F02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md
[F02CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_f02_tau8_state_mixing.py
[F02MAN]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/manifest.json
[F03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md
[F03MAN]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/manifest.json
[F05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f05_energy_phase_gap_20260922/report.md
[HANDOFF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/gpt_decision_handoff.md
[HEJ]: https://arxiv.org/pdf/2412.16811v1
[HF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md
[HFCODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/review_response/run_f_hf_mechanism_bridge.py
[LITERATURE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcdd405f49874f308a8abd433dae49cca5cd6e/docs/research_audits/pf_u1_ar_p1_static_preflight_20261016/literature_correspondence.md
[MAG]: https://arxiv.org/pdf/math/0609198v2
[NH3AUDIT]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/76d091f18b7f68b2612dc2c8267bbab5e23c12a1/artifacts/server_nh3_branch_protocol_audit_20260920_222119_d8c1d55/report.md
[NH3CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/run_full_electron_nh3_higher_term_diagnosis.py
[PHASEB]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/artifacts/pf_first_study_phase_b_20260925_5a2f0a2/report.md
[PROXYCODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/review_response/pf_first_study_experiment_a.py
[REN]: https://arxiv.org/pdf/2212.14144v4
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7f0b30d215e8094c95ae895b9469a04180e2385e/PF_first_study_final_synthesis_20260925.md
[X02CODE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/review_response/audit_x02_curve_model_integrity.py
