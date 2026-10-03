# H-chain component / mechanism controlled cross-check preflight

Status: `hchain_component_crosscheck_contract_blocked`。今回の完了はplanning/source auditまで。科学cross-check未実行。

## 1. Scope and fixed evidence

base `6cd821045baa070f4692e51870c2fab1e29396e0` は着手前にGitHub branch refで確認した。新規独立worktreeで作業し、前contract audit `hchain_current_m3_contract_not_justified` とS1A formal Dを変更していない。今回は人工的T0/B0、half-scale cap、domain-loss回復、B2/H1、selective routingを使用しない。分類は `controlled_component_mechanism_crosscheck`、主性能評価やholdoutではない。

## 2. System / PF identity

linear H2/H4/H6、STO-3G、spacing 1.0 Å、neutral singlet。固定current_m3 order4 coefficientをF01 registryおよびcanonical H6 holdoutから照合し、K=108/2556/14344をsource scalarで確認した。旧1-ULP current_m3 variant、m5/Y8、4th(new_3)は混ぜない。34 source blobsをbaseとbyte照合し、前manifestは13/13合格。

## 3. CISD inputs

H2/H4はreference+singles+doubles familyのarchived bundleがあり、そのfile hashとsaved normalization=1を確認した。H4 CISD subspace=27、population sector=36。H2は両方4。新しいnorm/residual計算やarray/state deserializationは0。predictor用sanitized Hchain adapterはまだ未検証で、exact stateを含むwhole NPZを渡せない。

H6はcompatible CISD hash/normalization/sector restrictionが未確定で `H6_state_contract_missing`。旧exact-state用200次元Z2をCISDへ移さない。H2/H4だけの実行を自動選択しない。

## 4. Fixed M1 versus H2 rank

継承coreはprimary=8とprefix=1,2,4,8を要求し、primary unavailableならfailure/abstention。H2の4次元sectorに8本のorthonormal Krylov basisは存在しない。これはsourceとdimensionからの静的推論であり、今回Arnoldiを走らせた結果ではない。m4へ変更しない。H2をexpected-abstention controlとして扱うかrank-aware仕様変更を別承認するかはreview事項。

同coreのwidthはempiricalであり、未実装のforward-action boundをcertificationとして主張しない。QPE allowance gateは継承実装に残るが、今回はbudget-performance評価とは分ける。

## 5. Time-grid audit

scientific shift/error magnitudeを使わず、sourceのpositive absolute timesだけを抽出した。

| system | saved finite-time CISD cheap times | direct scalar metadata times | saved M1 | cheap/truth exact metadata overlap |
| --- | ---: | ---: | ---: | ---: |
| H2 | 0 | 48 | 0 | 0 |
| H4 | 50 | 460 | 0 | 11 |
| H6 | 0 | 10 | 0 | 0 |

H4 cheap=39 decision-track＋11 positive fixed mechanism times。H4 truth=412 first-study＋48 F01。H6のoracle short-fitは別の5 timesとしてcatalogしたがcheapや完全truth行に数えない。全系canonical metadata unionは514 unique positive times。raw direct-scalar metadataの3系intersectionも空。operational cheap/M1-input/truth intersectionは空であり、selected time/coordinateは0。

H6追加direct 2点は別Hamiltonian coefficient hashでexcluded。time_grid_audit.csvに除外理由を残した。nearby/nearest/interpolationは0。最小/median/最大selection ruleは条件未達なので適用しない。even-cardinality medianの定義も勝手にmidpointへ拡張しない。

## 6. Matched-data inventory

matched_coordinate_inventory.csvの3行はsystem prerequisite placeholdersであり、実際の3点や9座標ではない。classificationはcontract_invalid、missing cheap/M1/truth/resource countはnull相当の空欄。selected grid未成立のため「9座標全部missing」とは言わない。歴史的同時刻cheap/truth scalar overlapも、M1/target gap/matched costを含むcomplete tupleの認定ではない。

## 7. Definitions and scorer

cheapはlocal CISD Im(echo)/tでありD4やexact-state echoへ置換しない。M1はsource/threshold/width不変。scorerはHF継承shift difference < phase-gap/(2t)の表現非依存diagnosticを計画し、unwrap整数を直接比較しない。保存Hchain truthに要求target phase gapがなく、principal-log cut marginやbranch-reliable flagでは代用できない。新gap/ground state計算は別承認。cheap branch labelも付けない。

## 8. Costs and execution limits

異種actionは分離。旧H4 full-matrix proxy timingをvector-only cheap armへ流用しない。conditional ceilingはcheap PF/Hexp各9、M1 PF/Hmatvec各72、direct<=9のみ。これはworst-case design ceilingでありexact missing countや実行権限ではない。新規PF/H/Arnoldi/cheap/M1/truth/state/gap/GPU/fitは全て0。wall/memory envelopeもreview前に独断で固定しない。

## 9. Decision and review handoff

primary statusはstate/M1 contract不成立による `hchain_component_crosscheck_contract_blocked`。time-grid substatusは `hchain_component_crosscheck_time_grid_requires_review`。既存snapshotだけで科学execution protocolの10 gateを全て満たせない。

reviewで必要なのは (1) H6 CISDが同family/identityで既存取得可能か、(2) H2 fixed-m8をexpected-abstention controlにするか別契約にするか、(3) 新absolute time gridの明示承認、(4) target-gap/scorer/sanitized input/resource envelopeの承認。これらが決まるまで追加取得に進まない。手法の精度や一般化の成功/失敗はこのpreflightから判断しない。

## 10. Integrity and stop

15 planning filesのみを作り、contentとprovenance/manifest commitを分離する。source registryはfirst publication originとverified snapshotを別fieldで持ち、manifestはself-excluded。既存artifactは変更せず、pushの新規承認がないためlocal commitで停止する。
