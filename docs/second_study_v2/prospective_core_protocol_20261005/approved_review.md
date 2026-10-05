確認しました。結論から言うと、**Direction Cは維持したまま、20条件案をそのまま採用するのではなく、科学的には16条件のcore prospective validationへ絞る**のがよいです。HCNは初回batchから外し、CH2はhistory監査を通過した場合のみ「new-family stratum」として採用します。

また、今回は本計算までは許可せず、

\[
\boxed{
\text{protocol化}
\rightarrow
\text{一般分子wrapper実装・focused tests}
\rightarrow
\text{bounded input/reference preparation}
}
\]

までを次工程として許可するのが妥当です。candidate cheap、M1、ground、direct truth、scoringはその次のレビュー後です。

---

# A. 承認できる科学的仕様

## A1. 対象条件：20条件案はそのまま採用しない

preflightの20条件は、

- LiH 4
- LiF 4
- BeH2 4
- CH2 singlet 4
- HCN 4

ですが、これを一つの20-condition validationとして扱うのは勧めません。

理由は明確です。

- LiH/LiF/BeH2は既使用family。
- CH2/HCNはrepository上のfamily-unseen認定が未完了。
- HCNはsector dimension 15,876で、truthのdense ledgerだけで約33.8 GiB、提案例では約37.8 GiB/workerとなり、allocation未確認の現状ではcore setに固定するには重すぎる。
- CH2 singlet案はclosed-shell実装には都合がよいものの、ground-state研究のprospective validationとして採用するにはspin-sectorの意味が曖昧になる。

したがって、以下を推奨します。

### Stratum U：既使用familyのnew-condition validation — 12 conditions

| family | geometry | basis/space | charge / sector |
|---|---|---|---|
| LiH | \(R=1.40,1.80,2.20,2.60\) Å | STO-3G, full 4e/6o | 0, \(n_\alpha=n_\beta=2\) |
| LiF | \(R=1.40,1.80,2.20,2.60\) Å | STO-3G, frozen-core 8e/8o | 0, \(4,4\) |
| BeH2 | symmetric \(R=1.20,1.40,1.80,2.20\) Å | STO-3G, full 6e/7o | 0, \(3,3\) |

これらは**new-familyではありません**。

LiH/BeH2は過去とactive-space contractも異なるものがあるので、

> `used_family_new_condition_or_contract`

として扱うのが正確です。

### Stratum N：new-family prospective validation — CH2 4 conditions

ただし、**repository-tracked history auditでCH2 familyが未使用と確認できた場合のみ採用**します。

singlet案ではなく、以下を推奨します。

- neutral CH2
- fixed \(2S=2\), multiplicity 3
- \(n_\alpha=5,n_\beta=3\)
- STO-3G full 8e/7o
- \(R_{\rm CH}=1.00,1.15,1.40,1.70\) Å
- angle 102°はpreflightのdesign geometryをそのまま固定
- 「平衡構造」や「global molecular ground state」とは呼ばない
- **fixed triplet-sector ground validation** と呼ぶ

state recipeは

\[
\boxed{\text{ROHF reference + determinant CISD}}
\]

とします。

UHFへの自動fallbackは認めません。

### HCN

初回prospective batchからは**除外**します。

これは科学結果を見た選別ではなく、preflight時点で既に分かっている計算量による除外です。

HCNは、

> `resource-contingent high-dimension extension`

として別batch候補に残します。

allocationとtruth feasibilityを別途確認してからです。

---

## A2. 推論単位

16 conditionsを16 independent samplesとは数えません。

最小単位はfamilyです。

- LiH geometry series
- LiF geometry series
- BeH2 geometry series
- CH2 geometry series

の4 strata/familiesとして扱います。

3 candidate timesも独立sampleではありません。

したがって、例えば

> 48/48 coordinates safe

より、

> 4 families中、各familyの何conditionsでどのregimeが観測されたか

を主に報告すべきです。

---

# A3. Hamiltonian/state contract

全条件で、

- canonical `current_m3`
- STO-3G
- JW/ordered grouping convention
- scalar identity origin
- MO ordering
- sector indices
- state hash
- group/Pauli coefficient hash
- current_m3 coefficient hex
- per-condition \(K\)

をprediction前にfreezeします。

\(K\) は各分子で新しく数えます。旧分子の値を流用しません。

### Closed-shell

LiH/LiF/BeH2：

\[
\boxed{\text{RHF + determinant CISD}}
\]

CISDはRHF determinantから、固定されたactive space内でpopulationを保存するsingle/double excitationを全列挙し、そのsubspace Hamiltonianの最低固有vectorを使います。

これはPySCFのRCISDと同一と仮定しません。

### CH2 triplet

\[
\boxed{\text{ROHF + determinant CISD}}
\]

とし、同じdeterminant-CISDロジックを \(n_\alpha=5,n_\beta=3\) sectorへ適用します。

prediction input生成でexact ground solveは禁止です。

SCF不成立なら、

`input_reference_ineligible`

として停止し、RHF↔ROHF↔UHFの救済切替をしません。

---

# A4. 一般分子 reference/time contract

ここは今回もっとも重要な判断です。

H-chain contractを無断コピーするのではなく、**一般分子用として明示的に新たに承認**します。

過去のNH3診断では、0.06–0.80の共有gridがfull-electronでは5/12しか通らなかった一方、0.02–1.8のsensitivity gridは24/24を通りました。ただしその資料自身も「universal replacement protocolではない」としています。

したがって、prospective validationで初めてそのtransferabilityを検証する、という位置付けにします。

### observable

\[
\delta_C(t)
=
\frac{
\Im
\langle
e^{+itH}\psi_{\rm CISD},
U_P(t)\psi_{\rm CISD}
\rangle
}{t}.
\]

これは、

- exact ground proxyではない
- \(\arg(\mathrm{echo})/t\) ではない
- D4 expectationではない

という現在の定義を維持します。

### reference grid

一般分子用として、

\[
\boxed{
t_j=\operatorname{geomspace}(0.02,1.8,34)
\ {\rm Ha}^{-1}
}
\]

を承認します。

全34点取得します。fitが早く見つかっても途中停止しません。

取得上限：

- 34 PF vector actions / condition
- 34 H exponential actions / condition

です。

### fit rule

- rolling 5 points
- formal order \(p=4\)
- \(|p_{\rm free}-4|\le0.2\)
- \(R^2\ge0.999\)
- noise floor：

\[
\boxed{5\times10^{-12}\ {\rm Ha}}
\]

を一般分子prospective用として固定することを推奨します。

ここだけH-chainの \(5\times10^{-13}\) から変更します。

理由は、過去のfull-electron NH3 sensitivity診断で0.02–1.8 gridとこのfloorが使用されているためです。

これはprospective結果を見た後の救済ではありません。

### \(\alpha_C\)

選ばれた最初のqualifying windowで、

\[
\alpha_C
=
10^{
\operatorname{mean}
[
\log_{10}|\delta_C(t)|
-
4\log_{10}t
]
}.
\]

exact implementationは既存`leading_fit` semanticsをCodexに転記・testさせます。

### \(t_{\rm ref}\)

\[
\boxed{
t_{\rm ref}
=
\left(
\frac{\epsilon_E}{5\alpha_C}
\right)^{1/4}
}
\]

とします。

重要なのは、これはleading model

\[
c(t)=\alpha_C t^4
\]

に対するcontinuous cost

\[
\frac{1}{t(\epsilon_E-\alpha_Ct^4)}
\]

の予測最適時刻です。

したがって今回は、H-chainのように最適点より左だけを見るのではなく、**予測optimumをbracketします。**

### 3 candidate times

\[
\boxed{
t\in
\{0.8,\ 1.0,\ 1.2\}t_{\rm ref}
}
\]

を採用します。

この方が今回のprospective studyには適しています。

H-chainの

\[
\{0.5,0.65,0.8\}t_{\rm ref}
\]

はbenchmark構造によって約33%削減がかなり決まっていました。

今回はそれを避け、

> predicted optimum周辺でfinite-time deviationとbudget safetyを見る

設計にします。

### candidate-domain gate

3候補すべてについて、

\[
0.02\le t\le1.8
\]

を要求します。

1つでも外れる場合は、

`candidate_time_domain_ineligible`

としてcondition全体を止めます。

外側へgridを追加しません。

### reference failure

fitが成立しない場合は、

`reference_scale_unavailable_under_frozen_protocol`

です。

別grid、別floor、exact-ground係数、D4、過去分子scaleによる救済は禁止です。

---

# A5. \(\epsilon,\beta,\) resource metric

これは継承してよいです。

\[
\boxed{
\epsilon_E
=
0.00015936001019904\ {\rm Ha}
}
\]

\[
\boxed{\beta=1.2}
\]

resource metric：

\[
\boxed{\texttt{continuous\_rotation\_cost\_proxy}}
\]

を維持します。

これらは分子固有のfit parameterではなく、現在のDirection Cそのものを定義するstudy-level contractだからです。

変更するとprospective validationではなく、resource model変更になります。

---

# A6. T0 / B0

prospective studyではB0を主成果にしません。

それでもbenchmark用に固定するなら、

\[
\boxed{
T_0=0.8t_{\rm ref}
}
\]

とし、

\[
\boxed{
B_0
=
B_{\gamma=1.10}(T_0)
}
\]

を**conservative benchmark anchor**として定義することを推奨します。

ただし、

- safeとは仮定しない
- fallbackには使わない
- truth後に安全性を採点する
- unsafeならB0-relative savingを主張しない

とします。

今回のprimary resultはB0比ではなく、

- safety
- required margin
- same-time oracle headroom
- native candidate oracle
- M1 comparison

です。

---

# A7. Fixed B1 gamma frontier

そのまま維持します。

\[
\boxed{
\gamma=
\{1.01,1.02,1.05,1.10\}
}
\]

各gammaについて独立に、

3候補の中で

\[
B_\gamma(t)
=
\gamma
\frac{\beta K}
{t(\epsilon_E-|\delta_C(t)|)}
\]

が定義される候補から最小budgetを選びます。

eligible candidateが0なら、

`B1_abstain_no_eligible_candidate`

です。

**B0への自動fallbackは行いません。**

truth後の最小safe gammaを新selectorへ転用しません。

現B2/H1は実行しません。

---

# A8. M1：全候補で取得する

ここはsubsetにしない方がよいです。

\[
\boxed{
\text{reference/time eligibleな全condition × 全3候補でM1}
}
\]

をprediction freeze前に取得します。

理由は、

- M1は今回の主要comparison package
- metadata-fixed subsetにすると、subset選択という新しい自由度が入る
- 3候補すべてあれば、point/width/abstention/headroomの関係を公平に比較できる

ためです。

### rank rule

既存rank-aware ruleを一般化します。

\[
m_{\rm primary}
=
\max\{m\in\{1,2,4,8\}:m\le d_{\rm sector}\}.
\]

prefix：

\[
\{1,2,4,8\}\cap[1,d_{\rm sector}].
\]

今回の想定conditionでは基本primary=8です。

actual Arnoldi breakdownにより8へ到達できない場合、lower prefixをaccepted primaryへ救済せずabstainします。

### M1 numerical contract

既存の一般的な数値gateを継承してよいです。

- complex128
- modified Gram-Schmidt 2 pass
- vector norm residual ≤ \(10^{-12}\)
- orthogonality Frobenius residual ≤ \(10^{-10}\)
- relative breakdown tol \(10^{-12}\)
- overlap ambiguity \(10^{-10}\)
- energy ambiguity \(10^{-10}\) Ha
- PF action norm residual ≤ \(10^{-10}\)
- U Ritz residual ≤0.05
- H Ritz residual ≤0.05 Ha

0.05はcertificateではなく、predeclared empirical feasibility gateのままです。

### width

\[
w_M
=
\max(w_{\rm local},w_{\rm prefix})
\]

を維持し、

`empirical_feasibility_width_not_certificate`

と明示します。

### M1 comparator

H1へadoptする仕組みは今回は作りません。

各conditionで独立に、

> `fixed M1 package`

として3候補からeligibleな最小予算を選びます。

全候補abstainならcondition-level M1 abstentionです。

---

# A9. Truth/scorer

全conditionのpredictionがfreezeされるまで、**一切の新truthを開かない**方針を承認します。

reference-ineligible等もsealed terminal statusとしてprediction manifestへ含めます。

全attempted conditionに、

- predicted
- input-ineligible
- reference-ineligible
- candidate-domain-ineligible
- M1-abstained

等の状態が固定された後、global truth barrierを開きます。

### same-H ground

同一、

- Hamiltonian
- scalar origin
- sector
- orbital ordering

のsector groundをprediction後だけ求めます。

### direct truth

ascending 3 candidate timesについて、

- full current_m3 PF
- complex Schur
- first time：same-H ground overlap最大
- later times：previous selected PF eigenvectorとのoverlap最大

を使います。

### numerical gates

H-chainで使用したgeneric numerical gatesをそのまま継承してよいです。

- ground norm error ≤ \(10^{-12}\)
- ground residual ≤ \(10^{-10}\) Ha
- ground ambiguity ≤ \(10^{-10}\) Ha
- PF unitarity Frobenius residual ≤ \(10^{-10}\)
- PF eigenpair residual ≤ \(10^{-10}\)
- Schur phase cluster separation ≤ \(10^{-8}\) radならunresolved
- ground/continuation overlap <0.9ならphysical branchをindeterminate

warningを無視して別branchへ救済しません。

### gap

target phase gapは全truth座標で記録します。

ただし用途は、

- branch resolution
- M1 branch diagnostic

だけです。

certificate用の\(g_{\rho,\mathrm{others}}\)や追加gap acquisitionは行いません。

### direct shift

\[
\delta_{\rm direct}
=
\frac{
\arg[e^{-iE_0t}\lambda_{\rm PF}]
}{t}
\]

のprincipal relative shift。

prediction値を使ったunwrap rescueは禁止です。

---

# A10. scoring

主要項目：

\[
e=|\delta_{\rm direct}|,
\qquad
c=|\delta_C|,
\qquad
u=e-c
\]

\[
M_\gamma
=
\left(1-\frac1\gamma\right)(\epsilon_E-c)
\]

\[
s_\gamma=M_\gamma-u
\]

\[
\gamma_{\rm req}
=
\frac{\epsilon_E-c}{\epsilon_E-e}
\]

を保存します。

ただし\(\gamma_{\rm req}\)はtruth diagnosticであってpredictorではありません。

また、

- same-time truth oracle headroom
- native 3-candidate oracle
- B1 selected budget
- M1 budget
- point error
- width
- abstention
- branch diagnostic

を分離します。

---

# B. Codex側で確定してよい技術項目

以下は研究方針を変えないため、Codex側で決めて構いません。

| 項目 | Codex裁量 |
|---|---|
| general-molecule truth-free wrapperのモジュール分割 | 可 |
| RHF/ROHF adapterの実装方法 | 可。ただしscientific state contractを変更しない |
| determinant enumeration/cache方式 | 可 |
| binary serialization/hash schema | 可 |
| condition workerのqueue方式 | 可 |
| CPU worker数 | 実allocation内でmemory-awareに決定可 |
| BLAS=1の実 enforcement/確認方法 | 可 |
| checkpoint形式 | 可 |
| coordinator-only Git操作 | 固定 |
| technical retry | 最大1回/phase/condition以内で可 |
| resource watchdog | 自worker treeのみ可 |
| cache reuse | hash-identical read-onlyの場合のみ可 |
| temp directory/layout | allocation/quota内で可 |
| focused unit/integration tests | 可 |
| failure logging/schema | 可 |
| non-force GitHub handoff | AGENTS.mdに従って可 |

Codexが勝手に変えてはいけないのは、

- molecule/geometry
- basis/active space
- state recipe
- reference grid/floor
- 3 candidate ratios
- gamma
- M1 rank rule
- width
- truth branch/scorer
- scientific retry
- missing condition replacement

です。

---

# C. 追加確認が必要な事項と最小範囲

全部を未確定に戻す必要はありません。残るのは3点です。

## C1. CH2 usage-history certification

必要なのは、**repository-tracked historyだけ**の追加監査です。

最低限：

- all reachable refs/commits
- tracked Markdown/JSON/CSV/source/manifests
- `CH2`, geometry identifiers, molecule registries
- executed scientific artifact references

をcontent-levelで検索する。

目的は、

> `repository_tracked_family_unseen`

を認定できるかだけです。

untracked/private/archiveまで不存在証明する必要はありません。

もしCH2既使用が判明した場合、

- HCNへ自動置換しない
- 別のnew familyを勝手に探索しない
- science実行前にGPT reviewへ戻る

とします。

---

## C2. 実allocation

本計算前に必要なのは以下だけです。

- usable CPU quota / affinity
- usable RAM quota
- job wall-time limit
- writable disk quota / approved output location

host全体の128 CPUsやavailable RAMをallocationとみなしません。

HCNをcore batchから外したため、GPU情報は今回不要です。

**初回prospective batchはCPU-onlyでよいです。**

---

## C3. implementation environment readiness

科学計算ではなく、実装testとして、

- NumPy
- SciPy
- PySCF
- OpenFermion
- BLAS backend
- BLAS threads=1

が実際にimport/runできることを確認する必要があります。

これはCodex側のimplementation readiness確認で十分です。

---

# D. 次にCodexへ渡す具体的な指示と停止点

次の工程は、以下まで許可してよいです。

\[
\boxed{
\textbf{protocol化}
+
\textbf{implementation/focused tests}
+
\textbf{bounded input/reference preparation}
}
\]

ただし順序を固定します。

### Phase P1 — protocol化

今回の科学仕様を正式protocolへ落とす。

対象は、

- 12 used-family conditions
- CH2 triplet 4条件はhistory certification成功時のみ
- HCN excluded/deferred

です。

ここでcondition setをfreezeします。

CH2 certificationが失敗したら、**P1で停止**。

### Phase P2 — implementation + tests

一般分子truth-free wrapperを実装します。

禁止：

- exact ground
- direct truth
- old truth-bearing `_prepare_system`
- candidate result inspection

focused testsでは、

- RHF/ROHF state recipe
- determinant CISD
- no-ground call graph
- H/group/K identity
- reference fit
- candidate arithmetic
- M1 rank rule
- truth barrier
- failure paths

を検証します。

ここまでscience actions 0でも構いません。

### Phase P3 — bounded input/reference preparation

P1/P2とallocation確認がすべてPASSした場合のみ許可します。

各final conditionについて、

1. SCF
2. Hamiltonian/group/K generation
3. determinant CISD state
4. input identity freeze
5. 34-point reference acquisition
6. \(t_{\rm ref}\) fit
7. 3 candidate times/float.hex generation
8. candidate plan freeze

まで。

このphaseでは、

- candidate cheap 3点：**まだ実行しない**
- M1：**0**
- exact ground：**0**
- direct PF truth：**0**
- gap：**0**
- scoring：**0**

です。

### P3の上限

final 16 conditionsなら最大：

\[
16\times34=544
\]

PF reference actions、

\[
544
\]

H exponential actionsです。

CH2が採用不可ならscienceへ入らず止めます。

---

# 停止status

P3完了時には、

\[
\boxed{
\texttt{prospective\_input\_reference\_preparation\_complete\_review\_required}
}
\]

で停止してください。

GPTが次に確認するのは、

- 何conditionsがinput eligibleだったか
- reference fit成功率
- \(t_{\rm ref}\)
- 3 candidate absolute times
- sector/K/CISD dimensions
- resource実測
- failure理由
- CH2 new-family certification

だけです。

**この結果を見てもgamma/rank/gridを調整しません。**

次の別承認で初めて、

\[
\text{candidate cheap}
\rightarrow
\text{M1 all-candidate}
\rightarrow
\text{global prediction freeze}
\]

を許可します。

そのさらに後にtruthです。

---

## 最終判断

今回のレビューで、科学仕様はかなり固定できます。

最も重要な変更は次の3点です。

\[
\boxed{
\text{20条件一括}
\rightarrow
\text{16条件・2 strata}
}
\]

\[
\boxed{
\{0.5,0.65,0.8\}t_{\rm ref}
\rightarrow
\{0.8,1.0,1.2\}t_{\rm ref}
}
\]

\[
\boxed{
\text{conditional M1}
\rightarrow
\text{全candidateのfixed M1 comparator}
}
\]

です。

これにより今回のprospective validationは、

> **既知データで作った説明が、事前固定した未知/new-condition条件でも成立するか**

を真正面から検証できます。

