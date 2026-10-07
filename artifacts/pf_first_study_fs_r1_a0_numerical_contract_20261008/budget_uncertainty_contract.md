# Prediction and budget intervals

Signed interval [p−tau,p+tau], magnitude [max(0,|p|−tau),|p|+tau], denominator [epsilon−c_max,epsilon−c_min].
When c_max≥epsilon, status NUMERICALLY_INDETERMINATE_BUDGET and nominal budget/B_min/B_max are null. No clipping or nominal feasibility rescue.
Otherwise B_min=gamma beta K/[t0(epsilon−c_min)], B_max=gamma beta K/[t0(epsilon−c_max)], nominal uses |p|. Every finite value must remain finite/positive.
Budget replay has no separate atol/rtol. After prediction replay passes, both finite intervals are analytically covered. Status changes, nonfinite intervals, or any nominal/min/max denominator sign change fail.
If both passes remain indeterminate with unchanged denominator signs, preserve undefined budgets, mark finite-budget coverage false, and make no budget/resource interpretation. Intentional null is not NaN/Inf.
Ratio interval [B_arm_min/B0_max,B_arm_max/B0_min] exists only for positive finite intervals and is labelled prediction_only_not_truth_scored.
