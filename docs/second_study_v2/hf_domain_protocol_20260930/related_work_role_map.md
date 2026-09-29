# Related-work role map

版は2026-09-30に書誌・scopeだけを確認した。HF pilotでは新しい外部手法を実装しない。

| ID | Work / version | Role | Inherited component | Not claimed by this study |
|---|---|---|---|---|
| L1 | Mehendale et al., *Estimating Trotter Approximation Errors…*, arXiv:2312.13282v3 | `core_related_work` | approximate-state eigenvalue-error calibrationとQPE resource relevanceという問題設定 | perturbative estimatorの新規性、同論文のpartition ranking |
| L2 | Maxwell et al., *Practical Estimation of Trotter Error…*, arXiv:2606.30738v1 | `core_related_work` | practical information-cost/error-estimation比較の背景 | compact BCH、importance sampling、scaling resultの実装・再現 |
| L3 | Hejazi et al., *Better product formulas for quantum phase estimation*, arXiv:2412.16811v1 | `core_related_work` | task-specific QPE eigenvalue errorとresource-aware PF analysis | custom PF設計、low-energy bound、新PFの新規性 |
| L4 | Epperly, Lin, Nakatsukasa, *A Theory of Quantum Subspace Diagonalization*, arXiv:2110.07492v2 | `method_source` | subspace conditioning/truncationを独立gateとして扱う数値解析上の動機 | 同論文のtheoremを本pilotのcertificateとして使用すること |
| L5 | Zhao et al., *Making Trotterization adaptive…*, arXiv:2209.12653v3 | `peripheral` | adaptive time-step研究とのtask boundaryの明示 | dynamics feedback algorithmをfrozen QPE selectorとして実装したとの主張 |
| L6 | Yi and Crosson, *Spectral Analysis of Product Formulas…*, arXiv:2102.12655v1 | `core_related_work` | PFのeigenvalue/eigenvector・gap-aware spectral analysisという背景 | 同論文のrigorous boundやasymptotic scalingを本pilotが達成したとの主張 |
| M1 | Local D2-A explicit-vector unitary Arnoldi core | `method_source` | one-chain m<=8、H-reference、phase lift、empirical width、resource counters | Arnoldi/Krylov自体の新規性、ground/branch certificate |

## External-baseline gate

初回HF pilotでは外部手法を追加実装しない。次の全条件を満たす場合だけ、別承認で最も近い代表法を最大1方式検討する。

1. resource-aware domain interventionにsignalがある。
2. cheap local proxyだけでは同じdecisionを再現できない。
3. 比較によりArnoldi固有効果と一般的高精度calibration効果を識別できる。

このgateを満たさない限りL1–L6は背景・方法source・task boundaryであり、pilot armではない。
