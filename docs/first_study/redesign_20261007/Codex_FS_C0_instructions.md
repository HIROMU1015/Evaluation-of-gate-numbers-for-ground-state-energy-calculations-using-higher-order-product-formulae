# Codex指示：第1研究 FS-C0（新設計のリポジトリ化。science未承認）

## 目的

別添FS_C0_design.mdを研究判断の入力として、次のN2/CO 2×2校正介入実験を実行可能な事前登録へ落とし込んでください。
単なるRitzの他分子展開ではなく、校正状態の変更と選択時刻でのlocal proxy評価の変更を分離することが目的です。

今回許可するのは、固定evidenceの読取、source/backend/cost closure、protocol・scorer・schema・synthetic testsの作成までです。
production N2/CO/H4の新規H/PF作用、Ritz state生成、proxy取得、fit、新規truth取得はまだ許可しません。

## 起点・原本保護

Repository:
HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae
起点の結果snapshot:
5b370ec22f7ffeac687ef70e1bcb87337f5fb976

新規worktree/branchとcreate-only output directoryを用意してください。既存uncommitted workを破壊しないこと。
旧formal、Phase0、Phase0.5、Phase0.6、H4 PhaseA Attempt1/2、PhaseBは一切変更しません。
H4のOutcome C point_onlyを維持します。新しいsafety規則で旧結果をA/Bへ再分類しないでください。

読む順序:
1. PF_first_study_paper_claim_ledger_20260926.md
2. artifacts/pf_first_study_completion_analysis_20260926_940ee7f/report.md
3. 同directoryのdecision_trace.csv、calibration_precision.csv、cost_factor_decomposition.csv
4. artifacts/pf_first_study_phase0_feasibility_20261006/README.md、report.md、resource_headroom.csv
5. artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/README.md、scientific_outcome.json、report.md、evaluation_scoring.csv
6. artifacts/pf_first_study_response_pilot_phase05_20261006/algorithm_design.md、response_pilot_protocol.json
7. docs/second_study_v2/evidence_integration_20261006/evidence_map.md（該当commitを明示）
8. 別添FS_C0_design.md

## 研究上すでに決めたこと

- 新研究の中心はdecision-relevant calibration intervention。
- Responseは既存mechanism/対照evidenceとして残す。新Response production armを追加しない。
- 新C1は古典的offline calibration。QPE入力状態は変更しない。
- 初回対象はN2_active_eq_sto3gとCO_active_eq_sto3gの2development条件。
- PF=current_m3、state refinement=m8固定、gamma=1.01、epsilon=0.00015936001019904 Ha、beta=1.2。
- Trainingは元CISD側の保存5点。Ritz側で時刻を再scaleしない。
- Evaluationは元S0のexact selected time t0だけ。
- Positive timesのみ。旧H4の正負22点の仕様は変更せず、新C1として記録。
- 4 arm: CISD_fit(M00), Ritz8_fit(M10), CISD_local(M01), Ritz8_local(M11)。primary=M11。
- localはimag-echo proxyの直接評価であり、PF固有値truthではない。
- 安全判定はs=epsilon-e-beta*K/(tB)>=0。S_under strict reductionを主条件にしない。
- 新C1のresource目標eta=2%。旧結果から独立に選ばれた定数とは主張せず、本development-informed新設計の目標として記録。
- resource gain、stateの増分value、safety repairを別フラグで評価。

## タスク1: immutable evidence registry

各sourceのorigin/result commit、verified snapshot、blob、SHA、用途、development/holdout区分を整理。
2つのstate×local factorと対照の役割を明示。
過去のpooled H4 588行と今回CISD/current_m3 12点を同じ分母にしない。

## タスク2: 既存scalarのみの再解釈

H4の既存evaluation_scoring.csvから、同時刻・同gammaの参考budget比
( epsilon-c_old ) / ( epsilon-c_new )
を別のpost-hoc tableへ出してください。新しいoperational budgetの成功結果として扱わない。
S_under総和を単一時刻のmarginと比較しない。
HF domain boundとN2/COのfixed-gamma perfect-prediction referenceを区別。

## タスク3: 数式・synthetic tests

1. B=gamma*beta*K/[t(epsilon-c)]とs=M_gamma-(e-c)の同値性。
2. baseline u+=0でもsafe/non-safeとsavingを別判定できること。
3. same-PF/domain cost lower boundとeta screening。
4. fixed OLS f(t)=ell(t)^T yとDelta f=ell(t)^T Delta y。
5. 4armのsigned差およびinteraction bookkeeping。
6. Responseの固定subspace表現:
   B=LZ, w=Q(B^+)^dagger Z^dagger r,
   g_resp=<A>-2Re<w|A|psi>。
   これは説明用の恒等式。production responseを改造・再実行しない。
7. 非正値rho_linがあり得ること。Ritzと同値/常に改善するという誤ったtestを作らない。
8. zero denominator、infeasible c、nonfinite、missing/duplicate truth、sign/time mismatch。
9. serialization / recovery / exact public payload roundtrip。

## タスク4: source/backend closure（最重要の実装確認）

N2/COの元H、ordered groups、CISD、実際のtraining times、t0、K、baseline prediction/B0、元S0 truthへのexact joinを確認。
同じ分子名だけでは不十分。sector/orbital ordering/energy origin/array identityを閉じてください。
metadata-only確認は可。原配列の値を使ったscience演算は不可。

H4用dense backendをそのまま大系へ拡大しないこと。
既存のN2/CO native vector-action backendを調べ、任意Ritz vectorへのPF作用とexact-H echo、numerical contractを確認。
必要なgroup spectral preprocessing、内部H-exponential matvec、memoryの費用を明示。
既存backendが新stateを受け付けない/identity不整合/数値精度契約が閉じない場合は、推測で別backendを選ばずimplementation blockerとして返してください。

exact t0 truth2点のreuseがidentity上成立しなければ、新truthやnearest-time代入で補わないこと。

## タスク5: machine-readable protocolとscorer skeleton

別添のarm、時刻、parameter、outcomesをJSON/MDの両方へ反映。
旧H4 protocolのファイルを編集せず、新FS-C1 protocolとしてversionを付ける。

primary_gain_i:
M11 valid and safe and B11<=0.98 B0。
local_gain_i:
M01 valid and safe and B01<=0.98 B0。
state_increment_i:
M01 and M11 safe and B11<=0.98 B01。
safety_repair_i:
M01 unsafe and M11 safe（gainとは別）。

全条件を保ち、平均でunsafeを相殺しない。予測・scorerをfreezeしてから保存truthを読む。
M00を元B0へ再現させるsource/numerical gateを、既存の誤差契約から事前固定する。

## タスク6: action/cost contract

2system・rank8・2state・6positive times・initial+coldのnominal:
explicit state-refinement H=36、PF forward=48、adjoint=0、exact-H echo=48、small Ritz=4、primary fits=4。
新direct truth/full-H ground/Schur/response solve=0。

これをtotal classical costと呼ばない。exact-H echo内部作用とgroup preprocessingを別counterへ。
joint/standalone/incremental/validation costsを分け、cold replay/失敗試行を隠さない。
任意のCPU秒→量子gate係数を導入しない。必要ならbreak-even coefficientのsymbolic式を示す。
Ritz校正stateを量子状態としてprepareする実験ではないため、未実装のquantum state-preparation costや利益を創作しない。

## タスク7: serializationと実行順序

production science前に、実際のmetadataとsynthetic scalar payloadを使い、公開までのwrite/hash/roundtrip/schema/readbackをend-to-endでtest。
将来scienceの各pass完了時のledgerとscalar、全run完了時のpayloadをprivate create-only recoveryへ先に保存する。
public freezeとは区別し、raw arraysやexact-state情報を誤公開しない。
保存失敗からの追加science再試行は自動許可しない。

## 必須成果物

- README.md
- research_decision.md（意図・新規性・論文到達点）
- evidence_registry.json
- fs_c1_protocol.md / json
- algorithm_design.md
- four_arm_design.md
- source_and_backend_closure.json
- predicted_action_budget.json
- cost_dictionary.md
- scoring_skeletonとsynthetic tests
- serialization_end_to_end_test結果
- H4_posthoc_decision_scale.csv
- GO_NO_GO_FOR_FS_C1.json
- source/publication manifest

GO_NO_GOにはdesign_complete、source_closure、backend_ready、truth_join_ready、test_status、unresolved_issues、science_authorized=falseを分離して記録。
C0完了を新N2/CO science実行許可にしない。

## 停止

新規成果物を通常commit/pushし、独立取得のhash照合後に停止してください。
原本を変更しない。新C1 scienceは開始しない。

最終報告は、(1)source/backendが閉じたか、(2)4arm・scorer・cost contract、(3)tests、(4)未解決点、(5)C1 readiness、(6)commit/branch、(7)production science=0、を提示してください。
