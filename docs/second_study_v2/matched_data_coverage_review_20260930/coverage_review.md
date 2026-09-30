# 第2研究v2 matched-data coverage review

Status: `second_study_v2_matched_data_coverage_review_complete_external_review_required`

## 1. 目的と境界

固定済みselective-calibration designを受け、既存tracked artifactだけから、cheap・M1 spectral・truth・resource costが同一PF、Hamiltonian、state、time coordinateでどこまで対応するかを監査した。本監査はread-onlyであり、新しいPF/H action、truth、Hamiltonian/state、gap、policy fit、threshold fitを生成していない。

今回決めるのは「既存データだけで次の限定prevalidationが可能か」と「追加取得の前に何をレビューすべきか」である。B2/H1の数値rule、query threshold、noninferiority margin、classical cost ceiling、minimum effect sizeは決めない。

## 2. 判定

- 既存データは、schema、情報遮断、freeze順序、resource-ledger結合を検証する`no-fit replay`には十分である。
- 既存データだけでB2/H1のpolicyをfit・選択し、科学的な優劣を主張するには不十分である。
- 不足M1はLiF 4座標、N2/CO 12座標の合計16座標である。ただし16点すべてを自動的に取得する結論ではない。
- 追加取得範囲を決める前に、development family、fold、候補時刻contractをレビューで固定する必要がある。

## 3. 完全に揃うtuple

### HF: 2条件、6座標

`T0, 1.3*T0, 1.6*T0`で、frozen cheap、frozen M1、post-freeze exact truth、cheap/M1のcoordinate別costが揃う。Hamiltonian SHA-256とsource pickle SHA-256も固定される。

ただしHFはpilotのmotivation/sanity-check dataであり、既知のroute outcomeをB2/H1 policy labelとして使用しない。combined H1のshared/reuse込み実測costはない。

### HCl: 2条件、6座標

`0.5, 0.65, 0.8*t_ana`で、same-H/state/timeのcheap、frozen M1、truth、coordinate別costが揃う。D2-Aの整数branch比較は座標系不一致だったが、別のread-only scoring auditでrepresentation-invariant physical branchは6/6と確認済みである。元のformal statusは変更されていない。

HClはHFとcandidate contractが異なる。cheap値の一部はPhase A freeze、一部はR1 post-hoc取得であり、HFと無条件にpoolしてpolicyをfitしない。combined H1 costも未測定である。

したがって、strictly materializedなcheap/M1/truth coordinate tupleは合計12であるが、同一development contractの12 training examplesという意味ではない。

## 4. 部分tuple

### LiF: 2条件、4座標

prior-selected coordinatesでcheap値、truth、Hamiltonian SHA-256、CISD-state SHA-256、cheap costはある。M1 prediction、M1 cost、combined H1 costがない。従ってM1追加取得なしにはB2/H1の直接比較へ使用できない。

### N2/CO: 4条件、12座標

first-study selected timeの`0.99, 1.00, 1.01` tripletにexact truthが存在する。center cheap optimumはmaterializedされ、非center cheap値はtruth-freeにfreezeされたmodel係数から決定論的にreplay可能だが、coordinate-level artifactとしては未materializedである。Hamiltonian SHA-256とsource-pickle SHA-256は保存される。

M1、M1 cost、combined H1 costは存在しない。cheap costもcoordinate別ではなくselector-level aggregateである。従って、これは完全tupleではなく`partial_replayable_tuple`である。

## 5. Resource accounting gap

HF/HClにはcheap armとM1 armの個別costがあるが、

`C_total_cal = C_shared + C_cheap + q*C_spectral_given_cheap + C_decision`

のうち、同一processでcheap後にM1を取得した場合のshared/reuse込みincremental costは測定されていない。単純和はno-reuse scenarioであり、observed H1 costではない。CPU wall、PF actions、H matvec/exponential action、materialization、memoryを単一scalarへ暗黙に合算しない。

## 6. 既存データで許される次作業

既存HF/HClの12座標を用いたS1A `existing_matched_tuple_replay`だけは、次の範囲で実行可能である。

1. input schemaとidentity gateの確認。
2. cheap/acquisition/final-decision freeze artifactの空または固定rule replay。
3. truthがfreeze前に読まれないことのtest。
4. arm別resource ledgerのjoinとunknown fieldの保持。
5. HClのinteger branchを直接比較せず、physical shift/gap auditを別fieldにする確認。

このreplayでpolicy fitting、threshold search、best-rule selection、一般化性能、量子予算改善を主張してはならない。

## 7. 追加取得をまだ承認しない理由

M1欠落16座標は明確になったが、familyごとにcandidate contractが異なる。全点取得しても、development foldと比較contractが未固定ならpolicy選択の自由度だけが増える。先に外部レビューで次を決める必要がある。

- HF/HClをno-fit replay以外に使うか。
- LiFの2座標contractとN2/COのtriplet contractを維持するか、共通contractを別途設計するか。
- conditionを独立単位とするfoldとfamily-level separation。
- 追加M1の最大condition/coordinate/action budget。
- shared/reuse costを再実行で測る必要があるか、conservative no-reuse boundで扱うか。

## 8. 次の停止点

本監査で停止し、外部の研究方針レビューへ戻る。レビュー通過前はS1A実装、S1B policy development、M1追加取得、truth生成、holdout、新PFを許可しない。
