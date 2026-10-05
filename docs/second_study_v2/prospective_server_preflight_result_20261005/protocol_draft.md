# Prospective budget-safety protocol draft

Status: `unresolved_requires_review`; governance/protocol proposal only.
今回の停止点は `prospective_budget_safety_preflight_complete_review_required`。
この文書はnumerical runnerでも新しい科学規則の承認でもない。

## 継承する承認済み範囲

Direction Cと [承認済みRQ・claim scope](../result_synthesis_20261005/approved_scope_and_rq.md) を維持する。
Fixed B1 gamma frontierを主要対照、現B2/H1をhistorical diagnostic、M1をrank/reference/empirical width/adoptionの組、
truth oracleをcost-free headroomとして扱う。B2/H1を主運用方式に復活させない。
q=1探索、新PF、H-chain追加、gate/gamma/threshold/rank/width調整、結果後の救済を行わない。
primary候補は `continuous_rotation_cost_proxy`。整数QPE queryや別resource modelへ変更しない。

保存契約は [quantity dictionary](../budget_safety_mechanism_20261005/quantity_dictionary_and_analysis_spec.md) に従う。
signed shiftとabsolute PF error、同時刻budget比較と候補時刻選択、oracleと実M1を区別する。
slackはbudget式の同値変形であり、未知系のpredictive certificateではない。
net/end-to-end advantage、state/rankの因果説明、汎用safe policyは未確立のままにする。

## 実行前に必要な10項目の研究判断

| ID | 未確定contract | 根拠付きproposalと承認条件 |
|---|---|---|
| U01 | 最終condition、strata、basis/active/frozen core、charge/spin、state recipe | CSVの20件は候補案のみ。LiH/LiF/BeH2は既使用family。CH2/HCNは未使用認定なし。geometry、構造、electron population、sector sizeで事前strataを作り、history certification後に固定。20〜40条件/各3候補は構想であり今回採用0 |
| U02 | current_m3 group/coefficient/energy origin/sectorとK | canonical coefficient hexと7-step symmetric S2 sequenceを既存PF contractから継承する案。ordered groups、Pauli term/coefficient hash、scalar removal、MO/sector/state order/hashを条件ごとにfreeze。Kはmerged PF stepのnonidentity Pauli rotations。group指数作用数やclassical matvec数と置換しない。分子別Kは未取得 |
| U03 | 一般分子truth-free reference、t_ref、grid上限、fit failure | 一般分子ruleは未確定。HF native metadataとH-chainの34点grid/leading_fit/t_refは異なる。H-chain gridやpower/rangeを無断コピーしない。observable/state、rule、取得回数、fit条件を結果前に承認し、不成立はreference-ineligibleとして止める |
| U04 | 各conditionの3候補、T0/B0、beta/epsilon単位・値、fallback | 時刻ruleとcandidate IDsを先にprotocol化し、承認済みreference後にabsolute binary64 timeとfloat.hexをfreeze。Hartree/Hartree inverse、beta dimensionless、K rotation count、B continuous cost。保存specのbeta=1.2、epsilon=0.00015936001019904 Hartreeを新条件へ継承する案は要承認。T0/B0/比率/thresholdは未確定。reference不成立を別ruleで救済しない |
| U05 | Fixed B1 gamma=1.01,1.02,1.05,1.10のbudget/selection/領域 | 全固定armsを保持する案。positive finite t,Kとc<epsilonのみ式を適用。arm内selector/eligible set/tie/fallbackをtruth前固定。truth後の最小safe gammaを運用方式にしない。gamma=1はarithmetic diagnosticでmargin比を作らない |
| U06 | M1範囲、rank、reference、width、abstention/adoption | 最終20件を採用した場合は全3候補=60 coordinatesをtruth前に取得する第一案。別案は事前metadataだけで固定したsubset。範囲は要承認。m=8を一般分子へ暗黙適用しない。dimension/rank-aware規則、actual prefix、breakdown、empirical width、eligibility/adoption/fallbackを結果前に固定 |
| U07 | same-H ground、physical branch/alias、direct scorer、gap、continuation/gates | H/energy origin/sector/coordinate/state linkageを一致させる。branchが認定不能ならindeterminate。ground solver/direct Schur/continuationを含む手法・numerical gatesは要承認。target gap取得の可否/範囲は別承認で、certificate用の追加gapはしない |
| U08 | phase別CPU/thread/RAM/wall/I/O・全体上限・watchdog | condition process、worker BLAS=1、memory-aware queue、truth座標逐次を提案。実CPU/RAM割当はunverified。phase worker数、wall上限、output quotaを固定できない。own-process/own-worker descendantsだけのwatchdogを設計し、他ユーザーprocessに介入しない |
| U09 | technical retry・checkpoint hash・失敗区分 | unchanged sealed input/source/env/protocol hashでtechnical retry最大1回/phase/conditionを提案、batch retry上限は要承認。科学的/numerical failureへの規則変更retryは0。再実行分の作用・CPU/wallを隠さず合算し、同一hash失敗を技術的と自動解釈しない |
| U10 | 適用不能/abstention/branch不定/resource stop/欠測と分母 | frozen / attempted / reference-eligible / predicted / truth-valid / scoredを別分母にする。欠測は理由/到達phase/source hashを保存し、条件を事後除外・置換しない。3時刻は条件内の依存観測、family内geometryも独立sampleとしない |

10項目すべて `unresolved_requires_review`。上表のproposalは承認済み科学規則と区別する。
20件案に加えたCH2 triplet 4件は、独立したopen-shell stratumの代替案であり自動追加しない。
geometry由来の伸長/correlation design intentを実測済みweak/strong correlationとして扱わない。
時間・allocationに収まらないと判明した後にbasis/active spaceを変更して同じ実験を救済せず、別レビューへ戻す。

## Implementation seal案

一般分子inputはRHF/CAS integral抽出と同一sectorのdeterminant CISDを分離する案。
PySCF upstreamのRCISD/UCISDと既存determinant-CISDは同一実装であると仮定しない。
legacy `_prepare_system` はground solveを含むのでprediction前に呼び出さない。
H8 inputのground分離は参考になるが、固定H8 geometry/populationのsourceを一般分子へ無断変更しない。

seal対象はinput schema/単位、MO identity/active indices、orbital/spin order、sector indices、
H/groups/scalar origin、state generator/subspace/phase convention、canonical coefficients/merged steps/K、
reference/selector/M1/width/abstention/fallback、library metadata、source hashes、resource/retry規則。
inputからexact-ground/旧truthへ到達するimport/call経路も監査する。

将来のfocused truth-free testsはsynthetic/schema/seal/barrier/budget算術/失敗経路を対象にし、
実分子SCF/actionやtruth payloadを読むtestと分ける。
既存full/legacy suiteはtruth読取・private runtime/path/optional dependency failureを持つため、
prediction前に無差別実行しない。H8の元full-suite caveatは隠さない。
今回はfocused testsの実装/実行もしておらず、資料形式の検証だけを行う。

## 承認後のfreezeとtruth barrier案

1. 最終対象・全科学規則・資源枠の承認とprotocol commit。
2. 別承認されたimplementation seal、truth-free tests。
3. input identity、承認済みreference、exact candidate coordinates/float.hexのfreeze。
4. cheap取得とfixed B1 decision。
5. 事前固定した全候補またはsubsetのM1取得・decision。abstention/fallbackも保存。
6. 全対象conditionのpredictionをcoordinatorがcommitし、hash/byte gateを全件確認。
7. gate後にだけsame-H groundとdirect truth。どのworkerもgate前に新truthを開かない。
8. truth freeze、immutable scoring、GitHub handoff、GPT review stop。

subset外M1はtruth後に有望条件だけ取得しない。selective q経路を含めるなら別承認が必要で、
q freeze前にM1を読むことはできない。現案はq selectionを実装しない。
global prediction barrierはcondition単位の先行truthを許さない。
prediction完了条件、未完了/abstentionのsealed record、fail-closed barrierをprotocolで固定する。
freeze未成立ならそのbatchのtruthを開始しない。

## 将来のimmutable scoring定義案

同一時刻の `e=abs(delta_direct)`, `c=abs(delta_cheap)`, `u=e-c` を用いる。
`B_gamma=gamma*beta*K/[t*(epsilon-c)]` が定義される領域で、
`M_gamma=(1-1/gamma)*(epsilon-c)`、`slack=M_gamma-u`。
gamma=1にもslackを使い、zero marginで割らない。
`gamma_req=(epsilon-c)/(epsilon-e)` は両allowanceが正の領域だけのtruth diagnostic。
e>=epsilon、nonfinite/missing、invalid branchにはinfeasible/indeterminateの理由を残す。

最終safetyは `e + beta*K/(t*B_frozen) <= epsilon`。
branch未認定をsafeにしない。数値gate toleranceをsafe化の救済に使用しない。
truthでselector、prediction、budget、widthを変更しない。
same-time比較と元3候補内のtime-selection/oracle比較を別fieldにする。
native baselineのB0を新しく再評価したfixed-B1に無断置換しない。

M1 point accuracy、empirical coverage、rank/eligibility、width budget denominator、abstention/adoptionを分ける。
PF/H-reference分解は同一H、energy origin、sector、独立same-H E0、physical branch/absolute targetの照合が成立する場合だけ。
不成立ならindeterminateで、旧truth_target_on_h_referenceを同一identityの代わりにしない。
quantum budgetとCPU secondsを足さず、保存stage会計からnet advantageを認定しない。

今回このscoringを実行していない。contract未確定のままinput/reference/prediction/truthを開始せず停止する。
