# GPUサーバー側Codexへの実装・実行依頼：H-chain direct最適時刻 H5/H7/H8/H9

ローカル環境では、PF固有値誤差をdirect Schur分解から求め、連続QPEコスト

\[
C(t)=\frac{\beta N_{\exp}}{t\{\epsilon_E-|\Delta E_{\rm PF}(t)|\}}
\]

の固定grid最小時刻をH2/H4/H6で評価しました。m5では小系power-lawが有望でしたが、Y8では
同じlawを支持できませんでした。次はGPUサーバーで、奇数鎖H5/H7/H9と偶数鎖holdout H8を、
事前固定・段階実行してください。

今回の範囲は **このH-chain検証だけ** です。第二研究safe-time-domainのPhase A/B、新分子、別PF、
係数探索、threshold調整へ進まないでください。

## 親結果と固定identity

- repository remote：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- 結果ブランチ：`hchain-direct-optimal-time-scaling-20260927`
- 親結果commit：`c27e31e82ca55fc404ed33123cfd5d2c6a76bc35`
- 親protocol commit：`4b559fab2f4e60b513ad77e82c6e3733445d1e45`
- ordering-aware実装commit：`ce7b961f2df0017c375bb1ccc4b92e8d4cd3b9cc`
- H6部分解析固定commit：`9f98749e5ebcd9c7939ff80a8730b0e3d61a4d45`
- 親protocol SHA-256：`12d10562cf481b836242786462184d8a6ffb342153404c9bf84ff4d5ca836ab9`
- sector amendment v1.1 SHA-256：`5ca0ea30f9ad08bc7e4a54fcd8bab8f50195752dcaf3717c219281a458b0122e`
- partial-stop amendment v1.2 SHA-256：`526bdede05c1b39d0fab21e062b39a48284a1338fd51bc3c94fd3488732c70ff`

親結果では次が確定しています。

- H2/H4/H6：m5、Y8とも各31点、計186 direct点が採点可能。
- m5の偶数鎖fit：`t*(N)=6.632829966478654 N^(-0.4751330558462548)`。
- m5のH2/H4/H6 LOO最大相対誤差：`0.04033603534575492`。
- Y8の参考fit：`t*(N)=9.0780545356022 N^(-0.3303918655799976)`だが、LOO最大相対誤差
  `0.41514767113379847`のため予測則として不採用。
- H5/m5：`t_ana=2.5939977275727855`、`t_grid*=3.5018969322232607`、採点可能。
- H5/Y8：見かけ上の`relative t_grid*=1.25`だが、全grid最大branch shift不一致
  `0.01341058883834719 Ha`のため不採用。
- H7 direct完了点は0。ローカルの未完了runtimeはGPU入力・cacheとして使わない。

親branchをGPU cloneから取得できない場合は計算を始めず停止してください。既存worktreeをreset、clean、
stashせず、`c27e31e...`から独立worktreeと新規branchを作ります。推奨branch名は

`gpu-hchain-direct-optimal-time-scaling-h5-h9-20260927`

です。同名があれば連番を付けます。mainへmerge、force-pushしません。

## 科学的役割を混ぜない

- H5/H7/H9：odd cation triplet系列。m5について3サイズがすべて採点可能な場合だけexploratoryな
  power-law/LOO解析を行う。
- H8：even neutral singlet。H2/H4/H6のm5 lawに対する独立holdoutとして扱う。
- H8の事前予測値は
  `t_pred_m5(H8)=2.469510966041552`。
- H8/m5のholdout成功閾値は、親protocolと同じ相対誤差`<=0.20`。
- Y8は既存3点で予測則不成立なので、H8をconfirmatory success/failureへ使わず、参考値としてのみ報告する。
- odd/even系列を同じfitへ混ぜない。
- H5/Y8を含め、一つのcellがgate失敗しても値を科学的解析に使わない。その失敗成果物を保存した上で、
  独立した他cellの実行は継続できる。ただし当該PFのfamily fitは、必要な全cellが採点可能な場合だけ行う。

## Phase A：truth計算前の固定

direct PF計算前に、次を実装・testし、commitしてください。

1. GPU extension protocol/amendment JSONと説明文。
2. H5/H7/H8/H9をcell単位で独立実行できるrunner。
3. H5 CPU結果とのGPU parity testと、numerical/source/cache gateのtest。
4. Phase A predictions JSON、SHA-256、audit、`PHASE_A_FROZEN`。
5. 下記resource-feasibility estimator。

Phase AではHamiltonian、state、group spectrum、short-time fit、PF unitary、direct truthを新規生成しません。
親成果物の数値を読む場合も、上に明記した固定値とsource identityの照合だけに限定します。

Phase Aに最低限固定する値は次です。

- `epsilon_E=0.00015936001019904 Ha`
- `beta=1.2`
- PF：`4th(m5_best)`と`8th(Morales-Y8m10b)`のみ
- relative grid：`0.20, 0.25, ..., 1.70`の31点
- selection：continuously tracked branchのfinite cost最小
- endpoint最小：不採用
- near-optimal interval：最小costの1.01倍以下の連結成分
- well-localized：relative-time幅`<=0.25`
- complex precision：`complex128`
- 単一process・単一GPU・BLAS thread 1
- 各cellのcache key：全protocol/amendment hash、system、sector identity、PF、grid、backend、dtypeを含む
- 他run・ローカルrun・別cellのdirect cache再利用：0

Phase A commitが完了するまでdirect truthを計算しないでください。

## 固定numerical gate

親protocolから変更しません。

- unitarity Frobenius residual `<=1e-10`
- Schur off-diagonal Frobenius residual `<=1e-10`
- maximum-ground-overlap branchとcontinuous branchのshift差：全31点で`<=1e-10 Ha`
- selected optimumのground overlap `>=0.9`
- previous overlap `<0.5`はwarning
- grid端点最小はnot scorable

H5/Y8で既知の不一致が再現されても閾値を緩めず、そのcellを不採用にしてください。

## backend parity gate

新GPU backendは近似法に変更してはいけません。許す構成はconserved-sector内のexact dense PF unitaryと
complex128 Schurです。GPUでunitaryを構築してCPU Schurを行っても構いません。低rank化、truncation、
Krylov近似、低エネルギー射影、別dtype、grid間引きは禁止です。

最初の科学計算はH5再計算です。親commit収録のH5 rawをcacheにせず、GPUで62点を新規計算し、次を照合します。

- H5/m5のselected relative timeが`1.35`。
- H5/m5の各direct shiftがCPU結果と絶対`1e-9 Ha`以内。
- H5/m5の`maximum-ground`/continuous branch identityが各点で一致。
- H5/Y8の既知branch不一致が再現されること。不一致を隠すbranch rule変更は禁止。
- GPU unitaryを小さいH5でCPU builderと比較し、Frobenius差`<=1e-10`。

parity不一致なら`failed_backend_parity`として停止し、H7以降へ進みません。

## 実行順序と出力分離

cellごとに上書きしないoutputを使い、次の順序で実行します。

1. H5/m5
2. H5/Y8
3. H7/m5
4. H7/Y8
5. H8/m5
6. H8/Y8
7. H9/m5
8. H9/Y8

H5、H7、H8、H9は別directoryとし、完了cellを後続の失敗から保護してください。各cellは同一output内の
protocol-identical cacheだけ再開可です。各31 direct点に加え、固定short-time fit点は別会計にします。

例：

```text
artifacts/server_hchain_direct_optimal_time_h5_20260927_<phaseA-short>/
artifacts/server_hchain_direct_optimal_time_h7_20260927_<phaseA-short>/
artifacts/server_hchain_direct_optimal_time_h8_20260927_<phaseA-short>/
artifacts/server_hchain_direct_optimal_time_h9_20260927_<phaseA-short>/
```

H7まで完了したら、実測wall time、最大CPU RSS、最大GPU memoryを用いてH8/H9 resource gateを再評価します。

## H8/H9 resource-feasibility gate

現行sectorは次を想定します。実測identityが異なる場合は計算せず停止します。

| system | family | populations | sector dimension | expected group count | complex128 matrix | group eigenvector lower bound |
|---|---|---:|---:|---:|---:|---:|
| H5 | odd cation triplet | (3,1) | 50 | 45 | 0.00004 GiB | 0.002 GiB |
| H7 | odd cation triplet | (4,2) | 735 | 105 | 0.0081 GiB | 0.85 GiB |
| H8 | even neutral singlet | (4,4) | 4900 | 136 | 0.358 GiB | 48.66 GiB |
| H9 | odd cation triplet | (5,3) | 10584 | 171 | 1.669 GiB | 285.44 GiB |

上のlower boundはgroup eigenvectorsだけであり、Hamiltonian、eigh workspace、PF block cache、unitary、Schur
workspaceを含みません。m5は11 S2 weights・6 unique weights、Y8は21 weights・11 unique weightsです。

各targetについて、device allocationやHamiltonian生成前に次を記録します。

- host total/available memory、GPU total/free memory、既存process
- backend別の全resident array一覧、shape、dtype、bytes、host/device配置
- group spectra、unique S2 block cache、unitary、Schur、eigenvector、workspaceを含むpeak memory上限
- H7実測を基にした一pointおよび31点のwall-time予測
- dense演算量の少なくとも`group_count * dimension^3`比例による保守的外挿

自動実行条件は、(a) 見積peakに対してhost/deviceとも最低20%の余裕があり、(b) allocation planが
`complex128` exact計算を維持し、(c) 対象system・PFの予測wall timeが72時間以下、の全てです。
一つでも満たさなければ、そのsystem以降を`not_run_resource_infeasible`として停止し、追加承認を求めてください。
OOMを試して確認しないでください。メモリ不足時にmethod、precision、gridを変更しません。

H8が不可でもH7結果は有効です。H9が不可でもH8以前の結果は有効です。resource stopを科学的な
scaling failureとして数えないでください。

## 分析

各採点可能cellについて少なくとも次を保存します。

- `t_ana`
- `t_grid*`と`t_grid*/t_ana`
- selected direct PF error、minimum cost
- `cost(t_grid*)/cost(t_ana nearest grid)`
- neighbor bracket
- 1% near-optimal intervalと幅
- sign-change intervalとの交差
- 全numerical residual、minimum overlap、gate結果

H8/m5では固定予測`2.469510966041552`に対する相対誤差を計算し、`<=0.20`だけをholdout successとします。
grid discretizationについては、観測` t_grid* `のneighbor bracketも併記し、連続最適値を得たとは主張しません。

H5/H7/H9のodd familyは、同一PFの3 cellすべてがscorableかつwell-localizedの場合だけ
`t*=a N^b`とconstant modelのleave-one-size-outを計算します。H5/Y8が既知gate失敗のままならY8 odd fitを
作りません。thresholdやdomainを結果に合わせて変更しません。

## tests、成果物、commit、push

Phase A前、各system後、最終時にfocused testsを実行します。最終時には全`review_tests`も実行します。
各outputには少なくとも次を保存します。

- `protocol.json`、全amendment
- `predictions.json`、`prediction.sha256`、`PHASE_A_FROZEN`
- `source_manifest.json`
- `resource_feasibility.json`
- cell別raw JSON
- `scoring.csv`
- `scaling.json`
- `audit.json`
- `manifest.json`
- `report.md`
- test logs

`.runtime`、大容量pickle/npy、archive、GPU一時配列はcommitしません。軽量成果物とraw JSON、report、test logを
新規結果branchへcommitし、originへnon-force pushします。既存結果をamend/rebaseしません。

最終報告には次を示してください。

- branch、Phase A commit、最終commit、全output path
- protocol/amendment/prediction hash
- Python/CUDA/GPU identity
- H5 parity結果
- system/PF別のdirect点数、`t_ana`、`t_grid*`、比、cost改善
- 最大unitarity/Schur/branch差、最小overlap、全gate結果
- H8/m5 holdout誤差と固定判定
- odd m5/Y8 scaling結果、またはfit不能理由
- H8/H9 memory/time見積、実行またはresource stop理由
- wall time、最大CPU RSS、最大GPU memory、test件数
- 未解決事項

その後停止してください。別PF、H10以降、time domain拡張、threshold調整、第二研究Phase A/Bへ自動的に
進まないでください。
