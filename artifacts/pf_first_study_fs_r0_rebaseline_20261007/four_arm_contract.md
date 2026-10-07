# New-source four arms

|condition|M00p=M10p training absolute|fixed t0|K|
|---|---|---|---|
|N2_active_eq_sto3g|[0.06263494343795273, 0.12526988687590546, 0.18790483031385818]|0.5983202971910435|19176|
|CO_active_eq_sto3g|[0.06546804264781796, 0.1309360852956359, 0.19640412794345388]|0.6127481451622522|37936|

M00p/M10pは元H01のt/t_ref・y/max_abs scaling、[4,6] no-intercept unweighted OLS。t_refも固定numerical scaling constantで、Ritzによる再推定をしない。M01p/M11pはlocal g(t0)のみでfitしない。M11p primary/M01p cheaper challenger。B0_primeは新M00pから計算し、historical保存B0を参照しない。c>=epsilonはinfeasible。
