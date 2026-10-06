基準commitは `533a52ca9eb20c5ab2281a9c4efbf37ff21fd838`。

Direction C、prospective core protocol、P3 input/reference freeze、candidate plan、cheap freeze、M1 freeze、global prediction freezeを変更しない。

今回許可するのは、13 `reference_candidate_plan_ready` conditions・最大39 frozen coordinatesについてのsame-H ground、direct PF truth、target phase-gap diagnostic、truth freeze、およびその後のimmutable scoringまで。

16 attempted conditions / 4 family unitsの分母を維持する。LiH_R1.40とLiH_R2.60は `candidate_time_domain_ineligible`、LiF_R2.60は `input_reference_ineligible` のterminal recordとして保持し、この3条件にはground/truthを実行しない。救済・置換しない。

### Pre-truth gate

truth実行前に以下を再照合する。

- HEADとauthorized source/protocol。
- `PREDICTION_FROZEN.json`。
- prediction SHA-256 `ac70d9d3fc02ce538f75678a5977be3aca507d2271a652487ae4b6d73bf3447d`。
- candidate plan、input identity、cheap/M1 manifests。
- 16 attempted / 13 ready / 39 coordinates。
- `truth_opened=false`。
- frozen gamma、rank、width、candidate times、state、PF、Kに変更がないこと。
- focused truth/scorer testsがfail/skip 0であること。
- fresh execution allocationが確認済みであること。

不一致があればtruthを1件も開かず停止する。

### Same-H ground

13 ready conditionsで各1回、最大13 solves。

同じHamiltonian、active space、scalar origin、orbital ordering、fixed alpha/beta population sectorを使用する。CH2は(5,3) fixed-population sector groundでありglobal molecular groundとは呼ばない。

ground norm residual <=1e-12、eigenpair residual <=1e-10 Ha、ground ambiguity <=1e-10 Ha。曖昧ならそのconditionをindeterminateとして停止し、state/solver contractを変更して救済しない。

ground solverの具体的実装はtruth開始前に固定する。既存same-H truth contractと同等のHermitian eigensolverを使用し、conditionごとの結果依存solver切替は行わない。

### Direct truth

P3で固定された39 coordinatesだけを対象にする。

各conditionについて0.8, 1.0, 1.2 t_refの昇順で逐次実行する。

- canonical current_m3。
- same frozen ordered groups/K/scalar origin。
- full PF materialization。
- complex Schur。
- first time: same-H ground overlap最大。
- later times: previous selected PF eigenvector overlap最大。
- shift=`arg(exp(-i*E0*t)*lambda_PF)/t`。
- predictorを利用したunwrap rescueは禁止。

unitarity Frobenius residual <=1e-10、eigenpair residual <=1e-10、phase cluster ambiguity <=1e-8 rad、ground/continuation overlap minimum 0.9を維持する。

branchがindeterminateになった場合、別anchor・個別eigenvector rescue・prediction matchingを行わない。continuationが定義不能なら後続座標もmissing/indeterminateとして記録する。

上限:
- exact ground solves <=13。
- full PF materializations <=39。
- direct Schur truth coordinates <=39。
- new candidate cheap actions=0。
- new M1 actions=0。
- new reference actions=0。
- new geometry/time/PF/rank=0。

target phase gapは同じSchur spectrumから計算するdiagnosticのみ。追加gap eigensolveやcertificate用gap acquisitionは0。

### Truth freeze

全conditionのtruth attempt/terminal statusをまとめ、truth result・source/input hashes・resource accountingをcommit/hash freezeする。

truth-validだけを抜き出して分母を作り替えない。attempted16、candidate-ready13、truth-attempted、truth-valid、scoredを別々の分母として保存する。

truth freeze成立前にscoringを開始しない。

### Immutable scoring

frozen predictionとfrozen truthだけを読む。

Cheap:
- e=abs(delta_direct)。
- c=abs(delta_C)。
- underestimation=e-c。
- M_gamma=(1-1/gamma)*(epsilon_E-c)。
- safety slack=M_gamma-(e-c)。
- frozen B1 gamma={1.01,1.02,1.05,1.10} selected decisionsの安全性を全て評価。
- B0も安全性を評価するがfallbackにはしない。
- gamma_reqはpositive allowance領域のtruth diagnosticのみ。

Oracle:
- same-time cost-free truth headroom。
- frozen 3-candidate native oracle。
- incomplete truthではcomplete oracleと呼ばない。
- oracleをoperational interventionと呼ばない。

M1:
- frozen package adoptionは39/39 abstainのまま変更しない。
- finite frozen delta_Mについて point error=abs(delta_M-delta_direct)を計算。
- empirical width coverageを計算。
- branch diagnosticを計算。
- cheap point errorとの比較を保存。
- CH2_R1.40_r1.2とCH2_R1.70_r1.0はpre-truth `h_ritz_residual` failureを保持し、raw diagnosticを出してもaccepted M1 performanceには数えない。
- truthを見てwidth/rank/adoptionを変更しない。

PF/H-reference decompositionはsame H、energy origin、sector、independent same-H E0、resolved physical branch/absolute targetが全て確認できる行だけで実施。不成立ならindeterminate。

3 candidate timesやfamily内geometryを独立sampleとして数えない。CH2は`repository_tracked_family_unseen` stratumとして保持する。

### Resource

truth開始前にfresh allocationを再確認する。既存prediction allocationの自動継承は禁止。

同等以上のquotaが得られる場合の上限:
- CPU <=16。
- BLAS=1/worker。
- total usable RAM <=128 GiB。
- worker RSS <=12 GiB。
- coordinator reserve 32 GiB。
- concurrent truth workers <=4。
- condition内3 coordinatesは逐次。
- direct truth <=1800 s/coordinate。
- condition truth phase <=7200 s。
- whole truth+scoring <=12 h。
- saved disk <=2 GiB、128 MiB stop reserve。
- scientific retry 0。
- technical retry最大1回。byte/hash-identical pre-action/checkpoint resumeのみ。

quotaが不足すれば、capや科学規則を変更せず停止してレビューへ戻る。

dense matrix/unitary/eigenvector/exact stateをGitへcommitしない。runtimeはprivate。公開するのはscalar result、hash、manifest、resource/action counts、tests、audit、handoff。

### Stop

truth acquisition、truth freeze、immutable scoring、focused post-tests、manifest/audit、commit/pushまで完了したら、

`prospective_truth_scoring_complete_review_required`

で停止する。

この後の新規分子、追加時刻、M1救済、rank/width変更、gamma変更、new gate、追加certificate計算は未承認。