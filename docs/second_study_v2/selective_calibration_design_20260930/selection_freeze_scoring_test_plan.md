# Selection, freeze, scoring test plan

本書は将来実装のtest計画であり、今回runnerや科学計算を実行するものではない。

## 1. Source and tuple identity tests

- allowlist外fileをpredictorへ渡すとfailする。
- Hamiltonian、state、PF、absolute time、budget constantsのいずれかが違えばmatched tupleとして拒否する。
- runtime/untracked cacheを暗黙に探索しない。
- manifestのbytes/SHA-256不一致で停止する。

## 2. Information-boundary tests

- acquisition freeze前にtruth fieldを読むとfailする。
- acquisition freeze前にM1 prefix/width/Ritz/branchを読むとfailする。
- condition名やequilibrium/stretch labelをroute特徴に使うとfailする。
- exact overlapなどoracle fieldを`I_C`へ入れるとfailする。
- allowed cheap fieldだけでB2とH1 acquisitionが再現できる。

## 3. B2/H1 fairness tests

- B2とH1のcheap feature schemaがbyte-identicalである。
- B2とH1のcheap policy hashが同一である。
- H1だけgamma、threshold、fallbackを変更できない。
- B2が未確立の場合、B1-based H1 comparisonにconfounding flagが必須である。

## 4. Acquisition/final-action separation tests

- `spectral_requested`と`spectral_result_used`が独立fieldである。
- queryしたが不採用、query失敗、cheap invalidation、fallbackを別々に表現できる。
- M1がcheap候補を不適格とした後、安いcheap budgetを保持するとfailする。
- 別時刻のM1結果で未評価cheap時刻を救済するとfailする。
- branch/reference indeterminateは事前固定fallbackまたはabstainになる。

## 5. Freeze-order tests

期待順序：

1. source/environment/tuple gate。
2. cheap feature materialization。
3. B2 decision freeze。
4. H1 acquisition decision freeze。
5. 選択M1取得。
6. H1 final-action freeze。
7. prediction artifact commit/hash freeze。
8. truth open。
9. scorer。

HEAD、prediction file set、blob identityがfreeze commitと異なればtruthを開かない。

## 6. Resource-accounting tests

- q=0でもcheap/decision費用を計上する。
- q=1ならM1失敗・不採用でもquery費用を計上する。
- PF action、H matvec、H exponentialを別counterにする。
- unmeasured zeroをactual zeroとして集約しない。
- reuse creditには一致したcache identityと実測reuse logを要求する。
- no-reuse timing scenarioをmeasured H1 runtimeとして出力できない。

## 7. Scoring tests

- safetyはfrozen budgetとdirect absolute PF errorだけで採点する。
- signed mechanism errorとabsolute budget errorを分離する。
- unsafeを低budgetの勝利に数えない。
- coverage/fallback/abstentionが異なる比較では差を明示する。
- global、per-family、per-condition集約を保存する。
- oracle gamma/C-S selectionをoperational resultへ混入させない。
- eta=10%のB0 domain targetとB2/M1/H1 incremental effectを別fieldにする。

## 8. Synthetic and replay tests

科学計算前には、synthetic recordsで次を検査する。

- no-query、query-and-use、query-but-retain-valid-cheap、query-invalidates-cheap、query-failure、abstain。
- safe/unsafe境界、coverage差、同率cost、Pareto dominance。
- manifest self-exclusionと明示stage file set。

既存HF/HCl replayはschemaとboundary確認に限り、new policyの独立性能評価とは呼ばない。

## 9. Pre-execution unresolved test constants

- noninferiority margin。
- classical budget ceiling。
- minimum practical effect size。
- query budget。
- failure-priority order。
- fold boundaryとthreshold candidate count。

これらがreviewされるまでexecution testを正式gateにしない。
