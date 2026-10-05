# Condition-wise CPU resource proposal

Status: `unresolved_requires_review`; worker launch count 0。
allocationは `allocation_unverified`。128 visible CPUsやhost available RAMを実割当に置換しない。

## Workerとqueue

将来はindependent conditionごとにworker processを分け、各worker BLAS threads=1を第一案とする。
coordinatorのみGit index/commit/pushを扱う。workerは固有output directoryとimmutable input manifestを使う。
shared cacheはsealed/read-onlyとし、matrix/vectorの無制限なworker複製を避ける。
condition内のtruth 3座標は逐次処理し、前のU/Schur/eigenvectors/temporaryを解放してから次へ進む。

将来のprocess-local設定案は次であり、今回は共有shell/profile・環境へ設定していない。

```text
PYTHONNOUSERSITE=1
PYTHONDONTWRITEBYTECODE=1
OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

SciPyのBLAS/LAPACKには独立thread poolがあるため、process数だけではCPU利用を制御できない。
これは [SciPy公式documentation](https://docs.scipy.org/doc/scipy/tutorial/parallel_execution.html) の確認範囲であり、
今回installed SciPyのthread数は測っていない。threadpoolctlをインストール/起動せず、import確認も保留する。
実thread制限の確認方法は承認後のimplementation reviewに含める。multithread速度最適化benchmarkは今回0。

承認済みCPU budgetをC、threads/workerをtauとすると `P*tau <= C`。
coordinatorのCPU予約もC内に含める。tau=1でも独立内部poolが動けば有効tauを再確認する。
RAM budgetをM、worker予約をR_iとすると、
`sum(R_i for running workers) + R_coordinator + R_shared_cache + R_slack <= M`。
heterogeneous sectorsをdimension/予約量で並べたmemory-aware queueとし、固定process数だけに依存しない。
`R_coordinator=2 GiB`、`R_slack=max(2 GiB,0.10*M)` は未承認の例で、OS/node空きの利用許可を意味しない。

| Phase | Worker/thread案 | RAM/wall/I/O案と未確定事項 |
|---|---|---|
| input / integral / determinant CISD | condition worker、BLAS=1、P_input未定 | full H/CISD subspace、SCF/integrals/group workspaceを別予約。多condition同時SCFを承認前に起動しない |
| reference / cheap / M1 prediction | condition worker、BLAS=1、P_prediction未定 | CSR H、group component spectra、gate cache、vectors/Arnoldi prefixes、preprocessingを別予約。rank/grid上限未定 |
| prediction freeze | coordinatorのみ | 全condition record/hash/commit/byte gate。どのworkerも新truthへ進めない |
| same-H ground / dense direct truth | memory-aware condition queue、BLAS=1、P_truth未定 | 下記dense ledgerとinput/cache分を予約。conditionの3座標逐次。input/predictionと同じPに固定しない |
| truth freeze / immutable scoring | coordinator案 | scalarのみ、methods/gates承認後。今回scoring0 |

割当とphase上限が未確定なので、実worker数・phase wall・全体wall・cache bytes・batch disk・I/O帯域は全てnull。
現時点で1 workerの科学計算も開始しない。割当確認後もmethod/condition/protocol承認を別に要する。

## Dense storage算術

complex128 matrix 1枚は `D=16*d*d bytes`。以下の予約ledgerはupper-bound実証ではなくproposal。
full PF U、Schur T、Schur vectors、ground/eigenvector storage、H、solver workspace reserve、
temporary copy 3枚を別fieldで積算する（合計9D）。input/cache/CSR/component/native workspaceの追加案を4 GiBとする。
groundとdirect phaseの実際のlifetimeが重ならない部分も保守的に数える例で、変更には実装reviewが必要。
native solver workspace、molecule-dependent grouping、SCF/ERI、cacheの実量が4 GiB以内とは確認していない。

STO-3G basis shell headerからH=1、Li/Be/C/N/F=5 spatial AOsと推定し、
`d=C(n_active,n_alpha)*C(n_active,n_beta)` を計算した。MO linear dependenceやSCF未成立は未検証。
electron populationと凍結内殻案はcandidate CSVに記録する。sectorはfixed alpha/betaで、pure-spin adapted dimensionではない。

| 初期案 | sector d | complex128 1枚 GiB | 9枚 GiB | 9枚+4 GiB予約例 |
|---|---:|---:|---:|---:|
| LiH full (4e,6o), (2,2) | 225 | 0.000754 | 0.00679 | 約4.01 GiB |
| CH2 triplet alternative (8e,7o), (5,3) | 735 | 0.00805 | 0.0724 | 約4.07 GiB |
| BeH2 full / CH2 singlet | 1225 | 0.0224 | 0.201 | 約4.20 GiB |
| LiF CAS(8e,8o), (4,4) | 4900 | 0.358 | 3.220 | 約7.22 GiB |
| HCN CAS(10e,9o), (5,5) | 15876 | 3.756 | 33.80 | 約37.80 GiB |

exact bytesは [resource_planning_arithmetic.json](resource_planning_arithmetic.json)。
one matrix容量やGPU VRAMだけでtruth feasibleと判定しない。
HCNの大きさは事前basis/electron metadataで判明する資源上の問題であり、spectral/policy成績で選別したものではない。
HCN CAS案を承認後のresource failureで別basis/spaceへ縮小して救済しない。

`/home` の観測空き約5.39 GiBにはworker/cache/truthの大規模出力を無断予約できない。
`/tmp` のfilesystem空きも共有容量である。出力先/保存quota/cleanup担当/保存policyは要承認。
今回は軽量review資料だけを作成し、既存data/cache/archiveを移動・削除しない。

## 保存timings/RSSの限定

historical H8、sector4900、CPU1 process/BLAS1のnamed direct stageは約479 s/座標、peak RSSは2507060 KiB（約2.39 GiB）。
同sourceのinput/reference/shared preprocessing/M1/ground timingsも原fieldとscopeをJSONに残す。
timersは重複し得るので無差別加算しない。H8の約226.5 s preflight予測は約479 sの実測を過小評価した。
H8旧1800 s/4 GiB上限をnew batchへ自動継承しない。

仮に全件が同じhistorical 479 sなら、20条件×3座標は28740 stage seconds（約7.98時間）、
40条件×3座標は57480 stage seconds（約15.97時間）。
これはworker named-stage wall合計の算術であり、server/new molecule予測、CPU time、aggregate makespanではない。
input/reference/decision/M1/ground/preprocessingを含まないのでend-to-end時間でもない。
d^2/d^3 scalingで新分子wallを保証しない。Pで割った値を保証makespanとして提示しない。

## 会計・停止・再開案

aggregate makespan、sum worker wall、process CPU time、phase/stage wall、own-process RSS peak、
実測concurrent worker/coordinator RSSを別fieldで保持する。
個別RSS peakの和は予約算術であり、実測concurrent peakではない。
PF vector action、H exponential action、H matvec、input/preprocessing/cache、decisionをphase別に記録する。
内部expm matvecはunknownのままにし、H exponential 1回をH matvec 1回と数えない。
quantum K/budgetとCPU secondsを直接加算せず、net advantageは未確立。

own-worker watchdogは承認されたCPU/RAM/wall/disk limitsでのみ自分のworker treeを停止する案。
他ユーザーprocessへsignal/nice/affinity操作をしない。scheduler予約や申請を迂回しない。
resource stopは元condition/到達phaseを残し、欠測を置換しない。
technical retry最大1回/phase/conditionの案と、batch retry/action/wall総枠を結果前に承認する。
sealed protocol/source/environment/input/coordinate/checkpoint hashesを照合し、numerical failureへの規則変更retryはしない。
再取得分も作用数とCPU/wallに記録する。今回はjob、worker、watchdog、runnerを起動していない。
