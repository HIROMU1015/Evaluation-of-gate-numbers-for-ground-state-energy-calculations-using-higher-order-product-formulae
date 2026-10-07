# Complete cold replay

Compare 16 raw proxy pairs: 3 CISD training +3 Ritz training +CISD t0 +Ritz t0 per condition.
Primary rule is |cold−initial|≤1e-11 Ha, including equality; rtol is absent, including near zero.
Fit coefficients and predictions use only frozen P/qP L1 bounds. Every derived coefficient diagnostic and prediction gate must pass; conflicting diagnostics fail closed.
Ritz categories match exactly. Each pass independently passes inherited gates. Energy/residual/other continuous differences are saved without an independent difference threshold; downstream proxies must pass.
Initial result stays primary. No averaging, extra replay, coordinate/rank/source/backend rescue or tolerance adjustment.
This tolerance concerns reproducibility and does not certify bias, direct truth or resource success.
