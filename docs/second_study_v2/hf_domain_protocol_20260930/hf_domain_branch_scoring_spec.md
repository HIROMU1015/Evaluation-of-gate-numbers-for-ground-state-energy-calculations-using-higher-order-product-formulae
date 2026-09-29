# HF domain pilot branch / phase scoring specification

## 1. 禁止する比較

旧D2-A formal scorerで使われた、absolute PF energyのunwrap integerとexact-ground除去後shiftのunwrap integerの直接一致を禁止する。D2-A scoring auditは、この二つが異なる座標系であることを確認した。

## 2. 保存する表現

各座標について最低限、次を別fieldで保存する。

- PF Ritz value（複素数）とprincipal phase
- H-reference Ritz energy
- H-referenceへliftしたabsolute PF energy
- predictionのsigned shift `delta_hat = E_PF_hat - E_H_ref`
- truth側のexact-ground除去後signed direct shift
- common physical gaugeへ変換したprediction/truth energy difference
- predictor側のabsolute unwrap integer（diagnostic only）
- truth側のrelative winding（diagnostic only）
- alias period `2*pi/t`
- branch/alias/conditioning/width gate

異なるintegerを同一fieldへ正規化しない。

## 3. Predictor branch rule

D2-A coreを変更しない。

1. 同一Krylov basis内のlowest H Ritz candidateを経験的H referenceとする。
2. U Ritz candidatesをH-reference overlapで順位付けする。
3. 同一conditionの直前候補とのprojector overlapをsecondary scoreにする。
4. H-referenceへ最も近いabsolute energyへphaseをliftする。
5. overlap/unwrap ambiguityまたは数値gate不合格ならabstainする。

H Ritz candidateをcertified ground stateと呼ばない。truthはpredictorのambiguityを解消しない。

## 4. Scorer validity

scorerはprediction identityを検証後、次を行う。

- predictionとtruthを同じenergy gaugeへ表現する。
- physical energy/shift differenceと、利用可能ならtruth branch separationを比較する。
- phase covarianceを確認する：共通energy offsetをHとPFへ加えてもsigned shiftとbranch判定が不変であること。
- branch identityが一意でなければ`unscorable`とし、未計画anchorを追加しない。

representation-independentなbranch validityが合格した後だけbudget safetyを採点する。

## 5. Failure fields

- `source_identity_failure`
- `h_reference_indeterminate`
- `overlap_ambiguity`
- `unwrap_ambiguity`
- `alias_indeterminate`
- `numerical_gate_failure`
- `truth_branch_unscorable`
- `physical_branch_mismatch`

これらをpoint error、width failure、unsafe budgetと混同しない。
