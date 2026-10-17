# PR最新2ブランチ：固定SOURCEに基づく差分

2026-10-17 JST。基礎はEvaluationの既存横断整理 `609a63231ee0786cf8da31f6b33358acfd6f2548`（[旧handoff][O01]）とPRの既存整理 `d09ba606a9fceef806a9313e3f7c43cd21d19e3f`（[既存20方向][P02]）。両整理を保存し、指定2ブランチの追加情報だけを記録する。本書の数式・科学的結果は固定資料の報告内容であり、今回新しい検算・証明・科学レビューは実施していない。

## 1. 固定対象と資料の役割

| 対象 | branch・固定commit | 位置付け |
| --- | --- | --- |
| A：有限step相対形式保証 | `qc-relative-form-finite-step-audit-20261017` / `051df4661eeffb6c6c4c978f70f43eeeaadfddd6` | 技術監査payloadは `f70acc51644f43fc35ad73edfdc3f180a9ce1f4f`。最終snapshotは公開receiptも含む。[handoff][A01]・[数学的監査][A02]・[先行研究表][A03] |
| B：H8主要6軸直接compile | `track-a-h8-key-compile-parallel-handover-20261017` / `ce6cd8ead5c0311ec72165c04869e7df4050b75b` | [完了報告][B01]・[研究ノート][B02]・[6軸保存値][B03]・[公開監査manifest][B04]。文書commitと実行SOURCEを区別 |

`source_registry.json` は各資料のorigin/result commit（当該pathの文書来歴）とverified snapshot commitを別fieldで保持する。Bの科学実行SOURCEは後述の旧・新2件であり、公開文書commitへ置換しない。

## 2. A：何が追加で確認されたか

### 2.1 A2との発展関係と原本公開

SOS-PF A2の保証理論を、全vector相対形式、有限step剰余、energy window、固定powers QPEへ具体化した**限定技術監査**である。独立した有利なPSD分割生成算法を得た記録ではない。分類は **`VALID_WITH_UNRESOLVED_NOVELTY`**。固定監査が明示仮定内で中心命題に重大な欠陥を見つけなかったという意味であり、新定理のpriority、科学的採択、実用的優位の認定ではない。[A01][A03]

旧横断整理L05でローカル観測として記録したGPT再設計レビュー原本は、今回の[公開inputs原本][A06]と同一である：38,606 bytes、SHA-256 `954bd40d1da7dce70a4b97336c71d1cd55031314df9c339a2de95b82fabf8527`、Git blob `3fde7ed394579395ee3836060e03782c12629d80`。**原本は現在、固定commitで公開取得可能**。旧「未公開」の記録は当時の観測として保存し、最新の取得不足とは数えない。公開は原本の全claim・承認記述の独立認証や正式採択を意味しない。[O07][A05][A06]

### 2.2 保証の対象・条件・限界

以下は[数学的監査][A02]の保存されたstatementの要約であり、本作業による再導出ではない。

共通条件：有限次元の同一不変sectorで `H=L I+G`、`G=ΣF_j`、`0≼F_j≼f_j I`、`Λ=Σf_j`。**各logical fragmentもsectorを保存**する。正のstageからなるpalindromic `S2(h)` と、原点近傍の解析的log `K(h)=i Log S2(h)/h` を用いる。既知の認証下界L・上界Uから `W=U−L≥e=E0−L≥0` を得る。eやground vectorは係数から無料で与えられる入力ではない。

| 項目 | 固定監査が成立と記録した対象 | 必須条件・残る境界 |
| --- | --- | --- |
| RF0 | 全vectorで `−η0 G≼K−G≼η0 G`、`η0=32(hΛ)^2/[1−16(hΛ)^2]` | `abs(h)Λ<1/4`、同じPSD分割・caps・S2。ker Gを含みGの逆を要求しない。負stage高次PFへの保証ではない |
| RF1/K0 | 既存K0の辞書・非負対称B・行和 `K_SOS` で `−K_SOS G≼D≼K_SOS G`。有限剰余 `ρ4=512(hΛ)^4/[1−16(hΛ)^2]` と `η1=h²K_SOS+ρ4` | 先導D・raw κの新規性ではない。RF0と同じ領域・認証caps。旧K0のscalar剰余 `r4 I` と今回の `ρ4 G` を区別。有限精度・証拠生成費は未取得 |
| EW | Kのenergy測定Yに対し、ground支持入力上で下側支持 `(1−η)e`、上側tail `Pr(Y>e+d)≤2ηe/(d+ηe)` | `η<1` とexact ground space支持（縮退可）が必要。`d≥ηe` なら下側tailは0。既知Wで `ηW≤α_spec d/(2−α_spec)` を満たす十分条件。低変分energyだけではgapなしにground品質を得ない |
| QPE/step | 同一の固定S2の整数powers、既知supportとunwrap、一様な読出し保証、別誤差予算の下でEWから出力保証に接続 | scalar Lを一回復元し、既知centeringもcontrolled phaseに保持。準備・モデル差・synthesis・実装・読出し・certificateの予算/費用を払う。通常QPE操作そのものは既知 |

`η=min(η0,η1)` の使用は同じG・S2・capsの共通条件内に限る。EWにはlog領域だけでなく `η<1` が必要。`h=0`、`Λ=0` 等の自明caseを分離する。未知gapはEWの入力ではないが、exact ground copiesや近似stateのtrace-distance証拠の取得費は消えない。EWの測定分布を平均複素signalや多round RPE/M1-Sの保証へ自動移植しない。[A02][A03]

原本の補助式(29)は、非自明eventに `0<|h|d≤π`、対象supportに `|h(Y−e)|≤π` が必要と補足されている。空event・h=0は別扱い。中心RF0/RF1/EW/QPEの証明はこの補助式に依存しない。原本を訂正せず、適用域の補足として記録している。[A01][A02]

### 2.3 既知研究との関係、未確定事項

[先行研究表][A03]の記録を再利用する。今回、以下の文献PDFを新たに取得・再監査したわけではない。

| 既知資料 | 固定監査の対応整理 | 今回も未判定の内容 |
| --- | --- | --- |
| SOS-PF K0/K0.5 | κ・B・行和、先導係数は既存。K0.5にもgap-free operator/QPE保証と強いChilds S2対照がある | RF0を旧粗い残差だけと比較して新規性/実用優位を決めない |
| Mizuta–Kuwahara `2504.20746v1` | PSD k-local、extensiveness、群内可換性、低energy支持でcommutator・leakageを含む有限時間PF保証が既知 | 全vectorのLoewner/log/有限領域を含む同一statementへの完全還元は未提示。DFを全supportで扱う粗い特殊化は排除しないがk・群数等の価格を保持 |
| Hejazi–Zini–Arrazola `2402.10362v1` | locality/degree/群内可換性、retained成分と漏洩、fermion even項条件 | cutoff支持と低期待値は同じでない。PSD shiftがcutoffを悪化させる費用も必要 |
| Maxwellほか `2606.30738v1` | compact BCH/先導係数・漸近dephasingは既知。固定監査はAppendix Aのgap分母も指摘 | 一様gap-free有限h相対log剰余へ置換しない。論文全体の否定ではない |
| N3 occupation certificate | PSD/認証という研究領域で接する既存別課題。Schur/Fantope/SDP/SOS、縮約・encoding等の条件がある | A2のRF0と同じ入力/出力・証拠生成規則とは認定しない。N3現検証系列CLOSED、理論/限定prototypeの条件付き保持を維持 |

「gap不要の有限step保証一般が存在するか」を新しい未解決問題として再提案しない。全statementの完全な既知定理対応、出版版/後続版との同一性、網羅的priorityは未確認。有用なh、W/Λ、認証K_SOS、PSD/下界証拠のbit長・古典取得費、controlled native費、state準備・readout込み総費用は未測定である。未測定を0と置かない。[A03][A04][P02]

### 2.4 状態と承認

A1現分割生成探索は **CLOSED**、A2は **NOT_ADOPTED**、K1-Fは **NOT_AUTHORIZED / NOT_EXECUTED** のまま。VALIDは技術分類であって状態変更ではない。[A04][A05] は追加実行を許可せず `automatic_next_phase=false`、mandatory STOPを記録する。レビューを勧める記述もレビュー実行承認ではない。

## 3. B：H8主要6軸直接compileの完了

### 3.1 固定条件

[完了報告][B01]・[保存JSON][B03]：linear H8、隣接1.0 Å、STO-3G、saved DF rank28、16 modes、sector次元4900、総時刻T=0.8、saved signed generation order、unrotated saved full H参照。prefix11/15、q1/4（microstep0.8/0.2）の登録3構成。B0+Iはown-prefix/full-Fock scalarを保持。controlは `symmetric_directional`。S4は**負のmiddle stageを持つ非mergeの3×S2 Yoshida**。

compiler `1239304c14c65cde2e66ac783646abae19455ad8af6ce0cafd157557eeabb33b`、profile `622ce4a8391002558b877240b48d831d9bb0a72aeabba2e4d73bfec64b9c9f12`、固定モデル `8420b9f247c63f47f10f40ba5e875f5ed971e8948ea6748b9845698fe6bdb8b0`。再fit・閾値緩和は行われていない。[B03]

### 3.2 保存実測値（再解析なし）

以下は `selected_axes` の保存値の転記。相対誤差の再計算・集計・順位付けはしていない。判定欄も保存された `model_check.PASS` を引用する。[B03]

| 登録構成 | 軸 | RZ | CX | depth | 保存モデル相対誤差 % | 保存判定 | 実行SOURCE |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| B0I_p15_q4_4th | cosine | 668636 | 297968 | 221226 | 0.21690212825598895 | PASS | 旧SOURCE、再利用 |
| B0I_p15_q4_4th | sine | 668636 | 297968 | 221226 | 0.21690212825598895 | PASS | 新SOURCE |
| B0I_p11_q1_2nd | cosine | 42268 | 18576 | 13786 | 0.8270356500696238 | PASS | 新SOURCE |
| B0I_p11_q1_2nd | sine | 42268 | 18576 | 13786 | 0.8270356500696238 | PASS | 新SOURCE |
| B0_p15_q4_2nd | cosine | 223940 | 99600 | 73930 | 0.2158741499636382 | PASS | 新SOURCE |
| B0_p15_q4_2nd | sine | 223940 | 99600 | 73930 | 0.2158741499636382 | PASS | 新SOURCE |

旧SOURCEは `352581103b7dbd4fa58e28af7a6ca65570d36e8e`、新SOURCEは `41e466e13f32e9224bb37790cc16f0ff6621c399`。旧S4 cosineの1軸だけが再利用され、新規5軸と合わせたlogical6軸。中断された旧S4 sineは再開可能な測定結果として流用されず、旧予約call（中断分を含む）はnonrefundableとして保存されている。旧STOPを完了へ書き換えない。[B01][B03]

固定資料は全6軸で契約のモデル誤差2%未満を満たし、native exit0・reaped、最終gate PASS、2026-10-17 **22:15:38 JST**完了と記録する。状態は **`PASS_ONLY_SIX_REGISTERED_AXES_MANDATORY_STOP`**。[旧handover][B05] のRUNNINGは途中時点の観測であり、この完了資料が後続記録である。今回compile・control probe・QPY処理は行っていない。

### 3.3 Phase C・非相殺費用比較への位置付け

旧横断整理が扱ったH8 Phase C `6dc5bf0de01a0aa23cafe0ff022c0cd21fbf1086` と非相殺費用比較 `23d46e489af054735d9d328aad0342ecdbddf305` の後続で、選ばれた決定論対照3構成のnative価格モデルを直接検証した記録である。旧2結果は、それぞれのsigned/非相殺、保存sampling・モデル条件における完了結果として保存する。[O06][B01]

**PR削減率は更新されていない。** 直接compile PASSは全184候補への保証、full-grid実測最適、PR母平均優位、厳密bias保証、全round絶対E0総費用優位を意味しない。`cost_reaccount_authorized=false`、`next_stage_authorized=false`。新shot重み付き再会計、ランキング、PR再sampling、model refitは別承認が必要で、今回実施しない。[B01][B03]

[保存監査manifest][B04]のpublic projection hashをsix_axis_results.jsonのbytesと照合した。元のprivate runtime結果/全proof61件を今回独立再監査したわけではない。JSONにも `source_inputs_verified.full_runtime_checked=false` と過去の `full_runtime_final_gate_already_PASS=true` が別に記録されている。

## 4. 二つの差分を結合する際の境界

Aは正stage S2のPSD相対保証、Bには負stage S4とsaved signed DF構成が含まれる。Bのcompile PASSをAのPSD仮定・bias certificateの充足としない。Aの紙上VALIDをBやEvaluationの総E0改善の保証としない。科学的比較・採択・追加実行は本資料の作成範囲外である。

**Mandatory STOP：差分資料の公開・照合後に停止。**

[O01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/future_review_preparation_handoff.md
[O06]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/pr_algorithm_improvement_history.md
[O07]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/source_registry.json
[P02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
[A01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/decision_handoff.md
[A02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/mathematical_audit.md
[A03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/prior_art_and_practical_conditions.md
[A04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/evidence_index.json
[A05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/publication_receipt.json
[A06]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/inputs/qc_track_iv_research_question_redesign_review_20261017.md
[B01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/ce6cd8ead5c0311ec72165c04869e7df4050b75b/docs/research/track_a_h8_key_compile_completed_results_20261017.md
[B02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/ce6cd8ead5c0311ec72165c04869e7df4050b75b/docs/research/%E7%A0%94%E7%A9%B6%E3%83%8E%E3%83%BC%E3%83%88/2026-10-17_H8%E4%B8%BB%E8%A6%816%E8%BB%B8%E7%9B%B4%E6%8E%A5compile%E5%AE%8C%E4%BA%86.md
[B03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/ce6cd8ead5c0311ec72165c04869e7df4050b75b/artifacts/resource_applicability/track_a_h8_key_compile_completed_six/2026-10-17/six_axis_results.json
[B04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/ce6cd8ead5c0311ec72165c04869e7df4050b75b/artifacts/resource_applicability/track_a_h8_key_compile_completed_six/2026-10-17/result_audit_manifest.json
[B05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/ce6cd8ead5c0311ec72165c04869e7df4050b75b/docs/research/track_a_h8_key_compile_parallel_handover_20261017.md
