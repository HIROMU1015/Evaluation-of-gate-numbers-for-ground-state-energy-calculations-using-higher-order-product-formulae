第1研究FS-R1 Phase Aのproduction実行前に、**FS-R1-A0：production numerical-contract freeze** を実施してください。

直前のPhase A試行は、production cold replayの合格許容差が未定義だったため、科学計算開始前に

`PHASE_A_NUMERICAL_CONTRACT_UNCLOSED`

として正しく停止しています。

今回はその不足だけを閉じます。

\[
\boxed{\text{FS-R1-A0ではproduction scienceを実行しない}}
\]

\[
\boxed{\text{Phase A / Phase Bとも実行しない}}
\]

数値契約・orchestration・lease・recovery wrapperを実装・freezeし、commit/pushして停止してください。

---

# 0. 起点

Repository:

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

直前の停止監査：

- Branch  
  `pf-first-study-fs-r1-phase-a-20261007`

- Commit  
  `4e5c3ba2e3497915cd1668d9ac5cd77640ab2938`

- Artifact  
  `artifacts/pf_first_study_fs_r1_phase_a_20261007/`

Current status:

`PHASE_A_NUMERICAL_CONTRACT_UNCLOSED`

Production started:

`false`

Production actions:

`0`

Truth access:

`0`

Prediction SHA:

`null`

---

# 1. 今回の目的

FS-R1 Phase Aのproduction runを開始する前に、以下を**観測前に固定**してください。

1. production vector norm gate
2. raw proxy cold replay acceptance
3. Ritz replay acceptance
4. fit coefficient uncertainty propagation
5. arm prediction uncertainty propagation
6. budget uncertainty propagation
7. near-infeasible handling
8. initial/cold orchestration
9. exclusive run lease
10. scientific return後のprivate recovery
11. serialization failure時のno-rerun policy

結果を一切見ずに契約を閉じることが目的です。

---

# 2. Authority

最低限以下を確認してください。

## Current stop audit

- `artifacts/pf_first_study_fs_r1_phase_a_20261007/README.md`
- `numerical_contract_audit.json`
- `GO_NO_GO_FOR_PHASE_B.json`
- `verification.json`

## FS-R0.1

- `fs_r1_protocol_v2.json`
- `branch_ladder.json`
- `branch_contract.md`
- `phase_barrier_v2.md`
- `truth_executor_contract.md`
- `predicted_action_budget_v2.json`

## Ritz numerical rules

H4 response pilot Phase 0.5 / Phase A Retry2で固定された数値規則。

既存の：

- complex128
- MGS exactly 2 passes
- \(64\epsilon N\) rank/orthogonality規則
- projected Hermiticity gate
- deterministic phase/tie rule

を維持してください。

---

# 3. Protocol version

新しいprotocol amendmentを作成してください。

例：

`FS-R1-20261007-v3`

Revision reason:

`close physical-production replay/norm acceptance contract before any Phase A observation`

旧v1/v2は上書きしないこと。

---

# 4. Machine precision

production numerical contractでは、

\[
\epsilon_{\rm mach}
=
2.220446049250313\times10^{-16}
\]

をbinary64 machine epsilonとして固定。

Sector dimension:

\[
N=1568
\]

を使用。

既存Ritz rulesで使用するscaleは引き続き

\[
64\epsilon_{\rm mach}N
\]

を基本とします。

---

# 5. Input state normalization gate

CISDおよびRitz stateについて、

\[
\boxed{
\left|\|\psi\|_2-1\right|
\le10^{-12}
}
\]

をproduction acceptance gateとして固定してください。

対象：

- M00′ CISD
- M01′ CISD
- M10′ Ritz
- M11′ Ritz
- initial
- cold replay

一度だけrenormalizeして隠すことは禁止。

source/state construction contractに基づくnormalization後のstateがgateを満たすこと。

---

# 6. PF output norm gate

各production PF actionについて、

\[
\boxed{
\left|\|U_P(t)\psi\|_2-1\right|
\le10^{-10}
}
\]

を要求してください。

全training/t0、全state、initial/coldに適用。

fail時はそのPhase A runをnumerical failureとして停止。

---

# 7. Exact-H evolved/reference norm gate

exact-H echo actionについて、

\[
\boxed{
\left|
\|e^{-iHt}\psi\|_2-1
\right|
\le10^{-10}
}
\]

を要求してください。

`expm_multiply`の内部workがunknownでも、このnorm gateは必須。

---

# 8. Echo amplitude sanity

echo amplitude

\[
z=
\langle e^{+iHt}\psi|U_P(t)\psi\rangle
\]

について、

- real finite
- imag finite
- magnitude finite

を要求。

さらにCauchy boundの数値監査として、

\[
|z|
\le
\|e^{+iHt}\psi\|_2
\|U_P(t)\psi\|_2
+\tau_{\rm round}
\]

を確認できるようにしてください。

\(\tau_{\rm round}\) はbinary64 scaleから事前に導出し、結果後に設定しないこと。

---

# 9. Raw proxy replay tolerance

production cold replayのraw proxyについて、固定絶対許容差：

\[
\boxed{
\tau_g=10^{-11}\ {\rm Ha}
}
\]

を採用してください。

各同一condition/state/timeについて、

\[
\boxed{
|g_{\rm cold}-g_{\rm initial}|
\le\tau_g
}
\]

を要求。

relative toleranceはprimary判定に使用しません。

near-zero proxyでもabsolute ruleのみ。

---

# 10. 対象となるraw proxy

cold replay comparisonの対象：

## M00′

3 training proxies

## M10′

3 training proxies

## M01′

t0 local proxy

## M11′

t0 local proxy

したがって1 condition/passで8 proxy coordinates。

N2/COで16。

initial vs coldの比較は16組。

---

# 11. Raw proxy toleranceの位置づけ

\(\tau_g=10^{-11}\) Haは、

- resource eta=0.02とは無関係
- fit residualとは無関係
- truth certificateではない
- model bias boundではない

ことを明記。

これは**physical-production replay reproducibility gate**です。

---

# 12. Fit uncertaintyは独立tolを設定しない

M00′ / M10′ fit coefficientについて、

「係数差が1e-X以下ならPASS」

のような独立手決めtoleranceを新設しないでください。

raw proxy uncertainty

\[
\tau_g
\]

をfitへ解析的に伝播します。

---

# 13. Fit matrix

各conditionについて固定3点

\[
t_1,t_2,t_3
\]

から、

\[
A=
\begin{pmatrix}
t_1^4&t_1^6\\
t_2^4&t_2^6\\
t_3^4&t_3^6
\end{pmatrix}
\]

を定義。

実際のfit implementationはhistorical H01 numerical implementationを維持します。

uncertainty propagation用には、同じlinear mapに対応するpseudoinverse

\[
P=A^+
\]

または実装上等価な固定linear mapを使用してください。

---

# 14. Coefficient uncertainty propagation

raw proxy vector

\[
y=(g_1,g_2,g_3)^T
\]

各成分に

\[
|\delta y_i|\le\tau_g
\]

があるとき、

\[
\delta a=P\delta y
\]

より、各係数のworst-case boundを

\[
\boxed{
\tau_{a_j}
=
\tau_g
\sum_i |P_{ji}|
}
\]

として計算してください。

この値をprotocol freeze時にN2/COそれぞれ計算・保存。

手入力近似値をauthorityにしないこと。

---

# 15. Fit prediction uncertainty at t0

\[
q(t_0)
=
\begin{pmatrix}
t_0^4&t_0^6
\end{pmatrix}
\]

として、

\[
w(t_0)=q(t_0)P.
\]

fit predictionについて、

\[
\boxed{
\tau_{\rm fit}(t_0)
=
\tau_g
\sum_i|w_i(t_0)|
}
\]

を使用。

N2/COそれぞれprotocol generation時に固定値を計算して保存。

---

# 16. M00′ / M10′ replay acceptance

初回とcoldのfit prediction差について、

\[
\boxed{
|f_{\rm cold}(t_0)-f_{\rm initial}(t_0)|
\le
\tau_{\rm fit}(t_0)
}
\]

を要求してください。

係数についても、各

\[
|a^{cold}_j-a^{initial}_j|
\le\tau_{a_j}
\]

を診断として要求可能。

ただしprediction gateと矛盾した場合はfail closed。

---

# 17. M01′ / M11′ prediction uncertainty

M01′/M11′はfitを通さないため、

\[
\boxed{
\tau_{01}=\tau_{11}=\tau_g=10^{-11}\ {\rm Ha}
}
\]

と固定。

initial/cold差も同じ絶対gate。

---

# 18. Arm prediction uncertainty registry

各armについて、

- signed prediction
- uncertainty bound
- lower signed bound
- upper signed bound
- absolute magnitude interval

を保存できるschemaを実装。

M00′/M10′:

\[
\tau_p=\tau_{\rm fit}(t_0)
\]

M01′/M11′:

\[
\tau_p=10^{-11}\ {\rm Ha}.
\]

---

# 19. Absolute magnitude interval

prediction \(p\) と uncertainty \(\tau_p\) に対し、

\[
c=|p|
\]

について、

\[
\boxed{
c_{\min}
=
\max(0,|p|-\tau_p)
}
\]

\[
\boxed{
c_{\max}
=
|p|+\tau_p
}
\]

を使用。

符号がuncertainty interval内で跨ぐ場合も、このabsolute interval ruleを使用してください。

---

# 20. Budget denominator interval

\[
d=\epsilon_E-c
\]

なので、

\[
d_{\min}
=
\epsilon_E-c_{\max}
\]

\[
d_{\max}
=
\epsilon_E-c_{\min}.
\]

---

# 21. Near-infeasible rule

もし、

\[
\boxed{
c_{\max}\ge\epsilon_E
}
\]

なら、

`NUMERICALLY_INDETERMINATE_BUDGET`

としてください。

この場合、

- finite budgetを報告しない
- clippingしない
- nominal signed predictionだけでfeasible扱いしない

こと。

---

# 22. Budget interval

\[
c_{\max}<\epsilon_E
\]

なら、

\[
\boxed{
B_{\min}
=
\frac{\gamma\beta K}
{t_0(\epsilon_E-c_{\min})}
}
\]

\[
\boxed{
B_{\max}
=
\frac{\gamma\beta K}
{t_0(\epsilon_E-c_{\max})}
}
\]

を計算してください。

Nominal:

\[
B=
\frac{\gamma\beta K}
{t_0(\epsilon_E-|p|)}
\]

も保存。

---

# 23. Budget replay acceptance

budget差に独立の

- absolute tolerance
- relative tolerance

を設定しないでください。

initial/cold predictionが上記prediction replay gateをPASSし、両budget intervalsがwell-definedなら、budget replayは解析的伝播でcoveredとします。

ただしinitial/coldで：

- feasible / indeterminate statusが変わる
- interval constructionが非有限
- denominator signが変わる

場合はfail。

---

# 24. Prediction-only budget ratio uncertainty

Phase Aでbudget ratioを報告する場合も、

nominal ratioだけでなくintervalを計算できるschemaを用意してください。

例：

\[
R_{11}=B_{11}/B_0.
\]

conservative intervalはpositive quantitiesとして、

\[
R_{\min}
=
B_{11,\min}/B_{0,\max}
\]

\[
R_{\max}
=
B_{11,\max}/B_{0,\min}
\]

を使用。

ただしPhase Aではtruth-scored resource successに使わない。

---

# 25. Ritz categorical replay contract

initial/coldで以下は**完全一致**を要求。

- retained rank
- rank-stop index
- rank-stop reason
- projected dimension
- phase pivot index
- tie-resolution branch
- zero-rank/nonzero-rank status

違えばcold replay failure。

---

# 26. Ritz continuous diagnostics

各passで既存gateを独立に満たすことを要求。

## Orthogonality

\[
\|Z^\dagger Z-I\|_F
\]

および

\[
\|\psi^\dagger Z\|_2
\]

について既存：

\[
\le64\epsilon_{\rm mach}N
\]

scaleのfixed rule。

---

# 27. Projected Hermiticity

既存rule：

\[
\|H_m-H_m^\dagger\|_F
\le
64\epsilon_{\rm mach}N
\max(\|H_m\|_F,\mathrm{tiny})
\]

を維持。

結果後にrelaxしない。

---

# 28. Rank thresholds

既存規則をそのまま使用。

Initial direction:

\[
64\epsilon_{\rm mach}N
\max(\|H\psi\|,|E|,\mathrm{tiny})
\]

Subsequent:

\[
64\epsilon_{\rm mach}N
\max(
\|Hz_{\rm previous}\|,
\|B_{\rm previous}\|,
|E|,
\mathrm{tiny}
)
\]

first rejected directionでstop。

---

# 29. Ritz energy/residual replay

Ritz energyやresidual normそのものに新しい手決めabsolute toleranceを設定しないでください。

initial/coldそれぞれが：

- same categorical construction
- same retained rank
- existing numerical gates PASS
- downstream proxy replay PASS

ならreplay acceptanceを満たすものとする。

ただし値自体は差を必ず保存。

---

# 30. State phase convention

Ritz stateは既存：

> largest-magnitude component positive; first index wins ties

を使用。

initial/coldでpivot index完全一致。

phase-adjusted vectorのdifferenceを診断として保存可能だが、新たなscience gateは結果を見て追加しない。

---

# 31. Nonfinite policy

以下のいずれかがNaN/Infなら即fail。

- state/vector
- norm
- proxy
- fit coefficient
- prediction
- Ritz energy
- Ritz residual
- uncertainty bound
- budget
- budget interval

救済禁止。

---

# 32. Production orchestration

Phase A productionの将来実行順を以下へ固定してください。

\[
\boxed{
\text{N2 initial}
\rightarrow
\text{CO initial}
\rightarrow
\text{N2 cold}
\rightarrow
\text{CO cold}
}
\]

または実装上両initialをまとめる場合でも、論理的に：

1. all initial conditions complete
2. initial scalar recovery
3. then all cold replays

の順序を保証。

N2 initial直後にその結果を見てN2 coldだけ走らせないこと。

---

# 33. Initial phase failure

N2 initialがtechnical failureなら、結果を見てprotocolを変更せず、runを停止してよい。

ただしN2 scientific valueを理由にCOをskipすることは禁止。

technical abortとscience selectionを明確に区別。

---

# 34. Exclusive lease

Phase A本番用にexclusive leaseを実装してください。

最低限：

- authorization/protocol hash
- source hashes
- run ID
- `RUN_STARTED`
- state: started/completed/failed
- timestamp
- process/host metadata

を保存。

既存leaseがstarted/completedなら同じauthorizationで再run禁止。

---

# 35. Lease semantics

serialization/publication failureはscience rerun権限を与えない。

以下を区別：

- calculation never started
- calculation started but technical failure
- science return completed
- recovery saved
- public serialization failed
- publication complete

---

# 36. Private recovery

production scientific return直後、public schema validationより前に、create-only private scalar recoveryを保存できるwrapperを完成させてください。

保存対象：

- all raw proxies
- fit coefficients
- arm predictions
- uncertainty bounds
- budget intervals
- nominal budgets
- Ritz diagnostics
- retained ranks
- action counts
- wall/RSS
- source/protocol/code identities

---

# 37. Recovery integrity

private recoveryは：

- fsync
- SHA256
- create-only
- run lease binding
- source identity binding
- protocol hash binding

を要求。

---

# 38. Public serialization failure

science return後にpublic artifact validationが失敗した場合、

- private scalar recoveryからのみ復旧
- production PF/echo/Ritzを再実行しない
- recovery bytesとpublic resultを照合

としてください。

---

# 39. New numerical-contract tests

最低限追加してください。

## Norm

1. input norm exactly at gate PASS
2. input norm over gate FAIL
3. PF norm gate
4. exact-H norm gate
5. nonfinite norm FAIL

## Raw proxy

6. replay diff <1e-11 PASS
7. replay diff =1e-11 PASS
8. replay diff >1e-11 FAIL
9. near-zero proxy uses absolute rule only

## Fit propagation

10. coefficient bound from linear propagation
11. t0 prediction bound from linear propagation
12. no independent fit tolerance
13. N2 fixed matrix deterministic
14. CO fixed matrix deterministic

## Budget

15. \(c_{\max}<\epsilon\) gives finite interval
16. \(c_{\max}=\epsilon\) indeterminate
17. \(c_{\max}>\epsilon\) indeterminate
18. no clipping
19. ratio interval propagation

## Ritz replay

20. rank mismatch FAIL
21. stop-reason mismatch FAIL
22. pivot mismatch FAIL
23. both passes satisfy existing orthogonality gate
24. one pass fails gate → replay FAIL

## Orchestration

25. all initial before cold
26. science result cannot determine whether CO runs
27. second authorization reuse rejected

## Lease/recovery

28. duplicate RUN_STARTED rejected
29. recovery created before public serialization
30. public failure does not rerun science
31. completed lease cannot rerun
32. recovery hash mismatch rejected

既存260 testsを壊さないこと。

---

# 40. Protocol output

machine-readable numerical contractを作成してください。

例：

`fs_r1_numerical_contract_v1.json`

最低限：

```text
input_state_norm_abs = 1e-12
pf_output_norm_abs = 1e-10
exact_h_reference_norm_abs = 1e-10
raw_proxy_replay_abs_hartree = 1e-11

fit_uncertainty = analytic_linear_propagation
budget_uncertainty = prediction_interval_propagation
near_infeasible = c_max >= epsilon_E

ritz_categorical_replay = exact_match
ritz_continuous_gates = inherited_64_eps_N_rules

phase_A_order =
all_initial_conditions_then_all_cold_replays
```

を含める。

---

# 41. N2/CO propagation constants

FS-R1-A0内で固定coordinatesから、

- \(P=A^+\)
- coefficient uncertainty factors
- \(w(t_0)\)
- \(\tau_{\rm fit}(t_0)\)

を実際に計算してください。

これらをmachine-readable artifactへ保存。

結果を見ず、固定coordinateのみから計算。

---

# 42. No production science

FS-R1-A0で禁止：

- N2/CO numeric source array decode for science
- H matvec
- Ritz construction
- PF production
- echo production
- fit production
- arm prediction
- budget production
- direct truth
- branch solve
- ground truth access

必要なstatic/hash/schema inspectionのみ許可。

---

# 43. GO criteria

最終status：

## `GO_FOR_FS_R1_PHASE_A_PRODUCTION`

条件：

- numerical contract frozen
- norm gates frozen
- replay gate frozen
- fit propagation frozen
- budget propagation frozen
- Ritz replay contract frozen
- orchestration fixed
- lease implemented
- recovery wrapper complete
- tests pass
- production actions=0
- truth access=0

---

## `NO_GO_NUMERICAL_CONTRACT`

数式/implementation上contractを閉じられない。

---

## `NO_GO_EXECUTION_WRAPPER`

lease/recovery/orchestrationが閉じない。

---

## `NO_GO_OTHER`

理由明示。

---

# 44. 必須成果物

例：

`artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261007/`

最低限：

1. `README.md`
2. `numerical_contract_amendment.md`
3. `fs_r1_protocol_v3.json`
4. `fs_r1_numerical_contract_v1.json`
5. `norm_contract.md`
6. `replay_contract.md`
7. `fit_uncertainty_propagation.json`
8. `budget_uncertainty_contract.md`
9. `ritz_replay_contract.md`
10. `phase_a_orchestration.md`
11. `run_lease_contract.md`
12. `recovery_contract_v2.md`
13. `predicted_action_budget_v3.json`
14. `tests.log`
15. `verification.json`
16. `source_manifest.json`
17. `publication_manifest.json`
18. `GO_NO_GO_FOR_PHASE_A_PRODUCTION.json`

---

# 45. 最終報告

完了時は以下を簡潔に報告してください。

1. final GO/NO-GO
2. raw proxy replay tolerance
3. input/PF/reference norm gates
4. N2 \(\tau_{\rm fit}(t_0)\)
5. CO \(\tau_{\rm fit}(t_0)\)
6. budget interval rule
7. near-infeasible rule
8. Ritz categorical replay rules
9. orchestration order
10. lease status
11. recovery wrapper status
12. tests total
13. production science actions=0
14. truth access=0
15. branch / commit
16. push / independent remote verification

---

# 46. 停止

FS-R1-A0完了後は必ず停止してください。

`GO_FOR_FS_R1_PHASE_A_PRODUCTION`でも、Phase A productionを自動実行しないでください。

次の順序は：

\[
\boxed{
\text{FS-R1-A0 numerical contract}
\rightarrow
\text{GPT review}
\rightarrow
\text{FS-R1 Phase A production}
\rightarrow
\text{prediction freeze}
\rightarrow
\text{GPT review}
\rightarrow
\text{Phase B}
}
\]

です。

既存FS-R0/R0.1、FS-C0/C0.5/C0.6、historical first-study、Phase0、H4 artifactsは変更しないでください。