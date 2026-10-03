# H-chain current_m3 T0/B0 contract recovery / design

Status: `hchain_current_m3_contract_not_justified` (D)。これはread-onlyな契約監査の完了結果であり、H-chainのscientific failureやspectral/selective-calibration手法の失敗を意味しない。

## 1. Objective

前preflightは `hchain_crosscheck_contract_revision_required` で停止した。指定base `09400dd1911022575db03d3cae51d727dd7d7d84` から独立worktreeを作り、current_m3固有のscale・T0・B0が同じ研究上の意味で回復できるかを追跡した。previous content commitは `7164bf521494c0b70f51f616e082e89fb276cf65`。remote branch先端 `09400dd1911022575db03d3cae51d727dd7d7d84` は着手前にGitHub ref APIで確認した。

## 2. Existing H-chain evidence

53 source blobsをbase snapshotとbyte照合した。H4の第一研究CISD prediction、H2/H4のCISD D4 diagnostic、旧H2/H4 refinement、初期H6 holdout、canonical H6 holdoutを分離した。m5/Y8のdirect scalingは今回の契約に利用しない。異なるPFのwide-direct filesや旧 `4th(new_3)` scalar cacheも除外した。

前registryにある別snapshot `4b1ca6be834ae728e4e153c91a1f9bdb3be40219` のm5/Y8結果は、このworktreeのobject storeにはなく再照合していない。前registryの記録を新しいcurrent_m3 evidenceとして扱っていない。

## 3. current_m3 identity

固定order4、S2 sequenceは `[0.1960294407008384,0.2092246690782796,0.3316118001935053,-0.4737318199452465,0.3316118001935053,0.2092246690782796,0.1960294407008384]`。signは `U_P~exp(+iHt)`。KはH2=108、H4=2556、H6=14344。Kはmerged PF stepのPauli rotationsであり、matvecやgroup数ではない。

旧refinementの末尾compact係数2個はcanonicalより各1 ULP大きい。exact identityなしとして保存した。legacy `4th(new_3)` のtail `[0.40653666,0.21638706,0.14924614]` は別PFで、同じorder/m/Kだけでは同一視しない。

geometryはsourceにある1.0 Å間隔linear STO-3G、偶数系はneutral singlet。H2/H4のarchived matrix hashとH6のterm-order hashは別種。H6の400 population sectorと旧exact-ground用200 Z2 restrictionも同一のoperational CISD cacheとは扱わない。

## 4. t_ana recovery

保存scalarへの `(epsilon_E/(5*alpha))^(1/4)` 代入7件を行い、各保存値との差は0。

| system / source role | alpha | t_ana | operational利用 |
| --- | --- | --- | --- |
| H2 CISD D4 | 2.7384116611797706e-6 | 1.847045747947876 | 別model。継承proxy contractに未採用 |
| H4 CISD decision track | 1.3583752443385904e-5 | 1.237648718781152 | scaleのみ回復、T0ではない |
| H4 CISD D4 | 1.3583990899692943e-5 | 1.237643287257238 | 別model。近さによる代替なし |
| H6 canonical exact-ground fit | 1.9524968888670854e-5 | 1.130328683486731 | oracle diagnosticのみ |

他の3件は旧exact-ground/PF-ULP-variant値。全件は `hchain_tana_recovery.csv` にsource commit/hash付きで保存。新fit、coefficient最適化は0。

## 5. T0=0.5 t_ana review

HFでhalf-scaleがbaselineになったのはcancellation fallbackが発火し、cap端点を選んだためである。H4のnative decision trackは `[0.25,2.0]*proxy_t_ana` でcurrent_m3内の `1.2397952598800155` を選んでいる。half-scale保守域は継承されていない。

H4 half-scaleは既存cheap exact行が1件、canonical truth exact行は0件。truth格子範囲内でも安全性やbranch正当性を補間で認定しない。全系で同じ「既存domain lossへの介入」という意味を保証できず、T0は採用しない。詳細は `hchain_T0_contract_review.md`。

## 6. B0 recovery

継承ruleは `B0=1.01*C_hat(T0)`、continuous metric、beta=1.2。gammaはcostへ掛ける。H01のD4一項costはbetaを含まないため、保存数値をB0へ流用しない。H4には凍結CISD polynomialがあるがT0未成立。H6のexact-ground coefficientからB0を作らない。全系B0はnull。

## 7. Candidate plan

T0/B0が一意の系は0。従って数値candidateは0、`hchain_candidate_contract.csv` はschema headerだけ。3系×3点の9個はsymbolic design slotsにすぎず、絶対時刻・hex・allowance・budgetを生成しない。

## 8. Existing matched tuple coverage

H4にはcurrent_m3 CISD proxy39行とcanonical positive truth412行があり、H6 holdoutにはcanonical direct10行がある。しかし契約candidateが存在しないためmatched-data coverageは評価不能。M1/combined H1 costのexact matched tupleも認定していない。`0` のreuseは「sourceがない」の意味ではなく「正式candidateへ再利用を認定していない」の意味。nearby/nearest/interpolation、different state/PFのreuseは全て0。

## 9. Minimum new acquisition needed

契約未成立なので「missing9点」等の正確な取得数は算出不能。inventoryはmissing countをunknown/nullとし、先にmodel/state/T0のdesign判断が必要と明記した。別承認で3候補を固定する場合の構造的上限だけ、系ごとに3 chains、PF/H vector action各24以下、local proxy3 PF action＋3 H-exponential action、direct truth最大3点（exact reuse前）と記録した。これは実行計画でも承認でもない。H2はrank最大4、H6のCISD restriction未確定。timing/memory実測やGPUは0。

## 10. Research recommendation

判定D: `hchain_current_m3_contract_not_justified`。H2/H4/H6の共通half-scale baselineを既存HF contractの回復として扱う根拠が不足する。H4 scaleやCISD D4 scalarの存在だけでA/B/Cへ繰り上げない。

次は研究方針レビューで、(i)このcontrolled cross-checkを見送る、または(ii)別研究条件としてnative proxy baseline/forced conservative capを明示的に再設計するかを判断する。後者ならHFで観測したdomain-loss回復と、新たに強制したcapの解除効果を区別する。今は不足M1やtruthを埋めない。

S1Aのformal DはHClの保存four-gamma frontier不足によるもの。B2/H1 policyの実行検証が成功したとは扱わず、rule specificationも変更しない。

## 11. Limitations and stop

H-chainは第2研究v2のcontrolled cross-check候補であり、主評価や独立holdoutではない。この契約監査を新しい性能評価として数えない。

これは指定snapshot上の追跡可能なsource auditであり、全てのprivate/untracked/server cacheに資料が存在しないという証明ではない。CISD D4 expectationは近似状態からの情報候補だがHFと同じcheap operational routeではなく、真のPF shiftそのものでもない。正式科学判定を置換しない。

新Hamiltonian/state/proxy/PF action/H action/Arnoldi/M1/direct truth/fit/threshold optimization/GPUは全て0。cross-check execution、C1、D2-B、LiF、新分子・PFは未承認。content commitとprovenance/manifest commitを分離し、今回のpush承認はないためpushせず停止する。
