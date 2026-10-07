第1研究について、historical H01 source復元路線を終了し、**新しく固定した再構成source上で内部整合したfollow-up experimentを行うための FS-R0：regenerated-source re-baselining protocol / preflight** を進めてください。

今回は**設計・source freeze・実装・preflightのみ**です。

\[
\boxed{\text{FS-R1 scienceはまだ実行しない}}
\]

特に、

- 新PF/echo science
- Ritz science
- 4-arm prediction
- new direct PF truth

は今回0のまま停止してください。

---

# 0. 起点

Repository:

`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

直前のFS-C0.6:

- Branch  
  `pf-first-study-fs-c06-functional-equivalence-20261007`

- Commit  
  `14972353238cb001ccb1f754288daaae1ec3f65e`

- Artifact  
  `artifacts/pf_first_study_fs_c06_functional_equivalence_20261007/`

FS-C0.6 final status:

`NO_GO_RECONSTRUCTION_MISMATCH`

理由：

historical H01 pickleはmissingであり、existing H02 candidateおよびone-shot reconstructionはhistorical Hamiltonian SHAに一致しなかった。

FS-C1は未実行。

---

# 1. 今回の研究判断

historical H01 sourceを復元してFS-C1を行う路線は終了します。

以下を今後行わないでください。

- historical pickle探索の継続
- historical Hamiltonian SHAへ合わせるための再構成反復
- PySCF / orbital / grouping / ordering等のparameter tuningによるhistorical sourceへの追従
- current reconstructed sourceをhistorical sourceと呼ぶこと
- historical direct PF truthをnew sourceのtruthとして流用すること
- historical B0をnew source baselineとして使用すること

代わりに、

\[
\boxed{\text{new internally consistent follow-up experiment}}
\]

として再設計します。

---

# 2. 新しい研究系列

今後は、

- **FS-R0**：regenerated-source re-baselining / preflight
- **FS-R1**：4-arm prediction + new direct truth scoring
- 必要ならその後のFS-R2

という新系列にします。

FS-C0/C0.5/C0.6はhistoryとして保持し、上書きしません。

---

# 3. New sourceの位置づけ

FS-C0.6で各条件について**一度だけpinned reconstruction**したsourceを、FS-R0のnew follow-up source候補とします。

historical sourceの代替物ではなく、

`new regenerated follow-up source`

として扱ってください。

---

# 4. 固定するnew source candidate

## N2 equilibrium

Condition:

`N2_active_eq_sto3g`

FS-C0.6 one-shot reconstructed Hamiltonian SHA:

`f4a08b755a4e903f4e9611fee394d6101a5d27279a1bd8af567b97920da5402e`

---

## CO equilibrium

Condition:

`CO_active_eq_sto3g`

FS-C0.6 one-shot reconstructed Hamiltonian SHA:

`27ed246b354c754a506541dac81650aafdfa413b375fadf0b736822c171fb4c5`

---

これらのsourceをhistorical H SHAへ近づけるために再構成し直さないでください。

結果を見てN2/COのうち「historicalに近い方だけ」を採用することも禁止です。

両条件を最初から登録したまま扱います。

---

# 5. Source freeze前の確認

FS-C0.6で作成されたprivate reconstruction binariesが現在利用可能か確認してください。

利用可能なら、そのexact bytesをFS-R0 candidateとして使用。

利用不能なら、**再構成を自動的にやり直さないでください。**

その場合は、

`NO_GO_REGENERATED_SOURCE_BYTES_UNAVAILABLE`

として停止してください。

FS-C0.6で一度だけ生成したものとは別のsourceを無断で作らないこと。

---

# 6. New source identity

new sourceについて、historical identityとは独立の新しいcanonical identityを固定してください。

N2/COごとに最低限：

- source kind = `FS-C0.6 one-shot pinned reconstruction`
- source generation commit / code identity
- environment
- Hamiltonian SHA
- restricted basis SHA
- CISD SHA
- ordered group identity SHA
- each group/component SHA
- sector metadata SHA
- removed constant
- dtype
- shape
- serialization rule

を保存してください。

---

# 7. Historical sourceとの関係

historical H01 sourceとの比較はprovenance/limitationとしてのみ保存。

FS-R0以降のscience gateには、

`historical H SHA exact match`

を使わないでください。

FS-R1で必要なのは、

> **FS-R0でfreezeしたnew source自身が、prediction phaseとtruth phaseの両方で同一であること**

です。

---

# 8. Operational source sanitization

FS-R1 operational input用にsanitized exportを作ってください。

含めてよいもの：

- restricted Hamiltonian
- ordered group representation / component spectra
- CISD vector
- restricted basis
- sector / mapping metadata
- removed constant
- current_m3 order / coefficients

含めてはいけないもの：

- exact ground vector
- exact ground overlap
- exact gap
- direct PF eigenvalue truth
- direct optimum
- historical truth
- branch label
- past safe/unsafe label
- FS-C0.6 acceptance/rejection resultsをselector inputにするfield

---

# 9. Exact groundの扱い

FS-C0.6 reconstruction sourceにexact groundが含まれていても、

**FS-R1 operational exportから必ず削除**してください。

exact groundは今後、

- source regeneration validation history
- new direct truthを生成するtruth-only module

以外では使わない。

M00′/M10′/M01′/M11′ computationへ入れないでください。

---

# 10. 新しい4-arm設計

historical M00/M10/M01/M11ではなく、new source上の

\[
M00',M10',M01',M11'
\]

として定義してください。

---

## M00′ — New-source CISD + fixed 3-point fit

State:

new regenerated source CISD

Training absolute coordinatesはhistorical studyから固定design coordinateとして継承します。

### N2

```text
0.06263494343795273
0.12526988687590546
0.18790483031385818
```

### CO

```text
0.06546804264781796
0.1309360852956359
0.19640412794345388
```

Fit:

\[
f_0'(t)=a_4t^4+a_6t^6
\]

- no intercept
- unweighted
- historical H01 numerical fit conventionを固定
- no extra point
- 0.4 historical relative coordinate追加禁止
- 0.5 sentinel追加禁止

---

## M10′ — New-source Ritz8 + same 3-point fit

State:

residual Krylov Ritz \(m=8\)

Training coordinates:

**M00′と全く同じ3 absolute times**

Ritz用に新しいanalytic timeを作らない。

fit:

\[
f_8'(t)=a_4t^4+a_6t^6
\]

same fit rule.

---

## M01′ — New-source CISD + local selected-time proxy

State:

new-source CISD

Coordinate:

historical selected \(t_0\)を**固定design coordinate**として継承。

### N2

\[
t_0=0.5983202971910435
\]

### CO

\[
t_0=0.6127481451622522
\]

Quantity:

\[
g_{\rm CISD}'(t_0)
\]

no fit.

---

## M11′ — New-source Ritz8 + local selected-time proxy

State:

same Ritz8 state as M10′

Coordinate:

same fixed \(t_0\)

Quantity:

\[
g_{\rm Ritz}'(t_0)
\]

M11′ remains primary.

M01′ remains cheaper challenger.

---

# 11. Historical coordinatesの意味

historical training times / \(t_0\) は、

> new sourceで再最適化したtime

ではありません。

これらは、

> prior development studyから固定されたexternal design coordinates

です。

FS-R1ではtime selection itselfを新しく最適化しません。

これによって、

state improvement vs local evaluation

だけを比較します。

---

# 12. New baseline \(B_0'\)

historical B0をnew source baselineへ流用しないでください。

new M00′ prediction

\[
c_{00}'=
|f_0'(t_0)|
\]

から、

\[
\boxed{
B_0'
=
\frac{
\gamma\beta K
}{
t_0(\epsilon_E-c_{00}')
}
}
\]

を計算します。

Constants:

\[
\epsilon_E=0.00015936001019904
\]

\[
\beta=1.2
\]

\[
\gamma=1.01
\]

historical current_m3 Kをdesign constantとして使う場合は、new sourceでもPF group/rotation contractが同じであることを先に確認してください。

不一致ならstop。

---

# 13. 各arm budget

各armのestimate magnitudeを \(c_j\) として、

\[
B_j
=
\frac{
\gamma\beta K
}{
t_0(\epsilon_E-c_j)
}
\]

を使用。

\[
c_j\ge\epsilon_E
\]

ならinfeasible。

後処理でclipしない。

---

# 14. Resource success criterion

旧FS-C1案を維持します。

Design target:

\[
\eta=0.02
\]

2% saving。

各conditionで、

### primary_gain

\[
M11' \text{ safe},
\qquad
B_{11}'\le0.98B_0'
\]

### local_gain

\[
M01' \text{ safe},
\qquad
B_{01}'\le0.98B_0'
\]

### state_increment

\[
M01',M11'\text{ safe},
\qquad
B_{11}'\le0.98B_{01}'
\]

### safety_repair

M01′ unsafe and M11′ safe.

savingとは別に扱う。

---

# 15. New direct truth

historical direct PF truthはnew sourceへ使用禁止。

FS-R1ではnew sourceごとに、

\[
\boxed{
\delta_{\rm direct}'(t_0)
}
\]

を新規取得します。

必要座標はまず：

- N2 \(t_0\) 1点
- CO \(t_0\) 1点

合計2 direct truth coordinates。

---

# 16. Truth generationはFS-R0では行わない

今回FS-R0では、

\[
\boxed{\text{new direct truth count = 0}}
\]

です。

truth generation code / contract / barrierは実装してよいですが、実行は禁止。

---

# 17. FS-R1のPhase A / Phase B構造

FS-R1は1つの承認scope内でも、内部的に必ず二段階にしてください。

## Phase A

new sourceだけを読み、

- M00′
- M10′
- M01′
- M11′
- all fits
- all budgets
- source/code/protocol hashes

を生成。

truth unopened。

Phase A prediction artifactをcommit/hash freeze。

---

## Phase B

verified frozen Phase Aを確認後、

new direct truth 2 pointsのみ取得/読む。

その後scoring。

Phase A predictionを変更しない。

---

# 18. New truth branch contract

direct PF truthの計算法をFS-R0で事前固定してください。

少なくとも：

- same regenerated Hamiltonian
- same sector
- same current_m3
- same group ordering
- same energy origin
- same \(t_0\)
- same physical branch continuation definition
- branch residual gate
- unitarity gate
- duplicate/missing prohibition

を明示。

historical branch ID 6 / 9はnew sourceへ継承しないでください。

new sourceにはnew branch identityを割り当てます。

---

# 19. New truth algorithm

既存のS0 exact-time direct PF truth generation methodを再利用できる場合でも、

new source identityへ明示的に接続してください。

historical direct valueをlookupして返すfallbackは禁止。

---

# 20. Truth barrier

Phase A completion前にtruth moduleが、

- direct PF eigensolve
- direct branch
- exact-state PF eigenvalue

を返せないようにしてください。

Phase B activationには最低限：

- Phase A commit SHA
- prediction SHA
- protocol hash
- source identity hash
- code hash
- remote verification

を要求。

---

# 21. Ritz construction

H4 Phase 0.5で固定したresidual Krylov/Ritz数値規則を基本として継承してください。

- \(m=8\) primary
- no result-dependent rank change
- MGS exactly 2 passes
- prefix rank stop
- no replacement direction
- deterministic phase convention
- projected Hermiticity gate
- lowest Ritz pair
- no full-H ground state input

ただしdimension=1568 backendに適用可能かpreflightで確認。

---

# 22. Rank diagnostics

FS-R1ではm=8 primaryのみをscience armとし、

m=1/2/4の大規模truth-scored diagnosticsを自動追加しないでください。

FS-R0で必要ならsynthetic rank-stop testだけ。

今回の研究質問はrank sweepではありません。

---

# 23. Native PF backend

new operational sourceを使い、

- arbitrary CISD/Ritz vector
- current_m3
- fixed group ordering
- complex128
- exact sign convention

を扱えるproduction adapterを実装してください。

FS-R0ではproduction science proxy値を取得しない。

---

# 24. Echo definition

\[
g_\psi(t)
=
\frac{
\operatorname{Im}
\langle\psi|
e^{-iHt}U_P(t)
|\psi\rangle
}{t}
\]

を固定。

等価実装の場合もsign/origin/state identityを保持。

---

# 25. Cold replay

FS-R1 Phase Aではcomplete cold replayを1回実施できるようにしてください。

cold replayでは、

- source load
- Ritz basis
- Ritz state
- PF
- echo
- proxy
- fit
- budget

をindependentに再構築。

science intermediate cache共有禁止。

---

# 26. Recovery snapshot

順序：

\[
\text{science return}
\rightarrow
\text{private scalar recovery}
\rightarrow
\text{public validation}
\rightarrow
\text{freeze}
\]

を固定。

public serialization failureを理由にscience rerunしない設計にしてください。

---

# 27. Cost accounting

classical calibration costとpredicted QPE costを分離。

最低限：

## Classical

- source load
- explicit H matvec
- Ritz small solve
- PF forward vector action
- exact-H echo action
- group application
- group materialization
- scalar fit
- wall seconds
- peak RSS
- threads/software

## Quantum resource proxy

- predicted PF rotations \(B_j\)

を別々に記録。

CPU seconds + rotationsを1 scalarへ加算しない。

---

# 28. `expm_multiply` internal cost

内部matvec等を取得可能なら保存。

取得不能ならnull/unknown。

0としない。

---

# 29. Incremental cost views

joint experiment costのほか、

baseline calibration already availableと仮定したincremental costも報告可能なschemaを作ってください。

### M01′ incremental

- local PF forward ×1
- local exact-H echo ×1

### M11′ incremental

- Ritz refinement
- small Ritz solve
- local PF forward ×1
- local exact-H echo ×1

ただし今回FS-R0では実測値を作らず、schema/action formulaのみ。

---

# 30. Expected FS-R1 coordinates

各conditionのPhase A operational coordinatesは、

### CISD

- three training times
- \(t_0\)

= 4 coordinates

### Ritz

- same three training times
- \(t_0\)

= 4 coordinates

両方合わせて1 condition 8 state-coordinate proxy evaluations。

2 conditionsで16。

cold replay込みで32 logical state-coordinate evaluations。

backend schedulingによるblock action数は別に計上。

---

# 31. New direct truth coordinates

Phase B:

2 total coordinatesのみ。

- N2 \(t_0\)
- CO \(t_0\)

新truthを近傍timeへ広げない。

---

# 32. Development status

N2/COは既知development条件です。

FS-R1が成功しても、

- independent validation
- prospective validation
- molecular transfer guarantee

とは呼ばないでください。

---

# 33. Historical resultsとの比較

historical first-study scalarは、

- motivation
- design history
- prior headroom

として参照可能。

ただしnew sourceの、

- B0′
- direct truth′
- savings′

とnumerically同一分母として混ぜない。

historical/new sourceの差をmethod improvementとして解釈しない。

---

# 34. FS-R0のscience禁止事項

今回禁止：

- new M00′ proxy production computation
- new M10′ Ritz construction
- new M01′ local proxy
- new M11′ local proxy
- new direct PF truth
- new branch solve
- new science fit
- new budget outcome
- state/rank/result inspectionによるprotocol tuning

---

# 35. FS-R0で許可すること

- FS-C0.6 reconstruction bytes availability確認
- source freeze
- source sanitization
- canonical hashing
- static/backend interface inspection
- synthetic tests
- metadata-only load
- schema/action counter implementation
- truth barrier implementation
- recovery/freeze implementation
- scorer implementation
- documentation
- commit/push

---

# 36. Source sanitization tests

最低限：

1. exact ground absent
2. overlap absent
3. gap absent
4. direct PF truth absent
5. branch truth absent
6. historical labels absent
7. required H/groups/CISD present
8. sanitized H hash equals frozen new-source H
9. group order preserved
10. CISD bytes preserved from new source

---

# 37. Prediction/truth barrier tests

最低限：

11. Phase B before Phase A freeze rejected
12. changed prediction rejected
13. changed source rejected
14. changed protocol rejected
15. changed code rejected
16. missing remote verification rejected
17. historical truth path rejected as new truth
18. historical branch ID cannot satisfy new-source truth
19. nearest-time substitution rejected
20. more than two truth coordinates rejected

---

# 38. Arm/scoring tests

21. M00′ 3-point fit
22. M10′ exact same absolute coordinates
23. M01′ no fit
24. M11′ no fit
25. B0′ arithmetic
26. infeasible \(c\ge\epsilon\)
27. safety slack
28. primary_gain
29. local_gain
30. state_increment
31. safety_repair
32. no post-hoc best arm

---

# 39. Recovery/cost tests

33. recovery before public validation
34. serialization failure does not rerun science
35. cold replay counts separately
36. internal expm unknown remains null
37. wall/RSS schema
38. classical and QPE units remain separate

既存FS-C0/C0.5/C0.6 testsを可能な範囲で維持。

---

# 40. FS-R1 protocol

新しいmachine-readable protocolを作ってください。

例：

`FS-R1-20261007-v1`

最低限：

- research question
- new source identities
- development status
- fixed training coordinates
- fixed \(t_0\)
- M00′/M10′/M01′/M11′
- Ritz m8
- fit rule
- constants
- B0′ definition
- safety definition
- eta=0.02
- outcome rules
- cost accounting
- Phase A/B barrier
- new truth count=2
- no historical truth reuse
- stop rules

を含める。

---

# 41. FS-R1 outcome rules

各condition個別に保存。

### `primary_gain`

M11′ valid + safe + at least 2% saving vs B0′.

### `local_gain`

M01′ valid + safe + at least 2% saving vs B0′.

### `state_increment`

M01′/M11′ safe and M11′ at least 2% below B01′.

### `safety_repair`

M01′ unsafe and M11′ safe.

---

# 42. Study-level interpretation

2 conditionsについて：

- 2/2 primary_gain  
  → small development support
- 1/2  
  → condition-dependent
- 0/2  
  → no resource-stage support

ただし平均でunsafe conditionを相殺しない。

---

# 43. Stop rules after FS-R1

protocolへ事前に記載してください。

- M11′ unsafe on either condition  
  → resource extension STOP
- both safe but 2% target not met  
  → stop micro-accuracy optimization
- M01′ already sufficient and M11′ adds no state_increment  
  → local evaluation becomes preferred simpler intervention
- state_increment 2/2  
  → consider state-refinement extension
- 1/2  
  → retain condition dependence; do not add molecules until success
- technical failure  
  → separate from science result

---

# 44. FS-R0 GO / NO-GO

最終statusは以下。

## `GO_FOR_FS_R1`

条件：

- exact FS-C0.6 one-shot source bytes available
- both new source identities frozen
- sanitized operational exports valid
- 4-arm protocol complete
- truth-generation contract complete
- Phase A/B barrier complete
- recovery complete
- cost accounting complete
- tests pass
- FS-R1 science action 0
- new direct truth 0

---

## `NO_GO_REGENERATED_SOURCE_BYTES_UNAVAILABLE`

C0.6 source bytesが失われている。

---

## `NO_GO_SANITIZATION`

oracle/truth-free operational sourceを作れない。

---

## `NO_GO_PROTOCOL_OR_BACKEND`

science-ready protocol/backendが閉じない。

---

## `NO_GO_OTHER`

reasonを明示。

---

# 45. 必須成果物

新しいartifact directory例：

`artifacts/pf_first_study_fs_r0_rebaseline_20261007/`

最低限：

1. `README.md`
2. `research_pivot.md`
3. `fs_r1_protocol.json`
4. `fs_r1_protocol.md`
5. `new_source_registry.json`
6. `new_source_identity.json`
7. `historical_vs_new_source_scope.md`
8. `sanitized_export_manifest.json`
9. `sanitization_audit.json`
10. `four_arm_contract.md`
11. `truth_generation_contract.md`
12. `truth_barrier.md`
13. `scoring_contract.json`
14. `cost_contract.json`
15. `predicted_action_budget.json`
16. `cold_replay_contract.md`
17. `recovery_contract.md`
18. `tests.log`
19. `verification.json`
20. `source_manifest.json`
21. `publication_manifest.json`
22. `GO_NO_GO_FOR_FS_R1.json`

private H/vector/group binariesはpolicyに従い、無断でGitへcommitしない。

hash/manifestは公開可能。

---

# 46. 最終報告

完了時は簡潔に、

1. historical recovery route終了を記録したか
2. exact FS-C0.6 source bytes availableか
3. N2 new H SHA
4. CO new H SHA
5. sanitized export status
6. M00′/M10′ training coordinates
7. fixed \(t_0\)
8. B0′ definition
9. new truth contract = 2 points
10. truth barrier
11. expected FS-R1 action counts
12. tests
13. FS-R1 science count=0
14. new direct truth count=0
15. final GO/NO-GO
16. branch / commit / push / remote verification

を報告。

---

# 47. 停止条件

FS-R0完了後、必ず停止してください。

\[
\boxed{\text{GO_FOR_FS_R1でもscienceを開始しない}}
\]

次のFS-R1 science executionはGPT/userの別承認後です。

historical first-study、Phase0、H4 intervention、FS-C0/C0.5/C0.6 artifactsは変更しないでください。