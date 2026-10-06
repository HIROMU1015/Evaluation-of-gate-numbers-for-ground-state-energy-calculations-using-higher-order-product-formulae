# Cost accounting — 実行回数の事前契約

**実測science countsは全部0。[JSON](expected_action_counts.json)は将来のnominal rank8見積もり。**

## 比較単位

H matvecはsaved Hと1vectorの積1回。basis構築でHpsi 1回、accepted direction毎のHz 1回、最大9回。r/E/LZ/Ritz H_mはこのcacheを使い、新しいH actionを足さない。projection1回はQv1回、orthogonalization1回はaccepted basis1列とのinner product/subtraction。フルrank8ならbasisだけでprojection25、MGS56。signed timeのa projection22を加えて47。

PF actionは`U_P(t)`またはそのadjointの1vectorへの作用。forward／adjointを別counterにする。`Wpsi`にはforward1回とexact-H echo1回、`W†psi`にはexact-H echo1回とadjoint1回が必要。adjoint chainのPF入力は`exp(+iHt)psi`なので、「original state上」は**original-state proxy chain**という意味であり、literalに未変化psiへ作用するという意味ではない。

Ritz scalarは`Im<phi|W|phi>/t`でforwardだけ。responseのfull aにはWpsiとW†psiが必要。baselineはresponseのforward expectationを再利用できる。保存baseline scalarはreferenceへ使えるが、responseに必要なWpsi vectorを代替できない。

## 予定回数

22 signed times、4 nonzero distinct prefixes k=1,2,4,8で、cacheを共有するjoint executionの回数：

| Counter | 1pass | cold replay込み |
|---|---:|---:|
| H matvec | 9 | 18 |
| Projection | 47 | 94 |
| Accepted-column MGS update | 56 | 112 |
| Response SVD factorization | 4 | 8 |
| Response RHS solve | 88 | 176 |
| Small projected Ritz eigh | 4 | 8 |
| PF forward | 110 | 220 |
| PF adjoint | 22 | 44 |
| Original-state proxy chain PF | 44 | 88 |
| Ritz-state PF | 88 | 176 |
| Exact-H echo action | 132 | 264 |
| New basis vectors | 8 | 16 |
| New Ritz states | 4 | 8 |
| Response vectors generated | 88 | 176 |
| Response vectors persistently stored | 0 | 0 |
| Unique signed PF/time coordinates | 22 | 22 |
| New H / ground / full-H eigh / Schur / direct truth | 0 | 0 |

Cold replayは独立のscience actionとして加算し、predictionは初回から一度だけfitする。9 operational/diagnostic arms×3 models=27 fits（うちprimary positive model9）。198 signed proxy rows、108 signed evaluation prediction rowsを保存。A3は後から既存scalarだけで3 reference fits、saved exact proxy22座標、saved direct12座標を読む。truth readerのraw processed rowsやcache-hit数も別記録し、distinct saved coordinate12をnew truthと数えない。

Primary m8だけのjoint executionなら1passでH9、forward44、adjoint22、合計PF66。cold込みH18、forward88、adjoint44、PF132。今回protocolはm1/2/4 diagnosticsも要求するため、実行予定全体はPF264。

単独methodの1pass費用は以下。standaloneは共通情報の構築費を各methodへ負わせる反実仮想の会計で、joint ledgerで二重請求しない。

| Primary method | H | forward | adjoint | small solver |
|---|---:|---:|---:|---|
| A0 bare | 0 | 22 | 0 | fitのみ |
| A1 response8 | 9 | 22 | 22 | SVD1、RHS22 |
| A2 Ritz8 | 9 | 22 | 0 | Ritz eigh1 |

baseline+H情報が既に共有されている場合の追加PFは、response=adjoint22、Ritz=新state forward22。単独PF数はresponseのほうが多い。どちらが有利かを結果前に決めない。Outcome Aにはaccuracy/riskとのtradeoffを示す必要がある。

## Dense backendの費用を隠さない

将来の固定CPU backendは、元S2-cache orderを保ち、保存groupの指数をscipy1.14.1のscaling/Padé expmで構築する。full H／group eigendecomposition、Schur、ground state取得は不要。4 unique S2 weightsそれぞれ25 group exponentials、7 block left compositions。各signed tにつきgroup expm100、PF dense matrix products107。22座標でgroup expm2200、PF dense matrix products2354、U builds22、exact-H expm22。cold込みで4400、4708、44、44。cacheは1build内の同じS2 blockだけを再利用し、signed time間やcold pass間で共有しない。

これは36×36 dense reconstruction費であり、logical PF actions264とは別の単位。実際のU/exact-H vector multiplicationとbackend internal norm/scaling/BLAS costをwall time/RSSと別counterに記録する。H spectral normはSVD1/passで取得し、full-H eigenvectorsを取得しない。PF unitarityと±U adjoint gateも別auditとして数える。group-sum/Hermiticity、hash/arraydecode/orthogonality/scalar fit costも無料とは扱わない。

PFは169 merged group steps、2556 Pauli rotations/stepという元定義を保持する。264 logical actionsのrotation equivalentは674784だが、dense cached simulationの実際のhardware gatesでも、fault-tolerant総資源費でもない。exact-H echo access、observable測定、state preparationを含む量子実装は今回確立していない。

## Rank stopとstorage

kはaccepted max rank、uは`min(m,k)`のnonzero unique prefixes数。1passのH=1+k、response SVD／Ritz eigh=u、RHS=22u、forward=22(1+u)、adjoint=22。m0相当のzero rankならRitzもbaselineを再利用する。同じprefixを別mラベルで再計算しない。uが同じでもactual state overlapで勝手にdedupして会計を減らさない。

Z/HZ/Bは最大8vectorずつ、4 Ritz states、psi/Hpsi/r、timeごとのa/z/echo buffersをprivate memoryで保持する。zは各timeをstreamしnorm/residualだけ保存するためpersistent response vectors=0。basis/stateのpeak memory、new-vector count、original CISD source reuse=1、cold rebuild count、temporary vectorsのpeak、backend matrices14種等のstorageを別記録する。working arraysの無承認commit/pushは行わない。Wall seconds、peak RSS、software/BLAS/thread情報はactionsと分離して保存する。

この見積もりはPhase 0の「追加response channels 22–44」の仮案を具体化した新仕様であり、元Phase 0 artifactを書き換えない。science posteriorによるcost scope変更はしない。
