# Track G truth-only continuation — results and audit

Status: `hchain_h6_geometry_sweep_truth_continuation_complete_review_required`.

新4 geometryの12 truthを一度だけ取得し、既存R=1.00 Å anchorの3 truthを加えた5 geometryを
immutable scorerで採点しました。科学source、既存prediction、ground、budget、width、gateは変更していません。
Direction Cや中心claimをCodexで変更する作業はしていません。

## 実行順序とimport修正

`61ae95ed...`のpredictionおよび`1e5d66a4...`のgroundのcommit blob・hashを確認し、
元recovery worktreeのinput/ground `.npz` 8件をbyte/hash照合してそのまま参照しました。
コピー・再生成・新ground solveは行っていません。新worktreeでは対象`__pycache__`は存在せず、
旧worktreeのcacheやfrozen artifactも変更していません。

Pythonはbytecodeを書かない設定でもcacheの読込を試みるため、cache削除だけに依存せず、
sealed `.py`をSHA-256確認して直接compileするsource-only loaderを導入しました。
`hchain_truth_scoring.py`のhashは
`a0ac9b1285e6d1369ab2007599fe33ca69851b9d7627359697a93ea8e119eb37`で固定されています。
`.pyc`はallowlistに追加せず、科学worker/solver/scorerの既存bodyは変更していません。

science前に、実際のtruth moduleをrepository access guard下でimportするtest、poisoned cacheを
無視するtest、hash不一致で停止するtest、synthetic 3時刻のworker/Schur/serialization経路を含む
focused tests **100 passed**を確認しました。science後も同じfocused testsが**100 passed**。
両方ともfail/error/skip 0、truth-bearing legacy testsは未実行です。

4 geometryを独立4 workerで実行し、各geometry内では`0.5 → 0.65 → 0.8*t_ref`の順に
最初はexact-ground overlap、その後はprevious-branch overlapでcontinuationしました。
4 workerともcomplete、access denial・`.pyc` read/writeとも0です。
truth freeze後に既存`run_hchain_supplement.analyze_G`を一度だけ適用しました。

## Budget safety

`c=|delta_C|`、`e=|delta_direct|`、`epsilon_E=0.00015936001019904 Ha`、`beta=1.2`、`K=14344`。
continuous frozen budgetのまま、`e + beta*K/(t*B_frozen) <= epsilon_E`を採点しています。

`M_gamma=(1-1/gamma)(epsilon_E-c)`、safety slack=`M_gamma-(e-c)`、
`gamma_req=(epsilon_E-c)/(epsilon_E-e)`です。gamma=1では比率を使わずadditive slackを使います。
gamma_req<1の値はclipしない診断値で、gamma変更の提案ではありません。

下表は全geometryで選択された`0.8*t_ref`の値です。R=1.00は保存値reuse。

| R (Å) | B1(1.01)/B0 | gamma_req | slack at 1.01 (Ha) | E_M/E_C | Cost-free oracle headroom at same time |
|---:|---:|---:|---:|---:|---:|
| 0.80 | 0.668977 | 0.992933 | 2.50277e-6 | 0.5442 | 1.690% |
| 1.00 (reuse) | 0.670347 | 0.987115 | 3.36823e-6 | 0.4871 | 2.266% |
| 1.20 | 0.673510 | 0.982835 | 3.99545e-6 | 0.8279 | 2.690% |
| 1.40 | 0.677139 | 0.987789 | 3.23194e-6 | 2.2176 | 2.199% |
| 1.60 | 0.677642 | 1.000929 | 1.30163e-6 | 55.8295 | 0.898% |

B0は各geometryの`0.5*t_ref`、gamma=1.01のbenchmarkで、安全とは事前に仮定していません。
truthによってB0は5/5、B1のgamma=1.01/1.02/1.05/1.10は各5/5でsafeと判定されました。
gamma=1.01については選択点だけでなく全15 coordinateがsafeです。

gamma=1のpost-hoc診断budgetは12/15でsafe、R=1.60の3 coordinateだけunsafeでした。
R=1.60では全3点で`e-c>0`、gamma_reqは最大1.002179で、固定1.01のmargin内に収まります。
他4 geometryでは全coordinateで`e-c<0`でした。

32.24–33.10%のB0比削減は、安全性を確認したnative 3候補内のbudget比較です。
固定された`0.5/0.8`時刻比そのものが構造的な削減余地を持つので、すべてを情報取得の寄与や
新policyの発見と帰属させません。oracle headroomはtruthを無料で知る仮想値であり、
実行可能なM1の節減量や古典費用を含むnet benefitではありません。

## M1 point / width / resource diagnostics

同じrank8の元predictionを診断し、abstentionを採用へ変更していません。

- R≤1.20の9 coordinateでは`E_M<E_C`、R≥1.40の6 coordinateでは`E_M>E_C`。
- `E_M`は3.02725e-8–7.51664e-6 Ha、empirical widthは1.31177e-3–1.00705e-2 Ha。
- empirical widthは15/15でpoint errorをcoverしますが、全15 coordinateで
  `no_positive_qpe_allowance`のabstentionが維持されています。
- same-time cheap gamma=1.01 budgetに対するM1 width windowは10/15でpositive。
  それらでも元widthはwindowを大幅に超過します。残る5点ではwindow自体がnonpositiveです。
- M1 operational selector/H1を新しく実行せず、hypothetical budget欄はformal resultの救済に使いません。

この限定されたsweepでは、point accuracyの改善が全geometryに一様ではないことと、
width coverageだけではusable resource decisionを保証しないことが観測されています。
一般分子・他rank・他候補時刻への外挿はしていません。

## Branch / numerical quality / error decomposition

新12 truthはすべてresolved。最大unitarity Frobenius residualは3.24760e-12、
最大eigenpair 2-norm residualは9.46468e-15、最小target phase gapは0.0349906 rad、
最小ground overlap probabilityは0.9999999861です。既存numerical gatesを変更していません。

anchorを含むM1 physical branch一致は15/15。unwrap integerの一致ではなく、
signed shift errorとphase gap/timeのcriterionを使っています。

same-H/sector/input hash、共通energy origin、physical branchが確認できた15点だけで、
`delta_M-delta_direct = PF_side_error-H_reference_error`を分解しました。
最大closure residualは3.15994e-16 Ha。大きなRでPF-sideとH-referenceの両誤差が増え、
その差にM1 point errorが現れます。差が小さいことを両側の絶対誤差が小さい証拠とはしません。

## Action accountingと過去の失敗の保持

| Stage | H / CISD generations | Reference PF / H-exp | Cheap PF / H-exp | M1 PF / H-matvec | Ground solves | Full PF / Schur / direct truth / gap |
|---|---:|---:|---:|---:|---:|---:|
| Original failed Track G | 4 / 4 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 / 0 / 0 |
| Prior approved recovery | 4 / 4 | 136 / 136 | 12 / 12 | 96 / 96 | 4 | 0 / 0 / 0 / 0 |
| This truth-only continuation | **0 / 0** | **0 / 0** | **0 / 0** | **0 / 0** | **0** | **12 / 12 / 12 / 12** |

H/CISD generation attemptsは履歴全体で8/8ですが、新規unique geometryは4、
anchor込みのdenominatorは5です。元のfailed recordとrecovery failed statusを消していません。
今回のtechnical/scientific retryはともに0で、one-continuation上限は消費済みです。

truth preprocessingにgroup spectra 228、connected-component eigh batches 524、
component gate materializations 2736、sparse-matrix × dense-matrix multiplies 9420も行いました。
これらを「計算0」に隠していません。前段に限定したH/reference/cheap/M1/ground取得が0です。

凍結済みground vectorはtruth workerで4件読んでいます。legacy ledgerの`truth_array_reads=0`は
未計測counterであり、ground vector未読の証拠ではありません。`PySCF_threads=4`も4 workerの
各1というmetadataの和であり、1 workerが4 thread使った意味ではありません。

4 worker、BLAS/PySCF各1。truth stage wallは3.58418 s、最大worker peak RSSは442260 KiB。
0.2秒samplingのcoordinator＋own workers合計peak RSSは2,065,104,896 bytes（約1.923 GiB）。
同時RSSであり、個々のpeakの単純和ではありません。own worker swapは0。
named run wall 6.83207 sはreadinessからscoring/post-testsまでで、CLI import・最終freeze・図作成を
含むend-to-end時間ではありません。GPU query/allocation/kernel、CuPy import、共有環境変更、
他job操作は行っていません。

## Figures / captions

1. **geometry_safety**：3 native ratiosについて、Rに対するunclipped gamma_reqと1.01 slack。
   gamma_req図の点線は1、破線は1.01。R=1.60ではgamma=1のboundaryを超えますが1.01未満です。
2. **M1_point_width**：cheap point error、M1 point error、元empirical widthを別panelで表示。
   log軸はpanelごとに異なります。point改善・幅coverage・resource usabilityを区別します。
3. **PF_H_reference_decomposition**：branch確認済みのsigned PF-side/H-reference誤差とM1 point error。
   元scorerのscalarを可視化しただけで、別Hamiltonianのgroundや追加gapは使用していません。

全図の黒い中抜きsquareはR=1.00の保存anchorです。線は点を結ぶ表示であり、
未取得geometry/timeのtruth補間ではありません。旧scorer rendererの[mechanism.png](tables_figures/mechanism.png)も
absolute timeを横軸とした参考図として保存しました。

## Provenance / review stop

新stage21/21 blob、upstream28/28 blob、source115件、旧recovery source109件、runtime8件の
byte/hash gateがPASS。base commitの既存tracked fileの変更は0です。
origin/result commitとverified snapshotは[source_registry.json](source_registry.json)で別fieldに記録し、
publication manifestは自己除外を明示します。runtime/arrayは公開対象外です。

GPTへの確認事項は、①この限定sweepのcheap-sufficient evidenceとsmall-gamma boundaryの位置付け、
②geometry依存のM1 point/widthおよびPF/H-reference cancellationをDirection Cのclaimへどう統合するか、
③上記の独立sample・certificate・net benefitを主張しない限定で十分か、です。
Codexから新scienceやpolicy変更を提案・実行せず、commit/push後にレビュー待ちで停止します。
