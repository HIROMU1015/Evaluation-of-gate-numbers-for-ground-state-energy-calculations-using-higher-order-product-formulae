# GPUサーバー側Codexへの実行依頼：P-SPEC-6 D1のみ

第二研究は`complete_no_benefit`で閉鎖済みで、R0/R1原因分離とD0 protocol設計も固定済みです。
今回は、研究方針を再検討するためのpost-hoc protocol-design pilotとして、既存HCl 6座標だけを使う
**P-SPEC-6/D1を一度だけ実行**してください。

D2、subspace/spectral surrogateの実装、新しいselector、安全margin、新分子holdout、複数PF比較、
新PF設計には進みません。D1の三分岐結果をcommit・pushして報告した時点で停止してください。

## 固定identity

- evidence commit：`a134ba3950a521225a14c46943d0dbe469425e00`
- D0 result commit：`0d13decb8793c5e6fd83075b1559e05424f93c04`
- D1 implementation commit：`03747a2ca85c46d593b4fcf1e4969fd45005e37e`
- D0 protocol：`review_response/pf_spectral_information_pilot_protocol_draft.json`
- D0 protocol SHA-256：
  `44d69fa249a075a6dd863ddc518a5d93da7e6699d4f888037c8476e68e5cdb9e`
- D0 authorization SHA-256：
  `74c7644a7e1f1f427e3fd2f9fe9d183828a588697f2d195bc5f04cd8f6f58f9a`
- D0 manifest SHA-256：
  `cb6bc10625c117ab025d2b94b54f6eccf4517cbd57e63c23417e712f958d8f87`
- D1 authorization：
  `review_response/pf_spectral_information_pilot_d1_authorization.json`
- D1 authorization SHA-256：
  `5ec7fc1d041f3b2c8d1ea9d1e5418a7a6e9c7d9773c96532d826a003714cc186`
- D1 runner：`review_response/run_pf_spectral_information_pilot_d1.py`
- D1 runner SHA-256：
  `aa2380feff4544b10e198c31ad0671deeac8d379a5d9f6b8996f3f45aa086caf`
- D1 unit test SHA-256：
  `ad860f4bdc732c907e9b711ab723fc9cccd471437aba78a9573b746ba831daae`
- Phase A cache amendment SHA-256：
  `a95a9abf87f1d428c35d34ed13cbea8c2ff930e91a3e5eb3a2550fd5d1dd1051`
- Phase A runtime inventory SHA-256：
  `5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91`

D0 protocolは`d1_not_authorized`のまま変更しません。今回の別authorizationだけが、固定D1を一回
実行する権限です。第二研究、R0、R1、D0の判定や成果物を変更しません。

## 今回許可する唯一の計算

固定済みの次の6座標だけを対象にします。

- HCl equilibrium：`0.5, 0.65, 0.8 * t_ana`
- HCl stretch150：`0.5, 0.65, 0.8 * t_ana`

元Phase A system cacheを読み、同じHamiltonianに対してCPU単一processで以下だけを許可します。

- same-H exact ground state：最大2件。
- 既存6座標のfull PF unitary再構築：最大6件。
- 既存6座標のPF eigendecomposition：最大6件。
- exact-ground spectral weights、phase cluster、top-K omitted contributionの事後診断。
- weight-rankedとoracle-contribution-rankedの分離評価。
- truth-free取得経路の資源上限内での候補整理。方法の実装・検証はしない。

## 禁止事項

- 新しい時刻座標、LiF計算、新分子、別geometry、別basis、別PFを追加しない。
- Phase A/Phase B、R1を再実行しない。
- 新しいdirect truth、追加proxy sampling campaignを開始しない。
- threshold、K、phase cluster閾値、allowance、三分岐規則を結果後に変更しない。
- subspace法、spectral surrogate、adaptive selectorを実装しない。
- GPUをquery、allocate、使用しない。`nvidia-smi`、CuPy import、GPU kernelを実行しない。
- Phase A runtimeを移動、コピー、修正、削除、再manifest化しない。
- 既存worktreeをreset、clean、stashせず、mainへmerge・force-pushしない。

## 元Phase A runtime

次の絶対pathだけを読み取り専用で使います。

```text
/home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694
```

`.runtime`は56 files、113,469,289 bytesです。runnerは全file set、relative path、bytes、SHA-256を
committed inventoryと照合した後、HCl system cache 2件だけを読み込みます。一件でも不一致なら
科学計算前に停止し、再構築や代替cacheを行いません。

## branchとworktree

```bash
git fetch origin --prune
git cat-file -e 0d13decb8793c5e6fd83075b1559e05424f93c04^{commit}
git cat-file -e 03747a2ca85c46d593b4fcf1e4969fd45005e37e^{commit}
git merge-base --is-ancestor \
  0d13decb8793c5e6fd83075b1559e05424f93c04 \
  03747a2ca85c46d593b4fcf1e4969fd45005e37e
```

このpromptを含むexecution bundle commitから独立worktreeと新規branchを作ります。推奨名は

`gpu-pf-spectral-information-pilot-d1-20260928`

です。同名があれば上書きせず連番を付けます。

## 固定process environment

Pythonは次をabsolute pathで使います。

```text
/home/AbeHiromu/venvs/trotter-common/bin/python
```

全commandで以下を置換設定します。

```text
PYTHONPATH=src:review_response:.
PYTHONNOUSERSITE=1
PYTHONDONTWRITEBYTECODE=1
OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

virtualenvをactivateせず、package、Python、CUDA、driver、shell設定を変更しません。D1はCPU-onlyで、
CuPy overlayとCUDA library pathを必要としません。

## 計算前gateとtest

1. 上記commit系譜と全固定SHA-256を照合する。
2. D0 decisionが`d0_complete_d1_not_authorized`で、新科学計算0であることを確認する。
3. D1 authorizationが一回のD1だけを許可し、D2を禁止していることを確認する。
4. 元Phase A runtime全56 filesとHCl system cache hashを照合する。
5. 次のfocused testsを実行し、fail/skip 0を要求する。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:." \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests/test_pf_spectral_information_pilot_d1.py \
  review_tests/test_pf_r1_reorientation_d0.py \
  review_tests/test_pf_candidate_validation.py \
  review_tests/test_second_study_safe_time_domain_execution.py \
  -p no:cacheprovider
```

続いて全`review_tests`を実行します。fail 0を要求し、skipは
`review_tests/test_pennylane_bch.py`の任意依存`pennylane`だけを最大1件許可します。
test logは一時pathへ保存し、D1 runner完了後に新規outputへ収録してください。runner実行前に
output directoryを作成しません。

## D1実行

新規outputは次を使います。

`artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2/`

実行前に存在する場合は上書きせず連番を付けます。単一CPU processで実行します。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:." \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_pf_spectral_information_pilot_d1.py \
  --project-root "$PWD" \
  --protocol review_response/pf_spectral_information_pilot_protocol_draft.json \
  --d0-authorization review_response/pf_spectral_information_pilot_authorization.json \
  --d1-authorization review_response/pf_spectral_information_pilot_d1_authorization.json \
  --phase-a-cache-amendment review_response/pf_candidate_validation_r1_phase_a_cache_amendment_v1_2.json \
  --phase-a-root /home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694 \
  --processes 1 \
  --output-dir artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2
```

中断時だけ、同じcommand・同じoutput・同じrun identityで再開できます。別outputへの切替、別run cache、
Phase B direct cache、R1 runtimeのコピー・流用は許可しません。

## 完了gateと三分岐

全source/numerical/resource gate合格時だけ、次のいずれかを正式完了とします。

- `d1_complete_prototype_candidate_stop`
- `d1_complete_information_cost_limit_stop`
- `d1_complete_close_spectral_route_stop`

以下を全件確認します。

- condition 2、既存coordinate 6、新規coordinate 0。
- full PF unitary 6、PF eigendecomposition 6、same-H exact ground 2以内。
- CPU単一process、GPU query/allocation/kernel 0。
- weight、eigenpair、unitarity、exact-ground、echo、saved direct shift/overlap、phase gap、branch gate合格。
- weight-rankedとoracle-contribution-rankedを混同せず、K=`1,2,4,8,all`を全座標で保存。
- omitted actual signed residualと`2*q_omit/t` conservative boundを別々に保存。
- D0のcoordinate allowanceに対する比を記録。
- concrete truth-free routeは候補と未解決点を記録し、D1で実装・検証済みとは主張しない。
- `D1_COMPLETE.json`は上記complete statusだけで存在する。
- `d2_authorized=false`、closed second-study判定不変。
- manifest記載fileのbytes/SHA-256が一致する。

数値またはsource/resource gateに失敗した場合はfailureとして停止し、閾値、K、座標、branch規則を
緩めません。別条件で救済しません。

## 計算後test、commit、push、停止

同じfocused/full testsを再実行し、pre/post command、Python identity、開始・終了時刻、pass/fail/skipを
新規output内のlog/auditへ保存します。runner生成manifestは書き換えず、記載fileを再hash照合します。

軽量CSV/JSON/report/test/resource logだけを新規branchへcommitします。`.runtime`、pickle、exact state、
unitary、eigenvector、npyをcommitしません。originへ新規non-force pushします。push権限がなければ
local result commitで停止し、次を正確に報告します。

```bash
git push -u origin <actual-branch>
```

最終報告には以下を示してください。

- branch、execution bundle/result commit、protocol/authorization/runner/manifest hash。
- Phase A runtime 56 files identityとHCl system cache 2件のhash。
- 6座標ごとのdimension、cluster数、target weight、direct shift、exact proxy、allowance。
- weight-ranked/oracle-rankedそれぞれの最小合格K、omitted weight、actual/bound allowance比。
- 最大eigenpair/unitarity/echo residual、最小phase gap、branch disagreement。
- exact/full-unitary/eigendecompositionのcomputed/reused件数、wall time、CPU peak RSS、GPU count 0。
- truth-free候補経路、資源見積り、未解決点。
- pre/post focused/full test件数。
- 三分岐statusと、その判定根拠。

報告後に停止してください。D2、方法開発、追加diagnostic、holdout、新分子、新PF、threshold調整へ
進まないでください。
