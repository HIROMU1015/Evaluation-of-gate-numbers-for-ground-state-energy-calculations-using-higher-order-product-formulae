# 第2研究v2 HF domain-intervention protocolization report

**Status:** `second_study_v2_hf_domain_protocol_complete_review_required`

## Outcome

HF 2条件に対するbudget-targeted domain-intervention pilotを、科学計算前のdesignとして固定した。P0ではGit-tracked sourceの読取、hash/provenance照合、保存scalarのcandidate-plan算術だけを行い、PF/H action、Arnoldi、truth生成、gap、GPU、selector/threshold fitは0である。

pilotの実行は未承認である。

## Fixed baseline and grid

| condition | T0 | B0 (`B_frozen`) | t_ana | K | cap |
|---|---:|---:|---:|---:|---|
| HF eq | 0.148871685974198 | 468461625.7375308 | 0.297743371948396 | 9108 | active at 0.5 t_ana |
| HF stretch150 | 0.20600464713499966 | 338265614.44010574 | 0.4120092942699993 | 9108 | active at 0.5 t_ana |

candidateは各条件`T0,1.3T0,1.6T0`、すなわちsource確認済みの`0.5,0.65,0.8 t_ana`である。decimalと`float.hex`はcandidate planへ固定した。

`B0`は第一研究metric dictionaryの`B_frozen=1.01*C_hat`であり、`C_hat`そのものではない。

提案`eta=0.10`では、T0は両条件とも`A_eta<0`のため10% intervention候補として構造的に不適格だが、control/fallbackとして保持する。cap外4候補は正のallowanceを持つ。これは保存scalarを用いたprotocol arithmeticであり、推定器やtruthの評価ではない。

## Truth availability

- T0 exact-time truth: S0 v1.1に2/2存在し、将来scorerで再利用可能。
- `1.3T0`, `1.6T0`: exact coordinateはtracked artifact内に0/4。将来取得するなら新truth 4件であり、別承認が必要。
- nearest saved grid、補間、別時刻への置換は禁止。

## Arms and comparison

- `B0`: inherited first-study baseline。
- `B1`: local CISD proxy gamma 1.01/1.02/1.05/1.10を独立armとしてfreeze。
- `M1`: D2-A explicit-vector unitary Arnoldi m<=8と同一のempirical width。

M1がpoint estimateで優れても、safe local arm/Pareto frontierをresourceとinformation costで上回らなければ追加価値とはしない。

## Branch and freeze boundary

D2-A scoring auditを反映し、absolute PF energy windingとground-removed shift windingの直接一致を禁止した。共通physical energy gauge/liftでbranchを採点する。

predictorがcandidate eligibility、selected time、budget、branch、abstention、resource countsをcommit/hash固定した後だけscorerがtruthを開く。scorerはpredictionの変更・救済・座標追加を行わない。

## Related-work boundary

6件を`core_related_work`、`method_source`、`peripheral`へ分類した。Arnoldi/Krylov、新PF、BCH estimatorを本研究の新規手法として主張しない。

HF pilotへ新しいexternal baselineは追加しない。signalがあり、cheap proxyが再現できず、比較がArnoldi固有効果を識別できる場合だけ別承認で最大1方式を検討する。

## Blocking items before execution

1. `eta=0.10`の人間承認。
2. continuous proxyしか存在しないbudgetについて、continuous-only評価か離散化規則かを承認すること。
3. wall-time limit。
4. HF 2 cache本体の実行環境上のpathとbyte identity。
5. cap外4 direct truthの別承認。
6. adapter、selector、freeze artifact、representation-independent scorer、testsの実装とreview。

これらが解消されてもP1は自動承認されない。implementation bundleとexecution authorizationを別途固定する。

## Stop

`pilot_execution_authorized=false`を維持して停止する。P1、C1、D2-B、LiF、holdout、新PF、外部baseline実装へ進まない。
