# Ritz8 replay

Keep complex128, exactly two MGS passes, prefix rejection, no replacement/rescue, rank≤8 and projected dimension≤9.
Keep rank thresholds 64 eps N max(||Hpsi||,|E|,tiny) and 64 eps N max(||Hz_previous||,||B_previous||,|E|,tiny).
Independent gates: ||Z†Z−I||_F and ||psi†Z||_2≤64 eps N; projected anti-Hermitian norm≤64 eps N max(||Hm||_F,tiny).
Categories match exactly: retained rank, rejection index/reason, projected dimension, phase pivot, lowest-eigenspace tie projection branch, zero/nonzero status.
Rejected direction index is zero-based (=accepted rank). No rejection gives null index/requested_rank_reached. Zero-rank reuses original CISD as in frozen Phase05; tie label zero_rank_reuse_CISD.
Nonzero state uses largest-magnitude pivot positive, first index ties; projected tie uses e0,e1,... as inherited.
AST annotations expose the already chosen small coefficients/tie index privately without replacing arithmetic. Cached Hpsi/HZ compute the Ritz residual with no new H action. No coefficients, basis or vector are published.
Continuous differences are diagnostics without a new hand-set energy/residual tolerance. Categories + independent gates + downstream proxies determine replay acceptance.
