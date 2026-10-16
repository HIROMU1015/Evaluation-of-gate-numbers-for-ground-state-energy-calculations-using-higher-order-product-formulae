# 障害を起点とした新アルゴリズム探索：問題と固定証拠

2026-10-16 JST。静的資料調査・概念検討のみ。**抽出した障害5件、構成仮説の限定照合2件、独立研究候補として残したもの0件。** 正式採択・科学実行・新証明は行っていない。

## 1. 入力と証拠の読み方

出発点はEvaluation repositoryのT1-D完結commit `00311e0326f82e80346417c8feb7097c8b22ec76` と、PR repositoryの探索scope `56f1cc55c59ab7bc42c6b24e0953675de9b29b1d`。T1-Dによる撤回と、U1/U3/U4・U1〜U7完結を保持する。[T1D] [U4_DECISION] [U4_CLOSURE]

PRの[coverage map][PR_COVERAGE]は、検討済み・生成規則未特定・既知構成・重要条件未確認・検討記録不足の可能性を区別している。最後の分類を「世界で未解決」「新規」「有望」と読み替えない。[state transition][PR_TRANSITION]に従い、H1〜H4の探索PAUSED、N1 STOP、N2 HOLD、N3 CLOSED、THRIFT現template CLOSED、PF小改変PAUSED、旧D HOLD、SOS-PF現探索CLOSED・A2 NOT_ADOPTED等を維持する。

以下の「障害」は、固定された有限実験で観測された失敗、又は固定技術監査が具体化した入力・構成上の制限である。一般の数学的不能性とは異なる。科学数値を再集計せず、原報告の結論と適用条件を読む。原本reviewの証明を再審査する詳細科学レビューでもない。

## 2. O1：安全なPF校正が、低費用な時刻選択に結び付かない

1. **実現したい計算**：元Hの基底エネルギーを所定精度で求めるPF・時刻・推定予算を、取得可能な近似状態情報から選ぶ。
2. **原因**：状態proxyの精度、PF固有枝との違い、finite-time model、許容時刻域、残余誤差予算は別の判断軸である。riskを検出しても、fallbackが既存baselineと同じ選択なら増分利益は出ない。
3. **固定証拠**：[第一研究final synthesis][FIRST_SYNTH] §§3–7では、S0〜S4完了、S4の二状態診断は固定development集合で `complete_no_benefit`。主集合はN2/COの凍結内殻active-space、HF全電子2条件はstressで、元2 PF・保存grid／exact selected timeの限定比較である。[claim ledger][FIRST_CLAIMS]はS4のbeta不一致を区別しており、原S4の絶対marginを新しい数値主張へ使わない。[第二研究closure][DIRECTION_C_CLOSURE]は、rankを上げたpoint改善と同時刻cheapに対するbudget advantageの不成立を区別する。
4. **既存法が十分でない範囲**：固定二状態risk、一般fallback、point精度向上だけでは当該比較の費用判断を改善しなかった。これは診断一般の無効性ではない。真値を無料入力にして許容域を広げる方法や、別のthresholdを探す方法は解決として採用できない。
5. **解消時に変わる量**：同じ精度・失敗確率の下で、情報取得費を含む総費用又はabstentionが変わり得る。ただし新selectorの成立は今回示していない。

**分類**：既存第一・第二研究の機構／限定成果。新しい回路生成規則の根拠にはならず、U1/U3/U4やFS-R1 Phase Bの再開先にしない。Direction Cの承認scopeも変更しない。[DIRECTION_C]

## 3. O2：coherent平均信号の保証を、一般DF・長時間energy推定へ移せない

1. **実現したい計算**：乱択回路で元Hに対応する複素信号を取得し、phase推定へ接続する。
2. **原因**：平均振幅、平均channel、各trajectory、normalization、visibility、phaseは別の対象である。先導係数の改善や同イベント数の比較は、有限stepの複素信号とnative費用・shotsの改善をそのまま与えない。
3. **固定証拠**：[Track B D1〜D3対応表][PR_S6]は、固定3-system-qubit synthetic involution・固定law・情報層・native価格で、finite多項式と誤差会計を分ける。[M1-S正式契約][PR_S9]はPauli/Hermitian involution、孤立対象state、exact deterministic half等に限定。[Checkpoint後addendum草稿][PR_S8]は、受理済み結果の帰属として固定有限系・小step・固定rの限定保証を整理し、概念的イベント数とnative回路価格を分離する。草稿自体のNOT ADOPTEDとGate 0未承認は維持する。
4. **既存法が十分でない範囲**：norm評価を鋭くすること、共有乱数を使うこと、rhoを改善することだけでは一般DF・guiding state・全RPE費用への移送条件を閉じない。一方、後続の限定受理結果を、旧統合資料だけに基づいて未実施／一括PAUSEDとも扱わない。
5. **解消時に変わる量**：利用できる発展時間、signalから必要shotsへの変換、分割方式の可否が変わり得る。現状の限定定理から一般的改善を認定しない。

**分類**：主に新しい数学的保証が必要になるが、既存Track Bの研究対象である。本作業の独立候補に移さず、証明・law変更・DF拡張を開始しない。

## 4. O3：有限標本の回路費用から、母平均の資源優位を認定できない

1. **実現したい計算**：同一精度のfinite complex-signal taskについて、測定込みcompiled資源を比較する。
2. **原因**：希少Taylor次数の未観測、history依存の回路価格、経験的数値allowance、候補選抜後の有限確認集合により、標本平均と母平均の保証が分かれる。強い決定論baselineと状態準備費用も順位に関係する。
3. **固定証拠**：[Track A H6確認結果][PR_S5]はlinear H6、1.00 Å、STO-3G、12 modes、alpha3/beta3 sector400、tol-only DF rank19、T=.8、prefix5の固定8構成、q=1/2/4/8、r=4/4/4/2、K2/K4、独立32 trajectory。Qiskit1.3/opt1/rz,sx,x,cx/no routing、準備P=0のsignal資源であり、母平均winnerを認定していない。[後続B0+I比較][PR_S10]は同H6のprefix5/10/15・q1/2/4/8の強い対照を追加し、取得済み集合のPR点優位は残した。これを「強対照で優位が消えた」と改変しない。[V2 readiness][PR_S11]はlaw・primitive・phaseと費用のbinding準備を行ったが、実H6の新理論費用は未評価とする。
4. **既存法が十分でない範囲**：標本SEや経験allowanceを、未観測tailを含む厳密母平均保証と呼べない。追加標本数が足りないというだけの問題ではなく、母分布と回路価格の対応・range/tailの情報契約が必要である。ただし完全lawに基づく既存費用モデルを接続する課題は、既にTrack A V2のscopeにある。
5. **解消時に変わる量**：資源比較の保証水準と、準備費用込みでどの選択が有効か。ただしここでのepsilonはsignal精度であり、Ha単位の最終energy精度ではない。

**分類**：既知の会計・実装接続と既存研究の保証課題。新たなproposal最適化、whole-path sampling、R5再開、保存値再解析には進まない。未実装のadapterを独立原理の根拠にしない。

## 5. O4：表現上の改善が、物理部分空間を保つ安い回路にならない

1. **実現したい計算**：元Hを保った表現から、安価でcoherent controlled可能な時間発展を生成する。
2. **原因**：factor／Pauli-weight proxy、PF近似誤差、basis変換費用は別量。さらにgenerator又は補正平均の部分空間保存は、個々のtrajectory／平均channelの保存と同じではない。
3. **固定証拠**：[表現探索toy報告][PR_S12] §§3–4・7–8。Aは2／3 modes・rank2・一体/定数0のsynthetic full-Fock例で、proxy／tail改善とPF誤差・compiled費用の競合を示す。Bは1 auxiliary＋1 systemの指定toy・K0/2/4で、補正平均とevent leakageを分け、whole-word twirlの代用が正しいgenerator平均にならない例を保存した。compilerはQiskit1.3/opt1/rz,sx,x,cx、topologyなし、準備・測定・FT合成は対象外である。分子・最適回路の下界ではない。
4. **既存法が十分でない範囲**：共通共役、factorの直交混合、単純echo／反射だけでは費用と正しい作用を同時に保証しない。既存レビューは可解mixed oracleや局所代数まで扱っているため、ここからN1/H3やTHRIFT現templateを再開しない。[PR_COVERAGE]
5. **解消時に変わる量**：basis／parity計算の重複、controlled depth、追加qubit、元Hへのbias。ただしどれか一つの減少で総費用改善とはしない。

**分類**：新回路生成規則が必要になり得る。狭い審査用仮説X1「code上で同値な演算子代表とparityネットワークをword全体で選ぶ」をPhase B/Cで検討した。結果と不採用理由は[構成原理資料](constructive_principle_candidates.md)に記す。旧圧縮反射法のlawを変更する案ではない。

## 6. O5：ground copiesは、安い絶対energy測定器を与えない

1. **実現したい計算**：既知の元電子Hと供給される対象ground copiesから、絶対E0を所定精度・成功確率で読む。
2. **原因**：H全体のprojective測定と、分解項の実行可能な測定は異なる。exact eigenstateでHの分散が0でも、個別測定の分散が0とは限らない。copies、coherent準備／逆準備、既知reference、複数copy操作は同一accessではない。
3. **固定証拠**：[静的K0報告][PR_S1] §§4–5と[open problem landscape][PR_PROBLEMS]観点C4が、このaccess障害と既知direct測定の対照を明示する。**これは固定技術監査の構造的な障害で、実分子での新たな失敗計測や全測定法の下界ではない。** H2の個別UNDETERMINEDとH1〜H4 PAUSEDは保持する。
4. **既存法が十分でない範囲**：uncontrolled channelの位相不変性は、既知Hの直接測定を禁止しない。一方、RDM／joint測定の存在だけでは、無料のstate情報・符号・coherent inverseや無視した準備費用を正当化できない。
5. **解消時に変わる量**：必要copies、測定回路depth、coherent操作の必要性。ただし近似状態の期待値を元HのE0と同定する保証は別途必要である。

**分類**：新しい情報取得規則が必要になり得る。X2「energyに特化したjoint測定／copy間の情報再利用」を限定照合した。一般filter比やphase referenceへ戻る構成はH2/H4の再開になるため扱わない。

## 7. Phase Aから先へ送る条件

| 障害 | 必要になり得る仕事 | 本作業での扱い |
|---|---|---|
| O1 | 新しい運用情報／selector | 既存限定成果と停止境界を記録。再設計しない |
| O2 | 新しい数学的保証 | 既存Track Bに帰属。新証明・拡張なし |
| O3 | 既知手法のbinding・費用保証 | 既存Track A V2等との重複。新候補にしない |
| O4 | 新回路生成規則 | X1を概念検討・限定文献/source照合 |
| O5 | 新情報取得・推定規則 | X2を概念検討・限定文献照合 |

O4/O5も、未測定・未実装・記録不足だけでは研究候補にならない。次資料は、入力→処理→出力の仮説を具体化して既報と比べた記録であり、独立した新原理の成立証明ではない。**候補0件は今回の限定探索結果で、分野全体の一般no-goでも正式な新しいSTOP採択でもない。**

既存SOURCE・結果・STOP・authorization等を変更せず、新規4資料のみを公開する。科学計算・保存値再解析・回路生成／compile・科学実装・新証明は0件。公開照合後Mandatory STOP。

<!-- fixed-source-references -->

[DIRECTION_C]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md
[DIRECTION_C_CLOSURE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/second_study_v2/evidence_integration_20261006/approved_closure.md
[FIRST_CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/PF_first_study_paper_claim_ledger_20260926.md
[FIRST_SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/PF_first_study_final_synthesis_20260925.md
[PR_COVERAGE]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_coverage_map.md
[PR_PROBLEMS]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/open_problem_landscape.md
[PR_S1]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/0d460c54f3bf54ea46d4d8129f6702703c4bb217/docs/research/qc_new_algorithm_static_screen_k0_20261016/technical_report.md
[PR_S10]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dd695e6584f15b88341d2446ed010c7bdfef1666/docs/research/track_a_h6_native_b0i_full_family_results_20261015.md
[PR_S11]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dd695e6584f15b88341d2446ed010c7bdfef1666/docs/research/track_a_v2_h6_cost_binding_readiness_20261016.md
[PR_S12]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/0d460c54f3bf54ea46d4d8129f6702703c4bb217/docs/research/representation_exploration_initial_validation_20261010.md
[PR_S5]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/0dd5c3d204dab9b731268a1aa2add621080f3d20/docs/research/track_a_h6_independent_confirmation_result_v1.md
[PR_S6]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d3a232a446062e6baadef2b69eab87faa0285363/docs/tracks/algorithm_codesign/d1_d3_prior_art_claim_evidence_and_gpt_handoff_20261014.md
[PR_S8]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/05513eea807fbfb841c6012d2fe2133d70b5f1f9/docs/tracks/algorithm_codesign/m1s_g0t1_post_checkpoint2_theory_addendum_draft_20261016.md
[PR_S9]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/373b8e4b9831f4d00bdc00ffc741ac61e03f0841/docs/tracks/algorithm_codesign/m1s_g0t1_s0_formal_theory_contract_20261016.md
[PR_TRANSITION]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_state_transition.md
[T1D]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/research_exploration/t1_withdrawal_20261016/decision_record.md
[U4_CLOSURE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/audited_candidate_scope_closure.md
[U4_DECISION]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/decision_record.md
