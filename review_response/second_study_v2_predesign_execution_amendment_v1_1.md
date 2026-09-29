# 第2研究v2 pre-design analysis execution amendment v1.1

このamendmentは`second_study_v2_predesign_analysis_prompt_20260929.md`へ追加適用する。
元指示の科学的範囲、禁止事項、停止条件は変更しない。矛盾時は、より厳しいtruth・独立性・資源・provenance境界を採用する。

## 1. factor表記

既存台帳に合わせ、PF選択因子は`F_PF`と記録する。`F_P`を別因子として導入しない。

## 2. isolated-factor headroom算術

同一baseline・同一resource metricで他因子を固定した形式的置換について、`F>0`なら
`H(F)=1-1/F`を用いる。`F<=1`は正のresource lossとして扱わない。
factorが区間または片側boundなら、単調変換したheadroom boundとして保存し、exact値またはmaximum improvementと呼ばない。

## 3. dominant factor

dominant factorは、同一baseline・同一resource metricで比較可能なexact factorの`log(F)`最大としてのみ分類する。
exactとbound、異なるbaseline、異なるstageが混在する場合は`indeterminate`とする。

## 4. materiality

materiality thresholdは今回固定しない。`materiality_status=not_prespecified`を用い、headroom値と候補threshold別のdescriptive sensitivityだけを保存する。科学的成功基準にはしない。

## 5. accessの分離

情報ごとに`available_in_verified_snapshot`と`operationally_truth_free_on_new_condition`を分離する。
取得可能性とcertificate十分性も別fieldにし、少なくとも`certificate_strength`を記録する。

## 6. 保存truthの読取り会計

`new_truth_count=0`とは別に、保存済みtruth artifactの読取りsource数・利用箇所を記録する。
truthを用いた再集計には`truth_used_for_post_hoc_scorer_only=true`を付ける。

## 7. 入力allowlist

入力はbase commit `599a9f2e9a45302b8d34192ef581fd3ea55a1f1e`から到達可能なGit-tracked sourceの明示allowlistに限定する。
dirty root、untracked artifact、runtime cache、外部network sourceを使用しない。

## 8. data-use ledger coverage

`docs/pf_data_use_ledger.md`はLiF/HCl以前の台帳なので、LiF/HClは監査済みS05–S13で補完する。
旧ledgerを変更せず、coverage gapと補完sourceをreportへ記録する。

## 9. provenance

source registryには各sourceについて`origin_result_commit`、`verified_snapshot_commit=599a9f2e9a45302b8d34192ef581fd3ea55a1f1e`、両commitのblob SHAを別々に記録する。
従来のscience evidence snapshot `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`は必要に応じて別fieldで保持する。

## 10. correction/audit成果物

`predesign_correction_log.md`は訂正0件でも作成する。
source row count、算術式、truth read count、生成row count、protected artifact差分、科学計算countを`analysis_audit.json`へ記録する。

## 11. Gitとidentity

同名branch/worktree/outputが存在する場合は上書きせず連番を付ける。
今回のfileだけを明示的にstageする。内容commitとidentity記録commitを分け、manifestは自己除外する。remote pushは別の明示的許可まで行わない。

## 12. headroomの因果的解釈を禁止する

`H(F)=1-1/F`で得る値は`isolated_factor_algebraic_headroom`として記録する。
これは同一baseline・同一resource metricで、他factorを固定したまま当該factorだけを1へ置き換えた場合の代数的改善余地であり、実際のinterventionによって達成可能な最大削減率とはみなさない。

出力では少なくとも次を分離する。

- `algebraic_headroom`
- `headroom_bound_type`
- `intervention_achievability=not_established`

既存の凍結方式による直接counterfactualが保存されている場合だけ、`observed_intervention_effect`等の別fieldとして記録してよい。
`algebraic_headroom`と`observed_intervention_effect`を同一視しない。

## 完了時の分類

pre-design reportは、成功判定ではなく、保存evidenceに基づき次の三分類を提示する。

- I: headroom大 × truth-free情報あり
- II: headroom大 × truth-free情報未確立
- III: 高精度情報あり × headroom小

ただし「大」「小」は未固定thresholdによる成功判定ではなく、保存値と候補threshold sensitivityに基づくdescriptive分類とする。
