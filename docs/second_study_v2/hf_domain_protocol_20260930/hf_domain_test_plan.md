# HF domain pilot test plan

この文書はP1実装時のtest仕様であり、P0では科学testを実行しない。

## Source and access

1. fixed source hashes and exact condition set
2. H/PF/CISD/cache identity一致
3. sanitizer出力にforbidden field/pathがない
4. predictor processからtruth artifactへアクセスできない
5. truthアクセスはprediction commit/hash後のみ
6. scorerがprediction blobを変更できない

## Coordinate and candidate rule

1. 6座標のdecimalと`float.hex`一致
2. nearest snap/interpolation拒否
3. `T0=0.5*t_ana`のsource identity
4. `A_eta<=0`の構造的棄却
5. 一方の外部候補failureが他方を棄却しない
6. 非単調errorを仮定しないsynthetic ordering test
7. eligibleとselectedのfield分離
8. 最小budget、exact tieで短い時刻、eligibleなしfallback
9. fallback/T0をdomain-intervention successへ数えない

## Budget identities

1. `B0=1.01*C_hat`
2. `B_target=(1-eta)B0`
3. allowance/cost algebra identity
4. `e_use==A_eta`はeligible、`e_use>A_eta`はnot eligible
5. `e_use>=epsilon_E`はabstain
6. truth safetyの`<=`境界
7. continuous/discrete field分離
8. unresolved discretizationのままP1 authorizationを拒否
9. zero-PF-errorでも`A_eta<=0`をreject

## Estimator integrity

1. one chain and prefixes 1/2/4/8
2. double reorthogonalization
3. max action count 8/coordinate
4. full-action residual after unit-circle projection
5. H Ritz residualとD2 U residualの単位・意味分離
6. breakdown、conditioning、overlap、unwrap ambiguity
7. width formula byte-for-byte semantic equivalence to D2-A
8. result後のm/width/threshold変更拒否

## Branch / phase

1. common global energy offsetに対するsigned shift covariance
2. absolute and ground-removed winding integersが異なっても同一physical branchを認識
3. representation-independent energy difference
4. alias-indeterminateを小幅へfallbackしない
5. truthがpredictor ambiguityを救済しない
6. unscorable時にanchorを追加しない

## Status and comparison

1. 2/2 robustと1/2 limitedを分離
2. unsafeをresource winへ数えない
3. safe B1 frontierがM1をdominateする場合`cheap_proxy_sufficient`
4. point estimateが良くwidthだけが失敗する場合`fixed_width_no_benefit`
5. primary status priorityがdeterministic
6. gammaをpost-hoc winnerへ昇格しない
7. external baseline gate不合格ならimplementationを拒否

## Resource counters

全counter、nested timing、cache/shared/new、predictor/scorerを分離する。classical secondsとPauli rotationsを足す処理を拒否する。
