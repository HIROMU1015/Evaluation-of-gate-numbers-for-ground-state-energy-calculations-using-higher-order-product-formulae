# FS-R1-20261007-v1

FS-R0で固定したnew sources・external design coordinateによるdevelopment比較。Phase Aで32 logical PF/echo評価（initial16+cold16）、rank8ならexplicit H36/small Ritz4、new fits8。Phase Aをcommit/hash/remote freeze後、Phase Bでnewtruth2pointsのみ。R0ではこれらを実行していない。

|condition|M00p=M10p training absolute|fixed t0|K|
|---|---|---|---|
|N2_active_eq_sto3g|[0.06263494343795273, 0.12526988687590546, 0.18790483031385818]|0.5983202971910435|19176|
|CO_active_eq_sto3g|[0.06546804264781796, 0.1309360852956359, 0.19640412794345388]|0.6127481451622522|37936|

新truthの物理branch continuationは未成立。同じnew sourceのlower-time anchorがなく、旧S0のhistorical anchorを再利用できない。t0だけの最大ground overlapへselection ruleを独自変更しない。追加truth座標も未承認。承認された最終statusはNO_GO_BRANCH_CONTINUATION_UNCLOSED（原§44分類はNO_GO_PROTOCOL_OR_BACKEND）。branch_continuation_amendment.mdに出典を記録した。全4arm基準・study interpretation・停止条件はJSONがnormative。
