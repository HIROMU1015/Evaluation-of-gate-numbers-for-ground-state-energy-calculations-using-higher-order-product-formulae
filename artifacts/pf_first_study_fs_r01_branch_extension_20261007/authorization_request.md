第1研究FS-R0の唯一のblockerである、**new source上のphysical branch continuation未確立**を解消するため、**FS-R0.1：branch-extension protocol / preflight** を実施してください。

今回は**branch contractの設計・実装・freezeのみ**です。

\[
\boxed{\text{direct PF truthはまだ計算しない}}
\]

\[
\boxed{\text{FS-R1 Phase A / Phase B scienceはまだ開始しない}}
\]

---

# 0. 起点

Repository:

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

FS-R0:

- Branch  
  `pf-first-study-fs-r0-rebaseline-20261007`

- Commit  
  `3469b29f53a2c559bb8f6785bcba68a2896d41a5`

- Artifact  
  `artifacts/pf_first_study_fs_r0_rebaseline_20261007/`

Current status:

`NO_GO_BRANCH_CONTINUATION_UNCLOSED`

FS-R0で以下は既に成立しています。

- new regenerated source freeze
- N2/CO source identities
- sanitized operational source
- 4-arm protocol
- scoring contract
- Phase A/B barrier
- recovery
- cost schema

未確立なのはnew source上のdirect PF truth branch continuationだけです。

---

# 1. 今回の研究判断

direct PF truth路線は維持します。

t0で単独のmaximum-ground-overlap eigenpairを選ぶ方式には変更しません。

旧S0と同様、

> lower-time anchorから同一source上のphysical branchを連続追跡する

方式を採用します。

ただしnew sourceではhistorical branch IDやhistorical truthを流用しません。

---

# 2. Branch continuation rule

各conditionについて、positive-time branchのみを扱います。

branch ladderを以下へ固定します。

\[
\boxed{
0.1t_{\rm ref}
\rightarrow
0.2t_{\rm ref}
\rightarrow
0.3t_{\rm ref}
\rightarrow
0.5t_{\rm ref}
\rightarrow
0.99t_0
\rightarrow
t_0
}
\]

各condition 6点。

N2/CO合計12 direct PF coordinatesです。

---

# 3. この12点の役割

重要：

12点すべてをresource scoringに使うわけではありません。

## Branch certification points

最初の5点：

- 0.1 \(t_{\rm ref}\)
- 0.2 \(t_{\rm ref}\)
- 0.3 \(t_{\rm ref}\)
- 0.5 \(t_{\rm ref}\)
- 0.99 \(t_0\)

はbranch continuity確立用。

## Primary scoring truth

最終の

\[
t_0
\]

のみを各conditionのresource safety/scoringに使用します。

したがって、

- truth calculations = 12 coordinates
- primary scored direct truth = 2 values

と明確に区別してください。

---

# 4. 座標を固定

## N2

Condition:

`N2_active_eq_sto3g`

new H SHA:

`f4a08b755a4e903f4e9611fee394d6101a5d27279a1bd8af567b97920da5402e`

Source identity:

`6b93735a56638c40a2bcd35e504f1ee823cfdbe396441fce15fd5e02502b044d`

Historical external design \(t_{\rm ref}\):

`0.6263494343795273`

Fixed \(t_0\):

`0.5983202971910435`

Branch ladder:

```text
0.06263494343795273   # 0.1 t_ref
0.12526988687590546   # 0.2 t_ref
0.18790483031385818   # 0.3 t_ref
0.31317471718976365   # 0.5 t_ref
0.5923370942191331    # 0.99 t0
0.5983202971910435    # t0
```

---

## CO

Condition:

`CO_active_eq_sto3g`

new H SHA:

`27ed246b354c754a506541dac81650aafdfa413b375fadf0b736822c171fb4c5`

Source identity:

`ed9ec93d6945a11bd144d2531ffedaf67da829383334b47206b78c11aee34f17`

Historical external design \(t_{\rm ref}\):

`0.6546804264781796`

Fixed \(t_0\):

`0.6127481451622522`

Branch ladder:

```text
0.06546804264781796   # 0.1 t_ref
0.1309360852956359    # 0.2 t_ref
0.19640412794345388   # 0.3 t_ref
0.3273402132390898    # 0.5 t_ref
0.6066206637106297    # 0.99 t0
0.6127481451622522    # t0
```

実装時は可能ならmachine-readable authority値から生成し、上記表示値とのbinary64一致も確認してください。

---

# 5. なぜこのladderを使うか

結果を見て新しく選んだtime gridではありません。

- 0.1/0.2/0.3 \(t_{\rm ref}\)：既存3-point calibration design
- 0.5 \(t_{\rm ref}\)：historical sentinel coordinate
- 0.99 \(t_0\)：旧S0 exact-time branch connection design
- \(t_0\)：primary decision coordinate

という既存design由来です。

このprovenanceをprotocolへ明記してください。

---

# 6. First anchor selection

各conditionの最小時刻

\[
0.1t_{\rm ref}
\]

では、physical branchのseedとして、

> maximum exact-ground overlap

を使用します。

ただしこれはbranch initialization専用です。

resource estimatorやPhase Aへexact groundを渡さないでください。

---

# 7. Subsequent selection

2点目以降は、

\[
\boxed{
\text{maximum previous-selected-vector overlap}
}
\]

でbranchを追跡します。

つまり、

\[
v(t_k)
=
\arg\max_j
|\langle v(t_{k-1})|v_j(t_k)\rangle|^2
\]

を基本選択則としてください。

t0でmaximum-ground-overlap comparatorへ戻らないでください。

---

# 8. Degenerate phase cluster

旧S0と同じく、phase gapが

\[
<10^{-8}
\]

のclusterについては単一vector overlapではなく、projector continuityを使用してください。

cluster内のbasis choiceによる偽branch jumpを避けるためです。

---

# 9. Fixed branch numerical gates

以下を固定してください。

## Eigenpair residual

\[
\le 10^{-10}
\]

## PF unitarity residual

\[
\le 10^{-10}
\]

## Degenerate phase gap

\[
10^{-8}
\]

## Previous-branch overlap warning/gate

旧S0に合わせ、

\[
|\langle v_{k-1}|v_k\rangle|^2 \ge 0.9
\]

をbranch-quality requirementとして扱ってください。

---

# 10. Ground-overlap comparator

各点でmaximum-ground-overlap eigenpairをdiagnostic comparatorとして保存して構いません。

ただしprimary branch selectorにはしない。

保存：

- selected branch ID
- ground-overlap comparator ID
- disagreement flag

を推奨。

---

# 11. Branch IDs

new sourceごとにbranch namespaceを新規作成。

例：

```text
FS-R1:<source_identity_sha>:<branch_id>
```

historical branch ID：

- N2 `6`
- CO `9`

は絶対に流用しないでください。

---

# 12. Truth budget amendment

FS-R0の

`new direct truth coordinates = 2`

を、FS-R0.1で正式に

\[
\boxed{12}
\]

へ変更します。

ただし内訳を必ず保存：

```text
branch_certification_coordinates = 10
primary_scoring_coordinates = 2
total_direct_truth_coordinates = 12
```

historical truth reuse = 0。

---

# 13. No adaptive insertion

非常に重要です。

FS-R1 Phase Bでbranch continuationに失敗しても、

- midpoint追加
- 0.4追加
- 0.75追加
- smaller anchor追加
- denser grid追加

をそのrun内で行わないでください。

---

# 14. Failure policy

以下のいずれかが起きたら、

\[
\boxed{\text{BRANCH\_CONTINUATION\_FAILED}}
\]

としてfail closed。

- previous overlap < 0.9
- unresolved phase cluster
- residual gate failure
- unitarity gate failure
- ambiguous projector continuation
- duplicate branch assignment
- source identity mismatch
- required coordinate missing

その後の追加truthは禁止。

---

# 15. Failure後の扱い

branch failureはtechnical/numerical validation failureとして扱い、

resource outcomeには数えないでください。

結果を見てbranch ruleを変えず、GPT/userへ戻すこと。

---

# 16. FS-R1のPhase Aは変更しない

4-arm science設計はFS-R0のまま維持。

## M00′

new CISD + fixed 3-point fit

## M10′

Ritz8 + same 3-point fit

## M01′

new CISD local proxy at t0

## M11′

Ritz8 local proxy at t0

M11′ primary。

M01′ challenger。

---

# 17. Phase Aにはdirect truthを入れない

branch ladder coordinatesが増えても、Phase Aからtruth informationは見えないようにしてください。

Phase A inputsはsanitized sourceのみ。

禁止：

- exact-ground direct PF shift
- branch eigenpair
- previous branch overlap
- final t0 direct truth
- branch IDs

---

# 18. Phase A freeze

Phase A終了時に少なくとも：

- all four arm estimates
- B0′
- B01′
- B10′
- B11′
- source identity
- protocol hash
- execution code hash
- prediction hash
- manifest hash
- commit SHA
- independent remote verification receipt

をfreeze。

これが成立する前はtruth dispatcherを開かない。

---

# 19. Phase B truth execution order

Phase Bで必ずconditionごとに時刻昇順で実行してください。

N2：

```text
0.1t_ref
→0.2t_ref
→0.3t_ref
→0.5t_ref
→0.99t0
→t0
```

COも同様。

並列化する場合でもcondition内部のbranch dependency順序は壊さないこと。

N2とCOの2系列は独立。

---

# 20. Truth execution output

各coordinateについて最低限保存：

- condition
- source identity
- time
- time role
- selected eigenvalue
- selected eigenphase
- signed direct shift
- direct error
- selected branch ID
- previous branch ID
- ground overlap
- previous vector overlap
- degenerate projector overlap
- phase cluster size
- minimum phase gap
- eigenpair residual
- unitarity residual
- selection rule
- ground-overlap comparator ID
- disagreement flag
- unwrap integer
- wall
- RSS

---

# 21. Scoring input

resource scoringへ渡すのは各conditionの

\[
t=t_0
\]

のsigned direct shiftのみ。

他の10 branch coordinatesを、

- resource optimum
- best time
- extended reference
- arm selection

に使わないこと。

---

# 22. No new time optimization

12-point truth ladderはbranch certification用です。

このtruthを見て、

- better t
- minimum direct cost
- optimal time

を選ばないでください。

FS-R1は固定t0 intervention studyです。

---

# 23. B0′ / budget contract維持

FS-R0の式を変更しない。

\[
B_0'
=
\frac{\gamma\beta K}
{t_0(\epsilon_E-|M00'(t_0)|)}
\]

各arm：

\[
B_j'
=
\frac{\gamma\beta K}
{t_0(\epsilon_E-|M_j'(t_0)|)}
\]

---

# 24. Safety scoring

t0のnew direct truthを

\[
e=|\delta'_{\rm direct}(t_0)|
\]

として、

\[
S_j
=
\epsilon_E
-e
-\frac{\beta K}{t_0 B_j'}
\]

を保存。

safe iff

\[
S_j\ge0.
\]

---

# 25. Resource outcome ruleは変更しない

\[
\eta=0.02
\]

維持。

### primary_gain

M11′ safe and

\[
B_{11}'\le0.98B_0'
\]

### local_gain

M01′ safe and

\[
B_{01}'\le0.98B_0'
\]

### state_increment

M01′ and M11′ safe and

\[
B_{11}'\le0.98B_{01}'
\]

### safety_repair

M01′ unsafe, M11′ safe。

---

# 26. Branch certificationはoutcomeにしない

branch ladder PASSはscience successではありません。

これはt0 truth validityを保証するnumerical gateです。

---

# 27. Production executor preflight

今回FS-R0.1ではtruth production executorを完成させてよいですが、実行は禁止。

確認対象：

- 1568-dimensional sector
- current_m3 PF
- Schur/eigensolve backend
- deterministic ordering
- selected vector checkpoint
- continuation callback
- branch namespace
- residual calculation
- unitarity calculation
- projector cluster handling
- serialization

---

# 28. Source identity barrier

truth executorは必ずFS-R0 source identityとbind。

N2：

`6b93735a56638c40a2bcd35e504f1ee823cfdbe396441fce15fd5e02502b044d`

CO：

`ed9ec93d6945a11bd144d2531ffedaf67da829383334b47206b78c11aee34f17`

別sourceでは停止。

---

# 29. Exact ground isolation

exact groundはtruth-only branch seed/comparatorに限って使用。

Phase A operational archiveには存在しない状態を維持。

truth outputにもground vector本体をpublic保存しない。

scalar overlap diagnosticsのみ。

---

# 30. Truth-only source

private original regenerated sourceからtruth moduleが必要なexact-ground informationを読む場合、

- explicit truth-only loader
- separate code path
- barrier requirement

を設けてください。

operational source loaderと混同しない。

---

# 31. Prediction recovery

H4と同じくPhase A scientific return直後にprivate scalar recovery snapshotを作る。

truth phaseはrecovery済みprediction hashを参照。

serialization failure後にPhase Aを勝手にrerunしない。

---

# 32. Branch vector checkpoints

branch continuation用selected vectorsはprivate checkpointとして保存可能。

Git/public artifactにはvector本体を出さない。

保存：

- private path
- SHA
- source identity
- time
- branch ID

だけpublic manifestへ記録可能。

---

# 33. Cost accounting

Truth Phase Bについて以下を別途計上可能なschemaにする。

- PF matrix/unitary construction
- Schur/eigendecomposition
- branch matching
- selected-vector checkpoint
- residual
- unitarity
- wall
- RSS/GPU memory

FS-R1 calibration costとは別カテゴリ：

`truth_validation_cost`

とする。

QPE resourceへ加算しない。

---

# 34. Action budget amendment

FS-R0 Phase A予定量は変更しない。

Phase Bのみ、

```text
direct_truth_coordinates = 12
branch_certification = 10
primary_scoring = 2
```

へ更新。

truth backend action countは実装から計算し、推測値ならplannedとして明記。

---

# 35. FS-R0.1で実行してよいこと

- protocol amendment
- branch ladder freeze
- truth-only executor implementation
- barrier implementation
- branch matcher implementation
- projector continuity implementation
- synthetic tests
- tiny-matrix tests
- serialization/recovery tests
- source identity tests
- cost schema
- documentation
- commit/push

---

# 36. FS-R0.1で禁止

- N2/CO actual PF truth construction
- Schur/eigendecomposition on N2/CO production source
- direct PF branch solve
- M00′/M10′/M01′/M11′ computation
- production Ritz
- production proxy
- resource outcome scoring

---

# 37. Tests — branch initialization

最低限：

1. first coordinate uses maximum ground overlap
2. later coordinates cannot use ground-overlap selector
3. historical branch IDs rejected
4. new source namespace enforced
5. wrong source SHA rejected

---

# 38. Tests — continuation

6. previous-vector overlap selector
7. overlap below 0.9 fails
8. exact tie deterministic
9. phase-cluster projector path
10. phase gap threshold exactly \(10^{-8}\)
11. ambiguous cluster fails
12. missing prior checkpoint fails
13. non-monotone time sequence fails

---

# 39. Tests — truth budget

14. exactly 6 coordinates per condition
15. exactly 12 total
16. only two t0 points marked scoring
17. adaptive midpoint rejected
18. extra coordinate rejected
19. historical truth substitution rejected
20. nearest-time substitution rejected

---

# 40. Tests — numerical quality

21. eigenpair residual >1e-10 fails
22. unitarity residual >1e-10 fails
23. NaN/Inf fails
24. duplicate eigenbranch assignment handled/fails appropriately
25. selected-vector normalization

---

# 41. Tests — Phase barrier

26. truth before Phase A freeze rejected
27. prediction hash mismatch rejected
28. source hash mismatch rejected
29. protocol mismatch rejected
30. code mismatch rejected
31. remote receipt mismatch rejected

---

# 42. Tests — scoring isolation

32. branch intermediate values cannot enter B0′
33. branch intermediate values cannot change t0
34. branch intermediate values cannot select arm
35. only final t0 truth reaches scorer
36. ground overlap not used as estimator

---

# 43. Existing tests

既存195 testsを壊さないこと。

新しいtest countを別途報告。

---

# 44. Protocol version

FS-R1 protocolをv2へamendしてください。

例：

`FS-R1-20261007-v2`

旧v1を上書きしない。

Revision reason：

`new-source physical branch continuation requires preregistered lower-time certification ladder`

---

# 45. v2 truth contract

最低限：

```text
truth_total_coordinates = 12
truth_primary_scoring_coordinates = 2
truth_branch_certification_coordinates = 10

branch_times =
[0.1*t_ref, 0.2*t_ref, 0.3*t_ref, 0.5*t_ref, 0.99*t0, t0]

first_selector = maximum_exact_ground_overlap
continuation_selector = maximum_previous_selected_vector_overlap

phase_cluster_gap = 1e-8
previous_overlap_gate = 0.9
eigenpair_residual_gate = 1e-10
unitarity_gate = 1e-10

adaptive_truth_extension = forbidden
```

を固定。

---

# 46. FS-R0.1 GO / NO-GO

## `GO_FOR_FS_R1_PHASE_A`

条件：

- branch ladder frozen
- all coordinates exact
- source identity bound
- production truth executor code complete
- continuation matcher complete
- projector continuity complete
- Phase A/B barrier updated
- action/cost schema complete
- tests pass
- production new truth = 0
- FS-R1 science = 0

---

## `NO_GO_BRANCH_PROTOCOL`

branch rule自体が実装/仕様上閉じない。

---

## `NO_GO_TRUTH_EXECUTOR`

production truth backendを実装readyにできない。

---

## `NO_GO_SOURCE_TRUTH_INTERFACE`

truth-only source / exact ground separationが成立しない。

---

## `NO_GO_OTHER`

理由を明示。

---

# 47. GO後も実行しない

`GO_FOR_FS_R1_PHASE_A`でも、FS-R1 Phase Aを自動実行しないでください。

必ずGPT/userへ戻してください。

---

# 48. 必須成果物

例：

`artifacts/pf_first_study_fs_r01_branch_extension_20261007/`

最低限：

1. `README.md`
2. `branch_extension_amendment.md`
3. `fs_r1_protocol_v2.json`
4. `fs_r1_protocol_v2.md`
5. `branch_ladder.json`
6. `branch_contract.md`
7. `truth_budget.json`
8. `truth_executor_contract.md`
9. `truth_only_source_contract.md`
10. `branch_checkpoint_schema.json`
11. `phase_barrier_v2.md`
12. `cost_contract_truth.json`
13. `predicted_action_budget_v2.json`
14. `tests.log`
15. `verification.json`
16. `source_manifest.json`
17. `publication_manifest.json`
18. `GO_NO_GO_FOR_FS_R1_PHASE_A.json`

private vectors/matrices/source binariesはGitへcommitしない。

---

# 49. 最終報告

完了時に以下を簡潔に報告してください。

1. branch ladder確定
2. N2 six coordinates
3. CO six coordinates
4. truth total=12 / scoring=2
5. first-anchor selector
6. continuation selector
7. overlap / residual / unitarity / cluster gates
8. adaptive insertion禁止
9. source identity binding
10. truth-only exact-ground isolation
11. production truth executor ready status
12. tests
13. actual new truth count=0
14. actual FS-R1 science count=0
15. final GO/NO-GO
16. branch / commit / push / remote verification

---

# 50. 停止条件

FS-R0.1完了後、必ず停止してください。

次の順序は、

\[
\boxed{
\text{FS-R0.1}
\rightarrow
\text{GPT review}
\rightarrow
\text{FS-R1 Phase A}
\rightarrow
\text{prediction freeze}
\rightarrow
\text{FS-R1 Phase B branch truth}
}
\]

です。

FS-R0までのartifact、historical first-study、Phase0、H4、FS-C0/C0.5/C0.6は変更しないでください。